# ============================================================
# Experiment: exp_078
# Agent: Bob
# Source: exp_078
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = day_context.get('supply', 0)
    day = day_context.get('day', 0)

    hp = my_status.get('hp', 0)
    budget = my_status.get('budget', 0)
    no_water_days = my_status.get('no_water_days', 0)

    alive_opps = [o for o in opponents_status.values() if o.get('alive', False)]

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from each opponent's previous_trace
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                yesterday_bids.append(float(bid))
            except Exception:
                pass

    # Base target bid
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If someone was already bidding very high, they likely need water urgently.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # If our hp is low or we've already missed water, lean more aggressive.
            urgency = 0.0
            if hp <= 2:
                urgency += 0.35
            if no_water_days >= 2:
                urgency += 0.25
            if no_water_days >= 3:
                urgency += 0.25
            bid_frac = 0.30 + urgency
            bid = DAILY_SALARY * bid_frac
            return max(0.0, min(budget, bid))
        else:
            # Otherwise, bid enough to compete while preserving budget.
            # Slightly overbid relative to their max to steal allocations.
            bid = max(DAILY_SALARY * 0.50, highest_prev_bid + 1.5)
            # If our hp is critical, increase.
            if hp <= 2:
                bid *= 1.35
            if no_water_days >= 2:
                bid *= 1.15
            return max(0.0, min(budget, bid))

    # No reliable yesterday bid info: decide using our internal state.
    if hp <= 2:
        return max(0.0, min(budget, DAILY_SALARY * 0.90))
    if no_water_days >= 3:
        return max(0.0, min(budget, DAILY_SALARY * 0.75))
    if no_water_days >= 2:
        return max(0.0, min(budget, DAILY_SALARY * 0.65))

    # Mild bid; scale with supply (higher supply => can bid less aggressively).
    # Ensure indices are safe: we only use scalar math.
    # Map supply in [15,25] to a factor in [0.55,0.40]
    s = float(supply)
    if s <= 15.0:
        factor = 0.55
    elif s >= 25.0:
        factor = 0.40
    else:
        factor = 0.55 - (s - 15.0) * (0.15 / 10.0)

    bid = DAILY_SALARY * factor
    return max(0.0, min(budget, bid))
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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace for immediate reaction
    prev_bids = []
    prev_hp_after = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass
        hpa = prev.get('hp_after', None)
        if hpa is not None:
            try:
                prev_hp_after.append(int(hpa))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev_bid

    # Estimate how many players might be competing: use supply relative to WATER_REQ
    # Note: supply is float; indices must be int but we only compute scalars.
    approx_water_units = max(1.0, supply / float(WATER_REQ))

    # Base bid: target a fraction of salary, tuned by our HP and observed opponent intensity.
    # If opponents bid extremely high yesterday, they likely overreact; we can undercut.
    pressure = 0.0
    if highest_prev_bid >= DAILY_SALARY * 1.05:
        pressure = 1.0
    elif highest_prev_bid >= DAILY_SALARY * 0.8:
        pressure = 0.7
    elif highest_prev_bid >= DAILY_SALARY * 0.4:
        pressure = 0.4
    else:
        pressure = 0.2

    # If we are in danger, increase bid sharply.
    danger = 0.0
    if my_hp <= 1:
        danger = 1.0
    elif my_hp <= 3:
        danger = 0.8
    elif my_no_water_days >= 2:
        danger = 0.6
    else:
        danger = 0.3

    # Undercut strategy: when pressure is high, don't match highest_prev_bid; instead bid near
    # a level slightly above the second-highest (to beat most) but below the highest.
    if pressure >= 0.7:
        target = max(DAILY_SALARY * 0.45, second_prev_bid + 2.0)
        target = min(target, highest_prev_bid - 5.0) if highest_prev_bid - 5.0 > 0 else target
    else:
        target = max(DAILY_SALARY * 0.55, second_prev_bid * 0.9 + 1.0)

    # Apply danger multiplier
    target = target * (1.0 + 0.6 * danger)

    # Supply-aware adjustment: if supply is low, competition is tighter.
    if supply <= (MIN_SUPPLY + 0.5):
        target *= 1.15
    elif supply >= (MAX_SUPPLY - 0.5):
        target *= 0.95

    # Budget safety: never exceed budget.
    bid = max(0.0, min(my_budget, target))

    # If our budget is tiny, still bid what we can to avoid further no-water days.
    if my_budget <= DAILY_SALARY * 0.2:
        bid = max(0.0, min(my_budget, DAILY_SALARY * 0.25))

    return float(bid)
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

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((opp_id, o))

    if not alive_opps:
        return float(min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids and pressure.
    yesterday_bids = []
    pressure_scores = []
    for opp_id, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

        prev_hp_after = prev.get('hp_after', None)
        prev_status = prev.get('status', None)
        opp_hp = float(o.get('hp', 0))
        opp_no_water = int(o.get('no_water_days', 0))

        # Pressure: low hp or many no-water days increases chance they will overbid today.
        score = 0.0
        score += max(0.0, 5.0 - opp_hp) * 1.2
        score += max(0, opp_no_water) * 1.0
        if prev_status in ('dead', 'dying'):
            score += 6.0
        if prev_hp_after is not None:
            try:
                score += max(0.0, 5.0 - float(prev_hp_after)) * 0.8
            except Exception:
                pass
        pressure_scores.append((score, opp_id))

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    top_pressure = max(pressure_scores)[0] if pressure_scores else 0.0

    # Supply-based urgency: with limited supply, competition increases.
    supply_frac = (supply - float(MIN_SUPPLY)) / max(1e-9, (float(MAX_SUPPLY) - float(MIN_SUPPLY)))
    supply_frac = max(0.0, min(1.0, supply_frac))

    # Base bid: if I'm low hp / no-water, bid more.
    if hp <= 2.0 or no_water_days >= 2:
        base = DAILY_SALARY * (0.75 + 0.25 * supply_frac)
    elif hp <= 4.0 or no_water_days == 1:
        base = DAILY_SALARY * (0.55 + 0.20 * supply_frac)
    else:
        base = DAILY_SALARY * (0.45 + 0.15 * supply_frac)

    # React to yesterday meta: Cindy/Eric bid very high; avoid wasting by anchoring to highest_prev_bid.
    # If yesterday highest bid was extreme, we shade slightly below it to conserve budget.
    if highest_prev_bid >= DAILY_SALARY * 1.8:
        target = min(base * 1.05, highest_prev_bid * 0.92)
    elif highest_prev_bid >= DAILY_SALARY * 1.1:
        target = min(base * 1.00, highest_prev_bid * 0.85)
    else:
        target = base

    # If opponents show high pressure, increase bid toward base.
    if top_pressure >= 6.0:
        target = max(target, base * 1.10)

    # Ensure we don't bid more than budget.
    # Also keep a floor to avoid getting shut out when supply is scarce.
    min_bid = DAILY_SALARY * (0.35 + 0.15 * supply_frac)
    bid = float(min(budget, max(min_bid, target)))

    # If budget is very low, spend just enough to try to survive.
    if budget <= DAILY_SALARY * 0.3:
        bid = float(min(budget, DAILY_SALARY * 0.25 + (hp <= 2.0) * DAILY_SALARY * 0.4))

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

    supply = day_context['supply']
    day = day_context['day']

    # Identify alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive'):
            alive_opps.append((oid, o))

    # If no one alive, spend enough to avoid no-water days
    if not alive_opps:
        target = DAILY_SALARY * 0.35
        return min(my_status['budget'], target)

    # Use yesterday's trace only (immediate reaction)
    prev_bids = []
    prev_bids_by_hp = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            b = prev.get('bid')
            prev_bids.append(b)
            prev_bids_by_hp.append((b, o.get('hp', 0)))

    # Compute a pressure estimate: how high others were bidding yesterday
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev_bid
        avg_prev_bid = sum(prev_bids) / float(len(prev_bids))
    else:
        highest_prev_bid = 0.0
        second_prev_bid = 0.0
        avg_prev_bid = 0.0

    # Supply tightness: lower supply => more competitive => bid higher
    # supply is float; map to [0,1] via normalized ratio
    if MAX_SUPPLY - MIN_SUPPLY > 0:
        tightness = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    else:
        tightness = 0.5
    if tightness < 0.0:
        tightness = 0.0
    if tightness > 1.0:
        tightness = 1.0

    # Base bid anchored to observed aggressive baseline (~105) but tempered by our budget/hp
    # If others were bidding high, we slightly overbid; otherwise, we bid near baseline.
    aggressive_baseline = 105.0

    # Determine our urgency
    hp = my_status.get('hp', 0)
    no_water_days = my_status.get('no_water_days', 0)
    budget = my_status.get('budget', 0)

    urgency = 0.0
    if hp <= 2:
        urgency = 1.0
    elif hp <= 4:
        urgency = 0.7
    elif hp <= 6:
        urgency = 0.45
    else:
        urgency = 0.25

    # If we've already missed water days, increase urgency
    if no_water_days >= 2:
        urgency = min(1.0, urgency + 0.25)

    # Competitiveness from yesterday
    # If highest was near/above baseline, assume strong bidding continuation.
    if highest_prev_bid >= aggressive_baseline * 0.95:
        competitiveness = 1.0
    elif highest_prev_bid >= aggressive_baseline * 0.75:
        competitiveness = 0.7
    elif highest_prev_bid >= aggressive_baseline * 0.5:
        competitiveness = 0.45
    else:
        competitiveness = 0.25

    # Compute target bid
    # Start from baseline, adjust for competitiveness and tightness, then discount if hp is very low.
    target = aggressive_baseline
    target += 25.0 * competitiveness * tightness
    target += 15.0 * urgency

    # If my hp is critically low, bid more but cap to budget
    if hp <= 2:
        target = max(target, DAILY_SALARY * 0.85)
    elif hp <= 4:
        target = max(target, DAILY_SALARY * 0.65)
    else:
        # Preserve budget early/mid
        target = min(target, DAILY_SALARY * 0.7 + (aggressive_baseline * 0.2))

    # If supply is extremely low, push a bit higher
    if supply <= float(WATER_REQ):
        target = max(target, DAILY_SALARY * 0.75)

    # Final cap
    bid = min(budget, target)

    # Ensure non-negative
    if bid < 0:
        bid = 0.0

    return bid
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

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive = []
    for opp_id, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((opp_id, o))

    if not alive:
        return min(budget, DAILY_SALARY * 0.4)

    # Use only yesterday previous_trace to infer aggressiveness
    prev_bids = []
    prev_hp_after = []
    for _, o in alive:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
                prev_hp_after.append(float(prev.get('hp_after', o.get('hp', 0))))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    # If someone was bidding near/above salary, they are likely pressuring for survival.
    pressure = 1 if highest_prev_bid >= DAILY_SALARY * 0.85 else 0

    # Supply pressure: lower supply means more competition for the same water.
    supply_ratio = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)  # 0..1
    supply_pressure = 1.0 - min(1.0, max(0.0, supply_ratio))

    # Base bid: moderate fraction of salary, increase when supply is tight or hp is low.
    if hp <= 2 or no_water_days >= 2:
        base = DAILY_SALARY * 0.9
    elif hp <= 4:
        base = DAILY_SALARY * 0.7
    else:
        base = DAILY_SALARY * 0.55

    # Adjust for observed opponent pressure yesterday.
    # If pressure=1, we slightly outbid the median aggressor without going all-in.
    if pressure == 1:
        base = base + DAILY_SALARY * (0.15 + 0.1 * supply_pressure)
    else:
        base = base + DAILY_SALARY * (0.05 * supply_pressure)

    # Clamp to budget and keep within reasonable bounds.
    bid = min(budget, base)

    # If supply is extremely low, add a small bump to avoid getting starved.
    if supply <= WATER_REQ + 2:
        bid = min(budget, bid + DAILY_SALARY * 0.1)

    # Ensure non-negative
    if bid < 0:
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    my_hp = int(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive'):
            alive_opps.append((oid, o))

    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace only
    yesterday_bids = []
    yesterday_hp_after = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass
        hp_after = prev.get('hp_after', None)
        if hp_after is not None:
            try:
                yesterday_hp_after.append(float(hp_after))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    lowest_prev_bid = min(yesterday_bids) if yesterday_bids else 0.0

    # Base urgency: if I have low HP or have already gone without water, bid higher.
    urgency = 0.0
    if my_hp <= 2:
        urgency += 0.8
    elif my_hp <= 4:
        urgency += 0.5
    else:
        urgency += 0.25

    if my_no_water_days >= 2:
        urgency += 0.5
    elif my_no_water_days == 1:
        urgency += 0.25

    # If someone was bidding extremely high yesterday, they likely secured water.
    # I should avoid matching extremes but still bid enough to compete.
    # Use a cap to protect budget.
    extreme_threshold = DAILY_SALARY * 1.6  # 144

    # Supply factor: higher supply reduces need to overbid.
    supply_factor = 0.9
    if supply >= 22.0:
        supply_factor = 0.85
    elif supply <= 17.0:
        supply_factor = 1.05

    # Determine target bid level.
    if highest_prev_bid >= extreme_threshold:
        # Cindy-like behavior: overbidding; we undercut.
        target = max(DAILY_SALARY * 0.45, highest_prev_bid * 0.55)
    else:
        # Otherwise, bid around median-ish level inferred from highest.
        target = max(DAILY_SALARY * 0.5, highest_prev_bid * 0.7)

    # Apply urgency and supply adjustment.
    target = target * supply_factor * (1.0 + 0.6 * urgency)

    # Budget safety: never bid more than budget.
    # Also avoid wasting money when already reasonably healthy.
    if my_hp >= 7 and my_no_water_days == 0:
        target *= 0.85

    max_affordable = my_budget
    bid = min(max_affordable, target)

    # Keep non-negative and add a tiny day-based jitter to avoid ties.
    if bid < 0.0:
        bid = 0.0
    bid += (day % 3) * 0.1

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
    day = day_context.get('day', 0)

    my_hp = float(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    if my_budget <= 0:
        return 0.0

    # Read yesterday bids from trace for immediate reaction.
    prev_bids = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    # If someone bid very high yesterday, they likely continued pressure.
    pressure = 0.0
    if prev_bids:
        pressure = max(prev_bids)

    # Base target: scale with supply; at max supply we can afford lower bids.
    # Ensure we bid enough to secure at least ~1 requirement when supply is tight.
    supply_band = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    supply_band = max(0.0, min(1.0, supply_band))

    # Convert supply to expected number of WATER_REQ units; use int indices safely.
    # (Not used as index, but keep explicit int where needed.)
    expected_units = int(supply / float(WATER_REQ)) if WATER_REQ > 0 else 0

    # Decide aggressiveness.
    # - If my HP is critical or I have been without water, bid harder.
    # - If yesterday pressure was high (~>=110), slightly undercut the high-bid crowd.
    critical = (my_hp <= 2.5) or (my_no_water_days >= 2)

    if pressure >= 110:
        # High-bid environment: choose a mid-high bid to beat them without fully matching.
        target = 0.62 * DAILY_SALARY + 0.10 * pressure
        if critical:
            target = 0.78 * DAILY_SALARY + 0.12 * pressure
    else:
        # Lower pressure: bid enough to avoid falling behind.
        target = (0.50 + 0.20 * (1.0 - supply_band)) * DAILY_SALARY
        if critical:
            target = 0.78 * DAILY_SALARY

    # Also anchor to water need: if supply is low, we should bid closer to salary.
    if supply <= float(WATER_REQ) * 1.2:
        target = max(target, 0.70 * DAILY_SALARY)

    # Final cap by budget.
    bid = min(my_budget, target)

    # Small floor to avoid zeroing when we can still survive.
    if my_budget > 0 and bid < 1.0 and (my_hp > 0):
        bid = min(my_budget, 5.0)

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

    # Determine how many units of water we can potentially get if we win enough allocation.
    # Use conservative estimate: each winning unit corresponds to one WATER_REQ consumption.
    # (We don't know exact mechanics; this is a bid heuristic.)
    est_units = max(1, int(supply / WATER_REQ))

    # Alive opponents and their yesterday bids
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Pressure-based adjustment: if we've already been dry, bid more.
    dryness_factor = 1.0 + min(0.8, 0.25 * max(0, no_water_days))
    low_hp_factor = 1.0
    if hp <= 2:
        low_hp_factor = 1.35
    elif hp <= 4:
        low_hp_factor = 1.15

    # Use yesterday's bid distribution to avoid overpaying.
    # If there were very high bids, we tilt upward slightly but cap spending.
    if prev_bids:
        avg_prev = sum(prev_bids) / float(len(prev_bids))
        max_prev = max(prev_bids)
        # Moderate target near David's behavior (~79) and below Cindy's (~112).
        # If max_prev is high, raise target modestly.
        if max_prev >= DAILY_SALARY * 1.15:  # ~103.5
            target = max(DAILY_SALARY * 0.75, avg_prev * 0.95)
        else:
            target = max(DAILY_SALARY * 0.68, avg_prev * 0.85)
    else:
        target = DAILY_SALARY * 0.7

    # Allocation intensity: with higher supply, we can bid slightly less.
    supply_factor = 1.0
    if supply >= 22:
        supply_factor = 0.92
    elif supply <= 16:
        supply_factor = 1.08

    # Convert target to final bid with caps.
    raw_bid = target * dryness_factor * low_hp_factor * supply_factor

    # Cap bids to avoid budget exhaustion; also keep within plausible range.
    # If we can afford, allow up to ~1.0*DAILY_SALARY; otherwise scale down.
    max_affordable = budget
    hard_cap = min(max_affordable, DAILY_SALARY * 1.0)

    bid = min(hard_cap, max(DAILY_SALARY * 0.35, raw_bid))

    # If extremely low budget, bid what we can.
    if bid < 1e-6:
        bid = min(budget, DAILY_SALARY * 0.4)

    return float(bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = day_context['supply']
    day = day_context['day']

    # Alive opponents and their yesterday bids
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive'):
            prev = o.get('previous_trace', {})
            alive_opps.append((oid, o, prev))

    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Extract yesterday bids (if present)
    yesterday_bids = []
    for oid, o, prev in alive_opps:
        b = prev.get('bid', None)
        if b is not None:
            yesterday_bids.append(float(b))

    # Estimate how aggressive the field is
    if yesterday_bids:
        avg_bid = sum(yesterday_bids) / len(yesterday_bids)
        max_bid = max(yesterday_bids)
    else:
        avg_bid = DAILY_SALARY * 0.6
        max_bid = DAILY_SALARY * 0.6

    my_hp = my_status['hp']
    my_budget = my_status['budget']

    # Supply pressure: higher supply => we can bid lower and still secure enough
    # Use integer-safe thresholds.
    # If supply is tight (<= 18), competition likely higher.
    tight = supply <= 18.0

    # Base bid: target just under the average competitor bid.
    # If competition was fierce yesterday (max high), shade a bit less.
    fierce = max_bid >= DAILY_SALARY * 0.85

    if tight:
        # Tight supply: bid closer to avg/max to avoid losing the allocation.
        target = avg_bid * (0.95 if fierce else 0.9)
    else:
        # Comfortable supply: bid lower to conserve budget.
        target = avg_bid * (0.85 if fierce else 0.8)

    # HP protection: if I'm low, bid more to prevent further no-water days.
    if my_hp <= 2:
        target = max(target, DAILY_SALARY * 0.8)
    elif my_hp <= 4:
        target = max(target, DAILY_SALARY * 0.6)

    # Budget cap
    bid = min(my_budget, target)

    # If bid is too low relative to WATER_REQ, raise slightly when supply is high enough
    # (to avoid being outbid by survivors using consistent bids).
    if supply >= 20.0 and bid < DAILY_SALARY * 0.45:
        bid = min(my_budget, DAILY_SALARY * 0.5)

    # Ensure non-negative
    if bid < 0:
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Identify alive opponents and extract yesterday bids
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    yesterday_bids = []
    yesterday_info = []
    for oid, o in alive:
        prev = o.get('previous_trace', {}) or {}
        if prev and prev.get('bid') is not None:
            b = float(prev.get('bid'))
            yesterday_bids.append(b)
            yesterday_info.append((oid, b, prev.get('status')))

    # Compute how many water units are needed to avoid dying today.
    # In this game, bids translate to water allocation; we hedge by bidding enough to cover our requirement.
    # If supply is scarce, we must bid relatively more.
    scarcity = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    # Base bid: aim near one unit of our requirement, adjusted for scarcity.
    # Convert to a bid scale using supply: if supply is low, more aggressive.
    base = DAILY_SALARY * (0.45 + 0.25 * scarcity)

    # React to aggressive bidding from yesterday (pressure signal)
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid

        # If someone bid extremely high yesterday, they likely tried to secure water and may continue.
        # We counter with a moderate escalation, but avoid matching the maximum to prevent budget depletion.
        if highest_prev_bid >= DAILY_SALARY * 1.6:
            # Eric-like behavior: bid enough to not lose the contest, but keep margin.
            base = max(base, DAILY_SALARY * (0.6 + 0.15 * scarcity))
        elif highest_prev_bid >= DAILY_SALARY * 1.1:
            base = max(base, DAILY_SALARY * (0.55 + 0.10 * scarcity))
        else:
            # If yesterday bids were low, we can be more conservative.
            base = min(base, DAILY_SALARY * (0.5 + 0.10 * scarcity))

        # If multiple opponents were depleted (yesterday status indicates death/0), reduce risk.
        depleted_count = 0
        for oid, b, status in yesterday_info:
            if status is not None and (('dead' in str(status).lower()) or ('die' in str(status).lower()) or ('0' in str(status))):
                depleted_count += 1
        if depleted_count >= 1:
            base *= 0.95

    # Urgency based on our hp and no_water_days
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # If very low HP or already on many dry days, we must secure water.
    if hp <= 1.5 or no_water_days >= 2:
        base = max(base, DAILY_SALARY * (0.75 + 0.15 * scarcity))
    elif hp <= 3.0 or no_water_days >= 1:
        base = max(base, DAILY_SALARY * (0.6 + 0.10 * scarcity))

    # Ensure we don't overspend: bid is capped by our budget.
    # Also keep within a sensible range relative to supply.
    # Use supply to set a soft cap: if supply is low, bidding too high is wasteful.
    soft_cap = DAILY_SALARY * (0.9 + 0.2 * scarcity)
    bid = min(budget, min(base, soft_cap))

    # If budget is tiny, spend what we can.
    if bid <= 0.0:
        bid = 0.0

    # Final safety: if supply is extremely low and we have budget, slightly increase.
    if supply <= float(WATER_REQ) and budget > 0:
        bid = min(budget, max(bid, DAILY_SALARY * 0.8))

    return float(bid)
"""
