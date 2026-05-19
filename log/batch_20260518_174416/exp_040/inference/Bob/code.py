# ============================================================
# Experiment: exp_040
# Agent: Bob
# Source: exp_040
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

    alive_opponents = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opponents:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Extract yesterday bids and urgency signals from previous_trace
    prev_bids = []
    prev_hp_after = []
    prev_no_water_days = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev['bid']))
            prev_hp_after.append(float(prev.get('hp_after', opp.get('hp', 0))))
            prev_no_water_days.append(int(prev.get('status', 0)) if isinstance(prev.get('status', 0), int) else int(opp.get('no_water_days', 0)))

    # If no meaningful trace, fall back to a conservative bid depending on our hp
    if not prev_bids:
        if my_status['hp'] <= 2:
            return float(min(my_status['budget'], DAILY_SALARY * 0.9))
        return float(min(my_status['budget'], DAILY_SALARY * 0.55))

    highest_prev_bid = max(prev_bids)
    lowest_prev_bid = min(prev_bids)

    # Estimate how many
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

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((opp_id, o))

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from immediate previous_trace only
    prev_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Use yesterday's max bid as a proxy for how hard someone is trying to secure water
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # If someone previously bid extremely high, we assume aggressive contention; adjust upward only slightly.
    aggressive = highest_prev_bid >= DAILY_SALARY * 0.85

    # Supply pressure: higher supply reduces marginal need to overbid.
    # Normalize to [0,1]
    if MAX_SUPPLY - MIN_SUPPLY > 0:
        pressure = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        pressure = 0.5
    pressure = max(0.0, min(1.0, float(pressure)))

    # Core target bid: aim to beat the low-bid cluster but avoid Cindy-style overbidding.
    # Estimate a baseline from yesterday's highest bid and a mid aggressiveness.
    # If aggressive, we bid closer to highest_prev_bid; otherwise we bid just above a typical level.
    if prev_bids:
        # Typical level: median of yesterday bids
        sorted_b = sorted(prev_bids)
        n = len(sorted_b)
        mid = sorted_b[int(n // 2)] if n > 0 else highest_prev_bid
    else:
        mid = DAILY_SALARY * 0.45

    # When my HP is low or I already missed water, I should secure water more reliably.
    urgency = 0.0
    if hp <= 2.0:
        urgency += 0.35
    if no_water_days >= 1:
        urgency += 0.25
    if hp <= 0.0:
        urgency += 0.35
    urgency = max(0.0, min(1.0, urgency))

    # Base bid fraction of salary, scaled by supply pressure (lower supply => bid higher).
    # When supply is low (pressure near 0), bid more.
    supply_adjust = 1.0 - 0.6 * pressure

    if aggressive:
        # Match contention: bid between mid and highest_prev_bid with urgency.
        target = (0.55 * mid + 0.45 * highest_prev_bid) * (0.85 + 0.3 * urgency)
    else:
        # Normal: bid slightly above the median, with urgency and supply adjustment.
        target = (mid * (1.08 + 0.15 * urgency)) * supply_adjust

    # Ensure bid is at least enough to matter; but cap to avoid budget exhaustion.
    # Also keep some budget for later days.
    min_reasonable = DAILY_SALARY * 0.35
    max_reasonable = DAILY_SALARY * (0.95 if urgency > 0.5 else 0.75)

    bid = max(min_reasonable, min(max_reasonable, target))

    # Never exceed my budget
    bid = min(bid, budget)

    # If budget is tiny, bid what we can.
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

    # Read yesterday bids from traces (immediate reaction)
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
    second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev_bid

    # Estimate how many water units are likely needed to stay safe today.
    # If supply is tight, we should bid closer to the competitive range.
    supply_ratio = supply / float(WATER_REQ)
    # target_units in [1..3] based on supply
    if supply_ratio <= 1.2:
        target_units = 1
    elif supply_ratio <= 2.2:
        target_units = 2
    else:
        target_units = 3

    # Convert units to a bid pressure. In this game, bids scale with water allocation competition.
    # Use yesterday's highest bid as a proxy for the current competitive threshold.
    # If others were aggressive (high highest_prev_bid), we slightly undercut to save budget.
    # If our hp is low or we've already missed water days, we must bid harder.
    pressure = 0.0
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # They were bidding near/above a high aggressive level.
        if my_hp <= 2 or my_no_water_days >= 1:
            pressure = highest_prev_bid + 2.0
        else:
            pressure = max(second_prev_bid + 1.5, highest_prev_bid * 0.92)
    else:
        # They were not at extreme aggression; bid enough to beat typical level.
        baseline = max(DAILY_SALARY * 0.45, second_prev_bid + 1.0)
        if my_hp <= 2 or my_no_water_days >= 2:
            baseline = max(baseline, DAILY_SALARY * 0.85)
        pressure = baseline

    # Adjust for supply tightness: lower supply => slightly higher bid to secure allocation.
    if supply <= (MIN_SUPPLY + 1.0):
        pressure *= 1.08
    elif supply >= (MAX_SUPPLY - 1.0):
        pressure *= 0.95

    # If we are very healthy, avoid overspending.
    if my_hp >= 8 and my_no_water_days == 0:
        pressure *= 0.92

    # Keep within budget and avoid negative.
    bid = max(0.0, min(my_budget, pressure))

    # Ensure at least a minimal bid if we have budget.
    if my_budget > 0 and bid < 1.0:
        bid = 1.0

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

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    # If no opponents alive, conserve budget.
    if not alive_opponents:
        return max(0.0, min(budget, DAILY_SALARY * 0.35))

    # Read yesterday bids to infer pressure.
    prev_bids = []
    prev_hp_after = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid', 0.0)))
                prev_hp_after.append(float(prev.get('hp_after', prev.get('hp', 0.0))))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    # Supply pressure: with higher supply, we can underbid slightly.
    # Use a target bid anchored between a floor and a ceiling.
    supply_frac = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_frac = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
        if supply_frac < 0.0:
            supply_frac = 0.0
        if supply_frac > 1.0:
            supply_frac = 1.0

    # If my hp is low or I've already been without water, bid more to avoid death.
    urgent = 0
    if hp <= 2.0:
        urgent += 2
    if no_water_days >= 1:
        urgent += 1

    # Base aggressiveness from yesterday's highest pressure.
    # Cindy/Eric survived with high bids; Alex/David died after low survival.
    # If highest_prev_bid was huge, we need to compete; otherwise we can shade.
    if highest_prev_bid >= DAILY_SALARY * 1.1:
        # Compete but shade slightly.
        target = highest_prev_bid * 0.92
    elif highest_prev_bid >= DAILY_SALARY * 0.85:
        target = max(avg_prev_bid * 0.95, DAILY_SALARY * (0.55 + 0.25 * supply_frac))
    else:
        target = max(DAILY_SALARY * (0.45 + 0.25 * supply_frac), avg_prev_bid * 0.8)

    # Urgency adjustment.
    if urgent >= 2:
        target *= 1.25
    elif urgent == 1:
        target *= 1.10

    # Never bid more than budget.
    # Also avoid extreme bids when supply is high.
    cap = budget
    # Soft cap: if supply is high, don't exceed a moderate fraction of salary.
    soft_cap = DAILY_SALARY * (0.95 if supply_frac < 0.5 else 0.75)
    cap = min(cap, soft_cap)

    bid = max(0.0, min(float(cap), float(target)))

    # If budget is too small, still bid something to try to secure.
    if bid <= 0.0 and budget > 0.0:
        bid = min(budget, DAILY_SALARY * 0.2)

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

    # Identify alive opponents
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    # If no one else is alive, bid conservatively
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Use yesterday's immediate trace to infer pressure
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', None)
        if isinstance(prev, dict):
            # Some environments might store a single trace dict
            bid_val = prev.get('bid', None)
            if bid_val is not None:
                yesterday_bids.append(float(bid_val))
        elif isinstance(prev, list):
            # Use the last element only (immediate reaction)
            if len(prev) > 0:
                last = prev[-1]
                if isinstance(last, dict) and last.get('bid', None) is not None:
                    yesterday_bids.append(float(last['bid']))

    # Default bid target based on supply level
    # Higher supply means water is easier to secure; lower supply means we may need to outbid.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Pressure from opponents: high bids imply they are protecting HP
    pressure = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # Normalize pressure against our typical salary scale
        pressure = max(0.0, min(1.0, highest_prev_bid / (DAILY_SALARY * 1.1)))
    else:
        highest_prev_bid = 0.0

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Urgency: if we're low HP or have missed water recently, bid more.
    urgency = 0.0
    if my_hp <= 2.0:
        urgency = 1.0
    elif my_hp <= 4.0:
        urgency = 0.7
    elif no_water_days >= 2:
        urgency = 0.6
    elif no_water_days >= 1:
        urgency = 0.35

    # Decide a base bid ceiling.
    # When supply is low, we need to be more competitive; when supply is high, we can shade down.
    shade = (1.0 - supply_ratio)  # more shading when supply is low

    # Target bid: combine pressure and urgency, but keep within a reasonable fraction.
    target = DAILY_SALARY * (0.35 + 0.35 * pressure + 0.25 * urgency) * (0.85 + 0.3 * shade)

    # If opponents were extremely aggressive yesterday, slightly overtake.
    if yesterday_bids:
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            target = max(target, highest_prev_bid + 2.0)
        elif highest_prev_bid >= DAILY_SALARY * 0.65:
            target = max(target, highest_prev_bid * 0.92)

    # Ensure we don't spend more than we can afford.
    bid = float(min(my_budget, max(0.0, target)))

    # Safety: if our budget is tiny, bid what we can.
    if my_budget <= DAILY_SALARY * 0.2:
        bid = float(min(my_budget, DAILY_SALARY * 0.25))

    # If extremely urgent, bid close to budget.
    if urgency >= 0.9 and my_hp <= 2.0:
        bid = float(min(my_budget, max(bid, DAILY_SALARY * 0.85)))

    return bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive.append((opp_id, opp))

    if not alive:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids for immediate pressure
    yesterday_bids = []
    for _, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Supply pressure: if supply is low, water is scarce; increase bid.
    # supply is in [15,25]; if near 15, only floor(15/9)=1 unit of our requirement fits.
    low_supply = supply <= 18.0
    very_low_supply = supply <= 16.0

    # HP urgency: if we're near death, bid aggressively.
    hp_critical = my_hp <= 2 or my_no_water_days >= 2
    hp_low = my_hp <= 4

    # Baseline bid: aim to secure water without matching the highest bidder.
    # Use a tiered approach relative to yesterday's pressure.
    if hp_critical:
        target = DAILY_SALARY * (0.85 if not very_low_supply else 0.95)
    elif hp_low:
        target = DAILY_SALARY * (0.60 if not low_supply else 0.75)
    else:
        target = DAILY_SALARY * (0.52 if not low_supply else 0.68)

    # If yesterday had extreme bidding, only escalate slightly unless critical.
    # Cindy/David were bidding ~128+; Eric died with low bids.
    if highest_prev_bid >= DAILY_SALARY * 1.25:  # >=112.5
        if hp_critical:
            target = max(target, highest_prev_bid * 0.92)
        else:
            # Avoid overpaying: bid just under the top pressure.
            target = max(target, highest_prev_bid * 0.70)

    # If supply is scarce, ensure we don't underbid against high pressure.
    if very_low_supply and highest_prev_bid >= DAILY_SALARY * 0.9:
        target = max(target, highest_prev_bid * 0.78)

    # Final cap by budget and non-negative.
    bid = max(0.0, min(my_budget, float(target)))

    # Small deterministic nudge by day to break ties.
    # Keep within budget.
    nudge = 0.5 if (day % 2 == 0) else 0.0
    bid = min(my_budget, bid + nudge)

    return float(bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    if not alive_opponents:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace only
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Estimate competition pressure
    pressure = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / float(len(yesterday_bids))
        # Cindy-type behavior: very high bids imply aggressive securing
        if highest_prev_bid >= DAILY_SALARY * 1.3:
            pressure = 0.85
        elif avg_prev_bid >= DAILY_SALARY:
            pressure = 0.65
        else:
            pressure = 0.45

    # If we are low HP or have gone multiple days without water, overbid more
    urgency = 0.0
    if my_hp <= 2.0:
        urgency = 0.95
    elif my_hp <= 4.0:
        urgency = 0.75
    elif my_no_water_days >= 2:
        urgency = 0.6
    else:
        urgency = 0.45

    # Supply level: lower supply increases chance of being priced out
    # supply is between 15 and 25; normalize to [0,1]
    supply_norm = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    # When supply is low (norm near 0), increase bid
    supply_factor = 1.0 + (0.25 * (1.0 - supply_norm))

    # Base target bid: moderate fraction of daily salary, adjusted by pressure/urgency and supply
    target = DAILY_SALARY * (0.5 + 0.25 * pressure + 0.25 * urgency)
    target *= supply_factor

    # If yesterday had very high highest bid, slightly shadow it without fully matching
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 1.3:
            target = max(target, DAILY_SALARY * 0.9)
        elif highest_prev_bid >= DAILY_SALARY:
            target = max(target, DAILY_SALARY * 0.7)
        # Avoid runaway: cap relative to highest_prev_bid
        target = min(target, highest_prev_bid * 0.85)

    # Ensure we can pay and still bid non-negative
    bid = max(0.0, min(my_budget, target))

    # If budget is extremely low, bid whatever we can but avoid zero if urgency is high
    if my_budget <= DAILY_SALARY * 0.15:
        if urgency >= 0.75 and my_hp <= 4.0:
            bid = max(0.0, min(my_budget, DAILY_SALARY * 0.25))
        else:
            bid = max(0.0, min(my_budget, DAILY_SALARY * 0.1))

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

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    # Alive opponents and yesterday bids
    alive_opps = []
    for opp_id, opp in opponents_status.items():
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

    # Base pressure from yesterday
    if yesterday_bids:
        sorted_bids = sorted(yesterday_bids)
        # Target to beat likely winner without matching extreme
        # Use 2nd highest if available, else highest
        if len(sorted_bids) >= 2:
            target = sorted_bids[-2]
        else:
            target = sorted_bids[-1]
        # Add a small increment to try to win the marginal allocation
        pressure_bid = target + 3.0
    else:
        pressure_bid = DAILY_SALARY * 0.5

    # Determine risk based on our hp and budget.
    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # If we are close to running out, bid aggressively.
    # We don't know exact water->hp dynamics, so use conservative triggers.
    low_hp = hp <= 3.0
    critical = (hp <= 2.0) or (no_water_days >= 2)

    # Supply factor: higher supply reduces need to overbid.
    # Convert supply to a normalized factor in [0,1]
    try:
        norm = (float(supply) - float(MIN_SUPPLY)) / (float(MAX_SUPPLY) - float(MIN_SUPPLY))
    except Exception:
        norm = 0.5
    if norm < 0.0:
        norm = 0.0
    if norm > 1.0:
        norm = 1.0

    # If supply is higher, we can bid slightly less; if lower, bid more.
    supply_adjust = 1.0 + (0.15 * (1.0 - norm))

    # Strategy:
    # - Safe: bid near pressure_bid but capped by a fraction of budget/salary.
    # - Low hp: bid closer to salary tiers.
    if critical:
        desired = max(DAILY_SALARY * 0.75, pressure_bid * 1.05) * supply_adjust
        cap = budget
    elif low_hp:
        desired = max(DAILY_SALARY * 0.6, pressure_bid * 1.0) * supply_adjust
        cap = budget
    else:
        # We can afford to be slightly under the top bid; aim to beat 2nd-highest.
        desired = max(DAILY_SALARY * 0.45, pressure_bid * 0.98) * supply_adjust
        cap = budget

    # Ensure we don't bid negative or exceed budget.
    if cap <= 0:
        return 0.0

    bid = float(desired)
    if bid < 0.0:
        bid = 0.0
    if bid > cap:
        bid = cap

    # Small safety floor: if budget is enough, bid at least a small amount to avoid ties at 0.
    min_bid = min(cap, DAILY_SALARY * 0.25)
    if bid < min_bid and cap > 1e-9:
        bid = min_bid

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

    supply = float(day_context['supply'])
    day = day_context['day']

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from immediate previous_trace only
    prev_bids = []
    for oid, o in alive:
        pt = o.get('previous_trace', {}) or {}
        b = pt.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate how competitive it was
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    # Identify likely aggressors/survivors from yesterday by bid magnitude
    # (Using only yesterday bid info.)
    target_bid = None
    # Prefer to outbid the strongest survivor's yesterday bid slightly.
    # We don't know current bids, so we use yesterday as a proxy.
    if prev_bids:
        target_bid = max(prev_bids)

    # Supply pressure: if supply is near minimum, water is scarce -> bid more.
    scarcity = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.0
    scarcity = max(0.0, min(1.0, scarcity))

    # Base bid policy: keep enough water to avoid long no-water streak.
    # If I'm already low on HP or have consecutive no-water days, increase bid.
    emergency = 0.0
    if hp <= 2.0:
        emergency = 1.0
    elif hp <= 4.0:
        emergency = 0.6
    if no_water_days >= 2:
        emergency = max(emergency, 0.5)

    # Compute desired bid.
    if target_bid is not None and target_bid > 0:
        # Try to slightly exceed the top yesterday bid when scarcity and my condition require it.
        # Otherwise, undercut to save budget.
        margin = 3.0 + 6.0 * scarcity
        if emergency >= 0.8:
            desired = target_bid + margin
        elif emergency >= 0.5:
            desired = max(target_bid, avg_prev_bid) + (margin * 0.6)
        else:
            desired = max(avg_prev_bid * 0.95, target_bid * 0.85) + (margin * 0.25)
    else:
        desired = DAILY_SALARY * (0.45 + 0.25 * scarcity)

    # Additional scaling with supply: if supply is high, bid less.
    desired *= (0.85 + 0.3 * (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 1.0)

    # Ensure we don't bid more than we can afford.
    desired = max(0.0, min(budget, desired))

    # If budget is tiny, just bid what we can.
    if budget <= 1.0:
        return max(0.0, budget)

    # Hard safety: if I'm in danger, bid close to daily salary cap.
    if emergency >= 0.8:
        cap = min(budget, DAILY_SALARY * 0.95)
        return min(desired, cap)

    # Otherwise, keep within a reasonable fraction of daily salary to preserve for future days.
    cap = min(budget, DAILY_SALARY * (0.65 + 0.25 * scarcity))
    return min(desired, cap)
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

    day = day_context.get('day', 0)
    supply = day_context.get('supply', 0)

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append((oid, o))

    if not alive_opponents:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace for immediate reaction
    prev_bids = []
    for oid, o in alive_opponents:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate competitive pressure from yesterday
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    median_prev_bid = 0.0
    if prev_bids:
        s = sorted(prev_bids)
        mid = len(s) // 2
        median_prev_bid = float(s[mid])

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Supply pressure: lower supply means we need more aggressive bidding to secure water.
    # supply is float; use thresholds without indexing.
    supply_ratio = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_ratio = (float(supply) - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_ratio = max(0.0, min(1.0, supply_ratio))
    low_supply = 1.0 - supply_ratio  # 1 when supply is low

    # Base target bid band
    # If opponents were bidding heavily yesterday, match slightly above median/highest band.
    pressure = 0.0
    if highest_prev_bid > 0:
        pressure = min(1.0, highest_prev_bid / (DAILY_SALARY * 1.2))

    # Determine a conservative bid ceiling based on our budget and survival risk
    # If HP is low or we've had many no-water days, increase bid.
    risk = 0.0
    if hp <= 2:
        risk += 0.6
    elif hp <= 4:
        risk += 0.3
    if no_water_days >= 2:
        risk += 0.3
    risk = min(1.0, risk)

    # Compute candidate bid
    # Target slightly above median when there was competitive bidding.
    target = 0.0
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Cindy/Alex style: bid in the same competitive band but not necessarily the max.
        target = max(median_prev_bid + 2.0, DAILY_SALARY * (0.55 + 0.25 * low_supply))
    else:
        target = max(DAILY_SALARY * (0.45 + 0.25 * low_supply), median_prev_bid + 1.0)

    # Risk adjustment
    target = target * (1.0 + 0.25 * risk)

    # Hard cap: don't exceed what we can afford; also avoid extreme overspending.
    # If we are healthy, keep cap around 0.75 of budget; if risky, allow up to 0.95.
    cap_frac = 0.75 if risk < 0.4 else 0.95
    cap = budget * cap_frac

    bid = min(float(budget), float(cap), float(target))

    # If supply is very low, ensure we bid at least a floor to compete.
    if float(supply) <= float(WATER_REQ) + 1:
        floor_bid = DAILY_SALARY * 0.6
        bid = max(bid, min(float(budget), floor_bid))

    # Final safety: if budget is tiny, bid what we can.
    if bid < 0:
        bid = 0.0

    return float(bid)
"""
