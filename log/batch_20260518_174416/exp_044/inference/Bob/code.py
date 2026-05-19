# ============================================================
# Experiment: exp_044
# Agent: Bob
# Source: exp_044
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

    # Alive opponents
    alive_opps = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opps.append(opp)

    # If no opponents, bid moderately based on budget
    if len(alive_opps) == 0:
        target = DAILY_SALARY * 0.45
        return min(my_status['budget'], target)

    # Read yesterday bids from previous_trace for immediate reaction
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # Pressure estimate from yesterday
    if len(yesterday_bids) > 0:
        highest_prev_bid = max(yesterday_bids)
        second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid
    else:
        highest_prev_bid = 0.0
        second_prev_bid = 0.0

    # Determine how aggressive to be
    # If someone bid very high yesterday, they likely need water soon.
    high_threshold = DAILY_SALARY * 0.85
    mid_threshold = DAILY_SALARY * 0.60

    # Budget/HP urgency
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status.get('no_water_days', 0))

    urgency = 0.0
    if hp <= 2.0:
        urgency += 1.0
    elif hp <= 4.0:
        urgency += 0.6
    if no_water_days >= 2:
        urgency += 0.6
    elif no_water_days == 1:
        urgency += 0.3

    # Supply-based scaling: lower supply => more competitive bidding
    # Map supply in [MIN_SUPPLY, MAX_SUPPLY] to competitiveness in [1.1, 0.85]
    if supply <= float(MIN_SUPPLY):
        supply_factor = 1.1
    elif supply >= float(MAX_SUPPLY):
        supply_factor = 0.85
    else:
        # linear interpolation
        supply_factor = 1.1 - (supply - float(MIN_SUPPLY)) * (1.1 - 0.85) / (float(MAX_SUPPLY) - float(MIN_SUPPLY))

    # Base bid target
    if highest_prev_bid >= high_threshold:
        # Opponents were under heavy pressure; outbid slightly but avoid paying full ceiling.
        # Use second_prev_bid to avoid extreme overbids when multiple opponents were high.
        target = max(DAILY_SALARY * 0.30, min(budget, (second_prev_bid + 5.0) * supply_factor))
        # If very urgent, increase
        if urgency >= 1.0:
            target = max(target, DAILY_SALARY * 0.55)
    elif highest_prev_bid >= mid_threshold:
        # Moderate aggression: bid around the leader but not fully.
        target = max(DAILY_SALARY * 0.35, min(budget, (highest_prev_bid * 0.92) * supply_factor))
        if urgency >= 0.8:
            target = max(target, DAILY_SALARY * 0.50)
    else:
        # Conservative yesterday: secure water with a mid bid.
        # Scale with urgency and supply
        target = DAILY_SALARY * (0.40 + 0.20 * urgency)
        target = target * supply_factor

    # Ensure bid does not exceed budget
    bid = min(budget, target)

    # If budget is tiny, bid whatever possible
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Alive opponents only
    alive_opps = []
    for oid, o in opponents_status.items():
        try:
            if o.get('alive', False):
                alive_opps.append(o)
        except Exception:
            pass

    # If no opponents, bid conservatively
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace for immediate reaction
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

    # Estimate how many water units are likely available; use this only to tune aggressiveness
    # (We don't know exact consumption mapping, but higher supply means we can bid less.)
    approx_units = int(supply / float(WATER_REQ)) if WATER_REQ > 0 else 0

    # Pressure model from yesterday: if someone bid very high, match just enough to compete.
    # Alex's behavior indicates threshold around ~0.85*DAILY_SALARY.
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    # Base target bid depending on supply
    if supply <= float(MIN_SUPPLY) + 0.5:
        base = DAILY_SALARY * 0.65
    elif supply >= float(MAX_SUPPLY) - 0.5:
        base = DAILY_SALARY * 0.45
    else:
        base = DAILY_SALARY * 0.55

    # If yesterday someone was extremely aggressive, increase bid to avoid being the next to die.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        if hp > 3.0:
            target = max(base, highest_prev_bid * 0.55 + 0.15 * DAILY_SALARY)
        else:
            target = max(base, highest_prev_bid * 0.75 + 0.1 * DAILY_SALARY)
    else:
        # Otherwise, slightly over base or near the leader to secure at least one allocation.
        target = max(base, highest_prev_bid + 2.0)

    # If my HP is low, bid higher; if HP is high, bid slightly lower.
    if hp <= 2.0:
        target *= 1.15
    elif hp >= 6.0:
        target *= 0.95

    # If supply is scarce (few units), bid more.
    if approx_units <= 1:
        target *= 1.08

    # Final cap by budget
    bid = float(min(budget, target))

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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday bids for immediate pressure.
    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Estimate scarcity pressure from supply.
    # How many full allocations of WATER_REQ fit into supply range.
    # Use int index safety only for lists; here we avoid indexing.
    # Higher scarcity => bid more.
    scarcity = 0.0
    if supply <= WATER_REQ:
        scarcity = 1.0
    else:
        # Normalize within [WATER_REQ, MAX_SUPPLY]
        scarcity = max(0.0, min(1.0, (MAX_SUPPLY - supply) / max(1e-9, (MAX_SUPPLY - WATER_REQ))))

    # Determine opponent aggressiveness from yesterday.
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    # Baseline: ensure we can survive multiple days by not overpaying.
    # If we are doing poorly (low hp / many no-water days), we must bid more.
    if my_hp <= 2 or my_no_water_days >= 2:
        base = DAILY_SALARY * (0.85 + 0.1 * scarcity)
    elif my_hp <= 4:
        base = DAILY_SALARY * (0.65 + 0.08 * scarcity)
    else:
        base = DAILY_SALARY * (0.52 + 0.06 * scarcity)

    # Exploit trace: Cindy spent heavily and survived; Alex/David died with low final budget.
    # If opponents previously bid very high, they are likely spending aggressively; we can shade down.
    # If opponents previously bid low, they may be conserving; then we should bid enough to secure water.
    # Thresholds tuned to observed averages/maxes.
    if highest_prev_bid >= 130.0:
        # Strong aggressors: shade down.
        bid = base * 0.85
    elif avg_prev_bid >= 95.0:
        # Moderate aggressors: slight shade.
        bid = base * 0.92
    elif highest_prev_bid <= 70.0:
        # Conservers: bid a bit more to win.
        bid = base * 1.05
    else:
        # Default: near base.
        bid = base

    # Additional micro-adjustment by day: late game should be more aggressive.
    # Episode is 10 days; meta_round_id=3 suggests mid-late. Use day fraction.
    day_frac = 0.0
    if day is not None:
        day_frac = max(0.0, min(1.0, float(day) / 10.0))
    bid *= (0.92 + 0.18 * day_frac)

    # Never exceed budget.
    bid = max(0.0, min(my_budget, bid))

    # Safety: if budget is too small, bid what we can.
    if my_budget <= 1e-6:
        return 0.0

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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    alive_opps = []
    for k, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # Base safety: if very low HP, buy maximum feasible water.
    if my_status['hp'] is not None and my_status['hp'] <= 2:
        return float(min(my_status['budget'], DAILY_SALARY * 0.95))

    # Read yesterday bids from immediate previous_trace only.
    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # If others heavily bid yesterday, slightly undercut to still secure allocation.
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # Estimate typical aggressive anchor around ~DAILY_SALARY.
        aggressive_anchor = DAILY_SALARY * 1.08  # ~97.2

        # Determine target bid: undercut highest but stay near anchor.
        # Also adjust by current supply: higher supply allows lower bid.
        supply_factor = 1.0
        if supply >= (MIN_SUPPLY + MAX_SUPPLY) / 2.0:
            supply_factor = 0.92
        else:
            supply_factor = 1.00

        # If they bid near anchor, bid just below highest.
        if highest_prev_bid >= aggressive_anchor * 0.95:
            target = min(highest_prev_bid - 1.0, aggressive_anchor) * supply_factor
        else:
            # Otherwise, bid around max(highest, half salary) with mild undercut.
            target = max(highest_prev_bid, DAILY_SALARY * 0.55) * supply_factor

        # Keep within budget and avoid overspending early.
        # Ensure we can sustain multiple days: leave some budget buffer.
        budget_cap = my_status['budget'] * 0.35 if day <= 3 else my_status['budget'] * 0.45
        bid = min(float(target), float(budget_cap), float(my_status['budget']))

        # If bid becomes too small relative to need, bump.
        if bid < DAILY_SALARY * 0.45 and my_status['hp'] is not None and my_status['hp'] <= 5:
            bid = min(float(my_status['budget']), DAILY_SALARY * 0.65)

        return float(max(0.0, bid))

    # No trace bids available: conservative mid bid.
    # If supply is low, bid higher to avoid no-water days.
    if supply < (MIN_SUPPLY + MAX_SUPPLY) / 2.0:
        return float(min(my_status['budget'], DAILY_SALARY * 0.65))
    return float(min(my_status['budget'], DAILY_SALARY * 0.55))
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
    day = day_context['day']

    # Alive opponents and yesterday bids (only immediate reaction)
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        # Conservative when alone
        cap = min(my_status['budget'], DAILY_SALARY * 0.4)
        return max(0.0, cap)

    yesterday_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                yesterday_bids.append(float(bid))
            except Exception:
                pass

    pressure = 0.0
    if yesterday_bids:
        pressure = max(yesterday_bids)

    # Supply pressure: with higher supply, we can bid slightly less; with lower supply, bid more.
    # Normalize supply to [0,1]
    denom = (MAX_SUPPLY - MIN_SUPPLY)
    if denom <= 0:
        supply_norm = 0.5
    else:
        supply_norm = (supply - MIN_SUPPLY) / denom
    if supply_norm < 0.0:
        supply_norm = 0.0
    if supply_norm > 1.0:
        supply_norm = 1.0

    # Base aggressiveness driven by our HP
    hp = float(my_status['hp'])
    if hp <= 2:
        hp_factor = 1.0
    elif hp <= 4:
        hp_factor = 0.85
    else:
        hp_factor = 0.65

    # If opponents were bidding near/above our salary yesterday, they are likely fighting for scarce water.
    if pressure >= DAILY_SALARY * 0.85:
        # Match their intensity but still slightly undercut to preserve budget
        target = pressure * 0.92
    elif pressure > 0.0:
        # Otherwise, bid enough to likely secure water without draining budget
        target = max(DAILY_SALARY * (0.45 + 0.2 * (1.0 - supply_norm)), pressure * 0.75)
    else:
        target = DAILY_SALARY * (0.5 + 0.25 * (1.0 - supply_norm))

    # Adjust with HP factor
    target = target * hp_factor

    # Ensure we don't bid more than budget
    budget = float(my_status['budget'])
    if budget <= 0.0:
        return 0.0

    # Soft cap: don't exceed a fraction of budget early/midgame
    # (episode_days=10, meta-round medium; keep some reserve)
    soft_cap = budget * 0.6
    final_bid = min(target, soft_cap, budget)

    # Avoid negative/zero bids if we can afford a meaningful bid
    if final_bid < 1.0:
        # If extremely low budget, bid whatever remains
        final_bid = min(budget, DAILY_SALARY * 0.15)

    # Clamp to non-negative
    if final_bid < 0.0:
        final_bid = 0.0

    return float(final_bid)
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

    # Identify alive opponents
    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append(o)

    # If alone, spend to guarantee water
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.6)

    # Read yesterday bids from traces (only immediate reaction)
    yesterday_bids = []
    for o in alive_opponents:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Determine market pressure
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = 0.0
    if len(yesterday_bids) >= 2:
        s = sorted(yesterday_bids, reverse=True)
        second_prev_bid = s[1]

    # Supply pressure: fewer water units means higher competition
    # Convert supply to an approximate number of water units available
    units = int(supply / float(WATER_REQ)) if float(WATER_REQ) > 0 else 0
    if units <= 0:
        units = 1

    # Base bid: moderate when supply is higher, aggressive when supply is lower
    # Normalize supply between MIN_SUPPLY..MAX_SUPPLY
    if MAX_SUPPLY > MIN_SUPPLY:
        t = (supply - float(MIN_SUPPLY)) / float(MAX_SUPPLY - MIN_SUPPLY)
    else:
        t = 0.5
    # t close to 0 => low supply => bid more
    supply_factor = 1.25 - 0.5 * t  # range about 1.25..0.75

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Urgency: if we're already close to death or have gone many days without water
    urgency = 0.0
    if hp <= 2.0:
        urgency = 1.0
    elif hp <= 4.0:
        urgency = 0.7
    elif no_water_days >= 3:
        urgency = 0.6
    elif no_water_days >= 2:
        urgency = 0.4
    else:
        urgency = 0.25

    # Decide target bid relative to yesterday highest bid.
    # If opponents were paying very high yesterday, we shadow just below to win when possible.
    # If their highest bid was moderate, we bid around it.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # High-pressure game: bid near (or slightly above) the likely clearing price.
        base = max(second_prev_bid + 2.0, highest_prev_bid * 0.92)
    elif highest_prev_bid > 0:
        base = max(highest_prev_bid * 0.75, second_prev_bid * 0.85)
    else:
        base = DAILY_SALARY * 0.55

    # Apply urgency and supply factor
    target = base * supply_factor * (1.0 + 0.35 * urgency)

    # Cap spending to avoid bankruptcy; also ensure we don't bid more than we can pay
    # Use a soft cap based on remaining budget and day index (early rounds can spend more)
    remaining_days_factor = 1.0
    if isinstance(day, (int, float)):
        try:
            remaining_days_factor = 1.15 if float(day) <= 3.0 else (1.0 if float(day) <= 7.0 else 0.85)
        except Exception:
            remaining_days_factor = 1.0

    cap = budget
    # Also cap at a fraction of daily salary to keep budget for later unless urgency is high
    salary_cap = DAILY_SALARY * (0.95 if urgency >= 0.7 else 0.65)
    cap = min(cap, salary_cap * remaining_days_factor)

    # Final bid: at least enough to be competitive, but not exceed cap
    floor_bid = DAILY_SALARY * (0.25 if urgency < 0.4 else 0.45)
    bid = min(max(target, floor_bid), cap)

    # If budget is tiny, just bid what we can
    if bid < 0:
        bid = 0.0
    if budget <= 0.0:
        return 0.0
    return float(min(bid, budget))
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Identify alive opponents
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        return max(0.0, min(float(my_status['budget']), DAILY_SALARY * 0.4))

    # Use yesterday trace to infer who is pressuring the market
    cindy_prev_bid = None
    max_prev_bid = None
    for opp_id, opp in opponents_status.items():
        if not opp.get('alive', False):
            continue
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid', None)
        if bid is None:
            continue
        if max_prev_bid is None:
            max_prev_bid = float(bid)
        else:
            max_prev_bid = max(max_prev_bid, float(bid))
        if opp_id == 'Cindy':
            cindy_prev_bid = float(bid)

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    # Determine a target bid band.
    # If Cindy previously bid very high, we anticipate a high clearing price and bid more to secure water.
    # Otherwise, bid conservatively to avoid overpaying.
    if cindy_prev_bid is not None and cindy_prev_bid >= 0.9 * 191.1:
        # High pressure from Cindy
        if hp > 4:
            bid = DAILY_SALARY * 0.55
        else:
            bid = DAILY_SALARY * 0.85
    elif max_prev_bid is not None and max_prev_bid >= DAILY_SALARY * 2.0:
        # Someone is splurging; slightly increase to stay competitive
        if hp > 4:
            bid = DAILY_SALARY * 0.6
        else:
            bid = DAILY_SALARY * 0.9
    else:
        # Market not extremely pressured; moderate bid
        if hp > 6:
            bid = DAILY_SALARY * 0.48
        elif hp > 3:
            bid = DAILY_SALARY * 0.62
        else:
            bid = DAILY_SALARY * 0.88

    # Ensure we don't bid more than budget and keep within a reasonable cap.
    bid = max(0.0, min(bid, budget))

    # If supply is low relative to our requirement, we should be more aggressive.
    # supply is between 15 and 25; if closer to 15, competition higher.
    if supply <= 16.0:
        bid = min(budget, bid * 1.15)
    elif supply >= 22.0:
        bid = bid * 0.95

    # Small day-based dithering to avoid ties.
    # Use int(day) for index safety.
    bid = bid + (0.5 if (day % 2 == 0) else 0.0)

    # Final clamp
    if bid < 0.0:
        bid = 0.0
    if bid > budget:
        bid = budget
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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace (immediate reaction only)
    yesterday_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Default target: secure water with a moderate bid; avoid Cindy-style overbidding
    # Supply affects how many bidders might need to be competitive.
    supply_factor = 1.0
    if supply <= float(MIN_SUPPLY):
        supply_factor = 1.15
    elif supply >= float(MAX_SUPPLY):
        supply_factor = 0.95

    # If we are in danger (multiple no-water days), bid more aggressively.
    if my_hp <= 2 or my_no_water_days >= 3:
        base = DAILY_SALARY * 0.95
    elif my_hp <= 4 or my_no_water_days >= 2:
        base = DAILY_SALARY * 0.75
    else:
        base = DAILY_SALARY * 0.55

    # Undercut strategy vs yesterday extremes: if someone overbid badly, don't match.
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        # If there was a very high bidder (likely Cindy), stay below that by a margin.
        if max_prev >= DAILY_SALARY * 1.25:
            # Use a cap just under the extreme to avoid price war.
            base = min(base * supply_factor, max(DAILY_SALARY * 0.65, max_prev - 25.0))
        else:
            # Otherwise, bid around the upper-middle of yesterday bids.
            sorted_b = sorted(yesterday_bids)
            idx = int(len(sorted_b) * 0.7) - 1
            if idx < 0:
                idx = 0
            mid_prev = sorted_b[idx]
            base = min(base * supply_factor, max(mid_prev + 1.0, base))

    # Convert bid to a feasible range
    bid = float(base)
    if bid > my_budget:
        bid = my_budget

    # Ensure non-negative
    if bid < 0.0:
        bid = 0.0

    # Small day-to-day jitter to avoid ties/predictability
    # (Deterministic, no randomness.)
    jitter = ((day % 5) - 2) * 0.8
    bid = bid + float(jitter)

    if bid > my_budget:
        bid = my_budget
    if bid < 0.0:
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

    supply = day_context['supply']
    day = day_context['day']

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Read yesterday bids from immediate previous_trace only
    prev_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Baseline from observed market pressure
    if prev_bids:
        prev_bids_sorted = sorted(prev_bids)
        n = len(prev_bids_sorted)
        median_bid = prev_bids_sorted[int(n // 2)]
        # 75th percentile-ish index
        idx75 = int((3 * n) // 4)
        if idx75 >= n:
            idx75 = n - 1
        high_bid = prev_bids_sorted[idx75]
    else:
        median_bid = DAILY_SALARY * 0.6
        high_bid = DAILY_SALARY * 0.85

    # If supply is high, we can afford to be more aggressive; if low, be conservative.
    # supply in [15,25]
    supply_ratio = 0.0
    try:
        supply_ratio = (float(supply) - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    except Exception:
        supply_ratio = 0.5

    # Decide aggression based on my HP
    hp = my_status['hp']
    budget = my_status['budget']

    # Target bid: slightly above median to beat cautious bidders, but below Cindy-like extremes.
    # Use high_bid as cap reference.
    target = median_bid + (10.0 * supply_ratio)

    # If my HP is critical, jump closer to high_bid.
    if hp <= 2:
        target = max(target, high_bid * 0.95)
    elif hp <= 4:
        target = max(target, median_bid * 0.95)

    # If supply is low, reduce spending to avoid overpaying.
    if supply_ratio < 0.35:
        target = min(target, median_bid + 5.0)

    # Never exceed budget; also keep within reasonable bounds relative to salary.
    # Salary-based soft cap prevents reckless bids.
    soft_cap = DAILY_SALARY * (0.95 if hp <= 2 else (0.75 if hp <= 4 else 0.65))
    target = min(target, soft_cap)

    bid = min(budget, max(0.0, target))

    # Ensure minimum meaningful bid when budget allows.
    if bid < DAILY_SALARY * 0.25 and budget >= DAILY_SALARY * 0.25:
        bid = DAILY_SALARY * 0.25

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

    supply = float(day_context['supply'])
    day = day_context['day']

    # Alive opponents and yesterday bids
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # If no opponents are alive, conserve budget
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.35))

    # Read yesterday bids only (immediate reaction)
    yesterday_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Estimate how competitive the market is based on yesterday
    comp = 0.0
    if yesterday_bids:
        high = max(yesterday_bids)
        avg = sum(yesterday_bids) / float(len(yesterday_bids))
        # Normalize: yesterday bids around 100-130 seem common; cap at 1
        comp = min(1.0, (avg + high) / 260.0)

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Base bid target: aim to win when supply is high; otherwise be stingier
    # Supply factor: 15->0.2, 25->0.8
    supply_factor = 0.2 + 0.6 * ((supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY))
    supply_factor = max(0.0, min(1.0, supply_factor))

    # Health pressure: if near death or already without water, increase bid
    pressure = 0.0
    if no_water_days >= 2:
        pressure += 0.35
    if hp <= 2.0:
        pressure += 0.55
    elif hp <= 4.0:
        pressure += 0.25

    # If competitive environment (others bid high), adjust upward slightly
    target = DAILY_SALARY * (0.38 + 0.22 * supply_factor + 0.25 * comp + pressure)

    # If yesterday had a very high bid, match a bit below that to avoid overpaying
    if yesterday_bids:
        high = max(yesterday_bids)
        # If market was extremely hot, don't go as high as the highest bidder; stay below by a margin
        if high >= DAILY_SALARY * 1.1:
            target = min(target, high * 0.78)

    # Budget-aware cap and floor
    # Ensure we can keep bidding but still try to secure water
    max_affordable = budget
    # Keep some reserve: if we have plenty of budget, don't spend it all early
    reserve_frac = 0.15 if hp > 4.0 else 0.05
    spend_cap = max_affordable * (1.0 - reserve_frac)

    bid = min(target, spend_cap)

    # If hp is critically low, spend more aggressively
    if hp <= 1.5:
        bid = min(max_affordable, max(bid, DAILY_SALARY * 0.85))

    # If budget is tiny, just bid what we can
    if bid < 0:
        bid = 0.0
    if budget <= 1.0:
        return float(budget)

    return float(bid)
"""
