# ============================================================
# Experiment: exp_070
# Agent: Bob
# Source: exp_070
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    hp = my_status.get('hp', 0)
    budget = my_status.get('budget', 0)

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    # Default: if no opponents or no useful trace, bid based on our HP.
    if not alive_opps:
        if hp <= 2:
            return min(budget, DAILY_SALARY * 0.95)
        if hp <= 4:
            return min(budget, DAILY_SALARY * 0.75)
        return min(budget, DAILY_SALARY * 0.55)

    # Extract yesterday bids from immediate previous_trace only.
    prev_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev.get('bid'))

    # Estimate how contested it was yesterday.
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev_bid

        # If they were already willing to pay near our daily salary, match/beat slightly.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if hp <= 2:
                bid = DAILY_SALARY * 0.95
            elif hp <= 4:
                bid = DAILY_SALARY * 0.85
            else:
                bid = DAILY_SALARY * 0.70
            # Nudge above their second-highest to win without going maximal.
            bid = max(bid, second_prev_bid + 1.0)
            return min(budget, bid)

        # Moderate contention: bid enough to stay competitive.
        if highest_prev_bid >= DAILY_SALARY * 0.60:
            target = max(highest_prev_bid + 1.0, DAILY_SALARY * 0.55)
            if hp <= 3:
                target = max(target, DAILY_SALARY * 0.75)
            return min(budget, target)

    # No/weak trace: use supply to decide aggressiveness.
    # When supply is higher, we can bid less; when lower, we must bid more.
    # supply is float; map to a normalized pressure.
    if supply <= MIN_SUPPLY:
        pressure = 1.0
    elif supply >= MAX_SUPPLY:
        pressure = 0.2
    else:
        pressure = 1.0 - (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)

    base = DAILY_SALARY * (0.45 + 0.35 * pressure)

    # If our HP is low, increase bid to avoid further losses.
    if hp <= 2:
        base = DAILY_SALARY * 0.90
    elif hp <= 4:
        base = max(base, DAILY_SALARY * 0.70)

    # Never exceed budget.
    return min(budget, base)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Alive opponents only
    alive_opps = []
    for k, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((k, opp))

    # If no opponents, just bid enough to cover our need safely
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.45))

    # Read yesterday trace bids to infer aggressiveness
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

    # Baseline bid: aim to be competitive but not reckless
    # With supply 15-25, one unit of our requirement is 9; we want to avoid being the lowest bidder.
    # Scale with supply: higher supply -> can bid slightly less.
    supply_scale = (25.0 - supply) / 10.0  # 0 at 25, ~1 at 15
    supply_scale = max(0.0, min(1.0, supply_scale))

    # Determine risk from our hp and opponents yesterday aggressiveness
    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    no_water_days = int(my_status.get('no_water_days', 0))

    # Aggression estimate from yesterday
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    # If someone previously overbid heavily (Cindy/Eric patterns), we don't need to match the absolute max;
    # but if Alex died, the room likely needs strong bids to survive.
    # Use a target that reacts to highest_prev_bid but keeps a cap.
    target = 0.55 * DAILY_SALARY + 0.25 * highest_prev_bid + 15.0 * supply_scale

    # If our hp is low or we've already missed water, increase bid urgency
    if my_hp <= 2.0 or no_water_days >= 2:
        target *= 1.25
    elif my_hp <= 4.0:
        target *= 1.10

    # If opponents were generally bidding very high yesterday, slightly raise to avoid being undercut
    if avg_prev_bid > 100.0:
        target *= 1.08

    # Final constraints: cannot exceed budget; also avoid bidding above a reasonable fraction of daily salary
    # since supply is limited and we need to last.
    cap = DAILY_SALARY * 0.95
    bid = min(my_budget, cap, target)

    # Ensure non-negative
    if bid < 0.0:
        bid = 0.0

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

    supply = day_context['supply']
    day = day_context['day']

    # Identify alive opponents
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    # If no alive opponents, conserve
    if not alive:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Use yesterday's behavior: extract their previous bid
    prev_bids = []
    for oid, o in alive:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            prev_bids.append(float(b))

    # Estimate opponent pressure from yesterday
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_highest = 0.0
    if len(prev_bids) >= 2:
        sorted_b = sorted(prev_bids, reverse=True)
        second_highest = sorted_b[1]

    # Supply-based aggressiveness: more supply -> can afford higher bids
    # Compute a simple tier using explicit int indexing constraints
    # Map supply to tiers 0..2
    tier = 0
    if supply >= 22.0:
        tier = 2
    elif supply >= 18.0:
        tier = 1
    else:
        tier = 0

    # Base bid targets: try to beat the top yesterday bid when necessary
    # Cindy bid was very high and she survived; mimic that only when our hp/budget allow.
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    # If we are in danger (low hp or already accumulating no-water days), bid to secure water.
    danger = (hp <= 2) or (no_water_days >= 2)

    # Compute a cap based on remaining budget and the need to last (10 days meta)
    # Conservative: don't spend more than ~70% of budget in a single day unless danger.
    spend_cap = budget * (0.7 if danger else 0.45)

    # Target logic
    if danger:
        # If someone bid high yesterday, overbid slightly; otherwise bid near salary.
        target = highest_prev_bid + 5.0 if highest_prev_bid > 0 else DAILY_SALARY * 0.9
        # Also ensure we don't underbid below a minimum threshold.
        target = max(target, DAILY_SALARY * (0.65 + 0.1 * tier))
    else:
        # Not in immediate danger: bid enough to compete with top yesterday bids in higher supply.
        if highest_prev_bid >= DAILY_SALARY * 0.9:
            # Top bidder is aggressive; match/just beat if supply is high.
            target = (highest_prev_bid + 2.0) if tier >= 1 else max(highest_prev_bid - 3.0, DAILY_SALARY * 0.55)
        else:
            # If yesterday bids were moderate/low, bid around the second-highest or a tiered baseline.
            baseline = DAILY_SALARY * (0.45 + 0.15 * tier)
            target = max(baseline, second_highest + 1.5)

    # Final bid with constraints
    bid = min(budget, spend_cap, target)

    # Ensure non-negative and at least something if we can
    if bid < 0:
        bid = 0.0

    # If our computed bid is too low vs typical requirements and supply is adequate, bump slightly.
    # This helps when opponents are not consistently high.
    # Use explicit int conversion only where indexing would occur; here none.
    if not danger and supply >= MIN_SUPPLY:
        min_reasonable = DAILY_SALARY * (0.35 + 0.1 * tier)
        if bid < min_reasonable and budget >= min_reasonable:
            bid = min_reasonable

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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Basic safety
    my_hp = int(my_status['hp'])
    my_budget = float(my_status['budget'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive'):
            alive_opps.append(o)

    if not alive_opps:
        # If alone, bid conservatively but enough to avoid no-water
        return float(min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday immediate pressure from previous_trace
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

    # Supply pressure adjustment: lower supply => more aggressive
    # We want to avoid float index issues; only compute thresholds.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY + 1e-9)  # 0..1-ish
    low_supply = supply_ratio < 0.5

    # If opponents were bidding very high yesterday, they likely expect to win water.
    high_pressure = highest_prev_bid >= DAILY_SALARY * 1.35  # ~121.5

    # Core bid targets
    # - When high pressure: bid near (highest_prev_bid - small discount) to undercut.
    # - When not: bid mid-level to still compete.
    if high_pressure:
        # Undercut strategy: slightly below their max pressure, but not too low.
        base = highest_prev_bid * 0.92
        if low_supply:
            base *= 1.05
        # If my HP is low, increase willingness.
        if my_hp <= 2:
            base *= 1.15
        bid = base
    else:
        # Moderate bid; more aggressive if low supply or low HP.
        bid = DAILY_SALARY * (0.55 if not low_supply else 0.75)
        if my_hp <= 2:
            bid *= 1.25
        # If they still bid something nontrivial, slightly track it.
        if highest_prev_bid > 0:
            bid = max(bid, highest_prev_bid * 0.6)

    # Budget cap: never exceed budget; also avoid burning too much early.
    # With 10-day episode, keep some cushion.
    day_factor = 1.0
    if day >= 7:
        day_factor = 1.15
    max_affordable = my_budget * day_factor

    # Additional cap to prevent extreme overspend vs 90/day salary baseline
    hard_cap = DAILY_SALARY * 2.6  # 234
    bid = min(bid, hard_cap, max_affordable)

    # Ensure non-negative
    if bid < 0:
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context['supply'])
    day = day_context['day']

    # If we are in critical health, prioritize survival.
    if my_status['hp'] <= 2:
        cap = min(my_status['budget'], DAILY_SALARY * 0.95)
        return max(0.0, cap)

    # Collect yesterday bids from alive opponents for immediate pressure read.
    alive_opponents = [o for o in opponents_status.values() if o.get('alive', False)]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Determine how aggressive the field was yesterday.
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / float(len(yesterday_bids))
    else:
        highest_prev_bid = 0.0
        avg_prev_bid = 0.0

    # Supply pressure: higher supply means we can bid a bit less.
    supply_norm = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)  # 0..1
    supply_norm = max(0.0, min(1.0, supply_norm))

    # Base bid: target around a fraction of salary, adjusted by yesterday aggressiveness.
    # If field was very aggressive (near Eric's high bids), we must match more closely.
    aggressive_threshold = DAILY_SALARY * 0.75  # 67.5
    if highest_prev_bid >= aggressive_threshold:
        base = DAILY_SALARY * (0.60 + 0.15 * (1.0 - supply_norm))
    else:
        base = DAILY_SALARY * (0.50 + 0.10 * (1.0 - supply_norm))

    # If yesterday average bids were high, slightly increase.
    if avg_prev_bid >= aggressive_threshold:
        base *= 1.10

    # If we have no_water_days, increase urgency.
    no_water_days = int(my_status.get('no_water_days', 0) or 0)
    if no_water_days >= 2:
        base *= 1.20
    elif no_water_days == 1:
        base *= 1.10

    # Health-based scaling (but avoid overcommitting when hp is healthy).
    hp = int(my_status.get('hp', 0) or 0)
    if hp >= 8:
        base *= 0.95
    elif hp >= 5:
        base *= 1.00
    elif hp >= 3:
        base *= 1.10

    bid = float(base)

    # Ensure we don't exceed budget.
    bid = min(bid, float(my_status['budget']))

    # Keep bid non-negative.
    if bid < 0.0:
        bid = 0.0

    # Light day-based variance to avoid ties at exact values.
    bid += (day % 3) * 0.5

    return bid
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from opponents' previous_trace (immediate reaction only)
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
    second_prev_bid = 0.0
    if len(yesterday_bids) >= 2:
        sorted_b = sorted(yesterday_bids, reverse=True)
        second_prev_bid = sorted_b[1]

    # Estimate how many water units are likely available
    # (Only used to scale bid; indices not needed.)
    expected_units = supply / WATER_REQ

    # Determine urgency: if I've already gone without water, increase pressure.
    urgency_factor = 1.0
    if no_water_days >= 2:
        urgency_factor = 1.25
    if hp <= 2:
        urgency_factor = 1.6
    elif hp <= 4:
        urgency_factor = 1.3

    # Cindy-like pattern: if someone previously bid very high and survived, she likely continues.
    # We avoid matching the absolute max; instead we target just above the likely low-mid bids.
    target_base = DAILY_SALARY * 0.55

    # If highest previous bid was extremely high, treat it as a ceiling threat.
    # Bid slightly above the second-highest to steal water from everyone except the top spender.
    if highest_prev_bid >= DAILY_SALARY * 1.35:
        target_base = max(target_base, second_prev_bid + 2.0)
        # Still cap below the top bidder to avoid unnecessary budget burn.
        cap = min(DAILY_SALARY * 1.05, highest_prev_bid - 5.0)
        target = min(cap, target_base)
    else:
        # Otherwise, bid around the cluster midpoint or just above highest_prev_bid.
        if highest_prev_bid > 0:
            target = max(target_base, min(highest_prev_bid + 1.5, DAILY_SALARY * 0.95))
        else:
            target = target_base

    # Scale with expected scarcity: lower supply => more competitive => bid a bit more.
    scarcity_factor = 1.0
    if supply <= 17.0:
        scarcity_factor = 1.15
    elif supply <= 19.0:
        scarcity_factor = 1.08
    elif supply >= 22.0:
        scarcity_factor = 0.95

    bid = target * urgency_factor * scarcity_factor

    # Budget safety: never exceed budget; also avoid bidding too low when hp is critical.
    bid = max(0.0, min(budget, bid))

    # Hard floor when hp is low to prevent immediate death.
    if hp <= 2.5 and budget > 0:
        bid = max(bid, min(budget, DAILY_SALARY * 0.9))

    # If budget is tiny, bid proportionally.
    if budget < DAILY_SALARY * 0.4:
        bid = min(budget, bid)

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

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', True):
            alive_opps.append(o)

    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace
    prev_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate a competitive target bid from yesterday's observed spending
    if prev_bids:
        highest_prev = max(prev_bids)
        # If others were bidding very high, we need a bit more to avoid losing the allocation.
        if highest_prev >= DAILY_SALARY * 0.85:
            base = DAILY_SALARY * 0.33
            if my_hp <= 3:
                base = DAILY_SALARY * 0.85
            target = base + 0.15 * highest_prev
        else:
            # Otherwise, stay near the middle to conserve budget.
            target = max(DAILY_SALARY * 0.45, (sum(prev_bids) / float(len(prev_bids))) * 0.85)
    else:
        target = DAILY_SALARY * 0.55 if my_hp > 3 else DAILY_SALARY * 0.85

    # Supply-aware adjustment: if supply is scarce, bid slightly more.
    scarcity = 0.0
    if supply <= (MIN_SUPPLY + WATER_REQ):
        scarcity = 1.0
    elif supply <= MAX_SUPPLY:
        scarcity = 0.5
    target = target * (1.0 + 0.12 * scarcity)

    # Budget and survival constraints
    # If low hp, prioritize survival.
    if my_hp <= 2.0:
        cap = my_budget
        bid = min(cap, DAILY_SALARY * 0.95)
        return max(0.0, bid)

    # Otherwise, bid but don't overspend: keep some budget for later days.
    # Aim to spend a fraction depending on how much budget remains.
    spend_fraction = 0.55
    if my_hp <= 4.0:
        spend_fraction = 0.75

    max_bid = my_budget * spend_fraction
    bid = min(float(target), float(max_bid), my_budget)

    # Ensure non-negative and not exceeding a reasonable upper bound.
    if bid < 0.0:
        bid = 0.0
    # Hard safety cap to avoid runaway bids.
    bid = min(bid, DAILY_SALARY * 1.2)
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
    day = day_context.get('day', 0)

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Extract yesterday bids and survival pressure
    prev_bids = []
    prev_info = []  # (oid, bid, hp_after, budget_after)
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                bid_f = float(bid)
            except Exception:
                continue
            prev_bids.append(bid_f)
            prev_info.append((oid, bid_f, prev.get('hp_after', None), prev.get('budget_after', None)))

    # Identify likely heavy bidder (Cindy-like): high yesterday bid and still alive
    heavy_bid = None
    if prev_bids:
        heavy_bid = max(prev_bids)

    # Supply pressure: fewer units implies higher chance of bidding wars
    # supply is in [15,25]; map to 0..2 buckets
    supply_bucket = int((supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY + 1e-9) * 2)
    if supply_bucket < 0:
        supply_bucket = 0
    if supply_bucket > 2:
        supply_bucket = 2

    # Core strategy
    # If Cindy-like heavy bidder existed, match or slightly undercut only when we are at risk.
    risk = 0
    if hp <= 2:
        risk += 2
    if no_water_days >= 1:
        risk += 1
    if supply_bucket == 0:  # tight supply
        risk += 1

    # Baseline bid depends on risk
    if risk >= 2:
        target = DAILY_SALARY * 0.95
    elif risk == 1:
        target = DAILY_SALARY * 0.65
    else:
        target = DAILY_SALARY * 0.45

    # If heavy bidder was very high yesterday, increase target to avoid losing water.
    if heavy_bid is not None:
        if heavy_bid >= DAILY_SALARY * 1.6:  # ~>=144
            if risk >= 1:
                target = max(target, heavy_bid * 0.92)
            else:
                target = max(target, heavy_bid * 0.75)
        elif heavy_bid >= DAILY_SALARY * 0.9:  # ~>=81
            if risk >= 2:
                target = max(target, heavy_bid * 0.85)
            else:
                target = max(target, heavy_bid * 0.65)

    # Budget guardrails
    # Ensure we don't overspend when budget is low.
    if budget <= 0:
        return 0.0

    # Cap bid to avoid bankrupting early; still aim to secure water when at risk.
    # Use remaining budget fraction; more risk -> spend more.
    spend_frac = 0.35
    if risk >= 2:
        spend_frac = 0.85
    elif risk == 1:
        spend_frac = 0.60

    max_affordable = budget * spend_frac
    bid = min(max_affordable, target)

    # Minimum meaningful bid to compete
    min_bid = DAILY_SALARY * 0.25
    if bid < min_bid and risk >= 1:
        bid = min(budget, min_bid)

    # Final clamp
    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget
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
    day = day_context['day']

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace for immediate reaction
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
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    # Supply pressure: lower supply implies fewer winners/less water; bid more.
    supply_ratio = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Base target bid: moderate-high to compete without burning budget.
    # When supply is scarce (ratio near 0), increase bid.
    scarcity_multiplier = 1.0 + (1.0 - supply_ratio) * 0.6  # up to +60%

    # If yesterday highest bids were very high, others may be overbidding; still ensure we get enough water.
    # Use hp/no_water_days to decide aggressiveness.
    urgency = 0.0
    if hp <= 2:
        urgency = 1.0
    elif hp <= 4:
        urgency = 0.7
    elif no_water_days >= 2:
        urgency = 0.6
    else:
        urgency = 0.3

    # Reference to yesterday: if others were bidding near/above salary, we can slightly undercut.
    # If others were low, we can bid just enough.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        undercut_factor = 0.92
    elif highest_prev_bid >= DAILY_SALARY * 0.65:
        undercut_factor = 0.97
    else:
        undercut_factor = 1.02

    # Construct bid target using a blend of salary fraction and yesterday signal.
    salary_component = DAILY_SALARY * (0.45 + 0.35 * urgency)  # between ~0.45 and 0.80 of salary
    if yesterday_bids:
        signal_component = (avg_prev_bid * 0.35 + highest_prev_bid * 0.25)
    else:
        signal_component = 0.0

    target = (salary_component + signal_component * 0.25) * scarcity_multiplier * undercut_factor

    # Ensure we don't exceed budget; also keep a minimum bid to avoid being ignored.
    # If budget is low, bid proportionally to preserve survival.
    min_bid = 5.0
    if budget <= 0.0:
        return 0.0

    # If we're already in danger (hp low), spend more of remaining budget.
    spend_frac = 0.65 if urgency >= 0.7 else 0.45
    max_affordable = budget * spend_frac

    bid = min(target, max_affordable)
    bid = max(min_bid, bid)

    # Final clamp
    bid = max(0.0, min(bid, budget))
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

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    # Identify alive opponents and extract yesterday bids
    alive_opps = []
    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    yesterday_bids.append(float(prev.get('bid')))
                except Exception:
                    pass

    # Baseline: if we're low on hp, be aggressive; otherwise stay cost-effective.
    if hp <= 2:
        base_frac = 0.95
    elif hp <= 4:
        base_frac = 0.75
    else:
        base_frac = 0.55

    # Supply pressure: higher supply reduces need to outbid aggressively.
    # Normalize supply in [0,1]
    if MAX_SUPPLY > MIN_SUPPLY:
        s_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        s_norm = 0.5
    s_norm = max(0.0, min(1.0, s_norm))

    # If Cindy likely paid a lot yesterday, avoid matching her unless necessary.
    # Use yesterday max as a rough proxy for competitive pressure.
    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
    else:
        max_prev_bid = 0.0

    # Competitive adjustment: only chase when my hp is critical or supply is low.
    chase = (hp <= 4 and supply <= (MIN_SUPPLY + WATER_REQ)) or (hp <= 2)

    # Convert to bid amount with budget cap.
    # Target spending: base_frac of DAILY_SALARY, reduced when supply is high.
    target = DAILY_SALARY * base_frac * (0.85 + 0.3 * (1.0 - s_norm))

    if chase and max_prev_bid > 0:
        # Slightly over the observed max to increase chance of securing water.
        target = max(target, min(DAILY_SALARY * 0.98, max_prev_bid * 1.05 + 2.0))

    # Final cap: cannot exceed budget.
    bid = min(budget, target)

    # Ensure non-negative bid
    if bid < 0:
        bid = 0.0

    return bid
"""
