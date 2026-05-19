# ============================================================
# Experiment: exp_082
# Agent: Bob
# Source: exp_082
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
    day = day_context.get('day', 0)

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    # Base cap: never bid more than we can afford.
    max_bid_affordable = max(0.0, budget)

    # If no opponents, bid enough to secure water.
    if not alive_opponents:
        target = min(max_bid_affordable, DAILY_SALARY * 0.45)
        return target

    # Read yesterday bids for immediate reaction.
    yesterday_bids = []
    yesterday_bids_by_id = {}
    for opp_id, opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                b_val = float(b)
                yesterday_bids.append(b_val)
                yesterday_bids_by_id[opp_id] = b_val
            except Exception:
                pass

    # Estimate opponent aggressiveness.
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = 0.0
    if len(yesterday_bids) >= 2:
        sorted_bids = sorted(yesterday_bids, reverse=True)
        second_prev_bid = sorted_bids[1]

    # Determine how much water we likely need to avoid running out.
    # If no_water_days is low, we should secure water more aggressively.
    urgency = 0.0
    if no_water_days <= 0:
        urgency = 1.0
    elif no_water_days == 1:
        urgency = 0.85
    elif no_water_days == 2:
        urgency = 0.65
    elif no_water_days >= 5:
        urgency = 0.25
    else:
        urgency = 0.45

    # HP pressure: lower hp => higher urgency.
    if hp <= 1.5:
        urgency = max(urgency, 0.95)
    elif hp <= 3.0:
        urgency = max(urgency, 0.8)

    # Supply context: if supply is tight relative to our requirement, increase bid.
    supply_pressure = 0.0
    if supply <= float(WATER_REQ):
        supply_pressure = 1.0
    elif supply <= (float(WATER_REQ) * 1.25):
        supply_pressure = 0.75
    elif supply <= (float(WATER_REQ) * 1.6):
        supply_pressure = 0.45
    else:
        supply_pressure = 0.25

    # Decide target bid.
    # If opponents were bidding aggressively yesterday, overbid slightly to beat them.
    aggressive_threshold = DAILY_SALARY * 0.85

    if highest_prev_bid >= aggressive_threshold:
        # Try to outbid the highest previous bid by a small increment.
        # Use second_prev_bid to avoid extreme overbidding when possible.
        baseline = max(second_prev_bid, highest_prev_bid)
        increment = 2.5 + 5.0 * urgency
        desired = baseline + increment
        # If our budget is low, scale down but keep urgency.
        desired = min(desired, max_bid_affordable)
    else:
        # Moderate bid: enough to be competitive but not wasteful.
        # Scale with urgency and supply pressure.
        desired = DAILY_SALARY * (0.35 + 0.35 * urgency + 0.2 * supply_pressure)
        # If we are behind on hp, bid more.
        if hp < 4.0:
            desired += DAILY_SALARY * 0.1
        # If yesterday bids suggest mild competition, bump slightly.
        if highest_prev_bid > 0.0:
            desired = max(desired, min(max_bid_affordable, highest_prev_bid + (1.0 + 2.0 * urgency)))

    # Final safety: do not exceed affordability.
    bid = float(desired)
    bid = max(0.0, min(bid, max_bid_affordable))

    # If budget is extremely low, bid the minimum to stay in play.
    if bid <= 0.0:
        bid = min(max_bid_affordable, DAILY_SALARY * 0.05)

    return bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = day_context['supply']
    day = day_context['day']

    # Identify alive opponents
    alive_ids = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_ids.append(oid)

    # If no opponents alive, spend to secure water
    if not alive_ids:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from traces (immediate reaction only)
    prev_bids = []
    for oid in alive_ids:
        prev = opponents_status[oid].get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid', 0.0)))
            except Exception:
                pass

    # Baseline: aim to beat typical surviving bids without going all-in
    # Use yesterday max as pressure signal
    pressure_bid = 0.0
    if prev_bids:
        pressure_bid = max(prev_bids)

    # If my HP is critical, bid aggressively
    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))

    # Estimate how many days supply can cover for me at this rate
    # supply is float; compute integer index safely
    # Higher supply -> less urgency
    supply_level = (int(supply) - int(15))  # rough scale
    if supply_level <= 0:
        urgency = 1.0
    elif supply_level >= 10:
        urgency = 0.7
    else:
        urgency = 0.85

    # Decide target bid
    # If yesterday pressure was high, try to slightly overbid
    if pressure_bid >= DAILY_SALARY * 0.85:
        if my_hp <= 3:
            target = DAILY_SALARY * 0.95
        else:
            target = min(DAILY_SALARY * 0.65, pressure_bid + 2.0)
    else:
        # Moderate equilibrium bid
        if my_hp <= 3:
            target = DAILY_SALARY * 0.85
        else:
            target = max(DAILY_SALARY * 0.48, pressure_bid * 0.9)

    # Adjust by urgency and budget
    target *= urgency

    # Keep some budget for later days
    budget_cap = my_budget
    # If budget is low, spend enough to keep from dying
    if my_budget <= DAILY_SALARY * 0.25:
        target = min(target, my_budget)
    else:
        # Don't overspend too early
        target = min(target, my_budget * 0.7)

    # Final clamp
    if target < 0.0:
        target = 0.0
    if target > my_budget:
        target = my_budget

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

    supply = day_context['supply']
    day = day_context['day']

    # Identify alive opponents and collect yesterday bids
    alive_opps = []
    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(float(prev['bid']))

    # If no opponents alive, bid conservatively
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Pressure signal from yesterday
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Budget/HP urgency
    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])

    # Estimate how many units are likely available (supply is total water)
    # We'll target 1 unit of water (the game likely consumes WATER_REQ per unit)
    # but bid in terms of salary; keep it robust to unknown mapping.
    # Use supply to scale bids slightly.
    supply_units = max(1, int(supply / float(WATER_REQ)))

    # Base bid: aim to be competitive but not match the top aggressors
    # If supply is higher, competition is lower => lower bid.
    supply_factor = 1.0
    if supply_units >= 2:
        supply_factor = 0.85
    else:
        supply_factor = 1.0

    # Escalate if yesterday's top bid was extremely high (indicating strong competition)
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        if my_hp > 3:
            bid = DAILY_SALARY * 0.30 * supply_factor
        else:
            bid = DAILY_SALARY * 0.95 * supply_factor
    else:
        # Moderate competition: bid around half salary, slightly above the highest bid if needed
        # (but avoid overcommitting)
        bid = max(DAILY_SALARY * 0.50 * supply_factor, highest_prev_bid * 0.60 + 5.0)

    # If I'm critically low HP, bid much more
    if my_hp <= 2:
        bid = max(bid, DAILY_SALARY * 0.90)

    # Clamp by budget and a safety cap
    bid = float(min(my_budget, bid))
    if bid < 0.0:
        bid = 0.0

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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Identify alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # If no opponents, bid to last
    if not alive_opps:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.35))

    # Read yesterday bids from previous_trace only
    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', None)
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    yesterday_bids.append(float(b))
                except Exception:
                    pass
        # In case previous_trace is a list, take the last entry
        elif isinstance(prev, list) and prev:
            last = prev[-1]
            if isinstance(last, dict):
                b = last.get('bid', None)
                if b is not None:
                    try:
                        yesterday_bids.append(float(b))
                    except Exception:
                        pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Compute our urgency
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Supply pressure: if supply is low, more competition for limited water
    # Normalize supply to [0,1]
    if MAX_SUPPLY <= MIN_SUPPLY:
        supply_factor = 0.5
    else:
        supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
        if supply_factor < 0.0:
            supply_factor = 0.0
        if supply_factor > 1.0:
            supply_factor = 1.0

    # Strategy:
    # - If yesterday had very high bids, we bid enough to avoid losing repeatedly, but not as high as Cindy's ~199.
    # - If our HP is low or we're already on no-water streak, we increase.
    # - Otherwise, we keep a moderate bid.
    base = DAILY_SALARY * 0.52

    # Pressure adjustment from yesterday
    # Cindy/others likely bid around 180-200; we treat >=170 as high pressure.
    if highest_prev_bid >= DAILY_SALARY * 0.85:  # >= 76.5, but in this game bids are ~150-270
        # More conservative than mirroring: add only a fraction of the gap
        pressure_boost = 0.18 * (highest_prev_bid - DAILY_SALARY * 0.6)
        if pressure_boost < 0.0:
            pressure_boost = 0.0
        bid_target = base + pressure_boost
    elif highest_prev_bid >= 170.0:
        bid_target = base + (highest_prev_bid - 170.0) * 0.25
    else:
        bid_target = base

    # Our urgency
    if hp <= 2.0:
        bid_target = max(bid_target, DAILY_SALARY * 0.9)
    elif hp <= 4.0:
        bid_target = max(bid_target, DAILY_SALARY * 0.7)

    if no_water_days >= 2:
        bid_target = max(bid_target, DAILY_SALARY * 0.75)

    # Supply factor: lower supply -> slightly higher bid
    # supply_factor near 0 means low supply (15), near 1 means high supply (25)
    bid_target = bid_target * (1.0 + (0.6 - supply_factor) * 0.15)

    # Cap bid to what we can afford
    # Also keep an upper cap to avoid bankruptcy risk
    max_affordable = budget
    if max_affordable < 0.0:
        max_affordable = 0.0

    # Safety cap: never exceed 0.95 budget, and don't go above ~3.2*WATER_REQ*DAILY_SALARY/9 scale
    # (keeps bids in observed range)
    hard_cap = min(max_affordable, DAILY_SALARY * 1.05)

    bid = bid_target
    if bid > hard_cap:
        bid = hard_cap
    if bid < 0.0:
        bid = 0.0

    # If budget is tiny, bid what we can
    if budget <= DAILY_SALARY * 0.15:
        return max(0.0, min(budget, DAILY_SALARY * 0.25))

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

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    if not alive:
        bid = DAILY_SALARY * 0.35
        return min(my_budget, bid)

    # Extract yesterday bids from immediate previous_trace
    prev_bids = []
    for oid, o in alive:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Identify likely dominant opponent from yesterday: highest bid among alive
    dominant_prev = 0.0
    for oid, o in alive:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is None:
            continue
        try:
            fb = float(b)
        except Exception:
            continue
        if fb >= dominant_prev:
            dominant_prev = fb

    # Supply pressure: with medium supply, Cindy likely tries to secure water early.
    # Target: bid slightly above dominant yesterday bid when my hp is healthy.
    supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_factor = max(0.0, min(1.0, supply_factor))

    # Base urgency
    urgent = 0
    if my_hp <= 2.0:
        urgent = 2
    elif my_hp <= 4.0:
        urgent = 1
    if my_no_water_days >= 2:
        urgent = max(urgent, 2)

    # Decide aggressiveness
    # If dominant_prev was high (Cindy-like), we counter slightly above it; else conserve.
    if dominant_prev >= DAILY_SALARY * 0.85:
        # Counter window: only if we can afford it and we need water.
        if my_budget <= 0:
            return 0.0
        counter = dominant_prev + (2.0 + 3.0 * supply_factor)
        # If urgent, raise closer to dominant; if not urgent, keep tight.
        if urgent >= 2:
            bid = min(counter, dominant_prev + 8.0)
        else:
            bid = min(counter, dominant_prev + 4.0)
    else:
        # No strong leader yesterday: bid around a fraction of salary adjusted by supply.
        bid = DAILY_SALARY * (0.45 + 0.25 * supply_factor)
        if urgent >= 2:
            bid = DAILY_SALARY * (0.75 + 0.1 * supply_factor)

    # Final clamps
    bid = max(0.0, bid)
    if my_budget < bid:
        bid = my_budget

    # If supply is very low, avoid overbidding late in episode; if very high, bid slightly more.
    # Episode length is fixed at 10, so day 10 is last: be more conservative then.
    if day >= 9:
        bid *= 0.85

    return float(min(my_budget, max(0.0, bid)))
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

    supply = day_context.get('supply', 0)
    day = day_context.get('day', 0)

    my_hp = my_status.get('hp', 0)
    my_budget = my_status.get('budget', 0)
    my_no_water_days = my_status.get('no_water_days', 0)

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append(o)

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Use only yesterday previous_trace bids for immediate reaction
    yesterday_bids = []
    yesterday_hp_after = []
    for o in alive_opponents:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass
        hp_after = prev.get('hp_after', None)
        if hp_after is not None:
            try:
                yesterday_hp_after.append(float(hp_after))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    median_prev_bid = 0.0
    if yesterday_bids:
        s = sorted(yesterday_bids)
        mid = int(len(s) // 2)
        median_prev_bid = float(s[mid])

    # Pressure estimate: if someone bid very high yesterday, expect bidding war.
    # Alex/Eric dying suggests others may not sustain that, but surviving high bidders likely continue.
    war_mode = highest_prev_bid >= DAILY_SALARY * 1.0 or median_prev_bid >= DAILY_SALARY * 0.8

    # Supply-based aggressiveness: higher supply reduces need to overpay.
    # supply is float; map to a [0,1] scale safely.
    if MAX_SUPPLY != MIN_SUPPLY:
        supply_scale = (float(supply) - float(MIN_SUPPLY)) / float(MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_scale = 0.5
    if supply_scale < 0.0:
        supply_scale = 0.0
    if supply_scale > 1.0:
        supply_scale = 1.0

    # Core target bid
    # When war_mode: bid closer to median/highest but still cap to avoid budget exhaustion.
    # When not war_mode: bid around a fraction of median/highest.
    base = 0.0
    if war_mode:
        # If my HP is low or no_water_days is high, increase bid to avoid death.
        urgency = 0.0
        if my_hp <= 2:
            urgency = 1.0
        elif my_hp <= 4:
            urgency = 0.6
        if my_no_water_days >= 2:
            urgency = max(urgency, 0.7)

        # Bid between median and highest depending on urgency and supply.
        # Higher supply -> slightly lower bid.
        mix = 0.55 + 0.25 * urgency - 0.15 * supply_scale
        mix = max(0.25, min(0.9, mix))
        base = median_prev_bid * (1.0 - mix) + highest_prev_bid * mix
    else:
        # Conservative: bid enough to beat typical bids.
        base = max(DAILY_SALARY * 0.45, median_prev_bid * 0.75)
        # Slightly reduce with higher supply.
        base = base * (0.95 - 0.15 * supply_scale)

    # Ensure we can afford it; also avoid overpaying when budget is low.
    # Target should be at least enough to compete, but never exceed budget.
    # Add a small day-based jitter to break ties.
    jitter = 0.0
    try:
        jitter = ((int(day) % 5) - 2) * 1.5
    except Exception:
        jitter = 0.0

    target = base + jitter

    # If my HP is critically low, go near maximum affordable.
    if my_hp <= 1:
        target = max(target, DAILY_SALARY * 0.9)
    elif my_hp <= 3:
        target = max(target, DAILY_SALARY * 0.65)

    # Cap target to avoid immediate budget depletion.
    # If supply is low (closer to MIN_SUPPLY), we may need to spend more.
    spend_fraction = 0.35 + 0.25 * (1.0 - supply_scale)  # 0.35..0.60
    if war_mode:
        spend_fraction += 0.1

    max_affordable = my_budget
    if max_affordable < 0:
        max_affordable = 0

    # Also cap by a fraction of budget to preserve future days.
    cap = max_affordable * min(0.95, spend_fraction)

    bid = min(max_affordable, target, cap) if cap > 0 else min(max_affordable, target)

    # Final safety: ensure non-negative bid
    if bid < 0:
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    my_hp = int(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for opp_id, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((opp_id, o))

    # If no opponents alive, conserve budget.
    if not alive_opps:
        cap = DAILY_SALARY * 0.4
        return min(my_budget, cap)

    # Read yesterday's bid pressure from previous_trace only.
    prev_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Determine how urgent we are.
    # If we've already gone multiple days without water or very low HP, bid aggressively.
    urgent = (my_hp <= 2) or (my_no_water_days >= 2)

    # Supply-based base bid: higher supply -> can bid slightly less.
    # Map supply in [15,25] to a multiplier in [1.05,0.85].
    if MAX_SUPPLY != MIN_SUPPLY:
        t = (supply - float(MIN_SUPPLY)) / (float(MAX_SUPPLY) - float(MIN_SUPPLY))
    else:
        t = 0.5
    t = max(0.0, min(1.0, float(t)))
    supply_mult = 1.05 - 0.20 * t

    # If others were bidding very high yesterday, undercut with a fraction.
    # Cindy/Alex were ~126-152 avg; avoid matching their max (~189).
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        if urgent:
            target = highest_prev_bid * 0.78
        else:
            target = highest_prev_bid * 0.62
    else:
        # If pressure was low, bid to secure without overpaying.
        if urgent:
            target = max(DAILY_SALARY * 0.75, highest_prev_bid * 0.8)
        else:
            target = max(DAILY_SALARY * 0.45, highest_prev_bid * 0.55)

    target *= supply_mult

    # Also ensure we don't bid too low when our water need is high relative to supply.
    # Approximate how many water units might be contested: higher supply reduces need.
    # Use a conservative floor based on supply/WATER_REQ.
    units = int(supply / float(WATER_REQ)) if WATER_REQ > 0 else 1
    if units <= 1:
        target *= 1.10

    # Final bounds: cannot exceed budget.
    # Keep a minimum bid fraction so we don't get starved when others are active.
    min_bid = DAILY_SALARY * (0.35 if not urgent else 0.65)
    bid = max(min_bid, target)

    return min(my_budget, bid)
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

    supply = day_context['supply']
    day = day_context['day']

    # Identify alive opponents and use yesterday trace to infer their aggression.
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    if not alive:
        # No competition: bid modestly to secure water.
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace.
    prev_bids = []
    for oid, o in alive:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Baseline from observed aggressive bidders.
    if prev_bids:
        # Use upper quantile-ish behavior via max/mean mix.
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / float(len(prev_bids))
    else:
        highest_prev = DAILY_SALARY * 0.8
        avg_prev = DAILY_SALARY * 0.6

    hp = my_status.get('hp', 0)
    budget = my_status.get('budget', 0.0)
    no_water_days = my_status.get('no_water_days', 0)

    # Pressure increases when my hp is low or I'm close to running out.
    # supply affects how many water units are likely to be available in general.
    # We don't know exact allocation rule, so we adjust bid level heuristically.
    supply_factor = 1.0
    if supply <= float(WATER_REQ):
        supply_factor = 1.15
    elif supply >= float(MAX_SUPPLY):
        supply_factor = 0.95

    # Target bid: slightly above the strongest recent bidder if I'm not in danger.
    # If I'm in danger, bid closer to/above highest_prev.
    if hp <= 2 or no_water_days >= 2:
        target = max(highest_prev * 0.98, avg_prev * 1.05)
    elif hp <= 4:
        target = max(avg_prev * 1.03, highest_prev * 0.92)
    else:
        # Safe: still compete, but don't overspend.
        target = max(avg_prev * 1.00, highest_prev * 0.88)

    target *= supply_factor

    # Convert to feasible bid within budget.
    # Also keep a floor to ensure we don't underbid when others are aggressive.
    min_floor = DAILY_SALARY * 0.65
    bid = max(min_floor, target)

    # If budget is low, scale down but keep enough to contest.
    if bid > budget:
        # If very low budget, take a last-stand bid.
        if hp <= 2:
            bid = budget
        else:
            bid = max(0.0, budget * 0.85)

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

    # Identify alive opponents and their yesterday bids
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)

    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Estimate how many
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

    supply = float(day_context['supply'])
    day = day_context['day']

    # Determine if supply is tight relative to our requirement
    # (use integer indices nowhere; just compute thresholds)
    tight = supply <= (MIN_SUPPLY + WATER_REQ) / 2.0  # ~12, but supply is >=15 so effectively all are not tight; keep safe
    # Better: treat lower end of range as tight
    tight = supply <= 18.0

    # Collect yesterday bids from alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Estimate opponent aggression from yesterday
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / float(len(yesterday_bids))
    else:
        highest_prev_bid = 0.0
        avg_prev_bid = 0.0

    # HP pressure: if we are low, bid to secure water
    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])

    # Baseline bid levels
    # If supply is lower, compete more; otherwise bid around salary fraction.
    if tight:
        base = DAILY_SALARY * 0.68
    else:
        base = DAILY_SALARY * 0.55

    # If yesterday saw very high bids, raise slightly to avoid losing to aggressive player(s)
    # Cindy/Alex were around 98-100 avg; use threshold near 0.9*salary.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        base = max(base, DAILY_SALARY * 0.75)

    # If we are critically low, bid harder (near max of base)
    if my_hp <= 2.0:
        base = max(base, DAILY_SALARY * 0.9)
    elif my_hp <= 4.0:
        base = max(base, DAILY_SALARY * 0.78)

    # Safety cap by budget
    bid = min(my_budget, base)

    # Small bump if we are likely to be outbid by aggressive players
    # Use avg_prev_bid as a guide.
    if yesterday_bids and avg_prev_bid >= DAILY_SALARY * 0.8:
        bid = min(my_budget, bid + 3.0)

    # Ensure non-negative
    if bid < 0.0:
        bid = 0.0

    return bid
"""
