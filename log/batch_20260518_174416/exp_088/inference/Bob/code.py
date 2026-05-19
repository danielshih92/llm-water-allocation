# ============================================================
# Experiment: exp_088
# Agent: Bob
# Source: exp_088
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    # If no one is alive, take as much as needed but keep some buffer.
    if not alive_opponents:
        target = min(budget, DAILY_SALARY * 0.7)
        return float(target)

    # Read yesterday's bids (immediate reaction only)
    yesterday_bids = []
    yesterday_pressures = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                b = float(bid)
            except Exception:
                continue
            yesterday_bids.append(b)
            # pressure proxy: bid relative to opponent's daily salary if available
            opp_salary = float(opp.get('daily_salary', DAILY_SALARY))
            if opp_salary > 0:
                yesterday_pressures.append(b / opp_salary)

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    max_pressure = max(yesterday_pressures) if yesterday_pressures else 0.0

    # Determine how many
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

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for k, o in opponents_status.items():
        try:
            if o.get('alive', False):
                alive_opps.append(o)
        except Exception:
            pass

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids to infer who overpays.
    prev_bids = []
    prev_pressured = []  # (bid, hp_after)
    for o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                b = float(b)
                prev_bids.append(b)
                hp_after = prev.get('hp_after', None)
                if hp_after is not None:
                    prev_pressured.append((b, float(hp_after)))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    # Determine urgency from my no-water streak.
    # If I'm close to death, bid harder.
    urgency = 0.0
    if no_water_days >= 2:
        urgency += 0.35
    if no_water_days >= 3:
        urgency += 0.35
    if hp <= 2:
        urgency += 0.35
    if hp <= 3:
        urgency += 0.15

    # Supply-based aggressiveness: with higher supply, we can bid less.
    supply_factor = 0.0
    if supply <= float(MIN_SUPPLY):
        supply_factor = 0.25
    elif supply >= float(MAX_SUPPLY):
        supply_factor = -0.05
    else:
        # linear interpolation between MIN_SUPPLY and MAX_SUPPLY
        t = (supply - float(MIN_SUPPLY)) / (float(MAX_SUPPLY) - float(MIN_SUPPLY))
        supply_factor = 0.25 + t * (-0.30)

    # If someone already bid very high yesterday (Cindy-like), we must not be too low.
    # Otherwise, keep a mid bid.
    if highest_prev_bid >= DAILY_SALARY * 0.95:
        base = DAILY_SALARY * 0.75
    elif highest_prev_bid >= DAILY_SALARY * 0.60:
        base = DAILY_SALARY * 0.62
    else:
        base = DAILY_SALARY * 0.48

    # Small adjustment using average pressure.
    if avg_prev_bid > 0:
        base += (avg_prev_bid - DAILY_SALARY * 0.5) * 0.25

    # Add urgency and supply factor.
    target = base * (1.0 + urgency) * (1.0 + supply_factor)

    # Also ensure we can secure at least once if supply is tight.
    # With supply around 15-25 and WATER_REQ=9, single unit is typically enough to recover.
    if supply < float(WATER_REQ) + 2.0:
        target *= 1.15

    # Cap by budget and keep within plausible range.
    bid = max(0.0, min(budget, target))

    # If budget is extremely low, bid what we can.
    if budget <= DAILY_SALARY * 0.2:
        bid = budget

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

    my_hp = int(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Read yesterday's bids only from previous_trace
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Estimate opponent pressure from yesterday
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else 0.0

    # Supply pressure: higher supply reduces need to outbid; lower supply increases it.
    # Use a simple normalized factor around mid-range.
    mid = (MIN_SUPPLY + MAX_SUPPLY) / 2.0
    if supply <= mid:
        supply_factor = 1.0
    else:
        supply_factor = 0.75

    # If someone was bidding very high yesterday, we must contest.
    # Cindy-like behavior: highest_prev_bid around 170.
    contest_threshold = DAILY_SALARY * 0.85  # 76.5

    # Base bid target
    if highest_prev_bid >= contest_threshold:
        # Bid just above the highest/second tier to avoid losing to top bidder.
        # If my hp is healthy, spend less; if low, spend more.
        hp_pressure = 0.9 if my_hp <= 2 else (1.0 if my_hp <= 4 else 0.75)
        target = max(highest_prev_bid + 2.0, second_prev_bid + 4.0)
        target *= supply_factor * hp_pressure
    else:
        # Otherwise, bid around a moderate share; if my hp is low, increase.
        hp_pressure = 1.05 if my_hp <= 2 else (0.95 if my_hp <= 4 else 0.7)
        target = max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5)
        target *= supply_factor * hp_pressure

    # Budget safety: never bid more than we can afford.
    # Also keep some runway if my_no_water_days is already high.
    runway_multiplier = 1.0
    if my_no_water_days >= 2:
        runway_multiplier = 0.65
    elif my_no_water_days >= 1:
        runway_multiplier = 0.8

    # Cap to a reasonable fraction of budget.
    max_affordable = my_budget * runway_multiplier

    # Ensure we bid at least enough to have a chance but not waste too much.
    # Use DAILY_SALARY as a soft cap since budgets can be large.
    soft_cap = DAILY_SALARY * 1.2
    final_bid = min(target, max_affordable, soft_cap)

    # If final_bid is too small, raise slightly to contest when supply is low.
    if final_bid < DAILY_SALARY * 0.35 and supply <= mid:
        final_bid = min(max_affordable, DAILY_SALARY * 0.55)

    # If hp is critical, spend aggressively (but still within budget).
    if my_hp <= 1:
        final_bid = min(max_affordable, DAILY_SALARY * 0.95)

    # Final clamp
    if final_bid < 0.0:
        final_bid = 0.0

    return float(final_bid)
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

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday bids and infer pressure.
    yesterday_bids = []
    near_max_flags = 0
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                b = float(b)
            except Exception:
                continue
            yesterday_bids.append(b)
            # If they were close to their max bid, they likely keep bidding high.
            try:
                max_bid = float(prev.get('max_bid', o.get('max_bid', None))) if 'max_bid' in prev else None
            except Exception:
                max_bid = None
            if max_bid is not None and max_bid > 0:
                if b >= 0.85 * max_bid:
                    near_max_flags += 1

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = (sum(yesterday_bids) / len(yesterday_bids)) if yesterday_bids else 0.0

    # Supply pressure: with higher supply, clearing cost should drop.
    # Normalize supply between MIN_SUPPLY and MAX_SUPPLY.
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_norm = 0.5
    supply_norm = max(0.0, min(1.0, supply_norm))

    # Base bid target: slightly above typical survival bids, but not matching extreme outliers.
    # Use avg as anchor; if someone was extremely aggressive, add a small increment.
    base = max(DAILY_SALARY * 0.45, avg_prev_bid * 0.55)

    # Escalation if highest bid is very high.
    if highest_prev_bid >= DAILY_SALARY * 1.3:
        base = max(base, DAILY_SALARY * 0.75)
    elif highest_prev_bid >= DAILY_SALARY * 0.9:
        base = max(base, DAILY_SALARY * 0.62)

    # If supply is high, reduce bid slightly; if supply is low, increase.
    # supply_norm=1 => high supply => cheaper
    base = base * (1.0 - 0.18 * supply_norm) + base * (0.12 * (1.0 - supply_norm))

    # HP urgency: if I'm low HP or have water-stress, bid more.
    if hp <= 2:
        base *= 1.35
    elif hp <= 4:
        base *= 1.18

    if no_water_days >= 2:
        base *= 1.15

    # If multiple opponents were near-max yesterday, slightly raise to avoid being outbid.
    if near_max_flags >= 2:
        base *= 1.12

    # Hard cap: never exceed what we can afford; keep some budget for later.
    # Also avoid overbidding beyond a fraction of daily salary.
    affordability_cap = budget
    strategic_cap = DAILY_SALARY * 1.05
    final_bid = min(affordability_cap, strategic_cap, base)

    # Ensure non-negative.
    if final_bid < 0:
        final_bid = 0.0

    # If my budget is tiny, bid what I can.
    if budget <= 5:
        return min(budget, 5.0)

    # Add small day-based jitter to avoid ties/predictability.
    jitter = (day % 3) * 1.0
    final_bid = final_bid + jitter

    # Final clamp.
    final_bid = min(final_bid, affordability_cap)
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

    # Read yesterday bids to infer pressure.
    prev_bids = []
    prev_by_opp = {}
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                bf = float(b)
                prev_bids.append(bf)
                prev_by_opp[oid] = bf
            except Exception:
                pass

    # Determine competitive tier.
    if prev_bids:
        max_prev = max(prev_bids)
        # If someone bid extremely high yesterday, assume they will keep bidding high.
        # We aim for a mid-high bid to avoid being starved, but not match max.
        if max_prev >= 300:
            base = DAILY_SALARY * 0.65
        elif max_prev >= 120:
            base = DAILY_SALARY * 0.55
        else:
            base = DAILY_SALARY * 0.45
    else:
        base = DAILY_SALARY * 0.45

    # Urgency adjustment based on our hp and no-water streak.
    # If we have been without water, raise bids sharply.
    if no_water_days >= 2 or hp <= 2:
        base *= 1.35
    elif no_water_days == 1 or hp <= 4:
        base *= 1.15

    # Supply-based adjustment: when supply is low, competition likely increases.
    if supply <= float(WATER_REQ):
        base *= 1.15
    elif supply >= 0.9 * float(MAX_SUPPLY):
        base *= 0.95

    # Cap by budget and keep within a reasonable band.
    bid = min(budget, base)

    # If budget is too low, bid what we can to avoid death.
    if bid < 1e-6:
        bid = min(budget, DAILY_SALARY * 0.2)

    # Final safety clamp.
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

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    # Identify alive opponents
    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    # If no opponents alive, conserve
    if not alive_opponents:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace for immediate reaction
    yesterday_bids = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Estimate dominant bidding pressure
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # Also consider typical upper range
        sorted_bids = sorted(yesterday_bids)
        top_two = sorted_bids[-2:] if len(sorted_bids) >= 2 else sorted_bids
        second_highest = top_two[0] if len(top_two) == 2 else top_two[0]
    else:
        highest_prev_bid = 0.0
        second_highest = 0.0

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # If we're close to death, bid to secure water
    if my_hp <= 2.5 or no_water_days >= 2:
        # Bid close to the highest observed pressure
        target = max(highest_prev_bid * 1.02, DAILY_SALARY * 0.85)
    else:
        # Healthy: bid just enough to beat the dominant bids
        # If opponents were bidding very high, slightly under/around to save budget.
        if highest_prev_bid >= DAILY_SALARY * 1.4:
            target = max(second_highest + 2.0, DAILY_SALARY * 0.75)
        else:
            target = max(highest_prev_bid + 1.0, DAILY_SALARY * 0.55)

    # Convert target to a feasible bid: cannot exceed budget
    bid = min(my_budget, target)

    # If supply is low relative to our requirement, slightly increase aggressiveness
    # (index-safe usage not needed since we don't index lists)
    if supply < float(WATER_REQ) * 1.1:
        bid = min(my_budget, bid * 1.05)

    # Ensure non-negative
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

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    # Identify alive opponents and collect yesterday bids
    alive_opps = []
    yesterday_bids = []
    highest_prev_bid = 0.0
    highest_opp = None
    for agent_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(agent_id)
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid', None)
            if bid is not None:
                try:
                    b = float(bid)
                except Exception:
                    b = 0.0
                yesterday_bids.append(b)
                if b > highest_prev_bid:
                    highest_prev_bid = b
                    highest_opp = agent_id

    # If no one is alive, bid conservatively
    if not alive_opps:
        return float(min(my_status.get('budget', 0.0), DAILY_SALARY * 0.4))

    hp = my_status.get('hp', 0)
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Pressure estimate: if someone previously bid very high, water is likely contested.
    # Cindy's pattern suggests high bids; we avoid matching her exactly unless we are in danger.
    pressure = 0.0
    if yesterday_bids:
        pressure = highest_prev_bid / max(1.0, DAILY_SALARY)

    # Base bid depends on our hp/no_water_days.
    # If we're low hp or have gone long without water, we must secure.
    danger = 0
    if hp <= 2:
        danger += 2
    elif hp <= 4:
        danger += 1
    if no_water_days >= 2:
        danger += 1

    # Supply factor: with higher supply, we can bid less.
    # supply is within [15,25] typically.
    try:
        supply_val = float(supply)
    except Exception:
        supply_val = float(MIN_SUPPLY)

    supply_factor = (supply_val - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY + 1e-9)
    supply_factor = max(0.0, min(1.0, supply_factor))

    # Target bid logic:
    # - If pressure is high, bid around 0.6*highest_prev_bid + small increment when in danger.
    # - Otherwise bid around 0.45*highest_prev_bid but not below a floor to avoid starvation.
    if yesterday_bids:
        if danger >= 2:
            target = 0.62 * highest_prev_bid + 3.0
        elif danger == 1:
            target = 0.52 * highest_prev_bid + 2.0
        else:
            target = 0.45 * highest_prev_bid + 1.0
    else:
        target = DAILY_SALARY * 0.55

    # Adjust by supply: more supply => reduce bid slightly
    target = target * (0.90 + 0.20 * supply_factor)

    # Ensure a reasonable floor/ceiling
    floor_bid = DAILY_SALARY * (0.35 if danger == 0 else (0.55 if danger == 1 else 0.85))
    cap_bid = min(budget, DAILY_SALARY * 0.98)

    bid = max(floor_bid, target)
    bid = min(bid, cap_bid)

    # If budget is tiny, just spend what we can
    if budget <= 0.0:
        return 0.0

    return float(max(0.0, min(budget, bid)))
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

    # Alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Yesterday bids (immediate reaction)
    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Determine how scarce water is relative to requirement
    # If supply is close to requirement, we must bid more to beat others.
    scarcity_ratio = supply / float(WATER_REQ)  # e.g., 15/9 ~ 1.67

    # Baseline bid: aim around a fraction of DAILY_SALARY, adjusted by scarcity and my HP.
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status.get('no_water_days', 0))

    # If I'm already in danger, bid aggressively.
    if hp <= 2 or no_water_days >= 2:
        cap = min(budget, DAILY_SALARY * 0.95)
        # If others were very aggressive yesterday, go higher within cap.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            return float(min(cap, DAILY_SALARY * 0.95))
        return float(cap)

    # If yesterday had very high bids, increase slightly to avoid being outbid.
    if highest_prev_bid >= DAILY_SALARY * 1.2:
        base = DAILY_SALARY * 0.75
    elif highest_prev_bid >= DAILY_SALARY * 0.85:
        base = DAILY_SALARY * 0.62
    else:
        base = DAILY_SALARY * 0.52

    # Scarcity adjustment: lower scarcity_ratio -> higher bid.
    # scarcity_ratio range roughly 1.67..2.78 for supply 15..25 with WATER_REQ=9
    if scarcity_ratio <= 1.75:
        base *= 1.15
    elif scarcity_ratio >= 2.5:
        base *= 0.92

    # Budget safety: don't overspend early; keep some reserve.
    # Reserve target: at least ~30% of budget or one more day salary.
    reserve = max(0.3 * budget, DAILY_SALARY * 0.35)
    max_affordable = max(0.0, budget - reserve)

    bid = min(max_affordable, base)

    # If computed bid is too low to matter, ensure a minimum meaningful bid.
    # But never exceed budget.
    min_bid = DAILY_SALARY * 0.35
    if bid < min_bid:
        bid = min(budget, min_bid)

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

    supply = day_context.get('supply', 0)
    day = day_context.get('day', 0)

    hp = my_status.get('hp', 0)
    budget = my_status.get('budget', 0)
    no_water_days = my_status.get('no_water_days', 0)

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Extract yesterday bids for immediate reaction
    yesterday_bids = []
    yesterday_pressures = []
    for opp_id, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                yesterday_bids.append(float(bid))
            except Exception:
                pass
        # Use remaining hp as a proxy for their urgency yesterday
        prev_hp_after = prev.get('hp_after', None)
        if prev_hp_after is not None:
            try:
                yesterday_pressures.append((float(prev_hp_after), opp_id))
            except Exception:
                pass

    # Determine aggressiveness threshold from yesterday
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        median_prev_bid = sorted(yesterday_bids)[len(yesterday_bids)//2]
    else:
        highest_prev_bid = 0.0
        median_prev_bid = 0.0

    # Estimate how many water units are likely needed/available
    # supply is between 15 and 25; our requirement is 9.
    # If supply is closer to 15, water is scarce -> bid more.
    scarcity = 0.0
    try:
        scarcity = (MAX_SUPPLY - float(supply)) / float(MAX_SUPPLY - MIN_SUPPLY)
    except Exception:
        scarcity = 0.5
    scarcity = max(0.0, min(1.0, scarcity))

    # Urgency from our own state
    urgency = 0.0
    if hp <= 2:
        urgency = 1.0
    elif hp <= 4:
        urgency = 0.7
    elif hp <= 6:
        urgency = 0.45
    else:
        urgency = 0.25

    if no_water_days >= 2:
        urgency = max(urgency, 0.8)

    # Decide target bid:
    # - If Cindy survived with high bid yesterday, we may need to match/just exceed the high cluster.
    # - Otherwise, bid around median+small premium.
    premium = 2.0 + 6.0 * scarcity

    # If someone previously bid very high, we counter with a near-top bid but cap by our budget.
    if highest_prev_bid >= DAILY_SALARY * 1.3:  # ~117+ 
        # Match just above the highest_prev_bid scaled by urgency.
        target = highest_prev_bid + premium
        # If we are healthy, avoid overpaying.
        if urgency < 0.5:
            target = min(target, median_prev_bid + premium + 10.0)
    else:
        # Bid around median with premium scaled by scarcity/urgency
        target = median_prev_bid + premium * (0.8 + 0.6 * urgency)

    # Convert target into a safe spend cap based on our budget and urgency
    # Keep some budget for later days.
    budget_cap = budget
    if hp <= 3:
        budget_cap = min(budget_cap, DAILY_SALARY * 0.95)
    elif hp <= 6:
        budget_cap = min(budget_cap, DAILY_SALARY * 0.75)
    else:
        budget_cap = min(budget_cap, DAILY_SALARY * 0.6)

    bid = min(budget_cap, target)

    # Ensure non-negative and at least a minimal competitive bid when urgency is high
    if bid < 0:
        bid = 0.0

    # Minimal floor to avoid losing when others likely bid aggressively
    min_floor = 15.0 + 40.0 * (0.6 * scarcity + 0.4 * urgency)
    if urgency >= 0.7:
        bid = max(bid, min_floor)

    # Hard cap: cannot exceed budget
    bid = min(bid, budget)

    return bid
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o is not None and o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return float(min(budget, DAILY_SALARY * 0.4))

    # Yesterday reaction: look at bids from alive opponents.
    prev_bids = []
    for oid, o in alive_opps:
        pt = o.get('previous_trace', {}) or {}
        b = pt.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Base urgency from our hp.
    if hp <= 2:
        urgency = 0.95
    elif hp <= 4:
        urgency = 0.75
    else:
        urgency = 0.55

    # Supply pressure: with only 15-25 supply, competition matters.
    # If supply is closer to minimum, increase bids to secure allocation.
    if supply <= 16.0:
        supply_factor = 1.10
    elif supply <= 19.0:
        supply_factor = 1.00
    else:
        supply_factor = 0.90

    target = DAILY_SALARY * urgency * supply_factor

    # If Cindy-style pressure existed yesterday (high highest bid), overbid slightly.
    # This exploits the observed willingness to pay while staying within budget.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Bid just above the strongest prior pressure.
        target = max(target, highest_prev_bid + 2.0)
    elif highest_prev_bid >= DAILY_SALARY * 0.55:
        target = max(target, highest_prev_bid * 0.85)

    # Never exceed budget.
    bid = min(budget, target)

    # If budget is very low, still try to get some water when hp is critical.
    if bid <= 0.0:
        if hp <= 2:
            bid = min(budget, DAILY_SALARY * 0.9)
        else:
            bid = min(budget, DAILY_SALARY * 0.3)

    return float(max(0.0, bid))
"""
