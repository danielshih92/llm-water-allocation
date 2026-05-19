# ============================================================
# Experiment: exp_105
# Agent: Bob
# Source: exp_105
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    budget = my_status.get('budget', 0.0)
    hp = my_status.get('hp', 0)

    alive_opps = []
    for opp_id, st in opponents_status.items():
        if st.get('alive', False):
            alive_opps.append((opp_id, st))

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday's bids (only immediate reaction)
    prev_bids = []
    for _, st in alive_opps:
        prev = st.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            prev_bids.append(b)

    # Base target: try to secure enough water for ourselves
    # If supply is around 15-25, a bid around our daily_salary*0.55 is typically competitive.
    base = DAILY_SALARY * 0.55

    # If opponents bid aggressively yesterday, increase slightly to avoid losing.
    if prev_bids:
        highest_prev = max(prev_bids)
        if highest_prev >= DAILY_SALARY * 0.85:
            # Only overcommit if my hp is healthy.
            if hp >= 4:
                base = DAILY_SALARY * 0.75
            else:
                base = DAILY_SALARY * 0.92
        elif highest_prev >= DAILY_SALARY * 0.65:
            base = max(base, highest_prev + 2.0)

    # If my hp is low, prioritize survival.
    if hp <= 2:
        base = max(base, DAILY_SALARY * 0.9)
    elif hp <= 3:
        base = max(base, DAILY_SALARY * 0.7)

    # If my budget is tight, cap aggressively.
    # Also avoid bidding above what I can afford.
    bid = min(budget, base)

    # Gentle adjustment based on supply scarcity.
    # Lower supply -> slightly higher bid to secure water.
    if supply <= 17.0:
        bid = min(budget, bid + 10.0)
    elif supply >= 22.0:
        bid = max(0.0, bid - 8.0)

    # Ensure non-negative
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

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Yesterday bids to infer opponent aggressiveness
    prev_bids = []
    prev_hp_after = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            prev_bids.append(float(b))
            prev_hp_after.append(float(prev.get('hp_after', 0.0)))

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    # Supply tightness: with supply near MIN_SUPPLY, winning water is more valuable.
    tight = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        tight = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    tight = max(0.0, min(1.0, tight))

    # Our urgency: if we've already gone without water, we must avoid death.
    urgency = 0.0
    if no_water_days >= 2:
        urgency = 1.0
    elif no_water_days == 1:
        urgency = 0.6
    else:
        urgency = 0.2

    # Baseline bid tries to be competitive but not wasteful.
    # If Cindy-like pressure existed (high highest_prev_bid), we undercut slightly unless we're urgent.
    # If pressure was low, we bid around a fraction of salary.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # High-pressure environment (likely Cindy bidding hard)
        if urgency >= 0.8 or hp <= 3.0:
            target = highest_prev_bid * (0.98)  # nearly match to secure water
        else:
            target = max(DAILY_SALARY * 0.45, highest_prev_bid * (0.78))
    else:
        # Moderate/low pressure
        target = max(DAILY_SALARY * (0.45 + 0.25 * tight), avg_prev_bid * 0.75)

    # Convert target into a safe cap based on our budget.
    # Also avoid bidding above what we'd reasonably spend per day.
    max_reasonable = DAILY_SALARY * (0.95 if urgency >= 0.8 else 0.65)
    target = min(target, max_reasonable)

    # If supply is extremely tight, increase slightly.
    if tight >= 0.75 and hp > 2.0 and urgency < 0.8:
        target *= 1.15

    # Ensure we always bid at least something meaningful if budget allows.
    min_bid = min(budget, DAILY_SALARY * 0.25)
    bid = max(min_bid, target)

    # Final safety clamp
    bid = max(0.0, min(budget, bid))
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

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opponents = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    if not alive_opponents:
        return float(min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids to infer aggressiveness.
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

    # Baseline: moderate bid to avoid Cindy's 150-style overbidding.
    # Supply 15..25: higher supply means we need less strategic pressure.
    # Aim to win when supply is tight, but don't chase extreme bids.
    supply_tightness = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)  # 0..1

    # If someone was extremely aggressive yesterday, slightly increase to ensure we don't get shut out.
    if highest_prev_bid >= 0.95 * 150.0:
        aggress_factor = 1.15
    elif highest_prev_bid >= 0.85 * 90.0:
        aggress_factor = 1.05
    else:
        aggress_factor = 1.0

    # If we are low on hp or have accumulated no-water days, we must secure water.
    if hp <= 2.0 or no_water_days >= 2:
        urgency = 1.25
    elif hp <= 4.0 or no_water_days == 1:
        urgency = 1.10
    else:
        urgency = 1.0

    # Target bid level: between ~0.45*salary and ~0.85*salary, scaled by urgency and tightness.
    target = DAILY_SALARY * (0.45 + 0.35 * supply_tightness) * aggress_factor * urgency

    # Hard cap: never bid near the extreme 150 unless we are in critical condition.
    critical = (hp <= 2.0 or no_water_days >= 2)
    if not critical:
        target = min(target, DAILY_SALARY * 0.85)
    else:
        target = min(target, DAILY_SALARY * 1.0)

    # Ensure we don't exceed budget.
    bid = float(min(budget, max(0.0, target)))

    # If budget is tiny, bid it all.
    if bid <= 0.0:
        return float(min(budget, DAILY_SALARY * 0.1))

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

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = float(my_status.get('no_water_days', 0.0))

    alive = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive.append(opp)

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace
    prev_bids = []
    for opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_prev_bid = 0.0
    if len(prev_bids) >= 2:
        sorted_b = sorted(prev_bids, reverse=True)
        second_prev_bid = sorted_b[1]

    # Pressure estimate: if someone previously bid very high, they likely value survival
    # Use that to slightly outbid, but cap by what we can afford.
    # Supply factor: higher supply reduces urgency to overbid.
    supply_ratio = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    if supply_ratio < 0.0:
        supply_ratio = 0.0
    if supply_ratio > 1.0:
        supply_ratio = 1.0

    urgency = 0.0
    if hp <= 2:
        urgency = 1.0
    elif hp <= 4:
        urgency = 0.7
    elif hp <= 7:
        urgency = 0.45
    else:
        urgency = 0.25

    # If we've already gone without water, urgency increases sharply.
    if no_water_days >= 2:
        urgency = min(1.0, urgency + 0.35)
    elif no_water_days >= 1:
        urgency = min(1.0, urgency + 0.15)

    # Base bid target
    # If highest_prev_bid suggests strong competition, aim near it; otherwise bid moderately.
    # Outbid by a small increment to win when needed.
    increment = 2.5

    # Determine target competition level
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Someone was willing to spend a lot; match/just-above highest to secure.
        target = highest_prev_bid + increment * (1.0 - supply_ratio)
    elif highest_prev_bid >= DAILY_SALARY * 0.55:
        # Medium competition: outbid around second-highest (or highest if only one)
        base = second_prev_bid if second_prev_bid > 0.0 else highest_prev_bid
        target = base + increment * (0.8 - 0.6 * supply_ratio) + 1.0
    else:
        # Low competition: bid based on urgency and supply
        target = DAILY_SALARY * (0.35 + 0.35 * urgency) * (0.9 - 0.25 * supply_ratio)

    # Adjust for supply: when supply is high, we can bid less; when low, bid more.
    # Convert supply to expected water units pressure: lower supply => more scarcity.
    scarcity = 1.0
    if MAX_SUPPLY > MIN_SUPPLY:
        scarcity = 1.0 - supply_ratio
    scarcity = max(0.0, min(1.0, scarcity))
    target = target * (0.85 + 0.3 * scarcity)

    # Ensure we don't bid above what we can afford.
    # Also, if budget is very low, bid whatever keeps us from wasting too much.
    if budget <= 0.0:
        return 0.0

    # Budget-aware cap: avoid committing entire budget unless urgency is extreme.
    if urgency >= 0.9:
        max_commit = budget
    else:
        max_commit = min(budget, DAILY_SALARY * (0.9 + 0.2 * urgency))

    bid = min(max_commit, target)

    # If hp is very low, ensure we bid at least a meaningful amount to avoid losing.
    if hp <= 2:
        min_bid = min(budget, DAILY_SALARY * 0.75)
        if bid < min_bid:
            bid = min_bid

    # Keep non-negative
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context['supply'])
    day = day_context['day']

    # Alive opponents
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    # If no opponents, bid just enough to keep water flow
    if not alive_opps:
        # Aim to buy roughly one unit of water per day
        target = DAILY_SALARY * 0.35
        return min(my_status['budget'], target)

    # Read yesterday bids for immediate reaction
    prev_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev['bid']))

    # Estimate how contested the market is
    avg_prev_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0
    max_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Supply pressure: lower supply means higher chance others outbid
    # Normalize supply into [0,1] where 0=MIN_SUPPLY, 1=MAX_SUPPLY
    denom = (MAX_SUPPLY - MIN_SUPPLY) if (MAX_SUPPLY - MIN_SUPPLY) != 0 else 1.0
    supply_norm = (supply - MIN_SUPPLY) / denom
    supply_norm = 0.0 if supply_norm < 0.0 else (1.0 if supply_norm > 1.0 else supply_norm)

    # Base bid: scale up when supply is scarce and when opponents previously bid high
    # Cindy died with avg ~69; treat ~70 as a threshold for aggressive competition.
    aggression = 0.0
    if max_prev_bid >= DAILY_SALARY * 0.85:
        aggression = 1.0
    elif max_prev_bid >= 70.0:
        aggression = 0.6
    elif avg_prev_bid >= 60.0:
        aggression = 0.4
    else:
        aggression = 0.25

    # HP and no-water days urgency
    hp = float(my_status['hp'])
    no_water_days = int(my_status['no_water_days'])

    # Urgency multiplier
    urgency = 1.0
    if hp <= 2:
        urgency = 1.35
    elif hp <= 4:
        urgency = 1.18
    if no_water_days >= 2:
        urgency += 0.15
    if no_water_days >= 3:
        urgency += 0.25

    # If supply is low, bid more; if high, bid less.
    scarcity_boost = 1.0 + (1.0 - supply_norm) * 0.55  # up to +55%

    # Day-based slight front-loading to secure early survival
    day_boost = 1.0
    if int(day) <= 3:
        day_boost = 1.08
    elif int(day) >= 8:
        day_boost = 1.02

    # Compute target bid
    # Aim around 0.45*DAILY_SALARY when calm; up to ~0.85*DAILY_SALARY when aggressive/scarce.
    calm_target = DAILY_SALARY * 0.45
    aggressive_target = DAILY_SALARY * 0.85
    blend = aggression
    base_target = calm_target * (1.0 - blend) + aggressive_target * blend

    target = base_target * scarcity_boost * urgency * day_boost

    # Budget cap
    budget = float(my_status['budget'])
    if budget <= 0:
        return 0.0

    # Avoid bidding so high that we risk running out before the end
    # Keep a reserve proportional to remaining days (episode length is 10)
    remaining = max(0, 10 - int(day))
    reserve = DAILY_SALARY * 0.2 * remaining
    max_affordable = max(0.0, budget - reserve)

    final_bid = min(budget, max_affordable, target)

    # Ensure minimum meaningful bid if we still need water
    if no_water_days >= 1 and final_bid < DAILY_SALARY * 0.25:
        final_bid = min(budget, DAILY_SALARY * 0.35)

    # Clamp to non-negative
    if final_bid < 0.0:
        final_bid = 0.0
    return float(final_bid)
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

    # Alive opponents
    alive_opps = []
    for k, o in opponents_status.items():
        if o.get('alive'):
            alive_opps.append(o)

    # If no opponents, bid modestly
    if not alive_opps:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday trace bids to infer aggressiveness
    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Supply pressure: tighter supply => need to secure water
    # Map supply in [15,25] to pressure in [1.0, 0.0]
    pressure = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    pressure = max(0.0, min(1.0, pressure))

    # Opponent aggressiveness: if they bid extremely high yesterday, they likely overspent.
    # We exploit by not matching their peak, but still respond when we are at risk.
    aggressive = 1.0 if highest_prev_bid >= DAILY_SALARY * 1.2 else 0.0

    # Base target bid: start below yesterday peak to avoid overspending
    # If supply is tight or we're at risk, move upward.
    risk = 0.0
    if hp <= 2.0:
        risk += 1.0
    if no_water_days >= 2:
        risk += 0.5
    if hp <= 4.0:
        risk += 0.4

    # Conservative anchor: around 0.55 salary when safe, higher when risky/tight.
    anchor = DAILY_SALARY * (0.45 + 0.25 * pressure + 0.35 * risk)

    # If yesterday bids were huge, reduce target to avoid repeating their mistake.
    # But if we are very risky, still pay enough to likely win.
    if aggressive > 0.0:
        anchor *= (0.78 + 0.22 * risk)

    # Also consider matching slightly above a fraction of the highest previous bid.
    # Use fraction rather than full to stay under their overspend.
    match_component = highest_prev_bid * (0.35 + 0.25 * pressure + 0.35 * risk)

    target = max(anchor, match_component)

    # Convert target into a bid cap based on budget and expected need.
    # Ensure we never bid more than we can afford.
    cap = budget

    # If budget is low, prioritize survival: bid a larger fraction of remaining budget.
    if budget <= DAILY_SALARY * 0.5:
        target = max(target, DAILY_SALARY * 0.6)

    # Final bid: clamp and keep non-negative
    bid = max(0.0, min(cap, target))

    # If we are extremely low HP, go near max affordable
    if hp <= 1.5:
        bid = max(bid, min(cap, DAILY_SALARY * 0.95))

    # If we are healthy and supply is abundant, bid lower
    if hp >= 7.0 and pressure <= 0.2 and risk <= 0.2:
        bid = min(bid, min(cap, DAILY_SALARY * 0.5))

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

    alive_opps = [o for o in opponents_status.values() if o.get('alive')]
    if not alive_opps:
        return max(0.0, min(float(my_status['budget']), DAILY_SALARY * 0.4))

    # Use only yesterday previous_trace to infer pressure
    yesterday_bids = []
    yesterday_hp_after = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(float(prev['bid']))
            yesterday_hp_after.append(prev.get('hp_after', None))

    my_budget = float(my_status['budget'])
    my_hp = float(my_status['hp'])

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    # Cindy-like behavior: survival implies she likely bid aggressively.
    # If someone bid very high yesterday, assume they will contest again.
    pressure = 0.0
    if highest_prev_bid >= 120.0:
        pressure = 1.0
    elif highest_prev_bid >= 60.0:
        pressure = 0.7
    elif highest_prev_bid >= 20.0:
        pressure = 0.4
    else:
        pressure = 0.2

    # Supply-based urgency: with lower supply, water is scarcer.
    # Map supply to a factor in [0.3, 1.0]
    if supply <= MIN_SUPPLY:
        supply_factor = 1.0
    elif supply >= MAX_SUPPLY:
        supply_factor = 0.3
    else:
        supply_factor = 1.0 - 0.7 * ((supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY))

    # Decide bid target.
    # If my hp is low, pay more to avoid death.
    # If my hp is high, still bid enough under pressure to avoid being outbid entirely.
    if my_hp <= 2.0:
        base = DAILY_SALARY * 0.95
    elif my_hp <= 4.0:
        base = DAILY_SALARY * (0.75 + 0.1 * pressure)
    else:
        base = DAILY_SALARY * (0.55 + 0.25 * pressure)

    target = base * (0.6 + 0.4 * supply_factor)

    # Additional adjustment: if highest_prev_bid was high, try to slightly exceed it.
    # But cap to not bankrupt.
    if highest_prev_bid > 0.0:
        target = max(target, highest_prev_bid * (0.92 + 0.08 * pressure))

    # Final clamp
    bid = min(my_budget, target)
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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append(o)

    if not alive_opponents:
        cap = DAILY_SALARY * 0.4
        return max(0.0, min(budget, cap))

    # Read yesterday bids from previous_trace only (immediate reaction)
    prev_bids = []
    for o in alive_opponents:
        prev = o.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    prev_bids.append(float(b))
                except Exception:
                    pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = sum(prev_bids) / float(len(prev_bids)) if prev_bids else 0.0

    # Determine pressure from opponent behavior
    # Cindy's pattern suggests some agents bid aggressively; Alex/Eric/David show punishment when budgets run out.
    pressure_level = 0.0
    if highest_prev_bid >= DAILY_SALARY * 1.7:  # ~153+
        pressure_level = 1.0
    elif highest_prev_bid >= DAILY_SALARY * 0.9:
        pressure_level = 0.7
    else:
        pressure_level = 0.4

    # Base target bid depends on hp and no_water_days
    if hp <= 2.0 or no_water_days >= 2:
        # Need to secure water now
        base = DAILY_SALARY * (0.85 + 0.1 * pressure_level)
    elif hp <= 4.0:
        base = DAILY_SALARY * (0.65 + 0.15 * pressure_level)
    else:
        base = DAILY_SALARY * (0.50 + 0.12 * pressure_level)

    # Scale with supply: lower supply -> bid more to compete
    if supply <= float(WATER_REQ):
        supply_factor = 1.15
    elif supply <= 18.0:
        supply_factor = 1.05
    else:
        supply_factor = 0.95

    target = base * supply_factor

    # If yesterday saw very high bids, slightly undercut to avoid budget death
    # but still stay near the competitive band.
    if highest_prev_bid > 0:
        # Competitive band midpoint: either chase avg or just below highest.
        band = max(avg_prev_bid, highest_prev_bid * 0.78)
        target = max(target, band * 0.95)

    # Final caps to avoid overspending
    # With water requirement 9 and supply range 15-25, winning often doesn't require extreme bids.
    max_cap = DAILY_SALARY * (1.25 if pressure_level >= 0.7 else 1.05)
    bid = min(budget, max_cap, target)

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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Alive opponents and yesterday bids
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # If no opponents alive, conserve
    if not alive_opps:
        return max(0.0, min(float(my_status['budget']), DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace
    yesterday_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Supply pressure: how many water units exist relative to our requirement
    # If supply is low (near 15), competition is tighter.
    supply_ratio = supply / float(WATER_REQ)  # e.g., 15/9=1.67, 25/9=2.78

    # Target bid baseline: aim to outbid likely low bidders but avoid Cindy's very high bids.
    # Use yesterday highest bid as signal: if it was huge, Cindy-like behavior exists.
    # We bid below that by a margin unless my hp is critical.
    critical_hp = 2.0
    very_low_hp = 1.0

    # Margin tuning
    if highest_prev_bid >= DAILY_SALARY * 1.4:  # ~126+ indicates Cindy-level aggression
        base = max(DAILY_SALARY * 0.65, highest_prev_bid * 0.75)
    elif highest_prev_bid >= DAILY_SALARY * 0.8:
        base = max(DAILY_SALARY * 0.55, highest_prev_bid * 0.85)
    else:
        base = max(DAILY_SALARY * 0.45, highest_prev_bid + 5.0)

    # Adjust for supply tightness: lower supply -> bid more
    if supply <= (MIN_SUPPLY + 1):
        base *= 1.08
    elif supply >= (MAX_SUPPLY - 1):
        base *= 0.95

    # Adjust for my health/budget risk
    if hp <= very_low_hp or no_water_days >= 2:
        # Need water; increase bid
        base *= 1.25
    elif hp <= critical_hp:
        base *= 1.12
    else:
        # Healthy: avoid overspending
        base *= 0.92

    # Keep within budget and avoid paying more than needed
    # Also cap to a fraction of budget to reduce risk if supply doesn't grant water.
    max_affordable = max(0.0, budget)
    desired = min(base, max_affordable)

    # If budget is small, bid aggressively up to budget.
    if max_affordable <= DAILY_SALARY * 0.6:
        return max(0.0, min(max_affordable, DAILY_SALARY * 0.9))

    # Final cap: don't bid above ~1.2*salary unless hp critical
    if hp > critical_hp:
        desired = min(desired, DAILY_SALARY * 1.2)
    else:
        desired = min(desired, DAILY_SALARY * 1.6)

    # Ensure non-negative
    if desired < 0.0:
        desired = 0.0
    return float(desired)
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

    # Alive opponents and their yesterday bids
    alive_opps = []
    for oid, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((oid, opp))

    yesterday_bids = []
    yesterday_hp_after = []
    for oid, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            yesterday_bids.append(float(b))
        hp_after = prev.get('hp_after', None)
        if hp_after is not None:
            yesterday_hp_after.append(float(hp_after))

    # Budget guard
    budget = float(my_status['budget'])
    hp = float(my_status['hp'])
    no_water_days = int(my_status['no_water_days'])

    # If we are in danger, we must secure water
    danger = (hp <= 2.0) or (no_water_days >= 2)

    # Estimate how many
"""
