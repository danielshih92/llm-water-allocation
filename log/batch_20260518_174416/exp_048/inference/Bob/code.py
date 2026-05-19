# ============================================================
# Experiment: exp_048
# Agent: Bob
# Source: exp_048
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

    # Alive opponents
    alive_opponents = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    # Emergency safeguard
    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    if budget <= 0:
        return 0

    # Read yesterday bids (immediate reaction)
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # Heuristic target bid based on opponent pressure
    # If someone was willing to pay very high yesterday, assume they are competing for survival.
    if len(prev_bids) > 0:
        highest_prev_bid = max(prev_bids)
    else:
        highest_prev_bid = 0.0

    # Estimate how many full water requirements the supply can cover.
    # Use explicit int() for any index-like behavior.
    # We only use it for scaling, not indexing.
    supply_units = supply / float(WATER_REQ) if WATER_REQ > 0 else 0.0

    # Base bid level tied to our survival state.
    if hp <= 2 or no_water_days >= 2:
        base = DAILY_SALARY * 0.85
    elif hp <= 3 or no_water_days >= 1:
        base = DAILY_SALARY * 0.65
    else:
        base = DAILY_SALARY * 0.5

    # If opponents were aggressive yesterday, slightly undercut to win without overpaying.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Undercut by a margin; ensure we still bid meaningfully.
        target = min(base, highest_prev_bid - 1.0)
        if target < DAILY_SALARY * 0.35:
            target = DAILY_SALARY * 0.45
    elif highest_prev_bid >= DAILY_SALARY * 0.6:
        # Moderate response
        target = max(base * 0.9, highest_prev_bid * 0.85)
    else:
        # Opponents were not under extreme pressure; bid enough to secure.
        # Scale with supply: if supply is near minimum, increase slightly.
        if supply <= float(MIN_SUPPLY) + 0.5:
            target = max(base, DAILY_SALARY * 0.55)
        else:
            target = base

    # Convert target into a bid bounded by budget and plausible daily salary multiples.
    # Keep bid within [0, budget].
    bid = float(target)
    if bid > budget:
        bid = budget
    if bid < 0:
        bid = 0.0

    # Additional cap to avoid wasting budget when supply is abundant.
    if supply_units >= 2.0:
        cap = DAILY_SALARY * 0.6
        if bid > cap:
            bid = cap

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

    supply = day_context['supply']
    day = day_context['day']

    # Identify alive opponents and use only yesterday's immediate trace.
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # If no one is alive, conserve budget.
    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Extract yesterday bids.
    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Pressure estimate from yesterday.
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Supply factor: with medium supply (15-25), we can afford moderate bids.
    # Normalize supply to [0,1].
    denom = (MAX_SUPPLY - MIN_SUPPLY) if (MAX_SUPPLY - MIN_SUPPLY) != 0 else 1.0
    supply_norm = (float(supply) - MIN_SUPPLY) / denom
    if supply_norm < 0.0:
        supply_norm = 0.0
    if supply_norm > 1.0:
        supply_norm = 1.0

    # Base bid tuned to compete without matching Eric's very high bids.
    # If opponents previously bid extremely high, slightly increase; otherwise stay moderate.
    if highest_prev_bid >= DAILY_SALARY * 0.75:
        base = DAILY_SALARY * (0.45 + 0.15 * supply_norm)
    else:
        base = DAILY_SALARY * (0.35 + 0.10 * supply_norm)

    # React to our hp: if low, bid more to avoid elimination.
    hp = float(my_status.get('hp', 0))
    if hp <= 1.5:
        base *= 1.25
    elif hp <= 3.0:
        base *= 1.10
    elif hp >= 7.0:
        base *= 0.95

    # If any opponent yesterday ended with 0 budget, assume they were price-sensitive; don't overbid.
    # Use only yesterday trace budget_after if available.
    zero_budget_seen = False
    for o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        bud_after = prev.get('budget_after', None)
        try:
            if bud_after is not None and float(bud_after) <= 0.0:
                zero_budget_seen = True
                break
        except Exception:
            pass

    if zero_budget_seen:
        base *= 0.92

    # Ensure we do not exceed our budget.
    budget = float(my_status.get('budget', 0))
    if budget <= 0.0:
        return 0.0

    bid = min(budget, base)

    # Final safety: avoid bidding too low when hp is critical.
    no_water_days = int(my_status.get('no_water_days', 0))
    if hp <= 3.0 and no_water_days >= 2:
        bid = min(budget, max(bid, DAILY_SALARY * 0.6))

    # Clamp to non-negative.
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

    # Alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # If everyone is dead, conserve.
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace only.
    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Estimate competitive pressure.
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    # Supply factor: higher supply reduces need to overbid.
    # Convert to an index-safe bucket.
    # Buckets: low [15..18.9], mid [19..21.9], high [22..25]
    if supply < 19.0:
        bucket = 0
    elif supply < 22.0:
        bucket = 1
    else:
        bucket = 2

    # Base aggressiveness: Cindy/Eric were high but stable; target a bid slightly above
    # the likely clearing price without matching their maximum.
    # If our HP is low, we must secure water.
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    # Determine target bid ceiling from budget.
    # Keep some reserve for later days.
    reserve_frac = 0.25 if hp > 3 else 0.05
    budget_cap = max(0.0, budget * (1.0 - reserve_frac))

    # Compute a competitive target using yesterday's highest/average.
    # If yesterday pressure was very high, we must bid closer to it.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # High pressure: bid near highest but still under budget cap.
        if hp > 3:
            target = highest_prev_bid * 0.92
        else:
            target = highest_prev_bid * 0.98
    else:
        # Moderate pressure: bid around average/need.
        # Use supply to decide whether to push or hold.
        # When supply is high, we can bid lower.
        multipliers = [1.05, 0.95, 0.85]
        m = multipliers[int(bucket)]
        # Anchor to avg_prev_bid if available; otherwise to a fraction of salary.
        anchor = avg_prev_bid if avg_prev_bid > 0 else DAILY_SALARY * 0.55
        target = anchor * m

    # Ensure we bid at least enough to matter when supply is tight.
    # If supply is near MIN_SUPPLY, bid more aggressively to avoid missing water.
    tightness = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)  # 0..1-ish
    min_bid = DAILY_SALARY * (0.45 + 0.35 * float(tightness))

    # If our HP is critical, increase min_bid.
    if hp <= 2.0:
        min_bid = DAILY_SALARY * 0.9
    elif hp <= 3.0:
        min_bid = max(min_bid, DAILY_SALARY * 0.7)

    bid = max(min_bid, target)

    # Final clamp to budget.
    if bid > budget_cap:
        bid = budget_cap

    # If budget is too low, still bid what we can.
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

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 1)

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive = []
    yesterday_bids = []
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)
            prev = o.get('previous_trace', {}) or {}
            b = prev.get('bid', None)
            if b is not None:
                try:
                    yesterday_bids.append(float(b))
                except Exception:
                    pass

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    max_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Pressure signals from opponents' yesterday state
    critical_count = 0
    for o in alive_opps:
        try:
            if float(o.get('hp', 0.0)) <= 2.0 or int(o.get('no_water_days', 0)) >= 2:
                critical_count += 1
        except Exception:
            pass

    # Supply-based urgency: higher supply reduces need to overbid
    # Convert to a rough affordability factor.
    supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    supply_factor = max(0.0, min(1.0, float(supply_factor)))

    # Base bid: aim to secure enough water without matching the highest aggressors.
    # If yesterday's max bid was very high, others likely bid aggressively; adjust.
    if max_prev_bid >= DAILY_SALARY * 1.6:
        base = DAILY_SALARY * (0.35 + 0.25 * (1.0 - supply_factor))
    elif max_prev_bid >= DAILY_SALARY * 1.1:
        base = DAILY_SALARY * (0.45 + 0.20 * (1.0 - supply_factor))
    else:
        base = DAILY_SALARY * (0.55 + 0.15 * (1.0 - supply_factor))

    # Increase bid if we are in danger
    if hp <= 2.0 or no_water_days >= 2:
        base = max(base, DAILY_SALARY * 0.9)
    elif hp <= 4.0:
        base = max(base, DAILY_SALARY * 0.65)

    # If multiple opponents are critical, expect bidding wars; still undercut slightly.
    if critical_count >= 2:
        base = max(base, DAILY_SALARY * 0.75)

    # Undercut strategy: if we have enough budget, bid just below yesterday max by a small margin.
    # Ensure index safety not needed here.
    target = base
    if max_prev_bid > 0:
        # Bid slightly under the max aggressor to avoid overpay while staying competitive.
        target = min(target, max_prev_bid - 2.0)
        # But never too low if we must survive.
        if hp <= 3.0:
            target = max(target, DAILY_SALARY * 0.7)

    # Final cap by budget and a sanity cap tied to supply.
    # If supply is low, slightly raise willingness; if high, lower.
    willingness_cap = DAILY_SALARY * (0.85 + 0.25 * (1.0 - supply_factor))
    bid = min(float(budget), float(willingness_cap), float(target))

    # If budget is extremely low, bid what we can.
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    my_hp = float(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from immediate trace
    prev_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    prev_bids.append(float(b))
                except Exception:
                    pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_prev_bid = 0.0
    if len(prev_bids) >= 2:
        sorted_b = sorted(prev_bids, reverse=True)
        second_prev_bid = sorted_b[1]

    # Pressure estimate: if someone already bid high yesterday, they likely contest water again.
    # Use a small overbid margin to win without going to extremes.
    margin = 3.0

    # Supply pressure: with higher supply, we can afford a slightly lower bid.
    # With lower supply, we need to outbid.
    if supply <= MIN_SUPPLY + 0.5:
        supply_tier = 0  # tight
    elif supply >= MAX_SUPPLY - 0.5:
        supply_tier = 2  # ample
    else:
        supply_tier = 1

    # Base target: try to beat yesterday's highest if it was competitive.
    # Competitive threshold relates to salary scale.
    competitive_threshold = DAILY_SALARY * 0.85  # 76.5

    # If my hp is critical, prioritize survival even if it costs more.
    critical_hp = my_hp <= 2.5
    low_budget = my_budget <= DAILY_SALARY * 0.6

    # Estimate required water days risk: if already no-water several days, bid harder.
    hunger_factor = 0.0
    if my_no_water_days >= 2:
        hunger_factor = 1.0
    elif my_no_water_days == 1:
        hunger_factor = 0.5

    if highest_prev_bid >= competitive_threshold:
        # Contest: bid just above the highest, with tier-based adjustment.
        tier_adjust = 1.0 if supply_tier == 0 else (0.7 if supply_tier == 1 else 0.5)
        target = highest_prev_bid + margin * tier_adjust
    else:
        # Not strongly contested yesterday: bid around a mid level.
        mid = DAILY_SALARY * (0.55 if supply_tier == 1 else (0.65 if supply_tier == 0 else 0.5))
        # If second highest exists, slightly above it to secure.
        target = max(mid, second_prev_bid + 2.0)

    if critical_hp:
        target *= 1.15
    if low_budget:
        target *= 0.9
    if hunger_factor > 0:
        target *= (1.0 + 0.12 * hunger_factor)

    # Never exceed budget; also keep non-negative.
    bid = max(0.0, min(my_budget, target))

    # If supply is extremely low, ensure we bid at least a meaningful fraction.
    if supply <= MIN_SUPPLY + 0.5 and bid < DAILY_SALARY * 0.6:
        bid = min(my_budget, DAILY_SALARY * 0.75)

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
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Immediate reaction from yesterday trace
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
    second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev_bid

    # Supply pressure: fewer units means higher chance others overbid.
    # Estimate how many water units we can buy if we win with a typical bid.
    # (We don't know conversion; we use relative supply to decide aggressiveness.)
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    low_supply = supply_ratio < 0.35

    # Decide baseline aggressiveness
    # If my hp is critical or I've gone several days without water, I must secure water.
    if hp <= 2.0 or no_water_days >= 2:
        # Escalate but cap to avoid matching the aggressive winners.
        target = DAILY_SALARY * (0.75 if low_supply else 0.65)
    else:
        # Stay moderate; only slightly react to their spikes.
        # If they were bidding extremely high yesterday, avoid bidding that high.
        if highest_prev_bid >= DAILY_SALARY * 1.9:
            target = DAILY_SALARY * (0.45 if not low_supply else 0.55)
        else:
            target = DAILY_SALARY * (0.5 if not low_supply else 0.6)

    # Add a small nudge based on their yesterday behavior, but don't chase it.
    # If their highest bid was not too extreme, we can outbid slightly.
    if highest_prev_bid > 0 and highest_prev_bid < DAILY_SALARY * 1.8:
        target = max(target, min(budget, second_prev_bid + 2.0))

    # Final clamp
    if budget <= 0:
        return 0.0
    bid = max(0.0, min(budget, target))
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
    day = int(day_context.get('day', 0))

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from immediate previous_trace only
    yesterday_bids = []
    yesterday_by_agent = {}
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                b_val = float(b)
            except Exception:
                continue
            yesterday_bids.append(b_val)
            yesterday_by_agent[oid] = b_val

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = 0.0
    if len(yesterday_bids) >= 2:
        sorted_b = sorted(yesterday_bids, reverse=True)
        second_prev_bid = float(sorted_b[1])

    # Determine how many allocations we likely need today
    # If supply is scarce, we must bid to secure at least one unit of water.
    # If supply is abundant, we can bid lower.
    supply_units = supply / float(WATER_REQ) if WATER_REQ > 0 else 0.0
    scarcity_level = 0
    if supply_units < 1.5:
        scarcity_level = 2
    elif supply_units < 2.5:
        scarcity_level = 1
    else:
        scarcity_level = 0

    # Base aggressiveness from my HP and no-water streak
    if hp <= 2 or no_water_days >= 2:
        urgency = 1.0
    elif hp <= 4:
        urgency = 0.75
    else:
        urgency = 0.55

    # Target Cindy-like competitive band: bids around 80-130 yesterday.
    # If someone already bid very high yesterday, try to slightly overtake.
    # Use highest_prev_bid and second_prev_bid to approximate the competition threshold.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Very competitive: bid just above second-highest to avoid overpaying.
        target = second_prev_bid + 2.0
    elif highest_prev_bid >= DAILY_SALARY * 0.65:
        # Moderate competitive: bid near highest_prev_bid + small increment.
        target = highest_prev_bid + 1.5
    else:
        # Low competitive: bid around mid band.
        target = max(DAILY_SALARY * 0.45, highest_prev_bid + 5.0)

    # Adjust for scarcity
    if scarcity_level == 2:
        target *= 1.15
    elif scarcity_level == 1:
        target *= 1.05

    # Apply urgency and cap by budget and a reasonable fraction of salary to avoid bankruptcy
    target *= urgency

    # Ensure non-negative and within budget
    max_reasonable = DAILY_SALARY * 1.1
    bid = max(0.0, min(budget, min(max_reasonable, target)))

    # If my HP is extremely low, go for survival: spend more aggressively.
    if hp <= 1:
        bid = max(0.0, min(budget, DAILY_SALARY * 0.95))

    # If budget is too small, bid what we can.
    if budget < 1.0:
        bid = max(0.0, budget)

    return float(bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    # Determine how many full WATER_REQ units the supply can cover.
    # Use int() to satisfy index safety and avoid float artifacts.
    supply_units = int(supply / float(WATER_REQ)) if WATER_REQ > 0 else 0

    # If supply is low, competition is tighter; bid more.
    # If supply is high, bid less since winning is easier.
    if supply_units <= 1:
        pressure = 0.85
    elif supply_units == 2:
        pressure = 0.70
    else:
        pressure = 0.55

    alive_opponents = []
    for oid, o in opponents_status.items():
        try:
            if o.get('alive', False):
                alive_opponents.append((oid, o))
        except Exception:
            continue

    # React to yesterday's bidding pressure.
    prev_bids = []
    for oid, o in alive_opponents:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Base bid target: upper-mid of yesterday leaders.
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        median_prev_bid = sorted(prev_bids)[len(prev_bids)//2]

        # Cindy died with avg ~66.9, so avoid going that low against active spenders.
        # If leaders bid near/above ~DAILY_SALARY, match slightly below to win efficiently.
        leader_cut = 0.92
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            target = max(median_prev_bid, highest_prev_bid * leader_cut)
        else:
            target = max(median_prev_bid, highest_prev_bid - 3.0)
    else:
        target = DAILY_SALARY * 0.55

    # Adjust by current HP: high HP can afford slightly lower bids.
    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))

    if hp <= 2:
        hp_factor = 0.95
    elif hp <= 4:
        hp_factor = 0.85
    elif hp <= 6:
        hp_factor = 0.75
    else:
        hp_factor = 0.70

    # Pressure adjustment based on supply.
    target = target * (0.65 + 0.35 * pressure) * hp_factor

    # Ensure we don't bid more than budget and keep within a reasonable cap.
    # Cap near daily salary to avoid runaway spending.
    cap = min(budget, DAILY_SALARY * 0.95)

    bid = float(target)
    if bid > cap:
        bid = cap

    # Also keep a floor so we don't get outbid by Alex/David/Eric.
    floor = min(budget, DAILY_SALARY * 0.50)
    if bid < floor:
        bid = floor

    # If budget is extremely low, just spend what we can.
    if budget <= 0:
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for k, o in opponents_status.items():
        if o is None:
            continue
        if o.get('alive', False):
            alive_opps.append(o)

    # Base target: aim to keep hp stable while conserving budget.
    # If we've had water shortage days recently, increase pressure.
    shortage_factor = 1.0
    if no_water_days >= 2:
        shortage_factor = 1.25
    elif no_water_days == 1:
        shortage_factor = 1.12

    # Use yesterday trace bids to infer aggressiveness.
    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    yesterday_bids.append(float(b))
                except Exception:
                    pass

    # Estimate how many water units we can buy if we win with our bid.
    # In this game, we don't know mapping bid->allocation, so we use conservative bid sizing.
    # Supply pressure: higher supply reduces need to overbid.
    supply_pressure = 1.0
    if supply <= float(WATER_REQ):
        supply_pressure = 1.35
    elif supply <= 18.0:
        supply_pressure = 1.18
    elif supply >= 23.0:
        supply_pressure = 0.92

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / float(len(yesterday_bids))

        # If opponents were bidding near/above salary, they likely overbid; counter with moderate bid.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # If my hp is low, I must secure water.
            if hp <= 2:
                target = DAILY_SALARY * 0.95
            else:
                target = DAILY_SALARY * 0.30 + (avg_prev_bid * 0.15)
        else:
            # Otherwise, slightly above average to beat timid bids.
            target = max(DAILY_SALARY * 0.50, avg_prev_bid + 2.0)
    else:
        target = DAILY_SALARY * 0.55

    target = target * shortage_factor * supply_pressure

    # Hard risk controls: avoid bidding too high when budget is low.
    # Also avoid bids that would likely bankrupt us before the end.
    # Remaining days: episode_days is 10 in meta-round state, but day_context may not include it.
    # We'll use a conservative fraction of budget.
    remaining_days = 10 - int(day) if day is not None else 10
    if remaining_days < 1:
        remaining_days = 1

    # Keep enough budget for future bids: allocate at most ~25% of current budget per day.
    max_per_day = budget * 0.25
    # But ensure we can still bid something meaningful if budget allows.
    bid_cap = min(budget, max_per_day + DAILY_SALARY * 0.25)

    # If hp is critical, allow larger spend but still bounded.
    if hp <= 1:
        bid_cap = min(budget, max(bid_cap, DAILY_SALARY * 0.8))

    bid = float(target)
    if bid > bid_cap:
        bid = bid_cap

    # Ensure non-negative bid.
    if bid < 0.0:
        bid = 0.0

    # Final conservative floor: if we have budget, bid enough to compete.
    if bid == 0.0 and budget > 0.0:
        bid = min(budget, DAILY_SALARY * 0.2)

    return bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for opp_id, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((opp_id, o))

    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace for immediate reaction
    prev_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', None)
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    prev_bids.append(float(b))
                except Exception:
                    pass

    peak_prev_bid = max(prev_bids) if prev_bids else 0.0
    # If opponents were bidding very high yesterday, we slightly undercut to win without exhausting budget.
    high_pressure = peak_prev_bid >= DAILY_SALARY * 0.85

    # If we've already had no water days, increase urgency.
    urgency = 0.0
    if my_no_water_days >= 2:
        urgency = 1.0
    elif my_no_water_days == 1:
        urgency = 0.5

    # Convert supply to an approximate scarcity signal: higher supply reduces needed bid.
    # supply is between 15 and 25 in this meta-round.
    scarcity = (25.0 - supply) / (25.0 - 15.0)  # 0..1

    # Base target bid
    if high_pressure:
        # Bid near but below peak to steal allocations.
        target = peak_prev_bid * (0.92 - 0.08 * (1.0 - scarcity))
        # Add urgency if we're at risk
        target += urgency * (DAILY_SALARY * 0.15)
    else:
        # Moderate bid to beat low bidders
        target = max(DAILY_SALARY * (0.45 + 0.25 * scarcity), peak_prev_bid * 0.75 + 5.0)
        target += urgency * (DAILY_SALARY * 0.1)

    # HP-aware adjustment: if low HP, bid higher.
    if my_hp <= 2.0:
        target *= 1.25
    elif my_hp <= 4.0:
        target *= 1.10

    # Budget cap: never bid more than what we can afford.
    # Also keep some reserve for later days.
    reserve_fraction = 0.15 if my_hp > 4 else 0.05
    max_affordable = max(0.0, my_budget * (1.0 - reserve_fraction))

    bid = min(max_affordable, target)
    # Ensure non-negative
    if bid < 0.0:
        bid = 0.0

    return bid
"""
