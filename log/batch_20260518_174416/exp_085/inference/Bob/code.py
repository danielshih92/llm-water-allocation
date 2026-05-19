# ============================================================
# Experiment: exp_085
# Agent: Bob
# Source: exp_085
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    # Alive opponents
    alive_opps = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        return min(float(my_status.get('budget', 0.0)), DAILY_SALARY * 0.4)

    # Extract yesterday bids
    yesterday_bids = []
    yesterday_pressure = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

        # Also use their yesterday hp_after/status if available to infer pressure
        hp_after = prev.get('hp_after', None)
        status = prev.get('status', None)
        if hp_after is not None:
            try:
                yesterday_pressure.append((float(hp_after), status))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))

    # Estimate how many
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

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids to infer aggressiveness
    prev_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                prev_bids.append(float(bid))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    # If Cindy was the dominant bidder yesterday, assume she continues to pressure.
    # We don't know who is Cindy, so use the highest previous bid as proxy.
    pressure = 0.0
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        pressure = 1.0
    elif highest_prev_bid >= DAILY_SALARY * 0.55:
        pressure = 0.6
    else:
        pressure = 0.3

    # Decide bid level.
    # Goal: outcompete only when needed; otherwise conserve budget.
    # If I'm in danger (low hp or already no-water days), bid more.
    danger = 0.0
    if hp <= 2.0:
        danger = 1.0
    elif hp <= 4.0:
        danger = 0.7
    elif no_water_days >= 2:
        danger = 0.6
    else:
        danger = 0.3

    # Supply affects how much water is likely to be contested; higher supply reduces need.
    supply_factor = 0.0
    if supply >= 22.0:
        supply_factor = 0.85
    elif supply >= 18.0:
        supply_factor = 1.0
    else:
        supply_factor = 1.15

    # Baseline bid: slightly above moderate range.
    # Use pressure and danger to scale.
    target = DAILY_SALARY * (0.45 + 0.25 * pressure + 0.25 * danger)
    target *= supply_factor

    # If yesterday pressure was extreme, nudge upward to avoid being starved.
    if highest_prev_bid >= DAILY_SALARY * 0.95:
        target = max(target, highest_prev_bid * 0.98)
    elif highest_prev_bid >= DAILY_SALARY * 0.7:
        target = max(target, highest_prev_bid * 0.9)

    # Keep within budget and reasonable cap.
    # Also avoid bidding above what would be wasteful given average supply.
    cap = min(budget, DAILY_SALARY * 1.25)
    bid = max(0.0, min(cap, target))

    # If we are already at/near zero budget, still bid what we can.
    if budget <= 1.0:
        return 0.0

    # Ensure at least a small bid if safe; otherwise conserve.
    if bid < DAILY_SALARY * 0.2 and danger < 0.7:
        bid = min(bid, DAILY_SALARY * 0.2)

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

    supply = float(day_context.get('supply', (MIN_SUPPLY + MAX_SUPPLY) / 2.0))
    day = day_context.get('day', 0)

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))

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
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate likely clearing price: if someone previously spent extremely high, we undercut.
    # Cindy ~135 suggests a high willingness to pay; we bid below that unless we're in danger.
    critical_hp = 2.5

    # Supply pressure: if supply is tight, raise bid modestly.
    # With WATER_REQ=9 and supply in [15,25], we can cover 1 unit reliably; extra water is valuable.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    tightness = 1.0 - max(0.0, min(1.0, supply_ratio))

    # Base bid anchored to a fraction of DAILY_SALARY.
    base = DAILY_SALARY * (0.55 + 0.25 * tightness)

    # If highest previous bid was huge, undercut aggressively but stay competitive.
    if highest_prev_bid >= DAILY_SALARY * 1.2:
        target = min(highest_prev_bid * 0.75, base * 1.05)
    elif highest_prev_bid >= DAILY_SALARY * 0.85:
        target = min(highest_prev_bid * 0.85, base * 0.95)
    else:
        target = base

    # If our HP is low, we must secure water.
    if hp <= critical_hp:
        target = max(target, DAILY_SALARY * 0.9)

    # Ensure we never bid more than budget.
    bid = max(0.0, min(budget, target))

    # Small deterministic bump by day to avoid ties.
    bid = bid + (1.0 if int(day) % 2 == 1 else 0.0)
    bid = max(0.0, min(budget, bid))

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

    supply = float(day_context.get('supply', (MIN_SUPPLY + MAX_SUPPLY) / 2.0))
    day = int(day_context.get('day', 0))

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Pull only yesterday immediate trace bids
    prev_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    # Estimate how many water units we might need to avoid death pressure.
    # If supply is near 15, water is scarce; if near 25, less scarce.
    # Target bid scales with scarcity.
    scarcity = 1.0
    if MAX_SUPPLY > MIN_SUPPLY:
        scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
        if scarcity < 0.0:
            scarcity = 0.0
        if scarcity > 1.0:
            scarcity = 1.0

    # Base bid: moderate, adjusted by scarcity and our HP.
    # Also react to extreme yesterday bids (Cindy-like behavior).
    extreme_threshold = DAILY_SALARY * 1.5  # 135

    # If our HP is low or we already went without water, we must secure water.
    urgent = (hp <= 2) or (no_water_days >= 2)

    if urgent:
        # Escalate but avoid reckless spending.
        target = DAILY_SALARY * (0.75 + 0.25 * scarcity)
    else:
        if highest_prev_bid >= extreme_threshold:
            # Others are spending big; undercut slightly to win with lower cost.
            target = min(DAILY_SALARY * (0.55 + 0.25 * scarcity), highest_prev_bid * 0.85)
        else:
            # No extreme bidding: bid near mid to secure share.
            target = DAILY_SALARY * (0.5 + 0.2 * scarcity)

    # Convert target to feasible bid given budget.
    # Keep some buffer to survive multiple days.
    max_affordable = budget
    # If budget is very low, bid what we can.
    if max_affordable <= 0.0:
        return 0.0

    # Budget-aware cap: don't spend more than ~60% of budget unless urgent.
    budget_cap = budget * (0.75 if urgent else 0.6)
    bid = min(target, budget_cap, max_affordable)

    # Ensure non-negative and at least 1 when possible (to avoid zero bids when urgent).
    if bid < 0.0:
        bid = 0.0
    if bid == 0.0 and urgent and budget >= 1.0:
        bid = 1.0

    return float(bid)
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

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for k in opponents_status:
        o = opponents_status[k]
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids to infer aggressiveness
    prev_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    if prev_bids:
        max_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / float(len(prev_bids))
    else:
        max_prev = 0.0
        avg_prev = 0.0

    # Base bid from supply pressure: higher supply -> lower need to outbid
    # supply in [15,25], WATER_REQ=9 => 1-2 units possible
    # If supply is near 15 (tight), bid more.
    tightness = (float(MAX_SUPPLY) - supply) / float(MAX_SUPPLY - MIN_SUPPLY)  # 0..1
    tightness = max(0.0, min(1.0, tightness))

    # Urgency from my hp/no-water days
    urgency = 0.0
    if hp <= 2.0:
        urgency += 1.0
    elif hp <= 4.0:
        urgency += 0.6
    if no_water_days >= 2:
        urgency += 0.8
    elif no_water_days == 1:
        urgency += 0.4

    # Opponent aggressiveness: if they were bidding around/above ~0.9*DAILY_SALARY, expect competition.
    opp_pressure = 0.0
    if avg_prev >= DAILY_SALARY * 0.9:
        opp_pressure = 1.0
    elif avg_prev >= DAILY_SALARY * 0.7:
        opp_pressure = 0.7
    elif avg_prev >= DAILY_SALARY * 0.5:
        opp_pressure = 0.4
    else:
        opp_pressure = 0.2

    # Decide target bid level
    # Keep below max_prev to avoid wasting money, but increase when tight/urgent.
    # Use a capped fraction of max_prev and salary.
    target = DAILY_SALARY * (0.45 + 0.25 * opp_pressure + 0.25 * tightness + 0.35 * urgency)

    if max_prev > 0.0:
        # If opponents previously spiked very high, only match a fraction.
        target = min(target, max_prev * (0.55 + 0.15 * urgency))

    # If supply allows two allocations (supply >= 18), reduce bid slightly.
    if supply >= 18.0:
        target *= 0.9

    # Ensure non-negative and do not exceed budget
    bid = max(0.0, min(budget, target))

    # If budget is tiny, still bid something to avoid death when urgent
    if bid <= 0.0 and urgency > 0.8:
        bid = max(0.0, min(budget, DAILY_SALARY * 0.2))

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

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        return min(float(my_status['budget']), DAILY_SALARY * 0.4)

    # Read yesterday bids from previous_trace only
    prev_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Urgency: if we've already gone without water, increase pressure.
    urgency = 0.0
    if no_water_days >= 2:
        urgency = 1.0
    elif no_water_days == 1:
        urgency = 0.6

    base_cap = DAILY_SALARY * 0.65  # conservative default

    if prev_bids:
        highest_prev_bid = max(prev_bids)
        second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev_bid

        # If someone previously bid extremely high (Cindy/Eric), we don't match fully.
        if highest_prev_bid >= DAILY_SALARY * 1.4:  # ~126
            # Bid enough to avoid being the one starved, but keep budget.
            target = DAILY_SALARY * 0.72 + urgency * DAILY_SALARY * 0.18
        elif highest_prev_bid >= DAILY_SALARY * 0.9:  # ~81
            target = max(DAILY_SALARY * 0.55, second_prev_bid * 0.55) + urgency * DAILY_SALARY * 0.15
        else:
            # If bids were low, we can secure water with a moderate bet.
            target = max(DAILY_SALARY * 0.45, highest_prev_bid * 0.85) + urgency * DAILY_SALARY * 0.10
    else:
        target = base_cap + urgency * DAILY_SALARY * 0.20

    # If our hp is low, we must bid more aggressively.
    if hp <= 2:
        target = max(target, DAILY_SALARY * 0.9)
    elif hp <= 4:
        target = max(target, DAILY_SALARY * 0.75)

    # Supply scaling: higher supply means we can bid less.
    # supply in [15,25]
    if supply <= MIN_SUPPLY + 1e-9:
        supply_factor = 1.0
    elif supply >= MAX_SUPPLY - 1e-9:
        supply_factor = 0.75
    else:
        supply_factor = 1.0 - 0.25 * ((supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY))

    target = target * supply_factor

    # Final clamp to budget.
    if budget <= 0:
        return 0.0
    bid = min(budget, target)

    # Avoid bidding 0 when we still need water soon.
    if bid <= 0 and no_water_days >= 1:
        bid = min(budget, DAILY_SALARY * 0.6)

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

    # Alive opponents
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace (immediate reaction)
    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Baseline: medium scenario, keep steady aggressive pressure but not maximal
    # Use supply to scale: higher supply -> can bid slightly lower; lower supply -> slightly higher.
    supply_scale = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_scale = max(0.0, min(1.0, supply_scale))

    # Estimate pressure from yesterday
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        median_prev = sorted(yesterday_bids)[len(yesterday_bids)//2]
        # If someone was bidding extremely high yesterday, match closer to them.
        if highest_prev >= DAILY_SALARY * 0.85:
            if my_status['hp'] <= 2:
                target = DAILY_SALARY * 0.95
            else:
                target = max(median_prev + 2.0, DAILY_SALARY * 0.35)
        else:
            # Otherwise, outbid the median slightly to capture water.
            target = max(median_prev + 1.5, DAILY_SALARY * 0.55)
    else:
        target = DAILY_SALARY * 0.55

    # Adjust for my hp: low hp -> bid more
    if my_status['hp'] <= 2:
        target *= 1.35
    elif my_status['hp'] <= 4:
        target *= 1.15

    # Adjust for supply: if supply is scarce, increase bid a bit.
    target *= (1.10 - 0.20 * supply_scale)

    # Convert target to a safe budget-bounded bid.
    # Also avoid overcommitting: keep some budget for later days.
    budget = float(my_status['budget'])
    no_water_days = int(my_status.get('no_water_days', 0))

    # If we're already accumulating no-water days, increase urgency.
    if no_water_days >= 2:
        target *= 1.25

    # Cap bid to not exceed a fraction of budget based on remaining days.
    # (Episode length is 10, but we don't rely on it; use a conservative fraction.)
    max_fraction = 0.65 if my_status['hp'] > 3 else 0.85
    cap = budget * max_fraction

    bid = float(min(budget, cap, target))

    # Ensure bid is non-negative and at least small if budget allows.
    if bid < 0.0:
        bid = 0.0
    return bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    # Alive opponents
    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    # If no opponents, take what we can afford
    if not alive_opponents:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))

    # Read yesterday's immediate pressure from previous_trace
    prev_bids = []
    for opp_id, opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Base bid depends on supply: higher supply means we can underbid
    # Approximate number of water units available
    units = supply / float(WATER_REQ) if WATER_REQ > 0 else 1.0

    # Determine a target bid level
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev_bid

        # If someone was bidding extremely high yesterday, we slightly overtake but not too much.
        # Otherwise, bid just above the second-highest to steal the marginal unit.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # My hp is good; avoid panic overpaying.
            if my_hp > 6:
                target = min(my_budget, DAILY_SALARY * 0.32)
            else:
                target = min(my_budget, DAILY_SALARY * 0.75)
        else:
            # Use relative position: aim above second-highest.
            # Add a small increment scaled down when supply is higher.
            increment = 2.0 + 6.0 * max(0.0, (2.0 - units) / 2.0)
            target = second_prev_bid + increment
            # Keep target within reasonable bounds
            lower = DAILY_SALARY * 0.35
            upper = DAILY_SALARY * 0.65
            target = max(lower, min(upper, target))
            target = min(my_budget, target)
    else:
        # No trace info: conservative moderate bid
        if my_hp > 6:
            target = min(my_budget, DAILY_SALARY * 0.42)
        else:
            target = min(my_budget, DAILY_SALARY * 0.85)

    # Ensure we bid at least enough to matter, but never exceed budget
    if my_budget <= 0:
        return 0.0

    # If supply is high, reduce bid; if low, increase slightly
    if supply >= 21.0:
        target *= 0.9
    elif supply <= 17.0:
        target *= 1.08

    # Final clamp
    target = float(max(0.0, min(my_budget, target)))
    return target
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
    day = day_context['day']

    # Alive opponents and yesterday bids
    alive_ids = []
    yesterday_bids = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_ids.append(oid)
            prev = o.get('previous_trace', {}) or {}
            if prev.get('bid') is not None:
                yesterday_bids.append(float(prev['bid']))

    # If nobody alive, conserve
    if not alive_ids:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Estimate how competitive yesterday was
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else (yesterday_bids[0] if yesterday_bids else 0.0)

    # If supply is tight, increase pressure
    # Determine how many water units are likely available relative to our requirement
    # (Use int indices safely; no list indexing needed here.)
    supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    supply_factor = max(0.0, min(1.0, supply_factor))

    # Base bid from my HP: low HP => bid harder
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    # Target: beat typical competition slightly, but cap to budget.
    # Use highest_prev_bid as proxy for others' willingness.
    # If competition was high, bid near that; otherwise bid around mid.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Very competitive yesterday
        target = highest_prev_bid + 2.0
        if hp <= 2.0:
            target = max(target, DAILY_SALARY * 0.95)
        elif hp <= 4.0:
            target = max(target, DAILY_SALARY * 0.75)
        else:
            target = max(target, DAILY_SALARY * 0.6)
    else:
        # Moderate competition
        # Push above second-highest to avoid ties/near-misses.
        target = max(second_prev_bid + 1.5, DAILY_SALARY * (0.5 + 0.25 * supply_factor))
        if hp <= 2.0:
            target = max(target, DAILY_SALARY * 0.9)
        elif hp <= 4.0:
            target = max(target, DAILY_SALARY * 0.7)

    # Convert target to final bid with budget safety and small day-based variation
    # (variation helps avoid exact tie patterns)
    day_jitter = ((int(day) % 5) - 2) * 0.5
    target = target + day_jitter

    # Never bid negative
    if target < 0.0:
        target = 0.0

    # Cap by budget
    bid = min(budget, target)

    # If budget is extremely low, still try to secure water when HP is critical
    if budget <= 5.0:
        if hp <= 2.0:
            return float(budget)
        return float(min(budget, DAILY_SALARY * 0.2))

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
    day = int(day_context['day'])

    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = [o for o in opponents_status.values() if o.get('alive')]
    if not alive_opps:
        return float(min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace only
    prev_bids = []
    for opp in alive_opps:
        pt = opp.get('previous_trace', {})
        if isinstance(pt, dict):
            b = pt.get('bid', None)
            if b is not None:
                try:
                    prev_bids.append(float(b))
                except Exception:
                    pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_highest = 0.0
    if len(prev_bids) >= 2:
        s = sorted(prev_bids, reverse=True)
        second_highest = float(s[1])

    # Supply pressure: higher supply means we can bid less to still get enough water.
    # Target water amount: aim to cover requirement, but only when we are at risk.
    risk = 0
    if hp <= 2:
        risk += 2
    if no_water_days >= 1:
        risk += 1

    # Baseline bid based on supply band
    # (These are tuned to medium scenario supply [15,25] and WATER_REQ=9)
    if supply >= 21:
        base = DAILY_SALARY * 0.45
    elif supply >= 18:
        base = DAILY_SALARY * 0.55
    else:
        base = DAILY_SALARY * 0.65

    # Reaction to opponents' yesterday aggressiveness
    # If someone previously bid extremely high, they likely overcommit; we can bid slightly above our base.
    # If bids were low, we must ensure we secure water to avoid falling behind.
    if highest_prev_bid >= DAILY_SALARY * 1.0:  # >=90
        bid = base * (0.85 if risk == 0 else 1.05)
    elif highest_prev_bid >= DAILY_SALARY * 0.4:  # >=36
        bid = base * (1.00 if risk == 0 else 1.20)
    else:
        bid = base * (1.10 if risk == 0 else 1.35)

    # Ensure bid is enough to compete: add a small increment over second-highest when risk is present
    # (Simultaneous bidding; we can't know current bids, so we hedge.)
    if risk >= 1:
        bid = max(bid, second_highest + 2.0)

    # Budget and survival guardrails
    # If budget is low, don't overspend; prioritize staying alive.
    # Also, if we are already in danger, bid close to a day salary.
    if budget <= DAILY_SALARY * 0.2:
        cap = budget
    else:
        cap = budget

    if risk >= 2:
        bid = min(bid, DAILY_SALARY * 0.95)
    else:
        bid = min(bid, DAILY_SALARY * 0.75)

    # Final clamp
    bid = float(max(0.0, min(cap, bid)))
    return bid
"""
