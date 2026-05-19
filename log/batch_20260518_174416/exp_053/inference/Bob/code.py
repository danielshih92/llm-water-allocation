# ============================================================
# Experiment: exp_053
# Agent: Bob
# Source: exp_053
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
    day = day_context['day']

    # Budget guard
    my_budget = float(my_status['budget'])
    my_hp = float(my_status['hp'])

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    if not alive_opponents:
        # If alone, bid enough to secure water without overpaying
        target = min(my_budget, DAILY_SALARY * 0.45)
        return float(target)

    # Read yesterday bids from previous_trace only
    prev_bids = []
    prev_hp = []
    for opp_id, opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass
        try:
            prev_hp.append(float(opp.get('hp', 0)))
        except Exception:
            prev_hp.append(0.0)

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else 0.0

    # Estimate how tight the market is today
    # If supply is near MIN_SUPPLY, scarcity likely; bid more to avoid no-water days.
    scarcity_ratio = (supply - float(MIN_SUPPLY)) / (float(MAX_SUPPLY) - float(MIN_SUPPLY) + 1e-9)
    scarcity_ratio = max(0.0, min(1.0, scarcity_ratio))
    scarcity = 1.0 - scarcity_ratio  # 0..1

    # Determine baseline bid based on our hp
    # If low hp, we must buy water more aggressively.
    if my_hp <= 2.0:
        base = DAILY_SALARY * (0.75 + 0.15 * scarcity)
    elif my_hp <= 4.0:
        base = DAILY_SALARY * (0.60 + 0.15 * scarcity)
    else:
        base = DAILY_SALARY * (0.50 + 0.10 * scarcity)

    # Exploit opponent pressure from yesterday
    # If someone bid very high yesterday, they likely continued; we slightly undercut/contest.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Contest but not fully: aim around 0.82..0.88 of salary depending on our hp
        if my_hp <= 2.0:
            bid = DAILY_SALARY * (0.88 + 0.05 * scarcity)
        elif my_hp <= 4.0:
            bid = DAILY_SALARY * (0.84 + 0.04 * scarcity)
        else:
            bid = DAILY_SALARY * (0.82 + 0.03 * scarcity)
    else:
        # If no extreme bids, we can try to win with a moderate bid.
        # Use highest_prev_bid as a soft anchor to stay competitive.
        anchor = highest_prev_bid
        if anchor > 0.0:
            # Slightly above second-highest to beat if they cluster bids
            bid = max(base, min(my_budget, second_prev_bid + 1.5))
        else:
            bid = base

    # Ensure we don't overspend beyond budget
    bid = min(float(my_budget), float(bid))

    # If supply is enough that we can afford a lower bid, reduce a bit to save budget.
    if scarcity < 0.35 and my_hp > 4.0:
        bid = min(bid, DAILY_SALARY * 0.45)

    # Never bid negative
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

    alive = []
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive.append(opp)

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from active opponents (immediate reaction)
    yesterday_bids = []
    for opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    # Supply pressure heuristic: when supply is low, water is scarce -> bid higher.
    # We avoid extreme bidding to exploit opponent overreaction.
    if supply <= (MIN_SUPPLY + 1):
        pressure = 1.0
    elif supply <= (MIN_SUPPLY + 4):
        pressure = 0.85
    elif supply <= (MIN_SUPPLY + 8):
        pressure = 0.7
    else:
        pressure = 0.55

    # If we've already gone without water, increase bid sharply to reset risk.
    if no_water_days >= 2:
        urgency = 1.0
    elif no_water_days == 1:
        urgency = 0.85
    else:
        urgency = 0.65

    # If our hp is critically low, prioritize survival.
    if hp <= 2:
        hp_factor = 1.0
    elif hp <= 4:
        hp_factor = 0.9
    elif hp <= 6:
        hp_factor = 0.75
    else:
        hp_factor = 0.6

    # Opponent reaction exploitation: if they bid very high yesterday, they likely overcommitted.
    # We bid enough to compete, but not match their peak unless we are in danger.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Their peak suggests they are willing to spend heavily; reduce slightly when our hp is safe.
        opponent_factor = 0.78 if hp > 3 else 0.95
    elif avg_prev_bid >= DAILY_SALARY * 0.6:
        opponent_factor = 0.85
    else:
        opponent_factor = 0.7

    target = DAILY_SALARY * pressure * urgency * hp_factor * opponent_factor

    # Cap bid to budget and avoid wasting when budget is low.
    # Also keep a floor so we don't always lose to mid bidders.
    min_floor = DAILY_SALARY * (0.25 if hp > 5 else 0.55)
    bid = max(min_floor, target)
    bid = min(bid, budget)

    # If budget is extremely low, just bid what we can.
    if budget <= 1e-6:
        return 0.0

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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    # If no one is alive, conserve budget
    if not alive_opponents:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday bids for immediate reaction
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    yesterday_bids.append(float(b))
                except Exception:
                    pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Supply pressure: higher supply reduces need to overbid
    # supply in [15,25]; normalize to [0,1]
    denom = (MAX_SUPPLY - MIN_SUPPLY) if (MAX_SUPPLY - MIN_SUPPLY) != 0 else 1.0
    supply_norm = (supply - MIN_SUPPLY) / denom
    supply_norm = 0.0 if supply_norm < 0.0 else (1.0 if supply_norm > 1.0 else supply_norm)

    # Base bid: aim to be competitive but not chase Cindy's extreme bids
    # If supply is higher, bid slightly less.
    base = DAILY_SALARY * (0.52 - 0.12 * supply_norm)

    # React to yesterday's max bid: if someone bid near/above daily_salary, competition is fierce.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # If my hp is low, I must secure water.
        if my_hp <= 2.0 or my_no_water_days >= 2:
            target = DAILY_SALARY * 0.85
        else:
            target = DAILY_SALARY * 0.65
    else:
        # Competition moderate: slightly increase if I'm in danger.
        if my_hp <= 2.0 or my_no_water_days >= 2:
            target = DAILY_SALARY * 0.75
        else:
            # Keep under aggressive leader bids
            target = base

    # Budget guardrails
    # Ensure we don't bid more than we can afford.
    target = min(target, my_budget)

    # If budget is too low, bid what we can.
    if my_budget <= 0.0:
        return 0.0

    # Small strategic increments to avoid ties/low bids
    # If competition was high, add a small bump.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        bump = DAILY_SALARY * 0.03
    else:
        bump = DAILY_SALARY * 0.02

    final_bid = target + bump
    if final_bid > my_budget:
        final_bid = my_budget

    # If I'm critically low on hp, prioritize survival
    if my_hp <= 1.0:
        final_bid = min(my_budget, DAILY_SALARY * 0.98)

    # Clamp non-negative
    if final_bid < 0.0:
        final_bid = 0.0

    return float(final_bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive.append((opp_id, opp))

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday's bids from previous_trace for immediate reaction.
    prev_bids = []
    for opp_id, opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev['bid']))

    # Identify if any opponent was bidding extremely high (likely budget-abusive / survival-maximizing).
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Base willingness: ensure we don't overspend early; scale with our danger.
    danger = 0
    if hp <= 2.0:
        danger += 2
    if no_water_days >= 2:
        danger += 1

    # Supply pressure: with medium supply (15-25), water is not scarce enough to require max bidding.
    # Use a target bid anchored to a fraction of salary.
    # If opponents were bidding huge yesterday, we need to match some of it to avoid losing.
    if highest_prev_bid >= DAILY_SALARY * 1.6:  # ~144
        # Cindy-like behavior: push higher but still cap to protect budget.
        if danger >= 2:
            target = DAILY_SALARY * 0.95
        elif danger == 1:
            target = DAILY_SALARY * 0.75
        else:
            target = DAILY_SALARY * 0.6
        # Slightly undercut the highest previous bid to reduce tie risk while saving budget.
        target = min(target, highest_prev_bid * 0.92)
    elif highest_prev_bid >= DAILY_SALARY * 0.9:  # ~81
        if danger >= 2:
            target = DAILY_SALARY * 0.85
        elif danger == 1:
            target = DAILY_SALARY * 0.65
        else:
            target = DAILY_SALARY * 0.55
        target = min(target, highest_prev_bid * 0.85)
    else:
        # Opponents generally not maxing; bid moderately.
        if danger >= 2:
            target = DAILY_SALARY * 0.8
        elif danger == 1:
            target = DAILY_SALARY * 0.6
        else:
            target = DAILY_SALARY * 0.5

    # If supply is at the low end, increase slightly.
    if supply <= float(MIN_SUPPLY) + 0.5:
        target *= 1.08
    elif supply >= float(MAX_SUPPLY) - 0.5:
        target *= 0.95

    # Final cap by budget.
    bid = max(0.0, min(budget, target))

    # Ensure we don't bid trivially when we're in danger.
    if danger >= 2 and bid < DAILY_SALARY * 0.4:
        bid = min(budget, DAILY_SALARY * 0.75)

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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opps:
        # If no one is alive, take as much as needed but don't overspend.
        target = min(budget, DAILY_SALARY * 0.4)
        return max(0.0, float(target))

    # Read yesterday bids from previous_trace for immediate reaction.
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                yesterday_bids.append(float(bid))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how many water units are likely needed today.
    # If supply is near max, competition likely drives bids up.
    supply_ratio = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    if supply_ratio < 0.0:
        supply_ratio = 0.0
    if supply_ratio > 1.0:
        supply_ratio = 1.0

    # Pressure signal: if someone bid very high yesterday, they likely keep bidding.
    high_pressure = highest_prev_bid >= (DAILY_SALARY * 0.85)

    # Baseline bid: moderate, scaled by supply.
    # Keep it below typical aggressive bids unless my hp is healthy and supply is high.
    if high_pressure:
        # Try to stay in the game without matching extreme bids.
        if hp <= 2 or no_water_days >= 2:
            # Can't afford a loss; bid closer to aggressive range.
            desired = DAILY_SALARY * (0.75 + 0.1 * supply_ratio)
        else:
            desired = DAILY_SALARY * (0.55 + 0.25 * supply_ratio)
    else:
        # Lower competition: bid enough to secure water.
        if hp <= 2 or no_water_days >= 2:
            desired = DAILY_SALARY * (0.65 + 0.2 * supply_ratio)
        else:
            desired = DAILY_SALARY * (0.45 + 0.25 * supply_ratio)

    # Convert desired to a budget-safe bid.
    # Also cap by a fraction of budget to avoid going to 0 too early.
    budget_cap = budget
    if budget_cap < 0.0:
        budget_cap = 0.0

    # If budget is tight, scale down.
    if budget_cap <= DAILY_SALARY * 0.6:
        desired = min(desired, budget_cap * 0.9)
    else:
        desired = min(desired, budget_cap * 0.6)

    # If supply is low, competition is less intense; reduce bid.
    if supply_ratio < 0.35:
        desired *= 0.85

    # Ensure non-negative and not exceeding budget.
    bid = float(desired)
    if bid < 0.0:
        bid = 0.0
    if bid > budget_cap:
        bid = budget_cap

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

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    # Gather yesterday bids from alive opponents
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    # If no opponents alive, bid minimally but still plausible
    if not alive_opps:
        return max(0.0, min(float(my_status.get('budget', 0.0)), DAILY_SALARY * 0.4))

    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Estimate how aggressive the field was yesterday
    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        min_prev_bid = min(yesterday_bids)
        # Cindy-like behavior: high bid around 120-150 in trace; we shade slightly below max
        # Use my HP to decide whether to contest harder.
        hp = float(my_status.get('hp', 0.0))
        budget = float(my_status.get('budget', 0.0))

        # Supply pressure heuristic: with higher supply, we can bid less; with lower supply, bid more.
        # Map supply in [15,25] to pressure in [1.1,0.9]
        if MAX_SUPPLY != MIN_SUPPLY:
            pressure = 1.1 - 0.2 * ((supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY))
        else:
            pressure = 1.0

        # Base competitive target: slightly below yesterday max to avoid overpaying,
        # but enough to beat the runner-up if they were near max.
        # If my HP is critical, increase to near max.
        if hp <= 2:
            target = max_prev_bid * 0.98
        elif hp <= 4:
            target = max_prev_bid * 0.93
        else:
            target = max_prev_bid * 0.88

        # Also ensure not too low relative to yesterday's minimum
        floor_target = max(DAILY_SALARY * 0.55, min_prev_bid + 2.0)
        target = max(target, floor_target)

        # Apply pressure shading
        target = target * pressure

        # Cap bids to budget and avoid exceeding typical salary-scale too much
        # (game likely has bid caps; keep within 1.8*DAILY_SALARY)
        cap = 1.8 * DAILY_SALARY
        bid = min(budget, cap, target)

        # If budget is extremely low, still bid at least a small fraction to prevent immediate death
        if bid <= 0.0:
            bid = min(budget, DAILY_SALARY * 0.2)

        return float(max(0.0, bid))

    # If no yesterday bids available, use HP + supply heuristic
    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))

    if supply <= float(WATER_REQ):
        base = DAILY_SALARY * 0.85
    else:
        base = DAILY_SALARY * 0.6

    if hp <= 2:
        base = DAILY_SALARY * 0.95
    elif hp <= 4:
        base = DAILY_SALARY * 0.75

    bid = min(budget, base)
    return float(max(0.0, bid))
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

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append((oid, o))

    # If no opponents are alive, conserve.
    if not alive_opponents:
        return max(0.0, min(budget, DAILY_SALARY * 0.35))

    # Read only yesterday's immediate trace bids.
    prev_bids = []
    for oid, o in alive_opponents:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Pressure estimate: if someone bid close to/above daily salary, they likely expect scarcity.
    high_pressure = highest_prev_bid >= (DAILY_SALARY * 0.85)

    # Base bid: aim to win when my hp is safe; otherwise bid aggressively.
    if hp <= 2 or no_water_days >= 2:
        target = DAILY_SALARY * 0.9
    elif high_pressure:
        target = DAILY_SALARY * 0.35 if hp > 3 else DAILY_SALARY * 0.75
    else:
        # Medium pressure: bid enough to beat low bidders but not match the top.
        target = max(DAILY_SALARY * 0.5, highest_prev_bid * 0.75)

    # Supply-aware adjustment: lower supply increases chance others overbid.
    # supply is between 15 and 25.
    if supply <= float(WATER_REQ):
        target *= 1.15
    elif supply <= 18.0:
        target *= 1.08
    elif supply >= 22.0:
        target *= 0.95

    # Clamp by budget.
    bid = max(0.0, min(budget, float(target)))

    # Avoid bidding too low when hp is at risk.
    if hp <= 3:
        bid = max(bid, min(budget, DAILY_SALARY * 0.65))

    # If budget is tiny, bid whatever remains (still must be non-negative).
    if budget <= 1.0:
        bid = max(0.0, budget)

    return float(bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    # Extract day context
    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append((oid, o))

    # If no opponents are alive, bid only enough to live.
    if not alive_opponents:
        # If we're already starving, bid harder.
        if no_water_days >= 2 or hp <= 2:
            return min(budget, DAILY_SALARY * 0.85)
        return min(budget, DAILY_SALARY * 0.45)

    # Look only at yesterday's previous_trace for immediate reaction.
    prev_bids = []
    prev_hp_after = []
    for oid, o in alive_opponents:
        prev = o.get('previous_trace', {}) or {}
        if prev.get('bid') is not None:
            prev_bids.append(float(prev.get('bid', 0.0)))
            prev_hp_after.append(int(prev.get('hp_after', o.get('hp', 0))))

    # Baseline: moderate bid to avoid overpaying.
    # If supply is high, we can bid slightly lower; if supply is tight, bid higher.
    # supply_range is [15,25], so normalize.
    supply_norm = (supply - 15.0) / 10.0  # 0..1 roughly
    supply_norm = 0.0 if supply_norm < 0.0 else (1.0 if supply_norm > 1.0 else supply_norm)
    tightness = 1.0 - supply_norm  # higher when supply is low

    # Determine opponent pressure from yesterday.
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        lowest_prev_bid = min(prev_bids)
        avg_prev_bid = sum(prev_bids) / float(len(prev_bids))
    else:
        highest_prev_bid = 0.0
        lowest_prev_bid = 0.0
        avg_prev_bid = 0.0

    # If my HP is low or I've had no water for a while, bid more aggressively.
    urgency = 0.0
    if hp <= 2:
        urgency += 0.45
    elif hp == 3:
        urgency += 0.25
    if no_water_days >= 2:
        urgency += 0.35
    elif no_water_days == 1:
        urgency += 0.15

    # Exploit risk observed: very high bids led to deaths yesterday.
    # So cap reaction to not exceed a fraction of the highest observed bid.
    # If opponents used extremely high bids, we don't need to match them.
    cap_factor = 0.75
    # If their highest bid was not too high, we can bid closer to it.
    if highest_prev_bid <= DAILY_SALARY * 0.75:
        cap_factor = 0.85

    # Core target bid.
    # Start from a base that depends on tightness.
    base = DAILY_SALARY * (0.40 + 0.20 * tightness)  # 0.40..0.60 of salary

    # Add a small adjustment toward yesterday's average, but keep it conservative.
    # If avg was high, slightly increase; if avg was low, slightly decrease.
    avg_ratio = (avg_prev_bid / DAILY_SALARY) if DAILY_SALARY > 0 else 0.0
    if avg_ratio > 0.9:
        base *= 1.08
    elif avg_ratio < 0.6:
        base *= 0.92

    # If yesterday's highest bid was huge, don't chase it; just ensure we can win when needed.
    pressure_target = highest_prev_bid * cap_factor

    # Combine: choose between base and pressure_target, weighted by urgency.
    # Higher urgency => move closer to pressure_target.
    target = base * (1.0 - min(1.0, urgency)) + pressure_target * min(1.0, urgency)

    # Additional rule: if we were already close to starving yesterday (approximated by no_water_days), bid more.
    if no_water_days >= 2:
        target *= 1.15

    # Never bid above what we can afford.
    bid = min(budget, target)

    # Ensure non-negative.
    if bid < 0.0:
        bid = 0.0

    # If budget is tiny, still bid all.
    if budget <= DAILY_SALARY * 0.15:
        return budget

    # Final safety: keep bid within a reasonable band to avoid the death spiral.
    # Upper band depends on urgency.
    upper = DAILY_SALARY * (0.70 + 0.25 * min(1.0, urgency))
    if bid > upper:
        bid = upper

    return bid
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

    # Alive opponents
    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive.append((opp_id, opp))

    # If no one is alive, bid conservatively
    if not alive:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Read yesterday bids from previous_trace only
    yesterday_bids = []
    for opp_id, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                yesterday_bids.append(float(bid))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how many full water units exist; indices must be int
    units = int(supply / WATER_REQ) if WATER_REQ > 0 else 0

    # Core strategy:
    # - If someone was bidding very high yesterday, raise bid today to avoid being outbid.
    # - Otherwise, bid enough to compete but not drain budget.
    # - If my hp is low, increase aggressiveness.

    hp = my_status['hp']
    budget = my_status['budget']

    # Pressure level from yesterday
    high_pressure = highest_prev_bid >= DAILY_SALARY * 0.85

    # Base bid scaled by supply units
    # If supply supports only 1 unit, competition is higher -> bid higher.
    if units <= 1:
        base = DAILY_SALARY * 0.65
    elif units == 2:
        base = DAILY_SALARY * 0.55
    else:
        base = DAILY_SALARY * 0.45

    if high_pressure:
        # Match/beat pressure, but cap by available budget
        if hp <= 2:
            target = DAILY_SALARY * 0.95
        elif hp <= 4:
            target = DAILY_SALARY * 0.8
        else:
            target = DAILY_SALARY * 0.7
    else:
        # Normal competition: adjust by hp
        if hp <= 2:
            target = DAILY_SALARY * 0.85
        elif hp <= 4:
            target = base + (DAILY_SALARY * 0.2)
        else:
            target = base

    # Also ensure we don't overspend when budget is tiny
    # (Cindy-like behavior suggests others may burn budget; we conserve.)
    if budget <= DAILY_SALARY * 0.1:
        target = min(target, budget)

    # Final clamp
    bid = min(budget, target)

    # If supply is extremely low relative to WATER_REQ, bid minimal to preserve budget
    if supply < WATER_REQ:
        bid = min(bid, max(1.0, budget * 0.2))

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

    # Alive opponents
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    # If no one alive, spend conservatively
    if not alive:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from immediate previous_trace
    prev_bids = []
    prev_by_opp = {}
    for oid, o in alive:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                b = float(b)
            except Exception:
                b = None
        if b is not None:
            prev_bids.append(b)
            prev_by_opp[oid] = b

    # Baseline target bid: scale with supply scarcity
    # If supply is low, we must bid more to avoid no-water days.
    scarcity = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)  # 0..1
    scarcity = max(0.0, min(1.0, scarcity))

    # Pressure signal: if someone previously bid extremely high, they likely needed water.
    # We'll respond with a slightly lower but still competitive bid to avoid overspending.
    highest_prev = max(prev_bids) if prev_bids else 0.0
    second_prev = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else 0.0

    # If my hp is low, prioritize survival.
    my_hp = float(my_status['hp'])
    my_no_water_days = float(my_status['no_water_days'])
    my_budget = float(my_status['budget'])

    # Estimate how many water units are available relative to requirement.
    # Supply is total water; each unit we need is WATER_REQ.
    water_units = supply / float(WATER_REQ)

    # Determine urgency
    urgency = 0.0
    if my_hp <= 2.0:
        urgency += 1.0
    if my_no_water_days >= 1.0:
        urgency += 0.6
    if scarcity >= 0.7:
        urgency += 0.4

    # Decide bid band
    # Typical mid bid around 0.55-0.75 salary; higher if scarcity/urgency.
    mid = DAILY_SALARY * (0.55 + 0.2 * scarcity + 0.15 * urgency)

    # If opponent previously overbid hard, we should at least match their level minus a small discount.
    # Use thresholds relative to salary.
    if highest_prev >= DAILY_SALARY * 0.85:
        # Eric yesterday max ~141 (~1.57 salary/?) so treat as high pressure.
        # Bid enough to compete but not necessarily exceed.
        target = max(mid, highest_prev * 0.92)
    elif highest_prev >= DAILY_SALARY * 0.65:
        target = max(mid, highest_prev * 0.85)
    else:
        # If no strong pressure, keep moderate and conserve.
        # If second highest exists, nudge slightly above it to secure allocation.
        if second_prev > 0:
            target = max(mid, second_prev * 1.03)
        else:
            target = mid

    # If we have very low budget, cap hard.
    # Also avoid bidding more than budget.
    bid = min(my_budget, target)

    # Ensure non-negative
    if bid < 0.0:
        bid = 0.0

    # Small dynamic adjustment to avoid ties when water is scarce.
    # If supply implies only ~1 unit, add a tiny premium.
    if water_units <= 1.5:
        bid = min(my_budget, bid + DAILY_SALARY * 0.03)

    return float(bid)
"""
