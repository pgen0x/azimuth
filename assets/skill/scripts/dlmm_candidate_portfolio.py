"""Finite-capital accounting for hypothetical candidate LP tickets. Never trade."""
import heapq


def simulate(cohorts, initial_cash, *, ticket=100000000, rent=45000000,
             retained_rent=1513840, reserve=20000000, network_cost=26151,
             cleanup_delay=1800, extra_cost=0):
    """Reserve cash before entry; unresolved outcomes keep the entire escrow.

    Capital and the rent allowance are financing requirements, not losses. All
    costs are included once in the ticket net, with a matching upfront reserve.
    A missing outcome is not a zero-return trade or a usable cash balance.
    """
    if (any(type(n) is not int or n<0 for n in (initial_cash,ticket,rent,retained_rent,
                                               reserve,network_cost,cleanup_delay,extra_cost))
            or ticket==0 or retained_rent>rent):
        raise ValueError('invalid_portfolio_budget')
    cash=initial_cash;events=[];serial=0;positions={};decisions=[];known_net=0;minimum_cash=cash
    def settle(until):
        nonlocal cash,known_net,minimum_cash
        while events and events[0][0]<=until:
            stamp,_,kind,ident,amount=heapq.heappop(events)
            row=positions[ident];cash+=amount
            if kind=='close':
                row['status']='closed_waiting_rent' if retained_rent else 'complete'
                known_net+=row['net_lamports']
            else:
                row['status']='complete'
            minimum_cash=min(minimum_cash,cash)
            decisions.append(dict(at=stamp,kind=kind,id=ident,credit_lamports=amount,cash_lamports=cash))
    for candidate in sorted(cohorts,key=lambda r:(r['entry_at'],r['id'])):
        ident=candidate['id'];start=candidate['entry_at'];settle(start)
        if ident in positions:
            raise ValueError('duplicate_candidate')
        if not candidate['entry_eligible']:
            decisions.append(dict(at=start,kind='entry_ineligible',id=ident))
            continue
        composition=candidate['entry_cost_lamports']
        if type(composition) is not int or composition<0:
            raise ValueError('invalid_entry_cost')
        escrow=ticket+rent+network_cost+composition+extra_cost
        if cash<escrow+reserve:
            decisions.append(dict(at=start,kind='insufficient_cash',id=ident,cash_lamports=cash,
                                  required_lamports=escrow+reserve))
            continue
        cash-=escrow;minimum_cash=min(minimum_cash,cash)
        row=dict(id=ident,status='unknown',escrow_lamports=escrow,entry_at=start)
        positions[ident]=row;decisions.append(dict(at=start,kind='entry',id=ident,escrow_lamports=escrow,cash_lamports=cash))
        net=candidate.get('modeled_net_lamports');end=candidate.get('exit_at')
        if net is None or end is None:
            continue
        if type(net) is not int or not end>start:
            raise ValueError('invalid_terminal')
        net-=extra_cost;row.update(status='open',net_lamports=net,exit_at=end)
        # The quote model already deducts lifecycle costs, so returning the
        # reserved budget plus net charges those costs exactly once.
        credit=escrow+net-retained_rent
        if credit<0:
            raise ValueError('terminal_loss_exceeds_reserved_budget')
        serial+=1;heapq.heappush(events,(end,serial,'close',ident,credit))
        if retained_rent:
            serial+=1;heapq.heappush(events,(end+cleanup_delay,serial,'rent',ident,retained_rent))
    settle(float('inf'))
    unknown=[r for r in positions.values() if r['status']=='unknown']
    unresolved=sum(r['escrow_lamports'] for r in unknown)
    if cash+unresolved!=initial_cash+known_net:
        raise AssertionError('cash_conservation_failed')
    completed=[r for r in positions.values() if r['status']=='complete']
    return dict(initial_cash_lamports=initial_cash,available_cash_lamports=cash,
                known_ticket_net_lamports=known_net,
                final_equity_lamports=cash if not unknown else None,
                final_net_lamports=known_net if not unknown else None,
                unresolved_escrow_lamports=unresolved,unknown_positions=len(unknown),
                selected_positions=len(positions),completed_positions=len(completed),
                positive_positions=sum(r['net_lamports']>0 for r in completed),
                nonpositive_positions=sum(r['net_lamports']<=0 for r in completed),
                capacity_skips=sum(r['kind']=='insufficient_cash' for r in decisions),
                eligibility_skips=sum(r['kind']=='entry_ineligible' for r in decisions),
                minimum_available_cash_lamports=minimum_cash,decisions=decisions,
                positions=list(positions.values()),promotion_allowed=False,
                basis='hypothetical_cash_flow_with_estimated_fills_and_costs; unresolved_escrow_not_equity')
