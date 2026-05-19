# ============================================================
# Experiment: exp_001
# Agent: Bob
# Source: exp_001
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = day_context['supply']
    day = day_context['day']

    # Basic budget/health guardrails
    if my_status['budget'] <= 0:
        return 0

    # Collect alive opponents and their yesterday bids
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    # If no opponents, bid just enough to cover our requirement when possible
    if not alive_opps:
        # If supply can satisfy us alone, bid moderately; else bid higher to avoid no-water days.
        if supply >= WATER_REQ:
            return min(my_status['budget'], int(DAILY_SALARY * 0.45))
        return min(my_status['budget'], int(DAILY_SALARY * 0.75))

    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Determine aggressiveness from yesterday
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = 0.0
    if len(yesterday_bids) >= 2:
        sorted_b = sorted(yesterday_bids, reverse=True)
        second_prev_bid = sorted_b[1]

    # Supply pressure: tighter supply implies higher chance of no-water
    # Use a smooth factor around requirement.
    if supply <= float(WATER_REQ):
        supply_pressure = 1.0
    elif supply <= float(WATER_REQ) * 1.3:
        supply_pressure = 0.7
    else:
        supply_pressure = 0.45

    # HP pressure: low HP should bid more
    hp = my_status.get('hp', 0)
    if hp <= 2:
        hp_pressure = 1.0
    elif hp <= 3:
        hp_pressure = 0.75
    else:
        hp_pressure = 0.5

    # If someone was aggressive yesterday, try to slightly outbid to secure allocation.
    aggressive_threshold = DAILY_SALARY * 0.85

    if highest_prev_bid >= aggressive_threshold:
        # Outbid by a small increment, scaled by supply/HP pressure.
        target = highest_prev_bid + (DAILY_SALARY * 0.05) * (0.7 + 0.6 * supply_pressure) * (0.7 + 0.6 * hp_pressure)
        # If we can, cap at a fraction of daily salary to avoid overspending.
        cap = DAILY_SALARY * (0.95 if hp <= 2 else 0.7)
        bid = min(target, cap)
    else:
        # Conservative baseline: enough to compete but not waste budget.
        # Use second-highest if available to avoid overpaying.
        baseline = max(DAILY_SALARY * 0.45, second_prev_bid + (DAILY_SALARY * 0.03))
        bid = baseline * (0.85 + 0.4 * supply_pressure) * (0.8 + 0.4 * hp_pressure)

    # If we have many no-water days already, increase urgency.
    no_water_days = my_status.get('no_water_days', 0)
    if no_water_days >= 2:
        bid *= 1.15
    if no_water_days >= 3:
        bid *= 1.25

    # Convert to int bid and clamp to budget
    try:
        bid_int = int(bid)
    except Exception:
        bid_int = int(DAILY_SALARY * 0.5)

    if bid_int < 0:
        bid_int = 0

    return min(my_status['budget'], bid_int)
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

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', True):
            alive_opps.append(opp)

    # If we can't win, still try to keep hp from collapsing.
    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * (0.35 if hp > 3 else 0.9)))

    # Read yesterday bids to infer aggressiveness.
    prev_bids = []
    prev_max = 0.0
    prev_min = None
    for opp in alive_opps:
        trace = opp.get('previous_trace', {}) or {}
        bid = trace.get('bid', None)
        if bid is not None:
            try:
                b = float(bid)
            except Exception:
                continue
            prev_bids.append(b)
            if b > prev_max:
                prev_max = b
            if prev_min is None or b < prev_min:
                prev_min = b

    # Aggression signals from yesterday.
    # Cindy: high average bids and survived -> likely bidding high again.
    # Alex: died early after high bids -> may reduce, but we can't rely on it.
    # Use hp/no_water_days to decide urgency.
    urgent = (hp <= 2.5) or (no_water_days >= 2)

    # Supply scaling: when supply is low, water is scarcer -> need stronger bids.
    # Map supply in [15,25] to a multiplier in [1.0, 1.35] for bid pressure.
    if MAX_SUPPLY > MIN_SUPPLY:
        scarcity = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        scarcity = 0.5
    scarcity = max(0.0, min(1.0, float(scarcity)))
    pressure_mult = 1.0 + 0.35 * scarcity

    # Baseline bid: aim to beat typical mid-range bids without matching top bids.
    # If yesterday's max bid was very high, avoid overpaying; bid around 60-75% of it.
    if prev_bids:
        target = prev_max * (0.68 if not urgent else 0.82)
        # Also ensure we bid at least a fraction of DAILY_SALARY to compete.
        floor_bid = DAILY_SALARY * (0.45 if not urgent else 0.75)
        bid = max(floor_bid, target)
    else:
        bid = DAILY_SALARY * (0.55 if not urgent else 0.8)

    bid *= pressure_mult

    # Cap by budget; also avoid wasting budget when hp is healthy.
    if not urgent and hp > 5:
        bid_cap = DAILY_SALARY * 0.65
    elif not urgent:
        bid_cap = DAILY_SALARY * 0.85
    else:
        bid_cap = DAILY_SALARY * 1.0

    bid = min(bid, bid_cap)
    bid = max(0.0, min(budget, bid))

    # Final safety: if budget is too low, bid whatever remains.
    if budget <= 1.0:
        return max(0.0, budget)

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

    supply = day_context['supply']
    day = day_context['day']

    # Alive opponents and their yesterday bids
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

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

    # Pressure-based target: if opponents were bidding high yesterday, we must match/beat to secure water.
    # Use our hp as survival pressure.
    hp = my_status['hp']
    budget = my_status['budget']

    # Estimate how many successful water units we might need from today's supply context.
    # (We only need to decide a bid; keep it simple and robust.)
    # If supply is low, competition likely increases -> bid more.
    supply_low = supply <= float((MIN_SUPPLY + MAX_SUPPLY) / 2.0)

    # Base aggressiveness
    if hp <= 2:
        base = DAILY_SALARY * 0.92
    elif hp <= 4:
        base = DAILY_SALARY * 0.70
    else:
        base = DAILY_SALARY * 0.55

    # If opponents pushed hard yesterday, increase to just above them when affordable.
    # Keep a small increment to win without excessive waste.
    if highest_prev_bid >= DAILY_SALARY * 0.80:
        target = max(base, highest_prev_bid + 2.0)
    else:
        target = base

    # If supply is low, add a bit more to secure allocation.
    if supply_low:
        target *= 1.08

    # Clamp by budget and keep within a reasonable fraction of daily salary.
    # Also prevent bidding beyond what would guarantee waste.
    upper_cap = min(budget, DAILY_SALARY * 1.25)
    bid = min(target, upper_cap)

    # Ensure bid is non-negative and not NaN.
    if bid != bid or bid < 0:
        bid = 0.0

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

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append(o)

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from alive opponents (immediate reaction only)
    yesterday_bids = []
    for o in alive:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Estimate how competitive the field was yesterday
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        second_prev = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev
    else:
        highest_prev = 0.0
        second_prev = 0.0

    # Target bid logic:
    # - If others were extremely aggressive (>= 85% of salary), only overtake if we can afford it.
    # - Otherwise, bid moderately to beat typical bids.
    # - Scale with our urgency (hp and no_water_days).
    urgency = 0.0
    if hp <= 2.0:
        urgency += 1.0
    if no_water_days >= 2:
        urgency += 0.7
    if hp <= 4.0:
        urgency += 0.4

    # Base competitiveness threshold based on supply (tighter supply -> higher chance we must win)
    # supply is between 15 and 25; map to [0,1]
    supply_norm = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
        if supply_norm < 0.0:
            supply_norm = 0.0
        if supply_norm > 1.0:
            supply_norm = 1.0

    # When supply is low, we need to be more aggressive.
    aggressiveness = 0.55 + (1.0 - supply_norm) * 0.25 + urgency * 0.25
    if aggressiveness > 0.95:
        aggressiveness = 0.95

    # Determine a candidate bid relative to yesterday's highest/typical
    # Use a small overbid to beat the likely winner without matching the full highest.
    candidate = None
    if highest_prev >= DAILY_SALARY * 0.85:
        # Cindy/David-like behavior: they overbid; avoid matching exactly unless urgent.
        # Bid around 0.65-0.9 of salary depending on urgency.
        candidate = DAILY_SALARY * (0.65 + 0.25 * urgency)
        # Also ensure we can beat the top if we must
        candidate = max(candidate, second_prev + 1.5)
    else:
        # Moderate bids: bid around (0.45-0.8) salary and slightly above second_prev
        candidate = DAILY_SALARY * aggressiveness
        if second_prev > 0.0:
            candidate = max(candidate, second_prev + 1.0)

    # If our HP is very low, push harder; if HP is high, conserve.
    if hp <= 2.0:
        candidate = max(candidate, DAILY_SALARY * 0.9)
    elif hp >= 8.0 and urgency < 0.4:
        candidate = min(candidate, DAILY_SALARY * 0.6)

    # Convert to final bid constrained by budget.
    bid = max(0.0, min(budget, candidate))

    # Safety: if budget is tiny, bid what we can.
    if bid <= 0.0:
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        try:
            if bool(o.get('alive', False)):
                alive_opps.append((oid, o))
        except Exception:
            pass

    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace.
    prev_bids = []
    prev_by_id = {}
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                b = float(bid)
                prev_bids.append(b)
                prev_by_id[oid] = b
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_highest_prev_bid = 0.0
    if len(prev_bids) >= 2:
        sorted_b = sorted(prev_bids, reverse=True)
        second_highest_prev_bid = float(sorted_b[1])

    # Pressure estimate: Cindy appears to outbid; Eric died with low bids.
    # Use highest_prev_bid as proxy for how expensive it is to win today.
    # If supply is high, we can bid lower because winning is easier.
    # If supply is low, bid higher to secure.
    supply_norm = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    # supply_norm in [0,1] ideally
    if supply_norm < 0.0:
        supply_norm = 0.0
    if supply_norm > 1.0:
        supply_norm = 1.0

    # Base bid target depending on our urgency.
    urgency = 0
    if my_hp <= 2:
        urgency = 2
    elif my_hp <= 4:
        urgency = 1
    if my_no_water_days >= 2:
        urgency = max(urgency, 1)

    # Determine a bid ceiling we are willing to pay.
    # Keep budget for future days; scale with urgency.
    if urgency == 2:
        budget_cap = DAILY_SALARY * 0.95
    elif urgency == 1:
        budget_cap = DAILY_SALARY * 0.7
    else:
        budget_cap = DAILY_SALARY * 0.55

    budget_cap = min(budget_cap, my_budget)

    # If yesterday pressure was high (someone like Cindy bidding ~135), we either match slightly above
    # or back off to avoid overpaying.
    high_pressure = highest_prev_bid >= DAILY_SALARY * 0.85

    # If supply is low, we should be more competitive.
    competitiveness = 0.35 + (1.0 - supply_norm) * 0.4  # 0.35..0.75

    if high_pressure:
        if urgency >= 1:
            # Try to outbid the second-highest slightly; if we don't win, still survive.
            target = second_highest_prev_bid + 2.5 + competitiveness * 5.0
        else:
            # Back off: bid enough to contend but not chase the top.
            target = min(budget_cap, (second_highest_prev_bid + 1.5) * 0.9 + 8.0)
    else:
        # Low/medium pressure: bid around a fraction of last highest plus a small premium.
        target = (highest_prev_bid * 0.55) + (competitiveness * 25.0) + 5.0

    # Ensure we don't bid more than budget cap and keep non-negative.
    bid = max(0.0, min(float(target), float(budget_cap)))

    # If our hp is very healthy and supply is high, bid minimal to conserve budget.
    if my_hp >= 7 and supply_norm > 0.5 and urgency == 0:
        bid = min(bid, DAILY_SALARY * 0.35)

    # If we are in danger, ensure a higher bid.
    if urgency == 2:
        bid = max(bid, DAILY_SALARY * 0.6)

    # Final clamp to budget.
    if my_budget <= 0.0:
        return 0.0
    bid = min(bid, my_budget)

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
    day = day_context.get('day', 0)

    # If we are already in trouble, prioritize survival.
    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    if not alive_opponents:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read only yesterday's immediate behavior from previous_trace.
    prev_bids = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                prev_bids.append(float(bid))
            except Exception:
                pass

    # Estimate how competitive the market was yesterday.
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    # Supply pressure: how many full water units exist.
    # Each agent needs WATER_REQ per day; supply is total.
    # Convert to an integer count of full units to avoid float index issues.
    units = int(supply // float(WATER_REQ))
    if units < 1:
        units = 1

    # Determine aggressiveness threshold from yesterday.
    # Cindy/Alex were bidding around ~95-98 avg; use that as a signal.
    competitive = highest_prev_bid >= (DAILY_SALARY * 0.85) or avg_prev_bid >= (DAILY_SALARY * 0.8)

    # Base bid depends on whether we are at risk.
    risk = 0
    if hp <= 2:
        risk += 2
    if no_water_days >= 1:
        risk += 1

    # If supply is tight (few units), bid closer to competitive band.
    tight_supply = units <= 2  # with supply 15-25 and WATER_REQ=9, units mostly 1-2

    # Compute target bid.
    if risk >= 2:
        # Survival mode: be willing to match aggression.
        if competitive and tight_supply:
            target = max(avg_prev_bid, highest_prev_bid * 0.9)
        else:
            target = DAILY_SALARY * 0.85
    else:
        # Healthy mode: avoid overpaying.
        if competitive and tight_supply:
            target = max(DAILY_SALARY * 0.65, avg_prev_bid * 0.75)
        elif competitive:
            target = max(DAILY_SALARY * 0.55, avg_prev_bid * 0.6)
        else:
            # If others weren't aggressive yesterday, bid moderately.
            target = DAILY_SALARY * 0.48

    # Cap by budget and keep within a reasonable range.
    # Also ensure we don't bid negative.
    bid = max(0.0, min(budget, float(target)))

    # If budget is extremely low, still bid something only if we must.
    if budget <= 1.0:
        return 0.0 if risk == 0 else 1.0

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
    day = day_context.get('day', 0)

    my_hp = float(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', True):
            alive_opps.append((oid, o))

    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday immediate behavior from previous_trace only
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
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

    # Estimate how many water units are likely needed/available this round
    # (We only use it to scale our bid; actual allocation depends on game rules.)
    supply_units = supply / float(WATER_REQ) if WATER_REQ > 0 else 0.0

    # Pressure-based adjustment: if we are already on low hp or have had no water recently, bid more.
    low_hp = my_hp <= 2.5
    critical_no_water = my_no_water_days >= 2

    # If someone yesterday bid extremely high, assume they were trying to secure survival.
    # We counter with a moderate-to-strong bid, but not full send unless we are critical.
    extreme_threshold = DAILY_SALARY * 0.85  # 76.5

    if highest_prev_bid >= extreme_threshold:
        if low_hp or critical_no_water:
            bid = DAILY_SALARY * 0.95
        else:
            # Shade above the likely second-best pressure to avoid losing to the extreme bidder.
            bid = max(DAILY_SALARY * 0.6, second_prev_bid + 2.0)
    else:
        # If no one was extremely aggressive, keep bid moderate to win at lower price.
        # Use supply_units to slightly reduce bid when supply is high.
        # supply_units near 1.0 => tight; near 2.7 => ample.
        tightness = 1.0
        if supply_units > 0:
            tightness = max(0.6, min(1.2, 1.6 / supply_units))
        bid = DAILY_SALARY * 0.52 * tightness

        if low_hp or critical_no_water:
            bid = max(bid, DAILY_SALARY * 0.75)

    # Final safety caps
    bid = float(bid)
    if my_budget <= 0:
        return 0.0

    # Ensure we don't exceed budget; also keep bids within a reasonable upper bound.
    upper = min(my_budget, DAILY_SALARY * 1.2)
    bid = min(max(0.0, bid), upper)

    # Tiny day-based dithering to avoid exact ties (still deterministic-ish)
    # (day may be int; use it safely)
    try:
        day_int = int(day)
    except Exception:
        day_int = 0
    if day_int % 3 == 1:
        bid *= 1.01
    elif day_int % 3 == 2:
        bid *= 0.99

    bid = min(max(0.0, bid), upper)
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

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday bids from previous_trace for immediate reaction
    yesterday_bids = []
    yesterday_pressures = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                yesterday_bids.append(float(bid))
            except Exception:
                pass
        # Use yesterday hp_after/status if available to infer pressure
        hp_after = prev.get('hp_after', None)
        if hp_after is not None:
            try:
                yesterday_pressures.append(float(hp_after))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Determine aggressiveness from supply level and yesterday's competitive pressure
    # Supply range 15-25: higher supply reduces competition, so we can bid slightly less.
    supply_ratio = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Base target bid: if others bid near/above 0.85*DAILY_SALARY, match closer.
    pressure_threshold = DAILY_SALARY * 0.85

    # If I'm in danger, bid to secure water.
    if hp <= 2.0 or no_water_days >= 2:
        target = DAILY_SALARY * (0.92 - 0.25 * supply_ratio)
    else:
        if highest_prev_bid >= pressure_threshold:
            # They were willing to spend heavily; bid moderately high to avoid losing.
            target = max(highest_prev_bid * 0.72, DAILY_SALARY * (0.55 - 0.15 * supply_ratio))
        else:
            # Competition lower; bid around a mid value, slightly increasing if my HP is lower.
            hp_factor = 0.55 if hp >= 6 else 0.62
            target = DAILY_SALARY * (hp_factor - 0.12 * supply_ratio)

    # Convert target into a safe spend cap
    # Keep some budget for later days; spend more when supply is high and day is later.
    # Episode is 10 days; day_context.day should be 1..10.
    day_int = int(day)
    day_frac = (day_int - 1) / 9.0 if 9.0 != 0 else 0.0
    day_frac = max(0.0, min(1.0, day_frac))

    # Spend cap: more aggressive later, but never exceed budget.
    spend_cap = budget * (0.55 + 0.25 * day_frac)

    bid = min(budget, spend_cap, target)

    # Ensure non-negative and at least a minimal competitive bid when budget allows.
    if bid < 0.0:
        bid = 0.0

    # If budget is tiny, bid it all.
    if budget <= 5.0:
        return budget

    # Add a small increment when we expect competition (highest_prev_bid high) to avoid ties/losing.
    if highest_prev_bid >= pressure_threshold and bid + 2.0 <= budget:
        bid += 2.0

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
    day = int(day_context.get('day', 0))

    # Alive opponents
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    if not alive:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Extract yesterday bids for immediate reaction
    prev_bids = []
    prev_by_id = {}
    for oid, o in alive:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                bval = float(b)
                prev_bids.append(bval)
                prev_by_id[oid] = bval
            except Exception:
                pass

    # If we can't read bids, use a conservative default
    if not prev_bids:
        base = DAILY_SALARY * (0.55 if my_status['hp'] > 2 else 0.9)
        return float(min(my_status['budget'], base))

    highest_prev_bid = max(prev_bids)
    second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev_bid

    # Pressure estimate: if someone was willing to pay near/above ~salary, expect aggressive bidding.
    aggressive = highest_prev_bid >= (DAILY_SALARY * 0.85)

    # Supply-based escalation: with higher supply, we can safely outbid slightly less.
    # Map supply to a multiplier in [0.8, 1.2]
    if MAX_SUPPLY > MIN_SUPPLY:
        t = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        t = 0.5
    if t < 0.0:
        t = 0.0
    if t > 1.0:
        t = 1.0
    supply_mult = 0.8 + 0.4 * t

    # Our urgency
    hp = int(my_status.get('hp', 0))
    no_water_days = int(my_status.get('no_water_days', 0))
    urgent = (hp <= 2) or (no_water_days >= 2)

    # Core strategy:
    # - If aggressive yesterday, target just above the likely second bidder to secure water.
    # - Otherwise, bid around a mid fraction to conserve budget.
    if aggressive:
        # Bid slightly above second highest to avoid overpaying while still beating most.
        target = second_prev_bid + 2.0
        # If we are very urgent, increase to ensure we win.
        if urgent:
            target = max(target, highest_prev_bid * 0.98)
        target *= supply_mult
    else:
        # Conservative: aim to be competitive but not maximal.
        if urgent:
            target = DAILY_SALARY * 0.85 * supply_mult
        else:
            # If supply is high, can bid lower and still win due to reduced competition.
            target = DAILY_SALARY * (0.45 + 0.1 * t) * supply_mult

        # Also cap relative to previous highest to avoid runaway spending.
        target = min(target, highest_prev_bid + 5.0)

    # Final safety: cannot exceed budget; also keep non-negative
    budget = float(my_status.get('budget', 0.0))
    bid = float(target)
    if bid < 0.0:
        bid = 0.0
    if bid > budget:
        bid = budget

    # If budget is extremely low, spend enough to survive this day if possible
    if budget <= DAILY_SALARY * 0.2:
        # Prefer to bid near the budget to avoid immediate death.
        bid = budget

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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    # Identify alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        try:
            if o.get('alive', False):
                alive_opps.append(o)
        except Exception:
            continue

    if not alive_opps:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Read yesterday bids from previous_trace only (immediate reaction)
    prev_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Pressure estimate: if someone was bidding near/above a strong fraction of salary, they likely contest.
    strong_pressure = highest_prev_bid >= (DAILY_SALARY * 0.85)

    # Supply factor: with more supply, winning water is cheaper; with less supply, contest harder.
    # Map supply in [15,25] to [0.2, 1.0]
    if MAX_SUPPLY != MIN_SUPPLY:
        supply_factor = 0.2 + 0.8 * ((supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY))
    else:
        supply_factor = 0.6
    supply_factor = max(0.2, min(1.0, float(supply_factor)))

    # Base target bid:
    # - If strong pressure, bid higher to avoid falling behind.
    # - Otherwise, bid moderate.
    if strong_pressure:
        target = DAILY_SALARY * (0.45 + 0.25 * supply_factor)
        # If their previous max bid is very high, match slightly below it to reduce overspend.
        if highest_prev_bid > 0:
            target = min(target, highest_prev_bid * 0.95)
    else:
        target = DAILY_SALARY * (0.35 + 0.20 * supply_factor)
        if highest_prev_bid > 0:
            # Stay close enough to beat average contestants.
            target = max(target, highest_prev_bid * 0.55)

    # Urgency adjustments based on my HP and no-water streak
    if my_hp <= 2 or my_no_water_days >= 2:
        target *= 1.35
    elif my_hp <= 4:
        target *= 1.15

    # Ensure we don't try to bid more than budget; also keep a minimum contest bid if we can.
    target = float(target)
    if my_budget <= 0:
        return 0.0

    # Cap to budget with a small safety margin
    bid = min(my_budget, target)

    # If budget is low, still bid enough to avoid immediate death pressure if HP is critical
    if my_hp <= 2:
        bid = max(bid, min(my_budget, DAILY_SALARY * 0.9))

    # Final clamp
    if bid < 0:
        bid = 0.0
    return float(bid)
"""
