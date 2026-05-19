# ============================================================
# Experiment: exp_074
# Agent: Bob
# Source: exp_074
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context['supply'])
    day = day_context['day']

    # Alive opponents
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    # If no opponents, bid enough to meet requirement without overspending
    if not alive_opps:
        return min(float(my_status['budget']), DAILY_SALARY * 0.35)

    # Read yesterday bids from previous_trace
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Determine pressure level
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = 0.0
    if len(yesterday_bids) >= 2:
        s = sorted(yesterday_bids, reverse=True)
        second_prev_bid = float(s[1])

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    no_water_days = float(my_status['no_water_days'])

    # Estimate how many days of water we can afford if we consistently win at/near requirement.
    # This is a rough heuristic to avoid running out.
    # budget per unit is abstract; we mainly use it as a cap.
    budget_cap = my_budget

    # If we are already in trouble, prioritize survival: bid aggressively.
    if my_hp <= 2 or no_water_days >= 1:
        bid = DAILY_SALARY * 0.9
        return min(budget_cap, bid)

    # If opponents were highly aggressive yesterday, match/just exceed to prevent them from outbidding us.
    aggressive_threshold = DAILY_SALARY * 0.85
    if highest_prev_bid >= aggressive_threshold:
        # Stay cost-effective: bid slightly above the likely leader.
        # Use second_prev_bid as a floor to avoid overreacting to a single spike.
        target = max(highest_prev_bid + 1.5, second_prev_bid + 2.0)
        # Still keep within a reasonable fraction of salary.
        bid = min(target, DAILY_SALARY * 0.75)
        return min(budget_cap, bid)

    # Otherwise, bid moderate: enough to compete but preserve budget.
    # We also scale with supply: lower supply -> higher bid.
    # Note: supply is in [15,25].
    supply_norm = (supply - float(MIN_SUPPLY)) / (float(MAX_SUPPLY - MIN_SUPPLY))
    # supply_norm: 0 at MIN_SUPPLY, 1 at MAX_SUPPLY
    scarcity_factor = 1.0 - max(0.0, min(1.0, supply_norm))

    base = DAILY_SALARY * 0.5
    bid = base + (DAILY_SALARY * 0.25) * scarcity_factor

    # If we have a budget constraint, cap it.
    return min(budget_cap, bid)
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

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday bids from immediate previous_trace only
    prev_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Pressure estimate: if others bid near/above salary, they likely secure water aggressively.
    aggressive_threshold = DAILY_SALARY * 0.85  # 76.5

    # Base strategy: if we are low HP or have accumulated no-water days, bid higher.
    # If others were aggressive yesterday, slightly overbid to secure.
    if hp <= 2.0 or no_water_days >= 2:
        target = max(DAILY_SALARY * 0.85, highest_prev_bid * 1.02)
    elif highest_prev_bid >= aggressive_threshold:
        # Healthy but likely contested: bid enough to not lose.
        target = max(DAILY_SALARY * 0.65, highest_prev_bid * 0.98)
    else:
        # Less contested: conserve budget.
        target = max(DAILY_SALARY * 0.45, highest_prev_bid * 0.9)

    # Supply-aware cap: when supply is tight, we should be more competitive.
    # supply range: 15..25; map to a multiplier.
    if supply <= MIN_SUPPLY:
        mult = 1.10
    elif supply >= MAX_SUPPLY:
        mult = 0.95
    else:
        # linear interpolation between 1.10 at 15 and 0.95 at 25
        mult = 1.10 - (float(supply) - float(MIN_SUPPLY)) * (1.10 - 0.95) / (float(MAX_SUPPLY) - float(MIN_SUPPLY))

    target *= mult

    # Hard budget/safety limits: don't overspend early; keep some reserve.
    # Reserve more when hp is good.
    if hp >= 6.0:
        reserve_frac = 0.25
    elif hp >= 3.0:
        reserve_frac = 0.15
    else:
        reserve_frac = 0.05

    max_affordable = max(0.0, budget * (1.0 - reserve_frac))
    bid = min(max_affordable, target)

    # Ensure non-negative and at least some minimal bid if budget allows.
    if bid < 0.0:
        bid = 0.0
    if bid == 0.0 and budget > 0.0:
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # If no opponents, conserve
    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Read yesterday bids from previous_trace
    prev_bids = []
    prev_hp_after = []
    for o in alive_opps:
        pt = o.get('previous_trace', {}) or {}
        if pt and pt.get('bid') is not None:
            prev_bids.append(float(pt.get('bid', 0.0)))
            prev_hp_after.append(int(pt.get('hp_after', 0)))

    # Determine a target bid based on yesterday's observed aggressiveness
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    median_prev_bid = 0.0
    if prev_bids:
        s = sorted(prev_bids)
        mid = len(s) // 2
        median_prev_bid = float(s[mid])

    # Supply pressure: when supply is scarce, competition likely increases
    supply_frac = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    scarcity = 1.0 - max(0.0, min(1.0, supply_frac))

    # If my HP is low, I must secure water more reliably
    my_hp = int(my_status['hp'])
    my_budget = float(my_status['budget'])

    # Base aggressiveness
    if my_hp <= 2:
        base = DAILY_SALARY * (0.85 + 0.1 * scarcity)
    elif my_hp <= 4:
        base = DAILY_SALARY * (0.65 + 0.08 * scarcity)
    else:
        base = DAILY_SALARY * (0.55 + 0.06 * scarcity)

    # If an opponent was extremely aggressive yesterday, try to outbid slightly
    # Cindy had high bids and survived; mimic a controlled overtake, not a full chase.
    if highest_prev_bid >= DAILY_SALARY * 2.0:
        target = min(my_budget, max(base, highest_prev_bid * 0.95 + 3.0))
    elif highest_prev_bid >= DAILY_SALARY * 1.4:
        target = min(my_budget, max(base, median_prev_bid * 0.95 + 2.0))
    else:
        # If overall bids were modest, bid around base but nudge above median
        target = min(my_budget, max(base, median_prev_bid * 0.85 + 1.5))

    # Ensure we don't bid so high we risk bankruptcy: keep within a fraction of budget
    # (still enough to win when needed)
    max_reasonable = my_budget * (0.55 if my_hp > 3 else 0.85)
    target = min(target, max_reasonable)

    # If my budget is very low, just spend what we can
    if my_budget <= DAILY_SALARY * 0.2:
        return my_budget

    # Final clamp
    if target < 0:
        target = 0.0
    return float(target)
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

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        try:
            if o.get('alive', False):
                alive_opps.append((oid, o))
        except Exception:
            continue

    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Yesterday trace reaction
    prev_bids = []
    prev_hp_after = []
    for _, o in alive_opps:
        pt = o.get('previous_trace', {}) or {}
        b = pt.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
                prev_hp_after.append(int(pt.get('hp_after', 0)))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = sum(prev_bids) / float(len(prev_bids)) if prev_bids else 0.0

    # Supply pressure: fewer total units -> more value per unit -> bid higher
    # Normalize supply into [0,1]
    if MAX_SUPPLY > MIN_SUPPLY:
        s_norm = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    else:
        s_norm = 0.5
    s_norm = max(0.0, min(1.0, s_norm))

    # Base bid target
    # If someone previously bid near/above salary, we must contest more.
    pressure = 0.0
    if highest_prev_bid > 0:
        pressure = min(1.0, highest_prev_bid / (DAILY_SALARY * 1.25))

    # If my HP is low, avoid overbidding; if HP is high, contest more.
    hp_factor = 0.6
    if my_hp >= 8:
        hp_factor = 1.0
    elif my_hp >= 5:
        hp_factor = 0.85
    elif my_hp >= 3:
        hp_factor = 0.7
    else:
        hp_factor = 0.45

    # If I have no_water_days high, I need water sooner -> bid up.
    urgency = 0.0
    if my_no_water_days >= 3:
        urgency = 1.0
    elif my_no_water_days == 2:
        urgency = 0.7
    elif my_no_water_days == 1:
        urgency = 0.4
    else:
        urgency = 0.2

    # Construct bid cap and target
    # Aim slightly above average, but below highest_prev_bid unless pressure is extreme.
    target = avg_prev_bid * (0.85 + 0.35 * s_norm) + (highest_prev_bid - avg_prev_bid) * (0.25 + 0.35 * pressure)

    # If pressure very high, try to just beat the leader from yesterday.
    if highest_prev_bid >= DAILY_SALARY * 1.8:
        target = highest_prev_bid + 5.0

    # Scale by hp and urgency
    target = target * hp_factor * (0.75 + 0.35 * urgency)

    # Keep within sensible bounds relative to salary and budget
    # Lower bound: ensure some chance to win when supply is high.
    min_bid = DAILY_SALARY * (0.35 + 0.35 * s_norm)
    # Upper bound: don't exceed budget and avoid reckless spending.
    max_bid = min(my_budget, DAILY_SALARY * (1.25 + 0.6 * s_norm) )

    bid = max(min_bid * (0.75 if my_hp <= 2 else 1.0), target)
    bid = min(bid, max_bid)

    # If budget is tiny, just spend what we can.
    if my_budget <= 5.0:
        return max(0.0, my_budget)

    # Final safety clamp
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

    my_hp = int(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive'):
            alive_opps.append((oid, o))

    if not alive_opps:
        return min(my_budget, DAILY_SALARY * 0.4)

    yesterday_bids = []
    yesterday_hp_after = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace') or {}
        if prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass
        try:
            if prev.get('hp_after') is not None:
                yesterday_hp_after.append(int(prev.get('hp_after')))
        except Exception:
            pass

    # Base target: around typical yesterday bids, but avoid overpaying.
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        mean_prev = sum(yesterday_bids) / float(len(yesterday_bids))
    else:
        max_prev = 0.0
        mean_prev = DAILY_SALARY * 0.6

    # Supply pressure: when supply is tight, increase bid.
    # Convert supply to an approximate scarcity factor.
    scarcity = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        scarcity = (float(MAX_SUPPLY) - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    # If I'm low hp or have been without water, bid more.
    low_hp = 1 if my_hp <= 2 else 0
    moderate_hp = 1 if my_hp == 3 else 0
    urgency = 0.0
    if my_no_water_days >= 2:
        urgency = 0.25
    if my_no_water_days >= 3:
        urgency = 0.45

    # Decide cap and aggressiveness based on yesterday's max.
    # If others were extremely aggressive, we slightly overbid; otherwise we undercut/meet.
    if max_prev >= DAILY_SALARY * 1.45:
        aggressiveness = 0.18
    elif max_prev >= DAILY_SALARY * 1.25:
        aggressiveness = 0.10
    else:
        aggressiveness = 0.06

    # Target bid formula.
    target = mean_prev * (1.0 + aggressiveness) + (DAILY_SALARY * 0.15) * scarcity

    # Raise for low hp / urgency.
    if low_hp:
        target = max(target, DAILY_SALARY * 0.9)
    elif moderate_hp:
        target = max(target, DAILY_SALARY * 0.7)

    if urgency > 0.0:
        target = target * (1.0 + urgency)

    # Ensure we don't exceed a reasonable fraction of budget.
    # If budget is very low, spend enough to avoid immediate death but not all.
    if my_budget <= DAILY_SALARY * 0.6:
        cap_frac = 0.85
    elif my_budget <= DAILY_SALARY * 1.2:
        cap_frac = 0.65
    else:
        cap_frac = 0.55

    bid = min(my_budget * cap_frac, target)

    # Safety floor: avoid bidding too tiny when supply is scarce.
    min_bid = DAILY_SALARY * (0.35 + 0.25 * scarcity)
    bid = max(bid, min_bid if my_hp > 0 else 0.0)

    # Final clamp to non-negative.
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

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Immediate reaction to yesterday's visible bids
    prev_bids = []
    prev_hp_after = []
    prev_budgets_after = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            prev_bids.append(float(bid))
            prev_hp_after.append(float(prev.get('hp_after', 0.0)))
            prev_budgets_after.append(float(prev.get('budget_after', 0.0)))

    if not prev_bids:
        # No signal; bid based on our pressure
        pressure = 0.0
        if no_water_days > 0:
            pressure += 0.35
        if hp <= 2:
            pressure += 0.6
        target = DAILY_SALARY * (0.45 + pressure)
        return max(0.0, min(budget, target))

    highest_prev_bid = max(prev_bids)
    avg_prev_bid = sum(prev_bids) / float(len(prev_bids))

    # Identify who likely over/underbid: dying quickly with low bid implies others can clear cheaply.
    # We use the pattern: if many opponents had low bids and still survived, bid lower.
    low_bid_ratio = 0.0
    cnt_low = 0
    for b in prev_bids:
        if b <= DAILY_SALARY * 0.7:
            cnt_low += 1
    low_bid_ratio = cnt_low / float(len(prev_bids))

    # Supply affects how many units are available; with higher supply, we can bid less.
    supply_norm = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    # supply_norm in [0,1] ideally
    if supply_norm < 0.0:
        supply_norm = 0.0
    if supply_norm > 1.0:
        supply_norm = 1.0

    # Our pressure
    pressure = 0.0
    if no_water_days >= 1:
        pressure += 0.25
    if no_water_days >= 2:
        pressure += 0.25
    if hp <= 2:
        pressure += 0.6
    elif hp <= 4:
        pressure += 0.25

    # Strategy:
    # - If yesterday's highest bid was very high, assume a bidding war; bid to clear but cap spending.
    # - If low bids were common, we can undercut.
    war_signal = 0.0
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        war_signal = 1.0
    elif highest_prev_bid >= DAILY_SALARY * 0.65:
        war_signal = 0.6

    # Base bid around a fraction of highest/average
    if war_signal >= 0.9:
        target = min(highest_prev_bid * 0.85 + 2.0, DAILY_SALARY * 0.95)
    elif war_signal >= 0.6:
        target = min(max(avg_prev_bid * 0.85, DAILY_SALARY * 0.6), DAILY_SALARY * 0.85)
    else:
        # Undercut if low bids were common
        if low_bid_ratio >= 0.5:
            target = max(DAILY_SALARY * 0.45, avg_prev_bid * 0.7)
        else:
            target = max(DAILY_SALARY * 0.55, avg_prev_bid * 0.8)

    # Adjust for our pressure and supply
    target *= (1.0 + pressure)
    target *= (1.0 - 0.2 * supply_norm)  # bid slightly less when supply is higher

    # Hard caps to avoid going broke like David did
    # If our budget is low, spend enough to survive this day but don't exceed 95% of budget.
    if budget <= 0.0:
        return 0.0

    max_spend = budget * 0.95
    # Also avoid extreme bids beyond a practical cap relative to supply
    practical_cap = DAILY_SALARY * (0.9 if war_signal > 0.5 else 0.75)
    max_spend = min(max_spend, practical_cap)

    bid = max(0.0, min(target, max_spend))

    # If we are extremely pressured, ensure we bid at least a floor
    if pressure >= 0.6:
        floor = DAILY_SALARY * 0.75
        bid = max(bid, min(budget * 0.95, floor))

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

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for k, o in opponents_status.items():
        if o is not None and o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Extract yesterday bids from immediate previous_trace only
    prev_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    prev_bids.append(float(b))
                except Exception:
                    pass

    # Estimate competitive pressure from yesterday
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    median_prev_bid = 0.0
    if prev_bids:
        srt = sorted(prev_bids)
        mid = len(srt) // 2
        median_prev_bid = float(srt[mid])

    # Supply tightness: fewer units favors higher bids
    # target_units ~ supply/WATER_REQ but clamp to [1,3]
    approx_units = int(max(1.0, min(3.0, supply / float(WATER_REQ))))
    tightness = 1.0
    if supply >= 22.0:
        tightness = 0.75
    elif supply >= 19.0:
        tightness = 1.0
    else:
        tightness = 1.15

    # My urgency: if low hp or building no-water streak, bid more
    urgency = 1.0
    if hp <= 2.0 or no_water_days >= 2:
        urgency = 1.35
    elif hp <= 4.0 or no_water_days >= 1:
        urgency = 1.15

    # Anchor around yesterday effective bids (~108-114 seen), but only overbid slightly
    # If we were already safe, don't overpay.
    base = max(DAILY_SALARY * 0.55, median_prev_bid)

    # If yesterday someone bid very high, we need to defend more aggressively today.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        target = base * 1.05 * tightness * urgency
    else:
        target = base * 0.95 * tightness * urgency

    # Keep within budget and avoid irrationally high bids
    # Also, if my hp is high, cap bid lower.
    if hp >= 7.0:
        target = min(target, DAILY_SALARY * 0.7)
    elif hp >= 5.0:
        target = min(target, DAILY_SALARY * 0.85)

    # If budget is low, scale down proportionally
    if budget <= DAILY_SALARY * 0.6:
        target = min(target, budget)

    # Final clamp
    target = max(1.0, min(budget, target))
    return float(target)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    alive_opps = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Immediate reaction from yesterday traces only
    prev_bids = []
    prev_pressures = []  # (bid, hp_after)
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                b = float(bid)
            except Exception:
                continue
            prev_bids.append(b)
            hp_after = prev.get('hp_after', None)
            if hp_after is not None:
                try:
                    prev_pressures.append((b, float(hp_after)))
                except Exception:
                    pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Supply pressure: lower supply means more competition.
    # supply is expected in [15,25]
    supply_ratio = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    # competition_factor: 1.0 at low supply, 0.0 at high supply
    competition_factor = 1.0 - max(0.0, min(1.0, supply_ratio))

    # If someone was extremely aggressive yesterday, bid enough to not lose allocation.
    # Cindy yesterday shows high bids; Alex moderate.
    if highest_prev_bid >= DAILY_SALARY * 1.35:
        base = DAILY_SALARY * (0.65 + 0.25 * competition_factor)
    elif highest_prev_bid >= DAILY_SALARY * 0.90:
        base = DAILY_SALARY * (0.55 + 0.20 * competition_factor)
    else:
        base = DAILY_SALARY * (0.45 + 0.15 * competition_factor)

    # Health/budget risk adjustment
    if my_hp <= 2.0:
        base *= 1.25
    elif my_hp <= 4.0:
        base *= 1.10

    # If we've already gone without water, prioritize survival.
    if no_water_days >= 2:
        base *= 1.20

    # Slightly outbid the previous highest when competition is high.
    if competition_factor >= 0.6 and prev_bids:
        base = max(base, highest_prev_bid * 0.95)

    # Ensure we don't exceed budget.
    bid = min(my_budget, base)

    # Keep bids within a reasonable band relative to budget.
    # If budget is tiny, just bid whatever we can.
    if my_budget <= DAILY_SALARY * 0.3:
        return my_budget

    # Final clamp
    min_bid = min(my_budget, DAILY_SALARY * 0.25)
    max_bid = min(my_budget, DAILY_SALARY * 0.95)
    if bid < min_bid:
        bid = min_bid
    if bid > max_bid:
        bid = max_bid

    return float(bid)
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

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from immediate previous_trace only
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    yesterday_bids.append(float(b))
                except Exception:
                    pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else 0.0

    # Supply pressure: medium means we usually don't need to chase the very top bidder
    # Estimate how many water units could be contested.
    # Use explicit int() for any indexing; here we don't index.
    supply_level = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5

    # If we are in danger (low hp or many no-water days), bid aggressively to avoid death.
    if my_hp <= 2 or my_no_water_days >= 2:
        bid = DAILY_SALARY * 0.9
        return max(0.0, min(my_budget, bid))

    # If someone previously overbid heavily, we can slightly undercut rather than match.
    # Cindy showed high bids with still-low hp; likely she continues to bid for survival.
    if highest_prev_bid >= DAILY_SALARY * 1.5:
        # Undercut by a small margin; keep it moderate.
        target = min(highest_prev_bid - 2.0, DAILY_SALARY * (0.7 + 0.2 * supply_level))
        return max(0.0, min(my_budget, target))

    # Otherwise, bid around a mid level: enough to beat low bidders, not enough to waste budget.
    # Use second-highest to avoid always losing to the top bidder.
    base = DAILY_SALARY * (0.45 + 0.2 * supply_level)
    # If we have evidence of a strong competitor but not extreme, nudge above second-highest.
    if second_prev_bid > 0:
        target = max(base, second_prev_bid + 1.0)
    else:
        target = base

    # Keep within budget and avoid bidding above a reasonable cap.
    cap = DAILY_SALARY * (0.85 if my_hp <= 4 else 0.65)
    bid = min(target, cap)
    return max(0.0, min(my_budget, bid))
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

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace only (immediate reaction)
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

    # Estimate how many water units supply might support (for intuition only)
    # Ensure integer indexing safety by explicit int() if used.
    est_units = int(supply / WATER_REQ) if WATER_REQ > 0 else 0

    # Base bid: enough to avoid being outbid by low bidders, but not matching Cindy-like aggression.
    # Use thresholds tied to DAILY_SALARY.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Someone was very aggressive yesterday.
        if hp <= 2.0 or no_water_days >= 2:
            target = DAILY_SALARY * 0.95
        else:
            target = DAILY_SALARY * 0.30
    else:
        # No extreme aggression yesterday: stay moderate.
        if hp <= 2.0 or no_water_days >= 2:
            target = DAILY_SALARY * 0.85
        else:
            # Slightly above half salary to beat typical low bids, but capped.
            target = max(DAILY_SALARY * 0.50, highest_prev_bid + 6.0)

    # Supply-aware adjustment: when supply is higher, we can bid less aggressively.
    # Normalize supply into [0,1]
    if MAX_SUPPLY > MIN_SUPPLY:
        norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        norm = 0.5
    norm = 0.0 if norm < 0.0 else (1.0 if norm > 1.0 else norm)

    # Higher supply -> reduce bid slightly; lower supply -> increase slightly.
    target = target * (1.12 - 0.24 * norm)

    # Hard caps to prevent overspending.
    # If our budget is low, bid proportionally to preserve future days.
    safety_fraction = 0.45 if hp > 5.0 else 0.65
    max_affordable = budget * safety_fraction

    # Also cap at a fraction of daily salary to avoid runaway bids.
    cap = DAILY_SALARY * 0.98
    bid = min(target, max_affordable, cap, budget)

    # If extremely low budget, bid whatever we can to secure at least some chance.
    if budget <= 0.0:
        return 0.0

    # Ensure non-negative.
    if bid < 0.0:
        bid = 0.0

    return float(bid)
"""
