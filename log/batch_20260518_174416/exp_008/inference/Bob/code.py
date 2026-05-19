# ============================================================
# Experiment: exp_008
# Agent: Bob
# Source: exp_008
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

    # Alive opponents and their yesterday bids
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                yesterday_bids.append(float(bid))
            except Exception:
                pass

    # Base strategy: aim to win around our requirement but avoid unnecessary spending.
    # If supply is low, we bid more aggressively; if high, bid less.
    # target_bid is centered near a fraction of DAILY_SALARY.
    supply_mid = (MIN_SUPPLY + MAX_SUPPLY) / 2.0
    if supply <= supply_mid:
        target_bid = DAILY_SALARY * 0.62
    else:
        target_bid = DAILY_SALARY * 0.5

    # Reactive adjustment: if someone bid very high yesterday, slightly raise to avoid being outcompeted.
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # If we are in danger, match pressure more.
            if float(my_status.get('hp', 0)) <= 2.0:
                target_bid = max(target_bid, DAILY_SALARY * 0.9)
            else:
                target_bid = max(target_bid, DAILY_SALARY * 0.7)
        elif highest_prev_bid >= DAILY_SALARY * 0.65:
            target_bid = max(target_bid, highest_prev_bid * 0.92)
        else:
            # If opponents were mild, we can be slightly cheaper.
            target_bid = min(target_bid, DAILY_SALARY * 0.55)

    # Health/budget risk management
    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # If we've already missed water, increase bid to recover.
    if no_water_days >= 2:
        target_bid = max(target_bid, DAILY_SALARY * 0.75)
    if hp <= 2.0:
        target_bid = max(target_bid, DAILY_SALARY * 0.85)

    # Never bid more than we can afford.
    bid = min(budget, target_bid)

    # Ensure non-negative
    if bid < 0:
        bid = 0.0

    return float(bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Alive opponents
    alive_opps = []
    for _aid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Read yesterday bids from previous_trace only (immediate reaction)
    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        if isinstance(prev, dict):
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

    # If opponents were bidding very high yesterday, avoid overpaying unless we are in danger
    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Base bid depends on our urgency
    if hp <= 2 or no_water_days >= 2:
        urgency_mult = 0.95
    elif hp <= 4 or no_water_days >= 1:
        urgency_mult = 0.75
    else:
        urgency_mult = 0.55

    # Supply pressure: higher supply means we can bid less to still get water
    # Normalize supply between MIN_SUPPLY and MAX_SUPPLY
    min_s = 15.0
    max_s = 25.0
    if max_s > min_s:
        supply_ratio = (supply - min_s) / (max_s - min_s)
    else:
        supply_ratio = 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # If yesterday highest was extreme, cap our bid to avoid bidding into a bidding war
    extreme = highest_prev_bid >= DAILY_SALARY * 0.85

    # Target bid: try to slightly undercut the likely winner unless we are urgent
    if yesterday_bids:
        # If we are not urgent, target around second-highest + small epsilon
        if not extreme and urgency_mult < 0.8:
            target = second_prev_bid + 2.0
        else:
            # Urgent or extreme: bid closer to highest but not exceeding our budget
            target = min(highest_prev_bid, second_prev_bid + 6.0) + 1.0
    else:
        target = DAILY_SALARY * 0.5

    # Adjust by urgency and supply
    # More supply => lower bid; less supply => higher bid
    supply_adjust = 1.0 - 0.25 * supply_ratio
    bid = target * urgency_mult * supply_adjust

    # Safety caps
    min_bid = DAILY_SALARY * 0.35
    max_bid = DAILY_SALARY * 0.98
    bid = max(min_bid, min(max_bid, bid))

    # Final budget constraint
    bid = min(bid, budget)

    # If budget is extremely low, spend what we can
    if bid <= 0.0:
        return 0.0
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

    # Identify alive opponents and read yesterday trace
    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    # If no opponents alive, bid conservatively
    if not alive_opponents:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Extract yesterday bids from immediate previous_trace
    yesterday_bids = []
    yesterday_pressures = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev:
            bid = prev.get('bid', None)
            if bid is not None:
                yesterday_bids.append(float(bid))
            # Use hp_after/status as a pressure proxy if available
            hp_after = prev.get('hp_after', None)
            status = prev.get('status', None)
            if hp_after is not None:
                try:
                    yesterday_pressures.append((float(hp_after), status))
                except Exception:
                    pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Decide aggressiveness based on yesterday's maximum bid
    # If someone was willing to spend near/above our daily salary, they likely overbid again.
    # We respond with a mid bid to avoid burning budget, but still compete.
    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Supply-based baseline: with supply in [15,25], number of full water units is 1 or 2.
    # We assume others will fight for 2 units when supply is high.
    supply_units = int(supply // float(WATER_REQ))
    if supply_units < 1:
        supply_units = 1
    if supply_units > 2:
        supply_units = 2

    # Baseline bid levels
    if supply_units == 2:
        baseline = DAILY_SALARY * 0.62
    else:
        baseline = DAILY_SALARY * 0.48

    # Pressure adjustment using yesterday highest bid
    # Thresholds tuned to the observed yesterday bids (~100-140)
    if highest_prev_bid >= DAILY_SALARY * 1.15:
        # Opponent(s) were extremely aggressive; increase bid to secure water this day.
        if my_hp <= 2.0 or no_water_days >= 2:
            target = DAILY_SALARY * 0.95
        else:
            target = DAILY_SALARY * 0.78
    elif highest_prev_bid >= DAILY_SALARY * 0.85:
        # Moderate aggression from others.
        if my_hp <= 2.0 or no_water_days >= 2:
            target = DAILY_SALARY * 0.82
        else:
            target = baseline + (DAILY_SALARY * 0.12)
    else:
        # Others were not too aggressive; keep bid near baseline.
        if my_hp <= 2.0 or no_water_days >= 2:
            target = DAILY_SALARY * 0.72
        else:
            target = baseline

    # Ensure we don't overbid beyond budget; also keep some reserve
    # Reserve fraction increases when our hp is low.
    if my_hp <= 2.0:
        reserve_frac = 0.15
    else:
        reserve_frac = 0.25

    max_affordable = max(0.0, my_budget * (1.0 - reserve_frac))
    bid = float(min(max_affordable, target))

    # Final guard: if budget is tiny, bid whatever we can.
    if bid <= 0.0:
        bid = float(min(my_budget, DAILY_SALARY * 0.3))

    return bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        return float(min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace only
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

    # Competitive target: react to pressure from the strongest surviving bidder
    # If someone bid very high yesterday, we must contest more to avoid falling behind.
    # Otherwise, we bid enough to be in the mix while conserving budget.
    if highest_prev_bid >= DAILY_SALARY * 1.3:
        # Very aggressive yesterday; contest but don't burn budget.
        if hp <= 2 or no_water_days >= 1:
            target = DAILY_SALARY * 0.95
        else:
            target = DAILY_SALARY * 0.45 + min(DAILY_SALARY * 0.35, highest_prev_bid * 0.25)
    elif highest_prev_bid >= DAILY_SALARY * 0.8:
        # Moderate-high; bid slightly above a conservative share.
        if hp <= 2 or no_water_days >= 1:
            target = DAILY_SALARY * 0.8
        else:
            target = DAILY_SALARY * 0.55 + min(DAILY_SALARY * 0.25, highest_prev_bid * 0.18)
    else:
        # Low pressure; conserve.
        if hp <= 2 or no_water_days >= 1:
            target = DAILY_SALARY * 0.75
        else:
            target = DAILY_SALARY * 0.35

    # Supply-aware scaling: if supply is near max, we can bid less; if near min, bid more.
    # supply in [15,25]
    if supply <= MIN_SUPPLY:
        supply_mult = 1.15
    elif supply >= MAX_SUPPLY:
        supply_mult = 0.85
    else:
        supply_mult = 1.05 - 0.2 * ((supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY))

    target *= float(supply_mult)

    # Ensure we don't exceed budget and keep a minimum bid to avoid zero-water spiral.
    # Minimum is tied to our requirement urgency.
    if hp <= 1 or no_water_days >= 2:
        min_bid = DAILY_SALARY * 0.5
    elif hp <= 3 or no_water_days >= 1:
        min_bid = DAILY_SALARY * 0.35
    else:
        min_bid = DAILY_SALARY * 0.2

    bid = max(min_bid, target)
    bid = min(bid, budget)

    # If budget is extremely low, just bid what we can.
    if bid < 0.0:
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

    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Use only yesterday's immediate trace bids to infer pressure.
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # Estimate how much water is likely needed to stay safe.
    # If we already have consecutive no-water days, increase urgency.
    urgency = 0
    if no_water_days >= 2:
        urgency = 2
    elif no_water_days == 1:
        urgency = 1

    # Determine opponent pressure from yesterday.
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Base target bid: if opponents were bidding high, we must match/just exceed.
    # Otherwise, bid enough to secure water without burning budget.
    # Keep indices safe (no arrays used), but still ensure numeric safety.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # High pressure day.
        if hp <= 2:
            target = highest_prev_bid + 5.0
        elif hp <= 4:
            target = highest_prev_bid + 2.5
        else:
            target = highest_prev_bid + 1.0
    else:
        # Moderate pressure.
        if hp <= 2:
            target = max(highest_prev_bid + 3.0, DAILY_SALARY * 0.85)
        elif hp <= 4:
            target = max(highest_prev_bid + 2.0, DAILY_SALARY * 0.65)
        else:
            target = max(highest_prev_bid + 1.0, DAILY_SALARY * 0.55)

    # Adjust by our urgency and today's supply (more supply => less need to overbid).
    # supply between 15 and 25, map to discount factor.
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
        supply_ratio = 0.0 if supply_ratio < 0.0 else (1.0 if supply_ratio > 1.0 else supply_ratio)
    else:
        supply_ratio = 0.5

    # If supply is high, reduce; if low, increase.
    target *= (1.0 + (0.5 - supply_ratio) * 0.25)

    # Urgency pushes bid up.
    target *= (1.0 + 0.08 * urgency)

    # Budget safety: never bid more than we can afford; also avoid bidding beyond a fraction unless critical.
    critical = (hp <= 2) or (no_water_days >= 2)
    max_affordable = budget
    if critical:
        cap = max_affordable
    else:
        cap = min(max_affordable, DAILY_SALARY * 1.6)

    bid = min(cap, max(0.0, target))

    # If budget is extremely low, bid what we can.
    if budget <= 1.0:
        return min(1.0, budget)

    # Ensure bid is at least 1 when trying to secure water.
    if bid < 1.0 and critical:
        bid = min(1.0, budget)

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

    supply = day_context['supply']
    day = day_context['day']

    # Identify alive opponents
    alive = []
    for agent_id, st in opponents_status.items():
        if st.get('alive', False):
            alive.append((agent_id, st))

    # Default conservative bid
    if my_status.get('budget', 0) <= 0:
        return 0

    # Read yesterday trace bids to infer pressure
    prev_bids = []
    for agent_id, st in alive:
        prev = st.get('previous_trace', {})
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                prev_bids.append(float(bid))
            except Exception:
                pass

    # Supply tightness: map [15,25] -> [0,1]
    try:
        tight = (MAX_SUPPLY - float(supply)) / float(MAX_SUPPLY - MIN_SUPPLY)
    except Exception:
        tight = 0.5
    if tight < 0:
        tight = 0
    if tight > 1:
        tight = 1

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # If we are in danger (very low hp or already no-water streak), bid harder
    danger = 0
    if hp <= 2:
        danger += 1
    if no_water_days >= 2:
        danger += 1

    # Estimate opponent pressure from yesterday
    pressure = 0
    if prev_bids:
        highest_prev = max(prev_bids)
        # Normalize relative to salary scale
        if highest_prev >= DAILY_SALARY * 0.85:
            pressure = 1
        elif highest_prev >= DAILY_SALARY * 0.55:
            pressure = 0.6
        else:
            pressure = 0.3

    # Base bid: aim for moderate share; scale with tightness and danger
    # Target fraction of salary
    base_frac = 0.38 + 0.22 * tight
    if pressure == 1:
        base_frac += 0.10
    elif pressure == 0.6:
        base_frac += 0.05

    if danger >= 2:
        base_frac += 0.35
    elif danger == 1:
        base_frac += 0.18

    # Convert to bid amount; keep within budget
    bid = base_frac * DAILY_SALARY

    # If supply is low enough that winning likely requires more, nudge up
    if float(supply) <= float(WATER_REQ) + 6:  # around 15-16
        bid += 0.15 * DAILY_SALARY

    # Make sure bid is not more than budget and not negative
    if bid < 0:
        bid = 0
    if bid > budget:
        bid = budget

    # If we have no budget, return 0 (already handled)
    return bid
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

    # Alive opponents
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    if not alive:
        # Conservative if no opponents
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids to infer who is applying pressure
    cindy_y = None
    max_prev_bid = 0.0
    for oid, o in alive:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                b = float(b)
            except Exception:
                b = 0.0
            if b > max_prev_bid:
                max_prev_bid = b
            if oid == 'Cindy':
                cindy_y = b

    # Determine how many allocations we likely need given supply
    # Approximate probability/urgency: if supply is low, bidding more helps secure water.
    # Use a simple urgency score.
    if supply <= WATER_REQ:
        urgency = 1.0
    else:
        # scale between 0.2..1.0 over supply range
        urgency = 0.2 + 0.8 * ((supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)) if MAX_SUPPLY != MIN_SUPPLY else 0.6
    urgency = max(0.2, min(1.0, urgency))

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # If we're already in danger, bid aggressively.
    danger = 1.0 if (hp <= 2.0 or no_water_days >= 2) else (0.6 if hp <= 4.0 else 0.2)

    # Base bid aimed to compete with Cindy's pressure.
    # If Cindy bid yesterday was very high, slightly undercut her; otherwise, bid mid-high.
    if cindy_y is not None and cindy_y > 0:
        if cindy_y >= DAILY_SALARY * 0.95:
            target = cindy_y - 5.0
        elif cindy_y >= DAILY_SALARY * 0.8:
            target = cindy_y - 10.0
        else:
            target = max(DAILY_SALARY * 0.55, cindy_y * 0.75)
    else:
        # Use max_prev_bid to infer general pressure
        if max_prev_bid >= DAILY_SALARY * 0.9:
            target = max_prev_bid - 8.0
        else:
            target = max(DAILY_SALARY * 0.5, max_prev_bid * 0.6)

    # Adjust for urgency and danger: bid more when supply is low or HP is critical.
    target = target * (0.75 + 0.5 * urgency) * (0.85 + 0.3 * danger)

    # Safety caps: never exceed budget and avoid wasting too much
    # Also keep within plausible bidding range
    cap = min(budget, DAILY_SALARY * 1.2)
    floor = 0.0

    bid = float(max(floor, min(cap, target)))

    # If budget is tiny, bid whatever we can.
    if bid <= 0.0 and budget > 0.0:
        bid = float(min(budget, DAILY_SALARY * 0.3))

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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opponents = [o for o in opponents_status.values() if o.get('alive')]
    if not alive_opponents:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from immediate previous_trace
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # Estimate how aggressive the field is
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        avg_prev_bid = sum(prev_bids) / float(len(prev_bids))
    else:
        highest_prev_bid = 0.0
        avg_prev_bid = 0.0

    # Pressure signal: if someone bid near/above salary, they were likely fighting for survival water.
    high_pressure = highest_prev_bid >= DAILY_SALARY * 0.85

    # Supply pressure: if supply is close to max, competition is more intense; if low, fewer can be satisfied.
    supply_mid = (MIN_SUPPLY + MAX_SUPPLY) / 2.0
    supply_factor = 0.85 if supply < supply_mid else 1.05

    # Core bid target
    if high_pressure:
        base = max(DAILY_SALARY * 0.55, avg_prev_bid * 0.95)
    else:
        base = max(DAILY_SALARY * 0.45, avg_prev_bid * 0.8)

    # My urgency: low hp or already accumulating no-water days => bid higher
    if my_hp <= 2.0:
        urgency = 1.35
    elif my_hp <= 4.0:
        urgency = 1.15
    else:
        urgency = 0.95

    if my_no_water_days >= 2:
        urgency *= 1.2

    target = base * urgency * supply_factor

    # Keep bid within budget and avoid overpaying late in episode
    # (episode_days not provided in function; use day_context day as proxy)
    # If close to end, spend more to ensure survival.
    endgame = 1.0
    if day >= 8:
        endgame = 1.15
    target *= endgame

    # Final cap
    bid = max(0.0, min(my_budget, target))
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    # Identify alive opponents and their yesterday bids
    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            prev = opp.get('previous_trace', {}) or {}
            if prev and prev.get('bid') is not None:
                alive.append((opp_id, float(prev.get('bid', 0.0)), opp))

    # If no info, bid conservative
    if not alive:
        base = DAILY_SALARY * 0.45
        return min(my_budget, max(0.0, base))

    # Use yesterday bids to gauge pressure
    yesterday_bids = [b for _, b, _ in alive]
    highest_prev_bid = max(yesterday_bids)
    second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid

    # Tight supply means higher chance we must win water.
    # Our share need is WATER_REQ; assume single allocation per day.
    # If supply is near minimum, we should be more aggressive.
    tightness = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)  # 0..1-ish
    tightness = max(0.0, min(1.0, tightness))

    # If we are in danger, spend more.
    danger = 0.0
    if my_hp <= 2.0:
        danger = 1.0
    elif my_hp <= 4.0:
        danger = 0.6
    if my_no_water_days >= 2:
        danger = max(danger, 0.7)

    # Cindy was aggressive yesterday (highest bids). If highest_prev_bid is large,
    # we don't match it; we slightly undercut unless we are in danger/tight supply.
    # Otherwise, we bid around a fraction of salary.
    if highest_prev_bid >= DAILY_SALARY * 1.2:
        # Aggressive field: target just above second-highest to beat most.
        target = second_prev_bid + (2.0 + 3.0 * tightness)
        if danger > 0.5:
            target = max(target, highest_prev_bid * 0.75)
    else:
        # Moderate field: bid enough to stay competitive but preserve budget.
        target = DAILY_SALARY * (0.45 + 0.35 * tightness) + (0.15 * (highest_prev_bid - second_prev_bid))
        if danger > 0.5:
            target = max(target, DAILY_SALARY * 0.75)

    # Ensure we don't bid more than budget; also keep non-negative.
    target = max(0.0, float(target))
    bid = min(my_budget, target)

    # If budget is extremely low, bid what we can.
    if my_budget <= 1e-6:
        return 0.0

    # Add a small floor to avoid always losing when we must survive.
    min_survival_bid = DAILY_SALARY * (0.25 + 0.25 * tightness)
    if danger > 0.5:
        min_survival_bid = DAILY_SALARY * 0.55
    bid = max(bid, min_survival_bid if my_budget >= min_survival_bid else bid)

    return float(min(my_budget, bid))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = day_context['supply']
    day = day_context['day']

    # Alive opponents
    alive_opps = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opps:
        # No competition: conserve but ensure survival
        target = DAILY_SALARY * 0.45
        return max(0.0, min(my_status['budget'], target))

    # Read yesterday bids from previous_trace
    prev_bids = []
    prev_high_pressure = None
    for opp in alive_opps:
        prev = opp.get('previous_trace') or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass
    if prev_bids:
        prev_high_pressure = max(prev_bids)

    # Determine if we should respond to pressure
    # Observed meta: surviving agents bid around 84-91; dying agent bid ~59.
    hp = my_status.get('hp', 0)
    budget = my_status.get('budget', 0.0)
    no_water_days = my_status.get('no_water_days', 0)

    # Base target depends on my survival urgency
    if hp <= 2 or no_water_days >= 2:
        base = DAILY_SALARY * 1.05  # aggressive to lock water
    elif hp <= 3:
        base = DAILY_SALARY * 0.95
    else:
        base = DAILY_SALARY * 0.62

    # If yesterday's max bid was high, slightly overbid to secure allocation
    if prev_high_pressure is not None:
        # If they were bidding near/above 85, we need to match or beat.
        if prev_high_pressure >= DAILY_SALARY * 0.85:
            # Bid enough to be competitive but still capped by budget.
            base = max(base, prev_high_pressure + 2.0)
        # If yesterday bids were low, we can bid closer to base cluster.
        elif prev_high_pressure <= DAILY_SALARY * 0.70:
            base = max(base, DAILY_SALARY * 0.55)

    # Convert supply context into a mild adjustment: lower supply => bid higher
    # Since supply_range is [15,25], map to [0,1] pressure.
    try:
        t = (float(supply) - 15.0) / (25.0 - 15.0)
    except Exception:
        t = 0.5
    # If supply is low (t small), increase bid; if high, decrease slightly.
    supply_adjust = (1.0 - t) * (DAILY_SALARY * 0.12)
    base = base + supply_adjust

    # Final cap: cannot exceed budget
    bid = max(0.0, min(float(budget), float(base)))
    return bid
"""
