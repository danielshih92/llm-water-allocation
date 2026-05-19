# ============================================================
# Experiment: exp_021
# Agent: Bob
# Source: exp_021
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context.get('supply', MIN_SUPPLY))
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Alive opponents
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    # If no opponents, bid just enough to satisfy requirement
    if not alive_opps:
        bid = WATER_REQ
        return float(min(budget, bid))

    # Read yesterday bids from previous_trace (immediate reaction)
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Survival logic
    if hp <= 2 or no_water_days >= 2:
        # Go high but cap by budget
        return float(min(budget, DAILY_SALARY * 0.95))

    # If opponents were bidding heavily yesterday, slightly increase to contest
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        # If they signaled high pressure, match/beat moderately
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            target = min(budget, DAILY_SALARY * 0.65)
        else:
            # Otherwise, bid near requirement plus a small premium
            # Premium scales with how tight the supply is
            tightness = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
            premium = 2.0 + 6.0 * float(tightness)
            target = WATER_REQ + premium
            target = min(target, DAILY_SALARY * 0.75)
        return float(max(0.0, min(budget, target)))

    # Default when no previous_trace data: bid moderately based on supply tightness
    tightness = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    base = WATER_REQ + (3.0 + 6.0 * float(tightness))
    # Keep it conservative to avoid overpaying
    target = min(base, DAILY_SALARY * 0.6)
    return float(max(0.0, min(budget, target)))
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

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Read only yesterday's immediate trace
    prev_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Pressure proxy: if someone bid very high yesterday, assume competition for scarce water
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Determine required aggressiveness based on supply and my health
    # If supply is high, fewer bidders need to overbid for survival; if low, competition is tighter.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0..1
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Base bid target: scale with supply and my hp pressure
    if hp <= 2.0 or no_water_days >= 2:
        # Critical: bid to secure water
        base = DAILY_SALARY * (0.75 + 0.2 * (1.0 - supply_ratio))
    elif hp <= 4.0:
        base = DAILY_SALARY * (0.6 + 0.2 * (1.0 - supply_ratio))
    else:
        base = DAILY_SALARY * (0.45 + 0.15 * (1.0 - supply_ratio))

    # React to yesterday's highest bid: if rivals were willing to pay near/above salary, we match enough
    # to avoid being outbid, but do not chase extreme values.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        base = max(base, DAILY_SALARY * 0.65)
    elif highest_prev_bid >= DAILY_SALARY * 0.55:
        base = max(base, DAILY_SALARY * 0.5)

    # Convert to final bid with budget cap and slight random-free adjustment by day parity
    parity_boost = 1.02 if (day % 2 == 0) else 0.98
    target = base * parity_boost

    # Hard cap: never exceed budget
    bid = min(budget, target)

    # Ensure minimum meaningful bid to avoid guaranteed loss when supply is scarce
    # (keep small if budget is low)
    min_bid = min(budget, DAILY_SALARY * 0.25)
    if bid < min_bid:
        bid = min_bid

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

    # Basic safety
    if my_status['budget'] <= 0:
        return 0

    # Alive opponents and yesterday bids
    alive_opponents = []
    yesterday_bids = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            if isinstance(prev, dict):
                b = prev.get('bid', None)
                if b is not None:
                    yesterday_bids.append(float(b))

    # If no info, conservative
    if not alive_opponents:
        return min(my_status['budget'], int(DAILY_SALARY * 0.5))

    # Use Cindy/Alex pressure from yesterday
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how many water units we can buy with our budget (rough)
    # Not exact game mechanics, but helps scale aggression.
    budget = float(my_status['budget'])
    hp = float(my_status['hp'])

    # Supply pressure: medium scenario suggests supply is near mid; bid slightly above typical
    # Normalize supply to [0,1]
    s_norm = (float(supply) - float(MIN_SUPPLY)) / (float(MAX_SUPPLY) - float(MIN_SUPPLY))
    if s_norm < 0:
        s_norm = 0.0
    if s_norm > 1:
        s_norm = 1.0

    # Base aggression factor
    # If Cindy was near the top, we need to overtake; else we can undercut.
    # Use a threshold tied to yesterday's best.
    # Target: win enough water to preserve HP; if HP low, bid more.
    if highest_prev_bid >= DAILY_SALARY * 1.35:
        # Cindy-like aggressive day
        if hp <= 2:
            target = DAILY_SALARY * (0.95 + 0.15 * s_norm)
        elif hp <= 4:
            target = DAILY_SALARY * (0.75 + 0.10 * s_norm)
        else:
            target = DAILY_SALARY * (0.65 + 0.10 * s_norm)
    elif highest_prev_bid >= DAILY_SALARY * 0.95:
        # Moderate pressure
        if hp <= 2:
            target = DAILY_SALARY * (0.85 + 0.10 * s_norm)
        else:
            target = DAILY_SALARY * (0.55 + 0.10 * s_norm)
    else:
        # Low pressure: bid just enough
        if hp <= 2:
            target = DAILY_SALARY * (0.75 + 0.10 * s_norm)
        else:
            target = DAILY_SALARY * (0.45 + 0.08 * s_norm)

    # Small bump to beat the previous highest bid when near win-critical
    # (We don't know today's bids, so use a gentle +1.5 rather than jumping to max.)
    target = float(target)
    if highest_prev_bid > 0:
        target = max(target, highest_prev_bid + 1.5)

    # If our budget is low relative to target, scale down
    if budget < target:
        target = budget * 0.95

    # Ensure integer and non-negative
    bid = int(target)
    if bid < 0:
        bid = 0

    # Never bid more than budget
    if bid > int(budget):
        bid = int(budget)

    return bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Identify alive opponents
    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append((opp_id, opp))

    # If no opponents alive, bid to cover requirement efficiently
    if not alive_opponents:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace (immediate reaction)
    yesterday_bids = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    yesterday_bids.append(float(b))
                except Exception:
                    pass

    pressure_bid = None
    if yesterday_bids:
        pressure_bid = max(yesterday_bids)

    # Budget / survival urgency
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Estimate how many no-water days we can tolerate (roughly hp corresponds to days left)
    # If hp is low or we already have consecutive dry days, raise bid.
    urgency = 0
    if hp <= 2:
        urgency += 2
    if hp == 3:
        urgency += 1
    if no_water_days >= 2:
        urgency += 2
    if no_water_days == 1:
        urgency += 1

    # Pressure response: Cindy/Eric averaged very high bids; Alex/David died (overaggressive or underbid).
    # If pressure is extremely high, we bid enough to compete but avoid matching the top bid.
    if pressure_bid is not None:
        if pressure_bid >= DAILY_SALARY * 1.15:
            base = DAILY_SALARY * 0.65
            # urgency bumps
            bid = base + urgency * (DAILY_SALARY * 0.12)
        elif pressure_bid >= DAILY_SALARY * 0.85:
            base = DAILY_SALARY * 0.55
            bid = base + urgency * (DAILY_SALARY * 0.10)
        else:
            base = DAILY_SALARY * 0.45
            bid = base + urgency * (DAILY_SALARY * 0.08)
    else:
        # No trace info
        base = DAILY_SALARY * 0.5
        bid = base + urgency * (DAILY_SALARY * 0.08)

    # Supply-aware adjustment: higher supply means cheaper to secure water; lower supply means more competitive.
    # supply is between 15 and 25.
    if supply <= float(MIN_SUPPLY + 1):
        bid *= 1.08
    elif supply >= float(MAX_SUPPLY - 2):
        bid *= 0.95

    # Never bid more than budget
    bid = float(min(budget, bid))

    # Ensure we don't bid zero when we are in danger
    if urgency >= 3 and bid <= 0.0:
        bid = float(min(budget, DAILY_SALARY * 0.9))

    # If budget is tiny, just bid what we can
    if budget <= 1.0:
        return float(budget)

    return float(max(0.0, bid))
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

    # Determine how aggressive opponents were yesterday from their last bid
    alive_opps = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opps.append(opp)

    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Base bid level: aim to compete without exhausting budget
    # Supply is split among bidders; higher supply usually means less need to overbid.
    # Use supply to set a target bid fraction.
    if supply >= 22.0:
        target_frac = 0.55
    elif supply >= 18.0:
        target_frac = 0.62
    else:
        target_frac = 0.70

    # React to yesterday aggression: if they were close to cap, raise slightly
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # Their observed maxes were around 147; treat that as near-cap pressure
        if highest_prev_bid >= 140.0:
            target_frac += 0.10
        elif highest_prev_bid >= 125.0:
            target_frac += 0.05

    # If I'm in danger, spend more
    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Emergency escalation
    if my_hp <= 1 or no_water_days >= 2:
        target_frac = max(target_frac, 0.85)
    elif my_hp <= 3:
        target_frac = max(target_frac, 0.70)

    bid = DAILY_SALARY * target_frac

    # Ensure we never bid more than budget
    if my_budget <= 0:
        return 0.0

    if bid > my_budget:
        bid = my_budget

    # Keep a small reserve for later if not urgent
    if my_hp > 3 and no_water_days < 2:
        reserve = 0.15 * my_budget
        if bid > my_budget - reserve:
            bid = my_budget - reserve

    # Clamp bid to non-negative
    if bid < 0:
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    # Identify alive opponents and compute yesterday bid pressure
    alive_opps = [o for o in opponents_status.values() if o.get('alive')]

    # If no opponents are alive, conserve budget
    if not alive_opps:
        return float(min(my_status.get('budget', 0.0), DAILY_SALARY * 0.4))

    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Supply factor: more supply -> less aggressive; less supply -> more aggressive
    # Ensure indices are integers if we ever use arrays (we won't).
    s = float(supply)
    if s <= MIN_SUPPLY:
        supply_factor = 1.0
    elif s >= MAX_SUPPLY:
        supply_factor = 0.75
    else:
        # Linear interpolation between 1.0 at MIN_SUPPLY and 0.75 at MAX_SUPPLY
        supply_factor = 1.0 - 0.25 * ((s - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY))

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # If my hp is critical or I'm already accumulating no-water days, bid hard.
    if my_hp <= 2 or no_water_days >= 2:
        target = DAILY_SALARY * 0.95
    else:
        # Use yesterday's observed pressure to decide baseline.
        # Cindy/Eric surviving with high bids implies we need to stay competitive.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            target = DAILY_SALARY * 0.55
        else:
            target = DAILY_SALARY * 0.45

    # Adjust by supply factor and slightly counteract high previous bids
    # If others were bidding extremely high, we increase a bit; if not, keep moderate.
    if highest_prev_bid > 0:
        if highest_prev_bid >= DAILY_SALARY * 1.05:
            target *= 1.10
        elif highest_prev_bid >= DAILY_SALARY * 0.85:
            target *= 1.00
        else:
            target *= 0.95

    target *= supply_factor

    # Never bid more than budget; also clamp to a reasonable range.
    # In this game, bids appear around 0..120 in traces.
    bid = min(my_budget, max(0.0, target))
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    my_hp = int(my_status['hp'])
    my_budget = float(my_status['budget'])

    # If we are about to die, bid enough to avoid losing to a high-demand field.
    if my_hp <= 2:
        return min(my_budget, DAILY_SALARY * 0.95)

    # Look only at yesterday's previous_trace for immediate reaction.
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        # No competition: bid conservatively but still secure water.
        return min(my_budget, DAILY_SALARY * 0.45)

    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Estimate aggressiveness from yesterday.
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / float(len(yesterday_bids))
    else:
        highest_prev_bid = 0.0
        avg_prev_bid = 0.0

    # Supply pressure: with medium scenario supply is between 15 and 25.
    # Higher supply reduces the need to overbid, but yesterday showed strong bidding anyway.
    supply_factor = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)  # 0..1

    # Core strategy:
    # - If yesterday bids were very high, match the field by bidding near the average/high.
    # - Otherwise, bid moderately above a baseline to secure at least one unit of water.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Field is aggressive; bid to avoid being the one who misses water.
        target = avg_prev_bid + 3.0
    else:
        # Less aggressive field; still bid above baseline.
        target = max(DAILY_SALARY * (0.50 + 0.10 * (1.0 - supply_factor)), avg_prev_bid * 0.9)

    # Cap by budget and keep some buffer.
    # If budget is low, bid more to prevent cascading no-water days.
    budget_pressure = 0.0
    if DAILY_SALARY > 0:
        budget_pressure = max(0.0, (DAILY_SALARY * 1.0 - my_budget) / (DAILY_SALARY * 1.0))

    if budget_pressure > 0.3:
        target = target * (1.0 + 0.25 * budget_pressure)

    # Final clamp.
    upper = DAILY_SALARY * 0.95
    bid = min(float(my_budget), float(target), upper)

    # Ensure non-trivial bid.
    min_bid = DAILY_SALARY * 0.35
    if bid < min_bid:
        bid = min(float(my_budget), min_bid)

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
    alive = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive.append(opp)

    if not alive:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from each opponent's previous_trace
    yesterday_bids = []
    for opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Estimate opponent pressure: if any opponent bid very high yesterday, expect contest today
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Base bid depends on supply tightness
    # When supply is near MIN, competition likely increases; bid higher.
    tightness = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)  # 0..1
    tightness = max(0.0, min(1.0, float(tightness)))

    # If we are in danger (low hp or multiple no-water days), bid more aggressively.
    danger = 0
    if hp <= 2:
        danger = 2
    elif hp <= 4:
        danger = 1
    if no_water_days >= 2:
        danger = max(danger, 1)

    # Strategy:
    # - If someone bid >= ~0.8*DAILY_SALARY yesterday, we expect high bids; slightly outbid but cap.
    # - Otherwise, bid around a fraction of DAILY_SALARY scaled by tightness.
    if highest_prev_bid >= DAILY_SALARY * 0.8:
        # Outbid pressure with a modest premium; avoid reckless spending.
        target = highest_prev_bid * 0.75 + DAILY_SALARY * (0.15 + 0.15 * tightness)
    else:
        target = DAILY_SALARY * (0.45 + 0.35 * tightness)

    # Apply danger multiplier
    if danger == 2:
        target *= 1.25
    elif danger == 1:
        target *= 1.10

    # Ensure we don't exceed budget and keep some reserve
    # Reserve more when hp is healthy.
    reserve_frac = 0.15 if hp <= 3 else 0.30
    max_affordable = budget * (1.0 - reserve_frac)
    bid = min(float(max_affordable), float(target))

    # Also ensure bid is not trivially low when tight supply and opponents likely contest
    if tightness > 0.6:
        bid = max(bid, DAILY_SALARY * 0.35)

    # Final clamp
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

    # Extract yesterday bids from previous_trace only
    prev_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    prev_bids.append(float(b))
                except Exception:
                    pass

    highest = max(prev_bids) if prev_bids else 0.0
    # Also keep second-highest to avoid fully mirroring the maximum
    sorted_bids = sorted(prev_bids) if prev_bids else []
    second_highest = sorted_bids[-2] if len(sorted_bids) >= 2 else highest

    # Pressure heuristic: if someone was bidding very high, competition is intense.
    intense = highest >= DAILY_SALARY * 1.45  # ~130+ based on meta traces

    # Supply pressure: lower supply means fewer winners/less water; bid more.
    # Use a smooth scaling between MIN_SUPPLY and MAX_SUPPLY.
    if supply <= MIN_SUPPLY:
        supply_factor = 1.0
    elif supply >= MAX_SUPPLY:
        supply_factor = 0.75
    else:
        supply_factor = 1.0 - 0.25 * ((supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY))

    # If we are at risk (low hp or many no-water days), we must secure water.
    urgent = (hp <= 2.0) or (no_water_days >= 2)

    # Target bid level
    if urgent:
        # Aggressive but capped by budget.
        target = DAILY_SALARY * (0.95 if not intense else 1.05) * supply_factor
    else:
        if intense:
            # Match near the lower of top two to win without always paying the max.
            target = (second_highest + 3.0) * 0.98
        else:
            # Moderate bid to beat low bidders.
            target = max(DAILY_SALARY * 0.55, highest * 0.75) * supply_factor

    # Final clamp
    bid = max(0.0, min(budget, target))

    # Avoid bidding too low when supply is scarce and others were bidding high.
    if supply <= MIN_SUPPLY and intense:
        floor_bid = min(budget, DAILY_SALARY * 0.9)
        if bid < floor_bid:
            bid = floor_bid

    # Ensure at least a minimal non-zero bid if budget allows
    if bid <= 0.0 and budget > 0.0:
        bid = min(budget, DAILY_SALARY * 0.2)

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

    supply = day_context.get('supply', 0)
    day = day_context.get('day', 0)

    # Alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        try:
            if o.get('alive', False):
                alive_opps.append((oid, o))
        except Exception:
            continue

    # If no opponents, bid a conservative amount
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace for immediate reaction
    prev_bids = []
    prev_by_opp = {}
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                b_val = float(b)
                prev_bids.append(b_val)
                prev_by_opp[oid] = b_val
            except Exception:
                pass

    # Estimate required intensity based on supply level (mid scenario)
    # Higher supply means less need to overbid; lower supply means more.
    # Use thresholds around the given range.
    try:
        s = float(supply)
    except Exception:
        s = float(MIN_SUPPLY)

    if s <= (MIN_SUPPLY + 1.0):
        supply_pressure = 1.0
    elif s >= (MAX_SUPPLY - 1.0):
        supply_pressure = 0.4
    else:
        supply_pressure = 0.7

    # Determine target bid based on yesterday's strongest bid
    if prev_bids:
        strongest = max(prev_bids)
        second = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else strongest

        # If opponent bids were high, they likely secured water; we must compete.
        # Cindy had highest average and survived; treat strongest as likely winner.
        # Beat by a small increment scaled by supply pressure.
        beat = 2.0 + 6.0 * supply_pressure

        # If our hp is low, increase aggressiveness to avoid death.
        hp = float(my_status.get('hp', 0))
        no_water_days = int(my_status.get('no_water_days', 0))

        # Aggression factor
        if hp <= 1.5 or no_water_days >= 2:
            urgency = 1.0
        elif hp <= 3.5:
            urgency = 0.8
        else:
            urgency = 0.55

        target = strongest + beat * urgency

        # Don't overpay beyond a fraction of budget; also cap relative to strongest
        # Budget safety: if budget is very low, bid what we can.
        budget = float(my_status.get('budget', 0))
        if budget <= 0:
            return 0.0

        # If strongest was extremely high, we may not be able to match; still bid a meaningful amount.
        # Use a floor to avoid bidding too low when supply is tight.
        min_bid = DAILY_SALARY * (0.35 + 0.35 * supply_pressure)
        # Use a cap to avoid draining budget.
        cap_bid = budget * (0.35 + 0.35 * urgency)

        bid = float(min(max(target, min_bid), cap_bid))
        return bid

    # Fallback when no previous bids available
    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    if budget <= 0:
        return 0.0

    if hp <= 2.0:
        return float(min(budget, DAILY_SALARY * 0.9))
    return float(min(budget, DAILY_SALARY * (0.5 + 0.3 * supply_pressure)))
"""
