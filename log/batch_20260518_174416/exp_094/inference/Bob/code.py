# ============================================================
# Experiment: exp_094
# Agent: Bob
# Source: exp_094
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

    alive_opponents = [o for o in opponents_status.values() if o.get('alive')]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Extract yesterday bids from immediate previous_trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Determine a target bid based on opponent aggressiveness yesterday
    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])

    # Supply pressure: if supply is low, raise bid slightly to secure water.
    # Compute how many full requirements could exist.
    # Use int() for any index-like usage; here we only use arithmetic.
    supply_factor = 0.55
    if supply <= float(MIN_SUPPLY) + 0.5:
        supply_factor = 0.75
    elif supply >= float(MAX_SUPPLY) - 0.5:
        supply_factor = 0.45

    # If opponents previously bid very high, match a bit lower to beat them without overspending.
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # Thresholds relative to our daily salary.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # Aggressive opponents: bid enough to contest.
            base = DAILY_SALARY * (0.28 if my_hp > 3 else 0.65)
            # Nudge above the highest bid margin, but cap by budget.
            bid = max(base, highest_prev_bid + 2.0)
        elif highest_prev_bid >= DAILY_SALARY * 0.55:
            base = DAILY_SALARY * 0.40
            bid = max(base, highest_prev_bid + 1.0)
        else:
            # Low aggressiveness: bid to secure at least our need.
            bid = DAILY_SALARY * supply_factor
    else:
        # No trace info: conservative moderate bid.
        bid = DAILY_SALARY * supply_factor

    # Ensure we don't bid more than budget.
    bid = min(bid, my_budget)

    # If we're in danger (low hp or many no-water days), increase.
    no_water_days = int(my_status.get('no_water_days', 0))
    if my_hp <= 2.0 or no_water_days >= 2:
        bid = min(my_budget, max(bid, DAILY_SALARY * 0.75))

    # Keep bid within reasonable bounds.
    # Never exceed a bit above daily salary to avoid reckless spending.
    bid = min(bid, DAILY_SALARY * 1.05)

    # If budget is extremely low, just bid what we can.
    if my_budget <= 1.0:
        return max(0.0, my_budget)

    return float(bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Identify alive opponents and read yesterday bids
    alive_opps = []
    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {}) or {}
            b = prev.get('bid', None)
            if b is not None:
                try:
                    yesterday_bids.append(float(b))
                except Exception:
                    pass

    # If nobody alive, bid conservatively
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Use yesterday's highest bid as proxy for current competitive intensity
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
    else:
        highest_prev_bid = 0.0

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    # Estimate how many water units are likely needed/available
    # Supply is total water; each unit is WATER_REQ.
    # Use int() to avoid float-index issues.
    units_available = int(supply / float(WATER_REQ)) if WATER_REQ > 0 else 0

    # Aggression target: if others were bidding near/above salary, match closely.
    # Otherwise, slightly exceed their top bid to secure water.
    pressure_threshold = DAILY_SALARY * 0.85

    # Base bid derived from competitive pressure
    if highest_prev_bid >= pressure_threshold:
        if hp > 3:
            target = DAILY_SALARY * 0.35
        else:
            target = DAILY_SALARY * 0.95
        # Ensure we are not too low versus their observed peak
        target = max(target, highest_prev_bid + 2.0)
    else:
        # Moderate competition: bid at least around half salary or just above their peak
        target = max(DAILY_SALARY * 0.55, highest_prev_bid + 1.5)

    # Supply-aware adjustment: when supply is low in this scenario, water is scarcer -> bid higher
    # supply range is 15..25; units_available will be 1..2.
    if units_available <= 1:
        target *= 1.15
    else:
        target *= 0.98

    # Emergency conservation: if budget is tight, cap aggressively
    # Keep enough to survive future days; with 10 days total, spend fractionally.
    # no_water_days indicates how many days we already missed.
    no_water_days = float(my_status.get('no_water_days', 0.0))
    remaining_days = max(1.0, 10.0 - float(day))

    # If we've already missed many days, prioritize survival: bid up to 95% of budget
    if hp <= 2.0 or no_water_days >= 2.0:
        cap = budget * 0.95
    else:
        cap = budget * 0.65

    bid = float(min(budget, cap, target))

    # Ensure non-negative
    if bid < 0.0:
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
    day = day_context.get('day', 1)

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive.append((opp_id, opp))

    if not alive:
        return float(min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids to infer aggressiveness
    prev_bids = []
    for _, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Baseline target: secure water when tight supply / low hp
    # Supply tiers: 15-18 tight, 19-22 medium, 23-25 loose
    if supply <= 18.0:
        tier = 0
    elif supply <= 22.0:
        tier = 1
    else:
        tier = 2

    # Pressure from opponents: if someone bid very high yesterday, they likely overvalue survival
    high_prev = max(prev_bids) if prev_bids else 0.0

    # My urgency
    # If I'm already accumulating no-water days, increase bid.
    urgency = 0
    if hp <= 2:
        urgency += 2
    elif hp <= 4:
        urgency += 1
    if no_water_days >= 2:
        urgency += 1

    # Compute a bid cap based on budget and urgency
    # Keep below aggressive bids unless necessary.
    # Use int() for any potential indexing (none used here).
    if tier == 0:
        base = DAILY_SALARY * 0.65
    elif tier == 1:
        base = DAILY_SALARY * 0.55
    else:
        base = DAILY_SALARY * 0.45

    # If opponents were bidding extremely high yesterday, slightly undercut unless I'm critical.
    # Eric's low bids suggest some may not spend; don't overreact to a single high value.
    if high_prev >= DAILY_SALARY * 1.3:
        # Cindy-like behavior: raise a bit, but still try to stay cost-effective.
        base += DAILY_SALARY * 0.15

    # Urgency adjustment
    base += urgency * (DAILY_SALARY * 0.18)

    # If supply is so tight that winning likely requires more, push further.
    # Rough heuristic: if supply < 2*WATER_REQ, competition is higher.
    if supply < float(2 * WATER_REQ):
        base += DAILY_SALARY * 0.10

    # Final bid: never exceed budget
    bid = float(min(budget, base))

    # If budget is tiny, bid whatever we can.
    if bid <= 0.0:
        return 0.0

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

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    # Alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        # Conservative if alone
        return max(0, min(my_status.get('budget', 0), int(DAILY_SALARY * 0.4)))

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    # Read yesterday bids from previous_trace
    yesterday_bids = []
    yesterday_high_pressure = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', None) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                b_val = float(b)
            except Exception:
                continue
            yesterday_bids.append((oid, b_val))
            if b_val >= 0.9 * DAILY_SALARY:
                yesterday_high_pressure.append((oid, b_val))

    # Supply pressure: higher supply means water is easier to secure, so we can bid less.
    # Map supply in [15,25] to a multiplier in [1.05,0.85]
    if MAX_SUPPLY > MIN_SUPPLY:
        t = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        t = 0.5
    supply_mult = 1.05 - 0.20 * max(0.0, min(1.0, t))

    # Base bid: aim to outbid low-mid bidders but not chase Cindy too hard.
    if yesterday_bids:
        # Consider top 2 bids to gauge ceiling without overreacting.
        bids_only = [b for _, b in yesterday_bids]
        bids_only.sort()
        top_bid = bids_only[-1]
        second_top = bids_only[-2] if len(bids_only) >= 2 else bids_only[-1]

        # If someone was bidding very high (near salary), increase to avoid losing the last water.
        if yesterday_high_pressure:
            target = max(second_top + 1.0, 0.85 * DAILY_SALARY)
        else:
            # Otherwise, bid slightly above the second-highest to steal when Cindy is the only heavy bidder.
            target = min(top_bid - 1.0, second_top + 3.0)

        # If my HP is critical or I already have no-water days, be more aggressive.
        if my_hp <= 2 or my_no_water_days >= 2:
            target = max(target, 0.75 * DAILY_SALARY)

        bid = target * supply_mult
    else:
        # No trace info: use HP-driven baseline
        if my_hp <= 2 or my_no_water_days >= 2:
            bid = 0.85 * DAILY_SALARY
        else:
            bid = 0.55 * DAILY_SALARY
        bid *= supply_mult

    # Ensure integer bid and within budget.
    bid_int = int(bid)
    if my_budget <= 0:
        return 0

    # Never bid more than budget
    bid_int = min(bid_int, int(my_budget))

    # Safety floor: if we can, bid at least a small amount to avoid frequent starvation.
    if bid_int < 5 and my_budget >= 5:
        bid_int = 5

    return max(0, bid_int)
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

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    # Alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # If no opponents, bid low to conserve budget
    if not alive_opps:
        return float(min(my_status.get('budget', 0.0), DAILY_SALARY * 0.4))

    # Read yesterday bids from traces for immediate pressure estimate
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

    my_hp = my_status.get('hp', 0.0)
    my_budget = my_status.get('budget', 0.0)

    # Estimate how many water units are likely available/needed
    # (Supply is total water; water requirement is per unit need)
    # Use int() to avoid float index issues; also keep it only for scaling.
    supply_units = int(supply / float(WATER_REQ)) if WATER_REQ else 0
    if supply_units <= 0:
        supply_units = 1

    # Base aggressiveness from observed meta: survival correlated with ~90+ bids.
    # If someone bid very high yesterday, we must not underbid.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # High pressure day
        if my_hp > 3:
            target = DAILY_SALARY * 0.32
        else:
            target = DAILY_SALARY * 0.92
    else:
        # Moderate pressure day: try to beat typical survival bids without overpaying
        # Use a function of remaining budget and supply units.
        budget_pressure = 0.0
        if my_budget > 0:
            budget_pressure = min(1.0, my_budget / (DAILY_SALARY * 1.2))
        target = max(DAILY_SALARY * 0.55, highest_prev_bid + 2.0)
        # If supply units are low, increase bid; if high, decrease slightly
        if supply_units <= 1:
            target *= 1.15
        elif supply_units >= 2:
            target *= 0.95
        target *= (0.85 + 0.15 * budget_pressure)

    # If very low budget or low hp, bid up to avoid death
    if my_hp <= 2:
        target = max(target, DAILY_SALARY * 0.9)
    if my_budget <= DAILY_SALARY * 0.35:
        target = min(my_budget, max(target, DAILY_SALARY * 0.6))

    # Final cap by budget
    bid = float(min(my_budget, target))

    # Ensure bid is non-negative
    if bid < 0:
        bid = 0.0

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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = [o for o in opponents_status.values() if o.get('alive')]

    # Base safety: if we're in trouble, prioritize survival.
    if hp <= 2 or no_water_days >= 2:
        bid = min(budget, DAILY_SALARY * 0.95)
        return float(bid)

    # Read yesterday bids for immediate opponent pressure.
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    # If there was high bidding pressure yesterday, we match moderately.
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        # If someone was bidding near salary, they likely continue to contest.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # Don't overpay; stay just below typical contest level.
            bid = min(budget, DAILY_SALARY * 0.65)
            return float(bid)
        # If bids were low, we can take supply with a mid bid.
        if highest_prev_bid <= DAILY_SALARY * 0.25:
            bid = min(budget, DAILY_SALARY * 0.45)
            return float(bid)

    # Otherwise, adapt to supply level: higher supply means we can bid less.
    # supply is within [15,25].
    # Map supply to a factor in [0.55..0.35].
    if MAX_SUPPLY > MIN_SUPPLY:
        t = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        t = 0.5
    t = max(0.0, min(1.0, float(t)))
    # More supply -> lower bid.
    factor = 0.55 - 0.20 * t
    bid = min(budget, DAILY_SALARY * factor)
    # Ensure at least a minimal competitive bid when budget allows.
    min_bid = min(budget, DAILY_SALARY * 0.30)
    if bid < min_bid:
        bid = min_bid
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
    day = int(day_context['day'])

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Identify alive opponents
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    if not alive:
        return float(min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids to gauge aggressiveness
    prev_bids = []
    for oid, o in alive:
        prev = o.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            prev_bids.append(float(b))

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    # If Cindy was extreme yesterday, she likely continues pressure.
    # We specifically look at Cindy's yesterday bid if present.
    cindy_prev_bid = None
    if 'Cindy' in opponents_status and opponents_status['Cindy'].get('alive', False):
        prev = opponents_status['Cindy'].get('previous_trace', {})
        if prev and prev.get('bid', None) is not None:
            cindy_prev_bid = float(prev['bid'])

    # Base bid target: ensure we can win water when supply is not huge.
    # Supply bracket: [15,25]
    # If supply is closer to 15, competition matters more.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_ratio = 0.0 if supply_ratio < 0.0 else (1.0 if supply_ratio > 1.0 else supply_ratio)

    # Urgency: if we've already gone without water, increase bid.
    urgency = 0.0
    if no_water_days >= 2:
        urgency = 1.0
    elif no_water_days == 1:
        urgency = 0.6
    else:
        urgency = 0.25

    # HP urgency
    if hp <= 2:
        hp_factor = 1.0
    elif hp <= 4:
        hp_factor = 0.75
    else:
        hp_factor = 0.45

    # Pressure from opponent bids
    pressure = 0.0
    if cindy_prev_bid is not None:
        # Cindy bid was ~121.5 yesterday; if still alive, treat as strong pressure.
        if cindy_prev_bid >= DAILY_SALARY * 1.0:
            pressure = 0.9
        elif cindy_prev_bid >= DAILY_SALARY * 0.7:
            pressure = 0.6
        else:
            pressure = 0.35
    else:
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            pressure = 0.8
        elif highest_prev_bid >= DAILY_SALARY * 0.6:
            pressure = 0.55
        else:
            pressure = 0.35

    # Compute target bid
    # More pressure when supply is low.
    low_supply_boost = (1.0 - supply_ratio)
    target = DAILY_SALARY * (0.45 + 0.35 * urgency + 0.25 * hp_factor + 0.25 * pressure + 0.15 * low_supply_boost)

    # If Cindy was extremely high, we match partially to avoid overpaying.
    if cindy_prev_bid is not None and cindy_prev_bid >= DAILY_SALARY * 1.0:
        target = min(target, cindy_prev_bid * 0.85)

    # If my HP is very low, be willing to overmatch.
    if hp <= 2:
        target = max(target, DAILY_SALARY * 0.9)

    # Cap by budget
    bid = float(min(budget, target))

    # Ensure non-negative
    if bid < 0.0:
        bid = 0.0

    return bid
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

    # Alive opponents
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        return min(float(my_status['budget']), DAILY_SALARY * 0.4)

    # Read yesterday trace bids to infer who is pressuring
    prev_bids = []
    prev_hp_after = []
    for opp_id, opp in opponents_status.items():
        if not opp.get('alive', False):
            continue
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            prev_bids.append(float(b))
            prev_hp_after.append(float(prev.get('hp_after', 0.0)))

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])

    # Estimate today's required intensity from supply
    # More supply => we can bid less; less supply => bid more.
    if supply <= MIN_SUPPLY:
        supply_factor = 1.0
    elif supply >= MAX_SUPPLY:
        supply_factor = 0.65
    else:
        # linear interpolation between MIN_SUPPLY and MAX_SUPPLY
        supply_factor = 1.0 - (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) * 0.35

    # Identify top yesterday bidder; Cindy likely highest and still alive.
    top_bid = max(prev_bids) if prev_bids else 0.0

    # If someone was bidding extremely high yesterday, they likely secured water.
    # We can undercut to avoid overspending.
    # Target: just enough to beat the second-tier, but not chase the top.
    sorted_prev = sorted(prev_bids, reverse=True)
    second_bid = sorted_prev[1] if len(sorted_prev) > 1 else (sorted_prev[0] if sorted_prev else 0.0)

    # Base bid determined by our health/budget
    if my_hp <= 2:
        base = DAILY_SALARY * 0.85
    elif my_hp <= 4:
        base = DAILY_SALARY * 0.65
    else:
        base = DAILY_SALARY * 0.5

    # If top bidder is very aggressive, we bid around second_bid + small margin scaled by supply.
    # Otherwise, bid more confidently.
    if top_bid >= DAILY_SALARY * 0.9:
        target = (second_bid + 2.0) * supply_factor
    else:
        target = max(second_bid * 0.9 + 1.0, base * supply_factor)

    # Budget-aware cap: never bid more than we can afford
    target = min(target, my_budget)

    # Ensure we bid at least something when supply is tight and we might be at risk.
    if supply <= MIN_SUPPLY and my_hp <= 4:
        floor_bid = min(my_budget, DAILY_SALARY * 0.55)
        target = max(target, floor_bid)

    # If budget is low, bid a smaller fraction.
    if my_budget <= DAILY_SALARY * 0.25:
        target = min(my_budget, DAILY_SALARY * 0.2)

    # Final clamp
    if target < 0.0:
        target = 0.0
    return float(target)
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

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp and opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Extract yesterday bids from previous_trace for immediate reaction
    prev_bids = []
    prev_pressures = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                prev_bids.append(float(bid))
            except Exception:
                pass
        # If they were already in trouble yesterday, assume higher urgency today
        prev_hp_after = prev.get('hp_after', None)
        if prev_hp_after is not None:
            try:
                prev_pressures.append(float(prev_hp_after))
            except Exception:
                pass

    # Baseline bid target from yesterday's market
    if prev_bids:
        avg_prev = sum(prev_bids) / float(len(prev_bids))
        max_prev = max(prev_bids)
        # If market was aggressive, we try to slightly overtake mid/high bids.
        # Use a conservative overbid factor to conserve budget.
        target = avg_prev * 0.98
        # If supply is high, winning is easier; we can bid lower than max.
        # If supply is low, we increase target to avoid losing.
        if supply <= float(MIN_SUPPLY) + 1.0:
            target = max(target, avg_prev * 1.05)
        elif supply >= float(MAX_SUPPLY) - 1.0:
            target = min(target, avg_prev * 0.95)

        # If someone bid extremely high yesterday, avoid getting undercut.
        if max_prev >= DAILY_SALARY * 1.15:
            target = max(target, max_prev * 0.92)
    else:
        target = DAILY_SALARY * 0.55

    # Urgency adjustments based on my hp and no_water_days
    # If I'm close to death, bid more to secure water.
    if hp <= 2.0 or no_water_days >= 2:
        target = max(target, DAILY_SALARY * 0.85)
    elif hp <= 4.0:
        target = max(target, DAILY_SALARY * 0.65)

    # If supply is scarce, scale up; if abundant, scale down.
    # Convert supply to a scarcity factor in [0,1]
    denom = float(MAX_SUPPLY - MIN_SUPPLY)
    if denom <= 0:
        scarcity = 0.5
    else:
        scarcity = (float(MAX_SUPPLY) - supply) / denom
        if scarcity < 0.0:
            scarcity = 0.0
        if scarcity > 1.0:
            scarcity = 1.0

    target = target * (0.85 + 0.3 * scarcity)

    # Cap target to a fraction of budget to avoid bankruptcy
    # If budget is low, we must spend to survive.
    if budget <= DAILY_SALARY * 0.7:
        cap_frac = 0.95
    else:
        cap_frac = 0.7

    bid = min(budget, target * cap_frac)

    # Ensure bid is non-negative and not trivially tiny
    if bid < 0.0:
        bid = 0.0

    # If we have enough budget, keep a minimum competitive bid.
    min_competitive = DAILY_SALARY * 0.35
    if budget >= min_competitive and bid < min_competitive:
        bid = min_competitive

    return bid
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

    # Determine alive opponents and their yesterday bids
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            prev = o.get('previous_trace', {})
            bid = prev.get('bid', None)
            alive_opps.append((oid, o, bid))

    if not alive_opps:
        # If no opponents, bid just enough to keep water flowing
        target = DAILY_SALARY * 0.35
        return float(min(my_status['budget'], target))

    # Extract bids from yesterday for immediate reaction
    yesterday_bids = []
    for _, _, bid in alive_opps:
        if bid is not None:
            yesterday_bids.append(float(bid))

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    # Identify Cindy's previous bid to gauge targeted pressure
    cindy_prev_bid = None
    for oid, o, bid in alive_opps:
        if oid == 'Cindy' and bid is not None:
            cindy_prev_bid = float(bid)
            break

    # Base bid depends on my HP urgency
    hp = int(my_status['hp'])
    no_water_days = int(my_status['no_water_days'])

    # Estimate how many water units are likely needed; supply is total water pool.
    # Index-safe computations only.
    # If supply is low, competition matters more.
    supply_factor = 0.55
    if supply <= MIN_SUPPLY + 1.0:
        supply_factor = 0.85
    elif supply >= MAX_SUPPLY - 1.0:
        supply_factor = 0.50

    # If Cindy was aggressive, slightly overbid to steal share.
    # Use thresholds relative to DAILY_SALARY.
    aggressive = False
    if cindy_prev_bid is not None and cindy_prev_bid >= DAILY_SALARY * 1.6:
        aggressive = True

    # If someone already bid very high yesterday, assume they will try to maintain pressure.
    very_high_pressure = highest_prev_bid >= DAILY_SALARY * 1.8

    # Decide bid
    if hp <= 2 or no_water_days >= 2:
        # Emergency: bid to avoid death
        bid = DAILY_SALARY * (0.85 if not very_high_pressure else 0.98)
    else:
        if aggressive:
            # Cindy is likely taking most of the water; bid enough to contest.
            bid = DAILY_SALARY * (0.72 if supply_factor < 0.7 else 0.82)
        elif very_high_pressure:
            # General high competition
            bid = DAILY_SALARY * (0.62 if supply_factor < 0.7 else 0.74)
        else:
            # Moderate competition: bid around mid-range
            bid = DAILY_SALARY * (0.50 if supply_factor < 0.7 else 0.60)

    # Add a small bump if yesterday highest bid was close to our planned bid
    if highest_prev_bid > 0:
        # Bump toward just above yesterday's highest by a small margin, capped.
        bump = max(0.0, highest_prev_bid - bid)
        if bump > 0:
            bid = bid + min(15.0, bump * 0.15)

    # Keep within budget
    bid = float(min(float(my_status['budget']), float(bid)))

    # Never bid negative
    if bid < 0.0:
        bid = 0.0

    return bid
"""
