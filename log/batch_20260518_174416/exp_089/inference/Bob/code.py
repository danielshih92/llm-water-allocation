# ============================================================
# Experiment: exp_089
# Agent: Bob
# Source: exp_089
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

    alive_opponents = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    # If we have no info from opponents, default to a pressure-aware baseline.
    # Higher bid when supply is tight relative to our requirement.
    if supply <= 0:
        supply_factor = 0.6
    else:
        # supply_factor in [~0.6, ~1.0]
        supply_factor = 0.6 + 0.4 * ((supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY))
        if supply_factor < 0.6:
            supply_factor = 0.6
        if supply_factor > 1.0:
            supply_factor = 1.0

    # HP/need urgency
    urgency = 0.0
    if hp <= 2:
        urgency += 0.35
    elif hp <= 4:
        urgency += 0.20
    if no_water_days >= 2:
        urgency += 0.25
    elif no_water_days == 1:
        urgency += 0.10

    # Base target: aim around 0.55 salary scaled by supply tightness and urgency.
    target = DAILY_SALARY * (0.55 * supply_factor + urgency)

    # If we can afford, bid more when many opponents are alive.
    n = len(alive_opponents)
    if n >= 3:
        target *= 1.15
    elif n == 2:
        target *= 1.07

    # Never exceed budget.
    bid = min(budget, target)

    # Ensure we still bid something meaningful when budget allows.
    # Keep a floor to avoid always losing when supply is competitive.
    min_bid = min(budget, DAILY_SALARY * 0.25)
    if bid < min_bid:
        bid = min_bid

    # If budget is very low, bid whatever we can.
    if budget <= DAILY_SALARY * 0.25:
        bid = budget

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

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append((oid, o))

    if not alive_opponents:
        return min(float(my_status['budget']), DAILY_SALARY * 0.4)

    # Extract yesterday bids from traces for immediate reaction
    yesterday_bids = []
    for oid, o in alive_opponents:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append((oid, float(b)))
            except Exception:
                pass

    # Identify Cindy-like pressure: highest yesterday bid
    highest_prev_bid = None
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids, key=lambda x: x[1])[1]

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])

    # Base bid depends on supply band: higher supply => lower bid needed to win water share
    # Supply is between 15 and 25 in this scenario.
    if supply <= 17.5:
        base = DAILY_SALARY * 0.65
    elif supply <= 21.0:
        base = DAILY_SALARY * 0.55
    else:
        base = DAILY_SALARY * 0.45

    # If Cindy (highest bidder) likely secured water yesterday, we shade slightly above a threshold
    # but avoid committing to very high bids that would mirror dying agents.
    if highest_prev_bid is not None:
        # If someone was bidding extremely high, we cap our aggression.
        if highest_prev_bid >= DAILY_SALARY * 0.9:
            target = min(base + 0.15 * DAILY_SALARY, DAILY_SALARY * 0.75)
        elif highest_prev_bid >= DAILY_SALARY * 0.55:
            target = min(base + 0.08 * DAILY_SALARY, DAILY_SALARY * 0.65)
        else:
            target = base
    else:
        target = base

    # HP emergency adjustment
    if my_hp <= 2.0:
        target = max(target, DAILY_SALARY * 0.9)
    elif my_hp <= 4.0:
        target = max(target, DAILY_SALARY * 0.7)

    # Budget safety: never bid more than budget, and avoid overbidding late in episode
    # (episode length inferred from meta-round context: 10 days)
    # If day is late, increase slightly to prevent last-day starvation.
    if day >= 8:
        target = min(target * 1.12, DAILY_SALARY * 0.78)

    bid = min(my_budget, float(target))

    # Ensure non-negative
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

    # If no opponents alive, bid conservatively.
    if not alive_opps:
        bid = DAILY_SALARY * 0.4
        return float(min(my_budget, bid))

    # Read yesterday bids of alive opponents.
    prev_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace') or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate opponent pressure from yesterday.
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_prev_bid = 0.0
    if len(prev_bids) >= 2:
        sorted_b = sorted(prev_bids, reverse=True)
        second_prev_bid = sorted_b[1]

    # Base target: mid-high to beat likely aggressive bidders, but not as high as their max.
    # Use our urgency to scale.
    urgency = 0.0
    if my_hp <= 2:
        urgency = 1.0
    elif my_hp <= 4:
        urgency = 0.7
    elif my_no_water_days >= 2:
        urgency = 0.6
    else:
        urgency = 0.4

    # Supply affects how many bidders might be satisfied; lower supply -> higher chance of competition.
    supply_factor = 0.55
    if supply <= float(MIN_SUPPLY):
        supply_factor = 0.8
    elif supply >= float(MAX_SUPPLY):
        supply_factor = 0.6

    # If yesterday highest bid was very high, reduce slightly to avoid overpaying into a war.
    # Otherwise, increase to secure water.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        war_mode = True
    else:
        war_mode = False

    # Candidate bid anchored around a fraction of DAILY_SALARY.
    if war_mode:
        base = DAILY_SALARY * (0.62 + 0.18 * urgency)
        # Nudge upward if we are in immediate danger.
        if my_hp <= 2 or my_no_water_days >= 3:
            base = DAILY_SALARY * (0.72 + 0.18 * urgency)
        # Also consider second-highest: try to be above it when budgets allow.
        if second_prev_bid > 0:
            base = max(base, second_prev_bid + 1.5)
    else:
        base = DAILY_SALARY * (0.55 + 0.25 * urgency)
        if highest_prev_bid > 0:
            base = max(base, min(DAILY_SALARY * 0.8, highest_prev_bid * 0.85 + 2.0))

    # Apply supply factor.
    bid = base * supply_factor

    # Safety caps: never bid more than we can afford; also avoid bidding above a reasonable ceiling.
    ceiling = DAILY_SALARY * 0.95
    bid = min(bid, ceiling)

    # If our budget is low, bid just enough to stay competitive.
    if my_budget < DAILY_SALARY * 0.3:
        bid = min(my_budget, DAILY_SALARY * 0.55)

    # Final clamp.
    bid = max(0.0, min(my_budget, bid))
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

    # Collect alive opponents and use only yesterday's previous_trace behavior.
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            prev = o.get('previous_trace', {}) or {}
            alive.append((oid, o, prev))

    if not alive:
        # No one to compete with: spend conservatively.
        return max(0.0, min(my_status.get('budget', 0.0), DAILY_SALARY * 0.4))

    # Extract yesterday bids.
    yesterday_bids = []
    for _, _, prev in alive:
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Estimate opponent aggressiveness from yesterday.
    # Cindy appears highest; we approximate by top-1 and top-2.
    top_bid = max(yesterday_bids) if yesterday_bids else 0.0
    sorted_bids = sorted(yesterday_bids, reverse=True)
    second_bid = sorted_bids[1] if len(sorted_bids) > 1 else sorted_bids[0] if sorted_bids else 0.0

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Determine urgency: if low HP or already in no-water streak, bid higher.
    urgency = 0
    if my_hp <= 2:
        urgency += 2
    elif my_hp <= 4:
        urgency += 1
    if no_water_days >= 1:
        urgency += 1

    # Supply pressure: if supply is high, competition is lower; if low, competition is higher.
    # supply is in [15,25].
    supply_norm = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    # low supply => supply_norm near 0 => pressure high.
    pressure = 1.0 - supply_norm

    # Strategy: avoid Cindy-like spending while still contesting.
    # Target bid is slightly below top_bid unless urgency is high.
    # If top_bid is very high (aggressive opponents), we try to undercut by a margin.
    undercut = 6.0 + 10.0 * pressure  # 6..16
    contest_margin = 2.0 + 6.0 * pressure  # 2..8

    if top_bid > 0:
        if urgency >= 2:
            target = min(top_bid + contest_margin, DAILY_SALARY * 1.2)
        elif urgency == 1:
            # Slightly undercut the leader to win at lower cost.
            target = max(0.0, top_bid - undercut)
            # If second bidder is close, add a bit to beat them.
            if second_bid > 0 and (top_bid - second_bid) < 8.0:
                target = max(target, second_bid + 1.5)
        else:
            # Low urgency: bid around a fraction of daily salary, but not too low vs leader.
            floor_bid = DAILY_SALARY * (0.35 + 0.2 * pressure)  # ~31.5..54
            target = max(floor_bid, top_bid - undercut)
    else:
        # No bid info: default mid-level.
        target = DAILY_SALARY * (0.45 + 0.15 * pressure)

    # Convert target to feasible bid: cannot exceed budget; also avoid wasting near end.
    # Episode length is 10 days; day_context['day'] likely 0..9 or 1..10.
    # We treat later days as higher urgency to secure water.
    try:
        d = int(day)
    except Exception:
        d = 0
    # Normalize day index roughly to 0..9.
    if d > 9:
        # if day is 1..10
        d = d - 1
    endgame = d >= 7

    if endgame and my_hp <= 5:
        target = max(target, DAILY_SALARY * 0.65)

    # If budget is very low, bid just enough to survive: proportional to remaining budget.
    if my_budget <= DAILY_SALARY * 0.2:
        target = min(target, my_budget)

    bid = min(my_budget, float(target))
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Determine alive opponents and their yesterday bids
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        # Conservative survival mode
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    prev_bids = []
    prev_hp_after = []
    for opp_id, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev.get('bid', 0.0)))
            prev_hp_after.append(float(prev.get('hp_after', opp.get('hp', 0.0))))

    # Pressure estimate from yesterday
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    # If we are in danger, bid hard to avoid running out
    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Supply-based urgency: higher supply needs less aggressive bidding
    # Normalize supply into [0,1]
    if MAX_SUPPLY == MIN_SUPPLY:
        supply_norm = 0.5
    else:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
        if supply_norm < 0.0:
            supply_norm = 0.0
        if supply_norm > 1.0:
            supply_norm = 1.0

    # Baseline bid to secure water when others are spending
    # Undercut the top yesterday bidder slightly, but not too low.
    # Also scale down when supply is high.
    target = highest_prev_bid

    # If yesterday had a very high bid, others likely expect competition.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Underbid just below the top pressure
        target = highest_prev_bid * 0.92
    else:
        # If moderate competition, bid around average + small edge
        target = max(avg_prev_bid * 0.95, DAILY_SALARY * (0.45 + 0.15 * (1.0 - supply_norm)))

    # Urgency adjustments
    if my_hp <= 2.0 or no_water_days >= 2:
        # Need water now
        target = max(target, DAILY_SALARY * 0.9)
    elif my_hp <= 3.5:
        target = max(target, DAILY_SALARY * 0.65)
    else:
        # Safe: conserve budget; scale with supply
        target = target * (0.85 + 0.15 * supply_norm)

    # Keep within budget and avoid overspending
    # Also cap relative to daily salary to prevent runaway bids.
    cap = DAILY_SALARY * 1.2
    bid = float(min(my_budget, cap, target))

    # Ensure non-negative
    if bid < 0.0:
        bid = 0.0

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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))

    # If we're broke, still try to get a token bid.
    if budget <= 0:
        return 0.0

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    # If no opponents are alive, bid conservatively.
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.3)

    # Read yesterday bids from previous_trace only (immediate reaction).
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how competitive today's bidding likely is.
    # Low supply tends to increase pressure; Cindy's high survival suggests she can sustain higher bids.
    supply_factor = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY + 1e-9)  # 0..1-ish
    supply_factor = max(0.0, min(1.0, supply_factor))

    # Base target: slightly above a typical mid bid, but not as extreme as Cindy's max.
    # Use highest_prev_bid as an anchor.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # They were willing to pay a lot; we should secure water if our hp is not great.
        base = DAILY_SALARY * (0.55 + 0.25 * supply_factor)
        # If we're healthy, undercut slightly; if low hp, match more.
        if hp > 4:
            target = min(base, highest_prev_bid * 0.75)
        else:
            target = min(base * 1.1, highest_prev_bid * 0.9)
    else:
        # Yesterday pressure was lower; bid enough to avoid falling behind.
        target = DAILY_SALARY * (0.45 + 0.25 * supply_factor)
        # If highest_prev_bid exists, nudge above it modestly.
        if highest_prev_bid > 0:
            target = max(target, highest_prev_bid + 5.0)

    # If our hp is critically low or no_water_days is high, bid more aggressively.
    no_water_days = float(my_status.get('no_water_days', 0.0))
    if hp <= 2.0 or no_water_days >= 2.0:
        target *= 1.35

    # Convert target to a safe bid within budget.
    # Also cap to prevent overspending beyond what salary can support.
    max_reasonable = DAILY_SALARY * (0.95 + 0.2 * supply_factor)
    bid = min(budget, max_reasonable, target)

    # Ensure non-negative.
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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    # If no opponents are alive, bid conservatively
    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from immediate previous_trace
    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Estimate aggressiveness from yesterday
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
    else:
        highest_prev_bid = 0.0

    # Supply pressure heuristic: higher supply -> lower need to outbid
    # Normalize supply to [0,1]
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_norm = 0.5
    supply_norm = max(0.0, min(1.0, supply_norm))

    # Base target bid: aim around a fraction of salary, adjusted by supply and yesterday aggressiveness
    # If opponents were bidding very high yesterday, we must match more.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        base = DAILY_SALARY * (0.75 - 0.25 * supply_norm)
    elif highest_prev_bid >= DAILY_SALARY * 0.65:
        base = DAILY_SALARY * (0.6 - 0.15 * supply_norm)
    else:
        base = DAILY_SALARY * (0.52 - 0.1 * supply_norm)

    # Urgency adjustment based on our HP and no_water_days
    # If we're already in danger, bid higher to secure water.
    if hp <= 2.5:
        base *= 1.35
    elif hp <= 4.0:
        base *= 1.15

    if no_water_days >= 2:
        base *= 1.2
    elif no_water_days == 1:
        base *= 1.08

    # If supply is low (near MIN_SUPPLY), water is scarce -> slightly more aggressive
    if supply <= (MIN_SUPPLY + 1.0):
        base *= 1.12

    # Cap by budget; also avoid bidding absurdly above what salary suggests
    # Keep a floor to not get shut out when we need water.
    min_bid = 0.0
    if hp <= 4.0 or no_water_days >= 2:
        min_bid = DAILY_SALARY * 0.35
    else:
        min_bid = DAILY_SALARY * 0.25

    bid = max(min_bid, base)
    bid = min(bid, budget)

    # Final safety clamp
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Identify alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # If no one alive, take what you need
    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Read yesterday bids from previous_trace for immediate reaction
    prev_bids = []
    for oid, o in alive_opps:
        pt = o.get('previous_trace', None)
        if isinstance(pt, dict):
            b = pt.get('bid', None)
            if b is not None:
                prev_bids.append(float(b))
        elif isinstance(pt, list) and len(pt) > 0:
            # Shouldn't happen per spec, but be defensive
            last = pt[-1]
            b = last.get('bid', None)
            if b is not None:
                prev_bids.append(float(b))

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Determine how many full allocations are feasible; use int indices safely
    # supply is 15..25 so thresholding is stable
    supply_level = 0
    if supply >= 21:
        supply_level = 2
    elif supply >= 18:
        supply_level = 1
    else:
        supply_level = 0

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    # Core strategy:
    # - If others were bidding high yesterday, we match a fraction above a baseline to avoid losing.
    # - If my hp is low, bid more conservatively to preserve budget for later survival.
    # - If supply is higher, we can bid slightly less since water is effectively more available.

    # Baseline bids by supply level
    if supply_level == 2:
        base = DAILY_SALARY * 0.45
    elif supply_level == 1:
        base = DAILY_SALARY * 0.55
    else:
        base = DAILY_SALARY * 0.65

    # Pressure adjustment based on yesterday's highest bid
    # If someone bid near/above 0.85*salary, assume they were fighting for survival.
    pressure = 0.0
    if highest_prev_bid > 0:
        pressure = highest_prev_bid / DAILY_SALARY

    if pressure >= 0.85:
        # Match pressure but not fully; aim to beat mid-tier while conserving budget.
        if hp > 3:
            target = base + (highest_prev_bid - base) * 0.55
        else:
            target = base + (highest_prev_bid - base) * 0.35
    elif pressure >= 0.6:
        target = base + (highest_prev_bid - base) * 0.35
    else:
        # If yesterday was low, bid just enough to secure water.
        target = base * 0.95

    # Safety caps to avoid overspending
    # Keep within budget and avoid bidding above a reasonable fraction of budget.
    budget_cap = budget

    # If my hp is critically low, prioritize survival by bidding closer to salary.
    if hp <= 2:
        target = max(target, DAILY_SALARY * 0.75)
    elif hp <= 4:
        target = max(target, DAILY_SALARY * 0.6)

    # If budget is too low, scale down proportionally
    if budget < DAILY_SALARY * 0.2:
        target = min(target, budget)
    else:
        # Do not exceed ~1.1 salary to prevent waste
        target = min(target, DAILY_SALARY * 1.1)

    bid = min(budget_cap, target)

    # Ensure non-negative
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

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    # Estimate opponent pressure from yesterday's trace bids
    prev_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    prev_bids.append(float(b))
                except Exception:
                    pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Base aggressiveness depends on supply: lower supply needs stronger bidding to avoid no-water days.
    # supply in [15,25] => aggressiveness in [0.75,0.45]
    if MAX_SUPPLY - MIN_SUPPLY <= 0:
        supply_factor = 0.6
    else:
        t = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
        supply_factor = 0.75 - 0.30 * t

    # React to yesterday's observed peak bids (Cindy/Alex were aggressive)
    # If someone bid near/above our daily salary, we match pressure slightly below to preserve budget.
    pressure_factor = 0.0
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        pressure_factor = 0.15
    elif highest_prev_bid >= DAILY_SALARY * 0.60:
        pressure_factor = 0.08
    else:
        pressure_factor = 0.00

    # If I'm already low HP or have accumulated no-water days, bid harder.
    hp = float(my_status['hp'])
    no_water_days = int(my_status['no_water_days'])
    budget = float(my_status['budget'])

    urgency = 0.0
    if hp <= 2.0:
        urgency = 0.30
    elif hp <= 4.0:
        urgency = 0.18
    elif no_water_days >= 2:
        urgency = 0.12
    elif no_water_days >= 1:
        urgency = 0.06

    target_fraction = supply_factor + pressure_factor + urgency
    # Clamp target_fraction
    if target_fraction < 0.30:
        target_fraction = 0.30
    if target_fraction > 0.95:
        target_fraction = 0.95

    # Convert fraction into bid amount; keep within budget.
    # Also ensure we don't overpay when budget is low.
    bid = DAILY_SALARY * target_fraction
    if budget < bid:
        bid = budget

    # Safety: if budget is extremely low, bid minimal nonzero to try to avoid complete starvation.
    if bid <= 0.0:
        return 0.0

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

    # Basic safety: if we are in danger, bid aggressively to secure water.
    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    # If no opponents, take what we can.
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday bids from previous_trace only.
    yesterday_bids = []
    yesterday_hp_after = []
    for opp_id, opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid', 0.0)))
                yesterday_hp_after.append(float(prev.get('hp_after', prev.get('hp', 0.0))))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how many water units might be available; use for baseline aggressiveness.
    # Ensure indices are int-safe even if we later use arrays (we don't).
    # If supply is closer to 15, competition is tighter -> bid higher.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Baseline bid: enough to beat typical mid bidders, but not chase Cindy's extreme.
    # Map supply_ratio: when supply is low, bid higher.
    baseline = DAILY_SALARY * (0.55 + (0.5 - supply_ratio) * 0.25)  # ~0.55-0.80 of salary

    # If someone previously bid extremely high, we may need to respond, but avoid overpaying.
    # Cindy max ~142.5 suggests extreme pressure; Alex/Eric indicate collapse when outbid.
    if highest_prev_bid >= DAILY_SALARY * 1.35:  # >=121.5
        # If we are healthy, we can let them fight; if low hp or no-water streak, counter.
        if hp <= 2.5 or no_water_days >= 2:
            bid = DAILY_SALARY * 0.9
        else:
            bid = baseline * 0.75
    elif highest_prev_bid >= DAILY_SALARY * 0.75:  # >=67.5
        # Moderate pressure: bid near baseline.
        if hp <= 2.5 or no_water_days >= 2:
            bid = baseline * 1.05
        else:
            bid = baseline
    else:
        # Low pressure: bid just enough.
        bid = DAILY_SALARY * 0.5

    # Convert bid into water-need-aware cap: if we have lots of no-water days, prioritize more.
    # This is a heuristic to avoid running out.
    if no_water_days >= 3:
        bid *= 1.15
    if hp <= 1.5:
        bid *= 1.25

    # Final clamp by budget.
    bid = max(0.0, float(bid))
    bid = min(bid, budget)

    # Ensure we don't bid trivially when we must survive; but also don't exceed budget.
    # If budget is very small, bid what we can.
    if budget <= 10.0:
        return budget

    # Soft lower bound: bid at least a fraction of salary when hp is low.
    if hp <= 2.5:
        bid = max(bid, DAILY_SALARY * 0.65)
        bid = min(bid, budget)

    return bid
"""
