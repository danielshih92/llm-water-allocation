# ============================================================
# Experiment: exp_034
# Agent: Bob
# Source: exp_034
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

    # Collect alive opponents and their yesterday bids
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return min(my_status.get('budget', 0), DAILY_SALARY * 0.4)

    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                yesterday_bids.append(float(bid))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    my_hp = my_status.get('hp', 0)
    my_budget = my_status.get('budget', 0)
    no_water_days = my_status.get('no_water_days', 0)

    # Determine how aggressive to be
    # If opponents were bidding very high yesterday, match enough to avoid losing again.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        if my_hp <= 2 or no_water_days >= 2:
            target = DAILY_SALARY * 0.95
        else:
            target = DAILY_SALARY * 0.35
    elif highest_prev_bid >= DAILY_SALARY * 0.55:
        # Moderate pressure: bid around the upper-middle.
        if my_hp <= 2 or no_water_days >= 2:
            target = DAILY_SALARY * 0.8
        else:
            target = max(highest_prev_bid + 5.0, DAILY_SALARY * 0.55)
    else:
        # Low pressure: bid conservatively to preserve budget.
        if my_hp <= 2 or no_water_days >= 2:
            target = DAILY_SALARY * 0.75
        else:
            target = DAILY_SALARY * 0.5

    # Convert target bid into a feasible bid given supply constraints.
    # If supply is tight, we should bid higher to secure water.
    try:
        s = float(supply)
    except Exception:
        s = float(MIN_SUPPLY)

    # Scale with supply tightness: lower supply -> higher bid.
    tightness = (MAX_SUPPLY - s) / float(MAX_SUPPLY - MIN_SUPPLY)
    if tightness < 0.0:
        tightness = 0.0
    if tightness > 1.0:
        tightness = 1.0

    scaled = target * (0.85 + 0.3 * tightness)

    # Also cap based on how many WATER_REQ units we can reasonably want.
    # Ensure bid doesn't exceed budget.
    bid = min(my_budget, scaled)

    # Hard lower/upper bounds for stability
    min_bid = 1.0
    max_bid = my_budget
    if bid < min_bid:
        bid = min_bid
    if bid > max_bid:
        bid = max_bid

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
    day = day_context.get('day', 0)

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', True):
            alive_opps.append((opp_id, opp))

    # If no opponents, spend enough to meet requirement.
    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Extract yesterday bids from previous_trace for immediate reaction.
    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid', 0.0)))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how many allocations exist relative to our requirement.
    # Use explicit int() for any indexing-like behavior (none here), but keep safe.
    # Tight supply -> higher chance others will also bid high.
    tight_supply = supply <= (MIN_SUPPLY + (MAX_SUPPLY - MIN_SUPPLY) * 0.25)

    # Pressure signal from yesterday: if someone bid very high, bandwagon bidding likely.
    high_band = highest_prev_bid >= DAILY_SALARY * 0.85

    # Base bid policy
    if hp <= 2.0 or no_water_days >= 2:
        # Need to secure water urgently.
        target = DAILY_SALARY * (0.85 if not tight_supply else 0.95)
    else:
        if high_band:
            # Match the band but avoid full overpay.
            target = min(DAILY_SALARY * 0.75, highest_prev_bid + 2.0)
        else:
            # If nobody overpaid yesterday, bid enough to be competitive.
            target = DAILY_SALARY * (0.55 if not tight_supply else 0.7)

    # Convert target into a budget-respecting bid.
    # Also cap to avoid bidding more than we can afford.
    bid = min(budget, target)

    # If budget is extremely low, bid what we can.
    if bid < 1e-6:
        return 0.0

    # Small adjustment: if supply is high, slightly underbid.
    if supply >= (MAX_SUPPLY - 1.0):
        bid *= 0.9

    # Ensure bid is non-negative.
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

    supply = float(day_context['supply'])
    day = day_context['day']

    # Alive opponents and their yesterday bids
    alive_opps = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opps.append(opp)

    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Pressure estimate from yesterday
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = 0.0
    if len(yesterday_bids) >= 2:
        sorted_bids = sorted(yesterday_bids, reverse=True)
        second_prev_bid = sorted_bids[1]

    # Tight supply -> more aggressive
    # Normalize supply into [0,1] where 0 is tight (15) and 1 is abundant (25)
    denom = (MAX_SUPPLY - MIN_SUPPLY)
    if denom <= 0:
        supply_factor = 0.5
    else:
        supply_factor = (supply - MIN_SUPPLY) / denom
        if supply_factor < 0.0:
            supply_factor = 0.0
        if supply_factor > 1.0:
            supply_factor = 1.0

    tightness = 1.0 - supply_factor

    # Base bid target
    # Target slightly above the highest yesterday bid if it looks like others were fighting for survival.
    # Otherwise, bid around a mid-high fraction of DAILY_SALARY.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Very high competition yesterday
        target = highest_prev_bid + 2.0
    elif highest_prev_bid >= DAILY_SALARY * 0.65:
        # Moderate competition
        target = max(DAILY_SALARY * (0.58 + 0.2 * tightness), highest_prev_bid * 0.95 + 1.0)
    else:
        # Low competition
        target = DAILY_SALARY * (0.50 + 0.25 * tightness)

    # If my hp is low, increase urgency
    hp = int(my_status['hp'])
    if hp <= 2:
        target *= 1.35
    elif hp <= 4:
        target *= 1.15

    # If budget is low, cap spending
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # If I'm close to running out of water, bid more
    if no_water_days >= 2:
        target *= 1.25
    if no_water_days >= 3:
        target *= 1.35

    # Final cap: cannot exceed budget
    # Also keep bids reasonable: never exceed 1.2*DAILY_SALARY unless budget forces it.
    max_reasonable = DAILY_SALARY * 1.2
    bid = min(budget, max_reasonable, target)

    # Ensure non-negative
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

    # Alive opponents and their immediate yesterday behavior
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    if not alive:
        return max(0.0, min(float(my_status['budget']), DAILY_SALARY * 0.4))

    # Extract yesterday bids (only immediate trace)
    prev_bids = []
    for oid, o in alive:
        pt = o.get('previous_trace', {}) or {}
        b = pt.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    # Estimate how many 9-water units are likely needed; supply is total water pool.
    # If supply is near 25, competition likely stronger; if near 15, fewer units.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # If I'm in danger, bid hard to secure water.
    if my_hp <= 2.0 or no_water_days >= 2:
        cap = my_budget
        # Use a strong but not maximal bid; react to yesterday's highest pressure.
        target = max(DAILY_SALARY * 0.75, highest_prev_bid * 0.9)
        return max(0.0, min(cap, target))

    # Otherwise, bid to beat aggressive survivors without overpaying.
    # If yesterday's highest bid was very high, assume a few agents are willing to spend; bid around that level.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Push moderately; do not match exactly to avoid budget drain.
        target = highest_prev_bid * (0.65 + 0.2 * supply_ratio)
    else:
        # If yesterday bids were moderate, bid slightly above average to increase win probability.
        target = max(DAILY_SALARY * (0.45 + 0.25 * supply_ratio), avg_prev_bid * (0.9 + 0.15 * supply_ratio))

    # Budget-aware smoothing: keep some reserve for later days.
    # Reserve fraction increases if day is later.
    reserve_frac = 0.25 + 0.15 * (day / 10.0)
    max_affordable = my_budget * (1.0 - reserve_frac)
    if max_affordable < 0:
        max_affordable = 0.0

    return max(0.0, min(my_budget, min(target, max_affordable)))
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

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    hp = my_status.get('hp', 0)
    budget = my_status.get('budget', 0.0)

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    # If no opponents are alive, spend enough to secure water.
    if not alive_opponents:
        target = min(budget, DAILY_SALARY * 0.6)
        return float(target)

    # Extract yesterday bids and also infer who is bidding aggressively.
    yesterday_bids = []
    yesterday_pressures = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                b = float(bid)
            except Exception:
                continue
            yesterday_bids.append(b)
            # Pressure proxy: high bid + still alive today implies strong willingness to pay.
            if opp.get('alive', False) and opp.get('hp', 0) > 0:
                yesterday_pressures.append(b)

    if not yesterday_bids:
        # Default conservative bid
        base = DAILY_SALARY * 0.55
        if hp <= 2:
            base = DAILY_SALARY * 0.9
        return float(min(budget, base))

    # Use top-1 and top-2 to slightly overbid the strongest threat.
    top1 = max(yesterday_bids)
    top2 = top1
    if len(yesterday_bids) >= 2:
        sorted_b = sorted(yesterday_bids, reverse=True)
        top1 = sorted_b[0]
        top2 = sorted_b[1]

    # Detect if someone previously died (likely overbid/was outbid early).
    # If any opponent had yesterday hp_after <= 0, we can exploit by not matching their full spend.
    died_yesterday = False
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        if prev and prev.get('hp_after', 1) <= 0:
            died_yesterday = True
            break

    # Supply-based aggressiveness: higher supply means less need to overbid.
    # supply is within [15,25].
    supply_ratio = 0.0
    try:
        supply_ratio = (float(supply) - float(MIN_SUPPLY)) / (float(MAX_SUPPLY) - float(MIN_SUPPLY))
    except Exception:
        supply_ratio = 0.5
    if supply_ratio < 0.0:
        supply_ratio = 0.0
    if supply_ratio > 1.0:
        supply_ratio = 1.0

    # If my hp is low, prioritize survival by bidding closer to top1.
    # Otherwise, bid just above top2/top1 depending on supply.
    if hp <= 2:
        bid_target = min(top1 * 1.03, DAILY_SALARY * 1.05)
    elif hp <= 4:
        bid_target = min(max(top2 * 1.02, top1 * 0.99), DAILY_SALARY * 0.95)
    else:
        # When supply is higher, we can undercut slightly; when lower, overbid slightly.
        undercut = 0.02 + 0.03 * (1.0 - supply_ratio)  # 0.02..0.05
        bid_target = min(top1 * (1.0 + undercut), DAILY_SALARY * (0.85 + 0.15 * supply_ratio))

    # Exploit if someone died yesterday: don't overpay as much.
    if died_yesterday:
        bid_target *= 0.95

    # Ensure we don't exceed budget.
    bid = min(float(budget), float(bid_target))

    # Also avoid bidding too low to secure water when hp is moderate.
    min_bid = 0.0
    if hp > 0:
        min_bid = DAILY_SALARY * (0.35 if supply_ratio > 0.6 else 0.45)
    if hp <= 4:
        min_bid = max(min_bid, DAILY_SALARY * 0.65)

    if bid < min_bid:
        bid = min(float(budget), float(min_bid))

    # Final cap: never bid more than what we can reasonably afford.
    if bid > budget:
        bid = float(budget)

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

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    # Base target: aim to buy just enough to avoid long no-water streaks.
    # Convert supply to an approximate number of water units available.
    # Use conservative fraction because bids are competitive and supply is limited.
    if supply <= 0:
        desired_fraction = 0.2
    else:
        # If supply is near minimum, competition is tighter.
        # desired_fraction increases as supply decreases.
        t = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
        desired_fraction = 0.35 + 0.25 * t

    # React to yesterday's bidding pressure.
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid', 0.0)))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # If someone was very aggressive yesterday, raise our bid slightly to avoid being outbid.
    # Cindy's high average suggests she can afford pressure; Alex's lower max suggests less.
    if highest_prev_bid >= DAILY_SALARY * 1.8:
        aggression = 0.80
    elif highest_prev_bid >= DAILY_SALARY * 1.2:
        aggression = 0.65
    else:
        aggression = 0.55

    # Health urgency: if we're low HP or have accumulated no-water days, bid more.
    if hp <= 2 or no_water_days >= 2:
        urgency = 0.92
    elif hp <= 4 or no_water_days >= 1:
        urgency = 0.72
    else:
        urgency = 0.55

    # Combine factors.
    bid_fraction = min(0.95, max(desired_fraction, 0.25))
    bid_fraction = 0.5 * bid_fraction + 0.5 * aggression
    bid_fraction = 0.6 * bid_fraction + 0.4 * urgency

    # Convert to bid amount. Keep within budget.
    target_bid = bid_fraction * DAILY_SALARY

    # If supply is low, slightly increase to improve chance of securing water.
    if supply < float(WATER_REQ):
        target_bid *= 1.15
    elif supply <= float(MIN_SUPPLY):
        target_bid *= 1.08

    # Ensure we don't bid more than budget.
    final_bid = min(budget, target_bid)

    # Avoid zero bids unless forced.
    if final_bid <= 0.0:
        final_bid = min(budget, DAILY_SALARY * 0.2)

    # Return integer bid (if environment expects numeric, int is safe).
    return float(final_bid)
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

    # Identify alive opponents and extract yesterday bids
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        # If alone, bid only enough to stay safe
        target = DAILY_SALARY * 0.35
        return max(0.0, min(budget, target))

    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Pressure estimate from yesterday
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid
    else:
        highest_prev_bid = 0.0
        second_prev_bid = 0.0

    # Supply pressure: higher supply reduces need to overbid
    # Map supply to aggressiveness multiplier
    if supply <= (MIN_SUPPLY + 0.5):
        supply_mult = 1.0
    elif supply >= (MAX_SUPPLY - 0.5):
        supply_mult = 0.75
    else:
        supply_mult = 0.9

    # If we are close to death or have had no water, bid more
    urgent = (hp <= 2.0) or (no_water_days >= 2)

    # Strategy:
    # - Cindy/David were bidding ~86-89 and survived; match a bit below their peak to win reliably.
    # - Use highest_prev_bid as a ceiling reference.
    base = DAILY_SALARY * 0.6  # baseline moderate bid

    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # High competition yesterday: bid near (but not fully at) their peak
        target = 0.92 * highest_prev_bid
    else:
        # Lower competition: bid between baseline and slightly above second-highest
        target = max(base, second_prev_bid + 5.0)

    if urgent:
        target = max(target, DAILY_SALARY * 0.85)

    # Apply supply multiplier and ensure within budget
    target *= supply_mult

    # Avoid extreme bids; keep under ~95% of daily salary unless urgent
    cap = DAILY_SALARY * (0.95 if urgent else 0.85)
    target = min(target, cap)

    # Final clamp
    bid = max(0.0, min(budget, target))
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

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    # If no opponents alive, conserve budget
    if not alive_opponents:
        bid = DAILY_SALARY * 0.35
        return min(my_budget, bid)

    # Read yesterday bids from previous_trace to infer aggressiveness
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

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    # Supply pressure: closer to MIN_SUPPLY implies tighter competition
    # Normalize to [0,1], where 1 means tightest
    if MAX_SUPPLY > MIN_SUPPLY:
        tightness = 1.0 - (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        tightness = 0.5
    if tightness < 0.0:
        tightness = 0.0
    if tightness > 1.0:
        tightness = 1.0

    # Base bid anchored to opponent aggressiveness observed yesterday
    # Others used ~125-161 avg and up to ~185. We'll target slightly below the top.
    anchor = 0.75 * avg_prev_bid + 0.25 * highest_prev_bid

    # If opponents were very aggressive yesterday, raise slightly
    if highest_prev_bid >= 0.85 * DAILY_SALARY:
        anchor *= 1.05

    # Urgency from my HP and no-water streak
    urgency = 1.0
    if my_hp <= 2:
        urgency = 1.35
    elif my_hp <= 4:
        urgency = 1.15

    # If I've already gone without water, increase further
    if my_no_water_days >= 2:
        urgency *= 1.25
    elif my_no_water_days == 1:
        urgency *= 1.10

    # Tightness increases bid
    anchor *= (0.85 + 0.3 * tightness)

    # Cap bid to avoid overspending; also ensure non-negative
    bid = max(0.0, anchor * urgency)

    # Practical cap: don't exceed a fraction of budget and a fraction of salary
    budget_cap = my_budget
    salary_cap = DAILY_SALARY * (0.95 if my_hp <= 2 else 0.75)
    bid = min(bid, budget_cap, salary_cap)

    # If budget is extremely low, still bid what we can
    if my_budget <= 1e-9:
        return 0.0

    # Ensure at least a small competitive bid when budget allows
    min_competitive = DAILY_SALARY * (0.35 + 0.15 * tightness)
    if bid < min_competitive and my_budget >= min_competitive:
        bid = min_competitive

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

    supply = float(day_context['supply'])
    day = day_context['day']

    # Alive opponents
    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive.append((opp_id, opp))

    # If no opponents, bid to cover our need safely.
    if not alive:
        target = DAILY_SALARY * 0.4
        return min(my_status['budget'], target)

    # Extract yesterday bids from previous_trace
    prev_bids = []
    for _, opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_prev_bid = sorted(prev_bids, reverse=True)[1] if len(prev_bids) >= 2 else 0.0

    # Pressure signals: if someone was bidding aggressively yesterday, they likely will again.
    # If highest_prev_bid is very high, we increase bid to avoid being outcompeted.
    aggressive = highest_prev_bid >= (DAILY_SALARY * 0.85)
    moderate_aggressive = (highest_prev_bid >= (DAILY_SALARY * 0.6)) and not aggressive

    # Our urgency based on hp/no_water
    hp = int(my_status.get('hp', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Supply-based baseline: with supply closer to MIN, competition is higher.
    # We scale our bid within a reasonable band.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Base bid: lower when supply is high and our hp is good; higher when supply is low or hp is critical.
    if hp <= 2 or no_water_days >= 2:
        base = DAILY_SALARY * (0.85 if aggressive else 0.75)
    elif hp <= 4 or no_water_days >= 1:
        base = DAILY_SALARY * (0.65 if aggressive else (0.55 if moderate_aggressive else 0.5))
    else:
        base = DAILY_SALARY * (0.55 if aggressive else (0.45 if moderate_aggressive else 0.4))

    # Adjust upward slightly if yesterday's top bids were extremely high.
    # Keep it small to avoid burning budget like the top bidders.
    if aggressive:
        base = max(base, min(my_status['budget'], highest_prev_bid * 0.55))
    elif moderate_aggressive:
        base = max(base, min(my_status['budget'], second_prev_bid * 0.45 + 10.0))

    # Ensure we don't bid above budget; also avoid bidding too low when supply is scarce.
    min_floor = DAILY_SALARY * (0.35 if supply_ratio >= 0.6 else 0.45)
    bid = max(min_floor, base)

    # If budget is low, bid proportionally to preserve survival.
    if my_status['budget'] < DAILY_SALARY * 0.4:
        bid = min(my_status['budget'], my_status['budget'] * 0.95)

    return min(my_status['budget'], float(bid))
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    # Identify alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o is not None and o.get('alive', False):
            alive_opps.append((oid, o))

    # If no opponents alive, bid conservatively
    if not alive_opps:
        return float(min(my_status.get('budget', 0.0), DAILY_SALARY * 0.4))

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))

    # Read yesterday bids from previous_trace for immediate reaction
    prev_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                prev_bids.append(float(bid))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate how many water units are likely feasible today
    # Use integer indices only; here we only need a coarse supply tier.
    # supply is between 15 and 25 => can cover 1 or 2 units (9 each) with remainder.
    supply_units = int(supply / float(WATER_REQ))  # 1 or 2

    # Strategy:
    # - If supply is low (1 unit), we bid to secure the scarce unit but avoid overpaying.
    # - If supply is higher (2 units), we bid less aggressively.
    # - If someone previously bid extremely high, we avoid matching fully; instead we bid enough to compete.

    # Determine a target bid ceiling based on supply tier
    if supply_units <= 1:
        base = DAILY_SALARY * 0.65
    else:
        base = DAILY_SALARY * 0.45

    # Adjust based on yesterday's highest bid pressure
    # If highest_prev_bid is very high, opponents are likely spending aggressively.
    if highest_prev_bid >= DAILY_SALARY * 1.6:
        # Compete, but don't chase to the maximum.
        target = max(base, highest_prev_bid * 0.35)
    elif highest_prev_bid >= DAILY_SALARY * 1.1:
        target = max(base, highest_prev_bid * 0.25)
    else:
        target = base

    # Survival pressure from my_hp
    if my_hp <= 2:
        # Need water; bid closer to salary to secure.
        target = max(target, DAILY_SALARY * 0.85)
    elif my_hp <= 4:
        target = max(target, DAILY_SALARY * 0.7)

    # Budget safety cap: never bid more than 2/3 of remaining budget to preserve future days
    # (unless critically low HP).
    critical = my_hp <= 2
    budget_cap = my_budget if critical else (my_budget * 2.0 / 3.0)

    # Final bid must be within [0, budget]
    bid = float(min(max(target, 0.0), max(0.0, budget_cap)))

    # If bid is too small and supply is scarce, bump slightly
    if supply_units <= 1 and bid < DAILY_SALARY * 0.3 and my_budget > 0:
        bid = float(min(my_budget, DAILY_SALARY * 0.5))

    return bid
"""
