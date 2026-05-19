# ============================================================
# Experiment: exp_026
# Agent: Bob
# Source: exp_026
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
    day = day_context.get('day')

    my_hp = my_status.get('hp', 0)
    my_budget = my_status.get('budget', 0)
    my_no_water_days = my_status.get('no_water_days', 0)

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Extract yesterday bids (immediate reaction only)
    prev_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Base pressure estimate from yesterday
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev_bid
    else:
        highest_prev_bid = 0.0
        second_prev_bid = 0.0

    # Risk controls: if low HP or already starving, bid more
    starvation_risk = (my_hp <= 2) or (my_no_water_days >= 2)

    # Supply-aware aggressiveness: when supply is tight, winning matters more
    # Convert supply to a rough tier without using it as an index.
    tight_supply = supply <= float(WATER_REQ) + 6.0  # heuristic for medium scenario

    # If someone bid extremely high yesterday, they likely had urgent need.
    # We avoid overpaying unless we are also in danger.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        if starvation_risk or tight_supply:
            bid = min(my_budget, DAILY_SALARY * 0.65)
        else:
            bid = min(my_budget, DAILY_SALARY * 0.25)
        return max(0.0, float(bid))

    # Otherwise, try to slightly beat the strongest yesterday bid.
    # Use a small increment to counter simultaneity.
    increment = 1.5
    target = highest_prev_bid + increment

    # If we can afford it, sometimes outbid the second-highest to reduce variance.
    if prev_bids and second_prev_bid > 0 and tight_supply:
        target = max(target, second_prev_bid + 1.0)

    # Apply caps based on our health/budget.
    cap = DAILY_SALARY * (0.85 if starvation_risk else (0.6 if tight_supply else 0.5))
    bid = min(my_budget, cap, target)

    # Ensure we bid at least a minimal amount when we are at risk
    if starvation_risk:
        bid = max(bid, min(my_budget, DAILY_SALARY * 0.35))

    return max(0.0, float(bid))
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

    alive_opponents = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opponents:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids and correlate with outcomes
    prev_bids = []
    prev_dead_bids = []
    prev_survive_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is None:
            continue
        bid_val = float(bid)
        prev_bids.append(bid_val)
        # Use yesterday hp_after/status as a proxy for overbidding punishment
        hp_after = prev.get('hp_after', None)
        status = prev.get('status', None)
        if hp_after is not None and float(hp_after) <= 0:
            prev_dead_bids.append(bid_val)
        elif status in ('alive', 'survived'):
            prev_survive_bids.append(bid_val)

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    dead_pressure = max(prev_dead_bids) if prev_dead_bids else 0.0
    survive_pressure = max(prev_survive_bids) if prev_survive_bids else 0.0

    # Supply pressure: when supply is high, bidding harder is more likely to secure water.
    supply_frac = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_frac = max(0.0, min(1.0, supply_frac))

    # Base bid conservatively to avoid the budget-collapse pattern seen in deaths.
    # If my hp is low or I'm already without water, increase.
    risk_factor = 0.0
    if hp <= 2.0:
        risk_factor += 0.35
    if no_water_days >= 2:
        risk_factor += 0.25

    # If someone survived with high bids, they likely keep bidding; but avoid matching their top bids fully.
    target = DAILY_SALARY * (0.45 + 0.35 * supply_frac)  # 0.45..0.80

    # If yesterday had extremely high bids that ended in deaths, slightly undercut.
    if dead_pressure > DAILY_SALARY * 0.9:
        target *= 0.85

    # If survival bids were high, we may need to pressure, but still not full-match.
    if survive_pressure > DAILY_SALARY * 0.8:
        target *= (1.0 + 0.15 * supply_frac)

    # If highest previous bid is not far above my target, nudge upward a bit.
    if highest_prev_bid > 0.0:
        if highest_prev_bid <= target * 1.2:
            target = min(target * 1.15, highest_prev_bid - 1.0)

    # Ensure we don't bid more than we can afford.
    bid = max(0.0, min(budget, target + DAILY_SALARY * risk_factor))

    # If budget is very low, bid a fraction to avoid total depletion.
    if budget <= DAILY_SALARY * 0.25:
        bid = min(budget, DAILY_SALARY * 0.15)

    return float(bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
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

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    if my_budget <= 0:
        return 0.0

    # Read yesterday bids from immediate previous_trace only
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', None)
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    prev_bids.append(float(b))
                except Exception:
                    pass

    # Pressure estimate: if any opponent bid extremely high yesterday, they likely expect scarcity.
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    # Compute a target bid based on supply regime.
    # With supply 15-25 and WATER_REQ=9, at most 2 units can be satisfied per day.
    # We avoid overbidding like Cindy/Eric unless necessary.
    supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    # supply_factor near 0 => lower supply => bid more
    scarcity = 1.0 - float(supply_factor)

    # Base bid: moderate fraction of daily salary.
    base = DAILY_SALARY * (0.38 + 0.22 * scarcity)

    # If opponents previously overbid, slightly increase.
    # Cindy/Eric avg ~121-128, so threshold near 100 indicates aggressive bidding.
    if highest_prev_bid >= 100.0:
        base *= 1.18
    elif highest_prev_bid >= 70.0:
        base *= 1.08

    # If my HP is low or I'm already on multiple no-water days, ramp sharply.
    if my_hp <= 2.0 or my_no_water_days >= 2:
        base = max(base, DAILY_SALARY * 0.85)
    elif my_hp <= 4.0 or my_no_water_days >= 1:
        base = max(base, DAILY_SALARY * 0.60)

    # Early days: slightly more conservative to preserve budget for later.
    if day <= 3:
        base *= 0.95

    # Cap by what I can afford.
    bid = min(my_budget, base)

    # Also keep bid within a practical range to avoid unnecessary depletion.
    # If supply is high, don't bid too high.
    if supply >= 22.0:
        bid = min(bid, DAILY_SALARY * 0.70)

    # Ensure non-negative
    if bid < 0:
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

    supply = day_context['supply']
    day = day_context['day']

    # Identify alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # If no opponents alive, bid to secure our requirement cheaply
    if not alive_opps:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace
    prev_bids = []
    prev_hp_after = []
    for oid, o in alive_opps:
        pt = o.get('previous_trace', {}) or {}
        bid = pt.get('bid', None)
        if bid is not None:
            prev_bids.append(float(bid))
            prev_hp_after.append(pt.get('hp_after', o.get('hp', 0)))

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    # Estimate how many water units are likely contested
    # Use supply bins to decide whether we can undercut or must match pressure.
    # int() to avoid float index issues (even though we won't index lists here).
    supply_int = int(supply)
    shortage = supply_int < (MIN_SUPPLY + MAX_SUPPLY) / 2  # below mid-range

    my_hp = my_status.get('hp', 0)
    my_budget = my_status.get('budget', 0.0)
    my_no_water_days = my_status.get('no_water_days', 0)

    # Pressure heuristic from yesterday: if someone bid near/above salary threshold, they likely fought for survival.
    pressure = 0.0
    if highest_prev_bid >= 0.85 * DAILY_SALARY:
        pressure = 1.0
    elif highest_prev_bid >= 0.6 * DAILY_SALARY:
        pressure = 0.7
    elif highest_prev_bid >= 0.3 * DAILY_SALARY:
        pressure = 0.4
    else:
        pressure = 0.25

    # If my HP is critical, I must bid higher regardless of supply.
    if my_hp <= 2 or my_no_water_days >= 2:
        base = DAILY_SALARY * (0.75 if not shortage else 0.95)
    elif shortage:
        base = DAILY_SALARY * (0.55 + 0.25 * pressure)
    else:
        base = DAILY_SALARY * (0.45 + 0.25 * pressure)

    # Undercut logic: try to bid slightly above the previous highest when pressure is high,
    # otherwise keep it around our base but not too high.
    if pressure >= 0.7:
        target = max(base, min(my_budget, highest_prev_bid + 2.0))
    else:
        target = max(base, min(my_budget, avg_prev_bid * 0.95 + 2.0)) if avg_prev_bid > 0 else base

    # Ensure we never exceed budget and never go negative
    bid = max(0.0, min(float(my_budget), float(target)))

    # Small day-based adjustment: later days require stronger bids to avoid running out.
    # episode_days is fixed at 10 in meta-round; use day to ramp.
    # day_context['day'] is assumed 1..10.
    if day is not None:
        try:
            d = int(day)
        except Exception:
            d = 1
        if d >= 8:
            bid = min(float(my_budget), bid * 1.12)
        elif d <= 2:
            bid = bid * 0.92

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

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return float(min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace for immediate reaction.
    prev_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    # Estimate how many water units are likely needed today to avoid hp loss.
    # If supply is low, water is scarcer -> bid higher.
    supply_ratio = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Base bid: mid level. Raise when supply is low (scarce) or my hp is critical.
    # Also raise if yesterday saw very high bids (indicating aggressive competition).
    critical = (hp <= 2) or (no_water_days >= 2)

    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Opponents were extremely aggressive yesterday; don't overpay to extinction, but ensure contention.
        base = DAILY_SALARY * (0.45 if supply_ratio > 0.5 else 0.65)
        if critical:
            base = DAILY_SALARY * 0.85
    elif avg_prev_bid >= DAILY_SALARY * 0.9:
        base = DAILY_SALARY * (0.4 if supply_ratio > 0.6 else 0.6)
        if critical:
            base = DAILY_SALARY * 0.75
    else:
        base = DAILY_SALARY * (0.35 if supply_ratio > 0.6 else 0.55)
        if critical:
            base = DAILY_SALARY * 0.7

    # Convert base into a bid cap that scales with remaining budget.
    # Keep a safety reserve to survive multiple days.
    safety_fraction = 0.25 if day < 7 else 0.15
    max_affordable = budget * (1.0 - safety_fraction)

    # If budget is very low, still bid enough to avoid immediate failure.
    if budget <= DAILY_SALARY * 0.2:
        bid = min(budget, DAILY_SALARY * 0.5)
        return float(max(0.0, bid))

    # Final bid: add a small increment over average aggression to beat likely bids.
    bid = base
    if prev_bids:
        # Use a fraction of the highest previous bid as a pressure signal.
        bid = max(bid, min(budget, highest_prev_bid * (0.55 if supply_ratio > 0.5 else 0.75)))

    # If I'm healthy, avoid burning too much; if low hp, push.
    if hp >= 6 and not critical:
        bid *= 0.85
    elif hp <= 3 or critical:
        bid *= 1.05

    bid = min(bid, max_affordable)
    bid = max(0.0, bid)

    # Ensure integer-free float output is acceptable; return float.
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

    supply = day_context['supply']
    day = day_context['day']

    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # React to yesterday bids (immediate pressure)
    prev_bids = []
    for _, o in alive:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_prev = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev_bid

    # Estimate how many allocations might be available: supply is total, water is per water_req unit.
    # Use it to decide aggressiveness: higher supply means we can bid less.
    # Ensure indices are int-safe (no list indexing used here).
    supply_units = supply / float(WATER_REQ)
    # Target bid fraction based on supply and observed opponent aggressiveness.
    if supply_units >= 2.5:
        base_frac = 0.42
    elif supply_units >= 1.8:
        base_frac = 0.55
    else:
        base_frac = 0.68

    # If yesterday someone bid very high, we must contest.
    if highest_prev_bid >= DAILY_SALARY * 1.25:
        contest_frac = 0.78
    elif highest_prev_bid >= DAILY_SALARY * 0.85:
        contest_frac = 0.66
    else:
        contest_frac = 0.52

    # HP pressure: if low HP or many no-water days, bid harder.
    if hp <= 1 or no_water_days >= 2:
        hp_frac = 0.9
    elif hp <= 3 or no_water_days >= 1:
        hp_frac = 0.75
    else:
        hp_frac = 0.58

    # Combine: bid = min(budget, DAILY_SALARY * frac) with a slight overtake vs yesterday high bidder.
    frac = max(base_frac, contest_frac, hp_frac)

    # Try to outbid the strongest yesterday bidder by a small margin, but only if affordable.
    # This assumes similar strategy persists.
    margin = 2.5
    target = min(budget, DAILY_SALARY * frac)
    if highest_prev_bid > 0:
        target = max(target, min(budget, highest_prev_bid + margin))

    # If our budget is tiny, bid whatever we can (but never negative).
    target = max(0.0, float(target))

    # Keep a floor to avoid getting starved when hp is critical.
    if hp <= 1:
        target = max(target, min(budget, DAILY_SALARY * 0.95))

    return target
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

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return float(min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace for immediate reaction
    prev_bids = []
    for _, o in alive_opps:
        pt = o.get('previous_trace', None) or {}
        b = pt.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate how many water units are likely needed to avoid death pressure.
    # We assume each winner gets at least WATER_REQ water; if supply is low, bidding should be more aggressive.
    approx_units = int(supply // float(WATER_REQ)) if WATER_REQ > 0 else 0
    # approx_units could be 1 or 2 in the stated supply range.
    if approx_units < 1:
        approx_units = 1

    # Baseline aggressiveness: if supply is scarce, bid more.
    scarcity_factor = 0.55 if supply >= 20 else 0.75

    # If opponents were bidding extremely high yesterday, don't fully mirror; just enough to compete.
    # Cindy/Eric were ~121 average; use that as a signal.
    if highest_prev_bid >= 115.0:
        base = DAILY_SALARY * 0.62
    elif highest_prev_bid >= 90.0:
        base = DAILY_SALARY * 0.52
    else:
        base = DAILY_SALARY * 0.45

    # React to own HP/no-water days.
    if hp <= 2 or no_water_days >= 2:
        base *= 1.35
    elif hp <= 4:
        base *= 1.15

    # If supply likely allows fewer winners, increase slightly.
    if approx_units == 1:
        base *= 1.10

    # Convert to final bid with budget safety.
    # Keep within a reasonable band to avoid the Alex/David failure mode (budget depletion).
    bid_cap = min(budget, DAILY_SALARY * 0.95)
    bid_floor = min(budget, DAILY_SALARY * 0.25)

    bid = float(base)
    if bid > bid_cap:
        bid = bid_cap
    if bid < bid_floor:
        bid = bid_floor

    # Final small day-based adjustment to avoid ties when late in episode.
    if day >= 7:
        bid *= 1.03
        if bid > bid_cap:
            bid = bid_cap

    return float(max(0.0, bid))
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

    supply = float(day_context.get('supply', (MIN_SUPPLY + MAX_SUPPLY) / 2.0))
    day = day_context.get('day', 0)

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append(o)

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids for immediate reaction
    prev_bids = []
    for o in alive:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate rival pressure from yesterday
    if prev_bids:
        avg_bid = sum(prev_bids) / float(len(prev_bids))
        max_prev = max(prev_bids)
    else:
        avg_bid = DAILY_SALARY * 0.6
        max_prev = avg_bid

    # Supply tightness: if supply is low, water is scarce -> increase bid
    # supply_needed_factor ~ how many water units can be bought relative to our requirement
    # (We only use it as a monotone heuristic.)
    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY + 1e-9)  # 0..1-ish

    # Base bid targets: slightly under yesterday average if healthy, otherwise near/above max_prev.
    if hp <= 2.0 or no_water_days >= 2:
        target = max_prev * (0.98 - 0.1 * scarcity)  # urgent: match top pressure
    elif hp <= 4.0:
        target = avg_bid * (1.02 - 0.15 * scarcity)
    else:
        # healthy: try to win at a discount
        target = avg_bid * (0.92 - 0.12 * scarcity)

    # Also cap by a fraction of salary to avoid bankruptcy
    # If supply is very tight, allow paying more.
    salary_cap = DAILY_SALARY * (0.55 + 0.35 * scarcity)
    target = min(target, salary_cap)

    # Ensure we don't bid more than budget
    bid = min(budget, target)

    # If budget is tiny, still bid something non-negative
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

    alive_opps = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids to infer aggressiveness
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                yesterday_bids.append(float(bid))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else 0.0

    # Estimate how many full water units are likely needed to stay safe.
    # If supply is tight, bidding more increases chance to secure at least one unit.
    # Use a conservative target tied to supply.
    supply_units = supply / float(WATER_REQ)
    # Convert to an integer index-like quantity safely.
    # (Used only for thresholds, not for list indexing.)
    if supply_units < 1.2:
        supply_pressure = 0.9
    elif supply_units < 1.8:
        supply_pressure = 0.7
    else:
        supply_pressure = 0.55

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # If I'm already in danger (low hp or accumulating no-water days), bid aggressively.
    if my_hp <= 2.0 or no_water_days >= 2:
        bid = DAILY_SALARY * (0.85 + 0.1 * supply_pressure)
        return float(min(my_budget, bid))

    # If an opponent was extremely aggressive yesterday, avoid mirroring their cost.
    # Instead, bid enough to compete but not enough to waste budget.
    if highest_prev_bid >= DAILY_SALARY * 1.05:
        # Cindy-like behavior; keep mid-high to beat overbidding opponents when possible.
        bid = DAILY_SALARY * (0.55 * supply_pressure + 0.25)
        # If second-highest was also high, slightly increase.
        if second_prev_bid >= DAILY_SALARY * 0.9:
            bid = bid * 1.15
        return float(min(my_budget, bid))

    # Otherwise, bid moderately based on supply pressure and day.
    # Slightly increasing over time to prevent late starvation.
    time_factor = 1.0 + min(0.15, (day / 10.0) * 0.15)
    bid = DAILY_SALARY * (0.45 * supply_pressure + 0.25) * time_factor

    # Ensure we don't bid too low when supply is near minimum.
    if supply <= MIN_SUPPLY + 0.5:
        bid = max(bid, DAILY_SALARY * 0.5)

    return float(min(my_budget, bid))
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

    # Identify alive opponents
    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive.append((opp_id, opp))

    # If no one is alive, conserve
    if not alive:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace for immediate reaction
    prev_bids = []
    for _, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate yesterday pressure
    highest_prev = max(prev_bids) if prev_bids else 0.0
    second_prev = 0.0
    if len(prev_bids) >= 2:
        s = sorted(prev_bids, reverse=True)
        second_prev = float(s[1])

    # Supply tiering: with supply 15-25 and WATER_REQ=9, typically 1 unit often matters.
    # We bias bids based on how likely the top bidder secured water yesterday.
    # If supply is lower, competition for the 1 unit increases.
    supply_ratio = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Base bid level
    # If yesterday highest bid was high, expect continued competition.
    if highest_prev >= DAILY_SALARY * 0.8:
        # High pressure environment
        if my_status['hp'] > 3:
            base = DAILY_SALARY * (0.25 + 0.15 * (1.0 - supply_ratio))
        else:
            base = DAILY_SALARY * (0.75 + 0.15 * (1.0 - supply_ratio))
    else:
        # Moderate pressure
        if my_status['hp'] > 3:
            base = max(DAILY_SALARY * 0.45, highest_prev * 0.95)
        else:
            base = max(DAILY_SALARY * 0.75, highest_prev * 1.05)

    # If there is a strong second bidder, slightly overtake their level to secure allocation.
    # (We don't know today's bids, so we use yesterday's gap as a proxy.)
    if second_prev > 0.0:
        target = second_prev + 2.0
        # Blend target with base to avoid overspending.
        base = 0.6 * base + 0.4 * target

    # If we are already in no-water streak, escalate
    no_water_days = int(my_status.get('no_water_days', 0) or 0)
    if no_water_days >= 2:
        base = max(base, DAILY_SALARY * 0.85)
    elif no_water_days == 1:
        base = max(base, DAILY_SALARY * 0.65)

    # Budget safety cap
    budget = float(my_status['budget'])
    bid = float(min(budget, base))

    # Ensure non-negative
    if bid < 0.0:
        bid = 0.0

    return bid
"""
