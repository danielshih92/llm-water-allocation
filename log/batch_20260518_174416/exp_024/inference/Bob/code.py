# ============================================================
# Experiment: exp_024
# Agent: Bob
# Source: exp_024
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
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    # Baseline bid: ensure we can pay while not risking bankruptcy.
    # If we're already in trouble (low hp or many no-water days), bid higher.
    trouble = (hp <= 2.0) or (no_water_days >= 2)

    # Read yesterday's behavior from previous_trace (immediate reaction only)
    prev_bids = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict) and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    # If no info, bid based on our status and today's supply.
    if not prev_bids:
        if trouble:
            target = DAILY_SALARY * 0.85
        else:
            # If supply is near lower bound, increase bid; otherwise keep moderate.
            if supply <= (MIN_SUPPLY + 1.0):
                target = DAILY_SALARY * 0.65
            else:
                target = DAILY_SALARY * 0.5
        return max(0.0, min(budget, target))

    highest_prev_bid = max(prev_bids)

    # If opponents were bidding very high yesterday, they likely needed water.
    # Bid slightly below their pressure to improve expected surplus.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        if trouble:
            # Still bid high enough to secure water, but cap below max pressure.
            target = min(budget, DAILY_SALARY * 0.92)
        else:
            # Underbid just a bit relative to yesterday's max.
            target = min(budget, highest_prev_bid - 1.0)
            # Ensure we don't bid too low when supply is tight.
            if supply <= (MIN_SUPPLY + 1.0):
                target = max(target, DAILY_SALARY * 0.55)
    else:
        # Opponents were not desperate; bid enough to win our requirement.
        if trouble:
            target = DAILY_SALARY * 0.8
        else:
            # If supply is tight, raise bid; if abundant, moderate.
            if supply <= (MIN_SUPPLY + 1.0):
                target = max(highest_prev_bid + 1.0, DAILY_SALARY * 0.6)
            else:
                target = max(highest_prev_bid + 0.5, DAILY_SALARY * 0.5)

    # Convert target into a safe bid within budget.
    target = float(target)
    if target < 0.0:
        target = 0.0
    if budget <= 0.0:
        return 0.0

    # Additional safeguard: if supply is extremely low relative to our requirement,
    # we should commit more; otherwise avoid overpaying.
    # (We don't know allocation rule, so we only modulate bid strength.)
    if supply < float(WATER_REQ):
        target = max(target, DAILY_SALARY * 0.75)

    return max(0.0, min(budget, target))
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    # Identify alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # If no opponents are alive, take what you need with minimal waste
    if not alive_opps:
        need = max(0.0, WATER_REQ - float(my_status.get('no_water_days', 0)) * 0.0)
        # In absence of exact mapping, bid a conservative amount
        cap = max(0.0, float(my_status.get('budget', 0.0)))
        return min(cap, DAILY_SALARY * 0.4)

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Read yesterday bids from previous_trace for immediate reaction
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    # Supply-based aggressiveness: medium scenario supply range ~15-25
    # If supply is closer to MAX, water is plentiful -> bid less.
    # If supply is closer to MIN, water is tight -> bid more.
    supply_pos = 0.0
    try:
        supply_pos = (supply - float(MIN_SUPPLY)) / (float(MAX_SUPPLY) - float(MIN_SUPPLY))
    except Exception:
        supply_pos = 0.5
    if supply_pos < 0.0:
        supply_pos = 0.0
    if supply_pos > 1.0:
        supply_pos = 1.0

    # Base target bid: Eric-like survival with modest bids; avoid Cindy's extreme spending.
    # Tight supply => increase toward ~0.7*salary, plentiful => decrease toward ~0.45*salary.
    base = DAILY_SALARY * (0.70 - 0.25 * supply_pos)  # ~63 to 45

    # React to pressure from yesterday's highest bids
    # If someone previously bid very high (>= 0.85*salary), contention is likely.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        pressure_factor = 1.15
    elif avg_prev_bid >= DAILY_SALARY * 0.60:
        pressure_factor = 1.05
    else:
        pressure_factor = 1.00

    # If my HP is low or I have accumulated no-water days, I must secure water.
    if my_hp <= 2.0 or no_water_days >= 2:
        urgency_factor = 1.35
    elif my_hp <= 4.0:
        urgency_factor = 1.15
    else:
        urgency_factor = 1.00

    target = base * pressure_factor * urgency_factor

    # Ensure we don't exceed budget; also avoid bidding too low to be effective.
    if my_budget <= 0.0:
        return 0.0

    # Minimum bid to compete when tight; still conservative to preserve budget.
    min_bid = DAILY_SALARY * (0.35 if supply_pos > 0.6 else 0.50)

    bid = target
    if bid < min_bid:
        bid = min_bid

    # Cap bid by budget and also by a safety ceiling to avoid Cindy-like overspending.
    safety_ceiling = DAILY_SALARY * 0.95
    if bid > safety_ceiling:
        bid = safety_ceiling

    if bid > my_budget:
        bid = my_budget

    # Final guard
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # If we are already in danger, prioritize survival.
    if my_status['hp'] is None:
        my_status['hp'] = 0
    if my_status['budget'] is None:
        my_status['budget'] = 0
    if my_status['no_water_days'] is None:
        my_status['no_water_days'] = 0

    budget = float(my_status['budget'])
    hp = float(my_status['hp'])
    no_water_days = int(my_status['no_water_days'])

    # Alive opponents that likely compete for water.
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    # Baseline: how many full allocations are possible.
    # Index-safe: convert to int before using as an index.
    # For our strategy, we only need a coarse estimate.
    # If supply is near 15, fewer winners; bid lower. If near 25, more can be satisfied; bid slightly higher.
    supply_ratio = (supply - float(MIN_SUPPLY)) / (float(MAX_SUPPLY) - float(MIN_SUPPLY) + 1e-9)
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Read yesterday's bids from traces to infer aggressiveness.
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    # If no trace info, use conservative bid.
    if not prev_bids:
        if hp <= 2 or no_water_days >= 2:
            target = DAILY_SALARY * 0.85
        else:
            target = DAILY_SALARY * (0.45 + 0.2 * supply_ratio)
        return max(0.0, min(budget, target))

    # Use top aggressor's yesterday bid to set our bid ceiling.
    highest_prev_bid = max(prev_bids)
    avg_prev_bid = sum(prev_bids) / float(len(prev_bids))

    # Heuristic: Alex survived with high bids; others died with low bids.
    # We don't want to mirror the highest bidder; we want to outbid only when needed.
    # If yesterday highest was very high, assume at least one agent is willing to spend heavily.
    # Bid enough to beat the likely threshold but keep budget.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # High competition: bid moderately high unless we are already safe.
        if hp <= 2 or no_water_days >= 2:
            target = DAILY_SALARY * (0.85 + 0.05 * supply_ratio)
        else:
            target = DAILY_SALARY * (0.55 + 0.15 * supply_ratio)
    else:
        # Competition was not extreme: lean on supply and our hp.
        if hp <= 2 or no_water_days >= 2:
            target = DAILY_SALARY * (0.75 + 0.1 * supply_ratio)
        else:
            # Slightly above average but capped.
            target = max(DAILY_SALARY * 0.45, avg_prev_bid * 0.9)
            target = target + (DAILY_SALARY * 0.1) * supply_ratio

    # Ensure we don't bid above budget; also keep a reserve for later days.
    # Reserve fraction increases when hp is high.
    if hp >= 7:
        reserve_frac = 0.35
    elif hp >= 4:
        reserve_frac = 0.25
    else:
        reserve_frac = 0.15

    max_affordable = max(0.0, budget * (1.0 - reserve_frac))
    bid = min(max_affordable, target)

    # If we are very low hp, override reserve.
    if hp <= 1:
        bid = min(budget, DAILY_SALARY * 0.95)

    # Final clamp.
    bid = max(0.0, float(bid))
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

    supply = float(day_context.get('supply', MIN_SUPPLY))
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

    # Extract yesterday bids (only immediate reaction)
    yesterday_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                yesterday_bids.append(float(bid))
            except Exception:
                pass

    # Identify Cindy's yesterday bid as a proxy for aggressive pressure
    cindy_prev = opponents_status.get('Cindy', {}).get('previous_trace', {}) or {}
    cindy_bid = cindy_prev.get('bid', None)
    try:
        cindy_bid = float(cindy_bid) if cindy_bid is not None else None
    except Exception:
        cindy_bid = None

    # Decide base bid level
    # If Cindy was aggressive, we slightly undercut to avoid overpaying, but still bid enough to secure water.
    if cindy_bid is not None:
        if cindy_bid >= DAILY_SALARY * 1.1:
            # Cindy likely willing to pay; avoid matching her full amount.
            target = cindy_bid * 0.85
        elif cindy_bid >= DAILY_SALARY * 0.85:
            target = cindy_bid * 0.8
        else:
            target = max(DAILY_SALARY * 0.45, cindy_bid + 5.0)
    else:
        if yesterday_bids:
            highest_prev = max(yesterday_bids)
            # If someone was very high, don't chase fully.
            if highest_prev >= DAILY_SALARY * 0.9:
                target = highest_prev * 0.75
            else:
                target = max(DAILY_SALARY * 0.55, highest_prev + 2.0)
        else:
            target = DAILY_SALARY * 0.55

    # Scale by our urgency
    # Lower HP / more no-water days -> bid higher.
    urgency = 0.0
    if my_hp <= 2:
        urgency = 0.35
    elif my_hp <= 4:
        urgency = 0.2
    elif my_hp <= 6:
        urgency = 0.1

    if my_no_water_days >= 2:
        urgency += 0.15
    if my_no_water_days >= 4:
        urgency += 0.25

    # Supply-based adjustment: with more supply, we can bid less.
    # Convert to a rough fraction of max supply.
    supply_frac = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_frac = max(0.0, min(1.0, supply_frac))

    # If supply is low, increase bid; if high, decrease.
    supply_factor = 1.0 + (0.5 - supply_frac) * 0.35  # ranges ~1.175 to 0.825

    target = target * (1.0 + urgency) * supply_factor

    # Hard caps to avoid bankruptcy.
    # In this meta, aggressive bidding drained others; keep a safety reserve.
    safety_reserve = DAILY_SALARY * 0.2
    max_affordable = max(0.0, my_budget - safety_reserve)

    # Also cap to a reasonable multiple to avoid matching Cindy too closely.
    # Since Cindy max bid was ~127.5, keep below ~1.45 salary.
    hard_cap = DAILY_SALARY * 1.45

    bid = min(target, max_affordable, hard_cap, my_budget)

    # If we are very low HP, allow a larger fraction of budget.
    if my_hp <= 2 and my_budget > 0:
        bid = min(my_budget, max(bid, DAILY_SALARY * 0.9))

    # Ensure non-negative
    if bid < 0.0:
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
        return float(min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from immediate previous_trace
    yesterday_bids = []
    yesterday_hp_after = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                yesterday_bids.append(float(bid))
            except Exception:
                pass
        try:
            yesterday_hp_after.append(int(prev.get('hp_after', o.get('hp', 0))))
        except Exception:
            yesterday_hp_after.append(int(o.get('hp', 0)))

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = 0.0
    if len(yesterday_bids) >= 2:
        sorted_bids = sorted(yesterday_bids, reverse=True)
        second_prev_bid = sorted_bids[1]

    # Supply pressure: moderate supply implies fewer winners; bid closer to incumbents.
    # We map supply to a multiplier.
    if supply <= MIN_SUPPLY:
        supply_mult = 1.0
    elif supply >= MAX_SUPPLY:
        supply_mult = 0.75
    else:
        # linear interpolation between 1.0 at 15 and 0.75 at 25
        supply_mult = 1.0 - 0.25 * ((supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY))

    # Urgency based on HP/no_water_days
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
        urgency = max(urgency, 0.8)

    # Core strategy: undercut the strongest yesterday bidder slightly,
    # but if we're very urgent, match closer.
    # Observed meta: Cindy/Eric average bids ~110; aim just below them.
    target_base = highest_prev_bid

    # If our urgency is low, underbid; if high, bid closer.
    if urgency < 0.5:
        target = target_base - 3.0
    else:
        target = target_base - 1.0

    # Add small adjustment for supply
    target = target * supply_mult

    # Ensure we don't bid too low to lose when supply is tight.
    # Use a floor tied to our urgency.
    if urgency >= 0.8:
        floor_bid = DAILY_SALARY * 0.75
    elif urgency >= 0.4:
        floor_bid = DAILY_SALARY * 0.55
    else:
        floor_bid = DAILY_SALARY * 0.45

    # If highest_prev_bid is extremely low (e.g., due to one agent dying), revert to a conservative bid.
    if highest_prev_bid < DAILY_SALARY * 0.4:
        target = max(target, floor_bid)
    else:
        target = max(target, floor_bid)

    # Cap by budget and avoid overcommitting when budget is low.
    # Also keep some buffer for later days.
    buffer_factor = 0.85 if day <= 5 else 0.95
    max_affordable = budget * buffer_factor

    bid = float(min(max_affordable, target))

    # If bid becomes non-positive due to budget, bid what we can.
    if bid <= 0.0:
        bid = float(min(budget, DAILY_SALARY * 0.3))

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
    day = day_context.get('day', 0)

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace for immediate reaction
    prev_bids = []
    prev_hp_after = []
    prev_budget_after = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                prev_bids.append(float(bid))
            except Exception:
                pass
        if prev:
            if 'hp_after' in prev:
                try:
                    prev_hp_after.append(float(prev.get('hp_after')))
                except Exception:
                    pass
            if 'budget_after' in prev:
                try:
                    prev_budget_after.append(float(prev.get('budget_after')))
                except Exception:
                    pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    # Determine aggressiveness: if others were spending heavily, we bid enough to avoid losing.
    # Use our hp/no-water days to decide urgency.
    urgency = 0
    if my_hp <= 2.0:
        urgency += 2
    elif my_hp <= 4.0:
        urgency += 1
    if my_no_water_days >= 2:
        urgency += 1

    # Supply pressure: with limited supply, higher bids are more valuable.
    # supply is between 15 and 25; normalize.
    supply_norm = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_norm = max(0.0, min(1.0, supply_norm))

    # Baseline bid levels
    # If others were bidding very high yesterday, we match a fraction to secure.
    if highest_prev_bid >= DAILY_SALARY * 1.3:
        base = max(DAILY_SALARY * 0.75, avg_prev_bid * 0.85)
    elif highest_prev_bid >= DAILY_SALARY * 0.9:
        base = max(DAILY_SALARY * 0.6, avg_prev_bid * 0.7)
    else:
        base = max(DAILY_SALARY * 0.45, avg_prev_bid * 0.55)

    # Adjust with urgency and supply pressure.
    # When supply is low, we increase bids to prevent starvation.
    base *= (1.0 + 0.35 * (1.0 - supply_norm))
    base *= (1.0 + 0.25 * urgency)

    # If we suspect opponents overextended (some had 0 budget yesterday), we can slightly undercut.
    undercut = 1.0
    if prev_budget_after:
        # If many had low budgets after, they might bid less today.
        low_budget_count = sum(1 for b in prev_budget_after if b <= 1e-6)
        if low_budget_count >= max(1, len(prev_budget_after) // 3):
            undercut = 0.9

    target = base * undercut

    # Convert to feasible bid: cannot exceed our budget.
    bid = min(my_budget, target)

    # Safety: if we are in critical hp state, ensure a higher bid floor.
    if my_hp <= 2.0:
        bid = max(bid, min(my_budget, DAILY_SALARY * 0.95))
    elif my_no_water_days >= 3:
        bid = max(bid, min(my_budget, DAILY_SALARY * 0.8))

    # If we are healthy and opponents were not bidding hard, conserve.
    if my_hp >= 7.0 and highest_prev_bid < DAILY_SALARY * 0.85:
        bid = min(bid, my_budget, DAILY_SALARY * 0.55)

    # Ensure non-negative
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Determine alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive'):
            alive_opps.append(o)

    # If no opponents alive, bid low
    if not alive_opps:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from immediate trace
    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    yesterday_bids.append(float(b))
                except Exception:
                    pass

    # Compute a pressure signal from yesterday
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = 0.0
    if len(yesterday_bids) >= 2:
        srt = sorted(yesterday_bids, reverse=True)
        second_prev_bid = srt[1]

    # Base bid: moderate to beat typical mid-pack without overpaying
    # If supply is high, competition likely increases but we can be cheaper.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY + 1e-9)
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Health pressure
    hp = float(my_status['hp'])
    no_water_days = int(my_status['no_water_days'])
    budget = float(my_status['budget'])

    # If we're in danger, bid aggressively; otherwise stay conservative.
    danger = 0
    if hp <= 2.0:
        danger = 2
    elif hp <= 4.0:
        danger = 1
    if no_water_days >= 2:
        danger = max(danger, 2)

    # Strategy: target around a fraction of highest yesterday bid, but cap by need.
    # If Cindy-like overbidding existed (very high highest_prev_bid), don't match it.
    target = 0.0
    if highest_prev_bid > 0:
        # Use second-highest as a safer anchor when available
        anchor = second_prev_bid if second_prev_bid > 0 else highest_prev_bid
        # In moderate competition, bid slightly above anchor; in high competition, bid a bit below highest.
        if danger == 0:
            target = min(highest_prev_bid * 0.85, anchor + DAILY_SALARY * (0.08 + 0.05 * (1.0 - supply_ratio)))
        elif danger == 1:
            target = min(highest_prev_bid * 0.95, anchor + DAILY_SALARY * (0.12 + 0.05 * (1.0 - supply_ratio)))
        else:
            target = min(highest_prev_bid * 1.05, anchor + DAILY_SALARY * (0.18 + 0.08 * (1.0 - supply_ratio)))
    else:
        # Fallback
        target = DAILY_SALARY * (0.45 + 0.15 * (1.0 - supply_ratio))

    # If supply is barely above requirement, we may need to secure water more reliably.
    if supply < (WATER_REQ * 1.2):
        target *= 1.12

    # Final clamp to budget and non-negative
    bid = max(0.0, min(budget, target))

    # Ensure we don't bid trivially low when danger is high
    if danger >= 2:
        bid = max(bid, min(budget, DAILY_SALARY * 0.75))
    elif danger == 1:
        bid = max(bid, min(budget, DAILY_SALARY * 0.55))

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

    my_hp = float(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    if not alive:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Estimate how competitive bids were yesterday from traces.
    prev_bids = []
    for oid, o in alive:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # Base bid depends on our hp and supply pressure.
    # If supply is high, we can bid less and still likely win water.
    # If our hp is low, we must bid to avoid death.
    supply_factor = 0.55
    if supply >= 22:
        supply_factor = 0.45
    elif supply <= 16:
        supply_factor = 0.65

    # Urgency: if we have gone without water, increase bid.
    urgency = 0.0
    if my_no_water_days >= 2:
        urgency = 0.35
    elif my_no_water_days == 1:
        urgency = 0.18

    # Opponent pressure: use yesterday's high bids.
    pressure = 0.0
    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / float(len(prev_bids))
        # Normalize pressure around typical aggressive levels.
        pressure = max(0.0, (avg_prev - DAILY_SALARY * 0.5) / (DAILY_SALARY * 0.5))
        pressure = min(1.0, pressure)
        # If someone was extremely aggressive yesterday, slightly increase our bid.
        if highest_prev >= DAILY_SALARY * 0.85:
            urgency = max(urgency, 0.25)

    # Target bid: undercut aggressive opponents while ensuring we can cover our need.
    # We assume winning requires outbidding some fraction; thus bid between base and base+pressure.
    base = DAILY_SALARY * supply_factor
    target = base * (1.0 + 0.6 * pressure + urgency)

    # Ensure we don't overspend when hp is healthy.
    if my_hp >= 7:
        target *= 0.85
    elif my_hp <= 3:
        target *= 1.25

    # Cap by budget.
    bid = max(0.0, min(my_budget, target))

    # Avoid zero bids unless budget is tiny.
    if bid < 1e-6:
        bid = min(my_budget, DAILY_SALARY * 0.2)

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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    if budget <= 0:
        return 0.0

    # Collect yesterday bids only from immediate previous_trace
    prev_bids = []
    prev_info = []
    for opp_id, opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                b = float(b)
            except Exception:
                continue
            prev_bids.append(b)
            prev_info.append((opp_id, b, prev.get('hp_after', None), prev.get('status', None)))

    # Baseline target: aim slightly above Eric-like pressure but far below Cindy-like extremes
    # Use supply to cap intensity: more supply -> can bid less while still securing water.
    # Approximate expected number of water units available.
    # Ensure indices are ints where needed.
    supply_units = int(supply / WATER_REQ) if WATER_REQ > 0 else 0
    if supply_units < 1:
        supply_units = 1

    # Determine yesterday pressure bands
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        lowest_prev_bid = min(prev_bids)
        # If Cindy-like high pressure exists, avoid matching it.
        high_band = 0.75 * highest_prev_bid
        mid_target = max(DAILY_SALARY * 0.55, lowest_prev_bid + 20.0)

        # If someone died yesterday, they likely over/under bid; use their direction to infer aggressiveness.
        # If any opponent had negative hp_after, treat as "failed" and bid moderately (not extreme).
        failed = False
        for _, b, hp_after, status in prev_info:
            if hp_after is not None:
                try:
                    if float(hp_after) < 0:
                        failed = True
                        break
                except Exception:
                    pass

        # Core bid decision
        if failed:
            target = min(mid_target, DAILY_SALARY * 0.75)
        else:
            # If nobody died, bid closer to the top but still avoid Cindy extremes.
            target = min(max(mid_target, DAILY_SALARY * 0.65), DAILY_SALARY * 0.85)

        # If yesterday highest bid was extremely high, we assume Cindy is pushing; reduce.
        if highest_prev_bid >= DAILY_SALARY * 1.5:
            target = min(target, DAILY_SALARY * 0.70)

        # If our hp is low, we must secure water: increase toward target+.
        if hp <= 2.0 or no_water_days >= 2:
            target = max(target, DAILY_SALARY * 0.85)
        elif hp <= 4.0:
            target = max(target, DAILY_SALARY * 0.70)

        # If supply is high, we can bid slightly less.
        if supply >= 22.0:
            target *= 0.95
        elif supply <= 16.0:
            target *= 1.05

    else:
        # No previous bids: use conservative mid bid.
        target = DAILY_SALARY * 0.60
        if hp <= 2.0 or no_water_days >= 2:
            target = DAILY_SALARY * 0.90
        elif hp <= 4.0:
            target = DAILY_SALARY * 0.75

    # Convert target to a feasible bid with budget and some safety margin.
    # Also avoid bidding above budget.
    bid = float(target)

    # Small day-based modulation to prevent ties/predictability.
    # Use day parity only.
    if int(day) % 2 == 0:
        bid *= 1.02
    else:
        bid *= 0.98

    # Final clamp
    if bid < 0.0:
        bid = 0.0
    if bid > budget:
        bid = budget

    # Ensure we don't bid trivially low when we need water.
    if (hp <= 2.0 or no_water_days >= 2) and bid < DAILY_SALARY * 0.6:
        bid = min(budget, DAILY_SALARY * 0.85)

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

    # Identify alive opponents
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        # If no opponents, bid enough to secure water but not waste budget
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.35))

    # Read yesterday bids from previous_trace (immediate reaction)
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Estimate how many water units are available this day
    # supply is total water; each unit costs WATER_REQ
    units_available = int(supply / float(WATER_REQ))
    if units_available < 1:
        units_available = 1

    # Determine a target bid based on yesterday pressure
    # If others bid very high, they likely overpay; we undercut.
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        lowest_prev_bid = min(yesterday_bids)

        # Thresholds tuned to yesterday meta outcomes (bids often ~80-160)
        very_high = DAILY_SALARY * 0.9  # 81
        high = DAILY_SALARY * 0.75     # 67.5

        # If someone was near/above very_high, bid slightly below to win with less spend.
        if highest_prev_bid >= very_high:
            # Conservative if our hp is low
            if float(my_status['hp']) <= 2:
                bid = DAILY_SALARY * 0.95
            else:
                bid = highest_prev_bid - 5.0
                # Ensure we still have a meaningful chance
                if bid < max(DAILY_SALARY * 0.45, lowest_prev_bid + 1.0):
                    bid = max(DAILY_SALARY * 0.45, lowest_prev_bid + 1.0)
        elif highest_prev_bid >= high:
            # Moderate pressure: bid around the upper-middle of yesterday bids
            bid = (highest_prev_bid + lowest_prev_bid) * 0.5
            # If supply allows multiple units, we can bid slightly lower
            if units_available >= 2:
                bid -= 5.0
        else:
            # Low pressure: bid enough to secure, but not chase
            bid = max(DAILY_SALARY * 0.5, highest_prev_bid + 2.0)
            if units_available >= 2:
                bid -= 3.0
    else:
        # No yesterday bid info: default mid
        bid = DAILY_SALARY * 0.55

    # Budget and survival-day risk controls
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status.get('no_water_days', 0))

    # If we are already at risk of running out, increase bid.
    # (Assume consecutive no-water days are costly; exact penalty handled by environment.)
    if no_water_days >= 2 or hp <= 2:
        bid = max(bid, DAILY_SALARY * 0.85)
    elif hp <= 4:
        bid = max(bid, DAILY_SALARY * 0.65)

    # If budget is tight, cap bid.
    max_affordable = budget
    # Also avoid spending more than needed per day: keep within a reasonable band.
    # Since winning requires competing, we allow up to ~1.2 salary when desperate.
    desperation_cap = DAILY_SALARY * 1.2 if (hp <= 2 or no_water_days >= 3) else DAILY_SALARY * 0.9

    bid = float(bid)
    if bid < 0.0:
        bid = 0.0
    bid = min(bid, max_affordable, desperation_cap)

    # Ensure we don't bid trivially low if we need water
    if hp > 4 and no_water_days <= 1:
        # Can be slightly lower
        bid = max(bid, DAILY_SALARY * 0.35)

    return float(bid)
"""
