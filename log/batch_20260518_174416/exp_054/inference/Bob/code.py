# ============================================================
# Experiment: exp_054
# Agent: Bob
# Source: exp_054
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

    # Identify alive opponents
    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    # If no opponents, bid low but not zero
    if not alive_opponents:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace for immediate reaction
    yesterday_bids = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # Helper to clamp bid
    def clamp_bid(x):
        if x < 0:
            x = 0.0
        if my_status['budget'] is not None:
            x = min(float(my_status['budget']), float(x))
        return float(x)

    # Determine market pressure
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        lowest_prev_bid = min(yesterday_bids)

        # If someone bid very aggressively yesterday, they likely expect scarcity.
        aggressive_threshold = DAILY_SALARY * 0.85
        if highest_prev_bid >= aggressive_threshold:
            # If our hp is low, match more; otherwise undercut slightly.
            if float(my_status['hp']) <= 2.0:
                bid = DAILY_SALARY * 0.95
            else:
                bid = max(highest_prev_bid - 1.0, DAILY_SALARY * 0.30)

        # If bids were moderate, bid around the lower end plus a small premium
        elif highest_prev_bid >= DAILY_SALARY * 0.55:
            bid = max(lowest_prev_bid + 1.5, DAILY_SALARY * 0.50)

        # If bids were low, conserve budget and bid near requirement to secure some water
        else:
            # Target a bid that corresponds to securing water without overpaying
            # Use supply to scale slightly: higher supply -> lower bid
            supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
            if supply_factor < 0:
                supply_factor = 0.0
            if supply_factor > 1:
                supply_factor = 1.0
            # Baseline bid near half salary, reduced when supply is high
            bid = DAILY_SALARY * (0.55 - 0.20 * supply_factor)

    else:
        # No trace bids available: use conservative default based on hp
        if float(my_status['hp']) <= 2.0:
            bid = DAILY_SALARY * 0.85
        else:
            bid = DAILY_SALARY * 0.55

    # Ensure we can afford it and avoid bidding far beyond likely need
    # Convert a rough need signal: if our hp is low or no_water_days is high, bid higher.
    no_water_days = float(my_status.get('no_water_days', 0))
    if float(my_status['hp']) <= 2.0 or no_water_days >= 2.0:
        bid = max(bid, DAILY_SALARY * 0.70)

    # If supply is tight, increase bid slightly; if ample, decrease.
    # Tightness: lower supply => higher bid.
    tight_factor = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)
    if tight_factor < 0:
        tight_factor = 0.0
    if tight_factor > 1:
        tight_factor = 1.0
    bid = bid * (0.90 + 0.20 * tight_factor)

    # Final clamp
    return clamp_bid(bid)
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

    # Alive opponents only
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive'):
            alive_opps.append((oid, o))

    # If no opponents alive, bid enough to cover requirement
    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Read yesterday bids from previous_trace
    yesterday_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Estimate how many water units we may need to outlast; supply is total water this day
    # We aim for a bid level that tends to win enough allocation share.
    # Use a conservative baseline to avoid the Alex/David failure mode.
    base_bid = DAILY_SALARY * 0.55

    # If my hp is low, increase urgency.
    if my_status['hp'] is not None and my_status['hp'] <= 2:
        base_bid = DAILY_SALARY * 0.9
    elif my_status['hp'] is not None and my_status['hp'] <= 4:
        base_bid = DAILY_SALARY * 0.7

    # React to yesterday's most aggressive opponent
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If someone bid near our daily salary, they likely were fighting for survival.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # If we are healthy, still bid to secure share; if not, bid very high.
            if my_status.get('hp', 0) > 3:
                target = DAILY_SALARY * 0.65
            else:
                target = DAILY_SALARY * 0.95
        else:
            # Keep slightly above baseline and scale with observed aggressiveness
            target = max(base_bid, highest_prev_bid + 5.0)
    else:
        target = base_bid

    # Adjust for supply level: lower supply means more competition, bid a bit higher.
    # supply in [15,25]
    if supply <= 18.0:
        target *= 1.15
    elif supply >= 22.0:
        target *= 0.95

    # Budget safety: never bid more than what we can afford comfortably.
    budget = float(my_status.get('budget', 0.0))
    if budget <= 0.0:
        return 0.0

    # If we are close to running out of budget, cap bid to preserve future days.
    # Use remaining no_water_days as a proxy for urgency.
    no_water_days = int(my_status.get('no_water_days', 0))
    if no_water_days >= 3:
        # Need water soon
        cap = DAILY_SALARY * 0.95
    else:
        cap = DAILY_SALARY * 0.7

    bid = min(budget, min(cap, target))

    # Ensure bid is non-negative and not absurdly high
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Alive opponents
    alive_opps = []
    for k, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # If no one alive, bid conservatively
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace only
    prev_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate how many water units might be needed from supply
    # (Used only to calibrate aggression.)
    # With supply 15-25 and WATER_REQ=9, typically 1 unit is enough; sometimes 2.
    expected_units = int(supply / float(WATER_REQ))  # safe integer
    if expected_units < 1:
        expected_units = 1

    my_hp = int(my_status['hp'])
    my_budget = float(my_status['budget'])

    # Pressure detection: if someone already spent near salary yesterday, we counter.
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Base bid depends on supply pressure and our HP.
    # If supply is low, winning costs more relative to survival; bid slightly higher to avoid losing.
    supply_low = supply <= (MIN_SUPPLY + 0.5)

    # Aggression tiers
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # They were willing to burn money; we should match enough to secure water.
        if my_hp > 3:
            bid = DAILY_SALARY * 0.35
        else:
            bid = DAILY_SALARY * 0.95
    elif highest_prev_bid >= DAILY_SALARY * 0.55:
        bid = DAILY_SALARY * 0.55
        if supply_low:
            bid *= 1.15
    else:
        bid = DAILY_SALARY * 0.48
        if supply_low:
            bid *= 1.08

    # Small bump to beat likely midrange bids when supply allows only limited allocations.
    # Use expected_units: when supply is closer to 15, allocations are tighter.
    if expected_units == 1:
        bid += 2.5
    else:
        bid += 1.0

    # Never exceed our budget; also avoid bidding too low.
    min_reasonable = 5.0
    bid = float(min(my_budget, max(bid, min_reasonable)))

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
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        cap = min(budget, DAILY_SALARY * 0.4)
        return max(0.0, cap)

    # Extract yesterday bids from previous_trace only
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Pressure model: if someone was bidding far above typical salary, assume they will bid to secure water.
    # We counter with moderate bids unless our survival is at risk.
    tight_supply = supply <= (MIN_SUPPLY + 1.0)
    very_tight_supply = supply <= (MIN_SUPPLY + 0.2)

    # Base bid depends on our HP/no-water risk.
    if hp <= 2 or no_water_days >= 2:
        base = DAILY_SALARY * (0.85 if tight_supply else 0.65)
    elif hp <= 4 or no_water_days == 1:
        base = DAILY_SALARY * (0.65 if tight_supply else 0.50)
    else:
        base = DAILY_SALARY * (0.55 if tight_supply else 0.40)

    # If yesterday someone overbid massively, don't chase their peak; instead slightly shade upward when tight.
    if highest_prev_bid >= DAILY_SALARY * 1.5:
        if very_tight_supply:
            base = max(base, DAILY_SALARY * 0.75)
        else:
            base = max(base, DAILY_SALARY * 0.60)

    # If yesterday bids were low, we can bid near base; if bids were moderately high, nudge up.
    elif highest_prev_bid >= DAILY_SALARY * 0.9:
        base = max(base, DAILY_SALARY * (0.60 if tight_supply else 0.50))

    # Convert supply into a small adjustment: lower supply -> higher chance we need to win.
    # Use explicit int indexing safeguard via simple arithmetic only.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    # supply_ratio in [0,1]; when low, add pressure
    pressure = (1.0 - max(0.0, min(1.0, supply_ratio)))
    base = base * (1.0 + 0.25 * pressure)

    # Final cap by budget
    bid = min(budget, base)

    # Ensure non-negative
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context['supply'])
    day = day_context['day']

    # Alive opponents and immediate reaction from yesterday
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # If no one is alive, conserve
    if not alive_opps:
        return max(0.0, min(float(my_status['budget']), DAILY_SALARY * 0.35))

    # Collect yesterday bids and survival pressure proxy
    yesterday_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        if prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how many units of water likely matter this day
    # (Only for scaling; actual allocation logic is handled by the game.)
    # supply is between 15 and 25, so water units are roughly 1-2.
    water_units = int(supply / float(WATER_REQ))  # int() to satisfy index rule
    if water_units < 1:
        water_units = 1

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))

    # Determine aggressiveness from yesterday's top bid.
    # If others paid very high, they likely believe water is scarce/critical.
    # We bid to compete but not to mirror the highest.
    if highest_prev_bid >= DAILY_SALARY * 1.0:
        # High competition: bid around 0.85 of the leader, slightly above a floor.
        base = highest_prev_bid * 0.85 + 2.0
    elif highest_prev_bid >= DAILY_SALARY * 0.75:
        base = highest_prev_bid * 0.75 + 1.5
    else:
        base = max(DAILY_SALARY * 0.45, highest_prev_bid + 1.0)

    # HP-based urgency: if low hp, increase bid.
    if my_hp <= 2:
        base *= 1.25
    elif my_hp <= 4:
        base *= 1.10

    # Supply scaling: at higher supply, we can bid slightly less.
    if supply >= 22.0:
        base *= 0.90
    elif supply <= 17.0:
        base *= 1.05

    # Budget cap: never exceed budget; keep some reserve for later days.
    # Reserve more when episode day is early.
    reserve_fraction = 0.35 if day <= 4 else 0.25 if day <= 7 else 0.15
    max_affordable = max(0.0, my_budget * (1.0 - reserve_fraction))

    bid = min(max_affordable, base)

    # Ensure non-negative and at least minimal participation if budget allows
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # Baseline: decide urgency from our hp and no_water_days
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Pressure from yesterday: use immediate previous_trace bid levels
    prev_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Supply tightness: if supply closer to MIN_SUPPLY, water is scarce
    scarcity = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        scarcity = (float(MAX_SUPPLY) - supply) / (float(MAX_SUPPLY) - float(MIN_SUPPLY))
    scarcity = max(0.0, min(1.0, scarcity))

    # Target bid logic
    # If others previously bid aggressively (high highest_prev_bid), we slightly shadow rather than match fully.
    # If our hp is low, we increase to protect survival.
    urgency = 0.0
    if hp <= 2:
        urgency = 1.0
    elif hp <= 4:
        urgency = 0.7
    elif hp <= 6:
        urgency = 0.4
    else:
        urgency = 0.2

    # If we've already had several no-water days, urgency rises.
    if no_water_days >= 2:
        urgency = min(1.0, urgency + 0.25)

    # Determine a reasonable cap tied to our budget and salary.
    budget_cap = max(0.0, min(budget, DAILY_SALARY * 1.2))

    # Shadow factor based on yesterday's highest bid
    # If highest_prev_bid is very high, we don't go as high; just enough to compete.
    aggressive_market = 1.0 if highest_prev_bid >= 0.9 * DAILY_SALARY else (0.6 if highest_prev_bid >= 0.6 * DAILY_SALARY else 0.25)

    # Base bid depends on scarcity and urgency
    base = DAILY_SALARY * (0.35 + 0.35 * scarcity + 0.25 * urgency)

    # If market was aggressive, add a small increment to compete
    add = (highest_prev_bid - DAILY_SALARY * 0.5) * 0.15 if highest_prev_bid > DAILY_SALARY * 0.5 else 0.0

    bid = base + add * aggressive_market

    # Ensure we never bid above a safe fraction of our budget while still being competitive when needed
    min_bid_floor = 0.0
    if hp <= 2:
        min_bid_floor = DAILY_SALARY * 0.85
    elif hp <= 4:
        min_bid_floor = DAILY_SALARY * 0.65
    else:
        min_bid_floor = DAILY_SALARY * (0.45 + 0.2 * scarcity)

    bid = max(min_bid_floor, bid)
    bid = min(bid, budget_cap)

    # If budget is extremely low, just bid what we can
    if budget <= 1.0:
        return 0.0

    # Final clamp to non-negative
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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive.append((opp_id, opp))

    if not alive:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from traces of alive opponents
    prev_bids = []
    for opp_id, opp in alive:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict) and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # If we have data, infer pressure from the top bidder (Cindy-like behavior)
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Base bid: scale with supply scarcity (lower supply -> higher bid)
    # Normalize scarcity in [0,1]
    if MAX_SUPPLY > MIN_SUPPLY:
        scarcity = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        scarcity = 0.5
    scarcity = max(0.0, min(1.0, scarcity))

    # Target bid level: moderate, but increase if others previously bid high
    # Cindy survived with ~115 avg; Alex/David died with ~28 avg.
    # We'll sit between: enough to beat low bidders, not as high as Cindy.
    if highest_prev_bid >= DAILY_SALARY * 1.2:
        # High-pressure environment: bid closer to but still below top
        base = 0.75 * highest_prev_bid
    elif highest_prev_bid >= DAILY_SALARY * 0.7:
        base = 0.55 * highest_prev_bid
    else:
        base = DAILY_SALARY * (0.45 + 0.25 * scarcity)

    # Health urgency: if low hp or already accruing no-water days, ramp
    if my_hp <= 2.0:
        urgency_mult = 1.15
    elif my_hp <= 4.0:
        urgency_mult = 1.05
    else:
        urgency_mult = 1.0

    # If we've already gone multiple days without water, increase bid
    if my_no_water_days >= 2:
        urgency_mult *= 1.10
    if my_no_water_days >= 3:
        urgency_mult *= 1.20

    bid = base * urgency_mult

    # Ensure bid is at least enough to compete when supply is tight
    # Use supply slots estimate to avoid too-low bids.
    # Estimated number of water units available ~ supply/WATER_REQ
    units = supply / float(WATER_REQ) if WATER_REQ > 0 else 1.0
    # If units small, increase floor
    if units <= 1.7:
        bid = max(bid, DAILY_SALARY * (0.55 + 0.25 * scarcity))
    elif units <= 2.2:
        bid = max(bid, DAILY_SALARY * (0.45 + 0.15 * scarcity))

    # Budget cap and non-negative
    bid = max(0.0, min(bid, my_budget))

    # If budget is extremely low, still bid something to avoid total starvation
    if my_budget <= 1.0:
        return 0.0

    # Slightly vary with day to avoid ties (bounded)
    jitter = ((day % 5) - 2) * 1.0
    bid = max(0.0, bid + jitter)

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

    alive_opps = []
    for k, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # React to yesterday bids (only immediate trace)
    yesterday_bids = []
    yesterday_hp = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
                yesterday_hp.append(float(prev.get('hp_after', prev.get('hp', 0))))
            except Exception:
                pass

    # Estimate opponent pressure: if any opponent was near-death yesterday, raise bid.
    # Cindy died yesterday, so her typical bid (~89) is a useful anchor for how hard others pushed.
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    min_prev_hp = min(yesterday_hp) if yesterday_hp else 10.0

    # Supply-based aggressiveness: medium scenario, supply in [15,25].
    # If supply is closer to MAX, we can bid slightly less; if closer to MIN, bid more.
    supply_norm = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_norm = max(0.0, min(1.0, supply_norm))

    # Base target: beat typical mid-tier bids (~118-136) without overpaying.
    # Use highest_prev_bid as an upper reference but cap it.
    target = max(DAILY_SALARY * 0.85, 0.0)
    # If others already bid very high yesterday, we slightly undercut unless we are low HP.
    if highest_prev_bid > 0:
        # Undercut by a small margin to keep surplus, but not below Cindy-like pressure.
        target = max(target, highest_prev_bid - 10.0)

    # If we are low HP or opponents were near death, increase.
    if my_status['hp'] <= 3 or my_status['no_water_days'] >= 2 or min_prev_hp <= 1:
        target *= 1.15

    # Adjust for supply tightness: lower supply -> higher bid.
    target *= (1.08 - 0.08 * supply_norm)

    # Convert to a safe bid within budget.
    # Also ensure we don't bid above what we can afford.
    bid = min(my_status['budget'], target)

    # If budget is very small, still try to secure water if possible.
    if my_status['budget'] < DAILY_SALARY * 0.4:
        bid = min(my_status['budget'], DAILY_SALARY * 0.55)

    # Final safety cap: don't exceed 1.25*DAILY_SALARY to avoid runaway spending.
    bid = min(bid, DAILY_SALARY * 1.25)

    # Ensure bid is non-negative.
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Alive opponents and their yesterday bids
    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append(o)

    yesterday_bids = []
    for o in alive_opponents:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(float(prev['bid']))

    # Estimate competitive pressure from yesterday
    pressure = 0.0
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / float(len(yesterday_bids))
        # Normalize around typical bids; emphasize highest bidder
        pressure = 0.55 * (highest_prev_bid / (DAILY_SALARY * 1.8)) + 0.45 * (avg_prev_bid / (DAILY_SALARY * 1.8))

    # Supply regime: with higher supply, we can bid less aggressively
    # Map supply to [0,1] where 0 => MIN_SUPPLY, 1 => MAX_SUPPLY
    if MAX_SUPPLY == MIN_SUPPLY:
        supply_factor = 0.5
    else:
        supply_factor = (supply - float(MIN_SUPPLY)) / float(MAX_SUPPLY - MIN_SUPPLY)
        if supply_factor < 0.0:
            supply_factor = 0.0
        if supply_factor > 1.0:
            supply_factor = 1.0

    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Base bid: keep enough water to survive while conserving budget
    # If hp is critical or already accruing no-water days, bid harder.
    if hp <= 2 or no_water_days >= 2:
        base = DAILY_SALARY * 0.85
    elif hp <= 4:
        base = DAILY_SALARY * 0.65
    else:
        base = DAILY_SALARY * 0.55

    # Adjust for competitive pressure: if others bid high yesterday, slightly increase.
    # If supply is high, decrease a bit (less need to overbid).
    bid = base * (1.0 + 0.35 * pressure) * (1.0 - 0.25 * supply_factor)

    # Ensure we don't exceed budget
    if budget <= 0.0:
        return 0.0

    # Cap bid to a fraction of budget to avoid going broke early
    # If pressure is high, allow higher fraction.
    budget_frac = 0.55 + 0.25 * min(1.0, pressure)
    max_affordable = budget * budget_frac

    # Also keep within reasonable daily spending bounds
    upper = min(budget, DAILY_SALARY * 1.2)
    if bid > upper:
        bid = upper

    # If bid is too low, still try to secure water when supply is low.
    if supply_factor < 0.4:
        min_bid = DAILY_SALARY * 0.45
        if bid < min_bid:
            bid = min_bid

    # Final clamp
    if bid < 0.0:
        bid = 0.0
    if bid > budget:
        bid = budget

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
    day = day_context['day']

    # Alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # If alone, bid enough to cover requirement
    if not alive_opps:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.45))

    # Read yesterday bids to estimate who is aggressive
    prev_bids = []
    prev_high_bid = 0.0
    prev_second = 0.0
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                b = float(b)
            except Exception:
                continue
            prev_bids.append((oid, b))

    if prev_bids:
        # Sort by bid
        prev_bids_sorted = sorted(prev_bids, key=lambda x: x[1], reverse=True)
        prev_high_bid = prev_bids_sorted[0][1]
        prev_second = prev_bids_sorted[1][1] if len(prev_bids_sorted) > 1 else 0.0

    # Supply pressure: more supply means we can bid less and still win enough water
    # Determine how many full requirements supply can satisfy (roughly)
    # Ensure indices are ints if used; here we compute only floats.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    # Base aggressiveness from yesterday's top bid
    # Cindy survived 10 days with very high average bid, so we may need to match/just beat.
    # But avoid overpaying relative to our budget.
    target = None
    if prev_bids:
        # If someone was bidding extremely high, we try to slightly undercut them when supply is decent.
        # Use a soft cap tied to budget.
        if prev_high_bid >= DAILY_SALARY * 1.0:
            # Supply decent -> bid near high; tight -> bid lower.
            target = prev_high_bid * (0.92 + 0.06 * supply_ratio)
        else:
            # If bids were moderate, try to beat the top by a small margin.
            target = prev_high_bid + 2.0

        # If second-high is close, we can aim just above second to win at lower cost.
        if prev_second > 0 and prev_high_bid - prev_second < 10:
            target = max(target, prev_second + 1.5)
    else:
        target = DAILY_SALARY * (0.45 + 0.25 * supply_ratio)

    # Adjust for our hp: if low hp, bid more to prevent no-water days.
    if hp <= 2:
        target *= 1.25
    elif hp <= 4:
        target *= 1.10
    else:
        target *= (0.98 - 0.08 * (1.0 - supply_ratio))

    # Convert to feasible bid: never exceed budget.
    # Also keep within a reasonable range relative to daily salary.
    min_bid = 0.0
    max_reasonable = min(budget, DAILY_SALARY * (2.0 if supply_ratio > 0.6 else 1.4))
    bid = max(min_bid, min(target, max_reasonable))

    # Final safeguard: if budget is tiny, bid it all.
    if budget <= 1.0:
        return max(0.0, budget)

    return float(bid)
"""
