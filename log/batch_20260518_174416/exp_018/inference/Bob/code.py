# ============================================================
# Experiment: exp_018
# Agent: Bob
# Source: exp_018
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Alive opponents
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    # If no opponents, conserve
    if not alive_opps:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.45))

    # Read yesterday's bids from previous_trace
    prev_bids = []
    prev_max_bid = None
    prev_second_max = None
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict) and prev.get('bid') is not None:
            b = float(prev.get('bid'))
            prev_bids.append(b)

    if prev_bids:
        prev_bids_sorted = sorted(prev_bids, reverse=True)
        prev_max_bid = prev_bids_sorted[0]
        prev_second_max = prev_bids_sorted[1] if len(prev_bids_sorted) > 1 else prev_max_bid

    # Determine aggressiveness threshold from their prior behavior
    # If they were bidding near our daily salary, they likely need water urgently.
    urgent_level = 0.0
    if prev_max_bid is not None:
        urgent_level = prev_max_bid / DAILY_SALARY

    # Estimate supply scarcity pressure: lower supply => more competitive bidding
    scarcity = 0.0
    if supply <= float(WATER_REQ):
        scarcity = 1.0
    else:
        scarcity = (float(MAX_SUPPLY) - supply) / (float(MAX_SUPPLY) - float(MIN_SUPPLY) + 1e-9)
        scarcity = max(0.0, min(1.0, scarcity))

    # Base bid fraction: conservative unless they were aggressive or scarcity is high
    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # If we're in danger, increase bids.
    danger = 0.0
    if hp <= 2.0:
        danger = 1.0
    elif hp <= 3.5:
        danger = 0.6
    else:
        danger = 0.2

    if no_water_days >= 2:
        danger = max(danger, 0.7)

    # Compute target bid.
    # - If opponents previously bid high, try to slightly overtake.
    # - Otherwise, bid around a moderate level with a buffer based on scarcity.
    if prev_max_bid is not None:
        if urgent_level >= 0.85:
            # They likely value survival; outbid by a small increment.
            target = prev_max_bid + 2.0
        elif urgent_level >= 0.55:
            # Mid pressure: either match or slightly above second max.
            target = prev_second_max + 1.0
        else:
            # Low pressure: don't overpay; bid near a scarcity-adjusted baseline.
            baseline = DAILY_SALARY * (0.35 + 0.25 * scarcity)
            target = max(baseline, prev_max_bid * 0.9)
    else:
        baseline = DAILY_SALARY * (0.35 + 0.25 * scarcity)
        target = baseline

    # Adjust for our danger and scarcity.
    target *= (0.85 + 0.3 * danger + 0.15 * scarcity)

    # Ensure we don't bid irrationally high.
    # Cap at a fraction of budget and daily salary.
    cap = min(budget, DAILY_SALARY * (0.95 if danger >= 0.6 else 0.65))
    bid = max(0.0, min(float(target), float(cap)))

    # If our budget is tiny, still bid something non-negative.
    if bid <= 0.0:
        bid = min(float(budget), DAILY_SALARY * 0.1)

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

    my_hp = float(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    # If no opponents, bid to cover requirement.
    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Read yesterday bids from previous_trace for immediate reaction.
    prev_bids = []
    for opp_id, opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Baseline from observed behavior.
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    lowest_prev_bid = min(prev_bids) if prev_bids else 0.0

    # Estimate how many water units are likely available; use to scale aggressiveness.
    # (We only need a rough pressure signal.)
    supply_units = int(supply / float(WATER_REQ)) if WATER_REQ > 0 else 0
    if supply_units < 1:
        supply_units = 1

    # Determine target bid level.
    # If my HP is critical, I must secure water.
    if my_hp <= 2.0 or my_no_water_days >= 2:
        # Aggressive: bid near/above yesterday leader but cap by budget.
        target = max(highest_prev_bid * 0.98, DAILY_SALARY * 0.85)
    else:
        # Otherwise, try to outbid the lower-mid competitor (Eric-like behavior) rather than the leader.
        # Use supply to decide whether to be more or less aggressive.
        if supply >= 20.0:
            # High supply: leader may be overbidding; still bid slightly above typical mid.
            target = max(DAILY_SALARY * 0.62, lowest_prev_bid + 10.0)
        else:
            # Moderate supply: push closer to leader if they likely contest.
            target = max(DAILY_SALARY * 0.55, lowest_prev_bid + 7.0)

        # If yesterday leader was extremely high, avoid getting undercut.
        if highest_prev_bid >= DAILY_SALARY * 1.15:
            target = max(target, highest_prev_bid * 0.9)

    # Ensure we don't exceed budget and keep within reasonable bounds.
    # Also avoid bidding too low when supply is tight.
    tight_supply = (supply <= 16.5)
    if tight_supply:
        target = max(target, DAILY_SALARY * 0.7)

    bid = min(my_budget, max(0.0, target))
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

    supply = day_context.get('supply', 0)
    day = day_context.get('day', 0)

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    # Base affordability
    budget = float(my_status.get('budget', 0.0))
    hp = int(my_status.get('hp', 0))

    # If we are in critical HP, prioritize survival
    if hp <= 2:
        return max(0.0, min(budget, DAILY_SALARY * 0.9))

    # Use only yesterday's immediate trace bids
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        if prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # Estimate how many allocations are plausible given supply and our requirement
    # (Use int indices safely; no lists here, but keep consistent.)
    supply_int = int(round(float(supply)))
    capacity = max(1, supply_int // WATER_REQ)

    # Determine pressure from opponents' yesterday bids
    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / float(len(prev_bids))

        # If they were bidding aggressively, we must match at a fraction to avoid losing
        if highest_prev >= DAILY_SALARY * 0.85:
            # Match pressure but not fully; assume competition splits water
            bid = DAILY_SALARY * 0.35
            # If our HP is healthy, slightly underbid to save budget
            if hp >= 5:
                bid = DAILY_SALARY * 0.28
            # If our HP is mid, bid closer
            elif hp >= 3:
                bid = DAILY_SALARY * 0.38
            # Use a small bump based on highest_prev to stay competitive
            bid = max(bid, min(budget, highest_prev * 0.62))
            return max(0.0, min(budget, bid))

        # Moderate bids: bid around average but cap by our budget and supply pressure
        # If supply likely tight (<=18), raise a bit.
        tight = 1 if supply_int <= 18 else 0
        bid = max(DAILY_SALARY * 0.45, avg_prev * 0.75 + tight * 10.0)
        return max(0.0, min(budget, bid))

    # No opponent traces available: conservative mid bid
    tight = 1 if supply_int <= 18 else 0
    bid = DAILY_SALARY * 0.5 + tight * 12.0
    return max(0.0, min(budget, bid))
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

    # Alive opponents
    alive = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive.append(opp)

    if not alive:
        return min(my_status.get('budget', 0.0), DAILY_SALARY * 0.4)

    # Read yesterday bids and pressure signals
    yesterday_bids = []
    for opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                yesterday_bids.append(float(bid))
            except Exception:
                pass

    # Estimate how much water is likely available relative to our requirement
    # (Used only to scale bid aggressiveness; indices are not needed here.)
    supply_units = supply / float(WATER_REQ) if WATER_REQ else 0.0

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))

    # Determine aggressiveness from yesterday outcomes
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    # If we expect strong competition (high bids yesterday), bid enough to avoid shortage.
    # If we are low HP, bid more.
    competition = 0.0
    if highest_prev_bid >= DAILY_SALARY * 1.2:
        competition = 1.0
    elif highest_prev_bid >= DAILY_SALARY * 0.8:
        competition = 0.7
    elif highest_prev_bid >= DAILY_SALARY * 0.4:
        competition = 0.4
    else:
        competition = 0.2

    hp_pressure = 0.0
    if my_hp <= 1.5:
        hp_pressure = 1.0
    elif my_hp <= 3.0:
        hp_pressure = 0.7
    elif my_hp <= 5.0:
        hp_pressure = 0.4
    else:
        hp_pressure = 0.2

    # Base bid targets: keep within budget and avoid overpaying.
    # When supply is tight (closer to MIN_SUPPLY), increase bids.
    tightness = 0.0
    if supply <= float(MIN_SUPPLY) + 0.5:
        tightness = 0.8
    elif supply <= float(MIN_SUPPLY) + 3.0:
        tightness = 0.5
    else:
        tightness = 0.25

    # Target bid heuristic
    # - If competition is high, anchor near avg/highest but cap at 0.95*budget.
    # - Otherwise, bid around 0.55*salary, adjusted by hp and tightness.
    if competition >= 0.7:
        target = max(avg_prev_bid, highest_prev_bid * 0.75)
        target *= (0.85 + 0.25 * hp_pressure + 0.15 * tightness)
    else:
        target = DAILY_SALARY * (0.45 + 0.35 * hp_pressure + 0.25 * tightness)

    # Additional scaling: if supply_units is low (<1.5), competition for full water is higher.
    if supply_units < 1.5:
        target *= 1.15

    # Final clamp
    max_affordable = my_budget
    if max_affordable <= 0:
        return 0.0

    bid = min(max_affordable, target)

    # Ensure we don't bid trivially when we still have budget and opponents likely bid for survival.
    min_reasonable = 0.15 * DAILY_SALARY
    if bid < min_reasonable and my_budget > min_reasonable:
        bid = min_reasonable

    # Also avoid bidding more than 95% of budget.
    bid = min(bid, 0.95 * my_budget)

    # Return as float
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

    # Alive opponents and yesterday bids
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        # No contest; bid modestly
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.4))

    yesterday_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Estimate aggressiveness from yesterday
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        avg_prev = sum(yesterday_bids) / float(len(yesterday_bids))
    else:
        highest_prev = 0.0
        avg_prev = 0.0

    # Base target: aim to win without matching Cindy's extreme behavior.
    # If someone previously bid very high, we slightly back off and rely on not overpaying.
    # If bids were generally low, we bid enough to secure.
    # Also incorporate my hp: lower hp => more aggressive to avoid death.
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    # Supply-aware heuristic: more supply reduces need to overbid.
    # Normalize supply into [0,1]
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_norm = 0.5
    supply_norm = max(0.0, min(1.0, supply_norm))

    # Determine aggressiveness factor
    if hp <= 2:
        hp_factor = 0.95
    elif hp <= 4:
        hp_factor = 0.75
    else:
        hp_factor = 0.60

    # Bid level selection
    # If highest_prev is extreme (>= 120), don't chase; use a mid bid.
    if highest_prev >= 120.0:
        base = DAILY_SALARY * (0.35 + 0.15 * (1.0 - supply_norm))
        # If average was also high, increase somewhat
        if avg_prev >= 60.0:
            base *= 1.15
    elif highest_prev >= 60.0:
        base = DAILY_SALARY * (0.45 + 0.15 * (1.0 - supply_norm))
    else:
        base = DAILY_SALARY * (0.55 + 0.10 * (1.0 - supply_norm))

    bid = base * hp_factor

    # Ensure we bid at least enough to plausibly secure 1 unit of water requirement.
    # Convert supply to estimated number of water units available.
    # We avoid float indices; this is just a scalar heuristic.
    # Target probability of winning increases with bid but we cap to budget.
    # Use a soft floor based on my water requirement.
    # If supply is low, be more aggressive.
    if supply < WATER_REQ:
        bid *= 1.25

    # Final cap
    bid = max(0.0, min(bid, budget, DAILY_SALARY * 0.9))

    # If budget is extremely low, bid whatever remains
    if budget <= 1.0:
        return max(0.0, budget)

    # If bidding too low could guarantee no water, enforce a minimal bid fraction
    # (still capped by budget)
    min_bid = DAILY_SALARY * 0.25
    if bid < min_bid and budget >= min_bid:
        bid = min_bid

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

    # Alive opponents
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append(o)

    # If no one alive, take what you can
    if not alive:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace
    prev_bids = []
    for o in alive:
        pt = o.get('previous_trace', {}) or {}
        b = pt.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev = max(prev_bids) if prev_bids else 0.0

    # Base aggressiveness by current HP
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # If we are at risk, bid high enough to secure water.
    if hp <= 2 or no_water_days >= 2:
        target = DAILY_SALARY * 0.85
    else:
        # If others were extremely aggressive yesterday, we can undercut to save budget.
        # Cindy/Eric showed very high bids (~115-128) while low-bid players died.
        if highest_prev >= DAILY_SALARY * 1.2:
            # Underbid relative to their peak while still trying to win at moderate supply.
            target = DAILY_SALARY * 0.55
        else:
            # Otherwise, bid around a mid level.
            target = DAILY_SALARY * 0.65

    # Adjust by supply: higher supply -> lower bid needed; lower supply -> slightly higher
    # Normalize supply within [MIN_SUPPLY, MAX_SUPPLY]
    if MAX_SUPPLY > MIN_SUPPLY:
        t = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        t = 0.5
    # t in [0,1] ideally
    if t < 0.0:
        t = 0.0
    if t > 1.0:
        t = 1.0

    # When supply is low, increase bid; when high, decrease
    target = target * (1.10 - 0.20 * t)

    # Never bid more than budget
    bid = max(0.0, min(budget, target))

    # Small day-based modulation to avoid exact ties
    bid = bid * (0.98 + (day % 5) * 0.01)

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

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    hp = my_status.get('hp', 0)
    budget = my_status.get('budget', 0.0)
    no_water_days = my_status.get('no_water_days', 0)

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    if not alive_opponents:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from immediate previous_trace only
    prev_bids = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Baseline: if my hp is low or I've already missed water, bid aggressively
    pressure = 0.0
    if hp <= 2:
        pressure += 1.0
    if no_water_days >= 1:
        pressure += 0.6
    if hp <= 4:
        pressure += 0.4

    # Determine opponent pressure from yesterday
    if prev_bids:
        highest_prev = max(prev_bids)
        # If someone heavily outbid yesterday, raise slightly to contest.
        if highest_prev >= DAILY_SALARY * 0.85:
            base = DAILY_SALARY * (0.35 + 0.25 * pressure)
        elif highest_prev >= DAILY_SALARY * 0.6:
            base = highest_prev * (0.75 + 0.15 * pressure)
        else:
            base = max(DAILY_SALARY * 0.45, highest_prev + 2.0) * (0.9 + 0.1 * pressure)
    else:
        base = DAILY_SALARY * (0.55 + 0.2 * pressure)

    # Supply-aware adjustment: when supply is tighter, bid higher.
    # supply is float; map to a 0..1 tightness score.
    tightness = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        tightness = (float(MAX_SUPPLY) - float(supply)) / float(MAX_SUPPLY - MIN_SUPPLY)
    tightness = max(0.0, min(1.0, tightness))

    base = base * (0.85 + 0.3 * tightness)

    # Keep within reasonable bounds to avoid going broke.
    # If budget is low, cap at budget.
    target = max(0.0, min(budget, base))

    # If budget is extremely low, still try to secure water when hp is critical.
    if budget <= DAILY_SALARY * 0.15:
        if hp <= 2 or no_water_days >= 1:
            target = max(0.0, min(budget, DAILY_SALARY * 0.95))
        else:
            target = max(0.0, min(budget, DAILY_SALARY * 0.35))

    # Final guard: never bid negative.
    return float(max(0.0, target))
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

    supply = day_context['supply']
    day = day_context['day']

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # If no opponents are alive, conserve budget.
    if not alive_opps:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday behavior (immediate reaction only)
    prev_bids = []
    prev_hp = []
    for oid, o in alive_opps:
        pt = o.get('previous_trace', None) or {}
        if pt and pt.get('bid') is not None:
            try:
                prev_bids.append(float(pt['bid']))
            except Exception:
                pass
        # also capture yesterday hp_after to infer aggressiveness/pressure
        if pt and pt.get('hp_after') is not None:
            try:
                prev_hp.append(float(pt['hp_after']))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    # Supply pressure: if supply is closer to MIN_SUPPLY, competition is tighter.
    # Normalize to [0,1] where 0 => MIN_SUPPLY, 1 => MAX_SUPPLY
    try:
        t = (float(supply) - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    except Exception:
        t = 0.5
    t = max(0.0, min(1.0, t))
    tightness = 1.0 - t

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])

    # Base bid target: aim around a fraction of DAILY_SALARY.
    # If tightness is high, increase.
    base = DAILY_SALARY * (0.52 + 0.18 * tightness)

    # If opponents bid aggressively yesterday, counter with a slight overbid.
    # But cap by what we can afford.
    bid = base

    # Cindy died with 0 bid; ignore if present, but if others still bid high, respond.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # High pressure: bid near high but not maximal.
        if my_hp > 4:
            bid = max(bid, min(my_budget, highest_prev_bid * 0.92 + 2.0))
        else:
            bid = max(bid, min(my_budget, highest_prev_bid * 1.00 + 4.0))
    elif highest_prev_bid > 0:
        # Moderate competition: bid around avg or slightly above.
        target = max(base, avg_prev_bid * (0.85 + 0.1 * (1.0 - tightness)))
        bid = max(bid, target)

    # Survival safeguard: if my HP is critical, spend more to secure water.
    if my_hp <= 2.0:
        bid = max(bid, DAILY_SALARY * 0.95)
    elif my_hp <= 4.0:
        bid = max(bid, DAILY_SALARY * 0.75)

    # Budget cap
    if my_budget <= 0.0:
        return 0.0

    bid = min(bid, my_budget)

    # If supply is very low (near MIN_SUPPLY), slightly increase to avoid being priced out.
    if float(supply) <= float(MIN_SUPPLY) + 0.5:
        bid = min(my_budget, bid * 1.08)

    # Final clamp
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

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opponents = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opponents:
        # If alone, bid enough to secure water but avoid overpaying.
        cap = int(min(my_budget, DAILY_SALARY * 0.5))
        return max(0, cap)

    # Read yesterday's bids from previous_trace only.
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Convert supply to an approximate number of water units we can cover if we win.
    # (We don't know exact allocation rule; use it only for bid scaling.)
    # Ensure integer indices if any list were used; here we avoid lists.
    supply_units = float(supply) / float(WATER_REQ)

    # Pressure-based bidding: if others were bidding near/above typical salary thresholds,
    # we raise our bid to avoid losing water.
    pressure_level = 0.0
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        pressure_level = 1.0
    elif highest_prev_bid >= DAILY_SALARY * 0.6:
        pressure_level = 0.7
    elif highest_prev_bid > 0:
        pressure_level = 0.45

    # Our urgency increases with low hp and consecutive no-water days.
    urgency = 0.0
    if my_hp <= 2:
        urgency = 1.0
    elif my_hp <= 4:
        urgency = 0.7
    else:
        urgency = 0.4

    if my_no_water_days >= 2:
        urgency = max(urgency, 0.85)
    elif my_no_water_days >= 1:
        urgency = max(urgency, 0.6)

    # Base bid anchored to pressure and urgency.
    # Target slightly above highest_prev_bid when pressure is high; otherwise stay moderate.
    if pressure_level >= 1.0:
        target = highest_prev_bid + 2.0
    elif pressure_level >= 0.7:
        target = max(highest_prev_bid * 0.85, DAILY_SALARY * 0.55)
    else:
        target = max(DAILY_SALARY * 0.45, highest_prev_bid * 0.7)

    # Adjust for our urgency and supply scarcity.
    # If supply is near minimum, bidding should be higher.
    scarcity = 0.0
    if float(supply) <= float(MIN_SUPPLY) + 0.5:
        scarcity = 1.0
    elif float(supply) <= float((MIN_SUPPLY + MAX_SUPPLY) / 2.0):
        scarcity = 0.6
    else:
        scarcity = 0.3

    target = target * (0.85 + 0.35 * urgency + 0.2 * scarcity)

    # Safety caps: never exceed budget; also avoid extreme bids.
    # Use budget-aware cap to preserve survival.
    max_reasonable = min(my_budget, DAILY_SALARY * 1.2 + 0.5)
    bid = int(min(max_reasonable, max(0.0, target)))

    # If we are extremely low on hp, ensure we bid aggressively but still within budget.
    if my_hp <= 1:
        bid = int(min(my_budget, DAILY_SALARY * 1.05))

    return max(0, bid)
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

    # Collect alive opponents and their yesterday bids
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # If no opponents, just ensure survival
    if not alive_opps:
        return min(float(my_status['budget']), DAILY_SALARY * 0.4)

    # Read yesterday trace bids (only immediate reaction)
    prev_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    my_hp = float(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0) or 0)

    # Base aggressiveness: react to whether others bid very high yesterday
    # Cindy died after low bids; Eric/Alex survived with high bids.
    pressure = 0.0
    if highest_prev_bid >= DAILY_SALARY * 1.5:
        pressure = 1.0
    elif highest_prev_bid >= DAILY_SALARY * 1.0:
        pressure = 0.7
    elif highest_prev_bid >= DAILY_SALARY * 0.6:
        pressure = 0.4
    else:
        pressure = 0.2

    # Supply sensitivity: if supply is scarce, bid more to secure enough allocation.
    # Normalize supply to [0,1] where 0=MIN_SUPPLY, 1=MAX_SUPPLY
    if MAX_SUPPLY > MIN_SUPPLY:
        s_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        s_norm = 0.5
    s_norm = max(0.0, min(1.0, float(s_norm)))

    scarcity = 1.0 - s_norm  # higher when supply is low

    # If we're close to starvation (low hp or many no-water days), increase bid.
    urgency = 0.0
    if my_hp <= 2.0:
        urgency = 1.0
    elif my_hp <= 4.0:
        urgency = 0.7
    elif no_water_days >= 2:
        urgency = 0.5
    else:
        urgency = 0.2

    # Decide target bid budget fraction.
    # Keep it moderate unless urgency+pressure is high.
    frac = 0.35 + 0.25 * pressure + 0.20 * scarcity + 0.25 * urgency
    # Cap to avoid overspending early
    frac = max(0.25, min(0.95, frac))

    target = my_budget * frac

    # Ensure at least a minimum to compete when pressure is high
    min_compete = DAILY_SALARY * (0.35 + 0.25 * pressure + 0.15 * scarcity)
    target = max(target, min_compete)

    # If we have very low budget, scale down to avoid going to zero
    if my_budget <= DAILY_SALARY * 0.25:
        target = min(my_budget, DAILY_SALARY * 0.6)

    # Final safety cap
    bid = min(my_budget, target)

    # If bid is too tiny, still bid something to avoid tie disadvantage
    if bid < 1.0:
        bid = min(my_budget, 1.0)

    return float(bid)
"""
