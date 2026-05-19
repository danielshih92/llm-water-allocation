# ============================================================
# Experiment: exp_019
# Agent: Bob
# Source: exp_019
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

    # Alive opponents and yesterday bids
    alive_opponents = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Compute pressure from yesterday
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid
    else:
        highest_prev_bid = 0.0
        second_prev_bid = 0.0

    # Estimate how tight the market is today
    # If supply is low, raise bids; if high, lower bids.
    # Use explicit int conversions for any indexing (none used here).
    supply_tightness = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)  # 0..1-ish
    supply_tightness = max(0.0, min(1.0, supply_tightness))

    # Budget and hp-based risk control
    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))

    # Target bid tiers
    strong_pressure = highest_prev_bid >= DAILY_SALARY * 0.85
    moderate_pressure = (highest_prev_bid >= DAILY_SALARY * 0.55) or (second_prev_bid >= DAILY_SALARY * 0.45)

    if strong_pressure:
        # Opponents likely desperate; match pressure but avoid full budget drain if hp is okay.
        base = DAILY_SALARY * (0.35 if hp > 3 else 0.75)
        # If supply is tighter than yesterday likely, add a bit.
        bid = base + DAILY_SALARY * 0.25 * supply_tightness
        # Ensure we are at least competitive versus their highest previous bid.
        bid = max(bid, min(budget, highest_prev_bid + 1.0))
    elif moderate_pressure:
        base = DAILY_SALARY * (0.45 if hp > 3 else 0.65)
        bid = base + DAILY_SALARY * 0.15 * supply_tightness
        bid = max(bid, min(budget, highest_prev_bid * 0.92 + 2.0))
    else:
        # Low observed bids: conserve budget.
        base = DAILY_SALARY * (0.35 if hp > 3 else 0.6)
        bid = base + DAILY_SALARY * 0.1 * supply_tightness
        # If supply is extremely tight, still increase.
        if supply <= float(WATER_REQ):
            bid = max(bid, DAILY_SALARY * 0.55)

    # Final cap by budget and a small safety floor to avoid 0 bids.
    bid = min(bid, budget)
    if bid < 0.0:
        bid = 0.0
    # Avoid bidding more than needed when budget is tiny.
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

    supply = day_context['supply']
    day = day_context['day']

    # Determine how many full water requirements are available/likely contested.
    # Use int casts to avoid float index issues.
    # (We don't index lists, but we keep arithmetic guarded.)
    supply_int = int(supply)
    # Target: if supply is tight, we bid higher.
    tightness = 0.0
    if supply_int <= MIN_SUPPLY:
        tightness = 1.0
    elif supply_int >= MAX_SUPPLY:
        tightness = 0.0
    else:
        tightness = (MAX_SUPPLY - supply_int) / float(MAX_SUPPLY - MIN_SUPPLY)

    alive_opponents = [o for o in opponents_status.values() if o.get('alive')]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Read yesterday bids from immediate previous_trace only.
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            prev_bids.append(float(b))

    prev_max_bid = max(prev_bids) if prev_bids else 0.0
    prev_avg_bid = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    hp = my_status.get('hp', 0)
    budget = my_status.get('budget', 0)

    # Base bid: enough to beat typical moderate bids but avoid Cindy-like extremes.
    # Tight supply pushes us upward.
    base = DAILY_SALARY * (0.45 + 0.25 * tightness)  # ~40-67

    # Escalate if someone already signaled extreme pressure yesterday.
    # Cindy's yesterday max was ~168 with high bids; if we see bids near that, respond.
    if prev_max_bid >= DAILY_SALARY * 1.6:
        base = DAILY_SALARY * (0.85 + 0.1 * tightness)  # ~76-90
    elif prev_max_bid >= DAILY_SALARY:
        base = DAILY_SALARY * (0.65 + 0.15 * tightness)  # ~59-77

    # If our HP is low, we must secure water; otherwise conserve.
    if hp <= 2:
        base *= 1.15
    elif hp >= 7:
        base *= 0.9

    # If our budget is low, cap to what we can afford.
    bid = min(budget, base)

    # Ensure non-negative and at least a small positive bid when budget allows.
    if bid <= 0 and budget > 0:
        bid = min(budget, DAILY_SALARY * 0.2)

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
    day = day_context.get('day', 0)

    # Alive opponents and their yesterday bids
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return min(float(my_status.get('budget', 0.0)), DAILY_SALARY * 0.4)

    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Competitive pressure from yesterday
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = (sum(prev_bids) / float(len(prev_bids))) if prev_bids else 0.0

    # If someone (likely Alex) died yesterday, reduce our overreaction; instead target a mid-high bid.
    # We detect death via yesterday hp_after.
    death_signal = False
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        hp_after = prev.get('hp_after', None)
        if hp_after is not None:
            try:
                if float(hp_after) <= 0:
                    death_signal = True
            except Exception:
                pass

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    # Supply factor: higher supply means less need to outbid.
    # Ensure indices are safe by using int() only where needed (no list indexing here).
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Base target bid: hover below the average competitive bids.
    # Use highest_prev_bid as an upper anchor only when my hp is critical.
    if my_hp <= 2.0 or my_no_water_days >= 2:
        # Critical: bid more aggressively but still try to undercut top bids.
        target = min(highest_prev_bid * 0.92 + 2.0, avg_prev_bid * 0.98 + 5.0)
    else:
        # Non-critical: bid around a strong-but-not-top fraction of the competitive band.
        # If death_signal, opponents may have overbid; slightly lower target.
        band = avg_prev_bid if avg_prev_bid > 0 else (DAILY_SALARY * 0.6)
        target = band * (0.78 + 0.12 * supply_ratio)
        if death_signal:
            target *= 0.95

    # Also cap by a fraction of our budget to avoid going broke.
    # If day is late (10-day episode), preserve less.
    day_int = int(day) if day is not None else 0
    late_factor = 0.85 if day_int >= 7 else 0.65
    budget_cap = my_budget * late_factor

    # Final bid bounded by budget and sensible minimum.
    bid = min(max(1.0, target), budget_cap, my_budget)

    # If we can afford, ensure we can cover at least one water requirement purchase.
    # (Game mechanics unknown; treat as direct bid amount.)
    if my_budget <= 0.0:
        return 0.0

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

    # Alive opponents only
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    # If no one alive, bid just enough to secure
    if not alive_opps:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.4))

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])

    # Estimate opponent pressure from yesterday's bids
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
    # Also look at second-highest to gauge how wide the gap was
    sorted_prev = sorted(prev_bids, reverse=True)
    second_prev_bid = sorted_prev[1] if len(sorted_prev) > 1 else sorted_prev[0] if sorted_prev else 0.0

    # Supply tightness: if supply is low, water is scarcer, so we should bid more.
    # Map supply into [0,1] where 0=MIN_SUPPLY, 1=MAX_SUPPLY
    if MAX_SUPPLY - MIN_SUPPLY > 0:
        supply_t = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_t = 0.5
    # Scarcity factor: higher when supply is low
    scarcity = 1.0 - max(0.0, min(1.0, supply_t))

    # Vulnerability-based escalation: if my hp is low, bid aggressively to avoid no-water days.
    hp_pressure = 0.0
    if my_hp <= 1.0:
        hp_pressure = 1.0
    elif my_hp <= 3.0:
        hp_pressure = 0.7
    elif my_hp <= 5.0:
        hp_pressure = 0.35

    # Base bid: aim to beat typical weaker bids without matching Cindy's top bid unless needed.
    # Use second_prev_bid as a proxy for "contested" level.
    base = max(DAILY_SALARY * 0.45, second_prev_bid + 2.0)

    # If highest_prev_bid was very high, Cindy likely secured; we can either try to beat her (expensive)
    # or outbid only the weaker one. We'll try to beat second-highest unless my hp is critical.
    if highest_prev_bid >= DAILY_SALARY * 1.9:
        if hp_pressure >= 0.7:
            # Critical: try to match/beat the top bid slightly
            target = highest_prev_bid + 3.0
        else:
            # Not critical: slightly above second-highest
            target = second_prev_bid + 3.0
    else:
        # Moderate pressure: adjust with scarcity
        target = base * (0.85 + 0.3 * scarcity)

    # Final bid with budget cap
    bid = float(target)

    # Ensure bid is non-negative and not above budget
    if bid < 0.0:
        bid = 0.0
    if my_budget < 0.0:
        my_budget = 0.0
    bid = min(bid, my_budget)

    # If supply is extremely low and we have enough budget, ensure some competitive bid
    if supply <= float(WATER_REQ) + 6.0:  # ~15
        bid = max(bid, min(my_budget, DAILY_SALARY * (0.55 + 0.25 * hp_pressure)))

    # If budget is too low, bid whatever we can
    if my_budget <= 1.0:
        return my_budget

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

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    # If no one alive, conserve.
    if not alive:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday bids only from previous_trace.
    prev_bids = []
    for oid, o in alive:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else 0.0

    # Determine risk level from my own hp/no-water days.
    # If I'm close to dying, I must bid aggressively.
    critical = (my_hp <= 2.0) or (my_no_water_days >= 2)
    low = (my_hp <= 4.0)

    # Supply pressure: higher supply reduces need to overbid.
    # Map supply in [15,25] to a factor in [1.0,0.7]
    if MAX_SUPPLY == MIN_SUPPLY:
        supply_factor = 1.0
    else:
        t = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
        supply_factor = 1.0 - 0.3 * max(0.0, min(1.0, t))

    # Opponent behavior inference:
    # If someone previously bid very high (near/above 0.85*DAILY_SALARY), expect bidding war.
    high_war = highest_prev_bid >= (DAILY_SALARY * 0.85)

    # Base target bid aiming to match competitive level but not exceed.
    # Use highest_prev_bid as anchor; otherwise use a conservative baseline.
    if highest_prev_bid > 0.0:
        # Slightly above the likely clearing level, but cap by budget.
        target = (highest_prev_bid + 1.0) * supply_factor
    else:
        target = DAILY_SALARY * 0.55 * supply_factor

    # Adjust based on my health.
    if critical:
        target = max(target, DAILY_SALARY * 0.9 * supply_factor)
    elif low:
        target = max(target, DAILY_SALARY * 0.65 * supply_factor)

    # If war is predicted, increase modestly; otherwise keep lean.
    if high_war and not critical:
        target = max(target, (DAILY_SALARY * 0.75) * supply_factor)
    elif not high_war and not critical:
        target = min(target, DAILY_SALARY * 0.7 * supply_factor)

    # Ensure non-negative and within budget.
    bid = max(0.0, min(my_budget, target))
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

    supply = day_context['supply']
    day = day_context['day']

    # Alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # If no opponents, bid modestly
    if not alive_opps:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.4))

    # Extract yesterday bids for immediate reaction
    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Supply pressure: higher supply means less need to overbid; lower supply means more competition.
    # Normalize supply into [0,1]
    try:
        norm = (float(supply) - float(MIN_SUPPLY)) / (float(MAX_SUPPLY) - float(MIN_SUPPLY))
    except Exception:
        norm = 0.5
    if norm < 0.0:
        norm = 0.0
    if norm > 1.0:
        norm = 1.0

    # Base bid target: aim around a fraction of salary, adjusted by supply and yesterday pressure.
    # Aggression increases if yesterday saw very high bids (Cindy/Eric pattern).
    if highest_prev_bid >= DAILY_SALARY * 1.55:  # ~140+ given salary 90
        # They are spending to guarantee survival; we must not be too low.
        base = DAILY_SALARY * (0.70 if my_status['hp'] > 3 else 0.95)
    elif highest_prev_bid >= DAILY_SALARY * 1.10:
        base = DAILY_SALARY * (0.60 if my_status['hp'] > 3 else 0.85)
    else:
        base = DAILY_SALARY * 0.55

    # Adjust for supply: when supply is low, increase bid; when high, decrease bid.
    # norm=0 => low supply => +15%; norm=1 => high supply => -15%
    supply_adjust = 1.0 + (0.5 - norm) * 0.30
    base *= supply_adjust

    # If I'm close to running out of water days, go higher.
    no_water_days = my_status.get('no_water_days', 0)
    if no_water_days >= 2:
        base *= 1.15

    # Ensure we don't bid more than budget.
    bid = min(float(my_status['budget']), float(base))

    # Hard floor/ceiling to avoid extreme behavior.
    # If hp is low, don't go too low.
    if my_status['hp'] <= 2:
        bid = max(bid, min(float(my_status['budget']), DAILY_SALARY * 0.85))
    else:
        bid = max(0.0, bid)

    return bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    # If no opponents alive, conserve.
    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace to infer aggressiveness.
    prev_bids = []
    for oid, o in alive:
        prev = o.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                prev_bids.append(float(bid))
            except Exception:
                pass

    # Identify if someone is a known high spender (likely Cindy from trace patterns).
    high_spender = False
    if prev_bids:
        max_prev = max(prev_bids)
        if max_prev >= 0.95 * 150.0:
            high_spender = True

    # Decide urgency based on hp/no_water_days.
    # If we're in danger, bid more to secure water.
    danger = (hp <= 2.0) or (no_water_days >= 2) or (hp <= 3.0 and no_water_days >= 1)

    # Supply pressure: lower supply means higher chance of contest; raise bid slightly.
    # Map supply in [15,25] to a multiplier in [1.15, 0.95].
    if MAX_SUPPLY > MIN_SUPPLY:
        t = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        t = 0.5
    t = max(0.0, min(1.0, float(t)))
    supply_mult = 1.15 - 0.20 * t

    # Estimate how much to bid relative to others.
    # Since Cindy appears to bid extremely high to survive, we avoid mirroring her max.
    # Instead, target winning against low/mid bidders: around 0.6-0.75 of DAILY_SALARY when safe,
    # and 0.85-0.95 when in danger.
    if danger:
        base = DAILY_SALARY * 0.9
    else:
        base = DAILY_SALARY * 0.65

    # If there is a very high spender, slightly reduce to avoid wasting budget.
    if high_spender:
        base *= 0.92

    bid = base * supply_mult

    # Budget cap and non-negative.
    bid = max(0.0, min(budget, bid))

    # If budget is tiny, still bid what we can.
    if bid <= 0.0 and budget > 0.0:
        bid = min(budget, DAILY_SALARY * 0.2)

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

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = [o for o in opponents_status.values() if bool(o.get('alive', False))]
    if not alive_opponents:
        # If no opponents, bid enough to guarantee allocation.
        return min(budget, DAILY_SALARY * 0.4)

    # Extract yesterday bids from previous_trace.
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_prev_bid = 0.0
    if len(prev_bids) >= 2:
        sorted_bids = sorted(prev_bids, reverse=True)
        second_prev_bid = sorted_bids[1]

    # Estimate how competitive the field is.
    # If someone bid very high yesterday (near/above salary), others may be bidding aggressively too.
    aggression = 0.0
    if highest_prev_bid >= DAILY_SALARY * 1.0:
        aggression = 1.0
    elif highest_prev_bid >= DAILY_SALARY * 0.7:
        aggression = 0.7
    elif highest_prev_bid >= DAILY_SALARY * 0.4:
        aggression = 0.4

    # If my hp is low or I already have no-water streak, increase bid.
    # Otherwise, keep it moderate to avoid burning budget.
    urgent = 0.0
    if hp <= 2.0:
        urgent = 1.0
    elif hp <= 4.0:
        urgent = 0.6
    if no_water_days >= 2:
        urgent = max(urgent, 0.8)

    # Supply pressure: lower supply means higher chance of losing if we bid too low.
    supply_pressure = 0.0
    if supply <= float(MIN_SUPPLY):
        supply_pressure = 1.0
    elif supply <= float(MIN_SUPPLY) + 2.0:
        supply_pressure = 0.7
    elif supply <= float(MIN_SUPPLY) + 5.0:
        supply_pressure = 0.4

    # Base bid target: aim to slightly exceed a typical competing bid.
    # Use second-highest as a proxy for the likely clearing price.
    target = second_prev_bid + 2.0

    # If aggression is high, raise target; if low, keep target closer to second-highest.
    target *= (1.0 + 0.25 * aggression)

    # Urgency and supply pressure push bid up.
    target *= (1.0 + 0.35 * urgent + 0.25 * supply_pressure)

    # Clamp target to sensible bounds relative to my budget and salary.
    # Keep moderate by default; only go high when urgent.
    default_cap = DAILY_SALARY * (0.65 if urgent < 0.6 else 0.95)
    cap = min(budget, default_cap)

    # Ensure we bid at least a minimal amount if budget allows.
    floor = 0.0
    if budget > 0:
        floor = min(budget, DAILY_SALARY * (0.25 if urgent < 0.6 else 0.55))

    bid = min(cap, max(floor, target))

    # If target is still too low and supply is tight, add a small bump.
    if supply_pressure >= 0.7 and bid < DAILY_SALARY * 0.6:
        bid = min(budget, DAILY_SALARY * 0.75)

    # Final safety: bid cannot exceed budget.
    if bid > budget:
        bid = budget
    if bid < 0:
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

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', None)

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    if not alive_opponents:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how many water units are effectively contested.
    # Use explicit int() to avoid float index issues.
    # If supply is low, being too conservative risks losing water.
    supply_units = int(supply // float(WATER_REQ)) if WATER_REQ > 0 else 0
    if supply_units < 1:
        supply_units = 1

    # Base aggressiveness: conservative unless pressure is high or my HP is low.
    pressure = 0.0
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        pressure = 1.0
    elif highest_prev_bid >= DAILY_SALARY * 0.65:
        pressure = 0.6
    else:
        pressure = 0.3

    # If I'm in danger, bid more.
    danger = 0.0
    if hp <= 2:
        danger = 1.0
    elif hp <= 4:
        danger = 0.7
    elif no_water_days >= 2:
        danger = 0.5
    else:
        danger = 0.2

    # Combine: target bid around a fraction of salary plus a small bump under pressure.
    # Keep under budget.
    target = DAILY_SALARY * (0.35 + 0.25 * pressure + 0.35 * danger)

    # If supply is relatively abundant, we can underbid more.
    if supply >= (MIN_SUPPLY + MAX_SUPPLY) / 2.0:
        target *= 0.9

    # If supply is tight, bid closer to salary.
    if supply <= MIN_SUPPLY + 1.0:
        target *= 1.1

    # If yesterday max bid was extremely high, slightly increase to avoid losing the water war.
    if highest_prev_bid >= DAILY_SALARY * 0.95:
        target = max(target, highest_prev_bid * 0.7)

    # Final cap by budget.
    bid = max(0.0, min(budget, target))

    # Ensure we don't bid trivially low when HP is critical.
    if hp <= 1:
        bid = max(bid, min(budget, DAILY_SALARY * 0.85))

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

    # If no budget, bid 0
    if my_status['budget'] <= 0:
        return 0.0

    # Consider only alive opponents
    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive.append((opp_id, opp))

    if not alive:
        # No competition: bid minimal to get water if possible
        return min(my_status['budget'], DAILY_SALARY * 0.2)

    # Extract yesterday bids from previous_trace (immediate reaction)
    prev_bids = []
    prev_by_id = {}
    for opp_id, opp in alive:
        prev = opp.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                b_val = float(b)
            except Exception:
                b_val = None
            if b_val is not None:
                prev_bids.append(b_val)
                prev_by_id[opp_id] = b_val

    # Determine pressure level from yesterday
    pressure = 0.0
    if prev_bids:
        pressure = max(prev_bids)

    # If Cindy exists and had high yesterday bid, treat as main pressure
    main_pressure = 0.0
    if 'Cindy' in opponents_status and opponents_status['Cindy'].get('alive', False):
        prev = opponents_status['Cindy'].get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                main_pressure = float(b)
            except Exception:
                main_pressure = 0.0

    # Supply-based aggressiveness: when supply is higher, we can bid less and still likely win.
    # Normalize supply in [MIN_SUPPLY, MAX_SUPPLY]
    if supply <= MIN_SUPPLY:
        supply_factor = 1.0
    elif supply >= MAX_SUPPLY:
        supply_factor = 0.6
    else:
        supply_factor = 1.0 - 0.4 * ((supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY))

    # HP urgency
    hp = float(my_status['hp'])
    no_water_days = int(my_status['no_water_days'])

    urgency = 0.0
    if hp <= 1.5:
        urgency = 1.0
    elif hp <= 3.0:
        urgency = 0.75
    elif hp <= 5.0:
        urgency = 0.5
    else:
        urgency = 0.25

    if no_water_days >= 2:
        urgency = max(urgency, 0.8)

    # Target bid logic:
    # - If Cindy bid was very high yesterday, bid moderately high to contest.
    # - Otherwise, bid around a fraction of DAILY_SALARY, scaled by urgency and supply.
    base = DAILY_SALARY * 0.45

    # Contest multiplier based on yesterday pressure
    contest = 1.0
    if main_pressure >= DAILY_SALARY * 1.4:
        contest = 1.25
    elif pressure >= DAILY_SALARY * 1.1:
        contest = 1.15
    elif pressure >= DAILY_SALARY * 0.8:
        contest = 1.05

    bid = base * contest * supply_factor * (0.7 + 0.6 * urgency)

    # If we are in critical HP, push higher but still cap by budget
    if urgency >= 0.8:
        bid = max(bid, DAILY_SALARY * 0.7)

    # Cap bid: never exceed budget
    bid = float(min(my_status['budget'], bid))

    # Add small day-based jitter to avoid ties (deterministic)
    jitter = ((day % 7) - 3) * 0.8
    bid = max(0.0, bid + jitter)

    return float(bid)
"""
