# ============================================================
# Experiment: exp_061
# Agent: Bob
# Source: exp_061
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

    # Basic safety checks
    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    # If no opponents, take a safe moderate bid.
    if not alive_opponents:
        target = DAILY_SALARY * 0.45
        return min(my_budget, target)

    # Read yesterday bids for immediate reaction.
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how much water is likely available relative to our requirement.
    # Use explicit int() for any indexing; here we only compute scalars.
    # Heuristic: if supply is low, we need to bid more aggressively.
    supply_pressure = 0.0
    if supply <= float(WATER_REQ):
        supply_pressure = 1.0
    elif supply <= (float(WATER_REQ) + 3.0):
        supply_pressure = 0.7
    elif supply <= 18.0:
        supply_pressure = 0.45
    else:
        supply_pressure = 0.25

    # Determine our urgency.
    urgency = 0.0
    if my_hp <= 2.0:
        urgency = 1.0
    elif my_hp <= 3.0:
        urgency = 0.75
    elif my_no_water_days >= 2:
        urgency = 0.7
    elif my_no_water_days >= 1:
        urgency = 0.45
    else:
        urgency = 0.25

    # If opponents overbid yesterday, they are likely trying to secure water under stress.
    # We counter with a slightly lower bid to win while conserving budget.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Counter-bid: just under their pressure, adjusted by our urgency.
        base = highest_prev_bid - 5.0
        # If we're very urgent, we may need to match more closely.
        if urgency >= 0.75:
            base = highest_prev_bid - 2.0
        elif urgency <= 0.35:
            base = highest_prev_bid - 8.0
        bid = base + (supply_pressure * 5.0)
    else:
        # They were not desperate: bid moderately to ensure we get water without burning budget.
        # Scale with supply pressure and our urgency.
        bid = DAILY_SALARY * (0.35 + 0.35 * supply_pressure + 0.25 * urgency)
        # If their highest bid was non-trivial, try to beat it by a small margin.
        if highest_prev_bid > 0.0:
            bid = max(bid, highest_prev_bid + 1.5)

    # Day-based slight tightening: later days increase willingness to spend.
    # episode_days is always 10 in meta-round state, but day_context only has supply/day.
    # We'll use day to gently increase bid.
    if day >= 7:
        bid *= 1.12
    elif day <= 2:
        bid *= 0.95

    # Clamp bid to budget and reasonable range.
    bid = float(bid)
    if bid < 0.0:
        bid = 0.0

    # Never bid more than we can afford.
    bid = min(bid, my_budget)

    # If budget is extremely low, bid whatever remains.
    if my_budget <= 1.0:
        return my_budget

    # Ensure we bid at least enough to have a chance (but don't overcommit).
    # Use a floor tied to our requirement and supply pressure.
    min_reasonable = max(DAILY_SALARY * 0.15, (float(WATER_REQ) / float(MAX_SUPPLY)) * DAILY_SALARY * 0.25)
    if bid < min_reasonable and my_hp <= 3.0:
        bid = min(my_budget, min_reasonable)

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
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from immediate previous_trace only
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid', 0.0)))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate how tight the market is: higher when supply is closer to WATER_REQ
    # supply in [15,25] => ratio in [1.67,2.78]
    ratio = supply / float(WATER_REQ)
    tightness = 1.0 / max(1.0, ratio)  # higher when supply smaller

    # If opponents previously bid very high, raise pressure; otherwise bid to beat typical bids.
    # Use a budget-aware cap to avoid repeating Cindy-like death by depletion.
    budget_cap = budget
    if hp <= 2 or no_water_days >= 2:
        base = DAILY_SALARY * (0.85 + 0.1 * tightness)
    else:
        base = DAILY_SALARY * (0.6 + 0.25 * tightness)

    # If someone was bidding near the top yesterday, match/beat slightly.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        bid = min(budget_cap, max(base, highest_prev_bid * 0.92 + 2.0))
    else:
        # If highest was moderate, bid somewhat above it to improve chance without overpay.
        bid = min(budget_cap, max(base, highest_prev_bid * 0.75 + 10.0 * tightness))

    # Hard safety: never bid more than what keeps at least one day of salary in reserve if possible
    # (prevents extreme depletion).
    reserve = DAILY_SALARY * 0.2
    if budget > reserve:
        bid = min(bid, budget - reserve)

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
        return float(min(my_budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from immediate previous_trace only
    yesterday_bids = []
    yesterday_highest = None
    yesterday_second = None
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            b = float(prev.get('bid'))
            yesterday_bids.append(b)

    if yesterday_bids:
        yesterday_highest = max(yesterday_bids)
        # second highest for pressure estimate
        sorted_b = sorted(yesterday_bids, reverse=True)
        if len(sorted_b) >= 2:
            yesterday_second = sorted_b[1]

    # Supply pressure: if supply is near minimum, contest is tighter
    supply_ratio = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Base bid: choose a level that beats typical surviving bids (~90-115) but not maxing out
    # If my HP is low or I already have no-water days, bid higher.
    if my_hp <= 2 or my_no_water_days >= 2:
        base = DAILY_SALARY * 0.95
    elif my_hp <= 4 or my_no_water_days >= 1:
        base = DAILY_SALARY * 0.75
    else:
        base = DAILY_SALARY * 0.6

    # React to yesterday pressure: if someone bid very high, match just above the second-highest.
    # This exploits that high bidders likely continue pressuring.
    if yesterday_highest is not None:
        # If yesterday pressure was high, move toward it.
        if yesterday_highest >= DAILY_SALARY * 0.85:
            if yesterday_second is not None:
                base = max(base, min(my_budget, yesterday_second + 2.5))
            else:
                base = max(base, min(my_budget, yesterday_highest - 1.0))
        # If pressure was moderate, still slightly over the upper cluster.
        else:
            if yesterday_second is not None:
                base = max(base, min(my_budget, yesterday_second + 1.5))

    # Tight supply increases urgency
    urgency = 1.0 + (1.0 - supply_ratio) * 0.25
    bid = base * urgency

    # Cap bid by budget
    bid = float(min(my_budget, bid))

    # Ensure bid is non-negative
    if bid < 0.0:
        bid = 0.0

    # If budget is extremely low, bid proportionally
    if my_budget <= DAILY_SALARY * 0.15:
        bid = float(min(my_budget, DAILY_SALARY * 0.1))

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

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Yesterday pressure from opponents' bids
    yesterday_bids = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', None)
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    yesterday_bids.append(float(b))
                except Exception:
                    pass
        elif isinstance(prev, list) and len(prev) > 0:
            # Defensive: if previous_trace is list, take last element
            last = prev[-1]
            if isinstance(last, dict) and last.get('bid', None) is not None:
                try:
                    yesterday_bids.append(float(last['bid']))
                except Exception:
                    pass

    pressure = 0.0
    if yesterday_bids:
        pressure = max(yesterday_bids)

    # Estimate how many full water blocks the supply can cover (for aggressiveness)
    # Use int() to avoid float index issues if any arrays are used.
    blocks = int(supply / float(WATER_REQ)) if WATER_REQ > 0 else 0
    blocks = max(0, blocks)

    # Base bid tied to supply level: higher supply => bid less
    # supply in [15,25], map to factor in [0.95,0.55]
    if MAX_SUPPLY > MIN_SUPPLY:
        t = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        t = 0.5
    t = max(0.0, min(1.0, float(t)))
    supply_factor = 0.95 - 0.40 * t

    # Risk control based on my hp and no-water streak
    # If I'm low hp or have been without water, bid more.
    hp_risk = 0.0
    if my_hp <= 2:
        hp_risk = 0.90
    elif my_hp <= 3:
        hp_risk = 0.60
    elif my_hp <= 5:
        hp_risk = 0.35
    else:
        hp_risk = 0.15

    streak_risk = 0.0
    if my_no_water_days >= 2:
        streak_risk = 0.80
    elif my_no_water_days == 1:
        streak_risk = 0.45
    else:
        streak_risk = 0.15

    urgency = max(hp_risk, streak_risk)

    # Pressure adjustment: if yesterday someone bid very high, avoid being undercut
    # but don't match blindly; target a fraction above typical pressure.
    high_pressure = pressure >= DAILY_SALARY * 0.85

    # Compute target bid
    if high_pressure:
        # If pressure was extreme, bid moderately high only when urgent
        target = DAILY_SALARY * (0.30 + 0.45 * urgency) * supply_factor
        # Ensure we don't go too low under high pressure
        target = max(target, DAILY_SALARY * (0.35 + 0.25 * urgency))
    else:
        target = DAILY_SALARY * (0.45 + 0.35 * urgency) * supply_factor

    # If supply is scarce (blocks <=1), increase bid
    if blocks <= 1:
        target *= 1.15

    # Cap by budget and add small day-based smoothing to avoid ties
    # (simultaneous bidding; slight variation can help)
    jitter = 0.98 + (0.02 * ((day % 7) / 6.0))
    target *= jitter

    bid = min(my_budget, float(target))

    # If budget is tiny, still bid something to prevent immediate death if needed
    if my_budget <= 1e-6:
        return 0.0

    # Keep bid within reasonable bounds
    bid = max(0.0, bid)
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
    day = int(day_context['day'])

    alive = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Read yesterday bids for immediate reaction
    prev_bids = []
    for opp in alive:
        prev = opp.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            prev_bids.append(float(b))

    # Estimate how hard the market is based on yesterday
    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / len(prev_bids)
    else:
        highest_prev = 0.0
        avg_prev = DAILY_SALARY * 0.55

    # Supply pressure: when supply is higher, we can bid less aggressively.
    # Approximate how many units might be contested.
    # Ensure indices are safe even if we used arrays (we don't).
    supply_ratio = (supply - MIN_SUPPLY) / max(1e-9, (MAX_SUPPLY - MIN_SUPPLY))
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Base bid target: around the observed average, adjusted by supply.
    # If my hp is low or no_water_days high, bid more.
    hp = int(my_status['hp'])
    no_water_days = int(my_status['no_water_days'])
    budget = float(my_status['budget'])

    # Urgency factor
    if hp <= 2 or no_water_days >= 2:
        urgency = 1.15
    elif hp <= 4 or no_water_days >= 1:
        urgency = 1.05
    else:
        urgency = 0.95

    # Market factor: if yesterday highest bid was very high, expect competition.
    if highest_prev >= DAILY_SALARY * 1.6:  # ~144
        market = 1.08
    elif highest_prev >= DAILY_SALARY * 1.2:  # ~108
        market = 1.03
    else:
        market = 0.98

    # Supply adjustment: higher supply -> lower needed bid
    supply_adjust = 1.08 - 0.16 * supply_ratio  # ranges ~1.08 to 0.92

    target = avg_prev * urgency * market * supply_adjust

    # Cap to avoid overspending; also ensure we can afford the bid.
    # If competition seems fierce, allow higher but still bounded.
    hard_cap = budget * 0.75
    soft_cap = DAILY_SALARY * 2.2  # 198
    bid = min(target, soft_cap, hard_cap)

    # If we are extremely healthy, reduce spending.
    if hp >= 9 and no_water_days == 0:
        bid = min(bid, DAILY_SALARY * 0.6, budget)

    # If we are in danger, push closer to highest_prev but not exceed caps.
    if hp <= 3 or no_water_days >= 2:
        push = max(bid, min(highest_prev * 0.92, soft_cap, hard_cap))
        bid = push

    # Final safety: at least a small bid if budget allows
    min_bid = min(budget, DAILY_SALARY * 0.25)
    bid = max(min_bid, bid)

    # Must be non-negative
    if bid < 0:
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

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    # Alive opponents and their yesterday bids
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # If no opponents alive, bid conservatively
    if not alive_opps:
        return max(0, min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace for immediate reaction
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    my_hp = float(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0))

    # Estimate how tight the day is; higher supply reduces need to overbid
    # (use ratio but keep simple)
    supply_ratio = 0.0
    if MAX_SUPPLY > 0:
        supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    # clamp
    if supply_ratio < 0.0:
        supply_ratio = 0.0
    if supply_ratio > 1.0:
        supply_ratio = 1.0

    # Detect Cindy aggression/budget crash from her yesterday trace
    cindy = opponents_status.get('Cindy', None)
    cindy_aggressive = False
    cindy_budget_crashed = False
    if cindy is not None:
        prev = cindy.get('previous_trace', {}) or {}
        c_bid = prev.get('bid', None)
        if c_bid is not None:
            try:
                if float(c_bid) >= DAILY_SALARY * 1.5:
                    cindy_aggressive = True
            except Exception:
                pass
        # if she ended yesterday with 0 budget, likely budget-constrained
        try:
            if float(cindy.get('budget', 0)) <= 0.0:
                cindy_budget_crashed = True
        except Exception:
            pass

    # Determine a target bid band
    # Base: moderate bid to stay competitive
    # If our hp is low, raise urgency.
    urgency = 0.0
    if my_hp <= 2:
        urgency = 1.0
    elif my_hp <= 4:
        urgency = 0.7
    elif my_hp <= 7:
        urgency = 0.4
    else:
        urgency = 0.25

    # If Cindy was aggressive and budget-crashed, we can undercut slightly but still pressure.
    # If overall yesterday bids were high, increase slightly.
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    base_bid = DAILY_SALARY * (0.45 + 0.25 * (1.0 - supply_ratio))  # tighter supply -> higher

    # Pressure adjustment
    if cindy_aggressive and cindy_budget_crashed:
        # Cindy likely cannot sustain aggression; bid just enough to beat her if she still tries.
        target = base_bid * (1.05 + 0.15 * urgency)
    else:
        # If yesterday market was hot, follow partially
        if highest_prev_bid >= DAILY_SALARY * 1.8:
            target = base_bid * (1.15 + 0.25 * urgency)
        elif avg_prev_bid >= DAILY_SALARY * 1.1:
            target = base_bid * (1.05 + 0.2 * urgency)
        else:
            target = base_bid * (0.95 + 0.2 * urgency)

    # Ensure we can afford it; also avoid overbidding beyond reasonable fraction of budget
    # (budget is finite; also prevent bidding too low when hp is critical)
    max_reasonable = my_budget
    if my_hp <= 2:
        max_reasonable = my_budget  # can spend to survive
    else:
        # keep some buffer
        max_reasonable = min(my_budget, DAILY_SALARY * 1.2)

    # Final clamp
    bid = float(target)
    if bid < 0:
        bid = 0.0
    if bid > max_reasonable:
        bid = max_reasonable

    # If our hp is extremely low, bid more aggressively
    if my_hp <= 1:
        bid = min(my_budget, DAILY_SALARY * 0.95)

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
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive.append((opp_id, opp))

    # If no one else alive, take what you can afford but keep some buffer
    if not alive:
        return max(0.0, min(float(my_status['budget']), DAILY_SALARY * 0.45))

    # Read yesterday bids and pressure indicators
    yesterday_bids = []
    lowest_hp = None
    any_low_no_water = False
    for opp_id, opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass
        hp = opp.get('hp', 0)
        if lowest_hp is None or hp < lowest_hp:
            lowest_hp = hp
        if opp.get('no_water_days', 0) >= 2:
            any_low_no_water = True

    # Supply pressure: lower supply increases chance of everyone fighting
    # Use conservative index-safe mapping to a target bid fraction.
    # Approximate how many full water-units exist; indices must be int().
    units = int(supply / float(WATER_REQ))  # may be 1 or 2

    # Estimate opponent aggressiveness from yesterday
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    # Base bid: enough to beat typical moderate bids, not to match Cindy's extreme bids.
    # If Cindy-like behavior (very high highest_prev_bid), stay around a fraction of that.
    if highest_prev_bid >= DAILY_SALARY * 1.2:
        # Cindy likely bidding very high; don't chase fully unless I'm in danger.
        danger = (my_status.get('hp', 0) <= 2) or (my_status.get('no_water_days', 0) >= 2)
        if danger:
            frac = 0.85
        else:
            frac = 0.45
    else:
        # More normal bidding: bid near average/highest but with a margin
        danger = (my_status.get('hp', 0) <= 2) or (my_status.get('no_water_days', 0) >= 2)
        frac = 0.65 if danger else 0.40

    # Adjust for supply units (if only ~1 unit, competition is tighter)
    if units <= 1:
        frac += 0.10
    else:
        frac -= 0.05

    # If someone is already missing water multiple days, they may overbid to recover
    if any_low_no_water:
        frac += 0.08

    # Clamp fraction
    if frac < 0.20:
        frac = 0.20
    if frac > 0.95:
        frac = 0.95

    # Convert to bid amount
    budget = float(my_status['budget'])
    bid = DAILY_SALARY * frac

    # If my budget is low, bid as much as possible but keep non-negative
    if bid > budget:
        bid = budget

    # If I'm very low hp, take a more aggressive stance
    if my_status.get('hp', 0) <= 1:
        bid = min(budget, DAILY_SALARY * 0.9)
    elif my_status.get('hp', 0) <= 2:
        bid = min(budget, DAILY_SALARY * 0.75)

    # Small reaction to yesterday: if average was high, slightly increase.
    if avg_prev_bid > DAILY_SALARY:
        bid = min(budget, bid + 5.0)

    # Ensure bid is valid
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = day_context['supply']
    day = day_context['day']

    # Alive opponents
    alive_ids = []
    for oid, o in opponents_status.items():
        if o.get('alive'):
            alive_ids.append(oid)

    # If no opponents, bid enough to secure water
    if not alive_ids:
        return min(my_status['budget'], DAILY_SALARY * 0.6)

    # Read yesterday bids from previous_trace only
    yesterday_bids = []
    yesterday_hp_after = []
    for oid in alive_ids:
        prev = opponents_status[oid].get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid', 0.0)))
                yesterday_hp_after.append(float(prev.get('hp_after', 0.0)))
            except Exception:
                pass

    # Determine pressure from yesterday
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    # If someone was aggressive with high bid, we match partially to avoid losing ties
    # Pressure thresholds tuned to observed meta-round values (~150-230)
    pressure_level = 0
    if highest_prev_bid >= 210:
        pressure_level = 3
    elif highest_prev_bid >= 175:
        pressure_level = 2
    elif highest_prev_bid >= 140:
        pressure_level = 1

    my_hp = my_status.get('hp', 0)
    my_budget = my_status.get('budget', 0)
    no_water_days = my_status.get('no_water_days', 0)

    # Urgency: if we've gone without water, increase bids.
    urgency = 0
    if no_water_days >= 2:
        urgency = 2
    elif no_water_days >= 1:
        urgency = 1

    # Base bid target: moderate share of daily salary
    base = DAILY_SALARY * 0.55

    # If my HP is low, bid more
    if my_hp <= 2:
        base = DAILY_SALARY * 0.9
    elif my_hp <= 4:
        base = DAILY_SALARY * 0.7

    # Scale with pressure and urgency
    bid = base + pressure_level * (DAILY_SALARY * 0.12) + urgency * (DAILY_SALARY * 0.15)

    # Also anchor to highest_prev_bid to react to aggressive players
    # Keep it below that to save budget, but not too low to lose allocation.
    if highest_prev_bid > 0:
        bid = max(bid, highest_prev_bid * 0.78)

    # Supply consideration: higher supply means less need to outbid
    # supply is float; translate to a discrete tier safely
    try:
        tier = int((float(supply) - float(MIN_SUPPLY)) / (float(MAX_SUPPLY) - float(MIN_SUPPLY) + 1e-9) * 3)
    except Exception:
        tier = 1
    if tier < 0:
        tier = 0
    if tier > 3:
        tier = 3

    # If supply is high, slightly reduce; if low, slightly increase
    if tier >= 2:
        bid *= 0.95
    elif tier <= 1:
        bid *= 1.03

    # Final clamp by budget
    if my_budget <= 0:
        return 0

    # Avoid overcommitting: keep within 95% of budget
    bid = min(bid, my_budget * 0.95)

    # Ensure non-negative
    if bid < 0:
        bid = 0

    # If we're near endgame (day 10), be more decisive
    if int(day) >= 9:
        bid = min(my_budget * 0.98, max(bid, DAILY_SALARY * 0.75))

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

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return min(float(my_status['budget']), DAILY_SALARY * 0.4)

    # Infer opponent aggressiveness from yesterday traces
    prev_bids = []
    for oid, o in alive_opps:
        tr = o.get('previous_trace', {})
        b = tr.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else 0.0

    # Tight supply implies need to outbid more; use a soft pressure score
    # supply in [15,25] => remaining slack in [0,2] relative to WATER_REQ
    slack = (supply - WATER_REQ) / float(WATER_REQ)  # ~0.67 to 1.78
    tightness = 1.0 - max(0.0, min(1.0, (slack - 0.6) / 1.2))  # higher when closer to 9

    # If someone previously bid extremely high, assume they will continue anchoring.
    anchor = 0.0
    if highest_prev_bid >= DAILY_SALARY * 1.6:
        anchor = 1.0
    elif highest_prev_bid >= DAILY_SALARY * 0.9:
        anchor = 0.6

    # Base bid: aim to be competitive but not reckless.
    # Use a target around a fraction of the anchor and tightness.
    base = DAILY_SALARY * (0.45 + 0.35 * tightness + 0.25 * anchor)

    # If we see a strong anchor, try to slightly exceed the typical high bidder yesterday.
    if highest_prev_bid > 0:
        # Don't chase the absolute max; use second-highest as a safer proxy.
        target = max(base, second_prev_bid * 0.95 + 2.0)
    else:
        target = base

    # My health/budget constraints: if low hp, pay more to survive; if high hp, conserve.
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    if hp <= 2.0:
        mult = 0.95
    elif hp <= 4.0:
        mult = 0.85
    elif hp <= 7.0:
        mult = 0.75
    else:
        mult = 0.65

    # Also consider no_water_days: if already accruing, increase urgency.
    no_water_days = int(my_status.get('no_water_days', 0))
    if no_water_days >= 2:
        mult += 0.15
    elif no_water_days >= 1:
        mult += 0.07

    bid = target * mult

    # Ensure bid is within reasonable bounds and budget-limited.
    # Keep some budget for future days; never exceed 95% of budget.
    cap = max(0.0, budget * 0.95)
    bid = min(bid, cap)

    # Lower bound: if budget allows, bid at least a small fraction to avoid being shut out.
    floor = min(cap, DAILY_SALARY * (0.35 + 0.2 * tightness))
    bid = max(bid, floor)

    # Final safety: if budget is tiny, bid whatever possible.
    if budget <= 1.0:
        return max(0.0, budget)

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

    my_hp = int(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday bids and identify who was most aggressive / most constrained.
    yesterday_bids = []
    aggressive_pressure = 0.0
    constrained_count = 0

    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                b = float(bid)
                yesterday_bids.append(b)
                # Aggression proxy: bids far above typical salary imply willingness to burn budget.
                if b >= DAILY_SALARY * 2.2:
                    aggressive_pressure += 1.0
            except Exception:
                pass
        # Budget constraint proxy from yesterday outcome
        opp_budget_after = prev.get('budget_after', opp.get('budget', None))
        if opp_budget_after is not None:
            try:
                if float(opp_budget_after) <= 0.0:
                    constrained_count += 1
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Determine how many "full" water units supply can cover.
    # Use explicit int conversion for safety.
    full_units = int(supply / float(WATER_REQ))
    if full_units < 1:
        full_units = 1

    # Base bid: aim for a share without overpaying.
    # If opponents were aggressive yesterday, we shade upward slightly; if Cindy likely burned out, shade down.
    burnout_signal = constrained_count

    # Pressure score: high bid + aggressive count.
    pressure = 0.0
    if highest_prev_bid > 0:
        pressure = min(1.0, highest_prev_bid / (DAILY_SALARY * 2.6))
    pressure = min(1.0, pressure + 0.25 * aggressive_pressure)

    # If we are in danger, increase bid to avoid accumulating no-water days.
    danger = 0.0
    if my_hp <= 2:
        danger = 1.0
    elif my_hp <= 4:
        danger = 0.6
    if my_no_water_days >= 2:
        danger = max(danger, 0.8)

    # Budget-aware cap
    max_affordable = max(0.0, my_budget)

    # Supply-dependent aggressiveness: more supply reduces need to overbid.
    supply_factor = 0.45
    if supply >= 22:
        supply_factor = 0.35
    elif supply <= 16:
        supply_factor = 0.55

    # Burnout reduces our need to chase.
    burnout_discount = 0.12 * burnout_signal

    # Final target multiplier of DAILY_SALARY.
    target_mult = supply_factor + 0.35 * pressure - burnout_discount + 0.35 * danger
    target_mult = max(0.25, min(1.2, target_mult))

    # Convert to bid.
    bid = DAILY_SALARY * target_mult

    # Ensure we don't bid more than budget; also keep a minimum bid if budget allows.
    bid = min(bid, max_affordable)

    # If budget is very low, still try to secure water only when in danger.
    if my_budget <= DAILY_SALARY * 0.25:
        if danger >= 0.8:
            bid = min(my_budget, DAILY_SALARY * 0.9)
        else:
            bid = min(my_budget, DAILY_SALARY * 0.2)

    # If supply is extremely low relative to requirement, bid harder.
    if supply < float(WATER_REQ):
        bid = min(my_budget, DAILY_SALARY * 0.95)

    return float(max(0.0, bid))
"""
