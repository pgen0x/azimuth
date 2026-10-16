#!/usr/bin/env python3
"""Offline: python3 assets/skill/scripts/test_dlmm_accounting.py"""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from dlmm_accounting import report, cleanup_owner, settlement_inventory

with TemporaryDirectory() as root:
    memories = Path(root) / "memories"
    (memories / "dlmm_entries").mkdir(parents=True)
    def write(name, records):
        (memories / name).write_text("".join(json.dumps(r) + "\n" for r in records))
    (memories / "dlmm_entries/child.json").write_text(json.dumps(
        dict(position="child", root_chain_id="root", parent_position="root")))
    write("dlmm_closes.jsonl", [dict(position="root"), dict(position="root"),
                               dict(position="child", recenter_of="root")])
    write("dlmm_realized.jsonl", [dict(position="root", realized_sol=0.01),
                                 dict(position="child", realized_sol=-0.02)])
    event = dict(signature="a", position="root", root_chain_id="root", wallet="wallet")
    write("dlmm_transactions.jsonl", [event, event,
        dict(signature="b", position="child", root_chain_id="root", wallet="wallet"),
        dict(signature="c", position="child", root_chain_id="root", wallet="wallet"),
        dict(signature="pending", position="child", root_chain_id="root", wallet="wallet")])
    write("dlmm_transaction_facts.jsonl", [
        dict(signature="a", wallet="wallet", wallet_delta_lamports=-100000000,
             fee_lamports=5000, failed=False, token_deltas_raw={"TOKEN": "9007199254740993"}),
        dict(signature="b", wallet="wallet", wallet_delta_lamports=90000000,
             fee_lamports=6000, failed=False, token_deltas_raw={}),
        dict(signature="c", wallet="wallet", wallet_delta_lamports=-7000,
             fee_lamports=7000, failed=True, token_deltas_raw={})])
    historical = report(root, 100)
    assert historical["chains"][0]["wallet_delta_lamports"] is None  # undated facts are not historical evidence
    result = report(root)
    assert result["nav_sol"] is None
    c, = result["chains"]
    assert c["positions"] == ["child", "root"]
    assert c["lp_pnl_sol"] == -0.01
    assert c["wallet_delta_lamports"] == -10007000  # fees already inside wallet delta
    assert c["network_fee_lamports"] == 18000  # failed transactions still cost fees
    assert c["pending_signatures"] == ["pending"]
    assert c["token_deltas_raw"]["TOKEN"] == "9007199254740993"
    assert c["net_pnl_sol"] is None
    assert c["accounting_status"] == "incomplete"
    write("dlmm_wallet_transactions.jsonl", [dict(signature="pending",wallet="wallet",landed=False,classification="expired_unlanded")])
    assert report(root)["chains"][0]["pending_signatures"] == []
    assert report(root)["chains"][0]["wallet_delta_lamports"] == -10007000
    assert report(root)["chains"][0]["expired_unlanded_signatures"] == ["pending"]
    write("dlmm_wallet_transactions.jsonl", [])
    write("dlmm_transaction_facts.jsonl", [])
    assert len(report(root)["chains"][0]["pending_signatures"]) == 4
    assert report(root)["chains"][0]["wallet_delta_lamports"] is None
    write("dlmm_transactions.jsonl", [event, dict(event, position="other")])
    try:
        report(root)
    except ValueError:
        pass
    else:
        raise AssertionError("conflicting attribution accepted")
print("Root-chain cash flows, deduplication, missing data and fee accounting passed")

with TemporaryDirectory() as root:
    memories = Path(root) / "memories"
    (memories / "dlmm_entries").mkdir(parents=True)
    def write(name, records):
        (memories / name).write_text("".join(json.dumps(r) + "\n" for r in records))
    (memories / "dlmm_entries/p.json").write_text(json.dumps(dict(position="p", deployed_at=100)))
    write("dlmm_closes.jsonl", [dict(position="p", ts=180)])
    write("dlmm_transactions.jsonl", [dict(signature=s, position="p", wallet="wallet", kind=k, ts=t)
          for s,k,t in [("entry","deploy",110),("exit","close",180)]])
    facts = [dict(signature=s,wallet="wallet",observed_at=t,block_time=t,slot=slot,
                  wallet_delta_lamports=amount,fee_lamports=5000,failed=False,
                  token_deltas_raw={"BOT":delta},position_account_closed=s=="exit")
             for s,t,slot,amount,delta in [("entry",110,10,-100000000,"1"),("exit",180,40,101000000,"-1")]]
    gift = dict(signature="gift",wallet="wallet",observed_at=150,block_time=150,slot=30,
                classification="external_token_inflow",token_deltas_raw={"GIFT":"10"})
    write("dlmm_wallet_transactions.jsonl", facts+[gift])
    write("dlmm_wallet_coverage.jsonl", [dict(ts=200,coverage_since=0,end_slot=50,wallet_history_complete=True,unclassified_transactions=[])])
    write("dlmm_nav.jsonl", [dict(ts=90,end_slot=9,nav_sol=1),dict(ts=200,end_slot=50,nav_sol=2,wallet_history_complete=True,unclassified_transactions=[])])
    result = report(root,200)
    assert result["chains"][0]["settled_cash_pnl_sol"] == 0.001  # unrelated gift does not contaminate bot chain
    assert result["flow_adjusted_wealth_change_sol"] is None  # gifted wealth is never profit
    assert result["unvalued_external_token_inflows"] == ["gift"]
    gift["token_deltas_raw"] = {"BOT":"10"}
    write("dlmm_wallet_transactions.jsonl", facts+[gift])
    assert report(root,200)["chains"][0]["settled_cash_pnl_sol"] is None
    assert "external_token_inflow_requires_attribution" in report(root,200)["chains"][0]["reasons"]
print("Passive token inflows do not fabricate wallet profit or contaminate unrelated settled chains")

with TemporaryDirectory() as root:
    memories = Path(root) / "memories"
    (memories / "dlmm_entries").mkdir(parents=True)
    def write(name, records):
        (memories / name).write_text("".join(json.dumps(r) + "\n" for r in records))
    (memories / "dlmm_entries/p.json").write_text(json.dumps(dict(position="p", deployed_at=100)))
    closes = {"p":dict(position="p",ts=180)}
    write("dlmm_closes.jsonl",list(closes.values()))
    events = [dict(signature=s,position=p,wallet="wallet",kind=k,ts=t)
              for s,p,k,t in [("entry","p","deploy",110),("exit","p","close",180),("cleanup",None,"swap",200)]]
    facts = [dict(signature=s,wallet="wallet",observed_at=t,block_time=t,slot=slot,
                  wallet_delta_lamports=amount,fee_lamports=5000,failed=False,
                  token_deltas_raw=delta,position_account_closed=s=="exit")
             for s,t,slot,amount,delta in [("entry",110,10,-100000000,{}),("exit",180,40,90000000,{"BOT":"100"}),
                                          ("cleanup",230,45,11000000,{"BOT":"-100"})]]
    facts[-1].update(token_pre_balances_raw={"BOT":"100"},token_post_balances_raw={})
    write("dlmm_transactions.jsonl",list(reversed(events)))  # journal append order is not chain order
    write("dlmm_wallet_transactions.jsonl",facts)
    coverage=dict(ts=240,coverage_since=0,end_slot=50,wallet_history_complete=True,unclassified_transactions=[])
    write("dlmm_wallet_coverage.jsonl",[coverage])
    result=report(root,240)
    c,=result["chains"]
    assert c["root_chain_id"] == "p" and c["settled_cash_pnl_sol"] == 0.001
    assert c["network_fee_lamports"] == 15000  # already included in cash, never deducted twice
    assert c["token_deltas_raw"] == {} and c["cleanup_settlements"][0]["signature"] == "cleanup"
    assert all(x["net_pnl_sol"] is None for x in report(root,220)["chains"])  # later evidence cannot backfill a decision
    chain=dict(root_chain_id="p",positions={"p"},token_deltas_raw={"BOT":100},pending_signatures=[],first_activity=100)
    args=[events[-1],facts[-1],{"p":chain},closes,coverage,[],float("inf"),240]
    assert cleanup_owner(*args)=="p"
    import copy
    for alter in (
        lambda a:a[1].pop("token_pre_balances_raw"),
        lambda a:a[1]["token_pre_balances_raw"].update(BOT="150"),
        lambda a:a[2].update(other=dict(a[2]["p"],root_chain_id="other",token_deltas_raw={"BOT":1})),
        lambda a:a[5].append(dict(block_time=150,token_deltas_raw={"BOT":"1"})),
        lambda a:a[2]["p"]["pending_signatures"].append("unknown"),
        lambda a:a[4].update(wallet_history_complete=False),
        lambda a:a[3]["p"].update(ts=201),
        lambda a:a.__setitem__(6,150),
        lambda a:a.__setitem__(7,1000),
    ):
        test=copy.deepcopy(args);alter(test);assert cleanup_owner(*test) is None
print("Exact cleanup settlement attribution preserves cash/fees and rejects ambiguous ownership or historical lookahead")

# Pooled exit: an old fee balance is sold by a later position. Cash is measurable
# jointly, but allocating it to the latest root would invent per-position PnL.
from copy import deepcopy
from dlmm_accounting import pooled_settlements, root_decision
base = dict(first_activity=100, last_activity=200, network_fee_lamports=5,
            reasons=["token_inventory_requires_valuation"], accounting_status="incomplete")
a = dict(base, root_chain_id="old", token_deltas_raw={"TOKEN":"9007199254740993"}, wallet_delta_lamports=-200)
b = dict(base, root_chain_id="new", token_deltas_raw={"TOKEN":"-9007199254740993"}, wallet_delta_lamports=180)
original = deepcopy([a,b])
group, = pooled_settlements([a,b])
assert group["settled_cash_pnl_sol"] == -20/1e9  # costs not subtracted twice
assert group["network_fee_sol"] == 10/1e9
assert group["root_chain_ids"] == ["new","old"]
assert [a,b] == original
assert not root_decision(a,1)["allow"] and not root_decision(b,1)["allow"]
assert pooled_settlements([a,dict(b,token_deltas_raw={"TOKEN":"-9007199254740992"})]) == []
for reason in ["unresolved_transactions","open_or_unjournaled_positions","wallet_wide_coverage_not_verified","external_token_inflow_requires_attribution","entry_or_close_evidence_missing"]:
    assert pooled_settlements([a,dict(b,reasons=b["reasons"]+[reason])]) == []
# A third owner must not be omitted just because a subset balances.
c = dict(base,root_chain_id="third",token_deltas_raw={"TOKEN":"1"},wallet_delta_lamports=1)
assert pooled_settlements([a,b,c]) == []
# All mints must cancel, including transitive ownership through another mint.
b2=dict(b,token_deltas_raw={**b["token_deltas_raw"],"OTHER":"2"})
c2=dict(c,token_deltas_raw={"OTHER":"-2"})
assert len(pooled_settlements([a,b2,c2])) == 1
assert pooled_settlements([a,b2,c2]) == pooled_settlements([c2,b2,a])
print("Pooled cash conservation, complete ownership and unchanged root gate passed")

# Shared refunds form disjoint cash groups; evidence cannot rewrite root gates.
from dlmm_accounting import rent_refund_groups
item_a=dict(account="ata-a",mint="A",lamports=100)
item_b=dict(account="ata-b",mint="B",lamports=100)
item_c=dict(account="ata-c",mint="C",lamports=100)
fund_a=dict(signature="fund-a",wallet="wallet",slot=10,failed=False,
            token_rent_evidence=dict(funded=[item_a,item_c]))
fund_b=dict(signature="fund-b",wallet="wallet",slot=11,failed=False,
            token_rent_evidence=dict(funded=[item_b]))
refund_a=dict(signature="refund-a",wallet="wallet",slot=40,block_time=200,failed=False,
              fee_lamports=5,wallet_delta_lamports=195,token_rent_evidence=dict(refunded=[item_a,item_b]))
refund_b=dict(signature="refund-b",wallet="wallet",slot=50,block_time=210,failed=False,
              fee_lamports=5,wallet_delta_lamports=95,token_rent_evidence=dict(refunded=[item_c]))
facts={r["signature"]:r for r in [fund_a,fund_b,refund_a,refund_b]}
chains=[dict(root_chain_id="a",positions=["a"],recorded_signatures=["fund-a"],
             accounting_status="settled_cash",first_activity=100,last_activity=180,
             wallet_delta_lamports=-1000,network_fee_lamports=5),
        dict(root_chain_id="b",positions=["b"],recorded_signatures=["fund-b"],
             accounting_status="settled_cash",first_activity=100,last_activity=180,
             wallet_delta_lamports=500,network_fee_lamports=5),
        dict(root_chain_id="unattributed",positions=[],recorded_signatures=["refund-a","refund-b"])]
histories=[dict(version=1,wallet="wallet",complete=True,observed_at=220,**item,
                refund_signature=refund,funding_signature=fund,history_signatures=[fund])
           for item,refund,fund in [(item_a,"refund-a","fund-a"),(item_b,"refund-a","fund-b"),(item_c,"refund-b","fund-a")]]
original=deepcopy([chains,facts,histories])
group,=rent_refund_groups(chains,facts,histories,220)
assert group["root_chain_ids"]==["a","b"]
assert group["refund_signatures"]==["refund-a","refund-b"]
assert group["cash_with_matched_refunds_sol"]==-210/1e9
assert group["network_fee_sol"]==20/1e9  # two root fees, two refund fees; no duplication
assert group["last_activity"]==210
assert [chains,facts,histories]==original
assert rent_refund_groups(chains,facts,histories,219)==[]  # no future evidence
for alter in (
    lambda a:a[0][0].update(accounting_status="incomplete"),
    lambda a:a[0][0].update(last_activity=300),
    lambda a:a[1]["fund-a"].update(wallet="other"),
    lambda a:a[1]["fund-a"].update(failed=True),
    lambda a:a[1]["fund-a"].update(token_rent_evidence=dict(funded=[])),
    lambda a:[r.update(version=99) for r in a[2]],
    lambda a:[r.update(history_signatures=r["history_signatures"]*2) for r in a[2]],
    lambda a:[r.update(history_signatures=["unknown"]+r["history_signatures"]) for r in a[2]],
):
    args=deepcopy(original);alter(args);assert rent_refund_groups(*args,220)==[]
# Reuse by known settled roots keeps the refund tied to its proved funder.
args=deepcopy(original)
args[2][0]["history_signatures"].insert(0,"fund-b")
remaining,=rent_refund_groups(*args,220)
assert remaining==group
# A refund already included in root cash must never be added again.
args=deepcopy(original);args[0][0]["recorded_signatures"].append("refund-b")
remaining,=rent_refund_groups(*args,220)
assert remaining["refund_signatures"]==["refund-a"]
print("Rent refund group conservation, shared fees, ambiguous roots and observation-time guards passed")

# Refund between root legs remains measurable after the whole chain settles.
args=deepcopy(original);args[0][0]["last_activity"]=215
between,=rent_refund_groups(*args,220)
assert between["last_activity"]==215 and between["cash_with_matched_refunds_sol"]==-210/1e9


# Advisory pool memory must not promote marks, partial roots or shared cross-pool
# refunds into realized net results. Shared fees count once for same-pool roots.
from dlmm_accounting import pool_cash_history
closes = [dict(position="a",pool="P",ts=100,pnl_sol=.01),
          dict(position="b",pool="P",ts=110,pnl_sol=.02)]
ledger = {"chains":[dict(root_chain_id=r,positions=[r],accounting_status="settled_cash") for r in ["a","b"]],
          "rent_refund_groups":[dict(root_chain_ids=["a","b"],cash_with_matched_refunds_sol=-.003)]}
summary = pool_cash_history(closes,ledger,120)["P"]
assert summary["prior_mark_pnl_sol"] == .03 and summary["prior_net_pnl_sol"] == -.003
assert summary["prior_cash_roots"] == 2 and summary["prior_closes"] == 2
split = deepcopy(closes);split[1]["pool"]="Q"
assert all(r["prior_net_pnl_sol"] is None for r in pool_cash_history(split,ledger,120).values())
partial = deepcopy(ledger);partial["chains"][0]["positions"].append("missing-root-leg")
assert pool_cash_history(closes,partial,120)["P"]["prior_net_pnl_sol"] is None
partial = deepcopy(ledger);partial["chains"][0]["accounting_status"]="incomplete"
assert pool_cash_history(closes,partial,120)["P"]["prior_net_pnl_sol"] is None
assert pool_cash_history(closes,ledger,105)["P"]["prior_net_pnl_sol"] is None
assert pool_cash_history(closes,ledger,120+31*86400) == {}
zero=deepcopy(ledger);zero["rent_refund_groups"][0]["cash_with_matched_refunds_sol"]=0
assert pool_cash_history(closes,zero,120)["P"]["prior_net_pnl_sol"] == 0
bad=deepcopy(closes);bad[0]["pnl_sol"]=None
assert pool_cash_history(bad,ledger,120)["P"]["prior_mark_pnl_sol"] is None
print("Pool cash history separates marks, unknown cash, whole roots and shared fees")

# Cross-pool bounds use individually proved refunds; shared fee is never split.
bounded_ledger = {"chains": chains, "rent_refund_groups": [group]}
views = pool_cash_history(split, bounded_ledger, 220)
assert views["P"]["prior_net_pnl_sol"] is None and views["Q"]["prior_net_pnl_sol"] is None
assert views["P"]["prior_pnl_basis"] == "matched_refund_cash_bounds"
assert views["P"]["prior_cash_lower_sol"] == -810/1e9 and views["P"]["prior_cash_upper_sol"] == -805/1e9
assert views["Q"]["prior_cash_lower_sol"] == 595/1e9 and views["Q"]["prior_cash_upper_sol"] == 600/1e9
whole = pool_cash_history(closes, bounded_ledger, 220)["P"]
assert whole["prior_net_pnl_sol"] == -210/1e9 and whole["prior_cash_lower_sol"] == whole["prior_cash_upper_sol"]
# The whole batch cash lies inside the sum of intervals, not at either end.
assert sum(v["prior_cash_lower_sol"] for v in views.values()) < whole["prior_net_pnl_sol"] < sum(v["prior_cash_upper_sol"] for v in views.values())
assert all(v["prior_cash_lower_sol"] is None for v in pool_cash_history(split, bounded_ledger, 205).values())
for mutate in [
    lambda g: g["refund_components"][0].update(fee_lamports=-1),
    lambda g: g["refund_components"][0]["gross_by_root"].update(a=True),
    lambda g: g["refund_components"][0]["gross_by_root"].update(a=101),
    lambda g: g["refund_components"].pop(),
    lambda g: g["refund_components"].append(g["refund_components"][0]),
]:
    bad = deepcopy(bounded_ledger);mutate(bad["rent_refund_groups"][0])
    assert all(v["prior_cash_lower_sol"] is None for v in pool_cash_history(split,bad,220).values())
partial = deepcopy(bounded_ledger);partial["chains"][0]["positions"].append("unselected")
assert pool_cash_history(split,partial,220)["P"]["prior_cash_lower_sol"] is None
print("Cross-pool refund bounds conserve full-group cash and retain unknown/partial evidence")

# A later account user did not finance its rent. Count both users' cash once,
# credit the recorded funder, and retain the shared fee range for either pool.
from dlmm_accounting import refund_cash_bounds
reuse=deepcopy(original)
reuse[0].append(dict(root_chain_id="c",positions=["c"],recorded_signatures=["use-a"],
                    accounting_status="settled_cash",first_activity=105,last_activity=180,
                    wallet_delta_lamports=-20,network_fee_lamports=5))
reuse[1]["use-a"]=dict(signature="use-a",wallet="wallet",slot=20,failed=False)
reuse[2][0]["history_signatures"].insert(0,"use-a")
reuse_before=deepcopy(reuse)
reused,=rent_refund_groups(*reuse,220)
assert reused["root_chain_ids"]==["a","b","c"]
assert reused["cash_with_matched_refunds_sol"]==-230/1e9
assert reused["network_fee_sol"]==25/1e9
component=next(p for p in reused["refund_components"] if p["signature"]=="refund-a")
assert component["gross_by_root"]=={"a":100,"b":100,"c":0}
by_root={c["root_chain_id"]:c for c in reuse[0]}
assert refund_cash_bounds(reused,by_root,{"c"})==(-25,-20)
assert refund_cash_bounds(reused,by_root,{"a","b","c"})==(-230,-230)
views=pool_cash_history(closes+[dict(position="c",pool="R",ts=115,pnl_sol=.01)],
                        dict(chains=reuse[0],rent_refund_groups=[reused]),220)
assert views["R"]["prior_cash_lower_sol"]==-25/1e9
assert views["R"]["prior_cash_upper_sol"]==-20/1e9
assert views["R"]["prior_net_pnl_sol"] is None
assert reuse==reuse_before
for mutate in (
    lambda a:a[0][-1].update(accounting_status="incomplete"),
    lambda a:a[0][-1].update(positions=[]),
    lambda a:a[0][-1].update(last_activity=221),
    lambda a:a[0][0]["recorded_signatures"].append("use-a"),
    lambda a:a[1]["use-a"].update(wallet="other"),
    lambda a:a[1]["use-a"].update(landed=False),
    lambda a:a[2][0]["history_signatures"].insert(0,"unknown"),
):
    invalid=deepcopy(reuse);mutate(invalid)
    surviving,=rent_refund_groups(*invalid,220)
    assert surviving["refund_signatures"]==["refund-b"]
assert rent_refund_groups(*reuse,219)==[]
print("Reused account refunds prove funding, all settled users, shared fee bounds and conservation")

# Legacy wallet inventory is never a source of automatic position settlement.
with TemporaryDirectory() as root:
    memories = Path(root) / "memories"
    (memories / "dlmm_entries").mkdir(parents=True)
    (memories / "dlmm_entries/p.json").write_text(json.dumps(
        dict(position="p", deployed_at=100, base_mint="TOKEN")))
    def write(name, records):
        (memories / name).write_text("".join(json.dumps(r) + "\n" for r in records))
    events = [dict(signature=s, position="p", wallet="wallet", kind=k, ts=t)
              for s,k,t in [("deploy","deploy",100),("close","close",200)]]
    facts = [dict(signature=s, wallet="wallet", observed_at=t, block_time=t, slot=slot,
                  wallet_delta_lamports=0, fee_lamports=5000, failed=False,
                  token_deltas_raw={"TOKEN":"0"}, token_pre_balances_raw={"TOKEN":"5433"},
                  token_post_balances_raw={"TOKEN":"5433"}, position_account_closed=s=="close")
             for s,t,slot in [("deploy",100,10),("close",200,20)]]
    write("dlmm_closes.jsonl", [dict(position="p", ts=200, deployed_at=100, base_mint="TOKEN")])
    write("dlmm_transactions.jsonl", events)
    write("dlmm_transaction_facts.jsonl", facts)
    proof = lambda: settlement_inventory(root,"p","TOKEN","wallet")
    assert proof() == {"success":True,"amount_raw":"0"}  # actual testicle pre-sale balances
    # A missing close report may complete ONLY zero owned inventory, using
    # finalized facts bound to the recorded position and wallet. Keep the
    # accounting journal incomplete, and leave all legacy tokens untouched.
    write("dlmm_closes.jsonl", [])
    assert not proof()["success"]  # legacy facts lack explicit position binding
    bound = deepcopy(facts)
    bound[1]["event_position"] = "p"
    write("dlmm_transaction_facts.jsonl", bound)
    assert proof() == {"success":True,"amount_raw":"0"}
    assert report(root)["chains"][0]["accounting_status"] == "incomplete"
    for change in [{"event_position":"other"}, {"wallet":"other"},
                   {"failed":True}, {"landed":False}, {"slot":0},
                   {"slot":True}, {"position_account_closed":False},
                   {"token_deltas_raw":{"TOKEN":"1"}, "token_post_balances_raw":{"TOKEN":"5434"}}]:
        invalid = deepcopy(bound)
        invalid[1].update(change)
        write("dlmm_transaction_facts.jsonl", invalid)
        assert not proof()["success"], change
    write("dlmm_transaction_facts.jsonl", facts)
    write("dlmm_closes.jsonl", [dict(position="p", ts=200, deployed_at=100, base_mint="TOKEN")])
    # A filled position adds exactly 100 raw units to 5433 old units.
    facts[1]["token_deltas_raw"]={"TOKEN":"100"}
    facts[1]["token_post_balances_raw"]={"TOKEN":"5533"}
    write("dlmm_transaction_facts.jsonl",facts)
    assert proof() == {"success":True,"amount_raw":"100","wallet_balance_raw":"5533","slot":20}
    assert not settlement_inventory(root,"p","TOKEN","other-wallet")["success"]
    assert not settlement_inventory(root,"p","OTHER","wallet")["success"]
    # Cached evidence is mandatory; a close not finalized yet cannot sell.
    write("dlmm_transaction_facts.jsonl",facts[:1])
    assert proof()["pending_signatures"] == ["close"]
    write("dlmm_transaction_facts.jsonl",facts)
    write("dlmm_closes.jsonl",[])
    assert not proof()["success"]
    write("dlmm_closes.jsonl",[dict(position="p",ts=200,deployed_at=100)])
    gift=dict(signature="gift",wallet="wallet",classification="external_token_inflow",slot=30,
              block_time=300,observed_at=300,token_deltas_raw={"TOKEN":"5"})
    write("dlmm_wallet_transactions.jsonl",[gift])
    assert not proof()["success"]  # also refuse gifts received AFTER the close
    write("dlmm_wallet_transactions.jsonl",[])
    # Other unsettled ownership of the same mint is not allocated pro rata.
    (memories / "dlmm_entries/other.json").write_text(json.dumps(dict(position="other",base_mint="TOKEN",deployed_at=250)))
    write("dlmm_transactions.jsonl",events+[dict(signature="other",position="other",wallet="wallet",kind="deploy",ts=250)])
    write("dlmm_transaction_facts.jsonl",facts+[dict(facts[0],signature="other",slot=30,token_deltas_raw={"TOKEN":"1"})])
    assert not proof()["success"]
    write("dlmm_transactions.jsonl",events)
    write("dlmm_transaction_facts.jsonl",facts)
    (memories / "dlmm_entries/other.json").unlink()
    # A fee claim and close in the same slot must choose the conserved endpoint.
    claimed=dict(facts[1],signature="aa-fee",position_account_closed=False,
                 token_deltas_raw={"TOKEN":"10"},token_post_balances_raw={"TOKEN":"5443"})
    closed=dict(facts[1],token_deltas_raw={"TOKEN":"90"},token_pre_balances_raw={"TOKEN":"5443"})
    write("dlmm_transactions.jsonl",events+[dict(signature="aa-fee",position="p",wallet="wallet",kind="claim",ts=199)])
    write("dlmm_transaction_facts.jsonl",[facts[0],claimed,closed])
    assert proof()=={"success":True,"amount_raw":"100","wallet_balance_raw":"5533","slot":20}
    write("dlmm_transactions.jsonl",events);write("dlmm_transaction_facts.jsonl",facts)
    # Historic debts for this mint cannot seize or strand a newly proved lot.
    (memories / "dlmm_entries/old.json").write_text(json.dumps(dict(position="old",base_mint="TOKEN",deployed_at=50)))
    old_event=dict(signature="old",position="old",wallet="wallet",kind="deploy",ts=50)
    old_fact=dict(facts[0],signature="old",slot=5,block_time=50,
                  token_pre_balances_raw={"TOKEN":"0"},token_post_balances_raw={"TOKEN":"9007199254740993"},
                  token_deltas_raw={"TOKEN":"9007199254740993"})
    write("dlmm_transactions.jsonl",events+[old_event]);write("dlmm_transaction_facts.jsonl",facts+[old_fact])
    assert proof()["amount_raw"]=="100" and proof()["wallet_balance_raw"]=="5533"
    # Fresh-wallet lot: old offsetting/unattributed accounting is not its inventory.
    fresh=[dict(facts[0],token_pre_balances_raw={"TOKEN":"0"},token_post_balances_raw={"TOKEN":"0"}),
           dict(facts[1],token_pre_balances_raw={"TOKEN":"0"},token_post_balances_raw={"TOKEN":"100"})]
    old_fact.update(token_pre_balances_raw={"TOKEN":"9007199254740993"},token_post_balances_raw={"TOKEN":"0"},
                    token_deltas_raw={"TOKEN":"-9007199254740993"})
    write("dlmm_transaction_facts.jsonl",fresh+[old_fact]);assert proof()["amount_raw"]=="100"
    (memories / "dlmm_entries/old.json").unlink();write("dlmm_transactions.jsonl",events)
    # Refuse unexplained baseline shifts despite a valid local close delta.
    for shift in (-10,10):
        moved=dict(facts[1],token_pre_balances_raw={"TOKEN":str(5433+shift)},
                   token_post_balances_raw={"TOKEN":str(5533+shift)})
        write("dlmm_transaction_facts.jsonl",[facts[0],moved]);assert not proof()["success"]
    # A known external outflow after close is not permission to sell legacy tokens.
    transfer=dict(facts[1],signature="transfer",slot=30,classification="external_token_outflow",
                  token_deltas_raw={"TOKEN":"-100"},token_pre_balances_raw={"TOKEN":"5533"},
                  token_post_balances_raw={"TOKEN":"5433"})
    write("dlmm_wallet_transactions.jsonl",[transfer]);write("dlmm_transaction_facts.jsonl",facts)
    assert not proof()["success"]
    write("dlmm_wallet_transactions.jsonl",[])
    invalid=dict(facts[1]);invalid.pop("token_pre_balances_raw")
    write("dlmm_transaction_facts.jsonl",[facts[0],invalid]);assert not proof()["success"]
    write("dlmm_transaction_facts.jsonl",facts)
    # Only the owned amount is removed; legacy wallet dust may remain nonzero.
    swap=dict(facts[1],signature="sale",slot=30,position_account_closed=False,
              token_deltas_raw={"TOKEN":"-100"},token_post_balances_raw={"TOKEN":"5433"})
    write("dlmm_transactions.jsonl",events+[dict(signature="sale",position="p",wallet="wallet",kind="swap",ts=300)])
    write("dlmm_transaction_facts.jsonl",facts+[swap])
    assert proof()=={"success":True,"amount_raw":"0"}
    # Historical legacy sales remain an error, never zeroed or called profit.
    swap["token_deltas_raw"]={"TOKEN":"-5533"}
    swap["token_post_balances_raw"]={}
    write("dlmm_transaction_facts.jsonl",facts+[swap])
    assert not proof()["success"]
print("Settlement inventory provenance, legacy preservation and finalized evidence passed")

# Evaluations use full-life selected roots and conserve shared refund fees.
from dlmm_evaluate import matched_refund_cash_cohort
from copy import deepcopy
def cash_root(root, cash, first=120, last=180, status="settled_cash"):
    return dict(root_chain_id=root,positions=[root],first_activity=first,last_activity=last,
                wallet_delta_lamports=cash,accounting_status=status)
def cash_group(ids, gross, fee, cash, signature, last=190):
    return dict(root_chain_ids=ids,refund_signatures=[signature],last_activity=last,
                refund_components=[dict(signature=signature,gross_by_root=gross,fee_lamports=fee)],
                cash_with_matched_refunds_sol=cash/1e9)
ledger=dict(chains=[cash_root("a",-100),cash_root("b",-100),cash_root("old",-500,20),
                    cash_root("zero",-10),cash_root("ambiguous",-2),cash_root("old2",-100,20),
                    cash_root("unknown",-9,status="incomplete"),cash_root("future",1,220,250)],
            rent_refund_groups=[cash_group(["a","b","old"],{"a":110,"b":90,"old":700},5,195,"batch"),
                                cash_group(["zero"],{"zero":12},2,0,"zero-refund"),
                                cash_group(["ambiguous","old2"],{"ambiguous":5,"old2":100},5,-2,"ambiguous-refund")])
view=matched_refund_cash_cohort(ledger,100,200)
assert view["window_roots"]==5 and view["measured_roots"]==4
assert view["unmeasured_root_ids"]==["unknown"]
assert (view["cash_positive_roots"],view["cash_negative_roots"],view["cash_zero_roots"],view["ambiguous_roots"])==(1,1,1,1)
assert view["sign_resolved_roots"]==3 and view["cash_positive_rate"]==1/3
assert (view["cohort_cash_lower_sol"],view["cohort_cash_upper_sol"])==(-7/1e9,3/1e9)
assert {r["root"] for r in view["roots"]}=={"a","b","zero","ambiguous"}
# Summing individual lower bounds would charge batch fees twice.
assert sum(round(r["cash_lower_sol"]*1e9) for r in view["roots"])==-12
assert round(view["cohort_cash_lower_sol"]*1e9)==-7
for mutate in [lambda g:g.update(last_activity=201),lambda g:g.pop("refund_components"),
               lambda g:g.update(cash_with_matched_refunds_sol=999),lambda g:g["refund_components"][0].update(fee_lamports=True)]:
    invalid=deepcopy(ledger);mutate(invalid["rent_refund_groups"][0])
    assert matched_refund_cash_cohort(invalid,100,200)["measured_roots"]==2
# Duplicate/overlapping groups must never count the same root/cost twice.
duplicate=deepcopy(ledger);duplicate["rent_refund_groups"].append(deepcopy(duplicate["rent_refund_groups"][0]))
assert matched_refund_cash_cohort(duplicate,100,200)["measured_roots"]==2
empty=matched_refund_cash_cohort(dict(chains=ledger["chains"],rent_refund_groups=[]),100,200)
assert empty["cohort_cash_lower_sol"] is None and empty["cash_positive_rate"] is None
assert empty["unmeasured_roots"]==5
print("Evaluation matched refunds, cohort boundaries, fee conservation and unknown denominators passed")

# A swap may return an account's rent inside its already-recorded wallet cash.
# Prove the entire funded lifecycle; never add its rent to that cash again.
inline_item=dict(account="inline-ata",mint="TOKEN",lamports=200)
inline_facts={
    "fund":dict(signature="fund",wallet="wallet",schema_version=11,slot=10,block_time=100,
                observed_at=105,failed=False,wallet_delta_lamports=-1210,fee_lamports=10,
                token_rent_evidence=dict(version=1,funded=[inline_item],refunded=[])),
    "failed":dict(signature="failed",wallet="wallet",slot=20,block_time=150,
                  observed_at=151,failed=True,wallet_delta_lamports=-5,fee_lamports=5),
    "inline-close":dict(signature="inline-close",wallet="wallet",schema_version=12,slot=30,
                        block_time=180,observed_at=181,failed=False,wallet_delta_lamports=1190,
                        fee_lamports=10,token_rent_evidence=dict(version=1,funded=[],refunded=[],
                        refunds_unmeasured=True,inline_closed=[dict(account="inline-ata",mint="TOKEN",pre_lamports=200)])),
}
inline_chain=dict(root_chain_id="inline",positions=["inline"],recorded_signatures=list(inline_facts),
                  accounting_status="settled_cash",first_activity=100,last_activity=180,
                  wallet_delta_lamports=-25,network_fee_lamports=25,lp_pnl_sol=.00001)
inline_history=dict(version=1,wallet="wallet",complete=True,observed_at=220,**inline_item,
                    refund_signature="inline-close",funding_signature="fund",history_signatures=["failed","fund"])
inline_args=[[inline_chain],inline_facts,[inline_history]]
inline_before=deepcopy(inline_args)
inline_group,=rent_refund_groups(*inline_args,220)
assert inline_args==inline_before
assert inline_group["cash_with_matched_refunds_sol"]==-25/1e9
assert inline_group["network_fee_sol"]==25/1e9
assert inline_group["refund_signatures"]==inline_group["refund_components"]==[]
assert refund_cash_bounds(inline_group,{"inline":inline_chain},{"inline"})==(-25,-25)
inline_ledger=dict(chains=[inline_chain],rent_refund_groups=[inline_group])
inline_view=matched_refund_cash_cohort(inline_ledger,100,220)
assert inline_view["measured_roots"]==inline_view["cash_negative_roots"]==1
assert inline_view["cohort_cash_lower_sol"]==inline_view["cohort_cash_upper_sol"]==-25/1e9
assert pool_cash_history([dict(position="inline",pool="P",ts=180)],inline_ledger,220)["P"]["prior_net_pnl_sol"]==-25/1e9
assert rent_refund_groups(*inline_args,219)==[]

# A proved expired submission has neither a landed slot nor a network fee.
# Keep the actual failed transaction's fee and every account-lifecycle check.
inline_expired=deepcopy(inline_args)
inline_expired[0][0]['recorded_signatures'].append('expired')
inline_expired[0][0]['expired_unlanded_signatures']=['expired']
inline_expired[1]['expired']=dict(signature='expired',wallet='wallet',schema_version=3,
    observed_at=210,landed=False,classification='expired_unlanded',
    last_valid_block_height=100,finalized_block_height=101,
    basis='finalized_wallet_history_and_expiry')
expired_group,=rent_refund_groups(*inline_expired,220)
assert expired_group['cash_with_matched_refunds_sol']==-25/1e9
assert expired_group['network_fee_sol']==25/1e9
assert expired_group['inline_rent_pairs']==inline_group['inline_rent_pairs']
for mutate in (
    lambda a:a[0][0].update(expired_unlanded_signatures=[]),
    lambda a:a[0][0]['expired_unlanded_signatures'].append('unknown'),
    lambda a:a[0][0]['expired_unlanded_signatures'].append('failed'),
    lambda a:a[0].append(dict(root_chain_id='other',recorded_signatures=['expired'])),
    lambda a:a[1]['expired'].update(wallet='other'),
    lambda a:a[1]['expired'].update(landed=True),
    lambda a:a[1]['expired'].update(classification='recorded_bot'),
    lambda a:a[1]['expired'].update(observed_at=221),
    lambda a:a[1]['expired'].update(observed_at=float('nan')),
    lambda a:a[1]['expired'].update(finalized_block_height=100),
    lambda a:a[1]['expired'].update(last_valid_block_height=True),
    lambda a:a[1]['expired'].update(basis='unknown'),
    lambda a:a[1]['expired'].update(fee_lamports=5),
    lambda a:a[1]['expired'].update(wallet_delta_lamports=-5),
    lambda a:a[2][0]['history_signatures'].insert(0,'expired'),
):
    invalid=deepcopy(inline_expired);mutate(invalid)
    assert rent_refund_groups(*invalid,220)==[]
print('Inline rent preserves failed fees and excludes only proved expired submissions')

for mutate in (
    lambda a:a[0][0].update(accounting_status="incomplete"),
    lambda a:a[0][0].update(last_activity=221),
    lambda a:a[0][0].update(wallet_delta_lamports=-24),
    lambda a:a[0][0].update(network_fee_lamports=20),
    lambda a:a[0].append(dict(root_chain_id="other",recorded_signatures=["fund"])),
    lambda a:a[1]["fund"].update(wallet="other"),
    lambda a:a[1]["fund"].update(observed_at=221),
    lambda a:a[1]["inline-close"].update(slot=10),
    lambda a:a[1]["inline-close"].update(schema_version=11),
    lambda a:a[1]["inline-close"].update(landed=False),
    lambda a:a[1]["inline-close"].update(block_time=float("nan")),
    lambda a:a[1]["inline-close"].update(token_rent_evidence=None),
    lambda a:a[1]["inline-close"]["token_rent_evidence"].update(refunds_unmeasured=False),
    lambda a:a[1]["inline-close"]["token_rent_evidence"].update(inline_closed=[]),
    lambda a:a[1]["fund"]["token_rent_evidence"]["funded"][0].update(lamports=201),
    lambda a:a[1]["fund"]["token_rent_evidence"]["funded"].append(dict(account="unclosed",mint="TOKEN",lamports=200)),
    lambda a:a[2][0].update(complete=False),
    lambda a:a[2][0].update(funding_signature="unknown"),
    lambda a:a[2][0].update(history_signatures=["unknown","fund"]),
    lambda a:a[2][0].update(history_signatures=["fund","fund"]),
):
    invalid=deepcopy(inline_args);mutate(invalid)
    assert rent_refund_groups(*invalid,220)==[]
for mutate in (
    lambda g:g.pop("inline_rent_pairs"),
    lambda g:g.update(cash_with_matched_refunds_sol=175/1e9),
    lambda g:g["inline_rent_pairs"][0].update(close_signature="outside"),
    lambda g:g["inline_rent_pairs"][0].update(funding_signature=[]),
    lambda g:g["inline_rent_pairs"][0].update(lamports=True),
    lambda g:g["inline_rent_pairs"].append(g["inline_rent_pairs"][0]),
):
    invalid=deepcopy(inline_group);mutate(invalid)
    assert refund_cash_bounds(invalid,{"inline":inline_chain},{"inline"}) is None

# The learner must see the negative wallet result despite a positive LP valuation.
from unittest.mock import patch
import dlmm_weights
with TemporaryDirectory() as root:
    file=Path(root)/"closes.jsonl"
    file.write_text(json.dumps(dict(position="inline",ts=180,signal=dict(volume_m5=1),pnl_sol=.00001))+"\n")
    with patch.object(dlmm_weights,"CLOSES_PATH",str(file)), patch.object(dlmm_weights,"report",return_value=inline_ledger), patch.object(dlmm_weights.time,"time",return_value=220):
        learned,=dlmm_weights.load_recent_closes()
        assert dlmm_weights.outcome_sol(learned)==-25/1e9
        assert learned["cash_pnl_lower_sol"]==learned["cash_pnl_upper_sol"]==-25/1e9
print("Owned inline rent lifecycle, exact cash conservation, hindsight guards and negative learner labels passed")

# Accounting needs two NAV records, not all historical payloads. Preserve the
# first complete record and the last eligible record in file order, not max(ts).
import tracemalloc
from dlmm_accounting import rows
with TemporaryDirectory() as directory:
    profile=Path(directory); memory=profile/'memories';memory.mkdir()
    file=memory/'dlmm_nav.jsonl'
    with file.open('w') as output:
        for ts in range(96):
            output.write(json.dumps(dict(ts=ts,end_slot=ts,nav_sol=1 if ts==10 else None,
                wallet_history_complete=True,padding='x'*65536))+'\n')
        output.write(json.dumps(dict(ts=80,end_slot=80,nav_sol=2,wallet_history_complete=True))+'\n')
        output.write(json.dumps(dict(ts=999,end_slot=999,nav_sol=99,wallet_history_complete=True))+'\n')
    tracemalloc.start()
    ledger=report(profile,200)
    _,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
    assert peak<2*1024**2,peak
    assert ledger['nav_snapshot']['ts']==80 and ledger['nav_sol']==2
    assert ledger['flow_adjusted_wealth_change_sol']==1
    assert rows(memory/'missing.jsonl')==[]
    small=memory/'small.jsonl';small.write_text('\n{"a":1}\n\n{"a":2}\n')
    assert rows(small)==[{'a':1},{'a':2}]
    with file.open('a') as output:output.write('{broken-json}\n')
    try: report(profile,200)
    except json.JSONDecodeError: pass
    else: raise AssertionError('Corrupt future NAV must remain visible')
print('Accounting streams NAV history while preserving first/last valuation and corruption visibility')
