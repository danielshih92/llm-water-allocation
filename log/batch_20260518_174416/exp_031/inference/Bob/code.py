# ============================================================
# Experiment: exp_031
# Agent: Bob
# Source: exp_031
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

    supply = day_context['supply']
    day = day_context['day']

    # Determine alive opponents and their yesterday bids
    alive_opponents = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opponents:
        # If alone, bid enough to cover requirement but not waste budget
        target = int(WATER_REQ)
        return max(0, min(int(my_status['budget']), target))

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # If no usable trace, use conservative baseline based on supply
    if not yesterday_bids:
        # Estimate per-agent clearing pressure: aim for requirement if supply is tight
        if supply <= (MIN_SUPPLY + MAX_SUPPLY) / 2:
            base = int(WATER_REQ)
        else:
            base = int(max(0, WATER_REQ - 2))
        # Scale down if low HP
        if my_status['hp'] <= 2:
            base = int(max(0, base - 2))
        return max(0, min(int(my_status['budget']), base))

    highest_prev_bid = max(yesterday_bids)
    second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid

    # Convert supply to an approximate number of full requirements available
    # (use int indices rule by keeping indices out; only arithmetic here)
    # If supply is tight, we need to be more competitive.
    tightness = 0.0
    if supply <= MIN_SUPPLY:
        tightness = 1.0
    elif supply >= MAX_SUPPLY:
        tightness = 0.0
    else:
        tightness = (MAX_SUPPLY - float(supply)) / float(MAX_SUPPLY - MIN_SUPPLY)

    budget = float(my_status['budget'])
    hp = float(my_status['hp'])

    # Strategy:
    # - If opponents were bidding aggressively yesterday, slightly outbid to secure water.
    # - Otherwise, bid near requirement plus a small margin.
    aggressive_threshold = DAILY_SALARY * 0.85

    if highest_prev_bid >= aggressive_threshold:
        # Outbid by a small increment; more if supply is tight, less if we are low HP
        increment = 2.0 + 3.0 * tightness
        if hp <= 2:
            increment = 1.0 + 2.0 * tightness
        desired = highest_prev_bid + increment
    else:
        # Bid around requirement; if another opponent was already near requirement, outbid slightly
        # Use second highest to avoid overreacting to one extreme outlier.
        near_clear = max(WATER_REQ, second_prev_bid)
        desired = float(near_clear) + (1.0 + 2.0 * tightness)
        # If supply is looser, we can bid closer to requirement
        if tightness < 0.4:
            desired = float(WATER_REQ) + 0.5
        if hp <= 2:
            desired = desired - 1.5

    # Cap by budget; also avoid paying far beyond a reasonable upper bound
    # Upper bound: aim to never exceed a fraction of budget unless very aggressive scenario.
    max_reasonable = budget * (0.65 if highest_prev_bid < aggressive_threshold else 0.85)
    bid = min(desired, max_reasonable)

    # Ensure integer bid
    bid_int = int(bid)
    if bid_int < 0:
        bid_int = 0

    # If bid is too low to matter, ensure at least 1 when we have budget and HP is not critical
    if bid_int == 0 and budget >= 1 and hp > 1:
        bid_int = 1

    return min(bid_int, int(budget))
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

    alive_opponents = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    # Read yesterday bids from immediate previous_trace only
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # Baseline target bid
    # If others were paying high yesterday, match a fraction to avoid being outbid.
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # Estimate how aggressive others were
        if highest_prev_bid >= DAILY_SALARY * 1.45:  # ~130+ given DAILY_SALARY=90
            # If our HP is healthy, bid enough to likely secure water.
            if my_hp >= 4 and my_no_water_days <= 1:
                target = highest_prev_bid * 0.85
            else:
                # If we are under pressure, bid closer to their level.
                target = highest_prev_bid * 0.95
        else:
            # Moderate pressure: bid around their average + small premium
            avg_prev = sum(yesterday_bids) / float(len(yesterday_bids))
            target = avg_prev * 0.8 + 5.0
    else:
        # No info: conservative mid bid
        target = DAILY_SALARY * 0.6

    # Adjust for current supply: with higher supply, we can bid slightly less.
    # supply in [15,25]
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_ratio = (supply - float(MIN_SUPPLY)) / float(MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_ratio = 0.5
    supply_ratio = max(0.0, min(1.0, float(supply_ratio)))

    # If supply is low, increase bid; if high, decrease bid.
    # Low supply implies scarcity; increase by up to ~15%.
    scarcity_mult = 1.15 - 0.15 * supply_ratio
    target *= scarcity_mult

    # HP/budget risk management
    # If our HP is very low, prioritize survival.
    if my_hp <= 2:
        target = max(target, DAILY_SALARY * 0.9)
    elif my_hp <= 3:
        target = max(target, DAILY_SALARY * 0.7)

    # If we've already had several no-water days, bid more.
    if my_no_water_days >= 2:
        target *= 1.15

    # Ensure we don't overspend: cap by a fraction of budget.
    # Keep some budget for later days.
    if my_budget <= 0:
        return 0.0

    # Fraction depends on HP
    if my_hp >= 5:
        budget_cap = my_budget * 0.45
    elif my_hp >= 3:
        budget_cap = my_budget * 0.65
    else:
        budget_cap = my_budget * 0.85

    bid = min(float(my_budget), float(budget_cap), float(target))

    # Avoid negative/NaN
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

    supply = day_context['supply']
    day = day_context['day']

    # Alive opponents
    alive_opps = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Yesterday bids from previous_trace
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        if prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Key opponent signals
    # If any opponent died yesterday, they likely underbid under pressure.
    died_yesterday = False
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        if prev:
            hp_after = prev.get('hp_after', None)
            if hp_after is not None and float(hp_after) <= 0:
                died_yesterday = True

    # Use yesterday bid distribution to calibrate
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = (sum(yesterday_bids) / len(yesterday_bids)) if yesterday_bids else 0.0

    # Estimate competition intensity: if Cindy-like bids are high, we need to match.
    # Also, if our no_water_days is high, we must bid more.
    no_water_days = my_status.get('no_water_days', 0)
    my_hp = my_status.get('hp', 0)
    my_budget = my_status.get('budget', 0)

    # Supply-aware urgency: with supply near MIN, competition is higher.
    # Convert to an integer index for safety.
    supply_bucket = int(round((supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) * 10))
    if supply_bucket < 0:
        supply_bucket = 0
    if supply_bucket > 10:
        supply_bucket = 10

    # Base bid: aim to secure water when supply is tight.
    # Use budget fraction rather than absolute, to avoid overspending.
    tight_factor = 0.45 + 0.35 * (supply_bucket / 10.0)  # 0.45..0.80

    # Pressure reaction
    if highest_prev_bid >= DAILY_SALARY * 1.4:  # very aggressive yesterday
        base = DAILY_SALARY * (0.75 + 0.15 * (supply_bucket / 10.0))
    elif highest_prev_bid >= DAILY_SALARY * 0.9:
        base = DAILY_SALARY * (0.60 + 0.20 * (supply_bucket / 10.0))
    else:
        base = DAILY_SALARY * (0.50 + 0.15 * (supply_bucket / 10.0))

    # If someone died yesterday, we can exploit by not overbidding too much,
    # but still ensure we don't get starved.
    if died_yesterday:
        base *= 0.95

    # Urgency from our own HP / starvation
    if my_hp <= 2 or no_water_days >= 2:
        base *= 1.25
    elif my_hp <= 3 or no_water_days >= 1:
        base *= 1.10

    # Convert to final bid with budget cap
    bid = min(my_budget, base * tight_factor)

    # Ensure we bid at least a small amount if budget allows, to avoid being shut out.
    min_bid = min(my_budget, DAILY_SALARY * 0.25)
    if bid < min_bid:
        bid = min_bid

    # Never bid negative
    if bid < 0:
        bid = 0

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

    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for opp_id, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((opp_id, o))

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday traces for immediate pressure
    yesterday_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = 0.0
    if len(yesterday_bids) >= 2:
        sorted_b = sorted(yesterday_bids)
        second_prev_bid = sorted_b[-2]

    # Supply pressure: higher supply means cheaper to secure water; lower supply means we must be competitive.
    # Normalize supply within [MIN_SUPPLY, MAX_SUPPLY].
    if MAX_SUPPLY > MIN_SUPPLY:
        s_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        s_norm = 0.5
    if s_norm < 0.0:
        s_norm = 0.0
    if s_norm > 1.0:
        s_norm = 1.0

    # Base aggressiveness from yesterday: Cindy-like high bids suggest competition; Eric-like moderate bids suggest we can hover.
    # Target: slightly above the likely clearing price but not near Cindy's extreme unless needed.
    # Use highest_prev_bid as a ceiling signal.
    if highest_prev_bid >= DAILY_SALARY * 1.15:
        # Someone was willing to spend a lot; we avoid full matching unless our hp is critical.
        base = DAILY_SALARY * (0.55 + 0.25 * (1.0 - s_norm))
        if hp <= 2 or no_water_days >= 2:
            base = DAILY_SALARY * 0.85
    elif highest_prev_bid >= DAILY_SALARY * 0.70:
        base = DAILY_SALARY * (0.50 + 0.15 * (1.0 - s_norm))
        if hp <= 2 or no_water_days >= 2:
            base = DAILY_SALARY * 0.75
    else:
        base = DAILY_SALARY * (0.45 + 0.20 * (1.0 - s_norm))
        if hp <= 2 or no_water_days >= 2:
            base = DAILY_SALARY * 0.70

    # If supply is high, reduce bid; if low, increase.
    # Additionally, if yesterday's highest bid was moderate, try to beat around that level.
    if supply >= 21.0:
        base *= 0.85
    elif supply <= 17.0:
        base *= 1.10

    # If we can afford to slightly overtake yesterday's high bid, do so; else stay near base.
    # This captures Cindy/Eric behavior: Cindy likely overbids, but we only need to beat the marginal.
    target = base
    if highest_prev_bid > 0.0:
        # Aim for just above the second-highest when known, otherwise above base.
        if second_prev_bid > 0.0:
            target = max(target, second_prev_bid + 1.5)
        else:
            target = max(target, highest_prev_bid * 0.85)

    # Critical survival: if hp is very low, spend aggressively.
    if hp <= 1:
        target = max(target, DAILY_SALARY * 0.95)
    elif hp <= 2:
        target = max(target, DAILY_SALARY * 0.80)

    # Budget cap
    target = min(target, budget)

    # If budget is too small, bid whatever we can.
    if target <= 0.0:
        return 0.0

    # Keep bids within reasonable bounds relative to daily salary.
    max_reasonable = DAILY_SALARY * 1.25
    if target > max_reasonable:
        target = max_reasonable

    return float(target)
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

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        # If no opponents, just bid conservatively to preserve budget.
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace only.
    yesterday_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Estimate how aggressive the pool is.
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / float(len(yesterday_bids))
    else:
        highest_prev_bid = 0.0
        avg_prev_bid = 0.0

    # Risk-based scaling: if I'm low HP or already have no-water days, bid more.
    # Also incorporate supply: when supply is tighter, increase bid.
    supply_tightness = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_tightness = (float(MAX_SUPPLY) - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
        if supply_tightness < 0.0:
            supply_tightness = 0.0
        if supply_tightness > 1.0:
            supply_tightness = 1.0

    # Base target bid anchored to yesterday aggression.
    # Cindy/David were high; avoid matching the very top unless my situation is critical.
    base = max(DAILY_SALARY * 0.45, avg_prev_bid * 0.75)

    # Pressure adjustment from highest yesterday bid.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        base = max(base, DAILY_SALARY * 0.6)

    # If I'm in danger, bid closer to the high-pressure level.
    danger = 0
    if my_hp <= 2.0:
        danger = 2
    elif my_hp <= 4.0:
        danger = 1

    if my_no_water_days >= 2:
        danger = max(danger, 1)

    if danger == 0:
        mult = 0.85 + 0.25 * supply_tightness
    elif danger == 1:
        mult = 1.05 + 0.35 * supply_tightness
    else:
        mult = 1.25 + 0.45 * supply_tightness

    bid = base * mult

    # Cap bid to budget and keep reasonable upper bound.
    bid = max(0.0, min(bid, my_budget))

    # If budget is too low to matter, still bid what we can (but not negative).
    if my_budget <= 1e-9:
        return 0.0

    # Small epsilon to avoid bidding exactly zero when competing.
    if bid <= 0.0 and my_budget > 0.0:
        bid = min(my_budget, DAILY_SALARY * 0.05)

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

    # React to yesterday's bidding pressure: focus on highest previous bid among alive opponents.
    prev_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                prev_bids.append(float(bid))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Supply pressure: if supply is near max, we can afford lower bid; if near min, raise bid.
    # Normalize to [0,1] where 0 => MIN_SUPPLY, 1 => MAX_SUPPLY
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_norm = 0.5
    supply_norm = max(0.0, min(1.0, supply_norm))

    # Baseline aggressiveness: Cindy bid ~124 avg and survived; match slightly below her typical pressure.
    # If highest_prev_bid was very high, increase bid; otherwise keep moderate.
    if highest_prev_bid >= DAILY_SALARY * 1.25:  # ~112.5
        base = DAILY_SALARY * 0.75
    elif highest_prev_bid >= DAILY_SALARY * 0.85:  # ~76.5
        base = DAILY_SALARY * 0.65
    else:
        base = DAILY_SALARY * 0.55

    # Adjust for my urgency.
    if my_hp <= 2:
        urgency = 1.35
    elif my_hp <= 4:
        urgency = 1.15
    else:
        urgency = 1.00

    if my_no_water_days >= 2:
        urgency *= 1.15

    # If supply is low, increase bid; if high, decrease.
    supply_factor = 0.95 + (1.0 - supply_norm) * 0.25  # low supply => up to ~1.2

    target_bid = base * urgency * supply_factor

    # Cap by budget and keep some reserve for later days.
    # Reserve more when HP is healthy.
    if my_hp >= 6:
        reserve_frac = 0.25
    elif my_hp >= 3:
        reserve_frac = 0.15
    else:
        reserve_frac = 0.05

    max_affordable = my_budget * (1.0 - reserve_frac)
    target_bid = min(target_bid, max_affordable)

    # Ensure non-negative and at least a minimal bid when budget allows.
    if target_bid < 0:
        target_bid = 0.0

    # If budget is extremely low, bid what you can.
    if my_budget <= 10:
        return min(my_budget, DAILY_SALARY * 0.2)

    # Final clamp to a reasonable range relative to DAILY_SALARY.
    lower = DAILY_SALARY * 0.25
    upper = DAILY_SALARY * 0.95
    target_bid = max(lower, min(upper, target_bid))

    return min(my_budget, target_bid)
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

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    if not alive_opponents:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids to infer aggressiveness
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

    # Baseline aggressiveness from yesterday
    baseline = 0.0
    if prev_bids:
        baseline = max(prev_bids)

    # Supply pressure: higher supply means less need to overbid; lower supply means more urgency
    # Normalize supply to [0,1]
    if MAX_SUPPLY <= MIN_SUPPLY:
        supply_norm = 0.5
    else:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
        if supply_norm < 0.0:
            supply_norm = 0.0
        if supply_norm > 1.0:
            supply_norm = 1.0

    # Urgency based on our HP and consecutive no-water days
    # If low HP or already missing water, bid more.
    urgency = 0.0
    if hp <= 2.0:
        urgency = 1.0
    elif hp <= 4.0:
        urgency = 0.7
    elif hp <= 6.0:
        urgency = 0.45
    else:
        urgency = 0.25

    if no_water_days >= 2:
        urgency = max(urgency, 0.85)
    elif no_water_days == 1:
        urgency = max(urgency, 0.55)

    # Target bid: slightly below yesterday's max pressure when we can afford to save budget.
    # If our urgency is high, we pay closer to baseline.
    # Use a small undercut to beat typical overbidders.
    undercut = 3.0 + (1.0 - supply_norm) * 2.0  # more undercut when supply is higher

    # Desired fraction of baseline
    if baseline > 0.0:
        if urgency >= 0.85:
            target = baseline - 1.0
        elif urgency >= 0.55:
            target = baseline - undercut * 0.6
        else:
            target = baseline - undercut
    else:
        # Fallback: bid around a moderate level
        target = DAILY_SALARY * (0.45 + 0.35 * urgency - 0.15 * supply_norm)

    # Convert target into a cap tied to our budget and a safety reserve.
    # If budget is low, don't overspend.
    # Reserve more when hp is healthy.
    reserve_frac = 0.15 if hp <= 3.0 else 0.35
    max_affordable = max(0.0, budget * (1.0 - reserve_frac))

    # Also cap by a reasonable fraction of daily salary to avoid runaway bids.
    # When urgency is high, allow higher bids.
    salary_cap = DAILY_SALARY * (0.85 if urgency >= 0.85 else (0.65 if urgency >= 0.55 else 0.55))

    bid = min(target, max_affordable, salary_cap, budget)

    # Ensure non-negative
    if bid < 0.0:
        bid = 0.0

    # If supply is very low, push up a bit to secure water
    if supply < (MIN_SUPPLY + 1.0):
        bid = max(bid, DAILY_SALARY * (0.55 + 0.25 * urgency))
        bid = min(bid, max_affordable, salary_cap, budget)

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

    # Safety caps
    budget = float(my_status['budget'])
    hp = float(my_status['hp'])

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        # If alone, try to secure enough water for survival
        target = DAILY_SALARY * 0.35
        if budget <= 0:
            return 0.0
        return float(min(budget, target))

    # Read yesterday bids from previous_trace only
    prev_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Determine aggressiveness from yesterday pressure
    # If someone was bidding near/above salary, expect aggressive competition today.
    aggressive_market = highest_prev_bid >= DAILY_SALARY * 0.85

    # Supply-based scaling: when supply is low, competition for water should be higher.
    # Normalize supply to [0,1]
    if MAX_SUPPLY <= MIN_SUPPLY:
        supply_norm = 0.5
    else:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_norm = max(0.0, min(1.0, supply_norm))

    # Base bid: aim to win a meaningful share without overspending.
    # When supply is scarce (low supply_norm), bid a bit more.
    scarcity_factor = 1.15 - 0.3 * supply_norm  # ~1.15 at MIN, ~0.85 at MAX

    # HP-based urgency
    if hp <= 2:
        hp_factor = 1.25
    elif hp <= 4:
        hp_factor = 1.10
    else:
        hp_factor = 0.95

    # If market is aggressive, increase bid modestly; otherwise keep it controlled.
    if aggressive_market:
        market_factor = 1.15
    else:
        market_factor = 0.95

    # Compute target bid
    target_bid = DAILY_SALARY * 0.55 * scarcity_factor * hp_factor * market_factor

    # If we know Cindy survived with very high bids yesterday, slightly bias upward
    # when her previous bid was extremely high.
    for opp_id, opp in alive_opps:
        if opp_id == 'Cindy':
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    c_bid = float(prev['bid'])
                    if c_bid >= DAILY_SALARY * 1.4:
                        target_bid *= 1.08
                except Exception:
                    pass

    # Also, if highest previous bid was not too far above our target, try to be competitive.
    # Keep within budget.
    if highest_prev_bid > 0:
        # Try to sit just above a fraction of the leader's bid, but not exceed aggressive cap.
        competitiveness = min(1.0, (highest_prev_bid / (DAILY_SALARY * 1.6)))
        target_bid = max(target_bid, highest_prev_bid * (0.65 + 0.2 * competitiveness))

    # Final constraints
    if budget <= 0:
        return 0.0

    # Never bid above budget; also avoid bidding more than a small multiple of salary
    # to prevent bankruptcy in competitive rounds.
    max_reasonable = DAILY_SALARY * 1.2
    bid = float(min(budget, max_reasonable, target_bid))

    # If we are extremely low on budget, bid what we can.
    if bid < 1e-9:
        bid = float(min(budget, DAILY_SALARY * 0.2))

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
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append((oid, o))

    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday bids from previous_trace only
    prev_bids = []
    prev_pressured = 0
    for oid, o in alive_opponents:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                bval = float(b)
                prev_bids.append(bval)
                if bval >= DAILY_SALARY * 0.85:
                    prev_pressured += 1
            except Exception:
                pass

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    # Supply pressure: lower supply => bid higher to secure water
    # Normalize supply into [0,1] where 0=MIN_SUPPLY, 1=MAX_SUPPLY
    if MAX_SUPPLY > MIN_SUPPLY:
        s_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        s_norm = 0.5
    s_norm = max(0.0, min(1.0, float(s_norm)))
    scarcity_factor = 1.0 - s_norm  # 1 near MIN_SUPPLY, 0 near MAX_SUPPLY

    # HP urgency
    if hp <= 1.5 or no_water_days >= 2:
        hp_factor = 1.0
    elif hp <= 3.5:
        hp_factor = 0.75
    else:
        hp_factor = 0.55

    # If someone bid extremely high yesterday, we match partially rather than full-commit
    # to avoid overpaying while still contesting.
    if highest_prev >= DAILY_SALARY * 0.85:
        base = DAILY_SALARY * (0.45 + 0.35 * scarcity_factor)
        # Increase slightly with number of pressured opponents
        base *= (1.0 + 0.08 * min(prev_pressured, 3))
    else:
        # Otherwise, anchor around average/low-mid
        anchor = avg_prev if avg_prev > 0 else DAILY_SALARY * 0.5
        base = max(DAILY_SALARY * 0.35, min(DAILY_SALARY * 0.7, 0.6 * anchor + 0.4 * (DAILY_SALARY * 0.5)))
        base *= (0.9 + 0.25 * scarcity_factor)

    bid = base * hp_factor

    # Cap bid to budget and keep some reserve
    # Reserve more when hp is healthy
    if hp > 4.0:
        reserve_frac = 0.25
    else:
        reserve_frac = 0.1
    max_affordable = max(0.0, budget * (1.0 - reserve_frac))

    # Also avoid bidding above a reasonable ceiling relative to DAILY_SALARY
    ceiling = DAILY_SALARY * (0.95 if hp_factor >= 0.9 else 0.8)
    bid = min(bid, ceiling, max_affordable)

    # Minimum meaningful bid
    min_bid = DAILY_SALARY * (0.25 + 0.25 * scarcity_factor)
    if bid < min_bid:
        # Only force a min bid if we can afford it and hp is not critical
        if budget > min_bid * 1.05 and hp > 2.0:
            bid = min(bid, max_affordable)
            bid = max(bid, min_bid)
        else:
            bid = min(budget, bid)

    # Final clamp
    bid = max(0.0, float(bid))
    bid = min(bid, budget)
    return bid
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

    # Determine how many full water units supply can support
    # (Used only for scaling; avoid float indices.)
    max_units = int(supply // WATER_REQ) if WATER_REQ > 0 else 0
    if max_units < 1:
        max_units = 1

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    # If no opponents are alive, bid conservatively
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace
    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    # Pressure estimate: if someone bid very high yesterday, expect continued contest.
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = 0.0
    if len(yesterday_bids) >= 2:
        sorted_b = sorted(yesterday_bids, reverse=True)
        second_prev_bid = sorted_b[1]

    # Supply tightness: lower supply => higher chance of bidding wars.
    # Normalize to [0,1] where 1 means tight.
    tightness = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        tightness = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)
    if tightness < 0.0:
        tightness = 0.0
    if tightness > 1.0:
        tightness = 1.0

    # Core strategy: undercut the highest bidder unless my HP is critical.
    # Target bid is slightly below (highest - margin), but not too low.
    # Margin increases with tightness.
    margin = 5.0 + 10.0 * tightness

    # Baseline bid levels
    if hp <= 2.0:
        # Critical: secure water even if it costs more
        target = max(DAILY_SALARY * 0.9, highest_prev_bid - 2.0)
    elif hp <= 4.0:
        # Medium urgency
        target = max(DAILY_SALARY * (0.65 + 0.1 * tightness), highest_prev_bid - margin)
    else:
        # Low urgency: conserve budget; still contest when others were aggressive
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            target = max(DAILY_SALARY * (0.55 + 0.15 * tightness), highest_prev_bid - margin)
        else:
            target = max(DAILY_SALARY * (0.5 + 0.1 * tightness), second_prev_bid + 1.0)

    # Ensure we don't overspend beyond budget; also keep within reasonable range
    # to avoid going broke early.
    # Since bids are simultaneous, aim for a mid/high probability win.
    max_reasonable = DAILY_SALARY * (1.2 + 0.3 * tightness)
    target = min(target, max_reasonable)

    # Final clamp to budget
    if budget <= 0.0:
        return 0.0

    bid = float(min(budget, target))

    # If budget is too low, bid what we can.
    # If hp is high, allow low bid to preserve budget.
    if bid < 1.0:
        bid = float(min(budget, DAILY_SALARY * 0.2))

    return float(bid)
"""
