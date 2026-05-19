# ============================================================
# Experiment: exp_062
# Agent: Bob
# Source: exp_062
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
    day = day_context.get('day', 0)

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp and opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    # Base cap: never bid more than we can afford.
    max_affordable_bid = max(0.0, budget)

    # If no opponents alive, conserve budget.
    if not alive_opponents:
        target = DAILY_SALARY * 0.35
        return min(max_affordable_bid, target)

    # Read yesterday bids to infer pressure.
    prev_bids = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # If we have no trace info, fall back to a conservative strategy.
    if not prev_bids:
        if hp <= 2 or no_water_days >= 2:
            target = DAILY_SALARY * 0.8
        else:
            target = DAILY_SALARY * 0.55
        return min(max_affordable_bid, target)

    highest_prev_bid = max(prev_bids)

    # Thresholds tuned to the example style: counter aggressively when others were near salary.
    high_pressure = DAILY_SALARY * 0.85
    mid_pressure = DAILY_SALARY * 0.60

    # Determine desired bid based on our condition.
    urgent = (hp <= 2) or (no_water_days >= 2)
    somewhat_urgent = (hp <= 3) or (no_water_days >= 1)

    # Also incorporate supply: if supply is tight, increase bids to secure allocation.
    # Use a safe discretization for indices.
    supply_bucket = int(max(0.0, min(1.0, (supply - float(MIN_SUPPLY)) / float(MAX_SUPPLY - MIN_SUPPLY + 1e-9))))
    tight_multiplier = [0.95, 1.10][supply_bucket]

    if highest_prev_bid >= high_pressure:
        # Opponents were very aggressive yesterday; counter to prevent losing water.
        if urgent:
            target = DAILY_SALARY * 0.95
        elif somewhat_urgent:
            target = DAILY_SALARY * 0.75
        else:
            target = DAILY_SALARY * 0.35
        target *= tight_multiplier
    elif highest_prev_bid >= mid_pressure:
        # Moderate aggression: match partially and adjust for our urgency.
        if urgent:
            target = max(highest_prev_bid + 1.0, DAILY_SALARY * 0.7)
        elif somewhat_urgent:
            target = max(highest_prev_bid * 0.9, DAILY_SALARY * 0.6)
        else:
            target = max(highest_prev_bid * 0.6, DAILY_SALARY * 0.5)
        target *= tight_multiplier
    else:
        # Low aggression: we can bid just enough to secure water; still scale with urgency.
        if urgent:
            target = DAILY_SALARY * 0.85
        elif somewhat_urgent:
            target = DAILY_SALARY * 0.65
        else:
            # Try to stay efficient: bid near a fraction of salary.
            target = DAILY_SALARY * 0.52
        # If supply is very high, slightly reduce.
        if supply >= float(MIN_SUPPLY) + (float(MAX_SUPPLY) - float(MIN_SUPPLY)) * 0.7:
            target *= 0.92
        target *= tight_multiplier

    # Ensure bid is at least a minimal positive amount when we need water.
    # Also avoid bidding negative.
    target = max(0.0, float(target))

    # If our hp is critically low, don't conserve.
    if hp <= 1:
        target = max(target, DAILY_SALARY * 0.95)

    return min(max_affordable_bid, target)
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

    # Identify alive opponents
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Extract yesterday bids
    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict) and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # Baseline: if low HP, bid to secure water
    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))

    # Contest level inferred from yesterday
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Medium scenario supply: if enough supply, expect Cindy to keep bidding high.
    # Use a small overbid to beat the highest likely bidder.
    if supply >= 19.0:
        # If opponent already showed willingness to pay near ~DAILY_SALARY*1.25, match/overbid slightly.
        target = highest_prev_bid + 2.0
        # Cap to avoid bankrupting
        if hp <= 2.0:
            cap = DAILY_SALARY * 0.95
        else:
            cap = DAILY_SALARY * 0.75
        bid = min(budget, min(target, cap))
        # Ensure non-trivial bid
        if bid < DAILY_SALARY * 0.45:
            bid = min(budget, DAILY_SALARY * 0.55)
        return float(bid)

    # Lower supply: avoid bidding into a price war unless critical HP
    if hp <= 2.0:
        return float(min(budget, DAILY_SALARY * 0.9))

    # Otherwise bid around a mid-tier, slightly below yesterday contest
    if highest_prev_bid > 0.0:
        bid = min(budget, max(DAILY_SALARY * 0.5, highest_prev_bid * 0.8))
    else:
        bid = min(budget, DAILY_SALARY * 0.55)

    # Keep within reasonable range for this scenario
    if bid > DAILY_SALARY * 0.7:
        bid = DAILY_SALARY * 0.7
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

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    # Collect alive opponents and their yesterday bids
    alive_opponents = []
    for opp_id, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append((opp_id, o))

    if not alive_opponents:
        # No one else to compete with
        return max(0.0, min(my_status.get('budget', 0.0), DAILY_SALARY * 0.4))

    yesterday_bids = []
    yesterday_high_pressure = False
    max_prev_bid = None
    for _, o in alive_opponents:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                b_val = float(b)
            except Exception:
                continue
            yesterday_bids.append(b_val)
            if max_prev_bid is None or b_val > max_prev_bid:
                max_prev_bid = b_val

    if max_prev_bid is None:
        # Fallback
        base = DAILY_SALARY * 0.55
        return max(0.0, min(my_status.get('budget', 0.0), base))

    # Determine supply pressure: higher supply reduces need to outbid
    # Use int() to safely index if needed; here just compute thresholds.
    supply_f = float(supply)
    supply_ratio = (supply_f - float(MIN_SUPPLY)) / max(1e-9, (float(MAX_SUPPLY) - float(MIN_SUPPLY)))
    # supply_ratio in [0,1] ideally
    if supply_ratio < 0.0:
        supply_ratio = 0.0
    if supply_ratio > 1.0:
        supply_ratio = 1.0

    # Yesterday aggression signal: if someone bid near the top, others likely follow
    # Yesterday meta shows max around ~121; treat >= 105 as high pressure.
    if max_prev_bid >= DAILY_SALARY * 1.15:  # 103.5
        yesterday_high_pressure = True

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0) or 0)

    # Core strategy:
    # - If my hp is low or I have multiple no-water days, bid to secure water.
    # - Otherwise, bid moderately below the highest observed bid to avoid budget burn.
    # - Adjust down when supply is high.

    # Target bid levels
    if my_hp <= 2.0 or no_water_days >= 2:
        # Emergency: be competitive but not maximal
        if yesterday_high_pressure:
            target = max_prev_bid * 0.78
        else:
            target = max_prev_bid * 0.65
        # Ensure at least a meaningful fraction of salary
        target = max(target, DAILY_SALARY * 0.7)
    else:
        if yesterday_high_pressure:
            # Compete but undercut
            target = max_prev_bid * (0.55 + 0.15 * (1.0 - supply_ratio))
            target = max(target, DAILY_SALARY * 0.45)
        else:
            # If yesterday bids were not extreme, stay lower
            target = DAILY_SALARY * (0.48 + 0.12 * (1.0 - supply_ratio))
            # If we have any evidence of bids, anchor slightly above median
            if yesterday_bids:
                sorted_b = sorted(yesterday_bids)
                mid = sorted_b[int(len(sorted_b) / 2)] if len(sorted_b) > 0 else None
                if mid is not None:
                    target = max(target, mid * 0.6)

    # Convert to final bid with budget cap
    # Also avoid bidding above what we can pay.
    bid = min(my_budget, float(target))

    # If budget is extremely low, still bid something if possible
    if bid < 0.0:
        bid = 0.0

    # Keep bid within a reasonable upper bound relative to salary to reduce risk
    upper = DAILY_SALARY * 1.35
    if bid > upper:
        bid = upper

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

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    if not alive_opponents:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids to infer the competitive band.
    prev_bids = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Base target bid from yesterday's surviving behavior.
    # Alex ~87-88 and Eric ~107 were the main survivors; aim just above typical pressure.
    if prev_bids:
        prev_max = max(prev_bids)
        prev_med = sorted(prev_bids)[len(prev_bids)//2]
    else:
        prev_max = 0.0
        prev_med = 0.0

    # Supply pressure: with higher supply, we can afford slightly lower bids.
    # Ensure indices are safe by using int() only when indexing; here none.
    supply_ratio = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Urgency: if we're close to running out of water, bid more.
    urgency = 0
    if my_no_water_days >= 2:
        urgency = 2
    elif my_no_water_days == 1:
        urgency = 1

    # Determine desired bid.
    # If yesterday had high bids (>= ~0.85*salary), push up; else hover around median + small premium.
    high_pressure = (prev_max >= DAILY_SALARY * 0.85)

    if high_pressure:
        target = prev_med + 10.0
        if my_hp <= 2 or urgency >= 2:
            target = max(target, DAILY_SALARY * 0.95)
        elif my_hp <= 3:
            target = max(target, DAILY_SALARY * 0.75)
    else:
        # Typical band: ~88-107. Bid slightly above median to steal allocations.
        target = prev_med + 6.0
        # If supply is low, increase slightly.
        if supply_ratio < 0.5:
            target += 6.0
        # If I'm healthy and supply is ample, don't overspend.
        if my_hp >= 7 and supply_ratio > 0.7:
            target = min(target, DAILY_SALARY * 0.6)
        if my_hp <= 2 or urgency >= 2:
            target = max(target, DAILY_SALARY * 0.9)

    # Clamp by budget and a reasonable fraction of salary.
    # Keep some budget for later days.
    max_allow = my_budget
    # If late in episode, be more aggressive.
    if day >= 7:
        max_allow = min(max_allow, my_budget)  # no extra cap
    else:
        max_allow = min(max_allow, DAILY_SALARY * 1.2)

    bid = max(0.0, min(float(target), float(max_allow)))

    # If budget is too small, still bid something minimal but nonzero if we need water soon.
    if bid <= 0.0 and (my_no_water_days >= 1 or my_hp <= 3):
        bid = min(my_budget, DAILY_SALARY * 0.2)

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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append(o)

    # Base bid: keep enough budget for future days.
    # If low HP or already in no-water streak, bid more.
    urgency = 0.0
    if hp <= 2.0:
        urgency += 0.7
    elif hp <= 4.0:
        urgency += 0.4
    if no_water_days >= 2:
        urgency += 0.35
    if no_water_days >= 4:
        urgency += 0.35

    # Use yesterday's bids to infer aggressiveness.
    prev_bids = []
    for o in alive_opponents:
        prev = o.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    prev_bids.append(float(b))
                except Exception:
                    pass

    if prev_bids:
        highest_prev_bid = max(prev_bids)
        avg_prev_bid = sum(prev_bids) / float(len(prev_bids))
    else:
        highest_prev_bid = 0.0
        avg_prev_bid = 0.0

    # Supply pressure: higher supply means less competition; lower supply means more.
    # Normalize between MIN_SUPPLY and MAX_SUPPLY.
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (supply - float(MIN_SUPPLY)) / (float(MAX_SUPPLY) - float(MIN_SUPPLY))
    else:
        supply_norm = 0.5
    supply_norm = max(0.0, min(1.0, supply_norm))

    # Target bid level.
    # If others were aggressive (high highest_prev_bid), lean upward but cap.
    aggressive_factor = 0.0
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        aggressive_factor = 0.35
    elif highest_prev_bid >= DAILY_SALARY * 0.6:
        aggressive_factor = 0.2
    elif highest_prev_bid >= DAILY_SALARY * 0.35:
        aggressive_factor = 0.1

    # When supply is low, increase bid; when supply is high, decrease.
    scarcity_factor = (1.0 - supply_norm)  # 1 when supply is MIN, 0 when MAX

    # Compose final desired multiplier.
    desired_multiplier = 0.45 + aggressive_factor + urgency + 0.25 * scarcity_factor

    # If we are already in danger, push closer to salary.
    if urgency >= 0.7:
        desired_multiplier += 0.25

    # Convert to bid.
    bid = DAILY_SALARY * desired_multiplier

    # If yesterday bids were extremely high, add a small increment to beat them.
    if highest_prev_bid > 0.0:
        if highest_prev_bid >= DAILY_SALARY * 0.9:
            bid = max(bid, highest_prev_bid * 0.9)
        elif highest_prev_bid >= DAILY_SALARY * 0.6:
            bid = max(bid, min(DAILY_SALARY, highest_prev_bid * 0.75))

    # Ensure we don't overspend; also avoid bidding too low.
    bid = max(0.0, bid)

    # Minimum bid to contest when alive opponents exist.
    if alive_opponents:
        min_contest = DAILY_SALARY * (0.25 + 0.25 * urgency + 0.15 * scarcity_factor)
    else:
        min_contest = DAILY_SALARY * 0.35

    bid = max(bid, min_contest)

    # Hard cap by budget.
    bid = min(bid, budget)

    # If budget is tiny, bid what's left.
    if bid <= 0.0 and budget > 0.0:
        bid = float(budget)

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
    day = day_context['day']

    # Alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive'):
            alive_opps.append((oid, o))

    # If no opponents, bid minimal to survive
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace
    yesterday_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid')
            if b is not None:
                try:
                    yesterday_bids.append(float(b))
                except Exception:
                    pass

    # Estimate how many water units are likely available today
    # supply is total supply; each unit requires WATER_REQ
    # Use int() for any indexing (none here), but keep careful with floats.
    est_units = int(supply / float(WATER_REQ))
    if est_units < 1:
        est_units = 1

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    # Determine pressure from yesterday: if someone bid very high, raise bid.
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = sum(yesterday_bids) / float(len(yesterday_bids)) if yesterday_bids else 0.0

    # Baseline bid: target slightly above lower survivable cluster.
    # Use supply to scale: higher supply -> lower competition -> lower bid.
    supply_mid = (MIN_SUPPLY + MAX_SUPPLY) / 2.0
    supply_scale = (supply_mid / max(supply, 1.0))

    # If I am in danger, bid more aggressively.
    if hp <= 2.0 or my_status.get('no_water_days', 0) >= 2:
        base = DAILY_SALARY * 0.75
    elif hp <= 4.0:
        base = DAILY_SALARY * 0.62
    else:
        base = DAILY_SALARY * 0.52

    # Adjust with yesterday pressure.
    # If highest yesterday bid was high, match a fraction of it.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        base = max(base, min(DAILY_SALARY * 0.95, highest_prev_bid * 0.65))
    else:
        # If bids were moderate, aim near avg but slightly higher to beat low bidders.
        base = max(base, min(DAILY_SALARY * 0.7, avg_prev_bid * 1.05))

    # Supply scaling and unit pressure: fewer units => higher bid.
    unit_pressure = 1.0
    if est_units <= 1:
        unit_pressure = 1.15
    elif est_units == 2:
        unit_pressure = 1.05
    else:
        unit_pressure = 0.95

    bid = base * supply_scale * unit_pressure

    # Cap and floor to keep within budget and avoid overbidding.
    # Also ensure bid is not trivially low when my HP is healthy.
    min_reasonable = DAILY_SALARY * 0.35 if hp > 4.0 else DAILY_SALARY * 0.55
    bid = max(bid, min_reasonable)
    bid = min(bid, budget)

    # If budget is too low, spend what we can.
    if bid <= 0.0:
        return 0.0

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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Alive opponents
    alive = []
    for k, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((k, o))

    # If no one alive, conserve budget
    if not alive:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace only
    cindy_bid = None
    other_bids = []
    for agent_id, o in alive:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            b = float(prev.get('bid'))
            if agent_id == 'Cindy':
                cindy_bid = b
            else:
                other_bids.append(b)

    # Determine pressure level from Cindy (dominant survivor)
    pressure = 0.0
    if cindy_bid is not None:
        pressure = cindy_bid
    elif other_bids:
        pressure = max(other_bids)

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    # Supply-based aggressiveness: medium scenario implies contesting at moderate-high supply.
    # Map supply to a multiplier in [0.9, 1.2]
    if MAX_SUPPLY == MIN_SUPPLY:
        supply_mult = 1.0
    else:
        t = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
        supply_mult = 0.9 + 0.3 * t

    # If Cindy bid extremely high yesterday, match her tier but slightly under to avoid overspending.
    # If Cindy bid low/unknown, use a baseline that targets survival.
    if cindy_bid is not None:
        if cindy_bid >= 120.0:
            base = 0.78 * cindy_bid
        elif cindy_bid >= 80.0:
            base = 0.65 * cindy_bid
        else:
            base = 0.55 * cindy_bid
    else:
        # No Cindy info: use others' max as proxy
        if other_bids:
            mx = max(other_bids)
            base = 0.6 * mx
        else:
            base = DAILY_SALARY * 0.55

    # Survival urgency adjustment
    if hp <= 2.0:
        base *= 1.25
    elif hp <= 4.0:
        base *= 1.10
    else:
        base *= 1.00

    # Apply supply multiplier
    base *= supply_mult

    # Cap by budget and also avoid going above a reasonable fraction of budget
    # (prevents bankrupting if contest is lost)
    safe_cap = budget

    # If budget is low, bid proportionally higher to secure at least one unit of water
    if budget <= DAILY_SALARY * 0.5:
        base = max(base, DAILY_SALARY * 0.35)

    bid = float(min(safe_cap, base))

    # Ensure non-negative
    if bid < 0.0:
        bid = 0.0

    # Also avoid bidding trivially low when supply is ample
    if supply >= 20.0 and bid < DAILY_SALARY * 0.25:
        bid = float(min(safe_cap, DAILY_SALARY * 0.25))

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
    day = int(day_context.get('day', 0))

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    # Base survival urgency
    if hp <= 2 or no_water_days >= 2:
        urgency = 0.82
    elif hp <= 4:
        urgency = 0.68
    else:
        urgency = 0.58

    # React to yesterday's bids from alive opponents
    prev_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Compute a target bid band from yesterday
    target = None
    if prev_bids:
        # Approximate the opponent's typical “alive” bid band (Alex/Eric)
        # and “risky” lower band (David/Cindy).
        avg_bid = sum(prev_bids) / float(len(prev_bids))
        max_prev = max(prev_bids)
        # If someone bid high yesterday, they likely expect contention today.
        if max_prev >= DAILY_SALARY * 1.25:  # ~112.5
            # Slightly undercut to capture allocation if others overpay.
            target = min(DAILY_SALARY * 1.22, max(DAILY_SALARY * 0.95, avg_bid - 6.0))
        else:
            # If nobody was extreme, we can bid closer to the mid/high but not top.
            target = max(DAILY_SALARY * 0.85, avg_bid - 4.0)

    # Supply tightness adjustment: lower supply => higher chance others compete
    # Use a simple normalized factor.
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_t = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_t = 0.5
    # When supply is tight (low supply_t), increase bid slightly.
    tightness_boost = (1.0 - float(supply_t)) * 0.12

    if target is None:
        target = DAILY_SALARY * urgency
    else:
        target = target * (0.92 + tightness_boost)

    # Hard caps to avoid overspending: keep within budget and avoid bidding above a reasonable threshold.
    # If budget is low, bid proportionally.
    if budget <= 0:
        return 0.0

    # Convert target to a safe bid: at most 1.35*salary and at most 90% of budget.
    cap = min(budget, DAILY_SALARY * 1.35)
    bid = min(cap, target, budget * 0.9)

    # Ensure non-negative and keep at least a small amount if we must fight for survival.
    if bid < 0.0:
        bid = 0.0
    if bid == 0.0 and (hp <= 3 or no_water_days >= 2):
        bid = min(budget, DAILY_SALARY * 0.4)

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

    # Alive opponents and their yesterday bids (only immediate reaction)
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # If no one is alive, conserve budget
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    yesterday_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Estimate how competitive the market was
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Core idea: Cindy/Eric were willing to pay ~160+ to survive; avoid that unless we are in danger.
    # Use supply to adjust aggressiveness: higher supply reduces the need to overbid.
    # Target: bid enough to beat low/medium bidders, but not chase 160+ unless my hp is critical.
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    # Danger thresholds
    critical = 2.0
    low_hp = 4.0

    # Base bid policy by supply
    # When supply is lower, competition is likely higher -> bid more.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if (MAX_SUPPLY - MIN_SUPPLY) != 0 else 0.5
    # supply_ratio in [0,1]; lower supply => smaller ratio => bid multiplier higher
    supply_multiplier = 1.25 - 0.5 * supply_ratio  # ~1.25 at 15, ~0.75 at 25

    # Reaction to yesterday market pressure
    # If someone bid extremely high yesterday, only match when my hp is critical.
    extreme_pressure = highest_prev_bid >= 150.0

    # If I am critical, bid close to salary to secure water.
    if hp <= critical:
        target = DAILY_SALARY * (0.85 if extreme_pressure else 0.75) * supply_multiplier
    elif hp <= low_hp:
        # Moderate aggressiveness
        target = DAILY_SALARY * (0.55 if extreme_pressure else 0.45) * supply_multiplier
    else:
        # Healthy: bid more conservatively; still react slightly to pressure.
        # If highest_prev_bid was non-trivial, raise above it slightly but cap far below 160.
        if highest_prev_bid > 0.0:
            # Keep margin but don't chase.
            target = max(DAILY_SALARY * 0.35, highest_prev_bid * 0.55 + 5.0)
            target = target * (0.85 + 0.15 * supply_ratio)
        else:
            target = DAILY_SALARY * 0.4 * supply_multiplier

    # Ensure bid is affordable and non-negative
    if budget <= 0.0:
        return 0.0

    bid = float(min(budget, max(0.0, target)))

    # Soft cap to avoid learning Cindy/Eric's expensive behavior unless necessary
    if hp > low_hp and extreme_pressure:
        bid = float(min(bid, DAILY_SALARY * 0.65))

    return bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # If no budget, bid 0
    if my_status['budget'] <= 0:
        return 0.0

    # Gather alive opponents and their yesterday bids (only immediate reaction)
    alive = []
    yesterday_bids = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    yesterday_bids.append(float(prev.get('bid')))
                except Exception:
                    pass

    # Baseline bid depends on my HP/no_water_days (pressure)
    hp = float(my_status.get('hp', 0))
    no_water_days = int(my_status.get('no_water_days', 0))
    budget = float(my_status.get('budget', 0))

    # Estimate urgency: if already accumulating dry days or low HP, overbid to avoid death
    urgency = 0
    if hp <= 2.0:
        urgency += 3
    elif hp <= 4.0:
        urgency += 2
    elif hp <= 6.0:
        urgency += 1

    urgency += min(3, max(0, no_water_days))

    # Use yesterday's max bid as a proxy for how hard others are pushing
    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        # If others were aggressive yesterday, match their band; if not, stay cheaper
        if max_prev_bid >= DAILY_SALARY * 1.5:
            aggressiveness = 1.0
        elif max_prev_bid >= DAILY_SALARY * 0.9:
            aggressiveness = 0.75
        else:
            aggressiveness = 0.55
    else:
        aggressiveness = 0.6

    # Supply pressure: if supply is near minimum, water is scarce; bid higher
    if supply <= 16.0:
        scarcity = 1.0
    elif supply <= 19.0:
        scarcity = 0.85
    elif supply <= 22.0:
        scarcity = 0.7
    else:
        scarcity = 0.6

    # Core target bid
    # - When urgency is low: bid around 0.5-0.8 salary
    # - When urgency is high: bid up to ~1.0-1.2 salary, but never exceed budget
    base = DAILY_SALARY * aggressiveness * scarcity

    if urgency >= 4:
        target = DAILY_SALARY * (0.95 + 0.15 * (urgency - 4))
    elif urgency >= 2:
        target = base * 1.15
    else:
        target = base * 0.85

    # If yesterday max bid was high, ensure we can compete (slightly above their max band)
    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        # Only nudge above if we are in moderate/high urgency; otherwise keep cost control
        if urgency >= 2:
            target = max(target, min(DAILY_SALARY * 1.05, max_prev_bid + 3.0))

    # Clamp to budget and reasonable ceiling
    ceiling = DAILY_SALARY * 1.25
    bid = min(budget, ceiling, target)

    # If HP is critical, go aggressive up to budget
    if hp <= 1.5:
        bid = min(budget, DAILY_SALARY * 1.3)

    # Ensure non-negative float
    if bid < 0:
        bid = 0.0
    return float(bid)
"""
