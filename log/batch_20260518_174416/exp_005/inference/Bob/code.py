# ============================================================
# Experiment: exp_005
# Agent: Bob
# Source: exp_005
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

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    # Alive opponents and their yesterday bids
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid', None)
            if bid is not None:
                alive_opps.append((opp_id, bid, prev))

    # Base affordability
    budget = float(my_status.get('budget', 0.0))
    hp = float(my_status.get('hp', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # If we have low hp or have been starving, escalate
    starving = (hp <= 2.0) or (no_water_days >= 2)

    # Determine opponent pressure from yesterday
    if alive_opps:
        prev_bids = [float(b) for _, b, _ in alive_opps]
        highest_prev_bid = max(prev_bids)
        second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev_bid
    else:
        highest_prev_bid = 0.0
        second_prev_bid = 0.0

    # Estimate how tight the market is: map supply to a 0..1 tightness score
    # (lower supply => higher tightness)
    supply_clamped = min(max(float(supply), float(MIN_SUPPLY)), float(MAX_SUPPLY))
    tightness = (float(MAX_SUPPLY) - supply_clamped) / float(MAX_SUPPLY - MIN_SUPPLY)

    # Strategy:
    # - If opponents signaled high urgency (high yesterday bids), bid to beat them.
    # - If not, bid moderately, scaling with tightness and our starvation.
    if highest_prev_bid >= 0.85 * DAILY_SALARY:
        # Very urgent opponents: try to outbid slightly.
        target = highest_prev_bid + 2.0
        if starving:
            target = max(target, 0.95 * DAILY_SALARY)
        else:
            # If I'm healthy, avoid reckless spending
            target = min(target, 0.75 * DAILY_SALARY)
    elif highest_prev_bid >= 0.6 * DAILY_SALARY:
        # Medium urgency: bid around their level but not full match unless starving
        target = max(highest_prev_bid, 0.55 * DAILY_SALARY)
        if starving:
            target = max(target, highest_prev_bid + 1.5)
        else:
            # slight undercut risk-managed
            target = min(target, highest_prev_bid + 0.5)
    else:
        # Low urgency: bid based on tightness and whether we are at risk
        # Convert tightness into a multiplier between ~0.45 and ~0.75
        base_mult = 0.45 + 0.30 * tightness
        target = base_mult * DAILY_SALARY
        if starving:
            target = max(target, 0.75 * DAILY_SALARY)

    # Ensure we never bid more than our budget
    bid = min(budget, float(target))

    # Practical caps: don't bid below a minimal useful level if possible
    # but keep it budget-safe.
    if bid < 1.0:
        bid = min(budget, 1.0)

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

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Identify alive opponents and use yesterday's bids for immediate pressure estimation.
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    # Baseline: conserve budget if not under immediate threat.
    # Escalate if we have no-water streak or low hp.
    if my_hp <= 2.0 or no_water_days >= 2:
        base = DAILY_SALARY * 0.85
    elif my_hp <= 4.0 or no_water_days == 1:
        base = DAILY_SALARY * 0.65
    else:
        base = DAILY_SALARY * 0.55

    # Use yesterday's bids from alive opponents to set a competitive target.
    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # If there was strong bidding pressure yesterday, slightly overtake it.
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If they were bidding near typical salary, we match/overbid.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # If we are healthy, bid a bit less than the leader but still competitive.
            if my_hp > 5.0 and no_water_days == 0:
                target = max(highest_prev_bid * 0.92, DAILY_SALARY * 0.65)
            else:
                target = max(highest_prev_bid * 1.02, DAILY_SALARY * 0.85)
        else:
            # Moderate bids: bid enough to beat the leader by a small margin.
            target = max(highest_prev_bid + 1.5, base)
    else:
        target = base

    # Supply-aware adjustment: when supply is tight, water is more scarce, so bid more.
    # Supply in [15,25] with WATER_REQ=9 means at most 2 units can be fully satisfied.
    scarcity_factor = 0.0
    if supply <= float(WATER_REQ + 6):
        scarcity_factor = 0.15
    elif supply <= float(WATER_REQ + 10):
        scarcity_factor = 0.07
    else:
        scarcity_factor = 0.0

    target = target * (1.0 + scarcity_factor)

    # Near the end of the episode, ensure survival by increasing bids.
    # Episode length is 10 days in meta-round context; use day to approximate.
    if day >= 8:
        target = max(target, DAILY_SALARY * 0.8)

    # Final cap by budget.
    bid = min(my_budget, target)

    # Ensure bid is non-negative.
    if bid < 0.0:
        bid = 0.0

    return bid
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

    # If no budget, bid 0.
    if my_status['budget'] <= 0:
        return 0.0

    # Alive opponents only.
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # Base target: aim to secure at least one water unit (enough for our requirement).
    # In this game, water allocation is driven by bids; we approximate a competitive bid.
    # Higher supply reduces urgency; lower supply increases urgency.
    supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_factor = max(0.0, min(1.0, supply_factor))

    # Pressure from yesterday: use previous_trace bid as a proxy for how aggressive they are.
    prev_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Determine aggression threshold.
    # Cindy's behavior suggests some agents can go very high; we avoid mirroring unless needed.
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        # If someone was bidding extremely high yesterday, we may need to defend our HP.
        extreme_pressure = highest_prev_bid >= DAILY_SALARY * 1.3
        moderate_pressure = highest_prev_bid >= DAILY_SALARY * 0.85
    else:
        highest_prev_bid = 0.0
        extreme_pressure = False
        moderate_pressure = False

    hp = float(my_status['hp'])
    no_water_days = int(my_status.get('no_water_days', 0))
    budget = float(my_status['budget'])

    # Urgency: if we've already had no-water days, increase bid.
    urgency = 0
    if no_water_days >= 2:
        urgency = 2
    elif no_water_days >= 1:
        urgency = 1

    # Compute a conservative bid ceiling to preserve budget for 10-day episode.
    # Keep average near ~0.55 salary unless urgency/pressure demands more.
    base_bid = DAILY_SALARY * (0.62 - 0.25 * supply_factor)  # lower supply -> higher base
    # Adjust with HP/urgency.
    if hp <= 2:
        base_bid *= 1.7
    elif hp <= 4:
        base_bid *= 1.35

    if urgency == 2:
        base_bid *= 1.25
    elif urgency == 1:
        base_bid *= 1.10

    # React to opponent pressure.
    if extreme_pressure:
        # Don't chase blindly; only overbid if our HP is at risk.
        if hp <= 3 or urgency >= 1:
            base_bid *= 1.15
        else:
            base_bid *= 0.95
    elif moderate_pressure:
        # Slightly increase to avoid being out-competed.
        if hp <= 4 or urgency >= 1:
            base_bid *= 1.10
        else:
            base_bid *= 1.00

    # Ensure bid not exceeding budget.
    # Also cap to avoid reckless spending: never bid more than 1.2*salary unless very low HP.
    hard_cap = DAILY_SALARY * 1.2
    if hp <= 2:
        hard_cap = DAILY_SALARY * 1.6

    bid = min(budget, min(hard_cap, base_bid))

    # If supply is very low, add a small bump to secure allocation.
    if supply < (MIN_SUPPLY + 1.0):
        bid = min(budget, bid + 8.0)

    # Final safety: bid at least 0.
    if bid < 0:
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

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        try:
            if opp.get('alive', False):
                alive_opps.append((opp_id, opp))
        except Exception:
            continue

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday bids from traces to infer pressure.
    prev_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    # Also check if any opponent was bidding extremely high (likely water-secure strategy).
    extreme_pressure = highest_prev_bid >= DAILY_SALARY * 1.45  # ~130+ given DAILY_SALARY=90

    # Estimate how many water units exist relative to our requirement.
    # This is only a heuristic for competition intensity.
    # supply is between 15 and 25; water units likely 1 or 2.
    units = int(supply / float(WATER_REQ))
    if units < 1:
        units = 1

    # Base bid policy: moderate unless our hp is low or opponent pressure is extreme.
    # When supply is higher (closer to 25), competition increases; bid slightly more.
    supply_frac = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_frac = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    if supply_frac < 0.0:
        supply_frac = 0.0
    if supply_frac > 1.0:
        supply_frac = 1.0

    # HP urgency factor
    if hp <= 2 or no_water_days >= 2:
        hp_factor = 0.95
    elif hp <= 4:
        hp_factor = 0.75
    else:
        hp_factor = 0.55

    # Opponent pressure factor
    if extreme_pressure:
        # Don't fully mirror, but raise to avoid being outbid for the last unit.
        pressure_factor = 0.78 if units == 1 else 0.68
    else:
        pressure_factor = 0.62 if units == 1 else 0.55

    # Supply factor: bid more when supply is higher (more likely others also bid).
    supply_factor = 0.50 + 0.25 * supply_frac

    target = DAILY_SALARY * hp_factor * pressure_factor * supply_factor

    # If yesterday's highest bid was already moderate, try to be slightly above it when we can afford.
    if highest_prev_bid > 0.0 and highest_prev_bid < DAILY_SALARY * 1.2:
        # Only chase if we have enough budget; otherwise stick to target.
        chase = highest_prev_bid + 2.0
        # Allow slight overtake when hp is not critical.
        if hp >= 3:
            target = max(target, chase * 0.95)
        else:
            target = max(target, chase)

    # Hard caps to preserve budget.
    # Never bid above what we can pay.
    bid = min(budget, target)

    # Ensure non-negative.
    if bid < 0.0:
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

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', True):
            alive_opponents.append(o)

    # Base safety: if we're already in trouble, bid hard.
    if hp <= 2 or no_water_days >= 2:
        return min(budget, DAILY_SALARY * 0.95)

    # React to yesterday's immediate pressure.
    yesterday_bids = []
    yesterday_hp_after = []
    for o in alive_opponents:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid', 0.0)))
                yesterday_hp_after.append(float(prev.get('hp_after', o.get('hp', 0.0))))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = 0.0
    if len(yesterday_bids) >= 2:
        sorted_bids = sorted(yesterday_bids, reverse=True)
        second_prev_bid = sorted_bids[1]

    # Supply-aware target: when supply is tight, we need to outbid more.
    # Convert supply to a tightness factor in [0,1].
    denom = (MAX_SUPPLY - MIN_SUPPLY)
    if denom <= 0:
        tightness = 0.5
    else:
        tightness = (MAX_SUPPLY - supply) / denom
        if tightness < 0.0:
            tightness = 0.0
        if tightness > 1.0:
            tightness = 1.0

    # If opponents were spending heavily yesterday, undercut instead of matching.
    # We aim to be competitive but cheaper than the highest bidder.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Undercut strategy: bid slightly above the second-highest (if available),
        # otherwise a fraction of the highest.
        if second_prev_bid > 0.0:
            target = second_prev_bid + 2.0 + 8.0 * tightness
        else:
            target = highest_prev_bid * (0.82 + 0.08 * tightness)
    else:
        # Lower pressure: bid around a fraction of salary, adjusted by tightness.
        target = DAILY_SALARY * (0.48 + 0.25 * tightness)

    # Ensure we don't bid beyond what our budget allows.
    # Also keep a floor to avoid losing to moderate bids when supply is tight.
    floor_bid = DAILY_SALARY * (0.35 + 0.25 * tightness)
    bid = max(floor_bid, target)

    if bid > budget:
        bid = budget

    # If budget is very low, still bid at least a small amount.
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

    # Identify alive opponents
    alive_opps = []
    for aid, o in opponents_status.items():
        if o.get('alive'):
            alive_opps.append((aid, o))

    # If no opponents are alive, conserve budget
    if not alive_opps:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.35))

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])

    # Read yesterday bids from previous_trace for immediate reaction
    prev_bids = []
    for aid, o in alive_opps:
        pt = o.get('previous_trace', {}) or {}
        b = pt.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate how many water units are likely needed to stay safe.
    # With water_requirement=9, each unit corresponds to one bid water share unit.
    # We bid in money; the game mechanics typically allocate water by bid share.
    # Strategy: aim to beat the top yesterday bidder only when supply is tighter.
    supply_tight = supply <= (MIN_SUPPLY + MAX_SUPPLY) / 2.0  # <=20

    # Base target bid determined by my hp and yesterday pressure
    if my_hp <= 2.5:
        # Critical: bid aggressively but cap by budget and a fraction of salary
        target = max(highest_prev_bid * 0.95, DAILY_SALARY * 0.9)
    else:
        if supply_tight:
            # Undercut the leader slightly to capture water without overpaying
            if highest_prev_bid > 0:
                target = highest_prev_bid * 0.92
            else:
                target = DAILY_SALARY * 0.65
        else:
            # Supply more abundant: bid moderate, still responsive to leader
            if highest_prev_bid > 0:
                target = max(highest_prev_bid * 0.80, DAILY_SALARY * 0.55)
            else:
                target = DAILY_SALARY * 0.55

    # Budget-aware cap: avoid exhausting early
    # Keep some buffer for later days
    buffer = DAILY_SALARY * 0.15
    max_affordable = max(0.0, my_budget - buffer)

    # Also avoid bidding beyond what seems like typical competitive range
    hard_cap = DAILY_SALARY * 1.2

    bid = min(target, max_affordable, hard_cap, my_budget)

    # Ensure non-negative
    if bid < 0.0:
        bid = 0.0

    # Small increment if we suspect leader is very high (to steal allocation)
    # Use yesterday max as proxy.
    if highest_prev_bid >= DAILY_SALARY * 1.6 and my_hp > 3.0:
        bid = min(my_budget, bid + 5.0)

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

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        try:
            if o.get('alive', False):
                alive_opps.append(o)
        except Exception:
            pass

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    top_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how many water units we can plausibly buy given supply.
    # Bids compete; we use supply to scale risk: higher supply -> can bid less.
    supply_scale = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    supply_scale = max(0.0, min(1.0, supply_scale))

    # Survival urgency: if we have gone several days without water or low HP, bid more.
    urgency = 0
    if hp <= 2.0:
        urgency = 3
    elif hp <= 4.0:
        urgency = 2
    elif no_water_days >= 2:
        urgency = 2
    elif no_water_days >= 1:
        urgency = 1

    # Base bid tracks opponent yesterday top bid but underbids to steal at lower cost.
    # If opponent was very aggressive (high top_bid), we respond with enough to avoid losing water.
    aggressive_threshold = DAILY_SALARY * 0.85

    if top_bid >= aggressive_threshold:
        if urgency >= 3:
            target = min(budget, DAILY_SALARY * 0.95)
        elif urgency == 2:
            target = min(budget, DAILY_SALARY * 0.75)
        else:
            # Underbid slightly to exploit potential overspending by others.
            target = min(budget, max(0.0, top_bid * 0.88))
    else:
        if urgency >= 3:
            target = min(budget, DAILY_SALARY * 0.9)
        elif urgency == 2:
            target = min(budget, DAILY_SALARY * 0.65)
        else:
            # When not under immediate threat, bid moderately; scale down when supply is higher.
            mid = max(0.0, DAILY_SALARY * (0.5 + 0.15 * (1.0 - supply_scale)))
            # Also ensure we are not wildly above the market.
            target = min(budget, max(0.0, min(mid, top_bid * 0.9 + 5.0 if top_bid > 0 else mid)))

    # If budget is tiny, just bid what we can.
    if budget <= 1.0:
        return max(0.0, budget)

    # Final clamp to reasonable range.
    target = max(0.0, min(budget, float(target)))
    return target
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

    supply = day_context['supply']
    day = day_context['day']

    # Alive opponents
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append(o)

    if not alive:
        # If no one else, take minimal to survive
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Read yesterday bids from traces (only immediate reaction)
    yesterday_bids = []
    yesterday_info = []  # (opp_id, bid, hp_after, status)
    for oid, o in opponents_status.items():
        if not o.get('alive', False):
            continue
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            b = prev.get('bid')
            yesterday_bids.append(b)
            yesterday_info.append((oid, b, prev.get('hp_after', None), prev.get('status', None)))

    # Estimate how competitive the pool is: use top yesterday bid
    top_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Determine how many water units are likely available this day
    # (Used only to scale aggression; indices are not required here.)
    # With supply in [15,25], max units about 2 (since 2*9=18) sometimes 3 if supply>=27 (won't happen).
    # We'll treat supply >=18 as 'high enough' for 2 units.
    high_supply = supply >= 18.0

    my_hp = my_status.get('hp', 0)
    my_budget = my_status.get('budget', 0)

    # Identify Cindy-like behavior: if any opponent had very high yesterday bid and is alive now, expect repeat.
    # Cindy is known to have survived and spent; we don't rely on name, just on high bid + alive.
    # Find strongest spender yesterday among alive.
    strongest = None
    strongest_bid = -1.0
    for oid, b, hp_after, status in yesterday_info:
        if b is not None and b > strongest_bid:
            strongest_bid = float(b)
            strongest = oid

    # Base target bid
    # - If Cindy-like strong pressure (top_bid large), we bid slightly above her typical pressure.
    # - Otherwise bid enough to secure water without burning budget.
    if strongest_bid >= DAILY_SALARY * 1.0:  # >=90
        # Aggressive response to avoid being starved
        target = top_bid + (8.0 if high_supply else 4.0)
    elif strongest_bid >= DAILY_SALARY * 0.6:  # >=54
        target = max(top_bid * 0.95, DAILY_SALARY * (0.55 if high_supply else 0.65))
    else:
        target = DAILY_SALARY * (0.5 if high_supply else 0.6)

    # Adjust for my HP/budget
    if my_hp <= 2:
        # Need water urgently
        target = max(target, DAILY_SALARY * 0.85)
    elif my_hp <= 4:
        target = max(target, DAILY_SALARY * 0.65)

    # If my budget is low, cap spending to avoid going negative
    if my_budget <= 0:
        return 0

    bid = min(my_budget, target)

    # Ensure bid is non-negative and not absurdly high
    if bid < 0:
        bid = 0

    # If supply is low, competition for scarce water is higher; add small bump
    if supply < 18.0:
        bid = min(my_budget, bid + 3.0)

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

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from immediate previous_trace
    prev_bids = []
    for oid, o in alive:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Base target: match the observed competitive bids (~109) but avoid going too high.
    # Also adjust for current supply: higher supply reduces urgency to overbid.
    supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_norm = max(0.0, min(1.0, supply_norm))

    # Urgency from hp/no_water_days
    urgency = 0.0
    if hp <= 2.0:
        urgency += 0.35
    if no_water_days >= 2:
        urgency += 0.25
    if hp <= 1.0:
        urgency += 0.25

    # If someone already bid very high yesterday, we slightly shadow them.
    # Otherwise, we bid around the mid-high equilibrium.
    target = 108.5
    if highest_prev_bid >= DAILY_SALARY * 1.15:  # ~103.5
        target = min(DAILY_SALARY * 1.25, highest_prev_bid * 0.95)
    elif highest_prev_bid >= DAILY_SALARY * 0.95:  # ~85.5
        target = max(target, highest_prev_bid * 0.9)

    # Reduce bid when supply is high and urgency is low.
    target *= (0.92 + 0.18 * (1.0 - supply_norm))
    target *= (1.0 + urgency)

    # Convert target into a safe bid cap based on budget.
    # Keep some budget for later days.
    budget_cap = budget * (0.55 if hp > 3.0 else 0.75)

    bid = min(budget_cap, target)

    # Ensure non-negative and do not exceed a reasonable fraction of daily salary.
    bid = max(0.0, min(bid, DAILY_SALARY * 1.3))

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

    my_hp = int(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_ids = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_ids.append(oid)

    if not alive_ids:
        return float(min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from immediate previous_trace
    prev_bids = []
    prev_by_id = {}
    for oid in alive_ids:
        tr = opponents_status[oid].get('previous_trace', {})
        bid = tr.get('bid', None)
        if bid is not None:
            try:
                bid_val = float(bid)
            except Exception:
                continue
            prev_bids.append(bid_val)
            prev_by_id[oid] = bid_val

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Identify likely aggressor: highest yesterday bid among alive
    aggressor_bid = highest_prev_bid
    aggressor_id = None
    if prev_bids:
        for oid in alive_ids:
            if oid in prev_by_id and prev_by_id[oid] == aggressor_bid:
                aggressor_id = oid
                break

    # Supply pressure: if supply is near max, we can afford to bid less; if near min, bidding is more valuable.
    # Convert to a 0..1 pressure factor.
    if MAX_SUPPLY == MIN_SUPPLY:
        pressure = 0.5
    else:
        pressure = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
        if pressure < 0.0:
            pressure = 0.0
        if pressure > 1.0:
            pressure = 1.0

    # Our need: if we're close to death, we must secure water.
    urgent = (my_hp <= 2) or (my_no_water_days >= 2)

    # Baseline bid depends on HP; also counter Cindy-like behavior by checking if highest_prev_bid was high.
    high_threat = aggressor_bid >= DAILY_SALARY * 0.75

    # Choose target bid.
    if urgent:
        # Spend to survive; outbid likely aggressor if they were strong.
        if high_threat:
            target = aggressor_bid + 5.0
        else:
            target = DAILY_SALARY * 0.85
    else:
        if high_threat:
            # Cindy-like: don't blindly overpay; bid just enough to avoid losing the water allocation.
            # If our HP is moderate, we can slightly undercut.
            if my_hp >= 6:
                target = min(aggressor_bid + 2.0, DAILY_SALARY * (0.55 + 0.2 * pressure))
            else:
                target = min(aggressor_bid + 3.5, DAILY_SALARY * (0.65 + 0.2 * pressure))
        else:
            # No strong aggressor: bid conservatively, scaled by pressure.
            target = DAILY_SALARY * (0.45 + 0.25 * pressure)

    # Ensure we never bid more than budget.
    if my_budget <= 0.0:
        return 0.0

    bid = float(min(my_budget, max(0.0, target)))

    # If supply is low and we are not urgent, still ensure some participation.
    if supply <= float(WATER_REQ) + 6.0 and bid < DAILY_SALARY * 0.35 and my_hp >= 4:
        bid = float(min(my_budget, DAILY_SALARY * 0.4))

    return bid
"""
