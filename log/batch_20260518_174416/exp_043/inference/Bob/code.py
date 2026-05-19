# ============================================================
# Experiment: exp_043
# Agent: Bob
# Source: exp_043
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

    # Collect alive opponents and their immediate (yesterday) behavior
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    # If no opponents, bid modestly
    if not alive_opps:
        target = min(my_status['budget'], DAILY_SALARY * 0.4)
        return max(0.0, float(target))

    # Immediate reaction to yesterday's bidding pressure
    prev_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Base bid: mid-range to beat cautious bidders but avoid overpaying
    # Use supply estimate to choose a bid that is likely to secure enough water.
    # We can't control allocation directly, but higher bids correlate with winning water.
    supply_ratio = supply / float(WATER_REQ)
    # Heuristic: if supply is near minimum, competition is tighter -> bid higher.
    if supply <= float(MIN_SUPPLY) + 0.5:
        base = DAILY_SALARY * 0.62
    elif supply >= float(MAX_SUPPLY) - 0.5:
        base = DAILY_SALARY * 0.48
    else:
        base = DAILY_SALARY * 0.55

    # Pressure adjustment from yesterday
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        # If someone bid very aggressively yesterday, we slightly overbid to prevent being starved.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status.get('hp', 0) > 3:
                base = max(base, DAILY_SALARY * 0.66)
            else:
                base = max(base, DAILY_SALARY * 0.92)
        # If bids were low, we can bid just enough.
        elif highest_prev_bid <= DAILY_SALARY * 0.45:
            base = min(base, DAILY_SALARY * 0.52)

    # Survival safeguard: if low hp or many no-water days, bid more.
    hp = float(my_status.get('hp', 0))
    no_water_days = int(my_status.get('no_water_days', 0))
    if hp <= 2 or no_water_days >= 2:
        base = max(base, DAILY_SALARY * 0.9)
    elif hp <= 3:
        base = max(base, DAILY_SALARY * 0.72)

    # Budget cap and non-negative
    budget = float(my_status.get('budget', 0))
    bid = min(budget, base)

    # Keep bid within plausible range
    if bid < 0.0:
        bid = 0.0

    return float(bid)
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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((opp_id, o))

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Yesterday bids from immediate trace
    prev_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate pressure from yesterday
    pressure = 0.0
    if prev_bids:
        pressure = max(prev_bids)

    # If others were paying ~97-116, we expect competition for scarce water.
    # Target slightly below the max-pressure tier to avoid overpaying.
    # Also adjust for our HP/no-water streak.
    if pressure >= DAILY_SALARY * 0.85:
        if hp > 6 and no_water_days <= 1:
            target = DAILY_SALARY * 0.95  # ~85.5, but undercuts typical ~97
        elif hp > 3:
            target = DAILY_SALARY * 1.05
        else:
            target = DAILY_SALARY * 1.25
    else:
        # Lower competition; bid enough to secure water if needed.
        if hp <= 2 or no_water_days >= 2:
            target = DAILY_SALARY * 0.9
        else:
            target = max(DAILY_SALARY * 0.45, pressure * 0.85 if pressure > 0 else DAILY_SALARY * 0.55)

    # Supply-aware cap: if supply is high, reduce bid.
    # If supply is low, increase bid.
    # Normalize supply within [MIN_SUPPLY, MAX_SUPPLY].
    if MAX_SUPPLY > MIN_SUPPLY:
        norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        norm = 0.5
    norm = max(0.0, min(1.0, norm))

    # When norm is low (scarce), multiply up; when high, multiply down.
    scarcity_mult = 1.15 - 0.3 * norm  # ~1.15 at MIN, ~0.85 at MAX
    target *= scarcity_mult

    # Final constraints: cannot exceed budget; keep non-negative.
    bid = max(0.0, min(budget, target))

    # Small deterministic jitter to avoid ties; bounded.
    jitter = ((day + 3) % 7) * 0.35  # 0..2.1
    bid = min(budget, bid + jitter)

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

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    hp = my_status.get('hp', 0)
    budget = my_status.get('budget', 0.0)
    no_water_days = my_status.get('no_water_days', 0)

    alive = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive:
        return float(min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids for immediate reaction
    prev_bids = []
    for opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev = max(prev_bids) if prev_bids else 0.0
    second_prev = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else 0.0

    # Estimate how many full allocations are likely possible today
    # (Used only to calibrate aggressiveness; exact outcome depends on all bids.)
    supply_units = int(supply // float(WATER_REQ)) if WATER_REQ > 0 else 0
    if supply_units <= 0:
        supply_units = 1

    # Pressure model: if someone previously bid near/above salary, they likely kept pressure.
    # Cindy-like behavior: high bids with survival => likely to keep bidding.
    aggressive_threshold = DAILY_SALARY * 0.85

    # Base bid: try to beat the second-highest yesterday (a common tactic when others are aggressive)
    # but keep it within budget and not too close to Cindy-high pressure.
    if highest_prev >= aggressive_threshold:
        # If I’m healthy, try to undercut; if low HP or accumulating no-water days, match pressure more.
        if hp <= 2 or no_water_days >= 2:
            target = min(highest_prev - 1.0, DAILY_SALARY * 0.95)
        elif hp <= 4 or no_water_days >= 1:
            target = min(highest_prev - 2.0, DAILY_SALARY * 0.75)
        else:
            target = min(second_prev + 3.0, DAILY_SALARY * 0.65)
    else:
        # Lower overall pressure: bid enough to secure water against low bidders.
        # Use second-highest as a floor.
        target = max(second_prev + 2.0, DAILY_SALARY * 0.5)
        # If my HP is bad, go higher.
        if hp <= 2 or no_water_days >= 2:
            target = max(target, DAILY_SALARY * 0.9)
        elif hp <= 4 or no_water_days >= 1:
            target = max(target, DAILY_SALARY * 0.7)

    # Supply calibration: when supply is tighter (closer to 15), increase bid slightly.
    # supply is between 15 and 25.
    tightness = (float(MAX_SUPPLY) - float(supply)) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    target *= (1.0 + 0.08 * tightness)

    # Budget cap and minimum practical bid
    min_bid = 1.0
    bid = float(min(budget, max(min_bid, target)))

    # If budget is extremely low, still bid something to avoid death.
    if budget <= DAILY_SALARY * 0.2:
        bid = float(min(budget, max(budget * 0.9, min_bid)))

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

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    my_hp = my_status.get('hp', 0)
    my_budget = my_status.get('budget', 0)

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        cap = my_budget
        return float(min(cap, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace for immediate reaction
    prev_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    prev_bids.append(float(b))
                except Exception:
                    pass

    # Baseline from yesterday: try to outbid the more conservative survivor (Eric-like)
    # while staying under the more aggressive one (Alex-like).
    if prev_bids:
        sorted_bids = sorted(prev_bids)
        # median and max give robustness
        median_bid = sorted_bids[len(sorted_bids)//2]
        max_bid = sorted_bids[-1]

        # Target: slightly above median, but not chasing max aggressively
        target = median_bid + 8.0
        # If max was very high, raise only a bit (avoid budget blow-up)
        if max_bid > DAILY_SALARY * 1.2:
            target = min(target + 6.0, max_bid - 5.0)
    else:
        target = DAILY_SALARY * 0.55

    # Supply pressure: higher supply means less need to overbid
    # Use a simple interpolation between MIN_SUPPLY and MAX_SUPPLY.
    s = float(supply)
    if s <= MIN_SUPPLY:
        supply_factor = 1.05
    elif s >= MAX_SUPPLY:
        supply_factor = 0.95
    else:
        supply_factor = 1.05 - (s - MIN_SUPPLY) * (0.10 / (MAX_SUPPLY - MIN_SUPPLY))

    # HP/budget risk control
    if my_hp <= 2:
        risk_factor = 1.35
    elif my_hp <= 4:
        risk_factor = 1.15
    else:
        risk_factor = 1.0

    # Budget cap: don't exceed what we can afford safely across remaining days (10-day meta)
    # Use a conservative per-day cap.
    per_day_safe_cap = my_budget * 0.35

    bid = target * supply_factor * risk_factor

    # Final clamps
    bid = float(max(0.0, bid))
    bid = float(min(bid, my_budget, per_day_safe_cap, DAILY_SALARY * 1.25))

    # Ensure at least a minimal competitive bid when we have enough budget
    if my_budget >= DAILY_SALARY * 0.4 and bid < DAILY_SALARY * 0.45:
        bid = float(DAILY_SALARY * 0.45)

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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    budget = float(my_status.get('budget', 0.0))
    hp = int(my_status.get('hp', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # If we're in danger, bid aggressively.
    if hp <= 2 or no_water_days >= 2:
        bid = min(budget, DAILY_SALARY * 0.95)
        return bid

    # Read yesterday's immediate pressure from alive opponents.
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', None)
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    yesterday_bids.append(float(b))
                except Exception:
                    pass

    # Supply-based baseline: if supply is closer to minimum, competition likely higher.
    # Supply range is [15,25], water requirement is 9.
    # Expected number of water units roughly supply/WATER_REQ.
    units = supply / float(WATER_REQ)
    scarcity = 0.0
    if units <= (MIN_SUPPLY / float(WATER_REQ)) + 0.1:
        scarcity = 1.0
    elif units >= (MAX_SUPPLY / float(WATER_REQ)) - 0.1:
        scarcity = 0.0
    else:
        # interpolate
        scarcity = ( (MAX_SUPPLY / float(WATER_REQ)) - units ) / ( (MAX_SUPPLY - MIN_SUPPLY) / float(WATER_REQ) )
        if scarcity < 0.0:
            scarcity = 0.0
        if scarcity > 1.0:
            scarcity = 1.0

    # Determine how much to overbid relative to observed pressure.
    # If opponents were bidding extremely high yesterday, we don't match fully unless needed.
    pressure_bid = 0.0
    if yesterday_bids:
        pressure_bid = max(yesterday_bids)

    # Target bid level:
    # - baseline: moderate fraction of salary
    # - add a small bump if yesterday pressure was high
    baseline = DAILY_SALARY * (0.45 + 0.25 * scarcity)  # between 0.45 and 0.70

    bump = 0.0
    if pressure_bid >= DAILY_SALARY * 0.85:
        bump = DAILY_SALARY * 0.08  # small bump; avoid burning budget
    elif pressure_bid >= DAILY_SALARY * 0.60:
        bump = DAILY_SALARY * 0.05
    else:
        bump = DAILY_SALARY * 0.02

    # If our budget is low, scale down.
    # Keep at least a small chance to win without going bankrupt.
    budget_factor = 1.0
    if budget < DAILY_SALARY * 0.5:
        budget_factor = 0.75
    elif budget < DAILY_SALARY * 0.25:
        budget_factor = 0.55

    target = (baseline + bump) * budget_factor

    # Hard cap by budget.
    if budget <= 0.0:
        return 0.0

    # Ensure we don't bid above a reasonable ceiling.
    ceiling = DAILY_SALARY * (0.75 + 0.15 * scarcity)
    bid = min(budget, min(target, ceiling))

    # If supply is high, bid lower.
    if supply >= 22.0:
        bid = min(bid, DAILY_SALARY * 0.5)

    # If we have not been getting water recently, slightly increase.
    if no_water_days == 1:
        bid = min(budget, bid + DAILY_SALARY * (0.08 + 0.05 * scarcity))

    # Final safety clamp.
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

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    my_hp = my_status.get('hp', 0)
    my_budget = my_status.get('budget', 0.0)
    my_no_water_days = my_status.get('no_water_days', 0)

    alive = []
    for k, o in opponents_status.items():
        if o.get('alive', False):
            alive.append(o)

    # If no opponents alive, spend enough to survive comfortably
    if not alive:
        return float(min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace only (immediate reaction)
    prev_bids = []
    for o in alive:
        pt = o.get('previous_trace', {})
        if pt and pt.get('bid') is not None:
            try:
                prev_bids.append(float(pt.get('bid', 0.0)))
            except Exception:
                pass

    # Estimate opponent aggressiveness from yesterday
    if prev_bids:
        # Focus on the upper cluster to avoid being undercut
        sorted_b = sorted(prev_bids)
        n = len(sorted_b)
        # Take median of top half
        start = int(n/2)
        idx = int(start + (n - start - 1) * 0.5)
        idx = max(0, min(n - 1, idx))
        top_mid = sorted_b[idx]
        target = top_mid
    else:
        target = DAILY_SALARY * 0.6

    # Scale target by supply: higher supply => less need to overbid
    # supply is in [15,25]; map to [1.15..0.95] multiplier roughly
    if MAX_SUPPLY <= MIN_SUPPLY:
        supply_mult = 1.0
    else:
        t = (float(supply) - float(MIN_SUPPLY)) / (float(MAX_SUPPLY) - float(MIN_SUPPLY))
        # t=0 => 1.15, t=1 => 0.95
        supply_mult = 1.15 - 0.20 * t

    # HP/urgency adjustment
    # If my HP is low, prioritize survival: bid closer to my budget (but cap)
    if my_hp <= 2 or my_no_water_days >= 2:
        urgency_mult = 1.25
    elif my_hp <= 4:
        urgency_mult = 1.10
    else:
        urgency_mult = 1.00

    # Slight overbid to beat the cluster
    bid = target * supply_mult * urgency_mult + 1.5

    # Also anchor to a fraction of daily salary so we don't wildly overspend
    # For medium scenario, their bids were ~1.45*salary; we can be slightly under but not too low.
    anchor = DAILY_SALARY * 1.45
    bid = 0.65 * bid + 0.35 * anchor

    # Cap by budget and keep within reasonable range
    bid = float(min(my_budget, bid))

    # Safety floor: if bid would be too low to matter while HP is critical, raise
    if (my_hp <= 2 or my_no_water_days >= 2) and bid < DAILY_SALARY * 0.7:
        bid = float(min(my_budget, DAILY_SALARY * 0.9))
    elif bid < DAILY_SALARY * 0.35 and my_hp > 4:
        bid = float(min(my_budget, DAILY_SALARY * 0.45))

    return bid
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

    # Determine alive opponents
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)

    # If no opponents, conserve
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # Estimate opponent pressure from yesterday
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # Also consider a typical bid level (median-like via sorting)
        sorted_b = sorted(yesterday_bids)
        mid = sorted_b[len(sorted_b)//2]
    else:
        highest_prev_bid = 0.0
        mid = DAILY_SALARY * 0.5

    # Target: beat high bidder only slightly, but cap by what we can afford
    # Use supply to scale: higher supply means we can win with less relative pressure.
    # Compute a conservative fraction of daily salary.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Base bid aggressiveness driven by yesterday pressure
    # If Cindy/Alex-like behavior (high bids), we raise but avoid matching highest exactly.
    if highest_prev_bid >= DAILY_SALARY * 1.6:
        # High pressure: bid in a band around mid-high, slightly under highest.
        desired = max(mid, DAILY_SALARY * (0.95 + 0.25 * supply_ratio))
        # Nudge upward if our hp is strong; downward if hp is weak.
        if my_status['hp'] <= 2:
            desired *= 0.75
        elif my_status['hp'] <= 4:
            desired *= 0.9
        else:
            desired *= 1.02
        # Do not exceed highest_prev_bid by too much; also cap by affordability.
        desired = min(desired, highest_prev_bid * 0.98)
    else:
        # Lower pressure: bid moderately to secure water.
        desired = max(DAILY_SALARY * (0.55 + 0.25 * supply_ratio), mid * 0.9)
        if my_status['hp'] <= 2:
            desired *= 1.15
        elif my_status['hp'] <= 4:
            desired *= 1.05

    # Ensure we don't bid more than our budget
    bid = float(min(my_status['budget'], desired))

    # If budget is tiny, still bid enough to avoid wasting day (but cannot exceed budget)
    if my_status['budget'] <= DAILY_SALARY * 0.2:
        bid = float(min(my_status['budget'], DAILY_SALARY * 0.25))

    # If we're already in no-water risk, increase slightly
    if int(my_status.get('no_water_days', 0)) >= 1:
        bid = float(min(my_status['budget'], bid * 1.08))

    # Final clamp
    if bid < 0:
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

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    if not alive_opponents:
        return float(min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids (immediate reaction only)
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
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    # Supply pressure heuristic: lower supply => higher competition
    # Expected number of water units relative to requirement
    supply_units = supply / float(WATER_REQ) if WATER_REQ else 0.0
    # Map to a competition multiplier in [0.9, 1.25]
    if supply <= MIN_SUPPLY:
        comp_mult = 1.25
    elif supply >= MAX_SUPPLY:
        comp_mult = 0.9
    else:
        # linear interpolation between bounds
        t = (supply - float(MIN_SUPPLY)) / float(MAX_SUPPLY - MIN_SUPPLY)
        comp_mult = 1.25 - 0.35 * t

    # Base target bid: track their equilibrium bids (~150) but keep budget safe
    # If their highest bid was very high, we must match more.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        target = max(avg_prev_bid, highest_prev_bid * 0.95)
    else:
        target = max(avg_prev_bid * 0.85, DAILY_SALARY * 0.55)

    # Adjust for our urgency
    urgency = 0.0
    if hp <= 2:
        urgency += 0.35
    if no_water_days >= 2:
        urgency += 0.25
    if hp <= 3:
        urgency += 0.15

    target = target * (1.0 + urgency) * comp_mult

    # Cap: don't overbid beyond a fraction of budget; also avoid bidding above typical max
    # Budget fraction increases when low HP.
    if hp <= 2:
        budget_cap_frac = 0.95
    elif hp <= 4:
        budget_cap_frac = 0.85
    else:
        budget_cap_frac = 0.70

    max_bid_allowed = budget * budget_cap_frac

    # Soft upper cap near observed opponent max (approx 173.5) but still bounded by budget
    soft_cap = 180.0
    bid = min(float(target), soft_cap, float(max_bid_allowed), budget)

    # Ensure non-negative and at least 1 when we can afford it
    if bid < 1.0:
        bid = 0.0 if budget < 1.0 else 1.0

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

    supply = day_context['supply']
    day = day_context['day']

    # Identify alive opponents and collect yesterday bids
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    # If no opponents, conserve
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Use only yesterday's previous_trace for immediate reaction
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Estimate how aggressive the market is
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_highest_prev = 0.0
    if len(yesterday_bids) >= 2:
        s = sorted(yesterday_bids, reverse=True)
        second_highest_prev = s[int(1)]

    # Base willingness depends on supply pressure
    # When supply is low, winning more water is more valuable.
    supply_frac = (float(supply) - float(MIN_SUPPLY)) / (float(MAX_SUPPLY) - float(MIN_SUPPLY) + 1e-9)
    supply_frac = max(0.0, min(1.0, supply_frac))
    low_supply = (supply_frac < 0.5)

    # If my hp is low, bid more to avoid death.
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    # Determine target bid level:
    # - If someone was bidding extremely high yesterday, the market likely over-allocates; bid just below the top to still secure.
    # - If top bids were low, bid enough to beat them but not overspend.
    extreme_threshold = DAILY_SALARY * 0.85

    if highest_prev_bid >= extreme_threshold:
        # Try to undercut the leader while still being competitive.
        # Use second-highest if available to avoid overbidding.
        if second_highest_prev > 0.0:
            target = second_highest_prev + 2.0
        else:
            target = highest_prev_bid * 0.85
    else:
        # Moderate market: bid around the highest previous bid plus a small premium.
        target = highest_prev_bid + (8.0 if low_supply else 4.0)

    # Adjust for my hp and remaining budget
    if hp <= 2.0:
        target *= 1.25
    elif hp <= 4.0:
        target *= 1.10

    # Cap by budget and keep within reasonable fraction of daily salary
    # (prevents catastrophic spending when supply is not very tight)
    max_reasonable = DAILY_SALARY * (0.95 if low_supply else 0.7)
    target = min(target, max_reasonable)

    bid = float(min(budget, max(0.0, target)))

    # Ensure nonzero bid when hp is critical and budget allows
    if bid <= 0.0 and hp <= 3.0 and budget > 0.0:
        bid = float(min(budget, DAILY_SALARY * 0.9))

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
    day = day_context['day']

    # Identify alive opponents and extract yesterday bids
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Base bid pressure estimate from yesterday
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / float(len(yesterday_bids))
    else:
        highest_prev_bid = 0.0
        avg_prev_bid = DAILY_SALARY * 0.6

    # Tight supply increases urgency; approximate how many water units exist
    # Use explicit int() indexing safety by avoiding list indices.
    supply_units = supply / float(WATER_REQ)

    # Determine aggressiveness based on my HP and supply tightness
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # If I'm already accumulating no-water days or low HP, bid harder
    if hp <= 2.5 or no_water_days >= 2:
        target = DAILY_SALARY * 0.9
    elif hp <= 4.0:
        target = DAILY_SALARY * 0.7
    else:
        # If supply is tight (few units), slightly higher; otherwise undercut
        if supply_units <= 2.0:
            target = DAILY_SALARY * 0.62
        else:
            target = DAILY_SALARY * 0.55

    # Undercut the highest yesterday bid to avoid overpaying, but respond if they were extremely aggressive
    # If highest_prev_bid is huge, we nudge upward; otherwise keep near target.
    if highest_prev_bid >= DAILY_SALARY * 1.8:
        target = max(target, DAILY_SALARY * 0.75)
    elif highest_prev_bid >= DAILY_SALARY * 1.2:
        target = max(target, DAILY_SALARY * 0.65)
    else:
        # keep slight undercut relative to average
        target = min(target, avg_prev_bid * 0.95) if avg_prev_bid > 0 else target

    # Ensure we don't exceed budget
    bid = min(budget, target)

    # Add a tiny deterministic adjustment by day to reduce ties without randomness
    # (bounded to not materially change strategy)
    bid += (float(day) % 3) * 0.75

    # Final clamp
    if bid < 0:
        bid = 0.0
    return float(bid)
"""
