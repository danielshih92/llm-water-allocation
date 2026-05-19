# ============================================================
# Experiment: exp_087
# Agent: Bob
# Source: exp_087
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

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    # Alive opponents only
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # Helper to safely read yesterday bid
    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = float(my_status.get('no_water_days', 0))

    # If no opponents, bid conservatively
    if not alive_opps:
        target = DAILY_SALARY * 0.4
        return min(budget, target)

    # Infer pressure from yesterday
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Baseline: ensure we can cover at least one WATER_REQ worth if possible
    # (We don't know mapping, but bids correlate with winning water allocation.)
    # Scale baseline by our urgency.
    urgency = 0.0
    if hp <= 2.0:
        urgency += 1.0
    if no_water_days >= 1.0:
        urgency += 0.7
    urgency += max(0.0, (3.5 - hp) / 3.5)

    # Supply context: if supply is closer to minimum, competition is harder -> bid more.
    # Map supply in [MIN_SUPPLY, MAX_SUPPLY] to [0,1]
    supply_norm = 0.0
    denom = float(MAX_SUPPLY - MIN_SUPPLY)
    if denom > 0:
        supply_norm = (float(supply) - float(MIN_SUPPLY)) / denom
    supply_norm = max(0.0, min(1.0, supply_norm))
    scarcity_boost = (1.0 - supply_norm) * 0.4

    # Strategy based on opponent aggression
    # If they bid high yesterday, they likely expect to win/need water; we contest.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Contest but avoid overspending when healthy
        if hp > 3.5 and no_water_days < 1.0:
            target = max(DAILY_SALARY * 0.35, highest_prev_bid * 0.85)
        else:
            target = max(DAILY_SALARY * 0.6, highest_prev_bid * 0.95)
    else:
        # They were timid: secure water with a moderate bid
        # Use scarcity and urgency to decide.
        target = DAILY_SALARY * (0.45 + urgency * 0.25 + scarcity_boost)
        # If they bid something non-trivial yesterday, slightly outbid
        if highest_prev_bid > 0.0:
            target = max(target, highest_prev_bid + 1.5)

    # Convert to feasible bid
    # Keep bid within budget and also avoid extreme bids beyond one-day salary scale.
    cap = min(budget, DAILY_SALARY * 0.98)

    # If budget is very low, bid whatever we can but not above cap
    if cap <= 0.0:
        return 0.0

    # Ensure a minimum meaningful bid when we are urgent
    min_bid = 0.0
    if hp <= 2.0:
        min_bid = DAILY_SALARY * 0.7
    elif no_water_days >= 1.0:
        min_bid = DAILY_SALARY * 0.55
    else:
        min_bid = DAILY_SALARY * 0.35

    bid = max(min_bid, target)
    bid = min(bid, cap)

    # Final safety clamp
    if bid < 0.0:
        bid = 0.0
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
    day = day_context['day']

    # Identify alive opponents
    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append(o)

    # If no one else is alive, conserve budget
    if not alive_opponents:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Use only yesterday's previous_trace for immediate reaction
    yesterday_bids = []
    for o in alive_opponents:
        prev = o.get('previous_trace', None)
        if isinstance(prev, dict):
            # Some environments provide a dict; handle defensively
            bid = prev.get('bid', None)
            if bid is not None:
                yesterday_bids.append(float(bid))
        else:
            # Could be missing or malformed
            pass

    # Fallback if previous_trace doesn't include bid info
    if not yesterday_bids:
        base = DAILY_SALARY * (0.55 if my_status['hp'] > 3 else 0.9)
        return float(min(my_status['budget'], base))

    highest_prev_bid = max(yesterday_bids)

    # Supply pressure: fewer full water units increases urgency
    # Use int() for safety; compute units as integer
    units = int(supply // WATER_REQ)
    tight_supply = (units <= 1)  # supply in [15,25] => units 1 or 2

    # Strategy:
    # - If opponents were bidding aggressively yesterday, undercut slightly while staying safe.
    # - If my HP is low or supply is tight, bid closer to their aggressive threshold.
    aggressive_threshold = DAILY_SALARY * 0.85  # 76.5

    if highest_prev_bid >= aggressive_threshold:
        if my_status['hp'] > 3 and not tight_supply:
            # Undercut by a small margin
            target = highest_prev_bid - 3.0
        else:
            # Need to match pressure
            target = highest_prev_bid - 1.0
    else:
        # Opponents not too aggressive: bid moderately
        if my_status['hp'] <= 2 or tight_supply:
            target = DAILY_SALARY * 0.85
        else:
            target = max(DAILY_SALARY * 0.55, highest_prev_bid + 1.5)

    # Clamp to budget and reasonable bounds
    # Also consider that bidding too high could waste budget; keep within ~1.2*salary
    cap = DAILY_SALARY * 1.2
    bid = float(min(my_status['budget'], min(cap, max(0.0, target))))

    # If budget is extremely low, still bid enough to avoid immediate death
    if my_status['budget'] <= DAILY_SALARY * 0.2:
        bid = float(min(my_status['budget'], DAILY_SALARY * 0.25))

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

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive'):
            alive.append((oid, o))

    if not alive:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from each opponent's previous_trace
    prev_bids = []
    for oid, o in alive:
        prev = o.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate how many allocation units are likely available today
    # (allocation model unknown; we use supply to modulate aggressiveness)
    supply_bucket = None
    if supply <= (MIN_SUPPLY + MAX_SUPPLY) / 2:
        supply_bucket = 'low'
    else:
        supply_bucket = 'high'

    # Base bid: try to secure water without overpaying against aggressive Cindy-like behavior
    # If someone previously bid very high, reduce relative to them.
    if highest_prev_bid >= DAILY_SALARY * 1.4:  # ~126+
        base = DAILY_SALARY * 0.45
    elif highest_prev_bid >= DAILY_SALARY * 0.9:  # ~81+
        base = DAILY_SALARY * 0.55
    else:
        base = DAILY_SALARY * 0.62

    # Adjust for my health pressure
    if my_hp <= 2.0 or my_no_water_days >= 2:
        base = DAILY_SALARY * 0.85
    elif my_hp <= 4.0:
        base = DAILY_SALARY * 0.70

    # Adjust for supply regime
    if supply_bucket == 'low':
        base *= 0.90
    else:
        base *= 1.00

    # Ensure we don't bid more than we can afford
    bid = min(my_budget, base)

    # If my budget is extremely low, bid whatever is left (can't do better)
    if my_budget <= DAILY_SALARY * 0.15:
        bid = my_budget

    # Clamp to [0, budget]
    if bid < 0.0:
        bid = 0.0
    if bid > my_budget:
        bid = my_budget

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

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for k, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append(o)

    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # React to yesterday's immediate pressure
    yesterday_bids = []
    for o in alive_opponents:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Supply-aware target: if supply is low, competition is higher; bid more.
    # With WATER_REQ=9, supply 15-25 means roughly 1-2 water units available.
    # Use a smooth scaling between 55% and 80% of salary.
    if supply <= float(MIN_SUPPLY):
        supply_factor = 0.80
    elif supply >= float(MAX_SUPPLY):
        supply_factor = 0.60
    else:
        # linear interpolation
        supply_factor = 0.80 - (supply - float(MIN_SUPPLY)) * (0.20 / (float(MAX_SUPPLY) - float(MIN_SUPPLY)))

    # If yesterday someone bid extremely high (~near 160), avoid matching; aim just below.
    # If yesterday pressure was moderate, bid to beat it.
    pressure_threshold = DAILY_SALARY * 0.85  # 76.5

    if highest_prev_bid >= pressure_threshold:
        # Avoid suicidal chase: take a capped response.
        target = min(DAILY_SALARY * supply_factor, highest_prev_bid - 5.0)
        # If our HP is critical or we've been without water, increase slightly.
        if hp <= 2 or no_water_days >= 2:
            target = min(budget, max(target, DAILY_SALARY * 0.75))
    else:
        # Lower pressure: bid around supply_factor*salary, but slightly above baseline.
        target = DAILY_SALARY * (supply_factor + 0.05)
        if hp <= 2 or no_water_days >= 2:
            target = max(target, DAILY_SALARY * 0.70)

    # Ensure we don't overspend: never exceed budget.
    # Also keep a floor to remain competitive when supply is low.
    floor_bid = DAILY_SALARY * 0.35 if supply > float(MIN_SUPPLY) else DAILY_SALARY * 0.55
    target = max(floor_bid, target)

    # Final clamp
    if budget <= 0:
        return 0.0
    return float(min(budget, target))
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

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    my_hp = my_status.get('hp', 0)
    my_budget = my_status.get('budget', 0)
    my_no_water_days = my_status.get('no_water_days', 0)

    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive.append((opp_id, opp))

    # Baseline: if we're in danger, spend to secure water.
    danger = (my_hp <= 2) or (my_no_water_days >= 2)

    # React to yesterday pressure: look at bids of alive opponents from their previous_trace.
    prev_bids = []
    for _, opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])

    # If we can estimate market pressure, bid around it.
    if prev_bids:
        highest_prev = max(prev_bids)
        # If someone previously bid extremely high, avoid going to the ceiling.
        # Use a cap factor based on how close supply is to the minimum.
        supply_frac = 0.0
        if MAX_SUPPLY > MIN_SUPPLY:
            supply_frac = (float(supply) - float(MIN_SUPPLY)) / float(MAX_SUPPLY - MIN_SUPPLY)
        if supply_frac < 0.0:
            supply_frac = 0.0
        if supply_frac > 1.0:
            supply_frac = 1.0

        # When supply is scarce, we must be more aggressive.
        scarcity_multiplier = 1.15 if supply_frac < 0.35 else (1.0 if supply_frac < 0.7 else 0.85)

        # Target bid: slightly below the highest previous bid unless we're in danger.
        if danger:
            target = min(my_budget, highest_prev * (0.92 * scarcity_multiplier) + 2.0)
        else:
            target = min(my_budget, max(DAILY_SALARY * 0.45, highest_prev * (0.72 * scarcity_multiplier)))
    else:
        # No signal: use supply-based heuristic.
        supply_frac = 0.0
        if MAX_SUPPLY > MIN_SUPPLY:
            supply_frac = (float(supply) - float(MIN_SUPPLY)) / float(MAX_SUPPLY - MIN_SUPPLY)
        if supply_frac < 0.0:
            supply_frac = 0.0
        if supply_frac > 1.0:
            supply_frac = 1.0
        if danger:
            target = DAILY_SALARY * 0.9
        else:
            target = DAILY_SALARY * (0.65 if supply_frac < 0.5 else 0.5)
        target = min(my_budget, target)

    # Ensure we never bid negative and keep within budget.
    if target < 0:
        target = 0.0
    if my_budget <= 0:
        return 0.0
    if target > my_budget:
        target = my_budget

    # If supply is very low, add a small bump to avoid tie-losing.
    if float(supply) <= float(MIN_SUPPLY) + 0.5:
        target = min(my_budget, target + DAILY_SALARY * 0.08)

    # Final small sanity cap: don't exceed ~1.05*DAILY_SALARY unless danger.
    if not danger:
        cap = DAILY_SALARY * 1.05
        if target > cap:
            target = cap

    return float(target)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    my_hp = float(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    if not alive_opponents:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace only (immediate reaction)
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                prev_bids.append(float(bid))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_highest_prev_bid = 0.0
    if len(prev_bids) >= 2:
        sorted_b = sorted(prev_bids, reverse=True)
        second_highest_prev_bid = sorted_b[1]

    # Estimate how many water units are realistically available today.
    # Use int() explicitly for any indexing; here we just compute.
    # If supply is tight, we need to secure at least one water unit.
    supply_units = int(supply // float(WATER_REQ)) if WATER_REQ > 0 else 0

    # Base aggressiveness: moderate to beat typical bids (~70-97) but avoid Cindy-like overbidding.
    # If opponents previously bid very high, slightly increase.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        target = max(second_highest_prev_bid + 2.0, DAILY_SALARY * 0.32)
    else:
        # Undercut: aim just above the likely median pressure.
        # If my hp is healthy, bid less; if low, bid more.
        if my_hp <= 2.0 or my_no_water_days >= 2:
            target = max(highest_prev_bid * 0.9, DAILY_SALARY * 0.55)
        else:
            target = max(highest_prev_bid * 0.75, DAILY_SALARY * 0.48)

    # Tight supply: increase slightly to secure water.
    if supply_units <= 1:
        target *= 1.15

    # Safety caps based on budget.
    bid = float(min(my_budget, target))

    # Ensure non-negative bid.
    if bid < 0.0:
        bid = 0.0

    return bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
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

    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Read yesterday bids for immediate reaction
    prev_bids = []
    prev_extreme = False
    highest_prev_bid = 0.0
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                bf = float(b)
            except Exception:
                continue
            prev_bids.append(bf)
            if bf > highest_prev_bid:
                highest_prev_bid = bf
            # Extreme indicates an aggressive/pressure response
            if bf >= DAILY_SALARY * 1.7:  # ~153
                prev_extreme = True

    # Base bid depends on current HP and supply
    hp = my_status.get('hp', 0)
    budget = my_status.get('budget', 0)
    no_water_days = my_status.get('no_water_days', 0)

    # How many full water-units are available per day; used to calibrate aggressiveness
    # Ensure indices are int-safe even though we don't index lists.
    # supply_units is a float but used only in arithmetic.
    supply_units = float(supply) / float(WATER_REQ)

    # If supply is tight (near min), we must bid more to avoid falling behind.
    tight_supply = float(supply) <= float(WATER_REQ) + 6.0  # heuristic

    # Strategy:
    # - If my HP is low or I've already had no-water days, bid high to secure water.
    # - If an opponent previously bid extremely high, assume they will compete; slightly overbid.
    # - Otherwise bid mid to conserve budget.
    if hp <= 2 or no_water_days >= 2:
        target = DAILY_SALARY * (0.85 if not tight_supply else 1.05)
    else:
        if prev_bids:
            if prev_extreme:
                # Cindy-like behavior: match/beat extreme pressure
                target = min(DAILY_SALARY * 1.2, highest_prev_bid + 5.0)
            else:
                # Moderate reaction to typical bids
                # If highest previous bid was already high, bid closer to it.
                if highest_prev_bid >= DAILY_SALARY * 1.1:
                    target = min(DAILY_SALARY * 0.95, highest_prev_bid * 0.95)
                else:
                    target = DAILY_SALARY * (0.55 if not tight_supply else 0.7)
        else:
            target = DAILY_SALARY * (0.55 if not tight_supply else 0.7)

    # Additional ramp late in episode (day near end)
    if day is not None:
        try:
            d = int(day)
            # episode_days is 10 in meta-round state; ramp on last 2 days
            if d >= 9:
                target *= 1.15
        except Exception:
            pass

    # Cap by budget and also by a reasonable maximum to avoid bankruptcy
    # Empirically bids in traces were around 40-160; keep within budget.
    max_reasonable = DAILY_SALARY * 1.9
    bid = min(float(budget), float(target), float(max_reasonable))

    # Ensure non-negative
    if bid < 0:
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    alive_opps = []
    for opp_id, o in opponents_status.items():
        if o.get('alive', True):
            alive_opps.append((opp_id, o))

    # If no opponents, bid just enough to avoid no-water days.
    if not alive_opps:
        return max(0.0, min(my_status.get('budget', 0.0), DAILY_SALARY * 0.4))

    # Read yesterday's bids to infer pressure.
    yesterday_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Default baseline: moderate bid.
    base = DAILY_SALARY * 0.55

    # Pressure adjustment from yesterday.
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If others were near my daily salary, they likely overbid for survival.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # If I'm healthy, undercut slightly; if low hp, match closer.
            if my_status.get('hp', 0) > 3:
                base = DAILY_SALARY * 0.35
            else:
                base = DAILY_SALARY * 0.85
        else:
            # Otherwise, bid slightly above the crowd average to secure water.
            avg_prev = sum(yesterday_bids) / float(len(yesterday_bids))
            base = max(base, avg_prev + 2.0)

    # Supply-based urgency: if supply is tight relative to WATER_REQ, increase.
    # Expected number of water units is roughly supply / WATER_REQ.
    # Tight supply => fewer winners => bid more.
    if supply <= (MIN_SUPPLY + MAX_SUPPLY) / 2.0:
        base *= 1.10
    else:
        base *= 0.95

    # HP urgency: if I'm close to death, spend more.
    hp = float(my_status.get('hp', 0))
    if hp <= 2:
        base = max(base, DAILY_SALARY * 0.9)
    elif hp <= 4:
        base = max(base, DAILY_SALARY * 0.7)

    # Budget cap with a survival bias: keep some budget for later days.
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # If I've already missed water, increase bid to break the streak.
    if no_water_days >= 2:
        base *= 1.15

    # Keep a reserve: never bid more than ~70% of budget early, ~90% if late.
    # Episode days are 10; later days need more certainty.
    late_factor = 0.7
    if day >= 7:
        late_factor = 0.9
    elif day >= 4:
        late_factor = 0.8

    cap = budget * late_factor
    bid = min(cap, base)

    # Ensure non-negative and not exceeding daily salary by too much.
    # (Still allow higher if budget forces it.)
    if bid < 0.0:
        bid = 0.0

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

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    my_hp = my_status.get('hp', 0)
    my_budget = my_status.get('budget', 0)
    my_no_water_days = my_status.get('no_water_days', 0)

    alive_opps = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from immediate previous_trace only
    prev_bids = []
    prev_hp_after = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        if prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid', 0.0)))
            except Exception:
                pass
        if prev.get('hp_after') is not None:
            try:
                prev_hp_after.append(float(prev.get('hp_after', 0.0)))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    # Supply pressure estimate: if supply is low relative to requirement, competition is higher.
    # With WATER_REQ fixed, translate supply to expected number of winners.
    # Use int() for any indexing; no indexing needed, but keep logic safe.
    supply_ratio = float(supply) / float(WATER_REQ) if WATER_REQ > 0 else 0.0
    low_supply = supply <= (MIN_SUPPLY + 0.5)

    # If I am in danger, bid to secure water.
    if my_hp <= 2 or my_no_water_days >= 1:
        target = DAILY_SALARY * (0.85 if low_supply else 0.75)
    else:
        # Otherwise, try to undercut the likely leaders but still be competitive.
        # If yesterday had very high bids, follow partially.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            target = DAILY_SALARY * (0.35 if my_hp > 3 else 0.7)
        else:
            # Use a blend of average and a small bump.
            target = max(DAILY_SALARY * 0.45, avg_prev_bid * 0.65)

    # Cap target to budget and keep within reasonable range.
    bid = min(float(my_budget), float(target))

    # If yesterday showed extremely high bids, add a small increment to avoid being outbid.
    if highest_prev_bid > 0 and highest_prev_bid >= DAILY_SALARY * 0.9:
        bid = min(float(my_budget), bid + DAILY_SALARY * 0.05)

    # Ensure non-negative
    if bid < 0:
        bid = 0.0
    return bid
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

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for k, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((k, o))

    if not alive_opps:
        cap = DAILY_SALARY * 0.4
        return max(0.0, min(budget, cap))

    # Extract yesterday bids from previous_trace only (immediate reaction)
    yesterday_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    # Supply pressure: if supply is low, bid more to avoid missing water.
    # If supply is high, bid less (water more likely to be allocated).
    if supply <= (MIN_SUPPLY + WATER_REQ):
        supply_factor = 0.85
    elif supply >= (MAX_SUPPLY - 1.0):
        supply_factor = 0.55
    else:
        supply_factor = 0.7

    # Our urgency: if we have gone without water, increase bid.
    if no_water_days >= 2 or hp <= 2:
        urgency_factor = 0.95
    elif no_water_days == 1 or hp <= 4:
        urgency_factor = 0.8
    else:
        urgency_factor = 0.65

    # Opponent aggression: if yesterday bids were very high, slightly raise.
    # Otherwise keep moderate to preserve budget.
    if highest_prev_bid >= DAILY_SALARY * 1.4:
        aggression_factor = 0.95
    elif highest_prev_bid >= DAILY_SALARY * 1.0:
        aggression_factor = 0.8
    else:
        aggression_factor = 0.65

    target = DAILY_SALARY * supply_factor * urgency_factor * aggression_factor

    # If we know someone was bidding near our salary, nudge above average but not too high.
    if yesterday_bids:
        target = max(target, avg_prev_bid * 0.75)

    # Safety cap: never exceed budget; also avoid reckless bids.
    # With medium scenario, keep within 0.75 of daily salary unless very urgent.
    if urgency_factor < 0.85:
        max_bid = DAILY_SALARY * 0.75
    else:
        max_bid = DAILY_SALARY * 1.05

    bid = min(budget, max_bid, target)

    # Ensure non-negative
    if bid < 0.0:
        bid = 0.0

    return float(bid)
"""
