# ============================================================
# Experiment: exp_100
# Agent: Bob
# Source: exp_100
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

    # Budget guardrails
    budget = float(my_status['budget'])
    hp = float(my_status['hp'])
    no_water_days = int(my_status['no_water_days'])

    # If we are in danger, bid aggressively regardless of opponent
    if hp <= 2 or no_water_days >= 2:
        return max(0.0, min(budget, DAILY_SALARY * 0.95))

    # Collect opponents that are alive and have a usable previous bid
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                alive_opps.append((opp_id, float(prev.get('bid', 0.0)), prev))

    # Default: moderate bid to avoid overspending
    base_bid = DAILY_SALARY * 0.55

    if alive_opps:
        prev_bids = [b for (_, b, _) in alive_opps]
        highest_prev_bid = max(prev_bids)
        lowest_prev_bid = min(prev_bids)

        # If someone previously signaled high urgency (near our salary), match/beat them
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # If we have decent hp, slightly undercut; if not, bid closer to max
            if hp >= 4:
                bid = highest_prev_bid + 2.0
            else:
                bid = highest_prev_bid + 6.0
        else:
            # If pressure was low, bid around base but nudge above the median/low bidder
            # Use highest_prev_bid as a conservative anchor
            bid = max(base_bid, highest_prev_bid + 1.0)

        # Supply-aware adjustment: when supply is tight, increase aggressiveness
        # supply is within [15,25] typically; normalize loosely
        if float(supply) <= 18.0:
            bid *= 1.15
        elif float(supply) >= 22.0:
            bid *= 0.95

        # Ensure bid is feasible
        return max(0.0, min(budget, bid))

    # No opponent trace info: bid moderately
    return max(0.0, min(budget, base_bid))
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

    # Alive opponents
    alive = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    supply = float(day_context['supply'])
    day = day_context['day']

    # Use only yesterday's immediate trace bid to infer pressure
    prev_bids = []
    for o in alive:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # If we saw very high bids, we should not fully mirror them; instead bid a controlled amount.
    highest_prev = max(prev_bids) if prev_bids else 0.0
    second_prev = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev

    # Estimate how many water units are likely needed per day
    # (This is just to adjust aggression; actual allocation is game-defined.)
    supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    supply_factor = max(0.0, min(1.0, supply_factor))

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Base bid target: slightly above typical mid pressure.
    # If Cindy/Eric were bidding high, we bid enough to secure water but not to drain budget.
    # Use highest_prev to decide whether to increase.
    pressure = 0.0
    if highest_prev >= DAILY_SALARY * 0.85:
        pressure = 1.0
    elif highest_prev >= DAILY_SALARY * 0.6:
        pressure = 0.6
    else:
        pressure = 0.3

    # If our HP is low or accumulating no-water days, we must bid more.
    urgency = 0.0
    if hp <= 2.0:
        urgency = 1.0
    elif hp <= 4.0:
        urgency = 0.7
    elif no_water_days >= 2:
        urgency = 0.6
    else:
        urgency = 0.3

    # Target bid formula
    # - Start from a mid baseline
    baseline = DAILY_SALARY * (0.45 + 0.2 * supply_factor)  # 40-65
    # - Add a small increment over second-highest yesterday to beat bids that follow similar patterns
    increment = 0.15 * (second_prev if second_prev > 0 else highest_prev)
    # - Increase with urgency and pressure, but cap to avoid matching Cindy/Eric extremes
    target = baseline + increment * (0.6 + 0.4 * urgency) + 20.0 * pressure * urgency

    # Hard caps based on budget and not overpaying relative to daily salary
    cap = DAILY_SALARY * (0.85 if urgency >= 0.7 else 0.65)
    bid = min(target, cap, budget)

    # Ensure non-negative and at least a small bid if budget allows
    if bid < 0:
        bid = 0.0
    if bid == 0.0 and budget > 0:
        bid = min(budget, DAILY_SALARY * 0.2)

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
    day = day_context['day']

    # Alive opponents
    alive = []
    for k, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((k, o))

    if not alive:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Immediate reaction from yesterday traces only
    prev_bids = []
    for _, o in alive:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Determine how many full water units supply can cover this day
    # (Used to calibrate aggressiveness; avoid float-index issues by not indexing arrays.)
    max_units = int(supply // float(WATER_REQ)) if WATER_REQ > 0 else 0

    # Baseline: secure moderate share
    # If supply is tight (<= 18), we must bid more to avoid being squeezed.
    tight_supply = supply <= 18.0

    # If opponents previously pushed very high, we undercut slightly unless low HP forces us.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        if my_status['hp'] <= 2 or my_status.get('no_water_days', 0) >= 2:
            bid = DAILY_SALARY * 0.95
        else:
            bid = max(DAILY_SALARY * 0.55, highest_prev_bid * 0.75)
    else:
        if my_status['hp'] <= 2 or my_status.get('no_water_days', 0) >= 2:
            bid = DAILY_SALARY * 0.85
        else:
            bid = DAILY_SALARY * (0.65 if tight_supply else 0.55)

    # If supply can cover only 1 unit, increase slightly to avoid losing the last slot
    if max_units <= 1:
        bid *= 1.15

    # Safety cap by budget
    bid = float(min(my_status['budget'], bid))

    # Ensure non-negative
    if bid < 0:
        bid = 0.0

    return bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        # If no opponents, bid conservatively to preserve budget.
        return max(0.0, min(my_budget, DAILY_SALARY * 0.35))

    # Read yesterday bids to gauge aggressiveness.
    prev_bids = []
    prev_hp_after = []
    for opp_id, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev['bid']))
            prev_hp_after.append(float(prev.get('hp_after', 0.0)))

    if prev_bids:
        highest_prev_bid = max(prev_bids)
        lowest_prev_bid = min(prev_bids)
        # If someone previously bid very low and died/was low HP, they likely continue to underbid.
        # Use that to avoid overbidding.
        min_hp_after = min(prev_hp_after) if prev_hp_after else 0.0
    else:
        highest_prev_bid = 0.0
        lowest_prev_bid = 0.0
        min_hp_after = 0.0

    # Supply pressure: more supply means we can bid less to still get water.
    # supply is between 15 and 25.
    # target_water_share is 1 unit of requirement, but we bid for winning allocation.
    # Estimate how many players could plausibly get water: supply / WATER_REQ.
    # Use float then convert to int for any indexing (none used), but keep safe.
    supply_units = supply / float(WATER_REQ)

    # Base bid scales with supply scarcity.
    # Scarcer supply (closer to 15) => higher bid.
    scarcity = (float(MAX_SUPPLY) - supply) / float(MAX_SUPPLY - MIN_SUPPLY)  # 0..1
    base = DAILY_SALARY * (0.42 + 0.18 * scarcity)  # ~0.42..0.60 of salary

    # React to our HP/no-water streak.
    # If we've gone without water, we must secure water more aggressively.
    urgency = 0.0
    if my_no_water_days >= 1:
        urgency += 0.22
    if my_no_water_days >= 2:
        urgency += 0.30
    if my_hp <= 2:
        urgency += 0.45
    if my_hp <= 1:
        urgency += 0.55

    # Opponent reaction: if Cindy/Alex likely bid high, we slightly shade below the highest.
    # But if someone died with low bid (Eric), we can shade more.
    aggressiveness_factor = 0.0
    if prev_bids:
        # If highest yesterday was high, competition exists.
        if highest_prev_bid >= DAILY_SALARY * 1.2:
            aggressiveness_factor += 0.10
        if lowest_prev_bid <= DAILY_SALARY * 0.35 and min_hp_after <= 0.0:
            # Underbidder likely continues; reduce our bid.
            aggressiveness_factor -= 0.08

    # Final bid target.
    bid = base * (1.0 + urgency + aggressiveness_factor)

    # Do not exceed budget.
    bid = min(bid, my_budget)

    # Ensure we bid at least a small fraction to avoid consistently losing when HP is low.
    min_bid = DAILY_SALARY * (0.20 if my_hp > 3 else 0.55)
    bid = max(min_bid, bid)

    # If supply is high enough, lower bid slightly.
    if supply >= 22.0:
        bid *= 0.92

    # If it's late in episode, increase urgency to prevent end-game death.
    if day >= 8:
        bid *= 1.10

    # Final clamp.
    if bid < 0.0:
        bid = 0.0
    if bid > my_budget:
        bid = my_budget

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

    # Identify alive opponents and yesterday bids
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            prev = o.get('previous_trace', {}) or {}
            bid = prev.get('bid', None)
            alive.append((oid, o, bid))

    if not alive:
        return max(0, min(my_status['budget'], int(DAILY_SALARY * 0.4)))

    # Use yesterday's bids to estimate competitive pressure
    bids = [b for (_, _, b) in alive if isinstance(b, (int, float))]
    bids_sorted = sorted(bids) if bids else []

    # If we have bid data, target below the median survivor pressure
    # (Cindy/David appear to overbid; we try to undercut.)
    if bids_sorted:
        # choose a conservative target: 2nd highest if available else highest
        # then underbid by a small margin
        if len(bids_sorted) >= 2:
            target = bids_sorted[-2]
        else:
            target = bids_sorted[-1]
        # Underbid to win when possible but keep budget
        bid = int(max(0, min(my_status['budget'], target * 0.92)))
    else:
        bid = int(min(my_status['budget'], DAILY_SALARY * 0.55))

    # Adjust for our own HP/urgency
    hp = my_status.get('hp', 0)
    no_water_days = my_status.get('no_water_days', 0)

    # If we're close to death or have already missed water, increase bid sharply
    if hp <= 2:
        bid = int(min(my_status['budget'], max(bid, DAILY_SALARY * 0.9)))
    elif hp <= 4 or no_water_days >= 2:
        bid = int(min(my_status['budget'], max(bid, DAILY_SALARY * 0.65)))

    # Supply-based adjustment: with higher supply we can bid less
    # supply range is 15..25, water requirement is 9 per unit; approximate scarcity
    # Use a simple scarcity factor without indexing.
    s = float(supply)
    scarcity = (MAX_SUPPLY - s) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    bid = int(bid * (0.9 + 0.2 * scarcity))

    # Final clamp and ensure non-negative integer
    if my_status['budget'] is None:
        return 0
    bid = max(0, min(int(bid), int(my_status['budget'])))
    return bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Identify alive opponents and their yesterday bids
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Estimate how contested this is: Cindy likely high bidder (survived 10 with high avg)
    # Use yesterday max as proxy for pressure.
    pressure = max(yesterday_bids) if yesterday_bids else 0.0

    # Budget-aware target: if Cindy is bidding high, we undercut slightly.
    # If pressure is low, we bid moderately.
    # Also react to our HP: if low, bid aggressively.
    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])

    # Supply heuristic: with supply in [15,25], at most 2 units of WATER_REQ fit.
    # When supply is closer to 15, competition is tighter.
    tightness = (25.0 - supply) / 10.0  # 0 at 25, 1 at 15
    tightness = max(0.0, min(1.0, tightness))

    # Base bid
    if my_hp <= 2.0:
        base = DAILY_SALARY * (0.9 + 0.05 * tightness)
    elif my_hp <= 4.0:
        base = DAILY_SALARY * (0.65 + 0.15 * tightness)
    else:
        base = DAILY_SALARY * (0.45 + 0.20 * tightness)

    # If yesterday pressure was high, raise to just below pressure to steal marginal water.
    # If pressure is extremely high, still cap by budget and salary scale.
    if pressure > 0.0:
        # Undercut by a small amount; ensure we don't go too low.
        target = min(base, pressure - 5.0) if pressure - 5.0 > 0 else base
        # If our base is too low relative to pressure, bump up near pressure but not exceed.
        if target < pressure * 0.55:
            target = pressure * (0.60 + 0.10 * tightness)
    else:
        target = base

    # Keep within reasonable bounds and budget
    # Also avoid bidding above what we can afford.
    bid = min(my_budget, max(0.0, target))

    # If budget is tiny, bid what we can (still non-negative)
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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    # If we are in critical health, prioritize staying alive.
    critical = (my_hp <= 2) or (my_no_water_days >= 2)

    # Observe yesterday bids from alive opponents.
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    yesterday_bids = []
    yesterday_pressures = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                b = float(b)
            except Exception:
                b = None
        if b is not None:
            yesterday_bids.append(b)
            # Track whether opponent ended yesterday with low hp / budget.
            hp_after = prev.get('hp_after', None)
            budget_after = prev.get('budget_after', None)
            status = prev.get('status', None)
            pressure = 0
            if hp_after is not None and int(hp_after) <= 0:
                pressure += 2
            if budget_after is not None and float(budget_after) <= 0:
                pressure += 2
            if status in ('dead', 'out', 'failed'):
                pressure += 1
            yesterday_pressures.append((b, pressure, oid))

    # If no data, fall back to a conservative bid.
    if not yesterday_bids:
        cap = min(my_budget, DAILY_SALARY * (0.85 if critical else 0.55))
        return max(0.0, cap)

    highest_prev_bid = max(yesterday_bids)

    # Estimate how many water units are likely needed this day.
    # We assume water allocation is proportional to bids vs total supply; use a heuristic.
    # If supply is low, we need to secure more aggressively.
    supply_ratio = (supply - MIN_SUPPLY) / max(1e-9, (MAX_SUPPLY - MIN_SUPPLY))
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Identify opponents who likely overreached yesterday (high bid but died/ran out).
    # We exploit by bidding just enough to beat their desperation without matching their waste.
    overreach_bids = []
    for b, pressure, oid in yesterday_pressures:
        if pressure >= 2:
            overreach_bids.append(b)

    # Base strategy:
    # - If we are critical: bid high but not maximum.
    # - Otherwise: bid around a fraction of the highest previous bid,
    #   adjusted down if overreach_bids exist.
    if critical:
        # Bid enough to avoid death; scale with supply.
        target = DAILY_SALARY * (0.75 + 0.15 * (1.0 - supply_ratio))
        # If others were bidding extremely high yesterday, we may need to match more.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            target = max(target, highest_prev_bid * 0.85)
        bid = min(my_budget, target)
    else:
        # Non-critical: try to win without draining budget.
        # If highest previous bid was very high, don't fully chase it.
        chase_factor = 0.65
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            chase_factor = 0.55
        if overreach_bids:
            # Overreachers likely wasted water; bid slightly below their peak.
            chase_factor = min(chase_factor, 0.52)
        target = highest_prev_bid * chase_factor

        # Also ensure we bid at least a reasonable baseline to compete.
        baseline = DAILY_SALARY * (0.42 + 0.18 * (1.0 - supply_ratio))
        bid = max(target, baseline)
        bid = min(my_budget, bid)

    # Safety: never bid negative.
    if bid < 0:
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
            alive_opponents.append((oid, o))

    if not alive_opponents:
        return float(min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids for immediate pressure signal
    yesterday_bids = []
    for _, o in alive_opponents:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Supply pressure: higher supply reduces marginal need; lower supply increases need
    # Map supply into [0,1]
    if MAX_SUPPLY <= MIN_SUPPLY:
        supply_factor = 0.5
    else:
        supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
        if supply_factor < 0.0:
            supply_factor = 0.0
        if supply_factor > 1.0:
            supply_factor = 1.0

    # Core bid target
    # If opponents previously bid aggressively, match/beat slightly.
    aggressive_threshold = DAILY_SALARY * 0.85

    # Base aggressiveness from my hp/no_water_days
    if hp <= 2.0 or no_water_days >= 2:
        survival_mode = 1.0
    elif hp <= 4.0 or no_water_days == 1:
        survival_mode = 0.6
    else:
        survival_mode = 0.3

    if highest_prev_bid >= aggressive_threshold:
        # They likely overbid to secure water; bid to avoid losing the auction.
        # Slightly outbid but keep bounded.
        target = highest_prev_bid + 2.0
        target *= (0.85 + 0.3 * survival_mode)
    else:
        # Otherwise, bid enough to stay competitive, more when supply is low.
        # When supply_factor is low (near MIN_SUPPLY), increase.
        target = DAILY_SALARY * (0.45 + 0.25 * (1.0 - supply_factor))
        target *= (0.85 + 0.4 * survival_mode)

    # Convert target into a budget-safe bid
    # Also cap to avoid burning budget too fast.
    # Use remaining days heuristic: with hp low, allow higher spend.
    # Approximate remaining safe window as hp.
    if hp <= 2.0:
        cap = DAILY_SALARY * 0.95
    elif hp <= 4.0:
        cap = DAILY_SALARY * 0.8
    else:
        cap = DAILY_SALARY * 0.65

    bid = float(min(budget, cap, max(0.0, target)))

    # Ensure at least a minimal bid if budget allows; helps against low bids.
    min_bid = 1.0
    if bid < min_bid and budget >= min_bid:
        bid = min_bid

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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append((oid, o))

    if not alive_opponents:
        return float(min(my_budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace for immediate reaction.
    yesterday_bids = []
    yesterday_high_pressure = []
    for oid, o in alive_opponents:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                b_val = float(b)
            except Exception:
                continue
            yesterday_bids.append(b_val)
            if b_val >= DAILY_SALARY * 0.85:
                yesterday_high_pressure.append((oid, b_val))

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = 0.0
    if len(yesterday_bids) >= 2:
        s = sorted(yesterday_bids)
        second_prev_bid = s[-2]

    # Supply pressure: higher supply reduces urgency; lower supply increases urgency.
    # Normalize to [0,1] where 0 means low supply (more scarce).
    if MAX_SUPPLY > MIN_SUPPLY:
        scarcity = 1.0 - (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        scarcity = 0.5
    scarcity = max(0.0, min(1.0, float(scarcity)))

    # Core target bid: try to outbid Cindy-like pressure but not match max.
    # If someone was very aggressive yesterday, bid slightly above the second-highest.
    if yesterday_high_pressure:
        # Aim: just above likely clearing level.
        target = max(second_prev_bid + 2.0, highest_prev_bid * 0.72 + 10.0)
    else:
        # Otherwise, bid around a mid fraction of salary, adjusted by scarcity.
        target = DAILY_SALARY * (0.45 + 0.25 * scarcity)

    # HP-based risk adjustment: if I'm low HP or already have many dry days, increase.
    if my_hp <= 2:
        target *= 1.35
    elif my_hp <= 4:
        target *= 1.15

    if my_no_water_days >= 2:
        target *= 1.25

    # Cap to budget and keep within sensible bounds.
    # Also avoid overbidding when budget is tight.
    max_affordable = my_budget
    # Soft cap at 1.0*salary unless budget forces otherwise.
    soft_cap = min(max_affordable, DAILY_SALARY * 1.05)
    bid = float(min(max_affordable, max(0.0, target)))
    bid = float(min(bid, soft_cap))

    # Ensure at least a minimal competitive bid if we have budget.
    min_competitive = min(max_affordable, DAILY_SALARY * (0.25 + 0.15 * scarcity))
    if bid < min_competitive and max_affordable > 0:
        bid = float(min(max_affordable, min_competitive))

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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    if not alive:
        return float(min(budget, DAILY_SALARY * 0.4))

    # Immediate reaction from yesterday's bids
    prev_bids = []
    prev_pressures = []
    for oid, o in alive:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            b = float(prev['bid'])
            prev_bids.append(b)
            # pressure proxy: if they ended with low hp, they likely lost water
            hp_after = prev.get('hp_after', None)
            if hp_after is not None:
                prev_pressures.append((b, int(hp_after)))

    if prev_bids:
        highest_prev_bid = max(prev_bids)
        lowest_prev_bid = min(prev_bids)
    else:
        highest_prev_bid = 0.0
        lowest_prev_bid = 0.0

    # Estimate how many water units likely exist; use to scale aggressiveness.
    # Note: indices are not used; only thresholds.
    # If supply is high, we can bid less because allocation is easier.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY + 1e-9)
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Base bid: keep enough budget for remaining days.
    # If we're low hp or have had no water, increase.
    urgency = 0.0
    if hp <= 2:
        urgency += 0.35
    elif hp <= 4:
        urgency += 0.2
    if no_water_days >= 2:
        urgency += 0.25
    if no_water_days >= 4:
        urgency += 0.25

    # Opponent behavior: if someone bid very high yesterday, we may need to match/just exceed.
    # But avoid overpaying when supply is lower/higher.
    match_factor = 0.0
    if highest_prev_bid > 0:
        # If highest bid was large relative to our daily salary, treat it as a strong signal.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            match_factor = 0.65
        elif highest_prev_bid >= DAILY_SALARY * 0.55:
            match_factor = 0.45
        else:
            match_factor = 0.25

    # Target bid computation
    # - When supply is high, reduce target.
    # - When urgency is high, increase target.
    # - If highest_prev_bid is meaningful, target slightly above it but dampened.
    damp = (1.0 - 0.45 * supply_ratio)
    target = DAILY_SALARY * (0.42 + 0.28 * urgency) * damp

    if highest_prev_bid > 0:
        # Try to beat the likely clearing price without going all-in.
        target = max(target, highest_prev_bid * (0.78 + 0.22 * match_factor) - 2.0)

    # Clamp to budget and keep within reasonable range
    # If budget is tiny, bid just enough to avoid immediate elimination.
    min_reasonable = DAILY_SALARY * (0.22 + 0.15 * urgency)
    bid = float(min(budget, max(min_reasonable, target)))

    # If we're in critical condition, push harder but still within budget.
    if hp <= 1 or no_water_days >= 5:
        bid = float(min(budget, max(bid, DAILY_SALARY * 0.9)))

    # Final safety clamp
    if bid < 0.0:
        bid = 0.0
    return bid
"""
