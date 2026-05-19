# ============================================================
# Experiment: exp_101
# Agent: Bob
# Source: exp_101
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

    supply = day_context['supply']
    day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opponents:
        # If no one else is alive, take enough to secure requirement while conserving budget.
        target = min(my_status['budget'], DAILY_SALARY * 0.4)
        return max(0.0, target)

    # Extract yesterday bids as immediate behavioral signal.
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Fallback if no trace.
    if not yesterday_bids:
        # Conservative default: bid enough to likely clear but not overspend.
        if my_status['hp'] <= 2:
            return min(my_status['budget'], DAILY_SALARY * 0.9)
        return min(my_status['budget'], DAILY_SALARY * 0.55)

    highest_prev_bid = max(yesterday_bids)
    my_hp = my_status.get('hp', 0)
    my_budget = my_status.get('budget', 0)

    # Convert budget to a bid cap; keep within plausible water amounts.
    # We assume bids correlate with water allocation; aim around WATER_REQ.
    # Use supply bounds to avoid bidding above reasonable share.
    supply_cap = max(MIN_SUPPLY, min(MAX_SUPPLY, float(supply)))

    # Aggression thresholds: if opponents were bidding near our salary, scarcity pressure is high.
    high_pressure = highest_prev_bid >= DAILY_SALARY * 0.85

    if high_pressure:
        # If our HP is fragile, we must secure water.
        if my_hp <= 2:
            bid = min(my_budget, DAILY_SALARY * 0.95)
        else:
            # Otherwise, bid aggressively but not maximal.
            bid = min(my_budget, DAILY_SALARY * 0.35 + highest_prev_bid * 0.25)
    else:
        # Opponents were not fighting hard: underbid slightly above requirement.
        # Use their highest bid to stay competitive without wasting budget.
        base = max(WATER_REQ, highest_prev_bid + 1.0)
        # Cap by a fraction of salary to control spending.
        bid = min(my_budget, DAILY_SALARY * 0.55, base)

    # Ensure bid is within [0, supply_cap] range to avoid nonsensical oversized offers.
    if bid < 0:
        bid = 0.0
    bid = min(float(bid), float(supply_cap))

    # If we have consecutive no-water days, increase bid to prevent elimination.
    no_water_days = my_status.get('no_water_days', 0)
    if no_water_days >= 2:
        # Emergency: bid toward salary cap.
        bid = min(my_budget, DAILY_SALARY * (0.75 if my_hp > 2 else 0.95), float(supply_cap))

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
    day = day_context.get('day', 0)

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Extract yesterday bids to infer aggressiveness.
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

    # Base urgency: if low HP or already no-water days, bid more.
    urgency = 0.0
    if my_hp <= 2:
        urgency = 1.0
    elif my_hp <= 4:
        urgency = 0.7
    elif my_hp <= 6:
        urgency = 0.4
    else:
        urgency = 0.25

    if my_no_water_days >= 2:
        urgency = min(1.0, urgency + 0.25)

    # Supply pressure: lower supply means fewer units; bid to secure water.
    # Map supply to [0,1] where 1 = tightest.
    if MAX_SUPPLY > MIN_SUPPLY:
        tightness = 1.0 - (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        tightness = 0.5
    tightness = max(0.0, min(1.0, float(tightness)))

    # Use yesterday's highest bid to decide whether to outbid.
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # If someone bid very high yesterday (likely desperation), avoid overbidding like Alex.
    # Instead, aim just above typical aggressive level.
    # Compute a target multiplier.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # High desperation observed; bid moderately high but not maximal.
        target = DAILY_SALARY * (0.45 + 0.35 * urgency + 0.15 * tightness)
        # Slightly react upward if my HP is critical.
        if my_hp <= 2:
            target = DAILY_SALARY * (0.65 + 0.2 * tightness)
    else:
        # Normal/medium competition: bid around mid-high to beat Cindy-like moderate aggressors.
        target = DAILY_SALARY * (0.55 + 0.25 * urgency + 0.2 * tightness)

        # If yesterday highest bid was moderate, try to be above it by a small margin.
        if highest_prev_bid > 0:
            target = max(target, highest_prev_bid + 2.0)

    # Cap target to budget and avoid reckless spending.
    # Keep a safety reserve so we don't repeat Alex's bankruptcy pattern.
    safety_reserve = DAILY_SALARY * 0.15
    max_affordable = max(0.0, my_budget - safety_reserve)
    bid = min(my_budget, max_affordable, target)

    # If budget is low, still bid enough to prevent imminent death.
    if my_hp <= 1 and my_budget > 0:
        bid = min(my_budget, DAILY_SALARY * 0.9)

    # Ensure non-negative.
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

    # Alive opponents
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append((opp_id, opp))

    # If no one alive, conserve budget
    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Read yesterday bids from immediate previous_trace
    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Estimate a competitive threshold from yesterday
    # Typical strong bids appear around 70-100; avoid chasing extreme bids.
    if yesterday_bids:
        sorted_bids = sorted(yesterday_bids)
        # median-ish, plus small bump
        mid = sorted_bids[len(sorted_bids)//2]
        # If someone bid very high, only react slightly since we have good hp.
        highest = sorted_bids[-1]
        target = mid + 5.0
        if highest > DAILY_SALARY * 2.0:
            target = min(highest * 0.55, target)
    else:
        target = DAILY_SALARY * 0.6

    # Urgency adjustments
    if hp <= 2.0 or no_water_days >= 2:
        # Need water now
        target = max(target, DAILY_SALARY * 0.9)
    elif hp <= 4.0:
        target = max(target, DAILY_SALARY * 0.7)

    # Supply pressure: when supply is near lower bound, increase bid slightly
    # (We don't know exact allocation rule; just make it robust.)
    if supply <= 18.0:
        target += 5.0

    # Cap bid to avoid bankruptcy; keep some budget for later days
    # With 10-day episode, a conservative cap works.
    remaining_days = max(1, int(10 - day))
    per_day_budget_cap = budget / float(remaining_days)
    cap = min(budget, max(DAILY_SALARY * 1.2, per_day_budget_cap))

    bid = min(cap, target)

    # Ensure non-negative and at least a minimal participation bid
    if bid < 0.0:
        bid = 0.0
    if bid == 0.0 and budget > 0.0:
        bid = min(budget, DAILY_SALARY * 0.25)

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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # If no opponents alive, conserve budget.
    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Use yesterday traces only for immediate reaction.
    prev_bids = []
    prev_high_pressure = 0.0
    for o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                b_val = float(b)
                prev_bids.append(b_val)
                if b_val > prev_high_pressure:
                    prev_high_pressure = b_val
            except Exception:
                pass

    # Supply pressure: higher supply reduces need to overbid.
    # Normalize supply to [0,1].
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_norm = 0.5
    supply_norm = max(0.0, min(1.0, float(supply_norm)))

    # Determine how many water units are likely available.
    # Use int() indices safety where needed.
    expected_units = int(supply // float(WATER_REQ)) if WATER_REQ > 0 else 0
    expected_units = max(0, expected_units)

    # Estimate how many bidders might compete: use alive opponents count.
    n_competing = len(alive_opps)

    # Base bid target: moderate aggressiveness.
    # If supply is low (fewer units), bid higher; if high, bid lower.
    # Also react to our hp/no-water streak.
    if my_hp <= 2 or my_no_water_days >= 2:
        urgency = 1.0
    elif my_hp <= 4 or my_no_water_days >= 1:
        urgency = 0.7
    else:
        urgency = 0.4

    # If yesterday someone bid very high, we avoid being outcompeted completely.
    # If yesterday bids were mostly low, we can bid slightly above low threshold.
    if prev_bids:
        prev_max = max(prev_bids)
        prev_avg = sum(prev_bids) / float(len(prev_bids))
    else:
        prev_max = 0.0
        prev_avg = 0.0

    # Convert expected units to a competition factor.
    # If expected_units is 0, we must fight hard.
    if expected_units <= 0:
        unit_pressure = 1.0
    else:
        # More units => less pressure.
        # Use ratio of competitors per unit.
        unit_pressure = min(1.0, float(n_competing) / float(max(1, expected_units)))

    # Target bid scale.
    # Keep below typical top bids (Cindy/David survived with very high bids), but above low-bid deaths.
    # Use DAILY_SALARY multipliers.
    # When pressure high, bid toward ~0.75-0.95 salary.
    # When pressure low, bid ~0.45-0.65 salary.
    pressure = 0.55 * unit_pressure + 0.45 * (1.0 - supply_norm)
    base_multiplier = 0.45 + 0.35 * pressure

    # React to previous max bid: if others were willing to spend heavily, nudge upward.
    # If prev_max is huge, we don't match it; just increase enough to avoid losing.
    if prev_max >= DAILY_SALARY * 1.2:
        base_multiplier += 0.10
    elif prev_max >= DAILY_SALARY * 0.85:
        base_multiplier += 0.05

    # Apply urgency.
    multiplier = base_multiplier + 0.25 * (urgency - 0.4)
    multiplier = max(0.35, min(0.98, float(multiplier)))

    target = DAILY_SALARY * multiplier

    # If our budget is small, scale down but still try to secure water when urgent.
    if my_budget <= 0.0:
        return 0.0

    # Ensure we don't exceed budget.
    bid = min(my_budget, target)

    # If we are very healthy and supply seems abundant, bid slightly lower to save budget.
    if my_hp >= 7 and my_no_water_days == 0 and supply_norm >= 0.7:
        bid = min(bid, DAILY_SALARY * 0.55)

    # If we are in danger, push up to a floor.
    if my_hp <= 3 or my_no_water_days >= 2:
        bid = max(bid, min(my_budget, DAILY_SALARY * 0.85))

    # Final clamp.
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # If no opponents alive, bid conservatively
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace for immediate reaction
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Supply pressure: higher supply means more water per unit allocation, so we can bid a bit more safely.
    # Normalize supply to [0,1]
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_norm = 0.5
    supply_norm = max(0.0, min(1.0, supply_norm))

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    no_water_days = int(my_status.get('no_water_days', 0))

    # Estimate how many consecutive days we can tolerate without water (roughly)
    # If no_water_days is high, increase bid to avoid death.
    urgency = 0.0
    if my_hp <= 2:
        urgency += 0.8
    elif my_hp <= 4:
        urgency += 0.45
    else:
        urgency += 0.2

    if no_water_days >= 2:
        urgency += 0.25
    if no_water_days >= 3:
        urgency += 0.35

    # If someone previously bid very high, match/beat slightly to deny them.
    # Cindy survived but ran out of budget -> likely to bid aggressively; we should not let her take all.
    # Use highest_prev_bid as a proxy for their current aggression.
    aggression_threshold = DAILY_SALARY * 0.85

    # Base bid: mid-level, scaled by supply and urgency
    base = DAILY_SALARY * (0.45 + 0.25 * supply_norm + 0.35 * urgency)

    # If yesterday saw high bids, add a small premium to stay competitive.
    if highest_prev_bid >= aggression_threshold:
        # If I'm in danger, bid closer to top; else just a bit above.
        premium = 0.08 * highest_prev_bid
        if my_hp <= 3 or no_water_days >= 2:
            premium = 0.15 * highest_prev_bid
        target = base + premium
    else:
        # Otherwise, lightly track the highest previous bid to avoid being undercut.
        # Keep it bounded to prevent budget collapse.
        target = max(base, 0.55 * highest_prev_bid + 0.25 * DAILY_SALARY)

    # Hard caps to avoid overbidding beyond budget and avoid suicidal spending.
    # Since daily_salary is 90, typical safe cap ~ 0.9*salary unless in critical hp.
    if my_hp <= 2:
        cap = DAILY_SALARY * 0.95
    elif my_hp <= 4:
        cap = DAILY_SALARY * 0.85
    else:
        cap = DAILY_SALARY * 0.7

    bid = float(min(my_budget, cap, target))

    # Ensure at least a small positive bid if budget allows (avoid wasting turns when supply is favorable)
    if bid < 1e-6:
        bid = float(min(my_budget, DAILY_SALARY * 0.2))

    return bid
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

    # Identify alive opponents and their yesterday bids
    alive_opps = []
    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {}) or {}
            if prev.get('bid') is not None:
                yesterday_bids.append(float(prev['bid']))

    # Baseline: aim for survival; if low HP or on no-water streak, bid more.
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # If supply is low, competition is harsher; bid more.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Use yesterday's aggressor signal to avoid being underbid when others overspend.
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If someone was bidding near/above typical daily salary, they likely forced water.
        pressure = 1.0 if highest_prev_bid >= DAILY_SALARY * 0.85 else 0.0
    else:
        pressure = 0.0
        highest_prev_bid = 0.0

    # Decide target bid level
    if hp <= 2 or no_water_days >= 2:
        # Critical survival mode
        base = DAILY_SALARY * (0.85 + 0.1 * (1.0 - supply_ratio))
    elif hp <= 4 or no_water_days == 1:
        base = DAILY_SALARY * (0.65 + 0.15 * (1.0 - supply_ratio))
    else:
        base = DAILY_SALARY * (0.55 + 0.10 * (1.0 - supply_ratio))

    # If yesterday had extreme high bids, nudge upward but cap well below max to avoid wars.
    if pressure > 0.0:
        base = max(base, DAILY_SALARY * 0.75)

    # Additional small adjustment: if supply is enough to cover at most 2 requirements, competition is tighter.
    # We avoid using float indices; this is numeric only.
    max_units = int(supply / WATER_REQ)  # int floor
    if max_units <= 1:
        base *= 1.10

    # Final bid with budget cap
    bid = min(budget, base)

    # Ensure non-negative and at least a minimal amount if budget allows
    if bid < 0.0:
        bid = 0.0

    # If budget is tiny, bid what we can.
    if budget <= DAILY_SALARY * 0.2:
        bid = min(budget, DAILY_SALARY * 0.4)

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

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    # If no opponents alive, bid as needed but stay budget-safe.
    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from immediate previous_trace.
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict) and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # Estimate a competitive target: slightly above the upper-middle yesterday bid.
    # This aims to outbid Cindy when she pressures, but avoid matching her highest bids.
    if yesterday_bids:
        yesterday_bids_sorted = sorted(yesterday_bids)
        # Choose 70th percentile-ish index without float indexing.
        k = int(0.7 * (len(yesterday_bids_sorted) - 1)) if len(yesterday_bids_sorted) > 1 else 0
        target = float(yesterday_bids_sorted[k])
        # If Cindy-like pressure existed (very high bid), don't fully mirror; add a small premium.
        highest = float(max(yesterday_bids_sorted))
        if highest >= DAILY_SALARY * 1.4:
            desired = min(highest * 0.78, target + 6.0)
        else:
            desired = target + 3.0
    else:
        desired = DAILY_SALARY * 0.55

    # Risk control based on my HP and consecutive no-water days.
    # If I'm low HP or already accumulating no-water days, increase bid.
    if my_hp <= 2.0 or my_no_water_days >= 2:
        desired *= 1.35
    elif my_hp <= 4.0:
        desired *= 1.15

    # Supply-aware adjustment: higher supply reduces need to overbid.
    # supply is in [15,25]; map to a factor.
    if supply >= 22.0:
        desired *= 0.92
    elif supply <= 17.0:
        desired *= 1.08

    # Budget cap and non-negative.
    bid = max(0.0, min(my_budget, desired))

    # Ensure we don't bid trivially low when we still need water.
    # If my budget allows, keep a minimum bid threshold.
    min_reasonable = DAILY_SALARY * 0.35
    if my_budget >= min_reasonable:
        bid = max(bid, min_reasonable)

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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    # Alive opponents
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    # If no opponents, take what we can afford
    if not alive_opps:
        return max(0.0, min(float(my_status.get('budget', 0.0)), DAILY_SALARY * 0.4))

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))

    # Read yesterday bids from previous_trace for immediate reaction
    prev_bids = []
    for _, opp in alive_opps:
        pt = opp.get('previous_trace', {}) or {}
        b = pt.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate how many shares we likely need: if supply is tight, bid more.
    # supply is in [15,25] so integer shares are 1 or 2.
    # We target securing at least 1 unit of water requirement.
    if supply <= WATER_REQ + 1e-9:
        scarcity_factor = 1.0
    else:
        # More supply -> less urgency
        # Map supply in [15,25] to [1.0,0.6]
        scarcity_factor = 1.0 - 0.4 * ((supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY))
        if scarcity_factor < 0.6:
            scarcity_factor = 0.6
        if scarcity_factor > 1.0:
            scarcity_factor = 1.0

    # If someone previously overbid heavily, avoid matching; instead bid enough to not be starved.
    # Cindy averaged ~133 and died; David bid 0 and died; Eric survived with ~68.
    aggressive_threshold = DAILY_SALARY * 0.85  # 76.5

    # Base bid policy
    if my_hp <= 2.0:
        base = DAILY_SALARY * 0.95
    elif my_hp <= 4.0:
        base = DAILY_SALARY * 0.75
    else:
        base = DAILY_SALARY * 0.55

    # Adjust based on yesterday's max bid (proxy for opponent aggressiveness)
    if highest_prev_bid >= aggressive_threshold:
        # Don't overpay: reduce compared to base, but still scale by scarcity.
        base *= 0.85
    else:
        # If yesterday bids were calmer, slightly increase to capture share.
        base *= 1.05

    target = base * scarcity_factor

    # Budget cap
    if my_budget <= 0.0:
        return 0.0

    # Ensure non-negative and not above budget
    bid = max(0.0, min(my_budget, target))

    # Small floor to avoid bidding too low when supply is scarce
    if scarcity_factor >= 0.9 and bid < DAILY_SALARY * 0.35:
        bid = min(my_budget, DAILY_SALARY * 0.35)

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

    # Identify alive opponents and extract yesterday bids
    alive_ids = []
    yesterday_bids = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_ids.append(oid)
            prev = o.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev.get('bid'))

    # If no one is alive, bid conservatively
    if not alive_ids:
        return max(0, min(my_status['budget'], int(DAILY_SALARY * 0.4)))

    # Use yesterday's max bid as a proxy for current aggressiveness
    # (We avoid overpaying like Alex did; we only slightly exceed a likely clearing bid.)
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how many water units might be needed to secure at least one allocation
    # (Assume each unit is WATER_REQ; approximate capacity)
    # Ensure safe float math; no list indexing used.
    capacity_units = max(1.0, supply / float(WATER_REQ))

    # Base bid policy: moderate bid unless our hp is low.
    # If others were bidding high yesterday, we bid just below the top to avoid a bidding war.
    if my_status['hp'] <= 2:
        urgency = 1.0
    elif my_status['hp'] <= 4:
        urgency = 0.75
    else:
        urgency = 0.55

    # If supply is tight, we increase bid slightly.
    tightness = 0.0
    if supply <= (MIN_SUPPLY + 1):
        tightness = 0.15
    elif supply <= (MIN_SUPPLY + 5):
        tightness = 0.08

    # Target clearing bid: aim around 60-80% of highest_prev_bid, but at least a floor.
    # If highest_prev_bid is very high, do not chase it fully.
    if highest_prev_bid > 0:
        target = highest_prev_bid * (0.68 + 0.1 * urgency)  # 0.68..0.78
    else:
        target = DAILY_SALARY * 0.55

    # Add a small premium when capacity is low (fewer allocations)
    # capacity_units near 1 => more competitive
    competitiveness = max(0.0, min(1.0, 1.5 - capacity_units))
    target = target * (1.0 + 0.25 * competitiveness)

    # Apply urgency and tightness
    target = target * (0.85 + 0.3 * urgency + tightness)

    # Budget and non-negative constraints
    max_affordable = my_status['budget']
    # Avoid spending everything unless critically low hp
    spend_cap = 0.95 if my_status['hp'] <= 2 else 0.7
    bid = int(min(max_affordable * spend_cap, target))

    # Ensure at least some reasonable bid if we have budget
    min_bid = 1
    if my_status['budget'] >= 10:
        min_bid = int(max(1, DAILY_SALARY * 0.25))
    bid = max(min_bid, bid)

    # If we have many no-water days, we should be more aggressive
    if my_status.get('no_water_days', 0) >= 2:
        bid = int(min(max_affordable * 0.85, bid * 1.25))

    # Final clamp
    bid = max(0, min(bid, max_affordable))
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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    if not alive_opponents:
        return float(min(my_budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from immediate previous_trace
    yesterday_bids = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Determine pressure level from yesterday
    aggressive = highest_prev_bid >= DAILY_SALARY * 0.85

    # Supply-based aggressiveness: closer to MAX_SUPPLY means more water likely, so bid slightly lower.
    supply_ratio = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Base target bid
    if aggressive:
        if my_hp > 4.0 and my_no_water_days <= 1:
            # Stay just under their aggressive ceiling to win without overspending
            target = min(my_budget, DAILY_SALARY * (0.28 + 0.12 * (1.0 - supply_ratio)))
        else:
            # If I'm under pressure, match the aggressive band
            target = min(my_budget, DAILY_SALARY * (0.85 + 0.05 * (1.0 - supply_ratio)))
    else:
        if my_hp <= 2.5 or my_no_water_days >= 2:
            target = min(my_budget, DAILY_SALARY * 0.9)
        else:
            # Conservative when others weren't bidding hard
            target = min(my_budget, max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5))

    # If supply is tight (near MIN_SUPPLY), increase bid modestly
    if supply <= (MIN_SUPPLY + 2.0):
        target = min(my_budget, target * 1.08)

    # Final safety clamps
    if my_budget <= 0.0:
        return 0.0

    # Ensure bid is non-negative
    if target < 0.0:
        target = 0.0

    return float(target)
"""
