# ============================================================
# Experiment: exp_098
# Agent: Bob
# Source: exp_098
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    # If no opponents, bid conservatively.
    if not alive_opponents:
        return max(0.0, min(my_status.get('budget', 0.0), DAILY_SALARY * 0.4))

    # Read yesterday's bids from immediate previous_trace.
    yesterday_bids = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Baseline target bid depends on how much water likely exists.
    # If supply is tight, we must bid more to secure water.
    # supply range is [15,25].
    if supply <= 16.0:
        pressure_supply = 1.0
    elif supply <= 19.0:
        pressure_supply = 0.8
    elif supply <= 22.0:
        pressure_supply = 0.6
    else:
        pressure_supply = 0.45

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))

    # Determine opponent pressure from yesterday.
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        lowest_prev_bid = min(yesterday_bids)

        # If someone was bidding aggressively, match just below to win without overpaying.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_hp > 3.0:
                target = DAILY_SALARY * 0.28 + (highest_prev_bid - DAILY_SALARY * 0.85) * 0.15
                target = min(target, highest_prev_bid - 1.0)
            else:
                target = DAILY_SALARY * 0.75
                target = min(target, highest_prev_bid - 0.5)
        # If bids were moderate, bid enough to be competitive.
        elif highest_prev_bid >= DAILY_SALARY * 0.55:
            target = max(highest_prev_bid * 0.92, lowest_prev_bid + 1.0)
        else:
            # Low bids: bid slightly above the likely clearing price.
            target = max(DAILY_SALARY * 0.45 * pressure_supply, lowest_prev_bid + 1.5)
    else:
        # No trace info: use supply pressure and our hp.
        if my_hp <= 2.0:
            target = DAILY_SALARY * 0.85
        elif my_hp <= 3.0:
            target = DAILY_SALARY * 0.65
        else:
            target = DAILY_SALARY * 0.5 * pressure_supply

    # Convert target into a bid amount; ensure we don't exceed budget.
    # Also cap at a reasonable fraction of budget to avoid going broke.
    max_reasonable = my_budget * 0.95
    bid = max(0.0, min(target, max_reasonable))

    # If supply is very low, increase bid to secure at least one WATER_REQ unit.
    # (We don't know exact allocation rule; this biases toward winning.)
    if supply < float(WATER_REQ) * 2.0:
        bid = min(max_reasonable, bid + DAILY_SALARY * 0.1)

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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Alive opponents
    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    if not alive_opponents:
        return min(float(my_status['budget']), DAILY_SALARY * 0.4)

    # Yesterday pressure: use max bid among alive opponents' previous_trace
    max_prev_bid = None
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is None:
            continue
        if max_prev_bid is None or b > max_prev_bid:
            max_prev_bid = float(b)

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Estimate whether we can likely secure enough water.
    # In this game, higher bids correlate with higher allocation; we calibrate using yesterday pressure.
    # Target bid: slightly above yesterday max when under pressure; otherwise moderate.
    if max_prev_bid is None:
        pressure_bid = DAILY_SALARY * 0.55
    else:
        pressure_bid = max_prev_bid

    # If we're close to death or already missing water, go for a high bid.
    urgent = (hp <= 2.5) or (no_water_days >= 1)

    # If supply is low, competition is higher: increase bid.
    supply_factor = 1.0
    if supply <= float(WATER_REQ):
        supply_factor = 1.15
    elif supply <= (MIN_SUPPLY + 0.5):
        supply_factor = 1.08

    # Budget-aware caps: never bid more than we can sustain for a few days.
    # Also keep some reserve for later rounds.
    reserve_ratio = 0.25
    max_affordable = max(0.0, budget * (1.0 - reserve_ratio))

    # Strategy tiers
    if urgent:
        # If someone was spending near/above salary yesterday, match + small overbid.
        if max_prev_bid is not None and max_prev_bid >= DAILY_SALARY * 0.85:
            bid = (pressure_bid + 5.0) * supply_factor
        else:
            bid = DAILY_SALARY * 0.95
    else:
        # Not urgent: bid to contest only if yesterday pressure was high.
        if max_prev_bid is not None and max_prev_bid >= DAILY_SALARY * 1.1:
            bid = (pressure_bid * 0.75) * supply_factor
        elif max_prev_bid is not None and max_prev_bid >= DAILY_SALARY * 0.85:
            bid = (pressure_bid * 0.6 + 10.0) * supply_factor
        else:
            bid = DAILY_SALARY * 0.55 * supply_factor

    # Additional day-based adjustment: later days require more survival probability.
    if day >= 7:
        bid *= 1.08

    # Final clamp
    bid = float(bid)
    if max_affordable <= 0.0:
        return 0.0
    if bid > max_affordable:
        bid = max_affordable

    # Ensure non-negative and not exceeding budget
    if bid < 0.0:
        bid = 0.0
    if bid > budget:
        bid = budget

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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # If no opponents are alive, take a safe low bid.
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bid pressure from previous_trace only.
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', None) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    # Supply pressure: lower supply means fewer units; bid more.
    # Expected number of allocations roughly scales with supply/WATER_REQ.
    alloc_factor = supply / float(WATER_REQ)  # float
    # Map alloc_factor to a pressure multiplier.
    if alloc_factor <= 1.1:
        pressure = 1.25
    elif alloc_factor <= 1.7:
        pressure = 1.10
    else:
        pressure = 0.95

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status.get('no_water_days', 0))

    # Base willingness: moderate. Prefer not to chase Cindy/David's high bids.
    base = DAILY_SALARY * 0.55

    # If my hp is critical or I've already been without water, increase.
    if hp <= 2.0 or no_water_days >= 2:
        base = DAILY_SALARY * 0.90
    elif hp <= 4.0:
        base = DAILY_SALARY * 0.70

    # If yesterday someone paid extremely high, we may need to counter slightly,
    # but cap below matching their max to preserve budget.
    # Cindy/David showed ~90-130; Alex died with high bid too; Eric was low.
    if highest_prev_bid >= DAILY_SALARY * 0.95:
        # Bid enough to avoid being priced out, but not equal to their ceiling.
        target = min(DAILY_SALARY * 0.75, highest_prev_bid * 0.55 + DAILY_SALARY * 0.15)
    else:
        # If bids were not extreme, bid around base adjusted by pressure and avg.
        target = base
        if avg_prev_bid > 0:
            target = 0.65 * target + 0.35 * avg_prev_bid

    bid = float(target) * float(pressure)

    # Ensure bid is at least a small positive amount when competing.
    # Also never exceed budget.
    bid = max(1.0, bid)
    bid = min(bid, budget)

    # If budget is too low, spend what's left.
    if budget <= 1.0:
        return float(budget)

    # Gentle day-based adjustment to avoid running out too early (episode up to 10).
    # Later days: slightly more aggressive.
    if day >= 8:
        bid = min(budget, bid * 1.15)
    elif day <= 2:
        bid = max(1.0, bid * 0.95)

    return float(bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    # Alive opponents and yesterday bids
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        return min(my_status.get('budget', 0.0), DAILY_SALARY * 0.4)

    high_prev_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            high_prev_bids.append(float(bid))

    max_prev_bid = max(high_prev_bids) if high_prev_bids else 0.0

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Supply pressure heuristic: when supply is close to MAX, fewer players need to bid extremely.
    # Convert supply to an integer bucket safely.
    supply_int = int(round(supply))
    # Expected maximum number of WATER_REQ units available (approx)
    units = max(0, int(supply_int // WATER_REQ))

    # Base aggressiveness: if we're low HP or have accumulated no-water days, bid more.
    urgent = (hp <= 2.5) or (no_water_days >= 2)

    # If opponents were bidding high yesterday, we shade slightly under their max to avoid price inflation.
    # But ensure bid is competitive when urgent.
    if max_prev_bid >= DAILY_SALARY * 0.85:
        if urgent:
            target = max_prev_bid * 0.65 + 15.0
        else:
            target = max_prev_bid * 0.55 + 10.0
    else:
        if urgent:
            target = DAILY_SALARY * 0.75
        else:
            target = DAILY_SALARY * 0.45

    # If supply is tight (few units), increase bid to secure water.
    if units <= 1:
        target *= 1.15
    elif units >= 2:
        target *= 0.95

    # Never exceed a fraction of budget; also cap relative to salary to keep sustainable.
    cap = DAILY_SALARY * (0.95 if urgent else 0.65)
    bid = min(budget, cap, target)

    # Ensure non-negative bid
    if bid < 0.0:
        bid = 0.0

    return bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    # Determine how many water units are likely available for a full requirement.
    # Use int() to avoid any float index issues (even though we don't index lists here).
    units = int(supply / float(WATER_REQ) + 1e-9)

    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive.append((opp_id, opp))

    if not alive:
        # If no one else is alive, conserve budget.
        return float(min(my_status.get('budget', 0.0), DAILY_SALARY * 0.4))

    # Use yesterday's bid pressure from opponents that were alive.
    prev_bids = []
    for opp_id, opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev.get('bid')))

    # If we have no trace data, default to a conservative mid bid.
    if not prev_bids:
        base = DAILY_SALARY * 0.55
    else:
        highest_prev_bid = max(prev_bids)
        # If someone was bidding aggressively yesterday, match closer to avoid losing the auction.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            base = DAILY_SALARY * (0.35 if my_status.get('hp', 0) > 3 else 0.95)
        else:
            # Otherwise, bid enough to beat low bidders but not overpay.
            base = max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5)

    # Adjust for our own urgency.
    hp = float(my_status.get('hp', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))
    budget = float(my_status.get('budget', 0.0))

    # If we're already low HP or have gone multiple days without water, push harder.
    if hp <= 2 or no_water_days >= 2:
        urgency_mult = 1.25
    elif hp <= 4 or no_water_days >= 1:
        urgency_mult = 1.10
    else:
        urgency_mult = 0.98

    # Supply-based adjustment: with tighter supply, we should be more competitive.
    if supply <= 18.0:
        supply_mult = 1.15
    elif supply <= 21.0:
        supply_mult = 1.05
    else:
        supply_mult = 0.95

    bid = base * urgency_mult * supply_mult

    # Hard caps: never exceed what we can pay, and avoid extreme overbidding.
    # Also, keep bids within a reasonable range relative to daily salary.
    bid = min(bid, budget)
    bid = min(bid, DAILY_SALARY * 1.75)

    # If our budget is tiny, still bid something to try to secure water.
    if bid < 1e-6:
        bid = min(budget, DAILY_SALARY * 0.25)

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

    # If we are in danger, bid aggressively.
    if my_status['hp'] <= 2:
        return min(my_status['budget'], int(DAILY_SALARY * 0.95))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    if not alive_opponents:
        return min(my_status['budget'], int(DAILY_SALARY * 0.4))

    # Read yesterday's bids from previous_trace for immediate reaction.
    prev_bids = []
    prev_by_id = {}
    for opp_id, opp in opponents_status.items():
        if not opp.get('alive', False):
            continue
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                bid_val = float(bid)
            except Exception:
                bid_val = None
            if bid_val is not None:
                prev_bids.append(bid_val)
                prev_by_id[opp_id] = bid_val

    # Estimate how many full water units supply can cover this day.
    # Use this to decide whether to fight for allocation.
    # supply is total water; each unit costs WATER_REQ water.
    units = int(supply / float(WATER_REQ))

    # Target bid heuristics based on yesterday's strongest bidder.
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        lowest_prev_bid = min(prev_bids)

        # If Cindy-like pressure existed (high bids), we bid just above a mid/high threshold.
        # If highest was very high, cap to avoid overspending.
        if highest_prev_bid >= DAILY_SALARY * 1.25:
            # Likely Cindy is forcing. Bid to secure at least some share.
            # Slightly above Alex-ish range but below Cindy ceiling.
            base = int(DAILY_SALARY * 0.8)  # 72
            # If we saw a strong highest bid, lean upward but not to the top.
            bid = int(min(my_status['budget'], max(base, highest_prev_bid * 0.75)))
        elif highest_prev_bid >= DAILY_SALARY * 0.8:
            # Moderate contention: bid around the leader but with a small edge.
            bid = int(min(my_status['budget'], highest_prev_bid * 0.9 + 5))
        else:
            # Low contention: bid just enough to beat low bidders.
            bid = int(min(my_status['budget'], max(lowest_prev_bid + 10, DAILY_SALARY * 0.55)))
    else:
        # No trace bids: play mid.
        bid = int(min(my_status['budget'], DAILY_SALARY * 0.6))

    # Adjust for supply regime: with more units, we can bid slightly less.
    if units <= 1:
        # Tight supply: increase bid
        bid = int(min(my_status['budget'], bid + 10))
    elif units >= 2:
        # Comfortable: decrease bid
        bid = int(max(0, bid - 10))

    # Ensure we don't bid more than we can afford.
    if my_status['budget'] is None:
        return 0
    if my_status['budget'] <= 0:
        return 0

    return int(min(my_status['budget'], max(0, bid)))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    # Alive opponents and their yesterday bids
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

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = 0.0
    if len(yesterday_bids) >= 2:
        s = sorted(yesterday_bids, reverse=True)
        second_prev_bid = float(s[1])

    # Supply pressure heuristic: if supply is tight, we need to bid to avoid no-water days.
    tight_supply = supply <= float(WATER_REQ) * 1.6  # roughly 14-15
    low_hp = my_status.get('hp', 0) <= 2
    mid_hp = my_status.get('hp', 0) <= 4

    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Base bid target
    if not alive_opps:
        target = DAILY_SALARY * 0.4
    else:
        # If someone already paid very high yesterday, don't mirror fully; bid just enough to compete.
        if highest_prev_bid >= DAILY_SALARY * 1.45:  # ~130+
            # Cindy-like behavior: keep moderate pressure.
            if low_hp:
                target = min(budget, DAILY_SALARY * 0.95)
            elif mid_hp or tight_supply or no_water_days >= 1:
                target = min(budget, max(DAILY_SALARY * 0.65, highest_prev_bid * 0.55))
            else:
                target = min(budget, max(DAILY_SALARY * 0.5, highest_prev_bid * 0.45))
        elif highest_prev_bid >= DAILY_SALARY * 0.9:
            # Moderate-high bids: bid slightly above second-high to beat most.
            target = max(DAILY_SALARY * 0.55, second_prev_bid * 0.95, highest_prev_bid * 0.75)
            if low_hp:
                target *= 1.15
            target = min(budget, target)
        else:
            # Low bids: conserve.
            if low_hp:
                target = min(budget, DAILY_SALARY * 0.9)
            elif mid_hp or tight_supply or no_water_days >= 1:
                target = min(budget, DAILY_SALARY * 0.65)
            else:
                target = min(budget, DAILY_SALARY * 0.5)

    # Final safety clamps
    if budget <= 0:
        return 0.0

    # Never bid more than budget; keep within reasonable range.
    bid = float(target)
    if bid > budget:
        bid = budget

    # If supply is extremely low, increase bid a bit to avoid starvation.
    if tight_supply and not low_hp:
        bid = min(budget, bid * 1.08)

    # If my hp is critically low, ensure strong bid.
    if low_hp:
        bid = min(budget, max(bid, DAILY_SALARY * 0.85))

    # If already had no-water days, increase modestly.
    if no_water_days >= 2:
        bid = min(budget, max(bid, DAILY_SALARY * 0.75))

    return float(bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.45))

    # Estimate opponent pressure from yesterday trace bids.
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Baseline bid target: slightly under yesterday's typical high bids.
    if prev_bids:
        prev_bids_sorted = sorted(prev_bids)
        # Use a robust high percentile to avoid being too low.
        idx = int(len(prev_bids_sorted) * 0.75)
        if idx >= len(prev_bids_sorted):
            idx = len(prev_bids_sorted) - 1
        target = prev_bids_sorted[idx]
        # Undercut to win while reducing cost.
        bid = target - 3.0
    else:
        bid = DAILY_SALARY * 0.55

    # If supply is low, water is scarcer; increase bid modestly.
    # supply in [15,25], so normalize scarcity.
    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    if scarcity < 0.0:
        scarcity = 0.0
    if scarcity > 1.0:
        scarcity = 1.0
    bid *= (1.0 + 0.25 * scarcity)

    # If we're at risk (multiple no-water days or low hp), bid more.
    if hp <= 2.0:
        bid = max(bid, DAILY_SALARY * 0.9)
    elif hp <= 4.0 or no_water_days >= 2:
        bid = max(bid, DAILY_SALARY * 0.7)
    else:
        # Healthy: keep spending controlled.
        bid = min(bid, DAILY_SALARY * 0.65)

    # Never exceed budget.
    if budget <= 0.0:
        return 0.0
    bid = max(0.0, min(budget, bid))

    return float(bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Extract yesterday bids from previous_trace for immediate reaction
    prev_bids = []
    prev_pressures = []  # (opp_id, prev_bid, prev_hp_after)
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            b = float(prev['bid'])
            prev_bids.append(b)
            prev_pressures.append((oid, b, prev.get('hp_after', None)))

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    # Determine how many allocation units are likely available (approx)
    # Use int() to avoid float index issues.
    # If supply is closer to MIN_SUPPLY, competition likely higher.
    supply_frac = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if (MAX_SUPPLY - MIN_SUPPLY) != 0 else 0.5
    supply_frac = max(0.0, min(1.0, supply_frac))

    # Conservative baseline: aim around a fraction of salary.
    # If opponents previously bid very high, reduce our bid to avoid overpaying.
    if highest_prev_bid > DAILY_SALARY * 1.2:
        base = DAILY_SALARY * (0.35 + 0.15 * supply_frac)  # 0.35..0.50
    elif highest_prev_bid > DAILY_SALARY * 0.7:
        base = DAILY_SALARY * (0.45 + 0.15 * supply_frac)  # 0.45..0.60
    else:
        base = DAILY_SALARY * (0.55 + 0.15 * supply_frac)  # 0.55..0.70

    # Pressure response: if I'm in danger, bid more.
    # no_water_days increases risk; when hp is low, bid close to salary.
    if hp <= 2 or no_water_days >= 2:
        base = max(base, DAILY_SALARY * 0.85)
    elif hp <= 4 or no_water_days == 1:
        base = max(base, DAILY_SALARY * 0.65)

    # If my hp is good and opponents were overbidding, bid slightly below their typical level.
    # Use trace info to exploit overbidding.
    if highest_prev_bid > DAILY_SALARY * 1.0:
        target = min(highest_prev_bid * 0.55, avg_prev_bid * 0.7 if avg_prev_bid > 0 else base)
        base = min(base, target) if target > 0 else base

    # Final cap by budget and a mild safety floor.
    bid = min(budget, base)

    # Ensure non-negative and at least a minimal amount if budget allows.
    if bid < 0:
        bid = 0.0

    # If budget is too small, spend what we can.
    if budget <= DAILY_SALARY * 0.2:
        bid = min(budget, DAILY_SALARY * 0.2)

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

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from immediate previous_trace
    prev_bids = []
    prev_hp_after = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid', 0.0)))
            except Exception:
                pass
            try:
                prev_hp_after.append(float(prev.get('hp_after', o.get('hp', 0.0))))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Pressure estimate: if someone paid near/above typical salary, they likely contested aggressively.
    aggressive = highest_prev_bid >= DAILY_SALARY * 0.85

    # Supply pressure: with higher supply, water is cheaper; with lower supply, bid more.
    # Normalize between MIN_SUPPLY and MAX_SUPPLY.
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_norm = 0.5
    supply_norm = max(0.0, min(1.0, supply_norm))

    # Base bid target
    # If aggressive: shade below their top bid to avoid overpaying while still contesting.
    # If not aggressive: bid enough to secure water when needed.
    if aggressive:
        # Shade factor: bid slightly below the highest previous bid but scale with my needs.
        need_factor = 1.0
        if my_hp <= 2.0 or my_no_water_days >= 2:
            need_factor = 1.25
        elif my_hp >= 7.0 and my_no_water_days <= 0:
            need_factor = 0.85
        target = highest_prev_bid * 0.92 * need_factor
    else:
        # When not aggressive, bid around a fraction of salary, more if supply is tight.
        tightness = 1.0 - supply_norm  # 1 at MIN_SUPPLY, 0 at MAX_SUPPLY
        target = DAILY_SALARY * (0.45 + 0.25 * tightness)
        if my_hp <= 2.0 or my_no_water_days >= 2:
            target *= 1.35
        if my_hp >= 7.0 and my_no_water_days <= 0:
            target *= 0.9

    # Ensure we don't bid more than budget; also add a small floor to avoid zero bids.
    # If my budget is very low, conserve.
    if my_budget <= 0.0:
        return 0.0

    # Soft cap relative to budget
    cap = my_budget

    # If my HP is critical, prioritize survival even if it means spending.
    if my_hp <= 1.5 or my_no_water_days >= 3:
        # Spend aggressively but not exceeding budget
        return max(0.0, min(cap, DAILY_SALARY * 0.95))

    # If my HP is moderate and budget allows, bid near target.
    bid = min(cap, target)

    # If supply is extremely low, ensure bid is not too small.
    if supply <= float(MIN_SUPPLY):
        bid = max(bid, DAILY_SALARY * 0.55)

    # Final clamp
    if bid < 0.0:
        bid = 0.0
    return float(bid)
"""
