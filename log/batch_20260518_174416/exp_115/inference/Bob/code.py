# ============================================================
# Experiment: exp_115
# Agent: Bob
# Source: exp_115
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

    # Alive opponents
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append(o)

    # Yesterday bids (immediate reaction only)
    prev_bids = []
    for o in alive:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Target: ensure we can cover requirement; if supply is tight, bid more.
    # Estimate how much water we need from the auction today.
    # If supply is below 2*WATER_REQ, competition is likely higher.
    supply_factor = 1.0
    if supply <= 2.0 * WATER_REQ:
        supply_factor = 1.15
    if supply <= 1.5 * WATER_REQ:
        supply_factor = 1.30

    # Urgency: if we have gone without water recently or hp is low.
    urgency = 1.0
    if no_water_days >= 2:
        urgency = 1.35
    if hp <= 2:
        urgency = max(urgency, 1.45)
    if hp <= 1:
        urgency = max(urgency, 1.60)

    # Opponent pressure adjustment
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        # If someone was bidding close to salary, they likely anticipate scarcity.
        if highest_prev_bid >= 0.85 * DAILY_SALARY:
            # Contest lightly unless we're in critical condition.
            base = 0.35 * DAILY_SALARY
            if urgency >= 1.45:
                base = 0.60 * DAILY_SALARY
            bid = base * supply_factor * urgency
        else:
            # Their bids were not extreme; we can take a stronger position.
            # Use a floor related to our requirement.
            base = 0.55 * DAILY_SALARY
            bid = base * supply_factor * (0.95 + 0.15 * urgency)
            # If they were bidding very low, push more to secure water.
            lowest_prev_bid = min(prev_bids)
            if lowest_prev_bid < 0.35 * DAILY_SALARY:
                bid *= 1.10
    else:
        # No trace bids: default to requirement-driven moderate bid.
        base = 0.50 * DAILY_SALARY
        bid = base * supply_factor * (0.90 + 0.20 * urgency)

    # Convert bid to a feasible range and budget cap.
    # Bid cannot exceed our budget.
    if budget <= 0:
        return 0

    # Keep bid within [0, budget] and avoid overbidding beyond what is likely needed.
    # We cap at 0.95*DAILY_SALARY unless urgency is high.
    cap = 0.95 * DAILY_SALARY
    if urgency >= 1.45:
        cap = 1.00 * DAILY_SALARY

    bid = float(bid)
    if bid > cap:
        bid = cap
    if bid > budget:
        bid = budget
    if bid < 0:
        bid = 0

    # Discretize to integer bids (typical auction style). Ensure int conversion.
    return int(bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # If no opponents, conserve budget.
    if not alive_opps:
        return max(0.0, min(my_status.get('budget', 0.0), DAILY_SALARY * 0.35))

    # Read only yesterday's immediate trace bids.
    prev_bids = []
    prev_hp_after = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            prev_bids.append(float(b))
            prev_hp_after.append(float(prev.get('hp_after', o.get('hp', 0.0))))

    # If traces missing, use a baseline strategy.
    if not prev_bids:
        base = DAILY_SALARY * 0.55
        if my_status.get('hp', 0.0) <= 2:
            base = DAILY_SALARY * 0.9
        return max(0.0, min(my_status.get('budget', 0.0), base))

    # Competitive level anchored to observed bids.
    highest_prev_bid = max(prev_bids)
    lowest_prev_bid = min(prev_bids)
    median_prev_bid = sorted(prev_bids)[len(prev_bids)//2]

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))

    # Estimate how many water units might be available; use it to avoid overspending.
    # supply is float; only indices require int; here we only use numeric comparisons.
    units_est = supply / float(WATER_REQ) if WATER_REQ else 0.0

    # Strategy:
    # - If my hp is critical, bid aggressively.
    # - Otherwise, bid near a fraction of the competitive pressure.
    if my_hp <= 2.0:
        target = min(DAILY_SALARY * 0.95, highest_prev_bid + 5.0)
    elif my_hp <= 4.0:
        target = min(DAILY_SALARY * 0.75, median_prev_bid + 3.0)
    else:
        # Medium scenario: don't chase the very top; aim slightly above median/low pressure.
        # If supply is tight (units_est < 2), increase modestly.
        tight_factor = 1.15 if units_est < 2.0 else 1.05
        target = min(DAILY_SALARY * 0.65, (median_prev_bid * 0.9 + lowest_prev_bid * 0.1) * tight_factor)

    # Ensure we don't exceed budget.
    bid = max(0.0, min(my_budget, float(target)))

    # Small day-based jitter to avoid deterministic ties.
    jitter = (int(day) % 5) * 0.5
    bid = min(bid + jitter, my_budget)

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

    alive_opps = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace for immediate reaction.
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Baseline target: stay below Cindy-like pressure but above Eric-like mid pressure.
    # Use yesterday highest/second-highest to gauge aggressiveness.
    if prev_bids:
        sorted_b = sorted(prev_bids)
        highest = sorted_b[-1]
        second = sorted_b[-2] if len(sorted_b) >= 2 else sorted_b[-1]
    else:
        highest = 0.0
        second = 0.0

    # Supply pressure: if supply is tight, we bid more.
    # With water requirement 9, supply 15-25 means ~1-2 units possible.
    tightness = 0.0
    if supply <= (MIN_SUPPLY + WATER_REQ * 0.0):
        tightness = 1.0
    elif supply <= (MIN_SUPPLY + WATER_REQ * 0.5):
        tightness = 0.7
    elif supply <= (MIN_SUPPLY + WATER_REQ * 1.0):
        tightness = 0.4
    else:
        tightness = 0.2

    # If we are close to death or have accumulated no-water days, bid more aggressively.
    emergency = 0.0
    if my_hp <= 2:
        emergency = 1.0
    elif my_hp <= 4:
        emergency = 0.7
    elif my_no_water_days >= 2:
        emergency = 0.5

    # Core strategy: bid around the second-highest yesterday + small increment, but cap below highest.
    # This aims to beat mid-tier bids while avoiding overpaying against the top bidder.
    base = second + 3.0
    if highest > 0:
        # Keep under the top aggressor by a margin unless emergency.
        under_top = highest - (8.0 if emergency < 1.0 else 2.0)
        base = min(base, under_top)

    # Adjust for tightness and emergency.
    desired = base + tightness * 6.0 + emergency * 25.0

    # Ensure we don't exceed what we can afford.
    desired = max(0.0, min(desired, my_budget))

    # Also ensure we don't bid trivially low when we need water.
    # If we have no-water days, enforce a minimum.
    min_bid = 0.0
    if my_no_water_days >= 1:
        min_bid = DAILY_SALARY * 0.45
    if my_no_water_days >= 2:
        min_bid = DAILY_SALARY * 0.65
    if my_hp <= 4:
        min_bid = max(min_bid, DAILY_SALARY * 0.75)

    desired = max(desired, min_bid)

    # Final cap: don't spend more than 1.2 daily salaries to avoid bankroll collapse.
    desired = min(desired, my_budget, DAILY_SALARY * 1.2)

    return float(desired)
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

    # Identify alive opponents
    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive.append((opp_id, opp))

    # If no opponents are alive, conserve budget
    if not alive:
        cap = my_status['budget']
        target = DAILY_SALARY * 0.35
        return min(cap, target)

    # Read yesterday bids (single-step reaction)
    yesterday_bids = []
    for _, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Pressure estimate: highest yesterday bid among alive
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Determine our risk level from hp and no_water_days
    hp = int(my_status['hp'])
    no_water_days = int(my_status['no_water_days'])
    budget = float(my_status['budget'])

    # If we are in danger, bid hard but still bounded by budget
    if hp <= 2 or no_water_days >= 2:
        base = DAILY_SALARY * 0.95
    elif hp <= 4 or no_water_days == 1:
        base = DAILY_SALARY * 0.7
    else:
        base = DAILY_SALARY * 0.55

    # Supply tightness: closer to MIN_SUPPLY implies higher competition
    tightness = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)  # 0..1
    tightness = max(0.0, min(1.0, tightness))

    # Cindy yesterday: if she bid extremely high, assume she may contest again.
    # We approximate her by using highest_prev_bid as proxy for aggressive contender.
    # If highest_prev_bid is very high, we only need to beat moderate bids; avoid matching extremes.
    if highest_prev_bid >= DAILY_SALARY * 2.0:
        # Aggressive hoarding likely; increase bid slightly with tightness
        base = max(base, DAILY_SALARY * (0.65 + 0.2 * tightness))
    elif highest_prev_bid >= DAILY_SALARY * 0.9:
        base = max(base, DAILY_SALARY * (0.6 + 0.15 * tightness))

    # Compute a strategic bid target: aim for enough to secure water this day.
    # Since we don't know opponent current bids, we use a conservative overtake margin.
    # Margin grows with tightness.
    margin = 2.0 + 6.0 * tightness

    # If we have a strong signal of competition (highest_prev_bid moderate), anchor near it.
    if highest_prev_bid > 0 and highest_prev_bid < DAILY_SALARY * 1.6:
        target = highest_prev_bid + margin
    else:
        target = base

    # Final cap by budget
    target = min(target, budget)

    # Ensure non-negative
    if target < 0:
        target = 0.0

    # If budget is too low, bid whatever remains
    return float(target)
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

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        cap = min(budget, DAILY_SALARY * 0.4)
        return max(0.0, cap)

    # Read yesterday's behavior from previous_trace (immediate reaction only)
    prev_bids = []
    prev_by_id = {}
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                bid_f = float(bid)
            except Exception:
                continue
            prev_bids.append(bid_f)
            prev_by_id[oid] = bid_f

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    # Identify Cindy if present
    cindy_bid = prev_by_id.get('Cindy', None)

    # Supply pressure: when supply is tight, bids must be more competitive.
    tightness = 0.0
    if supply <= WATER_REQ:
        tightness = 1.0
    elif supply <= 0.75 * 25:
        tightness = 0.6
    else:
        tightness = 0.3

    # Base bid aims to secure water for a 10-day horizon without overpaying.
    # If Cindy was aggressive yesterday, we anticipate continued competition.
    if highest_prev_bid >= DAILY_SALARY * 1.6:  # ~144
        # Cindy-like pressure: bid to avoid being outcompeted.
        if hp <= 2.0 or no_water_days >= 2:
            target = DAILY_SALARY * (0.85 + 0.15 * tightness)
        else:
            target = DAILY_SALARY * (0.55 + 0.25 * tightness)
    elif highest_prev_bid >= DAILY_SALARY * 0.9:  # ~81
        if hp <= 2.0 or no_water_days >= 2:
            target = DAILY_SALARY * (0.75 + 0.1 * tightness)
        else:
            target = DAILY_SALARY * (0.5 + 0.2 * tightness)
    else:
        # Opponents not bidding hard; conserve budget.
        if hp <= 2.0 or no_water_days >= 2:
            target = DAILY_SALARY * (0.7 + 0.1 * tightness)
        else:
            target = DAILY_SALARY * (0.45 + 0.15 * tightness)

    # If Cindy specifically bid extremely high yesterday, slightly overbid her baseline.
    if cindy_bid is not None and cindy_bid >= DAILY_SALARY * 1.7:
        target = max(target, cindy_bid * 0.92)

    # Budget safety: never exceed budget.
    # Also keep a minimum bid floor to stay in contention.
    min_floor = 0.0
    if hp <= 2.0 or no_water_days >= 2:
        min_floor = DAILY_SALARY * 0.6
    else:
        min_floor = DAILY_SALARY * 0.35

    bid = max(min_floor, target)
    bid = min(bid, budget)

    # Clamp to non-negative
    if bid < 0.0:
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Alive opponents and their yesterday bids
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # If we have no opponents (unlikely), bid conservatively
    if not alive_opps:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.4))

    yesterday_bids = []
    yesterday_pressures = []
    for o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass
        # Use hp_after/status as a crude pressure indicator
        hp_after = prev.get('hp_after', None)
        status = prev.get('status', None)
        if status in ('dead', 'eliminated') or (hp_after is not None and float(hp_after) <= 0):
            yesterday_pressures.append(1)

    # Determine competitive pressure from yesterday
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = 0.0
    if len(yesterday_bids) >= 2:
        sorted_b = sorted(yesterday_bids, reverse=True)
        second_prev_bid = sorted_b[1]

    # Base bid target: aim to beat the likely clearing price without matching Cindy/David extremes
    # Approximate clearing price as slightly above the second-highest yesterday bid.
    # Add a small premium only if we are in danger.
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Urgency factor
    urgency = 0.0
    if hp <= 2.0:
        urgency = 1.0
    elif hp <= 4.0:
        urgency = 0.6
    else:
        urgency = 0.3

    if no_water_days >= 2:
        urgency = max(urgency, 0.8)

    # Supply-based scaling: higher supply reduces need to overbid
    if supply >= 22.0:
        supply_factor = 0.85
    elif supply <= 17.0:
        supply_factor = 1.05
    else:
        supply_factor = 1.0

    # Compute candidate bid
    # If yesterday had very high bids (Cindy/David), we don't chase the max; we bid near the middle.
    chase_threshold = DAILY_SALARY * 1.2  # 108
    if highest_prev_bid >= chase_threshold:
        # competitive environment: bid around second-highest + premium
        premium = 6.0 + 10.0 * urgency
        target = second_prev_bid + premium
    else:
        # moderate environment: bid around highest_prev_bid with smaller premium
        premium = 4.0 + 8.0 * urgency
        target = highest_prev_bid + premium

    target *= supply_factor

    # Also ensure we don't bid beyond what we can afford
    # Keep a floor to avoid zeroing out when urgency is high.
    min_bid = 0.0
    if urgency >= 0.8:
        min_bid = DAILY_SALARY * 0.55
    elif urgency >= 0.6:
        min_bid = DAILY_SALARY * 0.45
    else:
        min_bid = DAILY_SALARY * 0.35

    bid = max(min_bid, target)
    bid = min(bid, budget)

    # If budget is extremely low, still bid something to prevent accumulating no_water_days
    if bid <= 0.0 and budget > 0.0:
        bid = min(budget, DAILY_SALARY * 0.2)

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

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    hp = my_status.get('hp', 0)
    budget = my_status.get('budget', 0.0)
    no_water_days = my_status.get('no_water_days', 0)

    alive_opps = []
    for oid, o in opponents_status.items():
        try:
            if o.get('alive', False):
                alive_opps.append((oid, o))
        except Exception:
            continue

    # Base conservative bid: enough to compete but not match the top bidders.
    # Scale with supply: higher supply -> lower competitive pressure.
    if supply >= 22:
        base_mult = 0.45
    elif supply >= 18:
        base_mult = 0.55
    else:
        base_mult = 0.65

    # React to yesterday's bidding intensity by alive opponents.
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) if isinstance(o, dict) else {}
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # If someone previously bid very high, we slightly undercut to grab water.
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        # Thresholds inferred from yesterday: Eric/Alex averaged ~112-123 with max ~226.
        if highest_prev_bid >= 200:
            pressure = 'extreme'
        elif highest_prev_bid >= 120:
            pressure = 'high'
        else:
            pressure = 'medium'
    else:
        pressure = 'low'
        highest_prev_bid = 0.0

    # Determine target bid.
    # If I'm in danger, bid more aggressively.
    if hp <= 2 or no_water_days >= 2:
        danger_mult = 0.85
    elif hp <= 3:
        danger_mult = 0.70
    else:
        danger_mult = 0.60

    if pressure == 'extreme':
        target = min(budget, DAILY_SALARY * 0.75)
        # Undercut the extreme bid if possible.
        target = min(target, highest_prev_bid * 0.92)
    elif pressure == 'high':
        target = min(budget, DAILY_SALARY * 0.65)
        target = min(target, highest_prev_bid * 0.90)
    elif pressure == 'medium':
        target = min(budget, DAILY_SALARY * base_mult * 1.05)
    else:
        target = min(budget, DAILY_SALARY * base_mult)

    # Ensure we don't bid trivially low when supply is low.
    if supply <= 16:
        floor_bid = DAILY_SALARY * 0.55
        if target < floor_bid:
            target = min(budget, floor_bid)

    # If budget is tiny, just spend what we can.
    if budget <= 1:
        return 0.0

    # Keep bid within reasonable bounds.
    if target < 0:
        target = 0.0

    return float(target)
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

    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # Default conservative if no opponents
    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.45)

    # Read yesterday bids from previous_trace only
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            prev_bids.append(float(b))

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev_bid

    # Estimate how many units of water are likely needed this day.
    # In this challenge, higher bid correlates with water allocation; we approximate aggressiveness needs.
    supply_ratio = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    low_supply = supply <= (MIN_SUPPLY + 1.0)

    # Pressure heuristic: if someone previously paid near our daily salary threshold, they likely contest.
    contesting = highest_prev_bid >= (DAILY_SALARY * 0.85)

    # Base bid: free-ride on David-like behavior unless we are in danger.
    # Target around 0.55 salary when not contesting; boost if low supply or our HP is low.
    if not contesting:
        base = DAILY_SALARY * (0.45 + 0.15 * supply_ratio)
    else:
        # If contesting, we don't want to be too low; match just above a likely non-top bidder.
        base = max(DAILY_SALARY * 0.55, second_prev_bid + 5.0)

    # Urgency adjustments
    if hp <= 2:
        base = max(base, DAILY_SALARY * 0.95)
    elif hp <= 4:
        base = max(base, DAILY_SALARY * 0.75)

    if no_water_days >= 2:
        base = max(base, DAILY_SALARY * 0.8)

    if low_supply:
        base = max(base, DAILY_SALARY * 0.7)

    # Budget safety: never exceed budget
    bid = min(budget, base)

    # If budget is extremely small, still bid something proportional to avoid zero-water.
    if bid <= 0.0:
        bid = min(budget, 1.0)

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

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    my_hp = my_status.get('hp', 0)
    my_budget = my_status.get('budget', 0.0)
    my_no_water_days = my_status.get('no_water_days', 0)

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', True):
            alive_opponents.append((oid, o))

    # If no one is alive, conserve budget.
    if not alive_opponents:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday bids only (immediate reaction).
    prev_bids = []
    for oid, o in alive_opponents:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            prev_bids.append(float(b))

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Heuristic: Cindy-like behavior (very high bids) indicates strong competition for water.
    # Alex/David dying with low bids suggests low-bid players are underbidding.
    # We target a mid bid that beats low bidders but avoids Cindy's extreme.
    # Scale with my urgency.
    urgency = 0
    if my_hp <= 2:
        urgency += 2
    if my_no_water_days >= 2:
        urgency += 1
    if my_hp <= 0:
        urgency += 3

    # Estimate likely required bid pressure.
    # If someone previously bid extremely high, raise to compete; otherwise stay moderate.
    if highest_prev_bid >= DAILY_SALARY * 1.3:
        base = DAILY_SALARY * 0.75
    elif highest_prev_bid >= DAILY_SALARY * 0.6:
        base = DAILY_SALARY * 0.6
    else:
        base = DAILY_SALARY * 0.45

    # Increase if I'm in trouble.
    bid = base + urgency * (DAILY_SALARY * 0.18)

    # Supply affects how many water units are likely available; with higher supply, we can bid less.
    # day_context['supply'] is float; clamp and convert to int safely.
    s_int = int(max(MIN_SUPPLY, min(MAX_SUPPLY, float(supply))))
    # More supply -> slightly lower bid.
    supply_factor = (MAX_SUPPLY - s_int) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    bid = bid * (0.9 + 0.2 * supply_factor)

    # Budget cap and non-negative.
    if my_budget <= 0:
        return 0.0

    # Don't overcommit beyond what we can afford.
    bid = max(0.0, min(float(my_budget), bid))

    # If urgency is high and budget allows, push closer to salary.
    if urgency >= 2 and my_budget >= DAILY_SALARY:
        bid = min(float(my_budget), DAILY_SALARY * 0.95)

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

    # Alive opponents and their yesterday bids
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # Budget and hp pressure
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # If we are close to death, spend to secure water.
    if hp <= 2 or no_water_days >= 2:
        bid = DAILY_SALARY * 0.85
    else:
        # Determine competitive pressure from yesterday.
        # Cindy-like behavior indicates high bids; but we don't want to mirror extremes.
        if yesterday_bids:
            highest_prev = max(yesterday_bids)
            # Use a capped response: aim to slightly beat the mid/high cluster.
            # If highest was very high, don't chase fully; bid enough to avoid losing.
            if highest_prev >= DAILY_SALARY * 1.7:
                # Likely at least one aggressive spender.
                bid = DAILY_SALARY * 0.65
            elif highest_prev >= DAILY_SALARY * 1.1:
                bid = DAILY_SALARY * 0.55
            else:
                bid = DAILY_SALARY * 0.45
        else:
            bid = DAILY_SALARY * 0.5

    # Adjust for supply: with higher supply, winning is easier; bid less.
    # Normalize supply in [0,1].
    denom = (MAX_SUPPLY - MIN_SUPPLY)
    if denom <= 0:
        supply_factor = 0.5
    else:
        supply_factor = (supply - MIN_SUPPLY) / denom
        if supply_factor < 0.0:
            supply_factor = 0.0
        if supply_factor > 1.0:
            supply_factor = 1.0

    # Reduce bid when supply is high; increase slightly when supply is low.
    # At supply=25 -> multiplier ~0.9, at supply=15 -> multiplier ~1.1
    bid *= (1.1 - 0.2 * supply_factor)

    # Ensure bid is feasible.
    if budget <= 0:
        return 0.0

    # Cap to not overspend: keep some budget for later days.
    # If supply is low and we're not in danger, still keep moderate cap.
    keep_fraction = 0.25 if hp > 3 else 0.05
    max_affordable = max(0.0, budget * (1.0 - keep_fraction))

    # Also cap absolute bid to avoid chasing extreme opponents.
    absolute_cap = DAILY_SALARY * 0.9
    bid = min(bid, absolute_cap, max_affordable)

    # Minimum bid to be competitive when not dying.
    min_competitive = DAILY_SALARY * 0.35
    if bid < min_competitive and (hp > 2 and no_water_days < 2):
        bid = min(budget, min_competitive)

    # Final clamp
    if bid < 0.0:
        bid = 0.0
    if bid > budget:
        bid = budget

    return float(bid)
"""
