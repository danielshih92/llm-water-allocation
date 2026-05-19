# ============================================================
# Experiment: exp_009
# Agent: Bob
# Source: exp_009
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

    hp = my_status.get('hp', 0)
    budget = my_status.get('budget', 0)
    no_water_days = my_status.get('no_water_days', 0)

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    # If no opponents, bid to cover requirement while staying budget-safe.
    if not alive_opponents:
        target = WATER_REQ
        return int(min(budget, max(0, target)))

    # Extract yesterday bids from traces.
    prev_bids = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid', 0.0)))
            except Exception:
                pass

    # Baseline bid depends on our urgency.
    urgency = 0
    if no_water_days is not None:
        try:
            urgency = int(no_water_days)
        except Exception:
            urgency = 0

    # If we're very low HP or have many no-water days, bid harder.
    if hp is None:
        hp = 0
    try:
        hp = int(hp)
    except Exception:
        hp = 0

    if urgency >= 2 or hp <= 2:
        urgency_multiplier = 0.95
    elif urgency == 1 or hp <= 3:
        urgency_multiplier = 0.75
    else:
        urgency_multiplier = 0.55

    # Opponent aggressiveness from yesterday.
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        lowest_prev_bid = min(prev_bids)

        # If someone bid extremely high yesterday, they likely needed water badly.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # Contest but avoid going as high as them.
            bid = highest_prev_bid * 0.55
            # Ensure we still try to secure at least near requirement.
            bid = max(bid, WATER_REQ * 0.9)
        else:
            # Otherwise, slightly outbid the likely baseline to win cheaply.
            # Use lowest_prev_bid as proxy for their willingness to pay.
            bid = max(WATER_REQ * 0.85, lowest_prev_bid + 1.5)
            # Also cap by a fraction of salary scaled by urgency.
            bid = min(bid, DAILY_SALARY * urgency_multiplier)
    else:
        # No reliable trace bids; bid around requirement with urgency.
        bid = max(WATER_REQ * 0.85, DAILY_SALARY * urgency_multiplier)

    # Supply-aware adjustment: if supply is high, we can bid less.
    try:
        supply_f = float(supply)
    except Exception:
        supply_f = (MIN_SUPPLY + MAX_SUPPLY) / 2.0

    if supply_f >= MAX_SUPPLY:
        bid *= 0.85
    elif supply_f <= MIN_SUPPLY:
        bid *= 1.05

    # Final safety: cannot exceed budget and keep non-negative integer.
    if budget is None:
        budget = 0
    try:
        budget = float(budget)
    except Exception:
        budget = 0

    bid = max(0.0, min(float(budget), float(bid)))

    return int(bid)
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

    # Identify alive opponents (only use current provided alive flag)
    alive_opps = []
    for k, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # If no opponents, take the safe minimum to meet requirement
    if not alive_opps:
        return int(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace for immediate reaction
    prev_bids = []
    for o in alive_opps:
        pt = o.get('previous_trace', {})
        if isinstance(pt, dict):
            b = pt.get('bid', None)
            if b is not None:
                try:
                    prev_bids.append(float(b))
                except Exception:
                    pass

    # Estimate opponent pressure from yesterday
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    # Supply pressure: when supply is low, competition for the 9-water requirement is tighter
    # Approximate how many full requirements exist
    reqs = supply / float(WATER_REQ)
    scarcity = 0.0
    if reqs <= 1.2:
        scarcity = 1.0
    elif reqs <= 1.6:
        scarcity = 0.6
    elif reqs <= 2.2:
        scarcity = 0.3
    else:
        scarcity = 0.1

    # Our risk management
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # If we're already in danger, bid harder to avoid further no-water days
    if hp <= 2 or no_water_days >= 2:
        base = DAILY_SALARY * (0.85 + 0.1 * scarcity)
    elif hp <= 4:
        base = DAILY_SALARY * (0.65 + 0.15 * scarcity)
    else:
        base = DAILY_SALARY * (0.5 + 0.2 * scarcity)

    # If yesterday's highest bids were extreme, we slightly overbid but still cap to preserve budget
    # (Cindy/Eric were very high; Alex/David died, so avoid matching the very top unless needed.)
    if highest_prev_bid >= DAILY_SALARY * 1.4:
        # High pressure environment: move toward the 60-75% of top pressure
        opponent_anchor = min(highest_prev_bid * 0.62, DAILY_SALARY * 0.95)
        bid = max(base, opponent_anchor)
    elif highest_prev_bid >= DAILY_SALARY * 0.9:
        bid = max(base, avg_prev_bid * 0.85)
    else:
        # Moderate environment: aim above average a bit
        bid = max(base, avg_prev_bid * 0.75)

    # Budget and day scaling: earlier days bid a bit more; later days conserve
    day_factor = 1.0
    if day <= 3:
        day_factor = 1.05
    elif day >= 8:
        day_factor = 0.9

    bid = bid * day_factor

    # Final cap: never exceed what we can afford
    bid = min(bid, budget)

    # Ensure non-negative and integer
    if bid < 0:
        bid = 0

    return int(bid)
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

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Inspect yesterday bids for immediate reaction
    yesterday_bids = []
    yesterday_hp = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                b = float(prev.get('bid'))
            except Exception:
                b = None
            if b is not None:
                yesterday_bids.append(b)
                yesterday_hp.append(float(prev.get('hp_after', o.get('hp', 0))))

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = sum(yesterday_bids) / float(len(yesterday_bids)) if yesterday_bids else 0.0

    # Determine how many water units are likely available today
    # (Used only to scale conservatively)
    expected_units = int(supply / float(WATER_REQ)) if WATER_REQ > 0 else 0
    # If supply is enough for at least one full unit, we can bid less aggressively.

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status.get('no_water_days', 0))

    # Aggression control:
    # If someone bid extremely high yesterday, assume they will continue; bid just enough to compete.
    # Cindy showed very high bids, so we avoid matching her ceiling but stay competitive.
    if highest_prev_bid >= DAILY_SALARY * 1.1:
        # Competitive but budget-aware
        if hp <= 2 or no_water_days >= 2:
            bid = DAILY_SALARY * 0.9
        else:
            bid = max(DAILY_SALARY * 0.55, min(DAILY_SALARY * 0.75, highest_prev_bid * 0.55))
    elif highest_prev_bid >= DAILY_SALARY * 0.6:
        if hp <= 2 or no_water_days >= 2:
            bid = DAILY_SALARY * 0.75
        else:
            bid = max(DAILY_SALARY * 0.45, highest_prev_bid * 0.5)
    else:
        # Low pressure yesterday: bid around a moderate baseline
        if hp <= 2:
            bid = DAILY_SALARY * 0.85
        elif no_water_days >= 2:
            bid = DAILY_SALARY * 0.7
        else:
            bid = DAILY_SALARY * 0.55

    # Scale down if supply likely supports multiple units; scale up slightly if supply is tight.
    if expected_units <= 0:
        bid = min(bid * 0.9, DAILY_SALARY * 0.8)
    elif expected_units == 1:
        bid = min(bid * 1.0, DAILY_SALARY * 0.85)
    else:
        bid = min(bid * 0.85, DAILY_SALARY * 0.75)

    # Ensure we don't overdraw budget
    bid = min(bid, budget)

    # If budget is too low, bid what we can
    if bid < 0:
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 1)

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for k, v in opponents_status.items():
        if v is not None and v.get('alive', False):
            alive_opps.append((k, v))

    if not alive_opps:
        return float(min(my_budget, DAILY_SALARY * 0.4))

    # Immediate reaction to yesterday's bids
    yesterday_bids = []
    yesterday_hp_after = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict) and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass
        if isinstance(prev, dict) and prev.get('hp_after') is not None:
            try:
                yesterday_hp_after.append(int(prev['hp_after']))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = (sum(yesterday_bids) / len(yesterday_bids)) if yesterday_bids else 0.0

    # Estimate how many water units are likely available; use as a pressure proxy
    # (We cannot see opponents' current bids, so we bias toward securing at least one unit.)
    expected_units = int(supply / float(WATER_REQ)) if WATER_REQ > 0 else 1
    if expected_units < 1:
        expected_units = 1

    # Baseline bid: moderate, tuned by our hp and no-water streak
    # If our hp is low or we already missed water, bid higher.
    if my_hp <= 2 or my_no_water_days >= 2:
        base = DAILY_SALARY * 0.85
    elif my_hp <= 4 or my_no_water_days == 1:
        base = DAILY_SALARY * 0.65
    else:
        base = DAILY_SALARY * 0.5

    # If yesterday's max bid was very high, others likely compete strongly today too.
    # Raise bid to be competitive but avoid overspending.
    if highest_prev_bid >= DAILY_SALARY * 1.2:
        base = max(base, DAILY_SALARY * 0.75)
    elif highest_prev_bid >= DAILY_SALARY * 0.9:
        base = max(base, DAILY_SALARY * 0.6)

    # If average yesterday bid was high, slightly increase.
    if avg_prev_bid >= DAILY_SALARY * 0.95:
        base = max(base, DAILY_SALARY * 0.62)

    # Budget guardrails: never exceed budget.
    # Also, if supply is low (near MIN_SUPPLY), competition is higher; slightly increase.
    if supply <= float(MIN_SUPPLY) + 0.5:
        base *= 1.06

    # Convert to final bid with a small day-based wobble to avoid ties.
    wobble = 1.0 + (0.01 * ((int(day) % 5) - 2))
    bid = base * wobble

    # Ensure bid is within reasonable bounds relative to budget.
    if my_budget <= 0:
        return 0.0

    bid = float(min(my_budget, bid))

    # If budget is too low, still try to bid something proportional to survival need.
    if bid < 1e-6:
        if my_hp <= 2:
            return float(min(my_budget, DAILY_SALARY * 0.9))
        return float(min(my_budget, DAILY_SALARY * 0.4))

    return bid
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', True) and o.get('hp', 0) > 0:
            alive_opps.append((oid, o))

    if not alive_opps:
        return float(min(my_status.get('budget', 0.0), DAILY_SALARY * 0.4))

    yesterday_bids = []
    yesterday_pressures = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                yesterday_bids.append(float(bid))
            except Exception:
                pass
        # Use yesterday hp_after as a proxy for how costly their last bids were
        hp_after = prev.get('hp_after', None)
        if hp_after is not None:
            try:
                yesterday_pressures.append((float(hp_after), float(bid) if bid is not None else None))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Pressure thresholds tuned to the observed meta-round (bids ~50-160+)
    high_pressure = highest_prev_bid >= DAILY_SALARY * 1.2  # >=108
    medium_pressure = (highest_prev_bid >= DAILY_SALARY * 0.7) and (highest_prev_bid < DAILY_SALARY * 1.2)  # 63-107

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Risk-aware base bid: if we're near critical hp or have accumulated no-water days, bid more.
    if my_hp <= 2.0 or no_water_days >= 2:
        base = DAILY_SALARY * (0.85 if high_pressure else 0.75)
    elif my_hp <= 4.0:
        base = DAILY_SALARY * (0.65 if medium_pressure else 0.55)
    else:
        base = DAILY_SALARY * (0.55 if high_pressure else 0.45)

    # If others were bidding very high yesterday, try to slightly undercut rather than match max.
    # Use a small increment over a fraction of the max to win ties more often.
    if high_pressure:
        target = max(base, highest_prev_bid * 0.92)
    elif medium_pressure:
        target = max(base, highest_prev_bid * 0.75)
    else:
        target = max(base, DAILY_SALARY * 0.5)

    # Supply-aware adjustment: if supply is tight, increase bid; if ample (within given range), decrease slightly.
    # supply is in [15,25]
    # Use int indices explicitly where needed (no lists used here, but keep safe style).
    if supply <= float(WATER_REQ):
        target *= 1.15
    elif supply <= 18.0:
        target *= 1.05
    elif supply >= 23.0:
        target *= 0.95

    # Safety cap: never exceed budget; also avoid spending too aggressively late in episode.
    # Episode length is 10 days; scale down after day 6.
    if isinstance(day, (int, float)):
        d = int(day)
    else:
        d = 0

    if d >= 7:
        target *= 0.85
    elif d >= 4:
        target *= 0.95

    bid = float(min(my_budget, target))

    # Ensure non-negative and at least a minimal bid if budget allows.
    if bid < 0.0:
        bid = 0.0
    if bid == 0.0 and my_budget > 0.0:
        bid = float(min(my_budget, DAILY_SALARY * 0.2))

    return bid
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

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    if not alive_opponents:
        return float(min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday bids to infer pressure
    yesterday_bids = []
    yesterday_bids_by_id = {}
    for agent_id, opp in opponents_status.items():
        if not opp.get('alive', False):
            continue
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                b = float(bid)
            except Exception:
                b = None
            if b is not None:
                yesterday_bids.append(b)
                yesterday_bids_by_id[agent_id] = b

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = 0.0
    if len(yesterday_bids) >= 2:
        sorted_bids = sorted(yesterday_bids, reverse=True)
        second_prev_bid = float(sorted_bids[1])

    # Supply pressure: with supply near 15, water is scarce so expect higher bids
    # With supply near 25, competition is less intense.
    supply_ratio = (supply - 15.0) / (25.0 - 15.0) if 25.0 != 15.0 else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Determine aggressiveness based on my HP / no-water streak
    if my_hp <= 2 or my_no_water_days >= 2:
        urgency = 1.0
    elif my_hp <= 4 or my_no_water_days >= 1:
        urgency = 0.75
    else:
        urgency = 0.5

    # Target bid: try to slightly beat the likely leader if they were aggressive yesterday.
    # If highest_prev_bid was very high, we must bid closer to it; otherwise bid enough to be competitive.
    leader_pressure = 0.0
    if highest_prev_bid > 0.0:
        leader_pressure = min(1.0, highest_prev_bid / (DAILY_SALARY * 1.2))

    # Compute base target
    # - In scarce supply (low supply_ratio), increase bid.
    # - In abundant supply (high supply_ratio), decrease bid.
    scarcity_factor = 1.1 - 0.2 * supply_ratio

    # If yesterday leader bid was high, we bid near it; else we bid around midrange.
    if highest_prev_bid >= DAILY_SALARY * 0.8:
        target = (highest_prev_bid * 0.92 + second_prev_bid * 0.08) * scarcity_factor
    else:
        target = (DAILY_SALARY * (0.45 + 0.25 * leader_pressure)) * scarcity_factor

    # Apply urgency
    target = target * (0.75 + 0.5 * urgency)

    # Keep within budget and avoid irrational overbids
    max_reasonable = DAILY_SALARY * (1.15 if my_hp <= 2 else 0.95)
    target = min(target, max_reasonable)

    # Ensure we don't exceed budget
    bid = float(min(my_budget, target))

    # If budget is tiny, still bid something to avoid wasting opportunity
    if bid <= 0.0:
        return 0.0

    # Add a small deterministic nudge to break ties (avoid randomness)
    # Use day parity to slightly vary by a couple dollars.
    nudge = 2.0 if (day % 2 == 0) else 1.0
    bid = float(min(my_budget, bid + nudge))

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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps or budget <= 0:
        return 0.0

    # Read yesterday bids from traces for immediate reaction
    prev_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate competitive level from yesterday
    if prev_bids:
        top_bid = max(prev_bids)
        second_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else top_bid
    else:
        top_bid = 0.0
        second_bid = 0.0

    # My urgency: if low hp or already missing water, increase bid
    urgency = 0.0
    if hp <= 2.0:
        urgency += 1.0
    if hp <= 4.0:
        urgency += 0.6
    if no_water_days >= 1:
        urgency += 0.7
    if no_water_days >= 2:
        urgency += 0.9

    # Supply factor: in medium, supply likely limits winners; bid more when supply is lower in range
    # Normalize supply within [15,25]
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_norm = 0.5
    # Lower supply => higher need => higher bid
    supply_need = 1.0 - min(1.0, max(0.0, supply_norm))

    # Baseline: aim around 0.55-0.75 of daily salary depending on urgency
    base = DAILY_SALARY * (0.55 + 0.20 * supply_need + 0.15 * min(1.0, urgency))

    # If Cindy-like behavior dominates (very high top bid), don't chase exactly; bid near second+small
    # to avoid overpaying while still competing.
    # Use ratio to detect aggressive opponents.
    aggressive = 1.0 if (top_bid >= DAILY_SALARY * 1.5) else 0.0

    if aggressive > 0.5 and second_bid > 0:
        target = min(budget, max(base, second_bid + 2.0))
    else:
        # Otherwise, slightly undercut top to conserve budget
        if top_bid > 0:
            target = min(budget, max(base, min(top_bid - 1.0, base + 25.0)))
        else:
            target = min(budget, base)

    # Hard caps to avoid bankruptcy
    # If hp is healthy, don't spend too much; if hp is critical, allow up to 0.95 salary.
    if hp >= 7.0 and no_water_days == 0:
        cap = DAILY_SALARY * 0.75
    elif hp >= 5.0:
        cap = DAILY_SALARY * 0.85
    else:
        cap = DAILY_SALARY * 0.95

    bid = min(target, cap, budget)

    # Ensure non-negative float
    if bid < 0:
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

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # If no opponents, bid conservatively.
    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday bids to infer aggressiveness.
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate aggressiveness and likely competition.
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Target bid: aim to outbid the main threat (Cindy-like) only when supply is favorable.
    # Supply factor: when supply is high (near 25), more water is available so we can afford higher bids.
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_factor = 0.5
    if supply_factor < 0.0:
        supply_factor = 0.0
    if supply_factor > 1.0:
        supply_factor = 1.0

    # Base aggressiveness from yesterday's highest bid.
    # Cindy survived with low hp, so she likely bids to secure enough water.
    # We match her zone but with a slight discount to avoid overpaying.
    if highest_prev_bid >= DAILY_SALARY * 1.6:
        # Very aggressive field.
        target = highest_prev_bid * (0.92 - 0.15 * (1.0 - supply_factor))
    elif highest_prev_bid >= DAILY_SALARY * 1.2:
        # Moderate competition.
        target = highest_prev_bid * (0.85 - 0.10 * (1.0 - supply_factor))
    else:
        # Mostly conservative.
        target = max(DAILY_SALARY * 0.45, highest_prev_bid + 5.0)

    # HP-based escalation: if we are low, spend more to avoid running out of water days.
    no_water_days = int(my_status.get('no_water_days', 0))
    if my_hp <= 2 or no_water_days >= 2:
        target *= 1.25
    elif my_hp <= 3:
        target *= 1.10

    # Ensure we do not bid more than we can afford.
    # Also keep a floor so we don't get fully outcompeted when supply is high.
    min_bid_floor = DAILY_SALARY * (0.35 + 0.25 * supply_factor)
    if target < min_bid_floor:
        target = min_bid_floor

    # Final cap.
    bid = max(0.0, min(my_budget, float(target)))
    return bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    MAX_BID_FRAC_SAFE = 0.75
    MAX_BID_FRAC_LOWHP = 0.98

    supply = day_context['supply']
    day = day_context['day']

    # Alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # If no opponents, just spend enough to meet requirement
    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.45)

    # Read yesterday bids from previous_trace
    yesterday_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(float(prev.get('bid', 0.0)))

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Determine how many units are even plausibly available vs requirement
    # (Used only to scale aggressiveness.)
    # Ensure integer indices if any list used; none here.
    units_possible = supply / float(WATER_REQ)

    # Base bid target: aim to be competitive but not wasteful.
    # If others were bidding high yesterday, increase.
    high_pressure = highest_prev_bid >= (0.8 * DAILY_SALARY)

    # HP-based ramp
    hp = my_status.get('hp', 0)
    budget = my_status.get('budget', 0.0)

    # If supply is tight (near min), bid more to avoid losing.
    tight_supply = supply <= (MIN_SUPPLY + 0.5)

    if hp <= 2:
        frac = MAX_BID_FRAC_LOWHP
    elif hp <= 4:
        frac = 0.85
    else:
        frac = MAX_BID_FRAC_SAFE

    # Adjust for observed opponent pressure
    if high_pressure:
        frac = min(0.99, frac + 0.12)
    elif tight_supply:
        frac = min(0.95, frac + 0.08)
    else:
        frac = max(0.45, frac - 0.05)

    # Convert fraction to bid, but keep within budget.
    bid = budget * frac

    # Additional steering: if yesterday highest bid was modest, try to slightly undercut.
    # This helps when opponents are not spending aggressively.
    if not high_pressure and highest_prev_bid > 0:
        bid = min(bid, highest_prev_bid + 0.15 * DAILY_SALARY)

    # Final cap: never exceed budget
    if bid > budget:
        bid = budget

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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Alive opponents
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    # If no one else is alive, conserve budget
    if not alive:
        return float(min(my_status['budget'], DAILY_SALARY * 0.35))

    # Estimate how many water units are likely needed to avoid starvation for us
    # (Assumption: water allocation scales with bid; we target a bid that tends to win a share.)
    # Use supply to set aggressiveness: higher supply -> lower bid needed.
    supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_factor = max(0.0, min(1.0, supply_factor))

    # Read yesterday bids to detect over-aggression
    yesterday_bids = []
    for _, o in alive:
        prev = o.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    median_prev_bid = 0.0
    if yesterday_bids:
        s = sorted(yesterday_bids)
        median_prev_bid = s[len(s)//2]

    # Our urgency
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Base bid target: mid-range to compete without burning budget
    # If supply is low, bid higher; if supply is high, bid lower.
    base = DAILY_SALARY * (0.48 - 0.10 * supply_factor)  # ~0.48 at low supply, ~0.38 at high

    # React to opponent overbidding: if someone bid extremely high yesterday (like Alex did),
    # we can undercut slightly because that player likely wasted budget.
    # If highest_prev_bid is very high compared to our salary, reduce.
    if highest_prev_bid >= DAILY_SALARY * 1.0:
        base *= 0.90
    elif highest_prev_bid >= DAILY_SALARY * 0.75:
        base *= 0.98

    # If we are in danger, increase bid to secure water
    if hp <= 2.5 or no_water_days >= 2:
        base *= 1.25
    elif hp <= 4.0:
        base *= 1.10

    # If others were generally bidding low, we can bid closer to median to ensure share
    if median_prev_bid > 0:
        base = 0.65 * base + 0.35 * float(median_prev_bid)

    # Cap bid by remaining budget and keep within reasonable fraction
    # Also avoid bidding above what would likely be wasteful given our requirement.
    cap = min(budget, DAILY_SALARY * 0.95)
    bid = float(min(cap, max(0.0, base)))

    # If we have very low budget, bid just enough to try to survive
    if budget <= DAILY_SALARY * 0.25:
        bid = float(min(budget, DAILY_SALARY * 0.6))

    # Ensure non-negative
    if bid < 0.0:
        bid = 0.0

    return bid
"""
