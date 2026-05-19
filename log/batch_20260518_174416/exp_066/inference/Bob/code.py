# ============================================================
# Experiment: exp_066
# Agent: Bob
# Source: exp_066
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

    budget = float(my_status.get('budget', 0.0))
    hp = float(my_status.get('hp', 0.0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    # Immediate reaction to yesterday's behavior (only previous_trace)
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    prev_bids.append(float(b))
                except Exception:
                    pass

    # Baseline bid sizing: tie to supply pressure but keep conservative
    # If supply is low, we bid slightly higher to secure enough water.
    # Ensure bid does not exceed budget.
    if supply <= MIN_SUPPLY:
        base = DAILY_SALARY * 0.60
    elif supply >= MAX_SUPPLY:
        base = DAILY_SALARY * 0.45
    else:
        # Linear interpolation between MIN_SUPPLY and MAX_SUPPLY
        t = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
        base = (DAILY_SALARY * 0.60) * (1.0 - t) + (DAILY_SALARY * 0.45) * t

    # Counter if opponents were aggressive yesterday
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        # If someone was bidding close to our daily salary, they likely value survival.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if hp > 3:
                bid = DAILY_SALARY * 0.75
            else:
                bid = DAILY_SALARY * 0.95
        else:
            # Match slightly above their typical pressure, but remain budget-safe
            bid = max(base, highest_prev_bid + 1.5)
    else:
        # No trace info: moderate bid; increase if hp is low
        if hp <= 2:
            bid = DAILY_SALARY * 0.90
        elif hp <= 3:
            bid = DAILY_SALARY * 0.70
        else:
            bid = base

    # Convert to final bid within budget and non-negative
    if budget <= 0:
        return 0.0
    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget

    return float(bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opponents = [o for o in opponents_status.values() if o.get('alive')]
    if not alive_opponents:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Reaction to yesterday's bidding pressure
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
    else:
        highest_prev_bid = 0.0

    # Estimate how many water units are likely needed to secure enough days.
    # With simultaneous bidding, we target a moderate share rather than maxing.
    # If supply is near 15, competition is tighter.
    supply_ratio = (supply - MIN_SUPPLY) / max(1e-9, (MAX_SUPPLY - MIN_SUPPLY))
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Base bid: moderate, higher when supply is lower.
    base = DAILY_SALARY * (0.62 - 0.18 * supply_ratio)  # ~0.62 at low supply, ~0.44 at high supply

    # Escalation logic: if someone previously bid very high, they likely try to secure water.
    # Punish by not matching unless our HP is critical.
    if highest_prev_bid >= DAILY_SALARY * 1.15:
        if hp <= 2.0 or no_water_days >= 2:
            target = DAILY_SALARY * 0.95
        else:
            target = base * 0.95  # keep moderate to avoid burning budget
    elif highest_prev_bid >= DAILY_SALARY * 0.85:
        if hp <= 3.0 or no_water_days >= 3:
            target = DAILY_SALARY * 0.78
        else:
            target = base * 1.05
    else:
        # If yesterday bids were not extreme, we can slightly undercut.
        if hp <= 2.0 or no_water_days >= 3:
            target = DAILY_SALARY * 0.85
        else:
            target = base * 0.92

    # Convert target into feasible bid given budget.
    bid = min(budget, target)

    # Ensure non-negative and avoid tiny bids that likely lose.
    min_reasonable = DAILY_SALARY * 0.25
    if bid < min_reasonable and budget >= min_reasonable:
        bid = min_reasonable

    # If budget is very low, just bid what we can.
    if budget <= 1e-9:
        return 0.0

    return max(0.0, float(bid))
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

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    # Identify alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive'):
            alive_opps.append((oid, o))

    # If no one is alive, conserve
    if not alive_opps:
        return float(min(my_status.get('budget', 0.0), DAILY_SALARY * 0.4))

    # Look only at yesterday's immediate bid pressure
    max_prev_bid = 0.0
    max_prev_opponent_id = None
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                bf = float(b)
            except Exception:
                bf = 0.0
            if bf > max_prev_bid:
                max_prev_bid = bf
                max_prev_opponent_id = oid

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))

    # Estimate how many full water units the supply likely supports
    # (use int() for index safety; though we don't index, keep logic robust)
    expected_units = int(supply / float(WATER_REQ)) if WATER_REQ > 0 else 0
    if expected_units < 1:
        expected_units = 1

    # Strategy: if Cindy was very aggressive yesterday, slightly undercut but stay competitive.
    # Cindy averaged ~157 and max ~171 in the meta context; treat high bids as threshold.
    high_pressure = max_prev_bid >= DAILY_SALARY * 1.6

    # Base bid depends on my HP (lower HP -> higher urgency)
    if my_hp <= 2.0:
        urgency = 0.95
    elif my_hp <= 4.0:
        urgency = 0.75
    else:
        urgency = 0.55

    # Competitive adjustment
    if high_pressure:
        # Underbid slightly vs the max previous bid, but not below a minimum competitive floor.
        target = max_prev_bid * 0.93
        # Ensure we don't go too low; also ensure we can still afford multiple days.
        floor = DAILY_SALARY * 0.55
        target = max(target, floor)
    else:
        # If no extreme pressure, bid around a moderate level to secure likely allocation.
        target = DAILY_SALARY * (0.45 + 0.25 * urgency)

    # Scale with expected units: if supply is tight, bid a bit more.
    tightness = 1.0
    if supply <= float(MIN_SUPPLY) + 0.5:
        tightness = 1.08
    elif supply >= float(MAX_SUPPLY) - 0.5:
        tightness = 0.95

    target = target * tightness

    # Hard caps: never exceed budget; also avoid bidding so high that it endangers survival later.
    # Since we only need 9 water requirement, we don't need to chase extreme bids.
    cap = my_budget
    soft_cap = DAILY_SALARY * 1.1  # keep spending controlled
    cap = min(cap, soft_cap)

    bid = float(min(cap, target))

    # If bid becomes too small relative to requirement pressure, bump minimally.
    if bid < DAILY_SALARY * 0.35 and my_hp > 2.0:
        bid = float(min(cap, DAILY_SALARY * 0.45))

    # Ensure non-negative
    if bid < 0.0:
        bid = 0.0

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
    day = day_context['day']

    # Identify alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # If no alive opponents, conserve
    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.35)

    # Use yesterday bids from previous_trace for immediate reaction
    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    yesterday_bids.append(float(b))
                except Exception:
                    pass

    # Baseline: target a bid slightly above the median of yesterday bids
    if yesterday_bids:
        yesterday_bids_sorted = sorted(yesterday_bids)
        mid_idx = int(len(yesterday_bids_sorted) // 2)
        median_bid = yesterday_bids_sorted[mid_idx]
        target = median_bid + 3.0
    else:
        target = DAILY_SALARY * 0.55

    # Supply pressure: if supply is low, increase competitiveness; if high, reduce
    # supply in [15,25]
    supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    # low supply => more aggressive
    supply_factor = 1.12 - 0.25 * supply_norm
    target *= supply_factor

    # HP-based risk control: with high hp, don't overpay
    hp = float(my_status['hp'])
    if hp >= 7:
        target *= 0.92
    elif hp >= 4:
        target *= 1.05
    else:
        target *= 1.25

    # Budget guardrails
    budget = float(my_status['budget'])
    no_water_days = int(my_status.get('no_water_days', 0))

    # If we've been without water too long, raise bid to avoid death spiral
    if no_water_days >= 2:
        target *= 1.18

    # Ensure bid does not exceed budget
    bid = min(budget, target)

    # Keep within reasonable bounds relative to salary
    min_bid = DAILY_SALARY * 0.25
    max_bid = min(budget, DAILY_SALARY * 0.95)
    if bid < min_bid:
        bid = min_bid
    if bid > max_bid:
        bid = max_bid

    # Final safety: if budget is tiny, bid whatever we can
    if budget <= 1.0:
        return max(0.0, budget)

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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    my_hp = int(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return float(min(my_budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace for immediate reaction
    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Pressure estimate: low supply increases competition; my hp/no-water increases urgency
    supply_factor = 0.0
    if supply <= MIN_SUPPLY:
        supply_factor = 1.0
    elif supply >= MAX_SUPPLY:
        supply_factor = 0.4
    else:
        # linear between 15 and 25
        supply_factor = 1.0 - (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) * 0.6

    my_urgency = 0.0
    if my_hp <= 2:
        my_urgency = 1.0
    elif my_hp <= 4:
        my_urgency = 0.7
    elif my_hp <= 6:
        my_urgency = 0.4
    else:
        my_urgency = 0.25

    if my_no_water_days >= 2:
        my_urgency = max(my_urgency, 0.8)

    # If someone bid very high yesterday, they likely expect scarcity/pressure; match partially.
    opponent_pressure = 0.0
    if highest_prev_bid >= DAILY_SALARY * 1.6:  # ~144
        opponent_pressure = 1.0
    elif highest_prev_bid >= DAILY_SALARY * 0.9:  # ~81
        opponent_pressure = 0.6
    else:
        opponent_pressure = 0.25

    # Target bid: base tuned to medium scenario; avoid extreme overspending.
    base = DAILY_SALARY * (0.35 + 0.25 * supply_factor)
    bid = base + DAILY_SALARY * 0.25 * my_urgency + DAILY_SALARY * 0.15 * opponent_pressure

    # If my hp is critical, bid close to salary cap.
    if my_hp <= 2:
        bid = max(bid, DAILY_SALARY * 0.9)
    elif my_hp <= 4:
        bid = max(bid, DAILY_SALARY * 0.65)

    # If supply is high and my hp is safe, keep conservative.
    if supply >= 22.0 and my_hp >= 6:
        bid = min(bid, DAILY_SALARY * 0.5)

    # Ensure bid doesn't exceed budget; also keep a small floor to remain competitive.
    bid = float(min(my_budget, bid))
    bid = float(max(1.0, bid))
    return bid
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

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', True):
            alive_opps.append(o)

    if not alive_opps:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Read yesterday bids from previous_trace only
    prev_bids = []
    prev_hp_after = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass
            try:
                prev_hp_after.append(float(prev.get('hp_after', 0.0)))
            except Exception:
                prev_hp_after.append(0.0)

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate how many water units are likely to be scarce
    # Use a simple scarcity score from supply.
    scarcity = 0.0
    if supply <= MIN_SUPPLY:
        scarcity = 1.0
    elif supply >= MAX_SUPPLY:
        scarcity = 0.0
    else:
        scarcity = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)

    # Base bid: aim to be competitive but not maxing out.
    # If yesterday saw high bids, increase slightly.
    base = DAILY_SALARY * (0.45 + 0.25 * scarcity)

    # If opponents were bidding very high yesterday, we must contest more.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        base = DAILY_SALARY * (0.55 + 0.25 * scarcity)

    # If my hp is low or I have accumulated no-water days, bid harder.
    if my_hp <= 2.0 or my_no_water_days >= 2:
        base = DAILY_SALARY * (0.85 + 0.1 * scarcity)
    elif my_hp <= 4.0:
        base = max(base, DAILY_SALARY * (0.65 + 0.1 * scarcity))

    # Convert base to a final bid with budget cap.
    bid = min(my_budget, base)

    # Add a small reactive bump when yesterday pressure was high.
    if highest_prev_bid > 0:
        bid = min(my_budget, bid + 0.1 * (highest_prev_bid - DAILY_SALARY * 0.5))

    # Ensure bid is non-negative.
    if bid < 0:
        bid = 0.0

    # If supply is very low, we may need to overpay to guarantee water.
    if supply <= float(WATER_REQ) + 2.0 and my_hp > 0.0:
        # push toward at least a strong fraction of salary
        bid = max(bid, min(my_budget, DAILY_SALARY * (0.6 + 0.2 * scarcity)))

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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    # If no opponents alive, bid conservatively
    if not alive_opps:
        bid = min(budget, DAILY_SALARY * 0.35)
        return max(0.0, bid)

    # Read yesterday bids from previous_trace for immediate reaction
    prev_bids = []
    for _opp_id, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev = max(prev_bids) if prev_bids else 0.0
    second_prev = sorted(prev_bids, reverse=True)[1] if len(prev_bids) >= 2 else 0.0

    # Pressure estimate: if someone previously bid very high, we must not be too low.
    # Cindy reached ~128 and Eric ~84.6; use those as thresholds.
    pressure = 0.0
    if highest_prev >= 0.95 * DAILY_SALARY:
        pressure = 1.0
    elif highest_prev >= 0.75 * DAILY_SALARY:
        pressure = 0.7
    elif highest_prev >= 0.55 * DAILY_SALARY:
        pressure = 0.45
    else:
        pressure = 0.25

    # Supply scarcity factor: lower supply => higher bid.
    # supply in [15,25]; map to [1.0..0.6]
    scarcity = 1.0 - (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY + 1e-9)
    scarcity = max(0.0, min(1.0, scarcity))

    # Survival urgency: if we've already missed water days, increase bid.
    urgency = 0.0
    if no_water_days >= 2:
        urgency = 1.0
    elif no_water_days == 1:
        urgency = 0.6
    else:
        urgency = 0.2

    # Base target bid: aim around a fraction of daily salary, adjusted by pressure/scarcity/urgency.
    # Avoid overpaying above the likely competition ceiling (near highest_prev) but be high enough to beat mid bids.
    target = DAILY_SALARY * (0.45 + 0.25 * pressure + 0.15 * scarcity + 0.25 * urgency)

    # If yesterday's highest bid was strong, consider matching just below it.
    if highest_prev > 0:
        # Bid slightly above second-highest to beat the runner-up, but cap near highest_prev.
        if second_prev > 0:
            target = max(target, second_prev + 2.0)
        # If target is too low versus highest_prev, lift it modestly.
        if target < highest_prev * 0.88:
            target = highest_prev * (0.88 + 0.04 * scarcity)

    # If our hp is low, we must secure water.
    if hp <= 2.0:
        target = max(target, DAILY_SALARY * 0.9)
    elif hp <= 4.0:
        target = max(target, DAILY_SALARY * 0.7)

    # Ensure we don't exceed budget and keep non-negative.
    bid = min(budget, target)

    # Additional safety: if budget is small, still bid something meaningful but not suicidal.
    if budget <= DAILY_SALARY * 0.35:
        bid = min(budget, DAILY_SALARY * 0.6)

    return max(0.0, float(bid))
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

    # Alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        # If alone, bid conservatively
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace
    yesterday_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', None)
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    yesterday_bids.append(float(b))
                except Exception:
                    pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    lowest_prev_bid = min(yesterday_bids) if yesterday_bids else 0.0

    # Identify if a specific opponent is under pressure (critical HP yesterday)
    critical_pressure = False
    for oid, o in alive_opps:
        hp = o.get('hp', 10)
        if hp is not None and float(hp) <= 3:
            critical_pressure = True
            break

    # Base bid target: aim around the low/medium band unless someone was very aggressive
    # Supply factor: with higher supply, we can bid less.
    supply_mid = (MIN_SUPPLY + MAX_SUPPLY) / 2.0  # 20
    if supply >= supply_mid:
        supply_factor = 0.85
    else:
        supply_factor = 1.05

    # If someone yesterday bid extremely high, likely they were trying to lock water.
    # We counter only enough to beat the low end, not the extreme.
    extreme_threshold = DAILY_SALARY * 2.0  # 180

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])

    # If my HP is low, prioritize survival with a higher bid.
    if my_hp <= 2.0:
        base = DAILY_SALARY * 0.95
    elif my_hp <= 3.0:
        base = DAILY_SALARY * 0.75
    else:
        base = DAILY_SALARY * 0.55

    # Adjust based on yesterday's bid distribution
    if highest_prev_bid >= extreme_threshold:
        # Avoid chasing the extreme; bid just above the low end or moderate target.
        if yesterday_bids:
            target = max(base * supply_factor, lowest_prev_bid + 5.0)
        else:
            target = base * supply_factor
    else:
        # Typical day: bid around base, but if critical pressure exists, nudge upward.
        target = base * supply_factor
        if critical_pressure:
            target = max(target, DAILY_SALARY * 0.65)
        # If lowest bid was very low, slightly outbid it to secure water.
        if yesterday_bids and lowest_prev_bid > 0:
            target = max(target, lowest_prev_bid + 2.5)

    # Ensure we don't bid more than we can afford
    bid = min(my_budget, target)

    # If budget is tiny, still bid something proportional to avoid zeroing out.
    if bid <= 0.0:
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
    day = day_context['day']

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Immediate reaction to yesterday bids
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    # Supply pressure heuristic: with more supply, fewer players need to overbid
    # but opponents already overbid yesterday (~100). We counter with a controlled bid.
    supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0..1
    supply_norm = 0.0 if supply_norm < 0.0 else (1.0 if supply_norm > 1.0 else supply_norm)

    # Base bid level tied to yesterday's aggressiveness
    # If opponents were very aggressive, we match moderately; if not, we shade upward.
    if highest_prev >= DAILY_SALARY * 0.85:
        # They likely bid to secure water; avoid getting outbid by bidding near their level but with a cap.
        base = DAILY_SALARY * (0.55 + 0.25 * supply_norm)
    else:
        base = max(DAILY_SALARY * 0.45, avg_prev * 0.85 + 5.0)

    # My urgency: low hp or many no-water days => bid more
    urgency = 0.0
    if hp <= 2.0:
        urgency = 0.35
    elif hp <= 4.0:
        urgency = 0.2
    else:
        urgency = 0.05

    if no_water_days >= 2:
        urgency += 0.15

    bid = base * (1.0 + urgency)

    # If my hp is extremely low, ensure survival attempt
    if hp <= 1.0:
        bid = max(bid, DAILY_SALARY * 0.85)

    # Budget safety
    bid = min(bid, budget)

    # Keep bids within reasonable bounds to avoid overspending
    # (still allow aggressive bids when needed)
    min_bid = 0.0
    max_bid = min(budget, DAILY_SALARY * 1.1)
    if bid < min_bid:
        bid = min_bid
    if bid > max_bid:
        bid = max_bid

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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # React to yesterday bids only (immediate reaction)
    yesterday_bids = []
    for opp_id, opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        if prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # Baseline: how much budget we can spend today while keeping some buffer
    buffer_factor = 0.25

    # Determine a target bid relative to yesterday's competitive pressure
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid

        # If they were bidding very high yesterday, we undercut slightly but stay competitive.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # If we're healthy, undercut to win at a lower price.
            if hp > 3 and no_water_days <= 1:
                target = highest_prev_bid - 5.0
            else:
                # Near-death: bid closer to the top tier to secure water.
                target = max(highest_prev_bid - 2.0, DAILY_SALARY * 0.7)
        else:
            # Moderate pressure: match slightly above the second-highest.
            target = max(second_prev_bid + 2.0, DAILY_SALARY * 0.55)
    else:
        # No data: conservative mid bid
        target = DAILY_SALARY * 0.55

    # Supply-aware adjustment: higher supply reduces needed aggression.
    # Normalize supply between MIN_SUPPLY..MAX_SUPPLY.
    if MAX_SUPPLY > MIN_SUPPLY:
        norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        norm = 0.5
    norm = max(0.0, min(1.0, float(norm)))

    # If supply is high, reduce bid; if low, increase slightly.
    supply_adj = 1.0 + (0.08 * (0.5 - norm))  # low supply => >1
    target *= supply_adj

    # Emergency escalation based on hp and no_water_days
    if hp <= 1.5 or no_water_days >= 2:
        target = max(target, DAILY_SALARY * 0.9)
    elif hp <= 3.0 or no_water_days == 1:
        target = max(target, DAILY_SALARY * 0.7)

    # Budget safety: don't spend all budget unless forced.
    max_spend = max(0.0, budget * (1.0 - buffer_factor))
    bid = min(budget, target, max_spend if max_spend > 0 else budget)

    # Ensure non-negative and at least minimal plausible bid
    if bid < 0.0:
        bid = 0.0

    return float(bid)
"""
