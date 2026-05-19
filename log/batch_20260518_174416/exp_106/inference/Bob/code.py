# ============================================================
# Experiment: exp_106
# Agent: Bob
# Source: exp_106
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context['supply'])
    day = day_context['day']

    alive_opps = []
    for opp in opponents_status.values():
        if opp.get('alive', True):
            alive_opps.append(opp)

    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Extract yesterday bids from previous_trace
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Base bid intensity from yesterday behavior
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents were strongly pressuring, we defend more.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status['hp'] > 3:
                bid = DAILY_SALARY * 0.32
            else:
                bid = DAILY_SALARY * 0.9
        else:
            # If they were cautious, we bid enough to secure while not overpaying.
            # Increase slightly above their max to gain allocation.
            bid = max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5)
    else:
        # No trace info: bid based on our health.
        if my_status['hp'] <= 2:
            bid = DAILY_SALARY * 0.85
        else:
            bid = DAILY_SALARY * 0.55

    # Supply-aware adjustment: tighter supply -> slightly higher bid.
    # supply is in [15,25]; map to a multiplier in [~1.1, ~0.9]
    tightness = (25.0 - supply) / 10.0  # 0..1
    bid *= (1.0 + 0.2 * tightness)

    # Ensure we never bid more than our budget.
    bid = min(float(my_status['budget']), float(bid))

    # If we are at risk (many no-water days), raise bid.
    no_water_days = float(my_status.get('no_water_days', 0))
    if no_water_days >= 2:
        bid = min(float(my_status['budget']), max(bid, DAILY_SALARY * 0.75))

    # Final safety clamp
    if bid < 0:
        bid = 0.0
    return bid
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

    supply = day_context['supply']
    day = day_context['day']

    # Identify alive opponents and extract yesterday bids
    alive_opps = []
    yesterday_bids = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)
            prev = o.get('previous_trace', {}) or {}
            b = prev.get('bid', None)
            if b is not None:
                try:
                    yesterday_bids.append(float(b))
                except Exception:
                    pass

    # If no opponents are alive, bid minimally
    if not alive_opps:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.4))

    # Use yesterday's max bid as a proxy for current threat
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how competitive today likely is from supply level
    # Lower supply => more competition => bid closer to opponents' pressure
    # supply is float; keep computations numeric only.
    supply_ratio = (float(supply) - float(MIN_SUPPLY)) / (float(MAX_SUPPLY) - float(MIN_SUPPLY))
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Base aggressiveness: undercut if I'm healthy, match if low hp
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status.get('no_water_days', 0))

    # Thresholds
    low_hp = 3.0
    critical_no_water = 2

    # If I'm in danger, bid near/at the highest previous bid
    if hp <= low_hp or no_water_days >= critical_no_water:
        target = highest_prev_bid + 2.0
    else:
        # If opponents were aggressive, undercut slightly; else bid moderately
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            target = highest_prev_bid - (8.0 + 6.0 * (1.0 - supply_ratio))
        else:
            target = max(DAILY_SALARY * (0.45 + 0.2 * supply_ratio), highest_prev_bid * 0.6)

    # Clamp target to feasible range
    # Keep some budget to survive remaining days; but we don't know exact remaining days, use conservative cap.
    max_affordable = budget
    # If budget is tight, scale down.
    if max_affordable <= 0:
        return 0.0

    # Safety cap: don't spend more than ~70% of budget unless critical.
    spend_cap = budget * (0.7 if (hp > low_hp and no_water_days < critical_no_water) else 0.95)
    target = min(target, spend_cap, max_affordable)

    # Ensure non-negative
    if target < 0:
        target = 0.0

    # Add a small day-based jitter to avoid ties; deterministic via day
    jitter = 1.0 + (int(day) % 3) * 0.5
    target = target + jitter

    # Final clamp
    target = min(target, max_affordable)
    return float(target)
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

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opponents = [o for o in opponents_status.values() if o.get('alive')]
    if not alive_opponents:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from immediate previous_trace only
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Pressure estimate: if someone yesterday bid very high, they likely competed hard.
    # Cindy maxed extremely high in trace, so treat that as a sign to avoid mirroring her waste.
    high_pressure = highest_prev_bid >= (DAILY_SALARY * 1.1)

    # Supply tightness: if supply is near minimum, winning water matters more.
    tight = supply <= (MIN_SUPPLY + 2.0)
    comfortable = supply >= (MAX_SUPPLY - 2.0)

    # Urgency from our HP / consecutive no-water days
    urgent = (hp <= 2.5) or (no_water_days >= 2)
    moderate_urgent = (hp <= 4.0) or (no_water_days >= 1)

    # Base bid policy
    # - If urgent or tight: bid mid-high to secure water.
    # - If comfortable and not urgent: bid lower to conserve budget.
    if urgent:
        target = DAILY_SALARY * (0.75 if high_pressure else 0.95)
    elif moderate_urgent:
        target = DAILY_SALARY * (0.6 if high_pressure else 0.8)
    else:
        if tight:
            target = DAILY_SALARY * (0.55 if high_pressure else 0.7)
        elif comfortable:
            target = DAILY_SALARY * 0.45
        else:
            target = DAILY_SALARY * 0.52

    # Slight reactive adjustment using yesterday highest bid, but cap to avoid Cindy-style overbidding.
    if high_pressure:
        # If others were bidding hard, we can raise a bit but do not chase extreme maxima.
        target = min(target + (DAILY_SALARY * 0.05), DAILY_SALARY * 0.95)
    else:
        # If no one was bidding crazy, we can bid near target.
        target = max(target - (DAILY_SALARY * 0.03), DAILY_SALARY * 0.35)

    # Final constraints: must be within budget and non-negative
    bid = max(0.0, min(budget, target))

    # If budget is very low, still bid enough to avoid guaranteed starvation if possible.
    if budget <= DAILY_SALARY * 0.2:
        bid = min(budget, max(0.0, DAILY_SALARY * 0.25))

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
    # Ensure integer indices if ever used
    supply_int = int(round(supply))

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Read yesterday bids from previous_trace
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate today's urgency based on hp/no-water days
    urgency = 0
    if my_hp <= 2:
        urgency += 3
    elif my_hp <= 4:
        urgency += 2
    elif my_hp <= 6:
        urgency += 1

    if my_no_water >= 2:
        urgency += 2
    elif my_no_water >= 1:
        urgency += 1

    # If someone previously bid very close to salary, they likely continue pressure.
    # Increase just enough to not get outbid, but avoid overpaying.
    pressure_threshold = DAILY_SALARY * 0.85

    # Base bid depends on supply: when supply is higher, bid lower.
    # supply_int is within [15,25] typically.
    if supply_int <= MIN_SUPPLY:
        base = DAILY_SALARY * 0.6
    elif supply_int >= MAX_SUPPLY:
        base = DAILY_SALARY * 0.45
    else:
        # linear interpolation between 0.6 and 0.45
        t = (supply_int - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
        base = DAILY_SALARY * (0.6 - 0.15 * t)

    if highest_prev_bid >= pressure_threshold:
        # Match pressure modestly; if low hp, bid higher.
        target = max(base, highest_prev_bid * 0.92)
        if urgency >= 3:
            target = max(target, DAILY_SALARY * 0.75)
        elif urgency == 2:
            target = max(target, DAILY_SALARY * 0.65)
    else:
        # No extreme pressure: bid around base, slightly up if urgent.
        target = base
        if urgency >= 3:
            target = max(target, DAILY_SALARY * 0.7)
        elif urgency == 2:
            target = max(target, DAILY_SALARY * 0.6)
        elif urgency == 1:
            target = max(target, DAILY_SALARY * 0.52)

        # If yesterday's highest bid was moderate, add a small premium to avoid losing ties.
        if highest_prev_bid > 0:
            target = max(target, highest_prev_bid + 2.0)

    # Budget safety: never bid more than budget.
    # Also, if budget is low, scale down to preserve survival.
    if my_budget <= 0:
        return 0.0

    # Cap by a fraction of budget to reduce risk of going to 0 too early.
    budget_cap = my_budget
    if my_budget < DAILY_SALARY:
        budget_cap = my_budget * 0.9

    bid = min(target, budget_cap)

    # If very low hp, ensure we don't underbid too much.
    if my_hp <= 2 and my_budget > 0:
        bid = max(bid, min(my_budget, DAILY_SALARY * 0.85))

    # Final clamp
    if bid < 0:
        bid = 0.0
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Identify alive opponents and use only their previous_trace (yesterday)
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        # If nobody is alive, spend conservatively but ensure survival
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.4))

    # Extract yesterday bids
    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Determine pressure from opponent bids
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_highest_prev_bid = 0.0
    if len(yesterday_bids) >= 2:
        sorted_b = sorted(yesterday_bids, reverse=True)
        second_highest_prev_bid = float(sorted_b[1])

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Supply-based urgency: higher supply reduces need to overbid
    # Target water fraction roughly proportional to (WATER_REQ / supply)
    # but we translate into a bid using opponent pressure.
    supply_ratio = WATER_REQ / max(1e-6, supply)

    # Base bid: ensure we can afford a meaningful bid but not overspend
    # If low hp or accumulating no-water days, bid harder.
    if my_hp <= 2.0 or no_water_days >= 2:
        base = DAILY_SALARY * 0.85
    elif my_hp <= 4.0 or no_water_days >= 1:
        base = DAILY_SALARY * 0.65
    else:
        base = DAILY_SALARY * 0.52

    # If Cindy/Alex-like behavior suggests aggressive bidding, match just above likely clearing price.
    # We don't know identities, so use highest/second-highest from yesterday.
    # Strategy: if highest prev bid is high relative to our base, bid slightly above second-highest.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Aggressive meta: bid near the top but cap by budget.
        # Add a small increment over second-highest to improve winning odds.
        bid = max(base, second_highest_prev_bid + 2.0)
    else:
        # Moderate meta: bid around base but adjust upward if supply is low.
        # When supply is close to MIN_SUPPLY, we need more certainty.
        low_supply_factor = 1.0 + (float(MIN_SUPPLY) - supply) / max(1e-6, float(MIN_SUPPLY))
        if low_supply_factor < 0.85:
            low_supply_factor = 0.85
        if low_supply_factor > 1.25:
            low_supply_factor = 1.25
        bid = base * low_supply_factor

    # Convert bid into an affordability-aware final bid.
    # Also avoid bidding above budget.
    if my_budget <= 0.0:
        return 0.0

    # Additional safeguard: if our budget is very low, prioritize survival over winning.
    # Keep some buffer for later days.
    budget_buffer = 0.15 * my_budget
    max_affordable = max(0.0, my_budget - budget_buffer)

    # Final cap: never exceed a reasonable multiple of our daily salary.
    # (Prevents runaway spending.)
    cap = DAILY_SALARY * 1.1
    if cap > max_affordable:
        cap = max_affordable

    final_bid = bid

    # If supply is very high (near MAX_SUPPLY), reduce bid to save budget.
    if supply >= 0.9 * MAX_SUPPLY:
        final_bid = min(final_bid, DAILY_SALARY * 0.55)

    # If supply is very low, increase slightly.
    if supply <= 1.05 * MIN_SUPPLY:
        final_bid = max(final_bid, DAILY_SALARY * 0.6)

    # Ensure numeric bounds
    if final_bid < 0.0:
        final_bid = 0.0
    if final_bid > cap:
        final_bid = cap

    return float(final_bid)
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

    supply = day_context['supply']
    day = day_context['day']

    # Determine our urgency
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    # Collect yesterday bids and infer pressure
    alive_opps = [o for o in opponents_status.values() if o.get('alive', False)]
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Baseline bid depends on our hp/no_water_days
    if hp <= 1:
        urgency_factor = 1.0
    elif hp <= 3:
        urgency_factor = 0.85
    elif no_water_days >= 2:
        urgency_factor = 0.7
    else:
        urgency_factor = 0.55

    # Supply favorability: more supply -> we can bid slightly lower and still get water
    # Convert supply to a discrete tier for index safety
    tier = int((supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) * 2)  # 0..2
    if tier < 0:
        tier = 0
    if tier > 2:
        tier = 2

    # Pressure from opponents yesterday
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        second_prev = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev
        # If someone was bidding extremely high, we must contest
        if highest_prev >= DAILY_SALARY * 1.45:
            contest = 1.0
        elif highest_prev >= DAILY_SALARY * 1.05:
            contest = 0.85
        elif second_prev >= DAILY_SALARY * 0.9:
            contest = 0.7
        else:
            contest = 0.55
    else:
        contest = 0.6

    # Target bid construction
    # When contest is high, bid around a bit above the median/second-highest to steal water.
    if yesterday_bids:
        sorted_bids = sorted(yesterday_bids)
        median_prev = sorted_bids[len(sorted_bids)//2]
        # Slightly outbid median/second-highest depending on contest
        target = median_prev + (DAILY_SALARY * 0.08) * contest
        # Also ensure we don't underbid too much when contest is high
        target = max(target, DAILY_SALARY * (0.45 + 0.35 * contest) * (1.05 - 0.1 * tier))
    else:
        target = DAILY_SALARY * (0.5 + 0.25 * contest) * (1.05 - 0.1 * tier)

    # Apply urgency
    target *= (0.85 + 0.3 * urgency_factor)

    # Cap by budget and keep some cushion
    # If budget is low, bid closer to budget to avoid wasting survival.
    cushion_ratio = 0.25 if budget > DAILY_SALARY else 0.1
    max_affordable = budget * (1.0 - cushion_ratio)
    bid = min(max_affordable, target)

    # Ensure non-negative
    if bid < 0:
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

    # If no opponents alive, conserve budget.
    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace only.
    prev_bids = []
    prev_hp_after = []
    for oid, o in alive_opps:
        pt = o.get('previous_trace', {}) or {}
        b = pt.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
                prev_hp_after.append(int(pt.get('hp_after', o.get('hp', 0))))
            except Exception:
                pass

    # Estimate opponent pressure.
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev_bid

    # Supply-based aggressiveness: medium scenario => supply often in [15,25].
    # If supply is high, competition is lower; if low, competition is higher.
    if supply <= (MIN_SUPPLY + MAX_SUPPLY) / 2.0:
        supply_factor = 1.0
    else:
        supply_factor = 0.75

    # If I'm in danger (low hp or many no-water days), bid harder.
    danger = (my_hp <= 2) or (my_no_water_days >= 2)

    # Cindy likely paid to survive (yesterday avg ~142). If she was high bidder, match/just beat.
    # Strategy: bid slightly above the highest yesterday bid when my situation is not safe.
    target = None
    if highest_prev_bid > 0:
        if danger:
            # Just over the likely winning bid.
            target = (highest_prev_bid + 5.0) * supply_factor
        else:
            # Moderate: try to beat without overpaying.
            target = max(DAILY_SALARY * 0.55, (second_prev_bid + 3.0) * supply_factor)
            # If Cindy was extremely aggressive, still tilt up.
            if highest_prev_bid >= DAILY_SALARY * 1.2:
                target = max(target, (highest_prev_bid - 10.0) * supply_factor)
    else:
        target = DAILY_SALARY * (0.9 if danger else 0.6) * supply_factor

    # Cap by budget.
    bid = max(0.0, min(my_budget, float(target)))

    # Ensure we don't bid trivially low when supply is scarce.
    if supply <= MIN_SUPPLY + 1.0:
        bid = max(bid, DAILY_SALARY * (0.7 if danger else 0.55))

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
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace only
    prev_bids = []
    for oid, o in alive:
        pt = o.get('previous_trace', None)
        if isinstance(pt, dict):
            b = pt.get('bid', None)
            if b is not None:
                prev_bids.append(float(b))
        elif isinstance(pt, list) and pt:
            # If somehow stored as list of events, take last element only
            last = pt[-1]
            if isinstance(last, dict) and last.get('bid', None) is not None:
                prev_bids.append(float(last['bid']))

    # Pressure estimate: how hard others were bidding yesterday
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        avg_prev_bid = sum(prev_bids) / float(len(prev_bids))
    else:
        highest_prev_bid = 0.0
        avg_prev_bid = 0.0

    # Convert supply to how many water units are likely available (heuristic)
    # Ensure integer indices if used (not strictly necessary here, but keep safe)
    likely_units = int(max(1.0, supply / float(WATER_REQ)))

    # Target bid: slightly above yesterday's high pressure if we can afford it
    # But back off if our hp is critical.
    if hp <= 2.0 or no_water_days >= 2:
        urgency_mult = 0.95
    elif hp <= 4.0:
        urgency_mult = 0.75
    else:
        urgency_mult = 0.6

    # If Cindy-like survivor likely bids consistently, outbid her pressure.
    # Use highest_prev_bid as a proxy.
    # If highest_prev_bid is already high relative to salary, bid close to it.
    base = max(DAILY_SALARY * 0.45, avg_prev_bid * 0.85)

    # Small day-based variation to avoid ties
    tie_break = 1.0 + (day % 3) * 0.5

    # Decide aggressiveness based on supply: lower supply => bid more to secure water
    supply_ratio = (supply - float(MIN_SUPPLY)) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    # supply_ratio near 0 means low supply => higher bid
    scarcity_mult = 1.15 - 0.3 * supply_ratio

    desired = (highest_prev_bid + tie_break) * 0.98
    desired = max(base, desired)
    desired *= urgency_mult * scarcity_mult

    # Clamp to budget and keep within reasonable bounds
    # Avoid bidding more than we can pay (budget) and don't exceed ~salary*1.2
    cap = min(budget, DAILY_SALARY * 1.2)
    bid = max(0.0, min(cap, desired))

    # If we are likely to need water units (heuristic), ensure minimum bid to compete
    min_compete = DAILY_SALARY * (0.35 if likely_units >= 2 else 0.55)
    if bid < min_compete and budget > 0:
        bid = min(budget, min_compete)

    return float(bid)
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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Extract yesterday bids from previous_trace
    yesterday_bids = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    yesterday_bids.append(float(b))
                except Exception:
                    pass

    # Base aggressiveness from yesterday
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid
    else:
        highest_prev_bid = 0.0
        second_prev_bid = 0.0

    # Estimate how tight supply is
    # If supply is near min, water is scarce: bid higher.
    scarcity = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    scarcity = max(0.0, min(1.0, scarcity))

    # If we've already gone without water, increase pressure quickly.
    urgency = 0.0
    if no_water_days >= 3:
        urgency = 0.95
    elif no_water_days == 2:
        urgency = 0.75
    elif no_water_days == 1:
        urgency = 0.45
    else:
        urgency = 0.25

    # If our hp is low, we must secure water.
    hp_pressure = 0.0
    if hp <= 1.5:
        hp_pressure = 1.0
    elif hp <= 3.0:
        hp_pressure = 0.75
    elif hp <= 5.0:
        hp_pressure = 0.45
    else:
        hp_pressure = 0.25

    # Target bid: slightly above the typical aggressive level from yesterday.
    # Use highest_prev_bid as a cap reference, but don't fully chase it.
    if highest_prev_bid > 0:
        # If others were extremely aggressive, match a fraction.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            target = highest_prev_bid * (0.55 + 0.25 * scarcity + 0.15 * hp_pressure) + (urgency * 5.0)
        else:
            target = max(second_prev_bid * 0.85, DAILY_SALARY * 0.55) + (scarcity * 10.0) + (urgency * 6.0)
    else:
        target = DAILY_SALARY * (0.55 + 0.2 * scarcity + 0.15 * hp_pressure) + (urgency * 6.0)

    # Convert to feasible bid: can't exceed budget.
    # Also avoid overbidding when budget is low.
    # Keep a floor to avoid being undercut too much when supply is scarce.
    floor_bid = DAILY_SALARY * (0.45 + 0.25 * scarcity + 0.15 * hp_pressure)
    bid = max(floor_bid, target)

    bid = min(bid, budget)

    # If budget is extremely low, still bid what we can to prevent further water loss.
    if budget <= 1.0:
        return 0.0

    # Safety: if our hp is critically low, use most of budget.
    if hp <= 2.0:
        bid = max(bid, budget * 0.75)
        bid = min(bid, budget)

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
    day = day_context.get('day', 0)

    # Alive opponents and their yesterday traces
    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive.append((opp_id, opp))

    if not alive:
        # If alone, bid just enough to likely secure water
        return float(min(my_status.get('budget', 0.0), DAILY_SALARY * 0.4))

    # Extract yesterday bids and yesterday hp_after if available
    yesterday_bids = []
    yesterday_hp_after = []
    yesterday_no_water_days = []
    for _, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass
        try:
            if 'hp_after' in prev and prev['hp_after'] is not None:
                yesterday_hp_after.append(float(prev['hp_after']))
        except Exception:
            pass
        try:
            if 'status' in prev and prev['status'] is not None:
                # status may contain no-water info; keep lightweight
                pass
        except Exception:
            pass

    # Baseline bid depends on our hp pressure
    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Supply pressure: if supply is low, water is scarce => slightly higher bids
    # Use int() for any index; here we only use arithmetic.
    scarcity = 0.0
    if supply <= float(MIN_SUPPLY):
        scarcity = 1.0
    elif supply >= float(MAX_SUPPLY):
        scarcity = 0.0
    else:
        scarcity = (float(MAX_SUPPLY) - supply) / (float(MAX_SUPPLY) - float(MIN_SUPPLY))

    # If any opponent was in danger yesterday (low hp_after), we should react
    danger = False
    if yesterday_hp_after:
        # If someone dropped below 4 yesterday, treat as danger
        if min(yesterday_hp_after) <= 3.5:
            danger = True

    # If yesterday there was a high bidding war, match a fraction to secure without overpaying
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / max(1, len(yesterday_bids))
    else:
        highest_prev_bid = 0.0
        avg_prev_bid = 0.0

    # Core strategy:
    # - If our hp is low or we've had consecutive no-water days, bid aggressively.
    # - Otherwise, bid around a moderate level below opponents' average to conserve budget.
    if my_hp <= 2.0 or no_water_days >= 2:
        target = DAILY_SALARY * (0.75 + 0.15 * scarcity)
        if danger:
            target = max(target, DAILY_SALARY * 0.9)
        # If opponents bid very high yesterday, slightly overbid
        if highest_prev_bid > DAILY_SALARY * 1.4:
            target = max(target, highest_prev_bid * 0.92)
    else:
        # Moderate bid to likely win given others conserved hp at moderate bids
        # Use avg_prev_bid as anchor, but keep a discount.
        anchor = avg_prev_bid if avg_prev_bid > 0 else DAILY_SALARY * 0.55
        # Discount to avoid bidding wars; increase with scarcity.
        target = anchor * (0.78 + 0.12 * scarcity)
        # If danger observed, reduce discount.
        if danger:
            target = anchor * (0.88 + 0.10 * scarcity)
        # If highest_prev_bid is extremely high, ensure we are not too low.
        if highest_prev_bid > 0:
            target = max(target, highest_prev_bid * 0.55)

    # Always cap by budget; also avoid bidding above a reasonable fraction of budget
    max_reasonable = my_budget
    bid = float(min(max_reasonable, target))

    # Ensure bid is non-negative
    if bid < 0.0:
        bid = 0.0

    return bid
"""
