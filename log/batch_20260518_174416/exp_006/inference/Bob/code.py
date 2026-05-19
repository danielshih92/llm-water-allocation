# ============================================================
# Experiment: exp_006
# Agent: Bob
# Source: exp_006
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

    my_budget = float(my_status.get('budget', 0.0))
    my_hp = float(my_status.get('hp', 0.0))

    alive_opponents = []
    for opp_id, o in opponents_status.items():
        if o is not None and o.get('alive', False):
            alive_opponents.append((opp_id, o))

    # Default conservative strategy: bid enough to cover our requirement, but not max.
    # Scale with supply: when supply is tight, bid more.
    supply_ratio = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Tight supply => higher bid; abundant => lower bid.
    base_fraction = 0.62 - 0.20 * supply_ratio  # ~0.42..0.62
    base_fraction = max(0.35, min(0.65, base_fraction))

    # React to yesterday's opponent bids if present.
    high_prev_threshold = DAILY_SALARY * 0.85
    prev_bids = []
    for opp_id, o in alive_opponents:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    if prev_bids:
        highest_prev_bid = max(prev_bids)
        # If someone was willing to pay aggressively, contest but undercut.
        if highest_prev_bid >= high_prev_threshold:
            # If our hp is low, we must secure water.
            if my_hp <= 2.0:
                target = min(my_budget, DAILY_SALARY * 0.92)
            else:
                target = min(my_budget, highest_prev_bid - 1.0)
                # Ensure still meaningful contest.
                target = max(target, DAILY_SALARY * 0.55)
        else:
            # Otherwise, bid around base but slightly above their max to win cheaply.
            target = max(DAILY_SALARY * base_fraction, highest_prev_bid + 1.5)
            target = min(my_budget, target)
    else:
        # No usable trace: bid around base.
        target = min(my_budget, DAILY_SALARY * base_fraction)

    # Safety bounds: never bid negative; also avoid bidding more than daily salary.
    target = max(0.0, min(target, DAILY_SALARY))

    # If our hp is critical, increase bid.
    if my_hp <= 1.5:
        target = min(my_budget, DAILY_SALARY * 0.98)
    elif my_hp <= 3.0:
        target = min(my_budget, max(target, DAILY_SALARY * 0.70))

    # If budget is extremely low, bid whatever we can.
    if my_budget <= 1.0:
        return float(my_budget)

    return float(target)
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

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids to infer how aggressive the surviving opponents were.
    prev_bids = []
    for oid, o in alive:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Pressure tiers from yesterday.
    high_pressure = highest_prev_bid >= DAILY_SALARY * 0.85  # ~76.5
    medium_pressure = (highest_prev_bid >= DAILY_SALARY * 0.55) and not high_pressure

    # Supply-based aggressiveness: with higher supply, we can bid less and still win water.
    # supply is between 15 and 25.
    supply_ratio = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Core bid target
    if high_pressure:
        # If they were willing to pay near salary, we must contest.
        base = DAILY_SALARY * (0.35 + 0.25 * (1.0 - supply_ratio))  # higher when supply is low
        if hp <= 2 or no_water_days >= 2:
            base = DAILY_SALARY * (0.75 + 0.1 * (1.0 - supply_ratio))
        else:
            # Slightly overtake their last highest bid if we're safe.
            base = max(base, min(budget, highest_prev_bid + 2.0))
    elif medium_pressure:
        base = DAILY_SALARY * (0.45 + 0.2 * (1.0 - supply_ratio))
        if hp <= 2 or no_water_days >= 2:
            base = DAILY_SALARY * (0.7 + 0.1 * (1.0 - supply_ratio))
        else:
            base = max(base, highest_prev_bid * 0.95)
    else:
        # Low pressure: bid enough to avoid being starved.
        base = DAILY_SALARY * (0.55 - 0.15 * supply_ratio)
        if hp <= 2 or no_water_days >= 2:
            base = DAILY_SALARY * 0.85

    # Convert to feasible bid within budget.
    # Ensure non-negative and do not exceed budget.
    bid = max(0.0, min(budget, float(base)))

    # If supply is minimal and my hp is critical, bid harder.
    if supply <= float(MIN_SUPPLY) + 0.5 and (hp <= 3 or no_water_days >= 2):
        bid = max(bid, min(budget, DAILY_SALARY * 0.9))

    return bid
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

    # Alive opponents + yesterday bids
    alive_opps = []
    yesterday_bids = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)
            prev = o.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(float(prev['bid']))

    # If no opponents alive, bid conservatively but still secure water
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Estimate opponent aggressiveness from yesterday
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else 0.0

    # Supply pressure: higher supply means cheaper water to secure; lower supply means we must bid more
    # Normalize supply to [0,1]
    denom = (MAX_SUPPLY - MIN_SUPPLY)
    if denom <= 0:
        supply_norm = 0.5
    else:
        supply_norm = (supply - MIN_SUPPLY) / denom
    supply_norm = max(0.0, min(1.0, supply_norm))

    # Base bid target: mid-high when supply is low; lower when supply is high
    # Also react if someone was extremely aggressive yesterday (Cindy-like)
    aggressive_threshold = DAILY_SALARY * 0.95
    if highest_prev_bid >= aggressive_threshold:
        # Try to slightly undercut the peak aggressor: bid near (peak - small margin)
        # but cap by what we can afford.
        target = highest_prev_bid - 8.0
        # If my HP is low, can't afford to lose water
        if my_status['hp'] <= 2:
            target += 10.0
    else:
        # Use supply to decide: lower supply -> higher bid
        # target ranges roughly [0.45*salary, 0.75*salary]
        target = DAILY_SALARY * (0.75 - 0.30 * supply_norm)
        # If someone bid high but not extreme, nudge upward
        if second_prev_bid > 0:
            target = max(target, second_prev_bid * 0.85)

    # If my HP is critical, bid much more (near max affordable)
    if my_status['hp'] <= 1:
        target = max(target, DAILY_SALARY * 0.95)
    elif my_status['hp'] <= 3:
        target = max(target, DAILY_SALARY * 0.75)

    # Budget safety: never exceed budget
    budget = float(my_status['budget'])
    if budget <= 0:
        return 0.0

    # Also avoid overbidding when we have long survival buffer
    if my_status.get('no_water_days', 0) is not None:
        no_water_days = int(my_status['no_water_days'])
    else:
        no_water_days = 0

    # If we can skip multiple days, reduce bid to save budget
    if no_water_days >= 5 and my_status['hp'] >= 4:
        target *= 0.75

    # Final clamp: at least small bid to have a chance, at most budget
    min_bid = 1.0
    bid = float(max(min_bid, min(budget, target)))
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
    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive.append(opp)

    # React to yesterday bids (immediate trace only)
    prev_bids = []
    for opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        if prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Base aggressiveness from supply level: higher supply => bid slightly more to outcompete
    # but cap to avoid overspending.
    supply_ratio = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # If my hp is low, spend to avoid death.
    if hp <= 2.0:
        target = DAILY_SALARY * 0.95
    elif hp <= 4.0 or no_water_days >= 2:
        target = DAILY_SALARY * 0.75
    else:
        target = DAILY_SALARY * (0.45 + 0.25 * supply_ratio)

    # If opponents were bidding very high yesterday, raise bid to match the arms race.
    if prev_bids:
        highest_prev = max(prev_bids)
        # Alex/Cindy were around 120-124; treat >=0.85*DAILY_SALARY as high pressure.
        if highest_prev >= DAILY_SALARY * 0.85:
            if hp > 3.0:
                target = max(target, DAILY_SALARY * 0.65)
            else:
                target = max(target, DAILY_SALARY * 0.9)
        else:
            # If they weren't extreme, bid a bit above yesterday typical to secure water.
            avg_prev = sum(prev_bids) / float(len(prev_bids))
            target = max(target, min(DAILY_SALARY * 0.8, avg_prev + 5.0))

    # Convert target to a final bid under budget.
    # Never bid more than budget or a reasonable fraction of budget.
    max_affordable = budget
    # Keep a reserve so we don't bankrupt early.
    reserve_factor = 0.15 if hp > 3.0 else 0.05
    bid_cap = max_affordable * (1.0 - reserve_factor)

    final_bid = min(bid_cap, target)

    # Ensure non-negative and at least a small amount if budget allows.
    if final_bid < 0.0:
        final_bid = 0.0
    if final_bid == 0.0 and budget > 0.0:
        final_bid = min(budget, DAILY_SALARY * 0.1)

    return float(final_bid)
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

    supply = day_context['supply']
    day = day_context['day']

    # Determine alive opponents and their yesterday bids
    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    # If no alive opponents, take a conservative amount
    if not alive_opponents:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Supply pressure: if supply is low, fewer winners; raise bid slightly.
    # Ensure indices are safe (not using lists, but keep logic float-safe).
    supply_ratio = (float(supply) - float(MIN_SUPPLY)) / (float(MAX_SUPPLY) - float(MIN_SUPPLY) + 1e-9)
    supply_ratio = max(0.0, min(1.0, supply_ratio))
    scarcity = 1.0 - supply_ratio  # 1 when supply low

    # Budget guard: never bid more than what we can afford.
    budget_cap = float(my_status['budget'])

    # If someone was extremely aggressive yesterday, don't fully match (avoid rapid depletion like Alex/Eric).
    # Instead, bid enough to compete when my hp is low.
    hp = float(my_status['hp'])
    no_water_days = int(my_status.get('no_water_days', 0))

    # Base bid target anchored to whether we are in danger.
    if hp <= 2 or no_water_days >= 2:
        risk_factor = 1.0
    elif hp <= 4:
        risk_factor = 0.75
    else:
        risk_factor = 0.55

    # Compete level based on yesterday's highest bid
    # If highest_prev_bid is high, we increase bid but with a ceiling to preserve budget.
    if highest_prev_bid >= DAILY_SALARY * 1.0:
        compete = 0.85
    elif highest_prev_bid >= DAILY_SALARY * 0.7:
        compete = 0.7
    elif highest_prev_bid > 0:
        compete = 0.6
    else:
        compete = 0.5

    # Convert scarcity to bid multiplier
    scarcity_mult = 1.0 + 0.35 * scarcity

    # Target bid: proportional to salary, adjusted by competition and scarcity, then capped.
    target = DAILY_SALARY * risk_factor * compete * scarcity_mult

    # If budget is tight, scale down smoothly.
    if budget_cap < DAILY_SALARY * 0.2:
        target = min(target, budget_cap)
    else:
        # Keep some reserve: don't spend more than ~60% of budget this day unless critical.
        if hp <= 2 or no_water_days >= 2:
            reserve_frac = 0.15
        else:
            reserve_frac = 0.4
        max_spend = budget_cap * (1.0 - reserve_frac)
        target = min(target, max_spend)

    # Final bid must be non-negative.
    bid = max(0.0, float(target))
    # Some games require integer bids; if so, rounding down is safer.
    # We'll round to 2 decimals to reduce precision issues.
    bid = round(bid, 2)

    # Ensure within budget
    if bid > budget_cap:
        bid = round(budget_cap, 2)

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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opponents = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opponents:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Yesterday bids (immediate reaction)
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev['bid']))

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate how many full water units we can buy if supply is split by bids (approx).
    # We don't know allocation rule, so we target a bid that is competitive but not maximal.
    # If supply is tight, we increase bid.
    supply_tightness = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    supply_tightness = max(0.0, min(1.0, supply_tightness))

    # Pressure from opponents: Cindy showed max 135 yesterday; we mirror partly.
    # If someone bid very high yesterday, increase our bid to avoid being outbid.
    if highest_prev_bid >= DAILY_SALARY * 1.3:  # ~117
        base = DAILY_SALARY * (0.95 + 0.15 * supply_tightness)
    elif highest_prev_bid >= DAILY_SALARY * 0.95:  # ~85.5
        base = DAILY_SALARY * (0.75 + 0.25 * supply_tightness)
    else:
        base = DAILY_SALARY * (0.55 + 0.20 * supply_tightness)

    # If we are already in danger, spend more.
    if hp <= 2.0 or no_water_days >= 1:
        base *= 1.25
    elif hp >= 6.0 and no_water_days == 0:
        base *= 0.9

    # Convert base into an actionable bid cap.
    # Keep within budget and avoid extreme overspend.
    bid = min(budget, base)

    # If supply is low, slightly increase; if high, slightly decrease.
    if supply <= float(WATER_REQ):
        bid = min(budget, bid * 1.15)
    elif supply >= 22.0:
        bid = bid * 0.9

    # Final clamp
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
    day = day_context['day']

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return max(0.0, min(float(my_status['budget']), DAILY_SALARY * 0.4))

    # Read yesterday bids from immediate previous_trace only
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        if isinstance(prev, dict) and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate how many full water units we likely need to avoid collapse.
    # If supply is high enough, a modest allocation can cover our requirement.
    # We map supply to a target fraction of water coverage.
    # Supply in [15,25] => coverage ratio in [15/9=1.67, 25/9=2.78]
    coverage = supply / float(WATER_REQ)

    # Base bid: aim to secure enough share without matching Cindy's overbids.
    # Scale down when supply is abundant.
    if coverage >= 2.4:
        base = DAILY_SALARY * 0.35
    elif coverage >= 1.9:
        base = DAILY_SALARY * 0.45
    else:
        base = DAILY_SALARY * 0.6

    # If someone previously bid extremely high, they likely chase survival; we slightly increase,
    # but keep well below their extreme to avoid budget burn.
    if highest_prev_bid >= DAILY_SALARY * 1.5:
        # Cindy-like behavior: raise only modestly.
        base = max(base, DAILY_SALARY * 0.55)
    elif highest_prev_bid >= DAILY_SALARY * 0.85:
        base = max(base, DAILY_SALARY * 0.5)

    # Urgency from our hp and no_water_days
    hp = float(my_status['hp'])
    no_water_days = int(my_status['no_water_days'])
    budget = float(my_status['budget'])

    if hp <= 2 or no_water_days >= 2:
        # Must secure water; bid more aggressively but still bounded.
        base = max(base, DAILY_SALARY * 0.8)
    elif hp <= 4 or no_water_days == 1:
        base = max(base, DAILY_SALARY * 0.65)

    # Final cap: never exceed budget.
    bid = min(budget, base)

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
    day = int(day_context['day'])

    # Identify alive opponents and read yesterday trace bids
    alive_opps = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opps:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.4))

    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Estimate how many water units we can potentially buy from supply
    # (Indexing guards: none needed here)
    tight_supply = supply <= (MIN_SUPPLY + 1.0)  # ~15-16

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    # Baseline target: aim to secure enough water when supply is tight.
    # Since water requirement is fixed (9), the winning bid threshold likely tracks others' bids.
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        second_prev = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev

        # If someone was bidding near our salary level, expect higher contention today.
        aggressive = highest_prev >= (DAILY_SALARY * 0.85)  # ~76.5

        if tight_supply:
            # If supply is tight, we slightly undercut the highest aggressive bid unless we're low HP.
            if hp <= 2.0:
                target = min(budget, max(highest_prev - 2.0, DAILY_SALARY * 0.95))
            else:
                # Undercut strategy: try to beat Eric-like capped bids without matching Cindy's peak.
                # Use second-highest as a proxy if highest is an outlier.
                proxy = second_prev if highest_prev - second_prev >= 8.0 else highest_prev
                target = min(budget, max(proxy + 1.5, DAILY_SALARY * 0.7))
        else:
            # Non-tight supply: conserve budget; still react to aggressive contention.
            if aggressive:
                target = min(budget, max(second_prev + 1.0, DAILY_SALARY * 0.65))
            else:
                target = min(budget, max(DAILY_SALARY * 0.5, highest_prev * 0.55))
    else:
        # No trace bids available: follow conservative default.
        if tight_supply:
            target = min(budget, DAILY_SALARY * (0.85 if hp <= 2.0 else 0.7))
        else:
            target = min(budget, DAILY_SALARY * (0.55 if hp > 2.0 else 0.9))

    # Ensure non-negative and not exceeding budget
    if target < 0.0:
        target = 0.0
    if target > budget:
        target = budget

    return float(target)
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

    supply = day_context.get('supply', 0)
    day = day_context.get('day', 1)

    hp = my_status.get('hp', 0)
    budget = my_status.get('budget', 0)
    no_water_days = my_status.get('no_water_days', 0)

    # Identify alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Use yesterday's immediate trace to infer aggressiveness
    yesterday_bids = []
    opp_pressures = []  # (bid, oid)
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                b_val = float(b)
            except Exception:
                continue
            yesterday_bids.append(b_val)
            opp_pressures.append((b_val, oid))

    # Baseline: if I'm already in danger, bid harder
    # (no_water_days increases risk; hp low means I must secure water)
    danger = 0
    if hp <= 2:
        danger += 2
    if hp <= 4:
        danger += 1
    if no_water_days >= 2:
        danger += 1

    # Estimate how competitive the market was yesterday
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / float(len(yesterday_bids))
    else:
        highest_prev_bid = 0.0
        avg_prev_bid = 0.0

    # If opponents were bidding extremely high yesterday, avoid matching unless I'm in danger
    # Cindy/Eric showed ~150+ averages; treat that as aggressive.
    aggressive_market = (highest_prev_bid >= 0.85 * 190.58) or (avg_prev_bid >= 120.0)

    # Compute a target bid based on supply and my need.
    # With medium supply (15-25), I only need 1 unit water per day to maintain hp.
    # Use a conservative bid to win occasionally without burning budget.
    supply_val = float(supply)
    # More supply => less need to overbid
    supply_factor = (supply_val - float(MIN_SUPPLY)) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    if supply_factor < 0:
        supply_factor = 0.0
    if supply_factor > 1:
        supply_factor = 1.0

    # Base bid: around 0.45-0.65 of salary depending on supply
    base = DAILY_SALARY * (0.65 - 0.2 * supply_factor)

    # Adjustment for danger
    if danger >= 2:
        target = DAILY_SALARY * 0.85
    elif danger == 1:
        target = DAILY_SALARY * 0.65
    else:
        target = base

    # If market was aggressive, slightly reduce unless danger is high
    if aggressive_market and danger == 0:
        target = min(target, DAILY_SALARY * 0.55)
    if aggressive_market and danger == 1:
        target = min(target, DAILY_SALARY * 0.7)

    # If any opponent bid near max yesterday, that indicates they may try to secure water again.
    # Only counter if I'm in danger.
    near_max = False
    for b_val, oid in opp_pressures:
        if b_val >= 0.95 * highest_prev_bid and b_val >= 160.0:
            near_max = True
            break
    if near_max and danger == 0:
        target = min(target, DAILY_SALARY * 0.5)
    elif near_max and danger >= 1:
        target = max(target, DAILY_SALARY * 0.75)

    # Ensure we don't bid more than budget
    bid = min(float(budget), float(target))

    # Final safety: if budget is very low, bid whatever keeps me alive (small but nonzero)
    if budget <= 1.0:
        return 0.0
    if bid < 1.0 and danger >= 1:
        bid = min(float(budget), DAILY_SALARY * 0.25)

    # Avoid bidding above a reasonable cap
    max_reasonable = DAILY_SALARY * 1.15
    if bid > max_reasonable:
        bid = max_reasonable

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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Identify alive opponents
    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive.append((opp_id, opp))

    if not alive:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Extract yesterday bids from previous_trace for immediate reaction
    yesterday_bids = []
    for opp_id, opp in alive:
        prev = opp.get('previous_trace', None) or {}
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Pressure estimation: if someone bid extremely high yesterday, expect competition today
    # Cindy survived 10 days yesterday; if alive, she likely continues bidding high.
    cindy = opponents_status.get('Cindy', None)
    cindy_alive = bool(cindy and cindy.get('alive', False))

    # Base target bid depends on supply scarcity and our hp
    scarcity = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)  # 0..1-ish
    scarcity = max(0.0, min(1.0, scarcity))

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    # If we are in danger, bid more aggressively
    danger = 1.0 if hp <= 2 else (0.6 if hp <= 4 else 0.2)

    # If Cindy is alive, assume she can pay; raise bid to avoid being outbid.
    cindy_factor = 1.15 if cindy_alive else 1.0

    # If yesterday's highest bid was very high, competition is intense.
    competition = 1.0
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        competition = 1.25
    elif highest_prev_bid >= DAILY_SALARY * 0.55:
        competition = 1.12

    # Compute a conservative bid cap to avoid bankruptcy
    # We want enough to secure water but not spend all budget.
    # Use a target fraction of DAILY_SALARY scaled by scarcity and pressure.
    target = DAILY_SALARY * (0.45 + 0.35 * scarcity + 0.25 * danger)
    target *= cindy_factor
    target *= competition

    # Ensure we don't bid more than budget or an absolute reasonable ceiling
    # (ceiling helps avoid runaway spending when others died early).
    ceiling = DAILY_SALARY * 0.95
    bid = min(budget, min(target, ceiling))

    # If budget is very low, still try to bid enough to avoid immediate death.
    if budget <= DAILY_SALARY * 0.2:
        bid = min(budget, DAILY_SALARY * 0.25)

    # If supply is high, we can bid lower since each unit is less scarce.
    if supply >= 21.0:
        bid *= 0.85

    # Final safety clamp
    if bid < 0.0:
        bid = 0.0
    return float(bid)
"""
