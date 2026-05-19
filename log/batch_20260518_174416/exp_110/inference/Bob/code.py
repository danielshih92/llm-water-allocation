# ============================================================
# Experiment: exp_110
# Agent: Bob
# Source: exp_110
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = day_context.get('supply', 0)
    day = day_context.get('day', 0)

    # Basic safety: if we are in danger, prioritize water.
    if my_status.get('hp', 0) <= 2:
        return min(my_status.get('budget', 0), DAILY_SALARY * 0.95)

    alive_opps = []
    for opp_id, st in opponents_status.items():
        if st.get('alive', False):
            alive_opps.append((opp_id, st))

    if not alive_opps:
        return min(my_status.get('budget', 0), DAILY_SALARY * 0.55)

    # Read yesterday behavior (single-step reaction only)
    prev_bids = []
    prev_pressures = []  # (opp_id, prev_bid, hp_after, budget_after)
    for opp_id, st in alive_opps:
        prev = st.get('previous_trace', {}) or {}
        pb = prev.get('bid', None)
        if pb is not None:
            prev_bids.append(pb)
            prev_pressures.append((opp_id, pb, prev.get('hp_after', None), prev.get('budget_after', None)))

    if not prev_bids:
        # Default: bid moderately to keep pace.
        return min(my_status.get('budget', 0), DAILY_SALARY * 0.55)

    highest_prev_bid = max(prev_bids)
    lowest_prev_bid = min(prev_bids)

    # If someone was willing to spend heavily yesterday, they likely value survival.
    # We shade our bid down unless our hp is also low.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        if my_status.get('hp', 0) > 3:
            bid = DAILY_SALARY * 0.65
        else:
            bid = DAILY_SALARY * 0.9
        return min(my_status.get('budget', 0), bid)

    # If everyone bid low yesterday, we can take advantage by bidding enough to win.
    if lowest_prev_bid <= DAILY_SALARY * 0.35:
        # Scale with how much water we need relative to expected supply.
        # supply is float; convert to int only for indexing-like operations (none here), but keep safe.
        expected_supply = float(supply)
        scarcity_factor = 1.0
        if expected_supply <= float(WATER_REQ):
            scarcity_factor = 1.25
        elif expected_supply <= 0.9 * float(WATER_REQ) + 15:  # medium heuristic
            scarcity_factor = 1.1
        bid = DAILY_SALARY * 0.6 * scarcity_factor
        # Also react to the gap vs highest bid.
        bid = max(bid, min(my_status.get('budget', 0), highest_prev_bid + 2.0))
        return min(my_status.get('budget', 0), bid)

    # Otherwise: mirror slightly above the median to stay competitive without overpaying.
    prev_bids_sorted = sorted(prev_bids)
    mid_index = int(len(prev_bids_sorted) // 2)
    median_prev_bid = prev_bids_sorted[mid_index]

    # If we have no-water days, we should increase urgency.
    no_water_days = my_status.get('no_water_days', 0)
    urgency = 1.0
    if no_water_days >= 2:
        urgency = 1.25
    elif no_water_days == 1:
        urgency = 1.1

    bid = median_prev_bid + 3.0
    bid = bid * urgency

    # Cap bid to avoid bankrupting.
    max_bid = min(my_status.get('budget', 0), DAILY_SALARY * 0.75)
    bid = min(bid, max_bid)

    # Ensure we bid at least a floor if we can.
    min_bid = min(my_status.get('budget', 0), DAILY_SALARY * 0.45)
    if bid < min_bid:
        bid = min_bid

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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if budget <= 0:
        return 0.0

    # Read yesterday bids to infer aggressiveness
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                yesterday_bids.append(float(bid))
            except Exception:
                pass

    # Baseline: aim to secure enough water for 1 day without overpaying
    # Scale with supply: higher supply -> lower need to outbid
    supply_mid = (MAX_SUPPLY + MIN_SUPPLY) / 2.0
    supply_factor = 1.0
    if supply >= supply_mid:
        supply_factor = 0.85
    else:
        supply_factor = 1.05

    # Pressure estimate from yesterday
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    # If someone was bidding near/above salary, they are likely trying to lock survival.
    # We respond with a moderate bid to avoid total loss.
    aggressive_threshold = DAILY_SALARY * 0.85

    # Urgency: if we're already in danger of running out of water, bid higher.
    # Approx: if no_water_days is close to a typical survival limit (unknown), treat hp as main signal.
    urgency = 1.0
    if hp <= 2:
        urgency = 1.25
    elif hp <= 4:
        urgency = 1.12

    # If we've been without water for multiple days, increase urgency.
    if no_water_days >= 3:
        urgency += 0.08

    # Core bid target
    if highest_prev_bid >= aggressive_threshold:
        # Cindy-like behavior: don't match her max; bid enough to compete but stay solvent.
        target = max(DAILY_SALARY * 0.35, avg_prev_bid * 0.55)
        target *= supply_factor
        target *= urgency
    else:
        target = max(DAILY_SALARY * 0.45, avg_prev_bid * 0.6)
        target *= supply_factor
        # If hp is healthy, slightly reduce to save budget
        if hp >= 7:
            target *= 0.92
        target *= urgency

    # Convert target into a safe cap based on budget
    # Keep some reserve to survive future days.
    reserve_fraction = 0.25 if hp <= 3 else 0.35
    max_affordable = budget * (1.0 - reserve_fraction)

    bid = min(target, max_affordable)

    # Ensure non-negative and avoid tiny bids when we are in danger
    if hp <= 2 and bid < DAILY_SALARY * 0.6:
        bid = min(budget, DAILY_SALARY * 0.75)

    if bid < 0:
        bid = 0.0

    # Small smoothing to avoid exact ties; deterministic by day
    bid += (day % 3) * 0.5

    # Final clamp
    if bid > budget:
        bid = budget

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

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    if not alive_opponents:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace
    prev_bids = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # If we have no trace bids, fall back to conservative mid bid
    if not prev_bids:
        base = DAILY_SALARY * 0.55
        return max(0.0, min(my_budget, base))

    highest_prev_bid = max(prev_bids)
    second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev_bid

    # Estimate likely number of
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

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    # If we are nearly out of water/HP, we must bid aggressively.
    must_win = (hp <= 2) or (no_water_days >= 2)

    # Read yesterday bids to infer their aggressiveness.
    prev_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Base aggressiveness from yesterday.
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        avg_prev_bid = sum(prev_bids) / max(1, len(prev_bids))
    else:
        highest_prev_bid = 0.0
        avg_prev_bid = 0.0

    # Supply pressure: with higher supply, we can bid slightly less.
    supply_norm = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    if supply_norm < 0.0:
        supply_norm = 0.0
    if supply_norm > 1.0:
        supply_norm = 1.0

    # Target bid bands.
    # Surviving opponents bid around ~97 yesterday; we try to be competitive but cheaper.
    # If they were bidding very high, increase.
    if must_win:
        target = DAILY_SALARY * (0.85 - 0.15 * supply_norm)  # 76.5..85.5
    else:
        # If their highest bid is high, we shadow slightly below it.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            target = min(DAILY_SALARY * (0.75 - 0.10 * supply_norm), highest_prev_bid - 2.0)
        else:
            # Otherwise, bid around the average/typical survival level.
            base = max(DAILY_SALARY * (0.55 - 0.05 * supply_norm), avg_prev_bid * 0.9)
            target = base

    # Convert target into a budget-safe bid.
    # Never bid more than we can afford.
    bid = min(budget, max(1.0, target))

    # If budget is low, cap more tightly to avoid early bankruptcy.
    if budget < DAILY_SALARY * 0.6:
        bid = min(bid, budget * 0.9)

    # Small late-episode escalation (day 8-10) to secure remaining survival.
    if day >= 8:
        bid = min(budget, bid * 1.08)

    return float(bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    # day_context: {supply, day}
    supply = day_context['supply']
    day = day_context['day']

    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    # If no opponents alive, conserve budget.
    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.35))

    # Estimate scarcity: higher supply reduces urgency.
    # supply is in [15,25]. If supply is near 15, water is tighter.
    # Use a smooth urgency score.
    if supply <= MIN_SUPPLY:
        urgency = 1.0
    elif supply >= MAX_SUPPLY:
        urgency = 0.15
    else:
        urgency = 1.0 - (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)

    # Read yesterday bids to infer pressure.
    prev_bids = []
    prev_hp_after = []
    for oid, o in alive:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            prev_bids.append(float(b))
            prev_hp_after.append(prev.get('hp_after', None))

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # If someone was bidding extremely high yesterday, increase bid to avoid losing.
    # Scale aggressiveness by our hp/no_water_days.
    critical = (hp <= 2) or (no_water_days >= 2)
    # Convert highest_prev_bid into a pressure factor.
    pressure = min(1.0, highest_prev_bid / (DAILY_SALARY * 1.6))

    # Base bid target: we want to win when urgency is high and pressure is high.
    # Use a margin over typical pressure.
    # Typical winners in this meta appear around 0.5-1.6*DAILY_SALARY.
    target = DAILY_SALARY * (0.35 + 0.45 * urgency + 0.25 * pressure)

    # If critical, be more aggressive.
    if critical:
        target *= 1.35

    # If highest_prev_bid was very low, we can undercut slightly.
    if highest_prev_bid > 0:
        if highest_prev_bid < DAILY_SALARY * 0.8:
            target *= 0.92

    # Cap by budget and avoid bidding more than affordable.
    bid = min(budget, target)

    # Ensure non-negative.
    if bid < 0.0:
        bid = 0.0

    # Add a tiny deterministic nudge based on day to break ties.
    # (No randomness to keep deterministic.)
    bid += (int(day) % 3) * 0.5

    # Final cap again.
    if bid > budget:
        bid = budget

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
    day = int(day_context.get('day', 0))

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp is not None and opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace for immediate reaction
    prev_bids = []
    for opp_id, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
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

    # Supply pressure estimate: higher supply => bid less.
    # Normalize within [MIN_SUPPLY, MAX_SUPPLY]
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_norm = 0.5
    supply_norm = max(0.0, min(1.0, supply_norm))

    # Base bid: moderate, scaled down when supply is plentiful.
    # Also react to low hp / accumulating no-water days.
    urgency = 0.0
    if my_hp <= 2.0:
        urgency += 1.0
    if my_hp <= 4.0:
        urgency += 0.5
    if my_no_water_days >= 2:
        urgency += 0.5
    if my_no_water_days >= 3:
        urgency += 0.5

    base = DAILY_SALARY * (0.62 - 0.25 * supply_norm)
    bid = base + urgency * (DAILY_SALARY * 0.25)

    # If someone previously overbid massively (like Cindy), avoid matching exactly unless we must.
    # Use thresholds relative to DAILY_SALARY.
    if highest_prev_bid >= DAILY_SALARY * 1.4:
        if my_hp > 4.0 and my_no_water_days <= 1:
            # Don't start a price war; slight undercut
            bid = min(bid, second_prev_bid + 1.0 if second_prev_bid > 0 else bid)
        else:
            # Need water soon; raise but still capped
            bid = max(bid, DAILY_SALARY * 0.95)
    elif highest_prev_bid >= DAILY_SALARY * 0.8:
        # Medium pressure: bid around the top-1 neighborhood
        bid = max(bid, min(highest_prev_bid + 1.5, DAILY_SALARY * 1.05))

    # Ensure we don't exceed budget and never negative
    bid = max(0.0, min(my_budget, bid))

    # If budget is tiny, still bid something nonzero to secure if possible
    if bid <= 0.0 and my_budget > 0.0:
        bid = min(my_budget, 1.0)

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

    # Alive opponents (current)
    alive_opps = [o for o in opponents_status.values() if o.get('alive')]
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday traces to infer who is under pressure
    low_hp_opps = []
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        prev_bid = prev.get('bid', None)
        if prev_bid is not None:
            try:
                yesterday_bids.append(float(prev_bid))
            except Exception:
                pass
        prev_hp_after = prev.get('hp_after', None)
        if prev_hp_after is not None:
            try:
                if float(prev_hp_after) <= 3:
                    low_hp_opps.append(opp)
            except Exception:
                pass

    # Baseline: aim to cover requirement with some margin.
    # Supply is 15..25, so water units are supply/WATER_REQ-ish; we bid in money.
    # Use a conservative bid that still competes.
    bid_floor = DAILY_SALARY * 0.45
    bid_cap = DAILY_SALARY * 0.95

    # Pressure-based adjustment: if multiple opponents ended yesterday with low hp, they may continue overbidding.
    pressure = len(low_hp_opps)

    # Use yesterday max bid as a proxy for market intensity.
    market = max(yesterday_bids) if yesterday_bids else bid_floor

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])

    # If I'm in danger, bid harder.
    if my_hp <= 2.0:
        target = max(market * 0.85, DAILY_SALARY * 0.75)
    elif my_hp <= 4.0:
        target = max(market * 0.7, DAILY_SALARY * 0.6)
    else:
        # Healthy: bid based on pressure and market.
        if pressure >= 2:
            target = max(market * 0.65, bid_floor * 1.05)
        elif pressure == 1:
            target = max(market * 0.55, bid_floor)
        else:
            target = max(market * 0.45, bid_floor * 0.95)

    # Supply-aware tweak: with higher supply, we can bid less.
    if supply >= 21.0:
        target *= 0.92
    elif supply <= 17.0:
        target *= 1.05

    # Ensure within budget and caps.
    target = min(target, bid_cap)
    target = min(target, my_budget)

    # If budget is too low, still bid something meaningful but not all-in.
    if my_budget < DAILY_SALARY * 0.5:
        target = min(target, my_budget * 0.75)

    # Final clamp
    if target < 0:
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Alive opponents
    alive = [o for o in opponents_status.values() if o.get('alive')]
    if not alive:
        # If alone, bid enough to guarantee water; keep budget safety.
        if my_status['hp'] <= 2:
            return min(my_status['budget'], DAILY_SALARY * 0.95)
        return min(my_status['budget'], DAILY_SALARY * 0.6)

    # Read yesterday traces for immediate reaction
    prev_bids = []
    prev_pressures = []
    for o in alive:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            prev_bids.append(float(b))
        # Use their yesterday hp_after/status as a proxy for pressure
        hp_after = prev.get('hp_after', None)
        if hp_after is not None:
            prev_pressures.append(float(hp_after))

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    lowest_prev_hp_after = min(prev_pressures) if prev_pressures else 10.0

    # Estimate how many water units are likely needed to avoid no-water day risk.
    # With per-unit requirement = WATER_REQ, each unit corresponds to WATER_REQ water.
    # We use a conservative target share.
    # target_units ~ ceil(WATER_REQ / (supply/units)) is not directly inferable.
    # Instead, map supply to a heuristic bid level.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Baseline bid: moderate when supply is mid, higher when our hp is low.
    if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
        base = DAILY_SALARY * (0.75 + 0.15 * (1.0 - supply_ratio))
    elif my_status['hp'] <= 4:
        base = DAILY_SALARY * (0.6 + 0.15 * (1.0 - supply_ratio))
    else:
        base = DAILY_SALARY * (0.52 + 0.12 * (1.0 - supply_ratio))

    # Exploit aggression: if others bid extremely high yesterday, they likely overcommitted.
    # So we shade down slightly to avoid price war while still staying competitive.
    # If highest_prev_bid is very high relative to our daily salary, reduce.
    if highest_prev_bid >= DAILY_SALARY * 1.2:
        base *= 0.86
    elif highest_prev_bid >= DAILY_SALARY * 0.95:
        base *= 0.93

    # If some opponents ended yesterday with very low hp, they may bid even more today.
    # Slightly increase to avoid being outbid.
    if lowest_prev_hp_after <= 2:
        base *= 1.05

    # Convert to final bid with budget cap and a small floor to stay in contention.
    # Keep a minimum bid fraction to avoid losing to low bids.
    min_bid = DAILY_SALARY * 0.35
    bid = max(min_bid, base)

    # Final cap by budget
    bid = min(bid, my_status['budget'])

    # If budget is extremely low, bid remaining budget to maximize chance of survival.
    if my_status['budget'] <= DAILY_SALARY * 0.2:
        bid = my_status['budget']

    # Ensure bid is positive integer-ish (game may accept float; keep as float but non-negative)
    if bid < 0:
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

    supply = day_context['supply']
    day = day_context['day']

    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opps = [o for o in opponents_status.values() if o.get('alive')]
    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday trace bids to infer how aggressively others competed.
    prev_bids = []
    prev_hp_after = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            prev_bids.append(b)
        prev_hp_after.append(prev.get('hp_after', None))

    # Aggression estimate from yesterday.
    if prev_bids:
        max_prev_bid = max(prev_bids)
        avg_prev_bid = sum(prev_bids) / float(len(prev_bids))
    else:
        max_prev_bid = 0.0
        avg_prev_bid = 0.0

    # If someone died yesterday, they likely overbid; we avoid mirroring extreme bids.
    # If many survived with decent hp, we still need to be competitive.
    died_count = 0
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        if prev.get('status') == 'dead' or prev.get('hp_after', 1) <= 0:
            died_count += 1

    # Supply pressure: lower supply means higher chance of losing water.
    # Convert supply to a rough scarcity level.
    scarcity = (MAX_SUPPLY - float(supply)) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    scarcity = max(0.0, min(1.0, scarcity))

    # Base bid target: mid-high, adjusted by our hp and scarcity.
    # If we are already low hp or have gone without water, increase bid.
    if hp <= 2 or no_water_days >= 1:
        urgency = 1.0
    elif hp <= 4 or no_water_days == 0:
        urgency = 0.7
    else:
        urgency = 0.45

    # Determine a competitive bid ceiling using yesterday's max/avg.
    # We target just below the highest yesterday bid to avoid waste (Alex died after high bids).
    # Use thresholds relative to DAILY_SALARY.
    competitive = avg_prev_bid
    if max_prev_bid > 0:
        competitive = min(competitive, max_prev_bid * 0.85)

    # If yesterday bids were generally high (indicating tough competition), raise our floor.
    if avg_prev_bid >= DAILY_SALARY * 1.4:
        floor_bid = DAILY_SALARY * (0.9 + 0.2 * scarcity)
    else:
        floor_bid = DAILY_SALARY * (0.6 + 0.25 * scarcity)

    # Final target combines urgency and competitive estimate.
    target = floor_bid + (competitive - floor_bid) * urgency

    # Small extra bump if someone died yesterday (suggests others were fighting hard around that time).
    target *= (1.0 + 0.05 * min(3, died_count))

    # Ensure we don't bid more than we can afford.
    # Also cap to avoid overpaying beyond what would be consistent with a mid-high strategy.
    cap = min(budget, DAILY_SALARY * 3.0)
    bid = min(cap, max(0.0, target))

    # If budget is very low, still bid enough to try to avoid death.
    if budget <= DAILY_SALARY * 0.3:
        bid = min(budget, DAILY_SALARY * 0.95)

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

    # Identify alive opponents and use yesterday's immediate bids
    alive_opponents = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opponents:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.4))

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Pressure detection: if someone was bidding very aggressively, we match partially.
    aggressive_threshold = DAILY_SALARY * 0.85  # 76.5

    # Supply-based aggressiveness: more supply means less need to overbid.
    # target_water_units: how many units we aim to secure (0..2 typically)
    target_water_units = 1
    if supply >= 21.0:
        target_water_units = 2
    else:
        target_water_units = 1

    # Convert desired water units into a bid heuristic using water requirement.
    # Since the game mechanics aren't provided, we use a monotone mapping:
    # more desired units => higher bid, scaled by remaining days and hp.
    remaining_days = max(1, int(10 - day))
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])

    # Safety factor: if low hp, bid harder.
    if hp <= 1:
        hp_factor = 0.95
    elif hp == 2:
        hp_factor = 0.85
    elif hp == 3:
        hp_factor = 0.75
    else:
        hp_factor = 0.65

    # If aggressive bids were seen, we slightly increase to avoid losing.
    if highest_prev_bid >= aggressive_threshold:
        base = DAILY_SALARY * (0.35 if hp > 3 else 0.75)
    else:
        base = max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5)

    # Supply adjustment: when supply is high, we can bid less; when low, bid more.
    supply_factor = 1.0
    if supply <= 17.0:
        supply_factor = 1.08
    elif supply >= 23.0:
        supply_factor = 0.92

    # Desired units adjustment
    units_factor = 1.0 if target_water_units <= 1 else 1.25

    # Time pressure: later days should preserve budget but ensure survival; bid a bit more earlier.
    time_factor = 1.0
    if remaining_days <= 3:
        time_factor = 1.08
    elif remaining_days >= 7:
        time_factor = 0.95

    bid = base * hp_factor * supply_factor * units_factor * time_factor

    # Budget cap: never exceed budget.
    bid = max(0.0, min(budget, bid))

    # Additional cap to avoid overextending in medium scenario.
    # Keep bids under ~0.9*DAILY_SALARY unless hp is critical.
    if hp > 2:
        bid = min(bid, DAILY_SALARY * 0.85)
    else:
        bid = min(bid, DAILY_SALARY * 0.98)

    return float(bid)
"""
