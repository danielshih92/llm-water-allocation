# ============================================================
# Experiment: exp_016
# Agent: Bob
# Source: exp_016
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    # Alive opponents only
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        return min(my_status.get('budget', 0.0), DAILY_SALARY * 0.4)

    # Read yesterday bids from previous_trace
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # Determine aggressiveness
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
    else:
        highest_prev_bid = 0.0

    my_budget = float(my_status.get('budget', 0.0))
    my_hp = float(my_status.get('hp', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # If we are close to failure, prioritize survival
    critical_survival = (my_hp <= 2.0) or (no_water_days >= 2)

    # Compute a target bid based on supply pressure
    # Approximate how many water units might be needed; use int() for safety.
    # (Indices are not used, but we keep consistent casting.)
    supply_units = int(supply / float(WATER_REQ)) if WATER_REQ > 0 else 0

    # High-pressure threshold: if opponent bid is near salary, they likely expect to win.
    high_pressure = DAILY_SALARY * 0.85

    if critical_survival:
        # Bid aggressively but not maxed out to avoid wasting budget.
        base = DAILY_SALARY * 0.95 if my_hp <= 1.5 else DAILY_SALARY * 0.75
        # If supply is low, increase bid.
        if supply < float(WATER_REQ) * 1.2:
            base *= 1.05
        bid = min(my_budget, base)
        return bid

    if highest_prev_bid >= high_pressure:
        # Undercut slightly to win if they overspend.
        # Add a small buffer depending on supply scarcity.
        scarcity_factor = 1.0
        if supply <= float(MIN_SUPPLY):
            scarcity_factor = 1.08
        elif supply >= float(MAX_SUPPLY):
            scarcity_factor = 0.95
        target = highest_prev_bid * 0.98 + 1.0 * scarcity_factor
        # If we have more budget, contest a bit more.
        if my_budget >= DAILY_SALARY:
            target = max(target, DAILY_SALARY * 0.65)
        bid = min(my_budget, target)
        return bid

    # If opponents were not bidding aggressively, conserve budget.
    # Use supply_units to decide how much to bid: fewer units => bid more.
    if supply_units <= 1:
        bid = DAILY_SALARY * 0.6
    else:
        bid = DAILY_SALARY * 0.48

    # Light reaction to their previous highest bid
    if highest_prev_bid > 0.0:
        bid = max(bid, min(my_budget, highest_prev_bid + 1.5))

    # Ensure we don't bid too low to be completely non-competitive.
    min_competitive = DAILY_SALARY * 0.35
    bid = max(min_competitive, bid)
    bid = min(my_budget, bid)
    return bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = day_context['supply']
    day = day_context['day']

    # Alive opponents only
    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append(o)

    if my_status.get('budget', 0) <= 0:
        return 0.0

    # Read yesterday bids from previous_trace for immediate reaction
    yesterday_bids = []
    for o in alive_opponents:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    hp = my_status.get('hp', 0)
    budget = my_status.get('budget', 0)
    no_water_days = my_status.get('no_water_days', 0)

    # Base allocation logic: aim to secure water when we're at risk.
    risk = 0
    if hp <= 2:
        risk += 3
    if hp <= 5:
        risk += 2
    if no_water_days >= 2:
        risk += 2
    if no_water_days >= 3:
        risk += 2

    # Supply pressure: lower supply => higher chance of bidding war.
    # supply is between 15 and 25 in this meta-round.
    supply_pressure = 0
    if supply <= 18.0:
        supply_pressure = 3
    elif supply <= 20.0:
        supply_pressure = 2
    elif supply <= 22.0:
        supply_pressure = 1
    else:
        supply_pressure = 0

    # If opponents were willing to bid near/above our salary yesterday, increase bid.
    # Cindy/Eric showed high bids in the trace.
    threshold = DAILY_SALARY * 0.85
    if highest_prev_bid >= threshold:
        # Win more often when others are already spending.
        target = DAILY_SALARY * (0.65 + 0.15 * risk + 0.05 * supply_pressure)
    else:
        # Keep costs moderate.
        target = DAILY_SALARY * (0.45 + 0.12 * risk + 0.04 * supply_pressure)

    # Ensure we bid enough to potentially beat moderate bids, but cap to budget.
    # Add a small increment if there was a strong bid yesterday.
    if highest_prev_bid > 0:
        target = max(target, min(budget, highest_prev_bid * 0.55 + 10.0))

    # Cap target by budget and also by a practical ceiling to avoid bankrupting.
    # In this game, overbidding can lead to 0 budget; keep within ~1.2 salary.
    max_reasonable = min(budget, DAILY_SALARY * 1.2)
    bid = min(max_reasonable, max(0.0, target))

    # If we're very healthy and supply is high, reduce to preserve budget.
    if hp >= 8 and supply >= 22.0 and no_water_days == 0:
        bid = min(bid, DAILY_SALARY * 0.35)

    # If extremely risky, push closer to max_reasonable.
    if risk >= 5:
        bid = max(bid, DAILY_SALARY * 0.8)
        bid = min(bid, max_reasonable)

    # Final safety: never exceed budget
    if bid > budget:
        bid = float(budget)

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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if my_budget <= 0:
        return 0.0

    # If we're in immediate danger, bid aggressively but not to the point of Cindy's extreme.
    if my_hp <= 2 or my_no_water_days >= 2:
        target = 0.85 * DAILY_SALARY
    else:
        target = 0.55 * DAILY_SALARY

    # React to yesterday's visible bids (only immediate reaction via previous_trace).
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    if yesterday_bids:
        highest = max(yesterday_bids)
        lowest = min(yesterday_bids)

        # If someone overbid heavily yesterday (likely Cindy), we undercut.
        if highest >= 0.95 * DAILY_SALARY:
            # Keep enough to beat typical low bidders, but avoid chasing the ceiling.
            target = min(target, 0.65 * DAILY_SALARY)
            # If we also have low HP, still bid higher.
            if my_hp <= 3:
                target = max(target, 0.75 * DAILY_SALARY)
        else:
            # If yesterday was generally low, we can bid slightly higher than the median/highest-low.
            # Use a conservative bump to secure water without overpaying.
            target = max(target, min(0.70 * DAILY_SALARY, lowest + 0.25 * DAILY_SALARY))

    # Supply-aware adjustment: higher supply means we can bid less to get allocated water.
    # Normalize supply into [0,1] range.
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_norm = 0.5
    supply_norm = 0.0 if supply_norm < 0.0 else (1.0 if supply_norm > 1.0 else supply_norm)

    # If supply is high, reduce bid; if low, increase slightly.
    target = target * (1.0 - 0.15 * supply_norm) + target * (0.15 * (1.0 - supply_norm))

    # Final clamp by budget and a reasonable upper bound.
    # Avoid bidding more than our budget.
    bid = min(my_budget, target)

    # Ensure we bid something meaningful when budget allows.
    if bid < 1.0 and my_budget >= 1.0 and my_hp > 2:
        bid = min(my_budget, 0.25 * DAILY_SALARY)

    # Return float.
    return float(bid)
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Identify alive opponents
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    if not alive:
        # Conservative: keep enough budget for later
        return float(min(my_status['budget'], DAILY_SALARY * 0.35))

    # Read yesterday bids from previous_trace for immediate reaction
    prev_bids = []
    for oid, o in alive:
        prev = o.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate number of water units we can buy relative to our requirement
    # (Supply is total water; winning share likely scales with bid.)
    # Use a heuristic target: bid enough to compete when supply is tight.
    supply_tight = supply <= (MIN_SUPPLY + MAX_SUPPLY) / 2.0  # ~20

    # Determine pressure from yesterday: Cindy survived and bid high -> likely consistently strong.
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # If we are in danger, increase bid sharply.
    danger = (hp <= 2.5) or (no_water_days >= 2)

    # If Cindy-like pressure exists (very high yesterday bids), avoid bidding at the top.
    # Aim for a mid-tier bid to secure some water.
    # Thresholds tuned to yesterday: Cindy avg ~69, others died with lower budgets.
    if danger:
        # Spend to survive, but cap to avoid bankruptcy.
        cap = DAILY_SALARY * (0.85 if supply_tight else 0.75)
        bid = min(budget, cap)
        # If competition was extreme, add a bit more.
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            bid = min(budget, DAILY_SALARY * 0.92)
        return float(bid)

    # Not in immediate danger: choose a strategic bid.
    # If yesterday highest bids were high, we underbid slightly to avoid a price war.
    if highest_prev_bid >= DAILY_SALARY * 0.65:
        # Bid around a fraction of salary, adjusted by supply tightness.
        base = DAILY_SALARY * (0.48 if supply_tight else 0.42)
        # If our budget is low, still bid enough to not fall behind.
        floor = min(budget, DAILY_SALARY * 0.25)
        bid = max(floor, base)
        # Small reaction to average opponent bidding.
        if avg_prev_bid > 0:
            bid = min(budget, max(bid, avg_prev_bid * 0.55))
        return float(min(budget, bid))

    # If yesterday bids were moderate/low, bid a bit more to secure water early.
    target = DAILY_SALARY * (0.55 if supply_tight else 0.5)
    # If budget is very low, scale down.
    if budget < DAILY_SALARY * 0.35:
        target = min(target, budget)
    bid = min(budget, target)

    # If we have already had no water days, increase slightly.
    if no_water_days >= 1:
        bid = min(budget, bid + DAILY_SALARY * 0.08)

    # Ensure non-negative
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))

    alive = []
    for agent_id, st in opponents_status.items():
        if st.get('alive', False):
            alive.append((agent_id, st))

    if not alive:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Read yesterday bids to infer opponent aggressiveness
    yesterday_bids = []
    for _, st in alive:
        prev = st.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # If someone was extremely aggressive yesterday, increase our bid to avoid being outbid.
    extreme = highest_prev_bid >= (DAILY_SALARY * 6.0)  # e.g., Cindy's 915

    # Supply pressure: higher supply usually reduces competition; lower supply increases it.
    # Map supply in [15,25] -> competition factor in [1.0,0.6]
    if MAX_SUPPLY > MIN_SUPPLY:
        t = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        t = 0.5
    t = max(0.0, min(1.0, t))
    comp_factor = 1.0 - 0.4 * t  # 1.0 at 15, 0.6 at 25

    # Base bid target: aim around 0.55-0.75 salary depending on hp.
    if my_hp <= 2:
        base = DAILY_SALARY * 0.9
    elif my_hp <= 5:
        base = DAILY_SALARY * 0.7
    else:
        base = DAILY_SALARY * 0.6

    # Adjust for extreme opponent behavior
    if extreme:
        base *= 1.25

    # Final target scales with competition
    target = base * comp_factor

    # Additional small bump if we are low on budget relative to target
    if my_budget < target:
        target = my_budget

    # Never bid more than we can afford
    bid = min(my_budget, target)

    # If budget is very low, still try to secure water proportionally
    if my_budget <= DAILY_SALARY * 0.2:
        bid = min(my_budget, DAILY_SALARY * 0.2)

    # Ensure non-negative bid
    if bid < 0:
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

    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive.append((opp_id, opp))

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids to infer pressure.
    prev_bids = []
    for _, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate how many water units likely exist; bid aggressiveness increases with tighter supply.
    # supply is float; indices are not used.
    units_possible = int(supply / WATER_REQ)  # e.g., 19/9 -> 2
    tight = (supply <= (MIN_SUPPLY + 1.0)) or (units_possible <= 1)

    # Determine opponent pressure from yesterday.
    pressure = 0.0
    if prev_bids:
        pressure = max(prev_bids)

    # If someone was bidding extremely high yesterday, we should match moderately; otherwise undercut.
    # Also, if my hp is low or I have had no water for several days, I must secure water.
    must_have = (hp <= 2) or (no_water_days >= 2)

    # Base target bid
    if must_have:
        target = DAILY_SALARY * (0.85 if tight else 0.75)
    else:
        # If yesterday pressure was high, raise; if low, lower.
        if pressure >= DAILY_SALARY * 1.6:
            target = DAILY_SALARY * (0.70 if tight else 0.60)
        elif pressure >= DAILY_SALARY * 1.1:
            target = DAILY_SALARY * (0.60 if tight else 0.50)
        else:
            target = DAILY_SALARY * (0.50 if tight else 0.40)

    # Slightly adapt to remaining budget to avoid overspending.
    # If budget is small, cap bid proportionally.
    budget_cap = budget * (0.75 if must_have else 0.55)
    target = min(target, budget_cap)

    # Add a small increment to beat typical aggressive bids when needed.
    if must_have and pressure > 0:
        target = max(target, min(budget, pressure * 0.55 + 10.0))
    elif not must_have and pressure > 0:
        # Underbid relative to max yesterday pressure.
        target = min(target, max(0.0, pressure * 0.45))

    # Final clamp
    if budget <= 0:
        return 0.0
    bid = max(0.0, min(float(budget), float(target)))
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

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # If no opponents alive, conserve budget.
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace only.
    prev_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Pressure estimate: if any opponent bid very high yesterday, expect a contest.
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate how many water units supply can support (used only for scaling).
    # Ensure indices are int-safe (though we won't index arrays).
    supply_units = int(supply / float(WATER_REQ))  # 15-25 => 1-2

    # Baseline bid: aim to secure 1 unit when supply is tight.
    # Use a moderate fraction of daily salary to avoid overpaying.
    if supply_units <= 1:
        base = DAILY_SALARY * 0.65
    else:
        base = DAILY_SALARY * 0.55

    # Adjust based on our HP.
    hp = float(my_status['hp'])
    if hp <= 1.5:
        hp_mult = 1.25
    elif hp <= 3.0:
        hp_mult = 1.05
    else:
        hp_mult = 0.95

    # If opponents were bidding aggressively yesterday, slightly outbid.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        contest_mult = 1.08
    elif highest_prev_bid >= DAILY_SALARY * 0.55:
        contest_mult = 1.03
    else:
        contest_mult = 0.98

    bid = base * hp_mult * contest_mult

    # If an opponent survived yesterday with low bids, we can undercut slightly.
    # Use their previous_trace if available.
    lowest_survivor_bid = None
    for _, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('hp_after', None) is not None:
            try:
                hp_after = float(prev.get('hp_after'))
            except Exception:
                hp_after = None
            if hp_after is not None and hp_after > 0:
                b = prev.get('bid', None)
                if b is not None:
                    try:
                        b = float(b)
                        if lowest_survivor_bid is None or b < lowest_survivor_bid:
                            lowest_survivor_bid = b
                    except Exception:
                        pass

    if lowest_survivor_bid is not None and lowest_prev_bid := float(lowest_survivor_bid):
        # Undercut if we are far above their typical spending.
        if bid > lowest_prev_bid * 1.25:
            bid = (bid + lowest_prev_bid) / 2.0

    # Hard caps: cannot exceed budget.
    budget = float(my_status['budget'])
    if budget <= 0:
        return 0.0

    # Keep bid within reasonable bounds relative to salary.
    bid_cap = DAILY_SALARY * 0.95
    bid = float(min(bid, bid_cap, budget))

    # If we are low on budget, scale down.
    if budget < DAILY_SALARY * 0.6:
        bid = float(min(bid, budget * 0.9))

    # Ensure non-negative.
    if bid < 0:
        bid = 0.0

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

    # Determine alive opponents and yesterday bids
    alive_opps = []
    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(float(prev['bid']))

    # Safety: if no opponents alive, bid low
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Pressure from yesterday
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        lowest_prev_bid = min(yesterday_bids)
    else:
        highest_prev_bid = DAILY_SALARY
        lowest_prev_bid = DAILY_SALARY * 0.3

    # Estimate how many water units are likely needed/available
    # If supply is near WATER_REQ, competition is intense; bid closer to top.
    supply_ratio = supply / float(WATER_REQ)
    scarcity = 0.0
    if supply_ratio <= 1.2:
        scarcity = 1.0
    elif supply_ratio <= 1.6:
        scarcity = 0.6
    else:
        scarcity = 0.25

    # Budget-aware cap: don't overextend early
    # Keep some buffer for later days (episode length is 10; assume remaining ~10-day).
    # We don't know remaining exactly, so use a conservative fraction.
    budget_cap = budget * 0.55

    # Base bid level from yesterday pressure
    # If someone was bidding very high yesterday, match a fraction to avoid losing.
    high_pressure = highest_prev_bid >= DAILY_SALARY * 1.4
    mid_pressure = highest_prev_bid >= DAILY_SALARY * 0.9

    # If our HP is low or we've had no water multiple days, bid aggressively.
    urgent = (hp <= 2.5) or (no_water_days >= 2)

    if urgent:
        # Aggressive: ensure we likely clear the clearing price.
        target = DAILY_SALARY * (1.1 + 0.6 * scarcity)
        if high_pressure:
            target = max(target, highest_prev_bid * 0.75)
        # Ensure at least above lowest-prev to avoid being undercut.
        target = max(target, lowest_prev_bid + 5.0)
    else:
        # Not urgent: bid enough to compete, but stay under budget cap.
        if high_pressure:
            target = DAILY_SALARY * (0.85 + 0.3 * scarcity)
            target = max(target, highest_prev_bid * 0.55)
        elif mid_pressure:
            target = DAILY_SALARY * (0.65 + 0.25 * scarcity)
            target = max(target, highest_prev_bid * 0.45)
        else:
            target = DAILY_SALARY * (0.55 + 0.2 * scarcity)

    # Final clamp to feasible range
    bid = float(min(budget_cap, target))
    if bid < 0.0:
        bid = 0.0

    # If supply is extremely low, push closer to cap to avoid zero-water death spiral.
    if scarcity >= 0.9 and hp > 0 and budget > 0:
        bid = float(min(budget, max(bid, DAILY_SALARY * 0.95)))

    # If budget is tiny, bid whatever possible.
    if budget <= 10.0:
        bid = float(min(budget, DAILY_SALARY * 0.2))

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

    # Alive opponents and their yesterday bids
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

    # If no opponents alive, bid minimally to stay solvent
    if not alive_opps:
        return max(0.0, min(float(my_status.get('budget', 0.0)), DAILY_SALARY * 0.4))

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Estimate how aggressive the field was yesterday
    if yesterday_bids:
        top_bid = max(yesterday_bids)
        second_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else top_bid
    else:
        top_bid = 0.0
        second_bid = 0.0

    # Supply pressure: higher supply reduces need to overpay
    # Map supply to a multiplier between ~0.85 (low supply) and ~0.55 (high supply)
    if MAX_SUPPLY > MIN_SUPPLY:
        t = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        t = 0.5
    t = max(0.0, min(1.0, float(t)))
    supply_mult = 0.85 - 0.30 * t

    # HP/no-water urgency
    urgency = 0.0
    if my_hp <= 2.0:
        urgency += 1.0
    elif my_hp <= 4.0:
        urgency += 0.6
    if no_water_days >= 2:
        urgency += 0.5
    if no_water_days >= 3:
        urgency += 0.4

    # Target bid heuristic: try to outbid safety bidders without matching their maximum
    # If top yesterday bid was very high, set target near it but slightly below/around.
    # Otherwise, anchor around second highest plus a small increment.
    if top_bid >= DAILY_SALARY * 1.25:
        target = top_bid * (0.92 - 0.08 * urgency)
    else:
        target = (second_bid + 2.0) * (0.90 - 0.10 * urgency) + (top_bid * 0.05)

    # Add urgency floor/ceiling relative to salary
    if urgency >= 1.0:
        target = max(target, DAILY_SALARY * 0.95)
    elif urgency >= 0.6:
        target = max(target, DAILY_SALARY * 0.75)
    else:
        target = max(target, DAILY_SALARY * 0.55)

    # If supply is high, reduce bid
    target *= supply_mult

    # Ensure we don't bid more than budget or absurdly high
    max_reasonable = my_budget
    if my_budget <= 0.0:
        return 0.0

    # Keep some budget buffer: don't spend all unless very urgent
    spend_frac = 0.65 if urgency >= 1.0 else (0.45 if urgency >= 0.6 else 0.35)
    cap = my_budget * spend_frac

    bid = min(target, cap, my_budget)
    if bid < 0.0:
        bid = 0.0
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

    supply = day_context['supply']
    day = day_context['day']

    # If we're already in danger, prioritize survival.
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    alive_opponents = []
    for opp in opponents_status.values():
        if opp.get('alive', False) and opp.get('budget', 0) > 0:
            alive_opponents.append(opp)

    # Default safe bid baseline: enough to be competitive without wasting budget.
    # Scale with supply: higher supply -> lower urgency.
    supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if (MAX_SUPPLY - MIN_SUPPLY) != 0 else 0.5
    supply_norm = max(0.0, min(1.0, float(supply_norm)))

    base = DAILY_SALARY * (0.62 - 0.25 * supply_norm)  # 0.62 at low supply, 0.37 at high supply

    # React to yesterday's bids: Cindy likely exhausted, Eric low, Alex moderate.
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    if prev_bids:
        highest_prev_bid = max(prev_bids)
        # If someone previously bid extremely high, they likely ran out of budget.
        # We can shade downward.
        if highest_prev_bid >= DAILY_SALARY * 5.0:
            base *= 0.78
        # If there was moderate competition, bid enough to secure water.
        elif highest_prev_bid >= DAILY_SALARY * 0.85:
            base *= 0.95
        else:
            base *= 1.05

    # If our no-water days are high, increase urgency.
    no_water_days = my_status.get('no_water_days', 0)
    if no_water_days >= 2:
        base *= 1.15
    if no_water_days >= 4:
        base *= 1.35

    # Cap to avoid suicidal spending; also ensure we don't bid more than budget.
    # Target is often around 0.5-0.9 of daily salary depending on pressure.
    bid = min(my_status['budget'], max(1.0, base))

    # Small final adjustment: if supply is very low, be more aggressive.
    if supply <= MIN_SUPPLY + 1.0:
        bid = min(my_status['budget'], bid * 1.12)

    return float(bid)
"""
