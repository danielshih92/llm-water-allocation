# ============================================================
# Experiment: exp_038
# Agent: Bob
# Source: exp_038
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

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    prev_bids = []
    prev_pressures = []  # (bid, opp_hp, opp_no_water_days)
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                bid_val = float(bid)
            except Exception:
                continue
            prev_bids.append(bid_val)
            prev_pressures.append((bid_val, int(opp.get('hp', 0)), int(opp.get('no_water_days', 0))))

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = (sum(prev_bids) / float(len(prev_bids))) if prev_bids else 0.0

    # Base aggressiveness scaled by our urgency.
    urgency = 0.0
    if hp <= 2:
        urgency += 1.0
    if no_water_days >= 2:
        urgency += 0.8
    if no_water_days >= 3:
        urgency += 1.0

    # Estimate how much to bid to likely secure at least our needed water.
    # If supply is tight, we bid more; if plentiful, bid less.
    supply_tightness = 0.0
    if supply <= float(WATER_REQ):
        supply_tightness = 1.0
    elif supply <= 18.0:
        supply_tightness = 0.7
    elif supply <= 22.0:
        supply_tightness = 0.4
    else:
        supply_tightness = 0.2

    # Opponent-reactive adjustment from yesterday.
    # If they were bidding aggressively, we slightly undercut to win efficiently.
    # If they were conservative, we push to secure water.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        target = avg_prev_bid + 2.0
        # Underbid relative to their peak to conserve budget.
        target = min(target, highest_prev_bid - 1.0)
        target += urgency * 6.0 + supply_tightness * 8.0
    elif highest_prev_bid >= DAILY_SALARY * 0.6:
        target = max(avg_prev_bid, highest_prev_bid - 2.0)
        target += urgency * 4.0 + supply_tightness * 6.0
    else:
        # They likely don't expect to be contested; bid enough to take water.
        # Keep it moderate to avoid burning budget.
        target = max(avg_prev_bid, DAILY_SALARY * 0.45)
        target += urgency * 5.0 + supply_tightness * 7.0

    # Convert target into a bid cap based on budget and requirement.
    # Bids should be within [0, budget]. Also avoid bidding above a reasonable bound.
    max_reasonable = min(budget, DAILY_SALARY * (0.95 if urgency > 0.7 else 0.75))

    # Ensure we bid at least something meaningful when supply is not too low.
    min_reasonable = 0.0
    if supply >= float(WATER_REQ):
        min_reasonable = DAILY_SALARY * 0.25
    if urgency > 0.9:
        min_reasonable = max(min_reasonable, DAILY_SALARY * 0.55)

    bid = float(target)
    if bid < min_reasonable:
        bid = min_reasonable
    if bid > max_reasonable:
        bid = max_reasonable

    # If budget is extremely low, bid what we can.
    if budget <= 1.0:
        return max(0.0, budget)

    # Final safety: never negative.
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
    day = day_context['day']

    # Identify alive opponents
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        # If alone, bid to ensure we get water
        return float(min(my_status['budget'], DAILY_SALARY * 0.6))

    # Read yesterday's bids from previous_trace for immediate pressure
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    pressure = 0.0
    if yesterday_bids:
        pressure = max(yesterday_bids)

    # Estimate how many water units are likely needed/available.
    # Goal: avoid no_water_days increment by securing at least WATER_REQ.
    # If supply is low, competition likely high -> bid more.
    supply_norm = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_norm = 0.5
    supply_norm = max(0.0, min(1.0, supply_norm))

    # Base bid: moderate, tuned to not enter Cindy's apparent high-bid loop.
    # If pressure is extremely high, we slightly increase to avoid losing to top bidder.
    base = DAILY_SALARY * (0.45 + 0.25 * supply_norm)

    # My urgency based on hp and no_water_days
    hp = float(my_status.get('hp', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    urgency = 0.0
    if hp <= 2.0:
        urgency = 0.35
    elif hp <= 4.0:
        urgency = 0.18
    else:
        urgency = 0.08

    if no_water_days >= 2:
        urgency += 0.15
    if no_water_days >= 4:
        urgency += 0.25

    # Convert yesterday pressure into an additive bump
    bump = 0.0
    if pressure >= DAILY_SALARY * 1.25:
        # Cindy-like aggressive pressure: raise some, but not to arms-race level
        bump = DAILY_SALARY * 0.10
    elif pressure >= DAILY_SALARY * 0.85:
        bump = DAILY_SALARY * 0.06
    elif pressure >= DAILY_SALARY * 0.55:
        bump = DAILY_SALARY * 0.03

    target = base * (1.0 + urgency) + bump

    # Ensure we bid at least enough to be competitive but cap to budget.
    budget = float(my_status.get('budget', 0.0))

    # Hard cap: never bid more than budget; also avoid extreme bids.
    cap = min(budget, DAILY_SALARY * 1.05)

    # If we are very low on budget, bid minimal to preserve survival
    if budget <= DAILY_SALARY * 0.25:
        return float(max(0.0, min(budget, DAILY_SALARY * 0.18)))

    # If supply is very low, slightly higher to secure WATER_REQ
    if supply < WATER_REQ + 3:
        target *= 1.12

    bid = float(min(cap, max(0.0, target)))

    # If bid is too low relative to supply competition, ensure a floor
    # (floor chosen to react to medium scenario without overpaying)
    floor_bid = DAILY_SALARY * (0.30 + 0.10 * supply_norm)
    if bid < floor_bid and budget > floor_bid:
        bid = float(min(cap, floor_bid))

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
    day = int(day_context['day'])

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace
    prev_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    clearing_hint = 0.0
    if prev_bids:
        clearing_hint = max(prev_bids)

    # If opponents were bidding extremely high, we must compete; otherwise bid moderately.
    # Target: slightly above the likely max previous bid, but capped by budget.
    # Use supply to decide aggressiveness: higher supply reduces need to overpay.
    supply_ratio = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    if supply_ratio < 0.0:
        supply_ratio = 0.0
    if supply_ratio > 1.0:
        supply_ratio = 1.0

    # Base pressure factor from my health/no-water streak
    hp_factor = 1.0
    if my_hp <= 2.0:
        hp_factor = 1.25
    elif my_hp <= 4.0:
        hp_factor = 1.15
    elif my_hp >= 8.0:
        hp_factor = 0.95

    no_water_factor = 1.0
    if my_no_water_days >= 2:
        no_water_factor = 1.2
    elif my_no_water_days >= 3:
        no_water_factor = 1.35

    # Aggression level based on yesterday's max bid
    # Cindy averaged ~150; if we see near that, we bid near but not equal to avoid waste.
    if clearing_hint >= 0.95 * 150.0:
        target = 145.0
    elif clearing_hint >= 120.0:
        target = clearing_hint + 3.0
    elif clearing_hint >= 60.0:
        target = max(DAILY_SALARY * 0.65, clearing_hint + 2.0)
    else:
        target = DAILY_SALARY * (0.55 + 0.25 * (1.0 - supply_ratio))

    # Adjust for supply: when supply is high, reduce target
    target *= (1.0 - 0.25 * supply_ratio)

    target *= hp_factor
    target *= no_water_factor

    # Ensure we can afford it; also keep minimum useful bid
    # If budget is very low, still try to buy water if we're at risk.
    if my_budget <= 0.0:
        return 0.0

    # Cap by budget and a reasonable upper bound (avoid irrational bids)
    cap = my_budget
    # If we're healthy, avoid spending everything
    if my_hp >= 7.0 and my_no_water_days <= 1:
        cap = min(cap, DAILY_SALARY * 0.9)

    bid = min(cap, target)

    # If bid becomes too small relative to WATER_REQ pressure, raise slightly
    # (We don't know exact conversion, so use a safe floor tied to DAILY_SALARY)
    if bid < DAILY_SALARY * 0.35 and (my_hp <= 4.0 or my_no_water_days >= 2):
        bid = min(cap, DAILY_SALARY * 0.6)

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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 1)

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append((oid, o))

    if not alive_opponents:
        return max(0.0, min(float(my_status.get('budget', 0.0)), DAILY_SALARY * 0.4))

    # Extract yesterday bids and classify pressure.
    yesterday_bids = []
    yesterday_by_opp = []
    for oid, o in alive_opponents:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                b_val = float(b)
            except Exception:
                continue
            yesterday_bids.append(b_val)
            yesterday_by_opp.append((oid, b_val))

    # If we have no yesterday bids, fall back to conservative mid bid.
    if not yesterday_bids:
        base = DAILY_SALARY * 0.55
        return max(0.0, min(float(my_status.get('budget', 0.0)), base))

    max_prev_bid = max(yesterday_bids)
    # Cindy likely consistently bids 135 and survives; avoid bidding near her.
    # Use her presence only to cap our bid.
    cindy_like = False
    for oid, b_val in yesterday_by_opp:
        if str(oid).lower() == 'cindy' and b_val >= 120:
            cindy_like = True
            break

    # Determine our urgency from hp and no_water_days.
    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Compute a target bid based on whether the strongest opponent was far above typical.
    # If strongest was low, we can bid slightly above second-highest to secure.
    sorted_bids = sorted(yesterday_bids)
    second_highest = sorted_bids[-2] if len(sorted_bids) >= 2 else sorted_bids[-1]

    # If max_prev_bid is extremely high (Cindy), we should not chase; bid near second_highest.
    if max_prev_bid >= 120:
        target = second_highest + 1.5
        # Cap to avoid overpaying against Cindy.
        cap = DAILY_SALARY * 0.85
        if cindy_like:
            cap = min(cap, 60.0)
    else:
        # Otherwise, bid above the strongest likely to win.
        target = max_prev_bid + 2.0

    # Urgency adjustments.
    if hp <= 2 or no_water_days >= 2:
        target *= 1.35
    elif hp <= 4 or no_water_days == 1:
        target *= 1.15

    # Supply-based scaling: higher supply means easier to win; bid less.
    # Ensure indices are safe by using int() anywhere needed (no lists here).
    if supply >= 21.0:
        target *= 0.85
    elif supply <= 17.0:
        target *= 1.05

    # Final clamp: cannot exceed budget.
    if budget <= 0.0:
        return 0.0

    # Keep within a reasonable fraction of budget.
    max_affordable = budget
    # If we are low on budget, scale down.
    if budget < DAILY_SALARY:
        max_affordable = min(max_affordable, budget)

    bid = max(0.0, min(float(max_affordable), float(target)))

    # If bid is too low to matter and we are urgent, ensure a minimum.
    if (hp <= 2 or no_water_days >= 2) and bid < 20.0:
        bid = min(budget, 25.0)

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

    supply = day_context.get('supply', 0)
    day = day_context.get('day', 0)

    hp = my_status.get('hp', 0)
    budget = my_status.get('budget', 0)
    no_water_days = my_status.get('no_water_days', 0)

    alive_opponents = []
    for o in opponents_status.values():
        if o.get('alive', True):
            alive_opponents.append(o)

    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday bids from previous_trace (only immediate reaction)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Estimate likely competitive level
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid
        # If others bid high, we slightly overtake; otherwise bid near the likely clearing band.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            base = max(second_prev_bid * 1.02, DAILY_SALARY * 0.65)
        else:
            base = max(second_prev_bid * 0.95, DAILY_SALARY * 0.55)
    else:
        base = DAILY_SALARY * 0.55

    # Supply pressure: lower supply means higher chance of losing.
    # Use thresholds around given range [15,25].
    if supply <= (MIN_SUPPLY + 2):
        base *= 1.15
    elif supply >= (MAX_SUPPLY - 2):
        base *= 0.95

    # Own urgency: if low hp or accumulating no-water days, increase bid.
    if hp <= 2:
        base *= 1.35
    elif hp <= 4:
        base *= 1.20

    if no_water_days >= 2:
        base *= 1.15

    # Keep bids within a reasonable fraction of budget.
    cap = budget
    # Also avoid overcommitting: target around 0.9*salary max unless hp is critical.
    if hp > 2:
        cap = min(cap, DAILY_SALARY * 0.95)
    else:
        cap = min(cap, DAILY_SALARY * 1.1)

    bid = min(cap, base)

    # Ensure non-negative and at least a small amount if we can.
    if bid < 0:
        bid = 0
    if bid == 0 and budget > 0:
        bid = min(budget, DAILY_SALARY * 0.25)

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
    day = day_context['day']

    # Alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # If no one is alive, spend to ensure survival
    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Extract yesterday bids from previous_trace
    yesterday_bids = []
    yesterday_hps = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        if isinstance(prev, dict) and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass
            try:
                yesterday_hps.append(float(prev.get('hp_after', o.get('hp', 0))))
            except Exception:
                pass

    # Baseline from supply: with 15-25 supply, typical number of winners is limited.
    # We want to be competitive but not match Cindy's consistent high bids.
    # Use a target fraction of DAILY_SALARY based on our HP.
    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])

    # Compute a conservative target using yesterday's distribution
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        # If someone overbid hard yesterday, we slightly undercut to win while saving budget.
        # Cindy's behavior tends to create a high ceiling; aim around 0.75 of max_prev or a floor.
        target = 0.75 * max_prev
    else:
        target = DAILY_SALARY * 0.55

    # Supply pressure adjustment: higher supply reduces need to overbid
    # Normalize supply to [0,1]
    denom = (MAX_SUPPLY - MIN_SUPPLY)
    if denom <= 0:
        s_norm = 0.5
    else:
        s_norm = (supply - MIN_SUPPLY) / denom
    # When supply is low, increase bids; when high, decrease.
    pressure = 1.0 + (0.25 * (0.5 - s_norm))  # low supply => >1

    # HP-based risk control
    if my_hp <= 2:
        hp_mult = 1.15
    elif my_hp <= 4:
        hp_mult = 1.05
    else:
        hp_mult = 0.95

    # Also react to no_water_days: if we are close to starvation, bid more.
    no_water_days = int(my_status['no_water_days'])
    if no_water_days >= 2:
        starvation_mult = 1.12
    elif no_water_days >= 1:
        starvation_mult = 1.06
    else:
        starvation_mult = 0.98

    # Final candidate bid
    candidate = target * pressure * hp_mult * starvation_mult

    # Keep within reasonable bounds: between 0.25 and 0.95 of DAILY_SALARY, but never above budget.
    lower = DAILY_SALARY * 0.25
    upper = DAILY_SALARY * 0.95
    bid = max(lower, min(upper, candidate))

    # Ensure we don't exceed budget
    if my_budget <= 0:
        return 0.0
    bid = min(bid, my_budget)

    # If budget is very tight, bid a smaller fraction rather than risking overspend
    if my_budget < DAILY_SALARY * 0.35:
        bid = min(bid, my_budget * 0.9)

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

    supply = day_context['supply']
    day = day_context['day']

    # Determine urgency from hp/no_water_days
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    # Alive opponents and yesterday bids
    alive_opponents = [o for o in opponents_status.values() if o.get('alive', False)]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Supply pressure: higher supply reduces need to overbid
    # Map supply to a 0..1 pressure where 1 means low supply
    if MAX_SUPPLY == MIN_SUPPLY:
        supply_pressure = 0.5
    else:
        supply_pressure = (MAX_SUPPLY - float(supply)) / (MAX_SUPPLY - MIN_SUPPLY)
        if supply_pressure < 0:
            supply_pressure = 0.0
        if supply_pressure > 1:
            supply_pressure = 1.0

    # Base bid target derived from opponent behavior
    # Cindy's recent max around ~115; use that as a near-win anchor.
    # If we see any high yesterday bids, slightly undercut them.
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        second_prev = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev

        # If someone was bidding very high, we try to match/just beat.
        # Otherwise, we bid around the mid-high band.
        if highest_prev >= 110:
            target = highest_prev - 1.0
        else:
            # Use a blend of second-highest and a band near 100
            target = max(95.0, second_prev + 2.0)
    else:
        # No signal: conservative mid bid
        target = 90.0 + 10.0 * supply_pressure

    # Adjust for our survival urgency
    if hp <= 2 or no_water_days >= 1:
        # Need water soon; be more aggressive
        target *= 1.15
    elif hp <= 4:
        target *= 1.05
    else:
        target *= (0.95 + 0.1 * supply_pressure)

    # Convert target to a feasible bid within budget
    # Also avoid bidding above what we can sustain (budget can be large, but keep some reserve).
    # Reserve more when hp is healthy.
    reserve_frac = 0.25 if hp > 4 else 0.10
    max_affordable = max(0.0, budget * (1.0 - reserve_frac))

    # Final clamp: at most DAILY_SALARY*1.3 and at least a small positive bid if possible
    upper = min(max_affordable, DAILY_SALARY * 1.3)
    lower = 5.0
    bid = target
    if bid < lower:
        bid = lower
    if bid > upper:
        bid = upper

    # If budget is too small, bid whatever remains
    if bid > budget:
        bid = budget

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
    day = day_context.get('day', 0)

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Extract yesterday bids from immediate previous_trace
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Baseline budget guardrails
    # We want to avoid going broke; also ensure we can pay on multiple days.
    budget_cap = my_budget

    # Estimate required aggressiveness from yesterday bids
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    # If someone was bidding very high, we target a strong but slightly conservative bid.
    # If our HP is low or we've missed water recently, we bid more.
    pressure = 0.0
    if highest_prev_bid >= DAILY_SALARY * 1.2:
        pressure = 1.0
    elif highest_prev_bid >= DAILY_SALARY * 0.9:
        pressure = 0.75
    elif highest_prev_bid >= DAILY_SALARY * 0.6:
        pressure = 0.5
    else:
        pressure = 0.35

    # Supply-based adjustment: higher supply means we can bid less to still get enough.
    # Use a normalized factor within [0,1].
    supply_norm = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (supply - float(MIN_SUPPLY)) / float(MAX_SUPPLY - MIN_SUPPLY)
        if supply_norm < 0.0:
            supply_norm = 0.0
        if supply_norm > 1.0:
            supply_norm = 1.0

    # Base bid target
    # When pressure is high, move toward ~0.75*DAILY_SALARY; otherwise ~0.55*DAILY_SALARY.
    base = DAILY_SALARY * (0.55 + 0.2 * pressure)

    # If supply is high, reduce bid a bit; if low, increase.
    base = base * (1.0 + 0.15 * (0.5 - supply_norm))

    # React to our own risk
    if my_hp <= 2 or my_no_water_days >= 2:
        base = base * 1.35
    elif my_hp >= 7 and my_no_water_days == 0:
        base = base * 0.9

    # Avoid overspending: if we are far from needing water, keep lower.
    # Also, do not exceed a fraction of budget to survive multiple days.
    # With 10 episode days, a conservative fraction helps.
    budget_fraction = 0.25
    if my_hp <= 3 or my_no_water_days >= 2:
        budget_fraction = 0.45
    elif my_hp >= 7:
        budget_fraction = 0.2

    hard_limit = my_budget * budget_fraction

    # If yesterday bids indicate extreme competition, slightly underbid the average-high.
    # Since bids are hidden, we use yesterday's max/avg as a proxy.
    target = base
    if highest_prev_bid > 0:
        # If opponents were bidding near/above our target, raise a bit but not to the max.
        if avg_prev_bid > target:
            target = (target + avg_prev_bid) / 2.0
        # If the max was extremely high, we try to be competitive but not match it.
        if highest_prev_bid >= DAILY_SALARY * 1.2:
            target = min(target, highest_prev_bid * 0.85)

    bid = float(target)

    # Final clamp
    if bid < 0.0:
        bid = 0.0
    bid = min(bid, hard_limit, budget_cap)

    # Ensure at least something meaningful if we have budget
    if my_budget > 0.0 and bid == 0.0:
        bid = min(my_budget, DAILY_SALARY * 0.1)

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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opponents = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Read only yesterday's immediate pressure signal from previous_trace
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    prev_bids.append(float(b))
                except Exception:
                    pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Supply pressure: if supply is close to our requirement, we must bid more to ensure allocation
    # Convert to an integer estimate of how many full water units could be funded in aggregate.
    # (We only use it as a heuristic; indices are not used.)
    supply_ratio = supply / float(WATER_REQ)

    # Base willingness to pay
    # If opponents were bidding high yesterday, we slightly increase to avoid being outbid.
    base = DAILY_SALARY * 0.55

    if highest_prev_bid >= DAILY_SALARY * 0.85:
        base = DAILY_SALARY * 0.65
    elif highest_prev_bid >= DAILY_SALARY * 0.65:
        base = DAILY_SALARY * 0.60

    # Tight supply -> increase
    if supply_ratio < 2.0:
        base *= 1.15
    elif supply_ratio < 2.5:
        base *= 1.05

    # If I'm in danger, bid more aggressively
    if hp <= 2 or no_water_days >= 2:
        base *= 1.35
    elif hp <= 3:
        base *= 1.15

    # Cap by budget and also avoid overcommitting when budget is low
    # Keep some reserve for later days.
    reserve_fraction = 0.25
    max_affordable = max(0.0, budget * (1.0 - reserve_fraction))

    # If budget is extremely low, bid just enough to extend survival
    if budget < DAILY_SALARY * 0.6:
        if hp <= 2:
            bid = min(budget, DAILY_SALARY * 0.9)
        else:
            bid = min(budget, DAILY_SALARY * 0.6)
        return float(bid)

    # Otherwise, bid around base, with a small nudge above the highest_prev_bid only when needed
    # (We don't know today's bids, so we use a conservative nudge.)
    nudge = 0.0
    if highest_prev_bid > 0:
        # If yesterday's highest bid was very high, match partially.
        if highest_prev_bid >= DAILY_SALARY * 1.0:
            nudge = DAILY_SALARY * 0.08
        elif highest_prev_bid >= DAILY_SALARY * 0.85:
            nudge = DAILY_SALARY * 0.05

    bid = base + nudge

    # Ensure within bounds
    bid = min(bid, max_affordable)
    bid = max(0.0, bid)

    # If we still bid too low relative to yesterday's top, slightly increase.
    if highest_prev_bid > 0 and bid < highest_prev_bid * 0.75 and hp <= 4:
        bid = min(max_affordable, highest_prev_bid * 0.8)

    return float(bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace only (immediate reaction)
    prev_bids = []
    for o in alive_opps:
        pt = o.get('previous_trace', {})
        b = pt.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate how many rounds of water we can afford if we win today
    # (not perfect, but helps avoid bankruptcy)
    # If supply is enough to cover our requirement, winning is valuable.
    supply_covers = supply >= WATER_REQ

    # Risk-based bid scaling
    # If we are already in danger of running out, bid more.
    danger = (hp <= 2.5) or (no_water_days >= 2)

    # If opponents were aggressive yesterday (high bids), slightly increase to compete.
    aggressive = highest_prev_bid >= (DAILY_SALARY * 0.8)

    # Baseline target: moderate spend to secure water when supply covers requirement.
    if supply_covers:
        base = DAILY_SALARY * 0.45
    else:
        base = DAILY_SALARY * 0.25

    if danger:
        bid = base + DAILY_SALARY * 0.35
    elif aggressive:
        bid = base + DAILY_SALARY * 0.15
    else:
        bid = base

    # Keep bid within budget and avoid reckless spending
    # Also cap by a fraction of budget to reduce variance.
    max_reasonable = budget * 0.35 if budget > 0 else 0.0
    bid = min(bid, max_reasonable if max_reasonable > 0 else bid)

    # If budget is very low, bid whatever we can to prevent death.
    if budget <= DAILY_SALARY * 0.2:
        bid = budget * 0.9

    # Ensure non-negative
    if bid < 0:
        bid = 0.0

    return float(bid)
"""
