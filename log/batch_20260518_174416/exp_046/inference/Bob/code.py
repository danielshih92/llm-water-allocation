# ============================================================
# Experiment: exp_046
# Agent: Bob
# Source: exp_046
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

    budget = float(my_status.get('budget', 0.0))
    hp = int(my_status.get('hp', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    # Base target: secure roughly one unit of requirement when supply is moderate.
    # Convert supply to a reasonable bid cap.
    # We avoid exact game mechanics assumptions; bid is the only lever.
    supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY + 1e-9)
    supply_norm = max(0.0, min(1.0, supply_norm))

    # If our HP is low or we've already missed water, raise urgency.
    urgency = 0.0
    if hp <= 2:
        urgency = 0.35
    elif hp <= 3:
        urgency = 0.2
    if no_water_days >= 2:
        urgency = max(urgency, 0.25)

    # Read yesterday bids from each opponent (immediate reaction only).
    prev_bids = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # Baseline bid: around 0.55 of daily salary, adjusted by supply and urgency.
    base = DAILY_SALARY * (0.45 + 0.2 * supply_norm + urgency)

    # If someone previously overbid heavily, don't fully mirror; slightly increase to avoid being outbid.
    if prev_bids:
        highest_prev = max(prev_bids)
        # Thresholds relative to salary: high pressure suggests they expect scarcity.
        if highest_prev >= DAILY_SALARY * 0.85:
            # Match partially: increase but cap to avoid runaway.
            bid = max(base, DAILY_SALARY * 0.65)
            # If we are in danger, go higher.
            if hp <= 2 or no_water_days >= 2:
                bid = max(bid, DAILY_SALARY * 0.85)
        elif highest_prev >= DAILY_SALARY * 0.65:
            bid = max(base, highest_prev * 0.75)
        else:
            # Otherwise, stay near baseline.
            bid = base
    else:
        bid = base

    # Ensure bid is at least enough to matter, but never exceed budget or a reasonable daily cap.
    # Use a minimum floor tied to requirement.
    min_reasonable = max(DAILY_SALARY * 0.25, WATER_REQ * 5)
    bid = max(min_reasonable, bid)

    # Final caps
    bid = min(bid, budget)
    bid = min(bid, DAILY_SALARY * 1.05)

    # If budget is extremely low, spend what we can.
    if budget <= 0:
        return 0.0

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
        if o.get('alive', True):
            alive_opps.append((oid, o))

    if not alive_opps:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Immediate reaction from yesterday's trace
    prev_bids = []
    prev_by_id = {}
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                b = float(b)
            except Exception:
                b = None
        if b is not None:
            prev_bids.append(b)
            prev_by_id[oid] = b

    # Estimate today's needed water to avoid starvation streak
    # If we've already gone multiple days without water, bid more aggressively.
    urgency = 0
    if my_no_water_days >= 2:
        urgency = 2
    elif my_no_water_days == 1:
        urgency = 1

    # Supply-based aggressiveness: higher supply => easier to secure water cheaply.
    supply_factor = 0.55
    if supply >= 21.0:
        supply_factor = 0.45
    elif supply <= 17.0:
        supply_factor = 0.65

    # If someone previously bid very high, they likely want to secure water; counter-bid slightly above.
    if prev_bids:
        highest_prev = max(prev_bids)
        second_prev = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev

        # If Alex is alive and previously bid high, treat as main competitor.
        alex_bid = prev_by_id.get('Alex', None)
        eric_bid = prev_by_id.get('Eric', None)

        # Determine target bid ceiling based on our urgency and hp.
        if my_hp <= 2.0 or urgency >= 2:
            base = DAILY_SALARY * 0.85
        elif my_hp <= 4.0 or urgency == 1:
            base = DAILY_SALARY * 0.65
        else:
            base = DAILY_SALARY * 0.50

        # Counter-bid logic: only pay above if others showed willingness to spend.
        if alex_bid is not None and alex_bid >= DAILY_SALARY * 0.75:
            target = min(my_budget, base)
            # If we can, nudge above Alex's previous bid; otherwise bid near base.
            target = min(my_budget, max(target, alex_bid + 1.0))
            return max(0.0, min(target, DAILY_SALARY * 0.95))

        if highest_prev >= DAILY_SALARY * 0.6:
            # Compete for water; just above the leader but capped.
            target = min(my_budget, (highest_prev + 1.5) * 1.0)
            # If we're healthy and supply is high, don't overpay.
            if my_hp > 6.0 and supply >= 21.0:
                target = min(target, DAILY_SALARY * 0.55)
            return max(0.0, min(target, DAILY_SALARY * 0.9))

        # If nobody bid huge, bid modestly to secure.
        # Use second-highest as a soft guide.
        target = min(my_budget, max(DAILY_SALARY * supply_factor, (second_prev * 0.75) + 5.0))
        if my_hp <= 3.0:
            target = min(my_budget, max(target, DAILY_SALARY * 0.75))
        return max(0.0, min(target, DAILY_SALARY * 0.8))

    # Fallback: no previous bids available
    if my_hp <= 2.0 or urgency >= 2:
        return min(my_budget, DAILY_SALARY * 0.9)
    if my_hp <= 4.0 or urgency == 1:
        return min(my_budget, DAILY_SALARY * 0.7)
    return min(my_budget, DAILY_SALARY * 0.55)
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

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive'):
            alive_opps.append((oid, o))

    if not alive_opps:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Extract yesterday bids for immediate reaction
    yesterday_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        if isinstance(prev, dict):
            bid = prev.get('bid', None)
            if bid is not None:
                yesterday_bids.append((oid, bid))

    # Identify Cindy-like aggressor from yesterday trace
    aggressor = None
    aggressor_bid = 0.0
    for oid, bid in yesterday_bids:
        if bid is None:
            continue
        if bid > aggressor_bid:
            aggressor_bid = float(bid)
            aggressor = oid

    # Supply pressure: with supply 15-25 and water_req=9, winners likely target at least 1 unit.
    # We translate supply to a rough expected water units and adjust bid to be competitive.
    # Use int() for any indexing; no lists used here.
    supply_units = int(supply / WATER_REQ)  # may be 1 for 15-17.9, 2 for 18-25

    # Base bid: aim to outbid the likely aggressor only when we can afford it.
    # Cindy previously ~97 avg; use a threshold near 85% of DAILY_SALARY.
    if aggressor is not None and aggressor_bid >= DAILY_SALARY * 0.85:
        # Cindy (or highest bidder) likely continues.
        # If my HP is healthy, bid moderately; if low HP, bid higher to secure water.
        if my_hp <= 2 or my_no_water_days >= 2:
            target = DAILY_SALARY * 0.75
        else:
            target = DAILY_SALARY * 0.55
        # If supply_units=2, competition may intensify; slightly increase.
        if supply_units >= 2:
            target *= 1.08
        # Ensure we are not too low vs aggressor's last bid.
        target = max(target, min(my_budget, aggressor_bid * 0.75))
    else:
        # No clear aggressor pressure: bid around a baseline.
        # If supply is tight (1 unit), bid more to secure.
        if supply_units <= 1:
            target = DAILY_SALARY * 0.5
        else:
            target = DAILY_SALARY * 0.42
        # If my HP is low, increase.
        if my_hp <= 2 or my_no_water_days >= 2:
            target = max(target, DAILY_SALARY * 0.7)

    # Cap by budget and avoid spending all budget unless critical.
    # If my HP is critical, allow larger fraction.
    if my_hp <= 1 or my_no_water_days >= 3:
        max_spend = my_budget * 0.85
    else:
        max_spend = my_budget * 0.55

    bid = min(my_budget, max_spend, target)

    # If bid becomes too small, still bid at least a minimal fraction to avoid being shut out.
    min_bid = min(my_budget, DAILY_SALARY * 0.25)
    if bid < min_bid and my_hp > 0:
        bid = min(my_budget, min_bid)

    # Final safety: non-negative
    if bid < 0:
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

    # Alive opponents
    alive = [o for o in opponents_status.values() if o.get('alive', True)]
    if not alive:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids to infer pressure
    prev_bids = []
    prev_max = None
    prev_min = None
    near_max_flags = 0
    for opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is None:
            continue
        try:
            b = float(b)
        except Exception:
            continue
        prev_bids.append(b)
        if prev_max is None or b > prev_max:
            prev_max = b
        if prev_min is None or b < prev_min:
            prev_min = b

        # If they bid very high yesterday, assume they may keep pressure
        if b >= 0.9 * DAILY_SALARY * 1.7:  # ~153
            near_max_flags += 1

    # Supply-dependent urgency: higher supply reduces need to overpay
    # Expected allocations are roughly proportional to bids; we just need enough to buy water.
    # When supply is low, survival is harder so we bid more.
    supply_factor = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)  # 0..1
    supply_factor = max(0.0, min(1.0, supply_factor))

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Base bid target: enough to compete but not to chase Cindy's aggressive strategy.
    # Start around 0.55 salary, increase when hp is low or supply is low.
    base = DAILY_SALARY * (0.55 + 0.25 * supply_factor)

    # Urgency adjustments based on my health and consecutive no-water days
    if hp <= 2.0:
        base = DAILY_SALARY * 0.95
    elif hp <= 4.0:
        base = DAILY_SALARY * 0.75

    if no_water_days >= 2:
        base = max(base, DAILY_SALARY * 0.85)

    # Reaction to yesterday's aggressive bidders
    if prev_max is not None:
        # If someone was extremely aggressive, don't mirror; instead slightly increase only if we are at risk.
        if prev_max >= DAILY_SALARY * 1.5:  # ~135
            if hp <= 4.0 or no_water_days >= 1:
                base = max(base, DAILY_SALARY * 0.7)
            else:
                base = min(base, DAILY_SALARY * 0.6)
        else:
            # Moderate environment: nudge toward winning
            base = max(base, (prev_min if prev_min is not None else base) * 0.6)

    # If multiple agents were near-max yesterday, reduce to preserve budget unless critical
    if near_max_flags >= 2 and hp > 4.0:
        base = min(base, DAILY_SALARY * 0.6)

    # Convert to feasible bid: cannot exceed budget
    bid = float(min(budget, base))

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
    day = day_context.get('day', 0)

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    # If no opponents are alive, conserve budget.
    if not alive_opponents:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from immediate previous_trace.
    prev_bids = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict) and prev.get('bid') is not None:
            prev_bids.append(float(prev['bid']))

    # Determine how many full water units we can cover if we secure enough allocation.
    # This is a heuristic: higher supply reduces need for max contest.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY + 1e-9)
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Base pressure from opponents yesterday.
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    median_prev_bid = 0.0
    if prev_bids:
        srt = sorted(prev_bids)
        mid = int(len(srt) // 2)
        median_prev_bid = float(srt[mid])

    # If I am already in danger (low hp or many no-water days), I must secure water.
    danger = (my_status.get('hp', 0) <= 2) or (my_status.get('no_water_days', 0) >= 2)

    # If supply is low, competition is more valuable; bid higher.
    low_supply = supply <= (MIN_SUPPLY + (MAX_SUPPLY - MIN_SUPPLY) * 0.35)

    # Strategy:
    # - When supply is low OR I'm in danger: bid near the top of yesterday's range.
    # - Otherwise: bid around median + small premium.
    if danger or low_supply:
        # If someone already bid very high yesterday, match slightly below to still win sometimes.
        target = max(median_prev_bid + 5.0, highest_prev_bid * 0.92)
        # Add extra when my hp is critically low.
        if my_status.get('hp', 0) <= 1:
            target = max(target, highest_prev_bid * 0.98)
    else:
        target = max(median_prev_bid + 2.0, highest_prev_bid * 0.75)

    # Convert target into a budget-safe bid with a soft cap tied to daily salary.
    # Also ensure we don't overspend if budget is small.
    soft_cap = DAILY_SALARY * (0.95 if (danger or low_supply) else 0.65)
    bid = min(float(my_status['budget']), float(soft_cap), float(target))

    # Ensure non-negative.
    if bid < 0.0:
        bid = 0.0

    # In case budget is extremely low, still bid something to avoid wasting the day.
    # (Keep it small but >0.)
    if bid == 0.0 and my_status.get('budget', 0.0) > 0.0:
        bid = min(float(my_status['budget']), 1.0)

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
    day = day_context['day']

    # Alive opponents
    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append(o)

    if not alive_opponents:
        # If alone, bid to maintain survival; avoid spending too much.
        target = DAILY_SALARY * 0.45
        return float(min(my_status['budget'], target))

    # Read yesterday bids from immediate previous_trace only
    prev_bids = []
    prev_hp_after = []
    for o in alive_opponents:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev['bid']))
            prev_hp_after.append(prev.get('hp_after', None))

    # Heuristic pressure signals
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    # If any opponent was bidding very high yesterday, they likely continue to contest.
    near_cap = highest_prev_bid >= 0.95 * 151.0  # using observed cap-ish magnitude

    # Estimate how many water units we can buy if we bid around a fraction of salary.
    # We want enough to cover at least one day of requirement.
    # Convert supply to a rough affordability factor.
    # (No opponent bids are visible today, so we use supply to decide aggressiveness.)
    supply_clamped = max(MIN_SUPPLY, min(MAX_SUPPLY, supply))

    # Base bid: enough to secure ~1 unit of water when supply is moderate.
    # Use a conservative fraction of salary unless pressure is high.
    base_frac = 0.55
    if near_cap:
        base_frac = 0.75

    # If our HP is low, we must spend more.
    hp = float(my_status['hp'])
    if hp <= 2.0:
        base_frac = max(base_frac, 0.95)
    elif hp <= 4.0:
        base_frac = max(base_frac, 0.80)

    # If supply is low, competition is more valuable; shade upward slightly.
    if supply_clamped <= 18.0:
        base_frac = min(0.95, base_frac + 0.10)
    elif supply_clamped >= 22.0:
        base_frac = max(0.45, base_frac - 0.05)

    # If yesterday we saw extremely high bids but our HP is safe, we still shade to avoid overpaying.
    # Use highest_prev_bid to set an upper bound for today's contest.
    my_budget = float(my_status['budget'])

    # Target bid derived from salary fraction
    target = DAILY_SALARY * base_frac

    # Upper bound: don't exceed what seems like typical high contest unless we are in danger.
    # If near_cap and our HP is not critical, cap at ~0.85 of highest_prev_bid.
    if not (hp <= 2.0):
        if highest_prev_bid > 0:
            target = min(target, highest_prev_bid * 0.85)

    # Ensure we don't bid above budget
    bid = min(my_budget, target)

    # Final safety: if bid is too low relative to requirement, bump slightly.
    # We don't know price mechanics; so just ensure a minimum meaningful spend.
    min_bid = DAILY_SALARY * 0.30
    if bid < min_bid and hp > 2.0:
        bid = min(my_budget, min_bid)

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

    # Alive opponents and yesterday bids
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        # No competition: bid conservatively
        return max(0, min(my_status['budget'], DAILY_SALARY * 0.4))

    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Estimate competitive pressure from yesterday
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / float(len(yesterday_bids))
    else:
        highest_prev_bid = 0.0
        avg_prev_bid = DAILY_SALARY * 0.55

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    no_water_days = int(my_status.get('no_water_days', 0))

    # Supply pressure: if supply is near the minimum, competition is more valuable
    supply_tight = supply <= 18.0

    # Base target: slightly under the average/typical bids to avoid overpaying
    # Typical observed bids ~116-120; we aim around 108-114 when safe.
    target = avg_prev_bid * 0.92

    # If market was intense yesterday, raise bid to avoid losing water.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        target = max(target, highest_prev_bid * 0.9)

    # If my hp is low or I've already gone without water, increase urgency.
    if my_hp <= 3.0 or no_water_days >= 1:
        target = max(target, DAILY_SALARY * (0.85 if supply_tight else 0.75))

    # If supply is tight and I'm healthy, still match closer to the market.
    if supply_tight and my_hp > 3.0:
        target = max(target, DAILY_SALARY * 0.7)

    # Never exceed budget; also cap to avoid reckless spending.
    cap = my_budget
    bid = min(cap, target)

    # Ensure non-negative integer-ish bid (game may accept float, but keep safe)
    if bid < 0:
        bid = 0.0
    return bid
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
            alive.append((oid, o))

    if not alive:
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday bids to infer aggressiveness.
    yesterday_bids = []
    yesterday_by_agent = {}
    for oid, o in alive:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                b = float(b)
            except Exception:
                continue
            yesterday_bids.append(b)
            yesterday_by_agent[oid] = b

    if yesterday_bids:
        max_bid_y = max(yesterday_bids)
        # Identify if Cindy was the top aggressor yesterday.
        cindy_bid = None
        for oid, b in yesterday_by_agent.items():
            if oid == 'Cindy':
                cindy_bid = b
                break
    else:
        max_bid_y = 0.0
        cindy_bid = None

    # Supply pressure: higher supply reduces need to overbid.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Urgency based on hp and no_water_days.
    urgency = 0.0
    if hp <= 2.0:
        urgency += 1.0
    elif hp <= 4.0:
        urgency += 0.6
    if no_water_days >= 2:
        urgency += 0.5
    if no_water_days >= 3:
        urgency += 0.7

    # Baseline bid: aim to win only when needed.
    # If we are in danger, bid closer to salary; otherwise bid mid.
    if urgency >= 1.0:
        base = DAILY_SALARY * (0.75 - 0.15 * supply_ratio)
    elif urgency >= 0.6:
        base = DAILY_SALARY * (0.6 - 0.1 * supply_ratio)
    else:
        base = DAILY_SALARY * (0.45 - 0.05 * supply_ratio)

    # Exploit yesterday: Cindy spiked; if she likely continues, slightly overcut her
    # but only when supply is not too low (so we can afford to contest).
    if cindy_bid is not None and supply >= (MIN_SUPPLY + (MAX_SUPPLY - MIN_SUPPLY) * 0.4):
        # If Cindy bid was very high yesterday, cap our aggression to avoid overspending.
        target = cindy_bid + 2.0
        cap = DAILY_SALARY * 0.85
        base = min(base, cap)
        base = max(base, target * 0.85)  # lean towards contesting

    # If yesterday max bid was extremely high, avoid matching unless we're urgent.
    if max_bid_y >= DAILY_SALARY * 1.3 and urgency < 0.6:
        base = min(base, DAILY_SALARY * 0.55)

    # Ensure bid is feasible.
    bid = min(budget, max(0.0, base))

    # If we have very low budget, bid proportionally.
    if budget <= DAILY_SALARY * 0.25:
        bid = min(bid, budget * 0.9)

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

    # If we can’t pay, bid 0.
    if my_status['budget'] <= 0:
        return 0.0

    # Alive opponents (for trace reaction)
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # Baseline: conserve budget unless pressure is high.
    # Supply pressure: with higher supply, we can bid less and still likely win.
    supply_frac = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_frac = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    if supply_frac < 0.0:
        supply_frac = 0.0
    if supply_frac > 1.0:
        supply_frac = 1.0

    # Extract yesterday bids from previous_trace (immediate reaction only)
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', None)
        if isinstance(prev, dict) and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass
        elif isinstance(prev, list) and len(prev) > 0:
            # In case previous_trace is a list of dicts, take last
            last = prev[-1]
            if isinstance(last, dict) and last.get('bid') is not None:
                try:
                    prev_bids.append(float(last['bid']))
                except Exception:
                    pass

    # Determine pressure level from yesterday
    highest_prev_bid = None
    if len(prev_bids) > 0:
        highest_prev_bid = max(prev_bids)

    # If no trace info, use a conservative supply-based bid.
    if highest_prev_bid is None:
        # Bid between 0.35 and 0.6 of DAILY_SALARY depending on supply.
        target = DAILY_SALARY * (0.60 - 0.25 * supply_frac)
        return float(min(my_status['budget'], max(0.0, target)))

    # If yesterday someone bid extremely high, avoid getting trapped by overbidding.
    # Instead, bid slightly below the highest to win when others are less aggressive.
    # Also, if my HP is low, I must secure water.
    my_hp = float(my_status['hp'])

    # Aggression thresholds from observed meta-round: ~90-100 were common.
    high_pressure = highest_prev_bid >= DAILY_SALARY * 0.95
    moderate_pressure = (highest_prev_bid >= DAILY_SALARY * 0.75) and (highest_prev_bid < DAILY_SALARY * 0.95)

    if my_hp <= 2.0:
        # Emergency: bid close to salary.
        base = DAILY_SALARY * (0.85 - 0.10 * supply_frac)
    elif high_pressure:
        base = DAILY_SALARY * (0.65 - 0.15 * supply_frac)
    elif moderate_pressure:
        base = DAILY_SALARY * (0.55 - 0.10 * supply_frac)
    else:
        base = DAILY_SALARY * (0.45 - 0.05 * supply_frac)

    # Undercut strategy: aim just below the highest previous bid.
    # Slightly larger undercut when my HP is healthy to save budget.
    undercut = 2.0
    if my_hp >= 8.0:
        undercut = 4.0
    elif my_hp >= 5.0:
        undercut = 3.0

    target = min(base, highest_prev_bid - undercut)

    # Ensure we’re not bidding too tiny when supply is low.
    # Low supply means water is scarce; increase floor.
    low_supply_floor = DAILY_SALARY * (0.40 + 0.15 * (1.0 - supply_frac))
    if target < low_supply_floor:
        target = low_supply_floor

    # Final cap by budget.
    if target > my_status['budget']:
        target = my_status['budget']

    # Never negative.
    if target < 0.0:
        target = 0.0

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
    day = int(day_context['day'])

    # Identify alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # If we are in critical hp, prioritize survival with a strong bid.
    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])

    # Reaction to yesterday bids (only immediate trace)
    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Estimate how much water we likely need today.
    # If supply is low, winning a larger share is more valuable.
    # Use a conservative scaling based on supply range.
    # target_bid_base is between ~0.45 and ~0.85 of daily salary.
    if supply <= MIN_SUPPLY:
        target_bid_base = 0.85
    elif supply >= MAX_SUPPLY:
        target_bid_base = 0.45
    else:
        # Linear interpolation between MIN_SUPPLY and MAX_SUPPLY
        t = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
        target_bid_base = 0.85 - 0.40 * t

    # If yesterday saw very high bids, it suggests pressure; slightly raise.
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If someone was bidding near/above typical salary, treat as high-pressure.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_hp > 3:
                target_bid_base = max(target_bid_base, 0.70)
            else:
                target_bid_base = max(target_bid_base, 0.95)
        # If bids were generally low, we can undercut.
        elif max(yesterday_bids) <= DAILY_SALARY * 0.60:
            target_bid_base = min(target_bid_base, 0.60)

    # Convert base to bid amount; also ensure we don't exceed budget.
    bid = DAILY_SALARY * target_bid_base

    # Budget-aware cap: never bid more than we can afford.
    if my_budget <= 0:
        return 0.0
    if bid > my_budget:
        bid = my_budget

    # Ensure some minimal competitive bid if budget allows.
    # If we have enough budget, avoid bidding too low.
    min_competitive = DAILY_SALARY * 0.35
    if my_budget >= min_competitive and bid < min_competitive:
        bid = min_competitive

    # If hp is extremely low, go aggressive.
    if my_hp <= 2:
        bid = min(my_budget, DAILY_SALARY * 0.95)

    return float(bid)
"""
