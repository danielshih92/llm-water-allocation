# ============================================================
# Experiment: exp_045
# Agent: Bob
# Source: exp_045
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

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    budget = float(my_status.get('budget', 0.0))
    hp = float(my_status.get('hp', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive = []
    for op in opponents_status.values():
        if op.get('alive', False):
            alive.append(op)

    if not alive:
        return float(min(budget, DAILY_SALARY * 0.4))

    prev_bids = []
    for op in alive:
        prev = op.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Estimate how many days of water we might need to stay safe
    # (Heuristic: if we've already gone without water, increase urgency.)
    urgency = 0.0
    if no_water_days >= 2:
        urgency = 0.25
    elif no_water_days == 1:
        urgency = 0.12

    # If opponent(s) were aggressive yesterday, we bid to contest.
    if prev_bids:
        max_prev_bid = max(prev_bids)
        min_prev_bid = min(prev_bids)

        # Thresholds tied to our daily salary.
        high_aggr = DAILY_SALARY * 0.85
        mid_aggr = DAILY_SALARY * 0.65

        if max_prev_bid >= high_aggr:
            # Contest but don't overpay unless low hp.
            if hp > 3:
                target = DAILY_SALARY * (0.30 + urgency)
            else:
                target = DAILY_SALARY * (0.85 + urgency)
            # Ensure we slightly overmatch yesterday's top bid if possible.
            target = max(target, max_prev_bid * 0.98)
        elif max_prev_bid >= mid_aggr:
            # Light contest: bid above their max but cap by budget.
            target = max(max_prev_bid + 2.0, DAILY_SALARY * (0.45 + urgency))
        else:
            # They were not aggressive: secure water with a small premium.
            target = max(max_prev_bid + 1.5, DAILY_SALARY * (0.40 + urgency))
            # If our hp is low, raise more.
            if hp <= 2:
                target = max(target, DAILY_SALARY * (0.75 + urgency))

    else:
        # No trace info; use hp-based baseline.
        if hp <= 2:
            target = DAILY_SALARY * (0.75 + urgency)
        else:
            target = DAILY_SALARY * (0.55 + urgency)

    # Convert target bid to a reasonable cap based on supply and our requirement.
    # We don't know exact allocation rules, so we bias toward being able to win
    # when supply is tight (closer to MIN_SUPPLY).
    tightness = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        tightness = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)
    tightness = max(0.0, min(1.0, tightness))

    # If supply is below our requirement, we cannot fully satisfy anyway; still contest.
    if supply < float(WATER_REQ):
        target = target * (1.0 + 0.15 * (1.0 + tightness))
    else:
        # If supply is ample relative to requirement, reduce overbidding.
        target = target * (1.0 - 0.10 * (1.0 - tightness))

    # Final bid: must be non-negative and not exceed budget.
    bid = float(max(0.0, min(budget, target)))

    # Small day-based variation to avoid ties (bounded).
    bid = bid * (1.0 + 0.01 * ((int(day) % 5) - 2))
    bid = float(max(0.0, min(budget, bid)))

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
    day = day_context.get('day', 1)

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    # Identify alive opponents and compute yesterday bid pressure
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        # No one to compete with; take what you can afford
        cap = max(0.0, my_budget)
        return min(cap, DAILY_SALARY * 0.4)

    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = 0.0
    if len(yesterday_bids) >= 2:
        sorted_b = sorted(yesterday_bids, reverse=True)
        second_prev_bid = sorted_b[1]

    # Supply pressure heuristic: if supply is tight, we need to bid more to ensure water.
    # With supply in [15,25], total water is enough for 1 day per player if they secure enough.
    # We aim to consistently avoid no-water days.
    tightness = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY + 1e-9)  # 0..1

    # Opponent aggressiveness: Cindy showed extreme spending yesterday.
    aggressive = highest_prev_bid >= DAILY_SALARY * 1.5

    # Health/budget response
    if my_hp <= 1.5:
        urgency = 1.0
    elif my_hp <= 3.5:
        urgency = 0.75
    else:
        urgency = 0.45

    if my_no_water_days >= 2:
        urgency = max(urgency, 0.9)

    # Base bid: moderate, scaled by tightness and urgency.
    base = DAILY_SALARY * (0.35 + 0.25 * tightness) * urgency

    # If someone was extremely aggressive yesterday, we may need to slightly overmatch to avoid losing.
    # But avoid overpaying like Cindy.
    if aggressive:
        # Try to bid near the leader but with a discount.
        target = 0.85 * highest_prev_bid
        # If our budget is low, fall back to base.
        bid = min(base, target) if my_budget < DAILY_SALARY else min(max(base, target * 0.6), target)
    else:
        # If competition was mild, bid around base with small lift.
        bid = base + 0.1 * second_prev_bid

    # Ensure bid is within budget and non-negative.
    bid = max(0.0, float(bid))
    if my_budget <= 0.0:
        return 0.0
    bid = min(bid, my_budget)

    # Final cap to reduce risk of early death cycles.
    # If we have enough budget, allow a higher cap; otherwise stay conservative.
    high_cap = DAILY_SALARY * (1.0 + 0.6 * tightness)  # up to ~1.6*salary
    bid = min(bid, high_cap)

    # If very late in episode and we still have budget, slightly increase to secure survival.
    # episode_days is 10, meta_round uses day within episode.
    # We only have day_context['day'], so approximate late-game at day>=8.
    if int(day) >= 8 and my_budget > 0:
        bid = min(my_budget, bid * 1.15)

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

    # Alive opponents and yesterday bids
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    # If no opponents alive, bid to survive cheaply
    if not alive_opps:
        return max(0.0, min(my_status.get('budget', 0.0), DAILY_SALARY * 0.4))

    yesterday_bids = []
    highest_prev_bid = None
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                b_val = float(b)
            except Exception:
                continue
            yesterday_bids.append(b_val)
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
    else:
        highest_prev_bid = 0.0

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Estimate how many water quanta are available this day
    # (Used only for aggressiveness; actual allocation is determined by bids.)
    quanta = supply / float(WATER_REQ) if WATER_REQ > 0 else 0.0

    # Baseline: if we're in danger, bid more. Otherwise conserve.
    danger = (my_hp <= 2) or (no_water_days >= 2)

    # Opponent pressure heuristic from yesterday: if someone bid very high, they likely expect contest.
    high_pressure = highest_prev_bid >= DAILY_SALARY * 0.9
    medium_pressure = (highest_prev_bid >= DAILY_SALARY * 0.6) and (highest_prev_bid < DAILY_SALARY * 0.9)

    # Supply affects how many can be satisfied: higher supply reduces need to overbid.
    supply_factor = 0.9 if supply >= 22.0 else (1.05 if supply <= 17.0 else 1.0)

    # Strategy:
    # - If high pressure and we're not safe, match aggressive spending.
    # - If high pressure but we're safe, undercut slightly.
    # - If no high pressure, bid just enough to secure water.
    if danger:
        if high_pressure:
            bid = DAILY_SALARY * 0.95
        elif medium_pressure:
            bid = DAILY_SALARY * 0.75
        else:
            bid = DAILY_SALARY * 0.65
    else:
        if high_pressure:
            bid = DAILY_SALARY * 0.70
        elif medium_pressure:
            bid = DAILY_SALARY * 0.55
        else:
            bid = DAILY_SALARY * 0.45

    # Adjust by supply factor and by quanta (more quanta => slightly lower bid)
    if quanta >= 2.2:
        bid *= 0.9
    elif quanta <= 1.8:
        bid *= 1.05

    bid *= supply_factor

    # Budget cap and non-negative
    bid = max(0.0, min(my_budget, bid))

    # If budget is extremely low, still try to get at least some allocation when danger is true
    if my_budget <= DAILY_SALARY * 0.25:
        if danger:
            bid = my_budget
        else:
            bid = min(my_budget, DAILY_SALARY * 0.2)

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

    supply = day_context['supply']
    day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o.get('alive')]
    if not alive_opponents:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace only
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace') or {}
        bid = prev.get('bid')
        if bid is not None:
            try:
                yesterday_bids.append(float(bid))
            except Exception:
                pass

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    # If our HP is critical, bid aggressively to avoid death.
    if hp <= 2.0:
        return float(min(budget, DAILY_SALARY * 0.95))

    # If someone already overbid yesterday, we can undercut slightly.
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # Cindy-like behavior: very high bids. Free-ride.
        if highest_prev_bid >= DAILY_SALARY * 1.8:
            # Moderate bid: enough to likely win some allocation, but cheaper than them.
            bid = DAILY_SALARY * 0.55
        # Other survivors bid mid-range: bid a bit above the median/high to secure.
        else:
            sorted_bids = sorted(yesterday_bids)
            mid = sorted_bids[int(len(sorted_bids) // 2)] if len(sorted_bids) > 0 else highest_prev_bid
            bid = max(DAILY_SALARY * 0.45, float(mid) * 1.05)
    else:
        bid = DAILY_SALARY * 0.55

    # Scale down as supply increases (more likely to get water without overpaying)
    # supply is in [15,25].
    if supply is not None:
        try:
            s = float(supply)
            # map s in [15,25] to multiplier in [1.05, 0.9]
            mult = 1.05 - (s - MIN_SUPPLY) * (0.15 / (MAX_SUPPLY - MIN_SUPPLY))
            bid *= mult
        except Exception:
            pass

    # Ensure we don't bid more than we can afford.
    bid = float(min(budget, bid))

    # If budget is too low, bid whatever remains (still try to get water).
    if bid <= 0.0:
        return 0.0

    # Slightly adjust by day to keep survival to the end (later days bid a touch more).
    # episode_days is 10 in meta state, but not provided here; we use day to infer.
    try:
        if day is not None and int(day) >= 8:
            bid = min(budget, bid * 1.15)
    except Exception:
        pass

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

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opps = [o for o in opponents_status.values() if o.get('alive')]
    if not alive_opps:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Extract yesterday bids from immediate previous_trace
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Estimate competitive pressure from yesterday
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    # If opponents already used very high bids, we can shade slightly lower than their peak.
    # If my hp is low or I'm accumulating no-water days, increase bid.
    pressure = 0.0
    if highest_prev_bid > 0:
        pressure = min(1.0, highest_prev_bid / (DAILY_SALARY * 1.9))

    # Supply factor: higher supply reduces need to overbid.
    supply_factor = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_factor = max(0.0, min(1.0, supply_factor))

    # Urgency
    urgency = 0.0
    if my_hp <= 1.0:
        urgency = 1.0
    elif my_hp <= 3.0:
        urgency = 0.75
    elif my_hp <= 5.0:
        urgency = 0.5
    else:
        urgency = 0.25

    if my_no_water_days >= 2:
        urgency = min(1.0, urgency + 0.25)

    # Base bid: mid-level, adjusted by pressure and urgency.
    # Aim: bid around 0.55*salary when not urgent; up to ~0.95*salary when urgent.
    target = DAILY_SALARY * (0.45 + 0.5 * urgency)  # 0.575..0.95 of salary

    # Shade based on yesterday peak/avg: if others overbid, we reduce slightly.
    if highest_prev_bid > 0:
        # If highest was extremely high, don't match it; instead bid between avg and 0.8*highest.
        if highest_prev_bid >= DAILY_SALARY * 1.6:
            target = min(target, 0.8 * highest_prev_bid)
        else:
            # If bids were moderate, keep closer to avg
            target = 0.6 * target + 0.4 * avg_prev_bid

    # Supply reduces bid need
    target = target * (0.95 - 0.15 * supply_factor)

    # Final cap by budget and sanity bounds
    # Ensure we don't bid too low when supply is tight and urgency is high.
    min_reasonable = DAILY_SALARY * (0.35 + 0.25 * urgency)
    bid = max(min_reasonable, target)

    # If budget is low, still bid as much as possible but not exceed budget.
    bid = min(bid, my_budget)

    # If we are very low budget, prioritize survival: bid near salary*0.9.
    if my_budget <= DAILY_SALARY * 0.6:
        bid = min(my_budget, DAILY_SALARY * (0.75 + 0.25 * urgency))

    # Avoid negative/NaN
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

    alive_opps = []
    for k, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((k, o))

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday bids from each opponent's previous_trace
    yesterday_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Estimate opponent pressure
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Cindy appears to be the main aggressor (high average bid yesterday, survived)
    # If Cindy bid high yesterday, we slightly overbid to secure enough water.
    cindy = opponents_status.get('Cindy')
    cindy_prev = cindy.get('previous_trace', {}) if cindy else {}
    cindy_prev_bid = float(cindy_prev['bid']) if (cindy_prev and cindy_prev.get('bid') is not None) else 0.0
    cindy_pressure = cindy_prev_bid

    # Determine our urgency: if low hp or close to running out of water days, bid more.
    urgency = 0.0
    if hp <= 2:
        urgency += 1.4
    elif hp <= 4:
        urgency += 0.9
    else:
        urgency += 0.5

    # If we've already had many no-water days, increase urgency.
    if no_water_days >= 4:
        urgency += 0.9
    elif no_water_days >= 2:
        urgency += 0.4

    # Base bid level: aim around half-day salary, adjusted by urgency.
    base = DAILY_SALARY * 0.5
    target = base * urgency

    # If Cindy was bidding high, raise target to contest.
    # Use a small increment above their previous bid to capture the marginal advantage.
    if cindy_pressure > 0:
        # Cindy's max yesterday was ~184.98; we don't want to match her fully forever.
        target = max(target, min(budget, cindy_pressure + 5.0))

    # If overall highest previous bid was very high, we need to respond.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        target = max(target, DAILY_SALARY * 0.65)

    # Supply scaling: when supply is higher, competition for water may soften.
    # If supply is near max, we can bid slightly less; if near min, bid slightly more.
    if supply <= MIN_SUPPLY + 1e-6:
        target *= 1.08
    elif supply >= MAX_SUPPLY - 1e-6:
        target *= 0.95

    # Safety caps: never bid more than budget or an aggressive but bounded fraction.
    cap = min(budget, DAILY_SALARY * 1.05)
    bid = min(target, cap)

    # Ensure non-negative and at least a small amount if we want a chance.
    if bid < 1.0:
        bid = min(budget, 10.0)

    return bid
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

    # If we are already in trouble, prioritize survival.
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        # No one to compete with; bid just enough to avoid running out.
        target = DAILY_SALARY * 0.35
        return min(budget, target)

    # Read yesterday bids from traces (only immediate reaction).
    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                yesterday_bids.append(float(bid))
            except Exception:
                pass

    # Estimate how aggressive the field was.
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
    else:
        highest_prev_bid = 0.0

    # Identify if Cindy was the dominant bidder yesterday (common in trace).
    cindy = opponents_status.get('Cindy', None)
    cindy_aggressive = False
    if cindy is not None and cindy.get('alive', False):
        prev = cindy.get('previous_trace', {}) or {}
        try:
            cindy_bid = float(prev.get('bid', 0.0) or 0.0)
        except Exception:
            cindy_bid = 0.0
        if cindy_bid >= DAILY_SALARY * 1.2:
            cindy_aggressive = True

    # Supply pressure: in lower supply days, we need to secure more water.
    # Winning typically depends on bid size; we convert supply to an urgency factor.
    # urgency in [0,1]
    if MAX_SUPPLY == MIN_SUPPLY:
        urgency = 0.5
    else:
        urgency = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)
        if urgency < 0.0:
            urgency = 0.0
        if urgency > 1.0:
            urgency = 1.0

    # Decide baseline bid.
    # If Cindy was aggressive, we try to beat her only when my hp is low or supply is scarce.
    # Otherwise we bid enough to avoid being outcompeted by the general field.
    if hp <= 2.0 or no_water_days >= 2:
        # Critical survival mode.
        if cindy_aggressive and urgency >= 0.6:
            target = DAILY_SALARY * 0.95
        else:
            target = DAILY_SALARY * (0.75 + 0.15 * urgency)
    else:
        # Healthy mode: conserve budget.
        if cindy_aggressive:
            # Don't chase her fully; just ensure we don't lose to everyone.
            target = DAILY_SALARY * (0.45 + 0.25 * urgency)
        else:
            # If field bids were generally low, bid modestly.
            target = DAILY_SALARY * (0.35 + 0.20 * urgency)

        # If yesterday's highest bid was extremely high, slightly increase to avoid being starved.
        if highest_prev_bid >= DAILY_SALARY * 1.4:
            target = max(target, DAILY_SALARY * (0.55 + 0.20 * urgency))
        elif highest_prev_bid >= DAILY_SALARY * 0.9:
            target = max(target, DAILY_SALARY * (0.45 + 0.15 * urgency))

    # Cap by budget.
    if budget <= 0.0:
        return 0.0

    bid = min(budget, target)

    # Keep bids non-negative.
    if bid < 0.0:
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

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace only
    prev_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                prev_bids.append(float(bid))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate how many units are likely needed to satisfy requirement
    # If supply is tight, we should bid more; if ample, bid less.
    # supply/WATER_REQ ~ number of requirements that can be satisfied.
    # Use int() to avoid float-index issues (though we don't index lists here).
    supply_ratio = supply / float(WATER_REQ) if WATER_REQ > 0 else 0.0

    # Base bid target
    # - If supply_ratio is low (tight), push closer to daily salary.
    # - Otherwise, keep moderate.
    if supply_ratio < 1.2:
        base = DAILY_SALARY * 0.75
    elif supply_ratio < 1.8:
        base = DAILY_SALARY * 0.60
    else:
        base = DAILY_SALARY * 0.45

    # React to yesterday's aggressiveness: others bid ~100-140.
    # If highest_prev_bid was very high, we slightly undercut rather than match.
    if highest_prev_bid > DAILY_SALARY * 1.0:  # >90
        # Undercut by a bit while still competitive.
        target = min(base, highest_prev_bid * 0.85)
    else:
        target = base

    # Urgency adjustments for our hp/no_water_days
    if hp <= 2:
        target = max(target, DAILY_SALARY * 0.85)
    elif hp <= 4:
        target = max(target, DAILY_SALARY * 0.65)

    if no_water_days >= 2:
        target = max(target, DAILY_SALARY * 0.7)

    # Final clamp to budget and non-negative
    bid = max(0.0, min(float(budget), float(target)))

    # If budget is extremely low, still bid something small to avoid going dry.
    if bid <= 0.0 and budget > 0.0:
        bid = min(float(budget), 5.0)

    return bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    # day_context: {'supply','day'}
    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        # conserve budget
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace only
    prev_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Pressure estimate: if someone bid extremely high yesterday, they likely expect scarcity
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate how many water units are likely available relative to our need.
    # supply is total available; if supply is just enough, competition rises.
    # Use int indices safely; no lists are indexed here but keep robust.
    supply_units = supply / float(WATER_REQ) if WATER_REQ > 0 else 0.0

    # Baseline bid: aim to be competitive but not max.
    # Medium scenario supply 15-25 => supply_units ~1.67-2.78
    # If supply_units is low, bid higher.
    if supply_units < 2.0:
        baseline = DAILY_SALARY * 0.7
    else:
        baseline = DAILY_SALARY * 0.55

    # Escalate based on our health and no-water streak.
    if hp <= 2.0:
        baseline = DAILY_SALARY * 0.9
    elif hp <= 4.0 or no_water_days >= 2:
        baseline = max(baseline, DAILY_SALARY * 0.75)

    # Reaction to opponent aggression yesterday
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Someone paid near capacity; match closer.
        baseline = max(baseline, DAILY_SALARY * 0.8)
    elif highest_prev_bid >= DAILY_SALARY * 0.6:
        baseline = max(baseline, DAILY_SALARY * 0.65)

    # Convert to final bid, capped by budget. Also keep within a reasonable fraction of daily salary.
    # If budget is tiny, don't exceed it.
    bid_cap = min(budget, DAILY_SALARY * 0.95)
    bid = min(bid_cap, baseline)

    # If we are still healthy and budget allows, slightly underbid to save funds.
    if hp >= 6.0 and no_water_days == 0:
        bid = min(bid_cap, bid * 0.9)

    # Ensure non-negative
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    my_hp = float(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday bids to infer who likely over-committed.
    prev_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict) and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate how many water units are available; use integer index safety.
    # supply is float, but we only use it for thresholds.
    units_available = int(supply / WATER_REQ)  # e.g., 19/9 -> 2

    # Base bid: aim to beat typical medium bids without matching Cindy's extreme spending.
    # If supply is tight (few units), bid higher.
    tightness = 0.0
    if units_available <= 1:
        tightness = 1.0
    elif units_available == 2:
        tightness = 0.6
    else:
        tightness = 0.3

    # If Cindy likely spent big yesterday (highest_prev_bid very high), avoid full race.
    # If my HP is low or I already missed water, increase urgency.
    urgency = 0.0
    if my_hp <= 2.0:
        urgency = 1.0
    elif my_hp <= 4.0:
        urgency = 0.7
    else:
        urgency = 0.3

    if my_no_water_days >= 2:
        urgency = max(urgency, 0.8)

    # Construct target bid cap.
    # When highest_prev_bid is huge, keep below it but still enough to secure.
    if highest_prev_bid >= DAILY_SALARY * 1.2:
        # Cindy-like behavior: spenders exist; I bid moderately.
        target = DAILY_SALARY * (0.35 + 0.25 * tightness + 0.25 * urgency)
        # Ensure not too low vs observed pressure.
        target = min(target, highest_prev_bid * 0.55)
    elif highest_prev_bid >= DAILY_SALARY * 0.85:
        # High pressure but not extreme.
        target = DAILY_SALARY * (0.45 + 0.2 * tightness + 0.25 * urgency)
        target = min(target, highest_prev_bid * 0.75)
    else:
        # Low to moderate pressure: bid around a survival-oriented baseline.
        target = DAILY_SALARY * (0.55 * tightness + 0.35 * urgency + 0.15)

    # Convert to final bid with budget constraints.
    # Also keep within a reasonable fraction of budget to avoid going to 0 too early.
    max_affordable = max(0.0, my_budget)
    # If budget is tiny, just bid what we can.
    if max_affordable <= 1e-9:
        return 0.0

    # Fractional safety: if urgency high, allow higher fraction.
    frac = 0.65 if urgency >= 0.8 else (0.5 if urgency >= 0.5 else 0.4)
    bid = min(max_affordable * frac, target)

    # If supply is extremely tight, nudge up slightly.
    if units_available <= 1 and urgency >= 0.7:
        bid = min(max_affordable, bid + DAILY_SALARY * 0.15)

    # Final clamp.
    if bid < 0.0:
        bid = 0.0
    if bid > max_affordable:
        bid = max_affordable
    return float(bid)
"""
