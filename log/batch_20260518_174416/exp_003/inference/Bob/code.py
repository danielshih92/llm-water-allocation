# ============================================================
# Experiment: exp_003
# Agent: Bob
# Source: exp_003
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context['supply'])
    day = day_context['day']

    # Alive opponents
    alive_opps = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opps.append(opp)

    # Base affordability
    budget = float(my_status.get('budget', 0.0))
    hp = float(my_status.get('hp', 0.0))

    # If no opponents, just bid enough to meet requirement if possible
    if not alive_opps:
        target = min(budget, DAILY_SALARY * 0.45)
        return max(0.0, float(target))

    # Read yesterday bids from previous_trace (immediate reaction only)
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Determine pressure from opponent yesterday bids
    pressure = 0.0
    if prev_bids:
        pressure = max(prev_bids)

    # Heuristic: if someone already overpaid aggressively, raise slightly to contest
    # Otherwise keep moderate to preserve budget for later days.
    if pressure >= DAILY_SALARY * 0.85:
        # If we're low HP, bid more to prevent future no-water days
        if hp <= 2.0:
            bid = DAILY_SALARY * 0.75
        else:
            bid = DAILY_SALARY * 0.55
    else:
        # Scale with supply: lower supply -> bid higher to secure water
        # supply in [15,25], requirement 9 => 1 unit likely; bid to contest but not max out
        if supply <= 17.0:
            bid = DAILY_SALARY * 0.60
        elif supply <= 20.0:
            bid = DAILY_SALARY * 0.50
        else:
            bid = DAILY_SALARY * 0.42

    # Ensure bid does not exceed budget
    bid = min(float(bid), budget)

    # If budget is extremely low, bid what we can
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    # Identify alive opponents
    alive_ops = []
    for oid, o in opponents_status.items():
        if o.get('alive', True):
            alive_ops.append(o)

    # If no opponents alive, conserve
    if not alive_ops:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace
    yesterday_bids = []
    for o in alive_ops:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    my_hp = float(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Base target bid derived from yesterday's competitive band
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        second_prev = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev

        # If Cindy/Eric-like pressure existed (very high bids), we must match/beat slightly
        if highest_prev >= 130:
            # Use a small increment over the second-highest to avoid always overpaying
            target = second_prev + 2.0
        else:
            # Moderate pressure: bid between median/high
            s = sorted(yesterday_bids)
            median = s[len(s)//2]
            target = median + 1.5
    else:
        # No trace info: default to a mid-high bid
        target = DAILY_SALARY * 0.6

    # Adjust for urgency: if we've gone many days without water, spend more
    if no_water_days >= 2:
        target *= 1.15
    elif no_water_days == 1:
        target *= 1.05

    # Adjust for low hp: bid more to secure water, but cap by budget
    if my_hp <= 2.5:
        target *= 1.25
    elif my_hp <= 4.0:
        target *= 1.12

    # Supply context: when supply is higher, we can afford slightly lower bids
    # Normalize supply to [0,1]
    if MAX_SUPPLY > MIN_SUPPLY:
        norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        norm = 0.5
    # If supply is high, reduce target a bit; if low, increase
    target *= (1.0 + (0.5 - norm) * 0.08)

    # Ensure bid is within reasonable bounds
    min_reasonable = DAILY_SALARY * 0.35
    max_reasonable = DAILY_SALARY * 0.95
    target = max(min_reasonable, min(max_reasonable, target))

    # Final cap by budget and non-negative
    bid = float(min(my_budget, target))
    if bid < 0:
        bid = 0.0

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

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return min(my_status.get('budget', 0.0), DAILY_SALARY * 0.4)

    # Read yesterday bids from immediate previous_trace only
    prev_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    # Pressure estimate: if someone previously bid very high, expect continued contest
    high_pressure = highest_prev_bid >= 0.85 * DAILY_SALARY

    # Supply-based aggressiveness: when supply is high, the marginal value of winning is lower.
    # We'll bid just enough to beat likely mid/high bids without burning budget.
    if supply >= 0.9 * MAX_SUPPLY:
        base = 0.55 * DAILY_SALARY
    elif supply <= 1.1 * MIN_SUPPLY:
        base = 0.65 * DAILY_SALARY
    else:
        base = 0.60 * DAILY_SALARY

    # If we're in danger (low hp or many no-water days), increase bid.
    if my_hp <= 2.0 or my_no_water_days >= 2:
        base = 0.85 * DAILY_SALARY
    elif my_hp <= 4.0:
        base = max(base, 0.70 * DAILY_SALARY)

    # If Cindy-like behavior suggests high contest (high_pressure), slightly raise; otherwise keep conservative.
    if high_pressure:
        base = max(base, 0.75 * DAILY_SALARY)
    else:
        base = min(base, 0.70 * DAILY_SALARY)

    # Ensure we don't exceed budget; also cap to avoid irrational overpay.
    bid = min(my_budget, base)

    # Small adaptive bump to outbid typical mid bids when we have enough budget.
    if my_budget > 0 and bid < 0.75 * DAILY_SALARY and supply >= 18.0:
        bid = min(my_budget, bid + 5.0)

    # Final safety clamp
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

    supply = day_context['supply']
    day = day_context['day']

    alive_opps = [o for o in opponents_status.values() if o.get('alive')]
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids to infer how aggressive opponents are.
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid
    else:
        highest_prev_bid = 0.0
        second_prev_bid = 0.0

    # Supply pressure: if supply is near max, competition is lower; if near min, competition is higher.
    # Map supply in [15,25] to a multiplier in [1.15, 0.85]
    if MAX_SUPPLY != MIN_SUPPLY:
        t = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        t = 0.5
    supply_mult = 1.15 - 0.30 * float(t)

    # Core policy:
    # - If our HP is low, we must secure water: bid closer to highest_prev_bid.
    # - If our HP is healthy, bid enough to stay competitive but avoid overpaying.
    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Determine target bid baseline from yesterday.
    # Use a slight undercut vs highest to avoid paying too much, unless HP is critical.
    critical = (hp <= 2.0) or (no_water_days >= 2)
    if critical:
        target = highest_prev_bid * 0.98 + 1.0
    else:
        # If others were bidding very high, still try to stay near but not exceed too much.
        if highest_prev_bid >= DAILY_SALARY * 1.1:
            target = second_prev_bid * 0.95 + 3.0
        else:
            target = max(DAILY_SALARY * 0.55, highest_prev_bid * 0.85)

    # Adjust by supply pressure.
    target = target * supply_mult

    # Cap by what we can afford.
    bid = min(budget, target)

    # Ensure we bid at least enough to matter when we have budget.
    min_reasonable = DAILY_SALARY * 0.35
    if bid < min_reasonable and budget >= min_reasonable:
        bid = min_reasonable

    # If budget is tiny, just spend what we can.
    if budget <= 0:
        return 0.0

    return float(max(0.0, bid))
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

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday bids for immediate reaction
    prev_bids = []
    prev_hp_after = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
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

    # Estimate pressure level from yesterday
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    # Base bid: aim to beat average but not chase peaks
    # Use supply to scale: with higher supply, lower competition.
    supply_mid = (MIN_SUPPLY + MAX_SUPPLY) / 2.0
    supply_factor = 1.0
    if supply > supply_mid:
        supply_factor = 0.92
    elif supply < supply_mid:
        supply_factor = 1.05

    # If someone previously bid very high, increase slightly; if my hp is low, increase more.
    pressure = 0.0
    if highest_prev_bid >= DAILY_SALARY * 1.7:
        pressure = 0.18
    elif highest_prev_bid >= DAILY_SALARY * 1.2:
        pressure = 0.10
    elif highest_prev_bid > 0:
        pressure = 0.06

    hp_boost = 0.0
    if my_hp <= 2:
        hp_boost = 0.28
    elif my_hp <= 4:
        hp_boost = 0.18
    elif my_hp <= 6:
        hp_boost = 0.10

    # Core target
    target = DAILY_SALARY * (0.66 + pressure + hp_boost) * supply_factor

    # If yesterday average was high, nudge toward it but cap below highest peak
    if avg_prev_bid > 0:
        target = max(target, avg_prev_bid * 0.92)

    # Cap: avoid runaway spending; also don't exceed budget.
    # Keep some budget for later days.
    budget_cap = my_budget * (0.55 if my_hp > 4 else 0.75)
    bid = min(target, budget_cap)

    # If supply is very low relative to requirement, ensure we bid at least a meaningful amount.
    if supply < WATER_REQ:
        bid = max(bid, DAILY_SALARY * 0.75)

    # Final clamp
    if bid < 0.0:
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

    supply = float(day_context.get('supply', MIN_SUPPLY))
    day = day_context.get('day', 0)

    budget = float(my_status.get('budget', 0.0))
    hp = float(my_status.get('hp', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Immediate reaction from yesterday trace only
    prev_bids = []
    prev_hp_after = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
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

    # Estimate how competitive the market was yesterday
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev_bid
    else:
        highest_prev_bid = DAILY_SALARY * 0.6
        second_prev_bid = highest_prev_bid

    # Supply pressure: if supply is tight, winning water is more valuable.
    # Convert supply to expected number of water units relative to requirement.
    # (We only use this for scaling; actual allocation is handled by the game.)
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Base bid: target just above mid-competitor when supply is tight.
    # If supply is ample, undercut to save budget.
    if supply_ratio < 0.35:
        target = second_prev_bid + 3.0
    elif supply_ratio < 0.7:
        target = (second_prev_bid + highest_prev_bid) / 2.0
    else:
        target = second_prev_bid - 2.0

    # Survival urgency adjustments
    # If my hp is low or I've already gone without water, I must bid more.
    if hp <= 2.0 or no_water_days >= 2:
        urgency = 1.0
    elif hp <= 4.0 or no_water_days == 1:
        urgency = 0.75
    else:
        urgency = 0.55

    # If yesterday saw very aggressive bids, slightly increase to avoid losing.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        market_factor = 0.85
    else:
        market_factor = 0.7

    bid = target * (market_factor + urgency * 0.35)

    # Clamp to reasonable range relative to budget
    # Ensure we don't exceed budget and avoid bidding near zero when alive.
    min_reasonable = DAILY_SALARY * (0.25 if hp > 4 else 0.6)
    bid = max(min_reasonable, bid)
    bid = min(bid, budget)

    # If budget is extremely low, still bid enough to have a chance.
    if budget < DAILY_SALARY * 0.3:
        bid = min(budget, DAILY_SALARY * 0.5)

    # Final safety clamp
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

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    # If we can't pay much, still try to extend survival.
    budget = float(my_status.get('budget', 0.0))
    hp = int(my_status.get('hp', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append(o)

    if not alive_opponents:
        # No contest: bid as low as possible while keeping some chance.
        return max(0.0, min(budget, DAILY_SALARY * 0.35))

    # Read yesterday bids from immediate trace only.
    prev_bids = []
    for o in alive_opponents:
        prev = o.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                prev_bids.append(float(bid))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    # If someone previously overpaid, they likely continue pressure; undercut slightly.
    very_aggressive = highest_prev_bid >= DAILY_SALARY * 1.3  # >=117

    # Base bid: aim to secure enough water without burning budget.
    # Use our hp/no_water_days to decide urgency.
    if hp <= 2 or no_water_days >= 2:
        base = DAILY_SALARY * 0.85
    elif hp <= 4 or no_water_days >= 1:
        base = DAILY_SALARY * 0.65
    else:
        base = DAILY_SALARY * 0.55

    # Adjust using yesterday aggressiveness.
    if very_aggressive:
        # Undercut the highest previous bid by a small margin.
        target = min(base, highest_prev_bid * 0.85)
    else:
        # If no one was too aggressive, slightly increase to secure allocation.
        target = max(base, DAILY_SALARY * 0.5)

    # Supply awareness: if supply is near minimum, competition is tighter -> bid a bit more.
    if supply <= 17.0:
        target *= 1.15
    elif supply >= 22.0:
        target *= 0.95

    # Ensure we don't exceed budget.
    target = max(0.0, min(float(budget), float(target)))

    # If budget is extremely low, bid whatever we can.
    if budget <= 1.0:
        return max(0.0, float(budget))

    # Final clamp: avoid wasting money far above typical scale.
    max_reasonable = DAILY_SALARY * 1.05
    if target > max_reasonable:
        target = max_reasonable

    return float(target)
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

    # Basic safety: if very low hp, bid aggressively to avoid death.
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids only from previous_trace.
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Supply-driven target: for medium supply, aim to be competitive but not maximal.
    # If supply is closer to MIN, competition matters more.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    # When supply is low, bid higher; when supply is high, bid lower.
    base_frac = 0.62 - 0.18 * supply_ratio  # ~0.62 at low supply, ~0.44 at high

    # If Cindy-like pressure existed (high previous bid), avoid matching max; bid enough to secure.
    # Use thresholds relative to DAILY_SALARY.
    if highest_prev_bid >= DAILY_SALARY * 1.55:
        # Someone is paying very high; bid moderately high to avoid being starved.
        base_frac += 0.18
    elif highest_prev_bid >= DAILY_SALARY * 0.95:
        base_frac += 0.08

    # If we've already missed water recently, increase bid.
    if no_water_days >= 2:
        base_frac += 0.18
    elif no_water_days == 1:
        base_frac += 0.08

    # If hp is critical, bid much more.
    if hp <= 2:
        base_frac = 0.95
    elif hp <= 3:
        base_frac = max(base_frac, 0.75)

    # Convert to bid, capped by budget.
    bid = budget * base_frac

    # Keep bid within reasonable bounds to avoid overspending.
    # Since daily_salary is 90, typical competitive bids are around 0.4-1.2x salary.
    min_bid = DAILY_SALARY * 0.35
    max_bid = DAILY_SALARY * 1.25
    bid = max(min_bid, min(max_bid, bid))

    # Final cap by budget.
    bid = max(0.0, min(budget, bid))

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

    supply = day_context['supply']
    day = day_context['day']

    # Alive opponents and yesterday bids
    alive_opps = [o for o in opponents_status.values() if o.get('alive')]
    if not alive_opps:
        # If alone, spend enough to cover requirement this day
        return min(my_status['budget'], DAILY_SALARY * 0.6)

    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace') or {}
        b = prev.get('bid', None)
        if b is not None:
            yesterday_bids.append(float(b))

    # If we saw aggressive behavior yesterday, match the pressure
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how many full water units are likely available relative to requirement
    # (Indices not used; safe math only.)
    supply_ratio = float(supply) / float(WATER_REQ)

    # Base bid: if supply is tight, increase willingness to pay.
    # Map supply_ratio roughly: 15/9=1.67 (tight) to 25/9=2.78 (less tight)
    if supply <= float(MIN_SUPPLY) + 0.5:
        tightness = 1.0
    elif supply >= float(MAX_SUPPLY) - 0.5:
        tightness = 0.6
    else:
        # linear interpolation between tight and less tight
        tightness = 1.0 - (float(supply) - (float(MIN_SUPPLY))) / ((float(MAX_SUPPLY) - float(MIN_SUPPLY)) + 1e-9) * 0.4

    # If someone previously bid very high, we must contest.
    # Cindy averaged ~112 with max ~126 in the trace; treat that as a strong signal.
    contest_threshold = DAILY_SALARY * 0.75  # 67.5

    # HP-based risk control: if low HP, pay more; if high HP, conserve.
    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))

    # Conservative cap to avoid bankruptcy
    # If budget is low, prioritize survival over maximizing remaining budget.
    if budget <= 0:
        return 0.0

    if highest_prev_bid >= contest_threshold:
        # Contest strongly but not necessarily equal to the maximum.
        if hp > 3:
            bid = DAILY_SALARY * 0.35 + (highest_prev_bid - contest_threshold) * 0.25
        else:
            bid = DAILY_SALARY * 0.75 + (highest_prev_bid - contest_threshold) * 0.15
    else:
        # No strong pressure: bid moderately, scaled by tightness.
        if hp > 3:
            bid = DAILY_SALARY * 0.5 * tightness
        else:
            bid = DAILY_SALARY * 0.85 * tightness

    # Ensure bid is at least enough to not be totally ignored, and at most budget.
    # Add small day-based jitter to reduce predictability.
    jitter = (float(day) % 3) * 2.0
    bid = bid + jitter

    # Final clamp
    bid = max(0.0, bid)
    bid = min(budget, bid)

    return float(bid)
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
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # If no opponents, bid to secure water efficiently
    if not alive_opps:
        # Aim for at most one unit of requirement per day
        target = min(my_status['budget'], DAILY_SALARY * 0.45)
        return max(0.0, target)

    # Read yesterday's bids from traces for immediate reaction
    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # Estimate whether others are bidding aggressively
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    # If someone was bidding extremely high yesterday, they likely overcommitted.
    # We can bid below that to win against most while conserving.
    # Cindy survived; others died. If Cindy exists and survived, her previous bid may be high.
    cindy_prev_bid = None
    for oid, o in opponents_status.items():
        if oid == 'Cindy' and o.get('alive', False):
            prev = o.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    cindy_prev_bid = float(prev.get('bid'))
                except Exception:
                    cindy_prev_bid = None

    # Supply pressure: with supply in [15,25], water is scarce. If supply is low, we must secure.
    # Approximate how many can be satisfied: floor(supply/WATER_REQ)
    # Ensure integer indices not needed; just compute.
    cap_units = int(supply // float(WATER_REQ))  # e.g., 15//9=1, 25//9=2

    # Core budget/HP risk control
    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Determine aggressiveness level
    # If we are in danger (low hp or already accumulated no-water days), bid higher.
    danger = (my_hp <= 2.0) or (no_water_days >= 2)

    # Base bid: try to be around a fraction of salary; adjust by supply and yesterday bids
    if danger:
        base = DAILY_SALARY * 0.72
    else:
        # If cap_units is 1, competition is higher -> bid more
        if cap_units <= 1:
            base = DAILY_SALARY * 0.58
        else:
            base = DAILY_SALARY * 0.48

    # Reaction to yesterday's outcomes
    # If others averaged high, we slightly underbid highest to conserve.
    # If highest_prev_bid is near salary, that implies very aggressive play; underbid.
    if highest_prev_bid > 0:
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # Underbid relative to the spike
            base = min(base, highest_prev_bid * 0.78)
        else:
            # If bids were moderate, try to be competitive
            # Use avg_prev_bid to anchor but keep under highest
            base = min(base, (avg_prev_bid * 0.95) if avg_prev_bid > 0 else base)

    # If Cindy is alive and likely strong, don't let her dominate; bid enough to contest.
    if cindy_prev_bid is not None:
        # If she bid high yesterday, we need a bit above a fraction of it to have a chance.
        if cindy_prev_bid >= DAILY_SALARY * 0.75:
            base = max(base, cindy_prev_bid * 0.62)

    # Final clamp to budget and non-negative
    bid = min(my_budget, base)
    if bid < 0.0:
        bid = 0.0

    # Small strategic floor: with low supply and not in danger, still bid a bit to avoid being shut out
    if cap_units <= 1 and not danger:
        bid = max(bid, min(my_budget, DAILY_SALARY * 0.35))

    return float(bid)
"""
