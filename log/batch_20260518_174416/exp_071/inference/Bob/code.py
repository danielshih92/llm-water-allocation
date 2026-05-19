# ============================================================
# Experiment: exp_071
# Agent: Bob
# Source: exp_071
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
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        # If alone, bid to secure water but stay budget-aware
        target = min(my_status['budget'], DAILY_SALARY * 0.45)
        return float(max(0.0, target))

    # Read yesterday bids from previous_trace
    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Determine pressure level
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
    else:
        highest_prev_bid = 0.0

    # Budget and HP urgency
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Estimate how many full requirements supply can cover
    # Ensure indices are safe by avoiding list indexing; only compute scalars.
    # (We still compute a rough share target.)
    max_full_units = supply / float(WATER_REQ)

    # If we are close to dying or have been without water, raise bids.
    urgent = (hp <= 2.0) or (no_water_days >= 2)

    # If opponents were bidding very high yesterday, they likely expect scarcity today.
    # Match/contest.
    high_bid_threshold = DAILY_SALARY * 0.85

    if highest_prev_bid >= high_bid_threshold or urgent:
        # Contest strongly but cap by our budget
        if urgent:
            bid = DAILY_SALARY * 0.85
        else:
            # Slightly above their max to win tie-breaks if applicable
            bid = highest_prev_bid + 2.0
        bid = min(budget, bid)
        bid = max(0.0, bid)
        return float(bid)

    # Otherwise, shade down: bid enough to be competitive but preserve budget.
    # Use supply to decide: higher supply -> lower bid.
    # Normalize supply between MIN_SUPPLY and MAX_SUPPLY.
    denom = float(MAX_SUPPLY - MIN_SUPPLY) if float(MAX_SUPPLY - MIN_SUPPLY) != 0.0 else 1.0
    norm = (supply - float(MIN_SUPPLY)) / denom
    if norm < 0.0:
        norm = 0.0
    if norm > 1.0:
        norm = 1.0

    # Base bid: between 0.35 and 0.6 of salary depending on scarcity.
    # Scarcer (low norm) => higher bid.
    scarcity_factor = 1.0 - norm
    base = DAILY_SALARY * (0.35 + 0.25 * scarcity_factor)

    # If our HP is moderate, bid a bit more.
    if hp <= 3.0:
        base *= 1.15

    # Also ensure we don't bid above what seems needed to secure one requirement.
    # Since bids are not directly water units, we just keep it budget-safe.
    bid = min(budget, base)

    # If yesterday bids existed but were not high, lightly react.
    if highest_prev_bid > 0.0:
        # Stay above a fraction of their bid to gain share.
        bid = max(bid, min(budget, highest_prev_bid * 0.65))

    bid = max(0.0, bid)
    return float(bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    hp = my_status.get('hp', 0)
    budget = my_status.get('budget', 0.0)
    no_water_days = my_status.get('no_water_days', 0)

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return float(min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace only (immediate reaction)
    prev_bids = []
    prev_hp_after = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            prev_bids.append(float(b))
            if prev.get('hp_after', None) is not None:
                prev_hp_after.append(float(prev.get('hp_after')))

    # Fallback if traces missing
    if not prev_bids:
        base = DAILY_SALARY * (0.75 if hp <= 2 else 0.55)
        return float(min(budget, base))

    highest_prev_bid = max(prev_bids)
    lowest_prev_bid = min(prev_bids)

    # Estimate how contested this day likely is using supply vs requirement.
    # If supply is tight, we need to outbid more.
    # supply is float, but we only use it for comparisons.
    supply_ratio = float(supply) / float(WATER_REQ) if WATER_REQ else 0.0

    # Determine aggression level
    # - If our HP is low or we have consecutive no-water days, bid higher.
    # - Otherwise, bid just enough to beat the lower cluster.
    if hp <= 2 or no_water_days >= 2:
        # Must secure water: target near the top of yesterday's effective bids
        target = max(highest_prev_bid * 0.92, DAILY_SALARY * 0.85)
    elif hp <= 3:
        # Moderate emergency: slightly under top bids
        target = max(highest_prev_bid * 0.80, DAILY_SALARY * 0.70)
    else:
        # Healthy: try to undercut while still competing
        # If supply is tight, move toward higher bids.
        tightness = 0.0
        if supply_ratio < 2.0:
            tightness = 1.0
        elif supply_ratio < 2.5:
            tightness = 0.6
        else:
            tightness = 0.3

        # Aim between lowest and highest, closer to lowest when not tight.
        # Use highest_prev_bid - lowest_prev_bid spread to adapt.
        spread = highest_prev_bid - lowest_prev_bid
        target = lowest_prev_bid + spread * (0.35 + 0.35 * tightness)

        # Also ensure we are not too low versus daily salary scale
        target = max(target, DAILY_SALARY * (0.50 + 0.15 * tightness))

    # Small strategic bump: if we are close to highest_prev_bid, add a tiny increment
    # to reduce tie risk (bids hidden; exact tie handling unknown).
    if target >= highest_prev_bid * 0.88:
        target = target + 1.0

    # Final clamp to budget and reasonable bounds
    # Never exceed budget; also avoid extreme overbids.
    max_reasonable = DAILY_SALARY * 1.75
    bid = float(min(budget, min(target, max_reasonable)))

    # Ensure non-negative
    if bid < 0.0:
        bid = 0.0

    return bid
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

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive.append((opp_id, opp))

    if not alive:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace only (immediate reaction)
    prev_bids = []
    for _, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Determine how aggressive others were yesterday
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # If others were paying near/above salary, we should match to ensure survival
    # Cindy/Alex patterns suggest high bids keep them alive.
    target = None

    # Urgency based on our HP and no-water streak
    if my_hp <= 2 or my_no_water_days >= 2:
        urgency = 1.0
    elif my_hp <= 4 or my_no_water_days >= 1:
        urgency = 0.75
    else:
        urgency = 0.45

    # Supply pressure: higher supply reduces need to overbid
    # approximate required number of winners: supply / WATER_REQ
    # (use int indices safety not needed here)
    supply_factor = 1.0
    if supply >= 21:
        supply_factor = 0.85
    elif supply <= 17:
        supply_factor = 1.05

    # Base bid level
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Match just below the top to win while saving budget
        target = (highest_prev_bid * 0.98) * urgency * supply_factor
    elif highest_prev_bid >= DAILY_SALARY * 0.55:
        target = (highest_prev_bid * 0.90 + 2.0) * urgency * supply_factor
    else:
        # If others were low, we can bid a moderate amount to secure water
        target = (DAILY_SALARY * 0.55 + 5.0) * urgency * supply_factor

    # Clamp to reasonable bounds and budget
    # Never exceed budget; also avoid extreme bids if we can.
    min_bid_floor = 0.0
    max_reasonable = DAILY_SALARY * 1.0
    bid = max(min_bid_floor, min(float(my_budget), float(target), max_reasonable))

    # If we're extremely low HP, ensure we bid high enough
    if my_hp <= 1:
        bid = max(bid, min(float(my_budget), DAILY_SALARY * 0.95))

    # Final safety: must be non-negative
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((opp_id, o))

    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace only
    yesterday_bids = []
    alive_prev = []
    for opp_id, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                b_val = float(b)
            except Exception:
                continue
            yesterday_bids.append(b_val)
            alive_prev.append((opp_id, b_val))

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = 0.0
    if len(yesterday_bids) >= 2:
        sorted_b = sorted(yesterday_bids, reverse=True)
        second_prev_bid = sorted_b[1]

    # Estimate how many water units might be needed from supply context
    # (We don't know exact allocation rule; still use supply to scale bid aggressiveness.)
    # More supply => less aggressive.
    supply_factor = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_factor = max(0.0, min(1.0, supply_factor))

    # Base bid: aim to be competitive but not wasteful.
    base = DAILY_SALARY * (0.45 - 0.15 * supply_factor)

    # If I'm in danger of running out of water, bid more.
    danger = 0
    if my_hp <= 2.0:
        danger = 2
    elif my_hp <= 4.0 or my_no_water_days >= 2:
        danger = 1

    # If opponents were bidding high yesterday, increase to avoid being priced out.
    # Cindy/Eric were around ~116 avg in the meta-round context.
    high_pressure = 1 if highest_prev_bid >= DAILY_SALARY * 0.85 else 0

    if high_pressure:
        if danger == 2:
            bid = max(base, highest_prev_bid * 0.95)
        elif danger == 1:
            bid = max(base, highest_prev_bid * 0.75)
        else:
            # Slightly under the highest to save budget; still enough to compete.
            bid = max(base, second_prev_bid * 0.9 if second_prev_bid > 0 else highest_prev_bid * 0.6)
    else:
        # If nobody bid extremely high, stay conservative.
        if danger == 2:
            bid = max(base, DAILY_SALARY * 0.75)
        elif danger == 1:
            bid = max(base, DAILY_SALARY * 0.6)
        else:
            bid = base

    # Budget safety and non-negative
    bid = float(bid)
    if my_budget <= 0:
        return 0.0

    # Cap bid to avoid overspending early; but allow higher if very low hp.
    cap = my_budget
    if danger == 0:
        cap = min(cap, DAILY_SALARY * 0.7)
    elif danger == 1:
        cap = min(cap, DAILY_SALARY * 0.9)
    else:
        cap = min(cap, DAILY_SALARY * 1.05)

    bid = max(0.0, min(bid, cap, my_budget))
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
    day = day_context.get('day', 0)

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Extract yesterday bids from immediate previous_trace only
    prev_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # Estimate how aggressive the field was yesterday
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_highest_prev_bid = 0.0
    if len(prev_bids) >= 2:
        sorted_bids = sorted(prev_bids, reverse=True)
        second_highest_prev_bid = float(sorted_bids[1])

    # If my hp is critical, spend to avoid death
    if my_hp <= 2:
        target = DAILY_SALARY * 0.92
    elif my_hp <= 4:
        target = DAILY_SALARY * 0.65
    else:
        # Otherwise, bid just enough to beat typical aggressive bids.
        # If yesterday's highest bid was extremely high, don't match it; bid around the middle.
        if highest_prev_bid >= DAILY_SALARY * 1.2:
            target = max(DAILY_SALARY * 0.5, second_highest_prev_bid + 2.0)
        else:
            # Moderate bids: bid slightly above the highest to secure water when needed.
            target = max(DAILY_SALARY * 0.48, highest_prev_bid * 0.75 + 5.0)

    # Budget and supply-aware cap
    # Higher supply reduces need to overbid.
    supply_factor = 1.0
    if supply >= 22.0:
        supply_factor = 0.75
    elif supply >= 18.0:
        supply_factor = 0.9
    else:
        supply_factor = 1.05

    bid = target * supply_factor

    # Hard cap to avoid bankrupting; keep some buffer for later days
    # (budget is in same scale as bids)
    max_affordable = my_budget
    if my_budget > 0:
        # Keep at least 10% of budget if possible
        max_affordable = max(0.0, my_budget * 0.9)

    bid = min(bid, max_affordable)

    # Ensure non-negative
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    # If alone, bid low but enough to survive.
    if not alive_opponents:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from each opponent's previous_trace.
    yesterday_bids = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Estimate a competitive bid target from yesterday.
    if yesterday_bids:
        # Use upper quantile to react to aggressive bidders without overpaying.
        sorted_bids = sorted(yesterday_bids)
        idx = int(len(sorted_bids) * 0.75)
        if idx < 0:
            idx = 0
        if idx >= len(sorted_bids):
            idx = len(sorted_bids) - 1
        q75 = float(sorted_bids[idx])

        # Clearing-level proxy: slightly above q75 but not too high.
        # If q75 is already extremely high, cap to avoid mirroring Alex-like overbidding.
        target = q75 * 0.98 + 1.0
        if q75 >= DAILY_SALARY * 0.95:
            target = min(target, DAILY_SALARY * 0.75)
    else:
        target = DAILY_SALARY * 0.55

    # Supply adjustment: in higher supply, we can bid lower.
    # Map supply in [MIN_SUPPLY, MAX_SUPPLY] to multiplier in [1.05, 0.9]
    if MAX_SUPPLY > MIN_SUPPLY:
        t = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        t = 0.5
    if t < 0.0:
        t = 0.0
    if t > 1.0:
        t = 1.0
    supply_mult = 1.05 - 0.15 * t

    # Urgency based on hp/no_water_days.
    urgency_mult = 1.0
    if hp <= 2:
        urgency_mult = 1.25
    elif hp <= 4:
        urgency_mult = 1.12

    if no_water_days >= 2:
        urgency_mult *= 1.10

    # Final bid computation.
    bid = target * supply_mult * urgency_mult

    # Bound by budget and keep within reasonable fraction of salary.
    # If my budget is low, go all-in only when hp is critical.
    if budget <= 0.0:
        return 0.0

    max_reasonable = DAILY_SALARY * 0.75
    if hp <= 2:
        max_reasonable = DAILY_SALARY * 0.95

    bid = min(bid, max_reasonable)
    bid = min(bid, budget)

    # Ensure non-negative
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        cap = min(budget, DAILY_SALARY * 0.4)
        return max(0.0, cap)

    # Read yesterday bids from previous_trace only
    yesterday_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how tight the market is; higher supply means we can bid less.
    # Ensure indices are int() even if we use them.
    # bins: [15..25] -> 0..2
    supply_bin = int((supply - MIN_SUPPLY) / ((MAX_SUPPLY - MIN_SUPPLY) / 3.0 + 1e-9))
    if supply_bin < 0:
        supply_bin = 0
    if supply_bin > 2:
        supply_bin = 2

    # Base bid: moderate aggressiveness.
    # When supply is low (bin 0), bid higher; when supply is high (bin 2), bid lower.
    base_bid_by_bin = [55.0, 45.0, 35.0]
    base_bid = base_bid_by_bin[supply_bin]

    # If someone previously bid very high, we slightly increase to avoid being outbid.
    # Yesterday: Cindy/Eric survived with high spending; Alex died, David bid 0.
    # Use threshold relative to DAILY_SALARY.
    pressure = 0.0
    if highest_prev_bid >= DAILY_SALARY * 1.2:
        pressure = 18.0
    elif highest_prev_bid >= DAILY_SALARY * 0.85:
        pressure = 10.0
    elif highest_prev_bid <= 5.0:
        pressure = -5.0

    # If my hp is critical, bid more to secure water.
    hp_boost = 0.0
    if hp <= 1.5:
        hp_boost = 35.0
    elif hp <= 3.0:
        hp_boost = 20.0
    elif hp <= 5.0:
        hp_boost = 10.0

    # Also, if day is late, increase slightly to avoid endgame starvation.
    late_boost = 0.0
    if day >= 7:
        late_boost = 8.0

    target = base_bid + pressure + hp_boost + late_boost

    # Budget cap: never bid more than we can afford.
    # Also keep within a reasonable band to avoid overpaying.
    max_reasonable = min(budget, DAILY_SALARY * 1.6)
    min_reasonable = 0.0

    if target > max_reasonable:
        target = max_reasonable
    if target < min_reasonable:
        target = min_reasonable

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

    # Alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # If no opponents, bid to survive comfortably
    if not alive_opps:
        return float(min(my_status.get('budget', 0.0), DAILY_SALARY * 0.4))

    # Use only yesterday previous_trace for immediate reaction
    prev_bids = []
    prev_hp_after = []
    for o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            prev_bids.append(float(b))
        hp_after = prev.get('hp_after', None)
        if hp_after is not None:
            prev_hp_after.append(float(hp_after))

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))

    # Estimate how competitive the market was yesterday
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_highest = 0.0
    if len(prev_bids) >= 2:
        sorted_b = sorted(prev_bids, reverse=True)
        second_highest = sorted_b[1]

    # If someone bid near very high levels yesterday, we expect bidding pressure today.
    # Cindy's behavior suggests aggressive spending; we counter with a moderate-to-high bid.
    pressure = 0.0
    if highest_prev_bid >= 0.85 * 300.0:  # near max bid scale
        pressure = 1.0
    elif highest_prev_bid >= 0.65 * 300.0:
        pressure = 0.7
    elif highest_prev_bid >= 0.45 * 300.0:
        pressure = 0.45
    else:
        pressure = 0.25

    # Also consider our own HP: if low, increase bid to avoid starvation.
    hp_factor = 0.0
    if my_hp <= 1.5:
        hp_factor = 0.9
    elif my_hp <= 3.0:
        hp_factor = 0.6
    elif my_hp <= 5.0:
        hp_factor = 0.35
    else:
        hp_factor = 0.2

    # Supply-based aggressiveness: with tighter supply (closer to MIN_SUPPLY), bid more.
    supply_tight = 0.0
    if supply <= float(MIN_SUPPLY):
        supply_tight = 0.9
    elif supply <= (MIN_SUPPLY + MAX_SUPPLY) / 2.0:
        supply_tight = 0.6
    else:
        supply_tight = 0.35

    # Core bid target (in budget units). Keep it below full budget to preserve longevity.
    base = DAILY_SALARY * 0.5
    target = base + DAILY_SALARY * (0.6 * pressure + 0.4 * hp_factor + 0.3 * supply_tight)

    # If highest yesterday was very close to max, try to outbid slightly.
    if highest_prev_bid > 0:
        # Use a small increment over second-highest to avoid overpaying.
        target = max(target, second_highest + 2.0)

    # Clamp by what we can afford and by a reasonable cap.
    # Never bid more than 95% of budget to reduce risk of going to 0.
    cap = my_budget * 0.95
    if cap <= 0:
        return 0.0

    # Also avoid extreme bids beyond a fraction of daily salary.
    extreme_cap = DAILY_SALARY * 1.4
    final_bid = float(min(cap, max(0.0, min(target, extreme_cap))))

    return final_bid
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

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opponents = []
    for k, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append(o)

    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Extract yesterday bids from previous_trace for immediate reaction
    prev_bids = []
    for o in alive_opponents:
        pt = o.get('previous_trace', {})
        if pt and pt.get('bid') is not None:
            try:
                prev_bids.append(float(pt['bid']))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_prev_bid = 0.0
    if len(prev_bids) >= 2:
        sorted_b = sorted(prev_bids, reverse=True)
        second_prev_bid = sorted_b[1]

    # Baseline aggressiveness: moderate to avoid budget collapse
    # Supply affects how many water units are likely available; higher supply => can bid lower.
    supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_norm = max(0.0, min(1.0, supply_norm))

    # Urgency based on hp and consecutive no-water days
    urgency = 0.0
    if hp <= 2.0:
        urgency += 0.9
    elif hp <= 4.0:
        urgency += 0.6
    elif hp <= 6.0:
        urgency += 0.35
    else:
        urgency += 0.15

    if no_water_days >= 2:
        urgency += 0.35
    elif no_water_days >= 1:
        urgency += 0.15

    # If opponents previously bid extremely high, try to undercut unless we are in danger.
    # Cindy/David were very high; Alex/Eric died. So we don't match extreme bids unless necessary.
    extreme_threshold = DAILY_SALARY * 0.95  # 85.5

    # Target bid computation
    if highest_prev_bid >= extreme_threshold:
        # If I'm healthy, bid around a fraction of salary; if low hp, bid closer to previous high.
        if hp > 5.0 and urgency < 0.6:
            target = DAILY_SALARY * (0.45 + 0.15 * (1.0 - supply_norm))
        else:
            # Bid slightly above second-highest to steal allocation
            target = max(second_prev_bid + 2.0, DAILY_SALARY * (0.7 + 0.2 * (1.0 - supply_norm)))
    else:
        # Not extreme yesterday: bid enough to be competitive but not wasteful
        target = DAILY_SALARY * (0.5 + 0.25 * (1.0 - supply_norm) + 0.2 * urgency)

    # Clamp to budget and keep within reasonable bounds
    target = max(0.0, target)
    # Never bid more than budget; also avoid bidding above 1.2*salary unless in critical hp
    critical = (hp <= 2.0 or no_water_days >= 3)
    cap = budget if critical else min(budget, DAILY_SALARY * 1.2)
    if cap <= 0.0:
        return 0.0

    bid = min(target, cap)

    # If budget is low, switch to survival-maximizing: bid a larger fraction of remaining budget.
    if budget < DAILY_SALARY * 0.6:
        bid = min(budget, budget * (0.75 + 0.25 * urgency))

    # Ensure bid is at least 1 when we can afford it, to avoid zero-lock.
    if bid < 1.0 and budget >= 1.0:
        bid = 1.0

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

    # Extract yesterday bids from previous_trace for immediate reaction
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Baseline aggressiveness from yesterday pressure
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        avg_prev_bid = sum(prev_bids) / float(len(prev_bids))
    else:
        highest_prev_bid = DAILY_SALARY * 0.6
        avg_prev_bid = DAILY_SALARY * 0.6

    # Supply pressure: with higher supply, we can bid less and still get enough water share
    # Supply units roughly scale with how many WATER_REQ blocks exist.
    blocks = supply / float(WATER_REQ)
    # Normalize to [0,1] over scenario range
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_norm = 0.5
    supply_norm = max(0.0, min(1.0, supply_norm))

    # Remaining urgency: if low hp or already on no-water days, bid more.
    urgency = 0.0
    if my_hp <= 2:
        urgency += 1.0
    elif my_hp <= 4:
        urgency += 0.6
    elif my_hp <= 6:
        urgency += 0.3

    if my_no_water_days >= 2:
        urgency += 0.7
    elif my_no_water_days == 1:
        urgency += 0.35

    # Late-game: slightly more conservative to avoid bankruptcy unless urgent
    # episode_days is fixed at 10 in meta-round state, but day_context only has day.
    # Use day/10 heuristic.
    late_norm = max(0.0, min(1.0, (float(day) / 10.0)))

    # Target bid: anchor around avg_prev_bid but discount when supply is high and urgency is low.
    # Also cap to avoid overspending beyond reasonable fraction of budget.
    base = 0.55 * avg_prev_bid + 0.15 * highest_prev_bid

    # Discount with supply_norm (more supply => cheaper to secure water)
    base *= (0.95 - 0.35 * supply_norm)

    # Add urgency
    base *= (1.0 + 0.55 * urgency)

    # Mild late-game discount if not urgent
    if urgency < 0.6:
        base *= (1.0 - 0.15 * late_norm)

    # Ensure minimum to compete, but not too high
    min_bid = DAILY_SALARY * 0.35
    max_bid = min(my_budget, DAILY_SALARY * 0.95)

    bid = max(min_bid, base)
    if bid > max_bid:
        bid = max_bid

    # If my hp is very low, push closer to max_bid
    if my_hp <= 2 and my_budget > 0:
        bid = max(bid, min(my_budget, DAILY_SALARY * 0.9))

    # If budget is tiny, just spend what we can
    if my_budget < DAILY_SALARY * 0.2:
        bid = my_budget

    return float(bid)
"""
