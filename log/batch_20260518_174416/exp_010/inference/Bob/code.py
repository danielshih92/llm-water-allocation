# ============================================================
# Experiment: exp_010
# Agent: Bob
# Source: exp_010
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

    # If no opponents, take a safe minimal bid to get our requirement.
    if not alive_opps:
        return min(my_status.get('budget', 0.0), DAILY_SALARY * 0.35)

    # Read yesterday's behavior from previous_trace only.
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                prev_bids.append(b)

    hp = my_status.get('hp', 0)
    budget = my_status.get('budget', 0.0)
    no_water_days = my_status.get('no_water_days', 0)

    # Determine aggressiveness from yesterday.
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        second_highest = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev_bid
    else:
        highest_prev_bid = 0.0
        second_highest = 0.0

    # Pressure thresholds: infer if opponents are spending heavily.
    high_pressure = highest_prev_bid >= DAILY_SALARY * 0.85
    medium_pressure = highest_prev_bid >= DAILY_SALARY * 0.55

    # Safety adjustment: if low hp or already missing water, increase bid.
    urgency = 0
    if hp is not None and hp <= 2:
        urgency += 2
    if hp is not None and hp == 3:
        urgency += 1
    if no_water_days is not None and no_water_days >= 2:
        urgency += 2
    if no_water_days is not None and no_water_days == 1:
        urgency += 1

    # Supply-aware cap: if supply is tight relative to our requirement, bid more.
    # Use only int indices if needed; here we avoid indexing.
    supply_ratio = float(supply) / float(WATER_REQ) if WATER_REQ > 0 else 0.0
    tight_supply = supply_ratio < 2.0  # heuristic for medium/low supply

    # Base strategy
    if high_pressure:
        # Compete but don't overpay: slightly under their top bid unless urgency is high.
        target = highest_prev_bid * (0.92 if urgency <= 1 else 1.02)
        if tight_supply:
            target *= 1.10
    elif medium_pressure:
        target = max(DAILY_SALARY * 0.55, second_highest + (1.0 if urgency <= 1 else 2.0))
        if tight_supply:
            target *= 1.05
    else:
        # Low observed aggression: bid moderately to secure water for 9.
        target = DAILY_SALARY * (0.48 + 0.08 * urgency)
        if tight_supply:
            target *= 1.10

    # Ensure we never bid above budget.
    if budget is None:
        budget = 0.0
    bid = min(float(budget), float(target))

    # If urgency is extreme, ensure at least a strong bid.
    if urgency >= 3:
        bid = max(bid, min(float(budget), DAILY_SALARY * 0.85))

    # Keep bid non-negative.
    if bid < 0:
        bid = 0.0

    return bid
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

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive.append((opp_id, opp))

    if not alive:
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday bids from immediate previous_trace only.
    prev_bids = []
    for opp_id, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                prev_bids.append(float(bid))
            except Exception:
                pass

    # Estimate opponent aggressiveness.
    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    # Base target bid: aim to win when supply is tight or my HP is critical.
    # Supply is between 15 and 25; higher supply means less need to outbid.
    supply_ratio = (supply - float(MIN_SUPPLY)) / float(MAX_SUPPLY - MIN_SUPPLY)  # 0..1
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # If I'm in danger, bid harder.
    if hp <= 2 or no_water_days >= 2:
        urgency = 1.0
    elif hp <= 4 or no_water_days >= 1:
        urgency = 0.65
    else:
        urgency = 0.35

    # If opponents were bidding high yesterday, raise slightly to avoid losing.
    # Cindy survived; others died; high highest_prev likely means some were aggressive.
    pressure = 0.0
    if highest_prev >= DAILY_SALARY * 0.85:
        pressure = 0.35
    elif highest_prev >= DAILY_SALARY * 0.6:
        pressure = 0.2
    elif highest_prev > 0:
        pressure = 0.1

    # Compute desired bid.
    # Keep it below full daily salary to preserve budget; escalate with urgency and pressure.
    target = DAILY_SALARY * (0.45 + urgency * 0.35 - supply_ratio * 0.15 + pressure)

    # If Cindy was the only one alive, she likely bids consistently; match her band.
    # Use avg_prev as a soft cap.
    if avg_prev > 0:
        target = min(target, avg_prev * 1.05)

    # Ensure we can pay.
    bid = min(budget, max(1.0, target))

    # If supply is very low (near 15), slightly increase bid to secure water.
    if supply <= float(MIN_SUPPLY) + 0.5:
        bid = min(budget, bid * 1.15)

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

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append(o)

    # If nobody alive, conserve.
    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from each opponent's previous_trace (immediate reaction only).
    yesterday_bids = []
    for o in alive:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Estimate opponent pressure: focus on high bidder (likely Cindy-like behavior).
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Supply-based aggressiveness: with higher supply, competition matters more.
    # Map supply in [15,25] to a multiplier in [0.9,1.2].
    if MAX_SUPPLY - MIN_SUPPLY > 0:
        t = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        t = 0.5
    t = max(0.0, min(1.0, float(t)))
    supply_mult = 0.9 + 0.3 * t

    # If I'm in danger, bid much closer to the pressure level.
    danger = 0
    if hp <= 2.0:
        danger += 2
    if no_water_days >= 2:
        danger += 1

    # Base target: undercut the highest previous bidder unless in danger.
    # Typical strategy: bid slightly below their max/pressure to win at lower cost.
    if highest_prev_bid > 0:
        if danger >= 2:
            target = highest_prev_bid * 0.98
        elif danger == 1:
            target = highest_prev_bid * 0.9
        else:
            target = highest_prev_bid * 0.78
    else:
        target = DAILY_SALARY * 0.55

    # Apply supply multiplier and keep within reasonable bounds.
    target *= supply_mult

    # Also cap by a fraction of daily salary to avoid over-spending.
    # When hp is safe, be conservative.
    if danger == 0:
        cap = DAILY_SALARY * 0.62
    elif danger == 1:
        cap = DAILY_SALARY * 0.85
    else:
        cap = DAILY_SALARY * 0.95

    bid = min(target, cap, budget)

    # Ensure non-negative and at least a small meaningful bid if budget allows.
    if bid < 0.0:
        bid = 0.0
    min_bid = 1.0
    if budget >= min_bid and bid < min_bid:
        bid = min_bid

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

    # If we are already in trouble, prioritize survival.
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95)
    if my_status['no_water_days'] >= 2 and my_status['hp'] <= 4:
        return min(my_status['budget'], DAILY_SALARY * 0.8)

    # Gather yesterday bids from alive opponents.
    alive_opps = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                alive_opps.append(float(prev.get('bid', 0.0)))

    # Baseline aggressiveness depends on supply scarcity.
    # With supply 15-25 and requirement 9, winning water is valuable; bid more when supply is low.
    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)  # 0..1, higher means scarcer
    scarcity = max(0.0, min(1.0, scarcity))

    # Default bid target.
    base = DAILY_SALARY * (0.45 + 0.35 * scarcity)

    if alive_opps:
        highest_prev_bid = max(alive_opps)
        lowest_prev_bid = min(alive_opps)

        # If someone was very aggressive yesterday, we must not lose water today.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            target = max(base, highest_prev_bid + (2.0 + 3.0 * scarcity))
        else:
            # Otherwise, try to beat the likely median pressure without overspending.
            # Use a small increment above the upper tail estimate.
            # Approximate by aiming above the 75% percentile using sorted list length.
            sorted_bids = sorted(alive_opps)
            n = len(sorted_bids)
            idx = int(n * 0.75) - 1
            if idx < 0:
                idx = 0
            if idx >= n:
                idx = n - 1
            upper_est = float(sorted_bids[idx])
            target = max(base, upper_est + (1.0 + 2.0 * scarcity))

        # Cap spending based on our current hp and budget.
        hp_factor = 0.6 + 0.1 * float(my_status['hp'])  # hp 0..10 => 0.6..1.6
        hp_factor = max(0.4, min(1.2, hp_factor))
        cap = my_status['budget'] * 0.35 + DAILY_SALARY * 0.65
        target = min(target, cap)

        # If budget is low, still bid enough to avoid immediate elimination.
        if my_status['budget'] <= DAILY_SALARY * 0.3:
            target = min(my_status['budget'], DAILY_SALARY * 0.6)

        return max(0.0, min(my_status['budget'], target))

    # If no opponent trace info, bid based on scarcity and our hp.
    return max(0.0, min(my_status['budget'], base))
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

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))

    # Alive opponents and their yesterday bids
    alive_opps = []
    for oid, o in opponents_status.items():
        if o is None:
            continue
        if bool(o.get('alive', False)):
            alive_opps.append((oid, o))

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    yesterday_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Determine opponent pressure from yesterday
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Supply-to-water urgency: with higher supply, we can bid less aggressively.
    # Normalize supply in [0,1]
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_norm = 0.5
    supply_norm = max(0.0, min(1.0, float(supply_norm)))

    # Base bid target: aim around 0.55-0.75 of salary depending on supply.
    # Higher supply => lower bid.
    base = DAILY_SALARY * (0.75 - 0.25 * supply_norm)

    # If opponents bid high yesterday, raise to contest.
    # Use a soft threshold near Eric/Cindy levels from context.
    pressure_boost = 0.0
    if highest_prev_bid >= DAILY_SALARY * 1.15:  # ~103.5
        pressure_boost = DAILY_SALARY * 0.25
    elif highest_prev_bid >= DAILY_SALARY * 0.9:  # ~81
        pressure_boost = DAILY_SALARY * 0.12

    # If we are low HP, bid more to secure water.
    hp_boost = 0.0
    if hp <= 2:
        hp_boost = DAILY_SALARY * 0.35
    elif hp <= 4:
        hp_boost = DAILY_SALARY * 0.2

    # If supply is tight (near MIN_SUPPLY), increase bid.
    tight_boost = 0.0
    if supply <= float(MIN_SUPPLY) + 0.5:
        tight_boost = DAILY_SALARY * 0.2

    target = base + pressure_boost + hp_boost + tight_boost

    # Ensure we don't exceed budget
    target = max(0.0, min(budget, target))

    # Add a small increment to outbid likely competitors when pressure is high.
    # Since bids are hidden, this is a robust heuristic.
    if highest_prev_bid > 0.0:
        # If our target is below yesterday's highest, try to slightly exceed it.
        if target < highest_prev_bid:
            target = min(budget, highest_prev_bid + 2.0)

    # Final safety cap: never spend more than 95% of budget.
    target = min(target, budget * 0.95) if budget > 0.0 else 0.0

    return float(target)
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

    # Determine alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # If no opponents, spend enough to meet requirement
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace only
    prev_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Baseline: competitive bid target based on yesterday's highest bid pressure
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate how many water units are plausible from supply range
    # (Used only to scale aggressiveness, not for indexing.)
    supply_ratio = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    if supply_ratio < 0.0:
        supply_ratio = 0.0
    if supply_ratio > 1.0:
        supply_ratio = 1.0

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # If we are in danger, bid hard; otherwise bid to beat the typical survivor bids.
    # Yesterday indicates Cindy/Eric bid ~130-140 to ensure survival.
    danger = (hp <= 2.5) or (no_water_days >= 2)

    if danger:
        # Near-max bid but bounded by budget and a reasonable cap
        target = max(highest_prev_bid * 0.98, DAILY_SALARY * 0.9)
    else:
        # If others were bidding very high, slightly under/near that to avoid overspending.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            target = highest_prev_bid * 0.92
        else:
            # Moderate competition: scale with supply
            target = max(DAILY_SALARY * (0.45 + 0.25 * supply_ratio), highest_prev_bid + 8.0)

    # Convert target to final bid with budget cap
    if budget <= 0.0:
        return 0.0

    # Ensure we don't bid above budget; also keep a floor to avoid accidental starvation
    bid = float(min(budget, target))

    # If our hp is healthy and supply is low, still bid enough to not lose the auction entirely.
    if (not danger) and supply_ratio < 0.25:
        bid = float(max(bid, DAILY_SALARY * 0.5))

    # Final clamp
    if bid < 0.0:
        bid = 0.0
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
    alive_opps = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opps.append(opp)

    # If no opponents alive, bid just enough to secure water
    if not alive_opps:
        target = DAILY_SALARY * 0.35
        return float(min(my_status['budget'], target))

    # Read yesterday bids from previous_trace for immediate pressure estimation
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Determine urgency from my hp and no_water_days
    hp = float(my_status['hp'])
    no_water_days = int(my_status['no_water_days'])
    budget = float(my_status['budget'])

    # Supply factor: when supply is near the lower bound, we need stronger bids to prevent being rationed
    # Normalize supply to [0,1]
    if MAX_SUPPLY <= MIN_SUPPLY:
        supply_norm = 0.5
    else:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
        if supply_norm < 0.0:
            supply_norm = 0.0
        if supply_norm > 1.0:
            supply_norm = 1.0

    # Base bid level: moderate-high to compete with Alex/David aggression
    # If supply is low, raise bid; if high, reduce slightly.
    base = DAILY_SALARY * (0.62 - 0.10 * supply_norm)  # ~0.52..0.62

    # If yesterday pressure was very high (>= ~0.85 salary), match closer
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        if hp > 3.0 and no_water_days <= 1:
            bid = base + DAILY_SALARY * 0.12
        else:
            bid = base + DAILY_SALARY * 0.28
    else:
        # Otherwise, bid slightly above typical pressure to secure water
        bid = max(base, highest_prev_bid * 0.95 + 8.0)

    # Urgency overrides
    if hp <= 2.0:
        bid = max(bid, DAILY_SALARY * 0.90)
    elif no_water_days >= 2:
        bid = max(bid, DAILY_SALARY * 0.75)

    # Budget safety: never exceed budget; also avoid overspending if budget is low
    bid = float(min(budget, bid))

    # If budget is extremely low, bid whatever remains but keep non-negative
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    if my_budget <= 0:
        return 0.0

    # Base bid: aim to secure enough water without matching Alex's high bids.
    # If my hp is low or I've already missed water, increase urgency.
    urgency = 0.0
    if my_hp <= 2:
        urgency += 0.45
    elif my_hp <= 4:
        urgency += 0.25
    if my_no_water_days >= 2:
        urgency += 0.25

    # Use yesterday's bids to infer pressure.
    prev_bids = []
    for oid, o in alive:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / float(len(prev_bids))
    else:
        highest_prev = 0.0
        avg_prev = 0.0

    # Determine a target bid band.
    # If someone previously bid extremely high, we slightly undercut rather than follow.
    # If everyone was low, we can bid more aggressively.
    if highest_prev >= DAILY_SALARY * 1.15:
        # Alex-like behavior: overbidding to survive.
        target = (avg_prev if avg_prev > 0 else DAILY_SALARY * 0.6)
        target = min(target * (1.0 + urgency), highest_prev * 0.72)
    else:
        # Low-to-mid pressure.
        target = max(DAILY_SALARY * 0.45, avg_prev * 0.95 if avg_prev > 0 else DAILY_SALARY * 0.55)
        target = target * (1.0 + urgency)

    # Scale with supply: higher supply reduces needed bid to secure water.
    # Ensure indices are safe.
    supply_ratio = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    if supply_ratio < 0.0:
        supply_ratio = 0.0
    if supply_ratio > 1.0:
        supply_ratio = 1.0

    # When supply is scarce, bid higher; when abundant, bid lower.
    scarcity_factor = 1.10 - 0.15 * supply_ratio  # 1.10 at MIN_SUPPLY, 0.95 at MAX_SUPPLY
    target = target * scarcity_factor

    # Hard caps based on budget and a reasonable fraction of salary.
    max_reasonable = DAILY_SALARY * (0.95 if my_hp <= 2 else 0.75)
    target = min(target, max_reasonable)

    # Final affordability cap.
    bid = min(my_budget, target)

    # Avoid tiny bids that likely lose when we need water.
    if my_hp <= 2 or my_no_water_days >= 2:
        bid = max(bid, min(my_budget, DAILY_SALARY * 0.8))
    else:
        bid = max(bid, min(my_budget, DAILY_SALARY * 0.5))

    # Ensure non-negative float.
    if bid < 0.0:
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
    day = int(day_context['day'])

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if my_budget <= 0:
        return 0.0

    # Baseline: ensure we can afford a few competitive bids.
    base = DAILY_SALARY * 0.55

    # Use yesterday traces to infer how aggressively others bid.
    prev_bids = []
    prev_hp_after = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            prev_bids.append(float(b))
            prev_hp_after.append(float(prev.get('hp_after', o.get('hp', 0.0))))

    # Determine scarcity pressure from supply level.
    # Lower supply => higher chance opponents overbid.
    scarcity_factor = 0.0
    if supply <= (MIN_SUPPLY + 1):
        scarcity_factor = 0.20
    elif supply <= (MIN_SUPPLY + 4):
        scarcity_factor = 0.12
    elif supply >= (MAX_SUPPLY - 1):
        scarcity_factor = -0.08

    # If others bid very high yesterday, match partially.
    if prev_bids:
        max_prev_bid = max(prev_bids)
        avg_prev_bid = sum(prev_bids) / float(len(prev_bids))

        # If someone was bidding near/above our salary, competition is intense.
        intense = max_prev_bid >= DAILY_SALARY * 0.85
        if intense:
            base = DAILY_SALARY * 0.70
        else:
            # If avg is moderately high, slightly lift.
            if avg_prev_bid >= DAILY_SALARY * 0.70:
                base = DAILY_SALARY * 0.62
            else:
                base = DAILY_SALARY * 0.55

    # React to our own health/no-water streak.
    # If we're near failure, bid to survive.
    if my_hp <= 2 or my_no_water_days >= 2:
        base = DAILY_SALARY * 0.95
    elif my_hp <= 4:
        base = max(base, DAILY_SALARY * 0.75)

    # Small day-based ramp: later days require more survival probability.
    # episode_days is 10 in meta-round; use day to gently increase.
    if day >= 7:
        base *= 1.08

    # Apply scarcity adjustment.
    base *= (1.0 + scarcity_factor)

    # Convert to final bid, ensuring affordability.
    bid = min(my_budget, base)

    # Clamp to a reasonable range to avoid overpaying.
    # Still allow high bids if budget allows and we are in danger.
    if bid > DAILY_SALARY * 1.6 and not (my_hp <= 4 or my_no_water_days >= 2):
        bid = DAILY_SALARY * 1.6

    # Ensure non-negative float.
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

    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Identify alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o is not None and o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        # If no opponents, conserve budget
        return float(min(budget, DAILY_SALARY * 0.4))

    # Use only yesterday's previous_trace to react
    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Base target bid: aim slightly below typical survivors to avoid overpaying
    # but still compete against Cindy/Eric/David range.
    if yesterday_bids:
        sorted_bids = sorted(yesterday_bids)
        # Median-like estimate without numpy
        m = sorted_bids[len(sorted_bids)//2]
        # If there was a very high bid, pressure likely exists; bid closer to it.
        top = sorted_bids[-1]

        # Detect if someone died yesterday => indicates too much competition; we can be careful.
        died_flag = False
        for o in alive_opps:
            prev = o.get('previous_trace', {}) or {}
            if prev and prev.get('hp_after', None) == 0:
                died_flag = True
                break

        # Compute aggressiveness based on our hp/no_water_days
        urgency = 0
        if hp <= 2:
            urgency = 2
        elif hp <= 4:
            urgency = 1
        if no_water_days >= 2:
            urgency += 1

        # Supply factor: if supply is near minimum, competition is higher; bid more.
        supply_factor = 0.0
        if supply <= float(MIN_SUPPLY):
            supply_factor = 0.12
        elif supply >= float(MAX_SUPPLY):
            supply_factor = -0.05
        else:
            # interpolate roughly
            supply_factor = 0.12 - (supply - float(MIN_SUPPLY)) * (0.17 / (float(MAX_SUPPLY) - float(MIN_SUPPLY)))

        # Target: median minus a small discount unless urgency forces escalation.
        discount = 0.08
        if died_flag:
            discount = 0.12  # be slightly more conservative when someone already died

        target = m * (1.0 - discount) + (top - m) * 0.15

        # Urgency adjustment
        if urgency == 0:
            target *= (1.0 + supply_factor)
        elif urgency == 1:
            target *= (1.0 + supply_factor + 0.07)
        else:
            target = max(target, m * 0.98)  # close to median
            target *= (1.0 + supply_factor + 0.12)

    else:
        # No trace bids available; default moderate
        target = DAILY_SALARY * 0.55
        if hp <= 4 or no_water_days >= 2:
            target = DAILY_SALARY * 0.75

    # Ensure we don't bid more than budget
    bid = float(min(budget, max(0.0, target)))

    # If our budget is very low, still try to survive: bid proportionally to urgency
    if budget < DAILY_SALARY * 0.6:
        if hp <= 2 or no_water_days >= 2:
            bid = float(min(budget, DAILY_SALARY * 0.9))
        else:
            bid = float(min(budget, DAILY_SALARY * 0.55))

    # Final cap: avoid extreme overbids late in day 10 (episode_days=10 typically)
    # day is within 1..10; be slightly more conservative as day increases.
    if day >= 9:
        bid *= 0.92

    return float(bid)
"""
