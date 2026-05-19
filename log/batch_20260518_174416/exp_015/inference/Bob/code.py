# ============================================================
# Experiment: exp_015
# Agent: Bob
# Source: exp_015
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

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return min(float(my_status['budget']), DAILY_SALARY * 0.4)

    # Immediate reaction to yesterday's bids (only previous_trace)
    prev_bids = []
    prev_hp_after = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass
        hp_after = prev.get('hp_after', None)
        if hp_after is not None:
            try:
                prev_hp_after.append(float(hp_after))
            except Exception:
                pass

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Estimate how desperate we should be
    desperation = 0.0
    if my_hp <= 2.0:
        desperation = 1.0
    elif my_hp <= 4.0:
        desperation = 0.7
    elif no_water_days >= 2:
        desperation = 0.6

    # If opponents were bidding aggressively yesterday, we increase to avoid losing allocation.
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        second_highest = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev_bid

        # Aggressive threshold tuned to DAILY_SALARY scale
        aggressive = highest_prev_bid >= DAILY_SALARY * 0.85
        if aggressive:
            # If we are healthy, don't fully mirror; if low HP, mirror more.
            base = DAILY_SALARY * (0.35 if my_hp > 4.0 else 0.9)
            # Nudge above second-highest to secure water when possible
            target = max(base, second_highest + 1.5)
        else:
            # Moderate bid: slightly above highest_prev_bid when close, else stay efficient.
            target = max(DAILY_SALARY * 0.5, highest_prev_bid + (2.0 if highest_prev_bid >= DAILY_SALARY * 0.55 else 0.0))

    else:
        # No bid info: use our own state and supply pressure.
        supply_pressure = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY + 1e-9)
        # Higher supply => lower bid
        target = DAILY_SALARY * (0.65 - 0.25 * supply_pressure)

    # Convert target into a safe budget-constrained bid
    # Also avoid spending too much when not desperate.
    if desperation <= 0.0:
        cap = DAILY_SALARY * 0.65
    elif desperation < 0.8:
        cap = DAILY_SALARY * 0.85
    else:
        cap = DAILY_SALARY * 0.98

    bid = min(my_budget, min(target, cap))

    # Ensure non-trivial bid
    min_bid = DAILY_SALARY * 0.25
    if bid < min_bid:
        bid = min(my_budget, min_bid)

    # Final clamp
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
    # day_context only: supply, day
    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Basic safety
    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday bids only from previous_trace
    prev_bids = []
    for oid, o in alive_opps:
        pt = o.get('previous_trace', {})
        b = pt.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate how many full water units supply can cover
    # (not used directly for indexing; only for scaling)
    max_units = max(1, int(supply // float(WATER_REQ)))

    # If someone was bidding very high yesterday, they are likely pressuring; increase slightly.
    # If bids were low, keep moderate to preserve budget.
    pressure_threshold = DAILY_SALARY * 0.85  # 76.5

    # Base bid strategy: keep within a fraction of budget to avoid bankruptcy.
    # Also react to my own low HP / no-water streak.
    if my_hp <= 2.0 or my_no_water_days >= 2:
        base_frac = 0.95
    elif my_hp <= 4.0:
        base_frac = 0.75
    else:
        base_frac = 0.55

    # Pressure adjustment using yesterday's highest bid
    if highest_prev_bid >= pressure_threshold:
        # opponents likely spending hard; bid enough to compete but not fully commit
        bid = DAILY_SALARY * 0.65
        bid = bid + (highest_prev_bid - pressure_threshold) * 0.15
    else:
        # no extreme pressure yesterday; bid around mid to secure water if needed
        bid = DAILY_SALARY * 0.50
        bid = bid + (highest_prev_bid * 0.10)

    # Scale with supply scarcity: lower supply => slightly higher bid to secure allocation
    if supply <= float(MIN_SUPPLY) + 0.5:
        bid *= 1.15
    elif supply >= float(MAX_SUPPLY) - 0.5:
        bid *= 0.95

    # Final cap to budget and fraction
    cap = my_budget * base_frac
    bid = min(bid, cap, my_budget)

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

    budget = float(my_status['budget'])
    hp = float(my_status['hp'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from immediate trace only
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = 0.0
    if len(yesterday_bids) >= 2:
        sorted_bids = sorted(yesterday_bids, reverse=True)
        second_prev_bid = float(sorted_bids[1])

    # Supply pressure: lower supply increases need to outbid
    # Use a conservative target based on supply band
    if supply <= float(MIN_SUPPLY):
        supply_pressure = 1.0
    elif supply >= float(MAX_SUPPLY):
        supply_pressure = 0.65
    else:
        supply_pressure = 0.65 + 0.35 * ((float(MAX_SUPPLY) - supply) / (float(MAX_SUPPLY) - float(MIN_SUPPLY)))

    # If we have multiple no-water days, we must secure water
    must_secure = (no_water_days >= 1) or (hp <= 3)

    # Strategy: bid just above the likely clearing price proxy.
    # If highest previous bid was high, we expect aggressive bidding; otherwise, we can undercut.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        base = highest_prev_bid * (0.98 if not must_secure else 1.02)
    else:
        # If not everyone is going aggressive, aim slightly above second-highest to win
        base = (second_prev_bid + 2.0) if second_prev_bid > 0 else (highest_prev_bid * 0.9 + 2.0)

    # Adjust by supply pressure and our HP
    if must_secure:
        base *= (1.10 * supply_pressure)
    else:
        # With full HP, don't overspend
        if hp >= 8:
            base *= (0.85 * supply_pressure)
        else:
            base *= (0.95 * supply_pressure)

    # Budget and safety caps
    # Avoid spending more than a fraction of budget; also keep within typical daily salary scale.
    spend_cap = min(budget, DAILY_SALARY * (0.95 if must_secure else 0.65))

    bid = max(0.0, min(spend_cap, base))

    # If supply is very low and we might lose, add a small deterministic bump
    if supply <= float(MIN_SUPPLY) and not must_secure:
        bid = min(budget, bid + 3.0)

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

    # Identify alive opponents
    alive_opps = [o for o in opponents_status.values() if o.get('alive')]
    if not alive_opps:
        return float(min(my_status.get('budget', 0.0), DAILY_SALARY * 0.4))

    # Use only yesterday previous_trace for immediate reaction
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Base aggressiveness from yesterday bidding pressure
    base = DAILY_SALARY * 0.6  # mid
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        avg_prev_bid = sum(prev_bids) / float(len(prev_bids))
        # If others were near max, we slightly overbid; if not, stay near avg
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            base = max(base, avg_prev_bid * 0.95)
        else:
            base = max(base, avg_prev_bid * 0.8)

    # Adjust for current supply: lower supply => higher bid to avoid no-water days
    # Normalize supply into [0,1] where 0 is MIN_SUPPLY (tight) and 1 is MAX_SUPPLY (plenty)
    if MAX_SUPPLY > MIN_SUPPLY:
        t = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    else:
        t = 0.5
    t = max(0.0, min(1.0, t))

    # Tight supply: push bid up; plentiful: pull down
    supply_multiplier = 1.15 - 0.3 * t  # between ~0.85 and ~1.15

    # Health/budget risk control
    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = float(my_status.get('no_water_days', 0.0))

    # If I'm close to danger or accumulating no-water days, bid more
    danger_factor = 1.0
    if hp <= 2.5:
        danger_factor = 1.6
    elif hp <= 4.0:
        danger_factor = 1.3
    if no_water_days >= 2:
        danger_factor *= 1.25

    target = base * supply_multiplier * danger_factor

    # Keep within budget and avoid overspending: cap at 1.2*DAILY_SALARY unless budget forces
    cap = DAILY_SALARY * 1.2
    bid = min(budget, cap, target)

    # If budget is very small, still bid something meaningful when supply is tight
    if bid <= 0 and budget > 0:
        bid = min(budget, DAILY_SALARY * (0.3 if t > 0.5 else 0.7))

    return float(max(0.0, bid))
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

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # If we are in danger, bid aggressively.
    if my_hp <= 2 or my_no_water_days >= 2:
        bid = min(my_budget, DAILY_SALARY * 0.95)
        return bid

    # Read yesterday bids from traces to infer who is pressuring.
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate how many units are likely to be contested based on supply.
    # If supply is low, we must outbid more to guarantee water.
    # If supply is high, we can bid slightly lower.
    if supply <= (MIN_SUPPLY + 0.5):
        pressure_from_supply = 1.0
    elif supply >= (MAX_SUPPLY - 0.5):
        pressure_from_supply = 0.7
    else:
        pressure_from_supply = 0.85

    # Determine target bid using yesterday's aggressiveness.
    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / float(len(prev_bids))

        # Cindy died yesterday: if she bid low, others may still be cautious.
        # Use highest_prev as a proxy for current competitive ceiling.
        # If highest_prev is high, we must match a fraction of it.
        if highest_prev >= DAILY_SALARY * 0.85:
            # Very competitive environment: bid to secure.
            target = max(DAILY_SALARY * 0.45, highest_prev * 0.85)
        elif highest_prev >= DAILY_SALARY * 0.6:
            target = max(DAILY_SALARY * 0.4, avg_prev * 0.9)
        else:
            # Low pressure: bid enough to beat typical bids.
            target = max(DAILY_SALARY * 0.35, avg_prev * 0.75)
    else:
        target = DAILY_SALARY * 0.45

    # Adjust for supply pressure.
    target = target * pressure_from_supply

    # Keep within a safe band so we don't run out early.
    # If budget is low, scale down.
    max_reasonable = DAILY_SALARY * 0.75
    min_reasonable = DAILY_SALARY * 0.28

    if my_budget <= 0:
        return 0.0

    bid = min(my_budget, max_reasonable)
    if bid < min_reasonable:
        bid = min(my_budget, min_reasonable)

    # Ensure we are at least near the computed target.
    if target > bid:
        bid = min(my_budget, target)

    # Final clamp to non-negative.
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

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    # Collect yesterday bids from alive opponents
    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if bool(opp.get('alive', False)):
            alive_opponents.append(opp)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Estimate how many units of water are available (for pressure scaling)
    # Use explicit int() for any index usage; here we only compute.
    units = int(supply / float(WATER_REQ)) if WATER_REQ > 0 else 0
    pressure = 0.0
    if units >= 2:
        pressure = 0.35
    elif units == 1:
        pressure = 0.55
    else:
        pressure = 0.75

    # If my HP is critical, bid to secure water
    if my_hp <= 2 or my_no_water_days >= 2:
        target = DAILY_SALARY * (0.85 + 0.15 * pressure)
        bid = min(my_budget, target)
        return max(0.0, bid)

    # If opponents were bidding very high yesterday, raise enough to beat the median/high tier
    if yesterday_bids:
        yesterday_bids_sorted = sorted(yesterday_bids)
        n = len(yesterday_bids_sorted)
        idx = int(0.6 * (n - 1)) if n > 1 else 0
        mid_high = yesterday_bids_sorted[idx]
        top = yesterday_bids_sorted[-1]

        # Strategy: aim slightly above mid_high, but cap well below top to avoid Cindy/Eric overspending
        cap = DAILY_SALARY * (1.05 + 0.15 * pressure)  # ~94.5-106.2
        # However, yesterday bids were ~118-152; allow higher cap when supply is scarce
        if units <= 1:
            cap = DAILY_SALARY * (1.35 + 0.25 * pressure)  # ~121.5-135
        else:
            cap = DAILY_SALARY * (1.15 + 0.15 * pressure)  # ~103.5-117

        desired = mid_high + 6.0
        bid = min(my_budget, min(desired, cap))

        # If yesterday top was extreme, don't chase it fully
        if top > DAILY_SALARY * 1.55:
            bid = min(bid, DAILY_SALARY * (1.25 + 0.2 * pressure))

        return max(0.0, float(bid))

    # No signal: moderate bid to secure water without burning budget
    base = DAILY_SALARY * (0.6 + 0.25 * pressure)
    bid = min(my_budget, base)
    return max(0.0, float(bid))
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

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        # If no one else is alive, we can bid low.
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace for immediate reaction.
    yesterday_bids = []
    for opp_id, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        if prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # Baseline bid: if supply is scarce, more likely to be contested.
    # Also, if I'm close to death (hp low or no-water streak), increase bid.
    if hp <= 2.0 or no_water_days >= 2:
        urgency = 1.0
    elif hp <= 4.0 or no_water_days >= 1:
        urgency = 0.75
    else:
        urgency = 0.55

    # Supply pressure factor.
    # When supply is near MIN_SUPPLY, competition is higher.
    if supply <= MIN_SUPPLY + 0.5:
        pressure = 1.0
    elif supply >= MAX_SUPPLY - 0.5:
        pressure = 0.7
    else:
        # Linear interpolation
        pressure = 0.7 + (1.0 - 0.7) * ((MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY))

    # Determine likely contest level from yesterday bids.
    # If opponents previously bid very high, match/beat slightly.
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid

        # If someone bid near/above a high fraction of DAILY_SALARY, expect aggressive bidding.
        high_bid_threshold = DAILY_SALARY * 0.85
        if highest_prev_bid >= high_bid_threshold:
            target = highest_prev_bid + 2.0
        else:
            # Otherwise, aim to beat the second-highest modestly to win.
            target = max(DAILY_SALARY * 0.5, second_prev_bid + 1.5)

        # Apply urgency and pressure.
        target = target * (0.85 + 0.3 * urgency) * (0.9 + 0.2 * pressure)
    else:
        # No trace info; use a conservative bid.
        target = DAILY_SALARY * (0.5 + 0.4 * urgency) * pressure

    # Hard caps to avoid bankrupting.
    # Keep some budget buffer for later days.
    # If budget is already low, bid what we can.
    if budget <= DAILY_SALARY * 0.4:
        cap = budget
    else:
        cap = budget * 0.6

    bid = max(0.0, min(cap, float(target)))

    # If I'm very safe, reduce slightly to conserve budget.
    if hp >= 8.0 and no_water_days == 0:
        bid = bid * 0.85

    # Ensure we don't bid above budget.
    if bid > budget:
        bid = budget

    return float(bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    # If no opponents alive, bid conservatively.
    if not alive_opps:
        return float(min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids to infer pressure.
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_prev_bid = 0.0
    if len(prev_bids) >= 2:
        sorted_b = sorted(prev_bids, reverse=True)
        second_prev_bid = float(sorted_b[1])

    # Estimate how many days water likely covers.
    # (Not used for indexing; only for sizing.)
    estimated_units = supply / WATER_REQ if WATER_REQ > 0 else 0.0

    # Base strategy: mid-high bid to secure enough water when supply is moderate.
    # React to whether others were bidding aggressively yesterday.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Someone was very aggressive; avoid overpaying but still compete.
        if hp <= 2 or no_water_days >= 2:
            target = max(second_prev_bid + 2.0, DAILY_SALARY * 0.65)
        else:
            target = max(second_prev_bid + 1.0, DAILY_SALARY * 0.55)
    else:
        # Generally not extreme bidding; bid around our share.
        if hp <= 2 or no_water_days >= 2:
            target = max(highest_prev_bid + 1.0, DAILY_SALARY * 0.75)
        else:
            target = max(highest_prev_bid * 0.6 + 10.0, DAILY_SALARY * 0.5)

    # Clamp bid to budget.
    if budget <= 0.0:
        return 0.0

    # Additional safeguard: if we are in danger, bid closer to salary.
    if hp <= 1.0:
        target = max(target, DAILY_SALARY * 0.95)
    elif hp <= 3.0:
        target = max(target, DAILY_SALARY * 0.75)

    # Never bid more than what we can afford.
    bid = float(min(budget, target))

    # If supply is at the low end, slightly increase bid to secure.
    if supply <= 18.0:
        bid = float(min(budget, bid + 5.0))

    # Ensure non-negative.
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    my_hp = int(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Read yesterday's immediate behavior from previous_trace
    prev_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else 0.0

    # Estimate how many water units are likely needed/available.
    # We aim to pay enough to beat the strongest yesterday bidder, but not too high.
    # Supply in [15,25] implies 1-2 units for WATER_REQ=9; higher supply reduces pressure.
    supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    # bid pressure factor: lower supply => bid more
    pressure = 1.0 + (0.5 - supply_norm)  # ranges roughly [0.5,1.5]

    # If our HP is low or we already have no-water days, increase aggressiveness.
    urgency = 1.0
    if my_hp <= 2:
        urgency = 1.35
    elif my_hp <= 4:
        urgency = 1.15

    if my_no_water_days >= 2:
        urgency *= 1.2

    # Base target: slightly above the highest previous bid if it was strong.
    # Otherwise, target around mid to contest.
    strong_prev = highest_prev_bid >= DAILY_SALARY * 0.85

    if strong_prev:
        target = highest_prev_bid + (3.0 * pressure)
    else:
        # If no one was extremely aggressive, contest near the leader but not overpay.
        target = max(DAILY_SALARY * 0.5, second_prev_bid + (5.0 * pressure))

    # Clamp target to reasonable fraction of our budget and salary scale.
    # Avoid spending all budget early.
    max_affordable = my_budget * 0.5 if day <= 5 else my_budget * 0.65
    # Also avoid paying more than a bit above salary unless urgency is high.
    salary_cap = DAILY_SALARY * (1.2 * urgency)

    bid = min(target * urgency, max_affordable, salary_cap)

    # Ensure bid is at least a small contest amount if possible.
    min_contest = DAILY_SALARY * (0.35 if supply_norm > 0.3 else 0.45)
    bid = max(bid, min_contest * (0.8 if my_hp > 5 else 1.0))

    # Final safety clamp
    bid = max(0.0, min(float(bid), my_budget))
    return bid
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

    alive_opps = [o for o in opponents_status.values() if o.get('alive')]
    if not alive_opps:
        return min(my_budget, DAILY_SALARY * 0.4)

    # React to yesterday's immediate pressure
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev_bid

    # Base aggressiveness: ensure we don't fall behind when supply is tight.
    # If supply is near minimum, competition likely higher -> bid more.
    supply_mid = (MIN_SUPPLY + MAX_SUPPLY) / 2.0
    tightness = (supply_mid - supply) / (supply_mid - MIN_SUPPLY + 1e-9)  # positive when supply < mid
    tightness = max(0.0, min(1.0, tightness))

    # If opponents were bidding very high yesterday, they likely expect to win water.
    # We counter with a bid that is competitive but not maxing out.
    high_pressure = 1.0 if highest_prev_bid >= DAILY_SALARY * 0.85 else 0.0

    # If our HP is low or we've already had no water days, we must bid more.
    urgency = 0.0
    if my_hp <= 2.0:
        urgency = 1.0
    elif my_hp <= 4.0:
        urgency = 0.6
    if my_no_water_days >= 2:
        urgency = max(urgency, 0.7)

    # Target bid (heuristic):
    # - When pressure is high, aim around 0.65-0.85 of the high bid level.
    # - Otherwise, aim around 0.45-0.65.
    if high_pressure > 0.0:
        target = (0.7 * highest_prev_bid) + (8.0 * tightness)
    else:
        target = (0.55 * max(second_prev_bid, highest_prev_bid)) + (6.0 * tightness)

    # Apply urgency scaling
    target *= (1.0 + 0.5 * urgency)

    # Clamp to reasonable range relative to our budget
    # (Game likely expects bids not exceeding budget; keep a cap.)
    cap = my_budget
    # Also avoid bidding above a fraction of daily salary unless urgency is high.
    salary_cap = DAILY_SALARY * (0.95 if urgency >= 0.7 else 0.7)
    cap = min(cap, salary_cap)

    # Ensure non-negative
    bid = max(0.0, min(cap, target))

    # Early-day slight increase to secure survival trajectory
    if day <= 3:
        bid = min(cap, bid * 1.08)

    return bid
"""
