# ============================================================
# Experiment: exp_058
# Agent: Bob
# Source: exp_058
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append(o)

    # If no opponents, bid conservatively but ensure we can meet requirement.
    if not alive_opponents:
        target = min(my_status['budget'], DAILY_SALARY * 0.35)
        return max(0.0, float(target))

    # Read yesterday bids from immediate previous_trace only.
    prev_bids = []
    for o in alive_opponents:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate how aggressive opponents are.
    if prev_bids:
        highest_prev = max(prev_bids)
        lowest_prev = min(prev_bids)
        # median without heavy history; compute from current list only.
        sorted_b = sorted(prev_bids)
        n = len(sorted_b)
        if n % 2 == 1:
            median_prev = sorted_b[int(n // 2)]
        else:
            median_prev = 0.5 * (sorted_b[int(n // 2) - 1] + sorted_b[int(n // 2)])
    else:
        highest_prev = 0.0
        lowest_prev = 0.0
        median_prev = DAILY_SALARY * 0.5

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Supply pressure: closer to MIN_SUPPLY means tighter water, so bid more.
    # Map supply in [15,25] -> pressure in [1.2,0.8]
    if MAX_SUPPLY > MIN_SUPPLY:
        t = (supply - float(MIN_SUPPLY)) / (float(MAX_SUPPLY - MIN_SUPPLY))
    else:
        t = 0.5
    pressure_mult = 1.2 - 0.4 * float(t)

    # If we are in danger, overbid to avoid another no-water day.
    danger = (hp <= 2.0) or (no_water_days >= 2)

    # If opponents were extremely aggressive yesterday, expect continuation.
    if highest_prev >= DAILY_SALARY * 0.85:
        if danger:
            bid = DAILY_SALARY * 0.95 * pressure_mult
        else:
            # Shade but still contest.
            bid = max(DAILY_SALARY * 0.45, highest_prev + 1.0) * 0.85 * pressure_mult
    else:
        # Otherwise, bid slightly above median to win share without wasting.
        # If their lowest was very low, we can bid closer to that.
        base = median_prev
        if lowest_prev > 0.0:
            base = 0.6 * median_prev + 0.4 * lowest_prev
        bid = (base + 1.5) * 0.9 * pressure_mult
        if danger:
            bid *= 1.25

    # Ensure bid is within budget and non-negative.
    bid = float(bid)
    if bid < 0.0:
        bid = 0.0
    bid = min(bid, budget)

    # If budget is too low, bid whatever we can.
    if budget <= DAILY_SALARY * 0.2:
        return max(0.0, budget)

    # Keep bid from going excessively high; still contest.
    cap = min(budget, DAILY_SALARY * (0.95 if danger else 0.75) * pressure_mult)
    bid = min(bid, cap)

    return float(bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context['supply'])
    day = day_context['day']

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    alive_opps = []
    for k, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday's bid pressure from previous_trace
    prev_bids = []
    for o in alive_opps:
        pt = o.get('previous_trace', {})
        b = pt.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate how many water units supply can cover for us
    # (only used to scale bid strength; indices not needed)
    water_units = supply / WATER_REQ

    # If yesterday saw very aggressive bidding, exploit by not matching unless we are safe.
    aggressive = highest_prev_bid >= DAILY_SALARY * 0.85

    # Base bid target depending on supply and our HP
    # When supply is higher, we can afford to secure water with less relative risk.
    supply_factor = 0.45
    if supply >= 22.0:
        supply_factor = 0.62
    elif supply >= 18.0:
        supply_factor = 0.52

    if hp <= 2.0:
        # Critical: prioritize survival.
        target = DAILY_SALARY * 0.9
    elif aggressive:
        # Opponents overbidding: bid moderately to avoid budget burn.
        target = DAILY_SALARY * (0.35 if hp > 4.0 else 0.6)
    else:
        # Normal: bid around a supply-scaled fraction.
        target = DAILY_SALARY * supply_factor

    # If our budget is low, scale down to avoid early bankruptcy.
    if budget <= DAILY_SALARY * 0.4:
        target *= 0.7

    # Final clamp
    bid = min(budget, target)

    # Ensure non-negative
    if bid < 0.0:
        bid = 0.0

    return bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    # Alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # Immediate reaction from yesterday's trace
    yesterday_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', None)
        if isinstance(prev, dict):
            # previous_trace is specified as containing yesterday behavior fields; bid is in dict
            b = prev.get('bid', None)
            if b is not None:
                try:
                    yesterday_bids.append(float(b))
                except Exception:
                    pass
        elif isinstance(prev, list):
            # Fallback if provided as list of entries
            for entry in prev:
                if isinstance(entry, dict) and 'bid' in entry and entry['bid'] is not None:
                    try:
                        yesterday_bids.append(float(entry['bid']))
                    except Exception:
                        pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how many water units we can/should aim for given supply and requirement.
    # We bid for a share; use supply band to set aggressiveness.
    # When supply is closer to 15, competition likely increases; bid higher.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Base bid: keep enough budget for late days.
    # If low hp/no_water_days, increase urgency.
    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Urgency factor
    urgency = 0.0
    if hp <= 2:
        urgency += 0.6
    elif hp <= 4:
        urgency += 0.35
    if no_water_days >= 2:
        urgency += 0.25

    # Pressure from opponent yesterday
    # Alex/Eric were bidding around 105-113; use that as a target threshold.
    pressure = 0.0
    if highest_prev_bid >= DAILY_SALARY * 0.9:  # ~81
        pressure += 0.35
    if highest_prev_bid >= DAILY_SALARY * 1.15:  # ~103.5
        pressure += 0.25

    # Determine target bid level
    # If pressure high, slightly undercut/meet their likely range.
    if highest_prev_bid > 0:
        target = min(DAILY_SALARY * 1.35, highest_prev_bid + 2.0)
    else:
        target = DAILY_SALARY * (0.50 + 0.25 * (1.0 - supply_ratio))

    # Adjust by urgency and supply scarcity
    target *= (1.0 + urgency)
    target *= (1.0 + 0.15 * (1.0 - supply_ratio))

    # Keep within budget and also avoid overbidding too much early
    # Late in episode, become more aggressive.
    days_left = max(0, 10 - day)
    late_factor = 1.0
    if days_left <= 3:
        late_factor = 1.25
    elif days_left <= 6:
        late_factor = 1.10

    target *= late_factor

    # Final cap: don't exceed budget or a reasonable fraction of remaining budget.
    # If budget is low, just bid what we can.
    max_reasonable = max(DAILY_SALARY * 0.95, DAILY_SALARY * 1.35)
    bid = min(budget, target)

    # If budget is extremely low, bid minimally but not zero if we need survival.
    if bid <= 0.0:
        bid = 0.0

    # Ensure we don't bid more than we can afford and keep some reserve.
    # Reserve fraction depends on urgency.
    reserve_frac = 0.25 if urgency >= 0.4 else 0.45
    if budget > 0:
        bid = min(bid, budget * (1.0 - reserve_frac) + 0.0)

    # If we are in critical danger, allow higher spend.
    if hp <= 2 or no_water_days >= 3:
        bid = min(budget, max(bid, DAILY_SALARY * 0.9))

    return float(bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    if not alive_opponents:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from immediate previous_trace only.
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how aggressive others were: if someone bid extremely high yesterday,
    # they likely needed water urgently and may keep bidding high.
    urgent_threshold = DAILY_SALARY * 0.85  # 76.5

    # Base bid depends on our urgency.
    if hp <= 2 or no_water_days >= 2:
        urgency_factor = 0.92
    elif hp <= 4 or no_water_days == 1:
        urgency_factor = 0.72
    else:
        urgency_factor = 0.55

    # Supply pressure: lower supply increases competition.
    # Normalize into [0,1] where 0 => MIN_SUPPLY, 1 => MAX_SUPPLY.
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_norm = 0.5
    supply_pressure = 1.0 - max(0.0, min(1.0, supply_norm))  # more pressure when supply is low

    # If highest_prev_bid was huge, we slightly overbid to avoid being outcompeted.
    if highest_prev_bid >= urgent_threshold:
        target = DAILY_SALARY * (0.35 + 0.35 * supply_pressure)  # ~0.35-0.70 of salary
    else:
        target = DAILY_SALARY * (0.28 + 0.30 * supply_pressure)  # ~0.28-0.58

    target = target * urgency_factor

    # Also, if our budget is low, cap strongly to avoid going to 0 early.
    # Keep enough for later days: reserve about 20% of remaining budget.
    reserve = 0.2 * budget
    max_affordable = max(0.0, budget - reserve)

    # Ensure we bid at least a small amount if we are at risk.
    min_bid = 5.0 if (hp <= 4 or no_water_days >= 1) else 2.0

    bid = min(max_affordable, target)
    bid = max(min_bid, bid)

    # Absolute safety cap: never exceed what we can pay.
    bid = min(bid, budget)
    return float(bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday bids only from previous_trace (immediate reaction)
    prev_bids = []
    prev_hp_after = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        if prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass
        if prev.get('hp_after') is not None:
            try:
                prev_hp_after.append(float(prev['hp_after']))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    # Estimate required aggressiveness: if someone bid high yesterday, match; if bids were low, slightly overcut.
    # Also react to my own hp/no-water pressure.
    pressure = 0.0
    if hp <= 2:
        pressure += 1.0
    if no_water_days >= 2:
        pressure += 0.7
    if hp <= 0:
        pressure += 2.0

    # Supply factor: more supply means water is easier; bid lower.
    # Ensure indices are integer-safe if we used arrays; here we just compute thresholds.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Base bid target
    # If yesterday's highest bid was strong, we need to contest.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        base = DAILY_SALARY * (0.65 + 0.25 * pressure)
        target = max(base, highest_prev_bid + 2.0)
    else:
        # If highest bid was not that high, exploit underbidding: bid just above avg/highest.
        target = max(avg_prev_bid + 3.0, highest_prev_bid + 2.0)
        # Adjust for my pressure and supply
        target *= (0.85 + 0.25 * pressure)
        target *= (0.95 - 0.15 * supply_ratio)

    # Clamp to budget and practical bounds
    target = max(0.0, target)

    # If my hp is critical, spend more (but never exceed budget)
    if hp <= 3:
        target = max(target, DAILY_SALARY * 0.9)

    # If I have plenty of budget and early/mid game, be slightly more aggressive
    if day <= 5 and budget > DAILY_SALARY * 1.2:
        target *= 1.05

    bid = min(budget, target)

    # Ensure we never bid negative and keep at least a small amount if budget allows
    if bid < 1e-6:
        bid = min(budget, DAILY_SALARY * 0.2)

    return float(bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive = []
    for _aid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append(o)

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace (immediate reaction only)
    yesterday_bids = []
    for o in alive:
        prev = o.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    yesterday_bids.append(float(b))
                except Exception:
                    pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    # Supply pressure: fewer units => higher chance of water shortage => bid more
    # Approximate number of
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    my_hp = my_status.get('hp', 0)
    my_budget = my_status.get('budget', 0.0)
    my_no_water_days = my_status.get('no_water_days', 0)

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return float(min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace for immediate reaction
    prev_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    # Supply pressure: if supply is near minimum, contest is more valuable
    # Ensure indices are int even if used; here we only compute a scalar.
    supply_ratio = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_ratio = (float(supply) - float(MIN_SUPPLY)) / (float(MAX_SUPPLY) - float(MIN_SUPPLY))
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Determine a target bid band based on yesterday aggressiveness
    # Yesterday: Alex/Cindy bid high (~76–81 avg), David low (~32), Eric died with ~6.
    # We exploit by bidding enough to beat the high bidders when they were active,
    # but not matching their max if our hp is comfortable.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Very aggressive lobby yesterday
        if my_hp <= 2 or my_no_water_days >= 1:
            target = DAILY_SALARY * 0.95
        else:
            target = max(DAILY_SALARY * 0.55, highest_prev_bid * 0.92)
    elif avg_prev_bid >= DAILY_SALARY * 0.7:
        # Moderately aggressive
        if my_hp <= 2 or my_no_water_days >= 1:
            target = DAILY_SALARY * 0.75
        else:
            target = max(DAILY_SALARY * 0.45, avg_prev_bid * 0.95)
    else:
        # Mostly low bids yesterday (like David)
        if my_hp <= 2 or my_no_water_days >= 1:
            target = DAILY_SALARY * 0.65
        else:
            target = max(DAILY_SALARY * 0.38, avg_prev_bid * 0.8)

    # Adjust for current supply: lower supply => slightly higher bid to secure survival
    # supply_ratio=0 at MIN_SUPPLY, 1 at MAX_SUPPLY
    target *= (1.15 - 0.3 * supply_ratio)

    # Budget safety: don't overcommit; also avoid bidding so low that we likely lose when hp is critical
    # If hp is high, cap bid to preserve budget.
    if my_hp >= 8:
        cap = DAILY_SALARY * 0.6
    elif my_hp >= 5:
        cap = DAILY_SALARY * 0.75
    else:
        cap = DAILY_SALARY * 0.95

    # Ensure we don't bid more than budget
    bid = float(min(my_budget, min(cap, target)))

    # If critical, enforce a minimum bid to avoid starvation
    if my_hp <= 2 or my_no_water_days >= 2:
        bid = float(min(my_budget, max(bid, DAILY_SALARY * 0.7)))

    # Avoid zero bids
    if bid < 0.0:
        bid = 0.0

    return bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Extract yesterday bids from previous_trace
    prev_bids = []
    prev_info = {}
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                b_val = float(b)
            except Exception:
                continue
            prev_bids.append(b_val)
            prev_info[oid] = b_val

    # Pressure signal from yesterday
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    # Base bid: aim to secure water but not match extreme bids
    # If supply is low, competition likely higher -> bid more.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # If we are in danger, bid aggressively.
    if my_hp <= 2 or my_no_water_days >= 2:
        target = DAILY_SALARY * 0.95
    else:
        # Moderate aggressiveness; escalate if others were bidding very high.
        if highest_prev_bid >= DAILY_SALARY * 1.2:
            # Cindy-like behavior: others overbid; we slightly undercut.
            target = min(DAILY_SALARY * 0.75 + (highest_prev_bid - DAILY_SALARY * 1.2) * 0.15, DAILY_SALARY * 0.95)
        elif highest_prev_bid >= DAILY_SALARY * 0.9:
            target = DAILY_SALARY * (0.6 + 0.2 * (1.0 - supply_ratio))
        else:
            target = DAILY_SALARY * (0.5 + 0.15 * (1.0 - supply_ratio))

    # Ensure we don't bid beyond budget.
    bid = min(my_budget, target)

    # If we have very low budget, conserve.
    if my_budget <= DAILY_SALARY * 0.35:
        bid = min(bid, my_budget)

    # Small adjustment: if yesterday we saw at least one opponent survive with high bids,
    # add a little to avoid being outcompeted.
    if prev_bids and avg_prev_bid >= DAILY_SALARY * 1.0 and my_hp >= 4:
        bid = min(my_budget, bid + DAILY_SALARY * 0.05)

    # Final clamp to reasonable range.
    if bid < 0.0:
        bid = 0.0
    return float(bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # If no one alive, bid minimal to conserve budget
    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Read yesterday bids from previous_trace only
    prev_bids = []
    prev_hp_after = []
    for oid, o in alive_opps:
        pt = o.get('previous_trace', {})
        if pt and pt.get('bid') is not None:
            try:
                prev_bids.append(float(pt['bid']))
                prev_hp_after.append(float(pt.get('hp_after', o.get('hp', 0))))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    # Also estimate how many were pressured: count of very high bids
    high_bid_count = 0
    for b in prev_bids:
        if b >= DAILY_SALARY * 1.2:
            high_bid_count += 1

    # Determine target bid based on supply pressure and opponent aggression
    # If supply is low, we must secure water more reliably.
    # supply_range is [15,25]; water allocation likely depends on bid.
    supply_ratio = 0.0
    try:
        supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    except Exception:
        supply_ratio = 0.5

    # Base aggressiveness: mid-tier
    # At low supply_ratio -> bid higher.
    base = DAILY_SALARY * (0.62 + (1.0 - supply_ratio) * 0.25)

    # If someone already went very high yesterday, avoid full matching but respond if my HP is low.
    if highest_prev_bid >= DAILY_SALARY * 1.5:
        if my_status['hp'] <= 2:
            target = DAILY_SALARY * 0.95
        elif my_status['hp'] <= 4:
            target = max(base, DAILY_SALARY * 0.75)
        else:
            # Don't overpay; try to win with slightly above base
            target = max(base, DAILY_SALARY * 0.68)
    else:
        # Moderate bids yesterday: bid near base.
        if my_status['hp'] <= 2:
            target = max(base, DAILY_SALARY * 0.9)
        elif my_status['hp'] <= 4:
            target = max(base, DAILY_SALARY * 0.75)
        else:
            target = base

    # If my no_water_days is high, I must secure water now.
    no_water_days = int(my_status.get('no_water_days', 0))
    if no_water_days >= 2:
        target = max(target, DAILY_SALARY * 0.9)
    if no_water_days >= 3:
        target = max(target, DAILY_SALARY * 1.05)

    # Budget cap
    budget = float(my_status.get('budget', 0.0))
    if budget <= 0:
        return 0.0

    # Ensure we don't bid above what we can pay
    bid = min(budget, target)

    # Small adjustment: if multiple opponents bid high yesterday, slightly increase
    if high_bid_count >= 2:
        bid = min(budget, bid * 1.08)

    # Keep bid non-negative
    if bid < 0:
        bid = 0.0

    return float(bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for oid, o in opponents_status.items():
        try:
            if o.get('alive', False):
                alive_opps.append(o)
        except Exception:
            continue

    # Baseline: conserve budget unless we're at risk
    if hp <= 2 or no_water_days >= 2:
        base_frac = 0.95
    elif hp <= 4 or no_water_days == 1:
        base_frac = 0.75
    else:
        base_frac = 0.55

    # Read yesterday bids from immediate trace to infer aggressive competitors
    prev_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    prev_bids.append(float(b))
                except Exception:
                    pass

    target_bid = None
    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / float(len(prev_bids))

        # If they were bidding near salary, we undercut slightly unless very safe
        if highest_prev >= 0.85 * DAILY_SALARY:
            if hp > 4:
                target_bid = 0.70 * DAILY_SALARY
            else:
                target_bid = 0.92 * DAILY_SALARY
        else:
            # Otherwise, bid around their average but slightly lower to win share cheaply
            target_bid = max(0.45 * DAILY_SALARY, avg_prev - 8.0)

    # Supply scaling: with higher supply, we can bid a bit less
    # Normalize supply to [0,1]
    denom = float(MAX_SUPPLY - MIN_SUPPLY)
    if denom <= 0:
        supply_norm = 0.5
    else:
        supply_norm = (supply - float(MIN_SUPPLY)) / denom
        if supply_norm < 0.0:
            supply_norm = 0.0
        if supply_norm > 1.0:
            supply_norm = 1.0

    supply_adjust = 1.0 - 0.15 * supply_norm  # bid slightly less when supply is high

    if target_bid is None:
        bid = base_frac * DAILY_SALARY * supply_adjust
    else:
        # Blend: ensure we respect our risk level
        risk_bid = base_frac * DAILY_SALARY * supply_adjust
        bid = 0.65 * risk_bid + 0.35 * float(target_bid)

    # Keep within budget and avoid bidding negative
    if budget <= 0:
        return 0.0

    if bid > budget:
        bid = budget
    if bid < 0.0:
        bid = 0.0

    # If supply is extremely low relative to WATER_REQ, ensure we bid enough to avoid starvation
    # (use integer thresholding carefully)
    # Approx water units available: supply / WATER_REQ
    water_units = supply / float(WATER_REQ)
    if water_units < 1.3:
        min_emergency = 0.85 * DAILY_SALARY
        if hp <= 3 and bid < min_emergency:
            bid = min_emergency
        if bid > budget:
            bid = budget

    return float(bid)
"""
