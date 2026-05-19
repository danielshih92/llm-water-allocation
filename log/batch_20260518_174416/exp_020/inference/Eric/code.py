# ============================================================
# Experiment: exp_020
# Agent: Eric
# Source: exp_020
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    supply = day_context['supply']
    day = day_context['day']
    
    # Estimate average supply based on range 15-25
    avg_supply = 20.0
    
    # Base bid: small fraction of salary when healthy
    if hp > 4:
        base_bid = DAILY_SALARY * 0.35
    elif hp > 2:
        base_bid = DAILY_SALARY * 0.6
    else:
        base_bid = DAILY_SALARY * 0.9
    
    # Adjust for no_water_days: increase if desperate
    if no_water_days >= 2:
        base_bid = min(base_bid + DAILY_SALARY * 0.2, DAILY_SALARY * 0.95)
    
    # Ensure we don't overbid relative to budget
    max_bid = budget
    if max_bid <= 0:
        return 0
    
    # Consider supply: if supply low, competition may be higher
    # But we don't have opponent info, so keep bid same
    bid = min(base_bid, max_bid)
    
    # Late game consideration (last few days): be more aggressive if low hp
    if day >= 7 and hp <= 3:
        bid = min(DAILY_SALARY * 0.95, max_bid)
    
    return bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    alive_opponents = {k: v for k, v in opponents_status.items() if v.get('alive', False)}
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    # Determine base bid
    base = DAILY_SALARY * 0.5
    if no_water_days >= 2 or hp <= 3:
        base = DAILY_SALARY * 0.9
    elif hp > 6:
        if yesterday_bids:
            base = max(yesterday_bids) + 1.0
        else:
            base = DAILY_SALARY * 0.6
    else:
        if yesterday_bids:
            base = max(yesterday_bids) + 0.5
        else:
            base = DAILY_SALARY * 0.7
    # Ensure we don't exceed budget
    bid = min(budget, base)
    # Ensure not negative
    bid = max(0.0, bid)
    # Round to avoid floats with too many decimals
    return round(bid, 2)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = int(day_context['supply'])
    day = int(day_context['day'])
    my_hp = int(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water = int(my_status['no_water_days'])

    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Base bid: 70 (50% salary)
    base_bid = DAILY_SALARY * 0.5

    # Adjust based on yesterday's max bid
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        # If yesterday's max was high, opponent may bid similarly or higher today
        if max_prev > DAILY_SALARY * 0.8:
            # Competitive bidding expected
            if my_hp <= 2 or my_no_water > 0:
                target = max_prev + 5
            else:
                target = max_prev + 1
        else:
            # Moderate bidding
            target = max_prev + 2
        # Cap by budget and sanity
        bid = min(my_budget, max(base_bid, target))
    else:
        # No history, use base adjusted by HP
        if my_hp <= 2 or my_no_water > 0:
            bid = min(my_budget, DAILY_SALARY * 0.9)
        else:
            bid = min(my_budget, base_bid)

    # Additional adjustment for supply scarcity
    if supply < MIN_SUPPLY + 3:
        bid = min(my_budget, bid * 1.2)
    elif supply > MAX_SUPPLY - 3:
        bid = min(my_budget, bid * 0.8)

    # Ensure bid is within [0, budget] and at least 0
    bid = max(0, min(bid, my_budget))
    return float(bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']
    supply = day_context['supply']
    
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Determine yesterday's maximum bid among alive opponents
    yesterday_max = 0.0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_max = max(yesterday_max, prev['bid'])
    
    # Base bid: if we urgently need water, bid high; otherwise low
    urgent = (hp <= 3) or (no_water > 0)
    if urgent:
        # Must win water: bid above yesterday's max or a safe threshold
        target = max(DAILY_SALARY * 0.7, yesterday_max + 1.0)
    else:
        # Conserve: bid low but not zero to avoid suspicion? Bid based on supply
        # If supply is low, competition may be high, so be a bit more aggressive
        if supply < 18:
            target = DAILY_SALARY * 0.4
        else:
            target = DAILY_SALARY * 0.25
    
    # Ensure we don't exceed budget and cap at sensible maximum
    bid = min(budget, target)
    # Also ensure bid is non-negative and not exceeding salary * 2 (defensive)
    bid = max(0.0, bid)
    return bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    prev_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])

    max_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Calculate baseline bid: salary * water_requirement / supply
    # supply is float, ensure division yields float
    baseline = DAILY_SALARY * WATER_REQ / supply

    # Determine urgency: if no_water_days > 0 or hp <= 2, very urgent
    urgent = (no_water_days > 0) or (hp <= 2)

    if urgent:
        # Need to win: bid just above max previous if feasible, else max budget
        target = max(baseline * 1.3, max_prev_bid + 1.0)
        # But cap at budget
        return min(budget, target)
    else:
        # Not urgent: bid moderately, try to save budget
        # If max_prev_bid is high, undercut slightly
        if max_prev_bid > baseline * 1.2:
            # Opponents are aggressive, bid conservative
            target = baseline * 1.1
        else:
            # Opponents moderate, bid a bit above baseline
            target = max(baseline, max_prev_bid + 0.5)
        # Ensure we don't exceed budget
        return min(budget, target)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    DAILY_SALARY = 140
    WATER_REQ = 8
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    
    # Collect opponents' previous bids from traces
    prev_bids = []
    for opp in opponents_status.values():
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    
    # Base bid as fraction of salary based on desperation
    if hp <= 2:
        base = 0.9 * DAILY_SALARY
    elif hp <= 5:
        base = 0.6 * DAILY_SALARY
    else:
        base = 0.4 * DAILY_SALARY
    
    # Adjust upwards if supply is low (competition high)
    supply_ratio = supply / 25.0  # normalize
    supply_factor = 1 + 0.3 * (1 - supply_ratio)
    
    # Consider opponents' max previous bid
    if prev_bids:
        max_prev = max(prev_bids)
        # If someone bid very high, we might need to match if we are desperate
        if max_prev > 110 and hp <= 3:
            target = min(budget, max_prev + 5)
        else:
            target = max(base, max_prev * 0.95)
    else:
        target = base
    
    target = target * supply_factor
    # Clamp to budget and salary
    bid = min(budget, target)
    bid = max(0, bid)
    # Ensure integer? Bids can be float.
    return bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    # Get alive opponents
    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    
    # Collect yesterday's bids from opponents that have previous_trace
    last_bids = []
    for opp in alive_opponents:
        trace = opp.get('previous_trace', {})
        if trace and 'bid' in trace and trace['bid'] is not None:
            last_bids.append(trace['bid'])

    # Base bid calculation
    if hp <= 2 or no_water_days > 0:
        # Critical: need water
        bid = DAILY_SALARY * 0.95
    else:
        # Healthy: try to bid strategically
        if last_bids:
            max_prev = max(last_bids)
            if max_prev >= DAILY_SALARY * 0.85:
                # Someone bid very high yesterday, likely will again
                # If we are healthy, we can undercut to save budget
                if hp > 3:
                    bid = DAILY_SALARY * 0.6
                else:
                    bid = DAILY_SALARY * 0.9
            else:
                # Opponents not too aggressive, bid slightly above their max
                bid = max(DAILY_SALARY * 0.5, max_prev + 5.0)
        else:
            # No yesterday data, default moderate bid
            bid = DAILY_SALARY * 0.65

    # Ensure we don't bid more than budget
    bid = min(budget, bid)
    # Also ensure non-negative
    bid = max(0.0, bid)
    return bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o['alive']]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    max_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Base bid: moderate
    base_bid = DAILY_SALARY * 0.5

    # Adjust for hp
    if hp <= 2:
        base_bid = DAILY_SALARY * 0.9
    elif hp <= 4:
        base_bid = DAILY_SALARY * 0.7

    # Adjust for no water days
    if no_water_days > 0:
        base_bid = min(base_bid + 20, DAILY_SALARY * 1.0)

    # Exploit yesterday's aggression: if max bid was very high, be conservative
    if max_prev_bid >= DAILY_SALARY * 0.85 and hp > 3:
        base_bid = min(base_bid, DAILY_SALARY * 0.35)

    # Supply scarcity
    if supply < 18:
        base_bid = max(base_bid, DAILY_SALARY * 0.6)

    # Budget cap
    bid = min(budget, base_bid)
    return max(0.0, bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    # Filter alive opponents
    alive_opps = {oid: o for oid, o in opponents_status.items() if o['alive']}
    
    # Collect yesterday's bids from alive opponents that have a trace
    yesterday_bids = []
    for oid, opp in alive_opps.items():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Determine a base bid from opponent pressure
    if yesterday_bids:
        highest_yesterday = max(yesterday_bids)
        # If we are desperate (low hp or no water yesterday), need to win
        if hp <= 2 or no_water_days > 0:
            # Outbid the highest yesterday by a small margin, but cap at budget
            bid = min(budget, highest_yesterday + 2.0)
        else:
            # Try to be efficient: bid just above average of yesterday's top half
            sorted_bids = sorted(yesterday_bids, reverse=True)
            # Use the second highest as reference
            if len(sorted_bids) >= 2:
                ref_bid = sorted_bids[1]  # second highest
            else:
                ref_bid = sorted_bids[0]
            # If supply is low, increase bid slightly
            if supply < 18:
                ref_bid = max(ref_bid, DAILY_SALARY * 0.5)
            # Comfortable: not exceeding DAILY_SALARY * 0.7 to save budget
            bid = min(budget, max(ref_bid + 1.0, DAILY_SALARY * 0.4))
            # But not lower than a minimum to stay alive
            bid = max(bid, DAILY_SALARY * 0.3)
    else:
        # No historical data: be cautious
        if hp <= 2 or no_water_days > 0:
            bid = min(budget, DAILY_SALARY * 0.8)
        else:
            bid = min(budget, DAILY_SALARY * 0.5)
    
    # Ensure at least 1 if budget allows (bidding 0 is invalid? Usually allowed but low chance)
    bid = max(1.0, bid)
    # Final cap to budget
    bid = min(budget, bid)
    
    # Ensure numeric type is float
    return float(bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MAX_BID_FACTOR = 0.85  # to stay conservative
    URGENT_FACTOR = 0.95
    
    supply = day_context['supply']
    day = day_context['day']
    
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water = my_status['no_water_days']
    
    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    
    # Estimate highest opponent expected bid
    highest_expected = 0.0
    for opp_id, opp in alive_opponents.items():
        prev_trace = opp.get('previous_trace', {})
        prev_bid = prev_trace.get('bid') if prev_trace else None
        # Estimate opponent's maximum possible bid today
        opp_budget_approx = opp['budget'] + DAILY_SALARY  # assuming they got salary
        opp_max_bid = min(opp_budget_approx, DAILY_SALARY * 0.95)
        # Take previous bid as strong indicator if available, else use urgency
        if prev_bid is not None:
            expected = max(prev_bid, opp_max_bid * 0.7)
        else:
            # No history - assume they are desperate if low HP or no water
            if opp['hp
"""
