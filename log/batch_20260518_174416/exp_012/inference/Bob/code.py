# ============================================================
# Experiment: exp_012
# Agent: Bob
# Source: exp_012
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

    # Determine alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', True):
            alive_opps.append(o)

    # If no opponents, bid modestly
    if not alive_opps:
        return float(min(my_status.get('budget', 0.0), DAILY_SALARY * 0.4))

    # Read yesterday bids from immediate previous_trace only
    prev_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Base target bid: aim to win a meaningful share without overcommitting.
    # With supply 15-25 and our requirement 9, winning around 1 unit is often critical.
    # Convert supply to an estimate of how many full requirements exist.
    est_units = int(max(0.0, (float(supply) / float(WATER_REQ))))
    # If supply is near 15, est_units=1; near 25, est_units=2.

    # Aggression adjustment from opponents' yesterday bids (if available)
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        # If they were spending near salary, be more conservative if our hp is low.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if hp > 3.0:
                bid = DAILY_SALARY * 0.30
            else:
                bid = DAILY_SALARY * 0.70
        else:
            # Slightly outbid their apparent level to secure water.
            bid = max(DAILY_SALARY * 0.45, highest_prev_bid + 1.5)
    else:
        # No trace info: choose a mid-high bid early.
        # Increase slightly if we have accumulated no-water days.
        if no_water_days >= 2:
            bid = DAILY_SALARY * 0.70
        elif no_water_days == 1:
            bid = DAILY_SALARY * 0.60
        else:
            # Earlier days: more aggressive; later days: taper.
            if int(day) <= 3:
                bid = DAILY_SALARY * 0.62
            else:
                bid = DAILY_SALARY * 0.55

    # Ensure bid is feasible given budget
    bid = float(min(budget, bid))

    # If our budget is extremely low, bid whatever we can but keep it positive
    if bid <= 0.0:
        return 0.0

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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = [o for o in opponents_status.values() if o.get('alive', True)]

    # If we have very low hp or already had waterlessness, increase urgency.
    urgency = 0
    if hp <= 2.0:
        urgency += 2
    elif hp <= 4.0:
        urgency += 1
    if no_water_days >= 1:
        urgency += 1

    # Read yesterday bids from opponents to infer competitive pressure.
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                yesterday_bids.append(float(bid))
            except Exception:
                pass

    pressure = 0.0
    if yesterday_bids:
        pressure = max(yesterday_bids)

    # Supply-based baseline: with higher supply, we can afford a bit less.
    # With lower supply, we bid more to avoid losing the allocation.
    supply_ratio = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Baseline fraction of DAILY_SALARY.
    # When supply is low, bid closer to 0.75; when high, closer to 0.55.
    base_frac = 0.75 - 0.20 * supply_ratio

    # If yesterday pressure was high (Alex/Eric aggressive), match moderately.
    # If pressure was low, keep base.
    if pressure >= 0.9 * DAILY_SALARY:
        base_frac += 0.08
    elif pressure >= 0.75 * DAILY_SALARY:
        base_frac += 0.04

    # Convert urgency to additional bidding.
    base_frac += 0.07 * urgency

    # Day 1-3: slightly more aggressive to secure early survival.
    if day <= 3:
        base_frac += 0.03

    # Clamp bidding to a reasonable band.
    bid_target = DAILY_SALARY * base_frac
    bid_floor = DAILY_SALARY * 0.35
    bid_cap = DAILY_SALARY * 0.95
    if bid_target < bid_floor:
        bid_target = bid_floor
    if bid_target > bid_cap:
        bid_target = bid_cap

    # Ensure we never bid more than our budget.
    bid = min(budget, bid_target)

    # If budget is tiny, still try to bid something proportional.
    if bid <= 0.0:
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
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        # If no one else is alive, bid low to save budget.
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace only.
    yesterday_bids = []
    yesterday_info = []
    for opp_id, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                b = float(prev.get('bid'))
                yesterday_bids.append(b)
                yesterday_info.append((opp_id, b, prev))
            except Exception:
                pass

    # Pressure signals from yesterday.
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_highest = 0.0
    if len(yesterday_bids) >= 2:
        sorted_b = sorted(yesterday_bids, reverse=True)
        second_highest = float(sorted_b[1])

    # Estimate how many water units are likely needed this day.
    # If supply is tight, increase bid to avoid no-water streak.
    supply_units = max(0.0, supply / float(WATER_REQ))
    tight_supply = supply_units < 2.0  # supply < 18 roughly

    # Base bid tied to my health and no-water streak.
    if hp <= 2 or no_water_days >= 2:
        base = DAILY_SALARY * 0.9
    elif hp <= 4 or no_water_days == 1:
        base = DAILY_SALARY * 0.65
    else:
        base = DAILY_SALARY * 0.5

    # React to opponent aggression from yesterday.
    # If someone bid near/above my salary, assume they will keep pressure.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Match enough to contest, but not fully commit.
        if hp > 3:
            target = max(base, min(DAILY_SALARY * 0.75, highest_prev_bid - 5.0))
        else:
            target = max(base, min(DAILY_SALARY * 0.95, highest_prev_bid))
    elif highest_prev_bid >= DAILY_SALARY * 0.55:
        # Moderate contest.
        target = max(base, min(DAILY_SALARY * 0.6, highest_prev_bid - 2.0))
    else:
        # If bids were low, take advantage with a slightly higher value bid.
        if tight_supply:
            target = max(base, DAILY_SALARY * 0.6)
        else:
            target = max(base, DAILY_SALARY * 0.48)

    # Budget-aware cap.
    # Also ensure we don't overbid beyond what we can sustain.
    # Use remaining budget as a soft cap.
    max_reasonable = min(budget, DAILY_SALARY * 1.05)
    bid = max(0.0, min(target, max_reasonable))

    # Ensure bid is at least small positive if we are in danger.
    if hp <= 1 and bid < DAILY_SALARY * 0.6:
        bid = min(budget, DAILY_SALARY * 0.85)

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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Gather alive opponents and their yesterday bids
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    if not alive:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    prev_bids = []
    prev_hp_after = []
    for oid, o in alive:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev.get('bid', 0.0)))
            prev_hp_after.append(float(prev.get('hp_after', o.get('hp', 0.0))))

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    # Estimate how many units of water are likely needed this day
    # (We only use supply to calibrate aggressiveness; exact allocation is handled by game engine.)
    # target_units is 1 when supply < 18, otherwise 2; keep it conservative.
    if supply < 18.0:
        target_units = 1
    else:
        target_units = 2

    # Base bid: aim to secure at least 1 unit without matching extreme overbids
    # Use a fraction of salary; adjust with yesterday's pressure.
    pressure = 0.0
    if highest_prev_bid > 0:
        pressure = min(1.0, highest_prev_bid / (DAILY_SALARY * 1.35))

    # If opponents were bidding extremely high yesterday, we must not be too low.
    if highest_prev_bid >= DAILY_SALARY * 1.25:
        base = DAILY_SALARY * (0.55 + 0.25 * pressure)
    elif highest_prev_bid >= DAILY_SALARY * 0.85:
        base = DAILY_SALARY * (0.45 + 0.20 * pressure)
    else:
        base = DAILY_SALARY * (0.35 + 0.15 * pressure)

    # If our hp is low, we should bid more aggressively to avoid cascading death.
    my_hp = float(my_status['hp'])
    if my_hp <= 1.5:
        base *= 1.25
    elif my_hp <= 3.0:
        base *= 1.10

    # If our budget is low relative to salary, reduce risk.
    my_budget = float(my_status['budget'])
    if my_budget < DAILY_SALARY * 0.6:
        base *= 0.75

    # Calibrate with supply: higher supply -> can bid slightly less while still winning.
    if supply >= 22.0:
        base *= 0.92
    elif supply <= 16.0:
        base *= 1.05

    # Final bid: also ensure we don't exceed budget.
    bid = min(my_budget, base)

    # Micro-adjust using yesterday average bid: if we were likely underbidding, bump a bit.
    if avg_prev_bid > 0:
        if bid < avg_prev_bid * 0.9 and my_hp > 2.0:
            bid = min(my_budget, avg_prev_bid * 0.95)

    # If our no_water_days is high, bid more to prevent death spiral.
    no_water_days = int(my_status.get('no_water_days', 0))
    if no_water_days >= 2:
        bid = min(my_budget, bid * 1.15)

    # Keep bid within a reasonable range.
    # (Game engine likely accepts any float, but we cap for safety.)
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
    day = int(day_context['day'])

    # Determine alive opponents and analyze yesterday bids
    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    if not alive_opponents:
        # If no one else is alive, spend conservatively to maintain budget
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.4))

    # Collect yesterday bids from previous_trace
    yesterday_bids = []
    yesterday_pressured = []  # (bid, hp_after if available)
    for opp in alive_opponents:
        prev = opp.get('previous_trace', None)
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    b_val = float(b)
                    yesterday_bids.append(b_val)
                    hp_after = prev.get('hp_after', None)
                    if hp_after is not None:
                        yesterday_pressured.append((b_val, float(hp_after)))
                except Exception:
                    pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Map supply to expected competition level (higher supply => less need to overbid)
    # Ensure indices are int-safe
    supply_band = int(0)
    if supply <= float(MIN_SUPPLY):
        supply_band = 0
    elif supply >= float(MAX_SUPPLY):
        supply_band = 2
    else:
        supply_band = 1

    # Base bid target as fraction of daily salary, adjusted by HP and supply
    # If my HP is low, bid more aggressively.
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    # Supply adjustment: at low supply, competition likely higher
    supply_fracs = [0.62, 0.52, 0.45]
    base_frac = supply_fracs[int(supply_band)]

    # If opponents bid extremely high yesterday, they likely valued survival and may continue.
    # Use thresholds relative to DAILY_SALARY.
    if highest_prev_bid >= DAILY_SALARY * 3.0:
        # Very aggressive opponent(s) yesterday
        if hp > 3.0:
            target = DAILY_SALARY * (0.75 if supply_band == 0 else 0.65)
        else:
            target = DAILY_SALARY * 0.95
    elif highest_prev_bid >= DAILY_SALARY * 1.5:
        # Moderate-high aggression
        if hp > 3.0:
            target = DAILY_SALARY * (0.62 if supply_band == 0 else 0.55)
        else:
            target = DAILY_SALARY * 0.85
    else:
        # No strong evidence of extreme bidding; keep steady
        if hp > 3.0:
            target = DAILY_SALARY * base_frac
        else:
            target = DAILY_SALARY * (base_frac + 0.25)

    # Ensure we don't bid more than budget; also avoid bidding too low when HP is critical
    no_water_days = int(my_status['no_water_days'])

    # If close to death, push harder
    if hp <= 1.5 or no_water_days >= 2:
        target = max(target, DAILY_SALARY * 0.9)

    # Small anti-overspend: if budget is low, cap to budget
    bid = min(budget, float(target))

    # Never bid negative
    if bid < 0.0:
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

    # Alive opponents
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    # If no one else is alive, conserve
    if not alive:
        return max(0.0, min(float(my_status['budget']), DAILY_SALARY * 0.35))

    # Read yesterday bids from previous_trace
    yesterday_bids = []
    top_prev = []
    for oid, o in alive:
        prev = o.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                bval = float(b)
                yesterday_bids.append((oid, bval))
            except Exception:
                pass

    # Baseline pressure from yesterday
    if yesterday_bids:
        # highest and second highest previous bids among alive
        bids_only = [b for _, b in yesterday_bids]
        highest_prev_bid = max(bids_only)
        sorted_bids = sorted(bids_only, reverse=True)
        second_prev_bid = sorted_bids[1] if len(sorted_bids) > 1 else sorted_bids[0]
    else:
        highest_prev_bid = 0.0
        second_prev_bid = 0.0

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])

    # Estimate how many water units are likely needed today.
    # If supply is close to WATER_REQ, a single winning allocation matters.
    # If supply is higher, competition is more likely but we still only need 1 unit.
    units_available = max(1, int(supply / float(WATER_REQ)))
    # Competitive factor: lower supply means fewer units -> higher bids likely.
    supply_competitive = (float(MAX_SUPPLY) - supply) / float(MAX_SUPPLY - MIN_SUPPLY + 1e-9)
    supply_competitive = max(0.0, min(1.0, supply_competitive))

    # If any opponent previously bid very high, they likely value survival; we must respond.
    # Use thresholds relative to DAILY_SALARY.
    high_bid_threshold = DAILY_SALARY * 1.05
    very_high_bid_threshold = DAILY_SALARY * 1.35

    # Decide target bid anchored to yesterday top.
    if highest_prev_bid >= very_high_bid_threshold:
        # Cindy-like behavior: push close to top but not necessarily exceed.
        target = max(second_prev_bid + 2.0, DAILY_SALARY * (0.75 + 0.25 * supply_competitive))
    elif highest_prev_bid >= high_bid_threshold:
        target = max(second_prev_bid + 1.0, DAILY_SALARY * (0.65 + 0.20 * supply_competitive))
    else:
        # Moderate competition: bid enough to avoid running out, but conserve.
        # If low HP, bid more aggressively.
        if my_hp <= 2.0:
            target = DAILY_SALARY * (0.90 + 0.10 * supply_competitive)
        elif my_hp <= 4.0:
            target = DAILY_SALARY * (0.70 + 0.15 * supply_competitive)
        else:
            target = DAILY_SALARY * (0.55 + 0.10 * supply_competitive)

    # Convert target into a feasible bid
    # Also consider remaining days: earlier in episode should secure water; later can conserve.
    day_factor = 1.0
    if day >= 8:
        day_factor = 0.85
    elif day <= 2:
        day_factor = 1.05

    bid = target * day_factor

    # Hard cap by budget
    bid = max(0.0, min(my_budget, bid))

    # If budget is extremely low, still try a minimal bid to avoid death spiral.
    if my_budget < DAILY_SALARY * 0.2:
        bid = min(my_budget, DAILY_SALARY * 0.25)

    return float(bid)
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
    day = day_context['day']

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Extract yesterday bids (immediate reaction only)
    yesterday_bids = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Pressure estimate from yesterday
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = 0.0
    if len(yesterday_bids) >= 2:
        sorted_bids = sorted(yesterday_bids, reverse=True)
        second_prev_bid = float(sorted_bids[1])

    # Determine how urgent water is for me
    # If I'm already accumulating no-water days, I must secure water.
    urgent = (no_water_days >= 2) or (hp <= 2.5)

    # Estimate how many water units might be needed this day.
    # Supply is in [15,25]; with WATER_REQ=9, at most 2 units are feasible.
    # Use this to decide how competitive to be.
    max_units = int(supply / float(WATER_REQ))  # safe int conversion
    if max_units < 1:
        max_units = 1

    # Base bid policy: avoid overpaying unless urgent or yesterday showed extreme aggression.
    # Use highest_prev_bid to infer their willingness to pay.
    if urgent:
        # Bid to beat at least typical aggressive level but cap by budget.
        target = max(DAILY_SALARY * 0.75, second_prev_bid + 3.0)
        # If yesterday had very high bids, raise slightly.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            target = max(target, highest_prev_bid * 0.85)
    else:
        # Non-urgent: bid around a fraction of salary, adjusted by yesterday pressure.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # They are paying a lot; bid just above second tier.
            target = max(DAILY_SALARY * 0.45, second_prev_bid + 1.5)
        else:
            # Gentle participation.
            target = DAILY_SALARY * 0.5

        # If supply likely allows multiple winners, we can bid lower.
        if max_units >= 2:
            target *= 0.85

    # Ensure target is within budget and non-negative.
    target = max(0.0, float(target))
    bid = min(budget, target)

    # If budget is extremely low, still try to secure water when urgent.
    if budget <= DAILY_SALARY * 0.15:
        if urgent:
            bid = min(budget, DAILY_SALARY * 0.3)
        else:
            bid = min(budget, DAILY_SALARY * 0.12)

    return float(bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Identify alive opponents and extract yesterday bids
    alive_opps = []
    yesterday_bids = []
    for oid, o in opponents_status.items():
        if o.get('alive'):
            alive_opps.append(o)
            prev = o.get('previous_trace', {}) or {}
            b = prev.get('bid', None)
            if b is not None:
                try:
                    yesterday_bids.append(float(b))
                except Exception:
                    pass

    # If no alive opponents, bid conservatively
    if not alive_opps:
        return max(0.0, min(float(my_status['budget']), DAILY_SALARY * 0.4))

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # React to yesterday's maximum pressure
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Base target: ensure some chance at getting water when supply is near/above requirement
    # With supply in [15,25], water allocation likely depends on relative bids.
    # We choose a mid-high bid to beat typical opponents without matching the top bidder.
    if hp <= 2 or no_water_days >= 2:
        # Critical: spend to secure water
        target = DAILY_SALARY * 0.9
    else:
        # Non-critical: adjust based on observed pressure
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # Someone was bidding very aggressively; counter with strong but not maximum
            target = min(DAILY_SALARY * 0.75, highest_prev_bid * 0.85)
        else:
            # Typical pressure: bid enough to stay competitive
            target = max(DAILY_SALARY * 0.55, highest_prev_bid * 0.7)

    # Scale slightly with supply: higher supply reduces need for extreme bidding
    # supply ~15 => more scarce; supply ~25 => less scarce
    scarcity = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)  # 0..1
    target = target * (0.9 + 0.2 * scarcity)

    # Budget cap
    bid = min(budget, target)

    # Ensure non-negative
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
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from immediate previous_trace
    prev_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    top_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate how many water units are available (integer count)
    # supply is float; compute integer units safely
    units = int(supply / float(WATER_REQ)) if WATER_REQ > 0 else 0
    # If supply is low, competition is harsher; bid slightly higher.
    low_supply = supply <= float(MIN_SUPPLY) + 0.5

    # Urgency factor from my hp and consecutive no-water days
    urgency = 0.0
    if hp <= 1:
        urgency = 1.0
    elif hp == 2:
        urgency = 0.85
    elif hp == 3:
        urgency = 0.65
    else:
        urgency = 0.45

    if no_water_days >= 2:
        urgency = max(urgency, 0.9)

    # Base bid: try to stay competitive against the highest yesterday bidder,
    # but do not overpay when my hp is healthy.
    # Aim: slightly above top_prev_bid when urgency is high; otherwise around mid-high.
    if top_prev_bid > 0:
        if urgency >= 0.8:
            target = top_prev_bid + (DAILY_SALARY * 0.05)
        else:
            target = max(top_prev_bid * 0.85, DAILY_SALARY * 0.55)
    else:
        target = DAILY_SALARY * 0.55

    if low_supply and urgency < 0.8:
        target = max(target, DAILY_SALARY * 0.65)

    # If I have very low hp, push closer to budget cap.
    if hp <= 2:
        target = max(target, DAILY_SALARY * (0.75 + 0.15 * (1 - hp)))

    # Cap by budget and keep within plausible range
    # Also ensure non-negative
    cap = budget
    if cap <= 0:
        return 0.0

    bid = min(cap, target)

    # If units are 0 (supply < WATER_REQ), any bid likely loses; still bid minimal to preserve budget.
    if units <= 0:
        bid = min(bid, DAILY_SALARY * 0.25)

    # Final safety clamp
    if bid < 0:
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Identify alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # If no opponents, bid conservatively
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from immediate previous_trace only
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Pressure estimate: how aggressive others were yesterday
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Base bid depends on supply: higher supply means we can bid slightly less while still staying competitive
    # Normalize supply into [0,1]
    denom = (MAX_SUPPLY - MIN_SUPPLY)
    if denom <= 0:
        s_norm = 0.5
    else:
        s_norm = (supply - MIN_SUPPLY) / denom
        if s_norm < 0.0:
            s_norm = 0.0
        if s_norm > 1.0:
            s_norm = 1.0

    # Convert supply into a rough expected water share pressure.
    # At supply ~15, water is scarce; at 25, less scarce.
    scarcity = 1.0 - s_norm

    # My urgency: low hp => bid harder to avoid death spiral
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    # If opponents were bidding near salary yesterday, they likely secured water; match more aggressively.
    # Cindy survived with moderate bids; Alex died with high bids -> both indicate bidding matters.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Match/contest
        if hp > 3:
            target = DAILY_SALARY * (0.35 + 0.25 * scarcity)
        else:
            target = DAILY_SALARY * (0.85 + 0.1 * scarcity)
    else:
        # Otherwise, bid enough to not be the low bidder (avoid Eric-like early death)
        if hp <= 2:
            target = DAILY_SALARY * (0.75 + 0.15 * scarcity)
        else:
            target = DAILY_SALARY * (0.50 + 0.25 * scarcity)

    # Also consider how many days I can survive without water; if already low, bid higher.
    try:
        no_water_days = int(my_status.get('no_water_days', 0))
    except Exception:
        no_water_days = 0
    if no_water_days <= 1:
        target *= 1.15

    # Ensure we don't exceed budget; also keep a floor to avoid going too low.
    # Floor chosen to be meaningfully above typical low bids.
    floor_bid = DAILY_SALARY * (0.35 + 0.1 * scarcity)
    bid = float(max(floor_bid, target))

    if budget <= 0:
        return 0.0
    if bid > budget:
        bid = budget

    # Safety: bid cannot be negative
    if bid < 0.0:
        bid = 0.0

    return float(bid)
"""
