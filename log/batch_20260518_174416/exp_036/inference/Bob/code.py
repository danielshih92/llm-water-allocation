# ============================================================
# Experiment: exp_036
# Agent: Bob
# Source: exp_036
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    # Fallback if no opponents
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.45)

    # Read yesterday bids from previous_trace for immediate reaction
    yesterday_bids = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Determine aggressiveness threshold
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid
    else:
        highest_prev_bid = 0.0
        second_prev_bid = 0.0

    # Budget/health based urgency
    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Target bid logic
    # If opponents were bidding very high yesterday, contest more but cap by budget.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # If we're weak or have been without water, be more aggressive.
        if hp <= 2.5 or no_water_days >= 2:
            raw_bid = max(highest_prev_bid, second_prev_bid) + 1.0
            # Ensure we don't exceed our ability
            raw_bid = min(raw_bid, budget, DAILY_SALARY * 0.95)
            return max(0.0, raw_bid)
        else:
            # Outbid slightly above the next best to secure water.
            raw_bid = second_prev_bid + 1.0
            raw_bid = min(raw_bid, budget, DAILY_SALARY * 0.75)
            return max(0.0, raw_bid)

    # If bids were moderate/low, bid enough to stay competitive but avoid overpay.
    # Use supply pressure: lower supply -> higher bid.
    supply_pressure = 1.0
    if supply <= float(MIN_SUPPLY):
        supply_pressure = 1.0
    elif supply >= float(MAX_SUPPLY):
        supply_pressure = 0.6
    else:
        # linear scale between 15..25
        supply_pressure = 1.0 - (supply - float(MIN_SUPPLY)) / (float(MAX_SUPPLY) - float(MIN_SUPPLY)) * 0.4

    base_bid = DAILY_SALARY * (0.42 * supply_pressure)

    # If we have been without water, increase bid
    if no_water_days >= 1:
        base_bid *= 1.25
    if hp <= 3.0:
        base_bid *= 1.35

    # If we have a signal from yesterday highest bid, nudge above it slightly when close.
    # (Still keep under budget.)
    if highest_prev_bid > 0.0:
        # If they were bidding close to our base, we should beat them.
        if highest_prev_bid >= base_bid * 0.9:
            base_bid = highest_prev_bid + 1.0

    bid = min(budget, base_bid)
    return max(0.0, bid)
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

    supply = day_context['supply']
    day = day_context['day']

    hp = my_status['hp']
    budget = my_status['budget']

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return float(min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace for immediate reaction
    opp_prev_bids = []
    for opp_id, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid', None)
        if bid is not None:
            opp_prev_bids.append((opp_id, bid))

    highest_prev_bid = None
    top_opp_id = None
    if opp_prev_bids:
        top_opp_id, highest_prev_bid = max(opp_prev_bids, key=lambda x: x[1])

    # Estimate how many days we need to buy ourselves; bid more when HP is critical
    # Simple risk factor: if hp <= 2 (likely near death), spend to secure water.
    if hp <= 2:
        target = DAILY_SALARY * 0.85
    elif hp <= 4:
        target = DAILY_SALARY * 0.65
    else:
        target = DAILY_SALARY * 0.52

    # Exploit Cindy-like pressure: if someone bid high yesterday, slightly undercut
    # to win without matching full cost.
    if highest_prev_bid is not None:
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # Undercut by a small margin; ensure bid is still meaningful.
            target = min(target, highest_prev_bid - 3.0)
            # If our hp is low, don't undercut too much.
            if hp <= 4:
                target = max(target, highest_prev_bid - 1.5)
        else:
            # If pressure was moderate, lean into winning at a modest premium.
            target = max(target, highest_prev_bid + 2.0)

    # Supply-based adjustment: with higher supply, winning is easier; bid less.
    # Use normalized factor based on [15,25].
    supply_clamped = max(MIN_SUPPLY, min(MAX_SUPPLY, supply))
    norm = (supply_clamped - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)  # 0..1

    # When supply is high (norm close to 1), reduce bid; when low, increase.
    # This helps avoid overpaying in abundant scenarios.
    if norm >= 0.7:
        target *= 0.88
    elif norm <= 0.3:
        target *= 1.08

    # Ensure we don't bid more than budget
    bid = float(min(budget, max(0.0, target)))

    # Also avoid bidding too low: if we likely need water this day, bid at least a fraction.
    no_water_days = my_status.get('no_water_days', 0)
    if no_water_days >= 2 and bid < DAILY_SALARY * 0.35:
        bid = float(min(budget, DAILY_SALARY * 0.45))

    return bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = day_context['supply']
    # supply is float; convert for any indexing/threshold logic
    supply_int = int(supply)

    # Alive opponents
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Extract yesterday bids from previous_trace
    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid', None)
        if bid is not None:
            yesterday_bids.append(float(bid))

    # Estimate contest intensity
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Base willingness depends on supply: lower supply -> slightly higher bid
    # supply_int in [15,25]
    if supply_int <= 16:
        supply_pressure = 1.0
    elif supply_int <= 19:
        supply_pressure = 0.9
    elif supply_int <= 22:
        supply_pressure = 0.8
    else:
        supply_pressure = 0.7

    # If someone was extremely aggressive yesterday, don't mirror fully; undercut slightly.
    aggressive_threshold = DAILY_SALARY * 0.85  # 76.5

    # If our HP is low, we must secure water.
    hp = my_status.get('hp', 0)
    budget = my_status.get('budget', 0)

    # Target bid logic
    if highest_prev_bid >= aggressive_threshold:
        # Underbid relative to their peak to win at lower cost.
        target = min(DAILY_SALARY * 0.95, highest_prev_bid * 0.92)
        # If our HP is critical, increase a bit
        if hp <= 2:
            target = min(DAILY_SALARY * 1.0, target + 8.0)
    else:
        # Moderate contest: bid around mid-high of salary scaled by supply pressure.
        target = DAILY_SALARY * 0.62 * supply_pressure
        if hp <= 3:
            target = DAILY_SALARY * 0.78 * supply_pressure

    # Ensure we don't overspend beyond budget
    # Also keep a floor to avoid losing when others spend heavily.
    floor_bid = DAILY_SALARY * 0.5
    if target < floor_bid and hp > 4:
        target = floor_bid * 0.9

    return float(min(budget, max(0.0, target)))
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

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opps = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday bids to infer pressure.
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = 0.0
    if len(yesterday_bids) >= 2:
        sorted_b = sorted(yesterday_bids, reverse=True)
        second_prev_bid = sorted_b[1]

    # Safety tiers based on my HP / no-water streak.
    if my_hp <= 1 or my_no_water_days >= 2:
        hp_factor = 1.0
    elif my_hp <= 3:
        hp_factor = 0.85
    else:
        hp_factor = 0.65

    # Supply pressure: with medium scenario supply (15-25), ensure enough to avoid starvation.
    # If supply is low, raise bid aggressiveness.
    if supply <= 18:
        supply_factor = 1.0
    elif supply <= 21:
        supply_factor = 0.9
    else:
        supply_factor = 0.8

    # Exploit Cindy-like behavior: if someone previously bid extremely high, don't match it.
    # Instead, bid just above the median/second-high to likely win without overspending.
    if highest_prev_bid >= DAILY_SALARY * 1.2:
        target = max(DAILY_SALARY * 0.75, second_prev_bid + 5.0)
    else:
        target = max(DAILY_SALARY * 0.55, highest_prev_bid * 0.55 + 10.0)

    bid = target * hp_factor * supply_factor

    # Clamp to budget and avoid bidding too low.
    min_reasonable = DAILY_SALARY * 0.25
    if my_budget <= min_reasonable:
        bid = my_budget
    else:
        bid = max(min_reasonable, bid)
        bid = min(my_budget, bid)

    # Final small adjustment by day to avoid predictable ties.
    # Use day parity only (deterministic, no randomness).
    if int(day) % 2 == 0:
        bid *= 1.02
    else:
        bid *= 0.98

    # Ensure non-negative.
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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        try:
            if opp.get('alive', False):
                alive_opponents.append((opp_id, opp))
        except Exception:
            continue

    if not alive_opponents:
        return float(min(my_budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace only
    yesterday_bids = []
    for opp_id, opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Determine pressure level from yesterday
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    # Supply-aware baseline: if supply is tight near MIN, increase bid to avoid losing allocation
    # Use a simple scaling between 15 and 25.
    if MAX_SUPPLY > MIN_SUPPLY:
        tightness = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    else:
        tightness = 0.5
    tightness = max(0.0, min(1.0, tightness))

    # If we are in danger (low HP or already no-water days), prioritize survival
    if my_hp <= 2 or my_no_water_days >= 2:
        target = DAILY_SALARY * (0.85 + 0.1 * tightness)
    elif my_hp <= 3:
        target = DAILY_SALARY * (0.65 + 0.15 * tightness)
    else:
        # Match the high cluster if someone paid aggressively yesterday.
        # If highest is very high, bid slightly below it to win with less cost.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            target = min(highest_prev_bid - 2.0, DAILY_SALARY * (0.75 + 0.1 * tightness))
        else:
            # Otherwise, bid around the average of yesterday but slightly boosted for tight supply.
            target = avg_prev_bid * 0.9 + DAILY_SALARY * 0.1 + DAILY_SALARY * 0.08 * tightness

    # Convert target into a safe bid within budget
    # Also ensure bid is not trivially low when supply is tight.
    min_floor = DAILY_SALARY * (0.35 + 0.2 * tightness)
    bid = max(min_floor, target)
    bid = float(min(my_budget, bid))

    # If budget is extremely low, still bid something proportional
    if bid <= 0.0:
        bid = float(min(my_budget, DAILY_SALARY * 0.1))

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

    supply = day_context['supply']
    day = day_context['day']

    # Alive opponents and yesterday bids
    alive_opps = []
    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {}) or {}
            if prev.get('bid') is not None:
                yesterday_bids.append(prev.get('bid'))

    # If no one alive, conserve
    if not alive_opps:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.4))

    # Pressure from yesterday: if someone bid near max salary, others likely over-traded
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how many
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

    # Alive opponents
    alive_opponents = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    # If no opponents alive, conserve budget
    if not alive_opponents:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace for immediate reaction
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how many water units are likely available per winner.
    # Use supply/water_req as a rough intensity proxy.
    supply_intensity = supply / float(WATER_REQ) if WATER_REQ else 0.0

    # Base bid: aim to secure enough water without burning budget.
    # If supply is high, we can bid less; if low, bid more.
    # Clamp into a sensible band around salary fractions.
    if supply_intensity >= 2.0:
        base = DAILY_SALARY * 0.45
    elif supply_intensity >= 1.4:
        base = DAILY_SALARY * 0.60
    else:
        base = DAILY_SALARY * 0.75

    # Escalate if yesterday showed very high pressure bids.
    # If someone was bidding close to salary, competition is intense.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        if my_status['hp'] > 3:
            base = max(base, DAILY_SALARY * 0.65)
        else:
            base = max(base, DAILY_SALARY * 0.95)

    # If my hp is critical, bid more aggressively.
    if my_status['hp'] <= 2:
        base = max(base, DAILY_SALARY * 0.95)
    elif my_status['hp'] <= 4:
        base = max(base, DAILY_SALARY * 0.75)

    # If I've already had no-water days, increase urgency.
    no_water_days = int(my_status.get('no_water_days', 0) or 0)
    if no_water_days >= 2:
        base = max(base, DAILY_SALARY * 0.85)

    # Convert to final bid within budget.
    budget = float(my_status.get('budget', 0.0))
    bid = min(budget, base)

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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive.append((opp_id, opp))

    if not alive:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Read yesterday bids from previous_trace only
    prev_bids = []
    prev_hp_after = []
    for _, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass
        try:
            prev_hp_after.append(int(prev.get('hp_after', 0)))
        except Exception:
            pass

    # Estimate opponent aggressiveness from yesterday
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    lowest_prev_bid = min(prev_bids) if prev_bids else 0.0

    # Supply pressure: with supply 15~25, water allocation likely matters.
    # If supply is low, we should bid more to secure enough water for WATER_REQ needs.
    supply_tight = supply <= (MIN_SUPPLY + MAX_SUPPLY) / 2.0  # <=20

    # Core strategy: avoid the failure mode of low bids seen in dead agents.
    # Target bid depends on my hp and yesterday's observed highest bid.
    # If opponents were bidding very high yesterday, we match a fraction.
    if highest_prev_bid >= DAILY_SALARY * 1.3:  # ~117
        base = DAILY_SALARY * (0.85 if supply_tight else 0.65)
        if my_hp <= 2 or my_no_water_days >= 2:
            base *= 1.15
        # Also ensure we are not too far below the leader
        target = max(base, highest_prev_bid * 0.55)
    else:
        # If yesterday bids were moderate, still bid enough to not be the low bidder.
        base = DAILY_SALARY * (0.65 if supply_tight else 0.5)
        if my_hp <= 2 or my_no_water_days >= 2:
            base *= 1.25
        # Nudge above the lowest observed bid
        target = max(base, lowest_prev_bid + 5.0)

    # Convert target into an amount we can afford; also cap to avoid bankruptcy.
    # Assume salary-like budget replenishment; still be conservative.
    max_affordable = my_budget
    if max_affordable <= 0:
        return 0.0

    # Slightly more aggressive when hp is critical
    if my_hp <= 1:
        target *= 1.25

    bid = min(max_affordable, target)

    # Ensure bid is non-negative and not absurdly tiny
    if bid < 0.0:
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

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opponents = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    if not alive_opponents:
        return float(min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace only
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Baseline from opponent behavior
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # Use a robust notion of "typical pressure": median
        sorted_b = sorted(yesterday_bids)
        mid = len(sorted_b) // 2
        median_prev_bid = sorted_b[mid]
    else:
        highest_prev_bid = 0.0
        median_prev_bid = DAILY_SALARY * 0.5

    # If supply is scarce, we must secure water; if abundant, we can bid less.
    # Approximate number of water units available (integer) to scale aggressiveness.
    # supply is float; ensure integer indices/quantities.
    supply_units = int(round(supply / WATER_REQ))
    if supply_units < 1:
        supply_units = 1

    scarcity_factor = 1.0
    if supply_units <= 1:
        scarcity_factor = 1.25
    elif supply_units == 2:
        scarcity_factor = 1.05
    else:
        scarcity_factor = 0.9

    # Health urgency
    hp_factor = 1.0
    if hp <= 2.0:
        hp_factor = 1.35
    elif hp <= 4.0:
        hp_factor = 1.15
    elif no_water_days >= 2:
        hp_factor = 1.1

    # Strategy: bid slightly above median previous bid (to beat typical competitor),
    # but cap below highest previous bid to avoid overpaying into Cindy's peak.
    target = (median_prev_bid + 5.0) * scarcity_factor * hp_factor

    # Cap: don't exceed ~90% of the highest prior bid unless hp is critical.
    cap = highest_prev_bid * 0.9
    if hp <= 2.0:
        cap = max(cap, highest_prev_bid * 0.95)

    # Also cap by a reasonable fraction of budget to avoid running out early.
    budget_cap = budget
    if day >= 1:
        # conservative: never spend more than 65% of current budget on a single day
        budget_cap = min(budget_cap, budget * 0.65)

    bid = min(target, cap, budget_cap)

    # Ensure non-negative and at least a small amount if we need water.
    if bid < 0.0:
        bid = 0.0

    # If we are in danger of running out of water, increase floor.
    if hp <= 3.0 or no_water_days >= 3:
        min_floor = min(budget, DAILY_SALARY * 0.75)
        if bid < min_floor:
            bid = min_floor

    # If supply is high and hp is safe, allow bidding lower.
    if supply_units >= 3 and hp >= 6.0 and no_water_days == 0:
        bid = min(bid, DAILY_SALARY * 0.45)

    return float(bid)
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

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', None)

    # Alive opponents
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    # If no one else is alive, conserve
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids for immediate reaction
    prev_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            prev_bids.append(float(bid))

    # Estimate how aggressive others were
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_prev_bid = 0.0
    if len(prev_bids) >= 2:
        sorted_b = sorted(prev_bids, reverse=True)
        second_prev_bid = sorted_b[1]

    my_hp = float(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Supply pressure: closer to MAX_SUPPLY means easier to secure water
    # We still need at least WATER_REQ water to avoid losing hp.
    supply_fraction = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_fraction = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_fraction = max(0.0, min(1.0, supply_fraction))

    # Base target bid: react to highest prior bid but cap to avoid overspending.
    # Alex had very high avg; Cindy had huge budget but max bid moderate; Eric died early.
    # So we bid around a fraction of DAILY_SALARY unless others were extremely aggressive.
    if highest_prev_bid >= DAILY_SALARY * 1.15:
        # Very aggressive environment; increase bid if we are at risk
        risk_multiplier = 1.0
        if my_hp <= 2.5:
            risk_multiplier = 1.25
        elif my_hp <= 4.5:
            risk_multiplier = 1.12
        else:
            risk_multiplier = 1.05

        # Try to beat the runner-up slightly, but not too high
        target = max(second_prev_bid + 2.0, DAILY_SALARY * 0.75) * risk_multiplier
    else:
        # Moderate environment: bid enough to compete without matching top bids
        target = max(DAILY_SALARY * (0.45 + 0.25 * supply_fraction), highest_prev_bid * 0.65)

    # If we have consecutive no-water days, we must secure water more urgently
    if no_water_days >= 2:
        target *= 1.25
    elif no_water_days == 1:
        target *= 1.12

    # Ensure affordability and survival constraints
    # If budget is low, spend a larger fraction to avoid death.
    budget_pressure = 0.0
    if my_budget > 0:
        budget_pressure = my_budget / (DAILY_SALARY * 2.0)
    if budget_pressure < 0.5:
        target *= 1.05

    # Hard caps: never exceed what we can pay, and avoid extreme bids
    cap = min(my_budget, DAILY_SALARY * 1.05)
    bid = float(min(cap, max(0.0, target)))

    # If our hp is critically low, bid more aggressively (still capped)
    if my_hp <= 1.5:
        bid = float(min(my_budget, DAILY_SALARY * 1.2))

    # Final sanity
    if bid < 0.0:
        bid = 0.0
    return bid
"""
