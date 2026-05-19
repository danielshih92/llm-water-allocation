# ============================================================
# Experiment: exp_050
# Agent: Bob
# Source: exp_050
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

    supply = day_context['supply']
    day = day_context['day']

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append(o)

    # If no opponents are alive, bid conservatively.
    if not alive_opponents:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read opponents' previous bids (yesterday) for immediate reaction.
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Baseline bid target based on our urgency.
    hp = float(my_status.get('hp', 0))
    no_water_days = int(my_status.get('no_water_days', 0))
    budget = float(my_status.get('budget', 0))

    # Estimate how many full requirements the supply can cover.
    # Indices are not needed, but keep numeric sanity.
    supply_int = int(supply)
    max_full = max(1, supply_int // int(WATER_REQ))

    # Determine aggressiveness from yesterday.
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev_bid
    else:
        highest_prev_bid = 0.0
        second_prev_bid = 0.0

    # Urgency adjustment: if we're close to failure, prioritize securing water.
    urgency = 0.0
    if no_water_days >= 2:
        urgency = 1.0
    elif no_water_days == 1:
        urgency = 0.6

    if hp <= 2.0:
        urgency = max(urgency, 1.0)
    elif hp <= 3.0:
        urgency = max(urgency, 0.7)

    # Compute a competitive bid.
    # If opponents bid very high yesterday, we contest but avoid overpaying.
    # If opponents were moderate, we bid slightly above their likely clearing level.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # High pressure: bid enough to win with moderate overtake.
        target = max(highest_prev_bid * 0.85, second_prev_bid + 1.5)
        # If we're in trouble, increase aggressiveness.
        target = target + (DAILY_SALARY * 0.15 * urgency)
    else:
        # Low/moderate pressure: bid around their level to secure water efficiently.
        # Use highest_prev_bid as a proxy; if it's too low, still bid a sensible amount.
        target = max(highest_prev_bid + 1.0, DAILY_SALARY * (0.45 + 0.25 * urgency))

    # Convert target into a bid bounded by budget and plausible supply scale.
    # Bids above supply are typically wasteful; cap using supply and requirement scale.
    # Ensure we can always bid at least something non-negative.
    cap = min(budget, DAILY_SALARY * 1.0)

    # Additional cap tied to supply: if supply is low, don't overbid far beyond what would be rational.
    # Approximate: per-unit water cost should not exceed budget fraction.
    supply_cap = min(cap, (supply_int / float(WATER_REQ)) * DAILY_SALARY)

    bid = min(cap, supply_cap, target)

    # If our urgency is high and bid is too low, bump it.
    if urgency >= 0.7 and bid < DAILY_SALARY * 0.6:
        bid = min(budget, DAILY_SALARY * 0.75)

    # Final safety: non-negative.
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return float(min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace for immediate reaction
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    prev_bids.append(float(b))
                except Exception:
                    pass

    # Estimate how aggressive the field was yesterday
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        avg_prev_bid = sum(prev_bids) / float(len(prev_bids))
    else:
        highest_prev_bid = 0.0
        avg_prev_bid = DAILY_SALARY * 0.6

    # Supply pressure: higher supply reduces need to overbid
    # Map supply in [15,25] to a factor in [1.05,0.85]
    if MAX_SUPPLY != MIN_SUPPLY:
        supply_factor = 1.05 - 0.2 * ((supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY))
    else:
        supply_factor = 1.0

    # HP urgency: if low HP or several no-water days, bid harder
    hp_urgency = 1.0
    if my_hp <= 2:
        hp_urgency = 1.25
    elif my_hp <= 4:
        hp_urgency = 1.12
    if my_no_water_days >= 2:
        hp_urgency *= 1.15

    # Target bid: aim slightly below yesterday's highest if I'm healthy,
    # but move toward avg if I'm in danger.
    base_target = avg_prev_bid * 0.95
    if my_hp <= 4 or my_no_water_days >= 2:
        base_target = max(base_target, avg_prev_bid * 1.02)

    # If someone was extremely aggressive yesterday, avoid getting undercut too much
    if highest_prev_bid > DAILY_SALARY * 0.85:
        base_target = max(base_target, highest_prev_bid * 0.92)

    bid = base_target * supply_factor * hp_urgency

    # Keep within budget and avoid irrationally high bids
    # Soft cap: don't exceed 1.2*DAILY_SALARY unless critical HP
    critical = (my_hp <= 2 or my_no_water_days >= 3)
    hard_cap = DAILY_SALARY * (1.5 if critical else 1.2)

    bid = min(bid, hard_cap, my_budget)

    # Ensure non-negative
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

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 1)

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    # If no opponents, just bid enough to secure water while respecting budget.
    if not alive_opps:
        return max(0.0, min(float(my_status['budget']), DAILY_SALARY * 0.6))

    # Read yesterday bids from traces for immediate reaction.
    prev_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate likely competing pressure from yesterday.
    # Cindy survived with high hp and high average bid, so she likely remains aggressive.
    # Alex ended with low hp after high bids, so she may either continue or drop; both can be exploited.
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev_bid
    else:
        highest_prev_bid = 0.0
        second_prev_bid = 0.0

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))

    # Determine how many water units are even possible today.
    # Supply is continuous, but bids decide allocation; we use supply to scale aggressiveness.
    # If supply is tight near MIN_SUPPLY, we must bid more to avoid no-water days.
    tightness = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    tightness = max(0.0, min(1.0, tightness))

    # Base target bid: aim slightly above the conservative competitor level.
    # Use a cap to avoid matching Cindy's ceiling (around 150 in trace).
    cindy_cap = 145.0

    # If yesterday pressure was high, increase bid; otherwise stay moderate.
    # Pressure heuristic: if highest_prev_bid is near/above 150, opponents are bidding hard.
    high_pressure = highest_prev_bid >= 145.0

    if high_pressure:
        # We don't want to fully mirror the top bid; instead, bid around the second-highest plus a small edge.
        target = second_prev_bid + 5.0
        # But also ensure enough when supply is tight.
        if tightness < 0.5:
            target += 10.0
    else:
        target = max(DAILY_SALARY * 0.45, second_prev_bid * 0.75 + 10.0)
        if tightness < 0.5:
            target += 10.0

    # HP-based adjustment: if we're low, bid harder.
    if my_hp <= 2.0:
        target *= 1.25
    elif my_hp <= 4.0:
        target *= 1.10

    # Budget safety: never bid more than we can afford.
    # Also avoid spending too much early in episode; but meta-round is 3/10, so keep moderate.
    spend_limit = my_budget

    # Final clamp: keep within [0, spend_limit] and below cap to exploit others' aggressiveness.
    target = min(target, cindy_cap)
    bid = max(0.0, min(spend_limit, target))

    # If budget is extremely low, bid minimal to preserve remaining budget.
    if my_budget <= DAILY_SALARY * 0.2:
        bid = min(my_budget, DAILY_SALARY * 0.15)

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

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Read yesterday bids from previous_trace (immediate reaction)
    prev_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    prev_bids.append(float(b))
                except Exception:
                    pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate how many water units are likely needed today.
    # If supply is high, one unit is easier to secure; if low, we must fight more.
    # Use a conservative target bid based on competition pressure.
    supply_ratio = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Base aggressiveness: higher when yesterday bidding was intense.
    # David/Eric averaged ~78-83; use that signal.
    pressure = 0.0
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        pressure = 1.0
    elif highest_prev_bid >= DAILY_SALARY * 0.65:
        pressure = 0.7
    elif highest_prev_bid >= DAILY_SALARY * 0.45:
        pressure = 0.45
    else:
        pressure = 0.25

    # If my HP is low or I've had no water days, bid more to avoid imminent death.
    urgency = 0.0
    if my_hp <= 2:
        urgency = 1.0
    elif my_hp <= 4:
        urgency = 0.7
    elif my_no_water_days >= 2:
        urgency = 0.6
    else:
        urgency = 0.3

    # Decide target bid.
    # When supply is high, we can bid slightly less; when low, bid more.
    # Combine pressure and urgency.
    target_multiplier = 0.45 + 0.35 * pressure + 0.25 * urgency - 0.15 * supply_ratio
    target_multiplier = max(0.25, min(0.95, target_multiplier))

    target_bid = DAILY_SALARY * target_multiplier

    # Never bid above budget.
    bid = min(my_budget, target_bid)

    # If budget is too small, still try to avoid death when urgent.
    if bid < 1e-6 and (my_hp <= 4 or my_no_water_days >= 2):
        return min(my_budget, DAILY_SALARY * 0.9)

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

    # Alive opponents only
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # If no opponents alive, spend enough to secure survival comfortably.
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Extract yesterday bids from immediate previous_trace only.
    prev_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate how competitive the market was yesterday.
    highest_prev = max(prev_bids) if prev_bids else 0.0
    second_prev = 0.0
    if len(prev_bids) >= 2:
        srt = sorted(prev_bids, reverse=True)
        second_prev = srt[1]

    # Supply pressure: if supply is low, everyone must bid more to secure water.
    # Convert to a rough number of water units needed/available.
    # Use explicit int() for indices; here only scalars.
    supply_ratio = (supply - MIN_SUPPLY) / max(1e-9, (MAX_SUPPLY - MIN_SUPPLY))
    # supply_ratio in [0,1] roughly; lower supply -> closer to 0.

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))

    # Base target bid band.
    # Yesterday highest was around 163.5 max in meta-round context, with typical high bids ~145.
    # We'll undercut slightly when supply is moderate/high; bid closer to top when supply is low or hp is critical.
    critical_hp = 2.5

    # Determine aggressiveness.
    if hp <= critical_hp:
        # Need water now.
        target = max(DAILY_SALARY * 0.75, highest_prev * 0.92) if highest_prev > 0 else DAILY_SALARY * 0.85
    else:
        # If supply is scarce, raise bid; if abundant, undercut.
        if supply_ratio < 0.35:
            target = max(DAILY_SALARY * 0.65, highest_prev * 0.88) if highest_prev > 0 else DAILY_SALARY * 0.7
        elif supply_ratio < 0.7:
            # Undercut top a bit.
            if highest_prev > 0:
                target = max(DAILY_SALARY * 0.55, highest_prev * 0.82)
            else:
                target = DAILY_SALARY * 0.6
        else:
            # Plenty of supply: conserve budget; still try to beat likely bids.
            if second_prev > 0:
                target = max(DAILY_SALARY * 0.45, second_prev * 0.98)
            elif highest_prev > 0:
                target = max(DAILY_SALARY * 0.45, highest_prev * 0.78)
            else:
                target = DAILY_SALARY * 0.5

    # Small day-based jitter (deterministic) to avoid exact ties.
    # Use day parity only.
    if int(day) % 2 == 0:
        target *= 0.995
    else:
        target *= 1.005

    # Ensure we bid at least enough to matter, but never exceed budget.
    # Also avoid bidding extremely low when hp is not great.
    min_bid = 0.15 * DAILY_SALARY
    if hp <= 4:
        min_bid = 0.35 * DAILY_SALARY

    bid = float(min(budget, max(min_bid, target)))
    # If budget is extremely low, just bid what we can.
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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        cap = min(budget, DAILY_SALARY * 0.4)
        return max(0.0, cap)

    # Extract yesterday bids from immediate previous_trace
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

    # Supply pressure: higher supply reduces need to overbid
    # Normalize supply to [0,1] where 0 is MIN_SUPPLY, 1 is MAX_SUPPLY
    denom = (MAX_SUPPLY - MIN_SUPPLY)
    if denom <= 0:
        supply_norm = 0.5
    else:
        supply_norm = (supply - MIN_SUPPLY) / denom
        if supply_norm < 0.0:
            supply_norm = 0.0
        if supply_norm > 1.0:
            supply_norm = 1.0

    # Base bid: aim to secure enough water for our requirement without matching overbidders
    # If supply is tight (low norm), bid closer to salary; if abundant, bid closer to mid.
    base = DAILY_SALARY * (0.35 + 0.35 * (1.0 - supply_norm))

    # If we are in danger (low HP or accumulating no-water days), increase bid aggressiveness
    danger = 0.0
    if hp <= 2.0:
        danger += 1.0
    if no_water_days >= 2:
        danger += 0.6
    if hp <= 4.0:
        danger += 0.4

    # If opponents were bidding very high yesterday, they likely value survival strongly.
    # Underbid slightly when we're safe; overbid when we're in danger.
    high_opponent = 1.0 if highest_prev_bid >= DAILY_SALARY * 0.85 else 0.0

    if high_opponent > 0.5:
        if danger >= 1.0:
            target = DAILY_SALARY * 0.95
        else:
            # Slight undercut/near-match
            target = min(DAILY_SALARY * 0.75, highest_prev_bid * 0.98)
    else:
        target = base
        if danger >= 1.0:
            target = max(target, DAILY_SALARY * 0.8)

    # Final cap by budget and non-negative
    bid = min(budget, target)
    if bid < 0.0:
        bid = 0.0

    # If supply is extremely low, add a small bump to avoid being starved
    if supply <= (MIN_SUPPLY + 1.0):
        bid = min(budget, bid + DAILY_SALARY * 0.08)

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

    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    if not alive:
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday bids from surviving opponents only (immediate reaction)
    prev_bids = []
    for oid, o in alive:
        prev = o.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate how aggressive others were yesterday
    if prev_bids:
        prev_max = max(prev_bids)
        prev_avg = sum(prev_bids) / float(len(prev_bids))
    else:
        prev_max = 0.0
        prev_avg = 0.0

    # Supply pressure: higher supply reduces need to overbid; lower supply increases need
    # Use a smooth factor between MIN_SUPPLY and MAX_SUPPLY.
    if MAX_SUPPLY == MIN_SUPPLY:
        supply_factor = 0.5
    else:
        supply_factor = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)  # 0 at high supply, 1 at low supply

    # Base bid target: slightly above yesterday average when supply is tight,
    # but cap below yesterday max to avoid wasting budget.
    # Also adapt to our HP.
    if hp <= 2.0 or no_water_days >= 1:
        hp_factor = 1.0  # urgent
    elif hp <= 4.0:
        hp_factor = 0.75
    else:
        hp_factor = 0.55

    # Target band
    # If others were bidding strongly yesterday, we must respond.
    if prev_max >= DAILY_SALARY * 0.8:
        target = max(prev_avg + 5.0, DAILY_SALARY * (0.55 + 0.25 * supply_factor))
    else:
        target = max(DAILY_SALARY * (0.45 + 0.25 * supply_factor), prev_avg * 0.9 + 10.0)

    target *= hp_factor

    # Convert to an integer bid and keep within budget
    # Also ensure bid is not trivially low.
    min_reasonable = DAILY_SALARY * 0.35
    bid = max(min_reasonable, target)

    # If budget is extremely low, bid conservatively but non-zero
    if budget <= 1.0:
        return 0.0

    bid = min(bid, budget)

    # Avoid bidding above what we can sustain: at most 1 day's salary fraction
    bid_cap = min(budget, DAILY_SALARY * 0.95)
    bid = min(bid, bid_cap)

    # Final integer conversion (bids are typically numeric; enforce int for stability)
    try:
        bid_int = int(bid)
    except Exception:
        bid_int = int(float(bid))

    if bid_int < 0:
        bid_int = 0
    return bid_int
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

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return float(min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from traces for immediate reaction
    prev_bids = []
    prev_pressures = []  # (bid, opp_hp_after)
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                b_val = float(b)
            except Exception:
                continue
            prev_bids.append(b_val)
            hp_after = prev.get('hp_after', o.get('hp', 0))
            try:
                hp_after_val = float(hp_after)
            except Exception:
                hp_after_val = 0.0
            prev_pressures.append((b_val, hp_after_val))

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    # Estimate how many water units are likely contested given supply.
    # If supply is high, we can bid lower; if supply is tight, bid higher.
    # Indices guarded by int() only where needed (none here).
    tightness = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        tightness = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)  # 0 when high supply, 1 when low
    tightness = max(0.0, min(1.0, float(tightness)))

    # Risk control: if we're already on many no-water days or low hp, bid more.
    urgent = 0.0
    if hp <= 2.0:
        urgent += 1.0
    if no_water_days >= 2:
        urgent += 1.0
    urgent = max(0.0, min(2.0, urgent))

    # Strategy: avoid Cindy-like overbidding unless supply is tight and/or we are urgent.
    # Use yesterday highest bid as a signal of aggression in the population.
    # Base target is a percentile of yesterday bids, adjusted by tightness and urgency.
    # If highest_prev_bid is very large, we assume at least one agent overcommitted.
    base = DAILY_SALARY * (0.35 + 0.35 * tightness)  # 31.5..63

    # If yesterday aggression was high, slightly increase to beat likely winners.
    aggression_factor = 0.0
    if highest_prev_bid > DAILY_SALARY * 1.2:
        aggression_factor = 0.15
    elif highest_prev_bid > DAILY_SALARY * 0.8:
        aggression_factor = 0.08

    # Urgency bumps
    urgency_bump = 0.0
    if urgent >= 2.0:
        urgency_bump = 0.35
    elif urgent >= 1.0:
        urgency_bump = 0.2

    # Compute target bid
    target = base * (1.0 + aggression_factor + urgency_bump)

    # Ensure we don't bid more than budget or an extreme fraction.
    # If budget is low, bid a conservative amount to preserve future rounds.
    max_affordable = budget
    conservative_cap = DAILY_SALARY * (0.95 if urgent >= 1.0 else 0.65)
    cap = min(max_affordable, conservative_cap)

    # If supply is extremely tight, push closer to cap.
    if tightness >= 0.8 and urgent >= 1.0:
        target = max(target, cap * 0.75)
    elif tightness >= 0.8:
        target = max(target, cap * 0.55)

    # If we are not urgent and supply is not tight, keep low to avoid wasting budget.
    if urgent < 1.0 and tightness <= 0.4:
        target = min(target, cap * 0.55)

    # Final clamp and slight anti-tie randomness based on day (deterministic)
    # to prevent exact collisions.
    jitter = 0.98 + ((int(day) % 7) * 0.01)  # 0.98..1.04
    target = target * jitter

    bid = float(min(max(target, 0.0), cap))
    # Ensure at least a minimal bid if we can.
    if bid < 1.0 and budget >= 1.0:
        bid = 1.0
    return bid
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

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive = []
    for agent_id, st in opponents_status.items():
        if st.get('alive', False):
            alive.append((agent_id, st))

    if not alive:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace for immediate reaction.
    cindy_trace = None
    max_prev_bid = -1.0
    prev_bids = []
    for agent_id, st in alive:
        prev = st.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                bid_val = float(bid)
            except Exception:
                continue
            prev_bids.append(bid_val)
            if bid_val > max_prev_bid:
                max_prev_bid = bid_val
            if agent_id == 'Cindy':
                cindy_trace = bid_val

    # Supply pressure estimate: higher supply reduces need to overbid.
    # Use a simple normalized factor.
    supply_norm = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_norm = max(0.0, min(1.0, supply_norm))

    # Base bid: aim to be competitive but not waste budget.
    # If supply is low (near 15), bid more; if high (near 25), bid less.
    base = DAILY_SALARY * (0.62 - 0.18 * supply_norm)

    # If Cindy was high yesterday, we anticipate continued pressure.
    cindy_high = False
    if cindy_trace is not None and cindy_trace >= DAILY_SALARY * 0.85:
        cindy_high = True

    # HP-aware escalation.
    # If my HP is low or I've had no water days, I must secure water.
    low_hp = my_hp <= 3.0
    urgent = low_hp or my_no_water_days >= 2

    # If yesterday there was a very high bid, slightly follow to avoid losing.
    if max_prev_bid >= DAILY_SALARY * 1.45:
        base = DAILY_SALARY * (0.75 - 0.12 * supply_norm)

    if urgent:
        target = DAILY_SALARY * (0.95 - 0.10 * supply_norm)
    elif cindy_high:
        target = base + DAILY_SALARY * 0.18
    else:
        target = base

    # Cap by budget and keep within reasonable bounds.
    target = max(0.0, min(my_budget, target))

    # If budget is too low, bid what we can.
    if my_budget <= 1e-6:
        return 0.0

    return float(target)
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

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for oid, o in opponents_status.items():
        try:
            if o.get('alive', False):
                alive_opps.append((oid, o))
        except Exception:
            continue

    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace for immediate reaction
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', None)
        if isinstance(prev, dict) and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Base willingness: ensure we can win when supply is tight, but avoid Cindy-like overbidding.
    supply_tight = supply <= (MIN_SUPPLY + 1.0)  # around 15-16
    supply_mid = supply <= 20.0

    # If opponents previously bid aggressively, we increase slightly to avoid losing to them.
    opp_pressure = 0.0
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        opp_pressure = 1.0
    elif highest_prev_bid >= DAILY_SALARY * 0.5:
        opp_pressure = 0.6
    else:
        opp_pressure = 0.3

    # HP urgency
    if my_hp <= 2:
        hp_factor = 1.0
    elif my_hp <= 4:
        hp_factor = 0.75
    else:
        hp_factor = 0.55

    # If we've already gone without water multiple days, bid more.
    if my_no_water_days >= 3:
        no_water_factor = 1.0
    elif my_no_water_days >= 1:
        no_water_factor = 0.85
    else:
        no_water_factor = 0.6

    # Target bid range
    if supply_tight:
        base = DAILY_SALARY * 0.65
    elif supply_mid:
        base = DAILY_SALARY * 0.55
    else:
        base = DAILY_SALARY * 0.45

    target = base * (0.7 + 0.6 * opp_pressure) * (0.5 + 0.5 * hp_factor) * (0.5 + 0.5 * no_water_factor)

    # Cap to budget and avoid extreme overbids
    # Keep below Cindy's observed max (~155) unless my HP is critical.
    if my_hp <= 2:
        cap = min(my_budget, DAILY_SALARY * 1.1)
    else:
        cap = min(my_budget, DAILY_SALARY * 0.95)

    bid = max(0.0, min(float(my_budget), target, cap))

    # If budget is too low, bid whatever we can.
    if my_budget <= 1.0:
        return max(0.0, my_budget)

    return bid
"""
