# ============================================================
# Experiment: exp_118
# Agent: Eric
# Source: exp_118
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
    
    # Check yesterday's highest bid from any alive opponent
    highest_prev_bid = None
    for opp_id, opp in opponents_status.items():
        if opp['alive']:
            prev = opp.get('previous_trace')
            if prev and prev.get('bid') is not None:
                if highest_prev_bid is None or prev['bid'] > highest_prev_bid:
                    highest_prev_bid = prev['bid']
    
    if highest_prev_bid is not None:
        # React to opponent history
        if hp <= 2:
            bid = min(budget, DAILY_SALARY * 0.9)
        else:
            bid = min(budget, max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5))
    else:
        # No opponent info: default strategy
        if hp <= 2:
            bid = min(budget, DAILY_SALARY * 0.8)
        else:
            bid = min(budget, DAILY_SALARY * 0.6)
    
    # Ensure bid is a float (as required by the game engine)
    return float(bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = int(day_context['day'])
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Get yesterday's highest bid from alive opponents
    highest_prev_bid = 0.0
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            highest_prev_bid = max(highest_prev_bid, float(prev['bid']))

    # Base bid: proportional to need and inverse of HP
    need_ratio = WATER_REQ / max(supply, 1e-9)
    hp_factor = 1.0 - (hp / 10.0)
    base_bid = need_ratio * DAILY_SALARY * hp_factor

    # Adjust based on no_water_days and HP
    if no_water_days >= 1 or hp <= 2:
        # Desperate: bid up to 90% of salary, but don't exceed highest_prev_bid+10
        target = min(DAILY_SALARY * 0.9, max(base_bid, highest_prev_bid + 1.0))
    else:
        # Normal: bid conservatively, try to beat highest_prev_bid by a small margin if possible
        if base_bid < highest_prev_bid + 2.0:
            target = min(DAILY_SALARY * 0.7, max(base_bid, highest_prev_bid + 1.5))
        else:
            target = base_bid

    # Ensure bid does not exceed budget and is non-negative
    bid = max(0.0, min(budget, target))
    return bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']
    
    alive_opponents = {aid: o for aid, o in opponents_status.items() if o['alive']}
    num_alive = len(alive_opponents)
    
    # Base bid: percentage of salary based on supply/competition
    # Expected supply per alive agent (including self)
    agents_total = num_alive + 1
    supply_per_agent = supply / agents_total
    
    # If supply per agent is less than required, we need to compete harder
    if supply_per_agent < WATER_REQ:
        base_ratio = 0.75
    else:
        base_ratio = 0.55
    
    # Adjust for HP desperation
    if hp <= 2 or no_water_days >= 1:
        base_ratio = min(0.95, base_ratio + 0.2)
    elif hp <= 4:
        base_ratio = min(0.85, base_ratio + 0.1)
    
    # Check yesterday's opponent bids for pressure
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and 'bid' in prev and prev['bid'] is not None:
            yesterday_bids.append(prev['bid'])
    
    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
        # If opponents bid very high yesterday, they might be aggressive -> we can undercut or match cautiously
        if max_yesterday >= DAILY_SALARY * 0.9:
            # high pressure, but we might not need to go that high if we have hp
            if hp > 3:
                base_ratio = min(base_ratio, 0.6)
            else:
                base_ratio = min(base_ratio + 0.1, 0.95)
        elif max_yesterday < DAILY_SALARY * 0.4:
            # opponents are low, we can bid low to save
            base_ratio = min(base_ratio, 0.5)
    
    bid = DAILY_SALARY * base_ratio
    # Ensure bid is within budget and non-negative
    bid = max(0, min(budget, bid))
    # Round to 2 decimals for realism
    return round(bid, 2)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25
    budget = my_status['budget']
    hp = my_status['hp']
    supply = day_context['supply']
    day = day_context['day']

    alive_opponents = {k: v for k, v in opponents_status.items() if v['alive']}

    # Get yesterday's highest bid from alive opponents
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Base decision on HP
    if hp <= 2:
        # Critical need: bid high to ensure water
        bid = min(budget, DAILY_SALARY * 1.0)
        return int(bid)

    # If we have good HP, be more strategic
    # Determine target bid based on yesterday's max
    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
        # Outbid by a small margin, but not too high
        target = max_yesterday + 2.0  # slightly above
    else:
        # No information: use conservative baseline
        target = DAILY_SALARY * 0.6

    # Adjust based on supply scarcity
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    # When supply is low, need to bid higher
    if supply_ratio < 0.3:
        target *= 1.3
    elif supply_ratio > 0.7:
        target *= 0.85  # surplus, can save

    # Ensure we don't exceed budget
    bid = min(budget, target)
    # Also ensure we don't go too low if we have good hp
    # But if hp is high, we can try to save
    # Minimum bid to stay safe: at least 0.3 * daily_salary if hp > 5
    if hp > 5 and bid < DAILY_SALARY * 0.3:
        bid = DAILY_SALARY * 0.3

    return int(bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    alive_opp = [o for o in opponents_status.values() if o.get('alive', False)]
    prev_bids = []
    for opp in alive_opp:
        trace = opp.get('previous_trace', {})
        if trace and trace.get('bid') is not None:
            prev_bids.append(trace['bid'])
    max_prev_bid = max(prev_bids) if prev_bids else 0

    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if hp <= 2 or no_water_days > 0:
        base_bid = min(budget, DAILY_SALARY * 0.9)
    elif hp <= 5:
        base_bid = min(budget, DAILY_SALARY * 0.7)
    else:
        base_bid = min(budget, DAILY_SALARY * 0.55)

    # Adjust based on opponent pressure
    if max_prev_bid > DAILY_SALARY * 0.8:
        target = max(base_bid, max_prev_bid + 1.0)
    elif max_prev_bid > DAILY_SALARY * 0.5:
        target = max(base_bid, max_prev_bid * 0.9)
    else:
        target = base_bid

    return min(budget, max(target, 1.0))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply']) if day_context['supply'] else 0
    day = int(day_context['day']) if day_context['day'] else 0
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Filter alive opponents
    alive_opponents = [o for o in opponents_status.values() if o['alive']]

    # Collect yesterday's bids from alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(float(prev['bid']))

    # Determine base water need
    if no_water_days > 0 or hp <= 2:
        # Desperate: must get water
        target_bid = DAILY_SALARY * 0.9
    elif hp <= 4:
        target_bid = DAILY_SALARY * 0.7
    else:
        target_bid = DAILY_SALARY * 0.4

    # Adjust based on supply scarcity
    if supply < 20:
        target_bid *= 1.3
    elif supply > 22:
        target_bid *= 0.8

    # Consider opponents' aggressive bids
    if yesterday_bids:
        max_yesterday = max(yesterday_bids)
        # If opponents were very high yesterday, we don't need to match if HP good
        if max_yesterday > DAILY_SALARY * 0.8 and hp > 4:
            target_bid = min(target_bid, DAILY_SALARY * 0.5)
        else:
            # Slightly outbid the max yesterday if we need water
            if hp <= 3:
                target_bid = max(target_bid, max_yesterday + 1)

    # Ensure we never exceed budget or daily salary
    final_bid = min(budget, DAILY_SALARY, target_bid)
    # Ensure non-negative
    final_bid = max(final_bid, 0.0)
    return final_bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    return 15.0
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    SALARY = 140
    supply = int(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    # base bid based on desperation
    if hp <= 2:
        base = 0.9 * SALARY
    elif no_water_days > 0:
        base = 0.8 * SALARY
    else:
        base = 0.6 * SALARY

    alive = {aid: opp for aid, opp in opponents_status.items() if opp['alive']}
    if alive:
        max_prev_bid = 0.0
        max_prev_budget = 0.0
        for opp in alive.values():
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                b = prev['bid']
                if b > max_prev_bid:
                    max_prev_bid = b
                    max_prev_budget = prev.get('budget_after', 0)

        if max_prev_bid > 0:
            if max_prev_bid >= 0.85 * SALARY and max_prev_budget < 2 * SALARY:
                # high spender now broke – we can lower
                pass
            elif max_prev_bid < 0.5 * SALARY and max_prev_budget > 3 * SALARY:
                # low spender with money – might jump
                base = min(base + 15, 0.85 * SALARY)
            else:
                # typical – undercut slightly
                base = max(base, max_prev_bid - 5)

    final = max(min(base, budget), 0.0)
    return final
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 8
    DAILY_SALARY = 140
    supply = int(day_context['supply'])
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    
    # Get alive opponents and their previous bids
    alive_opponents = {oid: opp for oid, opp in opponents_status.items() if opp['alive']}
    yesterday_bids = []
    for opp in alive_opponents.values():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
    
    # Ensure at least one water unit if supply enough
    max_possible_units = supply // WATER_REQ
    if max_possible_units == 0:
        # Very low supply, need to bid high
        if hp <= 3:
            bid = min(budget, DAILY_SALARY * 0.9)
        else:
            bid = min(budget, DAILY_SALARY * 0.5)
        return max(bid, 0.5)
    
    # Base bid calculation
    if day == 1:
        # First day, moderate bid based on supply
        if hp <= 3:
            bid = min(budget, DAILY_SALARY * 0.7)
        else:
            # supply typical 20 -> 2 units, bid enough to win one
            bid = min(budget, DAILY_SALARY * 0.4)
        return max(bid, 1.0)
    
    # From day 2, use yesterday bids
    if yesterday_bids:
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)
        highest_prev = max(yesterday_bids)
        # If we are low on HP, outbid the highest by a safe margin
        if hp <= 3:
            target = max(highest_prev + 2.0, DAILY_SALARY * 0.8)
        else:
            # Conservative: bid slightly above average to win at lowest cost
            target = max(avg_prev_bid + 1.5, DAILY_SALARY * 0.3)
        # Ensure we don't overpay relative to budget
        bid = min(budget, target)
        # Floor at 0.5
        if bid < 0.5:
            bid = 0.5
        return bid
    else:
        # No previous bid info (should not happen often)
        if hp <= 3:
            return min(budget, DAILY_SALARY * 0.85)
        else:
            return min(budget, DAILY_SALARY * 0.45)
"""
