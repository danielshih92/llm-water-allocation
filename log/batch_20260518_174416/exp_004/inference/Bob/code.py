# ============================================================
# Experiment: exp_004
# Agent: Bob
# Source: exp_004
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

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    # Identify alive opponents and read their yesterday bids
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        return min(my_status.get('budget', 0), DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            yesterday_bids.append(float(b))

    # Base urgency from our hp and no-water days
    my_hp = my_status.get('hp', 0)
    my_no_water = my_status.get('no_water_days', 0)
    budget = my_status.get('budget', 0)

    # Estimate how scarce water is today
    # Use supply to decide aggressiveness: lower supply => higher chance others bid more.
    # Avoid float indexing; no lists used.
    scarcity = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        scarcity = (float(MAX_SUPPLY) - float(supply)) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    # If we have been starving, increase bid to avoid imminent death
    starving = (my_no_water >= 2) or (my_hp <= 2)

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / float(len(yesterday_bids))

        # High urgency opponents: bid to secure water share
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # If we're in danger, bid very high; else moderate-high.
            if starving or my_hp <= 3:
                bid = DAILY_SALARY * (0.85 + 0.15 * scarcity)
            else:
                bid = DAILY_SALARY * (0.65 + 0.20 * scarcity)

        # Medium urgency: slightly outbid average
        elif highest_prev_bid >= DAILY_SALARY * 0.55:
            # Add a small premium to beat likely second-price dynamics
            bid = max(highest_prev_bid + 1.5, DAILY_SALARY * (0.45 + 0.20 * scarcity))

        # Low urgency: conserve budget unless we're starving
        else:
            if starving:
                bid = DAILY_SALARY * (0.75 + 0.10 * scarcity)
            else:
                # Underbid to keep cost low
                bid = max(DAILY_SALARY * (0.28 + 0.15 * scarcity), avg_prev_bid * 0.9)

    else:
        # No trace bids available: use our own state and scarcity
        if starving:
            bid = DAILY_SALARY * (0.75 + 0.10 * scarcity)
        else:
            bid = DAILY_SALARY * (0.40 + 0.15 * scarcity)

    # Convert bid into a feasible amount: cannot exceed budget
    bid = float(bid)
    if bid < 0.0:
        bid = 0.0
    bid = min(bid, float(budget))

    # If budget is very low, bid whatever we can
    if bid <= 0.0:
        return 0.0

    return bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = day_context.get('supply', 0)
    day = day_context.get('day', 0)

    hp = my_status.get('hp', 0)
    budget = my_status.get('budget', 0)
    no_water_days = my_status.get('no_water_days', 0)

    alive_opponents = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Reaction to yesterday bids (only immediate trace)
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev.get('bid'))

    highest_prev_bid = max(prev_bids) if prev_bids else 0

    # Estimate how many water units are needed vs available.
    # We aim to secure at least 1 unit when possible.
    supply_units = int(supply / WATER_REQ) if WATER_REQ > 0 else 0

    # Base aggressiveness: if someone bid very high yesterday, we slightly outbid but cap spending.
    # Cindy's behavior indicates willingness to spend; we avoid matching extreme bids.
    if highest_prev_bid >= DAILY_SALARY * 6:  # very high spending yesterday
        base = DAILY_SALARY * 0.75
    elif highest_prev_bid >= DAILY_SALARY * 1.2:
        base = DAILY_SALARY * 0.6
    else:
        base = DAILY_SALARY * 0.5

    # Urgency adjustments
    if hp <= 2:
        base *= 1.25
    elif hp <= 4:
        base *= 1.05

    # If we have already gone without water, increase pressure
    if no_water_days >= 2:
        base *= 1.15
    elif no_water_days >= 1:
        base *= 1.05

    # If supply is scarce, we need to bid more to secure water.
    if supply <= MIN_SUPPLY + 1:
        base *= 1.15
    elif supply >= MAX_SUPPLY - 1:
        base *= 0.9

    # If supply_units suggests we may not even get 1 full unit reliably, bid higher.
    if supply_units <= 1:
        base *= 1.1

    # Cap based on budget and survival horizon (10 days). Avoid bankrupting.
    # Keep a reserve to avoid getting stuck at 0 budget.
    reserve = DAILY_SALARY * 0.2
    max_affordable = max(0.0, budget - reserve)

    bid = min(max_affordable, base)

    # Ensure non-negative and at least a small competitive amount when we can.
    if bid < 1.0:
        bid = min(budget, DAILY_SALARY * 0.25)

    return float(max(0.0, bid))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = day_context['supply']
    day = day_context['day']

    # Identify alive opponents and read their yesterday bids only (immediate reaction)
    alive_opps = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            yesterday_bids.append(float(b))

    # Baseline: moderate bid to contest at mid supply
    # Scale with supply: higher supply => slightly lower bid since water is less scarce.
    supply_ratio = (float(supply) - float(MIN_SUPPLY)) / float(MAX_SUPPLY - MIN_SUPPLY)
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Estimate opponent pressure from yesterday
    pressure = 0.0
    if yesterday_bids:
        pressure = max(yesterday_bids)

    # If they were bidding aggressively yesterday (likely trying to secure water), match pressure but cap.
    # Observed: Alex/Cindy ~98-115; David/Eric low.
    if pressure >= DAILY_SALARY * 0.85:
        if my_status['hp'] > 3:
            target = DAILY_SALARY * 0.35 + (pressure * 0.15)
        else:
            target = DAILY_SALARY * 0.75 + (pressure * 0.10)
    else:
        # If no strong pressure, bid enough to be competitive but not waste budget.
        target = max(DAILY_SALARY * 0.45, pressure + 2.0)

    # Adjust with my urgency
    if my_status['hp'] <= 2:
        target *= 1.2
    elif my_status['hp'] <= 4:
        target *= 1.05

    # Adjust with no-water streak: if I'm close to running out, increase bid.
    if my_status.get('no_water_days', 0) >= 2:
        target *= 1.15

    # Supply adjustment: more supply => reduce slightly
    target *= (1.08 - 0.18 * supply_ratio)

    # Ensure we don't bid more than we can afford
    bid = float(min(my_status['budget'], target))

    # Also keep within a reasonable range relative to salary
    bid = float(max(DAILY_SALARY * 0.25, min(bid, DAILY_SALARY * 1.05)))

    return bid
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append((opp_id, opp))

    # If no opponents are alive, conserve.
    if not alive_opponents:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids (immediate reaction only).
    yesterday_bids = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Determine pressure from yesterday.
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_highest = 0.0
    if yesterday_bids:
        sorted_bids = sorted(yesterday_bids, reverse=True)
        if len(sorted_bids) > 1:
            second_highest = sorted_bids[1]

    # Estimate scarcity: higher supply reduces urgency.
    scarcity = 1.0 - (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0..1
    scarcity = max(0.0, min(1.0, scarcity))

    # Base bid: mid-high to outbid strong contenders, but not chase the very top.
    # Target slightly above the 2nd-highest when pressure is high.
    pressure = 0.0
    if highest_prev_bid > 0:
        pressure = min(1.0, highest_prev_bid / (DAILY_SALARY * 1.6))

    # If our hp is low or we have consecutive no-water days, we must secure water.
    urgent = (hp <= 3.0) or (no_water_days >= 2)

    if urgent:
        # Escalate aggressively but cap by budget.
        target = max(DAILY_SALARY * 0.75, second_highest + 2.0, highest_prev_bid * 0.92)
    else:
        # Non-urgent: bid enough to beat the mid/high pack.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            target = max(DAILY_SALARY * (0.55 + 0.2 * scarcity), second_highest + 1.5)
        else:
            target = max(DAILY_SALARY * (0.45 + 0.25 * scarcity), highest_prev_bid * 0.6)

    # Small strategic edge: if supply is tight, add a little.
    target *= (1.0 + 0.06 * scarcity)

    # Ensure within budget and non-negative.
    bid = max(0.0, min(budget, float(target)))

    # If budget is extremely low, still bid minimal to avoid total waste.
    if bid < 1e-6:
        bid = min(budget, DAILY_SALARY * 0.1)

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

    supply = day_context['supply']
    day = day_context['day']

    # Alive opponents and yesterday bids
    alive_opponents = []
    yesterday_bids = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append(o)
            prev = o.get('previous_trace', {}) or {}
            if prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])

    # If no opponents alive, spend conservatively
    if not alive_opponents:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.4))

    # Compute pressure from yesterday: who bid high
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    lowest_prev_bid = min(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how many water units are likely available today
    # Use int() to avoid float index issues if we ever bucket.
    # Here we only use it for a coarse scaling factor.
    units_available = int(supply / WATER_REQ) if WATER_REQ > 0 else 0

    # Base bid depends on supply scarcity
    # Scarce supply -> bid higher; abundant -> bid lower.
    scarcity_ratio = 0.0
    if MAX_SUPPLY > 0:
        scarcity_ratio = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - 0.0)
    scarcity_ratio = max(0.0, min(1.0, scarcity_ratio))

    # If my HP is critical, I must secure water
    my_hp = my_status.get('hp', 0)
    my_budget = my_status.get('budget', 0.0)
    no_water_days = my_status.get('no_water_days', 0)

    # Target bid logic:
    # - If others were bidding very high yesterday, they likely expect competition today.
    # - If others were bidding low (Eric), keep moderate to avoid wasting budget.
    # - Escalate when my HP/no_water_days are low.
    pressure_high = highest_prev_bid >= DAILY_SALARY * 0.85
    pressure_low = lowest_prev_bid <= DAILY_SALARY * 0.4

    # Decide a multiplier for bid
    if my_hp <= 2 or no_water_days >= 2:
        mult = 0.95 if pressure_high else 0.75
    elif my_hp <= 4 or no_water_days >= 1:
        mult = 0.70 if pressure_high else 0.55
    else:
        # Healthy: conserve unless competition pressure is high
        if pressure_high:
            mult = 0.60
        elif pressure_low:
            mult = 0.45
        else:
            mult = 0.52

    # Adjust for supply: fewer units -> more aggressive
    # If units_available is 0, supply < WATER_REQ, bid high to prevent starvation.
    if units_available <= 0:
        mult = min(1.0, mult + 0.25)
    elif units_available == 1:
        mult = min(1.0, mult + 0.10)
    else:
        mult = max(0.35, mult - 0.05)

    # Final bid capped by budget
    bid = my_budget
    desired = DAILY_SALARY * mult * (0.85 + 0.3 * scarcity_ratio)
    bid = min(my_budget, desired)

    # Ensure non-negative
    if bid < 0.0:
        bid = 0.0

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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opponents = [o for o in opponents_status.values() if o.get('alive', False)]

    # If no opponents, just bid conservatively.
    if not alive_opponents:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace to infer aggressiveness.
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Use the highest previous bid as a proxy for current bidding pressure.
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Determine how tight the supply is today.
    # If supply is near our requirement, we must secure water.
    tightness = 0.0
    if supply <= WATER_REQ:
        tightness = 1.0
    else:
        # Map supply in [WATER_REQ, MAX_SUPPLY] to [0,1]
        tightness = max(0.0, min(1.0, (MAX_SUPPLY - supply) / (MAX_SUPPLY - WATER_REQ)))

    # Budget safety: if we're low on budget, don't overcommit.
    # Keep a minimum reserve to survive multiple days.
    reserve_factor = 0.25
    reserve = reserve_factor * DAILY_SALARY * 1.5

    # Base target bid influenced by yesterday's aggressiveness and today tightness.
    # If others bid high yesterday, we match slightly above to secure allocation.
    # If others bid low, we bid around the minimum effective level.
    target = 0.0

    # Pressure from yesterday: normalize against DAILY_SALARY.
    pressure_ratio = highest_prev_bid / DAILY_SALARY if DAILY_SALARY > 0 else 0.0

    # Decide if we are in critical health/no-water streak.
    critical = (my_hp <= 3.0) or (my_no_water_days >= 2)

    # Compute a ceiling to avoid bankruptcy.
    # If critical, allow higher bids; otherwise keep tighter cap.
    if critical:
        cap = min(my_budget, DAILY_SALARY * 0.95)
    else:
        cap = min(my_budget, DAILY_SALARY * (0.55 + 0.25 * tightness))

    # If yesterday bids were very high, we must compete more.
    if pressure_ratio >= 1.0:
        # Match aggressiveness; add a small increment scaled by tightness.
        target = highest_prev_bid + (3.0 + 6.0 * tightness)
    elif pressure_ratio >= 0.85:
        target = max(DAILY_SALARY * (0.6 + 0.2 * tightness), highest_prev_bid + (2.0 + 4.0 * tightness))
    else:
        # Lower pressure: bid enough to likely win when tight.
        target = DAILY_SALARY * (0.45 + 0.35 * tightness)

    # Ensure we don't bid below a meaningful floor when tight.
    floor = DAILY_SALARY * (0.35 + 0.25 * tightness) if tightness > 0.2 else DAILY_SALARY * 0.25

    # Apply reserve constraint.
    max_affordable = max(0.0, my_budget - reserve)
    bid = min(cap, target, max_affordable)
    bid = max(bid, floor * 0.6)

    # Final clamp.
    if bid < 0.0:
        bid = 0.0
    if bid > my_budget:
        bid = my_budget

    return float(bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Determine alive opponents and extract yesterday bids
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.4))

    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Budget/HP pressure
    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Estimate how many water units might be available relative to our need.
    # Use supply range to decide whether to bid aggressively.
    supply_units = supply / float(WATER_REQ)  # may be ~1.67-2.78

    # If supply is tight (closer to 15), competition likely higher -> bid more.
    tight_supply = supply <= (MIN_SUPPLY + 0.5)

    # Strategy: moderate bid baseline; increase only when yesterday bids were extreme.
    extreme_market = highest_prev_bid >= DAILY_SALARY * 0.85

    # Base target bid depends on our hp and supply tightness.
    if my_hp <= 2 or no_water_days >= 1:
        base = DAILY_SALARY * (0.75 if not tight_supply else 0.9)
    else:
        base = DAILY_SALARY * (0.55 if not tight_supply else 0.7)

    # If others were bidding extremely high, we don't match fully; we step in slightly above baseline.
    if extreme_market:
        # Aim to beat typical bids without going to maximum.
        adjust = min(DAILY_SALARY * 0.15, max(0.0, highest_prev_bid * 0.05))
        target = base + adjust
    else:
        # When market was not extreme, bid closer to baseline.
        target = base

    # Convert target to a feasible bid bounded by our budget.
    # Keep a floor to avoid bidding 0 when alive.
    min_bid = 5.0
    bid = max(min_bid, min(my_budget, target))

    # If our budget is very low, bid just enough to try to survive today.
    if my_budget <= DAILY_SALARY * 0.25:
        bid = max(0.0, min(my_budget, DAILY_SALARY * 0.35))

    # Final clamp
    if bid < 0.0:
        bid = 0.0
    return float(bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = day_context['supply']
    day = day_context['day']

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive'):
            alive_opps.append(o)

    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Read yesterday bids from previous_trace for immediate reaction
    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid')
            if b is not None:
                yesterday_bids.append(float(b))

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate remaining water need urgency
    no_water_days = int(my_status.get('no_water_days', 0))
    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))

    # Base bid: aim to beat moderate bids but avoid Cindy/Eric-level max spending
    # Use supply to scale: when supply is near lower bound, competition likely higher.
    supply_norm = (float(supply) - 15.0) / (25.0 - 15.0)  # 0..1

    # If yesterday had very high bids, increase slightly but cap to protect budget.
    pressure = 0.0
    if highest_prev_bid > 0:
        pressure = min(1.0, highest_prev_bid / (DAILY_SALARY * 2.0))

    # Urgency multiplier: low hp or many no-water days => bid more
    urgency = 1.0
    if hp <= 2:
        urgency = 1.35
    elif hp <= 4:
        urgency = 1.18

    if no_water_days >= 2:
        urgency += 0.12

    # Target bid formula
    # - base around 0.55*salary
    # - add pressure and supply competition
    target = (DAILY_SALARY * (0.55 + 0.15 * pressure + 0.10 * supply_norm)) * urgency

    # If yesterday's highest bid was extreme, try to outbid only slightly (not full match)
    if highest_prev_bid >= DAILY_SALARY * 1.6:
        target = max(target, highest_prev_bid * 0.92)

    # If our hp is comfortable, reduce a bit to conserve budget
    if hp >= 8:
        target *= 0.85

    # Hard caps to avoid going broke
    # Keep enough for a few days: do not spend more than ~45% of current budget
    cap_by_budget = budget * 0.45
    # Also avoid bidding above a conservative cap relative to salary
    cap_by_salary = DAILY_SALARY * 1.55

    bid = min(target, cap_by_budget, cap_by_salary)

    # Ensure non-negative and at least small amount when budget allows
    if bid < 0:
        bid = 0.0

    # If budget is tiny, spend what we can
    if budget <= 5:
        return budget

    # Final clamp: at least 5% of salary if we can afford it
    min_affordable = min(budget, DAILY_SALARY * 0.05)
    if bid < min_affordable:
        bid = min_affordable

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

    # Identify alive opponents
    alive = []
    for k, o in opponents_status.items():
        if o.get('alive', False):
            alive.append(o)

    # If no opponents, bid to ensure our own survival
    if not alive:
        # Conservative: bid enough for at least one water day
        base = DAILY_SALARY * 0.5
        return float(min(my_status['budget'], max(0.0, base)))

    # Extract yesterday bids from traces for immediate reaction
    yesterday_bids = []
    for o in alive:
        prev = o.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Estimate how aggressive the field is
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / max(1, len(yesterday_bids))
    else:
        highest_prev_bid = 0.0
        avg_prev_bid = 0.0

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])

    # Supply pressure: higher supply reduces need to overbid
    # Normalize supply within [MIN_SUPPLY, MAX_SUPPLY]
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_norm = 0.5
    supply_norm = max(0.0, min(1.0, supply_norm))

    # Target bid logic:
    # - If opponents were bidding very high yesterday, we undercut slightly when healthy.
    # - If our hp is low, we join the aggressive bids to avoid death.
    # - Otherwise, bid around a mid level.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        if my_hp > 3:
            # Undercut: aim just below their max pressure
            target = highest_prev_bid * 0.92
        else:
            # Need to secure water
            target = max(highest_prev_bid * 0.98, DAILY_SALARY * 0.9)
    else:
        # Moderate field: bid near average, adjusted by our hp and supply
        hp_factor = 1.0
        if my_hp <= 2:
            hp_factor = 1.25
        elif my_hp <= 4:
            hp_factor = 1.12
        else:
            hp_factor = 0.95

        # If supply is high, reduce a bit; if low, increase a bit
        supply_factor = 0.85 + 0.3 * supply_norm  # low supply -> ~0.85, high -> ~1.15
        base = avg_prev_bid if avg_prev_bid > 0 else DAILY_SALARY * 0.55
        target = base * hp_factor * supply_factor

    # Ensure we never bid negative and respect budget
    target = float(max(0.0, target))

    # Safety cap: don't bid more than we can afford
    bid = min(my_budget, target)

    # If budget is extremely low, still bid something to avoid wasting chance
    if bid <= 0.0 and my_budget > 0.0:
        bid = min(my_budget, DAILY_SALARY * 0.2)

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

    my_hp = int(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    # Collect yesterday bids from alive opponents only (immediate reaction)
    alive_opponents = [o for o in opponents_status.values() if o.get('alive', False)]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        if prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Pressure signals
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = (sum(yesterday_bids) / len(yesterday_bids)) if yesterday_bids else 0.0

    # Estimate how many water units we can buy if we win at a given bid.
    # Assumption: allocation scales with bid share; we aim for at least 1 unit (9) when possible.
    # We'll convert supply to a rough scarcity factor.
    scarcity = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        scarcity = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    # Base bid depends on our survival risk
    # If we've already gone multiple no-water days or low hp, increase urgency.
    urgency = 0.0
    if my_hp <= 2:
        urgency = 1.0
    elif my_hp <= 4:
        urgency = 0.7
    else:
        urgency = 0.3

    if my_no_water_days >= 2:
        urgency = max(urgency, 0.8)
    elif my_no_water_days == 1:
        urgency = max(urgency, 0.55)

    # If opponents were bidding aggressively yesterday, we must match at least partially.
    # Observed: Cindy/David/Eric average ~93-117 with max ~147-151.
    opp_aggression = 0.0
    if highest_prev_bid >= DAILY_SALARY * 1.1:  # >= 99
        opp_aggression = 1.0
    elif highest_prev_bid >= DAILY_SALARY * 0.85:  # >= 76.5
        opp_aggression = 0.7
    elif highest_prev_bid >= DAILY_SALARY * 0.6:  # >= 54
        opp_aggression = 0.4
    else:
        opp_aggression = 0.2

    # Target bid fraction of daily salary.
    # Keep some budget for later; but react to scarcity and aggression.
    target_frac = 0.35 + 0.35 * urgency + 0.25 * scarcity + 0.25 * opp_aggression
    # Clamp
    target_frac = max(0.25, min(0.95, target_frac))

    # If supply is extremely low, bid more to secure water.
    if supply <= float(WATER_REQ) + 1.0:
        target_frac = max(target_frac, 0.75 if opp_aggression >= 0.7 else 0.6)

    # If we are in very good shape, bid less unless opponents were extremely high.
    if my_hp >= 8 and my_no_water_days == 0 and highest_prev_bid < DAILY_SALARY * 0.85:
        target_frac = min(target_frac, 0.45)

    bid = target_frac * DAILY_SALARY

    # Ensure we don't exceed budget
    bid = min(bid, my_budget)

    # If budget is tiny, still bid what we can.
    if my_budget <= 0:
        return 0.0

    # Add slight deterministic adjustment based on day to avoid ties.
    # (No randomness allowed; keep stable.)
    adjust = ((day % 5) - 2) * 1.5
    bid = bid + adjust

    # Final clamp
    bid = max(0.0, min(bid, my_budget))
    return float(bid)
"""
