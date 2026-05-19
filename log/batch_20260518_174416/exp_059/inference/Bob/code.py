# ============================================================
# Experiment: exp_059
# Agent: Bob
# Source: exp_059
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

    # Collect alive opponents and their yesterday bids
    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    # If no opponents, bid a safe amount to cover requirement
    if not alive_opponents:
        target = WATER_REQ
        return max(0.0, min(float(my_status.get('budget', 0.0)), target))

    yesterday_bids = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Determine how aggressive opponents were yesterday
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_highest_prev_bid = 0.0
    if len(yesterday_bids) >= 2:
        sorted_bids = sorted(yesterday_bids, reverse=True)
        second_highest_prev_bid = sorted_bids[1]

    my_budget = float(my_status.get('budget', 0.0))
    my_hp = float(my_status.get('hp', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0) or 0)

    # Estimate how many units we need to stay safe.
    # If we're already in bad shape, we bid more aggressively.
    urgency = 0.0
    if my_hp <= 2:
        urgency += 1.0
    if my_no_water_days >= 2:
        urgency += 0.7
    if my_no_water_days >= 3:
        urgency += 0.8

    # Supply-based scaling: lower supply => higher bid.
    # day_context supply is float; keep arithmetic safe.
    supply_f = float(supply)
    supply_ratio = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_ratio = (supply_f - float(MIN_SUPPLY)) / float(MAX_SUPPLY - MIN_SUPPLY)
    # supply_ratio in [0,1]; clamp
    if supply_ratio < 0.0:
        supply_ratio = 0.0
    if supply_ratio > 1.0:
        supply_ratio = 1.0
    scarcity = 1.0 - supply_ratio

    # Base target bid level
    # If opponents were bidding very high yesterday, they likely expect scarcity.
    # We respond with a moderate-to-high bid, but cap by budget.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # They were near-max; avoid overpaying unless we're critical.
        if urgency >= 1.0:
            bid = DAILY_SALARY * (0.55 + 0.25 * scarcity)
        else:
            bid = DAILY_SALARY * (0.35 + 0.20 * scarcity)
        # Slightly outbid the second-highest to increase chance of allocation
        if second_highest_prev_bid > 0.0:
            bid = max(bid, second_highest_prev_bid + 2.0)
    elif highest_prev_bid >= DAILY_SALARY * 0.55:
        # Medium aggression: bid to compete
        bid = DAILY_SALARY * (0.45 + 0.25 * scarcity) + urgency * DAILY_SALARY * 0.15
        if highest_prev_bid > 0.0:
            bid = max(bid, highest_prev_bid + 1.0)
    else:
        # Opponents were not aggressive: we can secure allocation with higher bid
        bid = DAILY_SALARY * (0.60 + 0.25 * scarcity) + urgency * DAILY_SALARY * 0.10
        if highest_prev_bid > 0.0:
            bid = max(bid, highest_prev_bid + 1.5)

    # Ensure bid is at least enough to cover our requirement when possible.
    # In this game, bid translates to water allocation; we bias toward WATER_REQ.
    # Cap bid to budget.
    min_reasonable = float(WATER_REQ)
    if bid < min_reasonable:
        bid = min_reasonable + urgency * 2.0

    # Final cap and floor
    if my_budget <= 0.0:
        return 0.0
    if bid > my_budget:
        bid = my_budget
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for agent_id, st in opponents_status.items():
        if st.get('alive', False):
            alive_opps.append((agent_id, st))

    if not alive_opps:
        # Conservative fallback
        return min(budget, DAILY_SALARY * 0.4)

    # Extract yesterday bids to infer their aggressiveness
    prev_bids = []
    for _, st in alive_opps:
        prev = st.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # If no trace info, use supply-based baseline
    if not prev_bids:
        if supply <= float(MIN_SUPPLY):
            target = DAILY_SALARY * 0.65
        else:
            target = DAILY_SALARY * 0.55
    else:
        highest_prev_bid = max(prev_bids)
        avg_prev_bid = sum(prev_bids) / float(len(prev_bids))

        # Their survival with high bids suggests a competitive market.
        # If they were bidding near/above salary, bid in that neighborhood.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if hp <= 2 or no_water_days >= 2:
                target = DAILY_SALARY * 0.95
            else:
                target = DAILY_SALARY * 0.70
        else:
            # Otherwise, slightly over average to maintain a competitive edge.
            target = max(avg_prev_bid + 2.0, DAILY_SALARY * 0.55)

        # Supply pressure: with higher supply, we can shade down a bit.
        # With lower supply, shade up.
        if supply <= float(WATER_REQ):
            target *= 1.10
        elif supply <= float(MIN_SUPPLY):
            target *= 1.05
        elif supply >= float(MAX_SUPPLY):
            target *= 0.95

    # Budget/hp risk management
    if hp <= 1 or no_water_days >= 3:
        # Must secure water
        cap = DAILY_SALARY * 1.05
    elif hp <= 3 or no_water_days >= 2:
        cap = DAILY_SALARY * 0.85
    else:
        cap = DAILY_SALARY * 0.75

    # Additional guard: never bid above what we can afford
    bid = min(budget, cap, target)

    # Ensure non-negative and at least small positive when budget allows
    if bid < 1.0 and budget >= 1.0:
        bid = min(budget, 1.0)

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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return float(min(my_budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from immediate previous_trace
    opp_prev_bids = []
    for opp_id, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                opp_prev_bids.append((opp_id, float(b)))
            except Exception:
                pass

    # Identify the most aggressive opponent yesterday (likely Alex)
    if opp_prev_bids:
        opp_prev_bids.sort(key=lambda x: x[1], reverse=True)
        top_opp_id, top_bid = opp_prev_bids[0]
    else:
        top_opp_id, top_bid = None, 0.0

    # Pressure estimate: if top bid was high, we must bid enough to beat it.
    # Use a slightly undercut strategy to win without overpaying.
    # Typical Alex behavior: avg ~65.5, max ~70.
    if top_bid >= DAILY_SALARY * 0.75:
        target = top_bid - 2.0
    elif top_bid > 0:
        target = max(top_bid * 0.9, DAILY_SALARY * 0.5)
    else:
        target = DAILY_SALARY * 0.55

    # If supply is low, water is more scarce; increase bid slightly.
    # supply in [15,25]; map to scarcity factor.
    scarcity = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    target = target * (1.0 + 0.12 * scarcity)

    # If my hp is low or I'm accumulating no-water days, bid more to secure survival.
    if my_hp <= 2.5 or my_no_water_days >= 2:
        target = max(target, DAILY_SALARY * 0.85)
    elif my_hp <= 4.0:
        target = max(target, DAILY_SALARY * 0.65)

    # Budget cap: never exceed what we can pay.
    bid = float(min(my_budget, target))

    # Also avoid bidding trivially low when we have budget and need water.
    min_reasonable = DAILY_SALARY * 0.35
    if my_budget > min_reasonable and bid < min_reasonable and my_hp > 2.5:
        bid = min_reasonable

    # Ensure non-negative.
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

    # Identify alive opponents and extract yesterday bids
    alive_opps = []
    yesterday_bids = []
    for agent_id, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(agent_id)
            prev = o.get('previous_trace', {}) or {}
            if prev.get('bid') is not None:
                try:
                    yesterday_bids.append(float(prev.get('bid')))
                except Exception:
                    pass

    # If no one alive, conserve
    if not alive_opps:
        return max(0.0, min(float(my_status['budget']), DAILY_SALARY * 0.4))

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Pressure estimate from yesterday
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    median_prev_bid = 0.0
    if yesterday_bids:
        s = sorted(yesterday_bids)
        mid = len(s) // 2
        median_prev_bid = float(s[mid])

    # Base target: aim to secure water when supply is tight.
    # Convert supply to an approximate number of full water units available.
    # (We don't know exact payoff mapping; this is a heuristic.)
    supply_units = int(supply / float(WATER_REQ))  # int index safety
    # If supply is below one requirement, we must fight harder.
    tight = supply < float(WATER_REQ)

    # Decide aggressiveness
    # Cindy likely overbids; we try to slightly undercut her typical pressure.
    # If she was the highest bidder yesterday, raise bid; otherwise moderate.
    pressure = highest_prev_bid

    # Core bid heuristic
    # - When our HP is low or we have consecutive no-water days, bid more.
    # - Otherwise, bid to beat typical competition but avoid draining budget.
    if hp <= 2 or no_water_days >= 2:
        aggressiveness = 0.95
    elif hp <= 4 or no_water_days == 1:
        aggressiveness = 0.75
    else:
        aggressiveness = 0.55

    if tight:
        aggressiveness = min(0.98, aggressiveness + 0.15)

    # Map pressure to bid: if competition was fierce, bid near 60-85% of their max.
    if pressure > 0:
        target = pressure * aggressiveness
    else:
        target = DAILY_SALARY * aggressiveness

    # Ensure we don't bid absurdly high; cap by a fraction of budget and salary.
    # Use supply to scale a bit: higher supply reduces urgency.
    supply_scale = (float(MAX_SUPPLY) - supply) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_scale = max(0.0, min(1.0, supply_scale))

    # Final cap: if supply is high, be more conservative.
    conservative_cap = DAILY_SALARY * (0.35 + 0.35 * supply_scale)
    hard_cap = min(budget, conservative_cap)

    # If yesterday pressure was extremely high, we may need to exceed hard_cap slightly.
    # But only if our budget allows and HP is not critical.
    if highest_prev_bid > DAILY_SALARY * 1.3:
        # Cindy-like behavior: push up a bit.
        hard_cap = min(budget, DAILY_SALARY * (0.55 + 0.25 * supply_scale))

    bid = min(target, hard_cap)

    # If bid becomes too low while HP is critical, bump to near-max affordability.
    if (hp <= 2 or no_water_days >= 2) and bid < DAILY_SALARY * 0.6:
        bid = min(budget, DAILY_SALARY * 0.9)

    # Never negative
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    hp = my_status.get('hp', 0)
    budget = my_status.get('budget', 0.0)
    no_water_days = my_status.get('no_water_days', 0)

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    # If no opponents alive, conserve.
    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace for immediate reaction.
    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Estimate target bid level from yesterday.
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        median_prev_bid = sorted(yesterday_bids)[len(yesterday_bids)//2]
    else:
        highest_prev_bid = 0.0
        median_prev_bid = 0.0

    # Supply pressure: higher supply implies we can bid less.
    # Map supply into [0,1] where 0 at MIN_SUPPLY and 1 at MAX_SUPPLY.
    try:
        supply_norm = (float(supply) - float(MIN_SUPPLY)) / (float(MAX_SUPPLY) - float(MIN_SUPPLY))
    except Exception:
        supply_norm = 0.5
    if supply_norm < 0.0:
        supply_norm = 0.0
    if supply_norm > 1.0:
        supply_norm = 1.0

    # Decide aggressiveness.
    # If I'm close to death or have already missed water, bid aggressively.
    # Otherwise, bid around the median/high band to beat typical survivors.
    if hp <= 2 or no_water_days >= 2:
        # Aggressive: try to outbid the highest observed.
        base = max(median_prev_bid, highest_prev_bid)
        # Add a small increment to likely win.
        target = base + 8.0
    elif hp <= 3:
        target = max(median_prev_bid, highest_prev_bid * 0.9) + 4.0
    else:
        # Conservative to preserve budget: bid near median, slightly above if supply is tighter.
        # When supply is low, increase bid.
        tighten = 1.0 - supply_norm
        target = max(median_prev_bid, 0.0) + 10.0 * tighten
        # If yesterday's highest was very high, we must respond.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            target = max(target, highest_prev_bid + 2.0)

    # Cap target by budget and a reasonable multiple of salary.
    # (Game likely pays/uses salary as a practical upper bound.)
    max_reasonable = DAILY_SALARY * 1.2
    target = min(target, max_reasonable)
    if budget < target:
        target = budget

    # Ensure non-negative.
    if target < 0.0:
        target = 0.0

    return float(target)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    # Alive opponents
    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append(o)

    if not alive_opponents:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Extract yesterday bids
    yesterday_bids = []
    for o in alive_opponents:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Pressure signal from yesterday
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # If someone yesterday bid close to/above our daily_salary, assume aggressive competition today
    aggressive_threshold = DAILY_SALARY * 0.85

    # Determine target bid based on our hp and observed aggression
    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))

    # Base aggressiveness scales with hp
    if hp <= 2:
        safety_factor = 0.95
    elif hp <= 4:
        safety_factor = 0.80
    else:
        safety_factor = 0.60

    if highest_prev_bid >= aggressive_threshold:
        # Match competition but don't burn budget: slightly above their likely floor
        target = min(budget, DAILY_SALARY * 0.30 + highest_prev_bid * 0.15)
        # If we are very low hp, spend more
        if hp <= 2:
            target = min(budget, DAILY_SALARY * 0.90)
    else:
        # Moderate bid: aim to outbid typical mid bidders without overpaying
        # Also scale with supply: when supply is higher, competition may be lower
        supply_ratio = (supply - 15.0) / (25.0 - 15.0) if (25.0 - 15.0) != 0 else 0.5
        # supply_ratio in [0,1], higher supply => reduce bid slightly
        target = DAILY_SALARY * (0.56 * (1.0 - supply_ratio) + 0.44 * supply_ratio) * safety_factor
        # Ensure we bid at least a meaningful fraction of DAILY_SALARY
        target = max(target, DAILY_SALARY * 0.35)
        target = min(budget, target)

    # If budget is too low, bid what we can
    if budget <= 0:
        return 0.0

    # Final clamp: bids shouldn't exceed remaining budget
    if target > budget:
        target = budget
    if target < 0:
        target = 0.0

    return float(target)
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

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Collect yesterday bids from alive opponents only.
    alive_opps = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opps.append(opp)

    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how many bidders might be competing: higher supply reduces need to overbid.
    # Use only simple thresholds; avoid float->index issues.
    # supply_ratio in [0,1]
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_ratio = 0.5
    if supply_ratio < 0.0:
        supply_ratio = 0.0
    if supply_ratio > 1.0:
        supply_ratio = 1.0

    # Base aggressiveness: if others were bidding high yesterday, they likely continue.
    # We'll try to slightly undercut/keep pressure without fully matching.
    # Target bid scale depends on my HP and no_water_days.
    if hp <= 2:
        urgency = 1.0
    elif hp <= 4:
        urgency = 0.75
    else:
        urgency = 0.45

    if no_water_days >= 2:
        urgency = min(1.0, urgency + 0.2)

    # If their highest yesterday bid was very high, increase our bid.
    if highest_prev_bid >= DAILY_SALARY * 1.45:  # ~130+ 
        pressure = 0.85
    elif highest_prev_bid >= DAILY_SALARY * 1.15:  # ~100+
        pressure = 0.65
    else:
        pressure = 0.45

    # Adjust for supply: with more supply, we can bid less.
    # effective_multiplier decreases as supply increases.
    effective_multiplier = pressure * (0.85 - 0.25 * supply_ratio) + urgency * (0.15 + 0.1 * (1.0 - supply_ratio))

    # Convert multiplier to a bid around salary scale.
    target = DAILY_SALARY * effective_multiplier

    # Safety caps: never exceed budget.
    if budget <= 0.0:
        return 0.0

    # If my HP is very low, ensure we bid close to high-pressure range.
    if hp <= 2 and highest_prev_bid >= DAILY_SALARY * 1.15:
        target = max(target, DAILY_SALARY * 0.88)

    # If my HP is safe, keep bids moderate to conserve budget.
    if hp >= 6 and highest_prev_bid < DAILY_SALARY * 1.15:
        target = min(target, DAILY_SALARY * 0.55)

    # Final bid: small increment to avoid ties when others are aggressive.
    # Use +1.5 as in example.
    tie_break = 1.5 if highest_prev_bid >= DAILY_SALARY * 1.15 else 0.5
    target = target + tie_break

    # Ensure within budget.
    if target > budget:
        target = budget

    # Also avoid bidding above a plausible max; keep it bounded.
    max_reasonable = DAILY_SALARY * 1.7
    if target > max_reasonable:
        target = max_reasonable

    # Return as float.
    return float(target)
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
    day = day_context.get('day', 0)

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return float(min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace for immediate reaction
    yesterday_bids = []
    yesterday_hp_after = []
    for opp_id, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid', 0.0)))
            except Exception:
                pass
            try:
                yesterday_hp_after.append(int(prev.get('hp_after', opp.get('hp', 0))))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    # Base target: aim slightly below the strong bidders to conserve budget.
    # If we see very high bids yesterday, we must raise to avoid losing.
    if highest_prev_bid >= DAILY_SALARY * 0.9:
        base = DAILY_SALARY * 0.75
    elif highest_prev_bid >= DAILY_SALARY * 0.65:
        base = DAILY_SALARY * 0.68
    else:
        base = DAILY_SALARY * 0.58

    # If we are under pressure (low hp or accumulating dry days), bid more.
    if hp <= 2 or no_water_days >= 2:
        base *= 1.25
    elif hp <= 4:
        base *= 1.10

    # If we are comfortably healthy, bid less.
    if hp >= 8 and no_water_days == 0:
        base *= 0.85

    # Supply-aware adjustment: with lower supply, competition is tighter.
    if supply <= float(MIN_SUPPLY):
        base *= 1.10
    elif supply >= float(MAX_SUPPLY):
        base *= 0.95

    # Ensure we don't overshoot budget.
    bid = min(budget, base)

    # Add a small increment if yesterday suggests others were just barely winning.
    # This helps us beat close contests without matching their full aggression.
    if highest_prev_bid > 0:
        # If our bid is far below their top bid, push closer.
        if bid < highest_prev_bid * 0.85:
            bid = min(budget, highest_prev_bid * 0.9)
        # If our bid is too close but still likely losing, nudge.
        if bid < highest_prev_bid and bid + 2.0 <= budget:
            bid = bid + 2.0

    # Final clamp: non-negative and not exceeding budget
    if bid < 0.0:
        bid = 0.0
    if bid > budget:
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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive = []
    for aid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((aid, o))

    if not alive:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Read yesterday bids from previous_trace only (immediate reaction)
    prev_bids = []
    for aid, o in alive:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate pressure from yesterday
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    # Our target bid: aim to beat likely non-Cindy bids but avoid Cindy's extreme spending
    # Use supply as a rough proxy: when supply is high, we can bid less.
    supply_norm = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (supply - float(MIN_SUPPLY)) / float(MAX_SUPPLY - MIN_SUPPLY)
    if supply_norm < 0.0:
        supply_norm = 0.0
    if supply_norm > 1.0:
        supply_norm = 1.0

    # Base aggressiveness from yesterday pressure
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Someone is willing to overpay; we only match partially
        base = max(DAILY_SALARY * 0.35, avg_prev_bid * 0.55)
    else:
        base = max(DAILY_SALARY * 0.5, avg_prev_bid * 0.6)

    # If we are in danger (low hp or many no-water days), bid more
    if my_hp <= 2 or my_no_water_days >= 2:
        base *= 1.35
    elif my_hp <= 4 or my_no_water_days >= 1:
        base *= 1.15

    # Adjust for supply: more supply -> bid less
    base *= (1.15 - 0.35 * supply_norm)

    # Cap to avoid bankrupting ourselves
    bid_cap = my_budget

    # Also avoid absurd bids beyond what would be needed for survival in typical ranges
    # (supply range 15-25, water requirement 9 => 1 unit usually; bid around salary fractions)
    hard_cap = DAILY_SALARY * 0.95
    target = min(bid_cap, min(hard_cap, base))

    # Ensure non-negative and at least small positive if budget allows
    if target < 0.0:
        target = 0.0
    if my_budget > 0.0 and target == 0.0:
        target = min(my_budget, DAILY_SALARY * 0.2)

    return float(target)
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

    # Basic safety
    if my_status['budget'] <= 0:
        return 0.0

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    alive_opps = [o for o in opponents_status.values() if o.get('alive', True)]
    if not alive_opps:
        # If alone, bid just enough to secure survival when needed
        target = DAILY_SALARY * (0.35 if my_status['hp'] > 3 else 0.85)
        return float(min(my_status['budget'], target))

    # Read yesterday bids from traces to infer aggressiveness
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        if prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    # If we have trace info, respond to the highest pressure
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        # Cindy shows willingness to overpay; treat very high bids as a signal to not chase blindly.
        # Instead, bid to stay competitive when our hp is low.
        if my_status['hp'] <= 2:
            # Must secure water; bid aggressively but cap by budget.
            # If others were bidding very high yesterday, we still try a strong bid.
            bid = DAILY_SALARY * (0.95 if highest_prev_bid < DAILY_SALARY * 2 else 0.85)
            return float(min(my_status['budget'], bid))
        elif my_status['hp'] == 3:
            # Medium urgency: bid around 0.65-0.75 of salary depending on pressure.
            bid = DAILY_SALARY * (0.75 if highest_prev_bid < DAILY_SALARY * 1.5 else 0.68)
            return float(min(my_status['budget'], bid))
        else:
            # Comfortable: bid modestly; if pressure was high, slightly increase.
            bid = DAILY_SALARY * (0.55 if highest_prev_bid < DAILY_SALARY * 1.5 else 0.62)
            return float(min(my_status['budget'], bid))

    # Fallback when no trace bids available
    if my_status['hp'] <= 2:
        return float(min(my_status['budget'], DAILY_SALARY * 0.9))
    return float(min(my_status['budget'], DAILY_SALARY * 0.55))
"""
