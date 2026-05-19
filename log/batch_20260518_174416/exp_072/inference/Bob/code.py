# ============================================================
# Experiment: exp_072
# Agent: Bob
# Source: exp_072
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
    hp = float(my_status.get('hp', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    # If we can’t read opponent behavior, choose a robust bid.
    # Baseline depends on supply: lower supply => higher bid to secure allocation.
    if supply <= float(MIN_SUPPLY):
        base_frac = 0.62
    elif supply >= float(MAX_SUPPLY):
        base_frac = 0.48
    else:
        # Linear interpolation between MIN_SUPPLY and MAX_SUPPLY
        t = (supply - float(MIN_SUPPLY)) / (float(MAX_SUPPLY) - float(MIN_SUPPLY))
        base_frac = 0.62 - 0.14 * t

    # React to our own risk.
    risk_boost = 0.0
    if hp <= 2.0:
        risk_boost = 0.35
    elif hp <= 3.0:
        risk_boost = 0.20

    if no_water_days >= 2:
        risk_boost = max(risk_boost, 0.25)
    elif no_water_days >= 1:
        risk_boost = max(risk_boost, 0.12)

    # Also, if any opponent yesterday bid was extremely high, slightly increase.
    # (We only look at previous_trace from yesterday per rules.)
    extreme_prev = False
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        prev_bid = prev.get('bid', None)
        if prev_bid is not None:
            try:
                if float(prev_bid) >= 0.85 * DAILY_SALARY:
                    extreme_prev = True
                    break
            except Exception:
                pass

    if extreme_prev:
        base_frac = max(base_frac, 0.70)

    target = DAILY_SALARY * (base_frac + risk_boost)

    # Convert target to a bid that is always feasible and conservative.
    bid = min(budget, target)

    # Ensure not bidding trivially low; still respect budget.
    min_bid = min(budget, DAILY_SALARY * 0.25)
    if bid < min_bid:
        bid = min_bid

    # If we are in late episode days, be more aggressive.
    if day >= 8:
        bid = min(budget, max(bid, DAILY_SALARY * 0.65))

    # Final clamp to non-negative.
    if bid < 0.0:
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Alive opponents
    alive_ids = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_ids.append(oid)

    if not alive_ids:
        # If alone, conserve budget while still paying enough when supply is tight
        base = DAILY_SALARY * 0.35
        if my_status['no_water_days'] >= 2:
            base = DAILY_SALARY * 0.75
        return float(min(my_status['budget'], base))

    # Immediate reaction to yesterday's bids (only previous_trace)
    yesterday_bids = []
    for oid in alive_ids:
        prev = opponents_status[oid].get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Supply pressure: how many full water requirements are available
    # Use int() for any indexing; here we only compute scalars.
    supply_units = supply / float(WATER_REQ)

    # Determine aggressiveness
    # If someone previously bid near our daily salary, they likely overbid to secure water.
    # We counter with a moderate bid to avoid getting outbid while not matching extremes.
    pressure = 0.0
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        pressure = 0.35
    elif highest_prev_bid >= DAILY_SALARY * 0.55:
        pressure = 0.20
    else:
        pressure = 0.10

    # HP and no-water urgency
    hp = float(my_status['hp'])
    no_water_days = int(my_status['no_water_days'])

    urgency = 0.0
    if hp <= 2:
        urgency = 0.65
    elif hp <= 4:
        urgency = 0.45
    elif no_water_days >= 3:
        urgency = 0.45
    elif no_water_days >= 2:
        urgency = 0.25
    else:
        urgency = 0.10

    # Base bid scales with supply tightness: tighter supply => higher bid
    # supply_units ~ 1.66 to 2.77 for 15-25 with WATER_REQ=9
    # We'll map to a tightness factor.
    tightness = 0.0
    if supply <= MIN_SUPPLY + 1e-6:
        tightness = 0.40
    elif supply >= MAX_SUPPLY - 1e-6:
        tightness = 0.10
    else:
        # linear between MIN_SUPPLY and MAX_SUPPLY
        tightness = 0.40 - 0.30 * ((supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY))

    # Final target fraction of daily salary
    frac = 0.30 + pressure + urgency + tightness

    # If supply is relatively abundant, reduce bids unless we're in danger
    if supply_units >= 2.4 and hp > 4:
        frac -= 0.10

    # Clamp fraction
    if frac < 0.20:
        frac = 0.20
    if frac > 0.95:
        frac = 0.95

    bid = DAILY_SALARY * frac

    # Never exceed budget
    if my_status['budget'] <= 0:
        return 0.0
    if bid > my_status['budget']:
        bid = float(my_status['budget'])

    # If very low budget, still try a small amount to avoid total starvation
    if my_status['budget'] < DAILY_SALARY * 0.25:
        # If we're already on multiple no-water days, spend more
        if no_water_days >= 2:
            bid = float(min(my_status['budget'], DAILY_SALARY * 0.55))
        else:
            bid = float(min(my_status['budget'], DAILY_SALARY * 0.20))

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

    supply = day_context['supply']
    day = day_context['day']

    # Identify alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # If no opponents are alive, conserve water
    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.35)

    # Read yesterday bids from immediate previous_trace only
    prev_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev['bid']))

    # Estimate what supply can support: number of full water quanta
    # (Not directly used for indexing; just for scaling)
    supply_quanta = max(1.0, float(supply) / float(WATER_REQ))

    # Determine if Cindy is likely to be the high-pressure bidder
    cindy = opponents_status.get('Cindy', None)
    cindy_alive = bool(cindy and cindy.get('alive', False))
    cindy_prev_bid = None
    if cindy:
        prev = cindy.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            cindy_prev_bid = float(prev['bid'])

    # Determine opponent pressure level from yesterday
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev_bid
    else:
        highest_prev_bid = 0.0
        second_prev_bid = 0.0

    # Core strategy:
    # - If Cindy was aggressive yesterday, match slightly above her to secure water.
    # - Otherwise, bid based on our HP: low HP => bid high; high HP => bid moderate.
    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])

    # Budget safety: never bid more than budget
    def clamp_bid(x):
        if x < 0:
            return 0.0
        return min(my_budget, x)

    # Aggressive match if Cindy was high
    if cindy_alive and cindy_prev_bid is not None:
        # Cindy averaged ~63.78 yesterday; use thresholds around that.
        if cindy_prev_bid >= DAILY_SALARY * 0.55:
            # Bid just above her yesterday bid, but scaled by supply pressure.
            # Supply 15 => less water; bid a bit more. Supply 25 => bid slightly less.
            supply_bias = 1.08 if supply <= (MIN_SUPPLY + 0.5) else 0.98
            target = (cindy_prev_bid + 2.0) * supply_bias
            # If our HP is very low, increase urgency
            if my_hp <= 2.0:
                target *= 1.25
            return clamp_bid(target)

    # Otherwise react to overall highest bid
    if highest_prev_bid >= DAILY_SALARY * 0.7:
        # Very high contention: bid to avoid being starved
        if my_hp <= 2.0:
            return clamp_bid(DAILY_SALARY * 0.95)
        return clamp_bid(max(highest_prev_bid + 1.5, DAILY_SALARY * 0.65))

    if highest_prev_bid >= DAILY_SALARY * 0.4:
        # Moderate contention
        if my_hp <= 3.0:
            return clamp_bid(max(highest_prev_bid + 1.0, DAILY_SALARY * 0.6))
        return clamp_bid(max(second_prev_bid + 2.0, DAILY_SALARY * 0.5))

    # Low contention: bid based on HP and remaining budget
    if my_hp <= 2.0:
        return clamp_bid(DAILY_SALARY * 0.85)
    if my_hp <= 4.0:
        return clamp_bid(DAILY_SALARY * 0.65)

    # If we have decent HP, conserve while still competing for water
    # Scale slightly with supply quanta (more supply => can afford lower bid)
    conserve_factor = 0.55 if supply_quanta >= (float(MAX_SUPPLY) / float(WATER_REQ)) else 0.6
    return clamp_bid(DAILY_SALARY * conserve_factor)
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

    # If no one alive, bid conservatively.
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from immediate previous_trace only.
    yesterday_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        if prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Estimate how aggressive the field is.
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = (sum(yesterday_bids) / len(yesterday_bids)) if yesterday_bids else 0.0

    # Convert supply to a rough urgency: lower supply => higher chance of contention.
    # supply between 15..25 -> urgency between ~1.0..0.0
    urgency = 1.0 - (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    urgency = max(0.0, min(1.0, urgency))

    # If opponents were bidding huge yesterday, they likely keep spending.
    # We shade below their top bid to conserve, but still scale with urgency.
    # Also, if we're low on hp, we must bid more.
    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Base bid target.
    # Use a fraction of DAILY_SALARY, adjusted by urgency and yesterday aggressiveness.
    aggressiveness = 0.0
    if avg_prev_bid > 0:
        aggressiveness = max(0.0, min(1.0, avg_prev_bid / (DAILY_SALARY * 1.2)))

    # Core target: between 0.45 and 0.85 of salary depending on urgency/aggressiveness.
    target = DAILY_SALARY * (0.45 + 0.35 * urgency * (0.5 + aggressiveness))

    # Pressure response: if we're in danger, raise bid.
    if my_hp <= 2.0 or no_water_days >= 2:
        target = max(target, DAILY_SALARY * (0.75 + 0.15 * urgency))
    elif my_hp <= 4.0:
        target = max(target, DAILY_SALARY * (0.60 + 0.15 * urgency))

    # Exploit: if highest_prev_bid was extremely high, don't match it; bid just under.
    # This leverages their tendency to overpay.
    if highest_prev_bid > DAILY_SALARY:
        # Bid slightly below their max to win when they overcommit.
        target = min(target, highest_prev_bid * (0.88 - 0.1 * urgency))

    # Safety clamp: never exceed budget.
    bid = float(min(my_budget, max(0.0, target)))

    # Ensure some minimal bid when contention is likely.
    # (If budget is tiny, this will still be capped by budget.)
    min_bid = 5.0 + 15.0 * urgency
    bid = float(min(my_budget, max(bid, min_bid if my_budget >= min_bid else bid)))

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

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace for immediate reaction.
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    yesterday_bids.append(float(b))
                except Exception:
                    pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_highest_prev_bid = 0.0
    if len(yesterday_bids) >= 2:
        sorted_bids = sorted(yesterday_bids)
        second_highest_prev_bid = float(sorted_bids[-2])

    # Supply pressure: lower supply means fewer water units; bid more to secure.
    # Normalize to [0,1]
    if MAX_SUPPLY > MIN_SUPPLY:
        s_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        s_norm = 0.5
    s_norm = max(0.0, min(1.0, float(s_norm)))

    # If my hp is low or I've already gone without water, I must bid higher.
    urgent = (my_hp <= 2) or (my_no_water_days >= 2)

    # If someone previously bid very high, they likely fought hard; try to slightly overcut.
    # Use DAILY_SALARY scale observed: Cindy ~105, Eric ~128, David low.
    if highest_prev_bid >= DAILY_SALARY * 0.9:
        target = highest_prev_bid + 2.0
        # If I'm healthy, don't fully match; bid a bit less than the leader.
        if my_hp >= 7 and not urgent:
            target = min(highest_prev_bid + 1.0, DAILY_SALARY * 0.75 + 10.0)
    elif highest_prev_bid >= DAILY_SALARY * 0.6:
        # Mid pressure: bid around the leader but with small buffer.
        target = max(DAILY_SALARY * 0.55, second_highest_prev_bid + 1.5)
        # Adjust with supply: lower supply -> higher bid.
        target = target + (1.0 - s_norm) * 10.0
    else:
        # Low observed bids: take a moderate stance, unless urgent.
        target = DAILY_SALARY * (0.45 + (1.0 - s_norm) * 0.25)

    if urgent:
        target = max(target, DAILY_SALARY * 0.85)

    # Convert to final bid with budget cap.
    bid = max(0.0, min(my_budget, float(target)))

    # Additional safeguard: if budget is tiny, bid all-in but never exceed.
    if my_budget <= DAILY_SALARY * 0.2:
        bid = my_budget

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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive = []
    for agent_id, st in opponents_status.items():
        if st.get('alive', False):
            alive.append((agent_id, st))

    if not alive:
        return float(min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids to gauge pressure.
    prev_bids = []
    for _, st in alive:
        prev = st.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate how many full allocations are feasible at this supply.
    # Each agent needs WATER_REQ units to avoid losing HP; supply is total water.
    # We approximate slots = floor(supply / WATER_REQ).
    slots = int(supply / float(WATER_REQ)) if WATER_REQ > 0 else 0
    if slots < 1:
        slots = 1

    # Pressure heuristic: if someone previously went extremely high, we must compete.
    # Alex's behavior suggests occasional spikes; target a bid slightly above expected clearing.
    tight_supply = supply <= (MIN_SUPPLY + 2.0)

    # Determine urgency from our HP / no_water_days.
    urgency = 0
    if hp <= 2.0:
        urgency = 3
    elif hp <= 4.0:
        urgency = 2
    elif hp <= 7.0:
        urgency = 1

    if no_water_days >= 2:
        urgency += 1

    # Base bid: aim to secure water when tight and/or urgent.
    # When not urgent, bid conservatively to save budget.
    if tight_supply and urgency >= 2:
        target = highest_prev_bid * 1.05 + 2.0
    elif tight_supply and urgency >= 1:
        target = max(highest_prev_bid * 0.7, DAILY_SALARY * 0.35)
    elif (not tight_supply) and urgency >= 3:
        target = highest_prev_bid * 0.85 + 1.0
    else:
        target = max(DAILY_SALARY * 0.28, highest_prev_bid * 0.45)

    # Convert target into a safe bid cap based on our budget.
    # Keep some budget reserve for later days.
    reserve_factor = 0.25 if urgency >= 2 else 0.4
    cap = budget * (1.0 - reserve_factor)

    # Also cap by a fraction of daily salary to avoid reckless spending.
    spend_cap = DAILY_SALARY * (0.95 if urgency >= 3 else 0.7 if urgency >= 1 else 0.55)

    bid = float(min(cap, spend_cap, target))

    # Ensure we bid at least a minimal positive amount when trying to survive.
    if urgency >= 2 and bid < 1.0:
        bid = 1.0

    # If budget is tiny, just spend what we can.
    if budget <= 1.0:
        bid = float(budget)

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

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Alive opponents
    alive_ids = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_ids.append(oid)

    if not alive_ids:
        # If alone, bid just enough to keep ourselves safe.
        target = DAILY_SALARY * 0.4
        return float(min(budget, target))

    # Read yesterday bids from previous_trace for immediate reaction
    prev_bids = []
    for oid in alive_ids:
        prev = opponents_status[oid].get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev = max(prev_bids) if prev_bids else 0.0
    # Also consider who seemed most aggressive yesterday
    # (use their max bid as a proxy if available)
    aggressive_prev = 0.0
    for oid in alive_ids:
        prev = opponents_status[oid].get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                bb = float(b)
            except Exception:
                continue
            # If they bid near the top, treat them as aggressive
            if bb >= 0.85 * highest_prev and highest_prev > 0:
                aggressive_prev = max(aggressive_prev, bb)

    # Supply pressure: when supply is higher, more water can be allocated; bidding can be slightly lower.
    # When supply is low, we must secure our share.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.0
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Our urgency: if low hp or already on no-water streak, bid more.
    urgency = 0.0
    if hp <= 2.0:
        urgency += 1.0
    if no_water_days >= 1:
        urgency += 0.6
    if no_water_days >= 2:
        urgency += 0.8

    # Baseline aggressiveness based on yesterday's top bids.
    # If others went very high, we must match/beat; otherwise, bid around a fraction of the top.
    if highest_prev > 0:
        if highest_prev >= 0.85 * DAILY_SALARY:
            # High contest: either we secure now or risk cascading no-water days.
            base = DAILY_SALARY * (0.35 if hp > 3.0 else 0.95)
            # Tighten to just above their aggression when supply is low.
            if supply_ratio < 0.5:
                base = max(base, aggressive_prev * 1.02)
        else:
            # Moderate contest: bid somewhat above their top to win when needed.
            base = max(DAILY_SALARY * 0.5, highest_prev + 1.5)
            if supply_ratio > 0.6:
                base *= 0.9
    else:
        base = DAILY_SALARY * (0.55 if hp > 3.0 else 0.75)

    # Adjust for urgency and supply.
    # When supply is low, increase bid; when supply is high, decrease slightly.
    bid = base * (1.0 + 0.25 * urgency) * (1.0 + (0.5 - supply_ratio) * 0.25)

    # Hard caps/floors to avoid overspending.
    # Never bid more than our budget; also avoid bidding too low when urgent.
    min_bid = 0.0
    if urgency >= 1.0:
        min_bid = DAILY_SALARY * 0.75
    elif urgency >= 0.6:
        min_bid = DAILY_SALARY * 0.55
    else:
        min_bid = DAILY_SALARY * 0.4

    bid = max(min_bid, bid)
    bid = min(budget, bid)

    # If budget is extremely low, bid what we can.
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

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from immediate previous_trace only
    prev_bids = []
    prev_bid_by_agent = {}
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                bval = float(b)
            except Exception:
                continue
            prev_bids.append(bval)
            prev_bid_by_agent[oid] = bval

    # Base bid pressure from yesterday
    if prev_bids:
        highest_prev = max(prev_bids)
        second_prev = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev
        # If someone clearly overpaid, we shade slightly to avoid bidding into their price.
        if highest_prev >= DAILY_SALARY * 0.95:
            target = max(DAILY_SALARY * 0.65, second_prev + 5.0)
        elif highest_prev >= DAILY_SALARY * 0.75:
            target = max(DAILY_SALARY * 0.55, highest_prev * 0.85)
        else:
            # Otherwise match the market a bit above the top to secure water.
            target = max(DAILY_SALARY * 0.5, highest_prev + 10.0)
    else:
        target = DAILY_SALARY * 0.55

    # Adjust for our health and need
    if my_hp <= 2.0:
        target = max(target, DAILY_SALARY * 0.9)
    elif my_hp <= 4.0:
        target = max(target, DAILY_SALARY * 0.7)

    # If we've already gone without water, increase urgency
    if my_no_water_days >= 1:
        target = max(target, DAILY_SALARY * (0.65 + 0.1 * min(3, my_no_water_days)))

    # Supply-aware shading: higher supply reduces urgency/price
    # We don't know exact allocation mechanics; use supply as a proxy for competitive intensity.
    supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    # When supply is high, shade down a bit.
    target *= (0.95 - 0.1 * supply_norm)

    # Ensure we never exceed our budget.
    bid = max(0.0, min(my_budget, target))

    # If budget is extremely low, still bid something to try to avoid starvation.
    if my_budget <= DAILY_SALARY * 0.15:
        bid = max(0.0, min(my_budget, DAILY_SALARY * 0.25))

    # Small deterministic nudge by day to avoid exact ties.
    bid += float((day % 3) - 1) * 1.5
    bid = max(0.0, min(my_budget, bid))

    return bid
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
    day = day_context['day']

    # Alive opponents
    alive = []
    for k, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((k, o))

    # If no opponents, bid conservatively
    if not alive:
        return max(0.0, min(float(my_status['budget']), DAILY_SALARY * 0.5))

    # Read yesterday bids (immediate reaction)
    yesterday_bids = []
    for _, o in alive:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Determine how aggressive others were
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = float(my_status['no_water_days'])

    # Supply pressure: tighter supply => bid higher to secure water
    # supply ranges 15..25, map to 0..1 pressure
    pressure = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    pressure = max(0.0, min(1.0, pressure))

    # If I'm in danger, bid much more
    if hp <= 2 or no_water_days >= 2:
        target = DAILY_SALARY * (0.75 + 0.25 * pressure)
    else:
        # Otherwise, bid to compete but not match the top aggressor
        # Use highest_prev_bid to avoid being undercut when others overbid.
        # Aim for between avg and slightly below highest.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # Others were very aggressive; try to be competitive but keep margin.
            target = min(highest_prev_bid * 0.85, DAILY_SALARY * (0.65 + 0.20 * pressure))
        else:
            target = max(DAILY_SALARY * (0.45 + 0.25 * pressure), avg_prev_bid * 0.75)

    # Never bid more than budget
    bid = min(budget, target)

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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # If we are already in bad shape, prioritize survival.
    if hp <= 2 or no_water_days >= 2:
        urgency = 0.88
    elif hp <= 4:
        urgency = 0.70
    else:
        urgency = 0.55

    # Use yesterday traces to infer aggressive bidding.
    alive_opps = []
    for k, o in opponents_status.items():
        try:
            if o.get('alive', False):
                alive_opps.append(o)
        except Exception:
            pass

    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # If others bid heavily, we bid just enough to compete rather than match max.
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If someone was bidding near max salary, treat as aggressive.
        aggressive = highest_prev_bid >= DAILY_SALARY * 0.85
    else:
        highest_prev_bid = 0.0
        aggressive = False

    # Supply pressure: with higher supply, we can bid less; with lower supply, bid more.
    # supply in [15,25]. Map to multiplier in [0.95..1.15].
    if MAX_SUPPLY > MIN_SUPPLY:
        t = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        t = 0.5
    t = max(0.0, min(1.0, float(t)))

    # Lower supply => higher multiplier
    supply_multiplier = 1.15 - 0.20 * t

    # Baseline bid target
    base = DAILY_SALARY * urgency * supply_multiplier

    # If aggressive, add a small premium rather than chasing their full level.
    if aggressive:
        premium = 0.12 * DAILY_SALARY
    else:
        premium = 0.05 * DAILY_SALARY

    target = base + premium

    # Hard caps to avoid bankruptcy.
    # Keep some budget buffer for later days.
    buffer = 0.10 * DAILY_SALARY
    max_affordable = max(0.0, budget - buffer)

    # If budget is low, spend what we can but still respect urgency.
    if budget <= 0.0:
        return 0.0

    # Also cap at a fraction of budget to reduce overbidding.
    budget_fraction = 0.95 if (hp <= 2 or no_water_days >= 2) else 0.60
    cap = budget_fraction * budget

    bid = min(target, max_affordable, cap)

    # Ensure bid is at least a small positive amount when we must compete.
    if (hp <= 4 or no_water_days >= 1) and bid < 1.0:
        bid = min(10.0, budget)

    return float(bid)
"""
