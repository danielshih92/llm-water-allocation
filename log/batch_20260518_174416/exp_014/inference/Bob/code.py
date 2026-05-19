# ============================================================
# Experiment: exp_014
# Agent: Bob
# Source: exp_014
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

    supply = day_context['supply']
    day = day_context['day']

    # Basic safety
    if my_status['budget'] <= 0:
        return 0

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    # If no opponents, bid to secure requirement efficiently
    if not alive_opponents:
        target = WATER_REQ * 1.0
        # Convert a target quantity to a reasonable price proxy
        # (game likely uses bid as price; we cap by budget and salary)
        return int(min(my_status['budget'], DAILY_SALARY * 0.6))

    # Look only at yesterday's immediate behavior
    yesterday_bids = []
    yesterday_high_pressure = []
    for opp_id, opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev:
            b = prev.get('bid', None)
            if b is not None:
                try:
                    yesterday_bids.append(float(b))
                except Exception:
                    pass
                # Mark if they were very aggressive
                try:
                    if float(b) >= DAILY_SALARY * 0.85:
                        yesterday_high_pressure.append(float(b))
                except Exception:
                    pass

    # Determine aggressiveness level
    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / float(len(yesterday_bids))
    else:
        max_prev_bid = 0.0
        avg_prev_bid = 0.0

    # My risk adjustment
    hp = my_status.get('hp', 0)
    no_water_days = my_status.get('no_water_days', 0)
    budget = my_status.get('budget', 0)

    # If I'm in danger, bid harder to avoid accumulating no-water days
    danger_multiplier = 1.0
    if hp <= 2:
        danger_multiplier = 1.15
    elif hp <= 3:
        danger_multiplier = 1.07

    # If I have already been without water, increase urgency
    if no_water_days >= 2:
        danger_multiplier *= 1.12

    # Supply-aware shading: lower supply => more competitive bidding
    # Normalize supply to [0,1] between MIN_SUPPLY and MAX_SUPPLY
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (float(supply) - float(MIN_SUPPLY)) / float(MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_norm = 0.5
    supply_competition = 1.0 + (1.0 - supply_norm) * 0.35  # more when supply is low

    # Aggression response to yesterday
    if yesterday_high_pressure:
        # Shade slightly below the maximum aggressive bid to control cost
        base = max_prev_bid * 0.93
        # Ensure we still bid meaningfully
        floor_bid = DAILY_SALARY * 0.35
        bid = max(base, floor_bid)
    else:
        # If they were not aggressive, bid around average plus a small premium
        # but keep it conservative to preserve budget.
        bid = max(DAILY_SALARY * 0.45, avg_prev_bid * 0.85 + DAILY_SALARY * 0.08)

    bid *= danger_multiplier
    bid *= supply_competition

    # Never exceed budget
    bid = min(float(budget), bid)

    # If low budget, scale down
    if budget < DAILY_SALARY * 0.6:
        bid *= 0.85

    # Convert to integer bid
    bid_int = int(bid)
    if bid_int < 0:
        bid_int = 0
    return bid_int
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opps:
        # If no opponents, spend enough to cover our requirement.
        return min(budget, DAILY_SALARY * 0.35)

    # Read yesterday bids from previous_trace only (immediate reaction)
    prev_bids = []
    prev_hp_after = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid', 0.0)))
            except Exception:
                pass
        if prev and prev.get('hp_after') is not None:
            try:
                prev_hp_after.append(float(prev.get('hp_after', 0.0)))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    # If someone was bidding extremely high yesterday, we assume strong competition.
    extreme_competition = highest_prev_bid >= (DAILY_SALARY * 0.85)

    # If we are already in danger (low hp / many no-water days), increase urgency.
    urgent = (hp <= 2.5) or (no_water_days >= 2)

    # Base bid scales with supply: lower supply increases competitive need.
    # Map supply in [15,25] to a multiplier in [1.05, 0.85]
    if MAX_SUPPLY != MIN_SUPPLY:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_norm = 0.5
    supply_multiplier = 1.05 - 0.20 * supply_norm  # 15->1.05, 25->0.85

    # Strategy:
    # - If extreme competition: bid enough to avoid losing, but not full send unless we are urgent.
    # - If not extreme: bid moderately and conserve budget.
    if extreme_competition:
        if urgent:
            target = DAILY_SALARY * 0.95
        else:
            target = max(highest_prev_bid * 0.55, DAILY_SALARY * 0.45)
    else:
        if urgent:
            target = DAILY_SALARY * 0.75
        else:
            # Slightly undercut expected winner pressure.
            target = max(DAILY_SALARY * 0.40, highest_prev_bid * 0.35)

    target *= supply_multiplier

    # Cap by budget and ensure non-negative
    if budget <= 0:
        return 0.0
    bid = min(budget, max(0.0, target))

    # Additional safeguard: if our hp is very low, go aggressive near end of episode.
    if day >= 8 and hp <= 3.0:
        bid = min(budget, max(bid, DAILY_SALARY * 0.85))

    return float(bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    my_hp = float(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return float(min(my_budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids for immediate reaction
    yesterday_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Estimate how many water units might be needed this day
    # (We assume 1 unit per WATER_REQ supply segment; use it only to scale aggressiveness.)
    # Ensure indices are safe: we don't index lists, but keep computations float-safe.
    expected_units = supply / float(WATER_REQ) if WATER_REQ > 0 else 0.0

    # Base bid: aim around a fraction of daily salary to avoid Cindy-style overbids.
    # Increase if we're under pressure (low hp or many no-water days).
    pressure = 0
    if my_hp <= 2:
        pressure += 2
    elif my_hp <= 4:
        pressure += 1
    if my_no_water_days >= 2:
        pressure += 1

    # If yesterday saw very high bids, undercut them to avoid price wars.
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid

        # Detect Cindy-like aggressive environment
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # Undercut: target slightly below highest, but not too low.
            target = 0.58 * highest_prev_bid + 0.22 * second_prev_bid
            # Add pressure adjustment
            target *= (1.0 + 0.18 * pressure)
        else:
            # More moderate market; bid near the upper-middle of yesterday bids
            target = 0.55 * highest_prev_bid + 0.35 * (second_prev_bid)
            target *= (1.0 + 0.12 * pressure)
    else:
        target = DAILY_SALARY * 0.55 * (1.0 + 0.12 * pressure)

    # Scale with expected supply pressure: if supply is low, bid a bit more.
    # supply range is [15,25], so normalize.
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (float(supply) - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_norm = 0.5
    # Lower supply -> higher bid
    target *= (1.10 - 0.20 * supply_norm)

    # Hard caps: never exceed budget; also avoid wasting beyond a fraction of budget when hp is okay.
    # If hp is very low, allow spending more.
    if my_hp <= 2:
        budget_cap = my_budget * 0.95
    elif my_hp <= 4:
        budget_cap = my_budget * 0.80
    else:
        budget_cap = my_budget * 0.65

    # Also avoid bidding above a reasonable ceiling relative to daily salary.
    ceiling = DAILY_SALARY * (1.10 + 0.25 * pressure)

    bid = float(min(budget_cap, ceiling, target))

    # Ensure non-negative
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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Identify alive opponents and their yesterday bids
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp_id)

    # If no opponents alive, bid conservatively
    if not alive_opps:
        bid = min(budget, DAILY_SALARY * 0.4)
        return float(max(0.0, bid))

    yesterday_bids = []
    for opp_id in alive_opps:
        prev = opponents_status[opp_id].get('previous_trace', None)
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    yesterday_bids.append(float(b))
                except Exception:
                    pass
        elif isinstance(prev, list):
            # Not expected per spec, but ignore gracefully
            for item in prev[-1:]:
                if isinstance(item, dict) and item.get('bid') is not None:
                    try:
                        yesterday_bids.append(float(item.get('bid')))
                    except Exception:
                        pass

    # Use yesterday's max bid as pressure signal
    pressure = 0.0
    if yesterday_bids:
        pressure = max(yesterday_bids)

    # Supply-based aggressiveness: lower supply => higher bid to secure water
    # Normalize supply to [0,1]
    if MAX_SUPPLY == MIN_SUPPLY:
        supply_norm = 0.5
    else:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_norm = max(0.0, min(1.0, float(supply_norm)))

    # My urgency: low hp or many no-water days => bid more
    urgency = 0.0
    if hp <= 2:
        urgency = 1.0
    elif hp <= 4:
        urgency = 0.7
    elif hp <= 6:
        urgency = 0.4
    else:
        urgency = 0.25

    if no_water_days >= 2:
        urgency = min(1.0, urgency + 0.25)

    # Target bid strategy:
    # Cindy/Eric used ~120-130; we don't match that fully, but we bid mid-high.
    # If yesterday pressure was very high, we slightly increase our bid to contest.
    base = DAILY_SALARY * (0.45 + 0.25 * (1.0 - supply_norm))  # 0.45..0.70 of salary
    pressure_boost = 0.0
    if pressure >= DAILY_SALARY * 1.2:
        pressure_boost = DAILY_SALARY * 0.12
    elif pressure >= DAILY_SALARY * 0.9:
        pressure_boost = DAILY_SALARY * 0.07

    bid_target = base + pressure_boost
    bid_target = bid_target * (0.65 + 0.55 * urgency)  # scale by urgency

    # If we are very low on budget, cap harder
    # Ensure we never bid above budget
    bid_cap = budget

    # Also avoid extreme bids beyond what would be rational given supply scarcity
    # (Still allow high bids if urgency is extreme)
    extreme_cap = DAILY_SALARY * 1.2 + max(0.0, (budget - DAILY_SALARY * 0.5)) * 0.2
    bid_cap = min(bid_cap, extreme_cap)

    bid = min(bid_target, bid_cap)

    # If bid becomes too small while urgent, raise to a minimum contest threshold
    min_contest = DAILY_SALARY * (0.35 + 0.25 * (1.0 - supply_norm))
    if urgency >= 0.7 and bid < min_contest:
        bid = min(budget, min_contest)

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
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    # If no one else is alive, conserve budget
    if not alive:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from traces for immediate pressure
    yesterday_bids = []
    for _, o in alive:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    # Cindy was the strongest survivor with highest avg bid; use highest_prev_bid as proxy.

    # Estimate scarcity: how many units of our water requirement fit in supply.
    # If supply is near MIN_SUPPLY, competition is higher.
    scarcity_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    # scarcity_ratio near 0 => tight supply

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    # Base bid target: mid-high to beat moderate bidders, but not match Cindy unless needed.
    # Use HP to decide urgency: low HP -> bid aggressively.
    tight = scarcity_ratio < 0.35

    # If Cindy-like pressure exists (high previous bid), we should respond but not always fully.
    # Threshold tuned from trace: Cindy's max/avg ~138.
    if highest_prev_bid >= DAILY_SALARY * 1.2:  # >=108
        if hp <= 3:
            target = DAILY_SALARY * (0.95 if tight else 0.8)
        else:
            target = DAILY_SALARY * (0.7 if tight else 0.55)
        # Slightly undercut the leader to reduce waste
        # (We can't know current bids, so we cap by leader proxy)
        target = min(target, highest_prev_bid - 5.0)
    else:
        # Less aggressive field; bid enough to secure when tight.
        if hp <= 3:
            target = DAILY_SALARY * (0.85 if tight else 0.75)
        else:
            target = DAILY_SALARY * (0.6 if tight else 0.5)

    # Ensure we don't bid more than budget and keep within reasonable range.
    bid = float(min(budget, max(0.0, target)))

    # If budget is extremely low, bid what we can.
    if budget <= 1.0:
        return float(budget)

    # Small day-based adjustment to avoid ties when supply is tight.
    if tight:
        bid = bid + (1.0 if (day % 2 == 0) else 0.5)

    # Final clamp
    bid = float(min(budget, max(0.0, bid)))
    return bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context['supply'])
    day = day_context['day']

    # Determine alive opponents and their yesterday bids
    alive_opponents = []
    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(float(prev.get('bid', 0.0)))

    # If no opponents, just bid enough to secure water
    if not alive_opponents:
        need = max(0.0, DAILY_SALARY * 0.4)
        return min(float(my_status['budget']), need)

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Estimate how aggressive the field was yesterday
    max_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    # Supply pressure: higher supply generally reduces need to overbid
    # supply in [15,25] => water units possible: 1 or 2
    water_units = int(supply // WATER_REQ)  # safe: int()
    if water_units < 1:
        water_units = 1

    # If supply allows 2 units (>=18), we can afford a lower bid
    two_unit_supply = supply >= (2 * WATER_REQ)

    # Core strategy: bid moderate under normal hp, escalate only when hp is low or supply is tight.
    # Also, if yesterday max bids were extremely high, avoid mirroring them.
    # Use a cap based on budget.
    budget_cap = my_budget

    # Target bid levels tuned to not match Cindy/Eric's ~140-150 unless I must.
    # Base bid attempts to secure at least some chance without wasting money.
    if two_unit_supply:
        base = DAILY_SALARY * 0.45
    else:
        base = DAILY_SALARY * 0.60

    # Escalation rules
    if my_hp <= 2.0 or no_water_days >= 2:
        # Near death: bid more aggressively, but still below yesterday's max to avoid waste.
        base = DAILY_SALARY * 0.85
    elif my_hp <= 4.0:
        base = DAILY_SALARY * 0.70

    # If opponents were not that aggressive yesterday (lower max), we can bid slightly less.
    if max_prev_bid < DAILY_SALARY * 0.9:
        base *= 0.85

    # If opponents were extremely aggressive (very high max), reduce to avoid getting dragged into overbidding.
    if max_prev_bid >= DAILY_SALARY * 1.4:
        base *= 0.75

    # Final bid: ensure non-negative and within budget
    bid = max(0.0, min(budget_cap, base))

    # If budget is very low, prioritize survival: bid remaining budget.
    if my_budget <= DAILY_SALARY * 0.2:
        bid = my_budget

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

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append(o)

    if not alive_opponents:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Yesterday bids: use only immediate previous_trace
    prev_bids = []
    for o in alive_opponents:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_prev_bid = 0.0
    if len(prev_bids) >= 2:
        sorted_b = sorted(prev_bids, reverse=True)
        second_prev_bid = float(sorted_b[1])

    # Supply pressure: tighter supply means higher chance others contest
    # Roughly, count how many full water units can be bought at once.
    # Use int() for any indexing; none needed here.
    supply_tightness = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY + 1e-9)  # 0..1-ish

    # Base bid: if supply is tight or others bid high, raise bid.
    # Target to slightly beat the historical highest with a cap.
    # If highest_prev_bid is very high, we should respond unless our hp is extremely low.
    if highest_prev_bid >= DAILY_SALARY * 1.05:
        aggressiveness = 0.70
    elif highest_prev_bid >= DAILY_SALARY * 0.85:
        aggressiveness = 0.58
    else:
        aggressiveness = 0.48

    # If my hp is low or I have accumulated no-water days, increase urgency.
    urgency = 0.0
    if hp <= 2.0:
        urgency = 0.35
    elif hp <= 4.0:
        urgency = 0.20
    elif no_water_days >= 2:
        urgency = 0.15

    # Combine: supply_tightness pushes bids up.
    bid_fraction = aggressiveness + 0.25 * supply_tightness + urgency
    bid_fraction = max(0.25, min(0.95, bid_fraction))

    # Compute candidate bid and ensure it is competitive but not wasteful.
    candidate = DAILY_SALARY * bid_fraction

    # If others were bidding high yesterday, try to outbid slightly.
    # Use a small increment over the second-highest to avoid overpaying.
    if second_prev_bid > 0.0 and highest_prev_bid > 0.0:
        # If we can afford it, aim between second and highest.
        target = min(highest_prev_bid, second_prev_bid + 2.5)
        candidate = max(candidate, target * (0.95 + 0.05 * supply_tightness))

    # Budget cap and safety floor.
    bid = max(0.0, min(budget, candidate))

    # If we are at risk of dying soon, ensure a stronger bid.
    if hp <= 1.0:
        bid = max(bid, min(budget, DAILY_SALARY * 0.9))

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

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    if not alive:
        # If everyone is dead, conserve
        target = DAILY_SALARY * 0.35
        return max(0.0, min(budget, target))

    # Read yesterday bids to infer aggressiveness
    prev_bids = []
    for oid, o in alive:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate opponent pressure from yesterday
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev_bid
    else:
        highest_prev_bid = 0.0
        second_prev_bid = 0.0

    # Determine how urgent we are
    urgent = 0
    if hp <= 3.0:
        urgent += 2
    if no_water_days >= 2:
        urgent += 2
    if day >= 7:
        urgent += 1

    # Supply-based water availability: if supply is low, water is scarce -> bid higher.
    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)  # 0..1
    scarcity = max(0.0, min(1.0, scarcity))

    # Base bid level: track Cindy/Alex were ~111-117 average; use that as a reference.
    # We don't know their exact code, but their trace suggests they spend heavily to survive.
    reference = 0.0
    if highest_prev_bid > 0.0:
        reference = 0.85 * highest_prev_bid
    else:
        reference = DAILY_SALARY * 0.7

    # If opponents were spending a lot yesterday, match/just-under to win water when it matters.
    # Use second-highest to avoid overpaying when only one player is extreme.
    if highest_prev_bid >= DAILY_SALARY * 1.15:
        target = max(DAILY_SALARY * 0.75, 0.9 * second_prev_bid + 5.0)
    else:
        target = max(DAILY_SALARY * 0.55, 0.75 * reference)

    # Adjust for our urgency and scarcity
    target *= (1.0 + 0.18 * urgent)
    target *= (1.0 + 0.25 * scarcity)

    # Cap by budget; also ensure we don't bid negative
    bid = max(0.0, min(budget, target))

    # Safety: if we are extremely low hp, push harder but still within budget
    if hp <= 1.5:
        bid = max(bid, min(budget, DAILY_SALARY * 0.95))

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

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append(o)

    # If no opponents, spend enough to avoid death.
    if not alive_opponents:
        target = DAILY_SALARY * 0.45
        return min(my_status['budget'], target)

    # Read yesterday bids from immediate previous_trace only.
    yesterday_bids = []
    for o in alive_opponents:
        prev = o.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                yesterday_bids.append(float(bid))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how tight the day is: fewer units -> more scarce -> higher bids needed.
    # supply is between 15 and 25; with WATER_REQ=9, units are ~1 or 2.
    units = int(supply / float(WATER_REQ))  # safe integer index behavior
    # units can be 1 or 2 in this range.
    scarcity = 1 if units <= 1 else 0

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Base aggressiveness: if others were bidding very high yesterday (Eric-like), we must not underbid.
    # Eric's survival suggests that bids near ~DAILY_SALARY*1.3 were effective.
    if highest_prev_bid >= DAILY_SALARY * 1.25:
        # If I am healthy, conserve while still contesting; if low hp, match aggressiveness.
        if hp <= 2.0 or no_water_days >= 2:
            desired = DAILY_SALARY * (1.05 if scarcity else 0.75)
        else:
            desired = DAILY_SALARY * (0.80 if scarcity else 0.60)
    else:
        # If yesterday bids were moderate/low, bid enough to stay in the game.
        if hp <= 2.0 or no_water_days >= 2:
            desired = DAILY_SALARY * (0.85 if scarcity else 0.70)
        else:
            desired = DAILY_SALARY * (0.55 if scarcity else 0.45)

    # Convert desired to a safe bid: never exceed budget; also avoid bidding too low when scarcity is high.
    min_contest = DAILY_SALARY * (0.35 if scarcity == 0 else 0.65)
    bid = max(min_contest, desired)

    # If budget is extremely low, bid remaining budget (to avoid wasting turns if close to death).
    if budget <= DAILY_SALARY * 0.15:
        return max(0.0, min(budget, DAILY_SALARY * 0.25))

    return float(min(budget, bid))
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

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Extract yesterday bids from previous_trace for immediate reaction
    prev_bids = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Baseline aggressiveness depends on our HP and no-water streak
    # If we are close to death, we must ensure water.
    if my_hp <= 2 or my_no_water_days >= 2:
        urgency = 0.95
    elif my_hp <= 4 or my_no_water_days >= 1:
        urgency = 0.75
    else:
        urgency = 0.55

    # Competitiveness: use yesterday's max bid as a proxy for how hard they will bid again.
    if prev_bids:
        max_prev_bid = max(prev_bids)
        # If they bid very high yesterday, we slightly undercut but remain competitive.
        if max_prev_bid >= DAILY_SALARY * 1.5:  # ~135
            # Try to match the pressure without overspending.
            target = min(my_budget, max(DAILY_SALARY * 0.65, max_prev_bid * 0.92))
        elif max_prev_bid >= DAILY_SALARY * 1.1:  # ~99
            target = min(my_budget, max(DAILY_SALARY * 0.55, max_prev_bid * 0.85))
        else:
            target = min(my_budget, DAILY_SALARY * urgency)
    else:
        target = min(my_budget, DAILY_SALARY * urgency)

    # Supply-based adjustment: with higher supply relative to our requirement, we can bid less.
    # supply is between 15 and 25; our requirement is 9.
    # If supply is closer to 25, contention is lower.
    if supply >= 21:
        target *= 0.92
    elif supply <= 17:
        target *= 1.05

    # Ensure non-negative and within budget
    if target < 0:
        target = 0.0
    if target > my_budget:
        target = my_budget

    # If budget is tiny, bid what we can.
    if my_budget <= 1.0:
        return my_budget

    # Small floor to avoid bidding 0 when we need water.
    if my_hp > 2 and my_no_water_days == 0:
        # keep it modest
        min_bid = DAILY_SALARY * 0.35
    else:
        min_bid = DAILY_SALARY * 0.55

    bid = max(min_bid, target)
    if bid > my_budget:
        bid = my_budget
    return float(bid)
"""
