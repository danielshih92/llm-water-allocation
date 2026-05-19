# ============================================================
# Experiment: exp_116
# Agent: Bob
# Source: exp_116
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    # Alive opponents
    alive_opps = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opps.append(opp)

    # If no opponents, bid to meet requirement with some slack
    if not alive_opps:
        bid = min(my_status.get('budget', 0.0), DAILY_SALARY * 0.6)
        return bid

    # Read yesterday bids from previous_trace only
    yesterday_bids = []
    yesterday_states = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            yesterday_bids.append(b)
            yesterday_states.append((opp, b, prev))

    # If we have no yesterday bids, fall back to conservative-mid bid
    if not yesterday_bids:
        # If low HP or many no-water days, increase bid
        hp = my_status.get('hp', 0)
        no_water_days = my_status.get('no_water_days', 0)
        if hp <= 2 or no_water_days >= 2:
            return min(my_status.get('budget', 0.0), DAILY_SALARY * 0.9)
        return min(my_status.get('budget', 0.0), DAILY_SALARY * 0.55)

    highest_prev_bid = max(yesterday_bids)
    lowest_prev_bid = min(yesterday_bids)

    hp = my_status.get('hp', 0)
    no_water_days = my_status.get('no_water_days', 0)
    budget = my_status.get('budget', 0.0)

    # Estimate how many water units are likely to be available (for urgency calibration)
    # Use explicit int() to avoid float index issues (even though we don't index arrays)
    approx_units = int(supply / float(WATER_REQ)) if WATER_REQ else 0

    # Determine pressure level from opponent bids
    # If they bid very high, they likely expect to be outbid or are desperate.
    high_pressure = highest_prev_bid >= DAILY_SALARY * 0.85
    medium_pressure = (highest_prev_bid >= DAILY_SALARY * 0.55) or (highest_prev_bid - lowest_prev_bid >= DAILY_SALARY * 0.2)

    # Core bidding policy
    if high_pressure:
        # If we're healthy, still bid to contest; if we're low HP, bid harder.
        if hp <= 2 or no_water_days >= 2:
            target = DAILY_SALARY * 0.95
        else:
            target = DAILY_SALARY * 0.75
        # If supply is tight (few units), increase slightly
        if approx_units <= 1:
            target += DAILY_SALARY * 0.1
        return min(budget, target)

    if medium_pressure:
        # Bid enough to stay competitive but avoid overpaying.
        # Also react to whether opponents previously bid clustered near our daily salary.
        if hp <= 2 or no_water_days >= 2:
            target = DAILY_SALARY * 0.7
        else:
            # Slightly above the median of yesterday bids if available
            sorted_bids = sorted(yesterday_bids)
            mid_idx = int(len(sorted_bids) // 2)
            medianish = sorted_bids[mid_idx]
            target = max(DAILY_SALARY * 0.55, medianish + 5.0)
        return min(budget, target)

    # Low pressure: bid moderately; if we're already suffering, increase.
    if hp <= 2 or no_water_days >= 2:
        return min(budget, DAILY_SALARY * 0.85)

    # Late in episode: increase bid to avoid endgame starvation.
    # day is 0-indexed or 1-indexed unknown; use relative position to 10 days.
    try:
        remaining_days = 10 - int(day)
    except Exception:
        remaining_days = 5

    if remaining_days <= 3:
        return min(budget, DAILY_SALARY * 0.65)

    return min(budget, DAILY_SALARY * 0.5)
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

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opponents:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace for immediate reaction
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Determine if the field is bidding aggressively yesterday
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    # Convert supply to an approximate number of days of water if we win enough share.
    # We only use it to scale aggressiveness slightly.
    # (Not a literal model of the game, just a heuristic.)
    supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_factor = max(0.0, min(1.0, supply_factor))

    # Base bid pressure
    # If someone was bidding near/surpassing DAILY_SALARY, they likely secure water reliably.
    aggressive_field = highest_prev_bid >= DAILY_SALARY * 1.2 or avg_prev_bid >= DAILY_SALARY * 0.9

    # If we are in danger (low hp or already no-water days), bid more.
    danger = (hp <= 3) or (no_water_days >= 2)

    if aggressive_field:
        # Compete but not fully match the top bidder; aim to be in the top cluster.
        if danger:
            target = DAILY_SALARY * (0.95 - 0.15 * supply_factor)
        else:
            target = DAILY_SALARY * (0.65 + 0.10 * supply_factor)
        # Also anchor to yesterday's highest bid to react to their intensity.
        # Avoid overspending by capping.
        target = max(target, min(DAILY_SALARY * 0.8, highest_prev_bid * 0.55))
    else:
        # Field is not aggressive; bid enough to avoid starvation but conserve budget.
        if danger:
            target = DAILY_SALARY * (0.75 + 0.10 * supply_factor)
        else:
            target = DAILY_SALARY * (0.45 + 0.10 * supply_factor)

    # Ensure we don't exceed budget; also avoid negative.
    bid = max(0.0, min(budget, target))

    # Small adjustment: if we already had no-water days, increase slightly.
    if no_water_days >= 1:
        bid = min(budget, bid * 1.08)

    # If budget is very low, bid all-in to prevent immediate death.
    if budget <= DAILY_SALARY * 0.2:
        bid = min(budget, DAILY_SALARY * 1.0)

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
    day = day_context.get('day', 0)

    # Estimate how many units of water we can/should aim for.
    # In this game, water is typically granted per WATER_REQ of supply; we bias around 1 unit.
    target_units = 1
    # If supply is very low, we still try for 1 unit; if very high, we can afford slightly more.
    if supply >= 21.0:
        target_units = 2

    # Read yesterday bids from alive opponents to infer their aggression.
    alive_opponents = [o for o in opponents_status.values() if o.get('alive', False)]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        if prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # Baseline: safe bid that preserves budget.
    # If our hp is low, we must bid more.
    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Pressure factor from our condition.
    if hp <= 2 or no_water_days >= 2:
        urgency = 1.0
    elif hp <= 4:
        urgency = 0.75
    else:
        urgency = 0.55

    # If opponents were bidding very high yesterday, we try to match just below the top.
    if yesterday_bids:
        top_bid = max(yesterday_bids)
        second_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else top_bid

        # If someone bid near/above salary, they're likely competing hard.
        high_competition = top_bid >= DAILY_SALARY * 0.85

        if high_competition:
            # Undercut: bid slightly above second-highest to beat most while saving budget.
            desired = max(second_bid + 1.0, DAILY_SALARY * 0.35)
            # If we're urgent, push closer to top.
            desired = desired + (top_bid - desired) * (0.35 * urgency)
        else:
            # If competition was moderate, bid around a bit above expected clearing.
            desired = max(top_bid * 0.85, DAILY_SALARY * 0.45)
            desired = desired * (0.9 + 0.2 * urgency)
    else:
        # No data: default moderate bid.
        desired = DAILY_SALARY * (0.45 + 0.25 * urgency)

    # Scale desired with target units (more supply -> slightly more water desired).
    if target_units == 2:
        desired *= 1.15

    # Hard caps to avoid running out.
    # Keep some buffer for later days.
    max_reasonable = min(budget, DAILY_SALARY * (1.0 + 0.15 * urgency))
    min_reasonable = min(budget, DAILY_SALARY * (0.25 if hp > 4 else 0.6))

    bid = float(desired)
    if bid < min_reasonable:
        bid = min_reasonable
    if bid > max_reasonable:
        bid = max_reasonable

    # Ensure non-negative and integer-ish bidding.
    if bid < 0:
        bid = 0.0
    # Many games accept floats; still, we can round to 0.1 for stability.
    return round(bid, 2)
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

    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        return float(min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from each opponent's previous_trace for immediate reaction
    prev_bids = []
    prev_hp_after = []
    for o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                prev_bids.append(float(bid))
            except Exception:
                pass
        if prev.get('hp_after', None) is not None:
            try:
                prev_hp_after.append(float(prev.get('hp_after')))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    # Estimate how tight water is: higher supply -> less need to overbid
    # supply is between 15..25; map to 0..1
    if MAX_SUPPLY <= MIN_SUPPLY:
        supply_tightness = 0.5
    else:
        supply_tightness = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
        if supply_tightness < 0.0:
            supply_tightness = 0.0
        if supply_tightness > 1.0:
            supply_tightness = 1.0

    # Base bid: try to be competitive but not waste budget
    # Use yesterday's highest bid as a pressure indicator
    pressure_target = max(avg_prev_bid, highest_prev_bid * 0.92)

    # If my hp is low, conserve budget (bid lower) unless pressure is extreme
    if hp <= 2 or no_water_days >= 2:
        conservative_cap = DAILY_SALARY * (0.35 + 0.25 * (1.0 - supply_tightness))
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # Extreme pressure: still bid enough to secure water
            bid = max(conservative_cap, pressure_target)
        else:
            bid = min(pressure_target, conservative_cap)
    else:
        # Healthy: bid more when supply is tighter and pressure is high
        aggressive_floor = DAILY_SALARY * (0.45 + 0.25 * supply_tightness)
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            bid = max(aggressive_floor, pressure_target)
        else:
            bid = max(aggressive_floor * 0.9, pressure_target * 0.9)

    # Also ensure we never exceed budget
    bid = float(bid)
    if bid > budget:
        bid = budget

    # If budget is very low, just go as low as possible while still having a chance
    # (simultaneous bids; small bid helps avoid immediate loss)
    min_reasonable = 5.0
    if budget < min_reasonable:
        return float(max(0.0, budget))

    if bid < min_reasonable:
        bid = min_reasonable

    # Small day-based wobble to avoid exact ties with opponents
    wobble = 1.0 + ((day % 5) - 2) * 0.02
    bid = bid * wobble

    if bid > budget:
        bid = budget
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

    supply = float(day_context['supply'])
    day = day_context['day']

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if bool(o.get('alive', False)):
            alive_opps.append(o)

    # If no opponents, just bid enough to cover requirement.
    if not alive_opps:
        target = DAILY_SALARY * 0.35
        return max(0.0, min(my_budget, target))

    # Read yesterday bids from immediate trace.
    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Pressure estimate: if someone previously bid extremely high, expect competition.
    # Use my hp/no_water to decide whether to join fight or conserve.
    hp_critical = (my_hp <= 2.0) or (my_no_water_days >= 2)
    supply_high = supply >= (MIN_SUPPLY + MAX_SUPPLY) / 2.0

    # Baseline: moderate bid; ramp with critical hp or high supply.
    if hp_critical:
        # Aggressive but not max-out; aim to beat typical mid bids.
        target = DAILY_SALARY * 0.85
    else:
        target = DAILY_SALARY * (0.45 if supply_high else 0.40)

    # If yesterday someone overbid near the top, slightly increase to avoid losing.
    if highest_prev_bid >= DAILY_SALARY * 1.65:  # ~148
        if hp_critical:
            target = max(target, highest_prev_bid * 0.70)
        else:
            target = max(target, highest_prev_bid * 0.55)

    # If yesterday bids were generally low, we can undercut.
    if highest_prev_bid > 0 and highest_prev_bid < DAILY_SALARY * 1.1:
        target = min(target, DAILY_SALARY * 0.55)

    # Ensure we never bid above budget.
    bid = max(0.0, min(my_budget, float(target)))
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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    # If we are in critical health, bid aggressively to prevent further no-water days.
    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Collect yesterday bids from alive opponents only.
    alive_opps = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opps.append(opp)

    # Compute a pressure estimate from yesterday.
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        if prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Baseline bid depends on expected number of water units.
    # If supply is tight (15), only 1 unit of 9 fits; if supply is 18-25, 2 units may fit.
    # We don't know allocation mechanics, so we use this to scale our aggressiveness.
    if supply < (WATER_REQ + 1):
        supply_tight = True
    else:
        supply_tight = False

    # Determine target bid using yesterday's distribution.
    # Cindy-like behavior suggests some agents overpay; we aim around the lower-mid to avoid waste.
    if yesterday_bids:
        sorted_bids = sorted(yesterday_bids)
        n = len(sorted_bids)
        median_bid = sorted_bids[int(n // 2)]
        # Also consider high-pressure tail.
        high_bid = sorted_bids[-1]

        # If someone bid very high yesterday, others likely followed; raise our bid slightly.
        if high_bid >= DAILY_SALARY * 1.5:
            target = median_bid + 5.0
        else:
            target = median_bid * 0.85 + 10.0
    else:
        target = DAILY_SALARY * 0.55

    # Health/no-water urgency adjustment.
    if hp <= 2 or no_water_days >= 2:
        target *= 1.35
    elif hp <= 4:
        target *= 1.15

    # Tight supply adjustment: bid more when supply likely limits water.
    if supply_tight:
        target *= 1.10
    else:
        target *= 0.95

    # Clamp to budget and keep within a reasonable fraction of daily salary.
    # Avoid extreme bids that could mirror Cindy's wasteful pattern.
    max_reasonable = DAILY_SALARY * 1.2
    bid = min(budget, max_reasonable, target)

    # If budget is too low, still bid something if possible.
    if bid <= 0.0:
        return 0.0
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

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append(o)

    if not alive_opponents:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Infer pressure from yesterday's immediate bids
    yesterday_bids = []
    for o in alive_opponents:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Identify Cindy-like high-pressure behavior (low hp but high bid)
    cindy_pressure = 0.0
    for o in alive_opponents:
        if o.get('hp', 0) <= 2:
            prev = o.get('previous_trace', {}) or {}
            b = prev.get('bid', None)
            if b is not None:
                try:
                    cindy_pressure = max(cindy_pressure, float(b))
                except Exception:
                    pass

    # Baseline target bid based on yesterday bids
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid
    else:
        highest_prev_bid = DAILY_SALARY * 0.6
        second_prev_bid = highest_prev_bid

    # If someone was extremely aggressive, match slightly below/near to avoid overpaying
    # but still likely secure enough water (game is about allocation vs bids).
    # Use supply pressure: lower supply -> higher bids.
    supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_pressure = 1.0 - max(0.0, min(1.0, supply_norm))  # 1 when low supply, 0 when high

    # Health urgency
    if hp <= 2:
        urgency = 1.0
    elif hp <= 4:
        urgency = 0.75
    elif hp <= 6:
        urgency = 0.55
    else:
        urgency = 0.4

    # If we've already missed water days, increase urgency
    if no_water_days >= 2:
        urgency = min(1.0, urgency + 0.15)

    # Target: slightly above second-highest when pressure is high; otherwise around a fraction of highest.
    # Cindy-pressure proxy: if someone had bid near 95+ yesterday while low hp, assume continued pressure.
    pressure_factor = 1.0
    if cindy_pressure >= DAILY_SALARY * 0.85:
        pressure_factor = 1.08

    # Candidate bid levels
    # Aim to be competitive without going full all-in.
    competitive_bid = (second_prev_bid + 2.0) * pressure_factor
    cautious_bid = max(DAILY_SALARY * 0.45, highest_prev_bid * 0.75)
    aggressive_bid = min(budget, max(competitive_bid, highest_prev_bid * 0.9))

    # Blend based on urgency and supply pressure
    blend = 0.35 + 0.45 * urgency + 0.2 * supply_pressure
    target = cautious_bid * (1.0 - blend) + aggressive_bid * blend

    # Clamp to ensure non-negative and not exceed budget
    target = max(0.0, min(budget, target))

    # If target is too low relative to likely competition, bump modestly.
    # Use highest_prev_bid as a soft guide.
    if target < highest_prev_bid * 0.6 and urgency >= 0.6:
        target = min(budget, highest_prev_bid * (0.75 + 0.1 * urgency))

    # Final safety: if budget is tight, don't overshoot
    if budget <= DAILY_SALARY * 0.6:
        target = min(target, budget * 0.95)

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
    day = int(day_context.get('day', 0))

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace only
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        if prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Pressure estimate: if someone was bidding near/above salary, competition is intense.
    intense = highest_prev_bid >= DAILY_SALARY * 0.85

    # Supply tightness: if supply is close to requirement, water is more scarce.
    scarcity = 1.0
    if MAX_SUPPLY > MIN_SUPPLY:
        scarcity = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)
        if scarcity < 0.0:
            scarcity = 0.0
        if scarcity > 1.0:
            scarcity = 1.0

    # Decide aggressiveness.
    # If my hp is low or I'm already accumulating no-water days, bid more.
    urgency = 0.0
    if my_hp <= 2.0:
        urgency = 1.0
    elif my_hp <= 4.0:
        urgency = 0.7
    elif my_no_water_days >= 2:
        urgency = 0.6
    else:
        urgency = 0.2

    # Base bid: conservative unless urgency+scarcity+intense.
    # Target is to secure water without matching the highest bidder when unnecessary.
    if intense:
        target = DAILY_SALARY * (0.35 + 0.25 * scarcity + 0.35 * urgency)
        # If urgency is high, near-match the leader; else undercut.
        if urgency >= 0.8:
            target = max(target, min(my_budget, highest_prev_bid * 0.95))
        else:
            target = min(target, highest_prev_bid * 0.6 + DAILY_SALARY * 0.2)
    else:
        target = DAILY_SALARY * (0.25 + 0.35 * scarcity + 0.4 * urgency)

    # Ensure we don't bid more than budget and keep non-negative.
    bid = max(0.0, min(my_budget, target))

    # If supply is extremely low and we are not in danger, still bid enough to avoid falling behind.
    if supply <= float(WATER_REQ) + 0.5 and my_hp > 4.0 and my_no_water_days == 0:
        bid = min(my_budget, max(bid, DAILY_SALARY * 0.45))

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

    # Basic safety
    budget = float(my_status.get('budget', 0.0))
    hp = int(my_status.get('hp', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    alive_opps = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday bids only (immediate reaction)
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Estimate how aggressive the field was
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid

    # If supply is near max, fewer competitors need to be beaten; if near min, bid more.
    # supply_ratio: 0 at MIN_SUPPLY, 1 at MAX_SUPPLY
    if MAX_SUPPLY == MIN_SUPPLY:
        supply_ratio = 0.5
    else:
        supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Urgency based on HP/no_water_days
    urgency = 0.0
    if hp <= 2:
        urgency += 1.0
    elif hp <= 4:
        urgency += 0.6
    if no_water_days >= 2:
        urgency += 0.6
    elif no_water_days == 1:
        urgency += 0.25

    # Target bid logic:
    # - If field's highest bid was very high, we don't fully match; we aim to beat typical high bids.
    # - Otherwise, bid enough to secure water without burning budget.
    base = DAILY_SALARY * (0.45 + 0.25 * urgency)

    # When supply is low, increase willingness to bid.
    # lower supply_ratio => add up to +0.25*DAILY_SALARY
    base += DAILY_SALARY * (0.25 * (1.0 - supply_ratio))

    # Use yesterday's second-highest as a proxy for what we need to beat.
    # Add a small premium to likely win against mid/high bidders.
    premium = 0.0
    if highest_prev_bid > 0.0:
        # If highest_prev_bid is extremely high, don't chase it; chase second-highest + small.
        premium = 0.08 * highest_prev_bid + 1.5
        # If highest_prev_bid was moderate, premium should be smaller.
        if highest_prev_bid < DAILY_SALARY:
            premium = 0.05 * highest_prev_bid + 1.0

    # Final desired bid
    desired = base + premium

    # Cap by budget; also avoid overbidding beyond a reasonable fraction of budget.
    # If urgency is high, allow up to 0.95 of budget.
    budget_cap = budget * (0.95 if urgency >= 1.0 else (0.7 if urgency >= 0.6 else 0.55))
    desired = min(desired, budget_cap)

    # Never bid negative
    if desired < 0.0:
        desired = 0.0

    return float(desired)
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

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return float(min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace only
    prev_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev['bid']))

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate how many rounds of water we might need given no-water streak
    # If we have been without water, increase aggressiveness.
    urgency = 0
    if no_water_days >= 2:
        urgency = 2
    elif no_water_days == 1:
        urgency = 1

    # Supply pressure: lower supply means higher chance opponents overbid; we adjust upward.
    supply_pressure = 0.0
    if supply <= float(WATER_REQ):
        supply_pressure = 0.25
    elif supply <= (MIN_SUPPLY + WATER_REQ) / 2.0:
        supply_pressure = 0.15
    else:
        supply_pressure = 0.05

    # If opponents were bidding extremely high yesterday (Cindy), we should bid high enough to not lose.
    # Cindy's ~97 suggests threshold around 0.85*DAILY_SALARY.
    extreme = highest_prev_bid >= DAILY_SALARY * 0.85

    if extreme:
        # Match a fraction of their pressure; scale with our hp and urgency.
        if hp <= 2.0:
            target = DAILY_SALARY * (0.95 - 0.05 * urgency)
        elif hp <= 4.0:
            target = DAILY_SALARY * (0.75 - 0.03 * urgency)
        else:
            target = DAILY_SALARY * (0.62 - 0.02 * urgency)

        # Add small bump to counteract low supply.
        target = target * (1.0 + supply_pressure)
    else:
        # If others were not extreme, conserve but still secure water when hp is low.
        if hp <= 2.0:
            target = DAILY_SALARY * 0.85
        elif hp <= 4.0:
            target = DAILY_SALARY * 0.65
        else:
            target = DAILY_SALARY * 0.48
        target = target * (1.0 + supply_pressure)

    # Ensure we don't overpay beyond budget; also cap to avoid unnecessary burn.
    # Use a soft cap relative to budget to survive 10-day horizon.
    max_reasonable = max(0.0, budget)

    # If budget is low, bid what we can.
    bid = float(min(max_reasonable, target))

    # If urgency is high, push closer to budget.
    if urgency >= 2 and bid < budget * 0.85:
        bid = float(min(budget, DAILY_SALARY * 0.9))

    # Final clamp: always non-negative.
    if bid < 0.0:
        bid = 0.0
    return bid
"""
