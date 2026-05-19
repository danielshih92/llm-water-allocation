# ============================================================
# Experiment: exp_097
# Agent: Bob
# Source: exp_097
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

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append((oid, o))

    # If no opponents, conserve budget.
    if not alive_opponents:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Read only yesterday's trace bid.
    yesterday_bids = []
    yesterday_hp_after = []
    for oid, o in alive_opponents:
        prev = o.get('previous_trace', {}) or {}
        if prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass
        if prev.get('hp_after') is not None:
            try:
                yesterday_hp_after.append(float(prev['hp_after']))
            except Exception:
                pass

    # Aggression signals.
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = (sum(yesterday_bids) / float(len(yesterday_bids))) if yesterday_bids else 0.0

    # Estimate how many water units are available; bids compete for allocation.
    # Use a conservative target: try to cover our own requirement with minimal overcommit.
    # Convert to a
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
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Extract yesterday bids for immediate reaction.
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate how competitive the market is yesterday.
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        avg_prev_bid = sum(prev_bids) / float(len(prev_bids))
    else:
        highest_prev_bid = 0.0
        avg_prev_bid = DAILY_SALARY * 0.6

    # Tight supply -> more likely many players bid around salary; aim to slightly over average.
    supply_ratio = (supply - float(MIN_SUPPLY)) / (float(MAX_SUPPLY - MIN_SUPPLY))
    supply_ratio = max(0.0, min(1.0, supply_ratio))
    tightness = 1.0 - supply_ratio  # 1 when MIN, 0 when MAX

    # If my hp is low, I must secure water.
    critical = (hp <= 2.0) or (no_water_days >= 2)

    # Base target bid.
    if critical:
        # Push hard but still bounded by budget.
        target = max(avg_prev_bid, DAILY_SALARY * 0.85) + 2.0 * tightness
    else:
        # Conservative: bid around average, modestly above when tight.
        target = avg_prev_bid + (3.0 + 3.0 * tightness)

    # If someone already bid extremely high yesterday, avoid getting outbid: cap to just above highest.
    if highest_prev_bid > 0:
        # Only react strongly if yesterday's max suggests a near-auction war.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            target = max(target, highest_prev_bid + 1.5)

    # Final clamp to budget and reasonable upper bound.
    # Keep some budget for later days.
    max_affordable = budget
    # If supply is extremely low, allow near-salary spending.
    if tightness > 0.7:
        budget_cap = min(max_affordable, DAILY_SALARY * 1.1)
    else:
        budget_cap = min(max_affordable, DAILY_SALARY * 0.75)

    bid = min(target, budget_cap)

    # Never bid negative.
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
    day = int(day_context['day'])

    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opps:
        return float(min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace only (immediate reaction)
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate scarcity pressure from supply
    # If supply near minimum, water is scarce -> bid higher; if near maximum, bid lower.
    scarcity = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    # Determine pressure from opponents' yesterday behavior
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    # If someone already spent aggressively yesterday, we try to beat the mid-tier rather than chase the top.
    # Use a target just above the median-ish of yesterday bids.
    sorted_prev = sorted(prev_bids)
    median_prev = sorted_prev[len(sorted_prev)//2] if sorted_prev else 0.0

    # Health/budget risk adjustment
    # If we've gone without water for multiple days or hp is low, increase bid.
    urgency = 0.0
    if hp <= 2:
        urgency = 1.0
    elif hp <= 4:
        urgency = 0.6
    else:
        urgency = 0.3

    urgency += 0.15 * min(3, no_water_days)
    urgency = max(0.0, min(1.5, urgency))

    # Core target bid
    # - Base on scarcity and urgency
    # - Try to slightly exceed median_prev when scarcity is high
    # - When scarcity is low, stay around a fraction of salary to conserve budget
    if scarcity >= 0.6:
        target = max(DAILY_SALARY * 0.55, median_prev + 5.0)
    elif scarcity >= 0.35:
        target = max(DAILY_SALARY * 0.45, median_prev * 0.95 + 3.0)
    else:
        target = max(DAILY_SALARY * 0.35, median_prev * 0.75)

    # If highest_prev_bid is extremely high (likely Cindy), avoid overcommitting; cap relative to it.
    if highest_prev_bid > DAILY_SALARY * 1.2:
        target = min(target, highest_prev_bid * 0.75)

    # Apply urgency scaling
    target = target * (0.85 + 0.3 * urgency)

    # Budget safety: never bid more than we can afford comfortably; also avoid going all-in unless hp is critical.
    if hp <= 2:
        cap = min(budget, DAILY_SALARY * 1.0)
    else:
        cap = min(budget, DAILY_SALARY * 0.8)

    bid = float(min(cap, max(0.0, target)))

    # Ensure at least a small meaningful bid when budget allows
    min_floor = 10.0
    if bid < min_floor and budget >= min_floor:
        bid = min_floor

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

    # If we are in critical condition, secure water aggressively.
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    # Determine yesterday's bid pressure from opponents we can observe.
    yesterday_bids = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        if prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # Baseline bid depends on our urgency and supply.
    # With supply 15-25, one unit of our requirement (9) is typically competitive; we avoid overbidding.
    urgency = 0
    if hp <= 2.0:
        urgency += 2
    if no_water_days >= 2:
        urgency += 1

    # If Cindy-like consistent high bidder exists, we slightly increase to avoid being outbid.
    # Use the maximum previous bid as a proxy for current competitive pressure.
    pressure = 0.0
    if yesterday_bids:
        pressure = max(yesterday_bids)

    # Compute a target bid.
    # - If pressure is very high, we bid mid-high but cap by our budget.
    # - If pressure is moderate, bid slightly above a mid level.
    if pressure >= DAILY_SALARY * 1.15:  # ~103.5
        base = DAILY_SALARY * 0.75
        if urgency >= 2:
            base = DAILY_SALARY * 0.95
    elif pressure >= DAILY_SALARY * 0.75:  # ~67.5
        base = DAILY_SALARY * 0.62
        if urgency >= 2:
            base = DAILY_SALARY * 0.85
    else:
        base = DAILY_SALARY * 0.52
        if urgency >= 1:
            base = DAILY_SALARY * 0.72

    # Adjust for supply: when supply is higher, we can lower bids slightly.
    # Normalize supply within [MIN_SUPPLY, MAX_SUPPLY].
    if MAX_SUPPLY > MIN_SUPPLY:
        t = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        t = 0.5
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)

    # Higher supply => less need to outbid.
    base = base * (1.0 - 0.12 * t)

    # Ensure at least enough to be competitive but never exceed budget.
    # Also avoid bidding too low when urgency is high.
    min_bid = 0.0
    if urgency >= 2:
        min_bid = DAILY_SALARY * 0.55
    elif urgency == 1:
        min_bid = DAILY_SALARY * 0.40

    bid = max(min_bid, base)

    # Final cap by budget.
    if budget <= 0.0:
        return 0.0
    if bid > budget:
        bid = budget

    # If budget is very low, bid all-in.
    if budget < DAILY_SALARY * 0.25:
        bid = budget

    # Return a float bid.
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

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    hp = my_status.get('hp', 0)
    budget = my_status.get('budget', 0.0)
    no_water_days = my_status.get('no_water_days', 0)

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append((oid, o))

    if not alive_opponents:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read opponents' yesterday bids (only immediate reaction)
    prev_bids = []
    for oid, o in alive_opponents:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            prev_bids.append((oid, float(b)))

    # Identify Cindy-like pressure: highest previous bid among alive
    highest_prev_bid = 0.0
    highest_prev_oid = None
    for oid, b in prev_bids:
        if b > highest_prev_bid:
            highest_prev_bid = b
            highest_prev_oid = oid

    # Supply pressure: near max supply means we can afford to bid less; near min supply bid more.
    # Map supply to [0,1]
    if MAX_SUPPLY == MIN_SUPPLY:
        supply_frac = 1.0
    else:
        supply_frac = (float(supply) - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
        if supply_frac < 0.0:
            supply_frac = 0.0
        if supply_frac > 1.0:
            supply_frac = 1.0

    # Base bid target: moderate when supply is abundant, higher when scarce.
    scarcity_multiplier = 1.0 + (1.0 - supply_frac) * 0.8  # up to 1.8 when very scarce

    # If Cindy was bidding very high yesterday, try to undercut her by bidding slightly above a fraction of her pressure.
    # Cindy average was ~158; use rule: if highest_prev_bid is huge, bid just below it but still competitive.
    if highest_prev_bid >= DAILY_SALARY * 1.4:  # ~126
        # Bid enough to likely beat her without mirroring her all-in behavior.
        # If we're in danger (low hp or many no-water days), increase aggressiveness.
        danger = 0
        if hp <= 2:
            danger = 2
        elif hp <= 4:
            danger = 1
        if no_water_days >= 2:
            danger += 1

        # Competitive but capped.
        # Target = min(highest_prev_bid * (0.78 + 0.08*danger), DAILY_SALARY*1.2*scarcity_multiplier)
        target = highest_prev_bid * (0.78 + 0.08 * float(danger))
        cap = DAILY_SALARY * 1.2 * scarcity_multiplier
        bid = min(target, cap)
    else:
        # Typical regime: bid around salary * 0.55-0.85 depending on danger and scarcity
        danger = 0
        if hp <= 2:
            danger = 2
        elif hp <= 4:
            danger = 1
        if no_water_days >= 2:
            danger += 1

        base = DAILY_SALARY * (0.55 + 0.12 * float(danger))
        bid = base * scarcity_multiplier

    # Ensure we never bid negative and respect budget.
    if bid < 0.0:
        bid = 0.0

    # If our budget is low, bid what we can but keep a small reserve.
    reserve_factor = 0.15
    max_affordable = max(0.0, budget * (1.0 - reserve_factor))

    bid = min(bid, max_affordable)

    # If we're very low hp, allow spending more of budget.
    if hp <= 2:
        bid = min(bid + budget * 0.15, budget)

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
    day = int(day_context['day'])

    # Identify alive opponents
    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive.append((opp_id, opp))

    # If no opponents, bid to secure enough water for remaining days
    if not alive:
        # Conservative: aim for at least one requirement unit worth of water
        need_units = max(1, int((my_status['no_water_days'] + 1)))
        target = min(my_status['budget'], DAILY_SALARY * 0.4)
        return float(target)

    # Use yesterday's bids (only immediate reaction)
    yesterday_bids = []
    for _, opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate competition intensity from yesterday
    # If Cindy-like aggressive behavior occurred (very high previous bid), we need to contest.
    # If highest_prev_bid is low, we can undercut.
    contest = False
    if highest_prev_bid >= DAILY_SALARY * 1.4:  # ~126
        contest = True

    # Convert supply to max number of WATER_REQ chunks we can plausibly buy/need.
    # We don't know exact auction mechanics; use supply to adjust aggressiveness.
    # More supply -> can bid less and still survive; less supply -> bid more.
    supply_ratio = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Base bid fraction: tuned for medium scenario and to beat aggressive spender without dying.
    # If contesting, bid around 0.75-0.95 of salary; otherwise 0.45-0.65.
    if contest:
        # If my HP is already low, don't overspend; if HP is ok, spend to secure.
        if my_status['hp'] <= 2:
            frac = 0.75
        elif my_status['hp'] <= 4:
            frac = 0.85
        else:
            # With decent HP, push harder when supply is not abundant.
            frac = 0.92 - 0.15 * supply_ratio
    else:
        if my_status['hp'] <= 2:
            frac = 0.70
        else:
            frac = 0.55 - 0.10 * supply_ratio

    # Also react to no_water_days: if close to starvation, bid more.
    # Using WATER_REQ=9, each day without water is dangerous; increase bid when no_water_days is high.
    no_water = int(my_status.get('no_water_days', 0))
    if no_water >= 2:
        frac += 0.10
    if no_water >= 3:
        frac += 0.15

    # Clamp fraction
    frac = max(0.25, min(0.98, frac))

    # Ensure we don't bid more than budget
    bid = my_status['budget'] * frac

    # If yesterday's highest bid was extremely high, we may need a minimum to avoid being shut out.
    # Bid just above a fraction of that pressure.
    if highest_prev_bid > 0:
        min_to_contest = highest_prev_bid * 0.85
        # But never exceed budget.
        bid = max(bid, min_to_contest)

    # Final cap: don't exceed 1.1 * salary to avoid reckless spending.
    cap = DAILY_SALARY * 1.1
    bid = min(bid, cap, my_status['budget'])

    # If budget is very low, bid whatever remains.
    if my_status['budget'] <= 1e-6:
        return 0.0

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

    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False) and o.get('hp', 0) > -999:
            alive.append((oid, o))

    if not alive:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids for immediate reaction
    prev_bids = []
    for oid, o in alive:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Estimate how contested the market was
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Supply pressure: higher supply reduces urgency to overbid
    # Map supply in [15,25] to a risk factor in [1.0,0.6]
    if MAX_SUPPLY > MIN_SUPPLY:
        risk = 1.0 - 0.4 * ((supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY))
    else:
        risk = 1.0

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])

    # If our HP is critical, bid to secure water regardless of others
    if my_hp <= 2.0:
        target = DAILY_SALARY * (0.85 * risk)
        return float(min(my_budget, target))

    # If others were very aggressive yesterday, slightly raise to avoid being outbid
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # We can afford moderate pressure; don't match extreme bids
        target = max(DAILY_SALARY * 0.45, highest_prev_bid * 0.55) * risk
        return float(min(my_budget, target))

    # Otherwise, bid conservatively but enough to compete in medium scenario
    # Base depends on supply: lower supply -> higher bid
    base = DAILY_SALARY * (0.42 + 0.18 * (1.0 - ((supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)))) if MAX_SUPPLY > MIN_SUPPLY else DAILY_SALARY * 0.5
    # Also scale down as our HP is healthy
    hp_scale = 0.95 if my_hp >= 7.0 else (0.75 if my_hp >= 4.0 else 0.9)
    target = base * hp_scale * risk
    return float(min(my_budget, target))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Alive opponents and yesterday bids
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how many water units might be needed this day.
    # If supply is low relative to WATER_REQ, competition is higher.
    # Use a conservative target unit count.
    units_available = int(supply / float(WATER_REQ)) if WATER_REQ > 0 else 0
    if units_available <= 0:
        units_available = 1

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = float(my_status['no_water_days'])

    # Base willingness to pay: depend on hp and no-water risk.
    if hp <= 2.0 or no_water_days >= 1.0:
        base = DAILY_SALARY * 0.95
    elif hp <= 4.0:
        base = DAILY_SALARY * 0.75
    else:
        base = DAILY_SALARY * 0.55

    # Exploit yesterday: if others were already bidding very high, they likely continue.
    # Cindy/Eric/David averaged 100+ yesterday, while Alex collapsed.
    # If highest prior bid is high, we slightly overtake; otherwise, undercut.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Try to be competitive without full commitment.
        bid_target = highest_prev_bid + 1.5
        # If my hp is safe, don't chase too hard.
        if hp > 6.0 and budget > 0:
            bid_target = min(bid_target, DAILY_SALARY * 0.75)
    elif highest_prev_bid >= DAILY_SALARY * 0.55:
        bid_target = max(highest_prev_bid * 0.92, DAILY_SALARY * 0.5)
    else:
        # Low bids yesterday: bid near base to secure water cheaply.
        bid_target = base

    # Adjust for supply pressure: lower supply -> higher chance others bid aggressively.
    # supply range is 15..25.
    if supply <= 17.0:
        bid_target *= 1.10
    elif supply >= 23.0:
        bid_target *= 0.95

    # Cap by budget; also avoid bidding above what could be wasted.
    final_bid = float(min(budget, bid_target))

    # Ensure non-negative and at least minimal if budget allows.
    if final_bid < 0.0:
        final_bid = 0.0

    return final_bid
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
    day = int(day_context.get('day', 0))

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append(o)

    if not alive:
        return float(min(my_budget, DAILY_SALARY * 0.4))

    # Read only yesterday's immediate behavior
    prev_bids = []
    for o in alive:
        pt = o.get('previous_trace', {}) or {}
        b = pt.get('bid', None)
        if b is not None:
            prev_bids.append(float(b))

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate how many total water units likely available (not exact, but guides aggressiveness)
    # Ensure integer indexing safety by explicit int conversions where needed.
    approx_units = int(supply / float(WATER_REQ)) if WATER_REQ > 0 else 0

    # Base aggressiveness by our survival pressure
    critical = (my_hp <= 2) or (my_no_water_days >= 2)

    # Opponent pressure: Cindy died; likely others bid to avoid being outbid.
    # If any opponent bid very high yesterday, assume they were competing for scarce supply.
    very_high_threshold = 0.85 * DAILY_SALARY  # 76.5
    high_bid_threshold = 0.65 * DAILY_SALARY  # 58.5

    # Budget-aware cap so we don't repeat Cindy-like collapse
    # Keep a reserve of one day's salary or a fraction depending on HP.
    reserve_frac = 0.25 if my_hp >= 6 else 0.1
    reserve = DAILY_SALARY * reserve_frac

    max_affordable = max(0.0, my_budget - reserve)
    if max_affordable <= 0.0:
        # Can't safely bid much; bid minimal to try to avoid death
        return float(min(my_budget, DAILY_SALARY * 0.2))

    # Decide bid
    if highest_prev_bid >= very_high_threshold:
        # High pressure: try to beat them slightly, but scale with our HP
        if critical:
            bid = highest_prev_bid + 5.0
        else:
            # If we are healthy, don't overpay; still beat slightly
            bid = max(highest_prev_bid + 2.0, DAILY_SALARY * 0.35)
    elif highest_prev_bid >= high_bid_threshold:
        # Moderate pressure: bid around mid-high to secure
        if critical:
            bid = DAILY_SALARY * 0.75
        else:
            bid = max(DAILY_SALARY * 0.55, highest_prev_bid + 1.5)
    else:
        # Low pressure: conserve budget
        if critical:
            bid = DAILY_SALARY * 0.65
        else:
            bid = DAILY_SALARY * 0.45

    # Supply-aware adjustment: if supply is low, increase bid; if high, slightly decrease.
    if supply <= float(MIN_SUPPLY) + 1e-9:
        bid *= 1.12
    elif supply >= float(MAX_SUPPLY) - 1e-9:
        bid *= 0.92

    # If approx_units is 0, water is extremely scarce; push harder.
    if approx_units <= 0:
        bid *= 1.25

    # Final clamp
    bid = float(bid)
    bid = min(bid, max_affordable)
    bid = min(bid, my_budget)

    # Ensure non-negative
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

    # Read yesterday trace bids for immediate pressure
    yesterday_bids = []
    yesterday_max_bid = 0.0
    yesterday_min_bid = None
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is None:
            continue
        try:
            b = float(b)
        except Exception:
            continue
        yesterday_bids.append(b)
        if b > yesterday_max_bid:
            yesterday_max_bid = b
        if yesterday_min_bid is None or b < yesterday_min_bid:
            yesterday_min_bid = b

    # Supply pressure: when supply is low, competition is higher.
    supply_frac = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    low_supply = 1.0 - max(0.0, min(1.0, supply_frac))

    # If I'm in danger (multiple dry days), bid much more.
    danger = 0
    if no_water_days >= 2:
        danger = 2
    elif no_water_days == 1:
        danger = 1

    # Base bid target derived from yesterday's observed aggressiveness.
    # Opponents averaged ~108-115; use that as a ceiling reference.
    if yesterday_bids:
        # If someone already bid near max yesterday, raise our bid slightly.
        # Use a soft threshold relative to DAILY_SALARY.
        high_pressure = 1.0 if yesterday_max_bid >= DAILY_SALARY * 1.2 else 0.0
        # Target between ~0.9x and ~1.2x of yesterday_max_bid depending on danger.
        mult = 0.95 + 0.08 * danger + 0.06 * low_supply + 0.05 * high_pressure
        target = yesterday_max_bid * mult
    else:
        # Fallback if no trace bids
        target = DAILY_SALARY * (0.55 + 0.25 * low_supply + 0.15 * danger)

    # Also ensure we don't underbid when supply is low and hp is critical.
    if hp <= 2.0:
        target = max(target, DAILY_SALARY * (0.85 + 0.1 * low_supply))
    elif hp <= 4.0:
        target = max(target, DAILY_SALARY * (0.65 + 0.08 * low_supply))

    # Convert target to a final bid with budget cap.
    # Keep some budget for later: avoid spending more than ~70% of current budget unless very dangerous.
    spend_cap = 0.7
    if danger >= 2 or hp <= 2.0:
        spend_cap = 0.95
    final_bid = min(budget * spend_cap, target)

    # If supply is extremely low, push closer to full spend cap.
    if low_supply >= 0.85 and danger == 0:
        final_bid = min(budget * 0.85, max(final_bid, DAILY_SALARY * 0.6))

    # Non-negative and within reasonable bounds.
    if final_bid < 0.0:
        final_bid = 0.0

    return float(final_bid)
"""
