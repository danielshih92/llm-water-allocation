# ============================================================
# Experiment: exp_117
# Agent: Bob
# Source: exp_117
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday bids from previous_trace only (immediate reaction)
    prev_bids = []
    prev_hp_after = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid')))
            except Exception:
                pass
        if prev and prev.get('hp_after') is not None:
            try:
                prev_hp_after.append(float(prev.get('hp_after')))
            except Exception:
                pass

    # Estimate how contested the day likely is
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = (sum(prev_bids) / float(len(prev_bids))) if prev_bids else 0.0

    # Base aggressiveness: if opponents previously bid high, we must match/beat to secure water.
    # Thresholds tuned for medium scenario where supply is 15-25.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Opponents were under heavy pressure; secure water with a strong bid.
        if hp > 3:
            target = DAILY_SALARY * 0.35
        else:
            target = DAILY_SALARY * 0.9
    elif highest_prev_bid >= DAILY_SALARY * 0.55:
        # Moderate contention; bid enough to be competitive.
        target = max(DAILY_SALARY * 0.45, highest_prev_bid + 1.0)
    else:
        # Low contention; conserve budget.
        target = max(DAILY_SALARY * 0.3, avg_prev_bid * 0.8)

    # If our hp is low, increase bid to avoid cascading no-water days.
    if hp <= 2.0:
        target = max(target, DAILY_SALARY * 0.85)
    elif hp <= 3.0:
        target = max(target, DAILY_SALARY * 0.6)

    # Supply-aware adjustment: when supply is scarce, raise bids.
    # Use integer indexing safely for any derived arrays.
    # Compute how many full WATER_REQ chunks supply can cover (approx).
    chunks = int(supply / float(WATER_REQ)) if WATER_REQ > 0 else 0
    if chunks <= 1:
        target *= 1.15
    elif chunks >= 2:
        target *= 0.95

    # Final clamp by budget and a reasonable cap.
    # Since bids are effectively payments, never exceed budget.
    bid = min(budget, target)

    # Ensure non-negative bid.
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if budget <= 0:
        return 0.0

    # Extract yesterday bids from immediate previous_trace only.
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # Baseline aggressiveness from supply pressure.
    # If supply is low, competition for the first WATER_REQ units is higher.
    if supply <= float(WATER_REQ):
        supply_pressure = 1.0
    elif supply <= (float(WATER_REQ) + 3.0):
        supply_pressure = 0.85
    elif supply <= 20.0:
        supply_pressure = 0.7
    else:
        supply_pressure = 0.55

    # React to yesterday's highest bid: high-bidder likely continues.
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        avg_prev_bid = sum(prev_bids) / float(len(prev_bids))
    else:
        highest_prev_bid = 0.0
        avg_prev_bid = 0.0

    # If someone bid very low yesterday (like Eric), they likely won't outbid us.
    # If others bid high, we need to match a fraction of that to secure water.
    target = None

    # My urgency: each no-water day reduces survival; if already behind, bid harder.
    urgency = 0.0
    if no_water_days >= 1:
        urgency = 0.25
    if no_water_days >= 2:
        urgency = 0.5
    if hp <= 3:
        urgency = max(urgency, 0.6)

    # Decision bands.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Others were extremely aggressive; bid to avoid being starved.
        target = (0.55 + 0.25 * urgency) * highest_prev_bid
        # Also ensure we don't underbid relative to average.
        target = max(target, (0.65 + 0.15 * urgency) * avg_prev_bid)
    elif highest_prev_bid >= DAILY_SALARY * 0.6:
        target = (0.45 + 0.25 * urgency) * highest_prev_bid
        target = max(target, (0.55 + 0.15 * urgency) * avg_prev_bid)
    else:
        # No strong signal; bid moderately based on supply pressure.
        target = (0.4 + 0.35 * urgency) * DAILY_SALARY * supply_pressure

    # Convert target into a practical cap/floor.
    # We must not exceed budget; also avoid wasting too much early.
    # If supply is high, we can bid lower.
    if supply >= 22.0:
        waste_cap = 0.45 * DAILY_SALARY
    elif supply >= 18.0:
        waste_cap = 0.55 * DAILY_SALARY
    else:
        waste_cap = 0.7 * DAILY_SALARY

    bid = min(budget, min(target, waste_cap))

    # Ensure non-trivial bid when hp is low.
    if hp <= 2.0:
        bid = max(bid, min(budget, 0.85 * DAILY_SALARY))
    elif hp <= 4.0 and supply_pressure >= 0.7:
        bid = max(bid, min(budget, 0.65 * DAILY_SALARY))

    # Final clamp.
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

    # Basic safety
    budget = float(my_status.get('budget', 0.0))
    hp = float(my_status.get('hp', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))
    supply = float(day_context.get('supply', 0.0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Use yesterday's bids only for immediate reaction
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate how many bid units might be needed given supply
    # If supply is low relative to WATER_REQ, we must be more competitive.
    supply_ratio = supply / float(WATER_REQ)  # ~1.67 to ~2.78

    # Target bid level: moderate baseline, increase if supply tight or my hp critical.
    # Also react to whether others were bidding aggressively yesterday.
    tight_supply = supply_ratio < 2.0  # supply < 18

    # Baseline aggressiveness
    if hp <= 2 or no_water_days >= 2:
        baseline = DAILY_SALARY * (0.75 if tight_supply else 0.6)
    elif hp <= 4:
        baseline = DAILY_SALARY * (0.6 if tight_supply else 0.5)
    else:
        baseline = DAILY_SALARY * (0.5 if tight_supply else 0.42)

    # If yesterday's highest bid was very high, others may be competing for water.
    # But avoid matching extreme bids; just nudge above baseline.
    if highest_prev_bid >= DAILY_SALARY * 1.7:  # ~153
        baseline *= 1.15
    elif highest_prev_bid >= DAILY_SALARY * 1.1:  # ~99
        baseline *= 1.07

    # Convert to final bid with budget cap and a small buffer.
    # Keep bid below a fraction of budget to avoid running out.
    max_affordable = max(0.0, min(budget, DAILY_SALARY * 1.0))

    # Add slight increment when supply is very tight
    if supply_ratio < 1.8:
        baseline *= 1.12

    bid = min(max_affordable, baseline)

    # If budget is extremely low, bid just enough to avoid total loss
    if budget <= DAILY_SALARY * 0.25:
        bid = min(budget, DAILY_SALARY * 0.2)

    # Ensure non-negative
    if bid < 0.0:
        bid = 0.0

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

    # Identify alive opponents and their yesterday bid.
    alive = []
    for agent_id, o in opponents_status.items():
        if o.get('alive', False):
            prev = o.get('previous_trace', {}) or {}
            alive.append((agent_id, o, prev.get('bid', None)))

    if not alive:
        # No competition: take what we can afford.
        return float(min(my_status.get('budget', 0.0), DAILY_SALARY * 0.4))

    # Yesterday's bids: use them to infer aggressiveness.
    prev_bids = []
    for _, _, b in alive:
        if b is not None:
            prev_bids.append(float(b))

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))

    # Estimate how many water units are likely available today.
    # Use supply/WATER_REQ as a rough proxy for how many
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
    day = day_context.get('day', 0)

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    # Collect alive opponents and their yesterday bids
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        # If alone, bid to ensure survival with minimal spend
        target = DAILY_SALARY * 0.35
        return max(0.0, min(my_budget, target))

    yesterday_bids = []
    yesterday_hp_after = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass
        hp_after = prev.get('hp_after', None)
        if hp_after is not None:
            try:
                yesterday_hp_after.append(float(hp_after))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    # If opponents were bidding very high yesterday, we must not underbid too much.
    # Cindy/Eric averaged ~111; treat >=110 as high pressure.
    high_pressure = highest_prev_bid >= 110.0

    # Supply pressure: higher supply reduces urgency; lower supply increases urgency.
    # Map supply into [0,1]
    if MAX_SUPPLY == MIN_SUPPLY:
        supply_factor = 0.5
    else:
        supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
        if supply_factor < 0.0:
            supply_factor = 0.0
        if supply_factor > 1.0:
            supply_factor = 1.0

    # Base bid level: moderate around 0.6*salary when supply is medium.
    # Adjust upward if high pressure or if my hp/no-water-days are critical.
    bid = DAILY_SALARY * (0.62 + 0.10 * supply_factor)

    # Reaction to my health
    if my_hp <= 2.0 or my_no_water_days >= 2:
        bid = DAILY_SALARY * 0.92
    elif my_hp <= 4.0:
        bid = DAILY_SALARY * 0.75
    elif my_hp <= 6.0:
        bid = DAILY_SALARY * 0.66

    # Reaction to opponents' yesterday bids
    if high_pressure:
        # Bid closer to their pressure ceiling but still conservative.
        bid = max(bid, min(DAILY_SALARY * 0.75, highest_prev_bid * 0.95))

    # If my budget is low, cap aggressively but still try to win if critical.
    if my_budget <= DAILY_SALARY * 0.25:
        if my_hp <= 4.0 or my_no_water_days >= 2:
            bid = min(my_budget, DAILY_SALARY * 0.95)
        else:
            bid = min(my_budget, DAILY_SALARY * 0.45)

    # Final clamp
    if my_budget < 0.0:
        my_budget = 0.0
    if bid < 0.0:
        bid = 0.0

    return min(my_budget, bid)
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

    # Alive opponents
    alive_opponents = []
    for oid, o in opponents_status.items():
        try:
            if o.get('alive', False):
                alive_opponents.append((oid, o))
        except Exception:
            continue

    # If no opponents, just bid enough to guarantee water
    if not alive_opponents:
        return float(min(my_status.get('budget', 0.0), DAILY_SALARY * 0.4))

    # Extract yesterday bids from traces
    yesterday_bids = []
    yesterday_hp_after = []
    for oid, o in alive_opponents:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass
        try:
            hp_after = prev.get('hp_after', None)
            if hp_after is not None:
                yesterday_hp_after.append(float(hp_after))
        except Exception:
            pass

    # Base target bid logic
    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Estimate scarcity pressure from supply
    # Higher supply => lower pressure; lower supply => higher pressure
    scarcity = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        scarcity = (float(MAX_SUPPLY) - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    # Compute opponent aggression from yesterday
    if yesterday_bids:
        highest = max(yesterday_bids)
        avg = sum(yesterday_bids) / float(len(yesterday_bids))
        # If someone bid very high yesterday, others likely followed aggressive strategy.
        high_pressure = 1.0 if highest >= DAILY_SALARY * 0.85 else 0.0
    else:
        highest = 0.0
        avg = 0.0
        high_pressure = 0.0

    # If I'm in danger, bid more. Otherwise, bid around a fraction of salary.
    danger = 0.0
    if my_hp <= 2.0:
        danger = 1.0
    elif my_hp <= 4.0:
        danger = 0.6
    else:
        danger = 0.2

    # Mild reaction to others: aim slightly above average when supply is tight.
    # Keep cap to avoid burning budget.
    target = DAILY_SALARY * (0.45 + 0.25 * scarcity + 0.15 * danger + 0.10 * high_pressure)

    # If yesterday bids suggest aggressive competition, nudge target upward but not to max.
    if yesterday_bids:
        # Use avg as anchor; bid a bit above avg when supply tight.
        anchor = avg * (0.85 + 0.15 * scarcity)
        target = max(target, anchor + (2.0 + 3.0 * scarcity))

        # If highest was extremely high, avoid copying fully; still stay moderate.
        if highest > DAILY_SALARY * 1.0:
            target = min(target, DAILY_SALARY * 0.85)

    # If I've already accumulated no-water days, increase bidding.
    if no_water_days >= 2:
        target *= (1.0 + 0.25)

    # Final bid constrained by budget and reasonable upper bound.
    # Add small buffer to secure water in simultaneous bidding.
    upper = min(my_budget, DAILY_SALARY * 0.95)
    lower = 0.0
    bid = max(lower, min(float(target), float(upper)))

    # Ensure non-zero bid if we have budget
    if bid <= 0.0 and my_budget > 0.0:
        bid = min(my_budget, DAILY_SALARY * 0.2)

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

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for k, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((k, o))

    # If everyone is dead, conserve.
    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids to infer who is pressuring.
    yesterday_bids = []
    for agent_id, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how much water is likely needed to avoid worsening.
    # If supply is low, we must secure water; if high, we can bid less.
    supply_frac = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_frac = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    if supply_frac < 0.0:
        supply_frac = 0.0
    if supply_frac > 1.0:
        supply_frac = 1.0

    # Base bid: mid level to compete without matching Cindy's extreme bids.
    # Scarce supply -> higher bid; abundant -> lower.
    scarce_factor = 1.0 - supply_frac
    base = DAILY_SALARY * (0.45 + 0.25 * scarce_factor)  # ~40-67

    # Pressure adjustment: if someone already paid very high yesterday, don't chase fully.
    # Instead, bid just enough to beat typical mid bids but below extreme max.
    if highest_prev_bid >= DAILY_SALARY * 1.3:
        # Cindy-like pressure: we cap below her level.
        base = min(base, DAILY_SALARY * 0.75)

    # Urgency from our HP / consecutive no-water days.
    if hp <= 2.0 or no_water_days >= 2:
        urgency = DAILY_SALARY * 0.85
    elif hp <= 4.0 or no_water_days >= 1:
        urgency = DAILY_SALARY * 0.65
    else:
        urgency = DAILY_SALARY * 0.55

    # Choose final bid: take max of base and urgency, but keep under a safety cap.
    # Safety cap prevents catastrophic spending.
    safety_cap = min(budget, DAILY_SALARY * (0.95 if hp <= 2.0 else 0.7))

    bid = max(base, urgency)
    if bid > safety_cap:
        bid = safety_cap

    # Ensure non-negative and not exceeding budget.
    if bid < 0.0:
        bid = 0.0
    if bid > budget:
        bid = budget

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

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace only
    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = 0.0
    if len(yesterday_bids) >= 2:
        s = sorted(yesterday_bids)
        second_prev_bid = s[-2]

    # Determine urgency based on my HP and no_water_days
    # If no_water_days is high, I must secure water.
    urgency = 0
    if hp <= 2.0:
        urgency += 3
    if hp <= 5.0:
        urgency += 2
    if no_water_days >= 2:
        urgency += 2
    if no_water_days >= 3:
        urgency += 3

    # Estimate how many water units are likely needed to last the day
    # (We don't know exact HP update, so we use a conservative approach.)
    # If supply is tight, bidding war is more likely.
    supply_tight = supply <= (MIN_SUPPLY + 1.0)

    # If the top opponent bid was very high yesterday, they likely continued pressure.
    pressure = 0
    if highest_prev_bid >= DAILY_SALARY * 0.9:
        pressure += 3
    elif highest_prev_bid >= DAILY_SALARY * 0.7:
        pressure += 2
    elif highest_prev_bid >= DAILY_SALARY * 0.45:
        pressure += 1

    # Base bid logic
    # - If I'm in danger (urgency high), overtake slightly above the previous top bid.
    # - Otherwise, bid enough to compete but avoid wasting budget.
    if urgency >= 4 or pressure >= 3:
        target = highest_prev_bid + 2.0
    elif urgency >= 2:
        # Mid-high: compete near top but not always exceed.
        target = max(second_prev_bid + 2.0, highest_prev_bid * 0.9)
    else:
        # Low urgency: bid around a fraction of salary; only escalate if supply is tight.
        target = DAILY_SALARY * (0.45 if not supply_tight else 0.6)
        # If there was already a strong bid, nudge upward.
        if highest_prev_bid > 0:
            target = max(target, min(highest_prev_bid * 0.75, DAILY_SALARY * 0.7))

    # Clamp by budget and ensure non-negative
    bid = max(0.0, min(budget, target))

    # If budget is too low, still try to get something proportional to urgency
    if bid <= 0.0 and budget > 0.0:
        bid = min(budget, DAILY_SALARY * (0.2 + 0.1 * urgency))

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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        try:
            if o.get('alive', False):
                alive_opps.append(o)
        except Exception:
            continue

    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from immediate previous_trace only.
    prev_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    prev_bids.append(float(b))
                except Exception:
                    pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    # Determine how many daily units we can cover with one win.
    # In this game, water is consumed; typical clearing is around WATER_REQ.
    # We use supply to infer scarcity: lower supply -> higher clearing price.
    scarcity = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        scarcity = (float(MAX_SUPPLY) - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    # Target bid: slightly under the highest observed pressure to undercut,
    # but ramp up when our hp/no_water_days is critical or supply is scarce.
    critical = (my_hp <= 2) or (my_no_water_days >= 2)

    # Baseline depending on scarcity.
    base = DAILY_SALARY * (0.45 + 0.35 * scarcity)

    # If someone was bidding very high yesterday, we should not be too low,
    # else we risk losing water and dying.
    # Use highest_prev_bid as an upper pressure signal.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        if critical:
            target = base + 0.25 * (highest_prev_bid - base)
        else:
            target = min(highest_prev_bid - 1.0, base + 0.15 * (highest_prev_bid - base))
    else:
        # When overall pressure was moderate, bid closer to average + small premium.
        if critical:
            target = max(base, avg_prev_bid * 0.9)
        else:
            target = min(max(base, avg_prev_bid * 0.75), avg_prev_bid + 10.0)

    # Clamp to budget and non-negative.
    target = max(0.0, float(target))
    bid = min(my_budget, target)

    # If budget is very low, still try to secure enough to survive.
    if my_budget < DAILY_SALARY * 0.2:
        bid = min(my_budget, DAILY_SALARY * 0.25)

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
    day = int(day_context.get('day', 1))

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    # Base safety: if we are in danger, bid hard.
    if my_hp <= 2 or my_no_water_days >= 2:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.95))

    # Read yesterday's bids (immediate reaction only).
    yesterday_bids = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # If nobody else bids, we can bid modestly.
    if not yesterday_bids:
        target = DAILY_SALARY * 0.55
        return max(0.0, min(my_budget, target))

    highest_prev_bid = max(yesterday_bids)

    # Supply pressure: when supply is tight, we need to be more competitive.
    # supply in [15,25], water requirement 9 -> only 1 unit possible near 15.
    tightness = 0.0
    if supply <= float(WATER_REQ) + 6.0:  # around 15
        tightness = 1.0
    elif supply <= float(WATER_REQ) + 9.0:  # around 18
        tightness = 0.7
    elif supply <= 22.0:
        tightness = 0.4
    else:
        tightness = 0.2

    # Undercut strategy: aim slightly above what the strongest bidder paid yesterday,
    # but only if they were truly aggressive; otherwise bid around a moderate level.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # They are spending to secure water; we should not lose the contest.
        # Bid just enough to compete while preserving budget.
        target = max(DAILY_SALARY * (0.35 + 0.25 * tightness), highest_prev_bid * 0.98 + 2.0)
    else:
        # They were not extreme; we can bid lower and still have a chance.
        target = max(DAILY_SALARY * (0.45 + 0.25 * tightness), highest_prev_bid * 0.70 + 5.0)

    # Budget cap and small day-based smoothing.
    # Later days: slightly more aggressive to avoid running out.
    aggress = 1.0 + min(0.15, (day - 1) * 0.01)
    target *= aggress

    # Ensure non-negative and within budget.
    if my_budget <= 0.0:
        return 0.0
    if target > my_budget:
        target = my_budget

    return float(max(0.0, target))
"""
