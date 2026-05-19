# ============================================================
# Experiment: exp_111
# Agent: Bob
# Source: exp_111
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

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    # Identify alive opponents and extract yesterday bids
    alive_opponents = [o for o in opponents_status.values() if o.get('alive', False)]
    yesterday_bids = []
    yesterday_highest = None
    yesterday_second = None

    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                b_val = float(b)
            except Exception:
                continue
            yesterday_bids.append(b_val)

    if yesterday_bids:
        yesterday_bids.sort(reverse=True)
        yesterday_highest = yesterday_bids[0]
        yesterday_second = yesterday_bids[1] if len(yesterday_bids) > 1 else None

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Convert supply to an estimate of how many full water units are likely available per requirement.
    # We use this only to scale our aggressiveness.
    supply_units = supply / float(WATER_REQ) if WATER_REQ > 0 else 1.0

    # Aggression thresholds based on typical behavior: near salary => high pressure.
    high_pressure = (yesterday_highest is not None and yesterday_highest >= 0.85 * DAILY_SALARY)
    medium_pressure = (yesterday_highest is not None and yesterday_highest >= 0.60 * DAILY_SALARY)

    # Base bid: aim to secure at least one requirement when possible.
    # If our budget is low, cap aggressively.
    target_min = 0.0
    # If supply is low, increase willingness to bid.
    if supply <= float(MIN_SUPPLY) + 1e-9:
        target_min = 0.55 * DAILY_SALARY
    elif supply >= float(MAX_SUPPLY) - 1e-9:
        target_min = 0.35 * DAILY_SALARY
    else:
        # Interpolate between low and high supply
        t = (supply - float(MIN_SUPPLY)) / (float(MAX_SUPPLY) - float(MIN_SUPPLY))
        target_min = (0.55 - 0.20 * t) * DAILY_SALARY

    # HP/burn logic: if we are in danger, bid harder.
    danger = (hp <= 2.0) or (no_water_days >= 2)

    if not alive_opponents:
        # No one to compete: bid conservatively but enough to avoid starvation.
        bid = max(target_min * 0.5, 0.25 * DAILY_SALARY)
        return min(budget, bid)

    # If they bid very high yesterday, they likely anticipate scarcity and will continue.
    if high_pressure:
        if danger:
            bid = 0.95 * DAILY_SALARY
        else:
            # Slightly above their expected top bid but still budget-safe
            # Use yesterday_highest as anchor; add a small premium.
            premium = 0.08 * DAILY_SALARY
            bid = min(DAILY_SALARY, yesterday_highest + premium)
            # If supply is low, add more premium.
            if supply_units <= 2.0:
                bid = min(DAILY_SALARY, bid + 0.05 * DAILY_SALARY)
        return min(budget, bid)

    # If they bid moderately high, we match partially to avoid losing all water.
    if medium_pressure:
        if danger:
            bid = 0.75 * DAILY_SALARY
        else:
            # Match between target_min and their bid level.
            anchor = yesterday_highest if yesterday_highest is not None else target_min
            bid = 0.55 * anchor + 0.45 * target_min
            # If supply is low, increase.
            if supply_units <= 2.0:
                bid *= 1.15
        return min(budget, bid)

    # Low pressure yesterday: we can undercut slightly unless we're in danger.
    if danger:
        bid = 0.65 * DAILY_SALARY
    else:
        # Conservative: enough to stay in the game, but not to waste budget.
        # Use supply_units to decide: lower supply => bid more.
        if supply_units <= 1.9:
            bid = 0.50 * DAILY_SALARY
        elif supply_units <= 2.6:
            bid = 0.42 * DAILY_SALARY
        else:
            bid = 0.34 * DAILY_SALARY

        # If they had a second-highest bid, we can try to be slightly below it.
        if yesterday_second is not None:
            bid = min(bid, 0.92 * yesterday_second + 0.02 * DAILY_SALARY)

    return min(budget, bid)
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Alive opponents
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive'):
            alive.append((oid, o))

    # If no opponents, just bid conservatively
    if not alive:
        return max(0.0, min(float(my_status['budget']), DAILY_SALARY * 0.4))

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Read yesterday bids from traces (only immediate reaction)
    yesterday_bids = []
    for _, o in alive:
        prev = o.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = 0.0
    if len(yesterday_bids) >= 2:
        sorted_b = sorted(yesterday_bids, reverse=True)
        second_prev_bid = sorted_b[1]

    # Supply pressure: lower supply => more competitive
    # Map supply to a multiplier without indexing lists.
    if supply <= MIN_SUPPLY:
        supply_mult = 1.15
    elif supply >= MAX_SUPPLY:
        supply_mult = 0.95
    else:
        # Linear interpolation between 1.15 and 0.95
        supply_mult = 1.15 - (supply - MIN_SUPPLY) * (1.15 - 0.95) / (MAX_SUPPLY - MIN_SUPPLY)

    # If we are in danger of running out of water, bid harder.
    danger = 0
    if no_water_days >= 2:
        danger = 1
    if hp <= 2:
        danger = 2

    # Cindy/Eric were high bidders and survived; we should not be too low.
    # Target: slightly above the previous high bidder when in danger, otherwise just above a mid level.
    if danger == 2:
        target = max(highest_prev_bid * 1.02, second_prev_bid * 1.05, DAILY_SALARY * 0.85)
    elif danger == 1:
        target = max(second_prev_bid * 1.03, highest_prev_bid * 0.98, DAILY_SALARY * 0.70)
    else:
        # Not in immediate danger: bid enough to beat aggressive bidders but conserve.
        # Use a fraction of highest_prev_bid if they were extremely high.
        if highest_prev_bid >= DAILY_SALARY * 0.9:
            target = max(DAILY_SALARY * 0.62, highest_prev_bid * 0.80)
        else:
            target = max(DAILY_SALARY * 0.55, highest_prev_bid + 1.5)

    # Convert target to a budget-limited bid.
    # Also cap to avoid bankrupting ourselves unnecessarily.
    cap = max(0.0, budget)
    # Soft cap: never bid more than 1.0 salary unless in extreme danger.
    if danger == 0:
        cap = min(cap, DAILY_SALARY * 0.75)
    elif danger == 1:
        cap = min(cap, DAILY_SALARY * 0.95)
    else:
        cap = min(cap, DAILY_SALARY * 1.10)

    bid = min(cap, target * supply_mult)

    # Ensure non-negative
    if bid < 0.0:
        bid = 0.0

    return float(bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive'):
            alive_opps.append((oid, o))

    # If no opponents, just ensure survival.
    if not alive_opps:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Read yesterday trace bids for immediate pressure.
    prev_bids = []
    prev_max_bid = 0.0
    prev_min_bid = None
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            b = float(prev['bid'])
            prev_bids.append(b)
            if b > prev_max_bid:
                prev_max_bid = b
            if prev_min_bid is None or b < prev_min_bid:
                prev_min_bid = b

    # Estimate how many water units are likely available.
    # (We don't know exact auction mechanics; use supply to decide urgency.)
    # If supply is low relative to our requirement, we must bid more.
    supply_ratio = supply / float(WATER_REQ)  # e.g., 15/9=1.67

    # Base bid: aim to beat the likely aggressive player without going all-in.
    # Use yesterday's max bid as a proxy for market clearing pressure.
    if prev_bids:
        # If someone already bid very high, we increase but not to full parity.
        if prev_max_bid >= DAILY_SALARY * 1.25:
            target = prev_max_bid * 0.92
        elif prev_max_bid >= DAILY_SALARY * 0.9:
            target = max(DAILY_SALARY * 0.65, prev_max_bid * 0.85)
        else:
            target = max(DAILY_SALARY * 0.55, prev_max_bid + 2.0)
    else:
        target = DAILY_SALARY * 0.55

    # Adjust for our urgency.
    if my_hp <= 2.0 or my_no_water_days >= 2:
        target *= 1.25
    elif my_hp >= 6.0 and my_no_water_days == 0:
        target *= 0.85

    # Adjust for supply conditions.
    # Lower supply => higher chance we need to secure water.
    if supply_ratio < 1.2:
        target *= 1.25
    elif supply_ratio > 1.8:
        target *= 0.9

    # Clamp to feasible budget.
    # Also avoid irrationally high bids: keep within a fraction of budget and a soft cap.
    soft_cap = min(my_budget, DAILY_SALARY * 1.6)
    bid = min(target, soft_cap)

    # Ensure non-negative and at least a small bid if budget allows.
    if bid < 0.0:
        bid = 0.0
    min_reasonable = min(my_budget, DAILY_SALARY * 0.2)
    if bid < min_reasonable and my_budget > 0:
        bid = min_reasonable

    # Final safety: cannot exceed budget.
    bid = min(bid, my_budget)
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

    supply = float(day_context['supply'])
    day = day_context['day']

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Immediate reaction from yesterday's trace
    yesterday_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    yesterday_bids.append(float(b))
                except Exception:
                    pass

    # Estimate how many full water units supply can support (for urgency scaling)
    # supply is float; ensure indices only used with int() if needed (none here)
    units_possible = supply / WATER_REQ
    # If supply is tight, bidding more is safer.
    tightness = 0.0
    if units_possible <= 1.0:
        tightness = 1.0
    elif units_possible <= 2.0:
        tightness = 0.6
    else:
        tightness = 0.3

    # Determine target bid relative to yesterday leaders
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        second_prev = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev
    else:
        highest_prev = 0.0
        second_prev = 0.0

    # Base strategy: if someone bid near/above salary threshold, we must match slightly.
    # Cindy averaged ~94 yesterday, so we aim to be competitive around 90-100.
    pressure = 0.0
    if highest_prev >= DAILY_SALARY * 0.85:
        pressure = 1.0
    elif highest_prev >= DAILY_SALARY * 0.7:
        pressure = 0.7
    else:
        pressure = 0.4

    # Urgency from our hp and consecutive no-water days
    urgency = 0.0
    if hp <= 2.0:
        urgency = 1.0
    elif hp <= 4.0:
        urgency = 0.75
    elif hp <= 6.0:
        urgency = 0.5
    else:
        urgency = 0.35

    if no_water_days >= 2:
        urgency = max(urgency, 0.9)
    elif no_water_days == 1:
        urgency = max(urgency, 0.6)

    # Compute bid cap based on budget and need
    # We generally avoid spending too much unless urgency is high.
    budget_fraction = 0.55
    if urgency >= 0.9:
        budget_fraction = 0.95
    elif urgency >= 0.75:
        budget_fraction = 0.8
    elif urgency >= 0.5:
        budget_fraction = 0.65

    # Target bid: try to slightly exceed the previous highest if pressure/tightness/urgency are high
    target = max(DAILY_SALARY * 0.55, highest_prev)

    if pressure >= 0.7 and tightness >= 0.6:
        target = highest_prev + 2.0
    elif pressure >= 0.7:
        target = max(highest_prev, second_prev + 1.5)
    else:
        # If low pressure, bid enough to avoid being undercut by Cindy-like bids
        target = max(target, DAILY_SALARY * 0.7)

    # Add small adjustment if our hp is low
    target += (urgency - 0.5) * 6.0

    # Final bid bounds
    max_affordable = max(0.0, budget * budget_fraction)
    bid = min(max_affordable, target)

    # Ensure non-negative and not absurdly high
    if bid < 0.0:
        bid = 0.0

    return float(bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for _, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append(o)

    # If we are effectively broke, bid what we can.
    if budget <= 0:
        return 0.0

    # Gather yesterday bids from alive opponents only (immediate reaction).
    yesterday_bids = []
    for o in alive_opponents:
        prev = o.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                yesterday_bids.append(float(bid))
            except Exception:
                pass

    # Estimate competitor pressure from yesterday.
    # Observed meta: Cindy died early (likely underbid). Others survived with avg bids ~88-102.
    # So we bid slightly above the typical surviving band when our hp is at risk.
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = (sum(yesterday_bids) / float(len(yesterday_bids))) if yesterday_bids else 0.0

    # Base target bid depends on our health and no-water streak.
    # If we're low hp or accumulating no-water days, increase aggressiveness.
    if hp <= 2.0 or no_water_days >= 2:
        base = DAILY_SALARY * 0.85
    elif hp <= 4.0 or no_water_days >= 1:
        base = DAILY_SALARY * 0.65
    else:
        base = DAILY_SALARY * 0.55

    # If yesterday pressure was high, nudge upward; if low, stay near base.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        base = max(base, avg_prev_bid * 0.95, DAILY_SALARY * 0.75)
    elif highest_prev_bid >= DAILY_SALARY * 0.65:
        base = max(base, avg_prev_bid * 0.90)

    # Supply-aware adjustment: higher supply reduces need to overbid.
    # supply range is [15,25]; map to a small adjustment.
    if MAX_SUPPLY > MIN_SUPPLY:
        t = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    else:
        t = 0.5
    # t in [0,1]; higher supply => slightly lower bid.
    base = base * (1.0 - 0.12 * t)

    # Cap bid to budget and keep within reasonable band.
    bid = min(budget, base)

    # Ensure non-negative and at least a minimal participation if budget allows.
    if bid < 0:
        bid = 0.0

    # If our budget is plenty, avoid bidding too low relative to typical surviving bids.
    # Use yesterday average if available.
    if yesterday_bids and budget >= DAILY_SALARY:
        floor_bid = min(budget, max(DAILY_SALARY * 0.45, avg_prev_bid * 0.85))
        if bid < floor_bid:
            bid = floor_bid

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

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace for immediate reaction
    prev_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Estimate opponent aggressiveness
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        median_prev_bid = sorted(prev_bids)[len(prev_bids)//2]
    else:
        highest_prev_bid = 0.0
        median_prev_bid = DAILY_SALARY * 0.6

    # Pressure heuristic: if someone bid near/above salary, they likely needed water to survive
    high_pressure = highest_prev_bid >= DAILY_SALARY * 0.85

    # Supply affects how many slots exist; higher supply reduces need to overbid.
    # Compute approximate number of requirements; ensure int indices not needed.
    # Use a soft factor instead of exact slotting.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Base bid target
    if my_hp <= 2.0:
        # Critical: bid to secure water
        target = max(median_prev_bid, DAILY_SALARY * 0.9)
    elif high_pressure:
        # Others were willing to pay heavily; outbid slightly if I'm not safe
        if my_hp <= 4.0:
            target = max(median_prev_bid, DAILY_SALARY * 0.75)
        else:
            # Safe: try to undercut highest while staying competitive
            target = min(highest_prev_bid, median_prev_bid) + 2.0
    else:
        # Low/medium pressure: bid around median but adjust for supply
        # If supply is high, bid less; if low, bid more.
        target = median_prev_bid + (0.5 - supply_ratio) * 10.0

    # Clamp target to sensible bounds and budget
    min_bid = 0.0
    max_reasonable = my_budget

    # Avoid bidding above budget; keep some buffer for later days
    buffer_factor = 0.85 if my_hp <= 4.0 else 0.75
    effective_cap = my_budget * buffer_factor

    bid = max(min_bid, min(target, effective_cap, max_reasonable))

    # If computed bid is too small, still bid enough to not resemble David-like collapse
    # (David died with very low bids; we keep a floor near 0.35 salary)
    floor_bid = DAILY_SALARY * 0.35
    if bid < floor_bid and my_hp > 2.0:
        bid = min(my_budget, floor_bid)

    return float(bid)
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Alive opponents and their yesterday bids
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # If no opponents alive, conserve
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Immediate reaction from yesterday trace
    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Estimate opponent pressure
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / float(len(yesterday_bids))
    else:
        highest_prev_bid = 0.0
        avg_prev_bid = DAILY_SALARY * 0.6

    # Supply tightness: fewer total units means higher chance of losing allocation
    # If supply >= 2*WATER_REQ, one unit likely available per winner; otherwise tighter.
    units = supply / float(WATER_REQ)
    tight = 1.0 if units < 2.0 else 0.0

    # Risk from our own HP/no-water streak
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Base bid targeting just enough to beat typical winners without matching their high spend.
    # Use avg_prev_bid as anchor; add a small premium when tight or when we are at risk.
    premium = 0.0
    if tight > 0.0:
        premium += 12.0
    if no_water_days >= 2:
        premium += 18.0
    if hp <= 3.0:
        premium += 25.0

    # If yesterday pressure was extremely high, we must respond more.
    if highest_prev_bid >= 0.85 * DAILY_SALARY:
        premium += 10.0

    target = avg_prev_bid + premium

    # Keep target under a fraction of their highest to avoid overspending.
    # If we are desperate, allow approaching highest_prev_bid.
    if hp <= 2.0 or no_water_days >= 3:
        cap = min(highest_prev_bid * 0.98 if highest_prev_bid > 0 else DAILY_SALARY * 0.95, DAILY_SALARY * 1.0)
    else:
        cap = min(highest_prev_bid * 0.92 if highest_prev_bid > 0 else DAILY_SALARY * 0.8, DAILY_SALARY * 0.85)

    bid = min(target, cap)

    # Also ensure we don't exceed budget
    if bid > budget:
        bid = budget

    # Never bid negative
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Immediate reaction to yesterday bids (only previous_trace)
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Estimate opponent aggressiveness from yesterday
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    # Detect if someone likely overcommitted yesterday (Cindy-like)
    # If highest is near cap, expect continued high bids.
    cap_like = 1.0 if highest_prev_bid >= 0.95 * 150.0 else 0.0

    # Supply pressure: if supply is scarce, everyone bids more; if abundant, bids drop.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))
    scarcity = 1.0 - supply_ratio

    # Urgency based on our hp and consecutive dry days
    urgency = 0.0
    if hp <= 2.0:
        urgency += 1.0
    elif hp <= 4.0:
        urgency += 0.6
    if no_water_days >= 2:
        urgency += 0.7
    elif no_water_days == 1:
        urgency += 0.35

    # Base bid: aim to beat typical moderate bids while not burning too much budget.
    base = DAILY_SALARY * (0.35 + 0.25 * scarcity)

    # If opponents were very aggressive yesterday, we slightly increase to secure water (punish others by not matching full cap).
    if cap_like > 0.0:
        base *= 1.15

    # If our hp is critical, go higher.
    base *= (1.0 + 0.7 * urgency)

    # If yesterday highest bid was extreme, don't fully chase; just add a small premium above our base.
    if highest_prev_bid > 0:
        premium = 0.08 * highest_prev_bid
        target = base + premium
    else:
        target = base

    # Hard safety: never bid more than budget.
    bid = max(0.0, min(budget, target))

    # If budget is tiny, bid all remaining only when urgent.
    if budget <= DAILY_SALARY * 0.15 and urgency >= 0.6:
        bid = budget

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

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday bids for immediate reaction
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

    # Estimate how scarce water is today; higher supply -> bid less
    # Normalize scarcity: at MIN_SUPPLY scarcity is high, at MAX_SUPPLY scarcity is low
    scarcity = 1.0 - max(0.0, min(1.0, (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)))

    # Base bid: target around a fraction of salary, adjusted by scarcity
    base = DAILY_SALARY * (0.45 + 0.25 * scarcity)

    # If someone previously bid extremely high, we must not lose all allocation.
    # Use a cap so we don't bleed budget.
    if highest_prev_bid >= DAILY_SALARY * 1.35:
        # Cindy-like pressure: bid closer to salary to stay competitive
        pressure_bid = DAILY_SALARY * (0.75 + 0.15 * scarcity)
    elif highest_prev_bid >= DAILY_SALARY * 0.85:
        pressure_bid = DAILY_SALARY * (0.6 + 0.1 * scarcity)
    else:
        pressure_bid = base

    # If low HP or already starving, increase bid sharply
    if hp <= 2.0 or no_water_days >= 2:
        pressure_bid *= 1.25

    # Slightly reduce bid if we are healthy and have budget slack
    if hp >= 6.0 and no_water_days == 0:
        pressure_bid *= 0.9

    # Ensure we don't bid more than we can afford
    bid = min(budget, pressure_bid)

    # If budget is very low, still try to bid enough to avoid further starvation
    if budget <= DAILY_SALARY * 0.2:
        bid = min(budget, DAILY_SALARY * 0.25)

    # Keep bid non-negative
    if bid < 0.0:
        bid = 0.0

    return bid
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

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    # If no opponents are alive, spend enough to secure water.
    if not alive_opponents:
        bid = DAILY_SALARY * 0.6
        return min(my_budget, bid)

    # Read only yesterday's immediate trace bids.
    prev_bids = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Estimate pressure from highest previous bid.
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Base bid depends on supply tightness.
    # When supply is close to WATER_REQ, competition likely increases.
    tightness = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)  # higher => tighter
    tightness = max(0.0, min(1.0, tightness))

    # My urgency: low hp or many no-water days.
    urgency = 0.0
    if my_hp <= 2:
        urgency += 1.0
    if my_hp <= 4:
        urgency += 0.6
    if my_no_water_days >= 2:
        urgency += 0.6
    if my_no_water_days >= 3:
        urgency += 0.8

    # If someone was bidding very high yesterday, raise my bid to avoid being crowded out.
    # Otherwise keep a moderate bid to conserve budget.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Aggressive market: bid slightly below their top to still win when possible.
        target = highest_prev_bid * 0.85
        if urgency > 0.0:
            target = max(target, DAILY_SALARY * (0.65 + 0.25 * urgency))
    elif highest_prev_bid >= DAILY_SALARY * 0.55:
        target = max(DAILY_SALARY * (0.45 + 0.25 * tightness), highest_prev_bid * 0.75)
        if urgency > 0.0:
            target = max(target, DAILY_SALARY * (0.55 + 0.25 * urgency))
    else:
        # Low observed pressure: bid enough to secure water when tight.
        target = DAILY_SALARY * (0.35 + 0.25 * tightness)
        if urgency > 0.0:
            target = max(target, DAILY_SALARY * (0.55 + 0.2 * urgency))

    # Ensure bid is feasible.
    # Also avoid overspending: keep some budget for later days.
    # If my budget is low, bid close to remaining budget.
    budget_safety_factor = 0.75
    if my_budget <= DAILY_SALARY * 0.8:
        budget_safety_factor = 0.95

    bid = min(my_budget * budget_safety_factor, target)

    # If supply is extremely tight relative to my requirement, ensure bid is not too low.
    if supply <= float(WATER_REQ) + 1.0:
        min_bid = DAILY_SALARY * (0.55 + 0.15 * tightness)
        bid = max(bid, min_bid)

    # Final clamp.
    if bid < 0.0:
        bid = 0.0
    if bid > my_budget:
        bid = my_budget

    return bid
"""
