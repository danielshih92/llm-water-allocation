# ============================================================
# Experiment: exp_086
# Agent: Bob
# Source: exp_086
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    budget = float(my_status.get('budget', 0.0))
    hp = float(my_status.get('hp', 0.0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday bids from traces
    prev_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # If no trace info, bid based on our hp
    if not prev_bids:
        if hp <= 2:
            return min(budget, DAILY_SALARY * 0.9)
        return min(budget, DAILY_SALARY * 0.55)

    highest_prev_bid = max(prev_bids)

    # Estimate how many full requirements the supply can cover
    # (use int() for any list indexing; here only for comparisons)
    max_full = int(supply / float(WATER_REQ)) if WATER_REQ > 0 else 0

    # Aggressive if opponents were bidding very high yesterday
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # If we are low hp, push harder.
        if hp <= 2:
            target = DAILY_SALARY * 0.95
        elif hp <= 3:
            target = DAILY_SALARY * 0.75
        else:
            target = DAILY_SALARY * 0.65
        # Slightly outbid the previous max to steal allocation
        target = max(target, highest_prev_bid + 1.0)
    else:
        # Moderate: compete but preserve budget
        # If supply is tight, raise bid; if abundant, lower.
        tightness = 0.0
        if max_full <= 1:
            tightness = 1.0
        elif max_full == 2:
            tightness = 0.6
        else:
            tightness = 0.3

        base = max(DAILY_SALARY * 0.45, highest_prev_bid + 1.5)
        target = base + tightness * (DAILY_SALARY * 0.15)

    # Final cap by budget and a minimum floor to avoid zeroing out when competing
    target = float(target)
    if budget <= 0:
        return 0.0

    # Ensure we never exceed budget
    bid = min(budget, target)

    # If our hp is critical, don't be too conservative
    if hp <= 1 and bid < DAILY_SALARY * 0.6:
        bid = min(budget, DAILY_SALARY * 0.85)

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
    day = day_context.get('day', 0)

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # React to yesterday's likely pressure: use opponents' previous bid if present.
    prev_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate how aggressive the field is.
    field_bid = 0.0
    if prev_bids:
        field_bid = max(prev_bids)

    # Supply tightness: if supply is closer to MIN_SUPPLY, competition is higher.
    # Use a normalized factor in [0,1].
    if MAX_SUPPLY <= MIN_SUPPLY:
        tight_factor = 0.5
    else:
        tight_factor = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)
        if tight_factor < 0.0:
            tight_factor = 0.0
        if tight_factor > 1.0:
            tight_factor = 1.0

    # Base bid: moderate to avoid overpaying, but enough to beat typical ~96-101 avg.
    # Scale with my hp/no_water_days.
    if hp <= 2 or no_water_days >= 2:
        urgency = 0.85
    elif hp <= 4 or no_water_days >= 1:
        urgency = 0.65
    else:
        urgency = 0.55

    # If yesterday had very high bids, slightly increase to avoid losing the water.
    # Otherwise keep near base.
    if field_bid >= DAILY_SALARY * 1.1:
        pressure = 0.10
    elif field_bid >= DAILY_SALARY * 0.9:
        pressure = 0.05
    else:
        pressure = 0.0

    # Tight supply increases competition.
    bid_fraction = urgency + pressure + 0.15 * tight_factor
    if bid_fraction < 0.35:
        bid_fraction = 0.35
    if bid_fraction > 0.95:
        bid_fraction = 0.95

    target = DAILY_SALARY * bid_fraction

    # Don't exceed budget.
    if budget <= 0.0:
        return 0.0

    # If supply is extremely low relative to requirement, we must secure water.
    # (Assume total water scales with supply; we just react via higher bid.)
    if supply < float(WATER_REQ):
        target = max(target, DAILY_SALARY * 0.9)

    # If my hp is already high, avoid overbidding above what seems necessary.
    if hp >= 7:
        target = min(target, DAILY_SALARY * (0.65 + 0.15 * tight_factor))

    # Final cap: ensure we can still survive multiple days.
    # Use a conservative cap of 0.7*budget to prevent depletion.
    cap = budget * 0.7
    return float(min(budget, max(0.0, min(target, cap))))
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

    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        cap = min(budget, DAILY_SALARY * 0.4)
        return max(0.0, cap)

    # Read yesterday bids from immediate previous_trace only
    prev_bids = []
    for opp_id, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate opponent pressure
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Choose aggressiveness based on my HP and their prior pressure
    # If Cindy-like high pressure existed, try to undercut slightly while staying strong.
    # Also scale with supply: when supply is higher, water is cheaper, so bid less.
    supply_ratio = 0.0
    if (MAX_SUPPLY - MIN_SUPPLY) > 0:
        supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    # Clamp
    if supply_ratio < 0.0:
        supply_ratio = 0.0
    if supply_ratio > 1.0:
        supply_ratio = 1.0

    # Base bid targets
    base = DAILY_SALARY * (0.62 - 0.25 * supply_ratio)  # lower bid when supply is higher

    # Pressure adjustment from yesterday
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Likely someone is paying near ceiling; undercut but remain competitive
        base = max(base, highest_prev_bid * 0.92)
    elif highest_prev_bid >= DAILY_SALARY * 0.45:
        base = max(base, highest_prev_bid * 0.75)

    # Urgency adjustment
    if hp <= 1:
        base = max(base, DAILY_SALARY * 0.95)
    elif hp <= 3:
        base = max(base, DAILY_SALARY * 0.78)

    # If we've gone multiple days without water, increase bid
    if no_water_days >= 2:
        base = max(base, DAILY_SALARY * 0.85)

    # Ensure we don't bid above reasonable fraction of budget
    # Keep some budget for later days; but if low budget, bid what we can.
    budget_cap = budget
    if budget_cap > 0.0:
        # If budget is healthy, keep at most ~70% of it for this day
        budget_cap = min(budget_cap, DAILY_SALARY * 1.2, budget * 0.7)

    bid = min(base, budget_cap)
    if bid < 0.0:
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = day_context['supply']
    day = day_context['day']

    # Alive opponents and yesterday bids
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Immediate reaction to yesterday's behavior (only previous_trace)
    yesterday_bids = []
    yesterday_hp_after = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass
        hp_after = prev.get('hp_after', None)
        if hp_after is not None:
            try:
                yesterday_hp_after.append(float(hp_after))
            except Exception:
                pass

    # Estimate competitive intensity from yesterday
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid

    # Convert supply to a rough
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

    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    if not alive:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday's bids from previous_trace for immediate reaction
    prev_bids = []
    for oid, o in alive:
        pt = o.get('previous_trace', {}) or {}
        b = pt.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate how many full water units might be needed from supply
    # (Used only to choose aggression; bidding is about winning share.)
    # Ensure integer indices if any are used later.
    max_units = int(supply // float(WATER_REQ)) if float(WATER_REQ) > 0 else 0

    # Baseline bid: if supply is tight, bid slightly more; if abundant, bid less.
    # With supply 15-25 and WATER_REQ=9, max_units is 1 or 2.
    if max_units <= 1:
        baseline = DAILY_SALARY * 0.62
    else:
        baseline = DAILY_SALARY * 0.48

    # Pressure from opponents: if yesterday bids were high, we must match/beat.
    if prev_bids:
        prev_high = max(prev_bids)
        prev_avg = sum(prev_bids) / float(len(prev_bids))
    else:
        prev_high = 0.0
        prev_avg = baseline

    # If we are in danger, escalate sharply.
    # No-water days increases risk; low hp increases urgency.
    danger = (my_hp <= 2.5) or (my_no_water_days >= 2)

    # Compute target bid.
    # Aim: slightly above the likely high-pressure cluster but not necessarily above absolute max.
    # Use 0.95 of max to avoid overpaying.
    target = baseline
    if prev_bids:
        # If others paid near our salary, we should not underbid.
        if prev_high >= DAILY_SALARY * 0.85:
            target = max(target, DAILY_SALARY * 0.72)
        # If average is high, follow it with a small premium.
        if prev_avg >= DAILY_SALARY * 0.55:
            target = max(target, prev_avg * 1.03)
        # If we must win under tight conditions, bump toward 95% of their max plus small step.
        if max_units <= 1 and prev_high > 0:
            target = max(target, prev_high * 0.95 + 2.0)

    if danger:
        target = max(target, DAILY_SALARY * 0.88)

    # Final clamp to budget and reasonable cap.
    # Keep within [0, budget].
    bid = max(0.0, min(my_budget, target))

    # If budget is extremely low, still bid something to avoid zero-water death spirals.
    if bid <= 0.0 and my_budget > 0.0:
        bid = min(my_budget, DAILY_SALARY * 0.2)

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
    day = day_context['day']

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Immediate reaction from yesterday's trace
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

    # Supply pressure: when supply is low, competition for survival increases
    # Map supply (15..25) to a pressure factor (0..1)
    if MAX_SUPPLY == MIN_SUPPLY:
        pressure = 0.5
    else:
        pressure = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    # Lower supply => higher pressure, so invert
    pressure = 1.0 - max(0.0, min(1.0, pressure))

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])

    # Base bid level: target around 0.55 salary at comfortable HP, higher at low HP
    if my_hp <= 2:
        base = DAILY_SALARY * 0.9
    elif my_hp <= 4:
        base = DAILY_SALARY * 0.75
    else:
        base = DAILY_SALARY * 0.55

    # If someone previously bid extremely high, avoid mirroring; instead outbid typical bids
    # while staying under the extreme to preserve budget.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Alex showed survival with high max bids; still we don't need to match.
        base = max(base, DAILY_SALARY * 0.65)

    # Adjust for supply pressure: low supply => bid more
    bid = base * (0.85 + 0.3 * pressure)

    # Safety: never bid more than budget
    bid = min(bid, my_budget)

    # If budget is tiny, bid as much as possible to avoid wasting turns
    if my_budget <= DAILY_SALARY * 0.25:
        bid = my_budget

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

    supply = day_context['supply']
    day = day_context['day']

    # Alive opponents and yesterday bids
    alive_opponents = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opponents:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.4))

    yesterday_bids = []
    yesterday_pressures = []  # (bid, hp_after, budget_after)
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is None:
            continue
        try:
            b_val = float(b)
        except Exception:
            continue
        yesterday_bids.append(b_val)
        hp_after = prev.get('hp_after', None)
        budget_after = prev.get('budget_after', None)
        try:
            hp_after_f = float(hp_after) if hp_after is not None else 0.0
        except Exception:
            hp_after_f = 0.0
        try:
            budget_after_f = float(budget_after) if budget_after is not None else 0.0
        except Exception:
            budget_after_f = 0.0
        yesterday_pressures.append((b_val, hp_after_f, budget_after_f))

    if not yesterday_bids:
        # No signal: bid based on my hp
        if my_status['hp'] <= 2:
            return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.9))
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.55))

    highest_prev_bid = max(yesterday_bids)
    second_highest = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid

    # Estimate how many water units supply can cover (use int indices safely)
    # This is a heuristic: if supply is near max, competition may be lower.
    supply_int = int(supply)
    supply_factor = (supply_int - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_factor = max(0.0, min(1.0, supply_factor))

    # If someone bid extremely high yesterday, they likely were in critical state.
    # Cindy survived with high-ish max bid (~149.5). We try to beat her by a small margin.
    critical_threshold = DAILY_SALARY * 0.85

    # Base aggressiveness
    if my_status['hp'] <= 2:
        base = DAILY_SALARY * 0.85
    elif my_status['hp'] <= 4:
        base = DAILY_SALARY * 0.65
    else:
        base = DAILY_SALARY * (0.55 + 0.15 * supply_factor)

    # If highest previous bid was high, try to just overtake it.
    if highest_prev_bid >= critical_threshold:
        # If I am healthy, still conserve slightly: outbid by a small step.
        step = 2.0 if my_status['hp'] > 4 else 5.0
        target = highest_prev_bid + step
        # If second highest is close, we may not need full target; aim between them.
        if (highest_prev_bid - second_highest) < 8.0:
            target = (highest_prev_bid + second_highest) / 2.0 + 2.0
    else:
        # When competition was moderate, bid around base but slightly above second-highest to win more often.
        target = max(base, second_highest + 1.5)
        # If supply is high, reduce a bit.
        target = target * (0.95 + 0.1 * (1.0 - supply_factor))

    # Budget and safety caps
    target = max(0.0, target)
    max_affordable = float(my_status['budget'])
    # Avoid bidding above a reasonable cap relative to salary; still allow if budget is huge.
    cap = max_affordable
    if cap > 0:
        cap = min(cap, DAILY_SALARY * 1.8)
    target = min(target, cap)

    # If my budget is low, scale down proportionally.
    if max_affordable <= DAILY_SALARY * 0.35:
        target = min(target, max_affordable * 0.95)

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
    day = day_context['day']

    # If we somehow have no budget, bid 0.
    if my_status['budget'] <= 0:
        return 0.0

    # Determine alive opponents and extract yesterday bids.
    alive_opps = []
    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {}) or {}
            if prev and prev.get('bid') is not None:
                try:
                    yesterday_bids.append(float(prev.get('bid')))
                except Exception:
                    pass

    # Supply pressure: fewer units per water requirement implies higher competition.
    # Use a conservative mapping to avoid fragile indexing.
    if supply <= MIN_SUPPLY:
        pressure = 1.0
    elif supply >= MAX_SUPPLY:
        pressure = 0.2
    else:
        # linear interpolation between MIN_SUPPLY and MAX_SUPPLY
        pressure = 1.0 - ((supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)) * 0.8
        if pressure < 0.2:
            pressure = 0.2
        if pressure > 1.0:
            pressure = 1.0

    # Baseline bid targets.
    # Goal: secure enough water to avoid no-water days cascading.
    hp = float(my_status['hp'])
    no_water_days = int(my_status.get('no_water_days', 0))
    budget = float(my_status['budget'])

    # If we are in danger, bid aggressively.
    if hp <= 2 or no_water_days >= 2:
        target = DAILY_SALARY * (0.85 + 0.15 * pressure)
    else:
        # When safe, bid just enough to compete with aggressive bidders.
        # Use yesterday's max bid as a signal of market clearing price.
        if yesterday_bids:
            highest_prev_bid = max(yesterday_bids)
            # If others were bidding near/above our daily salary, they likely overpay.
            # Counter by bidding moderately below that level.
            if highest_prev_bid >= DAILY_SALARY * 0.85:
                target = DAILY_SALARY * (0.35 + 0.25 * pressure)
            else:
                target = min(highest_prev_bid + 5.0, DAILY_SALARY * (0.55 + 0.25 * pressure))
        else:
            target = DAILY_SALARY * (0.45 + 0.25 * pressure)

    # Never exceed budget.
    if target > budget:
        target = budget

    # Add small day-based jitter to avoid exact ties.
    jitter = ((int(day) % 7) - 3) * 0.5
    target = target + jitter

    if target < 0:
        target = 0.0
    return float(target)
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
    day = int(day_context['day'])

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive'):
            alive.append(o)

    # If we are already in danger, prioritize survival.
    if hp <= 2 or no_water_days >= 2:
        # Aggressive but capped by budget.
        return max(0.0, min(budget, DAILY_SALARY * 0.95))

    # Read yesterday bids from alive opponents for immediate pressure.
    yesterday_bids = []
    for o in alive:
        prev = o.get('previous_trace', None) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Estimate how competitive the market was.
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / float(len(yesterday_bids))
    else:
        highest_prev_bid = 0.0
        avg_prev_bid = 0.0

    # Tight supply => bid higher. Looser supply => bid lower.
    # Normalize supply into [0,1].
    if MAX_SUPPLY == MIN_SUPPLY:
        supply_factor = 0.5
    else:
        supply_factor = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
        if supply_factor < 0.0:
            supply_factor = 0.0
        if supply_factor > 1.0:
            supply_factor = 1.0

    # Target bid: track around average/just above, but scaled by supply tightness.
    # If yesterday pressure was high, slightly overbid; otherwise, stay near a safe mid.
    pressure = 0.0
    if highest_prev_bid > 0.0:
        pressure = highest_prev_bid / float(DAILY_SALARY)

    # Base target
    if pressure >= 1.15:
        # Others were bidding ~>=103 for a 90 salary; compete.
        target = avg_prev_bid * (0.9 + 0.25 * (1.0 - supply_factor))
        # Ensure we are not far below the top bid.
        target = max(target, highest_prev_bid * (0.92 + 0.05 * (1.0 - supply_factor)))
    elif pressure >= 0.9:
        # Moderate competition.
        target = avg_prev_bid * (0.85 + 0.2 * (1.0 - supply_factor))
        target = max(target, DAILY_SALARY * (0.55 + 0.25 * (1.0 - supply_factor)))
    else:
        # Low competition: conserve.
        target = DAILY_SALARY * (0.45 + 0.25 * (1.0 - supply_factor))

    # If supply is very low (near 15), increase more.
    if supply <= (MIN_SUPPLY + 1.0):
        target *= 1.12

    # Cap by budget and keep some buffer.
    # If budget is low relative to salary, bid proportionally.
    if budget <= 0.0:
        return 0.0

    budget_cap = budget
    # Keep at least a small reserve for later days.
    reserve = min(budget_cap * 0.15, DAILY_SALARY * 0.15)
    max_affordable = max(0.0, budget_cap - reserve)

    bid = min(max_affordable, target)

    # Final sanity: bid must be non-negative.
    if bid < 0.0:
        bid = 0.0
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

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Read yesterday bids to infer who is pressuring
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

    # Estimate how many water units we can plausibly secure from supply
    # (We don't know allocation rule, but scarcity should raise bid pressure.)
    scarcity = 1.0
    if MAX_SUPPLY > MIN_SUPPLY:
        scarcity = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY + 1e-9)
    scarcity = max(0.0, min(1.0, scarcity))

    # If Cindy-like pressure existed yesterday, bid more only when we are at risk.
    # Targets: keep hp stable; conserve budget when possible.
    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Baseline bid: enough to avoid falling behind, but not as high as Cindy's average.
    # Increase when hp low or supply scarce.
    risk = 0.0
    if my_hp <= 2.0:
        risk += 1.0
    if my_hp <= 5.0:
        risk += 0.5
    if no_water_days >= 2:
        risk += 0.5
    risk = max(0.0, min(2.0, risk))

    # If yesterday's highest bid was very high, we assume strong competition.
    strong_competition = highest_prev_bid >= (DAILY_SALARY * 0.85)

    # Compute bid cap based on budget and urgency.
    # When strong competition and we're at risk, we partially match pressure.
    if strong_competition:
        if risk >= 1.0:
            target = DAILY_SALARY * (0.75 + 0.25 * scarcity)
        else:
            target = DAILY_SALARY * (0.55 + 0.20 * scarcity)
    else:
        target = DAILY_SALARY * (0.45 + 0.25 * scarcity)

    # Ensure we don't overbid beyond what we can sustain.
    # Spread budget over remaining days (roughly episode length 10).
    remaining_days = max(1, 10 - day + 1)
    budget_per_day = my_budget / float(remaining_days)

    bid = min(my_budget, target, budget_per_day * 1.1)

    # If extremely low hp, push close to daily salary.
    if my_hp <= 1.0:
        bid = min(my_budget, DAILY_SALARY * (0.95 + 0.05 * scarcity))

    # If supply is at minimum and we are not getting water, we must bid higher.
    if supply <= float(MIN_SUPPLY) + 1e-6 and my_hp <= 6.0:
        bid = max(bid, DAILY_SALARY * 0.65)

    # Final clamp
    if bid < 0.0:
        bid = 0.0
    return float(bid)
"""
