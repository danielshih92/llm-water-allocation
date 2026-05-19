# ============================================================
# Experiment: exp_007
# Agent: Bob
# Source: exp_007
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

    # Identify alive opponents
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    # If no opponents, bid enough to guarantee allocation
    if not alive_opps:
        # Aim for at most what we'd need for WATER_REQ, but cap by budget
        target = min(my_status['budget'], DAILY_SALARY * 0.4)
        return float(target)

    # Read yesterday bids from previous_trace to infer their aggressiveness
    prev_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Determine opponent pressure
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Budget and HP pressure
    hp = my_status.get('hp', 0)
    budget = my_status.get('budget', 0)
    no_water_days = my_status.get('no_water_days', 0)

    # Base strategy: moderate bid unless opponent was very aggressive
    # If my HP is low or I already have no-water days, I bid more.
    hp_critical = hp <= 2
    no_water_critical = no_water_days >= 2

    # Supply-related adjustment: if supply is low, water is more valuable -> bid higher.
    # Normalize supply into [0,1]
    if MAX_SUPPLY == MIN_SUPPLY:
        supply_norm = 0.5
    else:
        supply_norm = (float(supply) - float(MIN_SUPPLY)) / float(MAX_SUPPLY - MIN_SUPPLY)
    supply_factor = 1.0 + (1.0 - supply_norm) * 0.25  # up to +25% when supply is low

    # If opponent bid near/above my daily salary yesterday, they likely expect to win.
    aggressive = highest_prev_bid >= DAILY_SALARY * 0.85

    # Compute bid
    if aggressive:
        if hp_critical or no_water_critical:
            # Must contest strongly
            bid = DAILY_SALARY * 0.95
        else:
            # Contest but conserve budget
            bid = max(highest_prev_bid + 2.0, DAILY_SALARY * 0.35)
    else:
        # Not aggressive: bid moderately; if supply is low, bid a bit more.
        # Also, if I'm in trouble, increase.
        if hp_critical or no_water_critical:
            bid = DAILY_SALARY * 0.75
        else:
            bid = DAILY_SALARY * 0.52

        # If we have some signal of their bid, slightly overbid to secure allocation when needed
        if highest_prev_bid > 0.0:
            # Small overbid margin
            bid = max(bid, highest_prev_bid + 1.0)

    bid = float(bid) * float(supply_factor)

    # Final caps: cannot exceed budget
    bid = min(bid, float(budget))

    # Ensure non-negative
    if bid < 0.0:
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    # Identify alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # If no opponents, bid low
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Use yesterday's immediate behavior
    prev_bids = []
    prev_hp_after = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid', 0.0)))
                prev_hp_after.append(float(prev.get('hp_after', 0.0)))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Pressure estimate: if others were paying high yesterday, raise bid.
    # Supply affects urgency: higher supply reduces scarcity pressure.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Base target bid: track aggressiveness from yesterday.
    # If someone bid near/above 0.85*salary, we must respond.
    aggressive_threshold = 0.85 * DAILY_SALARY

    # Determine urgency from my hp and no-water streak
    urgency = 0.0
    if my_hp <= 2.0:
        urgency += 1.0
    if my_hp <= 3.0:
        urgency += 0.6
    if no_water_days >= 2:
        urgency += 0.6
    if no_water_days >= 3:
        urgency += 0.8

    # Compute desired bid
    if highest_prev_bid >= aggressive_threshold:
        # Match or slightly undercut the highest prior bid
        # Adjust with supply: if supply is high, we can undercut more.
        undercut = (1.0 - supply_ratio) * 6.0  # more undercut when supply is low? actually larger when supply low
        # We want to bid somewhat close to the highest prior bid.
        target = highest_prev_bid - undercut
        # If my hp is critical, bid closer to highest.
        if urgency >= 1.0:
            target = max(target, highest_prev_bid - 2.0)
    else:
        # Otherwise, bid around average/high-mid to stay competitive
        target = max(DAILY_SALARY * 0.5, avg_prev_bid + 2.0)
        # If supply is low, increase target
        if supply_ratio < 0.5:
            target += (0.5 - supply_ratio) * 10.0

    # Add small day-based variation to avoid ties (deterministic)
    # Use day parity to shift by a couple units.
    if int(day) % 2 == 0:
        target += 1.5
    else:
        target -= 1.0

    # Clamp to feasible budget and sensible bounds
    min_bid = 0.0
    max_affordable = my_budget

    # If my budget is very low, spend most of it to prevent death
    if my_budget <= DAILY_SALARY * 0.25:
        return float(min(my_budget, DAILY_SALARY * 0.9))

    # Ensure we don't overbid beyond what keeps us alive across days
    # Conservative cap depends on urgency.
    cap = DAILY_SALARY * (0.95 if urgency >= 1.0 else 0.75)
    target = min(target, cap)

    bid = float(max(min_bid, min(target, max_affordable)))
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

    # Alive opponents
    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive.append((opp_id, opp))

    # Baseline: ensure we can survive; bid more when supply is tighter or late game.
    # If we have low hp, bid aggressively.
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace (immediate reaction only)
    prev_bids = []
    for _, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        if prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    # If someone bid extremely high yesterday, they likely secure water; we should not match blindly.
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate how many water units are available relative to requirement
    # (used only to scale aggressiveness)
    # supply is between 15 and 25, so ratio is ~1.67 to 2.78
    supply_ratio = supply / float(WATER_REQ)

    # Tight supply -> more competition -> bid higher.
    # supply_ratio < 2 => supply < 18
    tight = supply_ratio < 2.0

    # Late game: increase bid to avoid running out.
    late = day >= 7

    # Opponent signals: Eric died with very low bid yesterday, so low bids may be non-threatening.
    # But strong survivors bid high; we infer a target around the upper-middle of yesterday bids.
    # Compute a conservative target bid level.
    if prev_bids:
        sorted_bids = sorted(prev_bids)
        # take median-ish
        mid_index = int(len(sorted_bids) // 2)
        median_prev_bid = float(sorted_bids[mid_index])
    else:
        median_prev_bid = 0.0

    # Target bid: slightly above median when tight/late or when our hp is low.
    # Otherwise, stay below highest to conserve budget.
    if hp <= 2 or no_water_days >= 2:
        aggressiveness = 1.0
    elif hp <= 4:
        aggressiveness = 0.75
    else:
        aggressiveness = 0.55

    if tight:
        aggressiveness += 0.15
    if late:
        aggressiveness += 0.15

    # Cap aggressiveness
    if aggressiveness > 1.0:
        aggressiveness = 1.0

    # Convert aggressiveness into bid fraction of DAILY_SALARY
    bid_cap = DAILY_SALARY * (0.25 + 0.75 * aggressiveness)

    # Use yesterday median as an anchor; aim for min(bid_cap, median + small increment)
    # to beat typical bidders without chasing outliers.
    target = median_prev_bid + (5.0 if tight else 2.0)

    # If highest_prev_bid is not too high, we may need to go closer; otherwise stay conservative.
    if highest_prev_bid > DAILY_SALARY * 1.2:
        # very aggressive market; still avoid maxing out
        target = min(target, highest_prev_bid - 8.0)
    else:
        target = min(target, highest_prev_bid - 5.0) if highest_prev_bid > 0 else target

    # Final bid: bounded by budget and bid_cap
    final_bid = min(budget, bid_cap, target)

    # Ensure non-negative
    if final_bid < 0.0:
        final_bid = 0.0

    # If our budget is extremely low, bid what we can.
    if budget <= DAILY_SALARY * 0.2:
        final_bid = min(budget, DAILY_SALARY * 0.25)

    return float(final_bid)
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
    day = day_context['day']

    # Alive opponents and their yesterday bids
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    yesterday_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and ('bid' in prev) and (prev.get('bid') is not None):
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Estimate how many water units are likely needed per day (supply is total units)
    # If supply is small, competition is higher; bid more.
    # Expected winners likely require at least 1 unit; we use a pressure factor.
    if supply <= float(WATER_REQ):
        pressure = 1.0
    else:
        pressure = (float(MAX_SUPPLY) - supply) / (float(MAX_SUPPLY) - float(MIN_SUPPLY) + 1e-9)
        pressure = max(0.0, min(1.0, pressure))

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Base bid target: mid-high when supply is tight.
    # Cindy's survival suggests she can pay; we try to beat her without matching her max.
    base = DAILY_SALARY * (0.45 + 0.35 * pressure)

    # React to yesterday's highest bid (if someone was aggressive, bid enough to contest)
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        # If someone bid very high, we contest but cap to preserve budget.
        if highest_prev >= DAILY_SALARY * 0.85:
            target = max(base, min(budget, highest_prev * 0.75))
        else:
            # If competition was moderate, slightly over base.
            target = max(base, min(budget, highest_prev + 2.0))
    else:
        target = base

    # Survival urgency: if low hp or accumulating no-water days, increase bid.
    if hp <= 2.5:
        target = max(target, DAILY_SALARY * 0.85)
    elif hp <= 4.0:
        target = max(target, DAILY_SALARY * 0.65)

    # If we've already gone without water several days, prioritize winning.
    if no_water_days >= 2:
        target = max(target, DAILY_SALARY * 0.7)

    # Budget safety cap: never bid more than we can afford.
    target = min(target, budget)

    # If budget is extremely low, just bid what we can.
    if budget <= 0.0:
        return 0.0

    # Ensure non-negative.
    if target < 0.0:
        target = 0.0

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

    # Alive opponents and yesterday bids
    alive_opps = [o for o in opponents_status.values() if o.get('alive', False)]
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Baseline: with supply 15-25, we can usually cover requirement if we win at least once.
    # Aim to bid enough to not be last, but not chase extreme bids.
    if supply <= float(WATER_REQ):
        # Very tight supply: bid higher to secure water.
        base = 0.75 * DAILY_SALARY
    else:
        # Moderate supply: bid mid.
        base = 0.55 * DAILY_SALARY

    max_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # If others were bidding very high yesterday, undercut slightly to win without overspending.
    # Use hp/no_water_days to decide urgency.
    my_hp = int(my_status['hp'])
    my_budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    urgency = 0
    if my_hp <= 2:
        urgency += 2
    elif my_hp <= 4:
        urgency += 1
    if no_water_days >= 2:
        urgency += 1

    # Aggression detector from yesterday
    if max_prev_bid >= 0.85 * DAILY_SALARY:
        # Others are in a high-pressure regime; bid closer to their level but still capped.
        # Undercut by a small amount.
        target = max_prev_bid - 5.0
        # If we're in danger, don't undercut too much.
        if urgency >= 2:
            target = max_prev_bid - 1.5
        bid = min(my_budget, max(base, target))
    else:
        # Not too aggressive yesterday: bid around baseline; increase if we're in danger.
        bid = base + 12.0 * urgency
        bid = min(my_budget, bid)

    # Safety caps: never bid more than what we can afford and avoid zero bids.
    if my_budget <= 0:
        return 0.0

    # Ensure at least a minimal competitive bid when we have budget.
    min_competitive = 0.25 * DAILY_SALARY
    if bid < min_competitive and my_budget >= min_competitive:
        bid = min_competitive

    # Final clamp
    if bid < 0:
        bid = 0.0
    if bid > my_budget:
        bid = my_budget
    return float(bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    budget = float(my_status['budget'])
    hp = float(my_status['hp'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opps:
        return float(min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace for immediate pressure signal
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
    second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else 0.0

    # Determine how many full WATER_REQ chunks supply can cover
    # Use int() to avoid float index issues.
    chunks = int(supply / float(WATER_REQ))

    # Base target: if others bid very high yesterday, we slightly undercut to conserve budget.
    # If my hp is low or I'm already on no-water days, I must secure water.
    need_security = (hp <= 2.5) or (no_water_days >= 1)

    # Supply-driven aggressiveness
    # With medium supply (15-25), chunks is typically 1 or 2.
    if chunks <= 1:
        supply_factor = 0.62
    else:
        supply_factor = 0.78

    # Estimate how costly it was to win yesterday.
    # If highest_prev_bid is huge, we don't match it; we bid around a fraction.
    if highest_prev_bid >= DAILY_SALARY * 1.6:  # very aggressive market
        market_factor = 0.72
    elif highest_prev_bid >= DAILY_SALARY * 0.9:
        market_factor = 0.82
    else:
        market_factor = 0.9

    if need_security:
        target = DAILY_SALARY * (0.95 * supply_factor * market_factor + 0.15)
    else:
        # Try to exploit undercut: bid above what likely clears when others overbid.
        # Use second_prev_bid to anchor; if it's unknown, fall back.
        anchor = second_prev_bid if second_prev_bid > 0 else highest_prev_bid
        # Undercut by a small margin relative to anchor.
        target = min(DAILY_SALARY * 1.25, max(DAILY_SALARY * 0.45, anchor * 0.55 + DAILY_SALARY * 0.25))
        target = target * supply_factor * market_factor

    # Clamp by budget and a reasonable cap
    target = float(min(budget, max(0.0, target)))

    # If budget is too low, still bid something to avoid starvation.
    if target < DAILY_SALARY * 0.15:
        target = float(min(budget, DAILY_SALARY * 0.2))

    return float(target)
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
    # Estimate how many water units are likely needed to survive remaining days.
    # We only act on immediate pressure from yesterday's trace.

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive'):
            alive_opps.append(o)

    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Read yesterday's bids from immediate previous_trace.
    prev_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace') or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Determine competitive pressure.
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_prev_bid = 0.0
    if len(prev_bids) >= 2:
        sorted_b = sorted(prev_bids, reverse=True)
        second_prev_bid = sorted_b[1]

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])

    # Supply-based urgency: higher supply reduces the need to overbid.
    # Convert supply into a coarse tier.
    supply_tier = 0
    if supply <= MIN_SUPPLY + 1e-9:
        supply_tier = 2  # tight
    elif supply < MAX_SUPPLY - 1e-9:
        supply_tier = 1  # medium
    else:
        supply_tier = 0  # ample

    # Base bid target.
    # If yesterday pressure was high (Cindy/Alex), we bid slightly above the likely runner-up.
    # Otherwise, bid around a fraction of daily salary.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Competitive day: try to secure water without draining budget.
        # If our HP is low, we must ensure allocation; bid closer to highest_prev_bid.
        if my_hp <= 2.0:
            target = highest_prev_bid + 2.0
        else:
            # bid above second-highest to win but not fully match highest
            target = max(highest_prev_bid * 0.92, second_prev_bid + 2.0)
    else:
        # Not extremely pressured: bid based on supply tier and our HP.
        if my_hp <= 2.0:
            target = DAILY_SALARY * (0.75 if supply_tier >= 1 else 0.6)
        else:
            target = DAILY_SALARY * (0.55 if supply_tier == 0 else (0.65 if supply_tier == 1 else 0.72))

    # Safety caps: don't bid more than budget, and avoid irrational overbids.
    # Also, if budget is too low, bid proportionally.
    if my_budget <= 0:
        return 0.0

    # Prevent spending beyond what is likely needed for remaining days.
    # We don't know remaining days exactly, but no_water_days indicates risk.
    no_water_days = int(my_status.get('no_water_days', 0) or 0)
    risk_multiplier = 1.0
    if no_water_days >= 2:
        risk_multiplier = 1.25
    elif no_water_days == 1:
        risk_multiplier = 1.1

    # Final target with risk and supply adjustments.
    target = target * risk_multiplier

    # Hard cap relative to daily salary and budget.
    hard_cap = DAILY_SALARY * (0.95 if my_hp <= 2.0 else 0.8)
    target = min(target, hard_cap)

    # If supply is tight, we slightly increase willingness.
    if supply_tier == 2:
        target = min(target * 1.05, hard_cap)

    bid = min(my_budget, target)
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

    supply = float(day_context['supply'])
    day = day_context['day']

    # If we are already in critical condition, prioritize survival.
    if my_status['hp'] is not None and my_status['hp'] <= 2:
        return min(float(my_status['budget']), DAILY_SALARY * 0.95)

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append(o)

    if not alive_opponents:
        return min(float(my_status['budget']), DAILY_SALARY * 0.4)

    # Read yesterday bids from previous_trace only.
    prev_bids = []
    for o in alive_opponents:
        prev = o.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            prev_bids.append(float(b))

    # Estimate competitive pressure from yesterday.
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else 0.0

    # Supply pressure: if supply is low, water is scarce; we should bid more.
    # Map supply to a [0,1] scarcity factor.
    if MAX_SUPPLY - MIN_SUPPLY <= 0:
        scarcity = 0.5
    else:
        scarcity = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)
        if scarcity < 0.0:
            scarcity = 0.0
        if scarcity > 1.0:
            scarcity = 1.0

    # Base bid: moderate, scaled by scarcity.
    base = DAILY_SALARY * (0.45 + 0.25 * scarcity)

    # If someone bid very high yesterday, they likely expect to secure water again.
    # We try to outbid just enough, but cap to avoid bankruptcy.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Cindy-like behavior: bid close to but slightly above likely threshold.
        target = min(highest_prev_bid, DAILY_SALARY * 1.0)
        # Add a small increment to beat them.
        bid = target + 5.0
    elif highest_prev_bid >= DAILY_SALARY * 0.65:
        # Eric-like: bid around the leader but not fully.
        bid = max(base, second_prev_bid + 8.0, highest_prev_bid * 0.92)
    else:
        # Low pressure: bid near base; still ensure we can win if needed.
        bid = base

    # If we have many no-water days, increase bid.
    no_water_days = float(my_status.get('no_water_days', 0.0) or 0.0)
    if no_water_days >= 2:
        bid *= 1.25
    if no_water_days >= 4:
        bid *= 1.45

    # Final clamp by budget.
    budget = float(my_status['budget'])
    if budget <= 0.0:
        return 0.0

    # Ensure bid is at least a small positive amount when budget allows.
    bid = float(bid)
    if bid < 1.0:
        bid = 1.0
    if bid > budget:
        bid = budget

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
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    if not alive_opponents:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Reaction to yesterday's pressure: use immediate previous_trace bids
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    prev_bids.append(float(b))
                except Exception:
                    pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Supply tightness heuristic: if supply is near minimum, water is scarce.
    # Aim to win more often when supply is low.
    scarcity = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        scarcity = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    # Core bid target: moderate base, escalate with low HP / long no-water streak / tight supply.
    # Exploit: Cindy/Eric used low bids and died; don't mirror their extreme low bids.
    base = DAILY_SALARY * (0.42 + 0.18 * scarcity)

    # If someone previously bid aggressively, slightly increase to avoid being outbid.
    # Alex survived with high bids; treat high previous bid as signal of stronger demand.
    if highest_prev_bid >= DAILY_SALARY * 0.75:
        base *= 1.12

    # Urgency adjustments
    if hp <= 2.0:
        base *= 1.45
    elif hp <= 4.0:
        base *= 1.20

    if no_water_days >= 2:
        base *= 1.25
    elif no_water_days == 1:
        base *= 1.10

    # Convert to final bid with budget cap. Also keep a floor to avoid always losing ties.
    bid = min(budget, base)

    # If budget is very small, still bid something nonzero when HP is critical.
    if bid <= 0.0:
        if hp <= 2.0:
            bid = min(budget, DAILY_SALARY * 0.05)
        else:
            bid = 0.0

    # Safety clamp
    bid = max(0.0, float(bid))
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
    day = day_context.get('day', 1)

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # If no opponents alive, conserve
    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from traces (immediate reaction)
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate required number of water units this day
    # Assume each unit is WATER_REQ; decide how many units are likely needed to keep HP stable.
    # Use supply to infer how many units the market can provide.
    supply_units = int(supply / float(WATER_REQ)) if WATER_REQ > 0 else 0
    # If supply is low, competition increases.
    low_supply = supply < (MIN_SUPPLY + MAX_SUPPLY) / 2.0

    # Base bid target: react to Cindy-like aggression (very high previous bids)
    # If someone previously bid very high, we avoid getting priced out by bidding enough to secure water
    # but not matching their peak unless my HP is critical.
    critical = (hp <= 2.0) or (no_water_days >= 2)
    safe = hp >= 6.0 and no_water_days <= 0

    # Determine aggressiveness from yesterday's highest bid
    # Thresholds tuned to yesterday: Cindy ~142.5, Alex ~92.8, David ~81.3, Eric ~21.3
    if highest_prev_bid >= DAILY_SALARY * 1.2:  # >=108
        if critical:
            target = DAILY_SALARY * 0.95
        elif safe:
            target = DAILY_SALARY * (0.55 if not low_supply else 0.7)
        else:
            target = DAILY_SALARY * (0.7 if not low_supply else 0.85)
    elif highest_prev_bid >= DAILY_SALARY * 0.8:  # >=72
        if critical:
            target = DAILY_SALARY * 0.85
        elif safe:
            target = DAILY_SALARY * (0.48 if not low_supply else 0.62)
        else:
            target = DAILY_SALARY * (0.62 if not low_supply else 0.78)
    else:
        # Opponents likely not spending much; bid enough to secure water
        if critical:
            target = DAILY_SALARY * 0.8
        elif safe:
            target = DAILY_SALARY * (0.4 if not low_supply else 0.55)
        else:
            target = DAILY_SALARY * (0.55 if not low_supply else 0.7)

    # If supply_units is 0, water is scarce; bid more aggressively
    if supply_units <= 0:
        target *= 1.15

    # Ensure we don't exceed budget
    target = float(target)
    bid = max(0.0, min(budget, target))

    # If budget is extremely low, still attempt minimal bid to avoid total starvation
    if budget < DAILY_SALARY * 0.2:
        bid = min(budget, DAILY_SALARY * 0.15)

    return bid
"""
