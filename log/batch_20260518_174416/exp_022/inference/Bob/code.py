# ============================================================
# Experiment: exp_022
# Agent: Bob
# Source: exp_022
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

    # Alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # If no opponents, bid to cover requirement safely
    if not alive_opps:
        target = WATER_REQ
        return int(min(my_status['budget'], max(0, target)))

    # Yesterday reaction: if any opponent bid info exists, mirror pressure
    yesterday_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Baseline: estimate likely clearing price from supply range
    # With supply 15-25, a reasonable competitive bid is around requirement plus a small premium.
    # Premium increases slightly as supply increases (more competition) but stays capped.
    supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY + 1e-9)
    premium = 2.0 + 3.0 * supply_norm
    base_bid = WATER_REQ + premium

    # If we have yesterday pressure, respond
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If they were bidding very high, we should not underbid too much.
        if highest_prev_bid >= 0.85 * DAILY_SALARY:
            if my_status.get('hp', 0) > 3 and my_status.get('no_water_days', 0) <= 1:
                bid = base_bid + 4.0
            else:
                bid = base_bid + 12.0
        else:
            # Otherwise, try to slightly outbid their typical level.
            bid = max(base_bid, highest_prev_bid + 1.5)
    else:
        bid = base_bid

    # Personal urgency adjustments
    hp = float(my_status.get('hp', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    if hp <= 2:
        bid *= 1.35
    elif hp <= 4:
        bid *= 1.15

    if no_water_days >= 2:
        bid *= 1.25

    # Budget and safety caps
    budget = float(my_status.get('budget', 0))
    # Never bid more than budget; also avoid extreme bids beyond daily salary scale.
    cap = min(budget, DAILY_SALARY * 0.95)
    bid_int = int(max(0, min(cap, bid)))

    # Ensure at least 1 if we can afford it (to avoid zero bids when competing)
    if bid_int <= 0 and budget >= 1:
        bid_int = 1

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

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    my_hp = my_status.get('hp', 0)
    my_budget = my_status.get('budget', 0)
    my_no_water_days = my_status.get('no_water_days', 0)

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Extract yesterday bids to infer who is aggressive.
    prev_bids = []
    for opp_id, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            prev_bids.append((opp_id, b))

    highest_prev_bid = max([b for _, b in prev_bids], default=0.0)
    # Identify Cindy's yesterday bid if present.
    cindy_prev_bid = None
    for opp_id, b in prev_bids:
        if opp_id == 'Cindy':
            cindy_prev_bid = b
            break

    # Base bid depends on supply level: with higher supply, we can bid less.
    # Use a conservative mapping.
    if supply <= float(MIN_SUPPLY):
        supply_factor = 1.0
    elif supply >= float(MAX_SUPPLY):
        supply_factor = 0.65
    else:
        # Linear interpolation between 1.0 at 15 and 0.65 at 25
        supply_factor = 1.0 - (float(supply) - float(MIN_SUPPLY)) * (1.0 - 0.65) / (float(MAX_SUPPLY) - float(MIN_SUPPLY))

    # If someone previously bid extremely high, they likely will continue.
    # Cindy survived with very high average bids; treat her as a likely constant aggressor.
    aggressive_pressure = 0.0
    if highest_prev_bid >= DAILY_SALARY * 1.3:
        aggressive_pressure += 1.0
    if cindy_prev_bid is not None and cindy_prev_bid >= DAILY_SALARY * 1.3:
        aggressive_pressure += 1.0

    # Urgency from our hp/no-water days.
    urgency = 0.0
    if my_hp <= 2:
        urgency = 1.0
    elif my_hp <= 4:
        urgency = 0.75
    elif my_hp <= 6:
        urgency = 0.45
    else:
        urgency = 0.25

    if my_no_water_days >= 2:
        urgency = max(urgency, 0.75)

    # Target bid: try to secure water when needed, otherwise avoid overpaying.
    # With aggressive pressure, we slightly increase, but cap to avoid burning budget.
    base = DAILY_SALARY * (0.45 * supply_factor)
    if aggressive_pressure >= 1.0:
        base *= 1.15
    if aggressive_pressure >= 2.0:
        base *= 1.25

    # Escalate with urgency.
    if urgency >= 0.75:
        target = DAILY_SALARY * (0.85 * supply_factor)
    elif urgency >= 0.45:
        target = DAILY_SALARY * (0.6 * supply_factor)
    else:
        target = base

    # If Cindy bid extremely high yesterday, we may need to match to avoid losing.
    if cindy_prev_bid is not None and cindy_prev_bid >= DAILY_SALARY * 1.3:
        target = max(target, min(my_budget, cindy_prev_bid * 0.85))

    # Ensure we never bid more than budget, and keep a minimum bid if we must compete.
    # Also avoid bidding above a reasonable fraction of budget.
    max_reasonable = my_budget * 0.35
    if urgency >= 0.75:
        max_reasonable = my_budget * 0.65
    elif urgency >= 0.45:
        max_reasonable = my_budget * 0.5

    bid = min(my_budget, max_reasonable, target)

    # If bid is too low relative to aggressive history, bump slightly but still bounded.
    if highest_prev_bid > 0 and highest_prev_bid >= DAILY_SALARY * 0.7:
        min_compete = min(my_budget, DAILY_SALARY * 0.55 * supply_factor)
        if bid < min_compete and urgency >= 0.45:
            bid = min_compete

    # Final safety: if budget is tiny, bid whatever we can.
    if bid <= 0:
        bid = min(my_budget, DAILY_SALARY * 0.1)

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
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    # If no opponents alive, bid conservatively.
    if not alive_opponents:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from each opponent's previous_trace.
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

    # Supply pressure: if supply is low, competition for water is higher.
    # Normalize to [0,1] where 0=MIN_SUPPLY, 1=MAX_SUPPLY.
    if MAX_SUPPLY - MIN_SUPPLY > 0:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_norm = 0.5
    supply_norm = max(0.0, min(1.0, supply_norm))

    # Base aggressiveness: Cindy survived with high average bids; match only when needed.
    # If we are low hp or have had no water days, we must secure water.
    must_have = (hp <= 3.0) or (no_water_days >= 2)

    # Estimate how much to bid.
    # - If someone previously bid very high, raise our bid to avoid losing.
    # - Otherwise, bid around a fraction of salary.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # High pressure environment.
        if must_have:
            target = DAILY_SALARY * 0.95
        else:
            target = max(highest_prev_bid + 2.0, DAILY_SALARY * 0.55)
    else:
        # Moderate pressure environment.
        # If supply is low, increase slightly.
        supply_factor = 1.0 + (1.0 - supply_norm) * 0.35
        if must_have:
            target = DAILY_SALARY * 0.75 * supply_factor
        else:
            target = DAILY_SALARY * 0.45 * supply_factor

    # Late-episode slight escalation to avoid running out.
    if day >= 7:
        target *= 1.08

    # Ensure we never exceed budget.
    bid = max(0.0, min(budget, target))
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

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    hp = my_status.get('hp', 0)
    budget = my_status.get('budget', 0.0)
    no_water_days = my_status.get('no_water_days', 0)

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday bids for immediate pressure signal
    prev_bids = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            prev_bids.append(float(b))

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate how many water units might be needed from supply
    # Use int() to avoid float indexing issues (though we don't index lists here)
    supply_int = float(supply)
    # Approximate number of
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

    # Identify alive opponents
    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    # If no opponents are alive, conserve budget
    if not alive_opponents:
        return max(0.0, min(float(my_status.get('budget', 0.0)), DAILY_SALARY * 0.4))

    # Read yesterday bids from each opponent's previous_trace
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    yesterday_bids.append(float(b))
                except Exception:
                    pass

    # Base bid aggressiveness: we expect Cindy/Eric-style high bids; avoid matching max
    # Use supply pressure to slightly increase bids when supply is scarce.
    supply_ratio = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_ratio = (supply - float(MIN_SUPPLY)) / (float(MAX_SUPPLY) - float(MIN_SUPPLY))
    supply_ratio = max(0.0, min(1.0, supply_ratio))
    scarcity_factor = 1.0 + (1.0 - supply_ratio) * 0.25  # up to +25% when supply is low

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))

    # If we saw a very high bid yesterday, bid just above a likely contention level.
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # Estimate a "contention" threshold as the 2nd-highest if possible
        sorted_bids = sorted(yesterday_bids)
        contention = sorted_bids[-2] if len(sorted_bids) >= 2 else sorted_bids[-1]

        # If contention is high, we need to be competitive but not reckless.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # With high hp, we can afford a medium bid; with low hp, pay more.
            if my_hp >= 7:
                target = max(contention * 0.98, DAILY_SALARY * 0.55)
            elif my_hp >= 4:
                target = max(contention * 1.02, DAILY_SALARY * 0.7)
            else:
                target = max(contention * 1.08, DAILY_SALARY * 0.9)
        else:
            # Otherwise, bid around the contention level plus a small premium.
            if my_hp >= 7:
                target = max(contention * 0.95, DAILY_SALARY * 0.5)
            elif my_hp >= 4:
                target = max(contention * 1.0, DAILY_SALARY * 0.65)
            else:
                target = max(contention * 1.08, DAILY_SALARY * 0.85)
    else:
        # No bid info: default moderate
        if my_hp >= 7:
            target = DAILY_SALARY * 0.55
        elif my_hp >= 4:
            target = DAILY_SALARY * 0.7
        else:
            target = DAILY_SALARY * 0.9

    target *= scarcity_factor

    # Hard caps to avoid overbidding beyond reasonable daily spend.
    # Keep below about 1.8*DAILY_SALARY unless budget forces it.
    cap = DAILY_SALARY * 1.8
    bid = min(my_budget, cap, target)

    # Ensure non-negative
    if bid < 0.0:
        bid = 0.0
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
    day = day_context.get('day', 0)

    # Alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # If no opponents, spend to meet requirement
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.5))

    # Read yesterday bids (only immediate reaction)
    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Estimate how many water units are likely available relative to requirement
    # supply is in [15,25], so possible allocations are limited; aim for at-least-one unit.
    # Convert supply to an approximate number of water blocks (integer count).
    supply_blocks = int(supply // float(WATER_REQ)) if WATER_REQ > 0 else 0
    if supply_blocks < 1:
        supply_blocks = 1

    # Identify yesterday's aggressive behavior
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    lowest_prev_bid = min(yesterday_bids) if yesterday_bids else 0.0

    # Pressure threshold: Cindy's max bids were ~148.5; use a conservative fraction.
    pressure = highest_prev_bid

    # If we are safe on hp, avoid matching extreme bids. If hp is low, bid more.
    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Base bid depends on supply scarcity
    scarcity = 1.0
    if supply <= float(MIN_SUPPLY) + 0.5:
        scarcity = 1.15
    elif supply >= float(MAX_SUPPLY) - 0.5:
        scarcity = 0.95

    # If we're close to failing, bid aggressively to secure water
    if hp <= 2 or no_water_days >= 1:
        target = DAILY_SALARY * 0.75 * scarcity
    else:
        # Otherwise, bid to beat typical bids but stay below the highest pressure
        # Use highest_prev_bid but discount it to avoid overpaying.
        discount = 0.72
        target = max(DAILY_SALARY * 0.45, pressure * discount)
        # If yesterday bids were generally low, we can bid lower
        if lowest_prev_bid > 0 and pressure < DAILY_SALARY * 0.9:
            target = max(DAILY_SALARY * 0.42, lowest_prev_bid * 0.95)

    # Cap by budget and keep within reasonable range
    bid = float(min(budget, target))

    # Ensure non-negative
    if bid < 0:
        bid = 0.0

    # If budget is tiny, still try to outbid the lowest previous bidder slightly
    if budget < DAILY_SALARY * 0.2 and lowest_prev_bid > 0:
        bid = float(min(budget, lowest_prev_bid + 1.0))
        if bid < 0:
            bid = 0.0

    return bid
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
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday bids from immediate previous_trace only
    prev_bids = []
    prev_pressures = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass
        # Use yesterday hp_after as a proxy for how hard they were hit
        hp_after = prev.get('hp_after', None)
        if hp_after is not None:
            try:
                prev_pressures.append((float(hp_after), float(b) if b is not None else 0.0))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev_bid

    # Supply pressure: moderate supply implies bidding competition; lower supply implies more aggressive bids.
    # Normalize supply to [0,1]
    if MAX_SUPPLY == MIN_SUPPLY:
        supply_norm = 0.5
    else:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
        if supply_norm < 0.0:
            supply_norm = 0.0
        if supply_norm > 1.0:
            supply_norm = 1.0

    # Base bid level: try to slightly beat the top yesterday bid when it was large.
    # If highest was high, we match/undercut depending on our hp.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Opponents were willing to spend heavily; ensure we don't get squeezed.
        if hp <= 2 or no_water_days >= 2:
            target = max(highest_prev_bid * 0.98, second_prev_bid * 1.02)
        else:
            target = max(highest_prev_bid * 0.80, second_prev_bid * 1.05)
    else:
        # Otherwise, bid around a mid level to win water share without burning budget.
        # Higher supply => lower bid.
        mid = DAILY_SALARY * (0.62 - 0.25 * supply_norm)
        # If we have a competitor with a meaningful prior bid, nudge upward.
        target = max(mid, (second_prev_bid * 0.9 + highest_prev_bid * 0.1))

    # Convert target into a budget-safe bid with HP-aware risk control.
    # If low HP, be more aggressive; if high HP, conserve.
    if hp <= 1:
        cap = DAILY_SALARY * 0.95
    elif hp == 2:
        cap = DAILY_SALARY * 0.85
    else:
        cap = DAILY_SALARY * (0.70 - 0.10 * supply_norm)
        if cap < DAILY_SALARY * 0.45:
            cap = DAILY_SALARY * 0.45

    # If budget is very low, don't exceed it.
    bid = min(budget, target, cap)

    # Ensure non-negative and at least small bid if budget allows.
    if bid < 0.0:
        bid = 0.0

    # If we are at risk of immediate failure (no_water_days high), push harder.
    if no_water_days >= 3 and budget > 0:
        bid = min(budget, max(bid, DAILY_SALARY * 0.75))

    # If supply is extremely low within the range, increase slightly.
    if supply <= (MIN_SUPPLY + 1.0):
        bid = min(budget, bid * 1.10)

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

    # Alive opponents
    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive'):
            alive_opponents.append(o)

    if not alive_opponents:
        # If alone, bid conservatively to keep budget
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Extract yesterday bids from immediate previous_trace
    yesterday_bids = []
    for o in alive_opponents:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Baseline: how many water units we can potentially win/need
    # If supply is high, we can afford lower bid; if low, we must secure water.
    # supply is total supply, water requirement is per agent.
    # We approximate urgency by whether supply is close to our requirement.
    urgency = 0.0
    if supply <= WATER_REQ:
        urgency = 1.0
    elif supply <= WATER_REQ + 2:
        urgency = 0.8
    elif supply <= WATER_REQ + 6:
        urgency = 0.5
    else:
        urgency = 0.25

    # If opponents were bidding high yesterday, we slightly overbid when urgency is moderate/high.
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid
        # Estimate a
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context['supply'])
    day = day_context['day']

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    # If no opponents alive, bid minimal to conserve.
    if not alive_opps:
        bid = DAILY_SALARY * 0.25
        if budget < bid:
            return max(0.0, budget)
        return bid

    # Read yesterday bids from immediate previous_trace only.
    prev_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', None) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Determine urgency from our HP and no-water streak.
    urgency = 0
    if hp <= 2.0:
        urgency += 2
    if hp <= 4.0:
        urgency += 1
    if no_water_days >= 2:
        urgency += 1

    # Supply pressure: if supply is low, competition is higher; raise bid slightly.
    # Use a conservative scale; avoid matching Cindy/Eric bids unless necessary.
    if supply <= 17.0:
        supply_factor = 1.15
    elif supply <= 21.0:
        supply_factor = 1.05
    else:
        supply_factor = 0.95

    # Baseline bid: aim around half salary to win occasionally without burning budget.
    # If yesterday aggressors bid extremely high, we still avoid overbidding unless urgency is high.
    aggressive_threshold = DAILY_SALARY * 1.2  # ~108

    if urgency >= 2:
        # High urgency: bid closer to aggressive level but cap.
        target = max(DAILY_SALARY * 0.75, highest_prev_bid * 0.65)
    elif urgency == 1:
        target = max(DAILY_SALARY * 0.55, highest_prev_bid * 0.45)
    else:
        # Low urgency: do not chase; bid just enough.
        if highest_prev_bid >= aggressive_threshold:
            target = DAILY_SALARY * 0.40
        else:
            target = max(DAILY_SALARY * 0.45, highest_prev_bid * 0.30)

    target *= supply_factor

    # Ensure we don't bid more than we can afford; keep non-negative.
    if budget <= 0.0:
        return 0.0

    if target > budget:
        target = budget

    # Also avoid bidding too low when supply is scarce and we need water to prevent death.
    # If we've already had 1+ no-water days, increase floor.
    min_floor = 0.0
    if no_water_days >= 1:
        min_floor = DAILY_SALARY * 0.35
    if hp <= 4.0:
        min_floor = max(min_floor, DAILY_SALARY * 0.5)

    if target < min_floor:
        target = min_floor
        if target > budget:
            target = budget

    return max(0.0, float(target))
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

    # Identify alive opponents and collect yesterday bids
    alive_opps = [o for o in opponents_status.values() if o.get('alive')]
    if not alive_opps:
        # If nobody to compete with, bid conservatively to preserve budget
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Baseline based on our hp
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    # Estimate how many
"""
