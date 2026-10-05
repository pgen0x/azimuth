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
improved = swap_execution([event], {"ok":dict(fact, wallet_delta_lamports=805)}, 100, 200)
assert improved['attempts'][0]['shortfall_lamports'] == -10
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
with tempfile.TemporaryDirectory() as directory:
    profile = Path(directory); memory = profile/'memories'; (memory/'dlmm_entries').mkdir(parents=True)
    for ident in ['p', 'q', 'closed']:
        (memory/'dlmm_entries'/f'{ident}.json').write_text(json.dumps(dict(liquid_entry, position=ident)))
    (memory/'dlmm_transactions.jsonl').write_text(''.join(json.dumps(dict(kind='deploy', position=i, wallet='wallet', signature=i, ts=9900))+'\n' for i in ['p','q','closed']))
    (memory/'dlmm_closes.jsonl').write_text(json.dumps(dict(position='closed'))+'\n')
    with patch.object(shadow_module.time, 'time', return_value=10000), \
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
