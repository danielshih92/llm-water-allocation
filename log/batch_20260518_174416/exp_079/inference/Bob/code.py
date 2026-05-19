# ============================================================
# Experiment: exp_079
# Agent: Bob
# Source: exp_079
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    alive_opps = []
    for opp_id, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((opp_id, o))

    if not alive_opps:
        return float(min(my_status.get('budget', 0.0), DAILY_SALARY * 0.4))

    # Extract yesterday bids to infer opponent pressure.
    yesterday_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    my_budget = float(my_status.get('budget', 0.0))
    my_hp = float(my_status.get('hp', 0.0))

    # Estimate how many units of water are likely needed given supply.
    # If supply is tight, we should bid more aggressively.
    tightness = 0.0
    if supply > 0.0:
        tightness = max(0.0, (WATER_REQ - (supply - WATER_REQ)) / max(1.0, float(WATER_REQ)))
    # Clamp tightness to [0,1] roughly.
    if tightness < 0.0:
        tightness = 0.0
    if tightness > 1.0:
        tightness = 1.0

    # If opponent(s) were bidding very high yesterday, they likely need water badly.
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

        # Aggressive counter if they were near their max willingness.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_hp > 3.0:
                bid = DAILY_SALARY * 0.30
            else:
                bid = DAILY_SALARY * 0.95
            # Add some pressure if supply is tight.
            bid = bid * (1.0 + 0.25 * tightness)
        else:
            # Otherwise, try to secure water at a modest premium.
            bid = max(DAILY_SALARY * 0.50, highest_prev_bid + 1.5)
            bid = bid * (1.0 + 0.15 * tightness)
    else:
        # No trace info: bid based on our hp and likely scarcity.
        if my_hp <= 2.0:
            bid = DAILY_SALARY * 0.90
        else:
            bid = DAILY_SALARY * (0.55 + 0.20 * tightness)

    # Ensure bid is within budget and non-negative.
    if my_budget <= 0.0:
        return 0.0
    if bid < 0.0:
        bid = 0.0
    if bid > my_budget:
        bid = my_budget

    return float(bid)
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
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # If no opponents, bid conservatively
    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace only
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Pressure estimate: who was willing to pay a lot yesterday?
    highest_prev = max(prev_bids) if prev_bids else 0.0
    second_prev = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev

    # Determine aggressiveness based on supply scarcity and my hp
    # When supply is low, winning the allocation matters more.
    scarcity = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY + 1e-9)
    scarcity = max(0.0, min(1.0, scarcity))

    # If I'm at risk, bid more aggressively.
    if hp <= 2.0 or no_water_days >= 2:
        base = DAILY_SALARY * (0.75 + 0.25 * scarcity)
    elif hp <= 4.0:
        base = DAILY_SALARY * (0.55 + 0.25 * scarcity)
    else:
        base = DAILY_SALARY * (0.45 + 0.25 * scarcity)

    # Use yesterday's highest bid as a ceiling/anchor.
    # Aim to slightly undercut the top payer unless my hp is critical.
    # If highest_prev is very high, don't chase fully; bid enough to beat typical mid bids.
    if highest_prev >= DAILY_SALARY * 0.95:
        # Cindy-like behavior: high bids. Try to beat her only if necessary.
        if hp <= 4.0 or no_water_days >= 2:
            target = min(budget, highest_prev - 1.0)
            bid = max(base, target)
        else:
            bid = min(budget, max(base, second_prev + 1.0))
    else:
        # Typical: match/beat second-highest slightly.
        bid = max(base, second_prev + 1.5)
        # If someone bid very high relative to my base, cap to avoid overpaying.
        if highest_prev > 0.0:
            bid = min(bid, highest_prev + 0.5)

    # Final budget and non-negative constraints
    bid = max(0.0, min(budget, bid))

    # If supply is extremely low (near 15), ensure we don't underbid too much.
    if supply <= (MIN_SUPPLY + 1.0):
        bid = max(bid, DAILY_SALARY * 0.6)
        bid = min(bid, budget)

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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Alive opponents
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    # If alone, conserve
    if not alive:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from immediate previous_trace
    prev_bids = []
    for oid, o in alive:
        pt = o.get('previous_trace', {})
        if pt and ('bid' in pt) and (pt.get('bid') is not None):
            try:
                prev_bids.append(float(pt['bid']))
            except Exception:
                pass

    # Determine how aggressive survivors were yesterday
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    # Survival pressure: if low hp or accumulating no-water days, bid higher
    hp = float(my_status['hp'])
    no_water_days = int(my_status['no_water_days'])
    budget = float(my_status['budget'])

    # Supply factor: with medium supply (15-25), winning usually requires competing when others bid high
    # We aim to beat the likely clearing competition without overpaying.
    supply_ratio = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Base target bid level
    # If yesterday's highest bid was high, match slightly above it; otherwise bid around a mid/high fraction.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # High competition yesterday (Alex/David-like). Bid to secure water.
        if hp > 3 and no_water_days <= 1:
            target = max(highest_prev_bid + 2.0, DAILY_SALARY * (0.35 + 0.2 * supply_ratio))
        else:
            target = max(highest_prev_bid + 5.0, DAILY_SALARY * (0.75 + 0.1 * supply_ratio))
    else:
        # Moderate competition: bid around avg or a conservative level.
        target = max(avg_prev_bid * 0.9, DAILY_SALARY * (0.5 + 0.15 * supply_ratio))
        if hp <= 2 or no_water_days >= 2:
            target = max(target, DAILY_SALARY * 0.85)

    # Ensure we don't exceed budget; also keep within reasonable bounds relative to salary
    # (Game likely uses bid as spend; avoid maxing out unless critical.)
    critical = (hp <= 2) or (no_water_days >= 2)
    cap = budget
    if not critical:
        cap = min(cap, DAILY_SALARY * 0.95)

    bid = min(float(cap), float(target))

    # If bid becomes too small, raise slightly to avoid getting shut out under competition.
    # Use a floor based on our need and typical clearing behavior.
    min_floor = DAILY_SALARY * (0.25 + 0.25 * supply_ratio)
    if bid < min_floor and budget >= min_floor:
        bid = min(budget, min_floor)

    return float(max(0.0, bid))
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

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append((oid, o))

    if not alive_opponents:
        return float(min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace for immediate reaction
    prev_bids = []
    for _, o in alive_opponents:
        prev = o.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    # Approximate pressure from who likely survived
    # If Cindy is alive and bid high yesterday, we anticipate her continuing.
    cindy = opponents_status.get('Cindy', None)
    cindy_pressure = 0.0
    if cindy is not None and cindy.get('alive', False):
        prev = cindy.get('previous_trace', {})
        if prev:
            b = prev.get('bid', 0.0)
            try:
                cindy_pressure = float(b)
            except Exception:
                cindy_pressure = 0.0

    # Determine how many allocations we likely need this day
    # If supply is enough for at least 1 unit per bidder, we can be more conservative.
    # Use a coarse fraction based on supply relative to WATER_REQ.
    supply_units = supply / float(WATER_REQ)

    # Base bid targets
    # - If Cindy pressured yesterday, we either match slightly or outbid only when necessary.
    # - Otherwise, bid around mid (0.55 salary) to beat low bidders (Alex/Eric died with low bids).
    base = DAILY_SALARY * 0.55

    # Escalate when my hp is low or I'm already accruing no-water days.
    risk = 0
    if hp <= 2.0:
        risk += 2
    if hp <= 4.0:
        risk += 1
    if no_water_days >= 2:
        risk += 1

    # If supply is high, we can reduce bid because water is more plentiful.
    # If supply is low, increase bid.
    if supply <= float(MIN_SUPPLY) + 1.0:
        scarcity = 1
    elif supply >= float(MAX_SUPPLY) - 1.0:
        scarcity = -1
    else:
        scarcity = 0

    # If opponent pressure is high, bid just under/around it depending on risk.
    # Goal: secure water without maxing out.
    target = base
    if cindy_pressure >= DAILY_SALARY * 1.3:
        # Cindy likely aggressive; choose a threshold strategy.
        if risk >= 2:
            target = max(target, cindy_pressure * 0.92)  # close to her
        else:
            target = max(target, cindy_pressure * 0.65)  # still competitive
    elif highest_prev_bid >= DAILY_SALARY * 0.85:
        # General high pressure
        if risk >= 2:
            target = max(target, highest_prev_bid * 0.9)
        else:
            target = max(target, highest_prev_bid * 0.6)

    # Apply scarcity adjustment
    if scarcity > 0:
        target *= 1.12
    elif scarcity < 0:
        target *= 0.92

    # Clamp by my budget and avoid overbidding beyond a reasonable fraction
    # since we don't know allocation mechanics exactly.
    max_reasonable = DAILY_SALARY * (1.8 if risk >= 2 else 1.2)
    target = min(target, max_reasonable)

    if budget <= 0:
        return 0.0

    bid = float(min(budget, target))

    # Ensure we bid at least enough to be non-trivial when we are at risk.
    if bid < DAILY_SALARY * 0.25 and risk >= 2:
        bid = float(min(budget, DAILY_SALARY * 0.85))

    # If supply likely supports only ~1 unit, avoid too-low bids.
    if supply_units <= 1.4 and bid < DAILY_SALARY * 0.6:
        bid = float(min(budget, DAILY_SALARY * 0.7))

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

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Read yesterday bids to infer how hard others are fighting.
    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # Estimate how competitive the market was.
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / float(len(yesterday_bids))
    else:
        highest_prev_bid = 0.0
        avg_prev_bid = 0.0

    # Determine urgency.
    hp_critical = my_hp <= 2.5
    hp_low = my_hp <= 5.0
    no_water_urgent = my_no_water_days >= 2

    # Supply pressure: lower supply means each unit of water is scarcer.
    # Map supply in [15,25] to [1.0,0.0] pressure.
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_pressure = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_pressure = 0.5

    # Base bid: slightly below the field's likely overbidding level.
    # If yesterday bids were high, we avoid matching them unless we are in danger.
    base = DAILY_SALARY * (0.40 + 0.25 * supply_pressure)

    # If field bid very high yesterday, reduce unless we are threatened.
    if highest_prev_bid >= DAILY_SALARY * 1.25:  # ~112.5+
        if hp_critical or no_water_urgent:
            base = DAILY_SALARY * (0.75 + 0.15 * supply_pressure)
        elif hp_low:
            base = DAILY_SALARY * (0.55 + 0.15 * supply_pressure)
        else:
            base = DAILY_SALARY * (0.35 + 0.10 * supply_pressure)
    elif avg_prev_bid > DAILY_SALARY * 0.95:  # ~85+
        if hp_critical or no_water_urgent:
            base = DAILY_SALARY * (0.70 + 0.15 * supply_pressure)
        else:
            base = DAILY_SALARY * (0.50 + 0.10 * supply_pressure)

    # If we are behind on water, increase.
    if no_water_urgent:
        base *= 1.15
    if hp_critical:
        base *= 1.25

    # Convert base to a conservative cap: don't spend beyond what keeps us alive.
    # With 10 days total, spending much more than ~1/3 of budget per day is risky.
    cap = my_budget * 0.35

    bid = min(my_budget, cap, base)

    # Ensure bid is at least a small positive amount if we can.
    if bid < 1.0:
        bid = min(my_budget, 1.0)

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

    # Basic survival urgency
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive'):
            alive_opps.append((oid, o))

    # If no opponents alive, bid a conservative amount
    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday bids from immediate previous_trace
    prev_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate competitive pressure from yesterday
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev_bid

    # Target bid logic:
    # - If others bid very high yesterday, we must not be too low.
    # - But we avoid matching their peak exactly to preserve budget.
    # - Increase urgency if we have gone without water.
    urgency = 0.0
    if no_water_days >= 2:
        urgency += 0.45
    if hp <= 2:
        urgency += 0.55
    elif hp <= 4:
        urgency += 0.25

    # Supply-based scaling: if supply is high, competition may be less intense.
    supply_factor = 0.9
    if supply >= 22:
        supply_factor = 0.85
    elif supply <= 16:
        supply_factor = 1.05

    # Base competitive threshold from yesterday
    # If highest was extremely high, bid slightly above the second-highest.
    if highest_prev_bid >= DAILY_SALARY * 1.35:
        target = (second_prev_bid + 5.0)
    elif highest_prev_bid >= DAILY_SALARY * 1.10:
        target = (highest_prev_bid * 0.92)
    else:
        target = max(DAILY_SALARY * 0.55, highest_prev_bid + 1.5)

    # Apply urgency and supply factor
    target = target * (1.0 + urgency) * supply_factor

    # Keep within budget and avoid overspending
    max_reasonable = DAILY_SALARY * 1.6
    if day <= 3:
        # Early days: ensure we don't get starved by underbidding
        max_reasonable = DAILY_SALARY * 1.7
    if hp <= 2:
        max_reasonable = DAILY_SALARY * 1.95

    bid = min(budget, max_reasonable, target)

    # Ensure non-negative
    if bid < 0:
        bid = 0.0

    # If we are bidding too low relative to yesterday high bids, bump slightly
    if highest_prev_bid > 0 and bid < highest_prev_bid * 0.75:
        bid = min(budget, highest_prev_bid * 0.82)

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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday bids only from previous_trace
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # If we have no signal, use a conservative baseline
    if not prev_bids:
        base = DAILY_SALARY * 0.55
        if hp <= 2 or no_water_days >= 2:
            base = DAILY_SALARY * 0.85
        return min(budget, base)

    highest_prev_bid = max(prev_bids)
    second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev_bid

    # Estimate how aggressive the market is: if someone was bidding near/above salary, expect high contention.
    high_contention = highest_prev_bid >= DAILY_SALARY * 0.85

    # Our goal: bid enough to secure water without matching the highest bidder.
    # Use a target near the second-highest, with a small bump when our hp is fragile.
    if high_contention:
        target = second_prev_bid + 5.0
    else:
        # Moderate contention: stay below the leader but above our baseline.
        target = max(DAILY_SALARY * 0.5, (highest_prev_bid + second_prev_bid) / 2.0)

    # Scale based on our urgency
    urgency = 0
    if hp <= 2:
        urgency = 2
    elif hp <= 4:
        urgency = 1
    if no_water_days >= 2:
        urgency = max(urgency, 2)

    if urgency == 2:
        target *= 1.10
    elif urgency == 1:
        target *= 1.05

    # Supply-aware adjustment: higher supply reduces need to overbid.
    # supply is in [15,25]
    supply_frac = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    # When supply is high, slightly reduce target.
    target *= (0.98 - 0.10 * supply_frac)

    # Hard caps to prevent bankrupting ourselves
    # Never bid more than a fraction of budget; keep some reserve for later days.
    reserve_frac = 0.25 if day <= 5 else 0.15
    max_affordable = budget * (1.0 - reserve_frac)

    # Also keep within reasonable bidding range relative to daily salary
    target = min(target, DAILY_SALARY * 1.2)

    bid = min(max_affordable, max(0.0, target))
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

    # Alive opponents
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    # If no opponents, take what we can safely
    if not alive:
        return int(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Extract yesterday bids to estimate competitive pressure
    prev_bids = []
    for oid, o in alive:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev_bid

    # Estimate how many water units are likely contested this day
    # supply is total units; each player needs WATER_REQ to avoid no-water days
    # Use a conservative index based on supply buckets.
    supply_bucket = int((supply - MIN_SUPPLY) / max(1.0, (MAX_SUPPLY - MIN_SUPPLY)) * 2)
    if supply_bucket < 0:
        supply_bucket = 0
    if supply_bucket > 2:
        supply_bucket = 2

    # Baseline bid: follow the observed aggressive clearing bids (~90-93)
    # Increase slightly when yesterday pressure was high.
    pressure = 0.0
    if highest_prev_bid > 0:
        pressure = highest_prev_bid / float(DAILY_SALARY)

    # Compute target bid
    # - If yesterday's high bid was near DAILY_SALARY, we match+small premium to secure water.
    # - Otherwise, bid around mid-range but still above likely second-high.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        base = max(highest_prev_bid + 2.0, second_prev_bid + 3.0)
    else:
        base = max(DAILY_SALARY * (0.45 + 0.1 * pressure), second_prev_bid + 1.5)

    # Adjust for my hp: if low, bid more to prevent elimination; if high, bid less to save budget.
    hp = int(my_status['hp'])
    if hp <= 2:
        hp_mult = 1.15
    elif hp <= 4:
        hp_mult = 1.05
    else:
        hp_mult = 0.95

    # Adjust for supply bucket: when supply is higher, competition may relax; bid slightly less.
    # supply_bucket: 0 (low supply) -> higher bid; 2 (high supply) -> lower bid
    supply_mult = [1.08, 1.00, 0.92][supply_bucket]

    target = base * hp_mult * supply_mult

    # Budget safety: never bid more than budget
    budget = float(my_status['budget'])
    if budget <= 0:
        return 0

    # Also cap bid to avoid burning too much when hp is already safe
    if hp >= 6:
        cap = DAILY_SALARY * 0.7
    else:
        cap = DAILY_SALARY * 0.95

    bid = int(min(budget, cap, target))
    if bid < 0:
        bid = 0
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

    supply = day_context['supply']
    day = day_context['day']

    alive_opps = [o for o in opponents_status.values() if o.get('alive', True)]
    if not alive_opps:
        # If no opponents, bid enough to secure water but conserve budget.
        return float(min(my_status['budget'], DAILY_SALARY * 0.45))

    # Extract yesterday bids from each opponent's previous_trace
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Estimate competitive pressure from yesterday
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid
    else:
        highest_prev_bid = DAILY_SALARY * 0.6
        second_prev_bid = highest_prev_bid

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Supply pressure: higher supply means less need to overbid; lower supply means overbid.
    # Normalize supply into [0,1] using known bounds.
    s_norm = (float(supply) - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    s_norm = max(0.0, min(1.0, s_norm))

    # Base target bid relative to yesterday's highest bid.
    # If others bid high, we slightly undercut to win while saving budget.
    # If my hp is low, we bid more aggressively.
    aggressiveness = 1.0
    if my_hp <= 2.0:
        aggressiveness = 1.25
    elif my_hp <= 4.0:
        aggressiveness = 1.12

    if no_water_days >= 2:
        aggressiveness *= 1.15

    # Choose a competitive target.
    # When highest_prev_bid is around ~115-120, aim near (highest - small delta).
    delta = 2.0 + (1.0 - s_norm) * 2.0  # bid slightly more when supply is low
    target = (highest_prev_bid - delta) * aggressiveness

    # Also ensure we are not too low relative to second-highest.
    floor_target = (second_prev_bid - 1.5) * (1.0 + 0.15 * (1.0 - s_norm))
    target = max(target, floor_target)

    # If supply is high and my hp is healthy, conserve more.
    if s_norm > 0.6 and my_hp >= 7.0 and no_water_days == 0:
        target *= 0.85

    # Convert to final bid within budget.
    # Keep bid at most a fraction of budget to avoid bankruptcy.
    # Near end of episode (day>=8), increase urgency.
    episode_days = 10
    endgame_boost = 1.0
    if int(day) >= episode_days - 2:
        endgame_boost = 1.15
    target *= endgame_boost

    # Safety caps
    max_affordable = my_budget
    # If my budget is tiny, bid proportionally.
    if my_budget <= 10:
        return float(min(my_budget, 10.0))

    # Final bid: cannot exceed budget and should be at least 1.
    bid = float(min(max_affordable, max(1.0, target)))
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

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if budget <= 0:
        return 0.0

    # Extract yesterday bids from alive opponents (immediate reaction only)
    prev_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    prev_bids.append(float(b))
                except Exception:
                    pass

    # Estimate opponent pressure
    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    # Supply pressure: lower supply means more competition -> bid higher
    # supply is between 15 and 25
    supply_mid = (MIN_SUPPLY + MAX_SUPPLY) / 2.0
    supply_factor = 1.0
    if supply <= supply_mid:
        supply_factor = 1.15
    else:
        supply_factor = 0.95

    # Our urgency: low HP or many no-water days => bid much higher
    urgency = 1.0
    if hp <= 2:
        urgency = 1.35
    elif hp <= 4:
        urgency = 1.20
    elif no_water_days >= 2:
        urgency = 1.15

    # Target bid baseline derived from yesterday's best signal
    # If someone bid extremely high yesterday, match pressure to avoid being outbid.
    if highest_prev >= DAILY_SALARY * 1.8:
        base = max(highest_prev * 0.75, DAILY_SALARY * 0.95)
    elif avg_prev > DAILY_SALARY * 1.2:
        base = max(avg_prev * 0.65, DAILY_SALARY * 0.75)
    else:
        base = max(DAILY_SALARY * 0.6, highest_prev * 0.55)

    # Apply factors and cap by budget
    bid = base * supply_factor * urgency

    # Keep some budget for later; but if we are in danger, spend more.
    if hp <= 2 or no_water_days >= 3:
        budget_cap = budget * 0.95
    elif hp <= 4 or no_water_days >= 2:
        budget_cap = budget * 0.85
    else:
        budget_cap = budget * 0.75

    bid = min(bid, budget_cap, budget)

    # Ensure non-negative
    if bid < 0:
        bid = 0.0

    return float(bid)
"""
