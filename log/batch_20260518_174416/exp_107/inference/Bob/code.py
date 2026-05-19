# ============================================================
# Experiment: exp_107
# Agent: Bob
# Source: exp_107
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

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opponents = [o for o in opponents_status.values() if o.get('alive')]

    # Default: moderate bid.
    # Target is to roughly cover our requirement when supply is near the low end.
    # We also scale with how constrained we are (hp/no_water_days).
    if supply <= (MIN_SUPPLY + MAX_SUPPLY) / 2.0:
        base = 0.55 * DAILY_SALARY
    else:
        base = 0.45 * DAILY_SALARY

    # Escalate if we're in danger.
    risk = 0.0
    if hp <= 2.5:
        risk += 0.45
    elif hp <= 4.0:
        risk += 0.25

    if no_water_days >= 2:
        risk += 0.25
    elif no_water_days >= 1:
        risk += 0.12

    # Try to react to immediate yesterday pressure if available.
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If they were aggressive yesterday, we slightly outbid but only when it matters.
        if highest_prev_bid >= 0.85 * DAILY_SALARY:
            if hp > 3.5:
                base = 0.65 * DAILY_SALARY
            else:
                base = 0.95 * DAILY_SALARY
        else:
            # Otherwise, bid enough to be competitive.
            base = max(base, highest_prev_bid + 2.0)

    bid = base * (1.0 + risk)

    # Budget and sanity caps.
    # In this environment, bids are effectively bounded; keep within reasonable range.
    bid = min(bid, budget)
    bid = max(0.0, bid)

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

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    my_hp = my_status.get('hp', 0)
    my_budget = my_status.get('budget', 0.0)
    my_no_water_days = my_status.get('no_water_days', 0)

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return float(min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace only (immediate reaction)
    prev_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        if prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate how many
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
    day = day_context.get('day', 0)

    # Alive opponents and their yesterday bids
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Pressure estimate from yesterday
    top_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_bid = 0.0
    if len(yesterday_bids) >= 2:
        sorted_b = sorted(yesterday_bids, reverse=True)
        second_bid = sorted_b[1]

    # Supply tightness: fewer winners likely when supply is near MIN_SUPPLY
    # Approximate number of full water units available
    units = supply / float(WATER_REQ)
    # Use an integer index safely if we ever map; here just compare thresholds.
    tight = supply <= (MIN_SUPPLY + 1.0)  # very scarce

    # Base bid: aim to be competitive but not the highest
    # If Cindy/Alex were bidding high yesterday, we undercut slightly.
    if top_bid > 0:
        # Target: slightly below the highest yesterday bid, but with floor/ceiling.
        target = top_bid * 0.92
        # If supply is tight, be more aggressive; if not, back off.
        if tight:
            target *= 1.08
        else:
            target *= 0.98
    else:
        target = DAILY_SALARY * 0.55

    # Risk management by HP and no-water streak
    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    if hp <= 2 or no_water_days >= 2:
        # Must secure water
        target = max(target, DAILY_SALARY * 0.75)
    elif hp <= 4:
        target = max(target, DAILY_SALARY * 0.60)

    # If supply is extremely low, cap to ensure budget sustainability
    # but still try to beat typical mid bids.
    if tight:
        target = max(target, DAILY_SALARY * 0.65)

    # Final clamp to budget and reasonable range
    # Never bid more than budget.
    bid = min(budget, max(0.0, target))

    # If budget is tiny, bid as much as possible.
    if budget <= DAILY_SALARY * 0.2:
        bid = budget

    return float(bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = day_context['supply']
    day = day_context['day']

    # Alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # If no opponents, bid just enough to cover requirement
    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.35)

    # Read yesterday bids from previous_trace only
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            prev_bids.append((oid, b))

    # Estimate competitive pressure from highest prior bid
    highest_prev_bid = max([b for _, b in prev_bids], default=0.0)

    # Identify if a specific opponent was extremely aggressive yesterday (likely Cindy)
    aggressive = False
    for oid, b in prev_bids:
        if b >= DAILY_SALARY * 1.8:  # ~162
            aggressive = True
            break

    # Identify if any opponent likely failed due to underbidding (Eric-like), reduce commitment slightly
    # If an opponent had very low bid yesterday, they likely won't contest as hard now.
    weak_contender = False
    for oid, b in prev_bids:
        if b <= DAILY_SALARY * 0.4:  # <=36
            weak_contender = True
            break

    my_hp = my_status['hp']
    my_budget = my_status['budget']

    # Strategy:
    # - With high hp, we can bid less than the aggressor but still enough to avoid losing to them.
    # - If aggressive yesterday, bid around 1.05x highest_prev_bid but capped to budget.
    # - If no aggression, bid mid-level.
    # - If my hp is low, bid more.
    if my_hp <= 2:
        target = DAILY_SALARY * 0.95
    elif my_hp <= 4:
        target = DAILY_SALARY * 0.75
    else:
        if aggressive:
            # Win-avoidance: outbid slightly, but don't overspend.
            target = max(DAILY_SALARY * 0.6, highest_prev_bid * 1.05)
        else:
            target = DAILY_SALARY * (0.55 if not weak_contender else 0.45)

    # Adjust for supply: higher supply reduces marginal need to overbid.
    # supply in [15,25]
    if supply >= 22:
        target *= 0.95
    elif supply <= 16:
        target *= 1.05

    # Final cap by budget and non-negative
    bid = max(0.0, min(my_budget, target))

    # Ensure at least some bid to avoid being shut out when others are aggressive
    if bid < DAILY_SALARY * 0.25 and aggressive:
        bid = min(my_budget, DAILY_SALARY * 0.3)

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

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive'):
            alive_opps.append((oid, o))

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from immediate previous_trace only
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate urgency: if we have low HP or already have no-water streak, bid more.
    urgency = 0.0
    if hp <= 2.5:
        urgency += 1.0
    if hp <= 4.0:
        urgency += 0.6
    if no_water_days >= 2:
        urgency += 0.8
    if no_water_days >= 3:
        urgency += 1.2

    # Supply scaling: with higher supply, we can afford slightly less aggressive bidding.
    # Map supply to [0,1] where 0 at MIN_SUPPLY and 1 at MAX_SUPPLY.
    if MAX_SUPPLY == MIN_SUPPLY:
        supply_factor = 0.5
    else:
        supply_factor = (supply - float(MIN_SUPPLY)) / (float(MAX_SUPPLY) - float(MIN_SUPPLY))
        if supply_factor < 0.0:
            supply_factor = 0.0
        if supply_factor > 1.0:
            supply_factor = 1.0

    # Target bid baseline.
    # If someone previously bid very high, we must respect that (avoid losing to them).
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Alex/Eric-like behavior; bid enough to compete, but not max out.
        base = DAILY_SALARY * (0.38 + 0.25 * urgency)  # up to ~0.63*salary
        # If our budget is large, slightly raise toward their pressure.
        if budget >= DAILY_SALARY * 1.2:
            base = max(base, min(budget, highest_prev_bid * 0.55))
    else:
        # Lower competitive pressure; bid moderately to secure water.
        base = DAILY_SALARY * (0.30 + 0.20 * urgency)  # up to ~0.50*salary
        # If supply is low, increase a bit.
        if supply <= float(MIN_SUPPLY) + 1.0:
            base *= 1.10

    # Convert baseline to an actionable bid with budget cap.
    # Also keep a small floor to avoid being undercut when stakes are high.
    bid_floor = DAILY_SALARY * (0.25 if hp > 4 else 0.55)
    bid = max(bid_floor, base)

    # If our HP is critical, push higher.
    if hp <= 1.5:
        bid = max(bid, DAILY_SALARY * 0.85)

    # Ensure bid does not exceed budget.
    if bid > budget:
        bid = budget

    # Never negative.
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
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Alive opponents and yesterday bid pressure
    alive_opps = []
    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    yesterday_bids.append(float(prev.get('bid')))
                except Exception:
                    pass

    # If no opponents, just bid conservatively based on whether we're already in danger
    if not alive_opps:
        if hp <= 2 or no_water_days >= 2:
            return min(budget, DAILY_SALARY * 0.85)
        return min(budget, DAILY_SALARY * 0.55)

    # Estimate how aggressive the field was yesterday
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = 0.0
    if len(yesterday_bids) >= 2:
        sorted_bids = sorted(yesterday_bids, reverse=True)
        second_prev_bid = float(sorted_bids[1])

    # Our budget safety
    # If we are in danger, we must secure water; otherwise avoid overbidding.
    in_danger = (hp <= 2.0) or (no_water_days >= 2)

    # Supply pressure: when supply is high, water is easier; when low, competition spikes.
    # Use a simple normalized factor.
    supply_norm = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (supply - float(MIN_SUPPLY)) / (float(MAX_SUPPLY) - float(MIN_SUPPLY))
    if supply_norm < 0.0:
        supply_norm = 0.0
    if supply_norm > 1.0:
        supply_norm = 1.0

    # Target bid logic.
    # Cindy showed strong survival with very high bids; we won't match her peak.
    # Instead, bid just above the second-highest pressure when we need water.
    # When not in danger, bid around a moderate fraction of DAILY_SALARY.
    if in_danger:
        # If yesterday's field was very high, we still need to win; bid above the likely threshold.
        if highest_prev_bid >= DAILY_SALARY * 1.2:
            target = second_prev_bid + 5.0
        else:
            target = max(second_prev_bid + 2.0, DAILY_SALARY * 0.65)
    else:
        # Not in danger: adjust with supply. Low supply => slightly higher bids.
        # supply_norm high => bid lower.
        base = DAILY_SALARY * (0.58 - 0.18 * supply_norm)
        # If the field was extremely aggressive yesterday, raise our bid a bit to avoid losing to Cindy.
        if highest_prev_bid >= DAILY_SALARY * 1.2:
            base = max(base, DAILY_SALARY * 0.75)
        target = base

    # Cap target to avoid wasting budget; also ensure non-negative.
    if budget <= 0.0:
        return 0.0

    # If our budget is small, spend enough to likely win once, but don't exceed budget.
    # Use a soft cap tied to remaining days (episode length fixed at 10, but we only have current day).
    remaining_days = max(0, 10 - day)
    # Keep some buffer for future: average daily spend should not exceed budget/remaining_days.
    avg_allow = budget / float(remaining_days) if remaining_days > 0 else budget
    # Spend at most the min of target and a conservative fraction of avg_allow.
    conservative_cap = avg_allow * 0.9 if remaining_days > 0 else budget

    bid = min(float(target), float(conservative_cap), budget)

    # Ensure we bid at least a minimal amount when we are not fully safe.
    if in_danger and bid < budget * 0.35:
        bid = min(budget, max(bid, DAILY_SALARY * 0.6))

    # Final safety clamp
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

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return float(min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace for immediate reaction
    yesterday_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Estimate aggressiveness from yesterday
    aggressiveness = 0.0
    if yesterday_bids:
        max_bid_prev = max(yesterday_bids)
        avg_bid_prev = sum(yesterday_bids) / float(len(yesterday_bids))
        # Normalize: heavy if close to cap-ish region
        aggressiveness = 0.6 * (max_bid_prev / 150.0) + 0.4 * (avg_bid_prev / 150.0)

    # Supply factor: when supply is higher, winning water is easier; bid less.
    supply_mid = (MIN_SUPPLY + MAX_SUPPLY) / 2.0
    supply_factor = 1.0
    if supply >= supply_mid:
        supply_factor = 0.85
    else:
        supply_factor = 1.05

    # Urgency: if we've had no water days or low hp, bid higher.
    urgency = 1.0
    if my_hp <= 2.5:
        urgency = 1.35
    elif my_hp <= 4.5:
        urgency = 1.15

    if my_no_water_days >= 2:
        urgency *= 1.15

    # Target bid: aim slightly below aggressive ceiling when hp is ok.
    # Use aggressiveness to set a baseline.
    baseline = DAILY_SALARY * (0.45 + 0.35 * aggressiveness)  # roughly 40-76 when aggressiveness 0-1

    # If yesterday had a very high bid, try to undercut it while still being competitive.
    if yesterday_bids:
        max_bid_prev = max(yesterday_bids)
        if max_bid_prev >= DAILY_SALARY * 0.85:
            target = max_bid_prev * 0.92
        else:
            target = baseline
    else:
        target = baseline

    target *= supply_factor * urgency

    # Ensure we can afford it and keep within reasonable bounds.
    # Also, if budget is scarce, bid proportionally.
    if my_budget <= 0:
        return 0.0

    # Cap bid to avoid bankruptcy when not critical.
    critical = (my_hp <= 3.5) or (my_no_water_days >= 2)
    if critical:
        cap = min(my_budget, DAILY_SALARY * 0.95)
    else:
        cap = min(my_budget, DAILY_SALARY * 0.65)

    bid = float(min(cap, max(0.0, target)))

    # If bid is too low relative to our need, bump modestly.
    # (We don't know exact allocation rule; this is a safe competitiveness nudge.)
    if bid < DAILY_SALARY * 0.35 and critical:
        bid = float(min(my_budget, DAILY_SALARY * 0.55))

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

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    if my_budget <= 0:
        return 0.0

    # If we are in danger, prioritize survival.
    if my_hp <= 2 or my_no_water_days >= 2:
        return min(my_budget, DAILY_SALARY * 0.95)

    # Read yesterday's bids from opponents for immediate reaction.
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate how many water units likely available today.
    # Use int() to avoid float index issues (even though we don't index lists here).
    expected_units = int(supply / WATER_REQ)  # 15-25 => 1
    if expected_units < 1:
        expected_units = 1

    # Base bid: aim to secure enough water without matching the top spenders.
    # Supply medium: typically 1 unit; so we target a competitive but not maximal bid.
    base = DAILY_SALARY * 0.55

    if prev_bids:
        highest_prev_bid = max(prev_bids)
        # If someone was bidding extremely high yesterday, undercut slightly.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # If our HP is decent, bid in the competitive mid-high band.
            bid = DAILY_SALARY * 0.68
            # If we had any recent water stress (no_water_days), push higher.
            if my_no_water_days >= 1:
                bid = DAILY_SALARY * 0.78
            # Keep under the highest previous bid to avoid overpaying.
            bid = min(bid, highest_prev_bid - 2.0)
        else:
            # Otherwise, follow the market: slightly above the median to capture water.
            sorted_bids = sorted(prev_bids)
            mid_idx = int(len(sorted_bids) // 2)
            median_prev = sorted_bids[mid_idx]
            bid = max(base, median_prev * 0.92)
            # If median is low, still ensure some chance.
            bid = max(bid, DAILY_SALARY * 0.50)
    else:
        bid = base

    # Convert bid to a safe range given our budget.
    # Also cap by daily salary fraction; avoid spending all budget early.
    cap = DAILY_SALARY * 0.85
    bid = min(bid, cap, my_budget)

    # If supply is at the low end, we slightly increase to avoid being starved.
    if supply <= float(MIN_SUPPLY) + 0.5:
        bid = min(my_budget, bid + DAILY_SALARY * 0.10)

    # Ensure non-negative.
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from immediate previous_trace
    prev_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Opponent pressure heuristic: Cindy/Eric were very high yesterday; if so, we must contest.
    # If my HP is low, I bid closer to the contest level; otherwise I bid just enough to avoid being shut out.
    pressure = 0.0
    if highest_prev_bid >= 140.0:
        pressure = 1.0
    elif highest_prev_bid >= 110.0:
        pressure = 0.75
    elif highest_prev_bid >= 60.0:
        pressure = 0.5
    else:
        pressure = 0.25

    # Supply-based scaling: when supply is tight (near 15), contest more.
    if supply <= float(MIN_SUPPLY) + 0.5:
        supply_tightness = 1.0
    elif supply >= float(MAX_SUPPLY) - 0.5:
        supply_tightness = 0.4
    else:
        # linear-ish between 15 and 25
        supply_tightness = 0.9 - 0.05 * ((supply - float(MIN_SUPPLY)) / (float(MAX_SUPPLY) - float(MIN_SUPPLY)) * 10.0)
        if supply_tightness < 0.4:
            supply_tightness = 0.4
        if supply_tightness > 1.0:
            supply_tightness = 1.0

    # Determine a target bid band
    # Contest level anchored near what won yesterday (around 143-146), but we don't always need to match.
    contest_target = 0.0
    if pressure >= 1.0:
        contest_target = 135.0
    elif pressure >= 0.75:
        contest_target = 115.0
    elif pressure >= 0.5:
        contest_target = 85.0
    else:
        contest_target = 65.0

    # My urgency: low hp or accumulating no-water days -> bid higher
    urgency = 0.0
    if hp <= 1.5:
        urgency = 1.0
    elif hp <= 3.0:
        urgency = 0.85
    elif hp <= 5.0:
        urgency = 0.65
    else:
        urgency = 0.45

    if no_water_days >= 2:
        urgency = min(1.0, urgency + 0.15)

    # Final bid: weighted by contest_target and urgency/supply tightness
    base = contest_target * (0.55 + 0.45 * (urgency * supply_tightness))

    # Keep within budget; also avoid overbidding when budget is low.
    # If budget can't cover base, spend enough to stay alive but capped.
    spend_cap = budget

    # If my budget is extremely low, bid near the maximum affordable to prevent immediate death.
    if budget <= DAILY_SALARY * 0.35:
        bid = min(spend_cap, DAILY_SALARY * (0.75 + 0.25 * urgency))
    else:
        bid = min(spend_cap, base)

    # Never bid negative
    if bid < 0.0:
        bid = 0.0

    # Small adaptive adjustment by day to avoid ties late: slightly increase on later days
    if day >= 8:
        bid *= 1.04

    # Final clamp to a reasonable fraction of daily salary when budget is large
    # (prevents reckless spending if opponents suddenly stop contesting)
    max_reasonable = DAILY_SALARY * (1.15 if pressure >= 0.75 else 0.95)
    if bid > max_reasonable:
        bid = max_reasonable

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
    day = day_context.get('day', 0)

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    # If we are already critically low or have many no-water days, bid hard.
    if my_hp <= 2 or my_no_water_days >= 2:
        target = DAILY_SALARY * 0.85
    else:
        # Use yesterday trace: if any opponent bid was extremely high, they likely fight for water.
        yesterday_bids = []
        for _, opp in alive_opps:
            prev = opp.get('previous_trace', {}) or {}
            b = prev.get('bid', None)
            if b is not None:
                try:
                    yesterday_bids.append(float(b))
                except Exception:
                    pass

        # Supply pressure: when supply is closer to MIN, fewer allocations exist.
        # Convert supply to an estimate of how many full water units exist.
        units = supply / float(WATER_REQ) if WATER_REQ > 0 else 0.0
        pressure = 0.55 if supply <= (MIN_SUPPLY + 0.5) else 0.35

        if yesterday_bids:
            highest_prev_bid = max(yesterday_bids)
            # If someone previously overreached (near/above salary), we must match moderately.
            if highest_prev_bid >= DAILY_SALARY * 1.2:
                target = DAILY_SALARY * (0.55 + pressure)
            elif highest_prev_bid >= DAILY_SALARY * 0.85:
                target = max(DAILY_SALARY * 0.5, highest_prev_bid * 0.55)
            else:
                target = DAILY_SALARY * (0.42 + pressure)
        else:
            target = DAILY_SALARY * (0.45 + pressure)

    # Convert target to a bid; cap by budget.
    bid = min(my_budget, target)

    # Ensure non-negative and avoid tiny bids when we are not safe.
    if bid < 0.0:
        bid = 0.0

    # If supply is high enough to likely support survival, we can slightly underbid.
    if supply >= 22.0 and my_hp > 4:
        bid = min(bid, my_budget, DAILY_SALARY * 0.48)

    # If supply is low and we are safe, still bid enough to compete.
    if supply <= 16.0 and my_hp > 3:
        bid = max(bid, min(my_budget, DAILY_SALARY * 0.6))

    return float(bid)
"""
