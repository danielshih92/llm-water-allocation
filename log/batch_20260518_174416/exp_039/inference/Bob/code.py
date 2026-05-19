# ============================================================
# Experiment: exp_039
# Agent: Bob
# Source: exp_039
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    # Basic sanity
    budget = float(my_status.get('budget', 0.0))
    hp = int(my_status.get('hp', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp is not None and opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    # If no opponents, take a safe amount
    if not alive_opponents:
        target = 0.55 * DAILY_SALARY
        return max(0.0, min(budget, target))

    # Read yesterday bids from previous_trace only (immediate reaction)
    prev_bids = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict) and prev.get('bid') is not None:
            prev_bids.append(float(prev.get('bid')))

    # Estimate competitive pressure
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        lowest_prev_bid = min(prev_bids)
    else:
        highest_prev_bid = 0.0
        lowest_prev_bid = 0.0

    # Supply-aware aggressiveness: if supply is scarce relative to requirement, bid more.
    # Avoid list indexing; only compute scalars.
    scarcity_ratio = 0.0
    if WATER_REQ > 0:
        scarcity_ratio = supply / float(WATER_REQ)

    # Base bid: mid level to avoid overpaying
    base_bid = 0.45 * DAILY_SALARY
    if scarcity_ratio < 2.0:
        base_bid = 0.60 * DAILY_SALARY
    elif scarcity_ratio > 2.5:
        base_bid = 0.40 * DAILY_SALARY

    # React to opponents' yesterday behavior
    if prev_bids:
        # If someone previously overbid heavily, we need to compete but not max out.
        if highest_prev_bid >= 0.85 * DAILY_SALARY:
            if hp >= 4:
                bid = min(0.75 * DAILY_SALARY, highest_prev_bid - 1.0)
            else:
                bid = min(0.95 * DAILY_SALARY, highest_prev_bid - 0.5)
        else:
            # If bids were modest, slightly over the lowest to secure water.
            # Add a small increment to beat typical low bids.
            bid = max(base_bid, lowest_prev_bid + 1.5)
    else:
        bid = base_bid

    # HP risk management: low HP increases bid
    if hp <= 2:
        bid = max(bid, 0.85 * DAILY_SALARY)
    elif hp == 3:
        bid = max(bid, 0.65 * DAILY_SALARY)

    # Budget cap
    bid = float(bid)
    if budget <= 0.0:
        return 0.0

    # Also cap by plausible daily salary-like scale
    bid = min(bid, DAILY_SALARY)
    return max(0.0, min(budget, bid))
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
    day = day_context['day']

    # Identify alive opponents
    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive'):
            alive_opponents.append(o)

    # If no opponents, bid conservatively
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Read yesterday bids from previous_trace only
    yesterday_bids = []
    for o in alive_opponents:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Baseline from typical yesterday behavior
    typical_bid = 0.0
    if yesterday_bids:
        typical_bid = sum(yesterday_bids) / float(len(yesterday_bids))
        highest_prev_bid = max(yesterday_bids)
    else:
        highest_prev_bid = 0.0

    # Pressure heuristic: if someone previously bid very high, we must match/beat moderately
    # Use hp to decide how aggressive we can be.
    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])

    # Supply pressure: lower supply => bid higher to avoid no-water days
    # Map supply in [15,25] to pressure in [1.0,0.6]
    if MAX_SUPPLY <= MIN_SUPPLY:
        supply_pressure = 1.0
    else:
        t = (supply - float(MIN_SUPPLY)) / (float(MAX_SUPPLY) - float(MIN_SUPPLY))
        if t < 0.0:
            t = 0.0
        if t > 1.0:
            t = 1.0
        supply_pressure = 1.0 - 0.4 * t

    no_water_days = int(my_status['no_water_days'])

    # Core target bid
    # If high previous bids exist, aim slightly above typical/highest depending on hp.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Very aggressive field
        if my_hp <= 2.0 or no_water_days >= 1:
            target = max(typical_bid * 1.05, highest_prev_bid * 0.98)
        else:
            target = max(typical_bid * 1.02, highest_prev_bid * 0.85)
    else:
        # Moderate field
        if my_hp <= 2.0 or no_water_days >= 1:
            target = max(typical_bid * 1.08, DAILY_SALARY * 0.7)
        else:
            target = max(typical_bid * 1.03, DAILY_SALARY * 0.55)

    # Adjust by supply pressure
    target = target * float(supply_pressure)

    # Keep within budget and also avoid overpaying late if budget low
    # Use remaining days heuristic lightly: episode_days not provided; rely on day index.
    # If day is late (>=8), be a bit more conservative.
    if day is not None:
        try:
            d = int(day)
        except Exception:
            d = 0
    else:
        d = 0

    if d >= 8:
        target = target * 0.9

    # Final cap: cannot exceed budget
    bid = min(my_budget, target)

    # Ensure non-negative
    if bid < 0.0:
        bid = 0.0

    # If bid becomes too small relative to need, enforce a minimum floor
    # (helps when supply is low and hp is critical)
    if my_hp <= 2.0:
        bid = max(bid, min(my_budget, DAILY_SALARY * 0.9))
    elif no_water_days >= 2:
        bid = max(bid, min(my_budget, DAILY_SALARY * 0.75))
    else:
        bid = max(bid, min(my_budget, DAILY_SALARY * 0.5)) if bid == 0.0 else bid

    return bid
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

    # Alive opponents only
    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append(o)

    # If no opponents, secure enough water cheaply
    if not alive_opponents:
        target = 1.0 * DAILY_SALARY * 0.4
        if my_status['budget'] is None:
            return 0
        return min(float(my_status['budget']), target)

    # Inspect yesterday bids for immediate pressure signal
    yesterday_bids = []
    for o in alive_opponents:
        prev = o.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    yesterday_bids.append(float(b))
                except Exception:
                    pass

    max_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how many water units are feasible; map supply to a pressure level.
    # Use int() to avoid float index issues.
    # For our requirement 9, supply 15-25 implies 1 unit always, sometimes 2 units depending on exact rules.
    # We still bid to win at least one unit.
    units_possible = int(supply / float(WATER_REQ))
    if units_possible < 1:
        units_possible = 1

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Strategy:
    # - If we're in danger (low hp or accumulating no-water days), bid aggressively.
    # - If yesterday had very high bids (Cindy/Eric ~100+), don't fully match; bid moderately above the level needed.
    # - Otherwise, bid around a mid level to secure water.
    danger = (hp <= 2.0) or (no_water_days >= 2)

    if max_prev_bid >= 105.0:
        # High competition; scale down vs max to avoid overpaying
        if danger:
            bid = DAILY_SALARY * 0.85
        else:
            bid = max(DAILY_SALARY * 0.55, max_prev_bid * 0.35)
    elif max_prev_bid >= 70.0:
        if danger:
            bid = DAILY_SALARY * 0.75
        else:
            bid = max(DAILY_SALARY * 0.48, max_prev_bid * 0.25)
    else:
        if danger:
            bid = DAILY_SALARY * 0.65
        else:
            bid = DAILY_SALARY * 0.42

    # Adjust slightly by supply: higher supply reduces need to overbid
    # supply in [15,25] => factor in [1.05..0.95]
    if supply >= float(MAX_SUPPLY):
        bid *= 0.95
    elif supply <= float(MIN_SUPPLY):
        bid *= 1.05

    # Final clamp to budget and non-negative
    if budget <= 0:
        return 0.0
    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget

    # Keep bids from going beyond what we'd reasonably pay for one unit
    # (acts as a soft cap)
    soft_cap = max(DAILY_SALARY * 0.95, max_prev_bid * 0.6)
    if bid > soft_cap:
        bid = soft_cap

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

    supply = day_context['supply']
    day = day_context['day']

    # Alive opponents
    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((opp_id, opp))

    # If no one else alive, conserve
    if not alive:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.35))

    # Use only yesterday trace bids for immediate reaction
    prev_bids = []
    for opp_id, opp in alive:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid', None)
        if bid is not None:
            prev_bids.append(float(bid))

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Determine aggressiveness target from yesterday
    # If others were bidding very high, bid enough to avoid losing the water, but not as high as them.
    # If they were moderate, bid near a mid level to still compete.
    aggressive = highest_prev_bid >= DAILY_SALARY * 0.85

    # Budget and HP based risk
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status.get('no_water_days', 0))

    # If we're running out of HP quickly, raise bids
    if hp <= 2.5 or no_water_days >= 2:
        base = DAILY_SALARY * (0.85 if aggressive else 0.70)
    elif hp <= 4.0:
        base = DAILY_SALARY * (0.70 if aggressive else 0.60)
    else:
        base = DAILY_SALARY * (0.55 if aggressive else 0.50)

    # Add a small premium over the observed highest bid to outbid when needed.
    # Keep it bounded to avoid overspending.
    premium = 0.0
    if aggressive:
        premium = min(DAILY_SALARY * 0.10, highest_prev_bid * 0.05 + 2.0)
    else:
        premium = min(DAILY_SALARY * 0.05, highest_prev_bid * 0.03 + 1.0)

    # Supply pressure: when supply is lower, competition increases, so slightly increase bid.
    # supply is float; map to a factor.
    if supply <= float(MIN_SUPPLY):
        supply_factor = 1.10
    elif supply >= float(MAX_SUPPLY):
        supply_factor = 0.95
    else:
        # linear between MIN_SUPPLY and MAX_SUPPLY
        supply_factor = 1.10 - 0.15 * ((supply - float(MIN_SUPPLY)) / (float(MAX_SUPPLY) - float(MIN_SUPPLY)))

    target = (base + premium) * supply_factor

    # Ensure we don't exceed budget
    bid = max(0.0, min(budget, target))

    # Safety floor: if budget is tiny, still bid what we can.
    if bid == 0.0 and budget > 0.0:
        bid = min(budget, DAILY_SALARY * 0.10)

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
    day = day_context.get('day', 0)

    my_hp = float(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append((oid, o))

    if my_budget <= 0:
        return 0.0

    # Collect yesterday bids for alive opponents (immediate reaction)
    yesterday_bids = []
    for oid, o in alive_opponents:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Estimate how many water units might exist; use only for aggressiveness scaling
    # (Indices not used; only for thresholds)
    supply_ratio = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    if supply_ratio < 0.0:
        supply_ratio = 0.0
    if supply_ratio > 1.0:
        supply_ratio = 1.0

    # Determine pressure from yesterday (avoid overbidding like Cindy/David)
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    # Also detect if someone likely overbid/broke budget yesterday
    broke_budget = False
    for oid, o in alive_opponents:
        prev = o.get('previous_trace', {}) or {}
        prev_budget_after = prev.get('budget_after', None)
        if prev_budget_after is not None:
            try:
                if float(prev_budget_after) <= 0.0:
                    broke_budget = True
            except Exception:
                pass

    # Base bid target: secure water without chasing extreme bids
    # When supply is scarce, raise bid; when abundant, lower.
    scarcity_multiplier = 0.55 + (1.0 - supply_ratio) * 0.55  # in [0.55, 1.10]

    # HP urgency
    if my_hp <= 2:
        hp_multiplier = 1.00
    elif my_hp <= 4:
        hp_multiplier = 0.85
    else:
        hp_multiplier = 0.65

    # If we've been without water, increase urgency
    if my_no_water_days >= 2:
        no_water_multiplier = 1.05
    elif my_no_water_days == 1:
        no_water_multiplier = 0.95
    else:
        no_water_multiplier = 0.85

    # Decide cap based on yesterday's peak but discount extremes if someone broke budget
    # Alex survived with moderate bids; Cindy/David likely overbid. So we target below peak.
    if highest_prev_bid > 0:
        if broke_budget:
            # If someone already collapsed budget, avoid matching peak; bid around 60% of peak.
            peak_target = highest_prev_bid * 0.60
        else:
            peak_target = highest_prev_bid * 0.75
    else:
        peak_target = DAILY_SALARY * 0.55

    # Compute final bid
    target = peak_target * scarcity_multiplier * hp_multiplier * no_water_multiplier

    # Keep within reasonable bounds relative to our budget and salary
    min_reasonable = DAILY_SALARY * 0.30
    max_reasonable = DAILY_SALARY * 0.95

    if target < min_reasonable:
        target = min_reasonable
    if target > max_reasonable:
        target = max_reasonable

    # If we are confident supply is decent, reduce a bit to conserve budget
    if supply_ratio >= 0.7 and my_hp > 4:
        target *= 0.85

    # Ensure we don't exceed budget
    if target > my_budget:
        target = my_budget

    # If budget is very low, still bid something to avoid zero-water streak
    if my_budget < DAILY_SALARY * 0.20:
        target = min(my_budget, DAILY_SALARY * 0.25)

    return float(target)
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

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append(o)

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids and some pressure signals
    prev_bids = []
    prev_max_candidates = []
    for o in alive:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass
        # Use yesterday's hp_after/status as a proxy for how costly it was
        hp_after = prev.get('hp_after', None)
        status = prev.get('status', None)
        if isinstance(status, str) and status.lower().find('dead') >= 0:
            prev_max_candidates.append(1.0)
        if hp_after is not None:
            try:
                if float(hp_after) <= 0:
                    prev_max_candidates.append(1.0)
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    # Determine urgency
    urgency = 0
    if hp <= 2.0:
        urgency += 2
    if hp <= 4.0:
        urgency += 1
    if no_water_days >= 2:
        urgency += 1

    # If opponents were spending a lot yesterday, raise bid slightly to avoid losing water.
    # Otherwise keep moderate to preserve budget.
    pressure = 0.0
    if highest_prev_bid >= DAILY_SALARY * 1.0:
        pressure += 1.0
    if avg_prev_bid >= DAILY_SALARY * 0.9:
        pressure += 0.5
    if prev_max_candidates:
        pressure += 0.25

    # Supply affects how many winners might be possible; higher supply -> can bid less.
    # Normalize supply to [0,1] using known min/max.
    supply_norm = 0.0
    if MAX_SUPPLY != MIN_SUPPLY:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    if supply_norm < 0.0:
        supply_norm = 0.0
    if supply_norm > 1.0:
        supply_norm = 1.0

    # Base target bid
    # When supply is high, bid lower; when supply is low, bid higher.
    base = DAILY_SALARY * (0.62 - 0.22 * supply_norm)

    # Adjust for pressure and urgency
    target = base + pressure * DAILY_SALARY * 0.18 + urgency * DAILY_SALARY * 0.12

    # Hard caps to avoid reckless spending
    # If hp is extremely low, allow near-salary bidding.
    if urgency >= 2:
        target = max(target, DAILY_SALARY * 0.85)
    elif urgency == 1:
        target = max(target, DAILY_SALARY * 0.65)

    # If opponents were bidding very high yesterday, ensure we are not too far behind.
    if highest_prev_bid > 0.0:
        if highest_prev_bid >= DAILY_SALARY * 1.15:
            target = max(target, highest_prev_bid * 0.75)
        elif highest_prev_bid >= DAILY_SALARY * 0.95:
            target = max(target, highest_prev_bid * 0.65)

    # Final clamp
    if budget <= 0.0:
        return 0.0
    bid = min(budget, target)

    # Keep bid non-negative
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
    day = day_context['day']

    # Collect alive opponents and use yesterday trace only for immediate reaction
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            prev = o.get('previous_trace', {})
            prev_bid = prev.get('bid', None)
            alive.append((oid, o, prev_bid))

    # If no opponents alive, bid conservatively
    if not alive:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.4))

    # Estimate opponent pressure from yesterday
    prev_bids = [pb for (_, _, pb) in alive if pb is not None]
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Base bid: aim to beat the likely leader without matching extreme bids
    # Cindy averaged ~55.5 and max ~82.5; we target a mid-high region.
    # If supply is low, competition is higher -> bid more.
    supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    low_supply_factor = 1.15 if supply_norm < 0.5 else 0.95

    # Health urgency
    hp = float(my_status['hp'])
    no_water_days = int(my_status['no_water_days'])

    if hp <= 1.0 or no_water_days >= 2:
        urgency_factor = 1.25
    elif hp <= 3.0 or no_water_days == 1:
        urgency_factor = 1.10
    else:
        urgency_factor = 0.95

    # Reaction to yesterday's max bid
    # If someone was bidding very high yesterday, we increase slightly to avoid getting shut out.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        reaction = 1.15
    elif highest_prev_bid >= DAILY_SALARY * 0.6:
        reaction = 1.05
    else:
        reaction = 0.95

    # Compute target bid
    # Anchor around a reasonable contest level: ~0.6 salary, adjusted by factors.
    target = DAILY_SALARY * 0.60 * low_supply_factor * urgency_factor * reaction

    # If we have a meaningful estimate of leader's yesterday bid, try to undercut/beat modestly.
    # Add a small margin but cap it to not overspend.
    if highest_prev_bid > 0:
        target = max(target, highest_prev_bid * 0.90 + 2.0)

    # Safety caps based on our budget and typical max reasonable spend
    budget = float(my_status['budget'])
    if budget <= 0:
        return 0.0

    # Don't spend more than we can afford; also keep below ~0.95 salary unless urgency is extreme.
    extreme = (hp <= 1.0 or no_water_days >= 2)
    cap = budget
    if extreme:
        cap = min(cap, DAILY_SALARY * 0.95)
    else:
        cap = min(cap, DAILY_SALARY * 0.75)

    bid = min(cap, target)

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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        return max(0.0, min(float(my_status['budget']), DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace
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

    # Estimate how many water units are likely available for allocation pressure.
    # Higher supply => can bid less aggressively while still securing water.
    supply_ratio = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    if supply_ratio < 0.0:
        supply_ratio = 0.0
    if supply_ratio > 1.0:
        supply_ratio = 1.0

    # Base bid: enough to compete but not match the top bidder unless needed.
    # Use hp pressure: lower hp => bid more.
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    # If Alex-like high pressure existed yesterday, slightly undercut.
    # If Cindy/Eric-like low bidders existed, we can safely bid higher than the low cluster.
    # We only have highest_prev_bid reliably; use it as a proxy for aggressiveness.
    aggressive_market = highest_prev_bid >= DAILY_SALARY * 0.85

    # Determine target fraction of DAILY_SALARY
    if hp <= 2.0:
        base_frac = 0.85
    elif hp <= 4.0:
        base_frac = 0.65
    else:
        base_frac = 0.55

    # Adjust for supply: more supply => reduce fraction a bit
    base_frac = base_frac - 0.12 * supply_ratio

    # If market was aggressive yesterday, increase but try not to fully chase.
    if aggressive_market:
        base_frac = base_frac + 0.15

    # If supply is at the low end, increase to ensure we don't get starved.
    if supply <= (MIN_SUPPLY + 1.0):
        base_frac = base_frac + 0.08

    # Convert to bid and cap by budget.
    target_bid = DAILY_SALARY * base_frac

    # Undercut highest_prev_bid when it is very high; otherwise keep target.
    if highest_prev_bid > 0.0:
        # Aim to be close but not equal; subtract a small margin.
        if aggressive_market:
            target_bid = min(target_bid, highest_prev_bid - 3.0)
        else:
            # If not aggressive, still ensure we beat mid-level bids slightly.
            target_bid = max(target_bid, highest_prev_bid * 0.75)

    # Final safety caps
    if budget <= 0.0:
        return 0.0

    bid = max(0.0, min(budget, target_bid))
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

    # Alive opponents only
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace
    prev_bids = []
    for o in alive_opps:
        pt = o.get('previous_trace', {}) or {}
        b = pt.get('bid', None)
        if b is not None:
            prev_bids.append(float(b))

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Supply-aware aggressiveness: with supply near 25, we can afford to bid a bit more
    # but still avoid overpaying.
    supply_ratio = 0.0
    try:
        supply_ratio = (float(supply) - 15.0) / (25.0 - 15.0)
    except Exception:
        supply_ratio = 0.5
    if supply_ratio < 0.0:
        supply_ratio = 0.0
    if supply_ratio > 1.0:
        supply_ratio = 1.0

    # Determine target multiplier based on yesterday aggressiveness
    # Alex/Cindy yesterday show bids around ~94-113; use that as a signal.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        base_mult = 0.75
    elif highest_prev_bid >= DAILY_SALARY * 0.6:
        base_mult = 0.62
    else:
        base_mult = 0.52

    # If our HP is low, we must secure water more reliably.
    hp = float(my_status.get('hp', 0.0))
    if hp <= 2.0:
        base_mult += 0.25
    elif hp <= 4.0:
        base_mult += 0.12

    # Slightly scale with supply_ratio (more supply -> can bid slightly more)
    mult = base_mult + 0.08 * supply_ratio

    # Convert to bid; keep within budget and avoid bidding above salary cap too often.
    bid = DAILY_SALARY * mult

    # Safety: never bid negative; never exceed budget.
    if bid < 0.0:
        bid = 0.0

    budget = float(my_status.get('budget', 0.0))
    bid = min(bid, budget)

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

    # Alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # If no opponents alive, conserve budget
    if not alive_opps:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.35))

    # Use yesterday trace bids to infer pressure
    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                yesterday_bids.append(float(bid))
            except Exception:
                pass

    # Baseline: bid enough to compete for water without burning budget
    # Scale with supply: higher supply reduces need to overbid.
    supply_factor = 0.6 + 0.4 * ((supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)) if MAX_SUPPLY != MIN_SUPPLY else 0.8
    supply_factor = max(0.5, min(1.0, supply_factor))

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    # If I'm low HP, prioritize survival
    if hp <= 2.0:
        target = DAILY_SALARY * 0.95
    elif hp <= 4.0:
        target = DAILY_SALARY * 0.75
    else:
        target = DAILY_SALARY * 0.55

    # If others were bidding aggressively yesterday, slightly outbid the crowd
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / float(len(yesterday_bids))

        # Cindy averaged ~123 and survived; treat high bids as strong demand signal.
        if highest_prev_bid >= DAILY_SALARY * 1.2:
            # Compete more; but cap to avoid bankruptcy
            target = max(target, avg_prev_bid * 0.95)
            # Ensure we are not too low when someone is clearly paying
            target = max(target, DAILY_SALARY * 0.65)
        elif highest_prev_bid >= DAILY_SALARY * 0.85:
            target = max(target, highest_prev_bid * 0.92)
        else:
            # If bids were low, we can bid closer to baseline
            target = min(target, avg_prev_bid * 1.05) if avg_prev_bid > 0 else target

    # Convert target to a bid that is affordable and sensible
    # Also incorporate no_water_days: if I've been without water, bid more.
    no_water_days = int(my_status['no_water_days'])
    if no_water_days >= 2:
        target *= 1.15
    elif no_water_days >= 1:
        target *= 1.05

    target *= supply_factor

    # Final clamp
    bid = max(0.0, min(budget, target))

    # Avoid bidding zero unless budget is tiny
    if bid <= 0.0 and budget > 0.0:
        bid = min(budget, DAILY_SALARY * 0.1)

    return float(bid)
"""
