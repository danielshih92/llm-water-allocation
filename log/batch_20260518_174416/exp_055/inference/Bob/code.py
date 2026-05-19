# ============================================================
# Experiment: exp_055
# Agent: Bob
# Source: exp_055
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

    # If supply is tight relative to our requirement, bid more.
    # If supply is plentiful, bid less.
    tightness = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        tightness = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    tightness = max(0.0, min(1.0, tightness))

    # Try to react to immediate yesterday bids if available.
    alive_opponents = [o for o in opponents_status.values() if o.get('alive', False)]
    highest_prev_bid = None
    if alive_opponents:
        prev_bids = []
        for o in alive_opponents:
            prev = o.get('previous_trace', {}) or {}
            b = prev.get('bid', None)
            if b is not None:
                try:
                    prev_bids.append(float(b))
                except Exception:
                    pass
        if prev_bids:
            highest_prev_bid = max(prev_bids)

    # Baseline: aim to win just enough. Convert tightness into a bid fraction.
    # Keep it below max daily salary to preserve budget.
    base_frac = 0.45 + 0.35 * tightness  # between ~0.45 and 0.80

    # Pressure response: if someone bid very high yesterday, increase a bit.
    if highest_prev_bid is not None:
        high_threshold = 0.85 * DAILY_SALARY
        if highest_prev_bid >= high_threshold:
            # If we are healthy, slightly reduce risk; if low hp, match pressure.
            if my_status.get('hp', 0) > 3:
                base_frac += 0.10
            else:
                base_frac += 0.25
        else:
            # If they weren't aggressive, stay near baseline.
            base_frac -= 0.05

    # Urgency from our hp and no_water_days.
    hp = int(my_status.get('hp', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    if hp <= 2 or no_water_days >= 2:
        base_frac += 0.25
    elif hp <= 3:
        base_frac += 0.10

    base_frac = max(0.25, min(0.95, base_frac))

    budget = float(my_status.get('budget', 0.0))
    # Final cap: cannot exceed budget.
    bid = DAILY_SALARY * base_frac
    if bid > budget:
        bid = budget

    # Also ensure we bid at least a minimal amount if budget allows.
    min_bid = min(budget, DAILY_SALARY * 0.25)
    if bid < min_bid:
        bid = min_bid

    # If we have no budget, bid 0.
    if budget <= 0:
        return 0

    # Return as float (game likely accepts numeric).
    return float(bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Extract yesterday bids from previous_trace for immediate reaction
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    yesterday_bids.append(float(b))
                except Exception:
                    pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how many allocations are likely needed; with fixed WATER_REQ, treat supply as proxy for competition
    # (We don't know exact water conversion, so use supply bands.)
    supply_band = 0
    if supply >= 22.0:
        supply_band = 2
    elif supply >= 18.0:
        supply_band = 1
    else:
        supply_band = 0

    # Decide target bid
    # If yesterday highest bid was extreme, we must contest more to avoid losing.
    extreme = highest_prev_bid >= DAILY_SALARY * 0.95
    very_high = highest_prev_bid >= DAILY_SALARY * 0.85

    # HP pressure: if low HP or already on no-water streak, increase bid.
    hp_pressure = 0
    if hp <= 2:
        hp_pressure = 3
    elif hp == 3:
        hp_pressure = 2
    elif hp == 4:
        hp_pressure = 1

    if no_water_days >= 2:
        hp_pressure = max(hp_pressure, 2)

    # Base bid by supply band (more supply => we can bid a bit less while still expecting allocation)
    if supply_band == 2:
        base = DAILY_SALARY * 0.55
    elif supply_band == 1:
        base = DAILY_SALARY * 0.65
    else:
        base = DAILY_SALARY * 0.75

    if extreme:
        base = max(base, DAILY_SALARY * 0.75)
    elif very_high:
        base = max(base, DAILY_SALARY * 0.70)

    # Adjust with HP pressure
    target = base + (DAILY_SALARY * 0.08 * hp_pressure)

    # If we're already doing okay and supply is high, avoid overbidding
    if hp >= 6 and supply_band == 2:
        target *= 0.85

    # Keep within budget and reasonable caps
    cap = min(budget, DAILY_SALARY * 1.2)
    bid = min(cap, target)

    # If budget is too small, still bid something to prevent total loss
    if bid < 1.0 and budget >= 1.0:
        bid = min(budget, 5.0)

    return float(bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from immediate previous_trace only
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append((float(b), oid))
            except Exception:
                pass

    highest_prev_bid = max([b for b, _ in prev_bids], default=0.0)
    top_prev_bidder_id = None
    if prev_bids:
        top_prev_bidder_id = max(prev_bids, key=lambda x: x[0])[1]

    # Base bid: aim for securing water without matching aggressive tops
    # If supply is higher, we can bid slightly less because allocation is easier.
    supply_factor = 1.0
    if supply <= MIN_SUPPLY:
        supply_factor = 1.0
    elif supply >= MAX_SUPPLY:
        supply_factor = 0.85
    else:
        # linear interpolate between 1.0 at 15 and 0.85 at 25
        supply_factor = 1.0 - 0.15 * ((supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY))

    # Pressure estimate from yesterday
    pressure_tier = 0
    if highest_prev_bid >= DAILY_SALARY * 1.6:
        pressure_tier = 3
    elif highest_prev_bid >= DAILY_SALARY * 1.0:
        pressure_tier = 2
    elif highest_prev_bid >= DAILY_SALARY * 0.6:
        pressure_tier = 1

    # If Alex/Eric were top bidders yesterday, they likely continue bidding high.
    # We undercut slightly to win price-efficiently.
    undercut = 0.92
    if top_prev_bidder_id in ('Alex', 'Eric'):
        undercut = 0.90
    elif top_prev_bidder_id is not None:
        undercut = 0.93

    # Emergency scaling based on my HP/no_water_days
    urgency = 0.0
    if my_hp <= 2:
        urgency = 1.0
    elif my_hp <= 3:
        urgency = 0.75
    elif my_hp <= 4:
        urgency = 0.55
    else:
        urgency = 0.35

    if my_no_water_days >= 2:
        urgency = max(urgency, 0.85)

    # Choose target bid level
    # Mid-high strategy: start around 0.55-0.75 salary, adjust by pressure tier and urgency.
    base = DAILY_SALARY * (0.55 + 0.1 * pressure_tier)  # 0.55..0.85
    target = base * supply_factor * undercut

    # If pressure was very high, increase but still try to avoid matching the top.
    if pressure_tier >= 2:
        target = max(target, DAILY_SALARY * 0.72 * supply_factor * undercut)
    if pressure_tier >= 3:
        target = max(target, DAILY_SALARY * 0.85 * supply_factor * undercut)

    # Apply urgency
    target = target * (0.85 + 0.3 * urgency)  # roughly 0.85..1.15

    # Cap by budget and keep non-negative
    bid = max(0.0, min(my_budget, target))

    # If we are extremely healthy and supply is high, reduce further to save budget.
    if my_hp >= 6 and supply >= 20:
        bid = min(bid, DAILY_SALARY * 0.6)

    # If we are in danger, ensure we bid enough to likely secure water.
    if my_hp <= 3 or my_no_water_days >= 2:
        bid = max(bid, DAILY_SALARY * 0.75 * supply_factor)
        bid = min(bid, my_budget)

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

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday bids to infer aggressiveness.
    yesterday_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Supply pressure: if supply is tight relative to our requirement, we need water.
    # Determine how many full water quanta could exist.
    # Use int() indices only; here we avoid indexing.
    full_quanta = int(supply / float(WATER_REQ)) if WATER_REQ > 0 else 0

    # Base bid: aim to be competitive but not always match the top spender.
    # If supply is low (<= 2 quanta), bid higher to secure.
    if supply <= float(MIN_SUPPLY) + 0.5:
        base = DAILY_SALARY * 0.75
    elif full_quanta <= 1:
        base = DAILY_SALARY * 0.7
    else:
        base = DAILY_SALARY * 0.58

    # Exploit yesterday: when someone bid very high, they likely try to lock water.
    # We counter with a slightly lower but still strong bid to win ties/near-ties.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        base = max(base, DAILY_SALARY * 0.78)

    # If my hp/no-water is critical, bid aggressively to avoid another no-water day.
    if my_hp <= 2 or my_no_water_days >= 2:
        base = max(base, DAILY_SALARY * 0.92)
    elif my_hp <= 4:
        base = max(base, DAILY_SALARY * 0.72)

    # Budget cap and non-negative.
    bid = max(0.0, min(my_budget, base))

    # If supply is high, we can safely bid a bit less.
    if supply >= float(MAX_SUPPLY) - 0.5 and my_hp >= 7 and my_no_water_days == 0:
        bid = max(0.0, min(my_budget, DAILY_SALARY * 0.5))

    # Ensure bid is within reasonable range.
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

    supply = day_context['supply']
    day = day_context['day']

    # Alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # If no one is alive, spend enough to ensure survival but not overspend
    if not alive_opps:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.45))

    # Read yesterday bids from previous_trace
    yesterday_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Pressure signals from yesterday
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = (sum(yesterday_bids) / float(len(yesterday_bids))) if yesterday_bids else 0.0

    # Estimate how many full water units are realistically available today
    # (We don't know exact allocation rules; use supply to set aggressiveness.)
    supply_units = int(supply / WATER_REQ)  # safe int index usage; not used for indexing

    # Base bid: ensure we compete for at least one allocation when supply is constrained
    # Medium scenario: supply between 15 and 25 => 1 to 2 units.
    if supply < (MIN_SUPPLY + MAX_SUPPLY) / 2.0:
        base = DAILY_SALARY * 0.55
    else:
        base = DAILY_SALARY * 0.48

    # Escalation if yesterday saw very high bids (likely scarcity fight)
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        if my_status['hp'] > 3:
            bid = DAILY_SALARY * 0.35
        else:
            bid = DAILY_SALARY * 0.85
    elif highest_prev_bid >= DAILY_SALARY * 0.65:
        # Moderate escalation
        bid = max(base, avg_prev_bid * 0.75)
    else:
        # If no extreme bidding, try to conserve budget
        bid = min(base, DAILY_SALARY * 0.52)

    # If our hp is low or we have many no-water days, increase to avoid death
    if my_status['hp'] <= 2:
        bid = max(bid, DAILY_SALARY * 0.9)
    elif my_status['no_water_days'] >= 2:
        bid = max(bid, DAILY_SALARY * 0.7)

    # If supply suggests only 1 unit, we should be a bit more competitive
    if supply_units <= 1:
        bid = max(bid, DAILY_SALARY * 0.6)

    # Budget cap
    bid = max(0.0, min(float(my_status['budget']), float(bid)))
    return bid
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids to infer aggressiveness.
    prev_bids = []
    prev_hp_after = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
                prev_hp_after.append(float(prev.get('hp_after', o.get('hp', 0.0))))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    # If someone was very aggressive yesterday, we slightly undercut rather than chase.
    aggressiveness = 0.0
    if highest_prev_bid >= DAILY_SALARY * 1.8:
        aggressiveness = 1.0
    elif highest_prev_bid >= DAILY_SALARY * 1.1:
        aggressiveness = 0.7
    elif highest_prev_bid >= DAILY_SALARY * 0.7:
        aggressiveness = 0.4

    # Supply pressure: higher supply reduces need for extreme bids.
    supply_norm = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)  # 0..1
    supply_norm = max(0.0, min(1.0, supply_norm))

    # Urgency based on our no-water streak and HP.
    urgency = 0.0
    if no_water_days >= 2:
        urgency = 1.0
    elif no_water_days == 1:
        urgency = 0.6
    else:
        urgency = 0.2

    if hp <= 1.5:
        urgency = max(urgency, 1.0)
    elif hp <= 3.0:
        urgency = max(urgency, 0.7)

    # Base bid: moderate fraction of salary, adjusted by urgency and supply.
    # If supply is high, bid less; if urgency is high, bid more.
    target = DAILY_SALARY * (0.45 + 0.35 * urgency - 0.15 * supply_norm)

    # Undercut strategy vs aggressive opponent(s): bid just below yesterday's highest.
    # This is a proxy; bids are hidden today.
    if aggressiveness > 0.0:
        # Aim to be competitive but not maxing out.
        target = min(target, highest_prev_bid * (0.85 - 0.1 * (1.0 - urgency)))

    # Ensure we don't overspend when budget is tight.
    # Also ensure non-negative.
    max_affordable = max(0.0, budget)

    # If budget is very low, conserve.
    if max_affordable <= DAILY_SALARY * 0.25:
        target = min(target, max_affordable * 0.9)
    else:
        # Keep a reserve to survive potential multi-day drought.
        reserve = DAILY_SALARY * (0.15 if hp > 4 else 0.05)
        target = min(target, max_affordable - reserve)

    # Final clamp.
    target = max(0.0, target)
    return float(min(target, max_affordable))
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

    alive_opps = []
    for opp_id, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((opp_id, o))

    my_hp = float(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    if not alive_opps:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Extract yesterday bids from immediate trace
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

    # Estimate competition pressure: if others were paying near/above salary, they likely contest aggressively.
    pressure = 0.0
    if highest_prev_bid > 0:
        pressure = min(1.0, highest_prev_bid / (DAILY_SALARY * 1.2))

    # Tight supply increases urgency.
    tightness = 0.0
    if supply <= MIN_SUPPLY:
        tightness = 1.0
    elif supply >= MAX_SUPPLY:
        tightness = 0.0
    else:
        tightness = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
        if tightness < 0.0:
            tightness = 0.0
        if tightness > 1.0:
            tightness = 1.0

    # Base bid: moderate under normal conditions, higher when hp is low or no-water streak grows.
    hp_factor = 1.0
    if my_hp <= 2.0:
        hp_factor = 1.25
    elif my_hp <= 4.0:
        hp_factor = 1.1
    else:
        hp_factor = 0.95

    streak_factor = 1.0
    if my_no_water_days >= 3:
        streak_factor = 1.25
    elif my_no_water_days == 2:
        streak_factor = 1.12

    # Target bid level
    # - If pressure high, move closer to salary to avoid losing the contested allocation.
    # - If pressure low, save budget.
    target = DAILY_SALARY * (0.42 + 0.35 * pressure)  # 0.42..0.77 of salary
    target *= (0.85 + 0.25 * tightness)              # up to ~1.10 when tight
    target *= hp_factor
    target *= streak_factor

    # If yesterday bids were extremely high, bump slightly.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        target = max(target, highest_prev_bid * 0.85)

    # Safety: never bid more than budget.
    bid = min(my_budget, target)

    # If budget is too low, bid whatever remains but avoid negative.
    if bid < 0.0:
        bid = 0.0

    # Small discrete adjustment to break ties: bid a tiny amount when contest likely.
    if pressure >= 0.6 and bid > 0:
        bid += 1.0

    # Clamp to budget again
    bid = min(bid, my_budget)

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

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Extract yesterday bids from immediate previous_trace only
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Estimate opponent pressure from yesterday
    if prev_bids:
        highest_prev = max(prev_bids)
        median_prev = sorted(prev_bids)[len(prev_bids)//2]
    else:
        highest_prev = 0.0
        median_prev = 0.0

    # Determine supply pressure: fewer units => more competition
    # supply is between 15 and 25; approximate number of water-quanta
    quanta = int(supply / float(WATER_REQ))  # explicit int to satisfy index rule
    # quanta will be 1 for 15-17, 2 for 18-25

    # Base target bid: slightly below median/highest to win without overpaying
    # Healthy: aim near median; low hp: bid higher to secure water if needed
    if my_hp <= 2 or my_no_water_days >= 2:
        target = max(median_prev, DAILY_SALARY * 0.75)
        # If others were extremely aggressive yesterday, shade just below highest
        if highest_prev > 0:
            target = min(target, highest_prev * 0.98)
    else:
        target = median_prev if median_prev > 0 else (DAILY_SALARY * 0.55)
        # If competition likely (quanta>=2), nudge upward a bit
        if quanta >= 2:
            target = target * 1.05
        # Shade below highest to avoid getting trapped in bidding wars
        if highest_prev > 0:
            target = min(target, highest_prev * 0.92)

    # Convert target into a feasible bid with budget cap
    bid = float(target)
    # Safety floor/ceiling relative to budget and salary
    bid = max(0.0, min(bid, my_budget, DAILY_SALARY * 1.2))

    # If quanta is low (1), competition is higher per unit; ensure we don't underbid too much
    if quanta <= 1 and my_budget > 0:
        bid = max(bid, min(my_budget, DAILY_SALARY * 0.65))

    # If budget is tiny, bid what we can
    if my_budget <= 1.0:
        return my_budget

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

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Extract yesterday bids from immediate previous_trace only
    yesterday_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev = max(yesterday_bids) if yesterday_bids else 0.0

    # If high-pressure bidders exist yesterday, we need to compete but not overpay.
    # Use a capped target bid based on supply: higher supply -> less need to overbid.
    # supply in [15,25] => scale from 1.0 to ~0.7
    supply_scale = 1.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_scale = 1.0 - (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) * 0.3
        if supply_scale < 0.7:
            supply_scale = 0.7
        if supply_scale > 1.0:
            supply_scale = 1.0

    # Determine urgency from our hp and consecutive no-water days.
    urgency = 0.0
    if my_hp <= 2.0:
        urgency += 1.0
    elif my_hp <= 4.0:
        urgency += 0.6
    if my_no_water_days >= 2:
        urgency += 0.6
    elif my_no_water_days == 1:
        urgency += 0.3

    # Base bid levels
    # - If yesterday had very high bids, we bid near a fraction of that but add a small buffer.
    # - If yesterday bids were low, bid moderately.
    if highest_prev >= DAILY_SALARY * 0.85:
        target = (highest_prev * 0.55 + 5.0) * supply_scale
    elif highest_prev >= DAILY_SALARY * 0.45:
        target = (highest_prev * 0.35 + 25.0) * supply_scale
    else:
        target = (DAILY_SALARY * 0.5) * supply_scale

    # Increase target under urgency
    target *= (1.0 + 0.35 * urgency)

    # Budget safety: never bid more than we can afford; also avoid bidding above a reasonable fraction of budget.
    max_reasonable = my_budget
    # Keep some budget for later days
    keep_fraction = 0.65
    if day is not None and int(day) >= 7:
        keep_fraction = 0.45
    max_reasonable = min(max_reasonable, my_budget * (1.0 - keep_fraction) + 1e-9)

    # Ensure at least a minimum bid to have a chance
    min_bid = DAILY_SALARY * 0.25
    bid = max(min_bid, target)

    # If we are critically low on hp, be aggressive up to most of budget
    if my_hp <= 2.0:
        bid = max(bid, DAILY_SALARY * 0.85)
        bid = min(bid, my_budget)
    else:
        bid = min(bid, my_budget)

    # Final clamp to non-negative
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

    alive_opps = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    supply = float(day_context['supply'])
    day = day_context['day']

    # Estimate how many units are likely needed to avoid losing to others.
    # If supply is near requirement, we must bid competitively.
    supply_pressure = 0.0
    if supply <= WATER_REQ:
        supply_pressure = 1.0
    else:
        supply_pressure = max(0.0, min(1.0, (MAX_SUPPLY - supply) / (MAX_SUPPLY - WATER_REQ)))

    # Read yesterday bids from traces (immediate reaction).
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    # If we saw high bids yesterday, assume they will keep pressure.
    high_bid = 0.0
    if prev_bids:
        high_bid = max(prev_bids)

    # Strategy: bid enough to beat Cindy/Alex style pressure when supply is tight.
    # Conserve if my HP is low.
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    # Base target bid tied to supply pressure.
    # Use thresholds inferred from yesterday: Cindy ~120.5, Alex ~100.4.
    if supply_pressure >= 0.7:
        target = max(DAILY_SALARY * 0.85, high_bid * 1.03)
    elif supply_pressure >= 0.4:
        target = max(DAILY_SALARY * 0.65, high_bid * 0.98)
    else:
        target = max(DAILY_SALARY * 0.5, high_bid * 0.9)

    # Adjust for survival: if low HP, bid more to avoid accumulating no-water days.
    if hp <= 2.0:
        target *= 1.15
    elif hp <= 4.0:
        target *= 1.05
    else:
        target *= 0.98

    # Ensure we don't overspend: if budget is small, cap aggressively.
    # Also keep some buffer for later days.
    buffer_factor = 0.75 if hp > 4 else 0.6
    cap = budget * buffer_factor

    bid = min(cap, target)

    # Final safety: non-negative and at least small bid if possible.
    if bid < 0:
        bid = 0.0
    return bid
"""
