# ============================================================
# Experiment: exp_073
# Agent: Bob
# Source: exp_073
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

    # Identify alive opponents
    alive_opponents = []
    for k, o in opponents_status.items():
        if o is not None and o.get('alive', False):
            alive_opponents.append(o)

    # Baseline bid logic: aim to be competitive but not reckless
    # Target share: if supply is low, bid higher; if high, bid moderate.
    # supply in [15,25] => need 1 unit of requirement is 9; typically 2 players may compete.
    if supply <= float(WATER_REQ + 6):
        base = DAILY_SALARY * 0.65
    elif supply <= float(WATER_REQ + 10):
        base = DAILY_SALARY * 0.58
    else:
        base = DAILY_SALARY * 0.50

    # React to yesterday's aggressive bids (immediate reaction only)
    prev_bids = []
    for o in alive_opponents:
        prev = o.get('previous_trace', {}) if isinstance(o.get('previous_trace', {}), dict) else {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    if prev_bids:
        highest_prev_bid = max(prev_bids)
        # If they were bidding near-salary, assume high urgency; slightly outbid if we can.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if my_status.get('hp', 0) > 3:
                base = max(base, highest_prev_bid * 1.02)
            else:
                base = max(base, highest_prev_bid * 1.05)
        # If they were bidding low, we can take initiative moderately.
        elif highest_prev_bid <= DAILY_SALARY * 0.45:
            base = max(base, DAILY_SALARY * 0.56)
        else:
            # Keep close to their level to avoid underbidding.
            base = max(base, highest_prev_bid * 1.01)

    # HP/budget risk management
    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # If we are close to starvation or low HP, bid harder.
    if hp <= 2.0 or no_water_days >= 2:
        base = max(base, DAILY_SALARY * 0.75)
    elif hp <= 3.0:
        base = max(base, DAILY_SALARY * 0.62)

    # Budget cap: never exceed budget.
    bid = min(budget, base)

    # Ensure non-negative
    if bid < 0:
        bid = 0.0

    # Return as float (game typically accepts numeric)
    return bid
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

    supply = day_context['supply']
    day = day_context['day']

    # Identify alive opponents and collect yesterday bids
    alive_opps = []
    yesterday_bids = []
    yesterday_trace_by_opp = {}
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {}) or {}
            yesterday_trace_by_opp[oid] = prev
            if prev.get('bid') is not None:
                yesterday_bids.append(prev['bid'])

    # If no info, be conservative
    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Use yesterday's max bid as a proxy for opponent aggressiveness
    max_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Convert supply to an estimate of how many full water units are available
    # (not strictly needed for indexing, but used for pressure scaling)
    est_units = int(supply / float(WATER_REQ)) if WATER_REQ > 0 else 0

    hp = my_status['hp']
    budget = my_status['budget']

    # Base bid policy: moderate if healthy, higher if low HP
    # Aggression adjustment: if yesterday max bid was very high, expect bidding war.
    if hp <= 2:
        # We are in danger; secure water aggressively.
        bid = DAILY_SALARY * 0.9
    elif hp <= 4:
        bid = DAILY_SALARY * 0.7
    else:
        bid = DAILY_SALARY * 0.55

    # If yesterday had extreme bids, we slightly increase to avoid losing tie/shortage.
    if max_prev_bid >= DAILY_SALARY * 1.7:  # ~153
        bid *= 1.15
    elif max_prev_bid >= DAILY_SALARY * 1.3:  # ~117
        bid *= 1.05

    # If supply is scarce (closer to MIN_SUPPLY), increase bid a bit.
    if supply <= (MIN_SUPPLY + 0.5):
        bid *= 1.08
    elif supply >= (MAX_SUPPLY - 0.5):
        bid *= 0.95

    # Never exceed budget
    bid = min(budget, bid)

    # Ensure at least a small bid if budget allows
    if bid <= 0 and budget > 0:
        bid = min(budget, 1.0)

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

    # Alive opponents and yesterday bids
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    # If no opponents, bid enough to avoid no-water streak
    if not alive_opps:
        cap = min(my_status.get('budget', 0.0), DAILY_SALARY * 0.6)
        return max(0.0, cap)

    # Extract yesterday bids from previous_trace
    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', None)
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    yesterday_bids.append(float(b))
                except Exception:
                    pass
        elif isinstance(prev, list) and len(prev) > 0:
            # Only immediate trace if list exists
            last = prev[-1]
            if isinstance(last, dict):
                b = last.get('bid', None)
                if b is not None:
                    try:
                        yesterday_bids.append(float(b))
                    except Exception:
                        pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Pressure from supply scarcity: fewer units means higher chance others win water
    # supply is 15-25, water requirement is 9 => scarcity increases when supply closer to 15
    scarcity = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.0
    scarcity = max(0.0, min(1.0, scarcity))

    # Baseline bid: moderate fraction of salary, adjusted by scarcity and my HP
    # If I'm close to death or already on no-water streak, bid aggressively.
    if hp <= 2.0 or no_water_days >= 2:
        base = DAILY_SALARY * (0.85 + 0.1 * scarcity)
    else:
        # If yesterday had aggressive bids (>=~100), slightly over-anchor but not maxing out.
        if highest_prev_bid >= DAILY_SALARY * 0.9:
            base = DAILY_SALARY * (0.55 + 0.25 * scarcity)
        else:
            base = DAILY_SALARY * (0.45 + 0.20 * scarcity)

    # Additional reaction: if highest_prev_bid is high, try to beat it by a small margin.
    # Keep this conservative to avoid overspending.
    target = base
    if highest_prev_bid > 0:
        # Beat by 2% of salary or 1.0, whichever is larger, but cap by a reasonable multiple.
        margin = max(1.0, DAILY_SALARY * 0.02)
        target = max(target, min(highest_prev_bid + margin, DAILY_SALARY * 1.05))

    # Final cap by budget
    bid = min(budget, target)
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Alive opponents and yesterday bids
    alive_opps = []
    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {}) or {}
            if prev.get('bid') is not None:
                yesterday_bids.append(float(prev['bid']))

    # If no info, bid a conservative amount
    if not alive_opps:
        return max(0.0, min(float(my_status['budget']), DAILY_SALARY * 0.45))

    # Use yesterday pressure as proxy for today's aggressiveness
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Estimate how many allocations we likely need/want.
    # If supply is low, winning a single unit is crucial; if high, we can be slightly less aggressive.
    # supply in [15,25] so supply/WATER_REQ is ~1.6 to 2.7; treat as 2 units target.
    target_units = 2
    # Convert target to a bid pressure scale.
    supply_factor = (supply - 15.0) / (25.0 - 15.0)  # 0..1

    # Base bid: slightly below yesterday aggressors to avoid overpaying.
    # If their highest bid was very high, we must match more closely to secure water.
    if highest_prev_bid >= DAILY_SALARY * 1.05:
        base = highest_prev_bid - 5.0
    elif highest_prev_bid >= DAILY_SALARY * 0.9:
        base = highest_prev_bid - 8.0
    else:
        base = max(DAILY_SALARY * (0.45 + 0.15 * supply_factor), second_prev_bid * 0.95)

    # Urgency adjustment based on HP and consecutive no-water days.
    # If HP is low or we have been without water, increase bid to secure survival.
    urgency = 0.0
    if my_hp <= 2.0:
        urgency += 0.35
    elif my_hp <= 4.0:
        urgency += 0.20
    if no_water_days >= 2:
        urgency += 0.20
    if no_water_days >= 3:
        urgency += 0.25

    # When supply is high, we can shade bids; when low, bid more.
    shade = 1.0 - 0.15 * supply_factor

    bid = base * shade
    bid = bid * (1.0 + urgency)

    # Cap bid to budget and keep within a reasonable band relative to salary.
    # Aggressive caps prevent irrational overbids.
    max_reasonable = min(my_budget, DAILY_SALARY * 1.35)
    min_reasonable = 0.0
    if bid > max_reasonable:
        bid = max_reasonable
    if bid < min_reasonable:
        bid = min_reasonable

    # If my budget is extremely low, switch to survival-minimum behavior.
    if my_budget <= DAILY_SALARY * 0.35:
        # Try to secure at least something when close to death.
        if my_hp <= 3.0 or no_water_days >= 2:
            bid = min(my_budget, DAILY_SALARY * 0.9)
        else:
            bid = min(my_budget, DAILY_SALARY * 0.5)

    return float(bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    # If no one alive, conserve budget.
    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from traces for immediate reaction.
    prev_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate how many
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
    day = day_context.get('day', 0)

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))

    # Identify alive opponents and read yesterday bids
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            prev = opp.get('previous_trace', {}) or {}
            prev_bid = prev.get('bid', None)
            alive_opps.append((opp_id, opp, prev_bid))

    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Yesterday pressure from bids
    prev_bids = [b for (_, _, b) in alive_opps if isinstance(b, (int, float)) and b is not None]
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate how many water units are likely needed/available
    # Supply is total units; our requirement is WATER_REQ per day.
    # If supply is near minimum, competition is higher.
    tight_supply = supply <= (MIN_SUPPLY + 0.5)

    # Strategy: If Cindy/Alex were aggressive yesterday, we bid moderately high to secure water when tight.
    # Otherwise, conserve and bid just above likely low bidders.
    # Use our HP to decide risk.
    if my_hp <= 2:
        # Desperate: try to secure water regardless
        bid = DAILY_SALARY * (0.85 if tight_supply else 0.75)
    else:
        # Determine target bid level based on yesterday highest bid
        if highest_prev_bid >= DAILY_SALARY * 1.6:
            # Very aggressive opponent yesterday (likely Cindy). Outbid slightly only when supply tight.
            if tight_supply:
                bid = min(my_budget, highest_prev_bid + 5.0)
            else:
                bid = min(my_budget, max(DAILY_SALARY * 0.55, highest_prev_bid * 0.75))
        elif highest_prev_bid >= DAILY_SALARY * 1.2:
            # Moderately aggressive
            if tight_supply:
                bid = min(my_budget, max(DAILY_SALARY * 0.7, highest_prev_bid * 0.9))
            else:
                bid = min(my_budget, max(DAILY_SALARY * 0.5, highest_prev_bid * 0.65))
        else:
            # Mostly low bidders (David low, others possibly failed)
            bid = min(my_budget, DAILY_SALARY * (0.45 if tight_supply else 0.35))

    # Ensure non-negative and do not exceed budget
    if bid < 0.0:
        bid = 0.0
    if bid > my_budget:
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

    budget = float(my_status['budget'])
    hp = int(my_status['hp'])
    no_water_days = int(my_status['no_water_days'])

    # If we cannot afford much, bid what we can.
    if budget <= 0:
        return 0.0

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday bids from previous_trace to infer aggressiveness.
    prev_bids = []
    for opp_id, opp in alive_opps:
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

    # Determine our target bid level.
    # If someone was bidding extremely high yesterday, we must not be too low.
    # But we also avoid overspending when our hp is already low.
    supply_factor = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)  # 0..1
    supply_factor = max(0.0, min(1.0, supply_factor))

    # Base bid depends on supply availability: higher supply -> can bid slightly lower.
    # Lower supply -> bid higher to secure water.
    base = DAILY_SALARY * (0.62 - 0.12 * supply_factor)  # ~0.50..0.62 of salary

    # Aggression adjustment from yesterday.
    # If Cindy/Eric style bids were near max (~140-163), we raise bid to compete.
    if highest_prev_bid >= 140.0:
        # Compete but do not fully match unless we are in danger.
        danger = (hp <= 2) or (no_water_days >= 1)
        target = max(base, second_prev_bid + 5.0) if not danger else max(base, highest_prev_bid * 0.92)
    elif highest_prev_bid >= 90.0:
        target = max(base, highest_prev_bid * 0.65)
    else:
        target = base

    # If our hp is low, we should secure water more aggressively.
    if hp <= 2:
        target = max(target, DAILY_SALARY * 0.85)
    elif hp <= 3:
        target = max(target, DAILY_SALARY * 0.70)

    # Cap by budget and a reasonable max to avoid bankruptcy.
    # In this game, bids around salary-scale are typical; keep below 1.2*salary.
    max_reasonable = DAILY_SALARY * 1.2
    bid = min(budget, max_reasonable, target)

    # Small day-based jitter to avoid ties.
    jitter = ((day % 5) - 2) * 1.0
    bid = bid + jitter

    if bid < 0:
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    # Identify alive opponents
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    # If alone, conserve
    if not alive:
        return float(min(my_status['budget'], DAILY_SALARY * 0.35))

    # Use yesterday's immediate trace bids to infer aggression
    prev_bids = []
    prev_hp_after = []
    for oid, o in alive:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass
        hpa = prev.get('hp_after', None)
        if hpa is not None:
            try:
                prev_hp_after.append(float(hpa))
            except Exception:
                pass

    # Defaults
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev_bid
    else:
        highest_prev_bid = 0.0
        second_prev_bid = 0.0

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))

    # Determine target bid band based on opponent pressure
    # Cindy likely highest; if highest_prev_bid is near salary, pressure is high.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # High pressure: pay enough to secure water if I'm not healthy
        if my_hp <= 2.5:
            target = DAILY_SALARY * 0.95
        elif my_hp <= 4.5:
            target = max(DAILY_SALARY * 0.75, second_prev_bid + 5.0)
        else:
            target = max(DAILY_SALARY * 0.55, second_prev_bid + 2.5)
    elif highest_prev_bid >= DAILY_SALARY * 0.55:
        # Moderate pressure: bid slightly above typical winner
        target = max(DAILY_SALARY * 0.50, second_prev_bid + 1.5)
    else:
        # Low pressure: conserve
        target = DAILY_SALARY * 0.45

    # Adjust for supply: if supply is low, competition for scarce water tends to be higher
    # Normalize supply to [0,1]
    if MAX_SUPPLY > MIN_SUPPLY:
        s_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        s_norm = 0.5
    s_norm = max(0.0, min(1.0, float(s_norm)))

    # If supply is scarce, add a small premium; if abundant, reduce
    target = target * (0.92 + 0.16 * s_norm)

    # Never bid more than budget; also avoid extreme bids when budget is low
    # Keep a floor to ensure we aren't always losing when pressured
    if my_budget <= 0.0:
        return 0.0

    # If budget is too small, spend a fraction based on HP
    if my_budget < DAILY_SALARY * 0.6:
        if my_hp <= 2.5:
            cap_frac = 0.95
        elif my_hp <= 4.5:
            cap_frac = 0.75
        else:
            cap_frac = 0.55
        bid = my_budget * cap_frac
    else:
        bid = min(my_budget, target)

    # Ensure bid is non-negative float
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((opp_id, o))

    if not alive_opps:
        return float(min(my_budget, DAILY_SALARY * 0.4))

    # Immediate reaction to yesterday: use their previous_trace bid levels.
    prev_bids = []
    prev_by_id = {}
    for opp_id, o in alive_opps:
        prev = o.get('previous_trace') or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                bf = float(b)
                prev_bids.append(bf)
                prev_by_id[opp_id] = bf
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    lowest_prev_bid = min(prev_bids) if prev_bids else DAILY_SALARY

    # Supply pressure estimate: with supply 15-25 and WATER_REQ=9, at most 2 units can be allocated.
    # We want enough water to avoid HP loss; bid more when supply is tighter.
    tight_supply = 1.0 if supply < 19.0 else 0.0

    # If we are already in danger (no-water streak), bid aggressively.
    danger = 0
    if my_hp <= 2:
        danger = 2
    elif my_hp <= 4:
        danger = 1
    if my_no_water_days >= 2:
        danger = max(danger, 2)

    # Base target bid.
    # - If someone was bidding near salary yesterday, they likely contest water; undercut slightly.
    # - If bids were low, we can take water with a moderate bid.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Undercut by a small amount but still stay high enough.
        target = highest_prev_bid - (DAILY_SALARY * 0.05) - (5.0 * tight_supply)
    elif highest_prev_bid >= DAILY_SALARY * 0.55:
        target = max(lowest_prev_bid + 2.0, DAILY_SALARY * 0.60)
    else:
        # Low contention yesterday; bid around salary to secure water.
        target = DAILY_SALARY * (0.55 + 0.15 * tight_supply)

    # Adjust for current danger.
    if danger == 2:
        target *= 1.25
    elif danger == 1:
        target *= 1.10

    # Budget-aware cap.
    target = float(min(target, my_budget))

    # Ensure we don't bid zero when we still need water.
    if my_budget <= 0.0:
        return 0.0

    # Hard safety minimum: if tight supply and we have budget, bid at least a fraction of salary.
    min_bid = DAILY_SALARY * (0.35 + 0.15 * tight_supply)
    bid = float(max(target, min_bid if my_budget >= min_bid else 0.0))

    # Final cap to avoid overspending.
    # If high contention yesterday, keep bids below salary*1.0 to preserve across days.
    cap = DAILY_SALARY * (1.0 if highest_prev_bid >= DAILY_SALARY * 0.55 else 0.85)
    bid = float(min(bid, cap, my_budget))

    # If we are extremely low on budget, bid whatever we can.
    if bid < 1e-6:
        bid = float(min(my_budget, DAILY_SALARY * 0.2))

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

    # Basic safety: if we are in trouble, bid to avoid further no-water days.
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.45))

    # Read yesterday bids from previous_trace to infer aggressiveness.
    prev_bids = []
    prev_hp_after = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        if prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass
        if prev.get('hp_after') is not None:
            try:
                prev_hp_after.append(float(prev['hp_after']))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    lowest_prev_bid = min(prev_bids) if prev_bids else 0.0

    # Supply pressure: more supply reduces need to overbid.
    # Convert to an approximate "competition level".
    # If supply is near max, we can bid slightly less.
    supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    supply_norm = max(0.0, min(1.0, supply_norm))

    # Determine target bid band.
    # Cindy's high bid suggests she will keep bidding aggressively; we try to beat her tier
    # only when our HP/no-water days require it.
    need_factor = 0.0
    if hp <= 2.0:
        need_factor = 1.0
    elif hp <= 4.0:
        need_factor = 0.75
    elif no_water_days >= 2:
        need_factor = 0.65
    elif no_water_days >= 1:
        need_factor = 0.45
    else:
        need_factor = 0.25

    # Base aggressiveness from yesterday.
    # If someone bid very high yesterday, we bid in the same order but scaled by need.
    # Otherwise, bid to slightly above the lower tier.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        target = highest_prev_bid * (0.78 + 0.22 * need_factor)
    else:
        # Not too extreme: anchor between lowest and a fraction of highest.
        anchor = lowest_prev_bid + 0.35 * (highest_prev_bid - lowest_prev_bid)
        target = anchor + (DAILY_SALARY * 0.18) * (0.5 + need_factor)

    # Adjust for supply: higher supply => reduce bid.
    target = target * (0.92 - 0.18 * supply_norm)

    # Budget constraints and floor.
    # Keep a minimum bid to stay competitive but never exceed budget.
    # Also avoid bidding more than a reasonable fraction of budget.
    cap = budget * 0.85 if budget > 0 else 0.0
    target = max(0.0, min(target, cap))

    # If our budget is tiny, bid whatever we can.
    if budget <= DAILY_SALARY * 0.15:
        return max(0.0, min(budget, DAILY_SALARY * 0.6))

    # Ensure bid is not trivially small when we need water.
    if need_factor >= 0.75:
        min_bid = DAILY_SALARY * 0.55
    elif need_factor >= 0.45:
        min_bid = DAILY_SALARY * 0.45
    else:
        min_bid = DAILY_SALARY * 0.30

    target = max(min_bid, target)
    target = min(target, budget)

    return float(target)
"""
