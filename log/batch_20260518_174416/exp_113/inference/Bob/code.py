# ============================================================
# Experiment: exp_113
# Agent: Bob
# Source: exp_113
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
    day = day_context['day']

    alive = [o for o in opponents_status.values() if o.get('alive', False)]

    # Baseline: aim to win enough water without overpaying.
    # If supply is near our requirement, we must bid higher; if abundant, bid lower.
    # Normalize supply relative to [MIN_SUPPLY, MAX_SUPPLY].
    if MAX_SUPPLY - MIN_SUPPLY > 0:
        t = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        t = 0.5
    t = max(0.0, min(1.0, t))

    # Look at yesterday bids only from immediate previous_trace.
    prev_bids = []
    for opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev['bid'])

    # Determine aggressiveness based on observed opponent pressure yesterday.
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        # If they were bidding near a salary scale, they likely needed water badly.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # If our HP is low, we must secure water.
            if my_status.get('hp', 0) <= 2:
                target = DAILY_SALARY * 0.95
            else:
                target = DAILY_SALARY * 0.35
        else:
            # Otherwise, slightly outbid the likely competitive level.
            target = max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5)
    else:
        # No trace info provided: use supply-driven moderate bid.
        # Lower when supply is abundant; higher when supply is tight.
        target = DAILY_SALARY * (0.68 - 0.18 * t)

    # Adjust for our own health/budget/no-water days.
    hp = my_status.get('hp', 0)
    budget = my_status.get('budget', 0)
    no_water_days = my_status.get('no_water_days', 0)

    if hp <= 1:
        target *= 1.15
    elif hp <= 2:
        target *= 1.05
    elif hp >= 6:
        target *= 0.9

    # If we've already missed several days, increase urgency.
    if no_water_days >= 2:
        target *= 1.12

    # Convert to final bid respecting budget.
    bid = min(budget, target)

    # Hard floor: if we can afford it, bid at least a fraction to avoid being starved.
    # (Still capped by budget.)
    min_bid = min(budget, DAILY_SALARY * 0.35)
    bid = max(min_bid, bid)

    # Ensure bid is non-negative.
    if bid < 0:
        bid = 0
    return float(bid)
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

    # Extract yesterday bids from traces (immediate reaction only)
    yesterday_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Baseline from yesterday: surviving bids clustered ~100-112; use that as target.
    target = DAILY_SALARY * 0.6  # 54
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        lowest_prev_bid = min(yesterday_bids)
        # If someone previously bid aggressively, match slightly below to win.
        if highest_prev_bid >= DAILY_SALARY * 0.85:  # >= 76.5
            target = min(DAILY_SALARY * 0.95, highest_prev_bid * 0.98)
        else:
            # Otherwise, anchor to the upper-middle of observed bids.
            target = max(DAILY_SALARY * 0.55, (lowest_prev_bid + highest_prev_bid) * 0.5)

    # Adjust for supply: higher supply reduces need to overbid.
    # supply in [15,25]; map to aggressiveness.
    if supply <= float(MIN_SUPPLY):
        supply_factor = 1.10
    elif supply >= float(MAX_SUPPLY):
        supply_factor = 0.90
    else:
        # Linear between 15 and 25
        supply_factor = 1.10 - (supply - float(MIN_SUPPLY)) * (1.10 - 0.90) / (float(MAX_SUPPLY - MIN_SUPPLY))

    # Adjust for my HP/no-water streak: if I'm in danger, increase bid.
    danger_boost = 1.0
    if hp <= 2:
        danger_boost = 1.25
    elif hp <= 4:
        danger_boost = 1.15
    if no_water_days >= 2:
        danger_boost = max(danger_boost, 1.20)

    bid = target * supply_factor * danger_boost

    # Clamp to sensible bounds relative to budget.
    # Ensure at least some bid if budget allows.
    min_bid = min(budget, DAILY_SALARY * 0.25)
    max_bid = min(budget, DAILY_SALARY * 1.20)
    if bid < min_bid:
        bid = min_bid
    if bid > max_bid:
        bid = max_bid

    # Final safety: never exceed budget.
    bid = min(bid, budget)

    # If budget is extremely low, bid it all.
    if budget <= 1.0:
        return budget

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

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # If we are in danger, pay to stay alive.
    if hp <= 2 or no_water_days >= 2:
        bid = min(budget, DAILY_SALARY * 0.95)
        return float(bid)

    alive_opps = []
    for opp_id, o in opponents_status.items():
        try:
            if o.get('alive', False):
                alive_opps.append((opp_id, o))
        except Exception:
            continue

    # Default: stay competitive but not maximal.
    # Use yesterday bids as a proxy for current aggressiveness.
    yesterday_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Estimate how much others are willing to pay.
    # Cindy and Eric showed high bids while surviving; target a fraction of their pressure.
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        second_prev = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev

        # Determine supply pressure: higher supply reduces need to overbid.
        supply_frac = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
        supply_frac = max(0.0, min(1.0, supply_frac))

        # Base bid anchored to our daily salary and requirement.
        # If others bid very high yesterday, slightly overmatch; otherwise bid mid.
        if highest_prev >= DAILY_SALARY * 0.85:
            # Aggressive field: bid enough to avoid being outcompeted.
            target = DAILY_SALARY * (0.55 + 0.25 * (1.0 - supply_frac))
        else:
            # Less aggressive: bid around mid.
            target = DAILY_SALARY * (0.45 + 0.15 * (1.0 - supply_frac))

        # If second-highest is close to our target, nudge up a bit.
        try:
            if second_prev > target:
                target = 0.85 * second_prev
        except Exception:
            pass

        # Keep within budget and below extreme spending.
        bid = min(budget, max(0.0, target))
        return float(bid)

    # If no opponent traces/available, bid conservatively.
    # Ensure we can afford repeated bids.
    if budget <= 0:
        return 0.0

    supply_frac = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_frac = max(0.0, min(1.0, supply_frac))

    bid = DAILY_SALARY * (0.40 + 0.10 * (1.0 - supply_frac))
    bid = min(budget, bid)
    return float(max(0.0, bid))
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

    supply = day_context.get('supply', 0)
    day = day_context.get('day', 0)

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return min(my_status.get('budget', 0), DAILY_SALARY * 0.4)

    # Read yesterday bids from previous_trace only (immediate reaction)
    prev_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            prev_bids.append(float(b))

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate how many
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
    day = int(day_context['day'])

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Identify alive opponents
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    # If no opponents are alive, conserve
    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.35))

    # Read yesterday bids from each opponent's previous_trace
    prev_bids = []
    for oid, o in alive:
        pt = o.get('previous_trace', {}) or {}
        b = pt.get('bid', None)
        if b is not None:
            prev_bids.append(float(b))

    # Baseline bid tied to our urgency
    # If we've already gone without water, increase sharply.
    if no_water_days >= 2 or hp <= 2:
        urgency = 0.95
    elif no_water_days == 1 or hp <= 4:
        urgency = 0.75
    else:
        urgency = 0.55

    # Supply pressure: higher supply means we can bid less aggressively.
    # Note: supply is 15-25 in this meta-round.
    supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    # When supply is high, reduce bid slightly; when low, increase.
    supply_factor = 1.0 + (0.5 - supply_norm) * 0.25  # range approx [0.94..1.06]

    # Exploit yesterday: Cindy survived and likely bid strongly; Alex/David died.
    # Use yesterday highest bid as a proxy for the competitive ceiling.
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        # If someone was bidding around/above typical daily salary, we must contest.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            target = DAILY_SALARY * (0.32 if hp > 3 else 0.9)
            # If our budget is low, cap by budget.
            bid = target * supply_factor
        else:
            # Otherwise, bid above the perceived mid field.
            target = max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5)
            bid = target * urgency * supply_factor
    else:
        bid = DAILY_SALARY * urgency * supply_factor

    # Ensure bid is within budget and non-negative
    bid = max(0.0, min(budget, bid))

    # If budget is extremely low, still try to get at least some allocation early.
    if bid < 1e-6:
        bid = max(0.0, min(budget, DAILY_SALARY * 0.2))

    # Small strategic adjustment on later days: if day is near end, bid more to secure survival.
    # Episode days are 10; meta-round day index likely starts at 1.
    if day >= 8:
        bid = min(budget, bid * 1.15)

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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for o in opponents_status.values():
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # React to yesterday bids (immediate trace only)
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', None)
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    prev_bids.append(float(b))
                except Exception:
                    pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Pressure estimate: if opponents were bidding near/above our daily salary, they likely continue.
    aggressive_market = highest_prev_bid >= DAILY_SALARY * 0.85

    # Base bid depends on current supply: higher supply reduces need to outbid.
    # supply in [15,25] => target fraction of daily salary.
    supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_norm = max(0.0, min(1.0, supply_norm))

    if aggressive_market:
        # If they were aggressive, we bid enough to avoid being starved.
        # If my HP is low, bid closer to daily salary; otherwise moderate.
        if hp <= 2.5 or no_water_days >= 2:
            target = DAILY_SALARY * (0.85 - 0.15 * supply_norm)
        else:
            target = DAILY_SALARY * (0.65 - 0.10 * supply_norm)
    else:
        # If they weren't aggressive, bid just above a reasonable threshold.
        target = DAILY_SALARY * (0.55 - 0.10 * supply_norm)

    # Ensure we don't exceed budget; also keep some reserve for later days.
    # Reserve more when HP is comfortable.
    reserve_factor = 0.25 if hp <= 2.5 else 0.35
    max_affordable = max(0.0, budget * (1.0 - reserve_factor))

    bid = min(max_affordable, target)

    # If budget is tiny, still bid what we can.
    if bid <= 0.0:
        bid = min(budget, DAILY_SALARY * 0.2)

    # Slightly nudge up on early days to secure water before opponents can snowball.
    if day <= 3:
        bid = min(budget, bid * 1.12)

    return float(max(0.0, min(budget, bid)))
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

    # Identify alive opponents and extract yesterday bids
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        if isinstance(prev, dict) and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Base bid policy: conserve budget unless I’m in danger
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Escalation triggers
    danger = (hp <= 3.0) or (no_water_days >= 2)

    # Use yesterday highest bid as proxy for opponent aggressiveness
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
    else:
        highest_prev_bid = 0.0

    # Supply pressure: higher supply reduces marginal need to overbid
    # Normalize supply within [15,25]
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_norm = 0.5
    supply_norm = max(0.0, min(1.0, float(supply_norm)))

    # Target bid
    # If opponents were aggressive yesterday, slightly undercut to save budget unless danger.
    if highest_prev_bid >= DAILY_SALARY * 1.6:  # ~144
        if danger:
            target = max(highest_prev_bid * 0.98, DAILY_SALARY * 0.85)
        else:
            target = max(highest_prev_bid * 0.82, DAILY_SALARY * (0.45 + 0.25 * supply_norm))
    elif highest_prev_bid >= DAILY_SALARY * 1.1:  # ~99
        if danger:
            target = max(highest_prev_bid * 0.95, DAILY_SALARY * 0.75)
        else:
            target = max(highest_prev_bid * 0.75, DAILY_SALARY * (0.40 + 0.20 * supply_norm))
    else:
        if danger:
            target = DAILY_SALARY * 0.90
        else:
            # Conservative default
            target = DAILY_SALARY * (0.50 + 0.15 * supply_norm)

    # Ensure bid is within budget and non-negative
    if budget <= 0:
        return 0.0

    target = float(target)
    if target < 0.0:
        target = 0.0

    # Cap to budget; also avoid extreme spending
    max_reasonable = min(budget, DAILY_SALARY * 1.9)
    bid = min(target, max_reasonable)

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
    day = int(day_context['day'])

    # Identify alive opponents
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    if not alive:
        # If no opponents, bid enough to guarantee water but stay conservative
        return min(my_status['budget'], DAILY_SALARY * 0.35)

    # Use only yesterday previous_trace for immediate reaction
    yesterday_bids = []
    for oid, o in alive:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Estimate how aggressive the field is
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # If Cindy is alive, her yesterday behavior suggests persistent high bidding
    # We'll also infer from highest_prev_bid.
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    # Determine target bid based on supply pressure.
    # At higher supply, we can bid less; at lower supply, bid more.
    supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0..1
    supply_norm = max(0.0, min(1.0, supply_norm))

    # Base aggressiveness: if someone previously bid very high, we must match/beat modestly.
    if highest_prev_bid >= DAILY_SALARY * 1.1:  # ~99
        base = DAILY_SALARY * (0.55 - 0.15 * supply_norm)  # 0.55..0.40
        # Add a small increment to beat the likely winner
        target = max(base, min(my_status['budget'], highest_prev_bid * 0.92 + 2.0))
    elif highest_prev_bid >= DAILY_SALARY * 0.6:  # ~54
        target = DAILY_SALARY * (0.45 - 0.10 * supply_norm)
    else:
        target = DAILY_SALARY * (0.35 - 0.05 * supply_norm)

    # Survival/urgency adjustment
    # If low HP or many no-water days, increase bid.
    no_water_days = int(my_status['no_water_days'])
    if hp <= 2.0 or no_water_days >= 2:
        target *= 1.35
    elif hp >= 7.0 and no_water_days == 0:
        target *= 0.85

    # Ensure target is within budget and not absurd.
    target = max(0.0, float(target))
    bid = min(budget, target)

    # If budget is too small, still bid something to avoid falling behind.
    if bid <= 0.0:
        # Minimal non-zero bid to try to secure water
        bid = min(budget, 5.0)

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

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return float(min(budget, DAILY_SALARY * 0.4))

    # Estimate opponents' likely pressure from yesterday's bids
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

    # Identify if a rival is a high spender (likely to win again)
    # Use yesterday's bid as a proxy.
    high_spender = False
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is None:
            continue
        try:
            if float(b) >= DAILY_SALARY * 1.1:
                high_spender = True
                break
        except Exception:
            continue

    # If my hp is low or I already went without water, bid more aggressively.
    if hp <= 2 or no_water_days >= 1:
        target = DAILY_SALARY * (0.85 if not high_spender else 1.05)
    else:
        # Otherwise, bid to beat the likely low bidders without matching Cindy-style spikes.
        if highest_prev_bid >= DAILY_SALARY * 1.0:
            # High pressure day: bid moderately below the leader to avoid burning budget.
            target = min(DAILY_SALARY * 0.95, highest_prev_bid * 0.9)
        else:
            # Low pressure: bid enough to secure water, but keep budget.
            target = max(DAILY_SALARY * 0.45, highest_prev_bid + 2.0)

    # Convert target to a feasible bid range given budget and typical supply scale.
    # Bids are in salary-like units; cap by budget.
    bid = float(min(budget, target))

    # Ensure we can still survive: if budget is tiny, bid what we can.
    if bid < 0.0:
        bid = 0.0

    # Additional heuristic: if today's supply is high, competition is less critical; bid lower.
    if supply >= (MIN_SUPPLY + MAX_SUPPLY) / 2.0:
        bid *= 0.9

    # Final clamp
    if budget <= 0.0:
        return 0.0
    return float(min(budget, max(0.0, bid)))
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
    day = day_context.get('day', 0)

    # Alive opponents
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    # If no opponents, be conservative
    if not alive_opps:
        return min(my_status.get('budget', 0.0), DAILY_SALARY * 0.4)

    # Use only yesterday's previous_trace for immediate reaction
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Baseline from yesterday: try to be slightly above the low-pressure survivor (Eric-like)
    if yesterday_bids:
        low = min(yesterday_bids)
        high = max(yesterday_bids)
        mid = (low + high) / 2.0
    else:
        low = DAILY_SALARY * 0.5
        mid = DAILY_SALARY * 0.6

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Urgency: if we've already gone without water, increase bids
    urgency = 0.0
    if no_water_days >= 2:
        urgency = 1.0
    elif no_water_days == 1:
        urgency = 0.5

    # If low hp, we must secure water; if high hp, we can underbid slightly
    hp_factor = 0.0
    if my_hp <= 2:
        hp_factor = 1.0
    elif my_hp <= 4:
        hp_factor = 0.7
    elif my_hp <= 6:
        hp_factor = 0.4
    else:
        hp_factor = 0.2

    # Supply pressure: lower supply means competition; scale with how tight supply is
    # Map supply in [15,25] to pressure in [1.0,0.2]
    if MAX_SUPPLY > MIN_SUPPLY:
        pressure = 1.0 - (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        pressure = 0.5
    pressure = max(0.2, min(1.0, pressure))

    # Core strategy: start from low-ish yesterday bids, then adjust upward for urgency/hp/pressure
    # Target around low + small premium to beat low bidders without chasing high bidders.
    target = low + (0.08 * (high - low if high > low else DAILY_SALARY))

    # Adjust by urgency/hp/supply
    target *= (1.0 + 0.35 * hp_factor + 0.25 * urgency + 0.25 * pressure)

    # Also cap to avoid overpaying like the top bidders unless we are in danger
    danger_cap = DAILY_SALARY * (0.95 if (my_hp <= 2 or urgency >= 1.0) else 0.75)
    target = min(target, danger_cap)

    # Never bid above budget
    bid = min(my_budget, target)

    # Ensure non-negative and at least a small amount if budget allows
    if bid < 0:
        bid = 0.0
    return bid
"""
