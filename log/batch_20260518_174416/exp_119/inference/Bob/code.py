# ============================================================
# Experiment: exp_119
# Agent: Bob
# Source: exp_119
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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # If no opponents, take safe minimum to stay alive.
    if not alive_opps:
        target = min(budget, DAILY_SALARY * 0.35)
        return max(0.0, target)

    # Read yesterday bids (immediate reaction only).
    yesterday_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how tight supply is; higher supply lets us bid less.
    # supply is in [15,25]; map to 0..1.
    tightness = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        tightness = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    tightness = max(0.0, min(1.0, tightness))

    # Determine aggressiveness based on their previous bid.
    # If they were near our salary, they likely expect to win; we respond with a near-just-enough bid.
    aggressive = highest_prev_bid >= DAILY_SALARY * 0.85

    # Base bid level: mid when not aggressive, higher when aggressive.
    # Also scale with our hp and no-water tolerance.
    if aggressive:
        # If we are healthy, conserve; if low hp or close to failure, bid more.
        if hp <= 2.0 or no_water_days >= 2:
            base = DAILY_SALARY * 0.95
        elif hp <= 3.0:
            base = DAILY_SALARY * 0.75
        else:
            base = DAILY_SALARY * 0.55
    else:
        # Not aggressive: bid around a fraction of salary, slightly higher when supply is tight.
        base = DAILY_SALARY * (0.40 + 0.20 * tightness)

    # Try to outbid their last highest by a small increment when we have budget.
    # Keep increment small to avoid overpaying.
    increment = 1.5 + 2.0 * tightness
    desired = base
    if highest_prev_bid > 0.0:
        desired = max(desired, highest_prev_bid + increment)

    # If we are in danger, ensure we bid enough to secure water.
    # (We don't know exact scoring, so we use a conservative boost.)
    if hp <= 1.5 or no_water_days >= 3:
        desired = max(desired, DAILY_SALARY * 0.90)

    # Cap by budget.
    if budget <= 0.0:
        return 0.0

    bid = min(budget, desired)
    # Ensure non-negative and not absurd.
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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 1))

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read only yesterday's immediate reaction from previous_trace
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

    # Estimate how many water units exist; use this to avoid waste
    # (indices not needed, but keep logic float-safe)
    max_units = max(0.0, supply / float(WATER_REQ))

    # Core strategy: if others were bidding aggressively, we match with a slight discount.
    # Thresholds tuned to yesterday's observed winners (~98-112).
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # If we're healthy, we can underbid slightly; if low HP, we must bid higher.
        if hp > 3:
            target = DAILY_SALARY * 0.78
        else:
            target = DAILY_SALARY * 0.92
    elif highest_prev_bid >= DAILY_SALARY * 0.55:
        target = DAILY_SALARY * 0.62
    else:
        target = DAILY_SALARY * 0.50

    # Supply-aware cap: if supply is low, bidding too high is inefficient.
    # With supply in [15,25], max_units in [1.66,2.77]. Cap bid to keep budget for later.
    if max_units < 2.2:
        target *= 0.9

    # Urgency adjustment based on no_water_days / hp
    # If we've already been without water, increase bid.
    if no_water_days >= 2 or hp <= 2:
        target *= 1.10

    # Late-episode pressure: bid a bit more as days approach end (episode_days=10)
    # day_context doesn't include episode_days; use day as proxy.
    if day >= 8:
        target *= 1.08

    # Final clamp by budget and a hard upper bound tied to supply
    # If budget is tight, spend enough to avoid immediate collapse.
    spend_cap = max(0.0, min(budget, DAILY_SALARY * 1.05))
    bid = max(0.0, min(spend_cap, target))

    # Ensure we don't bid trivially when we have budget and are at risk.
    if bid < DAILY_SALARY * 0.25 and (hp <= 3 or no_water_days >= 1):
        bid = min(spend_cap, DAILY_SALARY * 0.35)

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
    for oid, o in opponents_status.items():
        if bool(o.get('alive', False)):
            alive_opps.append(o)

    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    prev_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate aggressiveness from yesterday
    if prev_bids:
        max_prev_bid = max(prev_bids)
        avg_prev_bid = sum(prev_bids) / float(len(prev_bids))
    else:
        max_prev_bid = 0.0
        avg_prev_bid = 0.0

    # Supply pressure: when supply is high, water is easier to secure; bid less.
    # When supply is low, water is scarce; bid more.
    # Map supply in [15,25] to scarcity in [1.0,0.0]
    if MAX_SUPPLY <= MIN_SUPPLY:
        scarcity = 0.5
    else:
        scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
        if scarcity < 0.0:
            scarcity = 0.0
        if scarcity > 1.0:
            scarcity = 1.0

    # If our hp is low or we've already missed water, we must secure water.
    critical = (my_hp <= 2.5) or (my_no_water_days >= 1)

    # Target bid band: Cindy/Eric were ~132-145; try to undercut slightly while still winning.
    # If supply is scarce or we're critical, approach the top band.
    base = DAILY_SALARY * (0.35 + 0.35 * scarcity)  # ~31.5 to 63

    if critical:
        base = DAILY_SALARY * (0.75 + 0.15 * scarcity)  # ~67.5 to 90

    # Use yesterday's max bid as an upper reference; don't always match it.
    # If max_prev_bid is high, we increase our bid to compete.
    if max_prev_bid > 120.0:
        comp = 0.85 * max_prev_bid
    elif max_prev_bid > 80.0:
        comp = 0.75 * max_prev_bid
    else:
        comp = 0.0

    # Combine: choose the higher of base and a fraction of yesterday's max, but cap.
    bid_target = max(base, comp)

    # Slight day-based adjustment to avoid ties late: bid a bit higher on later days.
    # Keep it small.
    bid_target *= (1.0 + 0.01 * max(0, day - 1))

    # Cap by what we can pay and keep within reasonable range.
    bid = max(0.0, min(my_budget, bid_target))

    # Ensure we bid at least a minimal amount if we can; otherwise 0.
    if my_budget <= 0.0:
        return 0.0
    if bid < 1.0 and my_budget >= 1.0:
        bid = 1.0

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

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    # Alive opponents only
    alive_opps = []
    for opp_id, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((opp_id, o))

    # If no info, default conservative
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.5))

    # Read yesterday bids from previous_trace (immediate reaction)
    prev_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate what band opponents likely target today
    if prev_bids:
        # Use upper quantile-ish logic without heavy history
        sorted_b = sorted(prev_bids)
        n = len(sorted_b)
        idx = int(n - 1)  # max
        max_prev = sorted_b[idx]
        idx_mid = int(max(0, n // 2))
        mid_prev = sorted_b[idx_mid]
        # If someone bid very high yesterday, slightly overbid to secure water
        pressure = max_prev
    else:
        pressure = 0.0
        mid_prev = 0.0

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Determine aggressiveness by supply and our HP
    # More supply => cheaper to win; low supply => conserve.
    supply_ratio = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_ratio = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    if supply_ratio < 0.0:
        supply_ratio = 0.0
    if supply_ratio > 1.0:
        supply_ratio = 1.0

    # Base target
    # If Cindy/Eric were bidding high yesterday, we try to beat them when supply is favorable.
    favorable = supply_ratio >= 0.6

    # Conservative survival guard
    # If we're close to death, bid more.
    if hp <= 2 or no_water_days >= 2:
        base = DAILY_SALARY * (0.9 if favorable else 0.75)
    elif hp <= 4:
        base = DAILY_SALARY * (0.7 if favorable else 0.55)
    else:
        base = DAILY_SALARY * (0.6 if favorable else 0.45)

    # If yesterday pressure was high, nudge upward but not to full pressure.
    # Aim: slightly above mid, but capped below max_prev unless we must.
    target = base
    if prev_bids:
        # If max_prev indicates strong contention, overbid modestly.
        if pressure >= DAILY_SALARY * 1.2:
            target = max(target, mid_prev * 1.05)
        elif pressure >= DAILY_SALARY * 0.9:
            target = max(target, mid_prev * 0.98)
        else:
            # Mild contention: stay near base
            target = max(target, mid_prev * 0.9)

    # Hard caps to avoid bankrupting
    # Do not exceed a fraction of budget; also keep some runway.
    cap = budget * (0.55 if favorable else 0.45)
    # If budget is small, still bid up to what we can.
    cap = float(min(cap, budget))

    bid = float(min(target, cap))

    # Ensure non-negative
    if bid < 0.0:
        bid = 0.0

    # If we have very high budget but low HP, ensure meaningful bid
    if budget > 0 and bid < DAILY_SALARY * 0.25 and (hp <= 3 or no_water_days >= 2):
        bid = float(min(budget, DAILY_SALARY * (0.6 if favorable else 0.5)))

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

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    my_hp = my_status.get('hp', 0)
    my_budget = my_status.get('budget', 0.0)
    my_no_water_days = my_status.get('no_water_days', 0)

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    # If no opponents are alive, conserve.
    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Use only yesterday's immediate trace to gauge pressure.
    yesterday_bids = []
    yesterday_hp_after = []
    for opp_id, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            yesterday_hp_after.append(prev.get('hp_after', None))

    # Baseline from observed bids.
    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        min_prev_bid = min(yesterday_bids)
        # Target slightly above the weakest surviving bid to steal allocation.
        # Keep well below the top bid tier.
        target = 0.5 * (min_prev_bid + max_prev_bid)
        # Pull toward min_prev_bid more aggressively if my hp is healthy.
        if my_hp >= 8:
            target = min_prev_bid + 0.25 * (max_prev_bid - min_prev_bid)
        # If I'm in danger, move toward the upper tier.
        if my_hp <= 3 or my_no_water_days >= 2:
            target = min(max_prev_bid - 5.0, min_prev_bid + 0.75 * (max_prev_bid - min_prev_bid))
    else:
        # Fallback: moderate bid.
        target = DAILY_SALARY * 0.6

    # Incorporate supply pressure: higher supply reduces need to overbid.
    # supply is float; use thresholds with no indexing.
    if supply >= 22.0:
        target *= 0.9
    elif supply <= 17.0:
        target *= 1.05

    # Ensure we don't bid below a useful floor; also cap by affordability.
    floor_bid = DAILY_SALARY * 0.45
    danger_floor = DAILY_SALARY * 0.85
    if my_hp <= 2 or my_no_water_days >= 3:
        floor_bid = danger_floor

    bid = max(floor_bid, target)

    # If David died yesterday, it suggests some agents underbid; we can slightly undercut top tier.
    # Detect a likely underbidding agent from trace.
    for opp_id, opp in opponents_status.items():
        prev = opp.get('previous_trace', {})
        if prev and prev.get('status') == 'dead' and prev.get('hp_after', 0) is not None:
            # If their bid was low, keep our bid just above that level.
            dead_bid = prev.get('bid', None)
            if dead_bid is not None:
                bid = max(bid, float(dead_bid) + 10.0)

    # Final clamp to budget.
    if my_budget <= 0:
        return 0.0
    if bid > my_budget:
        bid = my_budget

    # Avoid negative or NaN.
    if bid < 0:
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Basic safety: if critically low hp, bid to secure water
    my_hp = int(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        # No one to compete with
        return min(my_budget, DAILY_SALARY * 0.4)

    # Read yesterday's immediate pressure from previous_trace
    prev_bids = []
    prev_hp_after = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
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
    # If someone was already bidding aggressively yesterday, match just enough
    aggressive_threshold = DAILY_SALARY * 0.85  # 76.5

    # Supply-aware base: with supply in [15,25], water is scarce but not extreme.
    # Aim to win at a discount relative to highest_prev_bid.
    if highest_prev_bid >= aggressive_threshold:
        # If my hp is low or I've already missed water, increase bid
        if my_hp <= 2 or my_no_water_days >= 1:
            bid = min(my_budget, highest_prev_bid * 0.98)
        else:
            bid = min(my_budget, max(DAILY_SALARY * 0.45, highest_prev_bid * 0.92))
    else:
        # Lower pressure overall: undercut the top bidder slightly
        if my_hp <= 2 or my_no_water_days >= 2:
            bid = min(my_budget, DAILY_SALARY * 0.85)
        else:
            # Undercut expectation by targeting around 55% salary, but not below a floor
            bid = min(my_budget, max(DAILY_SALARY * 0.55, highest_prev_bid * 0.85))

    # Additional micro-adjustment: if Cindy survived with high hp yesterday, she likely bids consistently.
    # If her previous bid was known and high, nudge slightly lower to steal.
    for oid, o in alive_opps:
        if oid == 'Cindy':
            prev = o.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    c_bid = float(prev['bid'])
                    # If Cindy was bidding higher than my computed bid, try to sit just below it
                    if c_bid > 0:
                        bid = min(bid, max(0.0, c_bid - 2.0))
                except Exception:
                    pass

    # Ensure non-negative and keep within budget
    if bid < 0.0:
        bid = 0.0
    bid = min(float(bid), my_budget)

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

    supply = day_context['supply']
    day = day_context['day']

    # Identify alive opponents and extract yesterday bids
    alive_opps = []
    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(float(prev['bid']))

    # If no opponents alive, conserve
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Use yesterday's max bid as pressure proxy
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Supply pressure: higher supply reduces need to overbid
    # Normalize supply into [0,1]
    if MAX_SUPPLY == MIN_SUPPLY:
        supply_factor = 0.5
    else:
        supply_factor = (float(supply) - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
        if supply_factor < 0.0:
            supply_factor = 0.0
        if supply_factor > 1.0:
            supply_factor = 1.0

    # Determine target bid bracket
    # If someone bid very high yesterday, we must match to secure water.
    # Otherwise, bid enough to beat typical low bids but avoid Cindy-like overpay.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        base = DAILY_SALARY * (0.33 if my_status['hp'] > 3 else 0.9)
    else:
        # Mildly react to observed pressure
        # Keep it below Cindy-like levels unless my hp is critical.
        react = highest_prev_bid + 5.0
        base = max(DAILY_SALARY * 0.45, react)
        if my_status['hp'] <= 2:
            base = max(base, DAILY_SALARY * 0.85)

    # Adjust for supply: when supply is abundant, reduce bid slightly
    # When supply is scarce, increase bid slightly
    # supply_factor=1 => abundant => reduce; supply_factor=0 => scarce => increase
    if supply_factor >= 0.5:
        base *= 0.92
    else:
        base *= 1.05

    # Budget safety: never bid more than what we can afford while keeping some runway
    budget = float(my_status['budget'])
    hp = int(my_status['hp'])

    # If hp is already healthy, be conservative with budget
    if hp >= 6:
        cap = budget * 0.35
    elif hp >= 4:
        cap = budget * 0.45
    else:
        cap = budget * 0.75

    bid = float(min(budget, base, cap))

    # Ensure non-negative and at least a small amount if possible
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

    # Alive opponents and their yesterday bids
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            prev = o.get('previous_trace', {}) or {}
            bid = prev.get('bid', None)
            if bid is None:
                continue
            alive.append((oid, float(bid), o))

    # Budget safety
    budget = float(my_status.get('budget', 0.0))
    hp = float(my_status.get('hp', 0.0))

    # If no info, bid a conservative amount
    if not alive:
        target = DAILY_SALARY * 0.55
        return min(budget, target)

    # Pressure from yesterday
    yesterday_bids = [b for _, b, _ in alive]
    highest_prev = max(yesterday_bids)
    second_prev = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev

    # Compute a pressure factor: how aggressive others were
    # If highest_prev was near/above 0.85*DAILY_SALARY, assume strong competition.
    pressure = 0.0
    if highest_prev >= 0.85 * DAILY_SALARY:
        pressure = 1.0
    elif highest_prev >= 0.6 * DAILY_SALARY:
        pressure = 0.7
    elif highest_prev >= 0.35 * DAILY_SALARY:
        pressure = 0.4
    else:
        pressure = 0.2

    # Base bid depends on supply: higher supply means we can bid less to secure water.
    # Supply is between 15 and 25.
    supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if (MAX_SUPPLY - MIN_SUPPLY) != 0 else 0.5
    supply_norm = 0.0 if supply_norm < 0.0 else (1.0 if supply_norm > 1.0 else supply_norm)

    # Need more when hp is low
    if hp <= 2:
        hp_mult = 1.25
    elif hp <= 4:
        hp_mult = 1.1
    else:
        hp_mult = 0.95

    # Aim to slightly beat the second-highest yesterday bid when competition is high.
    # Otherwise, bid around a fraction of the salary.
    if pressure >= 0.7:
        target = second_prev + 3.0
    else:
        target = DAILY_SALARY * (0.45 + 0.25 * pressure)

    # Adjust for supply: with more supply, reduce bid; with less, increase.
    target = target * (0.95 + 0.1 * (1.0 - supply_norm))

    # Ensure we don't overspend: keep a reserve for later days.
    # Reserve more when hp is healthy.
    if hp >= 6:
        reserve_frac = 0.35
    else:
        reserve_frac = 0.15

    max_affordable = max(0.0, budget * (1.0 - reserve_frac))
    target = min(target, max_affordable)

    # If budget is tiny, bid whatever remains.
    if budget <= 1.0:
        return max(0.0, budget)

    # Final clamp
    if target < 0.0:
        target = 0.0
    return min(budget, target)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        return float(min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from immediate previous_trace
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

    # Estimate how many water units we likely need to stay safe.
    # If hp is low or we've already had no-water days, bid more.
    urgency = 0.0
    if hp <= 2.0:
        urgency += 1.0
    if no_water_days >= 2:
        urgency += 0.8
    if hp <= 3.0:
        urgency += 0.4

    # Supply pressure: with supply in [15,25], per-water scarcity is higher near 15.
    supply_mid = (MIN_SUPPLY + MAX_SUPPLY) / 2.0
    scarcity = 0.0
    if supply <= supply_mid:
        scarcity = (supply_mid - supply) / (supply_mid - MIN_SUPPLY + 1e-9)  # 0..~1
        scarcity = max(0.0, min(1.0, scarcity))

    # Strategy: match/just-under top previous bid when supply is tighter; otherwise bid around a baseline.
    # Use a cap to avoid overspending.
    baseline = DAILY_SALARY * (0.45 + 0.25 * scarcity)

    # If opponents already bid very high yesterday, we must contest but not fully.
    # Target slightly below yesterday's highest bid to win if they overbid.
    target = baseline
    if highest_prev_bid > 0.0:
        if scarcity >= 0.4:
            # contest more when supply is tighter
            target = min(target, highest_prev_bid * 0.92)
        else:
            target = min(target, highest_prev_bid * 0.85)

    # Increase with urgency
    target = target * (1.0 + 0.35 * urgency)

    # Hard constraints: never exceed budget, and avoid suicidal bids.
    # Since bids are in same units as salary, keep within a reasonable fraction of budget.
    max_affordable = budget
    # If budget is very low, bid what we can.
    if max_affordable <= 0.0:
        return 0.0

    # Also avoid bidding above a soft cap to prevent running out.
    soft_cap = DAILY_SALARY * (1.05 + 0.25 * scarcity + 0.4 * urgency)
    bid = min(max_affordable, soft_cap, target)

    # If we are extremely urgent, ensure we bid enough to likely secure water.
    if urgency >= 1.0:
        bid = max(bid, min(max_affordable, DAILY_SALARY * 0.75 + 20.0 * scarcity))

    # Ensure non-negative
    if bid < 0.0:
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context['supply'])
    day = day_context['day']

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday bids from immediate previous_trace only
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate competitive level from yesterday
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        avg_prev_bid = sum(prev_bids) / float(len(prev_bids))
    else:
        highest_prev_bid = 0.0
        avg_prev_bid = 0.0

    # Supply pressure: with higher supply, we can bid less; with lower supply, bid more.
    supply_norm = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)  # 0..1
    supply_norm = max(0.0, min(1.0, supply_norm))

    # Base target: slightly below yesterday average/highest to exploit overbidding.
    # If others were extremely aggressive, we still need to be competitive.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        target = max(DAILY_SALARY * 0.35, avg_prev_bid * 0.88)
    else:
        target = max(DAILY_SALARY * 0.45, avg_prev_bid * 0.9)

    # My urgency: fewer hp or more consecutive no-water days -> bid up.
    if hp <= 2.0:
        target *= 1.35
    elif hp <= 4.0:
        target *= 1.15

    if no_water_days >= 2:
        target *= 1.25
    elif no_water_days == 1:
        target *= 1.10

    # Adjust with supply: lower supply means bid more.
    target *= (0.95 + (1.0 - supply_norm) * 0.25)

    # Hard caps to avoid budget ruin.
    # If budget is low, bid a fraction to preserve future rounds.
    if budget <= DAILY_SALARY * 0.6:
        cap = budget * 0.7
    elif budget <= DAILY_SALARY * 1.2:
        cap = budget * 0.55
    else:
        cap = budget * 0.45

    bid = min(cap, target)

    # Ensure non-negative and at least a small amount if needed.
    if bid < 0.0:
        bid = 0.0

    return float(bid)
"""
