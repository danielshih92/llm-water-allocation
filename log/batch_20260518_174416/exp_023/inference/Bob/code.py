# ============================================================
# Experiment: exp_023
# Agent: Bob
# Source: exp_023
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

    alive_opponents = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    # If no opponents, bid conservatively.
    if not alive_opponents:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read opponents' yesterday bids (immediate reaction only).
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate how many full requirements the current supply could satisfy.
    # (Used only for sizing our bid, not for indexing.)
    # If supply is low, we must be more aggressive.
    supply_ratio = supply / float(WATER_REQ)

    # Determine opponent aggressiveness from yesterday.
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        avg_prev_bid = sum(prev_bids) / float(len(prev_bids))
    else:
        highest_prev_bid = 0.0
        avg_prev_bid = 0.0

    # Base target bid.
    # If opponents were aggressive yesterday, we increase to contest.
    # Otherwise bid slightly above average to improve win probability.
    low_supply = supply < float(MIN_SUPPLY + 1)

    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # They likely needed water urgently.
        if my_status.get('hp', 0) > 3 and my_status.get('no_water_days', 0) <= 0:
            target = DAILY_SALARY * 0.35
        else:
            target = DAILY_SALARY * 0.6
    elif avg_prev_bid > 0:
        target = max(avg_prev_bid + 1.5, DAILY_SALARY * 0.45)
    else:
        target = DAILY_SALARY * 0.5

    # Adjust for supply pressure.
    if low_supply:
        target *= 1.15
    else:
        # If supply is healthier, conserve budget.
        target *= 0.95

    # If we are already in danger, bid more.
    if my_status.get('hp', 0) <= 2 or my_status.get('no_water_days', 0) >= 2:
        target = max(target, DAILY_SALARY * 0.75)

    # Final cap by budget.
    budget = float(my_status.get('budget', 0.0))
    bid = float(min(budget, target))

    # Ensure non-negative.
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

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    # Basic alive set
    alive_opps = []
    for k, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((k, o))

    if not alive_opps:
        # No competition: bid low but not zero
        return max(0.0, min(float(my_status.get('budget', 0.0)), DAILY_SALARY * 0.4))

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))

    # Read yesterday bids from previous_trace only
    yesterday_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', None)
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    yesterday_bids.append(float(b))
                except Exception:
                    pass

    # If we have no trace bids, use a conservative baseline
    if not yesterday_bids:
        base = DAILY_SALARY * 0.45
        if my_hp <= 2:
            base = DAILY_SALARY * 0.85
        return max(0.0, min(my_budget, base))

    highest_prev_bid = max(yesterday_bids)

    # Supply pressure heuristic: tighter supply -> slightly higher bid
    # Use integer indices safely; here we just map supply to a multiplier.
    # supply in [15,25], WATER_REQ=9 => about 1 or 2 units possible.
    units_possible = int(supply / float(WATER_REQ))  # e.g., 15/9=1.66 -> 1
    if units_possible <= 1:
        supply_mult = 1.10
    else:
        supply_mult = 0.95

    # If someone previously bid extremely high, they likely tried to secure water aggressively.
    # Counter with a moderate bid to avoid burning budget.
    if highest_prev_bid >= DAILY_SALARY * 1.10:
        # Cindy bid big and survived; don't mirror fully.
        if my_hp <= 2:
            bid = DAILY_SALARY * 0.75
        else:
            bid = DAILY_SALARY * 0.55
    elif highest_prev_bid >= DAILY_SALARY * 0.75:
        # Medium pressure
        if my_hp <= 2:
            bid = DAILY_SALARY * 0.65
        else:
            bid = DAILY_SALARY * 0.48
    else:
        # Low pressure: keep budget
        if my_hp <= 2:
            bid = DAILY_SALARY * 0.80
        else:
            bid = DAILY_SALARY * 0.40

    bid *= supply_mult

    # Ensure we never bid more than we can afford
    bid = max(0.0, min(my_budget, bid))

    # If budget is very low, still bid something small to avoid starvation
    if bid <= 0.0 and my_budget > 0.0:
        bid = min(my_budget, DAILY_SALARY * 0.1)

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
    day = day_context.get('day')

    # Identify alive opponents
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    # If no one is alive, conserve budget
    if not alive:
        return max(0.0, min(float(my_status.get('budget', 0.0)), DAILY_SALARY * 0.4))

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))

    # Read yesterday bids from previous_trace for immediate pressure
    prev_bids = []
    prev_by_id = {}
    for oid, o in alive:
        tr = o.get('previous_trace', {}) or {}
        bid = tr.get('bid', None)
        if bid is not None:
            try:
                b = float(bid)
                prev_bids.append(b)
                prev_by_id[oid] = b
            except Exception:
                pass

    # Pressure estimate
    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    # If we are in danger, prioritize winning water with a strong but not maximal bid.
    # Use supply to adjust aggressiveness: when supply is high, winning is cheaper.
    # supply in [15,25], water_needed is 1 unit of WATER_REQ.
    # Map supply to a confidence factor: higher supply => lower bid.
    # Ensure indices not used; only scalar math.
    supply_norm = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_norm = max(0.0, min(1.0, supply_norm))

    # Base target bid derived from yesterday's pressure.
    # Survivors were bidding around 105-130; we undercut unless our hp is very low.
    # If highest_prev is very high, we avoid overpaying unless critical.
    critical = (my_hp <= 2.0)
    moderate = (my_hp <= 4.0 and my_hp > 2.0)

    # Undercut factor: aim below highest_prev by 5-15% depending on our hp.
    if critical:
        target = max(DAILY_SALARY * 0.65, highest_prev * 0.92)
    elif moderate:
        target = max(DAILY_SALARY * 0.55, highest_prev * 0.85)
    else:
        # Not critical: bid near but below average pressure
        if avg_prev > 0:
            target = max(DAILY_SALARY * 0.45, avg_prev * 0.82)
        else:
            target = DAILY_SALARY * (0.5 + 0.1 * (1.0 - supply_norm))

    # Supply adjustment: when supply is high, reduce bid; when low, increase slightly.
    # Low supply increases competition for water.
    target *= (1.0 + 0.10 * (1.0 - supply_norm))

    # Cap target to a reasonable fraction of budget
    max_affordable = my_budget
    # Keep some budget buffer for later days
    buffer_frac = 0.15 if critical else (0.25 if moderate else 0.35)
    upper = max_affordable * (1.0 - buffer_frac)
    if upper < 0:
        upper = 0.0

    bid = min(target, upper)

    # Ensure non-negative and not exceeding budget
    bid = max(0.0, min(bid, my_budget))

    # If our hp is very low, don't go too low even if budget is small
    if critical and bid < my_budget * 0.6:
        bid = min(my_budget, max(bid, my_budget * 0.6))

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

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids and correlate to survival pressure.
    # We only use previous_trace (yesterday) for immediate reaction.
    prev_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate how many full water units supply can support.
    # If supply is tight, we must outbid the strongest remaining bidder.
    # Use int() to keep indices safe (though we don't index arrays).
    tightness = 0
    if supply <= (MIN_SUPPLY + WATER_REQ):
        tightness = 1
    if supply <= MIN_SUPPLY:
        tightness = 2

    # Identify likely main rival using yesterday max bid.
    yesterday_max_bid = max(prev_bids) if prev_bids else 0.0
    yesterday_avg_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    # Base bid depends on our HP and tightness.
    # If we are low HP or have accumulated no-water days, bid more aggressively.
    if hp <= 2 or no_water_days >= 2:
        base = DAILY_SALARY * (0.85 if tightness == 0 else 1.0)
    elif hp <= 4:
        base = DAILY_SALARY * (0.65 if tightness == 0 else 0.85)
    else:
        base = DAILY_SALARY * (0.5 if tightness == 0 else 0.7)

    # Exploit yesterday: if someone was willing to bid very high, we slightly undercut/meet them.
    # We aim to beat Cindy-like behavior without overspending.
    target = base
    if yesterday_max_bid >= DAILY_SALARY * 0.85:
        # High pressure yesterday: match just above the max to secure water.
        target = max(target, yesterday_max_bid + 2.0)
    elif yesterday_max_bid >= DAILY_SALARY * 0.65:
        # Moderate pressure: bid around average plus a small premium.
        target = max(target, yesterday_avg_bid + (8.0 if tightness >= 1 else 4.0))
    else:
        # Low pressure: bid enough to stay competitive.
        target = max(target, yesterday_avg_bid + (5.0 if tightness >= 1 else 2.0))

    # Convert to feasible bid within budget.
    bid = min(budget, target)

    # If budget is extremely low, still try to survive.
    if bid < 1.0:
        bid = min(budget, DAILY_SALARY * 0.2)

    # Ensure non-negative.
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    my_hp = int(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opponents = []
    for agent_id, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append((agent_id, o))

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Extract yesterday bids of alive opponents (immediate reaction)
    yesterday_bids = []
    yesterday_hp_after = []
    for agent_id, o in alive_opponents:
        prev = o.get('previous_trace', {}) or {}
        if prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass
        if prev.get('hp_after') is not None:
            try:
                yesterday_hp_after.append(float(prev['hp_after']))
            except Exception:
                pass

    base_bid = DAILY_SALARY * 0.55

    # If others were bidding aggressively yesterday, we slightly overbid to win water.
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / float(len(yesterday_bids))

        # Pressure estimate: low hp_after opponents likely will keep bidding to avoid death.
        low_hp_pressure = 0
        if yesterday_hp_after:
            low_hp_pressure = sum(1 for hp in yesterday_hp_after if hp <= 4) / float(len(yesterday_hp_after))

        # Aggression threshold tuned to meta medium; keep moderate overbid.
        # If highest prev bid is very high, bid closer to it but not fully.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_hp > 3 and my_no_water_days <= 1:
                target = max(base_bid, avg_prev_bid * 0.85, highest_prev_bid * 0.65)
            else:
                target = max(base_bid, avg_prev_bid * 0.95, highest_prev_bid * 0.75)
        else:
            # Otherwise, bid around avg with a small lift for low-hp pressure.
            target = max(base_bid, avg_prev_bid * (0.9 + 0.15 * low_hp_pressure))

        # Supply scaling: when supply is tighter, competition increases; bid slightly higher.
        # supply in [15,25]; map to factor ~[0.95,1.10]
        supply_factor = 0.95 + (supply - float(MIN_SUPPLY)) / float(MAX_SUPPLY - MIN_SUPPLY) * 0.15
        target *= supply_factor

    else:
        # Fallback if no trace bids available.
        target = base_bid
        if my_hp <= 2 or my_no_water_days >= 2:
            target = DAILY_SALARY * 0.85
        else:
            target = DAILY_SALARY * 0.55

    # Ensure we don't overspend: keep some buffer for future days.
    # If my budget is low, prioritize survival.
    if my_budget <= DAILY_SALARY * 1.0:
        cap = my_budget
    elif my_budget <= DAILY_SALARY * 2.0:
        cap = my_budget * 0.85
    else:
        cap = my_budget * 0.7

    # If I'm in danger, bid higher.
    if my_hp <= 2 or my_no_water_days >= 2:
        target = max(target, DAILY_SALARY * 0.75)

    # Never bid negative or above cap.
    bid = float(target)
    if bid < 0:
        bid = 0.0
    if bid > cap:
        bid = cap

    # Also avoid bidding above a reasonable fraction of max supply*? (safety)
    # Use WATER_REQ to avoid extreme overbids.
    max_reasonable = DAILY_SALARY * 1.2
    if bid > max_reasonable:
        bid = max_reasonable

    return bid
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

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opponents = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Extract yesterday bids from previous_trace for alive opponents
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Baseline target bid from yesterday competition
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        median_prev_bid = sorted(yesterday_bids)[len(yesterday_bids) // 2]
    else:
        highest_prev_bid = 0.0
        median_prev_bid = DAILY_SALARY * 0.6

    # Pressure increases when supply is lower (scarcer water)
    # Estimate how many full water units exist relative to our requirement.
    # Use int indices explicitly by converting to int where needed.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    scarcity_factor = 1.0 - max(0.0, min(1.0, supply_ratio))  # 0 at high supply, 1 at low supply

    # If I'm close to death, bid to secure water; otherwise bid to outcompete slightly.
    # no_water_days is consecutive days without water.
    urgent = (hp <= 2.5) or (no_water_days >= 2)

    # Compute a desired bid floor/ceiling.
    # If yesterday's highest bid was already high, we need to match/beat it a bit.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        base = highest_prev_bid + (2.0 + 8.0 * scarcity_factor)
    else:
        base = max(DAILY_SALARY * (0.45 + 0.25 * scarcity_factor), median_prev_bid * 0.95 + (1.0 + 6.0 * scarcity_factor))

    if urgent:
        # Spend more when urgent, but cap by budget.
        desired = min(budget, base + 0.35 * DAILY_SALARY)
    else:
        # Normal mode: bid just enough to beat the likely clearing level.
        desired = min(budget, base + 0.15 * DAILY_SALARY)

    # Safety: never bid above a reasonable fraction of budget early unless urgent.
    # Also ensure we don't bid trivially low when supply is tight.
    tight_min_bid = DAILY_SALARY * (0.35 + 0.35 * scarcity_factor)
    if not urgent:
        desired = max(tight_min_bid, desired)

    # Final clamp
    if budget <= 0:
        return 0.0
    return float(max(0.0, min(budget, desired)))
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

    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Extract yesterday bids to infer aggressiveness
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Supply pressure: with 15-25 water and requirement 9, typically 1 unit is ~enough for survival.
    # If supply is low, competition is higher.
    supply_factor = 0.0
    if supply <= (MIN_SUPPLY + 1e-6):
        supply_factor = 1.0
    elif supply >= (MAX_SUPPLY - 1e-6):
        supply_factor = 0.2
    else:
        # linear between 15..25
        supply_factor = 1.0 - (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)

    # Base bid target: midrange, scaled by supply pressure and our urgency.
    urgency = 0.0
    if no_water_days >= 2:
        urgency = 1.0
    elif no_water_days == 1:
        urgency = 0.6
    else:
        urgency = 0.2

    # If someone was extremely aggressive yesterday, slightly shadow to avoid losing the key allocation.
    # Use a conservative multiplier to avoid overpaying.
    shadow = 0.0
    if highest_prev_bid >= DAILY_SALARY * 1.6:
        shadow = 0.35
    elif highest_prev_bid >= DAILY_SALARY * 1.1:
        shadow = 0.2
    else:
        shadow = 0.05

    # Compute desired bid
    # Healthy hp -> don't overpay; low hp -> pay more.
    hp_factor = 0.0
    if hp <= 1:
        hp_factor = 1.0
    elif hp <= 3:
        hp_factor = 0.75
    elif hp <= 6:
        hp_factor = 0.45
    else:
        hp_factor = 0.25

    # Target around 0.6 salary when supply is low, lower when supply is high.
    target = DAILY_SALARY * (0.45 + 0.35 * supply_factor) * (0.55 + 0.45 * hp_factor)
    target *= (0.75 + 0.5 * urgency)
    target *= (1.0 + shadow)

    # Cap target by a fraction of budget to reduce risk.
    # If budget is already low, bid near budget to maximize survival probability.
    if budget <= DAILY_SALARY * 0.6:
        max_afford = budget
    else:
        max_afford = min(budget, DAILY_SALARY * 0.95)

    bid = min(max_afford, target)

    # Ensure non-negative and at least a minimal competitive amount when we must survive.
    if bid < 0.0:
        bid = 0.0

    # If we are at risk (hp low or no_water_days high), ensure we bid enough to compete.
    if (hp <= 3 or no_water_days >= 2) and bid < DAILY_SALARY * 0.65:
        bid = min(max_afford, DAILY_SALARY * 0.75)

    # If supply is abundant and we are healthy, avoid wasting money.
    if supply >= (MAX_SUPPLY - 1e-6) and hp >= 7 and no_water_days == 0:
        bid = min(bid, DAILY_SALARY * 0.4)

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

    # Identify alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # If no one alive, bid conservatively
    if not alive_opps:
        return max(0.0, min(float(my_status['budget']), DAILY_SALARY * 0.4))

    # Use only yesterday previous_trace for immediate reaction
    prev_bids = []
    for oid, o in alive_opps:
        pt = o.get('previous_trace', {})
        if pt and pt.get('bid') is not None:
            try:
                prev_bids.append(float(pt.get('bid', 0.0)))
            except Exception:
                pass

    # Compute perceived pressure from Cindy specifically if present
    cindy = opponents_status.get('Cindy', None)
    cindy_prev_bid = None
    if cindy is not None and cindy.get('alive', False):
        pt = cindy.get('previous_trace', {})
        if pt and pt.get('bid') is not None:
            try:
                cindy_prev_bid = float(pt.get('bid'))
            except Exception:
                cindy_prev_bid = None

    # Determine target spend based on supply and pressure
    # Higher supply reduces need to overbid.
    supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_factor = max(0.0, min(1.0, supply_factor))

    # Baseline: try to buy enough to avoid water starvation
    # Assume each day needs WATER_REQ and water allocation is proportional to bid.
    # We translate this into a bid fraction of DAILY_SALARY.
    base_bid = DAILY_SALARY * (0.55 - 0.15 * supply_factor)  # 0.55..0.40

    # Pressure escalation if Cindy was bidding aggressively
    # If Cindy maxed out yesterday (~>=150), treat as strong threat.
    if cindy_prev_bid is not None:
        if cindy_prev_bid >= 170:
            pressure_bid = DAILY_SALARY * 0.95
        elif cindy_prev_bid >= 140:
            pressure_bid = DAILY_SALARY * 0.75
        elif cindy_prev_bid >= 100:
            pressure_bid = DAILY_SALARY * 0.62
        else:
            pressure_bid = DAILY_SALARY * 0.55
    else:
        # Fallback: use max of previous bids among alive
        if prev_bids:
            highest_prev_bid = max(prev_bids)
            if highest_prev_bid >= 170:
                pressure_bid = DAILY_SALARY * 0.95
            elif highest_prev_bid >= 140:
                pressure_bid = DAILY_SALARY * 0.75
            elif highest_prev_bid >= 100:
                pressure_bid = DAILY_SALARY * 0.62
            else:
                pressure_bid = DAILY_SALARY * 0.55
        else:
            pressure_bid = DAILY_SALARY * 0.55

    # Health urgency: if low hp or many no-water days, increase bid.
    hp = float(my_status.get('hp', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    urgency_multiplier = 1.0
    if hp <= 2:
        urgency_multiplier = 1.15
    elif hp <= 4:
        urgency_multiplier = 1.07

    if no_water_days >= 2:
        urgency_multiplier = max(urgency_multiplier, 1.15)
    if no_water_days >= 4:
        urgency_multiplier = max(urgency_multiplier, 1.25)

    # Final bid: blend base and pressure; avoid overspending
    desired = (0.45 * base_bid) + (0.55 * pressure_bid)
    desired *= urgency_multiplier

    budget = float(my_status.get('budget', 0.0))

    # Clamp to budget and to a reasonable upper bound
    upper = min(budget, DAILY_SALARY * 1.1)  # don't exceed ~99 salary per day
    lower = 0.0

    bid = max(lower, min(upper, desired))

    # If budget is tiny, still bid what we can
    if budget <= 1e-6:
        return 0.0

    # Ensure bid is not negative and is float
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

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # If no opponents alive, bid low but keep survival margin.
    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace.
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
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    # Base bid: aim to win when supply is tight; otherwise conserve.
    # With supply in [15,25], the per-day water is enough for 1-2 agents.
    # We assume competition is strongest when supply is near MIN_SUPPLY.
    supply_ratio = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Tight supply -> higher base bid; abundant -> lower base bid.
    base = DAILY_SALARY * (0.40 + (1.0 - supply_ratio) * 0.25)  # 0.40..0.65

    # Pressure adjustment from yesterday's observed bids.
    # If others were bidding very high, raise slightly; otherwise keep moderate.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        pressure = 0.18
    elif highest_prev_bid >= DAILY_SALARY * 0.60:
        pressure = 0.10
    else:
        pressure = 0.05

    # Urgency from our hp/no_water_days.
    # If we are close to starvation, bid aggressively.
    urgency = 0.0
    if hp <= 2.0:
        urgency = 0.35
    elif hp <= 4.0:
        urgency = 0.20
    elif no_water_days >= 2:
        urgency = 0.18
    elif no_water_days >= 1:
        urgency = 0.08

    # Final target bid.
    target = base * (1.0 + pressure + urgency)

    # Avoid overspending: keep some buffer for future days.
    # If budget is low, cap at a fraction.
    if budget <= DAILY_SALARY * 0.8:
        target = min(target, budget * 0.85)
    else:
        target = min(target, budget * 0.6)

    # If yesterday bids were extremely high, we don't want to match; we exploit by underbidding.
    if highest_prev_bid >= DAILY_SALARY * 1.5:
        target = min(target, DAILY_SALARY * 0.55 + (highest_prev_bid - DAILY_SALARY * 0.55) * 0.25)

    # Ensure non-negative and within budget.
    bid = max(0.0, min(budget, target))

    # Small deterministic tie-breaker by day parity.
    if int(day) % 2 == 1:
        bid = bid * 1.01

    return float(bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o is not None and o.get('alive', False):
            alive_opponents.append(o)

    if not alive_opponents:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace only.
    prev_bids = []
    prev_hp_after = []
    for o in alive_opponents:
        prev = o.get('previous_trace', {})
        if isinstance(prev, dict) and prev.get('bid') is not None:
            prev_bids.append(float(prev.get('bid', 0.0)))
            prev_hp_after.append(float(prev.get('hp_after', 0.0)))

    # If we have no trace info, use conservative baseline.
    if not prev_bids:
        base = DAILY_SALARY * (0.55 if hp > 3 else 0.9)
        return max(0.0, min(budget, base))

    highest_prev_bid = max(prev_bids)
    second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev_bid

    # Estimate how many water units are even available today.
    # (Used only to scale aggressiveness.)
    units_available = int(supply / float(WATER_REQ)) if WATER_REQ > 0 else 0

    # Determine target bid: try to undercut the strongest pressure.
    # If they were bidding very high yesterday, we bid slightly below to win at lower cost.
    # If we were low HP / accumulating no-water days, we bid higher to avoid death.
    pressure = highest_prev_bid / float(DAILY_SALARY) if DAILY_SALARY > 0 else 0.0

    if hp <= 2 or no_water_days >= 2:
        target = min(budget, DAILY_SALARY * 0.95)
    else:
        # Healthy: bid near the heavy bidder but not equal.
        if pressure >= 1.15:
            # heavy bidding: aim just below highest, but also above second to beat ties
            target = second_prev_bid + 1.0
            # cap to avoid irrational overspending
            target = min(target, highest_prev_bid - 1.0)
            # if supply is low (fewer units), we need to be closer to highest
            if units_available <= 1:
                target = max(target, highest_prev_bid - 0.5)
        elif pressure >= 0.9:
            target = max(DAILY_SALARY * 0.6, second_prev_bid + 1.0)
        else:
            target = DAILY_SALARY * 0.55

        # Keep target within budget.
        target = min(target, budget)

    # Final safety clamp.
    if target < 0.0:
        target = 0.0
    return float(target)
"""
