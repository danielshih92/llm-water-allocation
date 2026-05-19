# ============================================================
# Experiment: exp_041
# Agent: Bob
# Source: exp_041
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
    day = day_context['day']

    # Alive opponents only
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append((opp_id, opp))

    # If no opponents, bid to ensure we can meet requirement
    if not alive_opps:
        target = min(my_status['budget'], DAILY_SALARY * 0.35)
        return max(0.0, float(target))

    # Read yesterday bids from previous_trace
    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # Baseline bid based on our health (hp) and budget
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    # Determine opponent pressure
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / float(len(yesterday_bids))

        # If someone overpaid yesterday, assume they were trying to lock supply.
        # Counter with a bid that is competitive but not maximal.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if hp > 3:
                bid = min(budget, DAILY_SALARY * 0.32)
            else:
                bid = min(budget, DAILY_SALARY * 0.75)
        elif highest_prev_bid >= DAILY_SALARY * 0.55:
            # Mid pressure: bid around the average plus a small premium
            bid = min(budget, max(DAILY_SALARY * 0.42, avg_prev_bid + 5.0))
        else:
            # Low pressure: bid enough to be near the likely clearing level
            bid = min(budget, max(DAILY_SALARY * 0.48, highest_prev_bid + 8.0))
    else:
        # No trace info: moderate bid
        if hp <= 2:
            bid = min(budget, DAILY_SALARY * 0.85)
        else:
            bid = min(budget, DAILY_SALARY * 0.55)

    # Supply-aware adjustment: if supply is scarce relative to our requirement, be more aggressive.
    # Supply range is [15,25], WATER_REQ=9. Use a simple scarcity factor.
    scarcity = 0.0
    if supply <= float(WATER_REQ):
        scarcity = 1.0
    else:
        # Normalize between 15..25 roughly
        denom = float(MAX_SUPPLY - MIN_SUPPLY)
        if denom > 0:
            scarcity = (float(MAX_SUPPLY) - supply) / denom
        scarcity = max(0.0, min(1.0, scarcity))

    # Increase bid when hp is low or supply is scarce
    if hp <= 2:
        bid = min(budget, bid + DAILY_SALARY * (0.25 + 0.25 * scarcity))
    elif hp <= 3:
        bid = min(budget, bid + DAILY_SALARY * (0.12 + 0.18 * scarcity))
    else:
        bid = min(budget, bid + DAILY_SALARY * (0.05 * scarcity))

    # Final cap: never exceed budget, never negative
    if bid < 0.0:
        bid = 0.0
    if bid > budget:
        bid = budget

    return float(bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
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

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        cap = my_budget
        bid = DAILY_SALARY * 0.35
        return min(cap, bid)

    # Use only yesterday's immediate trace
    prev_bids = []
    prev_hp_after = []
    prev_no_water = []
    for opp_id, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        if prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid', 0.0)))
            except Exception:
                pass
        if prev.get('hp_after') is not None:
            try:
                prev_hp_after.append(float(prev.get('hp_after', 0.0)))
            except Exception:
                pass
        if prev.get('status') is not None:
            # status may encode no-water; keep conservative
            pass
        prev_no_water.append(int(opp.get('no_water_days', 0)))

    # Estimate clearing pressure from yesterday
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        median_prev_bid = sorted(prev_bids)[len(prev_bids)//2]
    else:
        highest_prev_bid = 0.0
        median_prev_bid = DAILY_SALARY * 0.5

    # Supply-based aggressiveness: higher supply => can bid less
    # Convert supply to a rough water units factor
    units = supply / float(WATER_REQ)  # float
    # Normalize between MIN_SUPPLY and MAX_SUPPLY
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_factor = 0.5
    supply_factor = max(0.0, min(1.0, float(supply_factor)))

    # Base bid tuned to sit above typical strong bids but below extreme maxima
    # If others were spending heavily (highest_prev_bid near salary), we respond.
    pressure = 0.0
    if highest_prev_bid > 0:
        pressure = min(1.0, highest_prev_bid / (DAILY_SALARY * 1.2))

    # HP risk adjustment: if low HP or accumulating no-water days, bid more.
    hp_risk = 0.0
    if my_hp <= 2.0:
        hp_risk = 1.0
    elif my_hp <= 4.0:
        hp_risk = 0.6
    else:
        hp_risk = 0.2

    no_water_boost = 0.0
    if my_no_water_days >= 2:
        no_water_boost = 0.5
    elif my_no_water_days == 1:
        no_water_boost = 0.25

    # Decide aggressiveness level
    aggressiveness = 0.35 + 0.35 * pressure + 0.25 * hp_risk + no_water_boost
    aggressiveness = max(0.15, min(0.95, aggressiveness))

    # Target bid: slightly above median, scaled by aggressiveness, reduced if supply is high
    target = median_prev_bid * (0.85 + 0.3 * aggressiveness)

    # If highest_prev_bid is very high, ensure we don't undercut too much
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        target = max(target, DAILY_SALARY * (0.45 + 0.35 * aggressiveness))

    # Reduce when supply is abundant
    target = target * (0.85 + 0.3 * (1.0 - supply_factor))

    # Final cap by budget
    if my_budget <= 0:
        return 0.0

    # Keep some budget for future: don't spend more than a fraction unless in critical HP
    spend_cap_frac = 0.25
    if my_hp <= 2.0:
        spend_cap_frac = 0.9
    elif my_hp <= 4.0:
        spend_cap_frac = 0.55
    elif my_no_water_days >= 2:
        spend_cap_frac = 0.6

    max_bid = my_budget * spend_cap_frac
    bid = min(max_bid, target)

    # Ensure bid is non-negative
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

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    # Alive opponents only
    alive_ids = []
    for agent_id, st in opponents_status.items():
        if st.get('alive', False):
            alive_ids.append(agent_id)

    # If no opponents alive, conserve
    if not alive_ids:
        return min(float(my_status['budget']), DAILY_SALARY * 0.4)

    # Extract yesterday bids from previous_trace for immediate reaction
    prev_bids = []
    prev_hp_after = {}
    for agent_id in alive_ids:
        prev = opponents_status[agent_id].get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev['bid']))
            prev_hp_after[agent_id] = prev.get('hp_after', None)

    # Identify likely pressure leader: highest yesterday bid
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Also check if Cindy was the main survivor with high budget
    cindy_prev_bid = None
    if 'Cindy' in opponents_status and opponents_status['Cindy'].get('alive', False):
        prev = opponents_status['Cindy'].get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            cindy_prev_bid = float(prev['bid'])

    # Supply pressure: more supply means we can bid less to still secure water
    # Normalize supply to [0,1]
    if MAX_SUPPLY == MIN_SUPPLY:
        supply_norm = 0.5
    else:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
        if supply_norm < 0.0:
            supply_norm = 0.0
        if supply_norm > 1.0:
            supply_norm = 1.0

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Urgency: if we are already in no-water streak or low hp, we must secure water
    urgency = 0.0
    if my_hp <= 2.0:
        urgency += 1.0
    if no_water_days >= 1:
        urgency += 0.6
    if no_water_days >= 2:
        urgency += 0.6
    if my_hp <= 3.0:
        urgency += 0.4

    # Target bid baseline based on yesterday leader
    # If Cindy likely sets the pace (~85), we match slightly below/around it depending on urgency.
    leader_bid = highest_prev_bid
    if cindy_prev_bid is not None:
        # Prefer Cindy if she was strong survivor yesterday
        leader_bid = max(leader_bid, cindy_prev_bid)

    # Convert leader bid into a competitive bid
    # - If leader was very high, we raise only when urgency is high.
    # - Otherwise, we try to undercut to save budget.
    if leader_bid >= DAILY_SALARY * 0.85:
        if urgency >= 1.2:
            target = leader_bid * 0.98  # almost match
        elif urgency >= 0.6:
            target = leader_bid * 0.88  # likely enough
        else:
            target = leader_bid * 0.72  # conserve
    else:
        if urgency >= 1.2:
            target = max(DAILY_SALARY * 0.55, leader_bid + 5.0)
        elif urgency >= 0.6:
            target = max(DAILY_SALARY * 0.45, leader_bid + 2.5)
        else:
            target = max(DAILY_SALARY * 0.35, leader_bid * 0.75)

    # Adjust for supply: with higher supply, reduce bid; with lower supply, increase slightly
    # supply_norm high => cheaper
    target *= (1.10 - 0.25 * supply_norm)

    # Cap bid to avoid bankruptcy; also ensure not exceeding budget
    # If budget is low, bid more aggressively relative to remaining budget.
    if my_budget <= DAILY_SALARY * 0.6:
        budget_pressure = 1.0
    elif my_budget <= DAILY_SALARY * 1.2:
        budget_pressure = 0.8
    else:
        budget_pressure = 0.65

    target *= budget_pressure

    # Final clamp
    if target < 0.0:
        target = 0.0
    if target > my_budget:
        target = my_budget

    # If urgency is extreme, ensure a minimum competitive bid
    if urgency >= 1.2:
        min_competitive = DAILY_SALARY * 0.75
        if target < min_competitive:
            target = min(min_competitive, my_budget)

    # If we are doing fine, keep bids moderate
    if my_hp >= 6.0 and urgency < 0.6:
        target = min(target, DAILY_SALARY * 0.55)

    return float(target)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Identify alive opponents and extract yesterday bids
    alive_opps = []
    for opp_id, st in opponents_status.items():
        if st.get('alive', False):
            alive_opps.append((opp_id, st))

    yesterday_bids = []
    for _, st in alive_opps:
        prev = st.get('previous_trace', {}) or {}
        if prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # Baseline bid: aim to beat the lower bidder (Eric-like) but not match the top bidders (Alex/Cindy-like)
    # Use yesterday median/max as a proxy for the current competitive intensity.
    if yesterday_bids:
        sorted_b = sorted(yesterday_bids)
        median_bid = sorted_b[len(sorted_b)//2]
        max_bid = max(sorted_b)
        # Target slightly above median to gain share, but cap below max to avoid overpaying
        target = median_bid + 3.0
        cap = max_bid - 5.0
        if cap < 0:
            cap = DAILY_SALARY * 0.7
        base_bid = min(target, cap)
    else:
        base_bid = DAILY_SALARY * 0.55

    # HP-aware adjustment: if low HP, bid more aggressively; if healthy, conserve budget.
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Estimate remaining days risk: if already accumulating no-water days, increase bid.
    risk = 0
    if no_water_days >= 2:
        risk = 1
    if hp <= 2:
        risk = 2

    if risk == 2:
        mult = 0.95
    elif risk == 1:
        mult = 0.75
    else:
        mult = 0.60 if hp >= 7 else 0.70

    # Also consider supply: if supply is scarce relative to our need, increase bid.
    # supply is within [15,25], so scale modestly.
    if supply <= 16.0:
        supply_mult = 1.10
    elif supply >= 24.0:
        supply_mult = 0.90
    else:
        supply_mult = 1.00

    bid = base_bid * mult * supply_mult

    # Ensure we don't bid more than budget and keep within reasonable bounds.
    # Use a soft upper bound to avoid getting trapped in the Alex/Cindy bidding band.
    soft_upper = min(budget, DAILY_SALARY * 0.85)
    bid = min(bid, soft_upper)

    # If budget is very low, still bid something to avoid immediate elimination.
    if budget <= 5.0:
        return max(0.0, budget)

    # Final clamp
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
    day = int(day_context['day'])

    # Identify alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # If no one alive, conserve budget
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace only
    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Competition estimate
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = (sum(yesterday_bids) / len(yesterday_bids)) if yesterday_bids else 0.0

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status.get('no_water_days', 0))

    # Base bid depends on my urgency
    if hp <= 2.0 or no_water_days >= 2:
        urgency = 1.0
    elif hp <= 4.0:
        urgency = 0.75
    else:
        urgency = 0.5

    # Supply pressure: higher supply lowers need to outbid
    # Use a simple normalized factor
    supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_factor = max(0.0, min(1.0, supply_factor))

    # If opponents were bidding very high yesterday, slightly increase to avoid being starved
    # (but don't match their extremes unless I'm in danger)
    if highest_prev_bid >= DAILY_SALARY * 1.35:  # ~121.5
        competition = 1.0
    elif highest_prev_bid >= DAILY_SALARY * 0.95:  # ~85.5
        competition = 0.8
    else:
        competition = 0.6

    # Target bid construction
    # Keep bid generally below the leaders unless my hp is critical.
    # Use a small increment over a fraction of yesterday's highest.
    base = DAILY_SALARY * (0.35 + 0.35 * urgency)  # between ~0.525 and ~0.7 of DAILY_SALARY
    adjust = competition * (highest_prev_bid * (0.25 if urgency < 1.0 else 0.4))

    # If supply is high, reduce bid; if low, increase slightly
    bid = base + adjust
    bid = bid * (0.85 + 0.3 * (1.0 - supply_factor))

    # Critical cap: never exceed what I can spend
    bid = min(bid, budget)

    # Ensure bid is at least enough to be competitive when very low hp
    if hp <= 2.0 or no_water_days >= 2:
        floor_bid = min(budget, DAILY_SALARY * 0.9)
        bid = max(bid, floor_bid)
    else:
        # Otherwise keep a modest floor to avoid total starvation
        floor_bid = min(budget, DAILY_SALARY * 0.45)
        bid = max(bid, floor_bid * (0.6 + 0.4 * competition))

    # Final clamp to non-negative
    if bid < 0.0:
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

    # Basic safety/urgency
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Determine how many full water units supply can cover (use int indexing safeguard)
    # This is mainly to scale our bid aggressiveness.
    max_units = int(supply // float(WATER_REQ)) if WATER_REQ > 0 else 0

    alive = [o for o in opponents_status.values() if o.get('alive')]
    if not alive:
        return min(budget, DAILY_SALARY * 0.4)

    # Yesterday bids: immediate reaction only
    prev_bids = []
    for o in alive:
        prev = o.get('previous_trace', {}) or {}
        if prev.get('bid') is not None:
            prev_bids.append(float(prev['bid']))

    # Estimate opponent pressure from yesterday
    if prev_bids:
        top_bid = max(prev_bids)
        second_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else top_bid
        median_bid = sorted(prev_bids)[len(prev_bids)//2]
    else:
        top_bid = median_bid = second_bid = DAILY_SALARY * 0.5

    # If we are close to losing, bid high; otherwise stay near a competitive but not maximal level.
    # Heuristic: convert no_water_days to urgency.
    # When no_water_days is 0..2 we can be moderate; when >=3 we get aggressive.
    urgency = 0
    if no_water_days >= 3:
        urgency = 2
    elif no_water_days >= 2:
        urgency = 1

    # Also increase urgency if hp is low.
    if hp <= 2:
        urgency = max(urgency, 2)
    elif hp <= 4:
        urgency = max(urgency, 1)

    # Supply scarcity: lower supply implies stronger competition.
    scarcity = 0
    if supply <= (MIN_SUPPLY + 1):
        scarcity = 2
    elif supply <= (MIN_SUPPLY + 5):
        scarcity = 1

    # Decide target bid relative to observed opponent top bids.
    # We try to beat the likely leader only when competition is likely.
    # Use a small increment to reduce tie risk.
    if max_units <= 1:
        # Very scarce: compete near top
        if urgency >= 2 or top_bid >= DAILY_SALARY * 0.85:
            target = min(budget, top_bid + 3.0)
        else:
            target = min(budget, max(median_bid, second_bid + 2.0))
    else:
        # Less scarce: moderate bids unless urgent
        if urgency >= 2:
            target = min(budget, max(top_bid * 0.9, median_bid + 10.0))
        elif urgency >= 1:
            target = min(budget, max(median_bid, second_bid + 5.0))
        else:
            # Conservative: steal water if others overbid; otherwise preserve budget
            # Eric died yesterday, David bid low; so we can undercut slightly below median.
            target = min(budget, max(DAILY_SALARY * 0.45, median_bid * 0.75))

    # Ensure non-negative
    if target < 0:
        target = 0.0

    # Cap by budget
    if target > budget:
        target = budget

    return float(target)
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
    day = day_context.get('day', 0)

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return float(min(my_budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from immediate trace only
    prev_bids = []
    prev_by_id = {}
    for opp_id, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                bid_f = float(bid)
            except Exception:
                continue
            prev_bids.append(bid_f)
            prev_by_id[opp_id] = bid_f

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # If Cindy was aggressive yesterday, assume she will pressure again.
    cindy_prev = prev_by_id.get('Cindy', None)
    cindy_pressure = float(cindy_prev) if cindy_prev is not None else 0.0

    # Determine how many water units are feasible/needed today.
    # Bids are in budget units, but we use supply to decide how hard to compete.
    # Expected water per unit is 1, so 1 unit corresponds to meeting WATER_REQ.
    # We'll translate supply urgency into a bid aggressiveness level.
    supply_ratio = 0.0
    if MAX_SUPPLY > 0:
        supply_ratio = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Base bid target: aim to secure water when supply is tighter and when my HP/no-water is risky.
    # If my HP is low or I've already had no water days, bid harder.
    hp_risk = 0.0
    if my_hp <= 1:
        hp_risk = 1.0
    elif my_hp <= 3:
        hp_risk = 0.7
    elif my_hp <= 5:
        hp_risk = 0.4
    else:
        hp_risk = 0.2

    no_water_risk = 0.0
    if my_no_water_days >= 2:
        no_water_risk = 1.0
    elif my_no_water_days == 1:
        no_water_risk = 0.5
    else:
        no_water_risk = 0.1

    # Aggression from yesterday pressure
    pressure_risk = 0.0
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        pressure_risk = 1.0
    elif highest_prev_bid >= DAILY_SALARY * 0.6:
        pressure_risk = 0.7
    elif highest_prev_bid >= DAILY_SALARY * 0.35:
        pressure_risk = 0.4
    else:
        pressure_risk = 0.2

    # If Cindy specifically pressured yesterday, increase slightly.
    if cindy_pressure >= DAILY_SALARY * 0.8:
        pressure_risk = min(1.0, pressure_risk + 0.2)

    # Tight supply => bid more. supply_ratio low => tighter.
    tightness = 1.0 - supply_ratio

    # Compute target bid as a fraction of DAILY_SALARY, then clamp by budget.
    # Not going to max-out; we only need enough to beat likely bids.
    frac = 0.35 + 0.35 * hp_risk + 0.25 * no_water_risk + 0.25 * pressure_risk + 0.25 * tightness
    frac = max(0.25, min(0.95, frac))

    # If my HP is healthy and yesterday pressure was low, stay conservative.
    if my_hp >= 7 and highest_prev_bid < DAILY_SALARY * 0.4:
        frac = min(frac, 0.55)

    bid = DAILY_SALARY * frac

    # If Cindy bid very high yesterday, try to slightly over her while still not maxing.
    if cindy_pressure > 0:
        bid = max(bid, cindy_pressure * 0.98)

    # Final clamp to budget and a reasonable upper bound.
    bid = float(min(my_budget, bid))
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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    my_hp = float(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    if not alive:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # React to yesterday's immediate pressure: use max bid among alive opponents yesterday.
    prev_bids = []
    for oid, o in alive:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            prev_bids.append(float(b))

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate how many full water units supply can cover (1 unit == WATER_REQ water).
    # Use int() indices only; here we just compute a float ratio.
    units = supply / float(WATER_REQ) if WATER_REQ > 0 else 0.0

    # Baseline aggressiveness by supply regime.
    if supply >= 21.0:
        base = DAILY_SALARY * 0.65
    elif supply >= 17.0:
        base = DAILY_SALARY * 0.75
    else:
        base = DAILY_SALARY * 0.85

    # If someone previously bid very high, we must overtake to secure water.
    # Cindy averaged ~127 and survived; treat that as a threshold.
    if highest_prev_bid >= DAILY_SALARY * 1.25:
        target = highest_prev_bid + 5.0
    elif highest_prev_bid >= DAILY_SALARY * 0.95:
        target = max(base, highest_prev_bid + 2.0)
    else:
        target = base

    # Urgency adjustments.
    # If we have been dry, increase bid sharply.
    if my_no_water_days >= 2:
        target *= 1.25
    if my_hp <= 2:
        target *= 1.35

    # Budget safety: never bid above what we can afford.
    target = float(target)
    bid = min(my_budget, target)

    # If budget is low, still bid enough to try to prevent further no-water days.
    if bid < DAILY_SALARY * 0.25 and my_hp > 2:
        bid = min(my_budget, DAILY_SALARY * 0.3)

    # Clamp non-negative.
    if bid < 0.0:
        bid = 0.0

    return bid
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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))

    alive = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive.append(opp)

    if not alive:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Immediate reaction to yesterday's bids
    yesterday_bids = []
    for opp in alive:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict) and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how many full water units might exist; use this to scale bid
    # Index safety: not using lists, but keep int casts where needed.
    # If supply is tight (<= WATER_REQ), bidding must be stronger.
    tight = supply <= float(WATER_REQ) + 0.5

    # Baseline bid: enough to compete but not chase max.
    # If our HP is critical, we bid higher.
    if my_hp <= 2.0:
        base = DAILY_SALARY * (0.85 if tight else 0.75)
    elif my_hp <= 4.0:
        base = DAILY_SALARY * (0.65 if tight else 0.55)
    else:
        base = DAILY_SALARY * (0.55 if tight else 0.45)

    # If yesterday pressure was high, slightly undercut rather than mirror.
    # If pressure was low, raise toward baseline to secure.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # High bids likely indicate scarcity/strong competition; bid moderately.
        bid = min(base * 0.95 + 0.15 * highest_prev_bid, DAILY_SALARY * 0.8)
    elif highest_prev_bid >= DAILY_SALARY * 0.55:
        bid = min(base * 1.0 + 0.05 * highest_prev_bid, DAILY_SALARY * 0.7)
    else:
        # Low competition: bid close to baseline.
        bid = base

    # Cap by budget and non-negative
    bid = max(0.0, min(float(my_budget), float(bid)))

    # Small deterministic adjustment by day to avoid ties
    # (still budget-safe)
    tie_break = (day % 3) * 0.5
    bid = min(float(my_budget), bid + tie_break)

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
    day = int(day_context.get('day', 1))

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append(o)

    if not alive:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Read yesterday's immediate behavior
    prev_bids = []
    prev_by_agent = {}
    for o in alive:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                b_val = float(b)
                prev_bids.append(b_val)
                prev_by_agent[o.get('agent_id', '')] = b_val
            except Exception:
                pass

    # Estimate how aggressive the field was
    if prev_bids:
        highest_prev = max(prev_bids)
        second_prev = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev
    else:
        highest_prev = 0.0
        second_prev = 0.0

    # Determine today's urgency from supply and my hp
    # Higher supply reduces urgency; low supply increases urgency.
    supply_norm = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_norm = max(0.0, min(1.0, supply_norm))

    # If I'm in danger, bid to secure at least one allocation.
    danger = 0
    if my_hp <= 2.0:
        danger = 2
    elif my_hp <= 4.0:
        danger = 1
    if my_no_water_days >= 2:
        danger += 1

    # Target bid logic:
    # - If Cindy-like high bid existed yesterday (highest_prev high), try to slightly undercut/beat with a small premium.
    # - Otherwise bid moderately.
    base = DAILY_SALARY * (0.35 + 0.25 * supply_norm)  # 0.35..0.60 of salary

    # When opponent pressure was high, match it with a controlled increment.
    if highest_prev >= DAILY_SALARY * 0.85:
        # Bid just above the second-highest to win without paying the absolute highest.
        target = max(base, second_prev + 2.0)
        # If I'm safe, don't overpay.
        if danger == 0:
            target = min(target, highest_prev - 1.0)
        else:
            target = min(highest_prev + 1.0, target + 3.0)
    elif highest_prev >= DAILY_SALARY * 0.55:
        # Moderate pressure: bid around base but slightly above highest_prev if needed.
        target = max(base, highest_prev * 0.95)
        if danger >= 1:
            target = max(target, highest_prev + 1.5)
    else:
        # Low pressure: conserve.
        target = base
        if danger >= 2:
            target = max(target, DAILY_SALARY * 0.75)

    # Convert to feasible bid given budget
    # Also keep within a reasonable range to avoid bankruptcy.
    floor_bid = 1.0
    cap = my_budget
    if cap <= 0.0:
        return 0.0

    # If supply is extremely low, increase urgency.
    if supply < float(WATER_REQ) + 1.0:
        target = max(target, DAILY_SALARY * 0.7)

    bid = max(floor_bid, min(cap, target))
    return float(bid)
"""
