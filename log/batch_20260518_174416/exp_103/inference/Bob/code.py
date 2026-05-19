# ============================================================
# Experiment: exp_103
# Agent: Bob
# Source: exp_103
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    # Base caps
    max_affordable = max(0.0, budget)
    # We never bid more than what could be useful given supply; also keep some budget for later.
    useful_cap = max(0.0, min(max_affordable, supply))

    # If we are already in danger, bid harder.
    critical = (hp <= 2.0) or (no_water_days >= 2)

    # Read yesterday's bids from previous_trace only.
    prev_bids = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # If no info, choose a moderate bid.
    if not prev_bids:
        target = DAILY_SALARY * (0.75 if critical else 0.55)
        return min(useful_cap, target)

    highest_prev_bid = max(prev_bids)
    avg_prev_bid = sum(prev_bids) / float(len(prev_bids))

    # Aggression inference:
    # - If someone bid very high relative to daily salary, they likely expect to win water.
    # - We respond with a competitive bid but avoid overpaying when our HP is fine.
    pressure = 0.0
    if highest_prev_bid >= DAILY_SALARY * 0.95:
        pressure = 1.0
    elif highest_prev_bid >= DAILY_SALARY * 0.80:
        pressure = 0.8
    elif highest_prev_bid >= DAILY_SALARY * 0.60:
        pressure = 0.6
    elif avg_prev_bid >= DAILY_SALARY * 0.45:
        pressure = 0.4
    else:
        pressure = 0.2

    # Determine bid target.
    # When critical, bid close to pressure level; otherwise bid less.
    if critical:
        # Bid enough to likely beat them.
        target = min(useful_cap, max(highest_prev_bid + 1.0, DAILY_SALARY * (0.85 + 0.1 * pressure)))
    else:
        # If opponents were aggressive, we still bid to avoid losing HP.
        if pressure >= 0.8:
            target = min(useful_cap, max(highest_prev_bid * 0.98, DAILY_SALARY * 0.65))
        elif pressure >= 0.4:
            target = min(useful_cap, max(highest_prev_bid * 0.75, DAILY_SALARY * 0.55))
        else:
            # Opponents were timid; take advantage.
            # Bid toward a higher fraction to secure water, but not beyond supply.
            target = min(useful_cap, max(DAILY_SALARY * 0.62, avg_prev_bid + 5.0))

    # Ensure we bid at least something when we need water.
    # If our HP is low, increase slightly.
    if hp <= 3.0:
        target = min(useful_cap, max(target, DAILY_SALARY * 0.7))

    # Final clamp to [0, useful_cap]
    if target < 0.0:
        target = 0.0
    if target > useful_cap:
        target = useful_cap
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
    day = day_context['day']

    # Identify alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return min(float(my_status['budget']), DAILY_SALARY * 0.4)

    # Read yesterday bids for immediate reaction
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    prev_bids.append(float(b))
                except Exception:
                    pass

    # Estimate a competitive bid based on who was most aggressive yesterday
    # Prefer Cindy if present (often highest pressure), else use overall max.
    cindy = opponents_status.get('Cindy', None)
    cindy_prev = {}
    if cindy is not None:
        cindy_prev = cindy.get('previous_trace', {}) or {}
    cindy_bid = cindy_prev.get('bid', None)

    overall_max_prev_bid = max(prev_bids) if prev_bids else 0.0
    pressure_bid = 0.0
    if cindy_bid is not None:
        try:
            pressure_bid = float(cindy_bid)
        except Exception:
            pressure_bid = 0.0
    if pressure_bid <= 0.0:
        pressure_bid = overall_max_prev_bid

    # Supply-based aggressiveness: higher supply -> can bid less; lower supply -> bid more.
    # Normalize supply in [MIN_SUPPLY, MAX_SUPPLY]
    if MAX_SUPPLY == MIN_SUPPLY:
        supply_factor = 0.5
    else:
        supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
        if supply_factor < 0.0:
            supply_factor = 0.0
        if supply_factor > 1.0:
            supply_factor = 1.0

    # If Cindy was aggressive yesterday, we bid just under her typical pressure to win water
    # without paying her peak.
    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])

    # Base target: around 0.55 salary, adjusted by pressure and supply.
    target = DAILY_SALARY * (0.55 + 0.15 * (1.0 - supply_factor))

    # Pressure adjustment: if someone bid high, increase but cap.
    # Use thresholds relative to salary.
    if pressure_bid >= DAILY_SALARY * 1.6:
        target *= 1.15
    elif pressure_bid >= DAILY_SALARY * 1.2:
        target *= 1.05
    elif pressure_bid <= DAILY_SALARY * 0.7:
        target *= 0.95

    # My HP urgency: if low HP, bid higher.
    if my_hp <= 2.0:
        target *= 1.25
    elif my_hp <= 4.0:
        target *= 1.10

    # React to yesterday max pressure: try to be slightly below it.
    if overall_max_prev_bid > 0.0:
        # Bid below max by a small margin, but not too low.
        target = min(target, overall_max_prev_bid * 0.92 + 2.0)

    # Convert target to a safe bid within budget.
    # Also ensure we don't bid tiny amounts when supply is low.
    min_bid_floor = DAILY_SALARY * (0.35 + 0.25 * (1.0 - supply_factor))
    final_bid = max(min_bid_floor, target)

    # Budget cap
    if my_budget <= 0.0:
        return 0.0
    if final_bid > my_budget:
        final_bid = my_budget

    # Final sanity: never exceed a reasonable fraction of salary
    cap = DAILY_SALARY * 2.0
    if final_bid > cap:
        final_bid = cap

    # Ensure non-negative
    if final_bid < 0.0:
        final_bid = 0.0

    return float(final_bid)
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

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append((oid, o))

    if not alive_opponents:
        cap = my_budget if my_budget > 0 else DAILY_SALARY
        return float(min(cap, DAILY_SALARY * 0.4))

    # Immediate reaction to yesterday bids
    yesterday_bids = []
    yesterday_pressured = []  # (opp_id, bid) for those with high bid
    for oid, o in alive_opponents:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is None:
            continue
        try:
            b = float(b)
        except Exception:
            continue
        yesterday_bids.append(b)
        if b >= DAILY_SALARY * 0.85:
            yesterday_pressured.append((oid, b))

    # Supply pressure: when supply is tight, increase bid to avoid being outbid.
    # supply in [15,25]; map to a multiplier in [1.25, 0.85]
    if MAX_SUPPLY > MIN_SUPPLY:
        tightness = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        tightness = 0.5
    tightness = max(0.0, min(1.0, float(tightness)))
    supply_mult = 1.25 - 0.4 * tightness  # tighter supply => higher mult

    # If we are in danger, bid more aggressively.
    danger = 0
    if my_hp <= 2:
        danger = 2
    elif my_hp <= 4:
        danger = 1
    if my_no_water_days >= 2:
        danger = max(danger, 1)

    # Base bid from yesterday's observed market.
    if yesterday_bids:
        top_bid = max(yesterday_bids)
        avg_bid = sum(yesterday_bids) / float(len(yesterday_bids))

        if yesterday_pressured:
            # High-bid cluster: try to be competitive but not necessarily match the max.
            target = min(top_bid * 0.92, avg_bid * 1.05)
        else:
            # No extreme bids: bid near average.
            target = avg_bid * 0.95

        # Adjust by supply and our danger.
        if danger == 2:
            target *= 1.25
        elif danger == 1:
            target *= 1.10

        target *= supply_mult
    else:
        # No trace bids available: conservative
        target = DAILY_SALARY * (0.55 + 0.15 * tightness)
        if danger == 2:
            target *= 1.25
        elif danger == 1:
            target *= 1.10

    # Convert target to a safe cap based on budget.
    # Ensure some chance to win while not going bankrupt.
    if my_budget <= 0:
        # If no budget, still try to bid small (game may allow negative/zero; keep safe)
        return 0.0

    # Keep reserve: don't spend more than ~70% of current budget unless very dangerous.
    spend_frac = 0.7 if danger == 0 else (0.85 if danger == 1 else 0.95)
    cap = my_budget * spend_frac

    # Also avoid bidding above a reasonable fraction of supply*WATER_REQ scaling.
    # (Heuristic cap)
    heuristic_cap = DAILY_SALARY * (0.9 + 0.2 * tightness)

    bid = float(min(target, cap, heuristic_cap, my_budget))

    # Final guard: bid at least a small amount to avoid always losing.
    min_bid = DAILY_SALARY * 0.35
    if bid < min_bid:
        bid = float(min(my_budget, min_bid))

    return float(bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Alive opponents and their yesterday bid signals
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                alive_opps.append((opp_id, float(prev.get('bid', 0.0)), prev.get('hp_after', None), prev.get('budget_after', None)))

    # If no signal, default conservative
    if not alive_opps:
        base = DAILY_SALARY * 0.5
        return max(0.0, min(float(my_status['budget']), base))

    # Use yesterday's top bids as proxy for today's aggressive pressure
    yesterday_top_bid = max(b[1] for b in alive_opps)
    yesterday_second_bid = sorted([b[1] for b in alive_opps], reverse=True)[1] if len(alive_opps) >= 2 else yesterday_top_bid

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Supply pressure: higher supply reduces need to overbid
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # If my hp is critical, prioritize survival with a strong bid
    if my_hp <= 2 or no_water_days >= 2:
        target = max(yesterday_second_bid + 2.0, DAILY_SALARY * 0.75)
    else:
        # Otherwise, bid just enough to beat yesterday's common aggression
        # Cindy/David were high; aim slightly above the second-highest to avoid paying the absolute max.
        target = yesterday_second_bid + (1.0 + 4.0 * (1.0 - supply_ratio))
        # If yesterday top bid was extremely high, scale down a bit to avoid chasing
        if yesterday_top_bid >= DAILY_SALARY * 1.1:
            target = min(target, yesterday_top_bid - 5.0)
        # Ensure we don't underbid too much compared to typical pressure
        target = max(target, DAILY_SALARY * (0.45 + 0.15 * (1.0 - supply_ratio)))

    # Clamp to budget and keep within a reasonable per-day cap
    cap = min(my_budget, DAILY_SALARY * 1.2)
    bid = max(0.0, min(cap, target))

    # If budget is too low, bid what we can
    if my_budget <= 1.0:
        return my_budget

    return bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context['supply'])
    day = day_context['day']

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])

    # Collect alive opponents and their yesterday bids
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            prev = opp.get('previous_trace', {}) or {}
            alive_opps.append((opp_id, opp, prev))

    if not alive_opps:
        return min(my_budget, DAILY_SALARY * 0.4)

    yesterday_bids = []
    for _, opp, prev in alive_opps:
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Estimate how aggressive the field was yesterday
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = 0.0
    if len(yesterday_bids) >= 2:
        s = sorted(yesterday_bids, reverse=True)
        second_prev_bid = s[1]

    # Supply pressure: with higher supply, we can bid slightly less to secure enough water.
    # With lower supply, bid more to avoid losing.
    supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_norm = max(0.0, min(1.0, supply_norm))

    # Determine desired bid level
    # Aim to beat the leader if they were very aggressive; otherwise hover above the median/second.
    if highest_prev_bid >= DAILY_SALARY * 0.8:
        # Cindy-like behavior: bid to exceed the leader but not max out
        base = highest_prev_bid + 2.0
    else:
        # Eric-like moderate: bid around just above second-highest if available
        base = (second_prev_bid + 2.0) if second_prev_bid > 0.0 else max(DAILY_SALARY * 0.45, highest_prev_bid + 1.0)

    # Adjust for my HP: if low, pay more to avoid death.
    if my_hp <= 2.0:
        base *= 1.25
    elif my_hp <= 3.5:
        base *= 1.10
    else:
        base *= 0.95

    # Adjust for supply: lower supply => bid higher
    base *= (1.15 - 0.25 * supply_norm)

    # Clamp to budget and reasonable fraction of daily salary
    # Keep some budget for later days.
    # If supply is high and my HP is safe, bid conservatively.
    if my_hp > 5.0 and supply_norm > 0.6:
        cap = DAILY_SALARY * 0.6
    elif my_hp > 5.0:
        cap = DAILY_SALARY * 0.75
    else:
        cap = DAILY_SALARY * 0.95

    bid = min(my_budget, cap, base)

    # Ensure non-negative
    if bid < 0.0:
        bid = 0.0

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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    my_hp = int(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return min(my_budget, DAILY_SALARY * 0.4)

    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Estimate how many water units we can buy with a bid.
    # (We don't know conversion, so we use bid heuristics based on traces.)
    # Aggression calibration from yesterday.
    typical = None
    if prev_bids:
        prev_bids_sorted = sorted(prev_bids)
        mid = len(prev_bids_sorted) // 2
        typical = prev_bids_sorted[mid]

    # If supply is tight (closer to MIN_SUPPLY), we should bid more to avoid no-water.
    supply_tightness = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    supply_tightness = max(0.0, min(1.0, supply_tightness))

    # Pressure: if any opponent previously bid very high, raise our bid.
    highest_prev = max(prev_bids) if prev_bids else 0.0
    pressure = 0.0
    if highest_prev > 0:
        pressure = min(1.0, highest_prev / (DAILY_SALARY * 1.3))

    # Determine target bid.
    # Yesterday typical bids were ~105-119; exploit by slightly above typical when safe.
    if typical is None:
        typical = DAILY_SALARY * 0.6

    # Base aggressiveness depends on our hp and no-water days.
    # If we are near death, don't bargain.
    if my_hp <= 2 or my_no_water_days >= 2:
        target = max(DAILY_SALARY * 0.8, typical * (1.05 + 0.15 * supply_tightness + 0.2 * pressure))
    elif my_hp <= 4:
        target = max(DAILY_SALARY * 0.6, typical * (1.02 + 0.12 * supply_tightness + 0.12 * pressure))
    else:
        target = max(DAILY_SALARY * 0.5, typical * (1.00 + 0.08 * supply_tightness + 0.08 * pressure))

    # Ensure we beat the top previous bid only when we can afford it.
    # Use a small premium over highest_prev to exploit their aggression.
    if highest_prev > 0:
        premium = 2.0 + 6.0 * pressure + 4.0 * supply_tightness
        target = min(target, highest_prev + premium)
        # If we are safe, consider matching/just above highest_prev.
        if my_hp >= 5 and supply_tightness >= 0.5:
            target = max(target, highest_prev + 1.0)

    # Budget cap and conservative floor.
    max_affordable = my_budget
    # Don't bid unrealistically high relative to your daily salary unless critical.
    critical = (my_hp <= 2 or my_no_water_days >= 2)
    salary_cap = DAILY_SALARY * (1.2 if critical else 1.0)

    bid = min(max_affordable, target, salary_cap if not critical else max_affordable)

    # If bid becomes too low, raise slightly to avoid repeated no-water.
    min_bid = DAILY_SALARY * (0.35 if my_hp >= 5 else 0.55)
    bid = max(bid, min_bid)

    # Final clamp.
    if bid < 0:
        bid = 0.0
    if bid > my_budget:
        bid = my_budget

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
    day = day_context.get('day', 0)

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from immediate previous_trace
    prev_bids = []
    prev_hp_after = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        if prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid')))
            except Exception:
                pass
        if prev.get('hp_after') is not None:
            try:
                prev_hp_after.append(float(prev.get('hp_after')))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    lowest_prev_hp = min(prev_hp_after) if prev_hp_after else 999.0

    # Estimate how many water units likely exist
    # Use explicit int() for any indexing; here we just compute counts safely.
    est_units = max(1, int(supply / WATER_REQ))

    # Base target: if supply is tight, increase bid to avoid losing.
    # If supply is generous, bid lower.
    supply_tight = supply <= float(WATER_REQ) + 1.0
    supply_medium = (supply > float(WATER_REQ) + 1.0) and (supply <= 18.0)

    # Determine risk state for us
    near_death = (my_hp <= 2) or (my_no_water_days >= 2)
    mid_risk = (my_hp <= 4) or (my_no_water_days == 1)

    # Opponent pressure heuristic: if someone previously bid extremely high, they likely tried to secure water.
    # We'll try to slightly undercut unless we are near death.
    # Clamp reference bid to avoid runaway.
    pressure_level = 0
    if highest_prev_bid >= DAILY_SALARY * 2.0:
        pressure_level = 2
    elif highest_prev_bid >= DAILY_SALARY * 1.2:
        pressure_level = 1

    # Choose bid
    if near_death:
        # Must secure water: bid high but not necessarily max.
        target = DAILY_SALARY * (1.0 + 0.35 * pressure_level)
    elif mid_risk:
        target = DAILY_SALARY * (0.75 + 0.25 * pressure_level)
    else:
        if supply_tight:
            target = DAILY_SALARY * (0.65 + 0.25 * pressure_level)
        elif supply_medium:
            target = DAILY_SALARY * (0.55 + 0.20 * pressure_level)
        else:
            target = DAILY_SALARY * (0.45 + 0.15 * pressure_level)

    # If opponents previously showed very low hp_after, they may be desperate now; raise slightly.
    if lowest_prev_hp <= 0.0:
        target *= 1.08

    # Soft cap: don't bid above what we can afford
    target = max(0.0, min(my_budget, target))

    # If we have very low budget, bid whatever we can to avoid guaranteed loss.
    if my_budget <= DAILY_SALARY * 0.2:
        return max(0.0, my_budget)

    # Add a small strategic offset to beat likely median bids without overpaying.
    # Use supply units to adjust aggressiveness.
    if est_units <= 1:
        target *= 1.03
    elif est_units == 2:
        target *= 1.01

    # Final clamp
    bid = max(0.0, min(my_budget, target))
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
        return float(min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids (immediate reaction only)
    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Baseline target bid: aim to outbid the typical surviving level, but not chase extremes
    if yesterday_bids:
        sorted_bids = sorted(yesterday_bids)
        # Use median-ish to avoid being baited by one extreme
        mid_idx = int(len(sorted_bids) // 2)
        median_bid = float(sorted_bids[mid_idx])
        max_bid = float(sorted_bids[-1])
        # If bids were generally high, increase pressure; if low, stay efficient
        high_pressure = median_bid >= DAILY_SALARY * 1.2
        extreme_pressure = max_bid >= DAILY_SALARY * 2.0
    else:
        median_bid = DAILY_SALARY * 0.7
        max_bid = DAILY_SALARY * 1.5
        high_pressure = False
        extreme_pressure = False

    # Supply pressure: lower supply makes water scarcer; bid higher
    # Normalize between MIN_SUPPLY and MAX_SUPPLY
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_norm = 0.5
    scarcity = 1.0 - float(max(0.0, min(1.0, supply_norm)))

    # Health/bad-streak pressure
    health_pressure = 0.0
    if hp <= 2:
        health_pressure = 1.0
    elif hp <= 4:
        health_pressure = 0.6
    if no_water_days >= 2:
        health_pressure = max(health_pressure, 0.8)

    # Compute a bid cap based on budget and urgency
    # If budget is low, bid a fraction; otherwise bid enough to likely win
    budget_frac = 0.25
    if health_pressure >= 0.8:
        budget_frac = 0.75
    elif health_pressure >= 0.6:
        budget_frac = 0.55
    elif health_pressure >= 0.3:
        budget_frac = 0.4

    # Target: mix median with scarcity/health; avoid paying near max unless forced
    base = median_bid
    if high_pressure:
        base = max(base, DAILY_SALARY * 1.1)
    if extreme_pressure and scarcity >= 0.5:
        base = max(base, DAILY_SALARY * 1.6)

    target = base * (0.85 + 0.4 * scarcity) * (1.0 + 0.35 * health_pressure)

    # Ensure we bid at least enough to not be the low-bid outlier like Alex
    min_reasonable = DAILY_SALARY * (0.35 + 0.25 * scarcity + 0.25 * health_pressure)
    target = max(target, min_reasonable)

    # Final safety: never exceed a budget fraction; also keep within reasonable upper bound
    upper = budget * budget_frac
    if upper < 1.0:
        return float(max(1.0, min(budget, DAILY_SALARY * 0.3)))

    bid = min(target, upper)

    # If supply is very high, bidding too aggressively wastes budget; reduce
    if scarcity <= 0.2:
        bid *= 0.85

    # If day index suggests late game (no direct info, but we can slightly tighten)
    if day >= 7:
        bid *= (1.05 + 0.1 * health_pressure)

    # Clamp to budget
    bid = float(max(1.0, min(bid, budget)))
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

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    if not alive_opponents:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from immediate previous_trace only
    prev_bids = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict) and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate how many water units are plausible per day; use it to scale aggressiveness
    # (supply is float; indices must be int, avoid floor-division to list indices)
    # target_units ~ supply / WATER_REQ
    target_units = supply / float(WATER_REQ) if WATER_REQ else 1.0

    # Base bid: aim to secure water when supply is moderate, but avoid overpaying.
    # If supply is closer to MIN_SUPPLY, competition is tighter.
    supply_ratio = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY) if (MAX_SUPPLY - MIN_SUPPLY) else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # If yesterday had very high pressure (someone bid near salary), we raise our bid.
    pressure = 0.0
    if highest_prev_bid > 0:
        pressure = highest_prev_bid / float(DAILY_SALARY)

    if pressure >= 1.2:
        base = DAILY_SALARY * (0.85 + 0.1 * (1.0 - supply_ratio))
    elif pressure >= 0.9:
        base = DAILY_SALARY * (0.70 + 0.15 * (1.0 - supply_ratio))
    else:
        base = DAILY_SALARY * (0.55 + 0.20 * (1.0 - supply_ratio))

    # If our HP is low or we already went multiple days without water, bid more.
    if hp <= 2:
        base *= 1.25
    elif hp <= 4:
        base *= 1.10

    if no_water_days >= 2:
        base *= 1.15

    # If yesterday's highest bid was moderate, try to slightly undercut/beat by a small margin.
    # We don't know today's hidden bids, so we bias toward winning without maxing.
    if highest_prev_bid > 0:
        # Add a small increment capped to avoid runaway spending
        base = min(base, highest_prev_bid + DAILY_SALARY * 0.15)

    # Convert base into final bid with budget cap.
    # Also ensure we bid at least a small amount when budget allows.
    final_bid = max(0.0, min(budget, base))

    # If budget is very low, bid whatever remains to avoid immediate death.
    if budget <= DAILY_SALARY * 0.25:
        final_bid = min(budget, DAILY_SALARY * 0.9)

    return float(final_bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append(o)

    if not alive:
        return min(budget, DAILY_SALARY * 0.4)

    # Immediate reaction from yesterday trace only
    yesterday_bids = []
    yesterday_hp_after = []
    for o in alive:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass
            try:
                yesterday_hp_after.append(float(prev.get('hp_after')))
            except Exception:
                pass

    if not yesterday_bids:
        # Default: moderate pressure
        base = DAILY_SALARY * 0.55
        if hp <= 2 or no_water_days >= 2:
            base = DAILY_SALARY * 0.9
        return min(budget, base)

    highest_prev_bid = max(yesterday_bids)
    second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid

    # Estimate how costly it is to win: bid slightly above the upper competitive band
    # Cindy's behavior suggests high willingness to pay; Eric suggests sometimes she overpays.
    competitive_band = max(second_prev_bid, highest_prev_bid * 0.75)

    # If opponent(s) were extremely aggressive, we must decide whether to contest hard.
    # Preserve budget unless we are in danger.
    danger = (hp <= 2) or (no_water_days >= 2)
    low_budget = budget <= DAILY_SALARY * 1.0

    if highest_prev_bid >= DAILY_SALARY * 1.6:
        # Very aggressive yesterday: either contest slightly or conserve if in danger.
        if danger or low_budget:
            bid = min(budget, DAILY_SALARY * 0.95)
        else:
            bid = min(budget, max(competitive_band + 5.0, DAILY_SALARY * 0.7))
    else:
        # Moderate yesterday: bid just above the likely winner.
        if danger:
            bid = min(budget, max(competitive_band + 3.0, DAILY_SALARY * 0.85))
        else:
            bid = min(budget, max(competitive_band + 2.0, DAILY_SALARY * 0.55))

    # Supply-based adjustment: if supply is high, winning is cheaper; if low, we need more certainty.
    # supply is between 15 and 25.
    if supply <= 17.0:
        bid *= 1.08
    elif supply >= 22.0:
        bid *= 0.95

    # Final safety clamps
    bid = float(bid)
    if bid < 0:
        bid = 0.0
    if budget <= 0:
        return 0.0

    return min(budget, bid)
"""
