# ============================================================
# Experiment: exp_049
# Agent: Bob
# Source: exp_049
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = day_context['supply']
    day = day_context['day']

    budget = my_status['budget']
    hp = my_status['hp']

    alive_opponents = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    # If no opponents, take a safe moderate bid.
    if not alive_opponents:
        if hp <= 2:
            return min(budget, DAILY_SALARY * 0.85)
        return min(budget, DAILY_SALARY * 0.55)

    # Read yesterday's behavior from previous_trace.
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid', None)
        if bid is not None:
            yesterday_bids.append(bid)

    # Default if no trace.
    if not yesterday_bids:
        if hp <= 2:
            return min(budget, DAILY_SALARY * 0.8)
        return min(budget, DAILY_SALARY * 0.5)

    highest_prev_bid = max(yesterday_bids)
    lowest_prev_bid = min(yesterday_bids)

    # Estimate how many full water units we can roughly aim for.
    # Ensure indices are int-safe.
    # Target units based on supply: round down to avoid overshooting.
    target_units = int(supply // float(WATER_REQ))
    if target_units < 1:
        target_units = 1

    # Convert target units to a bid pressure level.
    # Higher target_units implies we want more water; map to bid fraction.
    # target_units of 1..2 (since supply range 15..25) => fractions 0.45..0.65
    if target_units <= 1:
        base_frac = 0.45
    else:
        base_frac = 0.65

    # If opponents previously bid very high, they were likely desperate.
    high_threshold = DAILY_SALARY * 0.85
    mid_threshold = DAILY_SALARY * 0.6

    if highest_prev_bid >= high_threshold:
        # Avoid getting into a pure bidding war; still bid enough to secure water.
        if hp <= 2:
            frac = 0.9
        else:
            frac = max(base_frac, 0.6)
    elif highest_prev_bid >= mid_threshold:
        # Moderate competition: slightly outbid to secure advantage.
        frac = max(base_frac, 0.55)
        # Nudge upward if our hp is healthy.
        if hp >= 4:
            frac = min(0.75, frac + 0.1)
    else:
        # They were not bidding aggressively; take more supply share.
        frac = max(base_frac, 0.6)
        if hp <= 2:
            frac = min(frac, 0.75)

    # Additional adjustment: if their lowest bid was also low, increase aggressiveness.
    if lowest_prev_bid < DAILY_SALARY * 0.35:
        if hp >= 4:
            frac = min(0.8, frac + 0.1)

    bid = DAILY_SALARY * frac

    # Never exceed budget.
    if bid > budget:
        bid = budget

    # If hp is critically low, conserve budget.
    if hp <= 1:
        bid = min(bid, DAILY_SALARY * 0.7)

    # Ensure non-negative.
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    # Identify alive opponents
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    # If no opponents alive, conserve budget
    if not alive:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace (immediate reaction only)
    yesterday_bids = []
    for oid, o in alive:
        prev = o.get('previous_trace', None)
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    yesterday_bids.append(float(b))
                except Exception:
                    pass

    # Estimate opponent pressure
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / float(len(yesterday_bids))
    else:
        highest_prev_bid = 0.0
        avg_prev_bid = 0.0

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Supply pressure heuristic: if supply is tight, bid more.
    supply_ratio = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    # supply_ratio near 0 => tight => pressure high
    tightness = 1.0 - max(0.0, min(1.0, supply_ratio))

    # Base bid target around yesterday survivors' band (~100-135)
    # Use highest_prev_bid as a cap-ish reference, but avoid chasing too hard.
    target = 0.0
    if my_hp <= 2.0 or no_water_days >= 2:
        # Critical: try to secure water aggressively.
        # Aim slightly below yesterday's highest to win without maximum waste.
        target = min(highest_prev_bid * 0.92, avg_prev_bid + 25.0)
        target += 15.0 * tightness
    else:
        # Comfortable: bid moderately above the average of alive opponents.
        # If highest_prev_bid was very high, we must match pressure.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            target = min(highest_prev_bid * 0.85, avg_prev_bid + 20.0)
        else:
            target = max(DAILY_SALARY * 0.45, avg_prev_bid * 0.95)
        target += 10.0 * tightness

    # Keep bid within reasonable bounds and budget
    # Also avoid bidding above a fraction of budget early.
    budget_cap = my_budget
    if day <= 3:
        budget_cap = min(my_budget, DAILY_SALARY * 0.95)
    else:
        budget_cap = min(my_budget, DAILY_SALARY * 1.2)

    bid = max(0.0, min(budget_cap, target))

    # If supply likely allows more than one unit, we can bid slightly lower.
    # Approx: if supply >= 2*WATER_REQ then competition for first unit is less.
    if supply >= 2.0 * WATER_REQ:
        bid *= 0.92

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

    # Extract yesterday bids only (immediate reaction)
    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Estimate opponent pressure from yesterday
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = 0.0
    if len(yesterday_bids) >= 2:
        sorted_b = sorted(yesterday_bids, reverse=True)
        second_prev_bid = sorted_b[1]

    # Base bid: aim to secure water without matching Alex's peak.
    # With supply in [15,25], a single unit of water is likely enough; avoid overbidding.
    # Use hp/no_water_days to decide urgency.
    urgency = 0
    if hp <= 2.0:
        urgency = 2
    elif hp <= 4.0:
        urgency = 1

    if no_water_days >= 2:
        urgency = max(urgency, 1)

    # Supply factor: higher supply reduces need to bid aggressively.
    if supply <= (MIN_SUPPLY + MAX_SUPPLY) / 2.0:
        supply_factor = 1.0
    else:
        supply_factor = 0.75

    # Target bid level.
    # If yesterday pressure was very high, we slightly undercut rather than chase the max.
    if highest_prev_bid >= DAILY_SALARY * 0.7:
        # Underbid relative to highest; if urgent, bid closer.
        target = (highest_prev_bid - 3.0) if urgency == 0 else (highest_prev_bid - 1.0)
    else:
        # Otherwise bid around a fraction of salary, scaled by supply/urgency.
        base = DAILY_SALARY * (0.45 + 0.15 * urgency)
        target = base * supply_factor

    # Safety: ensure non-negative and within budget.
    target = max(0.0, float(target))
    bid = min(budget, target)

    # If budget is too low, bid whatever remains (still non-negative).
    if bid < 0.0:
        bid = 0.0

    # Small day-dependent smoothing to avoid ties when not urgent.
    if urgency == 0:
        bid = max(0.0, bid - (day % 3) * 0.5)

    # Final clamp
    bid = min(budget, max(0.0, bid))
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

    # Identify alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # If no opponents alive, bid conservatively to avoid overspending
    if not alive_opps:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.4))

    # Use yesterday's trace to estimate competitive pressure
    prev_bids = []
    high_hp_bias = 0
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        bid = prev.get('bid', None)
        if bid is not None:
            prev_bids.append(float(bid))
        # If they were already near death yesterday, expect more aggressive bids today
        if prev.get('hp_after', None) is not None:
            if prev['hp_after'] <= 3:
                high_hp_bias += 1

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    # Estimate how many water units exist; supply is float, so convert to int index safely.
    # We don't directly need indexing, but keep logic stable.
    supply_units = int(supply / WATER_REQ) if WATER_REQ > 0 else 0
    # If supply is tight, competition is higher.
    tight_supply = supply_units <= 1

    my_hp = my_status.get('hp', 0)
    my_budget = my_status.get('budget', 0.0)

    # Base target: shade below typical competitive bids.
    # If competition was high yesterday, slightly undercut.
    if highest_prev_bid > 0:
        # Undercut by 5-12% depending on tightness and our HP.
        shade = 0.10
        if tight_supply:
            shade = 0.07
        if my_hp <= 2:
            shade = 0.03
        target = highest_prev_bid * (1.0 - shade)
    else:
        # Fallback to average-ish bid band
        target = max(avg_prev_bid * 0.95, DAILY_SALARY * (0.5 if my_hp > 3 else 0.85))

    # If multiple opponents were near death yesterday, bid a bit more to secure water.
    if high_hp_bias >= 2:
        target *= 1.08
    elif high_hp_bias == 1:
        target *= 1.04

    # If our HP is healthy, avoid overbidding; if low, bid closer to target/high.
    if my_hp > 6:
        target *= 0.92
    elif my_hp > 3:
        target *= 0.97
    else:
        target *= 1.05

    # Also cap by what we can afford and by a reasonable fraction of daily salary.
    # Keep some budget for later days.
    afford_cap = my_budget
    # In tight supply, allow higher spend; otherwise be conservative.
    spend_cap = DAILY_SALARY * (0.75 if tight_supply else 0.60)

    bid = min(afford_cap, spend_cap, target)

    # Ensure non-negative and at least a minimal bid to avoid zeroing out.
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    # If no opponents, bid enough to cover our need safely.
    if not alive_opps:
        need_bid = min(budget, DAILY_SALARY * 0.35)
        return max(0.0, need_bid)

    # Read yesterday's immediate behavior from previous_trace.
    prev_bids = []
    prev_max = 0.0
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                b = float(b)
                prev_bids.append(b)
                if b > prev_max:
                    prev_max = b
            except Exception:
                pass

    # Estimate how much water we need to avoid falling behind.
    # Supply is total available; we bid to compete for enough to keep hp stable.
    # Risk increases with no_water_days.
    risk = 0.0
    if no_water_days >= 2:
        risk = 0.35
    elif no_water_days == 1:
        risk = 0.15

    # If Cindy-like pressure existed yesterday (high max), don't match her ceiling; bid a competitive mid-high.
    # Use thresholds relative to DAILY_SALARY.
    pressure = 0.0
    if prev_max >= DAILY_SALARY * 1.8:
        pressure = 0.9
    elif prev_max >= DAILY_SALARY * 1.3:
        pressure = 0.7
    elif prev_max >= DAILY_SALARY * 0.9:
        pressure = 0.5
    else:
        pressure = 0.35

    # Supply factor: when supply is low, competition is tighter; increase bid slightly.
    supply_factor = 0.0
    if supply <= float(MIN_SUPPLY):
        supply_factor = 0.25
    elif supply >= float(MAX_SUPPLY):
        supply_factor = 0.05
    else:
        # linear between MIN_SUPPLY and MAX_SUPPLY
        t = (supply - float(MIN_SUPPLY)) / (float(MAX_SUPPLY) - float(MIN_SUPPLY))
        supply_factor = 0.25 * (1.0 - t) + 0.05 * t

    # Base bid depends on hp: if healthy, we can bid less; if low, bid more.
    if hp >= 8:
        base = DAILY_SALARY * (0.45 + supply_factor + risk)
    elif hp >= 5:
        base = DAILY_SALARY * (0.65 + supply_factor + risk)
    else:
        base = DAILY_SALARY * (0.85 + supply_factor + risk)

    # Adjust for observed pressure.
    target = base + pressure * (DAILY_SALARY * 0.25)

    # Never exceed a conservative fraction of budget; also ensure non-negative.
    # If budget is small, cap harder.
    if budget <= DAILY_SALARY:
        cap = budget
    else:
        cap = min(budget, DAILY_SALARY * 2.0)

    # Final bid rounding to 2 decimals.
    bid = min(target, cap)
    if bid < 0.0:
        bid = 0.0

    return float(round(bid, 2))
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

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return float(min(my_budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids (immediate reaction only)
    prev_bids = []
    prev_by_id = {}
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                fb = float(b)
                prev_bids.append(fb)
                prev_by_id[oid] = fb
            except Exception:
                pass

    # Baseline bid depends on my urgency
    if my_hp <= 2 or my_no_water_days >= 2:
        urgency_factor = 0.95
    elif my_hp <= 4 or my_no_water_days >= 1:
        urgency_factor = 0.75
    else:
        urgency_factor = 0.6

    # Opponent pressure from yesterday
    if prev_bids:
        max_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / float(len(prev_bids))

        # Cindy-like aggressiveness: if someone bid very high yesterday, we shade up but not fully match
        if max_prev >= DAILY_SALARY * 1.55:  # ~139.5
            # Increase to just above likely clearing level
            target = max(avg_prev * 0.9, DAILY_SALARY * 0.68)
        elif max_prev >= DAILY_SALARY * 1.15:  # ~103.5
            target = max(avg_prev * 0.85, DAILY_SALARY * 0.6)
        else:
            target = max(avg_prev * 0.75, DAILY_SALARY * 0.5)
    else:
        target = DAILY_SALARY * 0.55

    target *= urgency_factor

    # Budget-aware and supply-aware caps
    # If supply is low, water is scarce: bid relatively higher.
    scarcity = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        scarcity = (MAX_SUPPLY - min(MAX_SUPPLY, max(MIN_SUPPLY, supply))) / float(MAX_SUPPLY - MIN_SUPPLY)
    else:
        scarcity = 0.5

    # Add scarcity adjustment without exceeding salary too much
    target *= (1.0 + 0.25 * scarcity)

    # Ensure we don't overspend: keep a reserve for later days
    # Episode is 10 days; earlier days can spend more, later days should conserve.
    # day is 0-indexed or 1-indexed unknown; use a gentle curve.
    day_weight = 1.0
    if day >= 7:
        day_weight = 0.75
    elif day >= 5:
        day_weight = 0.85
    elif day <= 2:
        day_weight = 1.05

    target *= day_weight

    # Hard caps to avoid bankruptcy
    max_reasonable = DAILY_SALARY * 1.25
    bid = min(target, max_reasonable, my_budget)

    # If my budget is low, still bid enough to avoid death if very urgent
    if my_hp <= 2:
        bid = min(my_budget, max(bid, DAILY_SALARY * 0.85))

    # Final clamp
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

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from immediate previous_trace only
    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(float(prev['bid']))

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how many water units matter today (supply is total; water requirement is per day)
    # We only use this to scale bid pressure with supply.
    # If supply is low, winning water is more valuable.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))
    low_supply = 1.0 - supply_ratio

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    # Strategy:
    # - Cindy likely bids high; avoid matching her unless my hp is critical.
    # - If opponent yesterday bid was extremely high, increase slightly only when my hp is low.
    # - Otherwise bid a mid amount that should secure enough water without burning budget.
    pressure = 0.0
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        pressure = 0.75
    elif highest_prev_bid >= DAILY_SALARY * 0.55:
        pressure = 0.45
    elif highest_prev_bid > 0:
        pressure = 0.25

    # Base bid anchored to supply pressure and my hp
    # Keep bids below the likely top bidder unless survival is at stake.
    if hp <= 1.5:
        base = DAILY_SALARY * (0.85 + 0.1 * low_supply)
    elif hp <= 3.0:
        base = DAILY_SALARY * (0.65 + 0.15 * low_supply) + pressure * DAILY_SALARY * 0.15
    else:
        base = DAILY_SALARY * (0.45 + 0.10 * low_supply) + pressure * DAILY_SALARY * 0.10

    # If highest prev bid was very high, cap my bid to avoid overpaying.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        cap = highest_prev_bid * 0.55
    else:
        cap = DAILY_SALARY * 0.75

    bid = min(base, cap, budget)

    # Ensure non-negative and at least small bid if budget allows
    if bid < 0.0:
        bid = 0.0
    if budget > 0.0 and bid == 0.0:
        bid = min(budget, DAILY_SALARY * 0.15)

    return float(bid)
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

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    # If no opponents, bid enough to avoid starvation.
    if not alive_opps:
        target = DAILY_SALARY * 0.4
        return float(min(budget, target))

    # Read yesterday bids from opponent traces for immediate reaction.
    prev_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate how aggressive the market was.
    prev_max = max(prev_bids) if prev_bids else 0.0

    # Our baseline bid: moderate, responsive to supply and urgency.
    # Higher supply means we can bid slightly less to still clear.
    supply_factor = (supply - 15.0) / (25.0 - 15.0)  # in [0,1] roughly
    supply_factor = max(0.0, min(1.0, supply_factor))

    # Urgency increases with low hp and consecutive no-water days.
    urgency = 0.0
    if hp <= 2.0:
        urgency += 0.35
    elif hp <= 4.0:
        urgency += 0.20
    if no_water_days >= 2:
        urgency += 0.25
    elif no_water_days == 1:
        urgency += 0.10

    # Exploit: if others overbid yesterday (high prev_max), we can shade down.
    # Cindy/Eric showed survivable high bids; we avoid matching them unless needed.
    overbid = 1.0 if prev_max >= DAILY_SALARY * 0.9 else 0.0

    # Target bid range.
    # When overbid==1, start lower; otherwise bid more.
    base = DAILY_SALARY * (0.48 - 0.12 * overbid + 0.10 * supply_factor)
    target = base * (1.0 + urgency)

    # Safety: if we are in danger, bid more aggressively.
    if hp <= 1.0 or no_water_days >= 3:
        target = DAILY_SALARY * (0.85 - 0.05 * overbid)
    elif hp <= 3.0:
        target = max(target, DAILY_SALARY * (0.60 - 0.05 * overbid))

    # Cap by budget and keep within reasonable bounds.
    # Also ensure some minimum bid to avoid being shut out when supply is low.
    min_bid = DAILY_SALARY * (0.25 + 0.15 * (1.0 - supply_factor))
    target = max(target, min_bid)

    bid = min(budget, target)
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

    supply = day_context['supply']
    day = day_context['day']

    # Alive opponents
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    if not alive:
        # If alone, bid modestly to save budget
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.4))

    # Use only yesterday's previous_trace for immediate reaction
    prev_bids = []
    prev_hp = []
    for oid, o in alive:
        pt = o.get('previous_trace', {})
        if pt and pt.get('bid') is not None:
            prev_bids.append(float(pt['bid']))
        prev_hp.append(float(o.get('hp', 0)))

    # Estimate who is the main threat: highest previous bid
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Determine our urgency
    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))

    # If we are low HP, prioritize survival; otherwise, match/just-under pressure.
    # Alex likely continues high bids; Eric likely stays low; others likely 0.
    target = 0.0

    # Pressure banding
    if highest_prev_bid >= DAILY_SALARY * 0.75:
        # Alex is pressuring hard: bid near but not equal to reduce chance of losing all water
        if hp <= 2.5:
            target = DAILY_SALARY * 0.95
        elif hp <= 4.0:
            target = max(highest_prev_bid * 0.9, DAILY_SALARY * 0.7)
        else:
            target = max(highest_prev_bid * 0.85, DAILY_SALARY * 0.6)
    elif highest_prev_bid >= DAILY_SALARY * 0.35:
        # Moderate pressure: bid enough to be competitive
        if hp <= 2.5:
            target = DAILY_SALARY * 0.9
        else:
            target = max(highest_prev_bid * 0.75, DAILY_SALARY * 0.5)
    else:
        # Low pressure overall: conserve
        if hp <= 2.5:
            target = DAILY_SALARY * 0.85
        else:
            target = DAILY_SALARY * 0.45

    # Convert target to feasible bid given our budget
    bid = max(0.0, min(budget, float(target)))

    # If supply is low, competition for limited water increases: slightly increase bid
    # (supply is between 15 and 25)
    if supply <= (MIN_SUPPLY + 1.0):
        bid = min(budget, bid * 1.15)
    elif supply >= (MAX_SUPPLY - 1.0):
        bid = bid * 0.95

    # Final clamp
    if bid < 0.0:
        bid = 0.0
    if bid > budget:
        bid = budget

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
    day = int(day_context.get('day', 0))

    # Basic health/budget guards
    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        # If alone, bid enough to take water with minimal spend
        target = min(budget, DAILY_SALARY * 0.35)
        return float(max(0.0, target))

    # Yesterday trace reaction (only immediate, one-step)
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

    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    max_prev = max(prev_bids) if prev_bids else 0.0

    # Estimate how many water units are likely needed to survive the day.
    # If supply is tight, competition increases; bid slightly higher.
    # supply is in [15,25], water requirement is 9 per unit.
    # We'll translate to a rough urgency multiplier.
    # Ensure indices are int-safe if any arrays are used (none used).
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    urgency = 0.75 + 0.5 * max(0.0, min(1.0, supply_ratio))  # ~0.75..1.25

    # If my hp is low or I already have many no-water days, I must secure water.
    if hp <= 2 or no_water_days >= 2:
        # Push to beat the aggressive bidders (Alex/Cindy around ~90-96)
        desired = max_prev if max_prev > 0 else DAILY_SALARY * 0.9
        # Add a small premium for competition when supply is higher
        desired = desired * (0.98 + 0.04 * urgency) + 2.0
        bid = min(budget, desired, DAILY_SALARY * 1.2)
        return float(max(0.0, bid))

    # Otherwise, bid relative to yesterday's observed pressure.
    # If others bid high, match a fraction to avoid overpaying.
    if avg_prev > 0:
        # When their average is high, we bid closer to it; else bid around mid salary.
        pressure = avg_prev / DAILY_SALARY  # ~1.0 for 90-100 bids
        # Convert pressure into bid multiplier: 0.55..0.95
        mult = 0.55 + 0.40 * max(0.0, min(1.0, pressure))
        desired = DAILY_SALARY * mult * urgency
        # If their max is much higher, nudge upward slightly
        if max_prev > DAILY_SALARY * 0.9:
            desired = max(desired, DAILY_SALARY * 0.75 * urgency)
            desired = min(desired, max_prev + 5.0)
    else:
        desired = DAILY_SALARY * 0.55 * urgency

    bid = min(budget, desired)
    # Keep a floor so we don't bid too low versus aggressive neighbors
    bid = max(bid, DAILY_SALARY * 0.30)
    return float(max(0.0, bid))
"""
