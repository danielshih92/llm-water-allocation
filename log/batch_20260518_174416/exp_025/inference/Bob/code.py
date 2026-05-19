# ============================================================
# Experiment: exp_025
# Agent: Bob
# Source: exp_025
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

    # Alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # If no opponents, bid conservatively
    if not alive_opps:
        return min(my_status['budget'], int(DAILY_SALARY * 0.4))

    # Use yesterday trace if available (immediate reaction)
    prev_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Base bid depends on supply: higher supply -> lower urgency
    # Map supply in [MIN_SUPPLY, MAX_SUPPLY] to urgency in [0.8, 0.4]
    if MAX_SUPPLY - MIN_SUPPLY <= 0:
        urgency = 0.6
    else:
        t = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
        urgency = 0.8 - 0.4 * t
        if urgency < 0.4:
            urgency = 0.4
        if urgency > 0.8:
            urgency = 0.8

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Urgency boosts
    if hp <= 2.0:
        urgency *= 1.25
    elif hp <= 3.0:
        urgency *= 1.10

    if no_water_days >= 2:
        urgency *= 1.25
    elif no_water_days == 1:
        urgency *= 1.10

    # If we saw strong opponent bids yesterday, match/beat slightly.
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        # If they were near-salary, assume aggressive competition
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            target = highest_prev_bid + 1.0
        else:
            # Otherwise, bid enough to be competitive but not wasteful
            target = max(highest_prev_bid * 0.9, DAILY_SALARY * (0.45 + 0.35 * urgency))
    else:
        # No trace info: bid mid-high to secure water
        target = DAILY_SALARY * (0.45 + 0.35 * urgency)

    # Convert target to integer bid and cap by budget
    bid = int(target)
    if bid < 0:
        bid = 0
    if bid > budget:
        bid = int(budget)

    # Ensure we don't bid trivially low when hp/bad streak indicates need
    if (hp <= 3.0 or no_water_days >= 1) and bid < int(DAILY_SALARY * 0.55):
        bid = int(min(budget, DAILY_SALARY * 0.7))

    return bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    # Basic sanity
    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 1))

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))

    # If no budget, bid 0
    if my_budget <= 0:
        return 0.0

    # Collect yesterday bids from alive opponents
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

    # Estimate competitive pressure
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / float(len(yesterday_bids))
    else:
        highest_prev_bid = 0.0
        avg_prev_bid = 0.0

    # Supply pressure: with supply 15-25, number of winners is limited.
    # Higher supply => lower bid needed.
    if supply >= 21:
        supply_factor = 0.85
    elif supply >= 18:
        supply_factor = 1.0
    else:
        supply_factor = 1.15

    # HP safety: if low HP, prioritize survival (bid more to secure water), but cap by budget.
    if my_hp <= 2:
        hp_factor = 1.25
    elif my_hp <= 4:
        hp_factor = 1.10
    else:
        hp_factor = 0.95

    # Core strategy: anchor to fraction of daily salary, adjusted by observed pressure.
    # Aim to beat typical survivor bids without matching extreme max.
    target = DAILY_SALARY * 0.55

    if yesterday_bids:
        # If someone bid high yesterday, slightly overbid but not to the maximum.
        # Use average and highest to decide.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            target = max(target, avg_prev_bid * 0.95)
            target = max(target, highest_prev_bid * 0.70)
        else:
            target = max(target, avg_prev_bid * 0.85)

    bid = target * supply_factor * hp_factor

    # Ensure we don't exceed budget
    if bid > my_budget:
        bid = my_budget

    # Avoid tiny bids when we need water (no_water_days not provided reliably, so use hp)
    if my_hp <= 3 and bid < DAILY_SALARY * 0.35:
        bid = min(my_budget, DAILY_SALARY * 0.45)

    # Final clamp: non-negative
    if bid < 0:
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

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    # If no opponents alive, bid conservatively.
    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace only.
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', None)
        if isinstance(prev, dict):
            # Some environments may store a single trace dict; ignore if missing bid.
            bid = prev.get('bid', None)
            if bid is not None:
                yesterday_bids.append(float(bid))
        elif isinstance(prev, list):
            # Use only the last element (immediate reaction). Still respects "only previous_trace".
            if len(prev) > 0:
                last = prev[-1]
                if isinstance(last, dict) and last.get('bid', None) is not None:
                    yesterday_bids.append(float(last['bid']))

    # Fallback if trace missing.
    if not yesterday_bids:
        base = DAILY_SALARY * (0.75 if hp <= 2 or no_water_days >= 2 else 0.55)
        return max(0.0, min(budget, base))

    highest_prev_bid = max(yesterday_bids)
    second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid

    # Supply pressure: higher supply reduces need to overbid.
    # Use a conservative discretization; indices not needed.
    supply_level = 0.0
    if supply >= 0.9 * MAX_SUPPLY:
        supply_level = 1.0
    elif supply <= 1.1 * MIN_SUPPLY:
        supply_level = 0.0
    else:
        supply_level = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)

    # If others were bidding high yesterday, we must match/beat to secure water.
    high_threshold = DAILY_SALARY * 0.85  # ~76
    mid_threshold = DAILY_SALARY * 0.6    # ~54

    # Decide target bid.
    if highest_prev_bid >= high_threshold:
        # High-pressure market: try to win with a small increment.
        # If our HP is low, bid more aggressively.
        if hp <= 2 or no_water_days >= 2:
            target = max(highest_prev_bid + 2.5, second_prev_bid + 4.0)
        else:
            target = max(highest_prev_bid - 1.0, second_prev_bid + 3.0)
            # Still ensure competitiveness.
            if target < mid_threshold:
                target = mid_threshold
    elif highest_prev_bid >= mid_threshold:
        # Moderate competition: bid slightly above second-highest.
        target = second_prev_bid + 2.0
        if hp <= 2 or no_water_days >= 2:
            target += 5.0
    else:
        # Low competition: conserve unless we're in danger.
        target = DAILY_SALARY * (0.45 + 0.2 * (1.0 - supply_level))
        if hp <= 2 or no_water_days >= 2:
            target = DAILY_SALARY * 0.85

    # Budget and safety caps.
    # Never bid more than we can afford; also avoid extreme overspending.
    cap = min(budget, DAILY_SALARY * 1.2)
    bid = max(0.0, min(cap, target))

    # If we're critically low HP, ensure a high bid to avoid death.
    if hp <= 1:
        bid = max(bid, min(budget, DAILY_SALARY * 1.0))

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

    alive_opponents = [o for o in opponents_status.values() if o.get('alive', True)]
    if not alive_opponents:
        return min(float(my_status['budget']), DAILY_SALARY * 0.4)

    # Read yesterday bids from immediate previous_trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict) and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Pressure estimate: if opponents previously bid high, they likely contest.
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = (sum(yesterday_bids) / len(yesterday_bids)) if yesterday_bids else 0.0

    # Supply pressure: closer to MIN_SUPPLY means fewer units; bid slightly more.
    supply_mid = (MIN_SUPPLY + MAX_SUPPLY) / 2.0
    supply_factor = 1.0 + (supply_mid - supply) / (MAX_SUPPLY - MIN_SUPPLY + 1e-9)
    # clamp
    if supply_factor < 0.85:
        supply_factor = 0.85
    if supply_factor > 1.15:
        supply_factor = 1.15

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Base target bid
    # If opponents were bidding ~110 yesterday, contest with a bit above their average/threshold.
    # Use hp/no_water_days to decide aggressiveness.
    critical = (hp <= 2.5) or (no_water_days >= 2)
    if highest_prev_bid >= DAILY_SALARY * 0.95:
        # They were very aggressive yesterday.
        target = (avg_prev_bid if avg_prev_bid > 0 else highest_prev_bid) * 1.03
        if critical:
            target *= 1.12
        else:
            target *= 1.05
    elif highest_prev_bid >= DAILY_SALARY * 0.75:
        target = max(highest_prev_bid * 0.98, avg_prev_bid * 1.02) if avg_prev_bid > 0 else highest_prev_bid * 1.02
        if critical:
            target *= 1.10
        else:
            target *= 1.04
    else:
        # Lower contention: bid around a sustainable level.
        target = DAILY_SALARY * 0.55
        if critical:
            target = DAILY_SALARY * 0.85
        else:
            target = max(target, highest_prev_bid + 3.0)

    target *= supply_factor

    # Budget-aware cap: avoid going broke early.
    # Keep some runway: if budget is low, bid near what we can afford.
    min_reserve = DAILY_SALARY * 0.15
    max_affordable = max(0.0, budget - min_reserve)

    # Also keep bids within reasonable bounds for this game.
    # If supply is low, allow higher bids; if high, slightly lower.
    if supply <= MIN_SUPPLY + 0.5:
        bid_cap = DAILY_SALARY * 1.35
    elif supply >= MAX_SUPPLY - 0.5:
        bid_cap = DAILY_SALARY * 1.05
    else:
        bid_cap = DAILY_SALARY * 1.25

    final_bid = min(target, bid_cap, max_affordable if max_affordable > 0 else budget)

    # If we are extremely low budget, just spend what we can.
    if final_bid <= 0.0:
        final_bid = min(budget, DAILY_SALARY * (0.9 if critical else 0.5))

    # Ensure non-negative and not exceeding budget
    if final_bid < 0.0:
        final_bid = 0.0
    if final_bid > budget:
        final_bid = budget

    return float(final_bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Alive opponents and yesterday bids
    alive = []
    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace') or {}
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(float(prev['bid']))

    # If no one alive, conserve budget
    if not alive:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.4))

    # Use yesterday's max bid as proxy for competitive intensity
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how many water units are typically needed from supply range
    # (Not exact game mechanics, but guides bid aggressiveness.)
    # With WATER_REQ=9 and supply 15-25, one unit is likely pivotal.
    supply_units_est = supply / float(WATER_REQ)

    # Base bid: aim around slightly below yesterday's strongest demand
    # to win when they overcommit, but avoid matching top bids.
    target = highest_prev_bid * 0.9

    # If our HP is low, we must secure water more aggressively.
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # If we've already accumulated no-water days, increase urgency.
    urgency = 0
    if no_water_days >= 2:
        urgency = 1
    if hp <= 2:
        urgency = 2

    if urgency == 2:
        target = max(target, DAILY_SALARY * 0.65)
    elif urgency == 1:
        target = max(target, DAILY_SALARY * 0.55)

    # If supply is low end, competition for scarce water tends to rise.
    if supply <= (MIN_SUPPLY + 0.5):
        target = max(target, highest_prev_bid * 0.95)

    # Cap target to avoid bankrupting; keep some buffer.
    # Also avoid bidding above what we can afford.
    # If budget is tight, bid a fraction.
    if budget <= DAILY_SALARY * 0.2:
        target = min(target, budget)
    else:
        # Keep bid within a reasonable fraction of daily salary.
        target = min(target, DAILY_SALARY * 0.7)

    # Final clamp
    if budget <= 0:
        return 0.0
    return float(max(0.0, min(budget, target)))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    my_hp = int(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    if not alive:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # React to yesterday bids of alive opponents (only immediate trace)
    prev_bids = []
    for oid, o in alive:
        prev = o.get('previous_trace', {})
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                prev_bids.append(float(bid))
            except Exception:
                pass

    # Determine how aggressive the market was yesterday
    threshold = DAILY_SALARY * 0.85  # ~76.5
    aggressive = any(b >= threshold for b in prev_bids) if prev_bids else False
    max_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Supply-pressure: with higher supply, winning is cheaper; with lower supply, bid more
    # Expected number of units roughly supply / WATER_REQ (but we only need a monotone scaling)
    # Ensure indices are safe (no indexing used here).
    supply_ratio = (supply - 15.0) / (25.0 - 15.0)  # 0..1
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Base bid level
    if aggressive:
        # If they were already paying close to salary, we match moderately to secure our survival.
        base = DAILY_SALARY * (0.55 + 0.25 * (1.0 - supply_ratio))
        # If someone maxed yesterday, nudge up slightly but cap.
        if max_prev_bid > 0:
            base = max(base, min(my_budget, max_prev_bid * 0.85))
    else:
        base = DAILY_SALARY * (0.45 + 0.20 * (1.0 - supply_ratio))

    # Urgency from our hp / no-water streak
    urgency = 0.0
    if my_hp <= 2:
        urgency = 0.35
    elif my_hp <= 4:
        urgency = 0.22
    elif my_hp <= 6:
        urgency = 0.12
    else:
        urgency = 0.06

    if my_no_water_days >= 2:
        urgency += 0.15
    if my_no_water_days >= 4:
        urgency += 0.25

    target = base * (1.0 + urgency)

    # If day is late, slightly increase to avoid running out
    if day >= 8:
        target *= 1.08

    # Final caps: cannot exceed budget; also avoid overpaying beyond what likely wins
    # Use a soft cap near salary since bids seem around 90-120.
    soft_cap = DAILY_SALARY * 1.35
    target = min(target, soft_cap)

    # Ensure non-negative and within budget
    bid = max(0.0, min(my_budget, target))

    # If our budget is very low, still try to bid something only when critical
    if my_budget < DAILY_SALARY * 0.2:
        if my_hp <= 3 or my_no_water_days >= 3:
            bid = max(0.0, min(my_budget, DAILY_SALARY * 0.25))
        else:
            bid = max(0.0, min(my_budget, DAILY_SALARY * 0.1))

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

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Alive opponents and yesterday bids
    alive_opps = []
    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {}) or {}
            if prev and prev.get('bid') is not None:
                try:
                    yesterday_bids.append(float(prev.get('bid')))
                except Exception:
                    pass

    # If no info, default conservative
    if not alive_opps:
        cap = min(budget, DAILY_SALARY * 0.4)
        return max(0.0, cap)

    # Pressure estimate from yesterday
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    # Determine how many allocations are likely needed this day
    # Goal: secure at least one unit of water if possible, but avoid overspending.
    # supply is between 15 and 25; one water unit corresponds to 9.
    possible_units = int(supply / float(WATER_REQ))  # safe int index-like usage
    if possible_units < 1:
        possible_units = 1

    # Base bid depends on HP and how long we've already been without water
    if hp <= 2 or no_water_days >= 2:
        urgency = 0.85
    elif hp <= 4:
        urgency = 0.65
    else:
        urgency = 0.52

    # Opponent pressure adjustment
    # Cindy/David were high; Eric/Alex were low/failed. If highest prev bid is very high, don't match it.
    if highest_prev_bid >= DAILY_SALARY * 1.35:
        pressure = 0.45
    elif highest_prev_bid >= DAILY_SALARY:
        pressure = 0.55
    else:
        pressure = 0.62

    # Supply scaling: when supply is higher, we can bid less and still expect to survive.
    if supply >= 22.0:
        supply_factor = 0.85
    elif supply <= 17.0:
        supply_factor = 1.05
    else:
        supply_factor = 0.95

    target = DAILY_SALARY * urgency * pressure * supply_factor

    # If yesterday bids were low overall, we can be slightly more aggressive to steal allocation.
    if avg_prev_bid < DAILY_SALARY * 0.6:
        target *= 1.08

    # Ensure we don't bid more than budget
    target = min(target, budget)

    # Hard caps for stability
    max_reasonable = DAILY_SALARY * 0.75
    if hp > 5 and no_water_days == 0:
        max_reasonable = DAILY_SALARY * 0.6
    target = min(target, max_reasonable)

    # If budget is tiny, bid what we can
    if target < 0.0:
        target = 0.0

    return float(target)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace for immediate reaction.
    prev_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Base aggressiveness depends on our hp and water stress.
    if hp <= 2 or no_water_days >= 2:
        base = DAILY_SALARY * 0.9
    elif hp <= 4:
        base = DAILY_SALARY * 0.75
    else:
        base = DAILY_SALARY * 0.55

    # If someone was bidding high yesterday, slightly undercut to capture allocation.
    if prev_bids:
        highest = max(prev_bids)
        # Cindy-like pressure: bid high yesterday (>= ~110).
        if highest >= DAILY_SALARY * 0.9:
            target = min(base, highest - 5.0)
            # If our base is already low, still bid enough to compete.
            target = max(target, DAILY_SALARY * 0.45)
        else:
            # Otherwise, bid near the top but not max.
            target = max(base, min(budget, max(prev_bids) * 0.95))

    else:
        target = base

    # Adjust for supply: higher supply allows lower bid to secure enough water.
    # supply in [15,25]
    if supply >= 22:
        target *= 0.9
    elif supply <= 16:
        target *= 1.05

    # Final clamp: cannot exceed budget; also keep within reasonable band.
    target = max(0.0, min(budget, target))

    # If supply is very tight relative to our requirement, ensure we don't go too low.
    # (Assume allocation roughly proportional to bid; we keep a floor.)
    if supply < WATER_REQ + 5:
        target = max(target, DAILY_SALARY * 0.5)

    return float(target)
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

    alive_opps = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Estimate opponent pressure from yesterday's bids (immediate reaction only)
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

    # Base bid target: when others bid high, we must match to avoid being outbid on survival days.
    # Use supply to slightly adjust: higher supply can tolerate slightly lower bids.
    supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_norm = max(0.0, min(1.0, supply_norm))

    # If others were bidding near/above ~1.55*salary, they likely had enough to survive; match a fraction.
    # If highest was low (~0.4*salary), survival may require still being competitive; bid moderate-high.
    low_threshold = DAILY_SALARY * 0.45
    high_threshold = DAILY_SALARY * 1.55

    if highest_prev_bid >= high_threshold:
        target = DAILY_SALARY * (1.35 - 0.25 * supply_norm)
    elif highest_prev_bid >= low_threshold:
        target = max(DAILY_SALARY * 0.95, highest_prev_bid * 0.85)
        target = target * (0.98 - 0.08 * supply_norm)
    else:
        # Opponents likely underbidding like Alex/David; still bid enough to secure water for ourselves.
        target = DAILY_SALARY * (1.05 - 0.15 * supply_norm)

    # HP-aware adjustment: if we're low HP, bid more to prevent death.
    hp = float(my_status['hp'])
    no_water_days = int(my_status.get('no_water_days', 0) or 0)

    if hp <= 1.5:
        target *= 1.15
    elif hp <= 3.0:
        target *= 1.05
    elif no_water_days >= 2:
        target *= 1.10

    # Budget cap and safety floor: never exceed budget; also avoid bidding too low if budget allows.
    budget = float(my_status['budget'])
    if budget <= 0.0:
        return 0.0

    # If we can afford it, bid at least enough to be competitive; otherwise bid a fraction.
    min_competitive = DAILY_SALARY * 0.85
    if budget >= min_competitive:
        bid = min(budget, max(target, min_competitive))
    else:
        bid = min(budget, max(target, budget * 0.6))

    # Final clamp
    bid = max(0.0, min(bid, budget))
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

    # Alive opponents and yesterday bids
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Pressure estimate from yesterday
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = (sum(yesterday_bids) / len(yesterday_bids)) if yesterday_bids else 0.0

    # Base bid depends on current HP and no-water days
    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Supply tightness: when supply is near MIN, competition likely increases
    # Map supply to a 0..1 tightness score (1 = tight)
    if MAX_SUPPLY <= MIN_SUPPLY:
        tightness = 0.5
    else:
        tightness = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)
        if tightness < 0.0:
            tightness = 0.0
        if tightness > 1.0:
            tightness = 1.0

    # Target bid logic:
    # - If others were bidding very high yesterday, match partway.
    # - Otherwise bid around a moderate fraction of salary, scaled by tightness.
    if highest_prev_bid >= DAILY_SALARY * 1.15:
        # Very aggressive field: bid higher if we can survive; otherwise conserve.
        if hp <= 2 or no_water_days >= 1:
            target = DAILY_SALARY * (0.85 + 0.15 * tightness)
        else:
            target = DAILY_SALARY * (0.65 + 0.20 * tightness)
    elif highest_prev_bid >= DAILY_SALARY * 0.85:
        # Moderate-high competition
        if hp <= 2 or no_water_days >= 1:
            target = DAILY_SALARY * (0.75 + 0.20 * tightness)
        else:
            target = max(DAILY_SALARY * 0.55, avg_prev_bid * 0.75) * (0.85 + 0.15 * tightness)
    else:
        # Low competition: still bid enough to secure water under tight supply
        target = DAILY_SALARY * (0.45 + 0.25 * tightness)

    # Ensure feasibility: cannot exceed budget
    # Also avoid extreme overbidding early if budget is low
    max_reasonable = budget
    # If budget is tiny, bid proportionally
    if budget <= DAILY_SALARY * 0.6:
        target = min(target, budget * 0.9)

    # Clamp target
    if target < 0.0:
        target = 0.0
    if target > max_reasonable:
        target = max_reasonable

    # If we are already in danger, push harder
    if hp <= 1 or no_water_days >= 2:
        target = min(budget, max(target, DAILY_SALARY * 0.95))

    # Final safety: if budget is extremely low, bid what we can.
    if budget <= 1e-9:
        return 0.0

    return float(target)
"""
