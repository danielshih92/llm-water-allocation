# ============================================================
# Experiment: exp_068
# Agent: Bob
# Source: exp_068
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

    supply = float(day_context.get('supply', (MIN_SUPPLY + MAX_SUPPLY) / 2.0))
    day = day_context.get('day', 1)

    budget = float(my_status.get('budget', 0.0))
    hp = float(my_status.get('hp', 0.0))

    # React to immediate yesterday trace if present
    alive_opps = [o for o in opponents_status.values() if o.get('alive', False)]
    yesterday_max_bid = None
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        if prev and prev.get('bid') is not None:
            b = float(prev.get('bid'))
            if yesterday_max_bid is None or b > yesterday_max_bid:
                yesterday_max_bid = b

    # Base target bid: aim to cover our need but not overpay.
    # Convert supply to a heuristic scarcity factor.
    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)  # 0..1 roughly
    # If supply is low, bid higher.
    base_fraction = 0.42 + 0.28 * scarcity  # 0.42..0.70

    # If we have a signal that opponents were bidding very high yesterday, slightly increase.
    if yesterday_max_bid is not None:
        if yesterday_max_bid >= DAILY_SALARY * 0.85:
            base_fraction += 0.08
        elif yesterday_max_bid >= DAILY_SALARY * 0.60:
            base_fraction += 0.03

    # HP-based urgency.
    if hp <= 2.0:
        base_fraction = max(base_fraction, 0.90)
    elif hp <= 3.0:
        base_fraction = max(base_fraction, 0.70)

    # Final bid cap: cannot exceed budget; also avoid extreme overbids.
    # Use a soft cap tied to daily salary.
    target = DAILY_SALARY * base_fraction
    bid = min(budget, target)

    # Ensure at least a minimal bid if we have budget.
    if bid <= 0.0 and budget > 0.0:
        bid = min(budget, DAILY_SALARY * 0.25)

    # Round to a reasonable granularity.
    return float(bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # If no opponents alive, conserve budget.
    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids for immediate reaction.
    opp_last_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                opp_last_bids.append((oid, float(b)))
            except Exception:
                pass

    # Determine Cindy pressure (she was the main high bidder yesterday).
    cindy_bid = None
    highest_prev_bid = None
    for oid, b in opp_last_bids:
        if highest_prev_bid is None or b > highest_prev_bid:
            highest_prev_bid = b
        if str(oid).lower() == 'cindy':
            cindy_bid = b

    # Supply-based aggressiveness: with more supply, we can bid less.
    # supply in [15,25], water units are supply/WATER_REQ.
    units = supply / float(WATER_REQ)

    # Baseline bid target: fraction of daily salary.
    # If supply is high (~25), bid lower; if low (~15), bid higher.
    if units >= (MAX_SUPPLY / float(WATER_REQ)):
        base = DAILY_SALARY * 0.45
    elif units <= (MIN_SUPPLY / float(WATER_REQ)):
        base = DAILY_SALARY * 0.65
    else:
        # linear interpolation between 0.65 at 15 and 0.45 at 25
        t = (supply - float(MIN_SUPPLY)) / (float(MAX_SUPPLY) - float(MIN_SUPPLY))
        base = DAILY_SALARY * (0.65 - 0.20 * t)

    # Escalate if I'm in danger.
    if hp <= 2.0 or no_water_days >= 2:
        base = max(base, DAILY_SALARY * 0.85)

    # If Cindy was extremely aggressive yesterday, we slightly shade upward but not fully.
    if cindy_bid is not None:
        if cindy_bid >= DAILY_SALARY * 1.6:  # ~144
            # Try to stay competitive while controlling spend.
            base = max(base, min(DAILY_SALARY * 0.9, cindy_bid * 0.55))
        elif cindy_bid >= DAILY_SALARY * 1.1:  # ~99
            base = max(base, DAILY_SALARY * 0.65)

    # If overall highest previous bid was huge, bid a bit under it.
    if highest_prev_bid is not None and highest_prev_bid >= DAILY_SALARY * 1.4:
        base = min(base, highest_prev_bid * 0.55 + 5.0)

    # Final cap by budget.
    bid = min(budget, base)

    # Ensure non-negative.
    if bid < 0.0:
        bid = 0.0

    # If budget is too low, still bid something to prevent worst-case elimination.
    if bid == 0.0 and budget > 0.0:
        bid = min(budget, DAILY_SALARY * 0.2)

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

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    # Determine how many full water units are realistically needed per winner.
    # (We don't know exact auction mechanics, so we use supply to scale aggressiveness.)
    units_available = int(round(supply / float(WATER_REQ))) if WATER_REQ > 0 else 0
    if units_available < 1:
        units_available = 1

    # Alive opponents
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    # If no one else is alive, bid conservatively.
    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Read yesterday's immediate bids from previous_trace.
    prev_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate opponent pressure.
    highest_prev = max(prev_bids) if prev_bids else 0.0
    lowest_prev = min(prev_bids) if prev_bids else 0.0

    # Identify if there is a strong high bidder (likely Cindy-like behavior).
    # If someone previously bid near (or above) our daily salary, they likely contest.
    high_pressure = highest_prev >= DAILY_SALARY * 0.85

    # Our HP-based risk control.
    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))

    # Supply scaling: higher supply reduces need to overbid.
    # Map supply in [15,25] to aggressiveness in [1.05,0.85].
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_factor = 1.05 - 0.2 * ((supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY))
    else:
        supply_factor = 1.0

    # Base bid target.
    if high_pressure:
        # Try to slightly undercut the high bidder while still beating low bidders.
        # Use highest_prev as reference but cap near daily salary to avoid runaway.
        target = min(DAILY_SALARY * 0.95, highest_prev - 2.0)
        # If our HP is critical, we overrule and go closer to high bidder.
        if hp <= 2.5:
            target = min(my_status['budget'], max(target, highest_prev - 0.5))
    else:
        # No extreme bidder: aim above the low end but not too high.
        # Use a midpoint between lowest_prev and DAILY_SALARY.
        target = max(lowest_prev + 2.0, DAILY_SALARY * 0.55)

    # HP adjustment: lower HP -> higher bid.
    if hp <= 2:
        target *= 1.15
    elif hp <= 4:
        target *= 1.05
    else:
        target *= 0.95

    # Apply supply scaling.
    target *= supply_factor

    # Final clamp to budget and reasonable bounds.
    if target < 0:
        target = 0.0
    bid = min(budget, target)

    # Ensure we don't bid zero when we likely need water.
    # If supply is enough for at least one unit, keep a small floor.
    if bid <= 0 and supply >= WATER_REQ:
        bid = min(budget, DAILY_SALARY * 0.25)

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

    # Identify alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # If no opponents alive, bid conservatively
    if not alive_opps:
        cap = min(my_status['budget'], DAILY_SALARY * 0.4)
        return float(cap)

    # Use only yesterday's previous_trace bid for each opponent for immediate reaction
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Defaults based on our health/budget
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    # Estimate pressure from yesterday
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else (prev_bids[0] if prev_bids else 0.0)

    # Supply-aware aggressiveness: closer to max supply => more likely to allow higher bids; bid just above typical leader
    supply_ratio = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Target bid baseline
    # If Cindy-like high pressure existed yesterday, we must match/beat slightly.
    if highest_prev_bid >= DAILY_SALARY * 0.9:
        # Cindy was very aggressive; if our hp is low, bid more to guarantee water.
        if hp <= 2.0:
            target = DAILY_SALARY * (0.95 - 0.15 * supply_ratio)
        else:
            # Slightly above the second-highest to avoid tying into a loss
            target = max(second_prev_bid + 2.0, DAILY_SALARY * (0.65 + 0.15 * supply_ratio))
    else:
        # Moderate pressure: bid around Alex-like level, scaled by supply.
        # Use highest_prev_bid as an anchor but don't overpay.
        anchor = highest_prev_bid if highest_prev_bid > 0 else (DAILY_SALARY * 0.55)
        target = max(DAILY_SALARY * (0.45 + 0.2 * supply_ratio), min(anchor + 5.0, DAILY_SALARY * 0.75))

    # If our budget is tight, scale down
    if budget < DAILY_SALARY * 0.6:
        target = min(target, budget * 0.9)

    # If hp is critical, spend more (but never exceed budget)
    if hp <= 1.5:
        target = min(budget, max(target, DAILY_SALARY * 0.9))

    bid = min(budget, target)
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive = []
    for agent_id, st in opponents_status.items():
        try:
            if st.get('alive', False):
                alive.append((agent_id, st))
        except Exception:
            continue

    if not alive:
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday bids from traces for immediate reaction
    prev_bids = []
    for _, st in alive:
        prev = st.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    prev_bids.append(float(b))
                except Exception:
                    pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_prev_bid = 0.0
    if prev_bids:
        sorted_b = sorted(prev_bids)
        if len(sorted_b) >= 2:
            second_prev_bid = sorted_b[-2]

    # Convert supply into a rough count of winners; we assume water is scarce.
    # If supply is low, only a few bidders get water, so we bid more to avoid falling short.
    # Use int() indices explicitly even though we don't index lists.
    supply_int = int(supply)
    # Expected number of water units won per day is proportional; approximate winners count.
    # Ensure at least 1 winner.
    approx_winners = max(1, int(supply_int // WATER_REQ))

    # Pressure model: if Cindy-like behavior (very high bid) happened, increase slightly.
    # If my hp is low or I already have no_water_days, increase aggressively.
    critical = (hp <= 2) or (no_water_days >= 2)

    # Base bid target: just above what likely top bidder paid yesterday, but scaled down to avoid overspending.
    # If highest_prev_bid is huge, we still only match a fraction.
    if highest_prev_bid > 0:
        # If highest_prev_bid indicates heavy contest, bid to be competitive.
        if highest_prev_bid >= DAILY_SALARY * 0.9:
            target = highest_prev_bid * 0.72
        else:
            # Otherwise bid around the upper-middle.
            target = max(second_prev_bid * 0.85, highest_prev_bid * 0.6)
    else:
        target = DAILY_SALARY * 0.55

    # Scarcity adjustment: fewer winners -> bid higher.
    # approx_winners in [1,2,3] typically; map to multiplier.
    if approx_winners <= 1:
        target *= 1.15
    elif approx_winners == 2:
        target *= 1.05
    else:
        target *= 0.95

    if critical:
        target *= 1.25
    elif hp >= 7 and no_water_days == 0:
        target *= 0.85

    # Also cap so we don't bankrupt unless critical.
    # If not critical, keep some budget buffer.
    if not critical:
        max_spend = max(DAILY_SALARY * 0.65, budget * 0.35)
    else:
        max_spend = max(DAILY_SALARY * 0.9, budget * 0.75)

    bid = min(budget, target, max_spend)

    # Ensure non-negative and at least a small bid if budget allows.
    if bid < 0:
        bid = 0.0
    if bid == 0.0 and budget > 0:
        bid = min(budget, DAILY_SALARY * 0.2)

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

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        try:
            if opp.get('alive', False):
                alive_opps.append((opp_id, opp))
        except Exception:
            pass

    # If no opponents alive, conserve water
    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids to infer aggressiveness
    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    yesterday_bids.append(float(b))
                except Exception:
                    pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else 0.0

    # Supply-based urgency: with 15-25 supply, each unit of water is valuable.
    # If supply is high, lower bids may still win.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Base target bid: aim slightly above what strong opponents likely paid yesterday.
    # But avoid matching their full aggression unless we are in danger.
    # Use hp/no_water_days to decide whether to escalate.
    danger = 0
    if hp <= 2.0:
        danger = 2
    elif hp <= 4.0:
        danger = 1

    if no_water_days >= 2:
        danger = max(danger, 1)

    # Estimate a competitive threshold
    # If yesterday highest was very high, strong players are spending.
    # We counter with a moderate overbid; otherwise bid around a fraction of highest.
    if highest_prev_bid >= DAILY_SALARY * 1.0:  # ~90
        if danger >= 2:
            target = highest_prev_bid * 0.75 + 5.0
        elif danger == 1:
            target = highest_prev_bid * 0.55 + 3.0
        else:
            target = highest_prev_bid * 0.45 + 2.0
    else:
        if danger >= 2:
            target = max(DAILY_SALARY * 0.7, second_prev_bid * 0.8 + 2.0)
        elif danger == 1:
            target = max(DAILY_SALARY * 0.55, second_prev_bid * 0.6 + 2.0)
        else:
            target = max(DAILY_SALARY * 0.45, highest_prev_bid * 0.35 + 2.0)

    # Adjust for supply: higher supply => reduce bid pressure
    target = target * (1.0 - 0.15 * supply_ratio)

    # Clamp by budget and avoid overpaying near end-game
    # If late day, increase slightly.
    if day >= 8:
        target *= 1.08

    # Ensure non-negative
    target = max(0.0, target)

    # Final bid: never exceed budget
    bid = min(budget, target)

    # If budget is too low, bid whatever remains (still non-negative)
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

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    # Alive opponents only
    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    # If no opponents, conserve budget
    if not alive_opponents:
        return max(0.0, min(float(my_status.get('budget', 0.0)), DAILY_SALARY * 0.4))

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Yesterday pressure signal from previous_trace bids
    prev_bids = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev_bid

    # Supply pressure: if supply is low, chances of winning water are higher for higher bids.
    # We map supply to a competitiveness multiplier.
    if supply <= MIN_SUPPLY:
        supply_factor = 1.10
    elif supply >= MAX_SUPPLY:
        supply_factor = 0.95
    else:
        # Linear interpolation between 1.10 and 0.95
        supply_factor = 1.10 - (supply - MIN_SUPPLY) * (1.10 - 0.95) / (MAX_SUPPLY - MIN_SUPPLY)

    # HP urgency: if we're close to death, bid more aggressively.
    if my_hp <= 2.0 or no_water_days >= 2:
        hp_factor = 1.25
    elif my_hp <= 4.0:
        hp_factor = 1.05
    else:
        hp_factor = 0.90

    # Base bid aims to be competitive but not maximal.
    # Use highest_prev_bid as an anchor to avoid being underbid against high-pressure players.
    if highest_prev_bid >= DAILY_SALARY * 1.35:  # ~121+ in yesterday context
        # High pressure: bid slightly below the top bidder to win if others also bid high.
        target = min(highest_prev_bid - 2.0, DAILY_SALARY * 1.15)
    elif highest_prev_bid >= DAILY_SALARY * 0.85:  # ~77+ 
        # Moderate pressure: bid around the second-highest or mid-high.
        target = max(second_prev_bid - 1.5, DAILY_SALARY * 0.75)
    else:
        # Low pressure: bid near a baseline.
        target = DAILY_SALARY * 0.60

    # Apply factors
    target = target * supply_factor * hp_factor

    # Ensure we can afford it and keep it non-negative
    bid = max(0.0, min(my_budget, target))

    # If budget is very tight, still bid enough to avoid an extra no-water day when HP is low.
    if my_budget < DAILY_SALARY * 0.6 and (my_hp <= 4.0 or no_water_days >= 2):
        bid = max(0.0, min(my_budget, DAILY_SALARY * 0.85))

    # Final clamp to a reasonable range
    upper = min(my_budget, DAILY_SALARY * 1.30)
    lower = 0.0
    if bid < lower:
        bid = lower
    if bid > upper:
        bid = upper

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

    # Alive opponents
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)

    if not alive_opps:
        # If alone, bid conservatively to stay solvent
        return max(0.0, min(float(my_status.get('budget', 0.0)), DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace only
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

    # Estimate whether we likely need to secure at least one unit of water to avoid no-water days
    # (We don't know today's hidden bids; this is a heuristic.)
    no_water_days = int(my_status.get('no_water_days', 0))
    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))

    # Base bid: aim for a mid value that often beats low bidders but doesn't match overbidders.
    # Use supply to scale: higher supply reduces urgency.
    supply_factor = (float(supply) - 15.0) / (25.0 - 15.0) if (25.0 - 15.0) != 0 else 0.5
    supply_factor = max(0.0, min(1.0, supply_factor))

    # If opponents were bidding extremely high yesterday, they likely force contention.
    # Cindy's pattern suggests some agents can sustain high bids.
    urgent_pressure = highest_prev_bid >= DAILY_SALARY * 1.15  # ~103.5

    # If I'm low hp or have accumulated no-water days, I must raise bids.
    critical = (hp <= 2.5) or (no_water_days >= 2)

    # Compute target bid
    if urgent_pressure:
        if critical:
            target = DAILY_SALARY * 0.95
        else:
            # Slightly under the overbid to conserve budget
            target = max(DAILY_SALARY * 0.65, min(DAILY_SALARY * 0.85, highest_prev_bid * 0.75))
    else:
        if critical:
            target = DAILY_SALARY * 0.85
        else:
            # Mid bid; scale down when supply is higher
            target = DAILY_SALARY * (0.55 - 0.15 * supply_factor)
            target = max(DAILY_SALARY * 0.35, target)

    # Don't exceed budget; also avoid bidding negative
    bid = max(0.0, min(budget, float(target)))

    # If budget is very low, still bid enough to have a chance (but capped)
    if budget < DAILY_SALARY * 0.2:
        bid = max(0.0, min(budget, DAILY_SALARY * 0.1))

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
    day = int(day_context['day'])

    # Alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # If no opponents, spend enough to secure water.
    if not alive_opps:
        cap = my_status['budget']
        return min(cap, DAILY_SALARY * 0.5)

    # Read yesterday bids to infer aggressiveness.
    yesterday_bids = []
    yesterday_hp_after = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass
            try:
                yesterday_hp_after.append(float(prev.get('hp_after', o.get('hp', 0))))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = (sum(yesterday_bids) / len(yesterday_bids)) if yesterday_bids else 0.0

    # Supply pressure: if supply is high, we can bid lower and still win via equilibrium.
    # If supply is low, others must pay more to survive; we slightly raise bid.
    supply_mid = (MIN_SUPPLY + MAX_SUPPLY) / 2.0
    supply_factor = 0.9 if supply < supply_mid else 0.75

    # Our urgency based on hp and no-water days.
    hp = float(my_status['hp'])
    no_water_days = int(my_status['no_water_days'])

    # Target bid baseline: aim below the highest yesterday bid unless we're in danger.
    base = avg_prev_bid * 0.85 if avg_prev_bid > 0 else DAILY_SALARY * 0.55

    # If someone was clearly overbidding yesterday (>= 0.85*DAILY_SALARY), we don't mirror fully.
    # Instead, undercut slightly to avoid price war.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        base = min(base, DAILY_SALARY * 0.6)

    # Escalate only when we are actually at risk.
    if hp <= 2.0 or no_water_days >= 2:
        base = max(base, DAILY_SALARY * 0.75)
    elif hp <= 4.0:
        base = max(base, DAILY_SALARY * 0.62)

    # Day-based mild ramp near the end of episode.
    # episode is 10 days; meta-round gives day_context['day'].
    if day >= 8:
        base *= 1.08

    # Apply supply factor and ensure we are not bidding above a reasonable cap.
    bid = base * supply_factor

    # Hard caps by budget.
    bid = min(bid, float(my_status['budget']))

    # Ensure non-negative and at least some minimal bid if budget allows.
    if bid < 0:
        bid = 0.0
    if bid == 0.0 and my_status['budget'] > 0:
        bid = min(float(my_status['budget']), DAILY_SALARY * 0.15)

    return bid
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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    if not alive_opponents:
        return float(min(my_budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace for immediate reaction
    yesterday_bids = []
    yesterday_pressures = []  # (bid, opp_hp_after)
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                b = float(bid)
            except Exception:
                continue
            yesterday_bids.append(b)
            hp_after = prev.get('hp_after', None)
            if hp_after is not None:
                try:
                    yesterday_pressures.append((b, int(hp_after)))
                except Exception:
                    pass

    # Fallback if traces missing
    if not yesterday_bids:
        if my_hp <= 2 or my_no_water_days >= 2:
            return float(min(my_budget, DAILY_SALARY * 0.9))
        return float(min(my_budget, DAILY_SALARY * 0.55))

    highest_prev_bid = max(yesterday_bids)
    second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid

    # Estimate how many water units are available relative to requirement
    # Use int() indices: only for internal thresholds, not list access.
    units_available = int(supply / float(WATER_REQ)) if WATER_REQ > 0 else 0
    # When supply is moderate (15-25) and WATER_REQ=9, units_available is typically 1.

    # Risk model: if my HP is low or I already have no-water days, bid more aggressively.
    critical = (my_hp <= 2) or (my_no_water_days >= 2)

    # If someone bid very high yesterday, they likely secured water; to avoid losing again, match/beat slightly.
    # Otherwise, bid around the median/high end but not full.
    sorted_bids = sorted(yesterday_bids)
    median_prev_bid = sorted_bids[len(sorted_bids)//2] if sorted_bids else highest_prev_bid

    # Determine target bid
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        if critical:
            target = highest_prev_bid * 1.03
        else:
            # Slightly under/near the top to conserve budget
            target = max(median_prev_bid, second_prev_bid + 2.0)
            target = max(target, highest_prev_bid * 0.92)
    else:
        # No extreme pressure: bid to be competitive but not wasteful
        if critical:
            target = max(highest_prev_bid * 0.9, median_prev_bid + 10.0)
        else:
            # If units_available is low (likely 1), competition matters more
            if units_available <= 1:
                target = max(median_prev_bid + 5.0, second_prev_bid + 1.5)
            else:
                target = max(median_prev_bid, second_prev_bid + 0.5)

    # Convert target into a bounded bid with budget and salary constraints
    # Keep bids in a reasonable band to avoid overspending.
    upper_cap = DAILY_SALARY * 1.1
    lower_floor = DAILY_SALARY * 0.25
    bid = float(min(my_budget, min(upper_cap, max(lower_floor, target))))

    # If supply is at the low end, increase bid slightly since fewer units likely win.
    if supply <= float(MIN_SUPPLY) + 0.5:
        bid = float(min(my_budget, bid * 1.08))

    # Final safety clamp
    if bid < 0:
        bid = 0.0
    return bid
"""
