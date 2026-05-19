# ============================================================
# Experiment: exp_112
# Agent: Bob
# Source: exp_112
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

    alive_opps = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opps.append(opp)

    # Base target: aim to win enough to cover our requirement when supply is near mid/high.
    # Since bids are simultaneous and hidden, we use a heuristic bid fraction.
    # If supply is low, we bid more to avoid losing water.
    supply_norm = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_norm = max(0.0, min(1.0, supply_norm))

    # Conservative mid bid that scales with scarcity.
    scarcity = 1.0 - supply_norm
    base_frac = 0.45 + 0.25 * scarcity  # between ~0.45 and ~0.70

    # React to yesterday bids if available.
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    if prev_bids:
        highest_prev_bid = max(prev_bids)
        # If an opponent was bidding near our daily salary, they likely value survival highly.
        if highest_prev_bid >= 0.85 * DAILY_SALARY:
            # Overbid slightly unless we're already in very bad shape.
            if hp > 3:
                frac = min(0.95, base_frac + 0.20)
            else:
                frac = min(1.0, base_frac + 0.35)
        else:
            # Match the pressure just above their max previous bid.
            frac = base_frac
            # Translate their bid magnitude into an additional pressure.
            frac = max(frac, min(0.95, (highest_prev_bid + 5.0) / DAILY_SALARY))
    else:
        frac = base_frac

    # If our HP is low, we must prioritize water allocation.
    if hp <= 2:
        frac = min(1.0, frac + 0.35)
    elif hp <= 3:
        frac = min(0.98, frac + 0.15)

    # Convert fraction to bid, capped by budget.
    bid = frac * DAILY_SALARY
    if bid > budget:
        bid = budget

    # Also cap bid to a reasonable upper bound relative to supply.
    # (Prevents wasting budget when supply is abundant.)
    # We use a soft cap: 1.2 * supply as a proxy.
    soft_cap = max(0.0, 1.2 * supply)
    if bid > soft_cap:
        bid = min(bid, soft_cap)

    # Ensure non-negative.
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
    day = int(day_context['day'])

    # Alive opponents and their yesterday bids
    alive_opponents = [o for o in opponents_status.values() if o.get('alive', False)]
    yesterday_bids = []
    yesterday_hp_after = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        if prev.get('bid') is not None:
            yesterday_bids.append(float(prev['bid']))
            yesterday_hp_after.append(prev.get('hp_after', None))

    # Baseline: how many water units are likely available
    # We only need WATER_REQ=9 units; supply is 15-25 so usually enough for one requirement.
    # Use a conservative bid that scales with supply scarcity.
    scarcity = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)  # 0..1 roughly
    scarcity = max(0.0, min(1.0, scarcity))

    # Determine pressure from yesterday
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid
    else:
        highest_prev_bid = 0.0
        second_prev_bid = 0.0

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    # If we're in danger, bid aggressively.
    if my_hp <= 2 or my_no_water_days >= 2:
        bid = DAILY_SALARY * (0.85 + 0.15 * scarcity)
    else:
        # Otherwise, bid to beat typical moderate opponents (Alex/Eric) without matching Cindy.
        # Use a target anchored near second-highest yesterday bid, then add a small increment.
        # If no history, anchor to mid of salary.
        if yesterday_bids:
            target = second_prev_bid + 5.0
            # Cap below Cindy-like extreme pressure: do not exceed ~75% of highest_prev_bid unless needed.
            cap = 0.75 * highest_prev_bid if highest_prev_bid > 0 else DAILY_SALARY
            bid = min(target * (0.9 + 0.2 * scarcity), cap)
        else:
            bid = DAILY_SALARY * (0.55 + 0.15 * scarcity)

        # Small adjustment based on supply: if supply is scarce, increase bid slightly.
        bid = bid * (0.92 + 0.16 * scarcity)

    # Ensure bid is within budget and non-negative.
    bid = max(0.0, min(my_budget, bid))

    # If budget is too low, bid whatever remains.
    if my_budget <= 1.0:
        return my_budget

    # Avoid bidding fractions that could be penalized by some implementations.
    return float(round(bid, 2))
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive.append((opp_id, opp))

    if not alive:
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday bids from previous_trace (immediate reaction only)
    yesterday_bids = []
    for opp_id, opp in alive:
        prev = opp.get('previous_trace', None)
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    yesterday_bids.append(float(b))
                except Exception:
                    pass

    # Estimate scarcity pressure from supply relative to our requirement
    # If supply is closer to MIN_SUPPLY, competition is higher.
    scarcity = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    scarcity = max(0.0, min(1.0, float(scarcity)))

    # Determine aggressiveness based on yesterday's highest bid
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Baseline bid: mid level, scaled by scarcity
    # Keep it below extreme bids to avoid overpaying.
    base = DAILY_SALARY * (0.45 + 0.25 * scarcity)  # ~40-65

    # If someone was bidding very high yesterday, we slightly increase to avoid losing the allocation.
    if highest_prev_bid >= DAILY_SALARY * 0.85:  # >= 76.5
        base *= 1.15

    # If our HP is low or we already went without water, we must secure water.
    if hp <= 2.5 or no_water_days >= 2:
        base = max(base, DAILY_SALARY * (0.75 + 0.15 * scarcity))

    # If our HP is healthy and we are not starving, avoid overpaying.
    if hp >= 7 and no_water_days == 0:
        base = min(base, DAILY_SALARY * (0.55 + 0.15 * scarcity))

    # Also cap based on remaining budget
    bid = min(budget, base)

    # Ensure we bid at least a small positive amount when budget allows
    if bid <= 0 and budget > 0:
        bid = min(budget, DAILY_SALARY * 0.2)

    return float(bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    # Alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # If no opponents, bid conservatively
    if not alive_opps:
        return max(0.0, min(my_status.get('budget', 0.0), DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace only
    yesterday_bids = []
    yesterday_by_op = {}
    for oid, o in opponents_status.items():
        if not o.get('alive', False):
            continue
        prev = o.get('previous_trace', {})
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                bid_val = float(bid)
            except Exception:
                continue
            yesterday_bids.append(bid_val)
            yesterday_by_op[oid] = bid_val

    # Determine threat level from yesterday
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid
    else:
        highest_prev_bid = 0.0
        second_prev_bid = 0.0

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    # Base bid depends on urgency
    # If low HP or already accumulating no-water days, be more aggressive.
    if my_hp <= 2 or my_no_water_days >= 2:
        base = DAILY_SALARY * 0.85
    elif my_hp <= 4 or my_no_water_days == 1:
        base = DAILY_SALARY * 0.65
    else:
        base = DAILY_SALARY * 0.50

    # Exploit observed aggression: if someone previously bid near top, we need to outbid slightly.
    # Otherwise, undercut and rely on them overpaying.
    # Use supply to scale: when supply is high, we can bid lower.
    supply_scale = 0.9 if supply <= 18.0 else (1.0 if supply <= 21.0 else 0.85)

    # Target bid logic
    if highest_prev_bid >= DAILY_SALARY * 1.6:
        # Very aggressive field yesterday: bid to secure with slight margin.
        target = min(highest_prev_bid, second_prev_bid + 5.0)
        target = max(target, base)
    elif highest_prev_bid >= DAILY_SALARY * 1.1:
        # Moderate aggression: bid around base but try to beat second-highest.
        target = max(base, second_prev_bid + 2.5)
    else:
        # Generally conserved: bid around base, slightly reduced if supply is ample.
        target = base * supply_scale

    # Cap by budget and ensure non-negative
    bid = max(0.0, min(my_budget, target))

    # If budget is tiny, still bid enough to avoid wasting turn when urgent
    if my_budget <= 10.0:
        if my_hp <= 2 or my_no_water_days >= 2:
            bid = my_budget
        else:
            bid = min(my_budget, 5.0)

    return float(bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace only
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Baseline target bid based on yesterday
    if yesterday_bids:
        sorted_bids = sorted(yesterday_bids)
        # Mid-tier pressure estimate
        mid = sorted_bids[len(sorted_bids) // 2]
        # Upper pressure estimate (avoid chasing extremes)
        upper = sorted_bids[-1]
    else:
        mid = DAILY_SALARY * 0.55
        upper = DAILY_SALARY * 0.85

    # Supply scaling: with more supply, we can bid less aggressively
    # supply is between 15 and 25; normalize to [0,1]
    norm = (supply - 15.0) / (25.0 - 15.0)
    norm = max(0.0, min(1.0, norm))

    # Defensive adjustment if we are close to critical HP or have consecutive no-water days
    critical = (hp <= 2.5) or (no_water_days >= 2)

    if critical:
        # Try to secure water by bidding near/above mid-tier but not necessarily max
        target = max(mid + 3.0, DAILY_SALARY * 0.75)
    else:
        # If supply is higher, shade downward; if lower, shade upward slightly
        # Aim around mid-tier with a small edge.
        target = mid + (2.0 * (1.0 - norm))

        # If yesterday upper pressure was very high, we should avoid getting priced out
        if upper >= DAILY_SALARY * 0.95:
            target = max(target, DAILY_SALARY * 0.65)

    # Convert target to a feasible bid within budget
    # Also cap bid to avoid overpaying beyond what would be needed to win against mid-tier.
    bid_cap = min(budget, DAILY_SALARY * 1.0)
    bid = min(bid_cap, target)

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

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append(o)

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Read yesterday bids from previous_trace only (immediate reaction)
    yesterday_bids = []
    for o in alive_opponents:
        prev = o.get('previous_trace', None) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Pressure estimate: if someone previously bid very high, others likely try to outbid.
    high_bid_pressure = 1.0 if highest_prev_bid >= DAILY_SALARY * 0.85 else 0.0

    # Supply pressure: with higher supply, we can bid less to still secure water share.
    # Use explicit int conversion for any indices (none used here), keep arithmetic safe.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, float(supply_ratio)))

    # Core strategy:
    # - If my hp is low or I already had no-water days, bid to secure water.
    # - Otherwise bid moderately; only escalate if yesterday pressure was high.
    if my_hp <= 2 or my_no_water_days >= 2:
        base = DAILY_SALARY * (0.9 + 0.1 * high_bid_pressure)
    elif my_hp <= 4:
        base = DAILY_SALARY * (0.65 + 0.2 * high_bid_pressure)
    else:
        base = DAILY_SALARY * (0.55 + 0.15 * high_bid_pressure)  # safe hp

    # Adjust for supply: higher supply => bid slightly lower
    base *= (1.0 - 0.12 * supply_ratio)

    # If opponent pressure was very high, add a small increment to avoid losing the water contest
    if high_bid_pressure > 0.0:
        base += 5.0

    # Final cap by budget
    bid = min(my_budget, base)

    # Ensure non-negative and reasonable minimum
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Alive opponents and yesterday bids
    alive_opps = []
    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid', None)
            if bid is not None:
                try:
                    yesterday_bids.append(float(bid))
                except Exception:
                    pass

    # If no opponents alive, bid conservatively
    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Pressure estimate from yesterday
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # If we are already in danger (no water days accumulating), increase bid.
    # Each day without water costs hp; we react more aggressively near death.
    danger = (hp <= 2.5) or (no_water_days >= 2)

    # Determine a target bid level.
    # Since Cindy survived and likely bid high, we avoid matching her full strength unless we must.
    # We aim to beat typical underbidders: slightly above a fraction of yesterday's highest.
    if danger:
        # Must secure water; outbid by a margin.
        target = max(DAILY_SALARY * 0.75, highest_prev_bid * 0.65 + 5.0)
    else:
        # Moderate bid: enough to clear against low/medium bidders.
        # If yesterday's highest was very high, don't chase fully; bid around a mid percentile.
        if highest_prev_bid >= DAILY_SALARY * 1.2:
            target = max(DAILY_SALARY * 0.55, highest_prev_bid * 0.35 + 8.0)
        else:
            target = max(DAILY_SALARY * 0.45, highest_prev_bid * 0.5 + 6.0)

    # Supply-aware adjustment: if supply is low, competition is higher -> bid a bit more.
    if supply <= float(MIN_SUPPLY) + 1e-9:
        target *= 1.08
    elif supply >= float(MAX_SUPPLY) - 1e-9:
        target *= 0.95

    # Budget cap and non-negative
    bid = max(0.0, min(budget, target))

    # Also cap bid to a reasonable fraction of budget to avoid bankruptcy if we lose.
    # (Game uses daily_salary; keeping some buffer helps over 10-day horizon.)
    max_safe = max(0.0, budget * 0.65)
    if bid > max_safe and budget > 0:
        bid = max_safe

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

    supply = float(day_context['supply'])
    day = day_context['day']

    # If supply is low, we need to secure enough water; otherwise bid to compete lightly.
    # Compute how many full water units we can cover if we win at least one unit.
    # (We don't know exact mapping; use it as a conservative pressure proxy.)
    supply_units = supply / WATER_REQ

    alive_opps = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Use only yesterday's previous_trace for immediate reaction.
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev['bid']))

    # Estimate opponents' likely bidding level from yesterday.
    # If we saw a very high bid, assume strong competition continues.
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    median_prev_bid = 0.0
    if prev_bids:
        s = sorted(prev_bids)
        mid = len(s) // 2
        median_prev_bid = float(s[int(mid)])

    # Survival pressure: if our HP is low or we already have consecutive no-water days, bid aggressively.
    hp = int(my_status['hp'])
    no_water_days = int(my_status['no_water_days'])
    budget = float(my_status['budget'])

    # Determine aggressiveness target.
    # - If Cindy/Alex/Eric were bidding ~100+, we try to slightly over median/highest to capture water.
    # - If our HP is critical, go near daily salary to avoid death.
    if hp <= 2 or no_water_days >= 2:
        target = max(median_prev_bid + 5.0, DAILY_SALARY * 0.9)
    elif hp <= 4:
        target = max(median_prev_bid + 3.0, DAILY_SALARY * 0.7)
    else:
        # With buffer, undercut slightly relative to the highest observed.
        # Aim to beat the median cluster but not chase the absolute max.
        target = max(median_prev_bid + 2.0, DAILY_SALARY * 0.55)
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # Competition is intense; raise a bit.
            target = max(target, highest_prev_bid - 8.0)

    # Supply-aware scaling: when supply is scarce, increase bids to avoid losing the only effective allocation.
    if supply <= float(MIN_SUPPLY) + 0.5:
        target *= 1.08
    elif supply >= float(MAX_SUPPLY) - 0.5:
        target *= 0.92

    # Clamp to budget.
    bid = min(budget, target)

    # Ensure non-negative and at least a minimal bid if budget allows.
    if bid < 0.0:
        bid = 0.0
    if bid == 0.0 and budget > 0.0:
        bid = min(budget, DAILY_SALARY * 0.2)

    return float(bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
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

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return float(min(my_budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from each opponent's previous_trace
    prev_bids = []
    for opp_id, opp in alive_opps:
        pt = opp.get('previous_trace', {})
        b = pt.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev = max(prev_bids) if prev_bids else 0.0
    second_prev = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev

    # Pressure estimation: high bids imply competition; low bids imply we can undercut.
    # Also react to our own risk (no_water_days and low hp).
    risk = 0
    if my_hp <= 2.0:
        risk += 2
    if my_hp <= 4.0:
        risk += 1
    if my_no_water_days >= 1:
        risk += 1

    # Supply-to-need heuristic: higher supply reduces urgency.
    # Use safe integer index mapping for any list access (none used), but keep logic float-safe.
    supply_factor = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)  # 0..1
    if supply_factor < 0.0:
        supply_factor = 0.0
    if supply_factor > 1.0:
        supply_factor = 1.0

    # Target bid: aim slightly above typical upper pressure without going to max.
    # If opponents were bidding very high yesterday, we increase; else we moderate.
    # Normalize to DAILY_SALARY scale.
    high_threshold = DAILY_SALARY * 0.85

    if highest_prev >= high_threshold:
        # Competitive day: bid around a fraction of the top bids.
        base = min(my_budget, max(DAILY_SALARY * 0.55, second_prev * 0.98))
        # If we're in danger, bid closer to top.
        if risk >= 2:
            base = min(my_budget, max(DAILY_SALARY * 0.75, highest_prev * 0.98))
        elif risk == 1:
            base = min(my_budget, max(DAILY_SALARY * 0.65, highest_prev * 0.90))
        # Adjust by supply: lower supply -> slightly higher.
        urgency_mult = 1.0 + (1.0 - supply_factor) * 0.12
        bid = base * urgency_mult
    else:
        # Not extreme yesterday: undercut slightly above a reasonable level.
        # Use highest_prev as a weak signal.
        base = max(DAILY_SALARY * (0.45 + 0.1 * (1.0 - supply_factor)), highest_prev * 0.85)
        if risk >= 2:
            base = max(base, DAILY_SALARY * 0.8)
        elif risk == 1:
            base = max(base, DAILY_SALARY * 0.6)
        bid = base

    # Ensure we don't bid more than our budget and keep a floor to avoid wasting turns.
    bid = float(min(my_budget, bid))

    # If budget is extremely low, bid as much as possible.
    if my_budget <= 1.0:
        return float(my_budget)

    # Soft floor: if we have any budget, bid at least a small fraction when risk is nonzero.
    if risk >= 1:
        bid = max(bid, my_budget * 0.25)
    else:
        bid = max(bid, my_budget * 0.15)

    # Final cap to avoid overpaying late in day progression
    # (episode_days=10, so later days may warrant higher bids; we lightly increase).
    day_mult = 1.0 + (day / 10.0) * 0.05
    bid = bid * day_mult
    bid = float(min(my_budget, bid))

    # At minimum, bid non-negative.
    if bid < 0.0:
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

    supply = day_context['supply']
    day = day_context['day']

    # Alive opponents only
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # If no opponents, bid just enough to secure water
    if not alive_opps:
        # Conservative: aim for single-unit competition
        bid = DAILY_SALARY * 0.35
        return min(my_status['budget'], bid)

    # Read yesterday's immediate behavior from previous_trace
    prev_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        if prev.get('bid') is not None:
            prev_bids.append(prev['bid'])

    # Estimate market-clearing pressure from yesterday
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev_bid
    else:
        highest_prev_bid = 0.0
        second_prev_bid = 0.0

    # Our HP/budget urgency
    hp = my_status.get('hp', 0)
    budget = my_status.get('budget', 0.0)
    no_water_days = my_status.get('no_water_days', 0)

    # If we are in danger, we must bid aggressively.
    if hp <= 2 or no_water_days >= 2:
        target = max(DAILY_SALARY * 0.6, highest_prev_bid * 0.95)
        bid = min(budget, target)
        return bid

    # If others were bidding extremely high, undercut slightly.
    # Use a threshold tied to daily salary since traces show very large bids.
    if highest_prev_bid >= DAILY_SALARY * 1.5:
        # Undercut: aim around second-highest + small margin, but not too low.
        # Ensure we still compete.
        undercut = second_prev_bid + 2.0
        floor_bid = DAILY_SALARY * 0.45
        target = max(floor_bid, undercut)
        bid = min(budget, target)
        return bid

    # Otherwise, moderate bid: enough to secure without matching extremes.
    # Scale with supply: lower supply => higher bid.
    # supply is float; compute normalized in [0,1]
    norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    # If supply is low (norm near 0), bid higher.
    scarcity_factor = 1.0 - norm
    base = DAILY_SALARY * (0.42 + 0.18 * scarcity_factor)

    # Also react to highest_prev_bid if it was non-trivial.
    if highest_prev_bid > 0:
        target = max(base, highest_prev_bid * 0.55)
    else:
        target = base

    bid = min(budget, target)
    return bid
"""
