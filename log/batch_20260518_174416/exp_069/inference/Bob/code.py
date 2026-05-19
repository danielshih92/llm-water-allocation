# ============================================================
# Experiment: exp_069
# Agent: Bob
# Source: exp_069
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

    alive_opponents = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opponents:
        target = int(WATER_REQ)
        bid = min(my_status['budget'], max(0.0, target))
        bid = min(bid, DAILY_SALARY)
        return float(bid)

    # Immediate reaction from yesterday's trace only
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict) and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Baseline: aim to cover our requirement with some contest
    # If supply is low, increase bid to secure water.
    # If supply is high, slightly reduce bid to save budget.
    supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    # supply_norm in [0,1]; low supply => closer to 0
    urgency = 1.0 - max(0.0, min(1.0, supply_norm))

    # Survival pressure from our hp/no-water_days
    hp = float(my_status.get('hp', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))
    survival_pressure = 0.0
    if hp <= 2.0:
        survival_pressure += 0.6
    elif hp <= 4.0:
        survival_pressure += 0.3
    if no_water_days >= 2:
        survival_pressure += 0.4
    elif no_water_days >= 1:
        survival_pressure += 0.2

    # If any opponent bid extremely high yesterday, we assume aggressive contest.
    if prev_bids:
        highest_prev_bid = max(prev_bids)
    else:
        highest_prev_bid = 0.0

    aggressive_threshold = 0.85 * DAILY_SALARY
    if highest_prev_bid >= aggressive_threshold:
        # Defensive pivot: increase bid if we're at risk, otherwise match moderately.
        if survival_pressure >= 0.4:
            bid = 0.75 * DAILY_SALARY
        else:
            bid = min(0.6 * DAILY_SALARY, highest_prev_bid * 0.95)
    else:
        # Normal contest: bid around requirement plus urgency premium.
        # Ensure bid is at least requirement-ish but not wasteful.
        base = float(WATER_REQ)
        bid = base + (10.0 * urgency) + (20.0 * survival_pressure)
        # Keep within a reasonable fraction of daily salary.
        bid = min(bid, 0.75 * DAILY_SALARY)

    # Never bid more than budget; never negative.
    bid = max(0.0, float(bid))
    bid = min(bid, float(my_status['budget']))

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

    supply = float(day_context['supply'])
    day = day_context['day']

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday's bids from traces (immediate reaction only)
    prev_bids = []
    cindy_prev_bid = None
    alex_prev_bid = None
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                b = float(b)
            except Exception:
                b = None
        if b is not None:
            prev_bids.append(b)
        if oid == 'Cindy' and b is not None:
            cindy_prev_bid = b
        if oid == 'Alex' and b is not None:
            alex_prev_bid = b

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Base bid: aim to be competitive but not max.
    # With supply >= WATER_REQ we only need to ensure we don't get squeezed.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Convert supply to an approximate number of
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = day_context['supply']
    day = day_context['day']

    # Alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # If no one alive, bid modestly
    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Read yesterday bids from previous_trace
    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Pressure from opponents: high yesterday bids imply they expect to win water
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid
    else:
        highest_prev_bid = 0.0
        second_prev_bid = 0.0

    # Estimate how many
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

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Use only yesterday previous_trace to infer opponent pressure level.
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # Base bid from my urgency.
    # If I've already had consecutive no-water days or low hp, increase.
    urgency = 0.0
    if hp <= 2:
        urgency += 0.35
    if hp <= 3:
        urgency += 0.15
    if no_water_days >= 2:
        urgency += 0.2
    if no_water_days >= 3:
        urgency += 0.25

    # Estimate opponent aggressiveness: if someone previously bid very high, contest more.
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / float(len(yesterday_bids))
    else:
        highest_prev_bid = 0.0
        avg_prev_bid = 0.0

    # Eric collapsed with very low bids; treat low avg as sign others may still bid, but don't overreact.
    # Target: slightly above average-low pressure unless my hp is critical.
    target = DAILY_SALARY * (0.55 + urgency)

    # If high bidder pressure exists, nudge upward but cap by budget.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        target = max(target, avg_prev_bid * 0.9)
        target = max(target, highest_prev_bid * 0.65)
    else:
        # If no one was extremely aggressive, bid just above typical level.
        if avg_prev_bid > 0:
            target = max(target, avg_prev_bid * 0.75)

    # Supply-aware adjustment: when supply is tighter (near MIN_SUPPLY), contest a bit more.
    # supply in [15,25]
    tightness = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        tightness = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    target *= (1.0 + 0.15 * tightness)

    # Ensure we don't bid more than needed for survival; but since exact water allocation is unknown,
    # keep a practical cap.
    # Cap at 1.2 * DAILY_SALARY to reduce burn.
    target = min(target, DAILY_SALARY * 1.2)

    # If budget is low, scale down.
    if budget <= 0:
        return 0.0

    bid = min(budget, target)

    # Final safeguard: if my hp is extremely low, go aggressive within budget.
    if hp <= 1.0 and budget > 0:
        bid = min(budget, DAILY_SALARY * 0.95)

    # Return a float bid.
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

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return max(0.0, min(float(my_status.get('budget', 0.0)), DAILY_SALARY * 0.4))

    # Immediate reaction from yesterday's trace bids
    prev_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Supply pressure: near upper range, expect stronger competition.
    # Use a smooth threshold rather than exact equilibrium.
    supply_frac = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_frac = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    if supply_frac < 0.0:
        supply_frac = 0.0
    if supply_frac > 1.0:
        supply_frac = 1.0

    # If opponents previously bid very high, match a fraction to steal water.
    # Otherwise, bid enough to be competitive.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Competitors are likely in survival mode.
        if hp <= 2.0 or no_water_days >= 2:
            target = DAILY_SALARY * (0.85 + 0.1 * supply_frac)
        else:
            target = DAILY_SALARY * (0.55 + 0.25 * supply_frac)
    else:
        # Moderate competition.
        if hp <= 2.0 or no_water_days >= 2:
            target = DAILY_SALARY * (0.75 + 0.15 * supply_frac)
        else:
            # Slightly above baseline to beat overcautious bidders.
            target = DAILY_SALARY * (0.45 + 0.20 * supply_frac)

    # Ensure we don't exceed budget; also keep a small reserve late in episode.
    episode_days = int(day_context.get('episode_days', 10)) if 'episode_days' in day_context else 10
    # day_context only has supply/day, so we infer remaining pressure from day.
    # If day is near end, preserve less.
    try:
        remaining = max(0, int(10) - int(day))
    except Exception:
        remaining = 5

    reserve_factor = 0.25 if remaining <= 2 else 0.35 if remaining <= 4 else 0.45
    max_affordable = budget
    min_reserve = budget * reserve_factor

    bid = min(max_affordable, target)
    if bid < 0.0:
        bid = 0.0

    # If we can afford it while keeping reserve, bid a bit higher when supply is high.
    if budget - bid > min_reserve and supply_frac > 0.6:
        bid = min(budget, bid + DAILY_SALARY * 0.08)

    # If hp is critically low, override reserve.
    if hp <= 1.5:
        bid = min(budget, DAILY_SALARY * 0.95)

    # Final clamp
    if bid > budget:
        bid = budget
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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append((oid, o))

    if not alive_opponents:
        return float(min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace for immediate reaction
    yesterday_bids = []
    for oid, o in alive_opponents:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # Pressure estimate: use top-2 yesterday bids (Eric/Alex were high)
    top_bids = sorted(yesterday_bids, reverse=True)[:2]
    top_bid = top_bids[0] if len(top_bids) >= 1 else 0.0
    second_bid = top_bids[1] if len(top_bids) >= 2 else 0.0

    # Supply factor: higher supply reduces need to overbid
    # Convert to a simple 0..1 scale
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_scale = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_scale = 0.5
    if supply_scale < 0.0:
        supply_scale = 0.0
    if supply_scale > 1.0:
        supply_scale = 1.0

    # If we are near death or have accumulated no-water days, bid harder
    urgency = 0.0
    if hp <= 2:
        urgency = 1.0
    elif hp <= 4:
        urgency = 0.7
    elif no_water_days >= 2:
        urgency = 0.6
    else:
        urgency = 0.3

    # Target: beat the moderate bidder (likely David) without matching the top aggressors.
    # Use second_bid as a proxy for "not the absolute highest" pressure.
    # If top_bid is extremely high, we undercut by aiming slightly above second_bid.
    base_target = 0.0
    if second_bid > 0.0:
        base_target = second_bid + 2.0
    elif top_bid > 0.0:
        base_target = top_bid * 0.85
    else:
        base_target = DAILY_SALARY * (0.45 + 0.25 * urgency)

    # Adjust for supply: with more supply, lower bid; with less supply, raise slightly.
    # supply_scale=1 (high supply) => multiplier ~0.9; supply_scale=0 => ~1.1
    supply_multiplier = 1.1 - 0.2 * supply_scale

    # Final bid with urgency
    bid = base_target * supply_multiplier

    # Cap bid to avoid burning budget: never exceed 70% of budget unless very urgent
    budget_cap = budget * (0.7 if urgency < 1.0 else 0.95)
    bid = min(bid, budget_cap)

    # Ensure some minimum bid if we need water
    # If hp is low, ensure at least a meaningful fraction of DAILY_SALARY
    if urgency >= 0.7:
        bid = max(bid, DAILY_SALARY * 0.6)
    elif urgency >= 0.3:
        bid = max(bid, DAILY_SALARY * 0.35)

    # If budget is tiny, just bid whatever we can
    if bid > budget:
        bid = budget

    # If bid becomes negative due to weird inputs
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return min(my_status.get('budget', 0.0), DAILY_SALARY * 0.4)

    # Read yesterday bids from immediate previous_trace only
    prev_bids = []
    for opp_id, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            prev_bids.append((opp_id, float(b)))

    # Identify highest pressure opponent yesterday
    highest_prev_bid = None
    highest_prev_id = None
    for opp_id, b in prev_bids:
        if highest_prev_bid is None or b > highest_prev_bid:
            highest_prev_bid = b
            highest_prev_id = opp_id

    my_hp = my_status.get('hp', 0)
    my_budget = my_status.get('budget', 0.0)
    no_water_days = my_status.get('no_water_days', 0)

    # Estimate how many water units exist relative to our requirement (for bid aggressiveness)
    # supply is float; use int() only for indexing; here we just use comparisons.
    supply_units = supply / float(WATER_REQ)

    # Baseline: bid enough to compete but not burn budget.
    # If supply is tight (closer to 15), we bid more.
    tightness = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY + 1e-9)  # 0..1-ish
    base = DAILY_SALARY * (0.45 + 0.25 * tightness)  # ~40-65% salary

    # If an opponent previously bid very high, shade upward slightly to steal their intended allocation.
    # Cindy survived with high average bid in yesterday context; exploit likely continued aggression.
    if highest_prev_bid is not None:
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # High-pressure opponent: increase bid if we can afford and need water.
            need_boost = 1.0
            if my_hp <= 2 or no_water_days >= 2:
                need_boost = 1.25
            bid = base * need_boost + (highest_prev_bid - DAILY_SALARY * 0.85) * 0.15
        elif highest_prev_bid >= DAILY_SALARY * 0.6:
            bid = base + (highest_prev_bid - DAILY_SALARY * 0.6) * 0.10
        else:
            bid = base
    else:
        bid = base

    # If our hp is critical, prioritize survival.
    if my_hp <= 1:
        bid = max(bid, DAILY_SALARY * 0.95)
    elif my_hp <= 3 and no_water_days >= 1:
        bid = max(bid, DAILY_SALARY * 0.75)

    # Cap bid by what we can pay.
    bid = min(bid, my_budget)

    # Avoid bidding too low when supply is likely to be scarce.
    # Ensure at least a small fraction of salary.
    min_bid = DAILY_SALARY * (0.25 + 0.15 * tightness)
    bid = max(bid, min_bid if my_budget >= min_bid else my_budget)

    # Final clamp
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

    alive_opps = [o for o in opponents_status.values() if o.get('alive')]
    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    supply = float(day_context['supply'])
    day = day_context['day']

    # Extract yesterday bids for immediate pressure reaction
    prev_bids = []
    prev_hp_after = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev['bid']))
            prev_hp_after.append(float(prev.get('hp_after', opp.get('hp', 0))))

    # If we have no trace info, use conservative baseline
    if not prev_bids:
        if my_status['hp'] <= 2:
            return min(my_status['budget'], DAILY_SALARY * 0.9)
        return min(my_status['budget'], DAILY_SALARY * 0.55)

    highest_prev_bid = max(prev_bids)
    second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev_bid

    # Tight supply => more likely someone will fight; loosen when supply is abundant
    # supply is between 15 and 25; compare to 2*WATER_REQ=18 as a pivot
    tight = supply < (2.0 * WATER_REQ)

    # Decide bid aggressiveness
    # If someone already paid near our salary scale, we only need to slightly beat them when tight.
    # Otherwise, bid around the lower of (just above second-highest) and a cap tied to salary.
    if tight:
        # If yesterday's highest bid was very high, don't fully match; bid just above second-highest.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            target = second_prev_bid + 1.0
        else:
            target = highest_prev_bid + 1.0
    else:
        # Abundant supply: avoid bidding into arms race; bid near second-highest.
        target = min(highest_prev_bid, second_prev_bid + 0.5)

    # HP-aware adjustment: if we're healthy, be less aggressive; if low, increase.
    hp = float(my_status.get('hp', 0))
    if hp <= 2:
        cap = DAILY_SALARY * 0.95
        target = max(target, DAILY_SALARY * 0.75)
    elif hp <= 4:
        cap = DAILY_SALARY * 0.85
        target = max(target, DAILY_SALARY * 0.6)
    else:
        cap = DAILY_SALARY * 0.7

    # Ensure we don't exceed budget
    bid = min(float(my_status['budget']), min(cap, float(target)))

    # If budget is too low, still bid at least a minimal fraction to avoid wasting chance.
    # Minimal bid scales with need and supply tightness.
    min_bid = DAILY_SALARY * (0.25 if not tight else 0.35)
    if bid < min_bid:
        bid = min(float(my_status['budget']), min_bid)

    # Final sanity: non-negative
    if bid < 0:
        bid = 0.0
    return float(bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace for immediate reaction
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
    second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else 0.0

    # Estimate how competitive we need to be.
    # If someone previously bid near the daily salary ceiling, we assume they are willing to pay to secure water.
    # We undercut slightly unless our HP is critical.
    critical_hp = 3.0
    low_hp = hp <= critical_hp

    # Base target: aim around half salary normally, but react to high previous bids.
    # If highest_prev_bid is high, we bid to be competitive but not max.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        if low_hp:
            target = min(budget, DAILY_SALARY * 0.75)
        else:
            target = min(budget, max(DAILY_SALARY * 0.55, highest_prev_bid * 0.85))
    else:
        # If bids were moderate, bid slightly above the second-highest to secure allocation.
        if second_prev_bid > 0:
            target = max(DAILY_SALARY * 0.5, second_prev_bid + 1.0)
        else:
            target = DAILY_SALARY * 0.55

    # If we've already had no-water days, increase urgency.
    if no_water_days >= 2:
        target *= 1.15
    if no_water_days >= 3:
        target *= 1.25

    # If supply is tight relative to requirement, slightly increase.
    # (We only have current supply; higher supply reduces urgency.)
    # supply in [15,25], WATER_REQ=9 => urgency highest when supply is 15.
    if supply <= 16.0:
        target *= 1.08
    elif supply >= 22.0:
        target *= 0.95

    # Final clamp to budget and non-negative.
    bid = max(0.0, min(float(budget), float(target)))

    # Avoid bidding tiny amounts late if we are at risk.
    if day >= 7 and low_hp and bid < DAILY_SALARY * 0.3:
        bid = min(float(budget), DAILY_SALARY * 0.45)

    return float(bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday bids from previous_trace only (immediate reaction)
    prev_bids = []
    prev_bid_by_opp = {}
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                bval = float(b)
                prev_bids.append(bval)
                prev_bid_by_opp[oid] = bval
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_prev_bid = 0.0
    if len(prev_bids) >= 2:
        sorted_bids = sorted(prev_bids, reverse=True)
        second_prev_bid = sorted_bids[1]

    # Estimate how many water units are likely needed to avoid death pressure.
    # We don't know exact auction mechanics; we bid in proportion to urgency.
    urgency = 0.0
    if hp <= 2:
        urgency = 1.0
    elif hp <= 4:
        urgency = 0.7
    elif hp <= 6:
        urgency = 0.4
    else:
        urgency = 0.25

    # If we've already had no water days, increase urgency.
    if no_water_days >= 2:
        urgency = max(urgency, 0.9)
    elif no_water_days == 1:
        urgency = max(urgency, 0.55)

    # Supply pressure: lower supply means we should bid more to secure scarce water.
    supply_norm = (supply - float(MIN_SUPPLY)) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    # When supply is low (supply_norm small), scarcity high.
    scarcity = 1.0 - max(0.0, min(1.0, supply_norm))

    # Base bid target: try to slightly outbid the leader from yesterday if they were aggressive.
    # Use a small increment to avoid overpaying.
    aggressive_threshold = DAILY_SALARY * 0.85

    if highest_prev_bid >= aggressive_threshold:
        # If someone was already spending near daily salary, we match/beat but only if we are not in immediate danger.
        if hp > 3:
            target = highest_prev_bid + 3.0
        else:
            target = highest_prev_bid + 8.0
    else:
        # Otherwise, bid around a scarcity-adjusted fraction of daily salary.
        # Aim to beat mediocre bids without chasing the top aggressively.
        target = DAILY_SALARY * (0.45 + 0.35 * scarcity + 0.25 * urgency)

        # If yesterday had a non-trivial leader, bias upward slightly toward it.
        if highest_prev_bid > 0:
            target = max(target, min(highest_prev_bid + 2.0, highest_prev_bid * 1.08))

    # Safety cap: never exceed budget.
    # Also avoid bidding too high relative to daily salary unless urgency is high.
    max_reasonable = DAILY_SALARY * (0.95 if urgency >= 0.8 else 0.75)
    target = min(target, max_reasonable)

    # Final bid
    bid = min(budget, max(0.0, float(target)))

    # If we are very low HP or already missing water, ensure we bid close to daily salary.
    if hp <= 2 or no_water_days >= 2:
        bid = min(budget, DAILY_SALARY * 0.95)

    return float(bid)
"""
