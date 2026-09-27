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
 assert result['wealth_change'] is None
 assert result['unvalued_external_token_inflows']==['gift']
 assert result['accounting']['flow_adjusted_wealth_change_sol'] is None
 cash=assessment(dict(fact,classification='external_transfer',external_flow_lamports=500000000))
 assert cash['wealth_change']['flow_adjusted_change_sol']==0
 assert cash['accounting']['flow_adjusted_wealth_change_sol']==0
 assert assessment(dict(fact,slot=9))['wealth_change']['flow_adjusted_change_sol']==0.5
 assert assessment(dict(fact,slot=None))['wealth_change'] is None
print('Evaluation excludes unvalued gifts and subtracts known external cash flows')
