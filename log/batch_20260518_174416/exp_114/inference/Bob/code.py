# ============================================================
# Experiment: exp_114
# Agent: Bob
# Source: exp_114
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context['supply'])
    day = day_context['day']

    budget = float(my_status['budget'])
    hp = float(my_status['hp'])
    no_water_days = int(my_status['no_water_days'])

    alive_opponents = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    # Collect yesterday bids from immediate previous_trace only
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Safety cap: never bid more than budget
    if budget <= 0:
        return 0

    # Base bid target depends on our urgency
    # If we've already been without water, increase urgency.
    urgency = 0
    if no_water_days >= 2:
        urgency = 2
    elif no_water_days == 1:
        urgency = 1

    # If our HP is low, we must secure water.
    hp_pressure = 0
    if hp <= 2:
        hp_pressure = 3
    elif hp <= 3:
        hp_pressure = 2
    elif hp <= 5:
        hp_pressure = 1

    # Competitive response to opponent yesterday aggressiveness
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / float(len(yesterday_bids))

        # If they were bidding very high, they likely needed water badly.
        if highest_prev_bid >= 0.85 * DAILY_SALARY:
            # Bid to beat them, but avoid full budget burn unless critical.
            if hp_pressure >= 3 or urgency >= 2:
                bid = min(budget, highest_prev_bid + 5.0)
            else:
                bid = min(budget, max(highest_prev_bid + 1.5, 0.65 * DAILY_SALARY))
        # If they were moderate, match around their average plus a small edge.
        elif highest_prev_bid >= 0.45 * DAILY_SALARY:
            bid = min(budget, max(highest_prev_bid + 0.5, avg_prev_bid + 2.0))
        else:
            # They were relaxed; conserve budget and bid at a modest level.
            # Ensure we still try to get water if supply is not too high.
            if supply <= 18.0:
                bid = min(budget, 0.55 * DAILY_SALARY + 5.0 * urgency + 3.0 * hp_pressure)
            else:
                bid = min(budget, 0.45 * DAILY_SALARY + 4.0 * urgency + 2.0 * hp_pressure)
    else:
        # No trace info: choose a budget-aware starting bid.
        if hp_pressure >= 3 or urgency >= 2:
            bid = min(budget, 0.85 * DAILY_SALARY)
        elif hp_pressure >= 2 or urgency >= 1:
            bid = min(budget, 0.65 * DAILY_SALARY)
        else:
            # Light bid to preserve budget early.
            if day <= 3:
                bid = min(budget, 0.50 * DAILY_SALARY)
            else:
                bid = min(budget, 0.55 * DAILY_SALARY)

    # Additional adjustment based on supply: lower supply -> more likely competition.
    if supply <= 16.0:
        bid = min(budget, bid + 8.0)
    elif supply >= 23.0:
        bid = max(0.0, bid - 6.0)

    # Final clamp
    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget

    return bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Alive opponents and yesterday pressure cues
    alive_opps = [o for o in opponents_status.values() if o.get('alive')]
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

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

    # Supply pressure: if supply is near the lower end, bidding tends to be more competitive
    supply_low = supply <= 0.5 * (15.0 + 25.0)

    # Base aggressiveness tied to my HP
    my_hp = int(my_status['hp'])
    my_budget = float(my_status['budget'])

    # If yesterday had very high bids, assume others are fighting for survival.
    pressure_high = highest_prev_bid >= DAILY_SALARY * 0.85

    # If I'm critical, bid to secure water.
    if my_hp <= 2:
        target = DAILY_SALARY * (0.9 if pressure_high else 0.75)
    elif pressure_high:
        # When others overbid, I still don't want to burn budget; bid moderately.
        target = DAILY_SALARY * (0.35 if supply_low else 0.45)
    else:
        # Normal mode: bid enough to stay competitive but conserve budget.
        target = DAILY_SALARY * (0.55 if supply_low else 0.45)

    # Additional adjustment: if my no_water_days is high, increase bids.
    no_water_days = int(my_status.get('no_water_days', 0))
    if no_water_days >= 2:
        target *= 1.15
    if no_water_days >= 3:
        target *= 1.25

    # Clamp to budget
    bid = float(min(my_budget, target))

    # Ensure non-negative bid
    if bid < 0.0:
        bid = 0.0

    return bid
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

    supply = day_context['supply']
    day = day_context['day']

    # Identify alive opponents and extract yesterday bid pressure
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            prev = o.get('previous_trace', {})
            bid = prev.get('bid', None)
            if bid is not None:
                alive_opps.append((oid, bid, o))

    # Baseline: if no info or no opponents alive
    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Yesterday pressure signals
    yesterday_bids = [b for (_, b, _) in alive_opps]
    highest_prev_bid = max(yesterday_bids)
    # Find Cindy's behavior specifically (she survived with high average bid)
    cindy_prev = None
    for oid, b, o in alive_opps:
        if oid == 'Cindy':
            cindy_prev = b
            break

    # Supply-based aggressiveness: more supply means we can bid less and still win water
    # Convert supply to an integer bucket safely
    # supply is between 15 and 25; bucket 15-19 => 0, 20-25 => 1
    supply_bucket = 0
    if supply >= 20.0:
        supply_bucket = 1

    # Our urgency
    hp = my_status['hp']
    no_water_days = my_status['no_water_days']
    budget = my_status['budget']

    # Determine target bid
    # If Cindy likely bids high, we try to slightly undercut/meet her expected level.
    # If our hp is low, we must pay more.
    if cindy_prev is not None:
        # Cindy survived (hp 9) and had high average bids; treat her as main threat.
        # If her yesterday bid was very high, increase our bid.
        if cindy_prev >= DAILY_SALARY * 1.6:  # ~144
            base = DAILY_SALARY * (0.95 if hp <= 3 else 0.7)
            # If we can, match just below her pressure to avoid overpaying.
            target = min(base, cindy_prev - 2.0)
        else:
            target = DAILY_SALARY * (0.65 if hp > 3 else 0.9)
    else:
        # General case: use highest_prev_bid as pressure
        if highest_prev_bid >= DAILY_SALARY * 1.6:
            target = DAILY_SALARY * (0.75 if hp > 3 else 0.95)
        else:
            target = DAILY_SALARY * (0.6 if hp > 3 else 0.85)

    # Adjust for supply: with more supply, reduce bid; with less, increase slightly
    if supply_bucket == 1:
        target *= 0.92
    else:
        target *= 1.05

    # Urgency escalation if we've already missed water days
    if no_water_days >= 2:
        target *= 1.15

    # Clamp to budget and sensible bounds
    target = max(1.0, target)
    bid = min(budget, target)

    # If budget is too low, still bid what we can to avoid death
    if bid < DAILY_SALARY * 0.2 and hp <= 2:
        bid = min(budget, DAILY_SALARY * 0.9)

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

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return max(0.0, min(float(my_status['budget']), DAILY_SALARY * 0.4))

    # Read yesterday bids to infer pressure level.
    yesterday_bids = []
    yesterday_info = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                b_val = float(b)
            except Exception:
                continue
            yesterday_bids.append(b_val)
            yesterday_info.append((oid, b_val, prev.get('hp_after', None), prev.get('status', None)))

    # If no trace bids, fall back to conservative mid bidding.
    if not yesterday_bids:
        base = 0.55 * DAILY_SALARY
        if float(my_status['hp']) <= 2:
            base = 0.85 * DAILY_SALARY
        return max(0.0, min(float(my_status['budget']), base))

    highest_prev_bid = max(yesterday_bids)

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    no_water_days = int(my_status.get('no_water_days', 0))

    # Pressure mapping: if someone bid near or above Cindy-like level, we must contest.
    # Cindy's max/avg were ~142.5; use that as a proxy threshold.
    contest_threshold = 0.80 * DAILY_SALARY  # 72
    strong_threshold = 1.20 * DAILY_SALARY   # 108

    # Supply factor: with medium supply in [15,25], water is scarce; bid slightly more.
    # Map supply to a multiplier in [0.95, 1.15]
    if MAX_SUPPLY == MIN_SUPPLY:
        supply_mult = 1.0
    else:
        supply_mult = 0.95 + 0.20 * ((supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY))

    # Base bid depends on my HP and how many dry days already.
    if my_hp <= 2 or no_water_days >= 2:
        base = 0.88 * DAILY_SALARY
    elif my_hp <= 4:
        base = 0.70 * DAILY_SALARY
    else:
        base = 0.58 * DAILY_SALARY

    # Decide escalation vs. underbidding.
    if highest_prev_bid >= strong_threshold:
        # Someone was willing to pay a lot; match/beat slightly if we can.
        bid = max(base, (highest_prev_bid * 1.02))
    elif highest_prev_bid >= contest_threshold:
        # Moderate contest: try to be competitive but not wasteful.
        bid = max(base, (highest_prev_bid * 0.90 + 6.0))
    else:
        # Low bids elsewhere: we can shade downward.
        bid = base * 0.95

    bid *= supply_mult

    # Ensure we can afford it.
    bid = max(0.0, min(my_budget, bid))

    # If we are extremely low budget, still bid something minimal to avoid full dry streak.
    if my_budget <= 5.0:
        return max(0.0, my_budget)

    # Small epsilon to break ties.
    return float(bid + 0.01)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Alive opponents
    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append((oid, o))

    # If no one alive, conserve budget
    if not alive_opponents:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from traces (immediate reaction)
    yesterday_bids = []
    yesterday_by_id = {}
    for oid, o in alive_opponents:
        prev = o.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                b_val = float(b)
            except Exception:
                continue
            yesterday_bids.append(b_val)
            yesterday_by_id[oid] = b_val

    # Target a bid band based on who was aggressive yesterday
    # Cindy and David were around 118-140; Eric was 6.
    # We'll aim to outbid low bidders but not fully match high bidders.
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        min_prev = min(yesterday_bids)

        # If someone bid extremely high, assume strong contest; cap our bid.
        if max_prev >= DAILY_SALARY * 1.4:  # ~126
            # Our hp is presumably good; bid enough to secure but not too high.
            base = DAILY_SALARY * 0.7
        elif max_prev >= DAILY_SALARY * 1.1:  # ~99
            base = DAILY_SALARY * 0.6
        else:
            base = DAILY_SALARY * 0.5

        # If there exists a very low bidder (like Eric at 6), nudge above it.
        # Add a small premium to win against under-bidding.
        low_candidates = [b for b in yesterday_bids if b <= DAILY_SALARY * 0.2]
        if low_candidates:
            low_min = min(low_candidates)
            base = max(base, low_min + 5.0)

        # Supply-aware adjustment: higher supply reduces urgency.
        # If supply is tight (<= WATER_REQ), bid higher.
        if supply <= float(WATER_REQ) + 1.0:
            base *= 1.05
        elif supply >= float(WATER_REQ) + 6.0:
            base *= 0.95

    else:
        # Default if no trace bids
        base = DAILY_SALARY * 0.55

    # HP-based risk adjustment
    hp = float(my_status.get('hp', 0))
    if hp <= 2:
        base = DAILY_SALARY * 0.95
    elif hp <= 4:
        base = max(base, DAILY_SALARY * 0.75)

    # Budget cap
    budget = float(my_status.get('budget', 0))
    if budget <= 0:
        return 0.0

    # Final bid: keep within budget and a reasonable upper bound
    # Also avoid bidding above what would consume too much relative to salary.
    bid = float(min(budget, base))

    # If supply is near max, slightly reduce to conserve
    if supply >= float(MAX_SUPPLY) - 1.0:
        bid *= 0.9

    # Ensure non-negative
    if bid < 0:
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

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append((oid, o))

    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Read only yesterday's immediate bid from each opponent trace
    prev_bids = []
    for oid, o in alive_opponents:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # Estimate how many water units are likely to be contested
    # If supply is near max, we can bid less; if near min, bid more.
    supply_ratio = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Determine target bid band
    # Cindy's behavior: very high bids; avoid matching her unless we must.
    # We'll target slightly above the median of yesterday bids (if enough data),
    # but cap below Cindy-like extremes.
    target = None
    if prev_bids:
        prev_bids_sorted = sorted(prev_bids)
        n = len(prev_bids_sorted)
        mid = prev_bids_sorted[n // 2]
        # If there is a very high outlier (Cindy), don't chase it.
        high = prev_bids_sorted[-1]
        low = prev_bids_sorted[0]
        # Cushion above median to beat typical bids.
        target = mid + 5.0
        # If supply is tight (low ratio), push up toward high outlier but not too close.
        if supply_ratio < 0.5:
            target = (mid + high) / 2.0
        # If supply is abundant, stay closer to median.
        if supply_ratio >= 0.5:
            target = mid + 2.0

        # Cap to avoid Cindy's extreme bids.
        # Use a soft cap around 0.85 of the top observed bid.
        cap = high * 0.85
        if cap > 0:
            target = min(target, cap)

        # Ensure target isn't below a reasonable baseline.
        baseline = DAILY_SALARY * 0.45
        target = max(target, baseline)
    else:
        target = DAILY_SALARY * 0.55

    # HP pressure: if we're about to die or already low, bid harder.
    if hp <= 2 or no_water_days >= 2:
        target = max(target, DAILY_SALARY * 0.85)
    elif hp <= 4:
        target = max(target, DAILY_SALARY * 0.65)
    else:
        # With high hp, we can be selective.
        target = min(target, DAILY_SALARY * 0.75)

    # Convert to feasible bid: can't exceed budget.
    # Also keep within a reasonable per-day range.
    bid = min(budget, target)

    # If budget is too low, still bid something proportional to budget.
    if bid <= 0.0:
        bid = min(budget, DAILY_SALARY * 0.3)

    # Final safety clamp.
    bid = max(0.0, bid)
    return bid
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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    # If we have no budget, bid 0
    if my_budget <= 0:
        return 0.0

    # Gather yesterday bids from alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    top_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_top = 0.0
    if len(yesterday_bids) >= 2:
        s = sorted(yesterday_bids, reverse=True)
        second_top = s[1]

    # Estimate how many full water units supply can support
    # Use int indices explicitly (rule compliance)
    supply_units = int(supply / WATER_REQ) if WATER_REQ > 0 else 0

    # Baseline aggressiveness by supply and my health
    # If supply is low (15-18), competition is higher -> bid higher.
    if supply <= 18.0:
        base_mult = 0.70
    elif supply <= 21.0:
        base_mult = 0.55
    else:
        base_mult = 0.45

    # Health pressure
    if my_hp <= 2.0 or my_no_water_days >= 2:
        base_mult += 0.25
    elif my_hp <= 4.0:
        base_mult += 0.10

    # React to yesterday's extreme bidding: Cindy bid very high and survived; others died after overpay.
    # If someone bid extremely high, we can’t safely match; instead, bid around a fraction of that.
    extreme_threshold = 0.85 * DAILY_SALARY  # 76.5
    if top_bid >= extreme_threshold:
        # Avoid reckless matching; bid to secure at mid-level.
        base_mult = max(base_mult, 0.60)

    # Convert to bid, but cap by budget and a reasonable fraction
    desired = DAILY_SALARY * base_mult

    # If we expect others to bid around their top, try to slightly undercut using second_top when available
    if second_top > 0.0:
        # Bid between 5% below top and around second_top+ small epsilon, but not too high.
        undercut = min(desired, second_top * 0.98 + 1.0)
        desired = max(undercut, DAILY_SALARY * 0.35)

    # Supply_units influences how hard it is to secure water; if supply_units is small, bid more.
    if supply_units <= 1:
        desired *= 1.15
    elif supply_units >= 2:
        desired *= 0.95

    # Final cap
    bid = min(my_budget, desired)

    # If bid is too tiny relative to chance of winning, add a small floor when we still have budget
    min_floor = 0.25 * DAILY_SALARY
    if bid < min_floor and my_hp > 1.0:
        bid = min(my_budget, min_floor)

    # Ensure non-negative
    if bid < 0.0:
        bid = 0.0

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
    day = day_context['day']

    # Alive opponents
    alive_opponents = [o for o in opponents_status.values() if o.get('alive', True)]
    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.45)

    # Extract yesterday bids from previous_trace
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

    # Determine urgency from my hp and no-water days
    hp = float(my_status['hp'])
    no_water_days = float(my_status['no_water_days'])
    budget = float(my_status['budget'])

    # Supply factor: if supply is tight, we need to bid more to secure water.
    # With our fixed water requirement, treat supply < 20 as tighter.
    if supply <= 19.0:
        tight_supply_multiplier = 1.15
    elif supply >= 22.0:
        tight_supply_multiplier = 0.95
    else:
        tight_supply_multiplier = 1.0

    # Base bid depends on my health.
    if hp <= 2.0 or no_water_days >= 2.0:
        base = DAILY_SALARY * 0.85
    elif hp <= 4.0:
        base = DAILY_SALARY * 0.65
    else:
        base = DAILY_SALARY * 0.55

    # React to yesterday's highest pressure.
    # If someone bid very high, we must contest more.
    if highest_prev_bid >= DAILY_SALARY * 1.35:
        # Cindy-like aggressive pressure; bid close but not max.
        contest = highest_prev_bid * 0.92
    elif highest_prev_bid >= DAILY_SALARY * 1.05:
        contest = max(highest_prev_bid * 0.80, DAILY_SALARY * 0.60)
    else:
        # Low pressure; keep moderate bid to save budget.
        contest = max(DAILY_SALARY * 0.50, highest_prev_bid * 0.70)

    bid = contest * tight_supply_multiplier

    # Safety caps to avoid overspending.
    # If my budget is low, don't exceed a fraction.
    if budget <= DAILY_SALARY * 0.8:
        bid_cap = budget * 0.55
    elif budget <= DAILY_SALARY * 2.0:
        bid_cap = budget * 0.65
    else:
        bid_cap = budget * 0.75

    bid = min(bid, bid_cap)

    # Ensure non-negative and at least small positive to avoid 0-advantage.
    if bid < 0.0:
        bid = 0.0
    if bid == 0.0:
        bid = min(budget, DAILY_SALARY * 0.2)

    # Final clamp to budget
    if bid > budget:
        bid = budget

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

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        try:
            if opp.get('alive', False):
                alive_opponents.append(opp)
        except Exception:
            continue

    if not alive_opponents:
        cap = DAILY_SALARY * 0.4
        return max(0.0, min(my_budget, cap))

    # Immediate reaction to yesterday's bids
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate aggressiveness: Cindy survived with very high average bid yesterday
    # Use highest_prev_bid as proxy; if it was high, expect continued competition.
    critical = (my_hp <= 2) or (my_no_water_days >= 2)

    # Supply pressure: higher supply usually lowers required bids, but in simultaneous bidding
    # we still need enough to secure water when hp is low.
    supply_norm = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    if supply_norm < 0.0:
        supply_norm = 0.0
    if supply_norm > 1.0:
        supply_norm = 1.0

    # Base target bid: undercut likely top bidder while staying competitive.
    # If Cindy-like aggression (highest_prev_bid large), bid slightly higher; otherwise bid moderate.
    if highest_prev_bid >= DAILY_SALARY * 0.9:
        target = DAILY_SALARY * (0.72 - 0.15 * supply_norm)
    else:
        target = DAILY_SALARY * (0.62 - 0.10 * supply_norm)

    # If we are critical, override to ensure survival.
    if critical:
        target = DAILY_SALARY * (0.88 - 0.05 * supply_norm)

    # If we are healthy and not under pressure, avoid overpaying.
    if my_hp >= 7 and my_no_water_days == 0:
        target = min(target, DAILY_SALARY * 0.58)

    # Cap by budget
    if my_budget <= 0.0:
        return 0.0
    bid = min(my_budget, target)

    # Never bid negative
    if bid < 0.0:
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday's bids for immediate reaction
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

    # Identify Cindy-like pressure (survivor with high bid range)
    # We don't know exact opponent logic; use yesterday trace to infer aggressor.
    aggressor_prev = 0.0
    for opp_id, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        if prev.get('bid', None) is not None and opp.get('alive', False):
            try:
                bidv = float(prev['bid'])
            except Exception:
                bidv = 0.0
            if bidv >= highest_prev_bid * 0.85:
                aggressor_prev = max(aggressor_prev, bidv)

    # Base target based on my HP and no-water streak
    # If I'm healthy, try to bid just enough to beat weak opponents.
    # If I'm low HP or have accumulated no-water days, bid more.
    if hp <= 2.0 or no_water_days >= 2:
        urgency = 1.0
    elif hp <= 4.0 or no_water_days >= 1:
        urgency = 0.7
    else:
        urgency = 0.4

    # Supply factor: higher supply reduces need to overbid
    # supply in [15,25]
    supply_norm = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_norm = max(0.0, min(1.0, supply_norm))

    # If Cindy (or main survivor) was bidding very high yesterday, cap our bid below that.
    # Otherwise, bid around a moderate fraction of daily salary.
    if aggressor_prev >= DAILY_SALARY * 1.2 or highest_prev_bid >= DAILY_SALARY * 1.2:
        # Aggressive opponent likely consuming water; we respond with moderate undercut.
        # Undercut by ~10-25% depending on urgency.
        undercut = 0.25 - 0.15 * urgency  # ranges ~0.10..0.25
        target = aggressor_prev * (1.0 - undercut)
        # Also ensure we don't go too low to avoid starvation
        floor_bid = DAILY_SALARY * (0.35 + 0.35 * urgency)  # ~0.35..0.70
        target = max(target, floor_bid)
    else:
        # No extreme aggressor: bid to secure water reliably
        target = DAILY_SALARY * (0.45 + 0.35 * urgency) * (0.85 + 0.15 * (1.0 - supply_norm))

    # If highest_prev_bid was moderate, slightly increase to compete
    if highest_prev_bid > 0.0 and highest_prev_bid < DAILY_SALARY * 1.2:
        target = max(target, highest_prev_bid * (0.85 + 0.1 * urgency))

    # Final clamp: cannot exceed budget; also avoid wasting when budget is low
    # Use a conservative cap to reduce variance.
    max_affordable = budget
    if budget <= 0.0:
        return 0.0

    # Don't exceed a fraction of budget unless urgency is high
    budget_cap = budget * (0.55 + 0.35 * urgency)  # ~0.55..0.90
    final_bid = min(target, budget_cap, max_affordable)

    # Ensure non-negative
    if final_bid < 0.0:
        final_bid = 0.0

    return float(final_bid)
"""
