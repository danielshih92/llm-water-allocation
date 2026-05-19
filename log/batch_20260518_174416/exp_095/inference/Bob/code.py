# ============================================================
# Experiment: exp_095
# Agent: Bob
# Source: exp_095
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

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    prev_bids = []
    prev_pressures = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass
        # If they had trouble (no water), treat as higher pressure
        if prev.get('status', None) is not None:
            # status may encode water/no-water; we only use it lightly
            pass
        prev_no_water = int(opp.get('no_water_days', 0))
        prev_pressures.append(prev_no_water)

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    any_prev_high = highest_prev_bid >= DAILY_SALARY * 0.85

    # Estimate how many units might be needed; use supply to decide aggressiveness.
    # We avoid list indexing; only numeric comparisons.
    supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_factor = max(0.0, min(1.0, supply_factor))

    # If we are in danger, bid more.
    danger = (hp <= 2.0) or (no_water_days >= 2)

    # Base bid: aim to compete when supply is scarce.
    # When supply is lower, we bid somewhat higher.
    scarcity_boost = 0.35 + 0.35 * (1.0 - supply_factor)  # 0.35..0.70

    if any_prev_high or danger:
        # Bid to match/beat high prior bids.
        target = max(highest_prev_bid + 1.0, DAILY_SALARY * (0.55 + 0.25 * (1.0 - supply_factor)))
        if hp <= 1.5:
            target = max(target, DAILY_SALARY * 0.95)
        bid = min(budget, target)
        return float(max(0.0, bid))

    # If no one was bidding aggressively, shade: still ensure we can win water if needed.
    # Use hp/no_water_days to decide.
    if hp >= 4.0 and no_water_days == 0:
        bid = DAILY_SALARY * (0.45 + 0.15 * (1.0 - supply_factor)) * scarcity_boost
    else:
        bid = DAILY_SALARY * (0.55 + 0.20 * (1.0 - supply_factor))

    # Cap by budget.
    bid = min(budget, bid)
    return float(max(0.0, bid))
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
    day = day_context['day']

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Infer opponent aggressiveness from yesterday trace.
    # Focus on the strongest bidder yesterday (likely Cindy).
    highest_prev_bid = None
    highest_prev_agent = None
    for oid, o in alive:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            b = float(prev['bid'])
            if highest_prev_bid is None or b > highest_prev_bid:
                highest_prev_bid = b
                highest_prev_agent = oid

    # Safety baseline: if I'm in danger, bid closer to daily salary.
    danger = 0
    if hp <= 2:
        danger = 2
    elif hp <= 4:
        danger = 1

    # Estimate how many water units likely matter; with simultaneous bids, we target just above
    # the likely clearing pressure from the top bidder yesterday, but discount to avoid overspending.
    # Also account for supply being lower in this meta-round.
    supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    supply_factor = max(0.0, min(1.0, supply_factor))

    # Target bid: slightly under yesterday's top bid if possible; otherwise bid higher when needed.
    # Cindy showed max ~150 in yesterday context; we discount that to avoid matching.
    if highest_prev_bid is not None:
        top = float(highest_prev_bid)
        # Discount aggressiveness; if I'm not in danger, undercut.
        undercut = 0.88 if danger == 0 else (0.95 if danger == 1 else 1.02)
        target = top * undercut
    else:
        target = DAILY_SALARY * (0.55 if danger == 0 else (0.75 if danger == 1 else 0.95))

    # If I've already had no water for multiple days, increase bid.
    if no_water_days >= 2:
        target *= 1.12
    elif no_water_days >= 1:
        target *= 1.06

    # Convert to practical cap: cannot exceed what I can pay.
    # Also avoid extreme spending: keep within a fraction of budget unless in severe danger.
    if danger == 2:
        cap = min(budget, DAILY_SALARY * 1.05)
    elif danger == 1:
        cap = min(budget, DAILY_SALARY * 0.85)
    else:
        cap = min(budget, DAILY_SALARY * 0.65)

    bid = max(0.0, min(cap, target))

    # If supply is near minimum, competition is harsher; add a small bump.
    if supply <= (MIN_SUPPLY + 1.0):
        bid = min(bid * 1.08, cap)

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

    # Alive opponents
    alive = []
    for k, o in opponents_status.items():
        if o.get('alive', False):
            alive.append(o)

    # If no info, default conservative
    if not alive:
        return float(min(my_status['budget'], DAILY_SALARY * 0.55))

    # Read yesterday bids from previous_trace
    prev_bids = []
    prev_pressures = []
    for o in alive:
        pt = o.get('previous_trace', {}) or {}
        b = pt.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass
        # Also infer pressure from hp_after if present
        hp_after = pt.get('hp_after', None)
        if hp_after is not None:
            try:
                prev_pressures.append((float(hp_after), float(b) if b is not None else 0.0))
            except Exception:
                pass

    # Determine how aggressive the field was
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        avg_prev_bid = sum(prev_bids) / float(len(prev_bids))
    else:
        highest_prev_bid = 0.0
        avg_prev_bid = DAILY_SALARY * 0.5

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Supply pressure: with limited supply, others likely bid harder.
    # We only use supply to scale our bid ceiling.
    # If supply is just enough for one unit, competition is higher.
    units = supply / float(WATER_REQ)
    # units is float; use thresholds without indexing.
    near_single = units <= 1.35

    # Base bid target: aim to beat typical bids but not chase extreme outliers.
    # Use 70-85% of average if we are healthy; more if we're at risk.
    risk_factor = 1.0
    if my_hp <= 2.0:
        risk_factor = 1.25
    elif my_hp <= 4.0:
        risk_factor = 1.12

    if no_water_days >= 2:
        risk_factor *= 1.18

    # If someone previously went very high, we don't match their max; we bid around the 75th percentile proxy via avg/highest mix.
    # This exploits instability: Alex had a huge max but still died.
    aggressive_mix = 0.65 * avg_prev_bid + 0.35 * highest_prev_bid

    # If field average is already high, we can be slightly under to win when others overbid.
    # Otherwise, bid up to secure.
    if avg_prev_bid >= DAILY_SALARY * 1.6:
        target = 0.92 * aggressive_mix
    else:
        target = 1.05 * aggressive_mix

    # Adjust by supply scarcity
    if near_single:
        target *= 1.08
    else:
        target *= 0.98

    # Convert to a practical cap: never exceed budget and don't go beyond a reasonable multiple.
    cap = my_budget

    # If our budget is low, spend enough to avoid immediate death; otherwise preserve.
    if my_budget <= DAILY_SALARY * 0.6:
        target = max(target, DAILY_SALARY * 0.55)
        target *= 0.95

    # Final decision: if very low hp, bid very high to secure water.
    if my_hp <= 1.5:
        target = max(target, DAILY_SALARY * 0.95)

    bid = float(min(cap, target))

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

    supply = day_context['supply']
    day = day_context['day']

    # Alive opponents and yesterday bids
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    yesterday_hp_after = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(float(prev['bid']))
            yesterday_hp_after.append(prev.get('hp_after', None))

    # Estimate opponent aggressiveness from yesterday
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    # Supply pressure: with requirement 9, winning often depends on outbidding when supply is tight.
    # If supply is near minimum (15), demand is relatively harder.
    supply_tightness = (float(supply) - float(MIN_SUPPLY)) / float(MAX_SUPPLY - MIN_SUPPLY + 1e-9)
    # tightness in [0,1], where 0 is tight
    tight_factor = 1.0 - max(0.0, min(1.0, supply_tightness))

    # Base bid: target just below the highest aggressor unless our hp is low.
    # Use a small increment to beat typical high bids when tight.
    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # If we're in danger, bid more aggressively.
    danger = (hp <= 2.5) or (no_water_days >= 2)

    # Determine target from yesterday signals
    if highest_prev_bid > 0:
        # If they were bidding very high, try to undercut slightly when not in danger.
        if danger:
            target = min(highest_prev_bid + 2.0 * (0.5 + tight_factor), DAILY_SALARY * 0.98)
        else:
            target = max(DAILY_SALARY * 0.55, highest_prev_bid * (0.78 + 0.12 * tight_factor))
            # Add a small bump to avoid ties when supply is tight
            target = target + (1.0 + 2.0 * tight_factor)
    else:
        target = DAILY_SALARY * (0.75 if danger else (0.55 + 0.15 * tight_factor))

    # Convert target into a safe bid cap based on our budget
    # Also avoid spending too much early: keep some reserve for later days.
    reserve_ratio = 0.35 if danger else 0.55
    max_affordable = budget * (1.0 - reserve_ratio)

    # If budget is very low, bid what we can.
    if max_affordable <= 0:
        return min(budget, DAILY_SALARY * 0.2)

    bid = min(max_affordable, target)

    # Ensure bid is non-negative and not exceeding budget
    if bid < 0:
        bid = 0.0
    bid = min(bid, budget)

    # If we are likely to lose (hp low), push closer to budget cap
    if danger and budget > 0:
        bid = max(bid, min(budget, DAILY_SALARY * 0.85))

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

    # Alive opponents
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    # If no opponents alive, spend enough to satisfy requirement
    if not alive:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Extract yesterday bids (immediate reaction only)
    prev_bids = []
    for _, o in alive:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = sum(prev_bids) / float(len(prev_bids)) if prev_bids else 0.0

    # Supply pressure: less supply => more aggressive
    # supply is between 15 and 25; normalize to [0,1] where 0 is tight
    tightness = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5

    # If Cindy-like behavior (very high yesterday) exists, avoid matching her full spend.
    # Instead, bid slightly above likely clearing price based on others, but cap by budget.
    # Use highest_prev_bid only to decide whether to ramp.
    ramp = 0.0
    if highest_prev_bid >= 0.9 * 150.0:
        ramp = 0.15
    elif highest_prev_bid >= 0.7 * 150.0:
        ramp = 0.10
    elif highest_prev_bid >= 0.5 * 150.0:
        ramp = 0.06

    # HP urgency
    hp = float(my_status['hp'])
    no_water_days = int(my_status['no_water_days'])
    hp_urgent = 0.0
    if hp <= 1.5:
        hp_urgent = 0.35
    elif hp <= 3.0:
        hp_urgent = 0.22
    elif hp <= 5.0:
        hp_urgent = 0.10

    # Base bid target: aim around mid of salary scaled by tightness and urgency
    base = DAILY_SALARY * (0.42 + 0.25 * tightness + hp_urgent + ramp)

    # If yesterday clearing seemed high (avg high), nudge upward
    if avg_prev_bid >= 120.0:
        base *= 1.08
    elif avg_prev_bid >= 80.0:
        base *= 1.04

    # Ensure we don't overspend early; but if supply is tight and I'm low HP, ramp more
    if tightness > 0.6 and hp <= 4.0:
        base *= 1.18
    if day >= 7 and hp <= 4.0:
        base *= 1.10

    # Hard caps to preserve budget
    budget = float(my_status['budget'])
    if budget <= 0:
        return 0.0

    # Never exceed a fraction of budget; maintain optionality
    max_fraction = 0.75
    bid = min(budget * max_fraction, base)

    # If bid too low, ensure at least a minimal attempt when hp is critical
    if hp <= 2.0 or no_water_days >= 2:
        bid = max(bid, DAILY_SALARY * 0.65)

    # Final clamp
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Alive opponents
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append(o)

    # Baseline: bid enough to secure at least one unit of water share.
    # With supply in [15,25], typical winner bids cluster around ~0.5–1.0 salary.
    # We stay conservative to preserve budget across 10 days.
    if my_status['hp'] <= 2:
        base_bid = DAILY_SALARY * 0.85
    elif my_status['hp'] <= 4:
        base_bid = DAILY_SALARY * 0.65
    else:
        base_bid = DAILY_SALARY * 0.52

    # Supply pressure adjustment: lower supply => slightly higher bid.
    # Use ratio relative to WATER_REQ to estimate urgency.
    urgency = supply / float(WATER_REQ)
    # urgency ~1.7..2.8 in given range; map to factor.
    if urgency < 2.0:
        base_bid *= 1.15
    elif urgency > 2.5:
        base_bid *= 0.95

    # React to yesterday's extreme bids by survivors (likely indicates they were trying to lock water).
    # Only use previous_trace for immediate reaction.
    prev_bids = []
    for o in alive:
        pt = o.get('previous_trace', {})
        if pt and pt.get('bid') is not None:
            prev_bids.append(float(pt['bid']))

    if prev_bids:
        highest_prev = max(prev_bids)
        # If someone bid very high yesterday, they were under pressure; we can outbid slightly
        # but not overcommit.
        if highest_prev >= DAILY_SALARY * 0.95:
            base_bid = max(base_bid, DAILY_SALARY * 0.72)
        elif highest_prev >= DAILY_SALARY * 0.8:
            base_bid = max(base_bid, DAILY_SALARY * 0.6)
        else:
            # If bids were moderate, stay low.
            base_bid = min(base_bid, DAILY_SALARY * 0.58)

    # Budget safety: never bid more than budget.
    budget = float(my_status['budget'])
    if budget <= 0:
        return 0

    # If we have no_water_days, increase bid to avoid near-certain death.
    no_water_days = int(my_status.get('no_water_days', 0))
    if no_water_days >= 2:
        base_bid = max(base_bid, DAILY_SALARY * 0.8)

    # Final clamp: keep within reasonable band to avoid waste.
    bid = min(budget, base_bid)

    # Small strategic bump on later days to secure survival with remaining budget.
    if day >= 7 and my_status['hp'] > 2:
        bid = min(budget, bid * 1.08)

    # Ensure non-negative and integer-like bid (game may accept float, but keep stable).
    if bid < 0:
        bid = 0
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

    # Alive opponents
    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive.append((opp_id, opp))

    # If no opponents alive, conserve
    if not alive:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace
    prev_bids = []
    prev_hp = []
    for opp_id, opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            b = float(prev['bid'])
            prev_bids.append(b)
            prev_hp.append(int(opp.get('hp', 0)))

    # Baseline target: aim to secure water when supply is tight.
    # If supply is high, we can bid lower.
    supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    supply_norm = max(0.0, min(1.0, supply_norm))

    # Pressure estimate from competitors' yesterday bids
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    # If someone was bidding very high yesterday, likely they are trying to lock survival.
    # We counter with a modest overtake, but cap to avoid bankruptcy.
    budget = float(my_status['budget'])
    hp = int(my_status['hp'])
    no_water_days = int(my_status['no_water_days'])

    # Decide urgency
    urgent = (hp <= 2) or (no_water_days >= 2)

    # Base bid level
    base = DAILY_SALARY * (0.65 - 0.25 * supply_norm)  # lower when supply is high

    # If Cindy survived with high average bids, her behavior likely indicates a strong equilibrium.
    # Use highest/average to set a competitive bid.
    competitive = max(base, avg_prev_bid * 0.95)

    # If highest_prev_bid is near/above daily salary, increase slightly to avoid being outbid.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        competitive = max(competitive, highest_prev_bid * 1.02)

    # Urgency adjustments
    if urgent:
        competitive *= 1.12
    else:
        competitive *= 0.92

    # Final cap: never bid more than we can afford and keep some buffer.
    # Buffer fraction increases when not urgent.
    buffer_frac = 0.25 if urgent else 0.45
    max_affordable = budget * (1.0 - buffer_frac)

    bid = float(min(max_affordable if max_affordable > 0 else budget, competitive))

    # Also ensure we bid at least a small amount to have a chance when supply is tight.
    min_bid = DAILY_SALARY * (0.25 - 0.05 * supply_norm)
    if bid < min_bid:
        bid = float(min(budget, min_bid))

    # Safety: non-negative
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Determine how scarce water is relative to our requirement.
    # With supply in [15,25], approximate number of our-water units available.
    # Use int() for any indexing (none used), but keep arithmetic safe.
    scarcity_units = supply / float(WATER_REQ) if WATER_REQ > 0 else 0.0

    alive_opps = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Use only yesterday's immediate behavior.
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Baseline target bid: bid more when supply is lower or when we are at risk.
    # If we have been without water, increase urgency.
    urgency = 0.0
    if no_water_days >= 2:
        urgency = 1.0
    elif no_water_days == 1:
        urgency = 0.6

    # Pressure from opponents: if yesterday's max bid was huge, we bid to avoid being priced out,
    # but stay below the top to preserve budget.
    max_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = (sum(prev_bids) / float(len(prev_bids))) if prev_bids else 0.0

    # Supply factor: lower supply -> higher bid.
    supply_factor = 0.55
    if supply <= 17.0:
        supply_factor = 0.85
    elif supply <= 19.0:
        supply_factor = 0.75
    elif supply >= 22.0:
        supply_factor = 0.55
    else:
        supply_factor = 0.65

    # HP factor: lower HP -> bid more.
    hp_factor = 0.6
    if hp <= 2.0:
        hp_factor = 0.95
    elif hp <= 4.0:
        hp_factor = 0.8
    elif hp >= 7.0:
        hp_factor = 0.55

    # Choose a reference bid level.
    # If opponents were extremely aggressive (max_prev_bid high), anchor near avg but slightly under max.
    # Otherwise anchor around a fraction of salary.
    aggressive_threshold = DAILY_SALARY * 0.85  # 76.5

    if max_prev_bid >= aggressive_threshold:
        # Bid between avg and a capped value just below the max.
        target = 0.85 * avg_prev_bid + 0.15 * (max_prev_bid * 0.85)
    else:
        target = DAILY_SALARY * 0.55

    # Apply urgency/supply/hp multipliers.
    target *= (0.75 + 0.35 * supply_factor)
    target *= (0.75 + 0.35 * hp_factor)
    target *= (1.0 + 0.25 * urgency)

    # Keep target within sensible bounds given our budget.
    # If budget is low, we must conserve; still try to bid enough to compete when at risk.
    low_budget = budget < DAILY_SALARY * 0.6
    if low_budget:
        target *= (0.75 + 0.25 * urgency)

    # Hard caps: never exceed budget; also avoid bidding above a fraction of max supply pressure.
    # With supply [15,25], typical winning bids seem far above salary in yesterday traces,
    # but we intentionally undercut.
    cap = DAILY_SALARY * 0.95
    if max_prev_bid > cap:
        cap = max_prev_bid * 0.75

    bid = max(0.0, min(budget, min(target, cap)))

    # If we are extremely low HP, ensure we bid close to cap to survive.
    if hp <= 1.5:
        bid = max(bid, min(budget, cap * 0.95))

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

    # Alive opponents
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    # If no opponents, just bid enough to secure water
    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.6)

    # Read yesterday's immediate bidding pressure
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_highest = 0.0
    if len(prev_bids) >= 2:
        sorted_bids = sorted(prev_bids, reverse=True)
        second_highest = sorted_bids[1]

    my_hp = my_status['hp']
    my_budget = my_status['budget']

    # Estimate how many water units likely exist today
    # (used only to scale risk; indices are not used)
    # supply is float; compute units as float then use thresholds.
    units = supply / float(WATER_REQ)

    # Base aggressiveness: if our HP is healthy, undercut; if low, match pressure.
    # Thresholds derived from yesterday: Alex ~143, Cindy ~191, Eric ~110.
    extreme_pressure = highest_prev_bid >= DAILY_SALARY * 1.6  # >=144
    high_pressure = highest_prev_bid >= DAILY_SALARY * 1.1     # >=99

    # Choose target bid near but not equal to prior highest to win at lower cost.
    # If extreme pressure and our HP is low, we must bid closer to highest.
    if extreme_pressure:
        if my_hp <= 2:
            target = highest_prev_bid * 0.98
        else:
            target = max(second_highest + 2.0, highest_prev_bid * 0.92)
    elif high_pressure:
        if my_hp <= 2:
            target = highest_prev_bid * 0.95
        else:
            target = max(second_highest + 1.5, highest_prev_bid * 0.88)
    else:
        # Lower pressure: bid moderate to secure without wasting budget.
        # If supply is tight (few units), increase slightly.
        tight_supply = units <= 2.0
        if tight_supply:
            target = max(DAILY_SALARY * 0.55, highest_prev_bid * 0.85)
        else:
            target = max(DAILY_SALARY * 0.45, highest_prev_bid * 0.75)

    # Budget and HP safety caps
    # If no-water days high, we should bid more.
    no_water_days = my_status.get('no_water_days', 0)
    pressure_from_deficit = 0.0
    if no_water_days >= 2:
        pressure_from_deficit = DAILY_SALARY * 0.35
    if no_water_days >= 3:
        pressure_from_deficit = DAILY_SALARY * 0.55

    target += pressure_from_deficit

    # Final clamp: never exceed budget; also avoid bidding beyond a reasonable fraction when HP is good.
    if my_hp >= 6:
        cap = my_budget * 0.55
    elif my_hp >= 3:
        cap = my_budget * 0.75
    else:
        cap = my_budget * 0.95

    bid = min(my_budget, target, cap)

    # Ensure non-negative
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

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append(o)

    if not alive_opponents:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids to infer aggressiveness.
    yesterday_bids = []
    for o in alive_opponents:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how many "water units" we can cover today.
    # If supply is low relative to WATER_REQ, we need to be more competitive.
    supply_units = supply / WATER_REQ  # float

    # Base bid: aim for moderate share of salary.
    # If supply is scarce (<= 2 units), increase slightly.
    scarcity_factor = 1.0
    if supply_units <= 1.8:
        scarcity_factor = 1.15
    elif supply_units <= 2.2:
        scarcity_factor = 1.05

    # Aggression response: avoid repeating Alex/Cindy extreme bidding.
    # If someone was bidding extremely high yesterday, we don't mirror; we undercut.
    # Thresholds tuned to observed meta-round behavior.
    extreme_th = DAILY_SALARY * 1.25  # 112.5
    high_th = DAILY_SALARY * 0.95     # 85.5

    if highest_prev_bid >= extreme_th:
        # They likely overcommitted; bid below their likely level.
        base = DAILY_SALARY * 0.62
        if hp <= 2 or no_water_days >= 2:
            base = DAILY_SALARY * 0.85
    elif highest_prev_bid >= high_th:
        base = DAILY_SALARY * 0.68
        if hp <= 2 or no_water_days >= 2:
            base = DAILY_SALARY * 0.9
    else:
        base = DAILY_SALARY * 0.55
        if hp <= 2 or no_water_days >= 2:
            base = DAILY_SALARY * 0.8

    # If my hp is already healthy, don't overpay.
    if hp >= 7 and no_water_days <= 1:
        base *= 0.92

    # If hp is low, we must secure water.
    if hp <= 3 or no_water_days >= 3:
        base *= 1.18

    bid = base * scarcity_factor

    # Safety caps based on budget.
    # Also avoid bidding above a reasonable fraction of budget.
    max_bid_frac = 0.95
    if budget <= 0:
        return 0.0

    bid = min(bid, budget * max_bid_frac)

    # Ensure bid is non-negative.
    if bid < 0:
        bid = 0.0

    # If budget is tiny, still bid what we can.
    if budget < DAILY_SALARY * 0.2:
        bid = min(budget, DAILY_SALARY * 0.25)

    return float(bid)
"""
