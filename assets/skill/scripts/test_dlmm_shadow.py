from dlmm_shadow import bin_replay, rejected_outcome
from dlmm_accounting import root_decision

r=dict(id='a',ts=100,mode='pulse',gate='momentum',snapshot={'pool_price':1},candidate={'sol_is_x':False})
assert rejected_outcome(r,2,1800) is None
assert rejected_outcome(r,1.02,1900)['estimated_false_reject_proxy']
assert rejected_outcome(r,2,2601)['status']=='censored'
assert rejected_outcome(r,None,1900)['status']=='unmeasured'
root=dict(accounting_status='settled_cash',positions=['a','b'],network_fee_lamports=1000000,nonrefundable_account_cost_lamports=0,settled_cash_pnl_sol=-0.005)
assert root_decision(root,0.001)['allow'] is False
assert root_decision(root,0.02)['allow'] is True
assert root_decision(root,0.02,strike_cap=1)['reason']=='root_strike_cap'
assert root_decision(None,1)['reason']=='incomplete_chain'
assert root_decision(root,None)['allow'] is False
b=dict(id=0,x='0',y='1000000000',supply=str(1000000000*2**64),fee_x='0',fee_y='0',price=1)
entry=dict(size_sol=0.1,bin_snapshot=dict(ts=1,active_bin=0,sol_is_x=False,price=1,decimals_x=9,decimals_y=9,bins=[b]))
end=dict(ts=61,active_bin=0,price=1,bins=[dict(b,fee_y=str(2**64//100))])
replay=bin_replay(entry,[end],0.0001)
assert replay['status']=='modeled'
for v in replay['schemes'].values():
 assert v['active_bin_utilization']==1
 assert v['il_vs_hodl_sol']==0
 assert v['fee_capture_sol']>0
 assert v['net_after_observed_cost_sol']<v['gross_pnl_sol']
assert bin_replay({},[end])['status']=='unmeasured'

# A mixed active bin does not turn the SOL-only HODL benchmark into a token basket.
mixed_bin=dict(b,x='1000000000')
sol_entry=dict(entry,amount_x=0,amount_y=0.1,strategy='sol_bidask',entry_bin=0,
               bins_below=0,bins_above=0,bin_snapshot=dict(entry['bin_snapshot'],bins=[mixed_bin]))
dump=dict(end,price=0.5,bins=[dict(mixed_bin,x='1500000000',y='500000000')])
sol_replay=bin_replay(sol_entry,[dump])
assert sol_replay['hodl_basis']=='recorded_SOL_only_input'
assert sol_replay['expected_bidask_reference_scheme']=='far_active'
for v in sol_replay['schemes'].values():
 assert abs(v['il_vs_hodl_sol']+0.0375)<1e-12
 assert v['il_vs_hodl_sol']==v['principal_change_sol']
legacy=bin_replay(dict(sol_entry,amount_y=None),[dump])
assert legacy['hodl_basis']=='modeled_initial_bin_inventory'
assert abs(legacy['schemes']['uniform']['il_vs_hodl_sol']+0.0125)<1e-12
assert sol_replay['schemes']['uniform']['fee_capture_sol']==legacy['schemes']['uniform']['fee_capture_sol']
assert sol_replay['schemes']['uniform']['gross_pnl_sol']==legacy['schemes']['uniform']['gross_pnl_sol']
mirror=dict(sol_entry,amount_x=0.1,amount_y=0,
            bin_snapshot=dict(sol_entry['bin_snapshot'],sol_is_x=True))
mirror_replay=bin_replay(mirror,[dict(dump,price=2,bins=[dict(mixed_bin,x='500000000',y='1500000000')])])
assert mirror_replay['hodl_basis']=='recorded_SOL_only_input'
assert mirror_replay['expected_bidask_reference_scheme'] is None
assert abs(mirror_replay['schemes']['uniform']['il_vs_hodl_sol']+0.0375)<1e-12
for bad in (True,float('nan'),float('inf'),0.2):
 assert bin_replay(dict(sol_entry,amount_y=bad),[dump])['hodl_basis']=='modeled_initial_bin_inventory'
assert bin_replay(dict(sol_entry,amount_x=False),[dump])['hodl_basis']=='modeled_initial_bin_inventory'
for change in ({'strategy':'turnover_rebalance'},{'entry_bin':1},{'bins_below':True},{'bins_above':1}):
 assert bin_replay(dict(sol_entry,**change),[dump])['expected_bidask_reference_scheme'] is None
three_bins=[dict(b,id=i) for i in (-2,-1,0)]
wide=dict(sol_entry,bins_below=2,bin_snapshot=dict(sol_entry['bin_snapshot'],bins=three_bins))
wide_end=dict(end,bins=three_bins)
assert bin_replay(wide,[wide_end])['expected_bidask_reference_scheme']=='far_active'
gap=dict(wide,bin_snapshot=dict(wide['bin_snapshot'],bins=[three_bins[0],three_bins[-1]]))
assert bin_replay(gap,[wide_end])['expected_bidask_reference_scheme'] is None
print('Root loss/cost gates and forward shadow outcomes/bin replay passed')

from dlmm_evaluate import replay_root_decision
r=dict(ts=200,root_chain_id='a',chain=root,opportunity_sol=0.02,allow=True,reason='root_cost_budget_pass')
assert replay_root_decision(r)['proposed']=='recenter'
assert replay_root_decision(dict(r,opportunity_sol=None))['reason']=='fee_opportunity_unavailable'
assert replay_root_decision(dict(r,chain=None))['reason']=='incomplete_chain'

# Evaluate the actual report path, not just the shared inflow predicate.
import json
import tempfile
from pathlib import Path
from dlmm_evaluate import evaluate
with tempfile.TemporaryDirectory() as directory:
 profile=Path(directory); memory=profile/'memories'; memory.mkdir()
 snapshots=[dict(ts=100,end_slot=10,nav_sol=1,wallet_history_complete=True),
            dict(ts=200,end_slot=20,nav_sol=1.5,wallet_history_complete=True)]
 (memory/'dlmm_nav.jsonl').write_text(''.join(json.dumps(s)+'\n' for s in snapshots))
 fact=dict(signature='gift',observed_at=150,slot=15,classification='external_token_inflow',token_deltas_raw={'mint':'10'})
 def assessment(record):
  (memory/'dlmm_wallet_transactions.jsonl').write_text(json.dumps(record)+'\n')
  return evaluate(profile,100,200,profile/'rejects.jsonl')
 result=assessment(fact)
 assert result['native_cash_change'] is None
 assert result['wealth_change'] is None
 assert result['unvalued_external_token_inflows']==['gift']
 assert result['accounting']['flow_adjusted_wealth_change_sol'] is None
 cash=assessment(dict(fact,classification='external_transfer',external_flow_lamports=500000000))
 assert cash['wealth_change']['flow_adjusted_change_sol']==0
 assert cash['accounting']['flow_adjusted_wealth_change_sol']==0
 assert assessment(dict(fact,slot=9))['wealth_change']['flow_adjusted_change_sol']==0.5
 assert assessment(dict(fact,slot=None))['wealth_change'] is None
 # Reclaim transfers existing reserve into cash; only service/network fees
 # change wealth. A positive cash receipt must not become a positive NAV return.
 snapshots[0]['nav_sol']=1.000000200; snapshots[1]['nav_sol']=1.000000193
 (memory/'dlmm_nav.jsonl').write_text(''.join(json.dumps(s)+'\n' for s in snapshots))
 maintenance=assessment(dict(fact,classification='rent_maintenance',external_flow_lamports=0,
                            wallet_delta_lamports=193,rent_maintenance={'released_lamports':200,'service_fee_lamports':2},fee_lamports=5))
 assert abs(maintenance['wealth_change']['flow_adjusted_change_sol'] + 7e-9)<1e-15
 assert abs(maintenance['accounting']['flow_adjusted_wealth_change_sol'] + 7e-9)<1e-15
 # Cash remains measurable when token prices prevent complete NAV. A deployment
 # moves cash into LP/rent; displaying its outflow must not invent a net loss.
 snapshots=[dict(ts=100,end_slot=10,native_sol=0.5,nav_sol=None,lp_mark_sol=0,refundable_rent_sol=0.1),
            dict(ts=200,end_slot=20,native_sol=0.35,nav_sol=None,lp_mark_sol=0.1,refundable_rent_sol=0.15)]
 (memory/'dlmm_nav.jsonl').write_text(''.join(json.dumps(s)+'\n' for s in reversed(snapshots)))
 result=assessment(fact)
 assert result['wealth_change'] is None
 assert result['native_cash_change']['change_sol']==-0.15
 assert result['native_cash_change']['start']['ts']==100
 assert result['native_cash_change']['end']['lp_mark_sol']==0.1
 assert result['native_cash_change']['end']['refundable_rent_sol']==0.15
 assert result['native_cash_change']['basis']=='observed_native_balance_change_not_trading_profit'
 assert evaluate(profile,101,200,profile/'rejects.jsonl')['native_cash_change'] is None
print('Evaluation excludes unvalued gifts and subtracts known external cash flows')

# A positive LP mark can coexist with negative spendable cash while rent is held.
from dlmm_evaluate import root_cash_cohort
cash_root = dict(root_chain_id='closed', positions=['p'], first_activity=100,
                 last_activity=190, accounting_status='settled_cash',
                 wallet_delta_lamports=-865793, settled_cash_pnl_sol=-0.000865793,
                 lp_pnl_sol=0.000676761, reasons=[])
incomplete = dict(cash_root, root_chain_id='open', accounting_status='incomplete',
                  settled_cash_pnl_sol=None, reasons=['open_or_unjournaled_positions'])
cash = root_cash_cohort({'chains': [cash_root, incomplete,
    dict(cash_root, first_activity=99), dict(cash_root, last_activity=201),
    dict(cash_root, positions=[], root_chain_id='unattributed')]}, 100, 200)
assert (cash['window_roots'], cash['settled_roots'], cash['incomplete_roots']) == (2, 1, 1)
assert cash['settled_cash_sol'] == -0.000865793 and cash['cash_positive_roots'] == 0
assert cash['roots'][0]['lp_pnl_sol'] > 0
assert root_cash_cohort({'chains': [incomplete]}, 100, 200)['settled_cash_sol'] is None
print('Root cash cohort excludes carry-in, future and unattributed cash; incomplete is not zero')

# Refund-adjusted groups must fit the entire evaluation window.
from unittest.mock import patch
import dlmm_evaluate as evaluation_module
with tempfile.TemporaryDirectory() as root:
    profile=Path(root)
    inside=dict(first_activity=100,last_activity=200,root_chain_ids=["inside"])
    carry=dict(first_activity=99,last_activity=200,root_chain_ids=["carry"])
    late=dict(first_activity=100,last_activity=201,root_chain_ids=["late"])
    with patch.object(evaluation_module,"report",return_value=dict(chains=[],rent_refund_groups=[inside,carry,late])):
        result=evaluation_module.evaluate(profile,100,200,profile/"rejects.jsonl")
    assert result["rent_refund_groups"]==[inside]
print("Refund groups exclude carry-in roots and refunds after the evaluation window")

# Fixed mode horizons use the first terminal observation, not later outcomes.
import dlmm_shadow as shadow_module
pulse_entry=dict(entry,mode="pulse")
terminal=dict(end,ts=1801)
later=dict(end,ts=2001,price=999)
horizon=bin_replay(pulse_entry,[end,terminal,later])
assert horizon["horizon_complete"] and horizon["observed_until_ts"]==1801
assert horizon["schemes"]==bin_replay(pulse_entry,[end,terminal])["schemes"]
assert not bin_replay(pulse_entry,[end])["horizon_complete"]
assert bin_replay(pulse_entry,[dict(end,ts=2402)])["status"]=="unmeasured"
with tempfile.TemporaryDirectory() as directory:
    profile=Path(directory);memory=profile/"memories";(memory/"dlmm_entries").mkdir(parents=True)
    # At t=10000, pulse is inside terminal grace; turnover is expired, while
    # multiday still needs observations. No RPC/subprocess for expired entries.
    for pos,mode,started in [("pulse","pulse",8100),("expired","turnover",5000),("long","multiday",5000)]:
        e=dict(entry,position=pos,pool=pos,mode=mode,bin_snapshot=dict(entry["bin_snapshot"],ts=started))
        (memory/"dlmm_entries"/(pos+".json")).write_text(json.dumps(e))
    with patch.object(shadow_module.time,"time",return_value=10000), \
         patch.object(shadow_module.subprocess,"check_output",return_value=json.dumps(dict(end,ts=10000)).encode()) as fetch:
        result=shadow_module.collect(profile,profile/"rejects.jsonl")
        assert result["bin_snapshots_attempted"]==2
        assert {call.args[0][3] for call in fetch.call_args_list}=={"pulse","long"}
    with patch.object(shadow_module.time,"time",return_value=10300), \
         patch.object(shadow_module.subprocess,"check_output",return_value=json.dumps(dict(end,ts=10300)).encode()) as fetch:
        result=shadow_module.collect(profile,profile/"rejects.jsonl")
        assert result["bin_snapshots_attempted"]==1 and fetch.call_args.args[0][3]=="long"
print("Mode-bounded bin collection and explicit partial-horizon replay passed")

# Execution comparisons undo locked/refunded rent and fees exactly once; they
# must not silently classify missing, failed or late evidence as zero slippage.
from dlmm_evaluate import swap_execution
quote = dict(input_mint="TOKEN", output_mint="So11111111111111111111111111111111111111112",
             in_amount="10", out_amount="1000", minimum_out_amount="990",
             authorized_slippage_bps=100, observed_at=100)
event = dict(kind="swap", signature="ok", position="position", ts=101, swap_quote=quote)
fact = dict(observed_at=110, failed=False, basis="finalized_transaction_balances",
            wallet_delta_lamports=795, fee_lamports=5, token_deltas_raw={"TOKEN":"-10"},
            token_rent_evidence=dict(version=1, funded=[dict(lamports=300)], refunded=[dict(lamports=100)]))
failed = dict(event, signature="failed", swap_quote=dict(quote, authorized_slippage_bps=300))
missing = dict(event, signature="missing")
late = dict(event, signature="late")
result = swap_execution([event, event, failed, missing, late, dict(event, ts=201)],
                        {"ok":fact, "failed":dict(fact, failed=True), "late":dict(fact, observed_at=201)}, 100, 200)
assert len(result['attempts']) == 4
assert result['attempts'][0]['actual_gross_lamports'] == 1000
assert result['by_slippage_bps']['100']['pending'] == 2
assert result['by_slippage_bps']['300']['failed'] == 1
assert result['by_slippage_bps']['300']['known_network_fee_lamports'] == 5
assert result['by_slippage_bps']['100']['measured_shortfall_lamports'] == 0
for bad in [dict(fact, token_rent_evidence={}), dict(fact, token_deltas_raw={"TOKEN":"-9"}),
            dict(fact, fee_lamports=float('nan')), dict(fact, wallet_delta_lamports=True)]:
    assert swap_execution([event], {"ok":bad}, 100, 200)['attempts'][0]['status'] == 'unmeasured'
for bad in [dict(quote, out_amount="NaN"), dict(quote, minimum_out_amount="1001"),
            dict(quote, observed_at=102), dict(quote, output_mint="OTHER")]:
    assert swap_execution([dict(event, swap_quote=bad)], {"ok":fact}, 100, 200)['attempts'][0]['status'] == 'unmeasured'
# A mixed close's unknown rent must not look like a favorable fill. Exact proven
# refunds can still be deducted; root cash keeps the actual full wallet delta.
for rent in [dict(version=1, funded=[], refunded=[], refunds_unmeasured=True),
             dict(version=1, funded=[], refunded=[])]:
    combined = dict(event, swap_quote=dict(quote, token_rent_close_included=True))
    r = swap_execution([combined], {'ok':dict(fact, wallet_delta_lamports=1486220,
                        token_rent_evidence=rent)}, 100, 200)
    assert r['attempts'][0]['reason'] == 'token_rent_refund_unmeasured'
    assert r['by_slippage_bps']['100']['measured'] == 0
    assert r['by_slippage_bps']['100']['known_network_fee_lamports'] == 5
    assert 'actual_gross_lamports' not in r['attempts'][0]
    if rent.get('refunds_unmeasured'):
        assert swap_execution([event], {'ok':dict(fact, token_rent_evidence=rent)}, 100, 200)['attempts'][0]['status'] == 'unmeasured'
proven = dict(event, swap_quote=dict(quote, token_rent_close_included=True))
assert swap_execution([proven], {'ok':fact}, 100, 200)['attempts'][0]['actual_gross_lamports'] == 1000
improved = swap_execution([event], {"ok":dict(fact, wallet_delta_lamports=805)}, 100, 200)
assert improved['attempts'][0]['shortfall_lamports'] == -10
expired = dict(observed_at=110, landed=False, classification='expired_unlanded',
               basis='finalized_wallet_history_and_expiry')
result = swap_execution([event], {'ok':expired}, 100, 200)
assert result['by_slippage_bps']['100']['expired_unlanded'] == 1
assert result['by_slippage_bps']['100']['pending'] == 0
assert 'actual_gross_lamports' not in result['attempts'][0]
assert 'network_fee_lamports' not in result['attempts'][0]
for unproven in [dict(expired, observed_at=201), dict(expired, basis='unknown'),
                 dict(expired, classification='unknown')]:
    assert swap_execution([event], {'ok':unproven}, 100, 200)['attempts'][0]['status'] == 'pending'
print("Swap quote/fill evaluation preserves rent, failed fees, cutoff and unknown evidence")

# Sell-quote observations must not promote missing costs or malformed inventory
# to net profit; HTTP work stays bounded even when data is unavailable.
from copy import deepcopy
from dlmm_shadow import liquidation_observation, collect_liquidation
sol = 'So11111111111111111111111111111111111111112'
liquid_entry = dict(position='p', pool='pool', base_mint='TOKEN', mode='turnover',
                   bin_snapshot=dict(ts=9900, sol_is_x=False, decimals_x=6))
inventory = dict(balanceTokenX=dict(amount='10'), unclaimedFeeTokenX=dict(amount='0'),
                 balanceTokenY=dict(amount='0.09'), unclaimedFeeTokenY=dict(amount='0.001'),
                 unclaimedRewardTokenX=dict(amount='0'), unclaimedRewardTokenY=dict(amount='0'))
position = dict(positionAddress='p', isClosed=False, updatedAt=9990, pnlSol='0.002',
                allTimeDeposits=dict(total=dict(sol='0.1')),
                allTimeWithdrawals=dict(total=dict(sol='0')),
                allTimeFees=dict(total=dict(sol='0')), unrealizedPnl=inventory)
api = dict(tokenX='TOKEN', tokenY=sol, positions=[position])
quote = dict(inputMint='TOKEN', outputMint=sol, inAmount='10000000', outAmount='8000000',
             otherAmountThreshold='7920000', swapMode='ExactIn', slippageBps=100)
with patch.object(shadow_module.time, 'time', return_value=10000):
    from unittest.mock import Mock
    fetch = Mock(side_effect=[api, quote])
    observed = liquidation_observation(liquid_entry, 'wallet', fetch)
    assert observed['lp_mark_pnl_sol'] > 0
    assert observed['quoted_assets_change_before_network_fees_sol'] == -0.001
    assert observed['minimum_quoted_assets_change_before_network_fees_sol'] == -0.00108
    assert fetch.call_count == 2 and 'not_net_cash' in observed['basis']
    zero = deepcopy(api); zero['positions'][0]['unrealizedPnl']['balanceTokenX']['amount'] = '0'
    fetch = Mock(return_value=zero)
    assert liquidation_observation(liquid_entry, 'wallet', fetch)['quote'] is None
    assert fetch.call_count == 1
    for field, value in [('updatedAt', 9819), ('updatedAt', 10006), ('isClosed', True), ('pnlSol', 'NaN')]:
        bad = deepcopy(api); bad['positions'][0][field] = value
        fetch = Mock(return_value=bad)
        try: liquidation_observation(liquid_entry, 'wallet', fetch)
        except (ValueError, ArithmeticError): pass
        else: raise AssertionError(field)
        assert fetch.call_count == 1
    for key in ['balanceTokenX', 'unclaimedFeeTokenY', 'unclaimedRewardTokenX']:
        bad = deepcopy(api); bad['positions'][0]['unrealizedPnl'][key]['amount'] = '-1'
        try: liquidation_observation(liquid_entry, 'wallet', Mock(return_value=bad))
        except ValueError: pass
        else: raise AssertionError(key)
    for key, value in [('inputMint', 'OTHER'), ('inAmount', '9'), ('outAmount', 'NaN'),
                       ('otherAmountThreshold', '8000001'), ('slippageBps', True), ('swapMode', 'ExactOut')]:
        try: liquidation_observation(liquid_entry, 'wallet', Mock(side_effect=[api, dict(quote, **{key:value})]))
        except ValueError: pass
        else: raise AssertionError(key)
# Native quotes use exact transfer-adjusted withdrawal amounts, without reading
# indexed inventory. Expiry during the quote cannot become a risk observation.
native_mark = dict(success=True, source='onchain_sol_inventory', position='p', pool='pool',
    pnl_currency='SOL', observed_at=10000, pnl_pct=1, pnl_sol=.001,
    unclaimed_fees_sol=.002, deposit_lamports='100000000', value_lamports_upper='101000000',
    active_bin=0, lower_bin=-1, upper_bin=1, in_range=True, funding_signature='funding',
    inventory=dict(version=1, wallet='wallet', token_x_mint='TOKEN', token_y_mint=sol,
        net_x_raw='9000000', net_y_raw='90000000', net_fee_x_raw='1000000', net_fee_y_raw='1000000'))
with patch.object(shadow_module.time, 'time', return_value=10000):
    fetch = Mock(return_value=quote)
    observed = liquidation_observation(liquid_entry, 'wallet', fetch, native_mark=native_mark)
    assert fetch.call_count == 1 and 'api.jup.ag' in fetch.call_args.args[0]
    assert observed['inventory_source'] == 'onchain_sol_inventory'
    assert observed['lp_mark_basis'] == 'native_active_bin_spot'
    assert observed['token_sell_raw'] == '10000000'
    assert observed['native_lp_assets_including_fees_sol'] == .091
    assert observed['quoted_assets_change_before_network_fees_sol'] == -.001
    assert observed['native_inventory'] == native_mark['inventory']
    for mutate in (
        lambda m:m.update(observed_at=9969), lambda m:m.update(position='other'),
        lambda m:m.update(pool='other'), lambda m:m.update(funding_signature=''),
        lambda m:m.update(inventory=None), lambda m:m['inventory'].update(wallet='other'),
        lambda m:m['inventory'].update(token_y_mint='OTHER'),
        lambda m:m['inventory'].update(net_x_raw=True),
        lambda m:m['inventory'].update(net_fee_x_raw='-1'),
        lambda m:m['inventory'].update(net_x_raw=str(2**64)),
        lambda m:m['inventory'].update(net_x_raw=str(2**64-1)),
    ):
        bad=deepcopy(native_mark);mutate(bad);fetch=Mock()
        try:liquidation_observation(liquid_entry,'wallet',fetch,native_mark=bad)
        except ValueError:pass
        else:raise AssertionError('invalid native inventory accepted')
        assert not fetch.called
    from dlmm_shadow import read_native_risk_mark
    with patch.object(shadow_module.subprocess, 'check_output', return_value=json.dumps(native_mark).encode()) as probe:
        assert read_native_risk_mark(Path('/profile'), liquid_entry, 'wallet', shadow_module.time.monotonic()+20) == native_mark
        assert probe.call_count == 1 and probe.call_args.args[0][-3:] == ['pnl-onchain','pool','p']
        assert 0 < probe.call_args.kwargs['timeout'] <= 3
    for output in (b'bad json', b'{}', json.dumps(dict(native_mark,inventory=None)).encode()):
        with patch.object(shadow_module.subprocess, 'check_output', return_value=output):
            assert read_native_risk_mark(Path('/profile'),liquid_entry,'wallet',shadow_module.time.monotonic()+20) is None
    with patch.object(shadow_module.subprocess, 'check_output', side_effect=shadow_module.subprocess.TimeoutExpired('read',3)):
        assert read_native_risk_mark(Path('/profile'),liquid_entry,'wallet',shadow_module.time.monotonic()+20) is None
with patch.object(shadow_module.time, 'time', side_effect=[10000,10031]):
    try:liquidation_observation(liquid_entry,'wallet',Mock(return_value=quote),native_mark=native_mark)
    except ValueError:pass
    else:raise AssertionError('expired native inventory accepted after quote')
print('Native liquidation quotes preserve exact inventory, provenance, freshness and bounded fallback')

with tempfile.TemporaryDirectory() as directory:
    profile = Path(directory); memory = profile/'memories'; (memory/'dlmm_entries').mkdir(parents=True)
    for ident in ['p', 'q', 'closed']:
        (memory/'dlmm_entries'/f'{ident}.json').write_text(json.dumps(dict(liquid_entry, position=ident)))
    (memory/'dlmm_transactions.jsonl').write_text(''.join(json.dumps(dict(kind='deploy', position=i, wallet='wallet', signature=i, ts=9900))+'\n' for i in ['p','q','closed']))
    (memory/'dlmm_closes.jsonl').write_text(json.dumps(dict(position='closed'))+'\n')
    with patch.object(shadow_module.time, 'time', return_value=10000), \
         patch.object(shadow_module, 'read_native_risk_mark', return_value=None), \
         patch.object(shadow_module, 'liquidation_observation', side_effect=TimeoutError) as observe:
        assert collect_liquidation(profile) == 1 and observe.call_count == 1
        assert collect_liquidation(profile) == 1 and observe.call_count == 2
        assert collect_liquidation(profile) == 0 and observe.call_count == 2
    samples = shadow_module.rows(memory/'dlmm_liquidation_quotes.jsonl')
    assert {x['position'] for x in samples} == {'p', 'q'}
    assert all(x['status']=='unmeasured' for x in samples)
    assert len(evaluate(profile, 9999, 10000, profile/'rejects.jsonl')['liquidation_observations']) == 2
    assert not evaluate(profile, 9999, 9999, profile/'rejects.jsonl')['liquidation_observations']
print('Liquidation quotes preserve inventory, cost limits, unknown evidence and bounded collection')

# API float noise is break-even, and an empty position is not a carry-in trade.
from dlmm_evaluate import lp_cohort, compare_lp
lp = dict(positionAddress='win', createdAt=100, closedAt=150, pnlSol='0.001',
          allTimeDeposits=dict(total=dict(sol='0.1')))
records = [lp, lp, dict(lp, positionAddress='noise', pnlSol='2.7755575615628914e-17'),
           dict(lp, positionAddress='loss', pnlSol='-0.001'),
           dict(lp, positionAddress='one-lamport', pnlSol='0.000000001'),
           dict(lp, positionAddress='carry', createdAt=99),
           dict(lp, positionAddress='empty', allTimeDeposits=dict(total=dict(sol='0'))),
           dict(lp, positionAddress='future', closedAt=200)]
cohort = lp_cohort(records, 100, 200)
assert cohort['full_life_positions'] == 4 and cohort['carry_in_closes'] == 1
assert cohort['zero_deposit_closes'] == 1
assert (cohort['wins'], cohort['losses'], cohort['breakeven_positions']) == (2, 1, 1)
assert abs(cohort['lp_pnl_sol'] - 1e-9) < 1e-15
with patch.object(evaluation_module, 'fetch_pools', return_value=[dict(poolAddress='pool', lastClosedAt=150)]), \
     patch.object(evaluation_module, 'fetch_closed_positions', return_value=records):
    assert compare_lp({'azimuth':'wallet'}, 100, 200)['azimuth'] == cohort
    for bad in [dict(lp, pnlSol='NaN'), dict(lp, pnlSol=True), dict(lp, createdAt=151),
                dict(lp, allTimeDeposits=dict(total=dict(sol=True))),
                dict(lp, allTimeDeposits=dict(total=dict(sol='NaN'))),
                dict(lp, allTimeDeposits={})]:
        with patch.object(evaluation_module, 'fetch_closed_positions', return_value=[bad]):
            assert compare_lp({'azimuth':'wallet'}, 100, 200)['azimuth']['status'] == 'unmeasured'
print('LP cohorts exclude empty positions and float-noise wins; missing valuations stay unmeasured')

# Exercise the collector with slow providers: it must preserve time for bin/IL
# observations and resume unattempted records rather than inventing outcomes.
with tempfile.TemporaryDirectory() as directory:
    profile=Path(directory); memory=profile/'memories'; entry_dir=memory/'dlmm_entries'
    entry_dir.mkdir(parents=True)
    epoch=10000; clock=[0.0]; requests=[]; bin_calls=[]
    rejects=[dict(id=str(i),ts=epoch-1900,mode='pulse',gate='momentum',pool='pool',
                  snapshot={'pool_price':1},candidate={'base_mint':str(i),'sol_is_x':False}) for i in range(100)]
    reject_file=profile/'rejects.jsonl'
    reject_file.write_text(''.join(json.dumps(r)+'\n' for r in rejects))
    for i in range(12):
        entry=dict(position='p'+str(i),pool='pool',mode='pulse',
                   bin_snapshot=dict(ts=epoch-1800,bins=[dict(id=0)]))
        (entry_dir/(entry['position']+'.json')).write_text(json.dumps(entry))
    def slow_http(request,timeout):
        requests.append(timeout); clock[0]+=timeout
        raise OSError('provider unavailable')
    def slow_bins(command,stderr,timeout):
        bin_calls.append(timeout); clock[0]+=timeout
        raise shadow_module.subprocess.TimeoutExpired(command,timeout)
    def liquidation_probe(profile,deadline=None):
        if deadline is not None: assert deadline-clock[0]>=20
        return 1
    with patch.object(shadow_module.time,'time',side_effect=lambda:epoch+clock[0]), \
         patch.object(shadow_module.time,'monotonic',side_effect=lambda:clock[0]), \
         patch.object(shadow_module.urllib.request,'urlopen',side_effect=slow_http), \
         patch.object(shadow_module.subprocess,'check_output',side_effect=slow_bins), \
         patch.object(shadow_module,'collect_liquidation',side_effect=liquidation_probe):
        result=shadow_module.collect(profile,reject_file)
    assert clock[0]<240, (clock[0],result)
    assert result['reject_budget_exhausted'] and result['bin_budget_exhausted']
    assert result['liquidation_observations_attempted']==1
    assert 0<result['outcomes_attempted']<100 and 0<result['bin_snapshots_attempted']<12
    first_outcomes=[json.loads(line) for line in (memory/'dlmm_reject_outcomes.jsonl').read_text().splitlines()]
    assert len(first_outcomes)==len(requests)==result['outcomes_attempted']
    assert all(r['status']=='unmeasured' for r in first_outcomes)
    assert not (memory/'dlmm_bin_samples.jsonl').exists()
    class HealthyResponse:
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def read(self): return json.dumps({'data':[{'pool_address':'pool','pool_price':1.02}]}).encode()
    with patch.object(shadow_module.time,'time',side_effect=lambda:epoch+clock[0]), \
         patch.object(shadow_module.time,'monotonic',side_effect=lambda:clock[0]), \
         patch.object(shadow_module.urllib.request,'urlopen',return_value=HealthyResponse()), \
         patch.object(shadow_module.subprocess,'check_output',return_value=json.dumps({'ts':epoch+clock[0]}).encode()), \
         patch.object(shadow_module,'collect_liquidation',return_value=0):
        recovered=shadow_module.collect(profile,reject_file)
    outcomes=[json.loads(line) for line in (memory/'dlmm_reject_outcomes.jsonl').read_text().splitlines()]
    assert len(outcomes)==len({r['id'] for r in outcomes})==100
    assert recovered['outcomes_attempted']==100-len(first_outcomes)
    assert all(r['status']=='measured' for r in outcomes[len(first_outcomes):])
    assert recovered['bin_snapshots_attempted']==12
    assert len((memory/'dlmm_bin_samples.jsonl').read_text().splitlines())==12
print('Slow shadow phases retain bin/probe time and resume without fabricated or duplicate outcomes')

# Growing journals must not turn the periodic collector into an OOM victim.
# Most reject payloads are already complete; bin payloads need only timestamps.
import tracemalloc
with tempfile.TemporaryDirectory() as directory:
    profile=Path(directory);memory=profile/'memories';(memory/'dlmm_entries').mkdir(parents=True)
    reject_file=profile/'rejects.jsonl';payload='x'*(64*1024)
    with reject_file.open('w') as stream, (memory/'dlmm_bin_samples.jsonl').open('w') as bins:
        for i in range(96):
            stream.write(json.dumps(dict(id=str(i),ts=1,mode='pulse',gate='done',payload=payload))+'\n')
            bins.write(json.dumps(dict(position='old',ts=i,payload=payload))+'\n')
        pending=dict(id='pending',ts=1,mode='pulse',gate='first',payload=payload,
                     snapshot={'pool_price':1},candidate={'sol_is_x':False})
        stream.write(json.dumps(pending)+'\n')
        stream.write(json.dumps(dict(pending,gate='duplicate'))+'\n')
    (memory/'dlmm_reject_outcomes.jsonl').write_text(''.join(json.dumps({'id':str(i)})+'\n' for i in range(96)))
    tracemalloc.start()
    try:
        with patch.object(shadow_module.time,'time',return_value=10000), \
             patch.object(shadow_module.urllib.request,'urlopen') as http, \
             patch.object(shadow_module.subprocess,'check_output') as node, \
             patch.object(shadow_module,'collect_liquidation',return_value=0):
            result=shadow_module.collect(profile,reject_file)
        peak=tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()
    assert peak<2*1024*1024, peak
    assert result['rejects_total']==97 and result['outcomes_attempted']==1
    assert not http.called and not node.called
    outcomes=shadow_module.rows(memory/'dlmm_reject_outcomes.jsonl')
    assert len(outcomes)==97 and outcomes[-1]['gate']=='first' and outcomes[-1]['status']=='censored'
    with reject_file.open('w') as stream:
        for i in range(128):stream.write(json.dumps(dict(pending,id=str(i)))+'\n')
    (memory/'dlmm_reject_outcomes.jsonl').write_text('')
    tracemalloc.start()
    try:
        with patch.object(shadow_module.time,'time',return_value=10000), \
             patch.object(shadow_module,'collect_liquidation',return_value=0):
            backlog=shadow_module.collect(profile,reject_file)
        peak=tracemalloc.get_traced_memory()[1]
    finally:tracemalloc.stop()
    assert peak<2*1024*1024, peak
    assert backlog['rejects_total']==128 and backlog['outcomes_attempted']==100
    assert len(shadow_module.rows(memory/'dlmm_reject_outcomes.jsonl'))==100
    assert list(shadow_module.iter_rows(memory/'missing.jsonl'))==[]
    broken=memory/'broken.jsonl';broken.write_text('{"id":"good"}\n\ninvalid\n')
    scan=shadow_module.iter_rows(broken);assert next(scan)=={'id':'good'}
    try:next(scan);raise AssertionError('corrupt evidence was hidden')
    except json.JSONDecodeError:pass
    # A completion published while rejects are being indexed must still be
    # observed before deciding which candidates need another outcome.
    reject_file.write_text(json.dumps(dict(pending,id='racing'))+'\n')
    (memory/'dlmm_reject_outcomes.jsonl').write_text('')
    original_scan=shadow_module.iter_rows
    def concurrent_completion(file):
        yield from original_scan(file)
        if file==reject_file:
            with (memory/'dlmm_reject_outcomes.jsonl').open('a') as stream:
                stream.write(json.dumps({'id':'racing'})+'\n')
    with patch.object(shadow_module,'iter_rows',side_effect=concurrent_completion), \
         patch.object(shadow_module,'collect_liquidation',return_value=0):
        resumed=shadow_module.collect(profile,reject_file)
    assert resumed['outcomes_attempted']==0
    assert len(shadow_module.rows(memory/'dlmm_reject_outcomes.jsonl'))==1
print('Growing shadow journals stay within the memory budget; first IDs and visible corruption preserved')

# A position can finish entirely in SOL and still lose its entry composition
# cost. Reweighting its earned fees alone must not turn that cost into profit.
from copy import deepcopy
from dlmm_shadow import native_allocation_replay
allocation_entry=dict(position='position',pool='pool',strategy='sol_bidask',sol_is_x=False,
    amount_x=0,amount_y=.1,size_sol=.1,entry_bin=0,bins_below=1,bins_above=0,bin_step=100,deployed_at=45)
initial_allocation=dict(version=1,wallet='wallet',signature='funding',block_time=50,
    requested_lamports='100000000',deposit_lamports='99999999',executed_active_bin=0,max_active_bin_slippage=10,
    composition_fee_lamports='1652',protocol_fee_lamports='165',bins=[
        dict(id=-1,sol_deposit_lamports='66666666',composition_fee_lamports='0',protocol_fee_lamports='0'),
        dict(id=0,sol_deposit_lamports='33333333',composition_fee_lamports='1652',protocol_fee_lamports='165')])
allocation_observation=dict(version=1,position='position',pool='pool',source='onchain_sol_inventory',
    funding_signature='funding',observed_at=149.5,decision_at=149.6,recorded_at=151,
    lower_bin=-1,upper_bin=0,active_bin=1,deposit_lamports='99999999',value_lamports_upper='99999785',pnl_sol=-214e-9,
    bin_observation=dict(version=1,bin_step=100,sol_is_x=False,initial_funding=initial_allocation,bins=[
        dict(id=-1,liquidity_raw='100',x_raw='0',y_raw='66666666',fee_x_raw='0',fee_y_raw='0'),
        dict(id=0,liquidity_raw='200',x_raw='0',y_raw='33331681',fee_x_raw='0',fee_y_raw='1438')]))
allocation_funding=dict(signature='funding',wallet='wallet',failed=False,slot=1,block_time=50,observed_at=60)
allocation_close=dict(signature='close',wallet='wallet',failed=False,slot=2,block_time=150,
                      observed_at=160,position_account_closed=True)
def replay_allocation(e=allocation_entry,o=allocation_observation,f=allocation_funding,c=allocation_close,end=200):
    return native_allocation_replay(e,o,f,c,end_ts=end)
allocation_result=replay_allocation()
assert allocation_result['status']=='modeled'
assert allocation_result['native_baseline_reconciliation_lamports']==0
assert abs(allocation_result['schemes']['far_active']['gross_pnl_sol']+214e-9)<1e-15
assert allocation_result['actual_entry_composition_fee_sol']==1652e-9
assert allocation_result['schemes']['near_active']['fee_capture_sol']==2876e-9
assert abs(allocation_result['schemes']['near_active']['gross_pnl_sol']+428e-9)<1e-15
assert all(v['gross_pnl_sol']<0 for v in allocation_result['schemes'].values())
assert replay_allocation(o=None)['status']=='unmeasured'
legacy_observation=deepcopy(allocation_observation);del legacy_observation['bin_observation']['initial_funding']
assert replay_allocation(o=legacy_observation)['reason']=='missing_decoded_initial_bin_allocation'
for mutation in [
    lambda o:o.update(recorded_at=201),lambda o:o.update(observed_at=150.1,decision_at=150.2),
    lambda o:o.update(observed_at=119),lambda o:o.update(value_lamports_upper='99999786'),
    lambda o:o.update(pnl_sol=0),lambda o:o.update(version=True),
    lambda o:o['bin_observation']['initial_funding'].update(wallet='foreign'),
    lambda o:o['bin_observation']['initial_funding'].update(signature='other'),
    lambda o:o['bin_observation']['initial_funding'].update(deposit_lamports='100000000'),
    lambda o:o['bin_observation']['initial_funding'].update(executed_active_bin=11),
    lambda o:o['bin_observation']['initial_funding'].update(composition_fee_lamports='1817'),
    lambda o:o['bin_observation']['initial_funding']['bins'][1].update(protocol_fee_lamports='1653'),
    lambda o:o['bin_observation']['initial_funding']['bins'].reverse(),
    lambda o:o['bin_observation']['bins'][0].update(liquidity_raw='0'),
    lambda o:o['bin_observation']['bins'][0].update(y_raw=str(2**64)),
    lambda o:o['bin_observation']['bins'][0].update(fee_y_raw='-1'),
]:
    bad=deepcopy(allocation_observation);mutation(bad)
    assert replay_allocation(o=bad)['status']=='unmeasured'
for change in [dict(observed_at=201),dict(failed=True),dict(landed=False),dict(slot=True),dict(wallet='foreign')]:
    assert replay_allocation(f=dict(allocation_funding,**change))['status']=='unmeasured'
    assert replay_allocation(c=dict(allocation_close,**change))['status']=='unmeasured'
assert replay_allocation(c=dict(allocation_close,position_account_closed=False))['status']=='unmeasured'

# Execution moved down one bin: SOL never funded the old active bin. Keep that
# bin empty and compare only the actually funded support without dividing by 0.
shifted_observation=deepcopy(allocation_observation)
shifted_initial=shifted_observation['bin_observation']['initial_funding']
shifted_initial.update(executed_active_bin=-1,deposit_lamports='100000000',composition_fee_lamports='100',protocol_fee_lamports='10')
shifted_initial['bins'][0].update(sol_deposit_lamports='100000000',composition_fee_lamports='100',protocol_fee_lamports='10')
shifted_initial['bins'][1].update(sol_deposit_lamports='0',composition_fee_lamports='0',protocol_fee_lamports='0')
shifted_observation.update(deposit_lamports='100000000',value_lamports_upper='99999900',pnl_sol=-100e-9)
shifted_observation['bin_observation']['bins'][0].update(y_raw='99999900')
shifted_observation['bin_observation']['bins'][1].update(liquidity_raw='0',y_raw='0',fee_y_raw='0')
shifted_result=replay_allocation(o=shifted_observation)
assert shifted_result['status']=='modeled' and shifted_result['funded_bins']==1 and shifted_result['position_bins']==2
assert shifted_result['schemes']['near_active']['paired_gross_delta_sol']==0

# Verify the actual scheduled evaluator joins the funding/close facts and
# obeys journal recording time, rather than testing only the pure helper.
import dlmm_evaluate as native_evaluation
with tempfile.TemporaryDirectory() as directory:
    profile=Path(directory);memory=profile/'memories';(memory/'dlmm_entries').mkdir(parents=True)
    (memory/'dlmm_entries/position.json').write_text(json.dumps(allocation_entry))
    (memory/'dlmm_closes.jsonl').write_text(json.dumps(dict(position='position',ts=155,dry_run=False))+'\n')
    events=[dict(kind='deploy',position='position',signature='funding',wallet='wallet',ts=50),
            dict(kind='close',position='position',signature='close',wallet='wallet',ts=155)]
    (memory/'dlmm_transactions.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events))
    (memory/'dlmm_wallet_transactions.jsonl').write_text(''.join(json.dumps(f)+'\n' for f in [allocation_funding,allocation_close]))
    journal=memory/'dlmm_close_bin_observations.jsonl';journal.write_text(json.dumps(allocation_observation)+'\n')
    with patch.object(native_evaluation,'report',return_value={'chains':[],'rent_refund_groups':[]}):
        measured=native_evaluation.evaluate(profile,1,200,profile/'rejects.jsonl')['native_bin_replay']
        assert len(measured)==1 and measured[0]['status']=='modeled'
        journal.write_text(json.dumps(dict(allocation_observation,recorded_at=201))+'\n')
        assert native_evaluation.evaluate(profile,1,200,profile/'rejects.jsonl')['native_bin_replay'][0]['status']=='unmeasured'
        journal.write_text(json.dumps(allocation_observation)+'\n')
        (memory/'dlmm_wallet_transactions.jsonl').write_text(''.join(json.dumps(f)+'\n' for f in [allocation_funding,dict(allocation_close,failed=True)]))
        assert native_evaluation.evaluate(profile,1,200,profile/'rejects.jsonl')['native_bin_replay'][0]['status']=='unmeasured'
print('Native bin replay preserves composition cost, executed support and finalized observation cutoffs')

# Evaluate a small window in large unrelated journals. Indexing preserves file
# order/duplicates and the evaluator's original timestamp and first-reject rules.
import tracemalloc
from dlmm_evaluate import index_bin_samples, read_bin_samples
with tempfile.TemporaryDirectory() as directory:
    profile=Path(directory);memory=profile/'memories';(memory/'dlmm_entries').mkdir(parents=True)
    initial_bin=dict(id=0,x='0',y='1000000000',supply=str(1000000000*2**64),fee_x='0',fee_y='0',price=1)
    e=dict(position='position',mode='pulse',deployed_at=100,size_sol=.1,amount_x=0,amount_y=.1,
        bin_snapshot=dict(ts=100,active_bin=0,price=1,decimals_x=9,decimals_y=9,sol_is_x=False,bins=[initial_bin]))
    (memory/'dlmm_entries/position.json').write_text(json.dumps(e))
    samples=[dict(position='position',ts=ts,price=1,active_bin=0,
                  bins=[dict(initial_bin,fee_y=str((i+1)*2**64//100))])
             for i,ts in enumerate([101,101,2000,2100,3000])]
    file=memory/'dlmm_bin_samples.jsonl';rejects=profile/'rejects.jsonl'
    with file.open('w') as output, rejects.open('w') as rejected:
        for i in range(96):
            output.write(json.dumps(dict(position='unrelated',ts=1,padding='x'*65536))+'\n')
            rejected.write(json.dumps(dict(id=str(i),ts=1,padding='x'*65536))+'\n')
            rejected.write(json.dumps(dict(id='selected'+str(i),ts=150,mode='pulse',gate='memory',padding='x'*65536))+'\n')
        for sample in samples:output.write(json.dumps(sample)+'\n')
        for gate in ['first','duplicate']:
            rejected.write(json.dumps(dict(id='kept',ts=150,mode='pulse',gate=gate))+'\n')
    with patch.object(native_evaluation,'report',return_value={'chains':[],'rent_refund_groups':[]}):
        tracemalloc.start()
        evaluated=native_evaluation.evaluate(profile,100,2100,rejects)
        _,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
    assert peak<2*1024**2,peak
    assert evaluated['bin_replay'][0]['schemes']==bin_replay(e,samples[:-1])['schemes']
    assert set(evaluated['rejected_candidates'])=={'pulse/first','pulse/memory'}
    assert evaluated['rejected_candidates']['pulse/memory']['total']==96
    indexed=index_bin_samples(file,{'position'},2100)
    assert read_bin_samples(file,indexed['position'])==samples[:-1]
    with file.open('a') as output:output.write(json.dumps(dict(samples[0],ts=200))+'\n')
    assert read_bin_samples(file,indexed['position'])==samples[:-1]
    file.write_bytes(file.read_bytes().replace(b'"ts": 101',b'"ts": 102',1))
    try: read_bin_samples(file,indexed['position'])
    except ValueError: pass
    else: raise AssertionError('Changed indexed evidence must fail')
    with file.open('a') as output:output.write('{broken-json}\n')
    for positions in [set(),{'position'}]:
        try: index_bin_samples(file,positions,2100)
        except json.JSONDecodeError: pass
        else: raise AssertionError('Corrupt unrelated samples must remain visible')
    assert index_bin_samples(profile/'missing',{'position'},2100)=={'position':[]}
print('Evaluator bounds journal memory, preserves replay/reject semantics and detects changed indexed evidence')

# Candidate reads share the shadow timer, stay bounded, and never become yield
# labels. In particular, a sample fetched after entry cannot backfill history.
from copy import deepcopy
from dlmm_shadow import index_candidate, collect_candidate_bins, validate_candidate_snapshot, pre_entry_bin_coverage
candidate_mint='EkFRff9a2jKztJHML1LG9FRmEkPJDR6XAYp3uCPdpump'
candidate_pool='CqJVXBTY644ZBtPCkbaqV7Nu8Qzau2A4sChtpkvQQLLi'
def candidate_sample(pool=candidate_pool,stamp=10000):
    return dict(status='observed',pool=pool,ts=stamp,active_bin=0,anchor_bin=0,
        lower_bin=-69,upper_bin=16,decimals_x=6,decimals_y=9,sol_is_x=False,price=.001,
        token_x_mint=candidate_mint,token_y_mint=shadow_module.SOL_MINT,
        bins=[dict(id=i,x='0',y='1000000',supply=str(1000000*2**64),fee_x='0',fee_y='0',price=.001)
              for i in range(-69,17)])
def candidate_source(pool=candidate_pool,stamp=10000,ident='source'):
    return dict(id=ident,ts=stamp,pool=pool,mode='pulse',
                candidate=dict(base_mint=candidate_mint,sol_is_x=False,padding='discarded'))
candidates={}
for i in range(80):
    index_candidate(candidates,candidate_source('1'*30+str(i//9+1)+str(i%9+1),10000+i,str(i)),10100)
assert len(candidates)==64
assert min(c['source_ts'] for c in candidates.values())==10016
assert all(set(c)=={'pool','base_mint','mode','source_id','source_ts'} for c in candidates.values())
selected_pool=next(iter(candidates)); original=candidates[selected_pool]
index_candidate(candidates,candidate_source(selected_pool,9999,'older'),10100)
assert candidates[selected_pool]==original
for bad in [dict(candidate_source(),ts=10101),dict(candidate_source(),ts=8299),
            dict(candidate_source(),pool='invalid'),dict(candidate_source(),mode='unknown'),
            dict(candidate_source(),candidate=dict(base_mint=candidate_mint,sol_is_x=True))]:
    empty={};index_candidate(empty,bad,10100);assert empty=={}
validate_candidate_snapshot(candidate_sample(),candidate_pool,candidate_mint)
for change in [dict(pool='other'),dict(token_x_mint='other'),dict(token_y_mint='other'),
               dict(sol_is_x=True),dict(decimals_x=True),dict(decimals_y=6),dict(price=float('nan')),
               dict(anchor_bin=1),dict(upper_bin=17),dict(bins=candidate_sample()['bins'][:-1])]:
    bad=dict(candidate_sample(),**change)
    try: validate_candidate_snapshot(bad,candidate_pool,candidate_mint)
    except ValueError: pass
    else: raise AssertionError(change)
for field,value in [('x',str(2**64)),('fee_y',str(2**128)),('supply','-1'),('id',0),('price',0)]:
    bad=candidate_sample();bad['bins'][0][field]=value
    try: validate_candidate_snapshot(bad,candidate_pool,candidate_mint)
    except ValueError: pass
    else: raise AssertionError((field,value))

with tempfile.TemporaryDirectory() as directory:
    profile=Path(directory);clock=[0.0];epoch=10000;small={}
    for i in range(5):index_candidate(small,candidate_source('1'*31+str(i+1)),epoch)
    calls=[]
    def candidate_fetch(command,stderr,timeout):
        assert command[2]=='candidate-bin-snapshot' and command[-2:]==['69','16']
        assert 0<timeout<=3
        calls.append(command[3]);clock[0]+=timeout
        return json.dumps(candidate_sample(command[3],int(epoch+clock[0]))).encode()
    journal=profile/'memories/dlmm_candidate_bin_samples.jsonl'
    with patch.object(shadow_module.time,'time',side_effect=lambda:epoch+clock[0]), \
         patch.object(shadow_module.time,'monotonic',side_effect=lambda:clock[0]), \
         patch.object(shadow_module.subprocess,'check_output',side_effect=candidate_fetch):
        observed=collect_candidate_bins(profile,small,40)
        assert observed['candidate_bin_snapshots_attempted']==observed['candidate_bin_snapshots_observed']==3
        assert clock[0]==9 and 40-clock[0]>=20
        observed=collect_candidate_bins(profile,small,50)
        assert observed['candidate_bin_snapshots_observed']==2 and len(set(calls))==5
        assert collect_candidate_bins(profile,small,60)['candidate_bin_snapshots_attempted']==0
        stored=shadow_module.rows(journal)
        assert len(stored)==5 and all(s['source_id']=='source' and s['source_ts']==10000 for s in stored)
        assert all(s['request_started_at']<=s['ts']<=s['collected_at'] for s in stored)
        # No scan or subprocess when the liquidation reserve consumes all slack.
        with patch.object(shadow_module,'iter_rows',side_effect=AssertionError('No time to scan')):
            assert collect_candidate_bins(profile,small,clock[0]+20)['candidate_bin_budget_exhausted']
    journal.unlink();clock[0]=0
    with patch.object(shadow_module.time,'time',return_value=epoch), \
         patch.object(shadow_module.time,'monotonic',return_value=0), \
         patch.object(shadow_module.subprocess,'check_output',return_value=b'{"status":"deferred","reason":"wallet_trade_active"}') as fetch:
        deferred=collect_candidate_bins(profile,small,40)
        assert deferred['candidate_bin_trading_deferred'] and fetch.call_count==1
        assert not journal.exists()
    with patch.object(shadow_module.time,'time',side_effect=lambda:epoch+clock[0]), \
         patch.object(shadow_module.time,'monotonic',side_effect=lambda:clock[0]), \
         patch.object(shadow_module.subprocess,'check_output',side_effect=lambda *a,**kw: (_ for _ in ()).throw(OSError('https://secret.invalid'))):
        failed=collect_candidate_bins(profile,small,40)
        assert failed['candidate_bin_snapshots_attempted']==3 and failed['candidate_bin_snapshots_observed']==0
        assert all(s['reason']=='OSError' and 'bins' not in s for s in shadow_module.rows(journal))
        assert 'secret' not in journal.read_text()
    journal.unlink()
    # Exercise the actual collector source wiring without doing any live reads.
    rejects=profile/'rejects.jsonl';rejects.write_text(json.dumps(candidate_source())+'\n')
    with patch.object(shadow_module.time,'time',return_value=epoch), \
         patch.object(shadow_module.time,'monotonic',return_value=0), \
         patch.object(shadow_module.subprocess,'check_output',return_value=json.dumps(candidate_sample()).encode()), \
         patch.object(shadow_module,'collect_liquidation',return_value=0):
        assert shadow_module.collect(profile,rejects)['candidate_bin_snapshots_observed']==1

with tempfile.TemporaryDirectory() as directory:
    profile=Path(directory);memory=profile/'memories';(memory/'dlmm_entries').mkdir(parents=True)
    initial=candidate_sample(stamp=10000)
    initial['bins']=[dict(b,fee_y='100') for b in initial['bins'] if -44<=b['id']<=0]
    e=dict(position='entry',pool=candidate_pool,base_mint=candidate_mint,mode='pulse',
           deployed_at=10001,bin_snapshot=initial)
    file=memory/'dlmm_candidate_bin_samples.jsonl'
    before=dict(candidate_sample(stamp=8500),collected_at=8501,source_id='earliest')
    closer=dict(candidate_sample(stamp=9000),collected_at=9001,source_id='closer')
    after=dict(candidate_sample(stamp=8400),collected_at=10001,source_id='after-entry')
    outside=dict(candidate_sample(stamp=8000),collected_at=8001,source_id='too-old')
    too_near=dict(candidate_sample(stamp=9800),collected_at=9801,source_id='too-near')
    file.write_text(''.join(json.dumps(s)+'\n' for s in [closer,after,outside,too_near,before]))
    coverage=pre_entry_bin_coverage([e],file,11000)[0]
    assert coverage['status']=='observed' and coverage['span_seconds']==1500
    assert coverage['covered_entry_bins']==45 and coverage['prior_snapshot']['source_id']=='earliest'
    assert len(coverage['prior_sha256'])==64 and 'profit' not in coverage
    assert pre_entry_bin_coverage([e],file,10000)[0]['status']=='unmeasured'
    for bad in [dict(before,collected_at=10001),dict(before,collected_at=8499),dict(before,token_x_mint='other'),
                dict(before,decimals_x=9),dict(before,lower_bin=-43,bins=before['bins'][26:]),
                dict(before,bins=[dict(b,fee_y='101') for b in before['bins']])]:
        file.write_text(json.dumps(bad)+'\n')
        assert pre_entry_bin_coverage([e],file,11000)[0]['status']=='unmeasured'
    # Unrelated growing payloads are streamed, not retained alongside each entry.
    with file.open('w') as out:
        for i in range(96):out.write(json.dumps(dict(pool='unrelated',padding='x'*65536))+'\n')
        out.write(json.dumps(before)+'\n')
    tracemalloc.start();coverage=pre_entry_bin_coverage([e],file,11000)
    _,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
    assert peak<2*1024**2 and coverage[0]['status']=='observed',peak
    (memory/'dlmm_entries/entry.json').write_text(json.dumps(e))
    with patch.object(native_evaluation,'report',return_value={'chains':[],'rent_refund_groups':[]}):
        assert native_evaluation.evaluate(profile,10000,11000,profile/'rejects')['pre_entry_bin_history']==coverage
    file.write_text('{broken-json}\n')
    try:pre_entry_bin_coverage([e],file,11000)
    except json.JSONDecodeError:pass
    else:raise AssertionError('Candidate history corruption must remain visible')
print('Pre-entry candidate history: bounded reads, trading priority, fair rotation and no future backfill')

# The optional account archive cannot extend a phase or discard the quote.
from dlmm_shadow import archive_exit_bank
archive_sample = dict(status='measured', inventory_source='onchain_sol_inventory',
                      quote={'inAmount':'1'}, token_sell_raw='1')
with patch.object(shadow_module.time, 'monotonic', return_value=100), \
     patch.object(shadow_module.subprocess, 'run') as child:
    assert archive_exit_bank(Path('/profile'), dict(archive_sample,token_sell_raw='0'),120) is None
    assert archive_exit_bank(Path('/profile'), dict(archive_sample,inventory_source='indexed_position'),120) is None
    assert archive_exit_bank(Path('/profile'), archive_sample,103)['reason']=='exit_bank_budget'
    child.assert_not_called()
    child.return_value = type('Result',(),{'stdout':'{"status":"archived","snapshot_slot":123}'})()
    assert archive_exit_bank(Path('/profile'),archive_sample,110)['status']=='archived'
    assert child.call_args.kwargs['timeout']==10
    assert json.loads(child.call_args.kwargs['input'])['budget_ms']==10000
    child.side_effect = shadow_module.subprocess.TimeoutExpired('node',10)
    assert archive_exit_bank(Path('/profile'),archive_sample,110)['reason']=='exit_bank_unavailable'
print('Optional exit bank archive preserves source restrictions and the enclosing deadline')
