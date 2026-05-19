# ============================================================
# Experiment: exp_091
# Agent: Bob
# Source: exp_091
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

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return max(0, min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids (immediate reaction only)
    prev_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    max_prev_bid = max(prev_bids) if prev_bids else 0.0

    # If someone bid very high yesterday, they likely try to lock water again.
    # We respond with a moderate-to-high bid depending on our hp and budget.
    budget = float(my_status['budget'])
    hp = float(my_status['hp'])

    # Estimate how many units water we can realistically aim for.
    # In this game, bid is in currency; we use supply to decide urgency.
    # If supply is low, we need more water to avoid no-water days.
    scarcity = (supply <= (MIN_SUPPLY + MAX_SUPPLY) / 2.0)

    # Base target bid
    if max_prev_bid >= DAILY_SALARY * 0.85:
        # Opponent likely in high-pressure mode
        if hp <= 2.0 or scarcity:
            target = DAILY_SALARY * 0.95
        else:
            target = DAILY_SALARY * 0.65
    elif max_prev_bid >= DAILY_SALARY * 0.55:
        if hp <= 2.0:
            target = DAILY_SALARY * 0.85
        else:
            target = DAILY_SALARY * 0.55
    else:
        # No strong signal; bid to secure without overspending
        if hp <= 2.0 or scarcity:
            target = DAILY_SALARY * 0.6
        else:
            target = DAILY_SALARY * 0.45

    # If our budget is tight, scale down.
    # Also avoid bidding above budget.
    bid = min(budget, target)

    # Ensure non-negative
    if bid < 0:
        bid = 0.0

    # Small day-based jitter to break ties deterministically
    # (bounded and budget-safe)
    jitter = (day % 3) * 2.0
    bid = min(budget, bid + jitter)

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
    day = int(day_context['day'])

    # Collect yesterday bids from alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Base bid target from yesterday behavior
    if yesterday_bids:
        # Use a robust statistic to avoid extremes
        avg_bid = sum(yesterday_bids) / float(len(yesterday_bids))
        max_bid = max(yesterday_bids)
        # If others were bidding aggressively, we must not fall too far behind
        aggressiveness = 0.0
        if DAILY_SALARY > 0:
            aggressiveness = max_bid / float(DAILY_SALARY)

        # Supply pressure: higher supply should reduce required bid slightly
        # Normalize supply into [0,1]
        denom = float(MAX_SUPPLY - MIN_SUPPLY)
        if denom <= 0:
            supply_norm = 0.5
        else:
            supply_norm = (supply - float(MIN_SUPPLY)) / denom
        if supply_norm < 0.0:
            supply_norm = 0.0
        if supply_norm > 1.0:
            supply_norm = 1.0

        # Decide aggressiveness factor
        # If max_bid was near salary, bid near avg; else bid somewhat above avg.
        if aggressiveness >= 1.25:
            target = avg_bid + 2.0
        elif aggressiveness >= 0.95:
            target = avg_bid + 5.0
        else:
            target = avg_bid + 1.5

        # If supply is low, increase bid to secure water
        if supply_norm < 0.5:
            target += 6.0 * (0.5 - supply_norm)

    else:
        # No data: conservative baseline
        target = DAILY_SALARY * 0.55

    # HP/bad streak adjustments: if low HP or already starved, bid higher
    if hp <= 2.0:
        target = max(target, DAILY_SALARY * 0.9)
    elif hp <= 4.0:
        target = max(target, DAILY_SALARY * 0.75)

    if no_water_days >= 2:
        target = max(target, DAILY_SALARY * 0.7)

    # If we are doing well, avoid overspending
    if hp >= 8.5 and no_water_days == 0:
        target *= 0.9

    # Budget cap: never bid more than we can afford
    if budget <= 0:
        return 0.0

    # Also cap relative to salary to avoid runaway bids
    hard_cap = min(budget, DAILY_SALARY * 1.35)

    # Ensure non-negative
    if target < 0.0:
        target = 0.0

    # Final bid
    bid = min(target, hard_cap)
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for opp_id, st in opponents_status.items():
        if st.get('alive', False):
            alive_opps.append((opp_id, st))

    if not alive_opps:
        return float(min(budget, DAILY_SALARY * 0.4))

    # Read yesterday's bids from previous_trace for immediate reaction.
    yesterday_bids = []
    for opp_id, st in alive_opps:
        prev = st.get('previous_trace', {})
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                yesterday_bids.append(float(bid))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = sum(yesterday_bids) / float(len(yesterday_bids)) if yesterday_bids else 0.0

    # Estimate how many water units are likely needed to stay safe.
    # If supply is near MAX, competition may be lower; if near MIN, competition higher.
    supply_band = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)  # 0..1
    # When supply is low, bid more to avoid losing.
    low_supply_pressure = 1.0 - max(0.0, min(1.0, supply_band))

    # Baseline: target around 60-85% of daily salary depending on observed pressure.
    pressure_ratio = 0.0
    if DAILY_SALARY > 0:
        pressure_ratio = highest_prev_bid / float(DAILY_SALARY)

    # If opponents bid near/above salary, we must match to secure water.
    if pressure_ratio >= 1.6:
        base = DAILY_SALARY * (0.75 + 0.15 * low_supply_pressure)
    elif pressure_ratio >= 1.2:
        base = DAILY_SALARY * (0.65 + 0.12 * low_supply_pressure)
    else:
        base = DAILY_SALARY * (0.55 + 0.10 * low_supply_pressure)

    # If I'm close to danger (low hp or many no-water days), increase urgency.
    if hp <= 2:
        base *= 1.25
    elif hp <= 4:
        base *= 1.10

    if no_water_days >= 2:
        base *= 1.15

    # If budget is too low, cap aggressively.
    # Also avoid overspending if hp is healthy.
    if hp >= 7:
        base *= 0.85

    bid = float(min(budget, base))

    # Ensure non-negative and at least a small bid if budget allows.
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return min(my_status.get('budget', 0.0), DAILY_SALARY * 0.4)

    # Extract yesterday bids from previous_trace for immediate reaction
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Baseline from supply pressure: with higher supply, we can bid less and still secure.
    # With lower supply, bid more to prevent being outbid.
    supply_mid = 0.5 * (MIN_SUPPLY + MAX_SUPPLY)
    supply_factor = 0.95 if supply >= supply_mid else 1.08

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # If I'm already in danger, increase bid.
    danger_factor = 1.0
    if hp <= 2.0 or no_water_days >= 2:
        danger_factor = 1.25
    elif hp <= 4.0 or no_water_days == 1:
        danger_factor = 1.10

    # Use yesterday's max bid as an upper anchor (avoid Cindy-like overpay by not matching max).
    if prev_bids:
        max_prev = max(prev_bids)
        # If someone was bidding extremely high, we need to contest.
        if max_prev >= DAILY_SALARY * 0.85:
            target = DAILY_SALARY * 0.65 * supply_factor * danger_factor
            # Still cap relative to max_prev to avoid Cindy-style budget burn.
            target = min(target, max_prev * 0.85)
        else:
            # Moderate contention: bid enough to beat typical high bids but not the extreme.
            target = DAILY_SALARY * 0.55 * supply_factor * danger_factor
            # If max_prev is not too high, slightly nudge toward it.
            target = max(target, min(DAILY_SALARY * 0.65, max_prev * 0.75))
    else:
        target = DAILY_SALARY * 0.55 * supply_factor * danger_factor

    # Convert target into a bid that respects our budget.
    # Keep some budget for later days.
    reserve_ratio = 0.35 if day >= 7 else 0.25
    max_affordable = budget * (1.0 - reserve_ratio)
    if max_affordable < 0:
        max_affordable = 0.0

    bid = min(max_affordable, target)

    # Ensure non-negative and at least a minimal contest bid.
    if bid < 0:
        bid = 0.0
    min_contest = DAILY_SALARY * 0.35
    if bid < min_contest and budget >= min_contest:
        bid = min_contest

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

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append((oid, o))

    if not alive_opponents:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Yesterday pressure from immediate previous_trace
    prev_bids = []
    for oid, o in alive_opponents:
        prev = o.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    prev_bids.append(float(b))
                except Exception:
                    pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate urgency for us
    # If we've already gone without water for several days, bid more aggressively.
    urgency = 0
    if no_water_days >= 2:
        urgency += 1
    if no_water_days >= 3:
        urgency += 1
    if hp <= 2.0:
        urgency += 2

    # Supply scaling: higher supply reduces need to overbid; lower supply increases competition.
    supply_ratio = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Determine target bid.
    # If Cindy-like pressure existed yesterday (high highest bid), we slightly overtake.
    # Otherwise, bid moderately to secure water without burning budget.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        base = highest_prev_bid + 2.0
        # If we're healthy, we can afford to overtake with moderate margin.
        if hp > 3.0 and urgency <= 1:
            base = highest_prev_bid + 1.0
        # If we're in trouble, bid closer to our daily salary cap.
        if urgency >= 2:
            base = max(base, DAILY_SALARY * 0.9)
    else:
        # Moderate competition: bid around half salary, adjusted by supply.
        # Lower supply => bid higher.
        base = DAILY_SALARY * (0.45 + (1.0 - supply_ratio) * 0.25)
        # If we're very urgent, push upward.
        if urgency >= 2:
            base = DAILY_SALARY * 0.85

    # Convert base into a feasible bid: never exceed budget; also keep within a reasonable fraction of salary.
    max_reasonable = DAILY_SALARY * 1.1
    bid = min(budget, max_reasonable, base)

    # If bid is too low, still try to secure some water when supply is low.
    if supply <= float(MIN_SUPPLY) + 0.5 and bid < DAILY_SALARY * 0.4:
        bid = min(budget, DAILY_SALARY * 0.55)

    # Ensure non-negative
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
    day = day_context['day']

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append(o)

    # If no opponents are alive, bid conservatively.
    if not alive_opponents:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace for immediate reaction.
    prev_bids = []
    prev_hp_after = []
    for o in alive_opponents:
        prev = o.get('previous_trace', {}) or {}
        if prev.get('bid') is not None:
            prev_bids.append(float(prev['bid']))
            prev_hp_after.append(prev.get('hp_after', None))

    # Estimate how hard the market is pushing.
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev_bid
    else:
        highest_prev_bid = 0.0
        second_prev_bid = 0.0

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])

    # Supply-based target: when supply is moderate, strong agents likely overbid.
    # Convert supply to an approximate number of water units available.
    # (Indices are not used; still keep logic robust.)
    supply_ratio = (supply - MIN_SUPPLY) / max(1e-9, (MAX_SUPPLY - MIN_SUPPLY))
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # If we are in danger, prioritize survival: bid high enough to likely secure water.
    if my_hp <= 2.0:
        base = DAILY_SALARY * (0.9 + 0.1 * supply_ratio)
        return float(min(my_budget, base))

    # If yesterday saw very high bids, we should either match just above the second-highest
    # or hold slightly lower if my HP is comfortable.
    aggressive_threshold = DAILY_SALARY * 0.85  # 76.5
    if highest_prev_bid >= aggressive_threshold:
        # Attempt to outbid the likely winner without overspending.
        # If my HP is decent, bid around second-highest + small increment.
        increment = 2.0 + 3.0 * supply_ratio
        target = second_prev_bid + increment
        # Safety cap: don't exceed a fraction of budget.
        cap = DAILY_SALARY * (0.55 + 0.25 * supply_ratio)  # 49.5..76.5
        bid = min(target, cap)
        return float(min(my_budget, max(0.0, bid)))

    # Otherwise, bids were not extreme; bid enough to secure water but not to start a bidding war.
    # Use a supply-aware bid: higher supply -> slightly higher bid.
    # Ensure at least a minimal amount to avoid frequent no-water days.
    target = DAILY_SALARY * (0.45 + 0.25 * supply_ratio)  # 40.5..63
    # If my budget is low, scale down.
    bid = min(my_budget, target)
    return float(max(0.0, bid))
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

    # Identify alive opponents and extract yesterday bids
    alive_opps = []
    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    yesterday_bids.append(float(prev['bid']))
                except Exception:
                    pass

    # Budget safety
    budget = float(my_status['budget'])
    hp = int(my_status['hp'])

    # If no info, bid a conservative fraction
    if not alive_opps or not yesterday_bids:
        base = DAILY_SALARY * 0.55
        return max(0.0, min(budget, base))

    highest_prev_bid = max(yesterday_bids)
    second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid

    # Supply pressure heuristic: lower supply => more competition => bid higher
    # supply in [15,25], map to [0,1]
    t = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    # When t is low (supply low), we bid more
    supply_factor = 1.15 - 0.25 * t  # ~1.15 at 15, ~0.9 at 25

    # Opponent behavior exploitation:
    # Cindy likely used high bids; avoid paying that price.
    # If highest_prev_bid is very high (aggressive), we target around clearing between 2nd and 1st.
    # If my hp is low, I must secure water more aggressively.
    aggressive_threshold = DAILY_SALARY * 1.6  # 144

    if highest_prev_bid >= aggressive_threshold:
        # Target just above second-highest to beat most without overpaying
        target = (second_prev_bid + 2.0) * supply_factor
    else:
        # Otherwise target mid between highest and a baseline
        target = (0.6 * highest_prev_bid + 0.4 * (DAILY_SALARY * 0.55)) * supply_factor

    # HP urgency adjustment
    if hp <= 2:
        target *= 1.35
    elif hp == 3:
        target *= 1.15
    elif hp >= 7:
        target *= 0.9

    # Ensure we don't bid beyond reasonable fraction of budget
    # (prevents repeating others' overspending)
    max_reasonable = DAILY_SALARY * (0.95 if hp <= 3 else 0.7)
    target = min(target, max_reasonable)

    # Final clamp to budget
    bid = max(0.0, min(budget, target))

    # If budget is tiny, still bid something to avoid wasting the day
    if bid < 1e-6:
        return 0.0

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

    # Alive opponents and yesterday pressure
    alive_opps = []
    yesterday_bids = []
    yesterday_alive_count = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            yesterday_alive_count += 1
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {}) or {}
            if prev.get('bid') is not None:
                yesterday_bids.append(float(prev['bid']))

    # If no info, bid conservative
    if not alive_opps:
        return max(0.0, min(float(my_status['budget']), DAILY_SALARY * 0.5))

    # Determine how aggressive the field was yesterday
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    # Urgency based on hp and no-water streak
    urgency = 0.0
    if my_hp <= 2.0:
        urgency = 1.0
    elif my_hp <= 4.0:
        urgency = 0.7
    else:
        urgency = 0.4

    if my_no_water_days >= 2:
        urgency = max(urgency, 0.8)
    elif my_no_water_days >= 1:
        urgency = max(urgency, 0.6)

    # Supply affects how many units of water are available relative to our requirement
    # We don't know the exact mapping from bid->water, so we use supply as a proxy for competition.
    supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_factor = max(0.0, min(1.0, supply_factor))

    # If others were bidding very high yesterday, they likely continue to fight for survival.
    # We will slightly undercut the highest to avoid wasting budget, but still stay competitive.
    aggressive_threshold = DAILY_SALARY * 0.85

    # Base bid target
    if highest_prev_bid >= aggressive_threshold:
        # Undercut by a small amount; more urgent -> bid closer to highest
        undercut = 2.0 + 10.0 * (1.0 - urgency)
        target = highest_prev_bid - undercut
    else:
        # Field wasn't extremely aggressive: bid around mid, scaled by urgency and supply
        target = DAILY_SALARY * (0.45 + 0.35 * urgency) + 10.0 * supply_factor
        # If second-highest is meaningful, lean toward it to secure share
        if second_prev_bid > 0.0:
            target = max(target, second_prev_bid * (0.85 + 0.15 * urgency))

    # Clamp to budget and reasonable per-day spend
    max_reasonable = DAILY_SALARY * (0.95 if urgency >= 0.8 else 0.7)
    min_reasonable = 0.0

    target = max(min_reasonable, min(target, max_reasonable))
    target = min(target, my_budget)

    # If budget is very low, switch to survival-minimum behavior
    if my_budget <= DAILY_SALARY * 0.2:
        # Try to spend enough to avoid immediate death, but don't exceed budget
        target = min(my_budget, DAILY_SALARY * (0.35 + 0.4 * urgency))

    # Final guard
    if target < 0.0:
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    # Basic safety: if no budget, bid 0
    if my_status.get('budget', 0) <= 0:
        return 0

    supply = day_context.get('supply', 0)
    day = day_context.get('day', 1)

    hp = my_status.get('hp', 0)
    budget = my_status.get('budget', 0)

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        # If alone, try to secure water cheaply
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday bids as a proxy for today's aggressiveness
    yesterday_bids = []
    for opp_id, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how many days we can cover if we win water each day (approx)
    # Budget is in money; winning water costs bid, then you still earn salary.
    # We'll keep a conservative reserve.
    reserve_days = 3
    approx_daily_cost_cap = DAILY_SALARY * 0.7

    # Determine target bid based on pressure and our hp
    # If yesterday had very high bids, others likely compete; bid enough to avoid losing.
    pressure_threshold = DAILY_SALARY * 0.85

    # If my hp is low, prioritize winning now.
    if hp <= 2:
        base = DAILY_SALARY * 0.95
    elif hp <= 4:
        base = DAILY_SALARY * 0.75
    else:
        base = DAILY_SALARY * 0.55

    # Adjust with yesterday's highest bid
    if highest_prev_bid >= pressure_threshold:
        # Others were willing to pay near salary; match slightly below top to remain safe.
        target = min(base + 10.0, highest_prev_bid * 0.92)
    else:
        # If yesterday wasn't extreme, outbid moderately.
        target = max(base, highest_prev_bid * 0.6 + 5.0)

    # Budget-aware cap: don't spend more than we can reasonably sustain
    # across remaining episode (unknown exact total), use a conservative cap.
    cap = min(budget, approx_daily_cost_cap)
    bid = min(target, cap)

    # If supply is low, competition likely increases; nudge upward.
    try:
        if float(supply) <= float(MIN_SUPPLY) + 0.5:
            bid = min(budget, bid + 8.0)
    except Exception:
        pass

    # Ensure non-negative
    if bid < 0:
        bid = 0

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
    day = day_context.get('day', 0)

    # Determine how many full water units we can reasonably cover if supply is limited.
    # This is a heuristic; exact game mechanics are unknown.
    # For supply in [15,25], one unit (9) is always feasible.
    # We'll bid around a threshold that keeps us competitive without burning budget.

    # Alive opponents
    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive.append(opp)

    if not alive:
        return max(0.0, min(float(my_status['budget']), DAILY_SALARY * 0.4))

    # Use yesterday's immediate reaction: look at bids from previous_trace.
    prev_bids = []
    prev_pressures = []
    for opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        if prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass
        # Optional pressure proxy: low hp / many no-water days implies desperation.
        try:
            hp = float(opp.get('hp', 0))
            no_water_days = float(opp.get('no_water_days', 0))
            prev_pressures.append((hp, no_water_days))
        except Exception:
            prev_pressures.append((0.0, 0.0))

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    my_hp = float(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0))
    my_no_water_days = float(my_status.get('no_water_days', 0))

    # Base bid depends on our survival urgency.
    if my_hp <= 1 or my_no_water_days >= 2:
        urgency_factor = 0.92
    elif my_hp <= 3:
        urgency_factor = 0.78
    else:
        urgency_factor = 0.58

    # Competitive adjustment: if someone was bidding very high yesterday, we should not ignore it.
    # But we also avoid matching top bids exactly; we aim to slightly undercut.
    # Thresholds tuned to observed trace: Cindy high bids (~189-240), David moderate (~96), Eric low.
    if highest_prev_bid >= 200:
        # Cindy-like behavior: likely aggressive; bid near salary but cap by budget.
        target = max(DAILY_SALARY * 0.65, highest_prev_bid * 0.42)
    elif highest_prev_bid >= 120:
        target = max(DAILY_SALARY * 0.55, highest_prev_bid * 0.48)
    else:
        # If no one was aggressive, bid around moderate level.
        target = max(DAILY_SALARY * 0.5, avg_prev_bid * 0.85)

    # Supply heuristic: higher supply reduces need to overbid.
    # supply 15 -> more scarce; supply 25 -> less scarce.
    if supply <= float(MIN_SUPPLY):
        supply_factor = 1.08
    elif supply >= float(MAX_SUPPLY):
        supply_factor = 0.92
    else:
        # linear interpolation between 1.08 and 0.92
        supply_factor = 1.08 - (supply - float(MIN_SUPPLY)) * (1.08 - 0.92) / (float(MAX_SUPPLY) - float(MIN_SUPPLY))

    bid = target * urgency_factor * supply_factor

    # Final guardrails
    bid = max(0.0, bid)
    # Never exceed budget
    bid = min(bid, my_budget)

    # If budget is tiny, bid what we can (still try to be competitive).
    if my_budget <= 1.0:
        return my_budget

    # Keep a reasonable cap to avoid burning too much in medium scenario.
    # If we can afford it, aim below or around 0.9 salary.
    bid = min(bid, DAILY_SALARY * 0.9)

    return float(bid)
"""
