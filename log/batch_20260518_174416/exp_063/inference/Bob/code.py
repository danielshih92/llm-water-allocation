# ============================================================
# Experiment: exp_063
# Agent: Bob
# Source: exp_063
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = day_context['supply']
    day = day_context['day']

    # Base budget-aware bid
    budget = my_status['budget']
    hp = my_status['hp']

    alive_opponents = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    # If no opponents, bid enough to meet requirement or a safe fraction
    if not alive_opponents:
        target = DAILY_SALARY * 0.4
        # ensure we don't exceed budget
        if budget < target:
            return budget
        return target

    # Read yesterday bids for immediate reaction
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Determine opponent aggressiveness
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If they were very aggressive, we counter with a controlled bid.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # If our hp is low, we need protection; otherwise avoid overpaying.
            if hp is not None and hp <= 2:
                target = DAILY_SALARY * 0.9
            else:
                target = DAILY_SALARY * 0.35
        else:
            # If they were mild, we bid to take the water advantage.
            # Tie pressure to their max bid but keep within reasonable range.
            target = max(DAILY_SALARY * 0.55, highest_prev_bid + 1.5)
    else:
        # No trace info: default moderate bid
        target = DAILY_SALARY * 0.55

    # Adjust for our health: lower hp => bid more conservatively toward survival
    if hp is not None:
        if hp <= 1:
            target = max(target, DAILY_SALARY * 0.95)
        elif hp <= 2:
            target = max(target, DAILY_SALARY * 0.8)
        elif hp >= 5:
            target = min(target, DAILY_SALARY * 0.6)

    # Adjust for supply: if supply is tight, increase bid slightly.
    # day_context['supply'] is float; use thresholds without indexing.
    if supply is not None:
        if supply < (MIN_SUPPLY + 0.5):
            target = max(target, DAILY_SALARY * 0.7)
        elif supply > (MAX_SUPPLY - 0.5):
            target = min(target, DAILY_SALARY * 0.55)

    # Ensure we bid at least enough to be competitive but never exceed budget.
    # Use water requirement to scale a minimal competitive floor.
    # (We don't know exact mapping from bid->water, so we keep conservative floors.)
    min_floor = DAILY_SALARY * 0.25
    if target < min_floor:
        target = min_floor

    if budget is None:
        return target
    if budget <= 0:
        return 0

    if target > budget:
        return budget
    return target
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

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday bids from immediate previous_trace only
    prev_bids = []
    prev_hp_after = []
    for opp_id, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass
            try:
                if prev.get('hp_after') is not None:
                    prev_hp_after.append(float(prev['hp_after']))
            except Exception:
                pass

    # Determine pressure from highest previous bid
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Supply-aware target: if supply is tight, bid closer to required share.
    # We estimate opponent count by alive players.
    n_alive = int(len(alive_opps))
    # Rough share factor: more players -> bid less aggressively per player.
    share_factor = 1.0 / max(1, n_alive)

    # Base bid policy:
    # - If my HP is low or I already had no-water days, increase bid.
    # - If yesterday saw very high bids, avoid overbidding; bid just enough to beat typical mid bids.
    if hp <= 2 or no_water_days >= 2:
        base = DAILY_SALARY * 0.85
    elif hp <= 4 or no_water_days >= 1:
        base = DAILY_SALARY * 0.65
    else:
        base = DAILY_SALARY * 0.52

    # Adjust to yesterday extremes: Cindy/Eric were high; don't chase the maximum.
    # If highest_prev_bid is extremely high, set a cap below it.
    if highest_prev_bid >= DAILY_SALARY * 1.2:
        # Cap at ~0.95*DAILY_SALARY or slightly above base, whichever is lower.
        base = min(base + DAILY_SALARY * 0.05, DAILY_SALARY * 0.95)
    elif highest_prev_bid >= DAILY_SALARY * 0.85:
        base = min(base + DAILY_SALARY * 0.08, DAILY_SALARY * 0.9)

    # Supply tightness: map supply to aggressiveness.
    # If supply near MIN_SUPPLY, increase; near MAX_SUPPLY, decrease.
    supply_norm = (supply - float(MIN_SUPPLY)) / max(1e-9, float(MAX_SUPPLY - MIN_SUPPLY))
    supply_norm = max(0.0, min(1.0, supply_norm))
    # aggressiveness_multiplier: 1.15 at tight, 0.95 at abundant
    aggressiveness_multiplier = 1.15 - 0.20 * supply_norm

    # Final bid: scale by share_factor lightly (avoid too low bids when alone)
    bid = base * aggressiveness_multiplier
    bid = bid * (0.85 + 0.30 * share_factor)

    # Ensure bid is non-negative and within budget
    bid = max(0.0, bid)
    bid = min(budget, bid)

    # If budget is very small, still try to get something.
    if budget <= DAILY_SALARY * 0.2:
        bid = min(budget, max(1.0, budget * 0.7))

    return float(bid)
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

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o is None:
            continue
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        # Conservative fallback: keep enough budget for future days.
        bid = DAILY_SALARY * 0.4
        if my_budget < bid:
            bid = my_budget
        return max(0.0, float(bid))

    # Extract yesterday bids from traces for immediate pressure.
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_prev_bid = 0.0
    if len(prev_bids) >= 2:
        sorted_b = sorted(prev_bids, reverse=True)
        second_prev_bid = sorted_b[1]

    # Estimate how many allocations we can afford to
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

    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from immediate previous_trace only
    prev_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate scarcity pressure from supply level
    # If supply is low, competition for water increases.
    supply_frac = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_frac = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_frac = max(0.0, min(1.0, supply_frac))
    scarcity = 1.0 - supply_frac  # 1 when supply is at MIN

    # Base bid: moderate, increases with scarcity and low hp
    base = DAILY_SALARY * (0.42 + 0.25 * scarcity)

    # If my hp is critically low or I'm already on many no-water days, bid harder
    if my_hp <= 2:
        base = DAILY_SALARY * 0.9
    elif my_hp <= 4:
        base = DAILY_SALARY * 0.65

    if my_no_water_days >= 2:
        base = max(base, DAILY_SALARY * 0.6)

    # React weakly to yesterday's top bid: don't match huge bids; just ensure we don't underbid too far.
    # If yesterday's highest bid was enormous, it likely indicates others were overpaying.
    if highest_prev_bid >= DAILY_SALARY * 1.25:
        # Keep a cap to avoid getting dragged into a bidding war.
        base = min(base, DAILY_SALARY * 0.75)
    elif highest_prev_bid >= DAILY_SALARY * 0.85:
        # Slightly increase to avoid being left behind.
        base = max(base, DAILY_SALARY * 0.55)

    # Add a small increment proportional to scarcity to edge out aggressive but not runaway
    bid = base + (DAILY_SALARY * 0.08) * scarcity

    # Ensure we never bid above budget; also keep non-negative
    bid = max(0.0, min(my_budget, bid))
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

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for k, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append(o)

    if not alive_opponents:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Reaction to yesterday's bids (immediate pressure signal)
    yesterday_bids = []
    for o in alive_opponents:
        prev = o.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    yesterday_bids.append(float(b))
                except Exception:
                    pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how competitive the day is: higher supply reduces urgency
    # (supply is between 15 and 25)
    supply_norm = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    supply_norm = max(0.0, min(1.0, supply_norm))

    # Base bid: if I'm healthy, undercut; if low HP or accumulating dry days, bid up.
    # Use highest_prev_bid to avoid being outbid when others are aggressive.
    urgency = 0.0
    if hp <= 1.5:
        urgency = 1.0
    elif hp <= 3.0:
        urgency = 0.75
    elif hp <= 5.0:
        urgency = 0.45
    else:
        urgency = 0.25

    if no_water_days >= 2:
        urgency = max(urgency, 0.85)

    # Target competitiveness threshold: others' yesterday max suggests their typical winning range.
    # If they were bidding high, we slightly trail; if not, we bid moderate.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # They were very aggressive yesterday; match near their level but not exceed too much.
        target = highest_prev_bid - 5.0 + (urgency * 6.0)
    else:
        target = max(DAILY_SALARY * (0.45 + 0.25 * urgency), highest_prev_bid * 0.65 + 10.0)

    # Adjust for supply: more supply -> can bid less to secure water.
    target = target * (0.95 + 0.10 * (1.0 - supply_norm))

    # Hard caps to avoid bankruptcy; also ensure non-negative.
    # Since water requirement is 9, don't overcommit beyond a fraction of budget.
    max_affordable = budget * 0.35
    if budget <= 0:
        return 0.0

    # If my HP is critical, allow higher spending up to 0.75 of budget.
    if hp <= 2.0 or no_water_days >= 3:
        max_affordable = budget * 0.75

    bid = min(max_affordable, target)

    # If target is too low relative to likely competition, bump slightly.
    if highest_prev_bid > 0 and bid < highest_prev_bid * 0.6 and urgency >= 0.6:
        bid = min(max_affordable, highest_prev_bid * 0.75)

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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = day_context['supply']
    day = day_context['day']

    # Identify alive opponents and read yesterday bids
    alive_opps = []
    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {}) or {}
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(float(prev.get('bid', 0.0)))

    # If no info / no opponents alive, bid conservatively
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Estimate competitive pressure from yesterday
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid

    # Supply pressure: if supply is low, water is scarcer -> bid higher
    # supply in [15,25], map to scarcity factor
    scarcity = (MAX_SUPPLY - float(supply)) / float(MAX_SUPPLY - MIN_SUPPLY)  # 0 (high supply) .. 1 (low supply)

    # Base target bid: try to beat Cindy-like pressure only when necessary
    # Use highest_prev_bid as anchor but avoid overpaying.
    # Also react to my HP/no_water_days.
    urgency = 0.0
    if my_hp <= 2:
        urgency += 1.0
    elif my_hp <= 4:
        urgency += 0.7
    else:
        urgency += 0.3

    if no_water_days >= 2:
        urgency += 0.6
    elif no_water_days == 1:
        urgency += 0.3

    # If Cindy previously bid very high, we may need to match to secure water, but not always.
    # Thresholds tuned to observed meta-round behavior.
    high_pressure = highest_prev_bid >= DAILY_SALARY * 0.85

    if high_pressure:
        # Bid around a fraction of the pressure depending on urgency and scarcity
        target = highest_prev_bid * (0.65 + 0.25 * urgency) + 2.0 * scarcity
    else:
        # If no extreme bids, bid enough to be competitive: slightly above second-highest
        target = max(DAILY_SALARY * 0.45, second_prev_bid + 1.5 + 5.0 * scarcity)
        target = target * (0.75 + 0.25 * urgency)

    # Convert target into a safe cap based on budget
    # Keep some budget buffer to survive later days.
    # If day is late, be more aggressive.
    late_factor = 1.0
    if day >= 8:
        late_factor = 1.15
    elif day >= 6:
        late_factor = 1.08

    # Budget safety: if budget is low, scale down.
    budget_cap = my_budget
    if my_budget <= DAILY_SALARY * 0.25:
        budget_cap = my_budget * 0.95
    elif my_budget <= DAILY_SALARY * 0.6:
        budget_cap = my_budget * 0.9

    # Final bid: ensure non-negative and not exceeding cap
    bid = float(target) * late_factor
    if bid < 0.0:
        bid = 0.0
    if bid > budget_cap:
        bid = budget_cap

    # If we are extremely low HP, prioritize water.
    if my_hp <= 1.5:
        bid = min(budget_cap, max(bid, DAILY_SALARY * 0.85))

    # If supply is high, we can bid a bit less because water is easier to obtain.
    if float(supply) >= 22.0:
        bid = bid * 0.9

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

    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from immediate previous_trace
    opp_prev_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                opp_prev_bids.append(float(b))
            except Exception:
                pass

    # Pressure estimate: how aggressive were surviving opponents
    if opp_prev_bids:
        max_prev = max(opp_prev_bids)
        avg_prev = sum(opp_prev_bids) / float(len(opp_prev_bids))
    else:
        max_prev = 0.0
        avg_prev = 0.0

    # Supply pressure: higher supply reduces need to outbid; lower supply increases it.
    # Normalize to [0,1]
    if MAX_SUPPLY <= MIN_SUPPLY:
        supply_norm = 0.5
    else:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
        if supply_norm < 0.0:
            supply_norm = 0.0
        if supply_norm > 1.0:
            supply_norm = 1.0

    # Base bid target: ensure we can win when supply is tight and/or our hp is low.
    # Use yesterday aggressiveness as a proxy for current-day bids.
    # Target multiplier for bid
    hp_factor = 1.0
    if hp <= 1:
        hp_factor = 1.15
    elif hp == 2:
        hp_factor = 1.08
    elif hp >= 6:
        hp_factor = 0.92

    no_water_factor = 1.0
    if no_water_days >= 3:
        no_water_factor = 1.18
    elif no_water_days == 2:
        no_water_factor = 1.08

    # If someone was bidding near/above daily salary, we should not be too low.
    # Otherwise, bid around a fraction of that.
    aggressive_threshold = DAILY_SALARY * 0.85

    if max_prev >= aggressive_threshold:
        # Overmatch slightly vs aggressive opponents
        target = max_prev + (2.0 * (1.0 - supply_norm))
    else:
        # Moderate: aim above average but not wasteful
        target = max(avg_prev * (0.95 + 0.1 * (1.0 - supply_norm)), DAILY_SALARY * 0.45)

    # Adjust for hp and no-water pressure
    target *= hp_factor
    target *= no_water_factor

    # Convert target into a safe cap based on remaining budget
    # Also ensure we don't bid more than we can afford.
    max_affordable = max(0.0, budget)

    # Keep bids within reasonable band to avoid bankruptcy
    # Lower band: still bid something if we're in danger.
    min_reasonable = 0.0
    if hp <= 2 or no_water_days >= 2:
        min_reasonable = DAILY_SALARY * 0.65

    bid = min(max_affordable, target)
    if bid < min_reasonable:
        bid = min(max_affordable, min_reasonable)

    # Final sanity
    if bid < 0.0:
        bid = 0.0
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

    supply = day_context.get('supply', 0)
    day = day_context.get('day', 1)

    hp = my_status.get('hp', 0)
    budget = my_status.get('budget', 0)
    no_water_days = my_status.get('no_water_days', 0)

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from traces for immediate reaction
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
        elif isinstance(prev, list) and prev:
            # If trace is list-like, take last element
            last = prev[-1]
            if isinstance(last, dict):
                b = last.get('bid', None)
                if b is not None:
                    try:
                        yesterday_bids.append(float(b))
                    except Exception:
                        pass

    # Determine competitive pressure from yesterday
    top_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how many water units are realistically needed/available this day
    # supply is total pool; each unit costs WATER_REQ water.
    # We only use it to scale aggressiveness, not to compute exact allocation.
    try:
        units_available = int(supply / float(WATER_REQ))
    except Exception:
        units_available = 1
    if units_available < 1:
        units_available = 1

    # Baseline bid aggressiveness
    # If my hp is low or I have been without water, I must bid more.
    hp_pressure = 0.0
    if hp <= 1:
        hp_pressure = 1.0
    elif hp <= 3:
        hp_pressure = 0.7
    elif hp <= 5:
        hp_pressure = 0.4

    if no_water_days >= 2:
        hp_pressure = max(hp_pressure, 0.8)

    # Supply scaling: higher supply -> can bid slightly less; lower supply -> bid more.
    # Normalize supply between MIN_SUPPLY and MAX_SUPPLY.
    if MAX_SUPPLY != MIN_SUPPLY:
        supply_norm = (float(supply) - float(MIN_SUPPLY)) / float(MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_norm = 0.5
    if supply_norm < 0.0:
        supply_norm = 0.0
    if supply_norm > 1.0:
        supply_norm = 1.0

    # Convert yesterday top pressure into a target bid band.
    # Yesterday winners had max bids around ~152; we target below top to conserve budget.
    # If top_bid is very high, we must match closer.
    if top_bid >= DAILY_SALARY * 1.45:
        base_target = DAILY_SALARY * 0.95
    elif top_bid >= DAILY_SALARY * 1.2:
        base_target = DAILY_SALARY * 0.75
    elif top_bid >= DAILY_SALARY * 0.8:
        base_target = DAILY_SALARY * 0.62
    else:
        base_target = DAILY_SALARY * 0.55

    # Adjust target by supply and my health pressure
    # Lower supply -> higher bid; low hp -> higher bid.
    bid_scale = (1.0 - 0.25 * supply_norm) + 0.6 * hp_pressure
    target_bid = base_target * bid_scale

    # Ensure we react to yesterday's top bid: if top_bid is close to our baseline, bump slightly.
    # Add a small epsilon to beat likely tie margins.
    if top_bid > 0:
        # If top_bid is not too far above target, move toward it.
        if top_bid <= target_bid * 1.15:
            target_bid = (0.7 * target_bid) + (0.3 * top_bid) + 1.5
        else:
            # Otherwise, still try to be competitive but not reckless.
            target_bid = min(target_bid, top_bid * 0.85)

    # Cap by budget and keep within reasonable bounds
    # Also avoid bidding more than we can afford.
    max_affordable = max(0.0, float(budget))

    # If budget is very low, bid just enough to avoid starvation.
    if max_affordable <= 1.0:
        return 0.0

    # Final bid rule
    # Keep a floor so we don't lose when others overbid; but don't exceed 95% of budget.
    min_floor = DAILY_SALARY * 0.35
    bid = max(min_floor, target_bid)
    bid = min(bid, max_affordable * 0.95)

    # If hp is critical, push closer to budget.
    if hp <= 2:
        bid = min(max_affordable * 0.98, max(bid, DAILY_SALARY * 0.85))

    # If supply is very low, push a bit more.
    if float(supply) <= float(MIN_SUPPLY) + 0.5:
        bid = min(max_affordable * 0.98, bid * 1.08)

    # Return non-negative float
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

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday bids from previous_trace for immediate pressure estimate
    yesterday_bids = []
    yesterday_pressures = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                yesterday_bids.append(float(bid))
            except Exception:
                pass

        # If yesterday opp had low hp or died soon, treat as higher urgency
        prev_hp_after = prev.get('hp_after', None)
        if prev_hp_after is not None:
            try:
                prev_hp_after = float(prev_hp_after)
                yesterday_pressures.append(prev_hp_after)
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how many full water-req units supply can cover
    # (indexing safety with int() though not strictly needed here)
    capacity_units = int(supply / float(WATER_REQ)) if WATER_REQ > 0 else 0

    # Base aggressiveness: if supply is tight (15-18), bid more to ensure allocation.
    if supply <= (MIN_SUPPLY + 3):
        tight_factor = 1.0
    elif supply <= 20:
        tight_factor = 0.85
    else:
        tight_factor = 0.7

    # Urgency from our hp/no_water_days
    if hp <= 2 or no_water_days >= 3:
        urgency = 1.0
    elif hp <= 4 or no_water_days == 2:
        urgency = 0.85
    else:
        urgency = 0.65

    # If opponents were bidding very high yesterday, we slightly outbid the likely clearing zone.
    # Use a soft threshold around 0.85*DAILY_SALARY.
    threshold = 0.85 * DAILY_SALARY

    if highest_prev_bid >= threshold:
        # Keep some budget for later days; bid around high zone but not maxing.
        target = (highest_prev_bid * 0.92 + 3.0) * tight_factor
    else:
        # Otherwise follow average with a small premium.
        premium = max(6.0, 0.12 * avg_prev_bid)
        target = (avg_prev_bid + premium) * tight_factor

    # If we have lots of capacity units, we can bid less.
    if capacity_units >= 2:
        target *= 0.9

    # Clamp by urgency and budget
    target *= (0.85 + 0.3 * urgency)

    # Final bid constraints: never exceed budget; also avoid overshooting extreme values.
    max_reasonable = DAILY_SALARY * 1.25
    bid = min(budget, max_reasonable, target)

    # Ensure non-negative
    if bid < 0:
        bid = 0.0

    # If budget is tiny, bid what we can.
    if budget <= 10:
        return budget

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
    day = day_context.get('day', 0)

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    # Base safety: if we already are in trouble, bid to secure water.
    if my_hp <= 1 or my_no_water_days >= 2:
        target = DAILY_SALARY * 0.95
    elif my_hp <= 3:
        target = DAILY_SALARY * 0.75
    else:
        target = DAILY_SALARY * 0.58

    # Exploit yesterday trace: if someone bid aggressively, we should not be the cheapest.
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

    if prev_bids:
        highest_prev_bid = max(prev_bids)
        # If the strongest opponent was near our salary, we need to match somewhat.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            target = max(target, min(my_budget, highest_prev_bid * 0.92))
        # If bids were moderate, slightly overcut the median/mean.
        else:
            avg_prev = sum(prev_bids) / float(len(prev_bids))
            target = max(target, avg_prev * 0.95)

    # Supply pressure: lower supply implies more competition, so raise bid.
    # supply is between 15 and 25 in this meta-round.
    if supply <= (MIN_SUPPLY + 1.0):
        target *= 1.08
    elif supply >= (MAX_SUPPLY - 1.0):
        target *= 0.96

    # Clamp to what we can afford.
    bid = min(my_budget, target)

    # Ensure non-negative and at least a small bid if budget allows.
    if bid < 0:
        bid = 0.0
    if bid == 0.0 and my_budget > 0:
        bid = min(my_budget, DAILY_SALARY * 0.2)

    return float(bid)
"""
