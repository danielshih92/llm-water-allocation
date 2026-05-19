# ============================================================
# Experiment: exp_075
# Agent: Bob
# Source: exp_075
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

    # If no opponents are alive, bid minimally but enough to avoid no-water days if possible.
    alive_opponents = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.2)

    # React to yesterday's immediate pressure if available.
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        if prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Baseline target bid: aim to win enough water when supply is tight.
    # Convert supply to a rough expected number of winners; keep it simple.
    # If supply is low, bidding slightly higher helps secure water.
    supply_ratio = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # HP-aware risk control: if low hp, don't burn budget; if high hp, bid more.
    hp = float(my_status['hp'])
    if hp <= 2.0:
        hp_factor = 0.35
    elif hp <= 4.0:
        hp_factor = 0.55
    else:
        hp_factor = 0.75

    # If we observed high yesterday bids, slightly outbid to avoid being starved.
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If they were bidding near salary, we assume strong competition.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            base = DAILY_SALARY * 0.40 + (highest_prev_bid - DAILY_SALARY * 0.85) * 0.6
        else:
            base = max(DAILY_SALARY * 0.45, highest_prev_bid + 1.5)
    else:
        # No trace info: bid based on supply tightness.
        # When supply is near MIN_SUPPLY, bid more; when near MAX_SUPPLY, bid less.
        base = DAILY_SALARY * (0.62 - 0.22 * supply_ratio)

    # Ensure we never exceed budget.
    bid = base * hp_factor

    # Additional guard: if my no_water_days is high, increase urgency.
    no_water_days = float(my_status.get('no_water_days', 0.0))
    if no_water_days >= 2.0:
        bid *= 1.25
    elif no_water_days <= 0.5:
        bid *= 0.95

    # Clamp to sensible range.
    bid = max(0.0, min(float(my_status['budget']), bid))

    # If supply is extremely low relative to requirement, make a stronger attempt.
    # (We only have supply bounds, but still apply a small boost.)
    if supply < float(WATER_REQ) * 1.05:
        bid = min(float(my_status['budget']), bid * 1.15)

    return float(bid)
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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        cap = min(my_budget, DAILY_SALARY * 0.4)
        return max(0.0, cap)

    # Read yesterday bids from previous_trace only (immediate reaction)
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # Estimate how aggressive the field was
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    # Supply pressure: with medium supply, water is scarce enough that survival crowd bids matter
    # Compute how many water units supply can cover relative to our requirement
    units = supply / float(WATER_REQ) if WATER_REQ > 0 else 0.0
    # Convert to a rough multiplier: higher supply -> can bid slightly less
    if supply <= MIN_SUPPLY:
        supply_mult = 1.10
    elif supply >= MAX_SUPPLY:
        supply_mult = 0.95
    else:
        # linear interpolation between 1.10 at 15 and 0.95 at 25
        supply_mult = 1.10 - (supply - MIN_SUPPLY) * (1.10 - 0.95) / (MAX_SUPPLY - MIN_SUPPLY)

    # Decision thresholds based on yesterday crowd
    # If yesterday someone bid very high, we need to avoid losing water
    high_pressure = highest_prev_bid >= DAILY_SALARY * 0.85

    # If I'm in danger, overbid
    if my_hp <= 2 or my_no_water_days >= 2:
        target = DAILY_SALARY * (0.92 if high_pressure else 0.80)
    elif my_hp <= 3:
        target = DAILY_SALARY * (0.78 if high_pressure else 0.62)
    else:
        # Moderate bid: track average/highest slightly to beat typical bids without burning budget
        # Use highest_prev_bid when it is meaningful, otherwise use avg_prev_bid.
        anchor = avg_prev_bid if avg_prev_bid > 0 else (DAILY_SALARY * 0.55)
        target = max(anchor * 0.95, DAILY_SALARY * 0.50)
        if high_pressure:
            target = max(target, highest_prev_bid * 0.92)

    target *= supply_mult

    # Safety cap by budget
    bid = min(my_budget, target)

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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', True):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace for immediate reaction
    yesterday_bids = []
    for opp_id, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                yesterday_bids.append(float(bid))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid

    # Supply pressure: if supply barely covers our requirement, we need to secure water.
    # If supply is high, we can bid less and still likely win.
    # Our requirement is 9; supply range 15-25.
    supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY + 1e-9)  # 0..1

    # Base bid: aim slightly above typical opponent bids but cap by budget.
    # Use yesterday highest bid as a proxy for contest intensity.
    # If opponents were aggressive (near our salary), we must match/beat.
    aggressive_threshold = DAILY_SALARY * 0.85  # 76.5

    # If we are in danger (low hp or many no-water days), increase bid.
    danger = (my_hp <= 3.0) or (my_no_water_days >= 2)

    if highest_prev_bid >= aggressive_threshold:
        # Try to outbid the top yesterday bidder by a small increment unless too risky.
        target = highest_prev_bid + 5.0
        if danger:
            target = highest_prev_bid + 12.0
    else:
        # Moderate contest: bid around a fraction of yesterday top, adjusted by supply.
        # Higher supply => bid lower.
        mid = max(DAILY_SALARY * (0.42 + 0.18 * supply_factor), second_prev_bid * 0.85)
        if danger:
            mid = max(mid, DAILY_SALARY * 0.75)
        target = mid

    # Convert target to a safe bid range and ensure we can afford it.
    # Also keep bids from going extreme relative to budget.
    max_reasonable = my_budget * 0.85
    target = min(target, max_reasonable)

    # Final safety: if target is too low and we are likely to lose without water, bump.
    # When supply is low (closer to 15), competition for water is tighter.
    if supply < 18.0 and (my_hp <= 5.0 or my_no_water_days >= 1):
        target = max(target, DAILY_SALARY * (0.55 + 0.15 * (1.0 - supply_factor)))

    # Ensure non-negative and not exceeding budget.
    bid = max(0.0, min(my_budget, float(target)))

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
    day = int(day_context['day'])

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace (immediate reaction)
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Pressure estimate: use top 1-2 bids to gauge competition
    if prev_bids:
        top_bids = sorted(prev_bids, reverse=True)
        highest_prev = top_bids[0]
        second_prev = top_bids[1] if len(top_bids) > 1 else top_bids[0]
    else:
        highest_prev = 0.0
        second_prev = 0.0

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Supply factor: with supply 15-25, water is scarce relative to requirement; bid higher near low supply.
    # Map supply to [0,1] where 0=MIN_SUPPLY, 1=MAX_SUPPLY.
    denom = float(MAX_SUPPLY - MIN_SUPPLY) if (MAX_SUPPLY - MIN_SUPPLY) != 0 else 1.0
    supply_pos = (supply - float(MIN_SUPPLY)) / denom
    if supply_pos < 0.0:
        supply_pos = 0.0
    if supply_pos > 1.0:
        supply_pos = 1.0

    # Base bid: aim to beat typical mid-high opponents without matching extreme max bids.
    # Target around 0.62-0.78 of daily salary depending on supply and HP urgency.
    urgency = 0.0
    if no_water_days >= 2:
        urgency += 0.25
    if my_hp <= 2.0:
        urgency += 0.4
    elif my_hp <= 4.0:
        urgency += 0.2

    # Competition adjustment from yesterday.
    # If someone previously bid very high (>=0.9*salary), competition is intense.
    intense = 1.0 if highest_prev >= (0.9 * DAILY_SALARY) else 0.0
    moderate = 1.0 if highest_prev >= (0.6 * DAILY_SALARY) else 0.0

    # Bid scale: lower supply => higher bid.
    supply_boost = (1.0 - supply_pos) * 0.18

    # Compute candidate
    base = 0.68 * DAILY_SALARY
    base += supply_boost * DAILY_SALARY
    base += urgency * DAILY_SALARY
    if intense > 0.0:
        base += 0.12 * DAILY_SALARY
    elif moderate > 0.0:
        base += 0.06 * DAILY_SALARY

    # Also anchor to yesterday's second-highest bid to slightly outbid typical competition.
    # Avoid jumping to extreme highest_prev (which likely caused Alex's max spike).
    anchor = second_prev + 2.0 if second_prev > 0.0 else 0.0

    if anchor > 0.0:
        candidate = max(base, anchor)
    else:
        candidate = base

    # Cap candidate to avoid overpaying: never exceed 0.95*salary unless critically low HP.
    cap = 0.95 * DAILY_SALARY
    if my_hp <= 1.0:
        cap = 1.05 * DAILY_SALARY

    candidate = min(candidate, cap)

    # Final: ensure we don't exceed budget and keep some reserve.
    # Reserve fraction increases when HP is healthy.
    reserve_frac = 0.15
    if my_hp >= 7.0:
        reserve_frac = 0.28
    elif my_hp >= 4.0:
        reserve_frac = 0.22

    max_affordable = max(0.0, my_budget * (1.0 - reserve_frac))
    bid = min(candidate, max_affordable)

    # If budget is tiny, bid whatever possible.
    if bid <= 0.0:
        bid = min(my_budget, 0.25 * DAILY_SALARY)

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

    # Alive opponents
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    # If no opponents, just cover our requirement.
    if not alive_opps:
        # If we can, bid around one salary fraction; otherwise spend remaining.
        target = DAILY_SALARY * 0.45
        return float(min(my_status['budget'], target))

    # Read yesterday bids from previous_trace only (immediate reaction)
    prev_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate how competitive the market is
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Supply pressure: with higher supply, we can bid less; with lower supply, bid more.
    # supply is between 15 and 25.
    # Map to multiplier roughly in [1.0, 0.6]
    if MAX_SUPPLY - MIN_SUPPLY > 0:
        supply_pos = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_pos = 0.5
    supply_pos = max(0.0, min(1.0, float(supply_pos)))
    # Lower supply -> higher multiplier
    supply_mult = 1.0 - 0.4 * supply_pos

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # If we're already in danger, bid more aggressively.
    danger = (my_hp <= 2.0) or (no_water_days >= 1)

    # If opponents were bidding high yesterday, raise bid a bit; otherwise keep moderate.
    # Cindy/Eric averaged ~130-156 in trace; use that as a reference threshold.
    aggressive_market = highest_prev_bid >= (DAILY_SALARY * 0.85)  # ~76.5

    # Base target bid: aim to be competitive but not maximal.
    # When market is aggressive, we try to match a fraction of highest_prev_bid.
    if aggressive_market:
        # Match 70-85% of the highest prior bid depending on our hp.
        hp_factor = 0.85 if danger else 0.7
        target = highest_prev_bid * hp_factor
    else:
        # Moderate bid anchored around 0.55 salary; adjust by supply.
        target = DAILY_SALARY * 0.55

    target *= supply_mult

    # Ensure we don't bid so low that we likely lose when supply is tight.
    # For supply close to 15, raise floor.
    tight_floor = DAILY_SALARY * (0.6 if supply < 18.0 else 0.45)
    if target < tight_floor and danger:
        target = tight_floor

    # If we have very low budget, spend it.
    if my_budget <= 0.0:
        return 0.0

    # Cap bid to avoid reckless overspending: at most 0.95 salary unless danger.
    cap = DAILY_SALARY * (0.95 if danger else 0.75)
    target = min(target, cap)

    bid = min(my_budget, target)

    # Also, if supply is very high (near 25), we can slightly underbid.
    if supply >= 23.0 and not danger:
        bid *= 0.9

    # Final clamp to non-negative.
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for opp_id, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((opp_id, o))

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Extract yesterday bids from previous_trace
    yesterday_bids = []
    yesterday_hp_after = []
    for opp_id, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid', 0.0)))
                yesterday_hp_after.append(float(prev.get('hp_after', o.get('hp', 0.0))))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid

    # Base aggressiveness: if supply is high, competition likely wants to secure water.
    supply_ratio = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # If opponents were strong yesterday (high bids), we slightly undercut rather than mirror.
    # If my hp is low or I have been without water, I must bid more.
    need_multiplier = 1.0
    if hp <= 2:
        need_multiplier = 1.35
    elif hp <= 4:
        need_multiplier = 1.15

    if no_water_days >= 2:
        need_multiplier *= 1.25
    elif no_water_days == 1:
        need_multiplier *= 1.10

    # Determine target bid level.
    # Use DAILY_SALARY as scale; if highest_prev_bid was close to it, increase.
    pressure = 0.0
    if DAILY_SALARY > 0:
        pressure = highest_prev_bid / DAILY_SALARY
    pressure = max(0.0, min(1.5, pressure))

    # Undercut strategy: bid around (highest - small margin) when pressure high.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Undercut by 5-15% to avoid overpaying.
        margin = 0.08 + 0.07 * (1.0 - supply_ratio)
        target = highest_prev_bid * (1.0 - margin)
    else:
        # Moderate bid: scale with supply and pressure.
        target = DAILY_SALARY * (0.45 + 0.25 * supply_ratio + 0.15 * pressure)
        # If second bidder was meaningful, lean toward it.
        if second_prev_bid > 0:
            target = max(target, second_prev_bid * (0.85 + 0.1 * supply_ratio))

    # Convert target into feasible bid with budget cap.
    # Also keep a floor so we don't get outbid when supply is high.
    floor_bid = DAILY_SALARY * (0.35 + 0.25 * supply_ratio)
    bid = max(floor_bid, target) * need_multiplier

    # Budget safety: never bid more than budget.
    bid = min(bid, budget)

    # If budget is extremely low, bid conservatively.
    if budget <= DAILY_SALARY * 0.2:
        bid = min(budget, DAILY_SALARY * 0.25)

    # Ensure non-negative.
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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Read yesterday bids to infer pressure.
    prev_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # Pressure estimate from yesterday.
    pressure = 0.0
    if prev_bids:
        pressure = max(prev_bids)

    # Base target bid: enough to likely win when supply is tight.
    # Supply tight => higher bid.
    supply_ratio = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    # supply_ratio near 0 => low supply => bid higher
    tightness = 1.0 - max(0.0, min(1.0, supply_ratio))

    # Our urgency: if low hp or already no-water days, bid higher.
    urgency = 0.0
    if my_hp <= 2:
        urgency = 1.0
    elif my_hp <= 4:
        urgency = 0.7
    elif my_hp <= 6:
        urgency = 0.4
    else:
        urgency = 0.2

    if my_no_water_days >= 2:
        urgency = max(urgency, 0.8)

    # Strategy: never bid too low like the agents that died (~32 avg).
    # Use pressure to decide whether to match a high-demand regime.
    # If yesterday peak was very high, we bid moderately below it but above the death level.
    death_level = 35.0

    # Compute candidate bid.
    if pressure >= 150.0:
        # High-demand day: bid in the 110-150 band depending on urgency/tightness.
        target = 120.0 + 25.0 * urgency + 15.0 * tightness
        # Slightly anchor to yesterday peak but stay below it.
        target = min(target, 0.82 * pressure)
    elif pressure >= 80.0:
        target = 85.0 + 30.0 * urgency + 10.0 * tightness
        target = min(target, 0.9 * pressure + 20.0)
    else:
        # Low-demand regime: bid just enough, but still above death level.
        target = 55.0 + 35.0 * urgency + 20.0 * tightness

    # Ensure we don't go below the minimum safe band.
    target = max(target, death_level + 5.0)

    # Budget guard: don't exceed budget; also avoid overspending late.
    # If budget is low, spend proportionally to urgency.
    if my_budget <= 0.0:
        return 0.0

    # Cap spend to a fraction of budget depending on urgency.
    budget_cap = my_budget
    if my_budget > 0:
        # keep some reserve unless very urgent
        reserve_frac = 0.25 if urgency < 0.7 else 0.05
        budget_cap = my_budget * (1.0 - reserve_frac)

    bid = min(target, budget_cap)

    # If still too low relative to urgency and budget allows, lift to a minimum.
    min_bid = 0.0
    if urgency >= 0.8:
        min_bid = 70.0
    elif urgency >= 0.4:
        min_bid = 55.0
    else:
        min_bid = 45.0

    bid = max(bid, min_bid if my_budget >= min_bid else bid)

    # Final clamp
    bid = max(0.0, min(bid, my_budget))
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

    # Alive opponents only
    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive.append((opp_id, opp))

    # If no one is alive, conserve budget
    if not alive:
        return max(0.0, min(float(my_status.get('budget', 0.0)), DAILY_SALARY * 0.4))

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Read yesterday bids from traces for immediate reaction
    prev_bids = []
    for _, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate how competitive the market was
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_highest_prev_bid = 0.0
    if len(prev_bids) >= 2:
        sorted_b = sorted(prev_bids, reverse=True)
        second_highest_prev_bid = sorted_b[1]

    # Identify who is under pressure (no_water_days high or hp low) to anticipate their next bid
    pressure = 0
    for _, opp in alive:
        opp_hp = float(opp.get('hp', 0.0))
        opp_no = int(opp.get('no_water_days', 0))
        if opp_no >= 2 or opp_hp <= 2:
            pressure += 1

    # Baseline bid: aim to be competitive but not reckless
    # If I'm low hp or have missed water, increase bid to secure water.
    if my_hp <= 2.0 or no_water_days >= 2:
        base = DAILY_SALARY * 0.85
    elif my_hp <= 4.0 or no_water_days == 1:
        base = DAILY_SALARY * 0.65
    else:
        base = DAILY_SALARY * 0.52

    # If market was hot yesterday, slightly overbid the likely leader
    # Cindy showed very high average bid and survived; match the pattern when competition is high.
    hot_market = highest_prev_bid >= DAILY_SALARY * 0.9
    if hot_market:
        target = highest_prev_bid + 2.0
    else:
        # If not too hot, try to beat second tier
        target = max(base, second_highest_prev_bid + 1.5)

    # If many opponents are under pressure, expect higher bids; raise target modestly
    if pressure >= 2:
        target *= 1.05

    # Scale with remaining supply fraction: lower supply => higher chance to be contested
    # supply in [15,25]; map to multiplier in [1.10, 0.95]
    if supply <= 0:
        supply_mult = 1.0
    else:
        supply_clamped = max(MIN_SUPPLY, min(MAX_SUPPLY, supply))
        supply_mult = 1.10 - (supply_clamped - MIN_SUPPLY) * (0.15 / (MAX_SUPPLY - MIN_SUPPLY))

    bid = target * supply_mult

    # Never exceed budget; also avoid bidding above what would be wasteful late/early
    # Late game: bid more aggressively to avoid elimination.
    if day >= 8:
        bid *= 1.08

    bid = max(0.0, min(my_budget, bid))

    # Ensure some minimal bid if budget allows
    if my_budget > 0 and bid < DAILY_SALARY * 0.15:
        bid = min(my_budget, DAILY_SALARY * 0.15)

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

    # Identify alive opponents and their yesterday bids
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid', None)
            alive_opps.append((opp_id, opp, bid))

    if not alive_opps:
        # No one to compete with; conserve budget
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    yesterday_bids = []
    for _, _, bid in alive_opps:
        if bid is not None:
            try:
                yesterday_bids.append(float(bid))
            except Exception:
                pass

    # Supply scarcity pressure: fewer units means higher contest intensity
    # Use explicit int conversions for any indexing (none used here).
    scarcity = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        scarcity = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    # Compute a target bid based on yesterday's aggressiveness by survivors
    # If someone bid very high yesterday, we must match/beat to prevent them from securing water.
    high_thresh = DAILY_SALARY * 0.85
    mid_thresh = DAILY_SALARY * 0.55

    target = DAILY_SALARY * (0.45 + 0.35 * scarcity)

    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        lowest_prev = min(yesterday_bids)

        if highest_prev >= high_thresh:
            # Someone was extremely aggressive; bid to contest.
            if my_status.get('hp', 0) <= 2:
                target = DAILY_SALARY * (0.95 - 0.05 * scarcity)
            elif my_status.get('hp', 0) <= 3:
                target = DAILY_SALARY * (0.75 + 0.15 * scarcity)
            else:
                target = max(target, highest_prev + 1.0)
        elif highest_prev >= mid_thresh:
            # Moderate aggression; slightly over the median/typical range.
            target = max(target, (highest_prev * 0.9) + (1.0 * scarcity))
        else:
            # Low bids yesterday; we can undercut slightly but still secure.
            target = max(target, lowest_prev + 2.0 * (1.0 - scarcity))

    # If we're in danger (low hp or many no-water days), increase bid.
    hp = float(my_status.get('hp', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    if hp <= 1.0 or no_water_days >= 3:
        target = max(target, DAILY_SALARY * (0.85 + 0.1 * scarcity))
    elif hp <= 3.0:
        target = max(target, DAILY_SALARY * (0.6 + 0.15 * scarcity))

    # Clamp by budget and keep within a reasonable cap relative to supply
    budget = float(my_status.get('budget', 0))
    if budget <= 0:
        return 0.0

    # Convert target to feasible bid: never exceed budget.
    bid = float(min(budget, target))

    # Additional cap: avoid extreme bids beyond what supply range suggests.
    # Since supply max is 25, water units are at most floor(supply/9) ~ 2.
    # Keep bid around at most 2.2 * salary fraction.
    bid_cap = DAILY_SALARY * 1.5
    bid = min(bid, bid_cap)

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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    # Alive opponents
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    if not alive:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    # Read yesterday bids from previous_trace only
    prev_bids = []
    for oid, o in alive:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Identify Cindy-like aggressor by max yesterday bid
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate urgency: if we've already missed water days or low hp, bid more aggressively
    urgency = 0
    if my_hp <= 2:
        urgency += 2
    elif my_hp <= 4:
        urgency += 1
    if my_no_water_days >= 2:
        urgency += 1

    # Supply pressure: lower supply means fewer allocations; bid slightly more
    # supply is between 15 and 25; map to [0,1]
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_pressure = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_pressure = 0.5

    # Base bid target: conserve when healthy and no strong prior aggressor
    if urgency == 0 and highest_prev_bid < DAILY_SALARY * 0.7:
        target = DAILY_SALARY * (0.45 + 0.15 * supply_pressure)
    else:
        # If someone previously bid high (Cindy), overbid just enough to steal.
        # Use a small premium over the highest previous bid, but cap by urgency.
        premium = 5.0 + 10.0 * supply_pressure
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # High aggressor: respond with a near-daily-salary bid if we are at risk.
            target = highest_prev_bid + premium
            if urgency >= 2:
                target = max(target, DAILY_SALARY * 0.9)
            else:
                target = min(target, DAILY_SALARY * 0.75)
        else:
            # Moderate aggressor: bid around 60-75% salary depending on urgency
            target = DAILY_SALARY * (0.6 + 0.15 * supply_pressure + 0.1 * urgency)
            if highest_prev_bid > 0:
                target = max(target, min(highest_prev_bid + premium * 0.6, DAILY_SALARY * 0.8))

    # Ensure we don't bid more than budget; also avoid bidding above a plausible daily cap
    # (game likely uses budget and salary as constraints)
    cap = my_budget
    # If budget is tiny, bid whatever we can to avoid immediate death
    if my_budget <= DAILY_SALARY * 0.2:
        target = my_budget
    else:
        # Keep a safety margin so we can continue later days
        safety = 0.15 if my_hp >= 5 else 0.05
        cap = my_budget * (1.0 - safety)
        if cap < 0:
            cap = 0.0
        target = min(target, cap)

    # If we are very low hp, prefer spending to secure water.
    if my_hp <= 1:
        target = min(my_budget, max(target, DAILY_SALARY * 0.85))

    # Final clamp to non-negative
    if target < 0:
        target = 0.0
    return float(target)
"""
