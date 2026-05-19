# ============================================================
# Experiment: exp_109
# Agent: Bob
# Source: exp_109
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

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    # If no opponents, take minimal safe bid.
    if not alive_opponents:
        bid = min(budget, DAILY_SALARY * 0.4)
        return max(0.0, float(bid))

    # Read yesterday's bids from previous_trace.
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Determine opponent pressure.
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = (sum(prev_bids) / float(len(prev_bids))) if prev_bids else 0.0

    # Base strategy: react to revealed aggressiveness.
    # If opponents were bidding very high yesterday, we must contest water.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Our urgency increases if low hp or already several no-water days.
        urgency = 0.0
        if hp <= 2.5:
            urgency += 0.35
        if no_water_days >= 1:
            urgency += 0.25
        if no_water_days >= 2:
            urgency += 0.25
        # Bid strong but not maximal.
        target = DAILY_SALARY * (0.45 + urgency)
        bid = min(budget, target)
    else:
        # If they were not aggressive, conserve budget and bid around a moderate level.
        # Use their average as a signal.
        target = max(DAILY_SALARY * 0.35, avg_prev_bid * 0.9 + 5.0)
        # Adjust for our health: lower hp => higher bid.
        if hp <= 2.5:
            target = max(target, DAILY_SALARY * 0.75)
        elif hp <= 4.0:
            target = max(target, DAILY_SALARY * 0.55)
        bid = min(budget, target)

    # Supply-aware adjustment: if supply is scarce, slightly increase bid.
    # Normalize supply within [MIN_SUPPLY, MAX_SUPPLY].
    denom = float(MAX_SUPPLY - MIN_SUPPLY) if (MAX_SUPPLY - MIN_SUPPLY) != 0 else 1.0
    scarcity = (float(MAX_SUPPLY) - supply) / denom
    if scarcity > 0.0:
        bid = bid * (1.0 + 0.15 * min(1.0, scarcity))

    # Final clamps.
    bid = float(bid)
    if bid < 0.0:
        bid = 0.0
    if budget <= 0.0:
        return 0.0
    if bid > budget:
        bid = budget

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

    # Alive opponents
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append(o)

    # If no one else is alive, bid conservatively
    if not alive:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids only (immediate reaction)
    yesterday_bids = []
    yesterday_hp_after = []
    for o in alive:
        prev = o.get('previous_trace', {}) or {}
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
                yesterday_hp_after.append(float(prev.get('hp_after', 0)))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = (sum(yesterday_bids) / len(yesterday_bids)) if yesterday_bids else 0.0

    # Supply pressure: higher supply reduces need to overbid
    # Map supply in [15,25] to a factor in [1.1, 0.8]
    if MAX_SUPPLY - MIN_SUPPLY != 0:
        t = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        t = 0.5
    supply_factor = 1.1 - 0.3 * t

    # If I'm in danger, bid aggressively to avoid no-water days
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Estimate how many water units we can reasonably cover if we win/lose.
    # Use hp and no_water_days to decide urgency.
    urgency = 0
    if hp <= 2.0:
        urgency += 2
    if hp <= 5.0:
        urgency += 1
    if no_water_days >= 2:
        urgency += 2
    if no_water_days >= 1:
        urgency += 1

    # Decide target bid based on yesterday's observed pressure.
    # Alex/Eric were bidding very high and survived; Cindy died early (likely underbid).
    # So: if yesterday highest bid was very high, don't go too low; but avoid maxing out.
    if highest_prev_bid >= DAILY_SALARY * 1.15:
        base = DAILY_SALARY * 0.62
        if urgency >= 3:
            base = DAILY_SALARY * 0.85
        elif urgency == 2:
            base = DAILY_SALARY * 0.75
        else:
            base = DAILY_SALARY * 0.68
    else:
        # Lower overall pressure; bid enough to beat weaker bidders
        base = max(DAILY_SALARY * 0.48, avg_prev_bid * 0.9)
        if urgency >= 3:
            base = DAILY_SALARY * 0.8
        elif urgency == 2:
            base = DAILY_SALARY * 0.7

    # Scale by supply factor
    target = base * supply_factor

    # Ensure we don't overspend: keep some runway for later days.
    # If budget is low, cap by 95% of budget.
    cap = budget * 0.95
    target = min(target, cap)

    # If budget is extremely low, still bid something small to try to avoid death spiral
    if budget <= 1.0:
        return 0.0

    # Final clamp
    if target < 0.0:
        target = 0.0
    return float(target)
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

    alive_opps = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Immediate reaction from yesterday's trace
    prev_bids = []
    prev_hp_after = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        if prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid')))
            except Exception:
                pass
        if prev.get('hp_after') is not None:
            try:
                prev_hp_after.append(float(prev.get('hp_after')))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    # Scarcity factor: with supply 15-25 and requirement 9, scarcity is when supply is near 15.
    scarcity = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        scarcity = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0.0:
        scarcity = 0.0
    if scarcity > 1.0:
        scarcity = 1.0

    # If we are in danger, increase bid.
    danger = 0.0
    if hp <= 2.0:
        danger = 1.0
    elif hp <= 4.0:
        danger = 0.7
    else:
        danger = 0.2

    # If we've already had no water, escalate.
    if no_water_days >= 2:
        danger = max(danger, 0.9)
    elif no_water_days == 1:
        danger = max(danger, 0.6)

    # Rival pressure: Cindy/David were high spenders; use highest_prev_bid as a ceiling signal.
    # Target bid: moderately below the highest_prev_bid to avoid overpaying, but above a base when scarce.
    base = DAILY_SALARY * (0.38 + 0.25 * scarcity)  # ~0.38-0.63 of salary
    pressure = 0.0
    if highest_prev_bid > 0.0:
        # If someone was bidding very high, we must match more often.
        pressure = 0.25 * (highest_prev_bid / (DAILY_SALARY + 1e-9))

    # Choose multiplier depending on danger.
    mult = 0.55 + 0.45 * danger
    target = base * mult

    # If yesterday's highest bid was extremely high, lift target closer to it.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        target = max(target, min(DAILY_SALARY * 0.75, highest_prev_bid * 0.75))
    elif highest_prev_bid >= DAILY_SALARY * 0.55:
        target = max(target, min(DAILY_SALARY * 0.65, highest_prev_bid * 0.6))

    # Ensure we don't bid more than we can afford, and keep within reasonable bounds.
    bid = min(budget, target)

    # Additional safeguard: if budget is low, still try to secure when very scarce.
    if bid <= 0.0:
        bid = 0.0
    if bid < DAILY_SALARY * 0.15 and scarcity > 0.6 and budget > 0.0:
        bid = min(budget, DAILY_SALARY * (0.25 + 0.2 * scarcity))

    return max(0.0, float(bid))
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

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for agent_id, st in opponents_status.items():
        if st.get('alive', False):
            alive_opps.append((agent_id, st))

    # If no opponents are alive, take a conservative but sufficient bid.
    if not alive_opps:
        bid = DAILY_SALARY * 0.4
        return min(budget, bid)

    # Read yesterday's bids from previous_trace only.
    prev_bids = []
    prev_pressures = []
    for _, st in alive_opps:
        prev = st.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            prev_bids.append(float(b))
        # Use hp_after as a proxy for how costly yesterday was.
        hp_after = prev.get('hp_after', None)
        if hp_after is not None:
            prev_pressures.append(float(hp_after))

    # Estimate opponent bidding pressure.
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    # Supply pressure: if supply is near the lower end, expect higher competition.
    supply_tightness = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    supply_tightness = max(0.0, min(1.0, float(supply_tightness)))

    # Base bid: target just below the highest observed pressure unless my hp is very low.
    # Yesterday: Cindy bid ~127.5 and survived; Eric bid ~87.45 and survived.
    # We'll aim mid-high, but not reckless.
    if highest_prev_bid >= DAILY_SALARY * 1.2:
        # Someone was extremely aggressive; follow moderately.
        target = min(highest_prev_bid * 0.75, DAILY_SALARY * (0.85 + 0.1 * supply_tightness))
    else:
        # Otherwise, track the average/high but with a buffer.
        target = max(avg_prev_bid * 0.9, DAILY_SALARY * (0.55 + 0.25 * supply_tightness))

    # If I'm in danger, increase bid to avoid further no-water days.
    if hp <= 2 or no_water_days >= 2:
        target = max(target, DAILY_SALARY * 0.95)

    # If I'm healthy, avoid overspending.
    if hp >= 8 and no_water_days == 0:
        target = min(target, DAILY_SALARY * (0.65 + 0.15 * supply_tightness))

    # Convert target to a final bid within budget.
    bid = float(target)
    if bid > budget:
        bid = budget

    # Ensure non-negative.
    if bid < 0.0:
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

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    hp = my_status.get('hp', 0)
    budget = my_status.get('budget', 0)
    no_water_days = my_status.get('no_water_days', 0)

    alive_opps = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Immediate reaction from yesterday traces only
    prev_bids = []
    prev_hp_after = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev.get('bid', 0.0)))
            prev_hp_after.append(float(prev.get('hp_after', opp.get('hp', 0.0))))

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_prev_bid = 0.0
    if len(prev_bids) >= 2:
        sorted_b = sorted(prev_bids, reverse=True)
        second_prev_bid = sorted_b[1]

    # Estimate probability of winning: if we bid slightly above the highest previous bid, we likely take the allocation.
    # Keep bids conservative to preserve budget.
    supply_ratio = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_ratio = (float(supply) - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Base bid depends on our urgency
    urgency = 0
    if hp <= 2:
        urgency = 2
    elif hp <= 4:
        urgency = 1
    if no_water_days >= 2:
        urgency = max(urgency, 1)

    # Target bid level
    # If opponents were already bidding very high yesterday (Cindy/Eric range), we must not be too low.
    if highest_prev_bid >= DAILY_SALARY * 0.85:  # ~76.5 threshold; but yesterday showed ~130-150
        # Aim near highest_prev_bid + small increment, but cap by budget.
        target = highest_prev_bid + 2.5
        if urgency == 0:
            target *= 0.85
        elif urgency == 2:
            target *= 1.0
    elif highest_prev_bid >= DAILY_SALARY * 1.35:  # extra guard, though redundant
        target = highest_prev_bid + 1.5
    else:
        # Otherwise bid mid: enough to compete but not waste.
        # Scale with supply: higher supply => lower need to overbid.
        mid = DAILY_SALARY * (0.45 + 0.25 * (1.0 - supply_ratio))
        # Also slightly above second-highest to beat typical contender
        target = max(mid, second_prev_bid + 1.0)
        if urgency == 2:
            target *= 1.15

    # Ensure we don't bid more than we can afford
    bid = max(0.0, min(float(budget), float(target)))

    # If our hp is very low, push harder
    if hp <= 1:
        bid = min(float(budget), max(bid, DAILY_SALARY * 0.95))

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
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        return float(min(budget, DAILY_SALARY * 0.4))

    # Immediate reaction from yesterday trace
    prev_bids = []
    prev_hps = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid', 0.0)))
            except Exception:
                pass
        try:
            prev_hps.append(float(o.get('hp', 0.0)))
        except Exception:
            pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = sum(prev_bids) / float(len(prev_bids)) if prev_bids else 0.0

    # Supply pressure: fewer units => more aggressive bids
    # Convert supply to a 0..1 pressure signal.
    denom = float(MAX_SUPPLY - MIN_SUPPLY)
    if denom <= 0:
        pressure = 1.0
    else:
        pressure = (supply - float(MIN_SUPPLY)) / denom
        if pressure < 0.0:
            pressure = 0.0
        if pressure > 1.0:
            pressure = 1.0
    scarcity = 1.0 - pressure

    # If I'm in danger, bid harder.
    danger = 0
    if no_water_days >= 2:
        danger = 1
    if hp <= 2.0:
        danger = 2

    # Base bid anchored to yesterday competition without matching extreme bids.
    # Use a target slightly below the highest previous bid when I'm safe,
    # slightly above when I'm in danger.
    if highest_prev_bid > 0.0:
        if danger == 0:
            target = min(highest_prev_bid * 0.90, avg_prev_bid * 0.95 + 5.0)
        elif danger == 1:
            target = min(highest_prev_bid * 0.98, avg_prev_bid * 1.00 + 8.0)
        else:
            target = min(highest_prev_bid * 1.05, avg_prev_bid * 1.10 + 15.0)
    else:
        target = DAILY_SALARY * (0.45 + 0.35 * scarcity)

    # Adjust for scarcity and my hp.
    if hp <= 3.0:
        target *= 1.15
    elif hp >= 7.0:
        target *= 0.92

    target *= (0.90 + 0.25 * scarcity)

    # Convert to water units: prefer bidding for at least 1 unit of WATER_REQ when possible.
    # Since supply is in water units, winning 1 unit costs roughly target; we just cap bid.
    max_affordable = budget

    # Safety caps: never bid more than ~1.3*DAILY_SALARY unless danger.
    cap = DAILY_SALARY * 1.3
    if danger == 2:
        cap = DAILY_SALARY * 1.6
    bid = float(min(max_affordable, min(target, cap)))

    # Ensure at least a small nonzero bid if budget allows.
    if bid <= 0.0:
        bid = float(min(max_affordable, DAILY_SALARY * 0.2))

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

    # Identify alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive'):
            alive_opps.append((oid, o))

    # If no opponents, bid conservatively
    if not alive_opps:
        return max(0.0, min(float(my_status['budget']), DAILY_SALARY * 0.4))

    # Read yesterday bids from immediate previous_trace only
    yesterday_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Estimate opponent pressure: Cindy tended to bid highest; use max yesterday bid as proxy
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    # Safety: with full hp, we can afford to be a bit strategic
    # Determine aggressiveness by supply level (more water available => less need to overpay)
    supply_frac = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_frac = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    # supply_frac near 1 means abundant water

    # Baseline bid: aim to secure water while not matching top bids unnecessarily
    # If supply is abundant, reduce; if scarce, increase.
    # Also increase slightly if we're already accumulating no-water days.
    no_water_pressure = 0.0
    if my_no_water_days >= 2:
        no_water_pressure = 1.0
    if my_no_water_days >= 3:
        no_water_pressure = 1.25

    baseline = DAILY_SALARY * (0.48 - 0.18 * supply_frac)  # ~43 to 30
    baseline *= no_water_pressure if no_water_pressure > 0 else 1.0

    # If opponents were bidding very high yesterday, we should counter but not fully chase.
    # Target: slightly above a fraction of highest_prev_bid.
    if highest_prev_bid > 0:
        # If they were extremely aggressive, match closer to top to ensure winning.
        if highest_prev_bid >= DAILY_SALARY * 1.6:  # ~144
            target = min(highest_prev_bid * 0.92 + 2.0, DAILY_SALARY * 1.95)
        elif highest_prev_bid >= DAILY_SALARY * 1.2:  # ~108
            target = min(highest_prev_bid * 0.78 + 3.0, DAILY_SALARY * 1.7)
        else:
            target = max(baseline, highest_prev_bid * 0.6 + 5.0)
    else:
        target = baseline

    # HP-based adjustment: if low HP, bid harder.
    if my_hp <= 2.0:
        target = max(target, DAILY_SALARY * 0.9)
    elif my_hp <= 4.0:
        target = max(target, DAILY_SALARY * 0.65)

    # Budget cap
    bid = min(my_budget, target)
    # Ensure non-negative
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

    supply = day_context['supply']
    day = day_context['day']

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', True):
            alive_opps.append((oid, o))

    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Immediate reaction from yesterday's trace
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate competition intensity: if someone previously bid near/above our salary, expect aggressive bidding.
    aggressive = highest_prev_bid >= DAILY_SALARY * 0.85

    # Supply pressure: with supply in [15,25], our need is fixed; when supply is low, water is scarcer.
    # Normalize scarcity: lower supply => higher scarcity factor.
    scarcity = (MAX_SUPPLY - float(supply)) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    scarcity = max(0.0, min(1.0, scarcity))

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    # Base bid: aim to be competitive but avoid Cindy-like budget bust.
    # If aggressive, slightly outbid the previous highest but cap by a fraction of salary.
    if aggressive:
        target = min(DAILY_SALARY * (0.65 + 0.25 * scarcity), highest_prev_bid + 2.0)
    else:
        # If not aggressive, we can bid around a moderate level; more scarcity => bid higher.
        target = DAILY_SALARY * (0.45 + 0.25 * scarcity)

    # If our HP is low, increase urgency.
    if hp <= 2:
        target *= 1.25
    elif hp <= 3:
        target *= 1.10

    # Ensure we don't bid more than budget.
    bid = min(budget, target)

    # Safety floor: if we can afford it, bid at least something meaningful when supply is low.
    min_bid = DAILY_SALARY * (0.25 + 0.15 * scarcity)
    if bid < min_bid and budget > 0:
        bid = min(budget, min_bid)

    # If budget is tiny, bid whatever we can.
    if budget <= 1e-6:
        return 0.0

    return float(max(0.0, bid))
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

    # Alive opponents only
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # If no opponents, bid conservatively
    if not alive_opps:
        return min(float(my_status.get('budget', 0.0)), DAILY_SALARY * 0.4)

    # Look only at yesterday's immediate trace bids
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

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Determine target bid: exploit tendency to overbid (Cindy died; Alex/Eric survived with ~105-108 avg)
    # If yesterday pressure was high, undercut slightly unless I'm in danger.
    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))

    # Supply pressure heuristic: when supply is near max, competition rises less; when near min, competition rises more.
    supply_mid = (MIN_SUPPLY + MAX_SUPPLY) / 2.0
    supply_factor = 1.0
    if supply < supply_mid:
        supply_factor = 1.08
    elif supply > supply_mid:
        supply_factor = 0.95

    # Baseline: aim to secure water with a moderate bid
    baseline = DAILY_SALARY * 0.58  # ~52.2

    # If yesterday highest bid was high, opponents likely paid up; undercut by a margin.
    if highest_prev_bid >= DAILY_SALARY * 0.85:  # >=76.5
        if my_hp <= 2.0:
            bid = DAILY_SALARY * 0.92  # urgent survival
        else:
            bid = min(highest_prev_bid - 4.0, DAILY_SALARY * 0.70)
    else:
        # Yesterday bids were not extreme; stay near baseline but adjust with supply
        bid = baseline * supply_factor

    # If my HP is low, increase bid to avoid death
    if my_hp <= 3.0:
        bid = max(bid, DAILY_SALARY * 0.75)

    # Budget cap
    bid = min(bid, my_budget)

    # Ensure non-negative
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Alive opponents
    alive_ids = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_ids.append(oid)

    if not alive_ids:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids only (immediate reaction)
    yesterday_bids = []
    for oid in alive_ids:
        prev = opponents_status[oid].get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid

    # Estimate how many water units are likely to be needed to win allocation pressure.
    # Supply is in [15,25], so likely 1 or 2 water quanta (per WATER_REQ).
    # We don't know exact auction outcome, so we use a pressure-based bid.
    likely_quanta = int(supply / float(WATER_REQ))  # 15-25 => 1 or 2
    if likely_quanta < 1:
        likely_quanta = 1

    # If Cindy/Alex/Eric were bidding near high tier, opponents are willing to pay.
    high_pressure = highest_prev_bid >= DAILY_SALARY * 0.85
    medium_pressure = (highest_prev_bid >= DAILY_SALARY * 0.55) and not high_pressure

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    # Baseline bid depends on my hp.
    if hp <= 2:
        # Emergency: bid to avoid death spiral.
        bid = DAILY_SALARY * 0.9
    elif hp <= 4:
        bid = DAILY_SALARY * 0.75
    else:
        bid = DAILY_SALARY * 0.55

    # Adjust to exploit yesterday's observed willingness to pay.
    if high_pressure:
        # Secure at least one quantum; outbid only slightly unless my hp is low.
        if hp > 3:
            bid = max(bid, min(budget, highest_prev_bid + 3.0))
        else:
            bid = min(budget, max(bid, highest_prev_bid + 10.0))
    elif medium_pressure:
        # Competitive but don't burn budget.
        if hp > 3:
            bid = max(bid, min(budget, second_prev_bid + 2.0))
        else:
            bid = min(budget, max(bid, highest_prev_bid + 5.0))
    else:
        # Low pressure: bid enough to keep advantage.
        if likely_quanta >= 2:
            bid = max(bid, DAILY_SALARY * 0.6)
        else:
            bid = max(bid, DAILY_SALARY * 0.5)

    # Budget safety cap
    if budget <= 0:
        return 0.0
    bid = float(min(budget, bid))

    # Ensure non-negative
    if bid < 0:
        bid = 0.0

    return bid
"""
