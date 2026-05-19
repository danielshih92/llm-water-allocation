# ============================================================
# Experiment: exp_028
# Agent: Bob
# Source: exp_028
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

    # Alive opponents
    alive_opps = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opps.append(opp)

    # Base bid: aim to secure enough water to avoid no-water days early.
    # If supply is tight, bid more; if supply is generous, bid less.
    supply_clamped = max(float(MIN_SUPPLY), min(float(MAX_SUPPLY), float(supply)))
    # Normalize supply in [0,1]
    supply_norm = (supply_clamped - float(MIN_SUPPLY)) / (float(MAX_SUPPLY) - float(MIN_SUPPLY) + 1e-9)

    # Pressure from our own status
    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # If we've already had multiple no-water days or low hp, bid aggressively.
    if no_water_days >= 2 or hp <= 2.0:
        base = DAILY_SALARY * 0.85
    elif hp <= 3.0:
        base = DAILY_SALARY * 0.65
    else:
        # Otherwise scale with supply tightness (lower supply -> higher bid)
        base = DAILY_SALARY * (0.35 + 0.35 * (1.0 - supply_norm))

    # React to opponents' yesterday bids (immediate exploitation)
    # We only use previous_trace from each opponent once.
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                prev_bids.append(float(bid))
            except Exception:
                pass

    if prev_bids:
        highest_prev_bid = max(prev_bids)
        lowest_prev_bid = min(prev_bids)

        # If someone overbid heavily yesterday, they likely needed water; bid moderately to deny.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if hp > 3.0 and no_water_days < 2:
                base = max(base, DAILY_SALARY * 0.55)
            else:
                base = max(base, DAILY_SALARY * 0.9)
        # If everyone was cautious yesterday, we can undercut slightly while still securing water.
        elif lowest_prev_bid <= DAILY_SALARY * 0.35:
            base = min(base, DAILY_SALARY * 0.5)

    # Convert bid to an integer amount; also ensure within budget.
    bid = int(max(0, min(budget, base)))

    # Safety: if budget is extremely low, bid whatever remains.
    if budget <= 1.0:
        return int(max(0, budget))

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

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids to infer who is pressuring.
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    # Also check if Cindy (likely main competitor) was bidding high.
    cindy_prev = 0.0
    for oid, o in alive_opps:
        if str(oid) == 'Cindy':
            prev = o.get('previous_trace', {}) or {}
            b = prev.get('bid', None)
            if b is not None:
                try:
                    cindy_prev = float(b)
                except Exception:
                    cindy_prev = 0.0

    # Supply pressure: if supply is low, more agents will need to win water.
    supply_ratio = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)  # 0..1
    low_supply = supply_ratio < 0.35

    # Base bid targets.
    # Strategy: If Cindy was pressuring (high yesterday bid), match partially.
    if cindy_prev >= DAILY_SALARY * 1.25 or highest_prev_bid >= DAILY_SALARY * 1.35:
        target = DAILY_SALARY * (0.55 if hp > 3 else 0.85)
    elif low_supply:
        target = DAILY_SALARY * (0.65 if hp > 3 else 0.9)
    else:
        target = DAILY_SALARY * (0.45 if hp > 3 else 0.75)

    # If I'm already close to death, increase urgency sharply.
    if hp <= 2.0 or no_water_days >= 2:
        target = max(target, DAILY_SALARY * 0.95)

    # Budget safety: never bid more than budget.
    bid = min(budget, target)

    # If budget is tiny, bid what we can.
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
    # Safety caps
    MIN_BID_FLOOR = 1.0
    # Alive opponents
    alive = []
    for aid, st in opponents_status.items():
        if st.get('alive'):
            alive.append((aid, st))
    if not alive:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    supply = float(day_context['supply'])
    day = day_context.get('day', 0)

    # Yesterday pressure signal from previous_trace bids
    prev_bids = []
    prev_hp = []
    for _, st in alive:
        pt = st.get('previous_trace', {}) or {}
        bid = pt.get('bid', None)
        if bid is not None:
            try:
                prev_bids.append(float(bid))
            except Exception:
                pass
        hp_after = pt.get('hp_after', None)
        if hp_after is not None:
            try:
                prev_hp.append(float(hp_after))
            except Exception:
                pass

    if prev_bids:
        highest_prev_bid = max(prev_bids)
        # If someone was bidding near salary, expect tighter competition today.
        high_competition = highest_prev_bid >= DAILY_SALARY * 0.85
    else:
        highest_prev_bid = 0.0
        high_competition = False

    # Estimate how many full water units are likely needed today.
    # If supply is low, competition for water is more likely.
    # supply in [15,25] so units range [1,2]
    units = int(supply / float(WATER_REQ))  # explicit int index safety
    if units < 1:
        units = 1

    my_hp = float(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0))
    no_water_days = float(my_status.get('no_water_days', 0))

    # Base strategy: bid just enough to beat typical moderate bids unless our hp is critical.
    # Use yesterday highest bid as an upper anchor only when competition is high.
    if my_budget <= 0:
        return 0.0

    # Critical survival: if hp is low or we have gone several days without water, bid aggressively.
    if my_hp <= 2.5 or no_water_days >= 2:
        target = DAILY_SALARY * (0.90 if not high_competition else 0.98)
    else:
        # When supply is low (1 unit), be more competitive; when higher, hold back.
        supply_pressure = 0.65 if units == 1 else 0.50
        # If yesterday competition was high, slightly increase.
        if high_competition:
            supply_pressure += 0.15
        target = DAILY_SALARY * supply_pressure

    # If yesterday's highest bid exists, try to undercut slightly when not in critical mode.
    if prev_bids and not (my_hp <= 2.5 or no_water_days >= 2):
        # Aim to be above the likely clearing level but not exceed too much.
        # Use a conservative bump over a fraction of highest_prev_bid.
        target = max(target, highest_prev_bid * 0.60)

    # Final clamp: cannot exceed budget.
    bid = min(my_budget, max(MIN_BID_FLOOR, target))

    # If supply is at the low end, add a small increment to avoid losing to high bidders.
    if supply <= float(MIN_SUPPLY) + 0.5:
        bid = min(my_budget, bid + 5.0)

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

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    hp = my_status.get('hp', 0)
    budget = my_status.get('budget', 0)

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        return min(budget, int(DAILY_SALARY * 0.4))

    # Read yesterday bids from traces to infer pressure.
    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if not opp.get('alive', False):
            continue
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid', 0.0)))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Supply pressure: with limited supply, bids that secure water matter more.
    # Our need is fixed at 9; if supply is near minimum, competition is higher.
    supply_norm = 0.0
    try:
        supply_norm = (float(supply) - float(MIN_SUPPLY)) / (float(MAX_SUPPLY) - float(MIN_SUPPLY))
    except Exception:
        supply_norm = 0.0
    if supply_norm < 0.0:
        supply_norm = 0.0
    if supply_norm > 1.0:
        supply_norm = 1.0

    # Base bid: mid fraction of salary, higher when supply is tight.
    tight_multiplier = 1.0 + (1.0 - supply_norm) * 0.35  # up to +35% when tight

    # If Cindy-type pressure existed (high previous max bid), raise bid to avoid being outcompeted.
    pressure_multiplier = 1.0
    if highest_prev_bid >= DAILY_SALARY * 0.8:
        pressure_multiplier = 1.25
    elif highest_prev_bid >= DAILY_SALARY * 0.4:
        pressure_multiplier = 1.10

    # HP critical: bid more to protect survival.
    if hp <= 1:
        hp_multiplier = 1.35
    elif hp <= 2:
        hp_multiplier = 1.25
    elif hp <= 3:
        hp_multiplier = 1.15
    else:
        hp_multiplier = 1.0

    target = int(DAILY_SALARY * 0.55 * tight_multiplier * pressure_multiplier * hp_multiplier)

    # If yesterday pressure was extremely high, try to slightly overmatch.
    if highest_prev_bid > 0:
        target = max(target, int(highest_prev_bid * 0.95))

    # Never exceed budget.
    if budget <= 0:
        return 0
    if target > budget:
        target = int(budget)

    # Keep at least a minimal nonzero bid when we have budget and hp is not safe.
    if target <= 0 and budget > 0 and hp <= 3:
        target = int(min(budget, DAILY_SALARY * 0.7))

    return int(target)
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

    # Alive opponents only
    alive_opps = []
    for k, o in opponents_status.items():
        try:
            if o.get('alive', False):
                alive_opps.append(o)
        except Exception:
            continue

    # If no opponents, bid conservatively
    if not alive_opps:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace
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

    # Compute pressure signals
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = sum(yesterday_bids) / float(len(yesterday_bids)) if yesterday_bids else 0.0

    # My risk-aware cap
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = float(my_status.get('no_water_days', 0.0))

    # If I'm in danger, bid closer to salary to avoid death
    danger = 0
    if hp <= 2.0:
        danger = 2
    elif hp <= 4.0:
        danger = 1
    if no_water_days >= 2.0:
        danger = max(danger, 1)

    # Supply affects ability to win: with more supply, winning requires less aggressive bidding
    # But supply is the total water to allocate; higher supply increases chance others get water too.
    # We'll still anchor to observed opponent bidding.
    supply_factor = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    supply_factor = max(0.0, min(1.0, supply_factor))

    # Base strategy: slight undercut relative to highest yesterday bid, but not too low.
    # If yesterday bids were extreme (>= salary), opponents likely overbid; we can bid around 0.75-0.9 of that.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        target = highest_prev_bid * (0.78 + 0.12 * supply_factor)
    else:
        # Otherwise, bid around avg plus a small premium
        target = avg_prev_bid * (0.95 + 0.08 * supply_factor) + 2.0

    # Danger adjustment
    if danger == 2:
        target *= 1.15
    elif danger == 1:
        target *= 1.07

    # Ensure we don't overspend beyond what keeps us alive across remaining days.
    # With episode_days=10, approximate remaining horizon from day index.
    episode_days = 10
    remaining = max(1, episode_days - day)
    # Keep some buffer: reserve 20% of budget for later
    reserve = 0.2 * budget
    max_affordable_today = max(0.0, budget - reserve)

    # Also, never exceed a fraction of salary unless in high danger
    salary_cap = DAILY_SALARY * (1.0 if danger >= 1 else 0.75)

    bid = min(target, max_affordable_today, salary_cap)

    # If bid is too small relative to typical competition, nudge up
    if bid < DAILY_SALARY * 0.45:
        bid = min(max_affordable_today, DAILY_SALARY * (0.55 + 0.2 * supply_factor))

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

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    alive = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive:
        return max(0.0, min(float(my_status.get('budget', 0.0)), DAILY_SALARY * 0.4))

    # Read yesterday bids only (immediate reaction)
    prev_bids = []
    for o in alive:
        prev = o.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Heuristic: if someone was bidding close to salary, market is competitive.
    competitive = highest_prev_bid >= DAILY_SALARY * 0.85

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Base bid depends on supply abundance
    # If supply is near minimum, water is scarce -> bid higher.
    # If supply is near maximum, bid lower.
    supply_ratio = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Target spend levels
    if competitive:
        # Match pressure but not fully; conserve budget.
        base = DAILY_SALARY * (0.55 + 0.25 * (1.0 - supply_ratio))
    else:
        base = DAILY_SALARY * (0.45 + 0.20 * (1.0 - supply_ratio))

    # Urgency adjustments
    if my_hp <= 2.0 or no_water_days >= 2:
        base = max(base, DAILY_SALARY * 0.85)
    elif my_hp <= 4.0:
        base = max(base, DAILY_SALARY * 0.65)

    # Cap relative to highest observed bid to avoid overpaying
    if highest_prev_bid > 0.0:
        base = min(base, highest_prev_bid + 2.0)

    bid = max(0.0, min(my_budget, base))

    # Ensure we bid at least a small positive amount if we can
    if bid <= 0.0 and my_budget > 0.0:
        bid = min(my_budget, 5.0)

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

    supply = float(day_context.get('supply', MIN_SUPPLY))
    day = int(day_context.get('day', 0))

    # Identify alive opponents and extract yesterday bids
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

    # If no one alive, conserve
    if not alive_opps:
        return max(0.0, min(float(my_status['budget']), DAILY_SALARY * 0.4))

    # Pressure estimate from yesterday
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = (sum(yesterday_bids) / len(yesterday_bids)) if yesterday_bids else 0.0

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))

    # Supply-based intensity: higher supply -> can be a bit more aggressive without risking long no-water streaks
    # Convert to a 0..1 factor using safe bounds
    if MAX_SUPPLY <= MIN_SUPPLY:
        supply_factor = 0.5
    else:
        supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    if supply_factor < 0.0:
        supply_factor = 0.0
    if supply_factor > 1.0:
        supply_factor = 1.0

    # Target bidding band exploiting yesterday: opponents who survived bid around 95-103.
    # Undercut slightly to win when they overpay.
    base_target = 0.0

    # If someone previously paid very high, we must respond to avoid being outbid on critical days.
    if highest_prev_bid >= DAILY_SALARY * 0.95:  # ~85.5
        # Healthy: bid just below the top pressure; low HP: bid near top.
        if my_hp > 4.0:
            base_target = highest_prev_bid * 0.92
        else:
            base_target = highest_prev_bid * 0.98
    else:
        # Otherwise, hover around the average pressure, slightly below it.
        if avg_prev_bid > 0.0:
            base_target = avg_prev_bid * 0.93
        else:
            base_target = DAILY_SALARY * (0.50 + 0.20 * supply_factor)

    # Ensure minimum meaningful bid to secure water when supply is scarce.
    scarcity_boost = 0.0
    if supply < 18.0:
        scarcity_boost = 0.10 * DAILY_SALARY

    # If my HP is critical, prioritize survival.
    if my_hp <= 2.0:
        base_target = max(base_target, DAILY_SALARY * 0.85)
    elif my_hp <= 4.0:
        base_target = max(base_target, DAILY_SALARY * 0.65)

    # Slightly increase bids later in episode to avoid falling behind.
    # Episode length is 10; day is 0..9 typically.
    progress = 0.0
    try:
        progress = float(day) / 9.0
    except Exception:
        progress = 0.0
    if progress < 0.0:
        progress = 0.0
    if progress > 1.0:
        progress = 1.0

    base_target = base_target + scarcity_boost + (DAILY_SALARY * 0.05 * progress)

    # Cap by budget and keep within a reasonable range.
    bid = min(my_budget, base_target)

    # Safety clamp: bid should be non-negative.
    if bid < 0.0:
        bid = 0.0

    # If budget is extremely low, bid what we can.
    if my_budget <= 1.0:
        return my_budget

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

    # Extract yesterday bids to infer their aggressiveness.
    yesterday_bids = []
    yesterday_trace_by_id = {}
    for opp_id, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                bid_val = float(bid)
            except Exception:
                bid_val = None
            if bid_val is not None:
                yesterday_bids.append(bid_val)
                yesterday_trace_by_id[opp_id] = bid_val

    # Baseline aggressiveness from market.
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / float(len(yesterday_bids))
    else:
        highest_prev_bid = DAILY_SALARY * 0.6
        avg_prev_bid = DAILY_SALARY * 0.6

    # Pressure signals from opponents' yesterday behavior and current status.
    # If someone is low on budget or near death, they may either overbid to survive or stop bidding.
    # We counter by staying just below the typical high bids unless we are in danger.
    near_death_count = 0
    low_budget_count = 0
    for opp_id, opp in alive_opps:
        opp_hp = float(opp.get('hp', 0))
        opp_budget = float(opp.get('budget', 0))
        if opp_hp <= 2.5:
            near_death_count += 1
        if opp_budget <= DAILY_SALARY * 0.6:
            low_budget_count += 1

    # Supply affects how many water units are likely contested.
    # For medium scenario supply ~15-25, assume only a few can secure WATER_REQ each day.
    # We'll bid around the observed equilibrium (~110-120) but slightly under to avoid overpaying.
    # Compute a target based on supply band.
    if supply <= float(MIN_SUPPLY):
        supply_factor = 1.05
    elif supply >= float(MAX_SUPPLY):
        supply_factor = 0.95
    else:
        supply_factor = 1.0

    # Core strategy:
    # - If my hp is low or I've gone several days without water, bid high.
    # - Otherwise, bid slightly below the average/highest yesterday bids.
    if hp <= 2.0 or no_water_days >= 2:
        # Urgent survival bid.
        target = max(avg_prev_bid * 0.98, highest_prev_bid * 0.98)
        target *= 1.02
    else:
        # Conservative: undercut the observed average/high.
        # If others are extremely aggressive (highest_prev_bid high), still undercut.
        aggressiveness = highest_prev_bid / float(DAILY_SALARY)
        if aggressiveness >= 1.5:
            target = avg_prev_bid * 0.94
        else:
            target = avg_prev_bid * 0.90

        # If many opponents are near death, risk of overbidding increases; adjust upward slightly.
        if near_death_count >= 2:
            target *= 1.05
        elif near_death_count == 1:
            target *= 1.02

        # If many have low budgets, they may not sustain high bids; adjust downward.
        if low_budget_count >= 2:
            target *= 0.96

    # Apply supply factor and cap by what we can afford.
    target *= supply_factor

    # Ensure we never bid negative and always respect budget.
    bid = max(0.0, min(budget, target))

    # Additional safeguard: if budget is very low, bid as much as possible to avoid elimination.
    if budget <= DAILY_SALARY * 0.25:
        bid = max(0.0, min(budget, DAILY_SALARY * 0.35))

    return float(bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    # Alive opponents
    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        try:
            if opp.get('alive', False):
                alive_opponents.append((opp_id, opp))
        except Exception:
            continue

    if not alive_opponents:
        # If alone, bid conservatively to still secure water.
        return max(1.0, min(my_status.get('budget', 0.0), DAILY_SALARY * 0.4))

    # Use yesterday's bid to infer aggressiveness.
    prev_bids = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_prev_bid = 0.0
    if len(prev_bids) >= 2:
        s = sorted(prev_bids)
        second_prev_bid = s[-2]

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Estimate how many water units exist relative to requirement.
    # supply is total water; each allocation is WATER_REQ.
    units = int(supply / float(WATER_REQ)) if WATER_REQ > 0 else 0
    units = max(0, min(units, 100))

    # If supply is tight (few units), competition increases -> bid higher but avoid matching extreme bids.
    tight = supply <= (MIN_SUPPLY + 1.0)

    # Base target bid: slightly above a typical opponent, but cap below yesterday's max to avoid Cindy-like waste.
    # Use second-highest to reduce overfitting to one extreme.
    target = DAILY_SALARY * 0.55

    if prev_bids:
        # If yesterday's highest was very high, others likely overreacted; we shade below it.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            target = max(DAILY_SALARY * 0.45, second_prev_bid + 1.0)
        else:
            target = max(DAILY_SALARY * 0.50, (highest_prev_bid + second_prev_bid) / 2.0 + 1.0)

    # Adjust for our urgency.
    if my_hp <= 2.5 or no_water_days >= 2:
        urgency = 1.0
    elif my_hp <= 4.5:
        urgency = 0.7
    else:
        urgency = 0.5

    if tight:
        target *= (1.0 + 0.25 * urgency)
    else:
        target *= (1.0 + 0.15 * urgency)

    # Hard caps to prevent budget exhaustion.
    # Keep some budget for later days; also avoid exceeding a fraction of max salary.
    max_bid = min(my_budget, DAILY_SALARY * (0.95 if my_hp <= 2.5 else 0.75))

    # Shade below highest previous bid to avoid Cindy-like death from overbidding.
    if prev_bids and highest_prev_bid > 0:
        target = min(target, highest_prev_bid * 0.85)

    bid = max(1.0, min(max_bid, target))

    # If budget is extremely low, bid all-in.
    if my_budget <= 5.0:
        bid = my_budget

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

    # If no one alive, spend enough to ensure we don't run out
    if not alive:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Read yesterday bids from previous_trace only
    yesterday_bids = []
    yesterday_pressures = []
    for _, o in alive:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass
        # Approximate pressure: if they had low hp after, assume they were close to failing
        hp_after = prev.get('hp_after', None)
        if hp_after is not None:
            try:
                yesterday_pressures.append((float(hp_after), float(b) if b is not None else 0.0))
            except Exception:
                pass

    # Base bid depends on our hp
    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])

    # Determine supply-driven urgency: if supply is closer to MIN, competition is higher.
    # Use a conservative scaling.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))
    # competition_factor higher when supply is low
    competition_factor = 1.15 - 0.3 * supply_ratio

    # If opponents were bidding high yesterday, they likely continue to fight for water.
    # Use their max bid as a proxy.
    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        # Thresholds relative to DAILY_SALARY
        high_thresh = DAILY_SALARY * 1.15  # ~103.5
        very_high_thresh = DAILY_SALARY * 1.6  # ~144

        # If we are low hp, we must secure water; otherwise, undercut.
        if my_hp <= 2.0:
            target = DAILY_SALARY * 0.95 * competition_factor
            # If someone was extremely high yesterday, match closer
            if max_prev_bid >= very_high_thresh:
                target = DAILY_SALARY * 1.05 * competition_factor
            return min(my_budget, max(1.0, target))

        if max_prev_bid >= very_high_thresh:
            # They were desperate; bid moderately to avoid losing entirely.
            target = DAILY_SALARY * 0.75 * competition_factor
            return min(my_budget, max(1.0, target))

        if max_prev_bid >= high_thresh:
            # Bid slightly below their likely continuation to win some allocation
            target = DAILY_SALARY * 0.62 * competition_factor
            return min(my_budget, max(1.0, target))

        # If yesterday bids were low, we can bid less.
        target = DAILY_SALARY * 0.48 * competition_factor
        return min(my_budget, max(1.0, target))

    # Fallback if no bid info
    if my_hp <= 2.0:
        return min(my_budget, max(1.0, DAILY_SALARY * 0.9))
    return min(my_budget, max(1.0, DAILY_SALARY * 0.55))
"""
