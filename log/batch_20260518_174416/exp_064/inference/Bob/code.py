# ============================================================
# Experiment: exp_064
# Agent: Bob
# Source: exp_064
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

    # Basic sanity
    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    my_budget = float(my_status.get('budget', 0.0))
    my_hp = float(my_status.get('hp', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append((opp_id, o))

    # Budget guard
    def clamp_bid(x):
        if x < 0:
            return 0.0
        if my_budget <= 0:
            return 0.0
        return float(min(my_budget, x))

    # If no opponents, bid enough to satisfy need but don't waste
    if not alive_opponents:
        target = min(my_budget, DAILY_SALARY * 0.55)
        return clamp_bid(target)

    # Read yesterday bids from previous_trace only
    prev_bids = []
    prev_high = None
    for opp_id, o in alive_opponents:
        prev = o.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                prev_bids.append(float(bid))
            except Exception:
                pass

    if prev_bids:
        prev_high = max(prev_bids)
    else:
        prev_high = None

    # Determine urgency from my HP / no-water streak
    urgent = (my_hp <= 2.0) or (my_no_water_days >= 2)

    # Estimate how tight the market is today
    # If supply is low, we should bid more to secure allocation.
    # Use normalized pressure in [0,1].
    if MAX_SUPPLY == MIN_SUPPLY:
        pressure = 0.5
    else:
        pressure = (supply - float(MIN_SUPPLY)) / float(MAX_SUPPLY - MIN_SUPPLY)
    pressure = max(0.0, min(1.0, pressure))
    tightness = 1.0 - pressure

    # Core strategy:
    # - If opponent(s) overbid yesterday near salary, we slightly undercut.
    # - If they bid low, bid moderately based on tightness.
    if prev_high is not None:
        # threshold near daily salary
        high_bid_threshold = DAILY_SALARY * 0.85
        if prev_high >= high_bid_threshold:
            # Match pressure but avoid extreme spending
            base = DAILY_SALARY * (0.25 if not urgent else 0.55)
            # If supply is tight, increase
            base = base * (0.7 + 0.6 * tightness)
            # Slightly below the previous high to reduce overpay
            bid = min(base, prev_high - 1.0)
            # Ensure we still react when urgent
            if urgent and bid < DAILY_SALARY * 0.35:
                bid = DAILY_SALARY * 0.45
            return clamp_bid(bid)
        else:
            # Opponents were not desperate; bid to secure our need
            # Convert need into a rough bid fraction; keep within budget.
            # Higher tightness => higher bid.
            need_fraction = float(WATER_REQ) / float(MAX_SUPPLY)
            bid = DAILY_SALARY * (0.35 + 0.45 * tightness + 0.25 * need_fraction)
            if urgent:
                bid = bid * 1.25
            # If their previous high was meaningful, nudge upward slightly
            bid = max(bid, prev_high * 0.85)
            return clamp_bid(bid)

    # Fallback if no previous bids parsed
    bid = DAILY_SALARY * (0.4 + 0.45 * tightness)
    if urgent:
        bid = DAILY_SALARY * 0.75
    return clamp_bid(bid)
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

    # Identify alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive'):
            alive_opps.append((oid, o))

    # If no opponents, bid just enough to secure water
    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Use yesterday's immediate traces to infer aggressive bidding level
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            prev_bids.append(float(b))

    # Estimate today's supply pressure: lower supply => higher chance of being contested
    # supply in [15,25] with WATER_REQ=9 implies about 1-2 units per day; tight when closer to 15.
    tightness = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        tightness = (float(MAX_SUPPLY) - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    tightness = max(0.0, min(1.0, tightness))

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])

    # Determine target bid band from yesterday
    # Survivors likely bid enough; Cindy died with low avg bid, so avoid low bids.
    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / float(len(prev_bids))
    else:
        highest_prev = DAILY_SALARY
        avg_prev = DAILY_SALARY

    # Base strategy:
    # - If our hp is low, bid to secure water.
    # - If yesterday's highest bids were high, match/beat them slightly.
    # - Otherwise, bid near the average with a tightness adjustment.
    if my_hp <= 2.5:
        # Critical: bid aggressively but capped by budget
        target = max(highest_prev * 0.95, avg_prev * 1.05)
        target = target + 0.5 + 10.0 * tightness
    else:
        # Healthy: be competitive but not maximal
        # If highest_prev indicates an arms race, slightly undercut.
        if highest_prev >= DAILY_SALARY * 1.2:
            target = avg_prev * 1.02 + 8.0 * tightness
        else:
            target = max(avg_prev * 0.95, DAILY_SALARY * 0.6) + 6.0 * tightness

    # Ensure we don't exceed what we can pay
    target = min(target, my_budget)

    # Also avoid bidding trivially low; dying opponent suggests low bids are risky.
    floor_bid = DAILY_SALARY * 0.45
    if target < floor_bid:
        target = min(my_budget, floor_bid)

    # Final guard: if budget is extremely small, bid whatever remains
    if my_budget <= 1.0:
        return my_budget

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

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace only
    prev_bids = []
    prev_by_id = {}
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                bid_val = float(bid)
            except Exception:
                bid_val = None
            if bid_val is not None:
                prev_bids.append(bid_val)
                prev_by_id[oid] = bid_val

    # Identify key pressure opponent (highest bid yesterday)
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate how many water units we can reasonably target given supply
    # (We just use it to scale aggressiveness; actual allocation is market-based.)
    # supply is in [15,25], WATER_REQ=9 => about 1 unit per day.
    approx_units = int(supply / float(WATER_REQ)) if WATER_REQ > 0 else 1
    if approx_units < 1:
        approx_units = 1

    # Base bid depends on our survival risk
    # If we're close to death, bid harder.
    if hp <= 2 or no_water_days >= 3:
        risk_mult = 1.0
    elif hp <= 4:
        risk_mult = 0.75
    else:
        risk_mult = 0.55

    # Contest logic vs Cindy/Alex behavior (using yesterday trace only)
    # If someone bid very high yesterday, we slightly outbid to prevent them from securing water.
    # If highest_prev_bid is moderate, we bid around a mid-level to conserve budget.
    if highest_prev_bid >= DAILY_SALARY * 1.7:  # ~153
        # Cindy-like pressure: bid moderately above typical high pressure
        target = highest_prev_bid * 0.85 + 10.0
    elif highest_prev_bid >= DAILY_SALARY * 0.9:  # ~81
        target = highest_prev_bid * 0.65 + 20.0
    else:
        target = max(DAILY_SALARY * 0.45, highest_prev_bid + 5.0)

    # Scale with supply scarcity: lower supply => slightly higher bid
    scarcity = 1.0
    if supply <= float(MIN_SUPPLY) + 0.5:
        scarcity = 1.12
    elif supply >= float(MAX_SUPPLY) - 0.5:
        scarcity = 0.95

    bid = target * risk_mult * scarcity

    # Budget cap: never bid more than we can afford.
    # Also ensure we keep some budget for later if we're not in danger.
    if hp > 4 and no_water_days < 2:
        keep_fraction = 0.25
    else:
        keep_fraction = 0.05

    max_affordable = max(0.0, budget * (1.0 - keep_fraction))
    bid = min(bid, max_affordable)

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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opponents = []
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday bids from immediate previous_trace only
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace') or {}
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
        second_prev_bid = float(sorted_b[1])

    # Supply pressure: higher supply reduces need to outbid
    # Normalize supply into [0,1]
    if MAX_SUPPLY == MIN_SUPPLY:
        supply_factor = 0.5
    else:
        supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
        if supply_factor < 0.0:
            supply_factor = 0.0
        if supply_factor > 1.0:
            supply_factor = 1.0

    # Base aggressiveness: aim to beat typical top bids only when necessary
    # If yesterday highest bid was very high, opponents likely contest harder today.
    contest_mode = highest_prev_bid >= (DAILY_SALARY * 0.9)

    # If my HP is critical, bid harder regardless of supply.
    # Also if I've already had several no-water days, increase urgency.
    urgency = 0.0
    if hp <= 2.0:
        urgency += 1.0
    if no_water_days >= 2:
        urgency += 0.6
    if hp <= 4.0:
        urgency += 0.4

    # Target bid construction
    # - In low supply (supply_factor low), slightly higher bids.
    # - In high supply, bid lower.
    # - If contest_mode, try to slightly undercut the likely highest bidder rather than chase max.
    if contest_mode:
        # Try to be competitive but not maximal: just above second-highest (or a fraction of highest)
        target = max(DAILY_SALARY * (0.55 + 0.25 * (1.0 - supply_factor)),
                     (second_prev_bid + 1.0) if second_prev_bid > 0.0 else (highest_prev_bid * 0.75))
    else:
        target = max(DAILY_SALARY * (0.45 + 0.25 * (1.0 - supply_factor)),
                     (second_prev_bid + 0.5) if second_prev_bid > 0.0 else (DAILY_SALARY * 0.5))

    # Apply urgency boost
    if urgency >= 1.0:
        target = max(target, DAILY_SALARY * 0.9)
    elif urgency >= 0.6:
        target = max(target, DAILY_SALARY * 0.75)
    elif urgency >= 0.4:
        target = max(target, DAILY_SALARY * 0.65)

    # Budget safety: never exceed budget
    # Also avoid spending too much early if not urgent
    spend_cap = budget
    if urgency < 0.6 and day <= 5:
        spend_cap = min(spend_cap, DAILY_SALARY * 0.65)

    bid = min(spend_cap, target)

    # Ensure non-negative
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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    # If no opponents, just buy enough to stay alive.
    if not alive_opps:
        target = WATER_REQ if supply >= WATER_REQ else supply
        return float(min(budget, max(0.0, target)))

    # Read yesterday bids to infer aggressiveness.
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
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    # Determine our needed urgency.
    urgency = 0.0
    if hp <= 2:
        urgency += 0.9
    elif hp <= 4:
        urgency += 0.6
    elif hp <= 6:
        urgency += 0.3

    if no_water_days >= 2:
        urgency += 0.6
    elif no_water_days == 1:
        urgency += 0.3

    # Supply pressure: when supply is low, water is scarce; bid more.
    supply_ratio = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    scarce_factor = 1.0 - max(0.0, min(1.0, supply_ratio))  # 1 when low supply

    # Base bid: aim to be competitive but not match extreme bids.
    # Cindy's ~112.5 suggests others can go high; we use a fraction of that.
    if highest_prev_bid >= DAILY_SALARY * 1.0:
        base = max(avg_prev_bid * 0.6, highest_prev_bid * 0.45)
    else:
        base = max(avg_prev_bid * 0.55, DAILY_SALARY * 0.5)

    # Adjust by urgency and scarcity.
    bid = base * (1.0 + 0.9 * urgency * 0.6 + 0.8 * scarce_factor)

    # Keep within budget and avoid overbidding when budget is tight.
    # Also cap to ~1.2x salary to reduce variance.
    cap = max(0.0, min(budget, DAILY_SALARY * 1.2))
    bid = min(bid, cap)

    # If budget is very low, bid what we can.
    if budget <= 0.0:
        return 0.0

    # Ensure non-negative.
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opponents = [o for o in opponents_status.values() if o.get('alive', True)]
    if not alive_opponents:
        return max(0.0, min(budget, DAILY_SALARY * 0.35))

    # Extract yesterday bids from previous_trace
    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if not opp.get('alive', True):
            continue
        prev = opp.get('previous_trace', {}) or {}
        if prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    max_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how many units of water are likely needed per winner.
    # In this game, each unit of water corresponds to meeting WATER_REQ hp impact.
    # Use supply to gauge competition intensity.
    supply_units = max(0.0, supply / float(WATER_REQ))

    # Base willingness: if supply is scarce, bid more; if plentiful, bid less.
    # Normalize scarcity between MIN_SUPPLY and MAX_SUPPLY.
    if MAX_SUPPLY != MIN_SUPPLY:
        scarcity = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        scarcity = 0.5
    scarcity = max(0.0, min(1.0, scarcity))

    # Pressure from opponents: if yesterday someone bid very high, expect aggressive competition.
    pressure = 0.0
    if max_prev_bid >= DAILY_SALARY * 1.20:
        pressure = 1.0
    elif max_prev_bid >= DAILY_SALARY * 0.95:
        pressure = 0.7
    elif max_prev_bid >= DAILY_SALARY * 0.75:
        pressure = 0.4

    # Decide target bid based on our hp/no_water_days and observed pressure.
    # If we're in danger, overbid to secure water.
    if hp <= 2 or no_water_days >= 2:
        target = DAILY_SALARY * (0.95 + 0.25 * pressure)
    elif hp == 3:
        target = DAILY_SALARY * (0.70 + 0.20 * pressure)
    else:
        # hp >= 4
        target = DAILY_SALARY * (0.55 + 0.25 * scarcity + 0.15 * pressure)

    # Convert target into an absolute bid cap.
    # Keep within budget and avoid extreme overbids.
    # Also slightly anchor relative to max_prev_bid to beat typical aggressive bids.
    if max_prev_bid > 0:
        # If pressure is high, try to be competitive but not necessarily the top.
        if pressure >= 0.7:
            target = max(target, max_prev_bid * 0.88)
        elif pressure >= 0.4:
            target = max(target, max_prev_bid * 0.75)

    # Final clamp
    bid = float(target)
    bid = max(0.0, min(budget, bid))

    # Small deterministic jitter to avoid ties (still safe)
    jitter = ((day * 37) % 10) * 0.3
    bid = min(budget, bid + jitter)

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
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Yesterday pressure signal from opponents' previous bids
    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    yesterday_bids.append(float(b))
                except Exception:
                    pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = (sum(yesterday_bids) / len(yesterday_bids)) if yesterday_bids else 0.0

    # Estimate how many water units are likely to be available; bids compete for water
    # We convert supply to an approximate number of winners'
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
    day = day_context['day']

    # Identify alive opponents and use only their previous_trace
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            prev = opp.get('previous_trace', {})
            if prev:
                alive_opps.append((opp_id, prev))

    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Extract yesterday bids to infer aggression level
    yesterday_bids = []
    for _, prev in alive_opps:
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    # Supply pressure: higher supply usually reduces needed bid to secure water.
    # We'll map supply to a target bid fraction.
    # Use explicit int() for any indexing (none used), but keep calculations float-safe.
    supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    # More supply => lower target.
    base_frac = 0.62 - 0.25 * supply_norm

    # If opponents were bidding very high yesterday, increase slightly.
    if highest_prev_bid >= 0.85 * DAILY_SALARY:
        base_frac += 0.18
    elif avg_prev_bid >= 0.75 * DAILY_SALARY:
        base_frac += 0.08

    # My hp safety: if low hp, bid more aggressively.
    hp = float(my_status['hp'])
    no_water_days = int(my_status.get('no_water_days', 0))

    if hp <= 2 or no_water_days >= 2:
        base_frac = max(base_frac, 0.90)
    elif hp <= 4:
        base_frac = max(base_frac, 0.72)

    # Convert to bid, capped by budget.
    bid = DAILY_SALARY * base_frac

    # Ensure we don't spend too much when already safe.
    # If my hp is high and no-water-days is small, keep a tighter cap.
    if hp >= 7 and no_water_days <= 0:
        bid = min(bid, DAILY_SALARY * 0.70)

    bid = min(bid, float(my_status['budget']))

    # If budget is extremely low, still bid something minimal but nonzero.
    if bid <= 0:
        return 0.0
    return float(bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    # Extract context
    supply = day_context['supply']
    day = day_context['day']

    # Identify alive opponents
    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    # If no one is alive, conserve
    if not alive_opponents:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.4))

    # Use yesterday's immediate trace to infer aggressiveness
    yesterday_bids = []
    yesterday_hp_after = []
    for opp_id, opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(float(prev.get('bid', 0.0)))
            yesterday_hp_after.append(float(prev.get('hp_after', opp.get('hp', 0.0))))

    # Baseline need pressure: if my hp is low, I must bid more.
    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))

    # Determine supply tightness: medium scenario implies 15-25; if supply is close to 15, fewer winners.
    # Use a conservative fraction of DAILY_SALARY as bid floor.
    supply_tight = 1.0
    if supply >= 23.0:
        supply_tight = 0.75
    elif supply >= 19.0:
        supply_tight = 0.9

    # Compute yesterday max bid among alive opponents
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
    else:
        highest_prev_bid = 0.0

    # If someone bid very aggressively yesterday (near or above salary), counter with a moderate overbid.
    # Otherwise, bid around the top bid plus a small increment to win ties.
    target = None
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        if my_hp > 3.0:
            target = DAILY_SALARY * 0.32 * supply_tight
        else:
            target = DAILY_SALARY * 0.9 * supply_tight
    else:
        # Attempt to just beat the likely leader.
        target = highest_prev_bid + 2.0
        # Also ensure we bid at least a fraction of salary to avoid losing to Cindy/Eric-style bids.
        min_target = max(DAILY_SALARY * 0.48 * supply_tight, 10.0)
        if target < min_target:
            target = min_target

    # If my hp is critically low, override to protect survival.
    if my_hp <= 2.0:
        target = max(target, DAILY_SALARY * 0.85 * supply_tight)
    elif my_hp <= 4.0:
        target = max(target, DAILY_SALARY * 0.6 * supply_tight)

    # Cap by budget and keep non-negative
    bid = max(0.0, min(my_budget, target))

    # Small day-based jitter to avoid deterministic ties (bounded)
    jitter = ((int(day) % 5) - 2) * 0.5
    bid = max(0.0, min(my_budget, bid + jitter))

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

    supply = day_context['supply']
    day = day_context['day']

    # Alive opponents
    alive = []
    for opp_id, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((opp_id, o))

    # If no opponents, bid modestly
    if not alive:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.4))

    # React to yesterday bids (immediate trace only)
    yesterday_bids = []
    for _, o in alive:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(float(prev['bid']))

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how competitive the market is.
    # If others bid high, we don't need to match; we just need enough to avoid no-water.
    # Use supply to decide aggressiveness.
    # Higher supply => easier to secure water; bid lower.
    supply_norm = (float(supply) - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)  # 0..1
    supply_norm = max(0.0, min(1.0, supply_norm))

    # Base bid: moderate fraction of salary.
    base = DAILY_SALARY * (0.62 - 0.25 * supply_norm)  # ~0.62 at low supply, ~0.37 at high supply

    # If my hp is low, increase bid to prevent death.
    hp = float(my_status.get('hp', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    if hp <= 1.0 or no_water_days >= 2:
        urgency = 0.95
    elif hp <= 3.0:
        urgency = 0.78
    else:
        urgency = 0.55

    target = base * urgency

    # If yesterday market was very expensive, slightly raise but not to the top bid.
    # Exploit Cindy death: avoid bidding near high bids that drain budget.
    # Use thresholds relative to salary.
    if highest_prev_bid >= DAILY_SALARY * 1.1:
        target = max(target, DAILY_SALARY * 0.65)
    elif highest_prev_bid >= DAILY_SALARY * 0.85:
        target = max(target, DAILY_SALARY * 0.58)

    # If my budget is tight, cap aggressively.
    budget = float(my_status.get('budget', 0.0))
    if budget <= DAILY_SALARY * 0.35:
        target = min(target, budget * 0.9)
    else:
        # Keep some buffer for future days
        target = min(target, budget * 0.55)

    # Ensure non-negative
    if target < 0.0:
        target = 0.0

    # In case of extreme supply, adjust slightly
    if float(supply) >= 22.0:
        target *= 0.9
    elif float(supply) <= 16.0:
        target *= 1.05

    # Return as float
    return float(target)
"""
