# ============================================================
# Experiment: exp_108
# Agent: Bob
# Source: exp_108
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
    for opp_id, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append((opp_id, o))

    # Estimate expected water needed: if we've already gone without water, bid more.
    urgency = 0
    if no_water_days is not None:
        urgency = int(no_water_days)

    # React to yesterday's bids if available.
    yesterday_bids = []
    for _, o in alive_opponents:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Base bid target tied to supply level.
    # If supply is near max, we can try to win with moderate bid; if near min, bid more conservatively to avoid overpaying.
    supply_norm = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (float(supply) - float(MIN_SUPPLY)) / float(MAX_SUPPLY - MIN_SUPPLY)
    # supply_norm in [0,1] ideally
    if supply_norm < 0.0:
        supply_norm = 0.0
    if supply_norm > 1.0:
        supply_norm = 1.0

    # Conservative default: aim around 55% salary.
    base = DAILY_SALARY * (0.45 + 0.15 * supply_norm)

    # If hp is low, increase bid.
    if hp is not None and hp <= 2:
        base = DAILY_SALARY * 0.85
    elif hp is not None and hp <= 3:
        base = DAILY_SALARY * 0.65

    # If we've already had no water days, ramp up.
    if urgency >= 2:
        base = max(base, DAILY_SALARY * 0.8)
    elif urgency == 1:
        base = max(base, DAILY_SALARY * 0.6)

    # If we can see opponent yesterday bids, slightly outbid when they were high.
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If opponents were bidding aggressively, we match slightly above if we must.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if hp is not None and hp > 3:
                base = max(base, DAILY_SALARY * 0.35)
            else:
                base = max(base, DAILY_SALARY * 0.95)
        else:
            base = max(base, highest_prev_bid + 1.5)

    # Final cap by budget; also avoid bidding above what we can pay.
    bid = min(float(budget), float(base))

    # Ensure non-negative.
    if bid < 0:
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Alive opponents and yesterday bids
    alive_opps = []
    yesterday_bids = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)
            prev = o.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    yesterday_bids.append(float(prev.get('bid')))
                except Exception:
                    pass

    # Base: if low hp or already in danger, bid to avoid another no-water day
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Estimate how many water units are likely needed to keep hp stable.
    # We assume 1 bid unit corresponds to 1 water unit; bid must be >= WATER_REQ to secure water.
    # Use supply to scale aggressiveness.
    supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    supply_factor = max(0.0, min(1.0, supply_factor))

    # Reaction to yesterday: if bids were high, reduce relative bid to avoid getting into a bidding war.
    # If bids were low, we can slightly overbid to lock supply.
    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids)
    else:
        max_prev_bid = 0.0
        avg_prev_bid = 0.0

    # Determine target bid level
    # Keep a cap so we don't burn budget; also ensure bid is not too low to miss WATER_REQ.
    # Use daily_salary as a soft anchor.
    danger = (hp <= 2.5) or (no_water_days >= 1)

    if danger:
        # In danger: bid closer to WATER_REQ but still budget-aware.
        # If yesterday max bids were extreme, don't match; aim just above WATER_REQ.
        extreme = max_prev_bid >= DAILY_SALARY * 1.2
        if extreme:
            target = WATER_REQ + 1.0 + 2.0 * supply_factor
        else:
            target = max(WATER_REQ + 2.0, 0.65 * avg_prev_bid + 0.35 * (WATER_REQ + 3.0))
    else:
        # Not in immediate danger: bid moderately to control spend.
        # If yesterday bids were high, we shade down; if low, shade up slightly.
        if yesterday_bids:
            shade = 0.85 if max_prev_bid >= DAILY_SALARY else 1.05
        else:
            shade = 1.0
        # Blend between WATER_REQ and a fraction of average yesterday bid.
        target = (WATER_REQ + 2.0) * (0.55 + 0.25 * supply_factor) + 0.45 * avg_prev_bid * shade

    # Convert target into final bid with strict bounds.
    # Ensure bid is at least WATER_REQ*0.9 to have a chance, but don't exceed a fraction of budget.
    min_bid = max(1.0, WATER_REQ * 0.9)
    # Spend policy: keep enough budget for remaining days (10-day episode assumed).
    # Remaining days estimate: episode_days not provided; use day index heuristically.
    # If day is 1..10, remaining = 10-day.
    remaining_days = max(1, 10 - day)
    budget_cap = budget / float(remaining_days) if remaining_days > 0 else budget
    # Also cap by daily salary to avoid runaway bidding.
    budget_cap = min(budget_cap, DAILY_SALARY * 0.9)

    bid = max(min_bid, min(float(target), budget_cap))

    # If no budget, bid 0.
    if budget <= 0.0:
        return 0.0

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

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp is None:
            continue
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Extract yesterday bids from previous_trace for immediate reaction
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Baseline target from yesterday
    highest_prev = max(yesterday_bids) if yesterday_bids else 0.0
    second_highest_prev = 0.0
    if len(yesterday_bids) >= 2:
        sorted_bids = sorted(yesterday_bids)
        second_highest_prev = sorted_bids[-2]

    # Estimate how many units of water are likely to matter
    # (Supply is total; higher supply reduces competition)
    supply_ratio = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Safety pressure: if low HP or already starving, increase aggressiveness
    danger = 0
    if hp <= 2:
        danger += 2
    elif hp <= 4:
        danger += 1
    if no_water_days >= 2:
        danger += 1

    # Choose a clearing-style bid: try to beat yesterday’s likely clearing band but not overpay
    # If yesterday had very high bids, we only need to slightly over the second-highest.
    if highest_prev > 0:
        # Determine a reasonable opponent-bid reference
        if highest_prev >= DAILY_SALARY * 1.6:
            ref = second_highest_prev if second_highest_prev > 0 else highest_prev
            target = ref + 3.0
        else:
            # moderate regime: aim above highest by a small margin
            target = highest_prev + 2.0
    else:
        target = DAILY_SALARY * 0.6

    # Adjust for current supply: more supply => bid less, less supply => bid more
    # supply_ratio close to 0 means MIN_SUPPLY (scarce), close to 1 means MAX_SUPPLY (abundant)
    scarcity_boost = 1.15 - 0.3 * supply_ratio  # between ~0.85 and 1.15
    target *= scarcity_boost

    # HP/budget shaping
    if danger >= 2:
        target *= 1.25
    elif danger == 1:
        target *= 1.10

    # Cap target to avoid bankruptcy; also ensure we don't bid above budget
    # Use a soft cap based on budget and typical daily salary scale.
    max_reasonable = min(budget, DAILY_SALARY * (0.75 if danger == 0 else 0.95))
    bid = min(target, max_reasonable)

    # If we are extremely low HP, ensure we bid enough to likely secure water
    if hp <= 1:
        bid = max(bid, min(budget, DAILY_SALARY * 0.95))

    # Final clamp: non-negative
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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    # Alive opponents
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    # If no one else is alive, conserve
    if not alive:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace only
    prev_bids = []
    for oid, o in alive:
        pt = o.get('previous_trace', {})
        if isinstance(pt, dict):
            b = pt.get('bid', None)
            if b is not None:
                prev_bids.append(float(b))

    # Pressure estimate: Cindy likely bids high; use max yesterday bid
    max_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Target bid logic:
    # - If someone already showed willingness to pay (high max_prev_bid), match enough to compete.
    # - If my hp is low, raise bid to secure water.
    # - Otherwise bid around a mid value to avoid overspending.
    if my_status['hp'] <= 2:
        base = DAILY_SALARY * 0.85
    elif my_status['hp'] <= 4:
        base = DAILY_SALARY * 0.65
    else:
        base = DAILY_SALARY * 0.55

    # If max_prev_bid was very high, nudge upward but cap to avoid death spiral
    if max_prev_bid >= DAILY_SALARY * 0.65:
        base = max(base, min(DAILY_SALARY * 0.75, max_prev_bid * 0.95))
    elif max_prev_bid <= DAILY_SALARY * 0.05:
        # Opponents likely not paying; we can bid lower
        base = min(base, DAILY_SALARY * 0.45)

    # Supply-aware adjustment: when supply is tight, increase bid.
    # supply range is [15,25]; map to a factor.
    tightness = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    tightness = max(0.0, min(1.0, tightness))
    base = base * (1.0 + 0.25 * tightness)

    # Ensure we don't bid more than budget
    bid = float(min(my_status['budget'], base))

    # If budget is extremely low, still bid enough to try to prevent another no-water day
    if my_status['no_water_days'] >= 2 and my_status['budget'] > 0:
        bid = float(min(my_status['budget'], max(bid, DAILY_SALARY * 0.35)))

    # Final clamp
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

    supply = day_context['supply']
    day = day_context['day']

    # Alive opponents and their yesterday bids
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            prev = o.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                alive_opps.append((oid, prev.get('bid'), prev.get('hp_after'), prev.get('budget_after'), prev.get('status')))

    # Estimate pressure from yesterday: if someone overbid heavily, assume fear/urgency
    pressure_bid = 0.0
    if alive_opps:
        pressure_bid = max([b for (_, b, _, _, _) in alive_opps if isinstance(b, (int, float))])

    # Supply tightness: how many full water-units are available relative to our requirement
    # Use int() to avoid float index issues; here only for thresholding.
    supply_int = int(supply)
    tight = supply_int <= (MIN_SUPPLY + 2)  # ~15-17
    mid = (supply_int > (MIN_SUPPLY + 2)) and (supply_int < (MAX_SUPPLY - 2))  # ~18-22
    ample = supply_int >= (MAX_SUPPLY - 2)  # ~23-25

    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    # Base bid level
    # If I am near death or already have consecutive no-water days, bid high.
    if hp <= 2 or no_water_days >= 2:
        bid = DAILY_SALARY * (0.85 if ample else 0.95)
    elif hp <= 4:
        bid = DAILY_SALARY * (0.65 if mid else (0.75 if tight else 0.6))
    else:
        bid = DAILY_SALARY * (0.45 if ample else (0.55 if mid else 0.62))

    # React to yesterday's high-pressure behavior (Cindy/Eric style)
    # If someone bid extremely high yesterday, we should avoid losing water while still not suiciding.
    if pressure_bid >= DAILY_SALARY * 0.9:
        # Increase slightly; but cap to budget.
        bid *= 1.15
    elif pressure_bid <= 1.0:
        # If others were inactive, we can bid less.
        bid *= 0.9

    # If supply is very tight, slight extra bid.
    if tight and (hp > 4):
        bid *= 1.08

    # Final cap to budget and a safety minimum to compete
    bid = float(bid)
    if budget <= 0:
        return 0.0

    # Ensure bid does not exceed budget
    if bid > budget:
        bid = float(budget)

    # Keep a minimum bid if budget allows; otherwise can go low safely when hp is high.
    min_bid = 0.0
    if hp > 6:
        min_bid = DAILY_SALARY * 0.25
    elif hp > 4:
        min_bid = DAILY_SALARY * 0.35
    else:
        min_bid = DAILY_SALARY * 0.6

    if bid < min_bid and budget > min_bid:
        bid = min_bid

    # Never negative
    if bid < 0:
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

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        # If no opponents, bid just enough to ensure allocation.
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from immediate previous_trace only.
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

    # Estimate how competitive the market was.
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Determine target bid level.
    # Observed: Alex avg ~92 with survival; Cindy bid avg ~96 and still risky; so ~92 is a good anchor.
    anchor = DAILY_SALARY * 1.02  # 91.8

    # If my HP is low or I already had no-water days, I must secure water.
    if my_hp <= 2.5 or my_no_water_days >= 1:
        target = anchor * 1.03  # ~94.5
    else:
        # If opponents previously bid very high, slightly increase; otherwise stay near anchor but not max.
        if highest_prev_bid >= anchor * 1.05:
            target = anchor * 1.08
        elif highest_prev_bid >= anchor * 0.95:
            target = anchor * 0.98
        else:
            target = anchor * 0.90

    # Convert target into an actual bid constrained by budget.
    bid = max(0.0, min(my_budget, target))

    # Additional safeguard: if supply is low, competition likely higher; nudge up.
    if supply <= float(MIN_SUPPLY) + 0.5:
        bid = max(bid, min(my_budget, anchor * 1.05))

    # Final cap: never bid above budget.
    if bid > my_budget:
        bid = my_budget

    return float(bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = day_context['supply']
    day = day_context['day']

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Yesterday trace reaction
    prev_bids = []
    prev_hp = {}
    for opp_id, opp in alive_opps:
        prev = opp.get('previous_trace', None)
        if isinstance(prev, dict):
            bid = prev.get('bid', None)
            if bid is not None:
                prev_bids.append(float(bid))
            prev_hp[opp_id] = prev.get('hp_after', opp.get('hp', 0))
        else:
            prev_hp[opp_id] = opp.get('hp', 0)

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else 0.0

    # Supply pressure: medium scenario, supply between 15 and 25.
    # If supply is enough for 1 unit (>=9) but not huge, competition matters.
    # Scale target bid with supply magnitude.
    if supply < 18:
        supply_factor = 0.85
    elif supply < 22:
        supply_factor = 1.0
    else:
        supply_factor = 1.1

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])

    # If opponents were bidding near/above salary, match just above their likely clearing price.
    # Use a small overbid to beat Cindy/Eric without going to maximum.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # If we are healthy, be slightly conservative; if low hp, secure water.
        if my_hp > 5:
            target = (second_prev_bid + 3.0) * supply_factor
        else:
            target = (highest_prev_bid + 2.5) * supply_factor
    else:
        # Their bids were lower; we can bid around their top to ensure win.
        target = (highest_prev_bid + 1.5) * supply_factor

    # Convert target into a budget-safe cap based on our need to last across 10 days.
    # Conservative reserve: keep some budget for later if hp is OK.
    if my_hp > 5:
        budget_cap = my_budget * 0.35
    elif my_hp > 2:
        budget_cap = my_budget * 0.55
    else:
        budget_cap = my_budget * 0.85

    # Also cap by a fraction of daily salary to avoid overspending.
    max_reasonable = DAILY_SALARY * (0.95 if my_hp <= 2 else 0.75)

    bid = min(my_budget, budget_cap, max_reasonable, target)

    # Ensure non-negative and at least a minimal bid when we must compete.
    if bid < 0:
        bid = 0.0

    # If supply is very tight, increase slightly.
    if supply < 17 and my_hp <= 4:
        bid = min(my_budget, max(bid, DAILY_SALARY * 0.7))

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

    alive_opps = [o for o in opponents_status.values() if o.get('alive')]
    if not alive_opps:
        # If no opponents, spend enough to secure water.
        target = min(my_status['budget'], DAILY_SALARY * 0.6)
        return max(0.0, target)

    # Extract yesterday bids for immediate reaction
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Determine urgency
    urgency = 0
    if hp <= 2.0:
        urgency += 3
    if hp <= 4.0:
        urgency += 2
    if no_water_days >= 2:
        urgency += 2
    if no_water_days >= 3:
        urgency += 3

    # Supply pressure: lower supply increases need to outbid.
    # Map supply to a [0,1] pressure factor.
    if MAX_SUPPLY <= MIN_SUPPLY:
        supply_pressure = 0.5
    else:
        supply_pressure = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    # Invert: lower supply => higher pressure
    supply_pressure = 1.0 - max(0.0, min(1.0, supply_pressure))

    # Base bid anchored to yesterday's highest bid.
    # If others were bidding near DAILY_SALARY, match/just-above to secure water.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        base = DAILY_SALARY * (0.75 + 0.25 * supply_pressure)
        # If we're in danger, slightly exceed the top bid trend.
        if urgency >= 4:
            bid = max(base, highest_prev_bid * 1.03)
        else:
            bid = max(base, highest_prev_bid * 0.98)
    else:
        # If yesterday bids were lower, we can be more conservative unless urgent.
        base = DAILY_SALARY * (0.45 + 0.35 * supply_pressure)
        if urgency >= 4:
            bid = max(base, DAILY_SALARY * 0.85)
        elif urgency >= 2:
            bid = max(base, DAILY_SALARY * 0.65)
        else:
            bid = base

    # Never bid more than budget; keep non-negative
    bid = max(0.0, min(budget, float(bid)))

    # If budget is too low, bid what we can but avoid overcommitting.
    if budget <= DAILY_SALARY * 0.2:
        bid = min(budget, DAILY_SALARY * 0.25)

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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.4))

    # Extract yesterday bids and outcomes
    prev_bids = []
    prev_high_pressure = 0.0
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                b = float(b)
            except Exception:
                continue
            prev_bids.append(b)
            if b > prev_high_pressure:
                prev_high_pressure = b

    # Budget and HP pressure
    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Determine aggressiveness target based on yesterday's max bid (proxy for how costly water is)
    # If others were bidding extremely high, we avoid matching them (they may be budget-constrained).
    # If yesterday pressure was moderate, we bid to win.
    if prev_bids:
        highest_prev_bid = max(prev_bids)
    else:
        highest_prev_bid = 0.0

    # Supply-based baseline: lower supply -> higher chance others fight; but we still cap to avoid draining.
    # Normalize supply in [MIN_SUPPLY, MAX_SUPPLY]
    if MAX_SUPPLY == MIN_SUPPLY:
        supply_norm = 0.5
    else:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
        if supply_norm < 0.0:
            supply_norm = 0.0
        if supply_norm > 1.0:
            supply_norm = 1.0

    # Base bid: mid-tier to beat typical cautious bids but undercut extreme bidders
    # When supply is low (norm small), bid higher.
    base = DAILY_SALARY * (0.48 + (0.5 - supply_norm) * 0.35)  # roughly 0.48..0.655 of salary

    # React to our own survival risk
    if my_hp <= 2.0 or no_water_days >= 2:
        base = DAILY_SALARY * 0.85
    elif my_hp <= 4.0 or no_water_days >= 1:
        base = DAILY_SALARY * 0.65

    # Undercut extreme yesterday max bids: if others went very high, don't chase; bid just below a threshold.
    # Use a soft cap relative to highest_prev_bid.
    if highest_prev_bid >= DAILY_SALARY * 1.2:
        # Others likely overcommitting; bid lower than their peak by a margin
        target = min(base, highest_prev_bid * 0.78)
    elif highest_prev_bid >= DAILY_SALARY * 0.9:
        # Moderate-high pressure: bid around base but slightly higher
        target = max(base, highest_prev_bid * 0.62)
    else:
        target = base

    # Ensure we never exceed budget
    bid = min(my_budget, float(target))

    # If budget is tiny, still bid something proportional to avoid guaranteed loss when low supply
    if my_budget <= DAILY_SALARY * 0.2:
        bid = min(my_budget, DAILY_SALARY * 0.15 + my_budget * 0.85)

    # Final clamp
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

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace for immediate reaction
    yesterday_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how many water units are worth trying to secure (coarse)
    # If supply is tight, competition is higher -> bid a bit more.
    tightness = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        tightness = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
        if tightness < 0.0:
            tightness = 0.0
        if tightness > 1.0:
            tightness = 1.0

    # Base bid anchored to observed strong spending (~115-123)
    # Keep below their likely peak to avoid price war.
    base = DAILY_SALARY * 0.62  # 55.8

    # If yesterday's max bid was very high, increase slightly.
    if highest_prev_bid >= DAILY_SALARY * 1.25:
        base = DAILY_SALARY * 0.78  # 70.2
    elif highest_prev_bid >= DAILY_SALARY * 1.05:
        base = DAILY_SALARY * 0.70  # 63

    # If my HP is low or I've already gone without water, bid more to avoid death.
    if hp <= 2.0:
        base = max(base, DAILY_SALARY * 0.92)
    elif hp <= 4.0:
        base = max(base, DAILY_SALARY * 0.78)

    if no_water_days >= 2:
        base = max(base, DAILY_SALARY * 0.80)

    # Tight supply -> mild increase
    base = base * (1.0 + 0.18 * tightness)

    # Cap by budget and a safety ceiling to prevent overbidding
    safety_ceiling = DAILY_SALARY * 1.15  # 103.5
    bid = min(budget, safety_ceiling, base)

    # Ensure non-negative
    if bid < 0.0:
        bid = 0.0

    return float(bid)
"""
