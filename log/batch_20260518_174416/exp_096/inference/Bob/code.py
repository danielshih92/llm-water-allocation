# ============================================================
# Experiment: exp_096
# Agent: Bob
# Source: exp_096
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

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive'):
            alive_opponents.append(o)

    # Baseline: target just enough to meet our requirement with some buffer.
    # Convert to a bid within our budget.
    # If supply is tight, we must bid more.
    tightness = 0.0
    if supply <= float(WATER_REQ):
        tightness = 1.0
    else:
        # supply in [15,25] typically; map to [0,1]
        tightness = (float(MAX_SUPPLY) - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
        if tightness < 0.0:
            tightness = 0.0
        if tightness > 1.0:
            tightness = 1.0

    # Read yesterday bids from previous_trace for immediate reaction.
    yesterday_bids = []
    for o in alive_opponents:
        prev = o.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    yesterday_bids.append(float(b))
                except Exception:
                    pass

    # If opponents were aggressive yesterday, adjust upward.
    # We do not know their current hidden bids; we use their last bid as a proxy.
    aggressive_threshold = DAILY_SALARY * 0.85
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If someone was bidding extremely high, assume scarcity/low hp and bid to secure.
        if highest_prev_bid >= aggressive_threshold:
            # If our hp is low, we must prioritize water.
            if my_status.get('hp', 0) <= 2:
                target = DAILY_SALARY * (0.85 + 0.1 * tightness)
            else:
                target = DAILY_SALARY * (0.65 + 0.15 * tightness)
            # Ensure we don't blindly overpay: bid just above their likely level when possible.
            # Add a small increment to beat them.
            bid = max(target, highest_prev_bid + 1.0)
        else:
            # They were not too aggressive: bid moderately, enough to meet our needs.
            # Use their max as a soft cap.
            soft = max(DAILY_SALARY * (0.45 + 0.2 * tightness), highest_prev_bid * 0.9 + 0.5)
            bid = soft
    else:
        # No trace info: bid based on our hp and supply tightness.
        if my_status.get('hp', 0) <= 2:
            bid = DAILY_SALARY * (0.75 + 0.2 * tightness)
        else:
            bid = DAILY_SALARY * (0.5 + 0.15 * tightness)

    # Convert bid to a safe amount within our budget.
    budget = float(my_status.get('budget', 0.0))
    if budget <= 0.0:
        return 0.0

    # Also avoid bidding more than needed for our requirement when supply is ample.
    # Approximate: if supply is high, we can bid lower.
    # Scale with how many requirements fit in expected supply.
    # Note: no list indexing required.
    expected_fit = supply / float(WATER_REQ)
    if expected_fit >= 2.0:
        bid *= 0.75
    elif expected_fit >= 1.5:
        bid *= 0.9

    # Final clamp.
    if bid < 0.0:
        bid = 0.0
    if bid > budget:
        bid = budget

    # Keep some reserve for later days.
    # If we have many no-water days, we should be more willing to spend.
    no_water_days = int(my_status.get('no_water_days', 0))
    if no_water_days >= 2:
        reserve_frac = 0.05
    else:
        reserve_frac = 0.15
    max_affordable = budget * (1.0 - reserve_frac)
    if bid > max_affordable:
        bid = max_affordable

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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        return float(min(budget, DAILY_SALARY * 0.4))

    prev_bids = []
    for o in alive_opps:
        pt = o.get('previous_trace', {}) or {}
        b = pt.get('bid', None)
        if b is not None:
            prev_bids.append(float(b))

    # Baseline target bid: use yesterday's competitive level, but keep margin.
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        avg_prev_bid = sum(prev_bids) / max(1, len(prev_bids))
    else:
        highest_prev_bid = DAILY_SALARY * 0.55
        avg_prev_bid = DAILY_SALARY * 0.55

    # If any opponent shows high risk yesterday (low hp or many no-water days), slightly undercut.
    # If they were bidding high and survived, we need to match closer.
    risky_pressure = 0.0
    for o in alive_opps:
        if o.get('hp', 0) <= 2 or int(o.get('no_water_days', 0)) >= 2:
            risky_pressure += 1.0

    # Supply influences scarcity: higher supply reduces needed bid.
    supply_ratio = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_ratio = (supply - float(MIN_SUPPLY)) / float(MAX_SUPPLY - MIN_SUPPLY)
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Convert to a competitive bid band.
    # When supply is low, bid closer to highest_prev_bid; when supply is high, bid closer to avg.
    scarcity_factor = 1.0 + (1.0 - supply_ratio) * 0.25

    target = avg_prev_bid * scarcity_factor

    # If highest_prev_bid is very high, align upward but not fully.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        target = max(target, highest_prev_bid * 0.92)
    else:
        target = max(target, highest_prev_bid * 0.75)

    # My urgency: if I'm low hp or have water shortage, increase bid.
    if hp <= 2.0 or no_water_days >= 1:
        target *= 1.15
    elif hp >= 7.0 and no_water_days == 0:
        target *= 0.9

    # If opponents are risky (likely to drop out), we can bid slightly less.
    if risky_pressure >= 1.0:
        target *= 0.97

    # Ensure within budget and sensible bounds.
    target = float(min(target, budget))

    # Hard cap to avoid overspending when budget is tight.
    # Keep enough budget for later days.
    if budget > 0:
        reserve = max(0.0, budget - DAILY_SALARY * 0.6)
        target = float(max(target, 0.0))
        # If reserve would leave too little, reduce bid.
        if target > budget - reserve:
            target = float(max(0.0, budget - reserve))

    # Minimum competitive bid: if we can afford it, bid at least a fraction of salary.
    min_bid = DAILY_SALARY * 0.35
    if budget >= min_bid:
        target = float(max(target, min_bid))

    # Final clamp.
    if target < 0.0:
        target = 0.0
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
    day = day_context.get('day', 0)

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for k, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Extract yesterday bids from immediate previous_trace
    prev_bids = []
    prev_bids_by_id = {}
    for opp_id, o in opponents_status.items():
        if not o.get('alive', False):
            continue
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                b = float(b)
            except Exception:
                b = None
        if b is not None:
            prev_bids.append(b)
            prev_bids_by_id[opp_id] = b

    # Aggression calibration from yesterday
    highest_prev = max(prev_bids) if prev_bids else 0.0
    second_highest = 0.0
    if len(prev_bids) >= 2:
        s = sorted(prev_bids, reverse=True)
        second_highest = s[1]

    # Determine how many water units likely available given supply
    # Use only for coarse pressure; actual allocation depends on game rules.
    # If supply is scarce near MIN_SUPPLY, we need to outbid more.
    scarcity = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        scarcity = (float(MAX_SUPPLY) - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    # Base target bid: slightly above yesterday's top bid when others were aggressive.
    # Observed: Cindy/Eric ~140-155. We'll aim around 145-155 when hp is critical.
    critical = (hp <= 3) or (no_water_days >= 2)

    if highest_prev >= DAILY_SALARY * 1.4:  # ~126+ indicates aggressive bidding
        # If we were in danger, we must secure water.
        if critical:
            target = highest_prev + 5.0  # small overtake
        else:
            # Try to beat without burning too much
            target = max(highest_prev - 2.0, second_highest + 3.0)
    else:
        # Lower aggression: bid enough to be competitive
        target = max(DAILY_SALARY * (0.45 + 0.25 * scarcity), highest_prev + 1.5)

    # Convert target into a bounded bid using supply pressure
    # If supply is very low, increase; if high, decrease a bit.
    if scarcity > 0.6:
        target *= 1.05
    elif scarcity < 0.3:
        target *= 0.95

    # Cap bid by what we can afford and by a reasonable fraction of salary
    # Preserve budget for later days.
    max_affordable = budget
    # Keep some reserve when not critical
    reserve_fraction = 0.15 if critical else 0.35
    bid_cap = max_affordable * (1.0 - reserve_fraction)
    if bid_cap < 0.0:
        bid_cap = 0.0

    # Also avoid overbidding beyond typical observed maxima
    observed_ceiling = 160.0
    final_bid = min(float(target), bid_cap, observed_ceiling)

    # Ensure non-negative and at least small competitive amount if possible
    if final_bid < 0.0:
        final_bid = 0.0

    # If we can afford at least a minimal competitive bid, don't bid 0 unless forced.
    min_competitive = DAILY_SALARY * (0.35 + 0.2 * scarcity)
    if final_bid < min_competitive and budget >= min_competitive and not critical:
        final_bid = min(budget * 0.6, min_competitive)
    elif final_bid <= 0.0 and budget > 0.0:
        # critical fallback
        final_bid = min(budget, DAILY_SALARY * (0.9 if critical else 0.6))

    return float(final_bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    if not alive_opponents:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace for immediate reaction
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    yesterday_bids.append(float(b))
                except Exception:
                    pass

    max_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Supply pressure: with supply in [15,25], water units are roughly supply/WATER_REQ
    # If supply is lower, competition is higher.
    supply_ratio = supply / float(WATER_REQ) if WATER_REQ else 0.0
    # Normalize to [0,1] using expected range
    # At supply=15 => 15/9=1.67, at 25 => 2.78
    min_ratio = float(MIN_SUPPLY) / float(WATER_REQ)
    max_ratio = float(MAX_SUPPLY) / float(WATER_REQ)
    if max_ratio > min_ratio:
        pressure = (supply_ratio - min_ratio) / (max_ratio - min_ratio)
    else:
        pressure = 0.5
    pressure = max(0.0, min(1.0, pressure))

    # Determine aggressiveness
    # If yesterday max bid was high, overmatch slightly.
    # If our hp is low or we already had no-water days, bid higher.
    if max_prev_bid >= DAILY_SALARY * 0.85:
        base_bid = DAILY_SALARY * (0.35 + 0.25 * (1.0 - pressure))
        bid = max(base_bid, max_prev_bid * 1.02)
    elif max_prev_bid >= DAILY_SALARY * 0.65:
        bid = DAILY_SALARY * (0.45 + 0.2 * (1.0 - pressure))
        bid = max(bid, max_prev_bid * 0.98)
    else:
        bid = DAILY_SALARY * (0.55 + 0.15 * (1.0 - pressure))

    # Urgency adjustments
    if hp <= 2:
        bid *= 1.35
    elif hp <= 4:
        bid *= 1.15

    if no_water_days >= 2:
        bid *= 1.25

    # Budget and safety cap: don't exceed budget; also avoid wasting too much late.
    # Episode is 10 days; keep some runway.
    # Use a simple remaining-days heuristic.
    remaining_days = max(1, int(10 - int(day)))
    runway_fraction = min(1.0, remaining_days / 10.0)

    max_affordable = budget
    # Keep at most ~70% of budget when runway is short; otherwise allow more.
    budget_cap = budget * (0.7 + 0.3 * runway_fraction)

    bid = min(bid, max_affordable, budget_cap)

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

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    if not alive:
        return float(min(my_status.get('budget', 0.0), DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace only (immediate reaction)
    prev_bids = []
    prev_hp_after = []
    for oid, o in alive:
        prev = o.get('previous_trace', {}) or {}
        if prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid', 0.0)))
            except Exception:
                pass
        if prev.get('hp_after') is not None:
            try:
                prev_hp_after.append(float(prev.get('hp_after', 0.0)))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_highest_prev_bid = 0.0
    if len(prev_bids) >= 2:
        sorted_b = sorted(prev_bids, reverse=True)
        second_highest_prev_bid = sorted_b[1]

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))

    # Estimate how many allocations are possible this day (not exact, but guides aggressiveness)
    # Each unit of water is assumed to reduce no_water_days; we buy enough to cover WATER_REQ needs.
    # Use supply bands to decide whether to contest.
    supply_band = 'low'
    if supply >= 20.0:
        supply_band = 'high'
    elif supply >= 17.0:
        supply_band = 'mid'

    # If someone previously bid extremely high, they likely are contesting hard.
    # Avoid matching unless my HP is low.
    critical = my_hp <= 2.5
    very_low = my_hp <= 1.0

    # Target bid: beat the median/second-highest but stay below the highest unless critical.
    # Also incorporate supply band: with higher supply, lower pressure.
    base = 0.0
    if supply_band == 'high':
        base = max(DAILY_SALARY * 0.35, second_highest_prev_bid * 0.95)
    elif supply_band == 'mid':
        base = max(DAILY_SALARY * 0.45, second_highest_prev_bid * 1.02)
    else:
        base = max(DAILY_SALARY * 0.55, second_highest_prev_bid * 1.05)

    # If the highest yesterday was far above typical, don't overreact unless critical.
    if highest_prev_bid >= DAILY_SALARY * 1.65:  # ~149
        if very_low:
            bid = max(base, DAILY_SALARY * 0.95)
        elif critical:
            bid = max(base, DAILY_SALARY * 0.75)
        else:
            # stay competitive but not top-end
            bid = min(base, DAILY_SALARY * 0.65)
    else:
        # No extreme contest detected; bid to secure against low bidders.
        if critical:
            bid = max(base, DAILY_SALARY * 0.8)
        else:
            bid = max(base, DAILY_SALARY * 0.55)

    # Hard caps to avoid bankruptcy
    # Keep some budget for future days; scale with remaining budget and no_water_days.
    no_water_days = float(my_status.get('no_water_days', 0.0))
    budget_safety = 0.25 if no_water_days <= 1.0 else 0.15
    max_affordable = my_budget * (1.0 - budget_safety)
    if max_affordable < 0.0:
        max_affordable = 0.0

    # Final bid bounded by budget and a reasonable contest ceiling
    ceiling = DAILY_SALARY * 0.95 if critical else DAILY_SALARY * 0.7
    bid = float(min(max_affordable, bid, ceiling))

    # Ensure non-negative
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

    # Alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # If no one alive, take what we can afford (still bounded)
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.6))

    # Read yesterday bids from previous_trace only
    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Baseline from yesterday: typical winners appear around 100-120
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        # Use median-like proxy via sorted percentiles without long history
        sorted_b = sorted(yesterday_bids)
        mid = sorted_b[len(sorted_b)//2]

        # If someone was extremely aggressive yesterday (Cindy), we don't need to match; instead bid to secure
        # If someone was moderate, bid slightly above mid to win the water share.
        aggressive = max_prev >= DAILY_SALARY * 1.35  # ~121.5
    else:
        max_prev = 0.0
        mid = DAILY_SALARY * 0.55
        aggressive = False

    # Determine target bid based on current supply pressure.
    # Higher supply reduces need to overbid; lower supply increases urgency.
    if supply <= float(MIN_SUPPLY):
        urgency = 1.0
    elif supply >= float(MAX_SUPPLY):
        urgency = 0.7
    else:
        # Linear interpolation between 1.0 at 15 and 0.7 at 25
        urgency = 1.0 - 0.3 * ((supply - float(MIN_SUPPLY)) / (float(MAX_SUPPLY) - float(MIN_SUPPLY)))

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    # If low HP, bid more to avoid no-water days.
    if hp <= 2.5:
        hp_factor = 1.25
    elif hp <= 4.0:
        hp_factor = 1.1
    else:
        hp_factor = 0.95

    # Core strategy: bid around mid+small premium, tuned by urgency and hp.
    # Premium is small to avoid Cindy-like overbidding.
    premium = 7.0 if not aggressive else 10.0

    if yesterday_bids:
        target = (mid + premium) * urgency * hp_factor
    else:
        target = (DAILY_SALARY * 0.6 + 8.0) * urgency * hp_factor

    # Hard bounds: never exceed what we can pay; also avoid wasting too much.
    # Keep some budget for later days.
    # Use a conservative cap that still can beat typical bids.
    cap = DAILY_SALARY * (0.95 if hp <= 4.0 else 0.75)
    bid = float(min(budget, cap, max(0.0, target)))

    # If budget is very low, bid minimal but nonzero if possible.
    if bid < 1e-6 and budget > 0:
        bid = float(min(budget, 5.0))

    return bid
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

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from immediate previous_trace only
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Estimate how aggressive the field was yesterday
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        avg_prev_bid = sum(prev_bids) / float(len(prev_bids))
    else:
        highest_prev_bid = 0.0
        avg_prev_bid = 0.0

    # Supply pressure: higher supply reduces need to overbid
    # Expected water units available in this day (rough)
    # Ensure indices are int-safe (we don't index arrays, but keep safe computations)
    supply_pressure = 0.0
    if supply <= MIN_SUPPLY:
        supply_pressure = 1.0
    elif supply >= MAX_SUPPLY:
        supply_pressure = 0.0
    else:
        supply_pressure = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)

    # Base bid: aim around avg_prev_bid with a premium when supply is tight
    # Also react to our own urgency (no water days / low hp)
    urgency = 0.0
    if hp <= 2:
        urgency = 1.0
    elif hp <= 4:
        urgency = 0.7
    else:
        urgency = 0.4

    if no_water_days >= 2:
        urgency = max(urgency, 0.8)

    # If someone already bid very high yesterday, we need to contest but not necessarily match
    # Target premium: 8-18% over avg, plus extra for urgency and tight supply
    premium = 0.08 + 0.1 * urgency + 0.08 * supply_pressure

    if avg_prev_bid > 0.0:
        target = avg_prev_bid * (1.0 + premium)
    else:
        target = DAILY_SALARY * (0.45 + 0.2 * urgency + 0.15 * supply_pressure)

    # If highest_prev_bid was extremely high, nudge upward but keep below it to avoid waste
    if highest_prev_bid > 0.0:
        # Try to beat the likely clearing price: aim at 60-90% of highest_prev_bid depending on urgency
        contest = highest_prev_bid * (0.65 + 0.25 * urgency)
        target = max(target, contest)

    # Convert to a safe bid cap: never bid more than we can afford
    # Also avoid bidding near total budget when budget is low
    max_affordable = max(0.0, budget)

    # Budget-aware scaling: if budget is small relative to DAILY_SALARY, bid more conservatively
    if max_affordable <= DAILY_SALARY * 0.5:
        target *= 0.85

    # Final clamp
    bid = max(0.0, min(max_affordable, target))

    # If extremely low hp, bid closer to full salary to survive
    if hp <= 2.5:
        bid = max(bid, min(max_affordable, DAILY_SALARY * (0.85 + 0.05 * supply_pressure)))

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

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append(o)

    if not alive:
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday bids to infer aggression level
    prev_bids = []
    for o in alive:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev['bid']))

    if prev_bids:
        highest_prev_bid = max(prev_bids)
        second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev_bid
    else:
        highest_prev_bid = 0.0
        second_prev_bid = 0.0

    # Aggression estimate: if bids were large relative to our daily salary, opponents are likely bidding to secure
    pressure = 0.0
    if highest_prev_bid > 0:
        pressure = min(1.0, highest_prev_bid / (DAILY_SALARY * 1.6))

    # Our urgency: low hp or already missing water increases urgency
    urgency = 0.0
    if hp <= 1.0:
        urgency = 1.0
    elif hp <= 3.0:
        urgency = 0.8
    elif hp <= 5.0:
        urgency = 0.6
    else:
        urgency = 0.4

    if no_water_days >= 2:
        urgency = min(1.0, urgency + 0.2)

    # Supply factor: with lower supply, competition should be higher
    supply_factor = 0.5
    if supply <= (MIN_SUPPLY + 0.5):
        supply_factor = 0.95
    elif supply <= ((MIN_SUPPLY + MAX_SUPPLY) / 2.0):
        supply_factor = 0.75
    else:
        supply_factor = 0.6

    # Target bid: try to beat the likely clearing price without overmatching
    # Use second-highest as a proxy for where we need to be, but cap by our budget and a safety multiplier.
    base = DAILY_SALARY * (0.35 + 0.35 * urgency) * supply_factor

    # If yesterday highest was extreme, we should bid closer to it; otherwise bid near second-highest.
    if highest_prev_bid >= DAILY_SALARY * 1.2:
        target = max(base, second_prev_bid + 2.0)
        target = min(target, highest_prev_bid * (0.85 + 0.1 * pressure))
    else:
        target = max(base, second_prev_bid + 1.0)
        target = min(target, highest_prev_bid * 0.7 + base)

    # Convert to a practical bid with integer cents-like granularity (optional)
    target = float(target)

    # Budget safety: never bid more than we can afford; also avoid bankrupting unless very urgent
    max_affordable = budget
    if urgency < 0.8:
        max_affordable = min(max_affordable, DAILY_SALARY * (0.9 + 0.1 * pressure))

    bid = min(target, max_affordable)

    # If bid is too low to matter in high pressure, floor it
    if pressure > 0.6 and urgency > 0.5:
        bid = max(bid, DAILY_SALARY * 0.55)

    # If extremely urgent, allow higher bid
    if urgency >= 0.9:
        bid = max(bid, DAILY_SALARY * 0.85)
        bid = min(bid, budget)

    # Final clamp
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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    if not alive_opponents:
        return float(min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from traces for immediate pressure estimation
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    # Supply pressure: if supply is low, water is scarce -> bid higher to avoid no-water days.
    # With WATER_REQ=9, supply range 15..25 means 1..2 units possible.
    units_possible = int(supply / float(WATER_REQ))
    if units_possible < 1:
        units_possible = 1
    if units_possible > 2:
        units_possible = 2

    # Base aggressiveness: react to Cindy-like behavior (high previous bid) but don't match max.
    # If someone previously bid very high, we lift our bid to avoid being outcompeted.
    pressure = 0.0
    if highest_prev_bid > 0:
        pressure = min(1.0, highest_prev_bid / (DAILY_SALARY * 1.75))

    # Critical survival: if we're already low HP or have gone without water, bid strongly.
    emergency = 0.0
    if hp <= 2.0:
        emergency = 1.0
    elif hp <= 3.0:
        emergency = 0.6
    if no_water_days >= 2:
        emergency = max(emergency, 0.8)

    # Target bid level
    # - If supply only supports 1 unit, bid higher.
    # - Otherwise bid moderately but still informed by highest_prev_bid.
    if units_possible == 1:
        target = DAILY_SALARY * (0.65 + 0.25 * pressure + 0.25 * emergency)
    else:
        target = DAILY_SALARY * (0.55 + 0.20 * pressure + 0.30 * emergency)

    # Ensure we are competitive vs yesterday's top bid, but capped.
    # If top bid is extremely high, we don't fully chase; we slightly undercut to preserve budget.
    if highest_prev_bid > 0:
        chase = highest_prev_bid * (0.75 if emergency < 0.9 else 0.9)
        target = max(target, chase)

    # Budget and safety caps
    # Keep enough budget for multiple days: spend a fraction depending on emergency.
    spend_fraction = 0.45 if emergency < 0.5 else 0.75
    max_affordable = budget * spend_fraction

    # Also cap by a reasonable daily limit relative to salary
    daily_cap = DAILY_SALARY * (1.25 if emergency >= 0.8 else 1.0)

    bid = float(min(max_affordable, daily_cap, target))

    # Minimal bid to avoid zeroing out when budget is tiny
    if bid < 0.0:
        bid = 0.0
    return bid
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
    day = int(day_context['day'])

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Extract yesterday bids for immediate reaction
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    pressure = 0.0
    if prev_bids:
        pressure = max(prev_bids)

    # Supply tightness: if supply is near minimum, water is scarce -> bid more
    # Use a smooth factor rather than exact thresholds
    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY + 1e-9)
    scarcity = max(0.0, min(1.0, scarcity))

    # If we've already gone without water, increase urgency
    urgency = 0.0
    if my_no_water_days >= 2:
        urgency = 1.0
    elif my_no_water_days == 1:
        urgency = 0.6
    else:
        urgency = 0.25

    # HP-based risk: lower HP -> bid more
    hp_factor = 0.0
    if my_hp <= 2:
        hp_factor = 1.0
    elif my_hp <= 4:
        hp_factor = 0.75
    elif my_hp <= 7:
        hp_factor = 0.45
    else:
        hp_factor = 0.25

    # Target bid baseline: anchor to yesterday pressure but avoid overpaying
    # If pressure was high, match a fraction of it; otherwise bid around a mid level.
    if pressure > 0:
        # Match enough to beat typical surviving bids; add scarcity/urgency/Hp pressure
        base = pressure * (0.85 - 0.25 * hp_factor) + (DAILY_SALARY * 0.15)
    else:
        base = DAILY_SALARY * 0.55

    # Adjust upward for scarcity and urgency
    multiplier = 1.0 + 0.35 * scarcity + 0.35 * urgency + 0.25 * hp_factor
    bid = base * multiplier

    # Cap bid to budget and to a reasonable fraction of budget to preserve optionality
    # (Budget can be small; never exceed it.)
    max_allow = my_budget
    # Also keep bids from going extreme when budget is large
    soft_cap = DAILY_SALARY * (0.95 + 0.15 * scarcity)
    bid = min(bid, soft_cap, max_allow)

    # Ensure non-negative
    if bid < 0.0:
        bid = 0.0

    # If our budget is very low, bid it all to avoid dying
    if my_budget <= DAILY_SALARY * 0.2:
        return min(my_budget, DAILY_SALARY * 0.95)

    # If supply is very tight, ensure a minimum competitive bid
    if supply <= float(MIN_SUPPLY):
        min_competitive = DAILY_SALARY * (0.6 + 0.25 * urgency)
        bid = max(bid, min_competitive)
        bid = min(bid, my_budget)

    return float(bid)
"""
