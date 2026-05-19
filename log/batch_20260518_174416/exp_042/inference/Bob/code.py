# ============================================================
# Experiment: exp_042
# Agent: Bob
# Source: exp_042
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

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))

    # Collect immediate opponent reaction from yesterday's trace
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    # Default moderate bid: aim to win when supply is tight, but avoid wasting budget
    # Use supply ratio to scale aggressiveness.
    supply_ratio = 0.0
    if WATER_REQ > 0:
        supply_ratio = supply / float(WATER_REQ)

    # Baseline: bid around 0.45 of daily salary, boosted when supply is low relative to requirement.
    # supply_ratio < 2 means likely scarcity; raise bid.
    if supply_ratio <= 1.8:
        baseline = DAILY_SALARY * 0.65
    elif supply_ratio <= 2.4:
        baseline = DAILY_SALARY * 0.50
    else:
        baseline = DAILY_SALARY * 0.40

    # If yesterday we observed any high bids, respond more aggressively.
    observed_bids = []
    observed_highest = None
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                b_val = float(b)
                observed_bids.append(b_val)
            except Exception:
                pass

    if observed_bids:
        observed_highest = max(observed_bids)

    # Health pressure: if we're low hp, we must secure water.
    if hp <= 2:
        health_factor = 0.9
    elif hp <= 3:
        health_factor = 0.75
    else:
        health_factor = 0.6

    # Opponent pressure: if any opponent bid near their daily salary, likely contested.
    # We don't know their salary exactly, but we can compare to our DAILY_SALARY as a proxy.
    if observed_highest is not None:
        if observed_highest >= DAILY_SALARY * 0.85:
            bid = max(baseline, observed_highest + 1.0)
            bid *= 1.05
        elif observed_highest >= DAILY_SALARY * 0.65:
            bid = max(baseline, observed_highest + 0.5)
        else:
            bid = baseline
    else:
        bid = baseline

    bid *= health_factor

    # Budget cap and floor to avoid bidding zero when we need water.
    if budget <= 0:
        return 0.0

    # Ensure we never exceed budget.
    if bid > budget:
        bid = budget

    # If we still have enough budget, avoid extremely tiny bids when supply is scarce.
    # (No-water days not used directly since we only have it in my_status but not required.)
    if supply_ratio <= 1.8 and bid < DAILY_SALARY * 0.25:
        bid = min(budget, DAILY_SALARY * 0.35)

    # Final clamp
    if bid < 0.0:
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    # Alive opponents
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    # Fallback
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    supply = float(day_context['supply'])
    day = day_context['day']

    # Yesterday bids from previous_trace (immediate reaction only)
    prev_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict) and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # Estimate pressure level from yesterday
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev_bid
    else:
        highest_prev_bid = DAILY_SALARY * 0.6
        second_prev_bid = highest_prev_bid

    my_hp = float(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0))

    # Supply pressure: with low supply, competition is tighter; bid higher.
    # supply is between 15 and 25.
    supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    # When supply is low, supply_factor ~0 => we bid higher.
    scarcity_multiplier = 1.25 - 0.25 * supply_factor

    # Decide bid target based on our hp and yesterday's aggression.
    # If our hp is low, we must secure water; if high, we can slightly undercut.
    if my_hp <= 2.0:
        target = max(DAILY_SALARY * 0.85, second_prev_bid * 0.95)
    elif my_hp <= 4.0:
        target = max(DAILY_SALARY * 0.65, second_prev_bid * 0.8)
    else:
        # Underbid slightly relative to highest aggressors to save budget while still contesting.
        target = min(highest_prev_bid * 0.95, max(DAILY_SALARY * 0.55, second_prev_bid * 0.75))

    target *= scarcity_multiplier

    # Convert to an absolute bid cap by budget.
    # Also avoid overspending: keep within a fraction of budget depending on hp.
    if my_hp <= 2.0:
        budget_fraction = 0.95
    elif my_hp <= 4.0:
        budget_fraction = 0.8
    else:
        budget_fraction = 0.65

    bid = float(min(my_budget * budget_fraction, target))

    # Ensure non-negative and at least a small amount if budget allows.
    if bid < 0.0:
        bid = 0.0
    if bid == 0.0 and my_budget > 0.0:
        bid = float(min(my_budget, DAILY_SALARY * 0.2))

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

    # Alive opponents and yesterday bid signals
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # Default bid fraction based on my condition
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    if budget <= 0:
        return 0.0

    # Estimate pressure from yesterday: how aggressive others were
    yesterday_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid', 0.0)))
            except Exception:
                pass

    # If Cindy was alive with very high average bid, assume she continues to outbid others.
    # We react by bidding around her typical range but not maxing out.
    avg_prev_bid = None
    if yesterday_bids:
        avg_prev_bid = sum(yesterday_bids) / float(len(yesterday_bids))

    # Supply-based urgency: lower supply means fewer full water allocations are possible.
    # If supply is near MIN_SUPPLY, competition increases.
    supply_ratio = (supply - float(MIN_SUPPLY)) / max(1e-9, (float(MAX_SUPPLY) - float(MIN_SUPPLY)))
    low_supply = supply_ratio < 0.35

    # My urgency: if I have gone too many days without water or hp is low, increase bid.
    urgent = (hp <= 2.5) or (no_water_days >= 2)

    # Baseline target bid
    if avg_prev_bid is None:
        target = DAILY_SALARY * (0.55 if not urgent else 0.85)
    else:
        # If others were bidding high yesterday, raise bid slightly above their average.
        # Otherwise, bid enough to secure water without overpaying.
        if avg_prev_bid >= DAILY_SALARY * 0.8:
            target = DAILY_SALARY * (0.75 if not urgent else 0.95)
        else:
            target = max(DAILY_SALARY * (0.45 if not urgent else 0.75), avg_prev_bid + (5.0 if low_supply else 2.0))

    # Convert target to a conservative cap based on remaining budget.
    # Also ensure we don't bid more than we can afford.
    max_affordable = budget

    # If supply is high, we can bid less and still likely get water.
    if supply_ratio > 0.7 and not urgent:
        target *= 0.85

    # If supply is very low, bid more aggressively.
    if low_supply:
        target *= 1.08

    bid = min(max_affordable, target)

    # Final safety clamp
    if bid < 0.0:
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    hp = int(my_status['hp'])
    budget = float(my_status['budget'])

    alive_opps = [o for o in opponents_status.values() if o.get('alive')]
    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from traces (immediate reaction only)
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Estimate how aggressive others were
    highest_prev = max(prev_bids) if prev_bids else 0.0
    median_prev = 0.0
    if prev_bids:
        s = sorted(prev_bids)
        median_prev = s[len(s) // 2]

    # Supply pressure: lower supply means higher chance we must secure water
    # Use a conservative mapping to target a bid band.
    supply_ratio = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)  # 0..1
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Base bid: if low supply, bid more; if high supply, bid less.
    # Also react to our hp.
    if hp <= 2:
        base = DAILY_SALARY * 0.95
    elif hp <= 4:
        base = DAILY_SALARY * 0.75
    else:
        base = DAILY_SALARY * (0.55 + 0.15 * (1.0 - supply_ratio))

    # Opponent reaction: if they were bidding high yesterday, we need a slight overtake.
    # Target just above median when highest was very high; otherwise near median.
    if highest_prev >= DAILY_SALARY * 1.25:
        target = median_prev + 5.0
    elif highest_prev >= DAILY_SALARY * 0.9:
        target = median_prev + 2.0
    else:
        target = median_prev * 0.9 + 1.0

    bid = max(base, target)

    # If supply is low, add a small premium to reduce risk of losing the allocation.
    if supply <= float(MIN_SUPPLY) + 2.0:
        bid += 8.0

    # Never exceed budget
    bid = min(bid, budget)

    # Ensure non-negative
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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Extract yesterday bids from immediate previous_trace only
    prev_bids = []
    for oid, o in opponents_status.items():
        if not o.get('alive', False):
            continue
        prev = o.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                prev_bids.append(float(bid))
            except Exception:
                pass

    # Identify who was most aggressive yesterday
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Baseline: since my hp is high (9), avoid overpaying unless others were extreme.
    # Use supply pressure: higher supply reduces need to outbid.
    supply_factor = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    supply_factor = max(0.0, min(1.0, supply_factor))

    # If Cindy/Alex were very aggressive yesterday (high bid), I match moderately to secure water.
    # If their max bid was enormous, cap spending to preserve budget.
    if highest_prev_bid >= 0.85 * 953.5:  # Cindy-like max pressure
        target = DAILY_SALARY * (0.55 + 0.25 * supply_factor)
    elif highest_prev_bid >= 0.85 * 166.0:  # Alex-like pressure
        target = DAILY_SALARY * (0.50 + 0.20 * supply_factor)
    else:
        target = DAILY_SALARY * (0.45 + 0.15 * supply_factor)

    # If I'm already missing water, escalate more.
    if no_water_days >= 1:
        target *= 1.25
    if hp <= 2:
        target *= 1.8

    # Ensure we don't bid above what we can afford.
    bid = min(budget, target)

    # Keep bids discrete-ish and avoid too-low bids when supply is tight.
    min_bid = 0.15 * DAILY_SALARY
    if supply <= float(WATER_REQ) + 2.0:
        min_bid = 0.25 * DAILY_SALARY
    bid = max(min_bid, bid)

    # Final cap
    bid = min(bid, budget)
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

    my_hp = int(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for aid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace for immediate reaction
    prev_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        if isinstance(prev, dict) and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Use yesterday's max bid as a proxy for how aggressively they compete
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Scarcity pressure: lower supply means we must secure water
    # Normalize supply into [0,1] where 1 is scarce
    denom = float(MAX_SUPPLY - MIN_SUPPLY) if (MAX_SUPPLY - MIN_SUPPLY) != 0 else 1.0
    scarcity = (float(MAX_SUPPLY) - supply) / denom
    scarcity = 0.0 if scarcity < 0.0 else (1.0 if scarcity > 1.0 else scarcity)

    # If we are close to death (no water streak), bid more aggressively
    urgent = 0
    if my_hp <= 2:
        urgent = 1
    if my_no_water_days >= 2:
        urgent = 1

    # Base bid target: try to be competitive but avoid overpaying
    # If opponents previously bid very high, we slightly undercut/meet that pressure.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        target = highest_prev_bid * (0.92 if not urgent else 0.98)
    else:
        # If they weren't desperate yesterday, bid around mid-level adjusted by scarcity
        mid = DAILY_SALARY * (0.45 + 0.35 * scarcity)
        target = max(mid, highest_prev_bid * 0.6)
        if urgent:
            target = max(target, DAILY_SALARY * 0.75)

    # Convert to feasible bid: cannot exceed budget
    bid = min(my_budget, target)

    # If supply is extremely scarce, ensure we don't bid too low
    if scarcity >= 0.75 and my_budget > 0:
        floor_bid = DAILY_SALARY * (0.55 if not urgent else 0.85)
        bid = max(bid, min(my_budget, floor_bid))

    # If we have plenty of budget and are not urgent, avoid wasting money
    if not urgent and my_budget > DAILY_SALARY * 1.2:
        bid = min(bid, DAILY_SALARY * (0.6 + 0.25 * scarcity))

    # Ensure non-negative
    if bid < 0.0:
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # If we're already out of budget, bid 0.
    if my_status['budget'] <= 0:
        return 0.0

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    # Gather yesterday bids from alive opponents only.
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid', None)
            if bid is not None:
                alive_opps.append((opp_id, float(bid), prev))

    # Baseline target bid: try to be competitive but not reckless.
    # Use supply to infer competition intensity: higher supply reduces need to overbid.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Estimate how many water units exist.
    # Use int() for safety.
    units = int(supply / float(WATER_REQ)) if WATER_REQ > 0 else 0
    # Expected winners count roughly proportional to units.
    # If units are small, competition is harsher.
    harshness = 1.0
    if units >= 2:
        harshness = 0.75
    elif units >= 1:
        harshness = 1.0
    else:
        harshness = 1.25

    # React to yesterday's highest surviving pressure.
    if alive_opps:
        yesterday_bids = [b for (_, b, _) in alive_opps]
        highest_prev_bid = max(yesterday_bids)
        lowest_prev_bid = min(yesterday_bids)

        # If someone was bidding near/above ~0.85 salary, they likely secured survival.
        # Match just enough to avoid losing.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # If our hp is good, we can afford to bid to ensure survival.
            if hp > 3:
                target = DAILY_SALARY * (0.28 + 0.2 * (1.0 - supply_ratio))
            else:
                target = DAILY_SALARY * (0.85 + 0.1 * (1.0 - supply_ratio))
        else:
            # Otherwise, bid slightly above the median-ish pressure.
            # Use lowest+some fraction of range to avoid overbidding.
            target = lowest_prev_bid + 0.35 * (highest_prev_bid - lowest_prev_bid)
            # Ensure a minimum competitive level.
            target = max(target, DAILY_SALARY * (0.45 + 0.15 * (1.0 - supply_ratio)))

        target *= harshness
    else:
        # No alive opponent trace info; use conservative default.
        target = DAILY_SALARY * (0.5 + 0.15 * (1.0 - supply_ratio))
        target *= harshness

    # Budget preservation: if we've had many no-water days or low hp, increase bid; else keep moderate.
    no_water_days = float(my_status.get('no_water_days', 0))
    if hp <= 2.0 or no_water_days >= 2.0:
        target *= 1.15
    elif hp >= 7.0 and no_water_days <= 0.5:
        target *= 0.9

    # Final cap: never exceed budget.
    # Also avoid extreme bids above salary unless necessary.
    max_reasonable = min(budget, DAILY_SALARY * (1.2 if (hp <= 2.0 or no_water_days >= 2.0) else 0.95))
    bid = min(float(budget), float(target), float(max_reasonable))

    # If bid becomes tiny, still bid something if we need water soon.
    if bid < 1e-6:
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
        return min(my_budget, DAILY_SALARY * 0.4)

    # Read yesterday bids from previous_trace only (immediate reaction)
    yesterday_bids = []
    for opp_id, opp in alive_opps:
        prev = opp.get('previous_trace', None) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Estimate how many water units we can buy if we win allocation for our requirement.
    # Strategy: bid to be competitive, not necessarily maximum.
    # Supply is between 15 and 25, so total water units are about 1-2.
    # We assume each unit corresponds to one WATER_REQ consumption.
    supply_units = int(supply / float(WATER_REQ))
    if supply_units < 1:
        supply_units = 1

    # Pressure signal: if Cindy bid extremely high yesterday, she likely continues.
    cindy_bid = None
    for opp_id, opp in alive_opps:
        if str(opp_id) == 'Cindy':
            prev = opp.get('previous_trace', None) or {}
            if prev.get('bid', None) is not None:
                try:
                    cindy_bid = float(prev['bid'])
                except Exception:
                    cindy_bid = None

    # Base bid level depends on our HP.
    if my_hp <= 2 or my_no_water_days >= 2:
        base = DAILY_SALARY * 0.92
    elif my_hp <= 4:
        base = DAILY_SALARY * 0.70
    else:
        base = DAILY_SALARY * 0.58

    # If Cindy was very aggressive yesterday, raise to avoid being outcompeted.
    if cindy_bid is not None:
        if cindy_bid >= DAILY_SALARY * 1.35:
            base = max(base, DAILY_SALARY * 0.78)
        elif cindy_bid >= DAILY_SALARY * 1.05:
            base = max(base, DAILY_SALARY * 0.65)

    # Also react to the maximum yesterday bid among survivors.
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        # If someone paid near the top, we should ensure we don't lose all units.
        if highest_prev >= DAILY_SALARY * 1.65:
            base = max(base, DAILY_SALARY * 0.80)
        elif highest_prev >= DAILY_SALARY * 1.25:
            base = max(base, DAILY_SALARY * 0.68)

    # Convert base into a budget-feasible bid and add slight day-based variation.
    # Keep within reasonable bounds to avoid running out like the low-survivor agents.
    day_tweak = 1.0 + (int(day) % 3) * 0.03
    bid = base * day_tweak

    # If we can’t afford base, spend what we can but avoid going negative.
    if my_budget <= 0:
        return 0.0

    # Cap bid by budget and also by a soft upper bound linked to supply units.
    # With supply_units=1, being slightly less aggressive can still secure survival.
    soft_cap = DAILY_SALARY * (1.05 if supply_units >= 2 else 0.95)
    bid = min(bid, soft_cap)
    bid = min(bid, my_budget)

    # Ensure non-trivial bid if we’re not in emergency.
    if bid < 1.0 and (my_hp > 2):
        bid = min(my_budget, DAILY_SALARY * 0.45)

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

    supply = day_context['supply']
    day = day_context['day']

    # Determine alive opponents and their yesterday bids
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            yesterday_bids.append(float(b))

    # If someone was pressuring heavily yesterday, avoid overpaying; target just enough.
    pressure = 0.0
    if yesterday_bids:
        pressure = max(yesterday_bids)

    # Budget/HP based risk control
    hp = my_status.get('hp', 0)
    budget = my_status.get('budget', 0)
    no_water_days = my_status.get('no_water_days', 0)

    # Estimate how many full allocations are possible; used only to scale bids.
    # Convert supply to an integer count proxy.
    supply_int = int(round(supply))
    possible_units = max(1, supply_int // int(WATER_REQ))

    # Base bid: moderate, slightly above David-like behavior (~31.7) but far below Cindy/Eric spikes.
    # Scale with our urgency.
    urgency = 0
    if hp <= 2:
        urgency = 3
    elif hp <= 4:
        urgency = 2
    elif no_water_days >= 2:
        urgency = 1

    # If the max previous bid was extremely high, we assume others are wasting budget.
    # Keep our bid below that to avoid bidding war.
    if pressure >= 150:
        base = 38.0
    elif pressure >= 80:
        base = 45.0
    else:
        base = 34.0

    # Adjust for supply: with more supply, we can bid less.
    # supply_int in [15,25]
    if supply_int >= 22:
        base *= 0.9
    elif supply_int <= 17:
        base *= 1.05

    # Apply urgency
    target = base + urgency * 12.0

    # Hard cap by budget and a fraction of daily salary to prevent Alex-like depletion.
    cap = DAILY_SALARY * 0.65
    bid = min(budget, cap, target)

    # Ensure bid is positive but not excessive.
    if bid < 1.0:
        bid = min(budget, DAILY_SALARY * 0.15)

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

    # Identify alive opponents and extract yesterday bids
    alive_opps = []
    yesterday_bids = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)
            prev = o.get('previous_trace', {}) or {}
            bid = prev.get('bid', None)
            if bid is not None:
                yesterday_bids.append(float(bid))

    # If no opponents are alive, conserve budget
    if not alive_opps:
        return float(min(my_status.get('budget', 0.0), DAILY_SALARY * 0.4))

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Pressure estimate from yesterday
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid

    # Supply tightness: fewer units available implies we must secure water
    # supply is in [15,25]; water units roughly supply/WATER_REQ
    units = supply / float(WATER_REQ)
    tightness = 1.0
    if units >= 2.5:
        tightness = 0.6
    elif units >= 2.0:
        tightness = 0.75
    elif units >= 1.5:
        tightness = 0.95
    else:
        tightness = 1.15

    # Risk factor: if we have been without water, bid more
    risk = 1.0
    if no_water_days >= 2:
        risk = 1.25
    if my_hp <= 2:
        risk = 1.35
    elif my_hp <= 4:
        risk = 1.15

    # Strategy: bid slightly under the highest yesterday bid to avoid overpaying,
    # but increase toward it when we are at risk.
    target = highest_prev_bid * 0.92

    # If highest was very low, increase to at least a baseline to not get outbid by mid bidders
    baseline = DAILY_SALARY * 0.55
    if highest_prev_bid < baseline:
        target = baseline

    # If we are extremely at risk, try to match the top pressure
    if my_hp <= 2 or no_water_days >= 2:
        target = max(target, highest_prev_bid * 0.98)

    # Tightness and risk scaling
    target = target * tightness * risk

    # Add a small increment if we were likely to lose yesterday (infer from hp/no_water_days)
    # without using long history.
    if my_hp <= 3 and no_water_days >= 1:
        target = target + 3.0

    # Hard cap: never exceed budget
    if my_budget <= 0.0:
        return 0.0

    # Also keep within reasonable fraction of daily salary to avoid bankruptcy
    max_reasonable = DAILY_SALARY * 0.95
    bid = min(my_budget, max_reasonable, target)

    # Ensure non-negative and return float
    if bid < 0.0:
        bid = 0.0
    return float(bid)
"""
