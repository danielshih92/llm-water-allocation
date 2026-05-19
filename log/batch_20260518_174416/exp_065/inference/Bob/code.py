# ============================================================
# Experiment: exp_065
# Agent: Bob
# Source: exp_065
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

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # Base bid depends on our health/budget and remaining no-water days risk
    # (We don't know exact game mechanics; use a conservative mapping.)
    hp = my_status.get('hp', 0)
    budget = my_status.get('budget', 0)
    no_water_days = my_status.get('no_water_days', 0)

    # If we're in danger, bid to secure water
    danger = (hp <= 2) or (no_water_days >= 2)

    # Estimate how many full water requirements the supply can cover (for scaling)
    # Use int() for safety with float-derived indices.
    supply_int = int(supply)
    max_possible_full = int(supply_int // WATER_REQ) if WATER_REQ > 0 else 0

    # Read opponent pressure from yesterday
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / float(len(yesterday_bids))
    else:
        highest_prev_bid = 0.0
        avg_prev_bid = 0.0

    # Determine target bid range
    # If opponents were bidding near our daily_salary, they likely value water highly.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        if danger:
            target = DAILY_SALARY * 0.95
        else:
            # Match pressure but not fully; aim to outbid slightly
            target = min(DAILY_SALARY * 0.6, highest_prev_bid * 0.9)
            # If target is too low relative to observed bids, nudge upward
            target = max(target, highest_prev_bid * 0.75)
    else:
        if danger:
            # We need water; bid strongly but cap by salary
            target = DAILY_SALARY * 0.85
        else:
            # If bids were low, bid to secure without burning too much
            # Scale with supply coverage: fewer full units => higher chance competition
            scarcity_factor = 1.0
            if max_possible_full <= 1:
                scarcity_factor = 1.15
            elif max_possible_full == 2:
                scarcity_factor = 1.05
            target = max(DAILY_SALARY * 0.45, avg_prev_bid + 2.0) * scarcity_factor

    # Clamp to budget and sensible bounds
    lower_bound = 0.0
    upper_bound = float(budget)

    # Ensure we don't bid above what we can pay
    bid = max(lower_bound, min(upper_bound, target))

    # If supply is at the high end, we can bid slightly less
    if supply_int >= int(MAX_SUPPLY * 0.9):
        bid *= 0.95

    # Final clamp
    bid = max(0.0, min(float(budget), float(bid)))

    # Return as a number (float is acceptable in most simulators)
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])

    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    if not alive:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace (immediate reaction)
    prev_bids = []
    prev_hp = []
    for oid, o in alive:
        pt = o.get('previous_trace', {})
        if isinstance(pt, dict):
            b = pt.get('bid', None)
            if b is not None:
                prev_bids.append(float(b))
            hp_after = pt.get('hp_after', None)
            if hp_after is not None:
                prev_hp.append(float(hp_after))

    # Baseline aggressiveness from yesterday
    if prev_bids:
        avg_prev = sum(prev_bids) / float(len(prev_bids))
        max_prev = max(prev_bids)
    else:
        avg_prev = DAILY_SALARY * 0.55
        max_prev = DAILY_SALARY * 0.85

    # If someone was bidding very high yesterday, we must match to avoid losing allocation.
    # If my HP is low, preserve budget and avoid overbidding.
    if max_prev >= DAILY_SALARY * 0.85:
        target = avg_prev + 5.0
    else:
        target = max(avg_prev * 0.98, DAILY_SALARY * 0.5)

    # Supply pressure: lower supply means we should bid closer to the top of yesterday's range.
    # supply in [15,25] => scarcity factor in [1.0, ~0.4]
    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    scarcity = max(0.0, min(1.0, scarcity))

    # When supply is scarce, increase bid; otherwise slightly decrease.
    target = target * (1.0 + 0.35 * scarcity)

    # HP-based risk adjustment
    if my_hp <= 2.0:
        target = target * 0.75
    elif my_hp <= 4.0:
        target = target * 0.9
    else:
        target = target * 1.0

    # Cap to avoid bankrupting: keep some safety margin for later days
    safety = 0.15
    max_affordable = max(0.0, my_budget * (1.0 - safety))

    # Ensure non-negative and not above budget
    bid = min(max_affordable, target)
    bid = max(0.0, bid)

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
        if o.get('alive'):
            alive_opps.append((oid, o))

    if not alive_opps:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace for immediate reaction
    prev_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    # Cindy/Eric were high; use that as a pressure signal
    pressure = 0.0
    if highest_prev_bid >= DAILY_SALARY * 1.3:
        pressure = 1.0
    elif highest_prev_bid >= DAILY_SALARY * 0.8:
        pressure = 0.6
    else:
        pressure = 0.3

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Estimate how many water units are likely to be contested.
    # If supply is tight, we bid more to avoid falling behind.
    tightness = 0.0
    if supply <= float(WATER_REQ) + 6:
        tightness = 0.8
    elif supply <= float(WATER_REQ) + 10:
        tightness = 0.5
    else:
        tightness = 0.25

    # Base bid: aim to be competitive but not necessarily the top bidder.
    # Use hp/no_water_days to decide urgency.
    urgency = 0.0
    if hp <= 2.0 or no_water_days >= 2:
        urgency = 1.0
    elif hp <= 4.0 or no_water_days >= 1:
        urgency = 0.7
    else:
        urgency = 0.4

    # Target bid level: scale with pressure and urgency.
    # If others were bidding ~1.6x salary, we try to be a bit below the maximum.
    target = DAILY_SALARY * (0.55 + 0.35 * pressure + 0.25 * urgency + 0.15 * tightness)

    # If yesterday's max bid was extremely high, cap our aggressiveness slightly.
    if highest_prev_bid > DAILY_SALARY * 1.4:
        target = min(target, DAILY_SALARY * (0.95 + 0.1 * urgency))

    # If my hp is critical, push closer to top pressure.
    if hp <= 2.0:
        target = max(target, min(budget, DAILY_SALARY * 0.9))

    # Ensure we never bid negative and respect budget.
    bid = max(0.0, min(budget, target))

    # If budget is very low, still try to bid something proportional to avoid total starvation.
    if budget < DAILY_SALARY * 0.2:
        bid = max(0.0, min(budget, DAILY_SALARY * 0.15))

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

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((opp_id, o))

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace (immediate reaction only)
    prev_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Determine a target aggressiveness based on yesterday's pressure
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev_bid
    else:
        highest_prev_bid = 0.0
        second_prev_bid = 0.0

    # Supply pressure: higher supply means we can bid less; lower supply means bid more to secure water
    supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0..1
    supply_norm = max(0.0, min(1.0, supply_norm))

    # Base bid: aim to outbid surviving high bidders when supply is moderate/high.
    # If supply is low, we need more water certainty -> bid closer to top bidder.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Opponent(s) were very aggressive; try to match/just exceed when we can afford it.
        if hp > 3 and no_water_days <= 1:
            target = max(highest_prev_bid * 0.98, second_prev_bid + 2.0)
        else:
            target = max(highest_prev_bid * 1.02, second_prev_bid + 4.0)
    else:
        # Opponents not extremely aggressive; bid enough to stay competitive.
        # Lower supply -> higher bid.
        target = (DAILY_SALARY * (0.45 + 0.35 * (1.0 - supply_norm)))
        # If we saw any nontrivial bid, slightly chase it.
        if highest_prev_bid > 0:
            target = max(target, highest_prev_bid + 1.5)

    # If my hp is critical or I'm already on no-water streak, increase bid.
    if hp <= 2.0 or no_water_days >= 2:
        target *= 1.25

    # Never exceed budget; also keep below a reasonable cap to avoid bankruptcy.
    cap = max(0.0, budget)
    # Soft cap: don't exceed ~1.2*DAILY_SALARY unless budget forces it.
    soft_cap = min(cap, DAILY_SALARY * 1.2)

    bid = min(target, soft_cap)
    if bid < 0.0:
        bid = 0.0

    # Ensure we bid at least a minimal amount if we can; otherwise 0.
    min_reasonable = 1.0
    if budget >= min_reasonable:
        return float(min(max(bid, min_reasonable), cap))
    return float(max(0.0, min(bid, cap)))
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

    supply = day_context['supply']
    day = day_context['day']

    # Identify alive opponents and read yesterday's bid
    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid', None)
            if bid is not None:
                alive_opponents.append((opp_id, bid))

    # Baseline: target enough water for us (water requirement is 9 per day)
    # With supply 15-25, winning a bit above ~0.5*DAILY_SALARY is typically enough.
    # We'll adapt to yesterday's aggressive pressure.
    if not alive_opponents:
        # If no info, bid based on HP
        if my_status['hp'] <= 2:
            return min(my_status['budget'], DAILY_SALARY * 0.85)
        return min(my_status['budget'], DAILY_SALARY * 0.55)

    yesterday_bids = [b for _, b in alive_opponents]
    highest_prev_bid = max(yesterday_bids)

    # If someone bid extremely high yesterday, others likely need to match to survive.
    # Eric survived 10 days with ~133 bid; use it as a pressure signal.
    pressure_threshold = DAILY_SALARY * 1.35  # 121.5

    # Estimate how much water we need to keep HP safe: if low HP, bid more.
    hp = my_status.get('hp', 0)
    budget = my_status.get('budget', 0)

    # Supply-aware adjustment: higher supply means we can bid slightly less.
    # Convert supply to a normalized factor in [0,1]
    if MAX_SUPPLY == MIN_SUPPLY:
        supply_factor = 0.5
    else:
        supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
        if supply_factor < 0.0:
            supply_factor = 0.0
        if supply_factor > 1.0:
            supply_factor = 1.0

    # Core bidding policy
    if highest_prev_bid >= pressure_threshold:
        # High pressure: bid near the aggressor but not necessarily as high.
        # If our HP is critical, bid higher.
        if hp <= 2:
            base = DAILY_SALARY * (0.95 - 0.15 * supply_factor)
        elif hp <= 4:
            base = DAILY_SALARY * (0.75 - 0.10 * supply_factor)
        else:
            base = DAILY_SALARY * (0.65 - 0.10 * supply_factor)
    else:
        # Moderate pressure: bid enough to beat typical bids.
        if hp <= 2:
            base = DAILY_SALARY * (0.80 - 0.10 * supply_factor)
        elif hp <= 4:
            base = DAILY_SALARY * (0.62 - 0.08 * supply_factor)
        else:
            base = DAILY_SALARY * (0.52 - 0.06 * supply_factor)

    # Ensure we have a minimum bid to contend, but cap by budget
    min_bid = DAILY_SALARY * 0.25
    bid = base
    if bid < min_bid:
        bid = min_bid

    # Slightly increase on later days since episode is 10 days (day_context includes day)
    # This helps if others are also ramping up.
    try:
        if day is not None:
            # day is 1..10 typically; normalize
            day_factor = (float(day) - 1.0) / 9.0
            if day_factor < 0.0:
                day_factor = 0.0
            if day_factor > 1.0:
                day_factor = 1.0
            bid = bid * (1.0 + 0.10 * day_factor)
    except Exception:
        pass

    # Final clamp
    if budget is None:
        budget = 0.0
    if budget < 0.0:
        budget = 0.0
    if bid > budget:
        bid = budget

    # If budget is tiny, bid whatever we can
    return float(bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = day_context['supply']
    day = day_context['day']

    alive_opps = [o for o in opponents_status.values() if o.get('alive', True)]
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Immediate reaction to yesterday's bidding pressure
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', None)
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    prev_bids.append(float(b))
                except Exception:
                    pass

    my_hp = float(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0))

    if prev_bids:
        highest_prev_bid = max(prev_bids)
        # If others were bidding aggressively, undercut slightly to win supply cheaper.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # More conservative when low HP to avoid running out of budget.
            if my_hp > 3:
                target = highest_prev_bid - 3.0
            else:
                target = highest_prev_bid - 1.0
        else:
            # If pressure was low, bid enough to secure water.
            target = max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5)
    else:
        # No trace info: use a baseline bid.
        target = DAILY_SALARY * 0.55 if my_hp > 2 else DAILY_SALARY * 0.85

    # Safety caps: never exceed budget; also avoid extreme overspending.
    # Supply is in [15,25]; water requirement is 9 so at most one/limited winners.
    # Use a soft cap around 1.1*DAILY_SALARY for aggressive days.
    soft_cap = DAILY_SALARY * 1.1
    bid = float(min(my_budget, max(0.0, min(target, soft_cap))))

    # If we are very low on HP, prioritize survival.
    if my_hp <= 2:
        bid = float(min(my_budget, max(bid, DAILY_SALARY * 0.9)))

    # If supply is high within range, we can bid slightly lower.
    if supply >= 21.0:
        bid = float(max(0.0, bid - 2.0))

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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from traces
    prev_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Safety pressure: if we have low HP or already had no-water days, bid aggressively to secure water.
    danger = (hp <= 2.5) or (no_water_days >= 2)

    # If others were bidding in the surviving band, match/beat slightly.
    # Surviving band from yesterday: ~96-103. We'll target 98-105 depending on supply.
    if highest_prev_bid >= 90.0:
        if danger:
            target = min(DAILY_SALARY * 1.1, highest_prev_bid + 2.0)
        else:
            target = min(DAILY_SALARY * 1.05, highest_prev_bid - 1.0)
    else:
        # If yesterday bids were low (or missing), still bid enough to be competitive.
        if danger:
            target = DAILY_SALARY * 0.9
        else:
            target = DAILY_SALARY * 0.6

    # Supply-aware adjustment: when supply is higher, we can bid slightly less.
    # supply in [15,25]
    if supply >= 22.0:
        target *= 0.92
    elif supply <= 16.0:
        target *= 1.05

    # Clamp to budget and non-negative
    bid = max(0.0, min(budget, target))

    # Ensure we don't bid too tiny when in danger.
    if danger:
        min_bid = min(budget, DAILY_SALARY * 0.75)
        if bid < min_bid:
            bid = min_bid

    # If budget is extremely low, bid whatever remains.
    if budget <= 5.0:
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    budget = float(my_status.get('budget', 0.0))
    hp = float(my_status.get('hp', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append(o)

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Immediate reaction to yesterday's pressure
    prev_bids = []
    for o in alive:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate how many days of water we likely need to avoid death this horizon
    # If we've already gone without water, increase bid.
    urgency = 0
    if no_water_days >= 2:
        urgency += 2
    if no_water_days >= 1:
        urgency += 1
    if hp <= 2:
        urgency += 3
    elif hp <= 4:
        urgency += 1

    # Base bid: mid-level to win a fair share under medium scenario.
    # Scale with supply: more supply -> can bid less.
    supply_factor = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)  # 0..1-ish
    supply_factor = max(0.0, min(1.0, supply_factor))

    base = DAILY_SALARY * (0.45 + 0.25 * supply_factor)

    # If opponents were bidding extremely high yesterday, we must compete more today.
    if highest_prev_bid >= DAILY_SALARY * 1.1:
        base = base + DAILY_SALARY * 0.15

    # Add urgency
    base = base + urgency * (DAILY_SALARY * 0.08)

    # If our hp is healthy and no urgency, slightly discount to preserve budget.
    if urgency == 0 and hp >= 7:
        base = base * 0.9

    # Cap by budget
    bid = max(0.0, min(budget, base))

    # Avoid bidding too tiny amounts when supply is low
    if supply <= MIN_SUPPLY + 0.5:
        bid = max(bid, min(budget, DAILY_SALARY * 0.5))

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

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Extract yesterday's bids to infer aggressiveness
    cindy_bid = None
    max_prev_bid = 0.0
    for opp_id, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is None:
            continue
        try:
            b = float(b)
        except Exception:
            continue
        if b > max_prev_bid:
            max_prev_bid = b
        if str(opp_id).lower() == 'cindy':
            cindy_bid = b

    # Pressure signal: Cindy's high bid indicates others may also bid high
    pressure = 0.0
    if cindy_bid is not None:
        pressure = 1.0 if cindy_bid >= DAILY_SALARY * 0.9 else 0.5 if cindy_bid >= DAILY_SALARY * 0.6 else 0.0
    if pressure == 0.0 and max_prev_bid >= DAILY_SALARY * 0.85:
        pressure = 0.5

    # Supply-based aggressiveness: higher supply reduces need to overbid
    # Map supply to a multiplier in [0.85, 1.15]
    if MAX_SUPPLY > MIN_SUPPLY:
        t = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        t = 0.5
    if t < 0.0:
        t = 0.0
    if t > 1.0:
        t = 1.0

    supply_mult = 0.95 + 0.2 * t  # higher supply => slightly higher willingness to pay (to secure HP)

    # HP urgency: if low HP or building no-water days, bid more
    urgency = 0.0
    if hp <= 2:
        urgency = 1.0
    elif hp <= 4:
        urgency = 0.7
    elif hp <= 6:
        urgency = 0.4
    else:
        urgency = 0.2

    if no_water_days >= 2:
        urgency = max(urgency, 0.8)

    # Base bid target
    # If pressure high, try to outbid slightly below the top aggressiveness threshold.
    if pressure >= 0.5:
        target = DAILY_SALARY * (0.55 + 0.35 * urgency) * supply_mult
        # If we know someone previously bid very high, nudge upward but cap.
        if max_prev_bid > 0:
            target = max(target, min(DAILY_SALARY * 0.75, max_prev_bid * 0.95))
    else:
        target = DAILY_SALARY * (0.45 + 0.35 * urgency) * supply_mult

    # Ensure we don't exceed budget
    if budget <= 0:
        return 0.0

    # Cap to keep some budget for later days
    # When HP is critical, allow higher spend.
    budget_cap = DAILY_SALARY * (0.95 if urgency >= 0.8 else 0.7)
    bid = min(budget, min(target, budget_cap))

    # If we are extremely low HP, spend more aggressively
    if hp <= 1:
        bid = min(budget, DAILY_SALARY * 0.98)

    # Avoid negative/NaN
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

    supply = day_context['supply']
    day = day_context['day']

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive'):
            alive_opps.append((oid, o))

    # If no opponents alive, bid conservatively.
    if not alive_opps:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace for immediate reaction.
    prev_bids = []
    for oid, o in alive_opps:
        pt = o.get('previous_trace', {})
        if pt and pt.get('bid') is not None:
            prev_bids.append(float(pt['bid']))

    # Pressure estimate from yesterday.
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    # Supply pressure: higher supply should allow lower bids.
    # Normalize supply to [0,1] using explicit int indices not needed here.
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (float(supply) - float(MIN_SUPPLY)) / (float(MAX_SUPPLY) - float(MIN_SUPPLY))
    else:
        supply_norm = 0.5
    # supply_norm ~0 => tight (15), ~1 => abundant (25)

    # Base bid target: aim around a fraction of salary.
    # Tight supply => bid higher; abundant => bid lower.
    base = DAILY_SALARY * (0.62 - 0.18 * supply_norm)

    # If yesterday bids were very high, avoid getting into a bidding war unless low HP.
    # If my HP is low, increase bid to secure water.
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    # Determine scarcity threshold from supply.
    # If supply is close to WATER_REQ, we must bid more.
    scarcity_ratio = float(supply) / float(WATER_REQ)

    # Compute adjustment from opponents' yesterday behavior.
    # Cindy had high budget and survived; if highest_prev_bid is near salary, others likely overbid.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        war_risk = 1.0
    elif highest_prev_bid >= DAILY_SALARY * 0.6:
        war_risk = 0.6
    else:
        war_risk = 0.25

    # HP urgency
    if hp <= 2.0:
        hp_mult = 1.35
    elif hp <= 4.0:
        hp_mult = 1.15
    else:
        hp_mult = 1.0

    # Scarcity urgency
    if scarcity_ratio <= 1.25:
        scarcity_mult = 1.25
    elif scarcity_ratio <= 1.6:
        scarcity_mult = 1.1
    else:
        scarcity_mult = 0.95

    # Reduce bid when war risk is high and my HP is not critical.
    if war_risk >= 0.6 and hp > 4.0:
        war_mult = 0.85
    else:
        war_mult = 1.0

    bid = base * hp_mult * scarcity_mult * war_mult

    # Cap bid to budget and keep it within a reasonable range.
    bid = max(0.0, min(budget, bid))

    # Additional guard: if budget is low, don't overcommit.
    if budget <= DAILY_SALARY * 0.35:
        bid = min(bid, budget)

    # Ensure we don't bid above a typical maximum.
    # (No explicit max bid provided; keep under 2*salary to avoid extreme overbids.)
    bid = min(bid, DAILY_SALARY * 2.0)

    return float(bid)
"""
