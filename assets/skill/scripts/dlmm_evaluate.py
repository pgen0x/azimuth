#!/usr/bin/env python3
"""Deterministic read-only evaluation; persists report plus auditable inputs."""
import argparse
import collections
import concurrent.futures
import json
import math
import os
from pathlib import Path
import re
import subprocess
import time
from dlmm_accounting import report, root_decision, rows, unvalued_token_inflows
from dlmm_shadow import bin_replay, HORIZONS
from dlmm_realized import fetch_pools, fetch_closed_positions


def replay_root_decision(decision):
    # The executor persists the exact evidence used after settlement refresh.
    result=root_decision(decision.get('chain'),decision.get('opportunity_sol'),
                         decision.get('floor_sol',-0.015),decision.get('strike_cap',3))
    return dict(ts=decision['ts'],root=decision['root_chain_id'],
                original='recenter' if decision['allow'] else 'stop',
                proposed='recenter' if result['allow'] else 'stop',reason=result['reason'],
                original_reason=decision['reason'],cumulative_net_sol=result.get('cumulative_net_sol'),
                basis='persisted_executor_decision_evidence')


def root_cash_cohort(accounting, start, end):
    """Root cash for recorded activity contained in the window; unknowns stay visible."""
    cohort = [c for c in accounting['chains'] if c.get('positions')
              and c.get('first_activity') is not None
              and start <= c['first_activity'] <= c['last_activity'] <= end]
    settled = [c for c in cohort if c['accounting_status'] == 'settled_cash']
    return dict(window_roots=len(cohort), settled_roots=len(settled),
                incomplete_roots=len(cohort)-len(settled),
                cash_positive_roots=sum(c['wallet_delta_lamports'] > 0 for c in settled),
                settled_cash_sol=sum(c['wallet_delta_lamports'] for c in settled)/1e9 if settled else None,
                basis='root_wallet_cash_after_fees_and_rent_not_economic_profit_or_trading_win_rate',
                roots=[dict(root=c['root_chain_id'], status=c['accounting_status'],
                            cash_sol=c['settled_cash_pnl_sol'], lp_pnl_sol=c['lp_pnl_sol'],
                            reasons=c['reasons']) for c in cohort])


def evaluate(profile, start, end, rejects):
    memory=profile/'memories'
    accounting=report(profile, end)
    closes={r['position']:r for r in rows(memory/'dlmm_closes.jsonl') if r.get('position') and not r.get('dry_run') and start <= r.get('ts',0) <= end}
    facts={r['signature']:r for r in rows(memory/'dlmm_wallet_transactions.jsonl') if r.get('observed_at',end+1)<=end}
    events=rows(memory/'dlmm_transactions.jsonl')
    close_proofs={position:[e['signature'] for e in events if e.get('position')==position
                            and facts.get(e['signature'],{}).get('position_account_closed')]
                  for position in closes}
    decisions=[r for r in rows(memory/'dlmm_recenter_decisions.jsonl') if start <= r['ts'] <= end]
    comparisons=[]
    for decision in decisions:
        evidence=report(profile,decision['ts'])
        chain=next((c for c in evidence['chains'] if c['root_chain_id']==decision['root_chain_id']),None)
        opportunity=None
        if (decision.get('fee_pace_pct_30m') is not None and decision.get('size_sol') is not None
                and 0 <= decision['ts']-(decision.get('fee_pace_observed_at') or 0) <= 1800):
            opportunity=decision['fee_pace_pct_30m']*decision['size_sol']/100
        alternative=root_decision(chain,opportunity,decision.get('cb_floor_sol',-0.015),decision.get('strike_cap',3))
        comparisons.append(dict(ts=decision['ts'],root=decision['root_chain_id'],original=decision['decision'],
            proposed='recenter' if alternative['allow'] else 'stop',reason=alternative['reason'],
            cumulative_net_sol=alternative.get('cumulative_net_sol'),basis='evidence_observed_by_decision_time'))
    outcomes={r['id']:r for r in rows(memory/'dlmm_reject_outcomes.jsonl')}
    cohorts={}
    for r in rows(rejects):
        if start <= r['ts'] <= end: cohorts.setdefault(r['id'],r)
    groups={}
    for ident,r in cohorts.items():
        key=r['mode']+'/'+r['gate']
        group=groups.setdefault(key,dict(total=0,pending=0,measured=0,censored=0,unmeasured=0,positive_proxy=0))
        group['total']+=1
        outcome=outcomes.get(ident)
        if not outcome or outcome['observed_at']>end: group['pending']+=1;continue
        group[outcome['status']]+=1
        if outcome.get('estimated_false_reject_proxy'):group['positive_proxy']+=1
    for g in groups.values():
        g['estimated_false_reject_proxy_rate']=g['positive_proxy']/g['measured'] if g['measured'] else None
    samples=rows(memory/'dlmm_bin_samples.jsonl');bins=[]
    for file in (memory/'dlmm_entries').glob('*.json'):
        entry=json.loads(file.read_text())
        if not start <= entry.get('deployed_at',0) <= end:continue
        chain=next((c for c in accounting['chains'] if entry['position'] in c['positions']),None)
        cost=None
        if chain and chain.get('accounting_status')=='settled_cash':
            cost=(chain['network_fee_lamports']+chain.get('nonrefundable_account_cost_lamports',0))/1e9/max(1,len(chain['positions']))
        result=bin_replay(entry,[s for s in samples if s['position']==entry['position'] and s['ts']<=end],cost)
        bins.append(dict(position=entry['position'],**result))
    snapshots=[s for s in rows(memory/'dlmm_nav.jsonl') if start<=s['ts']<=end]
    cash_samples=sorted((s for s in snapshots if isinstance(s.get('native_sol'),(int,float))
                         and math.isfinite(s['native_sol'])),key=lambda s:s['ts'])
    native_cash=None
    if len(cash_samples)>=2 and cash_samples[-1]['ts']>cash_samples[0]['ts']:
        first,last=cash_samples[0],cash_samples[-1]
        fields=('ts','native_sol','refundable_rent_sol','lp_mark_sol','spl_mark_sol','nav_sol')
        native_cash=dict(start={k:first.get(k) for k in fields},end={k:last.get(k) for k in fields},
                         change_sol=round(last['native_sol']-first['native_sol'],9),
                         basis='observed_native_balance_change_not_trading_profit')
    valid=[s for s in snapshots if s.get('nav_sol') is not None]
    wealth=None
    unvalued_inflows=[]
    if len(valid)>=2 and valid[-1].get('wallet_history_complete') and not valid[-1].get('unclassified_transactions'):
        facts={r['signature']:r for r in rows(memory/'dlmm_wallet_transactions.jsonl') if r.get('observed_at',end+1)<=end and r.get('landed') is not False}
        unvalued_inflows=unvalued_token_inflows(facts.values(),valid[0]['end_slot'],valid[-1]['end_slot'])
        if not unvalued_inflows:
            external=sum(r.get('external_flow_lamports') or 0 for r in facts.values() if valid[0]['end_slot']<r['slot']<=valid[-1]['end_slot'])/1e9
            wealth=dict(start_ts=valid[0]['ts'],end_ts=valid[-1]['ts'],start_nav_sol=valid[0]['nav_sol'],end_nav_sol=valid[-1]['nav_sol'],external_flow_sol=external,
                    flow_adjusted_change_sol=valid[-1]['nav_sol']-valid[0]['nav_sol']-external)
    last_nav=snapshots[-1] if snapshots else {}
    price_coverage=dict(collection_status=last_nav.get('price_sources',{}),
        token_counts=dict(collections.Counter(t.get('basis','unknown') if t.get('mark_sol') is not None else 'unpriced' for t in last_nav.get('tokens',[]))))
    live=[r for r in rows(memory/'dlmm_root_decisions.jsonl') if start<=r['ts']<=end]
    return dict(start=start,end=end,generated_at=int(time.time()),close_count=len(closes),close_account_proofs=close_proofs,accounting=accounting,
                root_cash_cohort=root_cash_cohort(accounting,start,end),
                wealth_change=wealth,native_cash_change=native_cash,unvalued_external_token_inflows=unvalued_inflows,price_coverage=price_coverage,nav_samples=len(snapshots),complete_nav_samples=len(valid),
                root_replay=[replay_root_decision(r) for r in live],eligibility_replay=comparisons,root_live_decisions=live,
                rejected_candidates=groups,bin_replay=bins,
                limits=['Native SOL changes include deployments, withdrawals, swaps, fees, rent and external transfers; they are not trading profit. Rent and incomplete token marks are shown separately, never treated as complete NAV.',
                        'LP PnL is a position valuation before wallet settlement, not net wallet profit.',
                        'Rejected-candidate rate is a price proxy above a fixed 1% hurdle, not realized LP profit.',
                        'Bin replay assumes infinitesimal fixed shares; no market-impact or hypothetical recenter execution.',
                        'Unavailable historical bin/settlement observations are unmeasured; never reconstructed using future information.'])


def compare_lp(wallets, start, end):
    result = {}
    for name, wallet in wallets.items():
        try:
            pools = [p for p in fetch_pools(wallet) if int(p.get("lastClosedAt") or 0) >= start]
            def get(pool):
                return fetch_closed_positions(wallet, pool["poolAddress"])
            positions = {}
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as workers:
                for batch in workers.map(get, pools):
                    for p in batch:
                        if start <= int(p.get("closedAt") or 0) < end:
                            positions[p["positionAddress"]] = p
            cohort = [p for p in positions.values() if start <= int(p.get("createdAt") or 0)
                      and float(p.get("allTimeDeposits", {}).get("total", {}).get("sol") or 0) > 0]
            pnl = [float(p["pnlSol"]) for p in cohort]
            deposit = sum(float(p["allTimeDeposits"]["total"]["sol"]) for p in cohort)
            result[name] = dict(status="measured", full_life_positions=len(cohort), carry_in_closes=len(positions)-len(cohort),
                                lp_pnl_sol=sum(pnl), deposits_sol=deposit, wins=sum(v>0 for v in pnl),
                                pnl_per_deposit_pct=sum(pnl)/deposit*100 if deposit else None,
                                basis="Meteora_position_LP_valuations_not_wallet_NAV", positions=list(positions.values()))
        except Exception as exc:
            result[name] = dict(status="unmeasured", error=type(exc).__name__)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profile',type=Path,default=Path(os.path.abspath(__file__)).parent.parent.parent.parent)
    p.add_argument('--start',type=int,required=True);p.add_argument('--end',type=int,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--rejects',type=Path,default=Path.home()/'.local/state/azimuth/solana_rejects.jsonl')
    p.add_argument("--reference-wallet")
    a=p.parse_args()
    if a.end<=a.start or a.end>time.time():p.error('evaluation requires a completed positive window')
    a.output.mkdir(parents=True,exist_ok=True)
    data=evaluate(a.profile,a.start,a.end,a.rejects)
    if a.reference_wallet:
        values = {}
        for line in (a.profile/".env").read_text().splitlines():
            if line.startswith("SOLANA_PUBLIC_KEY="):
                values["azimuth"] = line.split("=", 1)[1].strip().strip("\"'")
        values["meridian"] = a.reference_wallet
        data["lp_comparison"] = compare_lp(values,a.start,a.end)
    raw=subprocess.run(['journalctl','--user','-u','azimuth.service','-u','azimuth-sol-monitor.service','--since','@'+str(a.start),'--until','@'+str(a.end),'--no-pager'],capture_output=True,text=True,timeout=60)
    logs=re.sub(r'https?://[^\s\"\']+','[URL REDACTED]',raw.stdout)
    (a.output/'runtime.log').write_text(logs)
    data['runtime']={'journal_ok':raw.returncode==0,'expired_mentions':logs.lower().count('expired'),
        'rpc_warning_mentions':logs.count('[RPC WARN]'),'root_refusals':logs.count('ENTRY REFUSED:'),
        'note':'Counts are log mentions, not unique transactions or proof of provider outage.'}
    (a.output/'evaluation.json').write_text(json.dumps(data,indent=2,allow_nan=False))
    lines=['# Azimuth Solana evaluation',f"Window UTC epoch: {a.start} – {a.end}",
        f"Closes: {data['close_count']}; account deletion proofs: {sum(bool(v) for v in data['close_account_proofs'].values())}; complete marked NAV samples: {data['complete_nav_samples']}/{data['nav_samples']}.",
        '## Native SOL cash (not trading profit)',json.dumps(data['native_cash_change']) if data['native_cash_change'] else 'Unmeasured: fewer than two distinct native balance snapshots in this window.',
        'Cash uses the displayed snapshot times. Rent is recoverable reserve; token and LP marks are not necessarily executable proceeds. Complete wallet profit remains unmeasured when NAV is incomplete.',
        '## LP comparison (full-life cohort; not net wallet profit)',json.dumps({k:{field:value for field,value in v.items() if field!="positions"} for k,v in data.get('lp_comparison',{}).items()}),'## Wallet wealth',json.dumps(data['wealth_change']) if data['wealth_change'] else 'Unmeasured: incomplete marks/history or external token inflows without transfer-time valuation.',
        'Unvalued external token inflows: '+json.dumps(data['unvalued_external_token_inflows']),
        '## Root settlement cash (recorded activity within window; not economic profit)',
        json.dumps(data['root_cash_cohort']),
        'Cash includes network fees and rent paid by recorded root transactions. Recoverable rent remains an asset; later wallet-level rent refunds are not credited to these roots. Cash-positive roots are not a trading win rate. Incomplete roots are excluded from the cash subtotal, not counted as zero.',
        '## Pooled settlement cash (full-life groups; no per-root allocation)',
        json.dumps([g for g in data['accounting'].get('pooled_settlements',[]) if a.start <= g['first_activity'] and g['last_activity'] <= a.end]),
        '## Latest token valuation coverage',json.dumps(data['price_coverage']),
        '## Root-chain replay',f"Decisions: {len(data['root_replay'])}; reasons: {dict(collections.Counter(r['reason'] for r in data['root_replay']))}",
        '## Pre-settlement eligibility replay',f"Decisions: {len(data['eligibility_replay'])}; evaluated before settlement refresh, separately from executor authorization.",
        '## Rejected candidates','```json',json.dumps(data['rejected_candidates'],indent=2),'```',
        '## Bin replay',str(dict(collections.Counter(r['status'] for r in data['bin_replay']))),
        '## Runtime',json.dumps(data['runtime']), '## Limits',*['- '+s for s in data['limits']],
        'Full evidence: evaluation.json and runtime.log. No trading parameters were changed by this evaluation.']
    (a.output/'report.md').write_text('\n\n'.join(lines)+'\n')
    print(json.dumps({'report':str(a.output/'report.md'),'closes':data['close_count'],'nav_samples':data['nav_samples']}))

if __name__=='__main__':main()
