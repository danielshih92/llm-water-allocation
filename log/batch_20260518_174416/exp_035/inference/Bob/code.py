# ============================================================
# Experiment: exp_035
# Agent: Bob
# Source: exp_035
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
    day = day_context.get('day', 1)

    budget = float(my_status.get('budget', 0.0))
    hp = int(my_status.get('hp', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    # Default target: moderate bid to compete without burning budget.
    base_bid = DAILY_SALARY * 0.55

    # React to yesterday's behavior (only immediate previous_trace).
    # If any opponent was aggressive yesterday, we slightly outbid to secure water.
    aggressive_threshold = DAILY_SALARY * 0.85
    highest_prev_bid = None
    if alive_opponents:
        for _, opp in alive_opponents:
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                b = float(prev.get('bid'))
                if highest_prev_bid is None or b > highest_prev_bid:
                    highest_prev_bid = b

    # If we are in danger (low hp or many no-water days), bid higher.
    danger = (hp <= 2) or (no_water_days >= 2)

    if highest_prev_bid is not None:
        if highest_prev_bid >= aggressive_threshold:
            # Opponent likely willing to spend; match/beat with a small premium.
            bid = DAILY_SALARY * (0.75 if not danger else 0.95)
        else:
            # Opponent not too aggressive; bid around base, but slightly above their likely level.
            bid = max(base_bid, highest_prev_bid + 1.5)
            if danger:
                bid = max(bid, DAILY_SALARY * 0.80)
    else:
        bid = DAILY_SALARY * (0.70 if danger else 0.55)

    # Supply-aware adjustment: when supply is tight, increase bid.
    # supply in [15,25], so normalize.
    if supply <= float(MIN_SUPPLY) + 0.5:
        bid *= 1.15
    elif supply >= float(MAX_SUPPLY) - 0.5:
        bid *= 0.95

    # Ensure we never exceed budget.
    bid = min(bid, budget)

    # Also keep bid within reasonable bounds (non-negative).
    if bid < 0.0:
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

    supply = day_context['supply']
    day = day_context['day']

    # Alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # If alone, bid enough but not wasteful
    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Read yesterday bids from previous_trace only
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

    # Estimate how many winners are likely: with supply in [15,25] and requirement 9,
    # at most 2 players can be fully satisfied; competition tends to be for the top 1-2.
    # Use this to decide whether to match the aggression.
    try:
        supply_int = int(supply)
    except Exception:
        supply_int = int(float(supply))

    # Target bid logic: if others were aggressive yesterday, we slightly undercut to win
    # while preserving budget.
    aggressive_threshold = DAILY_SALARY * 0.85  # 76.5

    hp = my_status.get('hp', 0)
    budget = my_status.get('budget', 0)
    no_water_days = my_status.get('no_water_days', 0)

    # Base bid depending on our urgency
    if hp <= 2 or no_water_days >= 2:
        urgency_mult = 0.95
    elif hp <= 4 or no_water_days >= 1:
        urgency_mult = 0.75
    else:
        urgency_mult = 0.6

    # If yesterday's highest bid was high, we bid near it but not equal.
    if highest_prev_bid >= aggressive_threshold:
        # Undercut by a small margin; also cap by urgency.
        target = highest_prev_bid - 3.0
        # Ensure still competitive
        floor = DAILY_SALARY * 0.55
        target = max(target, floor)
    else:
        # When others were moderate, bid around mid
        target = max(DAILY_SALARY * 0.5, highest_prev_bid * 0.85 + 5.0)

    # Supply adjustment: lower supply -> higher competition
    if supply_int <= 17:
        target *= 1.10
    elif supply_int >= 23:
        target *= 0.95

    # Final cap by budget
    bid = min(budget, target * urgency_mult)

    # If budget is very small, still bid something rational
    if bid < 0:
        bid = 0
    if bid == 0 and budget > 0:
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

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for agent_id, st in opponents_status.items():
        if st.get('alive'):
            alive_opps.append((agent_id, st))

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday bids to infer who pressures prices
    yesterday_bids = []
    for agent_id, st in alive_opps:
        prev = st.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Identify Cindy-like heavy bidder by yesterday bid magnitude
    heavy_prev = None
    for agent_id, st in alive_opps:
        prev = st.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                b = float(prev.get('bid'))
            except Exception:
                continue
            if heavy_prev is None or b > heavy_prev[1]:
                heavy_prev = (agent_id, b)

    heavy_bid = heavy_prev[1] if heavy_prev is not None else 0.0

    # Base strategy: bid higher when supply is tight or HP is low.
    # Supply factor: lower supply -> higher urgency.
    supply_tightness = (float(MAX_SUPPLY) - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if supply_tightness < 0.0:
        supply_tightness = 0.0
    if supply_tightness > 1.0:
        supply_tightness = 1.0

    urgency_hp = 0.0
    if hp <= 2.0:
        urgency_hp = 1.0
    elif hp <= 4.0:
        urgency_hp = 0.6
    elif hp <= 6.0:
        urgency_hp = 0.3
    else:
        urgency_hp = 0.1

    urgency_no_water = 0.0
    if no_water_days >= 2:
        urgency_no_water = 0.8
    elif no_water_days == 1:
        urgency_no_water = 0.4
    else:
        urgency_no_water = 0.1

    urgency = 0.45 * supply_tightness + 0.35 * urgency_hp + 0.20 * urgency_no_water

    # If a clear heavy bidder existed yesterday (Cindy), avoid matching her exactly.
    # Instead, bid enough to not be completely priced out.
    # Target: either slightly below heavy_bid scale, or a fraction of DAILY_SALARY.
    if heavy_bid >= 110.0:
        target = 0.62 * heavy_bid
    elif highest_prev_bid >= 80.0:
        target = 0.55 * highest_prev_bid
    else:
        target = DAILY_SALARY * 0.55

    # Adjust by urgency and remaining budget.
    # Cap to avoid overspending: never exceed ~1.1*DAILY_SALARY per day when possible.
    target = target * (0.75 + 0.5 * urgency)
    hard_cap = DAILY_SALARY * 1.1

    bid = min(budget, hard_cap, target)

    # If very low budget, still bid something to extend survival when urgent.
    if bid < 1.0 and urgency >= 0.7:
        bid = min(budget, DAILY_SALARY * 0.3)

    # Ensure non-negative
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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive.append((opp_id, opp))

    if not alive:
        return float(min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace only (immediate reaction)
    prev_bids = []
    prev_by_id = {}
    for opp_id, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                b = float(bid)
                prev_bids.append(b)
                prev_by_id[opp_id] = b
            except Exception:
                pass

    # Estimate how many days of water we can buy if we win today.
    # Use a conservative mapping from supply to water units.
    # (We avoid assuming exact game mechanics; use it only for relative pressure.)
    supply_level = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_level = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_level = max(0.0, min(1.0, supply_level))

    # Determine opponent pressure from yesterday.
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    # If Cindy exists, use her yesterday bid as a proxy for the current equilibrium.
    cindy_bid = prev_by_id.get('Cindy', None)

    # Urgency: if we are close to starving, bid more.
    # no_water_days is consecutive days without water; if high, increase bid.
    urgency = 0.0
    if no_water_days >= 2:
        urgency = 1.0
    elif no_water_days == 1:
        urgency = 0.6
    else:
        urgency = 0.2

    # Base target: slightly under the highest yesterday bid to win without overpaying.
    # If Cindy bid is known and high, shadow just below it.
    target = 0.0
    if cindy_bid is not None and cindy_bid > 0:
        # Shadow Cindy: bid a bit less than her typical winning bid.
        # When supply is high, we can afford to bid lower; when low, bid closer.
        cushion = 6.0 * (1.0 - supply_level)  # smaller cushion when supply is low
        target = max(0.0, cindy_bid - cushion)
    elif highest_prev_bid > 0:
        cushion = 5.0 * (1.0 - supply_level)
        target = max(0.0, highest_prev_bid - cushion)
    else:
        # No signal: default to moderate bid.
        target = DAILY_SALARY * (0.45 + 0.15 * supply_level)

    # Adjust for our hp: if low, we must bid up.
    if hp <= 2:
        target = max(target, DAILY_SALARY * 0.85)
    elif hp <= 4:
        target = max(target, DAILY_SALARY * 0.65)
    else:
        # If healthy, reduce bid somewhat.
        target = target * (0.9 - 0.15 * (1.0 - supply_level))

    # Urgency boost
    target = target * (1.0 + 0.25 * urgency)

    # Clamp to what we can pay.
    # Also avoid bidding above daily salary too often; budget may be low.
    max_reasonable = min(budget, DAILY_SALARY * (0.95 if urgency >= 0.6 else 0.75))
    bid = float(min(max_reasonable, max(0.0, target)))

    # If we have very low budget, bid all we can.
    if budget <= 1.0:
        bid = float(budget)

    # Ensure integer-ish stability (bids are typically numeric; keep as float).
    return bid
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

    # If we cannot afford to cover one water requirement for the day, bid what we can.
    if my_status['budget'] <= 0:
        return 0.0

    # Alive opponents and their yesterday bid
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Estimate how aggressive the field was yesterday
    field_pressure = 0.0
    if yesterday_bids:
        field_pressure = max(yesterday_bids)

    # Supply-based aggressiveness: higher supply reduces need to overbid.
    # Compute how many water units are likely available; use int() to avoid float indexing issues.
    # We only use this as a scalar, not for indexing.
    expected_units = max(1, int(supply / WATER_REQ))

    # Base bid target: aim to beat typical high bids when supply is tight.
    # Observed: survivors bid around 90-100; dead ones had very low/failed.
    # We choose a cap to protect budget.
    budget = float(my_status['budget'])
    hp = float(my_status['hp'])
    no_water_days = int(my_status['no_water_days'])

    # Determine urgency
    urgent = (hp <= 2.5) or (no_water_days >= 2)
    late_game = (day >= 7)

    # If field pressure indicates strong spending, bid near it but slightly under to avoid overspending.
    # If field pressure is low, bid enough to secure water.
    if field_pressure > 0:
        # When supply is low (15-16), we need to be more competitive.
        supply_tight = supply <= (MIN_SUPPLY + 0.5)
        competitiveness = 1.03 if supply_tight else 0.98
        target = field_pressure * competitiveness
    else:
        target = DAILY_SALARY * 0.6

    # Adjust for urgency and late game
    if urgent:
        target *= 1.15
    if late_game:
        target *= 1.08

    # Convert target into a safe bid range
    # Cap: never exceed 70% of remaining budget; also avoid exceeding a day-salary scale too much.
    cap_budget = 0.7 * budget
    cap_salary = DAILY_SALARY * 0.95
    cap = min(cap_budget, cap_salary)

    # Floor: if urgent, bid higher floor; otherwise moderate.
    if urgent:
        floor = DAILY_SALARY * 0.55
    else:
        floor = DAILY_SALARY * 0.45

    bid = max(floor, target)
    bid = min(bid, cap)

    # If supply is very high (near 25), we can lower bid.
    if supply >= (MAX_SUPPLY - 1.0):
        bid *= 0.9

    # Ensure non-negative and not above budget
    bid = max(0.0, min(float(bid), budget))
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

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive = []
    for oid, o in opponents_status.items():
        try:
            if bool(o.get('alive', False)):
                alive.append((oid, o))
        except Exception:
            continue

    if not alive:
        # No opponents alive: bid conservatively.
        return max(0.0, min(my_budget, DAILY_SALARY * 0.35))

    # Read yesterday bids to infer aggression.
    prev_bids = []
    for oid, o in alive:
        prev = o.get('previous_trace', None)
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    prev_bids.append(float(b))
                except Exception:
                    pass
        elif isinstance(prev, list) and len(prev) > 0:
            # If previous_trace is a list, use the last element.
            last = prev[-1]
            if isinstance(last, dict) and last.get('bid', None) is not None:
                try:
                    prev_bids.append(float(last.get('bid')))
                except Exception:
                    pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate how many water units are likely needed.
    # Supply is total available water; we only need 1 unit of WATER_REQ.
    # If supply is low, we should bid closer to the aggressive opponents.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Base bid target: follow aggressive surviving opponents but leave room.
    # If they were bidding very high yesterday, match a fraction.
    aggressive_threshold = DAILY_SALARY * 0.75

    if highest_prev_bid >= aggressive_threshold:
        # They likely fight for the water. If my HP is low, bid more.
        if my_hp <= 2 or my_no_water_days >= 2:
            target = highest_prev_bid * 0.98
        elif my_hp <= 4 or my_no_water_days >= 1:
            target = highest_prev_bid * 0.90
        else:
            target = highest_prev_bid * 0.80
    else:
        # They were not extremely aggressive; bid enough to secure water when needed.
        if my_hp <= 2 or my_no_water_days >= 2:
            target = max(highest_prev_bid * 0.9, DAILY_SALARY * 0.85)
        elif my_hp <= 4 or my_no_water_days >= 1:
            target = max(highest_prev_bid * 0.75, DAILY_SALARY * 0.65)
        else:
            # Higher supply -> can bid slightly less.
            target = max(highest_prev_bid * 0.65, DAILY_SALARY * (0.55 + 0.15 * supply_ratio))

    # Clamp to feasible budget.
    target = max(0.0, min(my_budget, target))

    # If budget is too small, bid whatever we can.
    if my_budget <= 0.0:
        return 0.0

    # Add a small strategic nudge to beat ties when supply is moderate.
    # Keep it small to avoid overpaying.
    tie_nudge = 1.5 if supply_ratio >= 0.4 else 1.0
    bid = min(my_budget, target + tie_nudge)

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

    # Identify alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive'):
            alive_opps.append(o)

    # Fallback if no opponents
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday immediate bids from previous_trace
    prev_bids = []
    prev_info = []
    for o in alive_opps:
        pt = o.get('previous_trace', {}) or {}
        b = pt.get('bid', None)
        if b is not None:
            prev_bids.append(float(b))
            prev_info.append((o.get('agent_id', None), float(b), float(o.get('hp', 0))))

    # Determine opponent pressure: use top-two yesterday bids
    prev_bids_sorted = sorted(prev_bids, reverse=True)
    top1 = prev_bids_sorted[0] if len(prev_bids_sorted) >= 1 else 0.0
    top2 = prev_bids_sorted[1] if len(prev_bids_sorted) >= 2 else 0.0

    # Supply-based aggressiveness: when supply is scarce, winning costs more
    supply = float(day_context.get('supply', (MIN_SUPPLY + MAX_SUPPLY) / 2.0))
    # Map supply to a 0..1 scarcity factor (1 means scarce)
    scarcity = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    scarcity = max(0.0, min(1.0, scarcity))

    my_hp = float(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0))

    # If we're in danger, bid close to salary to secure water
    if my_hp <= 2.0:
        bid = DAILY_SALARY * (0.85 + 0.1 * scarcity)
        return float(min(my_budget, bid))

    # Otherwise, try to outbid the weaker of the two leaders (top2) by a small margin,
    # but don't exceed a budget cap.
    # Leaders yesterday were around 108-114; Eric was ~72.8.
    # We aim around (min(top1, top2) + margin) with margin increasing when scarce.
    base_target = top2 if top2 > 0.0 else top1
    margin = 4.0 + 6.0 * scarcity

    # If top1 is extremely high, avoid chasing blindly; bid near top2+margin.
    if top1 > DAILY_SALARY * 1.2:
        bid = base_target + margin
    else:
        bid = max(DAILY_SALARY * 0.6, base_target + margin)

    # Ensure we don't overspend: keep bid within a fraction of budget and salary.
    # If we already have plenty of budget, allow higher; else be conservative.
    budget_fraction = 0.35 if my_budget > DAILY_SALARY else 0.55
    bid_cap = min(my_budget, DAILY_SALARY * (0.75 + 0.1 * scarcity), my_budget * budget_fraction + 0.2 * DAILY_SALARY)

    # Final bid
    bid = min(bid, bid_cap)

    # Never bid negative
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

    supply = day_context['supply']
    day = day_context['day']

    # Alive opponents and yesterday bids
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # If no opponents, conserve
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    prev_bids = []
    prev_hp_after = []
    for o in alive_opps:
        pt = o.get('previous_trace', {}) or {}
        b = pt.get('bid', None)
        if b is not None:
            prev_bids.append(float(b))
            prev_hp_after.append(pt.get('hp_after', None))

    # Estimate Cindy pressure: use high quantile of yesterday bids
    # (No long history; only yesterday trace.)
    if prev_bids:
        prev_bids_sorted = sorted(prev_bids)
        n = len(prev_bids_sorted)
        # high pressure threshold
        idx = int(max(0, min(n - 1, int(0.75 * (n - 1)))))
        high_bid = prev_bids_sorted[idx]
        peak_bid = prev_bids_sorted[-1]
    else:
        high_bid = DAILY_SALARY * 0.9
        peak_bid = DAILY_SALARY * 0.9

    my_hp = float(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0))

    # Supply scaling: with higher supply, we can bid less and still secure enough water.
    # With lower supply, we must bid closer to the top.
    # Normalize supply in [MIN_SUPPLY, MAX_SUPPLY]
    if MAX_SUPPLY == MIN_SUPPLY:
        supply_factor = 0.5
    else:
        supply_factor = (float(supply) - float(MIN_SUPPLY)) / float(MAX_SUPPLY - MIN_SUPPLY)
        if supply_factor < 0.0:
            supply_factor = 0.0
        if supply_factor > 1.0:
            supply_factor = 1.0

    # Decide target bid: try to undercut peak/high pressure by a small margin
    # while ensuring we don't go too low when supply is tight.
    # Undercut margin grows when supply is high.
    undercut = 2.0 + 6.0 * supply_factor  # 2..8

    # If my hp is low, I must bid more aggressively.
    if my_hp <= 2:
        aggressiveness = 1.15
    elif my_hp <= 4:
        aggressiveness = 1.0
    else:
        aggressiveness = 0.88

    # Baseline: aim near high_bid but slightly below peak to beat Cindy-like behavior.
    target = (high_bid * aggressiveness) - undercut

    # If target is too low relative to pressure, lift it.
    # Use peak as an upper reference but keep under budget.
    min_floor = DAILY_SALARY * (0.35 + 0.25 * (1.0 - supply_factor))  # higher when supply tight
    if target < min_floor:
        target = min_floor

    # Safety: never exceed a reasonable portion of budget to last.
    # If budget is small, be proportional.
    budget_cap = my_budget * 0.55
    # If budget is very low, spend to survive this day.
    if my_budget <= DAILY_SALARY * 0.25:
        budget_cap = my_budget * 0.85

    bid = float(min(my_budget, budget_cap, target))

    # Ensure non-negative
    if bid < 0.0:
        bid = 0.0

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

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        cap = my_status.get('budget', 0.0)
        return min(cap, DAILY_SALARY * 0.4)

    # Reaction to yesterday bids
    prev_bids = []
    prev_hp_after = []
    for opp_id, opp in alive_opps:
        prev = opp.get('previous_trace', None)
        if isinstance(prev, dict) and prev.get('bid') is not None:
            prev_bids.append(float(prev['bid']))
            prev_hp_after.append(float(prev.get('hp_after', opp.get('hp', 0.0))))
        elif isinstance(prev, list) and len(prev) > 0:
            # If previous_trace is list, use last element only (still within rule: no long history)
            last = prev[-1]
            if isinstance(last, dict) and last.get('bid') is not None:
                prev_bids.append(float(last['bid']))
                prev_hp_after.append(float(last.get('hp_after', opp.get('hp', 0.0))))

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate how many water units are typically needed to cover a day
    # Supply is total water capacity; water units are implicit. We'll use supply ratio to scale aggression.
    supply_frac = 0.0
    if MAX_SUPPLY > 0:
        supply_frac = (float(supply) - float(MIN_SUPPLY)) / float(MAX_SUPPLY - MIN_SUPPLY)
    if supply_frac < 0.0:
        supply_frac = 0.0
    if supply_frac > 1.0:
        supply_frac = 1.0

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = float(my_status.get('no_water_days', 0.0))

    # Identify if any opponent likely is a budget/pressure risk based on yesterday
    # (Cindy died yesterday with budget 0 and moderate bids; if someone has low budget now, we can target.)
    low_budget_opps = []
    for opp_id, opp in alive_opps:
        if float(opp.get('budget', 0.0)) <= 0.0:
            low_budget_opps.append(opp_id)

    # Base bid aggressiveness
    # If supply is high, we can afford to bid more to secure water.
    # If my hp is low, bid less to preserve budget.
    if my_hp <= 2.0 or my_no_water_days <= 1.0:
        base = DAILY_SALARY * (0.35 + 0.2 * supply_frac)
    elif my_hp <= 4.0:
        base = DAILY_SALARY * (0.45 + 0.25 * supply_frac)
    else:
        base = DAILY_SALARY * (0.55 + 0.3 * supply_frac)

    # Use yesterday highest bid as a competitive anchor.
    # If others were bidding very high, we must match closer; otherwise we can undercut slightly.
    if highest_prev_bid >= DAILY_SALARY * 1.4:
        target = max(base, highest_prev_bid * 0.85)
    elif highest_prev_bid >= DAILY_SALARY * 0.9:
        target = max(base, highest_prev_bid * 0.70)
    else:
        # Slightly above base to avoid being outbid by aggressive survivors
        target = base * 1.05

    # If there are low-budget opponents, we can reduce bid because they may not sustain high bids.
    if low_budget_opps:
        target *= 0.9

    # Ensure we don't exceed budget
    if my_budget <= 0.0:
        return 0.0

    # Small safety margin: don't spend all budget unless pressure is extreme
    spend_limit = my_budget
    if my_budget > 0.0:
        # Keep at least a small reserve
        reserve = min(my_budget * 0.1, DAILY_SALARY * 0.2)
        spend_limit = max(0.0, my_budget - reserve)

    bid = min(spend_limit, target)

    # If bid is too low while supply is high and my hp is high, increase slightly
    if bid < DAILY_SALARY * 0.25 and supply_frac > 0.6 and my_hp > 5.0:
        bid = min(spend_limit, DAILY_SALARY * 0.45)

    # Final clamp
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context['supply'])
    day = day_context['day']

    # Alive opponents
    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append(o)

    # If no opponents alive, spend enough to finish requirement safely
    if not alive_opponents:
        return float(min(my_status['budget'], DAILY_SALARY * 0.45))

    # Read yesterday bids only (immediate reaction)
    yesterday_bids = []
    yesterday_hp_after = []
    for o in alive_opponents:
        prev = o.get('previous_trace', {})
        if prev:
            b = prev.get('bid', None)
            if b is not None:
                yesterday_bids.append(float(b))
            hp_after = prev.get('hp_after', None)
            if hp_after is not None:
                yesterday_hp_after.append(float(hp_after))

    # Estimate opponent pressure from yesterday
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / float(len(yesterday_bids))
    else:
        highest_prev_bid = 0.0
        avg_prev_bid = 0.0

    # Tight supply increases competition; wide supply reduces it
    # Use discrete tiers to avoid overfitting
    tightness = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)  # 0..1
    # When supply is near minimum, bid more aggressively
    supply_factor = 0.85 + (1.0 - tightness) * 0.35  # ~0.85..1.2

    # If we are in danger, prioritize survival
    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])

    # Pressure thresholds based on observed meta-round bids
    # Cindy/David/Eric were bidding extremely high while surviving; Alex died.
    # If highest prior bid is very high, opponents are likely competing hard today.
    very_high_pressure = highest_prev_bid >= (DAILY_SALARY * 1.5)
    high_pressure = highest_prev_bid >= (DAILY_SALARY * 1.0)

    # Base bid target
    if my_hp <= 2.0:
        target = DAILY_SALARY * 0.9
    elif very_high_pressure:
        # Compete but not max-out; aim to beat most without exhausting budget
        target = DAILY_SALARY * 0.65
    elif high_pressure:
        target = DAILY_SALARY * 0.55
    else:
        target = DAILY_SALARY * 0.45

    # Adjust by supply tightness
    target *= supply_factor

    # If we have low budget, cap by budget
    bid = min(my_budget, target)

    # If budget is extremely low, still bid something to avoid starvation
    if bid < 1.0 and my_budget > 0.0:
        bid = min(my_budget, 5.0)

    return float(bid)
"""
