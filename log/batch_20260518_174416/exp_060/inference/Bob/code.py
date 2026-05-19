# ============================================================
# Experiment: exp_060
# Agent: Bob
# Source: exp_060
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

    # Identify alive opponents
    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    # If no opponents, bid based on survival needs
    if len(alive_opponents) == 0:
        if my_status['hp'] <= 2:
            return min(my_status['budget'], DAILY_SALARY * 0.9)
        if my_status['no_water_days'] >= 2:
            return min(my_status['budget'], DAILY_SALARY * 0.65)
        return min(my_status['budget'], DAILY_SALARY * 0.5)

    # Read yesterday bids from previous_trace
    yesterday_bids = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Estimate aggressiveness
    highest_prev_bid = max(yesterday_bids) if len(yesterday_bids) > 0 else 0.0
    avg_prev_bid = sum(yesterday_bids) / float(len(yesterday_bids)) if len(yesterday_bids) > 0 else 0.0

    # Supply pressure: closer to MIN_SUPPLY means more scarce
    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)  # 0..1-ish
    scarcity = max(0.0, min(1.0, scarcity))

    # Base target bid: aim to secure enough water without overpaying
    # If supply is low, increase bid modestly.
    # If opponents were aggressive yesterday, we hold unless our hp is critical.
    critical_hp = my_status['hp'] <= 2
    low_water_risk = my_status['no_water_days'] >= 2

    # Determine a reference bid from yesterday behavior
    # If they were bidding high, don't chase unless needed.
    aggressive_threshold = DAILY_SALARY * 0.85

    if highest_prev_bid >= aggressive_threshold:
        # Opponents likely fear running out; conserve unless critical.
        if critical_hp:
            target = DAILY_SALARY * (0.75 + 0.2 * scarcity)
        elif low_water_risk:
            target = DAILY_SALARY * (0.6 + 0.15 * scarcity)
        else:
            # Let them overpay; bid just enough to compete slightly.
            target = max(DAILY_SALARY * 0.45, avg_prev_bid * 0.75)
            target = target * (0.85 + 0.1 * scarcity)
    else:
        # They weren't too aggressive; attempt to win by bidding around their average/high.
        # Slightly above avg to steal allocation when possible.
        if len(yesterday_bids) > 0:
            target = avg_prev_bid + 0.1 * (highest_prev_bid - avg_prev_bid) + 5.0
        else:
            target = DAILY_SALARY * (0.55 + 0.2 * scarcity)
        # If my hp is low, increase.
        if critical_hp:
            target = max(target, DAILY_SALARY * 0.75)
        elif low_water_risk:
            target = max(target, DAILY_SALARY * 0.65)

    # Convert target to a bid that is safe w.r.t. budget and water need.
    # We can't buy fractional water; bids are just numbers, but we cap at what we can afford.
    bid = min(my_status['budget'], target)

    # Additional sanity: if supply is extremely low, bias upward.
    if supply <= float(WATER_REQ):
        bid = min(my_status['budget'], max(bid, DAILY_SALARY * 0.7 + 10.0 * scarcity))

    # Ensure non-negative
    if bid < 0:
        bid = 0.0

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

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday bids from previous_trace for immediate competitive signal
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Competitive band from yesterday (Alex/Eric/Cindy were active around ~75-88)
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        second = sorted(prev_bids, reverse=True)[1] if len(prev_bids) > 1 else highest_prev_bid
    else:
        highest_prev_bid = 0.0
        second = 0.0

    # Decide aggressiveness based on supply and my survival pressure
    supply_frac = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_frac = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_frac = max(0.0, min(1.0, supply_frac))

    # If I'm low HP or have consecutive no-water days, bid more to secure water
    urgent = (hp <= 2.5) or (no_water_days >= 2)

    # Baseline bid targets
    # - If supply is high, we can undercut slightly.
    # - If supply is low, we bid closer to the competitive band.
    if supply_frac >= 0.6:
        target = max(DAILY_SALARY * 0.45, second + 1.0)
    elif supply_frac >= 0.3:
        target = max(DAILY_SALARY * 0.55, (second + highest_prev_bid) / 2.0)
    else:
        target = max(DAILY_SALARY * 0.65, highest_prev_bid - 2.0)

    # Adjust for urgency and avoid overspending
    if urgent:
        target = max(target, highest_prev_bid - 1.0)
        target = max(target, DAILY_SALARY * 0.85)
    else:
        # Not urgent: try to win with a slight undercut to save budget
        target = min(target, highest_prev_bid + 0.5)
        target = target * 0.95

    # Hard caps by budget and reasonable maximum
    # Prevent bidding above what would likely waste money relative to daily salary.
    max_reasonable = DAILY_SALARY * (0.95 if urgent else 0.75)
    bid = min(budget, max_reasonable, target)

    # Ensure non-negative and at least a small bid if budget allows
    if bid < 0.0:
        bid = 0.0
    if bid == 0.0 and budget > 0.0:
        bid = min(budget, DAILY_SALARY * 0.1)

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
    day = day_context.get('day', 0)

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # If no opponents alive, bid conservatively.
    if not alive_opps:
        cap = min(budget, DAILY_SALARY * 0.4)
        return max(0.0, cap)

    # Read yesterday bids from previous_trace for immediate reaction.
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate competitive pressure from yesterday.
    pressure = 0.0
    if prev_bids:
        pressure = max(prev_bids)

    # Supply factor: when supply is higher, we can bid less and still win.
    if supply >= 22.0:
        supply_factor = 0.78
    elif supply >= 18.0:
        supply_factor = 0.84
    else:
        supply_factor = 0.92

    # HP/urgency: if we're low or have accumulated no-water days, increase.
    urgency = 1.0
    if hp <= 2.0:
        urgency = 1.15
    elif hp <= 4.0:
        urgency = 1.08
    if no_water_days >= 2:
        urgency += 0.08

    # Baseline bid: undercut the observed max pressure slightly.
    # If opponents were bidding very high, we avoid matching exactly.
    baseline = DAILY_SALARY * 0.55
    if pressure > 0:
        # Undercut by ~10% but keep above baseline.
        baseline = max(baseline, pressure * 0.90)

    target = baseline * supply_factor * urgency

    # Ensure we don't overcommit beyond a reasonable fraction of budget.
    # If budget is tight, scale down.
    max_fraction = 0.95
    if budget <= DAILY_SALARY:
        max_fraction = 0.85
    cap = budget * max_fraction

    bid = min(target, cap)

    # If hp is critically low, we must bid close to cap.
    if hp <= 1.5:
        bid = min(budget, max(bid, DAILY_SALARY * 0.9))

    # Final clamp.
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = day_context['supply']
    day = day_context['day']

    # Alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive'):
            alive_opps.append(o)

    # If no opponents, buy enough to cover requirement
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace only
    prev_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            prev_bids.append(float(b))

    # Estimate opponent aggressiveness
    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / float(len(prev_bids))
    else:
        highest_prev = 0.0
        avg_prev = DAILY_SALARY * 0.6

    # Supply pressure: higher supply reduces need to overbid
    # Map supply range [15,25] to a pressure factor in [1.15,0.85]
    if MAX_SUPPLY != MIN_SUPPLY:
        t = (float(supply) - float(MIN_SUPPLY)) / float(MAX_SUPPLY - MIN_SUPPLY)
    else:
        t = 0.5
    if t < 0.0:
        t = 0.0
    if t > 1.0:
        t = 1.0
    pressure = 1.15 - 0.30 * t

    # HP-based urgency
    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))

    # Base bid target: slightly above average, but below highest to preserve budget
    # Use highest_prev to react to aggressive meta.
    # Target band depends on our HP.
    if hp <= 2.0:
        hp_factor = 0.95
    elif hp <= 4.0:
        hp_factor = 0.80
    elif hp <= 7.0:
        hp_factor = 0.68
    else:
        hp_factor = 0.60

    # Compute a candidate bid
    # If opponents were very aggressive yesterday, we try to beat them but not fully match max.
    aggressive_threshold = DAILY_SALARY * 0.85
    if highest_prev >= aggressive_threshold:
        # Beat the pack: aim at 0.92*highest or 1.05*avg, whichever is lower
        target = min(0.92 * highest_prev, 1.05 * avg_prev)
    else:
        # Normal: aim around 1.00*avg_prev, with pressure adjustment
        target = 1.00 * avg_prev

    target = target * float(pressure) * float(hp_factor)

    # Ensure we don't exceed budget
    bid = min(budget, target)

    # Safety floor: if we are bidding too low relative to typical prices, raise slightly
    # to avoid being consistently outbid.
    min_reasonable = max(DAILY_SALARY * 0.35, 0.55 * avg_prev)
    if bid < min_reasonable:
        bid = min(budget, min_reasonable * float(pressure) * 0.95)

    # If budget is very low, still bid something proportional to avoid total starvation
    if bid <= 0.0:
        bid = min(budget, DAILY_SALARY * 0.1)

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

    # Alive opponents and their yesterday bids
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # If no opponents, bid conservatively
    if not alive_opps:
        return float(min(my_status.get('budget', 0.0), DAILY_SALARY * 0.4))

    yesterday_bids = []
    yesterday_hp_after = []
    for oid, o in alive_opps:
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

    # Baseline from supply: aim to secure at least one full requirement share when possible
    # (We don't know pricing, so translate supply pressure into a bid scale.)
    supply_band = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_band = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_band = max(0.0, min(1.0, supply_band))

    # Use yesterday's max/median bid to infer who is likely to pressure today
    max_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    sorted_bids = sorted(yesterday_bids) if yesterday_bids else []
    median_prev_bid = 0.0
    if sorted_bids:
        mid = len(sorted_bids) // 2
        median_prev_bid = float(sorted_bids[mid])

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))

    # If Cindy-style extreme pressure existed yesterday, avoid matching it; still bid enough to beat low bidders.
    # Heuristic thresholds based on observed yesterday: Cindy ~160+, David ~22, Eric ~149.
    extreme_pressure = max_prev_bid >= 150.0
    high_pressure = max_prev_bid >= 120.0

    # Determine target bid
    # - If I'm low HP, I must bid more.
    # - If yesterday showed extreme pressure, bid around (median + margin) rather than max.
    # - Otherwise, bid around median or a supply-adjusted mid.
    if my_hp <= 2.0:
        base = max(median_prev_bid + 10.0, DAILY_SALARY * 0.85)
    elif my_hp <= 4.0:
        base = max(median_prev_bid + 7.0, DAILY_SALARY * 0.65)
    else:
        if extreme_pressure:
            # Cindy likely spends to survive; don't chase max. Beat the low/medium bidders.
            base = max(median_prev_bid + 5.0, DAILY_SALARY * (0.45 + 0.15 * supply_band))
        elif high_pressure:
            base = max(median_prev_bid + 3.0, DAILY_SALARY * (0.55 + 0.10 * supply_band))
        else:
            base = max(median_prev_bid, DAILY_SALARY * (0.40 + 0.10 * supply_band))

    # Cap by budget and also avoid overspending beyond what supply suggests
    # Supply suggests how many batches might exist; translate to a soft cap.
    # When supply is higher, we can bid slightly less.
    # batches ~ supply/WATER_REQ
    batches = supply / float(WATER_REQ) if WATER_REQ > 0 else 1.0
    # soft cap factor: more batches => lower cap
    cap_factor = 1.0
    if batches >= 2.0:
        cap_factor = 0.9
    elif batches <= 1.2:
        cap_factor = 1.05

    bid = base * cap_factor

    # Final constraints
    if my_budget <= 0.0:
        return 0.0
    bid = min(bid, my_budget)

    # Ensure non-negative float
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
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Yesterday trace reaction: infer aggressiveness.
    # We only use previous_trace from each opponent.
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Base bid derived from supply pressure.
    # If supply is near minimum, competition likely matters more.
    # Map supply in [15,25] to a multiplier in [0.65,1.0]
    if MAX_SUPPLY <= MIN_SUPPLY:
        supply_mult = 1.0
    else:
        t = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
        if t < 0.0:
            t = 0.0
        if t > 1.0:
            t = 1.0
        supply_mult = 0.65 + 0.35 * t

    # Target bid budget fraction: moderate by default.
    # Increase if our hp/no_water_days are critical.
    if hp <= 1.5 or no_water_days >= 2:
        frac = 0.85
    elif hp <= 3.0 or no_water_days >= 1:
        frac = 0.65
    else:
        frac = 0.45

    # If someone was extremely aggressive yesterday, we slightly raise to avoid being starved.
    # Cindy-like behavior corresponds to very high previous bids.
    if highest_prev_bid >= DAILY_SALARY * 1.4:
        frac = max(frac, 0.60)
    elif highest_prev_bid >= DAILY_SALARY * 0.9:
        frac = max(frac, 0.52)

    bid = budget * frac

    # Add a small supply-scaled floor to ensure we participate when supply is tight.
    # Use int() indices only where needed; none here.
    floor_bid = DAILY_SALARY * 0.35 * supply_mult
    if bid < floor_bid:
        bid = floor_bid

    # Cap: never exceed what we can spend.
    if bid > budget:
        bid = budget

    # Also avoid overbidding beyond a reasonable ceiling.
    ceiling = DAILY_SALARY * 0.95
    if bid > ceiling:
        bid = ceiling

    # Ensure non-negative.
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Identify alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # If no opponents alive, conserve
    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Read yesterday bids from previous_trace only
    prev_bids = []
    for o in alive_opps:
        pt = o.get('previous_trace', {})
        if isinstance(pt, dict):
            b = pt.get('bid', None)
            if b is not None:
                try:
                    prev_bids.append(float(b))
                except Exception:
                    pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Pressure estimate: if someone was willing to spend a lot, they likely continued
    # but we don't know today's hidden bids; we only react conservatively.
    high_pressure = highest_prev_bid >= DAILY_SALARY * 1.3  # ~117

    # Compute how many
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
    day = int(day_context['day'])

    # Alive opponents and their yesterday bids
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', True):
            alive_opps.append((opp_id, opp))

    # If no one alive, bid conservatively
    if not alive_opps:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.4))

    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Estimate how competitive the market was yesterday
    # If bids were huge, we should not underbid, but also avoid matching the top.
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    median_prev_bid = 0.0
    if yesterday_bids:
        s = sorted(yesterday_bids)
        mid = len(s) // 2
        median_prev_bid = s[mid] if len(s) % 2 == 1 else 0.5 * (s[mid - 1] + s[mid])

    # My urgency: if low hp or already had no-water days, increase pressure.
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = float(my_status.get('no_water_days', 0))

    # Base bid tied to supply: more supply => lower competitive bid needed.
    # supply is between 15 and 25. Map roughly to [0.6, 1.0] multiplier.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))
    supply_multiplier = 0.6 + 0.4 * supply_ratio

    # Competitive target: slightly above median, but capped below the highest aggressor.
    # If highest is extremely high, still stay below it to conserve.
    target = median_prev_bid * 1.08
    if highest_prev_bid > 0:
        # Keep target within a band relative to highest
        target = min(target, highest_prev_bid * 0.78)
        # Ensure not too low when market was very hot
        target = max(target, highest_prev_bid * 0.45)

    # Urgency adjustments
    if hp <= 2.0 or no_water_days >= 2.0:
        target *= 1.35
    elif hp <= 4.0 or no_water_days >= 1.0:
        target *= 1.18
    else:
        target *= 0.98

    target *= supply_multiplier

    # Also anchor to my daily salary: never bid more than salary * 0.95 unless desperate.
    desperate = (hp <= 1.0) or (no_water_days >= 3.0)
    cap = DAILY_SALARY * (0.95 if desperate else 0.75)
    target = min(target, cap)

    # If target is too low and supply is tight for my requirement, bump.
    # Tightness: if supply is near minimum, water is scarce.
    if supply <= (MIN_SUPPLY + 1.0):
        target = max(target, DAILY_SALARY * 0.5)

    # Final feasible bid
    bid = max(0.0, min(budget, target))

    # If budget is extremely low, bid whatever remains.
    if budget <= 1e-6:
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # If no one alive, conserve budget
    if not alive_opps:
        return max(0.0, min(float(my_status['budget']), DAILY_SALARY * 0.4))

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    # Read yesterday bids to infer aggressiveness
    yesterday_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Identify if any opponent was in trouble yesterday (likely over/under-bid)
    trouble_count = 0
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev:
            hp_after = prev.get('hp_after', None)
            status = prev.get('status', '')
            if (hp_after is not None and float(hp_after) <= 0) or (isinstance(status, str) and 'dead' in status.lower()):
                trouble_count += 1

    # Supply pressure: with supply in [15,25], water is scarce near 15-18.
    # Approximate how many water units are available.
    # If supply < 2*WATER_REQ, only 1 unit can be allocated; bidding competition is higher.
    scarce = supply < (2.0 * WATER_REQ)

    # Baseline bid: aim to secure water without burning budget.
    # When scarce, bid higher; otherwise bid moderate.
    if scarce:
        base = DAILY_SALARY * 0.62
    else:
        base = DAILY_SALARY * 0.48

    # React to yesterday's highest bid: if others were very aggressive, we can undercut slightly.
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # If we are low HP or have been without water, increase urgency.
    urgency = 0.0
    if my_hp <= 2.0:
        urgency += 1.0
    if my_no_water_days >= 2:
        urgency += 0.7

    # If trouble_count is high, opponents may be conservative today; we can push slightly above base.
    # If trouble_count is low and highest_prev_bid is high, we should avoid overbidding.
    if highest_prev_bid > DAILY_SALARY * 0.9:
        # Others overreached; undercut.
        target = min(base * (1.0 + 0.25 * urgency), highest_prev_bid - 5.0)
    else:
        target = base * (1.0 + 0.35 * urgency)

    if scarce and trouble_count >= 1:
        target *= 1.08

    # Ensure we don't bid above our budget.
    bid = max(0.0, min(my_budget, target))

    # If budget is extremely low, bid whatever remains.
    if my_budget <= 1.0:
        return float(my_budget)

    # Slightly vary by day to avoid deterministic ties.
    # Use a small, safe increment.
    bid += (day % 3) * 0.5

    # Final clamp
    if bid > my_budget:
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
    day = int(day_context['day'])

    # Identify alive opponents and collect their yesterday bid
    alive_opps = []
    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {}) or {}
            b = prev.get('bid', None)
            if b is not None:
                yesterday_bids.append(float(b))

    # If no data, default conservative
    if not alive_opps or not yesterday_bids:
        base = DAILY_SALARY * 0.55
        return min(my_status['budget'], base)

    highest_prev_bid = max(yesterday_bids)
    avg_prev_bid = sum(yesterday_bids) / float(len(yesterday_bids))

    # Pressure estimate: if others were bidding near/above salary, they likely overcommit.
    # We underbid slightly to avoid burning budget while still contesting.
    # Also, if our hp is low, we must secure water.
    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    # Supply factor: when supply is tight, bids need to be higher.
    # Map supply in [15,25] to [0.85,1.15]
    if MAX_SUPPLY == MIN_SUPPLY:
        supply_factor = 1.0
    else:
        supply_factor = 0.85 + 0.30 * ((supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY))

    # Core bid target near the lower band of observed bids.
    # Alex/Eric were ~109-126; Cindy ~128. We aim around (avg_prev - 10%)
    target = avg_prev_bid * 0.90

    # If others bid extremely high, reduce further.
    if highest_prev_bid >= DAILY_SALARY * 1.35:
        target = avg_prev_bid * 0.75

    # If our hp is critical or we have many no-water days, override to ensure survival.
    if my_hp <= 2.0 or my_no_water_days >= 2:
        target = max(target, DAILY_SALARY * 0.85)

    # If our hp is very healthy, we can bid less.
    if my_hp >= 8.5 and my_no_water_days == 0:
        target = min(target, DAILY_SALARY * 0.60)

    # Apply supply pressure
    target *= supply_factor

    # Ensure we don't exceed what we can pay
    bid = min(my_budget, target)

    # Keep bid positive and within reasonable range
    if bid < 0:
        bid = 0
    # Avoid bidding too tiny amounts when supply is likely scarce
    if supply <= 16.0:
        bid = max(bid, DAILY_SALARY * 0.45)

    return bid
"""
