# ============================================================
# Experiment: exp_020
# Agent: Bob
# Source: exp_020
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

    budget = float(my_status.get('budget', 0.0))
    hp = int(my_status.get('hp', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append((opp_id, o))

    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Immediate reaction from yesterday traces
    prev_bids = []
    prev_pressures = []
    for _, o in alive_opponents:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass
        # Use their previous hp_after/status if available to infer pressure
        hp_after = prev.get('hp_after', None)
        status = prev.get('status', None)
        if hp_after is not None:
            try:
                prev_pressures.append((float(hp_after), status))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Supply-based aggressiveness: lower supply -> higher chance of scarcity -> bid more
    # Convert to a 0..1 scarcity factor
    if MAX_SUPPLY <= MIN_SUPPLY:
        scarcity = 0.5
    else:
        scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
        if scarcity < 0.0:
            scarcity = 0.0
        if scarcity > 1.0:
            scarcity = 1.0

    # Base bid aiming to secure enough water without overspending
    # Target: around 1 water unit when possible; scale by scarcity and competition.
    # Since bids are abstract, map to budget fraction.
    base_fraction = 0.35 + 0.25 * scarcity

    # If we are in danger (many no-water days or low hp), increase bid.
    if hp <= 2 or no_water_days >= 2:
        base_fraction += 0.35
    elif hp <= 3:
        base_fraction += 0.15

    # If opponents were already bidding high yesterday, counter.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        if hp > 3:
            base_fraction += 0.10
        else:
            base_fraction += 0.25
    elif highest_prev_bid >= DAILY_SALARY * 0.60:
        base_fraction += 0.05

    # Convert fraction to an actual bid, capped by budget.
    bid = budget * base_fraction

    # Additional cap to avoid extreme overbids; still responsive to competition.
    # Keep bid within [0.2*salary, 1.0*salary] adjusted by scarcity.
    min_bid = DAILY_SALARY * (0.20 + 0.10 * scarcity)
    max_bid = DAILY_SALARY * (1.00 if scarcity >= 0.5 else 0.85)

    if bid < min_bid:
        bid = min_bid
    if bid > max_bid:
        bid = max_bid

    # Final safety: cannot exceed budget
    if bid > budget:
        bid = budget

    # If budget is tiny, just bid what we can.
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace only
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    yesterday_bids.append(float(b))
                except Exception:
                    pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Base bid level from yesterday pressure
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Opponents were willing to pay a lot; secure water with a stronger bid
        base = DAILY_SALARY * 0.75
    else:
        # Otherwise, stay competitive but not maxing out
        base = DAILY_SALARY * 0.60

    # Scale with my urgency
    urgency = 0.0
    if hp <= 2.0:
        urgency = 0.35
    elif hp <= 4.0:
        urgency = 0.20
    elif no_water_days >= 2:
        urgency = 0.15

    # Supply-aware small adjustment: lower supply => higher chance others fight; bid slightly more
    # Use safe int indices if needed, but here only compute thresholds.
    if supply <= float(MIN_SUPPLY):
        supply_adj = 0.10
    elif supply >= float(MAX_SUPPLY):
        supply_adj = -0.05
    else:
        supply_adj = 0.0

    bid = base * (1.0 + urgency + supply_adj)

    # Hard caps to avoid bankrupting
    # Keep bid within budget and reasonable fraction of salary.
    max_reasonable = DAILY_SALARY * 0.95
    bid = min(bid, max_reasonable, budget)
    bid = max(0.0, bid)
    return bid
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

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if bool(opp.get('alive', False)):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        cap = DAILY_SALARY * 0.4
        return min(my_budget, cap)

    # Extract yesterday bids from previous_trace for immediate reaction
    prev_bids = []
    for opp_id, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Use bid pressure from yesterday
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        avg_prev_bid = sum(prev_bids) / float(len(prev_bids))
        # If someone was bidding very high, we must not be too low.
        pressure = 0.6 * avg_prev_bid + 0.4 * highest_prev_bid
    else:
        highest_prev_bid = 0.0
        avg_prev_bid = 0.0
        pressure = DAILY_SALARY * 0.55

    # Supply affects how many water units exist; bid more when supply is tight.
    # If supply is near 15, competition likely increases.
    supply_tightness = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY + 1e-9)
    supply_tightness = max(0.0, min(1.0, supply_tightness))

    # Risk control based on our hp/no-water streak.
    # If low hp or accumulating no-water days, increase bid.
    risk_factor = 0.0
    if my_hp <= 2.0:
        risk_factor += 0.35
    elif my_hp <= 4.0:
        risk_factor += 0.18

    if my_no_water_days >= 2:
        risk_factor += 0.25
    elif my_no_water_days == 1:
        risk_factor += 0.12

    # Base bid: slightly above the recent cluster to beat typical bids (~112-119 from trace)
    # while avoiding extreme overbidding.
    target = pressure * (1.03 + 0.25 * supply_tightness + risk_factor)

    # Also ensure we don't bid below a floor that would resemble David's losing ~89 region.
    floor = DAILY_SALARY * 0.6  # 54
    if highest_prev_bid > 0:
        floor = max(floor, min(highest_prev_bid * 0.8, DAILY_SALARY * 0.95))

    target = max(target, floor)

    # Cap by budget and a reasonable fraction of daily salary to avoid bankruptcy.
    # If our budget is already low, bid close to budget to secure survival.
    budget_ratio = my_budget / float(max(DAILY_SALARY, 1e-9))
    if budget_ratio <= 0.4:
        cap = my_budget
    else:
        cap = min(my_budget, DAILY_SALARY * (0.95 + 0.2 * supply_tightness + risk_factor))

    bid = min(cap, target)

    # Final safety: bid must be non-negative
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    # Alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # If alone, bid conservatively but ensure survival
    if not alive_opps:
        return float(min(my_status.get('budget', 0.0), DAILY_SALARY * 0.4))

    # Extract yesterday bids only from previous_trace
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
    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Supply pressure: higher supply reduces need to overbid
    # Normalize supply to [0,1]
    if MAX_SUPPLY == MIN_SUPPLY:
        supply_norm = 0.5
    else:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
        if supply_norm < 0.0:
            supply_norm = 0.0
        if supply_norm > 1.0:
            supply_norm = 1.0

    # Base target bid: slightly below typical observed bids (~112-118) to win with less burn
    # If supply is low, increase bid.
    base = DAILY_SALARY * (0.50 + (1.0 - supply_norm) * 0.15)  # ~45 to 63

    # React to yesterday highest bid pressure.
    # If someone was willing to pay very high yesterday, we must bid closer to it.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # If we're healthy, undercut slightly; if low HP, match more aggressively.
        if my_hp > 3.0:
            target = max(base, highest_prev_bid * 0.85)
        else:
            target = max(base, highest_prev_bid * 0.95)
    else:
        # If yesterday bids were moderate, bid around base and just above to avoid tie losses.
        target = max(base, highest_prev_bid * 0.70 + 5.0)

    # Urgency from no-water days / low HP
    if my_hp <= 2.0 or no_water_days >= 2:
        target *= 1.15

    # Budget safety: never exceed budget; also avoid spending all budget unless forced.
    # Keep a buffer proportional to remaining days (episode is 10; we don't know current day count reliably).
    # Use a simple fraction buffer.
    spend_cap = my_budget * (0.35 if my_hp > 3.0 else 0.65)
    bid = min(my_budget, target, spend_cap if spend_cap > 0 else my_budget)

    # Final clamp to non-negative
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
    day = int(day_context.get('day', 0))

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Read only yesterday's single trace per opponent (immediate reaction)
    prev_bids = []
    prev_hp_after = []
    for opp_id, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass
        hp_after = prev.get('hp_after', None)
        if hp_after is not None:
            try:
                prev_hp_after.append(int(hp_after))
            except Exception:
                pass

    # Estimate how aggressive the field is based on yesterday
    if prev_bids:
        sorted_bids = sorted(prev_bids)
        # Use median and top quartile for robustness
        median_bid = sorted_bids[int(len(sorted_bids) // 2)]
        top_bid = sorted_bids[-1]
        top_quartile = sorted_bids[int((len(sorted_bids) - 1) * 0.75)]
    else:
        median_bid = DAILY_SALARY * 0.5
        top_bid = DAILY_SALARY * 1.0
        top_quartile = DAILY_SALARY * 0.7

    # Pressure policy:
    # - If our hp is low or we've already had water stress, bid higher.
    # - Otherwise, bid just above the likely low/mid bidders while avoiding matching top bids.
    # Approximate target: beat median/top_quartile slightly, but cap far below top_bid.
    urgency = 0.0
    if hp <= 2:
        urgency = 1.0
    elif hp <= 4:
        urgency = 0.6
    if no_water_days >= 2:
        urgency = max(urgency, 0.8)
    elif no_water_days == 1:
        urgency = max(urgency, 0.4)

    # Supply affects how likely we can secure water; higher supply -> bid less.
    supply_scale = 1.0
    if supply >= MAX_SUPPLY:
        supply_scale = 0.85
    elif supply <= MIN_SUPPLY:
        supply_scale = 1.1

    # Compute a bid target using yesterday signals.
    # We expect Cindy/Eric to keep bidding high; avoid chasing them.
    base_target = 0.0
    if prev_bids:
        # Bid slightly above median to steal water from mid bidders.
        base_target = median_bid + 2.0
        # If top quartile is not too extreme, add a bit more pressure.
        base_target = max(base_target, top_quartile * 0.75 + 5.0)
    else:
        base_target = DAILY_SALARY * 0.55

    # Urgency adjustment
    target = base_target * (0.9 + 0.25 * urgency) * supply_scale

    # Hard caps to avoid overpaying against top bidders
    # If yesterday top bids were huge, keep our cap at ~0.65 of top_bid unless urgency is extreme.
    extreme = 1.0 if urgency >= 0.8 else 0.0
    cap = (top_bid * (0.65 + 0.25 * extreme)) if prev_bids else (DAILY_SALARY * 0.9)
    target = min(target, cap)

    # Ensure we don't exceed budget
    target = min(target, budget)

    # If budget is very low, still bid something to avoid immediate death.
    if target < 1e-6:
        return 0.0

    # Keep bids integer-ish but safe for floats
    return float(max(0.0, target))
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

    # Alive opponents
    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive.append(opp)

    # If no opponents alive, bid conservatively
    if not alive:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace (immediate reaction)
    yesterday_bids = []
    for opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Estimate how aggressively others are bidding
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = (sum(yesterday_bids) / len(yesterday_bids)) if yesterday_bids else 0.0

    # Supply pressure heuristic: lower supply => higher chance others fight harder
    # Map supply in [15,25] to a pressure multiplier in [1.15,0.85]
    if MAX_SUPPLY > MIN_SUPPLY:
        t = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        t = 0.5
    pressure = 1.15 - 0.30 * t

    # Decide target bid relative to yesterday aggressiveness
    # Goal: be competitive against Cindy/Eric-style bids, but not match their max.
    # Use 0.78 of highest_prev_bid plus a small bump.
    target = 0.78 * highest_prev_bid + 2.0

    # If our hp is low or we already have no-water days, increase bid
    hp = int(my_status['hp'])
    no_water_days = int(my_status['no_water_days'])

    if hp <= 2:
        target *= 1.25
    elif hp <= 4:
        target *= 1.10

    if no_water_days >= 2:
        target *= 1.15

    # Apply supply pressure
    target *= pressure

    # Also keep a floor/ceiling around typical daily salary bidding
    # Floor ensures we don't get shut out at low supply; ceiling preserves budget.
    floor_bid = DAILY_SALARY * 0.50
    ceiling_bid = DAILY_SALARY * 0.90

    # If yesterday bids were extremely high, raise floor slightly.
    if highest_prev_bid >= DAILY_SALARY * 1.6:
        floor_bid = DAILY_SALARY * 0.65

    # Final bid clamp
    bid = max(floor_bid, target)
    bid = min(bid, ceiling_bid)
    bid = min(bid, float(my_status['budget']))

    # If budget is too low, bid what we can but still attempt to win if possible
    if bid <= 0.0:
        return 0.0

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

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_highest = 0.0
    if len(prev_bids) >= 2:
        s = sorted(prev_bids, reverse=True)
        second_highest = s[1]

    # Base pressure from yesterday: if others were bidding aggressively, slightly raise.
    aggressive = highest_prev_bid >= DAILY_SALARY * 1.7  # ~153

    # Survival urgency for us.
    urgent = (hp <= 2.5) or (no_water_days >= 2)

    # Supply-based scaling: with higher supply, we can bid less.
    # target water share proxy: more supply => lower bid.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Compute a bid target.
    # Moderate baseline around 0.55 salary; adjust with urgency and aggressiveness.
    base = DAILY_SALARY * (0.55 - 0.15 * supply_ratio)

    if urgent:
        target = DAILY_SALARY * (0.85 - 0.05 * supply_ratio)
    else:
        target = base
        if aggressive:
            target = max(target, DAILY_SALARY * 0.7)
        else:
            # If others were not bidding high, try to undercut slightly.
            target = min(target, DAILY_SALARY * 0.6)

    # If yesterday top bids were very high, try to beat them by a small margin.
    # Use second-highest to avoid overreacting to a single outlier.
    if highest_prev_bid > 0:
        # Cap how much we chase.
        chase = min(DAILY_SALARY * 1.2, second_highest + 5.0)
        target = max(target, chase * 0.95) if aggressive else min(target, chase)

    # Final constraints.
    bid = max(0.0, min(budget, target))

    # Avoid bidding too low when we are at risk.
    if urgent and bid < DAILY_SALARY * 0.6:
        bid = min(budget, DAILY_SALARY * 0.75)

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

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from immediate previous_trace only
    yesterday_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    # Cindy-like behavior: high bids around 120-150; adapt to contest intensity
    # If others were already spending heavily, we match moderately to secure water.
    pressure = 0.0
    if highest_prev_bid >= 0.85 * DAILY_SALARY:
        pressure = 1.0
    elif highest_prev_bid >= 0.6 * DAILY_SALARY:
        pressure = 0.7
    elif highest_prev_bid >= 0.4 * DAILY_SALARY:
        pressure = 0.45
    else:
        pressure = 0.25

    # Supply pressure: more supply means we can bid less to still get allocation.
    # Use normalized factor in [0,1]
    if MAX_SUPPLY != MIN_SUPPLY:
        supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_factor = 0.5
    supply_factor = max(0.0, min(1.0, float(supply_factor)))

    # If we're low HP or have consecutive no-water days, bid more.
    urgency = 0.0
    if hp <= 2.0:
        urgency = 1.0
    elif hp <= 4.0:
        urgency = 0.7
    else:
        urgency = 0.35

    if no_water_days >= 2:
        urgency = max(urgency, 0.85)

    # Base bid target: mid-high to beat aggressive bidder but avoid full matching.
    # Target is near 0.65-0.9 of Cindy-like max spend depending on urgency.
    # Also reduce slightly when supply is high.
    target = DAILY_SALARY * (0.55 + 0.35 * pressure + 0.25 * urgency - 0.15 * supply_factor)

    # If yesterday highest bid was extremely high, add a small increment to ensure we can win allocation.
    if highest_prev_bid > 0:
        target = max(target, min(DAILY_SALARY * 0.95, highest_prev_bid * 0.78 + 5.0))

    # Hard cap: don't exceed budget; also avoid bidding more than needed when budget is tight.
    # Keep a reserve for later days.
    reserve_ratio = 0.25
    max_affordable = max(0.0, budget * (1.0 - reserve_ratio))

    bid = min(max_affordable, target)

    # Ensure non-negative and at least some minimal bid if budget allows.
    if budget > 0 and bid <= 0:
        bid = min(budget, DAILY_SALARY * 0.2)

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

    # Collect yesterday bids and pressure signals
    yesterday_bids = []
    extreme_bid_bids = []
    critical_hp_opps = 0
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                bval = float(b)
                yesterday_bids.append(bval)
                if bval >= DAILY_SALARY * 1.2:
                    extreme_bid_bids.append(bval)
            except Exception:
                pass
        if int(o.get('hp', 0)) <= 1:
            critical_hp_opps += 1

    # Baseline bid: aim to secure enough water without joining extreme wars
    # If supply is higher, we can bid less; if supply is lower, bid more.
    supply_factor = 0.5
    if supply <= MIN_SUPPLY:
        supply_factor = 0.78
    elif supply >= MAX_SUPPLY:
        supply_factor = 0.45
    else:
        # linear interpolation between 0.78 at 15 and 0.45 at 25
        supply_factor = 0.78 - (supply - MIN_SUPPLY) * (0.78 - 0.45) / (MAX_SUPPLY - MIN_SUPPLY)

    # If we are in danger (many no-water days or low hp), bid more aggressively.
    danger = 0
    if hp <= 2:
        danger += 1
    if no_water_days >= 2:
        danger += 1

    # If opponent bids were extreme yesterday, they likely overcommitted. We underbid unless we must.
    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
    else:
        max_prev_bid = 0.0

    # Compute target based on signals
    if danger >= 2:
        target = DAILY_SALARY * 0.85 * supply_factor
    elif danger == 1:
        target = DAILY_SALARY * 0.65 * supply_factor
    else:
        # default: undercut extreme behavior
        if max_prev_bid >= DAILY_SALARY * 1.2:
            target = DAILY_SALARY * 0.38 * supply_factor
        else:
            target = DAILY_SALARY * 0.52 * supply_factor

    # If multiple opponents are critical, we may need to bid higher to prevent them from locking water.
    if critical_hp_opps >= 2:
        target *= 1.25

    # Cap by budget and keep some reserve for later days.
    reserve_fraction = 0.25
    max_affordable = max(0.0, budget * (1.0 - reserve_fraction))
    bid = min(target, max_affordable, budget)

    # Ensure non-negative and at least small bid if budget allows
    if bid < 0.0:
        bid = 0.0

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

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Pull yesterday bids from previous_trace for immediate reaction
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', None)
        if isinstance(prev, dict):
            bid = prev.get('bid', None)
            if bid is not None:
                try:
                    prev_bids.append(float(bid))
                except Exception:
                    pass
        elif isinstance(prev, list) and prev:
            # If previous_trace is list of events, only use the last entry (still immediate)
            last = prev[-1]
            if isinstance(last, dict):
                bid = last.get('bid', None)
                if bid is not None:
                    try:
                        prev_bids.append(float(bid))
                    except Exception:
                        pass

    # Estimate how hard others fought yesterday
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        avg_prev_bid = sum(prev_bids) / float(len(prev_bids))
    else:
        highest_prev_bid = 0.0
        avg_prev_bid = 0.0

    # Supply pressure: with higher supply, winning doesn't need to be as expensive.
    # With lower supply, bid higher to secure enough water.
    supply_frac = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_frac = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    supply_frac = max(0.0, min(1.0, supply_frac))
    low_supply_factor = 1.15 - 0.15 * supply_frac  # 1.15 at min supply, 1.00 at max supply

    # Base target bid derived from observed surviving pressure.
    # Surviving agents bid around 100-120; we try to slightly exceed average or a fraction of highest.
    target = max(DAILY_SALARY * 0.45, avg_prev_bid * 1.02)

    # If someone bid very high yesterday, we match/overshoot to prevent being outbid.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        target = max(target, highest_prev_bid * 1.03)

    # If our HP is low or we've gone without water, increase aggressiveness.
    if my_hp <= 2.0 or my_no_water_days >= 2:
        target *= 1.25
    elif my_hp <= 4.0:
        target *= 1.10

    # Apply supply factor
    target *= low_supply_factor

    # Final clamp: never exceed budget; also keep within reasonable bounds.
    # Budget might be small late-game; ensure non-negative.
    bid = max(0.0, min(my_budget, target))

    # Safety: if budget is tiny, still bid something to avoid zero-water streak.
    if bid <= 0.0 and my_budget > 0.0:
        bid = min(my_budget, DAILY_SALARY * 0.2)

    return float(bid)
"""
