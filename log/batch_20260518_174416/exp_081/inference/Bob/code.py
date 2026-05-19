# ============================================================
# Experiment: exp_081
# Agent: Bob
# Source: exp_081
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 1)

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opps.append(opp)

    # If no opponents, take what you can afford but avoid overpaying.
    if not alive_opps:
        target = min(budget, DAILY_SALARY * 0.45)
        return max(0.0, float(target))

    # Read yesterday bids from opponents' previous_trace.
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Determine how many WATER_REQ units supply can likely support.
    # Use explicit int() on any index-like operations; here we only compute counts.
    # Heuristic: aim to win 1 unit when supply is in [15,25].
    expected_units = int(supply / float(WATER_REQ)) if WATER_REQ > 0 else 0
    if expected_units < 1:
        expected_units = 1

    # Urgency: if low hp or already many no-water days, bid more aggressively.
    urgency = 0.0
    if hp <= 2.0:
        urgency += 0.35
    elif hp <= 4.0:
        urgency += 0.2
    if no_water_days >= 2:
        urgency += 0.25
    elif no_water_days >= 1:
        urgency += 0.1

    # Base bid level: fraction of daily salary scaled by expected units.
    # In medium scenario supply 15-25 => expected_units is 1 or 2.
    base_frac = 0.55
    if expected_units >= 2:
        base_frac = 0.45
    base_frac = base_frac + urgency

    # If opponents were bidding very high yesterday, avoid direct chase; counter slightly below peak.
    if highest_prev_bid > 0.0:
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # Price war likely; bid just enough to compete.
            bid = min(budget, highest_prev_bid * 0.92)
        else:
            # Moderate competition; bid around base but ensure it beats typical bids.
            bid = max(base_frac * DAILY_SALARY, highest_prev_bid * 0.98)
    else:
        bid = base_frac * DAILY_SALARY

    # If my hp is extremely low, increase to near desperation.
    if hp <= 1.5:
        bid = max(bid, DAILY_SALARY * 0.85)

    # Cap by budget and keep non-negative.
    bid = float(bid)
    if bid < 0.0:
        bid = 0.0
    if bid > budget:
        bid = budget

    return bid
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

    supply = day_context['supply']
    day = day_context['day']

    # Alive opponents
    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive.append((opp_id, opp))

    # Baseline bid depends on my HP urgency
    hp = my_status['hp']
    budget = my_status['budget']

    # If I'm in danger, bid high but still below typical top bids unless needed
    if hp <= 1:
        target = DAILY_SALARY * 0.95
    elif hp <= 3:
        target = DAILY_SALARY * 0.75
    else:
        target = DAILY_SALARY * 0.55

    # React to yesterday's highest bid among opponents (immediate trace)
    highest_prev_bid = None
    highest_prev_opp_budget = None
    for opp_id, opp in alive:
        prev = opp.get('previous_trace', None) or {}
        prev_bid = prev.get('bid', None)
        if prev_bid is None:
            continue
        if highest_prev_bid is None or prev_bid > highest_prev_bid:
            highest_prev_bid = prev_bid
            highest_prev_opp_budget = opp.get('budget', None)

    # If someone was paying near a high bid (Cindy-like), undercut slightly.
    # Otherwise, keep a moderate bid.
    if highest_prev_bid is not None:
        # Cindy-like behavior: bids around 142.5 previously
        if highest_prev_bid >= DAILY_SALARY * 1.55:  # ~139.5
            # Underbid by a small margin to still win water when possible
            target = min(target, highest_prev_bid - 2.0)
        elif highest_prev_bid >= DAILY_SALARY * 0.85:  # ~76.5
            target = max(target, highest_prev_bid * 0.65)

    # Supply-aware scaling: when supply is scarce, we should bid slightly more.
    # supply is in [15,25]; map to scarcity factor.
    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)  # 0..1
    target = target * (1.0 + 0.20 * scarcity)

    # Ensure bid not exceeding budget
    bid = min(budget, target)

    # If budget is extremely low, bid what we can.
    if bid <= 0:
        return 0.0

    # Clamp to a reasonable range to avoid overspending early
    min_bid = 5.0
    max_reasonable = DAILY_SALARY * 1.8
    if bid < min_bid:
        bid = min(budget, min_bid)
    if bid > max_reasonable:
        bid = max_reasonable
    bid = min(bid, budget)

    return float(bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = day_context['supply']
    day = day_context['day']

    # Identify alive opponents
    alive_ids = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_ids.append(oid)

    if not alive_ids:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids and HP context from previous_trace
    prev_bids = []
    prev_hp_after = []
    for oid in alive_ids:
        prev = opponents_status[oid].get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            prev_bids.append(float(b))
            prev_hp_after.append(prev.get('hp_after', opponents_status[oid].get('hp', 0)))

    # Baseline estimate of market pressure
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    # If Cindy was the dominant bidder yesterday, pressure is high.
    # Use name-based heuristic if present in opponent_status.
    cindy = opponents_status.get('Cindy', None)
    cindy_prev = cindy.get('previous_trace', {}) if cindy else {}
    cindy_bid = cindy_prev.get('bid', None)
    cindy_pressure = (cindy_bid is not None and float(cindy_bid) >= DAILY_SALARY * 1.0)

    # If my HP is low, prioritize survival over winning extra water
    my_hp = my_status.get('hp', 0)
    my_budget = my_status.get('budget', 0.0)

    # Supply affects how many agents can get water; with higher supply, we can bid less.
    # Normalize supply between MIN_SUPPLY and MAX_SUPPLY.
    s_norm = 0.0
    if MAX_SUPPLY != MIN_SUPPLY:
        s_norm = (float(supply) - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    if s_norm < 0.0:
        s_norm = 0.0
    if s_norm > 1.0:
        s_norm = 1.0

    # Strategy: target a bid slightly above the median/second tier, but below Cindy's likely ceiling.
    # Compute a conservative target from yesterday bids.
    sorted_prev = sorted(prev_bids) if prev_bids else [0.0]
    # second-highest if available
    if len(sorted_prev) >= 2:
        second_highest = sorted_prev[-2]
    else:
        second_highest = sorted_prev[-1]

    # Base target
    if cindy_pressure:
        # Cindy likely bids aggressively; try to outbid Eric/second-highest by a small margin.
        target = second_highest + 3.0
        # But cap below Cindy's previous bid to avoid overpaying.
        if cindy_bid is not None:
            target = min(target, float(cindy_bid) - 1.0)
    else:
        # If no dominant bidder, bid around average but nudge above.
        target = avg_prev_bid + 2.0

    # Adjust for my HP
    if my_hp <= 2:
        target = max(target, DAILY_SALARY * 0.85)
    elif my_hp <= 4:
        target = max(target, DAILY_SALARY * 0.65)
    else:
        # With comfortable HP, scale down when supply is high.
        target = target * (0.9 - 0.2 * s_norm)

    # Adjust for budget constraints
    # Also avoid bidding above an amount that would likely bankrupt us.
    # Keep a survival reserve: if budget is tight, bid proportionally.
    if my_budget <= 0:
        return 0.0

    # Reserve fraction based on HP
    reserve_frac = 0.35
    if my_hp <= 2:
        reserve_frac = 0.15
    elif my_hp <= 4:
        reserve_frac = 0.25

    max_affordable = max(0.0, my_budget * (1.0 - reserve_frac))
    bid = min(max_affordable, target)

    # Ensure bid is non-negative
    if bid < 0.0:
        bid = 0.0

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
    day = int(day_context['day'])

    # Alive opponents and their yesterday bids
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            prev = o.get('previous_trace', {}) or {}
            bid = prev.get('bid', None)
            alive_opps.append((oid, o, bid))

    if not alive_opps:
        # No competition: conserve budget
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for oid, o, bid in alive_opps:
        if bid is not None:
            try:
                yesterday_bids.append(float(bid))
            except Exception:
                pass

    # Estimate how aggressive the field was
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    # Base bid depends on our hp
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    # If our hp is low, we must buy more water (higher bid)
    if hp <= 2:
        base = DAILY_SALARY * 0.85
    elif hp <= 4:
        base = DAILY_SALARY * 0.65
    else:
        base = DAILY_SALARY * 0.52

    # If Cindy (the consistent survivor) was very aggressive yesterday, slightly increase
    cindy_prev_bid = None
    if 'Cindy' in opponents_status and opponents_status['Cindy'].get('alive', False):
        prev = opponents_status['Cindy'].get('previous_trace', {}) or {}
        c_bid = prev.get('bid', None)
        if c_bid is not None:
            try:
                cindy_prev_bid = float(c_bid)
            except Exception:
                cindy_prev_bid = None

    # Supply pressure: higher supply reduces need to overbid
    # Normalize supply into [0,1]
    supply_norm = (supply - float(MIN_SUPPLY)) / (float(MAX_SUPPLY) - float(MIN_SUPPLY))
    if supply_norm < 0.0:
        supply_norm = 0.0
    if supply_norm > 1.0:
        supply_norm = 1.0

    # If supply is high, we can bid a bit less; if low, bid a bit more
    supply_adjust = 1.0 + (0.08 * (0.5 - supply_norm))  # +/- ~4%

    # Aggression adjustment based on yesterday
    aggression_adjust = 1.0
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        aggression_adjust = 1.10
    elif highest_prev_bid >= DAILY_SALARY * 0.65:
        aggression_adjust = 1.05
    else:
        aggression_adjust = 0.98

    if cindy_prev_bid is not None and cindy_prev_bid >= DAILY_SALARY * 0.85:
        aggression_adjust = max(aggression_adjust, 1.12)

    bid = base * supply_adjust * aggression_adjust

    # Never exceed budget
    bid = min(bid, budget)

    # Safety floor/ceiling to avoid extreme bids
    min_bid = 1.0
    max_bid = DAILY_SALARY * 0.95
    if bid < min_bid:
        bid = min_bid
    if bid > max_bid:
        bid = max_bid

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

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # If no opponents, conserve.
    if not alive_opps:
        bid = DAILY_SALARY * 0.35
        if my_no_water_days >= 2 or my_hp <= 2:
            bid = DAILY_SALARY * 0.8
        return float(min(my_budget, bid))

    # Read yesterday's immediate behavior (previous_trace only).
    prev_bids = []
    prev_hp_after = []
    for oid, o in alive_opps:
        pt = o.get('previous_trace', {})
        if pt and pt.get('bid') is not None:
            prev_bids.append(float(pt['bid']))
            if pt.get('hp_after') is not None:
                prev_hp_after.append(float(pt['hp_after']))

    # Competitive band estimate.
    if prev_bids:
        max_prev = max(prev_bids)
        # Median helps avoid overreacting to a single extreme.
        sorted_b = sorted(prev_bids)
        mid = len(sorted_b) // 2
        median_prev = sorted_b[mid] if len(sorted_b) % 2 == 1 else 0.5 * (sorted_b[mid - 1] + sorted_b[mid])
    else:
        max_prev = 0.0
        median_prev = 0.0

    # If I'm in danger, bid aggressively.
    if my_hp <= 2 or my_no_water_days >= 3:
        target = max(DAILY_SALARY * 0.85, median_prev + 5.0)
    elif my_hp <= 4 or my_no_water_days >= 2:
        target = max(DAILY_SALARY * 0.65, median_prev + 3.0)
    else:
        # Otherwise, aim to be competitive but not wasteful.
        # Since others averaged ~120-150, bidding around (median + small) helps.
        target = max(DAILY_SALARY * 0.5, median_prev + 2.0)

    # Don't overpay beyond what seems to be the top band.
    # If max_prev is very high, still try to slightly exceed median rather than max.
    cap = max_prev * 1.05 if max_prev > 0 else DAILY_SALARY * 1.0
    target = min(target, cap)

    # Supply-aware adjustment: with higher supply, can bid slightly less.
    # Normalize supply into [0,1].
    if MAX_SUPPLY > MIN_SUPPLY:
        s_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        s_norm = 0.5
    # reduce bid when supply is high
    target = target * (0.92 + 0.16 * (1.0 - s_norm))

    # Ensure within budget.
    bid = float(min(my_budget, target))

    # Minimal bid to avoid zeroing out budget unnecessarily.
    if bid <= 0:
        bid = min(my_budget, DAILY_SALARY * 0.2)

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

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive'):
            alive_opps.append((oid, o))

    # If no opponents alive, bid conservatively.
    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from traces for immediate reaction.
    prev_bids = []
    prev_hp_after = []
    for oid, o in alive_opps:
        tr = o.get('previous_trace', {})
        if tr and tr.get('bid') is not None:
            try:
                prev_bids.append(float(tr['bid']))
            except Exception:
                pass
            try:
                prev_hp_after.append(float(tr.get('hp_after', 0.0)))
            except Exception:
                pass

    # Estimate opponent competitive level.
    if prev_bids:
        # If someone was willing to pay near the top, we must contest.
        top_prev = max(prev_bids)
        second_prev = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else top_prev
    else:
        top_prev = 0.0
        second_prev = 0.0

    # Base aggressiveness by supply: higher supply reduces urgency to overpay.
    # supply in [15,25] => urgency factor in [~1.1..0.9]
    urgency = 1.1 - 0.2 * ((supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY))
    urgency = float(urgency)

    # If my hp is critical or I already missed water, bid higher.
    critical = (hp <= 2.5) or (no_water_days >= 2)
    medium = (hp <= 4.0) or (no_water_days >= 1)

    # Determine target bid.
    # Aim to beat the likely incumbent by a small margin.
    # Use top_prev/second_prev to avoid overpaying.
    if top_prev >= DAILY_SALARY * 0.7:
        # High contest yesterday: match-and-beat.
        target = second_prev + 2.5
        if critical:
            target = max(target, top_prev * 0.95)
    else:
        # Moderate contest: bid around top_prev + small increment, but cap by budget.
        target = top_prev + 3.0
        if medium:
            target = max(target, DAILY_SALARY * 0.55)

    # Adjust for supply: when supply is low, water is scarcer => bid slightly more.
    if supply <= 17:
        target *= 1.07
    elif supply >= 23:
        target *= 0.95

    # Convert to feasible bid within budget.
    # Also avoid bidding more than a reasonable fraction of budget early.
    # Since episode is 10 days, keep some runway.
    runway_fraction = 0.75
    if day >= 8:
        runway_fraction = 0.95
    if critical:
        runway_fraction = 0.95

    max_reasonable = budget * runway_fraction
    bid = min(max_reasonable, target)

    # Ensure at least some bid if we need survival.
    if critical and bid < DAILY_SALARY * 0.7:
        bid = min(budget, DAILY_SALARY * 0.85)

    # Never negative.
    if bid < 0.0:
        bid = 0.0

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

    alive_opps = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opps:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.55))

    # Estimate opponent pressure from yesterday's bids
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # If an opponent bid very high yesterday, they likely were pressured and will bid again.
    # Use a slightly higher offer than their observed peak, but cap by budget.
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    # Supply pressure: closer to minimum supply implies more competition.
    supply_tightness = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    supply_tightness = max(0.0, min(1.0, supply_tightness))

    # Base bid target
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Strong pressure: be competitive
        target = max(highest_prev_bid + 2.0, DAILY_SALARY * (0.35 + 0.35 * supply_tightness))
        if hp <= 2.0:
            target = max(target, DAILY_SALARY * 0.85)
    else:
        # Moderate pressure: slightly above typical survival bids
        target = max(DAILY_SALARY * (0.50 + 0.25 * supply_tightness), highest_prev_bid * 0.95 + 1.0)
        if hp <= 2.0:
            target = max(target, DAILY_SALARY * 0.75)

    # Ensure we don't overspend when supply is ample
    if supply >= 21.0:
        target *= 0.92

    # Final cap by budget and reasonable upper bound
    max_reasonable = min(budget, DAILY_SALARY * (1.05 + 0.15 * supply_tightness))
    bid = min(max_reasonable, target)

    # Never bid negative or zero when we can afford something meaningful
    if bid <= 0.0:
        bid = min(budget, DAILY_SALARY * 0.2)

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

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    hp = my_status.get('hp', 0)
    budget = my_status.get('budget', 0)
    no_water_days = my_status.get('no_water_days', 0)

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday's bids from immediate previous_trace only
    prev_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate how many allocations are likely available today
    # (Supply is total pool; each unit of water is auctioned by bid ranking.)
    # Use a coarse mapping to decide aggressiveness.
    supply_int = int(round(supply))
    # how many full requirements could be satisfied by supply
    possible_full = max(1, supply_int // WATER_REQ)

    # If supply is tight (15), competition likely higher; if supply is ample (25), we can bid less.
    tightness = 1.0
    if supply_int >= 22:
        tightness = 0.75
    elif supply_int <= 16:
        tightness = 1.1

    # Determine pressure from opponents' max/avg bids yesterday
    if prev_bids:
        max_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / float(len(prev_bids))
    else:
        max_prev = 0.0
        avg_prev = DAILY_SALARY * 0.5

    # Base bid: target slightly above the typical opponent average,
    # but below the max to avoid inefficient spending.
    # Also react to our HP/no-water days.
    if hp <= 2 or no_water_days >= 2:
        urgency = 1.0
    elif hp <= 4 or no_water_days >= 1:
        urgency = 0.75
    else:
        urgency = 0.55

    # If someone previously bid very high, we may need to match to secure water.
    # Use thresholds relative to DAILY_SALARY.
    high_pressure = 0.0
    if max_prev >= DAILY_SALARY * 1.1:
        high_pressure = 1.0
    elif max_prev >= DAILY_SALARY * 0.85:
        high_pressure = 0.7

    target = avg_prev * (0.95 + 0.15 * tightness) + 0.25 * high_pressure * (max_prev - avg_prev)

    # If supply can satisfy multiple full requirements, lower target slightly.
    if possible_full >= 2:
        target *= 0.9

    # Apply urgency
    target *= (0.85 + 0.3 * urgency)

    # Clamp to reasonable bounds: at least enough to matter, at most budget.
    min_bid = DAILY_SALARY * 0.35
    max_bid = min(budget, DAILY_SALARY * 1.2)

    bid = float(target)
    if bid < min_bid:
        bid = min_bid
    if bid > max_bid:
        bid = max_bid

    # Final safety clamp
    bid = max(0.0, min(float(bid), float(budget)))
    return bid
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

    my_hp = int(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opponents = [o for o in opponents_status.values() if o.get('alive')]
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Immediate reaction to yesterday bids (only previous_trace)
    prev_bids = []
    prev_hp_after = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        if prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass
        if prev.get('hp_after') is not None:
            try:
                prev_hp_after.append(int(prev['hp_after']))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    # Supply pressure: if supply is closer to MIN_SUPPLY, water is scarcer.
    # Map to [0,1] where 0=abundant, 1=scarce.
    scarcity = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0.0:
        scarcity = 0.0
    if scarcity > 1.0:
        scarcity = 1.0

    # Determine base aggressiveness
    # If opponent bids were extremely high, competition is already intense.
    extreme_competition = highest_prev_bid >= DAILY_SALARY * 1.6  # ~144

    # If my hp is low or I have already missed water days, I must secure allocation.
    urgent = (my_hp <= 2) or (my_no_water_days >= 2)

    # Target bid logic
    if urgent:
        # Push near top-of-market but still cap by budget.
        target = DAILY_SALARY * (0.95 + 0.15 * scarcity)
    else:
        if extreme_competition:
            # Bid high enough to not be outcompeted, but undercut slightly.
            # Use avg as anchor and add small premium based on scarcity.
            anchor = avg_prev_bid if avg_prev_bid > 0 else highest_prev_bid
            target = min(anchor + 5.0 * (0.5 + scarcity), DAILY_SALARY * (1.75 + 0.1 * scarcity))
        else:
            # Moderate bid; increase with scarcity.
            target = DAILY_SALARY * (0.55 + 0.35 * scarcity)

    # Convert target to final bid within budget and reasonable bounds.
    # Also avoid bidding above what seems like typical high bids by too much.
    max_reasonable = DAILY_SALARY * 2.0
    target = min(target, max_reasonable)

    final_bid = min(my_budget, target)

    # If budget is tiny, still bid something consistent to possibly win.
    if final_bid <= 0.0:
        final_bid = min(my_budget, DAILY_SALARY * 0.1)

    # Ensure non-negative float
    if final_bid < 0.0:
        final_bid = 0.0

    return float(final_bid)
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
    day = day_context.get('day', 0)

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids for immediate reaction
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                prev_bids.append(float(bid))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Identify Cindy/Alex pressure via yesterday max bid
    # Since we only have previous_trace, use global highest as proxy.

    # Determine how many units likely available; use supply to set aggressiveness
    # If supply is tight relative to WATER_REQ, bidding higher increases chance to secure water.
    supply_ratio = supply / float(WATER_REQ) if WATER_REQ > 0 else 0.0

    # Base target bid: attempt to beat the strongest recent bidder when we can afford it.
    # Use hp/no_water_days to decide whether to spend.
    must_spend = (hp <= 2.5) or (no_water_days >= 1)
    can_afford = budget >= DAILY_SALARY * 0.6

    # Aggression schedule
    if must_spend:
        # Urgent: bid to secure water against Cindy-like aggressor.
        target = max(highest_prev_bid + 3.0, DAILY_SALARY * 0.85)
    else:
        # Non-urgent: only outbid if supply is tight or Cindy was very high yesterday.
        if highest_prev_bid >= DAILY_SALARY * 1.55 or supply_ratio < 2.2:
            target = max(highest_prev_bid + 1.5, DAILY_SALARY * 0.65)
        else:
            # Conservative: bid around mid-level
            target = max(DAILY_SALARY * 0.45, highest_prev_bid * 0.75)

    # Convert to feasible bid within budget and reasonable cap
    # Keep within [0, budget] and avoid overspending.
    cap = min(budget, DAILY_SALARY * 1.8)
    bid = max(0.0, min(cap, target))

    # If budget is very low, bid proportionally to remaining ability
    if budget < DAILY_SALARY * 0.2:
        bid = max(0.0, min(budget, DAILY_SALARY * 0.1))

    return float(bid)
"""
