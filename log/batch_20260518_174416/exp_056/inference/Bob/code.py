# ============================================================
# Experiment: exp_056
# Agent: Bob
# Source: exp_056
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    MAX_SUPPLY = 25

    supply = day_context.get('supply', float(MAX_SUPPLY))
    day = day_context.get('day', 0)

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append(o)

    if not alive_opponents:
        return min(my_status.get('budget', 0), DAILY_SALARY * 0.4)

    # Read yesterday bids (immediate reaction)
    prev_bids = []
    for o in alive_opponents:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            prev_bids.append(b)

    # If we have no signal, bid moderately; later days bid more.
    if not prev_bids:
        hp = my_status.get('hp', 0)
        budget = my_status.get('budget', 0)
        base = DAILY_SALARY * (0.45 if day <= 5 else 0.6)
        if hp <= 2:
            base = DAILY_SALARY * 0.85
        return min(budget, base)

    highest_prev_bid = max(prev_bids)
    avg_prev_bid = sum(prev_bids) / float(len(prev_bids))

    hp = my_status.get('hp', 0)
    budget = my_status.get('budget', 0)
    no_water_days = my_status.get('no_water_days', 0)

    # Estimate how much water is needed this day.
    # Target: secure at least WATER_REQ unless budget/HP is critical.
    # Convert supply to a rough scarcity factor.
    # Note: avoid float indices; no indexing used here.
    scarcity = 0.0
    if MAX_SUPPLY > 0:
        scarcity = (float(MAX_SUPPLY) - float(supply)) / float(MAX_SUPPLY)

    # Base bid logic driven by opponent pressure.
    # If opponents bid very high yesterday, they are likely competing hard today.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Match pressure but keep a budget-aware cap.
        if hp <= 2 or no_water_days >= 1:
            target = DAILY_SALARY * 0.95
        else:
            target = DAILY_SALARY * (0.75 + 0.1 * scarcity)
    elif avg_prev_bid >= DAILY_SALARY * 0.55:
        target = max(highest_prev_bid + 1.0, DAILY_SALARY * (0.55 + 0.15 * scarcity))
    else:
        # Low yesterday bids: bid just enough to outcompete while conserving.
        target = max(DAILY_SALARY * (0.45 + 0.2 * scarcity), avg_prev_bid + 2.0)

    # Ensure we don't overbid beyond budget.
    # Also, if our HP is low, increase aggressiveness.
    if hp <= 1:
        target = max(target, DAILY_SALARY * 0.9)
    elif hp <= 3:
        target = max(target, DAILY_SALARY * 0.65)

    # Final clamp to budget.
    bid = min(budget, target)

    # If supply is extremely low, add a small urgency bump.
    if float(supply) <= float(WATER_REQ):
        bid = min(budget, max(bid, DAILY_SALARY * 0.8))

    # Never negative.
    if bid < 0:
        bid = 0

    return bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
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

    alive_opps = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday bids to infer who is pressuring.
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    # Cindy likely overbids; Alex/David died with low bids.
    # Use a conservative bid unless we are in danger.

    # Danger level: if we've already gone without water, increase bid.
    # Max days is 10; aim to secure water before HP collapses.
    danger = 0
    if hp <= 2.5:
        danger += 2
    if no_water_days >= 1:
        danger += 1

    # Estimate how many water units supply can cover.
    # supply is total supply; each unit covers WATER_REQ water requirement.
    # Use this to scale our willingness to pay: higher supply => lower bid.
    units = supply / float(WATER_REQ)
    # Normalize units into [0,1] roughly between 15 and 25.
    norm_supply = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    if norm_supply < 0.0:
        norm_supply = 0.0
    if norm_supply > 1.0:
        norm_supply = 1.0

    # Base bid: moderate, not matching Cindy's ~100 unless necessary.
    base = DAILY_SALARY * (0.35 + 0.15 * (1.0 - norm_supply))

    # If someone previously bid extremely high, we may need to contest only when in danger.
    # Otherwise, let them spend.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        if danger >= 2:
            target = DAILY_SALARY * 0.75
        elif danger >= 1:
            target = DAILY_SALARY * 0.6
        else:
            target = base
    else:
        if danger >= 2:
            target = DAILY_SALARY * 0.7
        elif danger >= 1:
            target = DAILY_SALARY * 0.55
        else:
            target = base

    # If our budget is low, cap aggressively.
    # Keep enough budget for remaining days: episode_days=10, current day index unknown but last 1-2 days matter.
    # Use a simple remaining-days heuristic.
    remaining_days = max(1, 10 - (day - 1))
    per_day_budget_cap = budget / float(remaining_days)
    # Ensure at least some bid if we are in danger.
    if danger >= 1:
        min_bid = DAILY_SALARY * 0.35
    else:
        min_bid = DAILY_SALARY * 0.2

    bid = max(min_bid, target)
    bid = min(bid, per_day_budget_cap, budget)

    # Final safety: never bid negative.
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
        # If alone, conserve but ensure survival
        cap = min(budget, DAILY_SALARY * 0.4)
        return max(0.0, cap)

    # Read yesterday's bids from previous_trace only
    prev_bids = []
    prev_pressures = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                b = float(b)
                prev_bids.append(b)
                prev_pressures.append((b, float(opp.get('hp', 0.0)), float(opp.get('budget', 0.0))))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_prev_bid = 0.0
    if prev_bids:
        sorted_b = sorted(prev_bids, reverse=True)
        if len(sorted_b) > 1:
            second_prev_bid = sorted_b[1]

    # Estimate how many water units we can/should aim for
    # If supply is low, we must bid more aggressively to secure the required 9.
    # If supply is high, we can bid closer to a competitive-but-not-winning threshold.
    supply_ratio = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Base bid: moderate, increases as supply decreases and hp/no_water_days worsen.
    # Target: beat the likely leader slightly when yesterday saw extreme bids.
    extreme_threshold = DAILY_SALARY * 0.85  # 76.5

    # Pressure from yesterday: if someone bid extremely high, we assume they tried to secure water.
    # We respond by bidding enough to prevent being outcompeted.
    if highest_prev_bid >= extreme_threshold:
        # If we are in danger, bid closer to the high end; otherwise just outbid slightly.
        if hp <= 2 or no_water_days >= 2:
            desired = max(highest_prev_bid * 0.95, second_prev_bid + 2.0)
        else:
            desired = max(second_prev_bid + 2.0, highest_prev_bid * 0.75)
    else:
        # No extreme bids: bid around a competitive fraction.
        desired = max(DAILY_SALARY * (0.45 + 0.25 * (1.0 - supply_ratio)), highest_prev_bid * 0.6)

    # Additional survival urgency
    if hp <= 1:
        desired *= 1.35
    elif hp <= 3:
        desired *= 1.15

    if no_water_days >= 3:
        desired *= 1.25
    elif no_water_days == 2:
        desired *= 1.10

    # Convert desired into a safe cap based on budget and typical spending.
    # Avoid overspending: never exceed what we can afford and keep some buffer.
    max_affordable = budget
    # In medium scenario, keep within ~0.95 salary when possible.
    max_reasonable = DAILY_SALARY * (0.95 if hp > 2 else 1.05)
    cap = min(max_affordable, max_reasonable)

    bid = min(max(0.0, desired), cap)

    # If supply is very low, ensure we don't underbid.
    if supply <= float(WATER_REQ) + 1.0:
        # push toward at least 0.6 salary
        min_floor = DAILY_SALARY * 0.6
        bid = max(bid, min_floor)
        bid = min(bid, cap)

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
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday's bids from each opponent's previous_trace.
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        if prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid', 0.0)))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = (sum(yesterday_bids) / len(yesterday_bids)) if yesterday_bids else 0.0

    # Base bid: aim around half salary to beat typical mid bids, but conserve.
    # Increase when supply is tighter or opponents bid aggressively yesterday.
    # Tight supply implies fewer winners and higher chance we lose without a stronger bid.
    supply_factor = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.0
    supply_factor = max(0.0, min(1.0, supply_factor))

    pressure = 0.0
    if highest_prev_bid >= DAILY_SALARY * 1.6:
        pressure = 0.35
    elif highest_prev_bid >= DAILY_SALARY * 1.0:
        pressure = 0.22
    elif avg_prev_bid > 0:
        pressure = 0.12

    # Urgency: if we've already missed water days, we must bid more.
    urgency = 0.0
    if no_water_days >= 3:
        urgency = 0.45
    elif no_water_days == 2:
        urgency = 0.28
    elif no_water_days == 1:
        urgency = 0.15

    # HP-based urgency (lower hp => bid more)
    hp_urgency = 0.0
    if hp <= 2:
        hp_urgency = 0.55
    elif hp <= 3:
        hp_urgency = 0.35
    elif hp <= 5:
        hp_urgency = 0.18

    # Compute target bid.
    base = DAILY_SALARY * 0.5
    target = base * (1.0 + pressure + 0.45 * supply_factor + urgency + hp_urgency)

    # Clamp to budget and keep within a reasonable range.
    # Also, if opponents were extremely high yesterday, we slightly overbid to secure a share.
    if highest_prev_bid >= DAILY_SALARY * 1.8:
        target = max(target, min(budget, highest_prev_bid * 0.95))
    elif highest_prev_bid >= DAILY_SALARY * 1.1:
        target = max(target, min(budget, highest_prev_bid * 0.7))

    # Final conservative cap to avoid going broke too early.
    cap = max(DAILY_SALARY * 0.95, budget * 0.35)  # ensure we can still survive if needed
    bid = min(budget, min(target, cap))

    # If hp is critical, ensure aggressive bid.
    if hp <= 1.5:
        bid = min(budget, DAILY_SALARY * 0.95)

    # If budget is very low, spend what we can.
    if bid < 0:
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

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    alive_opps = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Yesterday trace reaction
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', None)
        if isinstance(prev, dict):
            bid = prev.get('bid', None)
            if bid is not None:
                try:
                    yesterday_bids.append(float(bid))
                except Exception:
                    pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid

    # Supply pressure estimate: with supply 15-25, water units are small; bidding too high wastes budget.
    # Estimate how many units are likely available today.
    units_est = int(supply / float(WATER_REQ))
    if units_est < 1:
        units_est = 1

    # Base aggressiveness: mid-high when supply is moderate; lower when supply is high.
    # Normalize supply to [0,1] where 15->0, 25->1
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_norm = 0.5

    # Target bid band
    # If yesterday's max bid was very high, opponents are likely willing to pay; raise slightly.
    very_aggressive_market = highest_prev_bid >= DAILY_SALARY * 1.35  # ~121.5
    aggressive_market = highest_prev_bid >= DAILY_SALARY * 1.15      # ~103.5

    # If I'm in danger, bid more.
    if hp <= 2.0:
        safety_factor = 0.95
    elif hp <= 4.0:
        safety_factor = 0.75
    else:
        safety_factor = 0.60

    # If supply is higher, I can bid less; if supply is lower, I bid more.
    # supply_norm high => bid down.
    supply_adjust = (1.0 - supply_norm)  # 15 => 1, 25 => 0

    # Construct bid
    # Use highest_prev_bid as a soft ceiling driver, but don't fully match.
    if very_aggressive_market:
        target = (second_prev_bid + 2.0) if second_prev_bid > 0 else (highest_prev_bid * 0.65)
        target *= (0.70 + 0.25 * safety_factor)
    elif aggressive_market:
        target = max(DAILY_SALARY * 0.55, (highest_prev_bid * 0.60) + 5.0)
        target *= (0.65 + 0.30 * safety_factor)
    else:
        target = max(DAILY_SALARY * 0.50, (highest_prev_bid * 0.45) + 8.0)
        target *= (0.60 + 0.25 * safety_factor)

    # Supply adjustment
    target *= (0.85 + 0.30 * supply_adjust)

    # Ensure we don't overpay: cap relative to my budget and a multiple of salary
    cap = DAILY_SALARY * (0.95 if hp <= 2.0 else 0.80 if hp <= 4.0 else 0.70)
    bid = min(budget, cap, target)

    # If budget is very low, bid as much as possible to secure survival.
    if budget <= DAILY_SALARY * 0.25:
        bid = min(budget, DAILY_SALARY * 0.95)

    # Final clamp
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Extract yesterday bids from previous_trace only
    prev_bids = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate competitive pressure from yesterday
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_highest_prev_bid = 0.0
    if len(prev_bids) >= 2:
        s = sorted(prev_bids, reverse=True)
        second_highest_prev_bid = s[1]

    # Supply pressure: if supply is low, water is scarce; bid more.
    # Use a simple scarcity factor.
    scarcity = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        scarcity = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    # Decide aggressiveness based on our condition.
    # If we're close to death or already have many no-water days, bid very aggressively.
    urgent = (hp <= 2) or (no_water_days >= 2)

    if urgent:
        target = DAILY_SALARY * (0.9 + 0.1 * scarcity)  # ~81-99
    else:
        # If others previously bid high (Cindy survived), we must match/beat.
        # Otherwise, bid moderately above the likely floor.
        if highest_prev_bid >= DAILY_SALARY * 1.6:  # ~144+
            target = highest_prev_bid + (2.0 + 6.0 * scarcity)
        elif highest_prev_bid >= DAILY_SALARY * 1.1:
            target = max(DAILY_SALARY * (0.55 + 0.25 * scarcity), second_highest_prev_bid + 3.0)
        else:
            target = DAILY_SALARY * (0.5 + 0.25 * scarcity)

    # Clamp by budget and a reasonable cap to avoid overspending.
    # If budget is low, spend what we can.
    cap = max(DAILY_SALARY * 2.5, highest_prev_bid + 20.0)
    bid = min(budget, max(0.0, min(target, cap)))

    # If budget is extremely low, still bid something if urgent.
    if bid <= 0.0 and urgent:
        bid = min(budget, DAILY_SALARY * 0.2)

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
    day = day_context.get('day', 0)

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    # If no opponents, bid to survive comfortably.
    if not alive_opps:
        base = DAILY_SALARY * 0.35
        if hp <= 2 or no_water_days >= 2:
            base = DAILY_SALARY * 0.9
        return max(0.0, min(budget, base))

    # Read yesterday bids to infer pressure level.
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

    # Estimate how many water units are likely contested.
    # supply is in [15,25]; with WATER_REQ=9, 1 unit is guaranteed, 2 units possible.
    # Use this to decide whether to contest for 2 units (higher bid) or just secure 1.
    possible_units = int(supply / float(WATER_REQ))
    # possible_units will be 1 for 15-17.99, 2 for 18-25.

    # Strategy: if opponents previously bid very high, avoid matching; still bid enough to get 1 unit.
    # If my hp is low, increase bid to reduce risk of missing water.
    urgency = 0.0
    if hp <= 2:
        urgency = 1.0
    elif hp <= 4:
        urgency = 0.7
    elif hp <= 6:
        urgency = 0.4
    else:
        urgency = 0.2

    if no_water_days >= 2:
        urgency = max(urgency, 0.9)
    elif no_water_days == 1:
        urgency = max(urgency, 0.6)

    # Baseline bids.
    # Target bid fractions: low when not urgent, moderate when urgent, higher if supply likely allows 2 units.
    if possible_units >= 2:
        base_fraction = 0.45 + 0.35 * urgency  # 0.45..0.80
    else:
        base_fraction = 0.35 + 0.30 * urgency  # 0.35..0.65

    # Adjust based on yesterday's highest pressure.
    # If highest_prev_bid is already extreme, opponents may be overbidding; cap our bid to stay solvent.
    extreme_threshold = 0.9 * DAILY_SALARY
    if highest_prev_bid >= extreme_threshold:
        base_fraction *= 0.85
    elif highest_prev_bid >= 0.7 * DAILY_SALARY:
        base_fraction *= 0.95

    # Convert to amount.
    bid = DAILY_SALARY * base_fraction

    # Ensure we don't bid more than we can afford.
    bid = max(0.0, min(budget, bid))

    # Hard floor: if budget is tiny, bid whatever remains.
    if budget <= 1e-6:
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context['supply'])
    day = day_context['day']

    # Alive opponents
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    # If no one else, bid to secure water efficiently
    if not alive:
        return min(my_status['budget'], DAILY_SALARY * 0.45)

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])

    # Read yesterday trace bids to infer aggressiveness
    yesterday_bids = []
    for oid, o in alive:
        prev = o.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                yesterday_bids.append(float(bid))
            except Exception:
                pass

    highest_prev = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev

    # Supply pressure: with supply in [15,25], max water units roughly 15/9..25/9.
    # Lower supply means fewer total units, so increase bid to avoid losing.
    scarcity = 0.0
    if supply <= 17.0:
        scarcity = 1.0
    elif supply <= 20.0:
        scarcity = 0.6
    else:
        scarcity = 0.25

    # Opponent aggression indicator: Cindy survived with very high bids yesterday.
    # If highest_prev is large relative to our salary, assume strong continuation.
    aggressive = 1.0 if highest_prev >= DAILY_SALARY * 1.2 else 0.0

    # Base target bid
    # - If aggressive: slightly overbid the likely second-highest to secure.
    # - If not aggressive: bid around midrange.
    if aggressive > 0.5:
        target = max(second_prev + 2.0, DAILY_SALARY * (0.55 + 0.25 * scarcity))
    else:
        target = DAILY_SALARY * (0.45 + 0.25 * scarcity)

    # If my HP is low, I must secure water more urgently
    if my_hp <= 2.0:
        target *= 1.6
    elif my_hp <= 4.0:
        target *= 1.25

    # Budget cap and non-negative
    if my_budget <= 0.0:
        return 0.0

    bid = min(my_budget, target)

    # Avoid bidding too tiny amounts when supply is scarce
    min_bid = 2.0 if scarcity <= 0.25 else 8.0
    if bid < min_bid:
        bid = min(my_budget, min_bid)

    # Final clamp to a reasonable upper bound (can't exceed budget anyway)
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday's bids only from previous_trace.
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

    # Estimate how many water units we can/should buy.
    # If supply is near upper bound, being more aggressive is safer; if low, be conservative.
    # Use a conservative target: aim for 1 unit if possible, else hold.
    # Convert supply to an expected per-unit affordability signal.
    # (We don't know exact pricing; bidding higher increases chance of winning water.)

    # Base bid: mid-low to conserve budget against aggressive bidders.
    # Scale with supply: higher supply -> slightly lower urgency, but still bid enough to secure.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # If my hp is low, increase bid to avoid running out.
    if hp <= 2.0:
        base = DAILY_SALARY * (0.75 + 0.1 * supply_ratio)
    elif hp <= 4.0:
        base = DAILY_SALARY * (0.55 + 0.1 * supply_ratio)
    else:
        base = DAILY_SALARY * (0.42 + 0.08 * supply_ratio)

    # Exploit yesterday: if someone already bid extremely high, others may be constrained.
    # We don't want to match Cindy's level; we just want to be above typical mid bids.
    # If highest_prev_bid is very high, keep base moderate; if it's low, we can bid closer to it.
    if highest_prev_bid >= DAILY_SALARY * 1.1:
        # Aggressive opponent likely spent heavily; don't overreact.
        target = min(base, highest_prev_bid * 0.55)
    else:
        # If yesterday's pressure was low, we can bid closer to it to secure.
        target = max(base, highest_prev_bid * 0.85)

    # Final cap by budget.
    bid = max(0.0, min(budget, target))

    # If budget is tiny, still bid enough to have a chance but never exceed budget.
    if budget < DAILY_SALARY * 0.2:
        bid = min(budget, DAILY_SALARY * 0.25)

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
    day = int(day_context.get('day', 0))

    # Alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        try:
            if o.get('alive', False):
                alive_opps.append(o)
        except Exception:
            continue

    # If no one else is alive, bid to ensure full allocation for us cheaply
    if not alive_opps:
        return float(min(my_status.get('budget', 0.0), DAILY_SALARY * 0.4))

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))

    # Use only yesterday's immediate trace bids
    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is None:
            continue
        try:
            yesterday_bids.append(float(b))
        except Exception:
            continue

    # Heuristic: typical winning bids around ~110 from survivalists; avoid going too high
    # Determine pressure
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how many water units might be needed today given supply and fixed WATER_REQ
    # We don't know exact allocation rule, but we can use supply to decide aggressiveness.
    # Use int() to ensure indices safety.
    # target_units is how many WATER_REQ blocks supply suggests.
    target_units = int(supply / float(WATER_REQ)) if WATER_REQ > 0 else 1
    # Cap target_units to reasonable range
    if target_units < 1:
        target_units = 1
    if target_units > 3:
        target_units = 3

    # Base bid band
    # If opponents were bidding very high yesterday, conserve; else bid around their survival band.
    if highest_prev_bid >= DAILY_SALARY * 1.55:  # ~140
        base = avg_prev_bid if avg_prev_bid > 0 else (DAILY_SALARY * 0.6)
        # Conserve more if our hp is ok
        if my_hp > 4:
            base *= 0.75
        else:
            base *= 0.9
    else:
        # Aim slightly above their average to secure water, but not max
        base = avg_prev_bid if avg_prev_bid > 0 else (DAILY_SALARY * 0.6)
        # Push toward ~110-120 band
        # If base too low, lift it; if too high, moderate.
        if base < 95.0:
            base = 110.0
        elif base > 125.0:
            base = 120.0

    # Adjust for our hp: lower hp -> bid more
    if my_hp <= 2.0:
        base *= 1.25
    elif my_hp <= 4.0:
        base *= 1.12
    elif my_hp >= 8.0:
        base *= 0.9

    # Adjust for supply: higher supply -> bid slightly less
    # supply in [15,25]
    supply_factor = 1.0
    if supply >= 22.0:
        supply_factor = 0.92
    elif supply <= 17.0:
        supply_factor = 1.08
    base *= supply_factor

    # Translate target_units into a mild scaling (more units available -> less need for extreme bids)
    if target_units == 1:
        base *= 1.08
    elif target_units == 3:
        base *= 0.95

    # Final cap by budget and ensure nonnegative
    bid = float(base)
    if bid < 0.0:
        bid = 0.0

    # Don't exceed budget; also avoid bidding above what salary could justify too aggressively
    max_reasonable = my_budget
    if max_reasonable < 0.0:
        max_reasonable = 0.0

    # Keep bid within a practical ceiling to avoid waste
    practical_ceiling = min(max_reasonable, DAILY_SALARY * 1.6)
    if bid > practical_ceiling:
        bid = practical_ceiling

    # If budget is extremely low, bid remaining (still capped)
    if my_budget <= 1.0:
        bid = my_budget

    return float(bid)
"""
