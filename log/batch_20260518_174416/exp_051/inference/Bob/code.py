# ============================================================
# Experiment: exp_051
# Agent: Bob
# Source: exp_051
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

    alive_opponents = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opponents:
        return max(0.0, min(float(my_status.get('budget', 0.0)), DAILY_SALARY * 0.45))

    prev_bids = []
    prev_hp_after = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid', 0.0)))
            except Exception:
                pass
            try:
                prev_hp_after.append(float(prev.get('hp_after', opp.get('hp', 0.0))))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = sum(prev_bids) / float(len(prev_bids)) if prev_bids else 0.0

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))

    # Determine target aggressiveness based on yesterday pressure.
    # If someone overreached near our salary, assume they are desperate -> we conserve.
    overbid_threshold = DAILY_SALARY * 0.85

    # Estimate how much water we need relative to expected supply.
    # If supply is tight, we bid more; if abundant, bid less.
    tightness = 0.0
    if supply <= float(WATER_REQ):
        tightness = 1.0
    elif supply <= float(MIN_SUPPLY):
        tightness = 0.75
    elif supply <= float(MAX_SUPPLY):
        tightness = 0.5
    else:
        tightness = 0.25

    if my_hp <= 2.0:
        # Critical: secure water at almost any reasonable cost.
        base = DAILY_SALARY * (0.88 if highest_prev_bid < overbid_threshold else 0.95)
    else:
        if highest_prev_bid >= overbid_threshold:
            # Opponents likely desperate; avoid price war.
            base = DAILY_SALARY * (0.25 + 0.25 * tightness)
        else:
            # Match slightly above average/leader to win without overspending.
            # Use a small increment over avg and leader to exploit their likely conservative bidding.
            base = max(DAILY_SALARY * (0.35 + 0.25 * tightness), avg_prev_bid + 2.0)
            if highest_prev_bid > 0.0:
                base = min(base, highest_prev_bid + 5.0)

    # Final clamp to budget.
    bid = max(0.0, min(my_budget, base))

    # If budget is extremely low, still bid enough to avoid wasting the day.
    if my_budget < DAILY_SALARY * 0.15:
        bid = max(0.0, min(my_budget, DAILY_SALARY * 0.12))

    return float(bid)
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

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Read yesterday bids only from previous_trace
    yesterday_bids = []
    yesterday_hp_after = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        if prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])
            yesterday_hp_after.append(prev.get('hp_after', None))

    my_hp = my_status['hp']
    my_budget = my_status['budget']

    # Estimate how many
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    # Alive opponents
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    # If no opponents alive, conserve budget
    if not alive_opps:
        return max(0.0, min(float(my_status.get('budget', 0.0)), DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace (immediate reaction)
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))

    # Determine pressure from extremes
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    lowest_prev_bid = min(yesterday_bids) if yesterday_bids else 0.0

    # Base bid scales with supply: higher supply -> can bid less
    # Use integer index safety by constructing discrete tiers.
    # supply in [15,25], map to 3 tiers.
    tier = int((supply - 15.0) / 5.0)  # 0..2
    if tier < 0:
        tier = 0
    if tier > 2:
        tier = 2

    # Conservative survival target: aim to secure water when supply is low and HP is not high.
    # Tiered fractions
    tier_frac = [0.62, 0.52, 0.44][tier]

    # If opponents showed extreme behavior yesterday, adjust.
    # If someone overbid near salary, avoid matching; bid just enough to stay alive.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        if my_hp > 3.0:
            bid = DAILY_SALARY * 0.35
        else:
            bid = DAILY_SALARY * 0.65
    # If someone underbid to zero while others overbid, competition likely uneven; bid slightly higher than base.
    elif lowest_prev_bid <= 1e-6 and highest_prev_bid >= DAILY_SALARY * 0.55:
        bid = DAILY_SALARY * (tier_frac + 0.10)
    else:
        # Normal case: bid based on tier and current HP pressure
        if my_hp <= 2.0:
            bid = DAILY_SALARY * (tier_frac + 0.20)
        elif my_hp <= 4.0:
            bid = DAILY_SALARY * (tier_frac + 0.10)
        else:
            bid = DAILY_SALARY * tier_frac

    # Cap by budget
    bid = max(0.0, min(my_budget, float(bid)))

    # Ensure we don't bid trivially when budget allows (to avoid no-water streak)
    if my_budget >= DAILY_SALARY * 0.25 and bid < DAILY_SALARY * 0.20:
        bid = DAILY_SALARY * 0.20

    return bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    # If no opponents, spend enough to secure water.
    if not alive_opponents:
        target = DAILY_SALARY * 0.45
        return float(min(budget, target))

    # Extract yesterday bids from each alive opponent.
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Determine pressure from yesterday.
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / float(len(yesterday_bids))
    else:
        highest_prev_bid = 0.0
        avg_prev_bid = DAILY_SALARY * 0.6

    # Base bid: undercut typical surviving bids (~90-95) but avoid matching the top if they escalated.
    # Use supply to slightly adjust aggressiveness: higher supply reduces need to overbid.
    supply_norm = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_norm = max(0.0, min(1.0, supply_norm))

    # If someone was very aggressive yesterday, we must counter more.
    if highest_prev_bid >= DAILY_SALARY * 1.15:  # ~103.5+
        # If our hp is low, bid close to salary to secure water.
        if hp <= 3 or no_water_days >= 2:
            target = DAILY_SALARY * 0.95
        else:
            target = DAILY_SALARY * 0.80
    elif highest_prev_bid >= DAILY_SALARY * 1.05:  # ~94.5+
        # Slightly above the average pressure.
        target = max(DAILY_SALARY * 0.75, avg_prev_bid + 2.0)
    else:
        # Comfortable: bid just below the common surviving range.
        target = DAILY_SALARY * (0.88 - 0.08 * supply_norm)  # ~79-88
        # If our hp is critically low, override.
        if hp <= 2 or no_water_days >= 3:
            target = DAILY_SALARY * 0.95
        elif hp <= 4:
            target = max(target, DAILY_SALARY * 0.75)

    # Cap by budget and keep non-negative.
    if budget <= 0:
        return 0.0
    bid = float(min(budget, target))
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Identify alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        # No competition: bid for safety but not wastefully
        return min(my_status['budget'], DAILY_SALARY * 0.35)

    # Read yesterday bids from previous_trace (immediate reaction)
    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Baseline: ensure we can survive 10 days; conserve budget when possible
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Pressure estimate: if someone bid high yesterday, expect higher clearing price.
    # Cindy was strong yesterday; treat high bids as signal.
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid
    else:
        highest_prev_bid = 0.0
        second_prev_bid = 0.0

    # Supply-based aggressiveness: higher supply -> lower need to outbid.
    # We convert to a normalized factor in [0,1].
    norm_supply = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if (MAX_SUPPLY - MIN_SUPPLY) != 0 else 0.5
    norm_supply = max(0.0, min(1.0, norm_supply))

    # Decide target bid scale
    # If we are in danger (low hp or many no-water days), bid more.
    danger = (hp <= 2) or (no_water_days >= 2)

    # If yesterday highest bids were near/above Cindy-like level (~135), anticipate stiff competition.
    # We'll bid slightly below the top pressure to avoid overpaying, unless we're in danger.
    if highest_prev_bid >= DAILY_SALARY * 1.4:  # ~126
        if danger:
            target = min(budget, highest_prev_bid * 0.98)
        else:
            target = min(budget, max(DAILY_SALARY * 0.75, highest_prev_bid * 0.80))
    elif highest_prev_bid >= DAILY_SALARY * 0.9:  # ~81
        if danger:
            target = min(budget, max(DAILY_SALARY * 0.95, highest_prev_bid * 0.92))
        else:
            target = min(budget, max(DAILY_SALARY * 0.60, second_prev_bid * 0.85))
    else:
        # Competition seems weak (Eric/David-like collapse bids). Bid modestly.
        if danger:
            target = min(budget, DAILY_SALARY * 0.90)
        else:
            # With supply likely adequate, we can underbid slightly.
            target = min(budget, DAILY_SALARY * (0.45 + 0.25 * norm_supply))

    # Safety cap: never bid more than budget.
    bid = float(target)

    # Small day-based adjustment to avoid ties/monotony: later days slightly more aggressive.
    # Keep it gentle to avoid budget burn.
    if day >= 7:
        bid = min(budget, bid * 1.08)

    # Ensure bid is non-negative.
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Extract yesterday bids from traces for immediate reaction
    yesterday_bids = []
    highest_prev_bid = None
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            b = float(prev['bid'])
            yesterday_bids.append(b)
            if highest_prev_bid is None or b > highest_prev_bid:
                highest_prev_bid = b

    # Supply pressure: higher supply reduces need to overbid
    # Expected number of water units roughly scales with supply/WATER_REQ
    # (use only to adjust aggressiveness)
    supply_ratio = supply / float(WATER_REQ)

    # Emergency if low HP or already several no-water days
    emergency = (hp <= 2.5) or (no_water_days >= 2)

    # Determine base bid using yesterday's strongest pressure
    # If someone was bidding very high yesterday, raise our bid to not get starved.
    if highest_prev_bid is not None:
        high_pressure = highest_prev_bid >= DAILY_SALARY * 0.85
        if emergency:
            target = DAILY_SALARY * (0.88 if high_pressure else 0.78)
        else:
            if high_pressure:
                # Match the pressure but not fully; aim to win with moderate edge
                target = max(highest_prev_bid * 0.92, DAILY_SALARY * 0.45)
            else:
                target = max(highest_prev_bid * 0.75, DAILY_SALARY * (0.48 + 0.08 * (supply_ratio - 1.0)))
    else:
        if emergency:
            target = DAILY_SALARY * 0.85
        else:
            target = DAILY_SALARY * (0.55 + 0.08 * (supply_ratio - 1.0))

    # If supply is low (closer to 15), slightly increase bid; if high (closer to 25), decrease
    if supply <= float(MIN_SUPPLY):
        target *= 1.08
    elif supply >= float(MAX_SUPPLY):
        target *= 0.95

    # Clamp to budget and keep within reasonable bounds
    target = max(0.0, target)
    bid = min(budget, target)

    # If we have extremely low budget, bid what we can
    if bid < 1e-6:
        bid = min(budget, DAILY_SALARY * 0.1)

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

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    # If no opponents, conserve.
    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace only (immediate reaction).
    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Estimate how aggressive the field was.
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    # Supply pressure: lower supply tends to require stronger bids.
    # Normalize into [0,1] where 1 = tightest.
    if MAX_SUPPLY > MIN_SUPPLY:
        tightness = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    else:
        tightness = 0.5
    tightness = max(0.0, min(1.0, tightness))

    # Base bid: aim below the leaders to avoid overpaying.
    # If leaders were very aggressive (high highest_prev_bid), increase slightly.
    leader_signal = 0.0
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        leader_signal = 0.25
    elif highest_prev_bid >= DAILY_SALARY * 0.55:
        leader_signal = 0.15
    else:
        leader_signal = 0.05

    # Need-based escalation.
    if hp <= 2 or no_water_days >= 1:
        need_mult = 0.95
    elif hp <= 3:
        need_mult = 0.75
    else:
        need_mult = 0.55

    # Compute target bid.
    # Use a blend of supply tightness and leader signal, but keep under leader bids.
    target = DAILY_SALARY * (need_mult + leader_signal) * (0.65 + 0.35 * tightness)

    # If yesterday bids were known, cap relative to average/highest to stay exploitative.
    if avg_prev_bid > 0:
        target = min(target, avg_prev_bid * 0.95)
    if highest_prev_bid > 0:
        target = min(target, highest_prev_bid * 0.85)

    # Ensure non-negative and within budget.
    bid = max(0.0, min(budget, target))

    # If budget is tiny, still bid something to avoid wasting the day.
    if bid < 1e-6 and budget > 0:
        bid = min(budget, 1.0)

    return bid
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context['supply'])
    day = day_context['day']

    # Alive opponents
    alive_opps = []
    for k, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # If no opponents, bid just enough to keep hp safe
    if not alive_opps:
        # Aim to secure at least one unit of requirement
        target = int((supply + 1e-9) / WATER_REQ)
        # Conservative: if target is 0, bid high; else moderate
        if target <= 0:
            return min(my_status['budget'], DAILY_SALARY * 0.95)
        return min(my_status['budget'], DAILY_SALARY * 0.55)

    # Extract yesterday bids from traces (immediate reaction only)
    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Compute a pressure estimate from yesterday
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    # Determine urgency based on my hp and supply tightness
    # If supply is low (near 15), water is scarce -> need to outbid pressure.
    tightness = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)  # 0..1
    tightness = max(0.0, min(1.0, tightness))

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    # Baseline bid: if my hp is low, bid higher.
    if hp <= 2:
        base = DAILY_SALARY * (0.85 + 0.1 * tightness)
    elif hp <= 4:
        base = DAILY_SALARY * (0.65 + 0.15 * tightness)
    else:
        base = DAILY_SALARY * (0.50 + 0.20 * tightness)

    # Opponent exploitation: Cindy/Eric appear to bid high (~100+). If yesterday pressure was high,
    # we slightly overtake; if it was moderate, shade down.
    # David's collapse suggests low bids are punished; avoid going too low.
    if highest_prev_bid >= DAILY_SALARY * 0.95:
        # High pressure: bid around highest_prev_bid but capped by budget.
        # Add a small premium to beat ties.
        bid = max(base, highest_prev_bid + 2.0)
    elif highest_prev_bid >= DAILY_SALARY * 0.75:
        # Medium-high pressure: bid somewhat above average.
        bid = max(base, avg_prev_bid + 5.0)
    else:
        # Lower pressure: shade down but stay above a safe floor.
        safe_floor = DAILY_SALARY * (0.35 + 0.25 * tightness)
        bid = max(base, safe_floor)

    # Budget safety: never exceed budget, and avoid extreme overspending.
    # Also ensure at least some bid if budget is tiny.
    bid = min(bid, budget)

    # If budget is too small, spend most of it to avoid dying.
    if budget <= DAILY_SALARY * 0.2:
        bid = min(budget, DAILY_SALARY * 0.9)

    # Final guard: bid must be non-negative
    if bid < 0.0:
        bid = 0.0

    return bid
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

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Extract yesterday bids from previous_trace only (immediate reaction)
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Pressure estimate from yesterday
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Supply pressure: if supply is tight relative to requirement, we must secure water
    # Use integer math for any indexing (none used here), but keep thresholds float-safe.
    tight_supply = supply <= (MIN_SUPPLY + 1.0)

    # Core strategy: bid into the high-pressure band if others previously bid high.
    # Cindy/others likely anchor around ~0.85-1.0 of DAILY_SALARY.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # If we are in danger, match/just beat; otherwise undercut slightly.
        if my_status['hp'] <= 3 or my_status['no_water_days'] >= 2 or tight_supply:
            target = highest_prev_bid + 3.0
        else:
            target = max(DAILY_SALARY * 0.75, highest_prev_bid - 2.0)
    else:
        # If opponents were not bidding extremely, bid moderately to win without burning budget.
        if my_status['hp'] <= 2 or my_status['no_water_days'] >= 3 or tight_supply:
            target = DAILY_SALARY * 0.85
        else:
            target = DAILY_SALARY * 0.55

    # Convert target into a feasible bid: scale with our need level.
    # If we have very low hp, be more aggressive.
    if my_status['hp'] <= 1:
        target = max(target, DAILY_SALARY * 0.95)

    # Ensure bid does not exceed budget.
    bid = min(my_status['budget'], target)

    # Avoid extremely tiny bids when we have urgent need.
    if my_status['hp'] <= 3 and bid < DAILY_SALARY * 0.4:
        bid = min(my_status['budget'], DAILY_SALARY * 0.6)

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
    day = day_context['day']

    # Alive opponents
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    # If no opponents, just bid enough to get water while conserving budget
    if not alive:
        return min(float(my_status['budget']), DAILY_SALARY * 0.4)

    # Read yesterday bids from previous_trace only
    prev_bids = []
    prev_by_id = {}
    for oid, o in alive:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                bval = float(b)
                prev_bids.append(bval)
                prev_by_id[oid] = bval
            except Exception:
                pass

    # Estimate contest pressure
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    # Cindy appears to be the main aggressor when her bid was high yesterday
    cindy_bid = 0.0
    if 'Cindy' in opponents_status and opponents_status['Cindy'].get('alive', False):
        prev = opponents_status['Cindy'].get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                cindy_bid = float(b)
            except Exception:
                cindy_bid = 0.0

    # Supply pressure: higher supply reduces urgency to overpay
    # Normalize to [0,1]
    if MAX_SUPPLY - MIN_SUPPLY <= 0:
        supply_factor = 0.5
    else:
        supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_factor = max(0.0, min(1.0, supply_factor))

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    # Dynamic target bid
    # If someone paid near/above salary, we must match to avoid being starved.
    # Otherwise, bid moderately above the highest recent bid.
    pressure = 0.0
    if highest_prev_bid > 0:
        pressure = highest_prev_bid / DAILY_SALARY

    # Base aggressiveness: more aggressive when supply is high (more water to allocate, but also more competition)
    # and when my hp is lower.
    hp_factor = 0.0
    if hp <= 2.0:
        hp_factor = 1.0
    elif hp <= 4.0:
        hp_factor = 0.7
    else:
        hp_factor = 0.4

    # Compute a desired bid ceiling
    # Keep a reserve so we can keep bidding later
    # (roughly 2 days of salary reserve)
    reserve = DAILY_SALARY * 2.0
    effective_budget = max(0.0, budget - reserve)

    # If Cindy was very aggressive yesterday, anticipate similar behavior.
    if cindy_bid >= DAILY_SALARY * 1.2:
        target = cindy_bid + 2.0
    elif pressure >= 1.0:
        target = highest_prev_bid + 1.0
    else:
        # Moderate: aim slightly above highest bid to win but not overspend
        target = max(DAILY_SALARY * (0.45 + 0.25 * (1.0 - supply_factor)) , highest_prev_bid + 0.5)

    # Adjust for my hp urgency and supply
    # Higher supply_factor => slightly less urgent
    target *= (0.85 + 0.3 * hp_factor)
    target *= (0.95 + 0.15 * (1.0 - supply_factor))

    # Final bid: bounded by budget and a reasonable fraction of salary
    # Since bids are monetary, cap at 1.6*salary to avoid runaway.
    cap = min(budget, DAILY_SALARY * 1.6)
    bid = min(cap, target)

    # Ensure non-negative
    if bid < 0.0:
        bid = 0.0

    return float(bid)
"""
