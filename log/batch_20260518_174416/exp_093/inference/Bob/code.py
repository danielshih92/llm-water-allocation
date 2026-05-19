# ============================================================
# Experiment: exp_093
# Agent: Bob
# Source: exp_093
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
    day = int(day_context.get('day', 0))

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    # If no opponents, take the safe maximum we can afford.
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.8)

    # Read yesterday bids from previous_trace for immediate reaction.
    prev_bids = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Determine aggressiveness.
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        avg_prev_bid = sum(prev_bids) / float(len(prev_bids))
    else:
        highest_prev_bid = 0.0
        avg_prev_bid = 0.0

    # Supply pressure: when supply is scarce, increase bid to secure water.
    supply_ratio = (supply - float(MIN_SUPPLY)) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))
    scarcity_factor = 1.0 + (1.0 - supply_ratio) * 0.35  # up to +35% when near MIN_SUPPLY

    # Our urgency: low hp or consecutive no-water days increases bid.
    urgency = 1.0
    if hp <= 2:
        urgency = 1.25
    elif hp <= 3:
        urgency = 1.12

    if no_water_days >= 2:
        urgency *= 1.15

    # Core strategy:
    # - If opponents were paying near our salary, we bid to stay competitive but not max.
    # - If opponents were paying low, we slightly overbid the likely clearing price.
    competitive_threshold = DAILY_SALARY * 0.85

    if highest_prev_bid >= competitive_threshold:
        # Match competitiveness while preserving budget.
        target = max(avg_prev_bid, highest_prev_bid * 0.92)
        target *= 0.95
    else:
        # Assume clearing price closer to average; outbid modestly.
        # Add a small premium to beat ties.
        target = max(avg_prev_bid + 3.0, highest_prev_bid + 1.5)

    # Adjust with scarcity and urgency.
    target *= scarcity_factor
    target *= urgency

    # Ensure we don't bid more than we can afford.
    bid = min(budget, target)

    # Also keep a floor so we actually compete when necessary.
    # If budget is extremely low, just bid what we can.
    min_bid = min(budget, DAILY_SALARY * 0.35)
    if bid < min_bid:
        bid = min_bid

    # Final clamp to non-negative.
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
    day = int(day_context.get('day', 0))

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        return float(min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from alive opponents; use max as proxy for who is pressuring.
    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    pressure = max(yesterday_bids) if yesterday_bids else 0.0

    # Supply pressure: higher supply reduces need to overbid.
    # Normalize supply to [0,1]
    norm_supply = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        norm_supply = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
        if norm_supply < 0.0:
            norm_supply = 0.0
        if norm_supply > 1.0:
            norm_supply = 1.0

    # If others bid extremely high yesterday, they likely will again; avoid being the one starved.
    # Use HP/no_water_days to decide aggressiveness.
    if pressure >= DAILY_SALARY * 1.0:
        # Survivors likely outbid; we only need enough to secure water consistently.
        base = DAILY_SALARY * (0.45 + 0.25 * (1.0 - norm_supply))
        if my_hp <= 2 or my_no_water_days >= 1:
            base = DAILY_SALARY * 0.75
    elif pressure >= DAILY_SALARY * 0.6:
        base = DAILY_SALARY * (0.40 + 0.20 * (1.0 - norm_supply))
        if my_hp <= 2 or my_no_water_days >= 1:
            base = DAILY_SALARY * 0.62
    else:
        base = DAILY_SALARY * (0.35 + 0.15 * (1.0 - norm_supply))
        if my_hp <= 2 or my_no_water_days >= 1:
            base = DAILY_SALARY * 0.55

    # Slight day-based ramp to prevent late collapse.
    if day >= 7:
        base *= 1.08

    # Convert base into a bid with a small competitive premium.
    # If pressure exists, try to be near but not exceed it drastically.
    bid = base
    if pressure > 0.0:
        # Target: either just above a fraction of pressure or base whichever is higher.
        target = pressure * 0.55
        if target > bid:
            bid = target
        # Cap premium
        if bid > pressure * 0.85:
            bid = pressure * 0.85

    # Final clamp by budget and a safety floor.
    if my_budget <= 0.0:
        return 0.0

    # Ensure we don't bid more than budget.
    if bid > my_budget:
        bid = my_budget

    # If budget is tight, still bid something proportional.
    min_bid = 0.0
    if my_budget > 0.0:
        min_bid = min(DAILY_SALARY * 0.15, my_budget)

    if bid < min_bid:
        bid = min_bid

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

    # Alive opponents only
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append(o)

    # If no one else is alive, conserve
    if not alive:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids to infer pressure
    prev_bids = []
    for o in alive:
        prev = o.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    prev_bids.append(float(b))
                except Exception:
                    pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Base bid: tie/beat their typical aggression without burning budget
    # If they already bid near my salary, increase; otherwise match mid-high.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        base = DAILY_SALARY * 0.72
    elif highest_prev_bid >= DAILY_SALARY * 0.55:
        base = DAILY_SALARY * 0.62
    else:
        base = DAILY_SALARY * 0.50

    # Supply pressure: lower supply -> higher bids to avoid no-water days
    # supply in [15,25]
    supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0..1
    # When supply is low (norm near 0), add pressure
    supply_multiplier = 1.12 - 0.25 * supply_norm

    # My hp urgency
    hp = float(my_status['hp'])
    no_water_days = int(my_status['no_water_days'])
    if hp <= 1.5 or no_water_days >= 2:
        urgency = 1.25
    elif hp <= 3.0 or no_water_days == 1:
        urgency = 1.10
    else:
        urgency = 1.00

    bid = base * supply_multiplier * urgency

    # Ensure we never bid more than our budget
    bid = float(min(my_status['budget'], bid))

    # If budget is tiny, still bid something to avoid total starvation
    if bid <= 0.0:
        return 0.0

    # Small strategic floor to compete against typical bids (Alex/Cindy ~80-95)
    # but remain within budget.
    competitor_floor = 75.0
    if bid < competitor_floor and my_status['budget'] >= competitor_floor:
        bid = competitor_floor

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

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.35))

    # Extract yesterday bids from alive opponents
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # If opponent(s) were willing to spend very aggressively yesterday, raise slightly.
    # Cindy survived with very high average bid, so treat high prior bid as a signal.
    aggressive_threshold = DAILY_SALARY * 0.95  # 85.5

    # Base bid depends on our urgency (hp/no_water_days)
    urgency = 0
    if hp <= 2.0:
        urgency += 3
    if hp <= 4.0:
        urgency += 2
    if no_water_days >= 2:
        urgency += 2
    if no_water_days >= 3:
        urgency += 3

    # Supply pressure: lower supply means more competition; bid more.
    # Map supply in [15,25] to a factor in [1.25, 0.9]
    if MAX_SUPPLY > MIN_SUPPLY:
        t = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        t = 0.5
    t = max(0.0, min(1.0, float(t)))
    supply_factor = 1.25 - 0.35 * t

    if highest_prev_bid >= aggressive_threshold:
        # We expect aggressive contention; bid enough to avoid being starved,
        # but still keep budget for continued competition.
        base = DAILY_SALARY * 0.45
        if urgency >= 4:
            base = DAILY_SALARY * 0.75
        elif urgency >= 2:
            base = DAILY_SALARY * 0.6
        else:
            base = DAILY_SALARY * 0.5

        bid = base * supply_factor
        # Slightly undercut the highest prior bid to avoid waste while still contesting.
        bid = min(bid, highest_prev_bid * 0.92 + 2.0)
    else:
        # No extreme spending observed: bid moderately.
        base = DAILY_SALARY * 0.35
        if urgency >= 4:
            base = DAILY_SALARY * 0.65
        elif urgency >= 2:
            base = DAILY_SALARY * 0.5
        bid = base * supply_factor

    # Budget safety: never bid more than what we can afford while keeping some runway.
    # Reserve fraction increases when urgency is low.
    reserve_frac = 0.25
    if urgency <= 1:
        reserve_frac = 0.45
    elif urgency <= 3:
        reserve_frac = 0.35

    max_affordable = budget * (1.0 - reserve_frac)
    if max_affordable < 0.0:
        max_affordable = 0.0

    bid = max(0.0, min(bid, max_affordable, budget))

    # If we are critically low on HP, push harder.
    if hp <= 1.0:
        bid = max(bid, min(budget, DAILY_SALARY * 0.95))

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

    # Alive opponents and yesterday bids
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    yesterday_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Base bid depends on our HP and budget
    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    supply = float(day_context.get('supply', (MIN_SUPPLY + MAX_SUPPLY) / 2.0))
    # Approximate how many
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

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    if not alive_opponents:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from immediate trace only
    yesterday_bids = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # Estimate how hard the market is based on yesterday
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = 0.0
    if len(yesterday_bids) >= 2:
        sorted_b = sorted(yesterday_bids, reverse=True)
        second_prev_bid = sorted_b[1]

    # Aggression detection: if someone consistently bid very high, we can bid just under typical pressure.
    # Cindy survived with high bids yesterday -> likely top bidder.
    # We react by bidding moderately unless our HP is critical.
    # Supply pressure: higher supply reduces need to overbid.
    supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0..1 (approx)
    if supply_factor < 0.0:
        supply_factor = 0.0
    if supply_factor > 1.0:
        supply_factor = 1.0

    # Base target bid: try to be competitive but not match highest_prev_bid unless necessary.
    # Use a fraction of highest_prev_bid to avoid wasting budget.
    if highest_prev_bid > 0.0:
        # If highest_prev_bid is extremely high, bid around 65% of it (unless HP critical)
        base = highest_prev_bid * (0.65 + 0.15 * supply_factor)
    else:
        base = DAILY_SALARY * (0.45 + 0.2 * supply_factor)

    # HP/no-water urgency
    if hp <= 1.5:
        urgency_mult = 1.25
    elif hp <= 3.0:
        urgency_mult = 1.05
    else:
        urgency_mult = 0.95

    # If we've already gone multiple days without water, increase bid to avoid death spiral
    if no_water_days >= 3:
        urgency_mult += 0.15
    elif no_water_days >= 2:
        urgency_mult += 0.08

    target = base * urgency_mult

    # If yesterday pressure was very intense, we may need to bid closer to it.
    if highest_prev_bid >= DAILY_SALARY * 1.6:
        # Cindy-like behavior: still avoid full match unless needed.
        if hp <= 3.0 or no_water_days >= 2:
            target = max(target, highest_prev_bid * 0.85)
        else:
            target = max(target, highest_prev_bid * 0.7)

    # Keep within budget and sensible bounds
    # Also ensure we don't bid more than we can afford, and bid at least a small amount if budget allows.
    max_affordable = max(0.0, budget)
    bid = min(max_affordable, target)

    # If budget is too low, still try to bid something to compete.
    if bid <= 0.0:
        bid = min(max_affordable, DAILY_SALARY * 0.05)

    # Final clamp to non-negative
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

    # Collect yesterday bids from alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    yesterday_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {})
        if isinstance(prev, dict) and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Pressure estimate: if any opponent bid very high yesterday, expect competition today.
    high_pressure = False
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # Cindy/Eric were ~184+; treat >= 0.95*DAILY_SALARY as high pressure.
        if highest_prev_bid >= 0.95 * DAILY_SALARY:
            high_pressure = True

    # Base target based on current supply (more supply => can lower bid and still win water).
    # Use a simple piecewise heuristic.
    if supply >= 21.0:
        supply_factor = 0.95
    elif supply >= 18.0:
        supply_factor = 1.05
    else:
        supply_factor = 1.15

    # HP/urgency adjustment
    # If low hp or already had no-water days, bid more.
    urgency = 1.0
    if my_hp <= 2.0:
        urgency = 1.35
    elif my_hp <= 4.0:
        urgency = 1.20
    if my_no_water_days >= 2:
        urgency = max(urgency, 1.25)

    # If opponents show high pressure, increase bid to outcompete.
    pressure = 1.0
    if high_pressure:
        pressure = 1.25

    # Determine bid cap to avoid bankruptcy.
    # Keep some buffer for later days.
    budget_safety = 0.15
    max_affordable = max(0.0, my_budget * (1.0 - budget_safety))

    # Compute raw bid
    # Target around salary*0.55 normally; higher under pressure/urgency.
    target = DAILY_SALARY * 0.55 * supply_factor * urgency * pressure

    # If supply is scarce, bump further slightly.
    if supply <= 16.0:
        target *= 1.10

    # Ensure we don't bid below a minimal competitive amount when high pressure.
    if high_pressure:
        target = max(target, DAILY_SALARY * 0.75)

    bid = min(max_affordable, target)

    # If budget is tiny, just spend what we can.
    if my_budget <= 1.0:
        return 0.0

    # Final clamp
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Immediate reaction from yesterday trace
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate how tight supply is today
    # If supply is high, competition for water is lower (more total water), so bid less.
    # If supply is low, bid more to avoid being outbid.
    supply_tightness = (float(MAX_SUPPLY) - supply) / float(MAX_SUPPLY - MIN_SUPPLY + 1e-9)
    supply_tightness = max(0.0, min(1.0, supply_tightness))

    # Pressure from opponents: if someone bid very high yesterday, they likely will contest again.
    high_pressure = 1.0 if highest_prev_bid >= DAILY_SALARY * 0.8 else 0.0

    # If I'm in danger (low hp or already missing water), increase bid.
    danger = 0.0
    if my_hp <= 2:
        danger = 1.0
    elif my_hp <= 4:
        danger = 0.6
    if my_no_water_days >= 2:
        danger = max(danger, 0.7)

    # Base bid tuned for medium scenario: moderate to avoid overpaying vs Cindy/Eric.
    base = DAILY_SALARY * (0.45 + 0.25 * supply_tightness)

    # Adjustments
    bid = base
    if high_pressure > 0.0:
        bid *= (1.15 + 0.15 * supply_tightness)
    bid *= (1.0 + 0.55 * danger)

    # Cap by budget and avoid bidding too low when supply is tight.
    min_reasonable = DAILY_SALARY * (0.25 + 0.35 * supply_tightness)
    bid = max(min_reasonable, bid)

    # Final clamp
    bid = max(0.0, min(my_budget, bid))
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Alive opponents
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    # Base bid: aim for stable allocation when supply is medium
    # If supply is closer to MIN_SUPPLY, competition likely higher -> bid more.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Read yesterday's immediate pressure from opponents' previous bids
    prev_bids = []
    for oid, o in alive:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    highest_prev = max(prev_bids) if prev_bids else 0.0
    second_prev = 0.0
    if len(prev_bids) >= 2:
        s = sorted(prev_bids)
        second_prev = s[-2]

    # If opponents were bidding very high yesterday, we need to match partially.
    # Otherwise, underbid slightly to preserve budget.
    my_hp = int(my_status['hp'])
    my_budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Urgency factor
    urgency = 0.0
    if my_hp <= 2:
        urgency = 1.0
    elif my_hp <= 4:
        urgency = 0.7
    elif my_hp <= 6:
        urgency = 0.4
    else:
        urgency = 0.2

    if no_water_days >= 2:
        urgency = max(urgency, 0.8)

    # Competition factor from yesterday
    comp = 0.0
    if highest_prev >= DAILY_SALARY * 1.15:
        comp = 0.95
    elif highest_prev >= DAILY_SALARY * 0.95:
        comp = 0.7
    elif highest_prev >= DAILY_SALARY * 0.6:
        comp = 0.45
    else:
        comp = 0.25

    # Tight supply -> increase bid
    tight = 1.0 - supply_ratio  # 1 when supply==MIN_SUPPLY

    # Target bid
    # Use a blend of: fraction of daily salary, plus slight response to highest_prev.
    target = DAILY_SALARY * (0.45 + 0.25 * tight + 0.25 * urgency) + 0.15 * highest_prev

    # If yesterday bids were high, don't fall too far behind.
    if highest_prev > 0:
        # Ensure we are at least somewhat competitive.
        target = max(target, 0.65 * highest_prev)

    # If my hp is good, avoid overspending.
    if my_hp >= 7 and urgency < 0.35:
        target = min(target, DAILY_SALARY * (0.65 + 0.15 * tight))

    # Clamp by budget
    bid = min(my_budget, target)

    # If budget is extremely low, spend what we can.
    if my_budget <= 10:
        return max(0.0, my_budget)

    # Final safety: never negative
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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Extract yesterday bids from all alive opponents (immediate reaction)
    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                yesterday_bids.append(float(bid))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how many full water units exist; use int indices safely
    # (not strictly needed, but keeps logic stable)
    units = int(supply / float(WATER_REQ)) if WATER_REQ > 0 else 0

    # Base aggressiveness: medium scenario tends to require contesting
    # Target band anchored to survivors' bids from yesterday.
    # If someone previously bid very high, we must respond.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        if my_hp > 3.0 and my_no_water_days <= 0:
            desired = DAILY_SALARY * 0.32
        else:
            desired = DAILY_SALARY * 0.92
    else:
        # If bids were not extreme, slightly overbid the top to secure water.
        desired = max(DAILY_SALARY * 0.52, highest_prev_bid + 1.5)

    # If supply is tight (few units), increase bid.
    if units <= 1:
        desired *= 1.15

    # If our HP is critical, bid more.
    if my_hp <= 2.0:
        desired = max(desired, DAILY_SALARY * 0.9)

    # If we've already had no-water days, increase bid to break the streak.
    if my_no_water_days >= 1:
        desired = max(desired, DAILY_SALARY * 0.7)

    # Ensure we never exceed budget.
    bid = min(my_budget, desired)

    # If budget is tiny, still bid something nonzero only when needed.
    if bid <= 0.0:
        return 0.0
    return bid
"""
