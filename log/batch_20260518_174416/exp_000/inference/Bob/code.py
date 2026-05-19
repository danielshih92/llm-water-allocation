# ============================================================
# Experiment: exp_000
# Agent: Bob
# Source: exp_000
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

    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opponents = [o for o in opponents_status.values() if o.get('alive')]

    # If no opponent info, bid based on our urgency and likely competition.
    urgency = 0.0
    if no_water_days >= 2:
        urgency = 0.35
    elif no_water_days == 1:
        urgency = 0.18

    # Base bid: aim around one unit of requirement share.
    # With supply in [15,25], competition likely means we should bid moderately.
    supply_ratio = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    if hp <= 2:
        base = DAILY_SALARY * (0.70 + 0.25 * supply_ratio)
    elif hp <= 3:
        base = DAILY_SALARY * (0.55 + 0.20 * supply_ratio)
    else:
        base = DAILY_SALARY * (0.45 + 0.15 * supply_ratio)

    # If we had yesterday bids, react. (Yesterday context may be missing; handle safely.)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        if prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If they were aggressive yesterday, slightly outbid; otherwise bid near base.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            base = max(base, highest_prev_bid * 1.05)
        elif highest_prev_bid >= DAILY_SALARY * 0.55:
            base = max(base, highest_prev_bid * 0.95)
        else:
            base = max(base, highest_prev_bid + 1.0)

    # Add urgency bump.
    base = base * (1.0 + urgency)

    # Never exceed what we can pay.
    # Also cap to avoid burning budget early.
    cap = min(budget, DAILY_SALARY * (0.95 if hp <= 3 else 0.75))
    bid = min(cap, base)

    # Ensure non-negative and at least a small bid.
    if bid < 0:
        bid = 0.0
    if bid == 0.0 and budget > 0:
        bid = min(budget, DAILY_SALARY * 0.15)

    return float(bid)
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

    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace to infer aggressiveness.
    yesterday_bids = []
    for oid, o in alive:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Estimate how aggressively others bid: Cindy hit 150 and survived 10 days; Eric bid ~105.
    # Use the maximum yesterday bid as a proxy for current-day pressure.
    pressure = 0.0
    if yesterday_bids:
        pressure = max(yesterday_bids)

    # Base target: secure water at mid-high bids, but avoid matching Cindy's apparent 150-maxing.
    # Scale with supply: if supply is tighter, bid more.
    # supply_ratio near 0 means tight (15), near 1 means abundant (25)
    denom = (MAX_SUPPLY - MIN_SUPPLY)
    if denom <= 0:
        supply_ratio = 0.5
    else:
        supply_ratio = (supply - MIN_SUPPLY) / denom
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Tight supply -> raise bid; abundant -> lower.
    tightness_factor = 1.25 - 0.5 * supply_ratio  # ~1.25 at 15, ~0.75 at 25

    # HP urgency: if low HP or accumulating no-water days, we must bid more.
    hp_factor = 1.0
    if hp <= 2.0:
        hp_factor = 1.35
    elif hp <= 4.0:
        hp_factor = 1.15

    if no_water_days >= 2:
        hp_factor *= 1.15

    # Determine bid ceiling based on observed pressure.
    # If someone previously maxed high, we undercut slightly rather than chase.
    # If pressure is low, bid moderately.
    if pressure >= 140.0:
        target = 105.0 * tightness_factor * hp_factor
    elif pressure >= 90.0:
        target = 85.0 * tightness_factor * hp_factor
    else:
        target = 65.0 * tightness_factor * hp_factor

    # Never exceed what we can afford.
    # Also keep a minimum bid to avoid going to zero unless budget is tiny.
    bid = max(0.0, min(budget, target))

    # Safety: if budget is very low, spend most of it to avoid immediate death.
    if budget <= DAILY_SALARY * 0.35:
        bid = max(0.0, min(budget, DAILY_SALARY * 0.9))

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
    day = int(day_context.get('day', 0))

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append((oid, o))

    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Extract yesterday bids from traces for immediate reaction
    yesterday_bids = []
    yesterday_hp_after = []
    for _, o in alive_opponents:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass
        hp_after = prev.get('hp_after', None)
        if hp_after is not None:
            try:
                yesterday_hp_after.append(int(hp_after))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = (sum(yesterday_bids) / len(yesterday_bids)) if yesterday_bids else 0.0

    # Supply pressure: with higher supply, we can bid less; with lower supply, increase to avoid losing.
    # supply is 15-25; map to [0..1]
    if MAX_SUPPLY > MIN_SUPPLY:
        pressure = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        pressure = 0.5
    pressure = max(0.0, min(1.0, pressure))

    # Base bid: mid-band between 0.45 and 0.75 of salary depending on supply pressure.
    # If supply is low (pressure small), bid higher.
    base = DAILY_SALARY * (0.75 - 0.30 * pressure)

    # React to yesterday's high bidding: if someone else pushed near salary, we must not be too low.
    # Yesterday meta shows Cindy/Alex around 82-84 (~0.92*salary), so target slightly below that.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # If our hp is low, bid closer to the high band.
        if hp <= 2 or no_water_days >= 2:
            target = DAILY_SALARY * 0.90
        else:
            target = DAILY_SALARY * 0.78
    else:
        # If bids were generally low, we can bid around avg to secure water.
        if avg_prev_bid > 0:
            target = max(base, min(budget, avg_prev_bid + 5.0))
        else:
            target = base

    # Ensure we don't overspend early: cap based on remaining days in episode (10 days total).
    # With no_water_days increasing, we should spend more.
    remaining_days = max(1, 10 - day)
    urgency = min(1.0, (no_water_days + (2 if hp <= 2 else 0)) / 4.0)
    cap = DAILY_SALARY * (0.55 + 0.35 * urgency)

    bid = min(budget, target, cap)

    # If we are at critical hp, force a higher bid to avoid elimination.
    if hp <= 1:
        bid = min(budget, DAILY_SALARY * 0.95)

    # Also if supply is extremely low relative to requirement, bid higher.
    # Use integer indexing safety not needed here, but keep logic consistent.
    if supply < float(WATER_REQ):
        bid = min(budget, DAILY_SALARY * 0.95)

    # Final sanity: bid must be non-negative.
    if bid < 0:
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

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    my_hp = my_status.get('hp', 0)
    my_budget = my_status.get('budget', 0.0)
    my_no_water_days = my_status.get('no_water_days', 0)

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return float(min(my_budget, DAILY_SALARY * 0.45))

    # Read yesterday bids from previous_trace only
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

    # Compute pressure from yesterday
    pressure = 0.0
    if yesterday_bids:
        pressure = max(yesterday_bids)

    # Base bid depends on our hp/no_water_days
    # If we're close to death, we must secure water.
    if my_hp <= 2 or my_no_water_days >= 2:
        urgency = 1.0
    elif my_hp <= 4 or my_no_water_days >= 1:
        urgency = 0.75
    else:
        urgency = 0.55

    # Supply scaling: higher supply reduces required aggressiveness.
    # supply in [15,25]
    supply_norm = 0.0
    try:
        supply_norm = (float(supply) - 15.0) / 10.0
    except Exception:
        supply_norm = 0.0
    if supply_norm < 0.0:
        supply_norm = 0.0
    if supply_norm > 1.0:
        supply_norm = 1.0

    # Target bid: follow yesterday pressure but discount when supply is high.
    # Empirically, others bid around 80-130; we aim slightly below top pressure unless urgent.
    top_pressure = pressure
    if top_pressure <= 0.0:
        top_pressure = DAILY_SALARY * 0.6

    # Discount with supply_norm and urgency
    # When supply is high, we can bid less; when urgency is high, bid more.
    supply_discount = 0.85 - 0.25 * supply_norm  # ~0.85 at low supply, ~0.60 at high

    if urgency >= 0.9:
        target = top_pressure * 0.92
    elif urgency >= 0.7:
        target = max(DAILY_SALARY * 0.65, top_pressure * 0.80)
    else:
        target = max(DAILY_SALARY * 0.50, top_pressure * 0.70)

    target = target * supply_discount

    # Keep within budget and avoid extreme overbids.
    # Cap around 1.45*DAILY_SALARY to avoid catastrophic spending.
    cap = DAILY_SALARY * 1.45
    bid = float(min(my_budget, min(cap, target)))

    # If budget is very low, still bid enough to avoid wasting survival opportunities.
    if my_budget <= DAILY_SALARY * 0.25:
        bid = float(min(my_budget, DAILY_SALARY * 0.35))

    # Ensure non-negative
    if bid < 0.0:
        bid = 0.0

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

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    # Alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        return min(my_status['budget'], int(DAILY_SALARY * 0.4))

    # Read yesterday trace bids for immediate reaction
    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # If no yesterday info, use a conservative bid
    if not yesterday_bids:
        base = DAILY_SALARY * 0.55
        if my_status['hp'] <= 2:
            base = DAILY_SALARY * 0.9
        return min(my_status['budget'], int(base))

    highest_prev_bid = max(yesterday_bids)
    lowest_prev_bid = min(yesterday_bids)

    # Estimate how many water units supply can cover (mostly to decide how aggressive)
    # Use int() explicitly for index safety; computations are fine.
    units = int(supply / float(WATER_REQ)) if WATER_REQ > 0 else 0

    # Strategy:
    # - If someone was bidding very high yesterday, undercut slightly to win at lower price.
    # - Otherwise, bid in the mid-lower band to avoid overpaying.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Undercut top pressure
        target = highest_prev_bid - 6.0
        # If our hp is low, stop undercutting and bid closer to pressure
        if my_status['hp'] <= 3:
            target = highest_prev_bid - 1.5
        # If supply is tight (near min), be a bit more aggressive
        if supply <= float(MIN_SUPPLY) + 0.5:
            target += 4.0
    else:
        # Use a blend between low and typical bids
        typical = (highest_prev_bid + lowest_prev_bid) / 2.0
        target = max(lowest_prev_bid + 8.0, typical - 10.0)
        # If hp is very high, we can be slightly cheaper
        if my_status['hp'] >= 8:
            target -= 6.0
        # If supply is abundant, reduce bid
        if supply >= float(MAX_SUPPLY) - 0.5:
            target -= 4.0

    # Budget and survival pressure
    # If we've had no water for several days, increase bid.
    no_water_days = int(my_status.get('no_water_days', 0) or 0)
    if no_water_days >= 2:
        target += 20.0
    if my_status['hp'] <= 2:
        target += 35.0

    # Ensure within budget and non-negative
    target_int = int(max(0, target))
    return min(my_status['budget'], target_int)
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

    # Identify alive opponents and their yesterday bids
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Use only yesterday previous_trace
    prev_bids = []
    prev_bid_by_id = {}
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                b = float(b)
            except Exception:
                continue
            prev_bids.append(b)
            prev_bid_by_id[oid] = b

    # Infer Cindy pressure if present
    cindy_bid = None
    if 'Cindy' in prev_bid_by_id:
        cindy_bid = prev_bid_by_id['Cindy']

    # Supply pressure: if supply is close to our requirement, competition matters more.
    # Convert to an approximate "water scarcity" factor.
    # (Higher factor => bid more.)
    scarcity = 0.0
    if supply > 0:
        scarcity = (float(WATER_REQ) / float(supply))
    scarcity = max(0.0, min(1.5, scarcity))

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Baseline aggressiveness: keep budget for survival; avoid matching Cindy's extreme bids.
    # If we're in danger, bid more.
    danger = 0.0
    if my_hp <= 2:
        danger = 1.0
    elif my_hp <= 4:
        danger = 0.6
    else:
        danger = 0.25

    # Target bid: slightly under Cindy's likely pressure.
    # If Cindy bid big yesterday, she's likely to keep bidding; we counter with a moderate amount.
    if cindy_bid is not None:
        # If Cindy was very aggressive, we don't fully match; we bid around 60-75% of her bid.
        # Scale down further when our hp is healthy.
        scale = 0.65 if danger >= 0.6 else 0.55
        target = cindy_bid * scale
    else:
        # Otherwise react to max previous bid.
        max_prev = max(prev_bids) if prev_bids else 0.0
        target = max_prev * (0.55 if danger < 0.6 else 0.7)

    # Adjust for scarcity and our no-water streak.
    target *= (0.85 + 0.3 * scarcity)
    if no_water_days >= 2:
        target *= 1.15

    # Cap target to a reasonable fraction of daily salary to avoid runaway bidding.
    # With hp danger, allow higher cap.
    cap = DAILY_SALARY * (0.95 if danger >= 0.6 else 0.7)
    target = min(target, cap)

    # Always ensure non-negative and within budget.
    bid = max(0.0, min(my_budget, target))

    # If supply is at the high end, competition is lower: reduce bid.
    if supply >= float(MAX_SUPPLY) - 0.5:
        bid *= 0.75

    # If supply is at the low end, increase slightly.
    if supply <= float(MIN_SUPPLY) + 0.5:
        bid *= 1.1

    # Final clamp
    bid = max(0.0, min(my_budget, bid))
    return float(bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    # Identify alive opponents
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append(o)

    if not alive:
        # If no opponents, spend enough to secure water; cap by budget.
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Read yesterday bids from previous_trace for immediate reaction
    yesterday_bids = []
    for o in alive:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Baseline: moderate bid to compete against typical bids (Alex/Eric were high)
    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))

    # Estimate how many water units are effectively relevant today
    # (We don't know mapping from bid->water, so we use supply to scale aggressiveness.)
    supply_factor = 0.0
    if supply > 0:
        supply_factor = (supply - 15.0) / (25.0 - 15.0)  # in [0,1] for given meta
        if supply_factor < 0.0:
            supply_factor = 0.0
        if supply_factor > 1.0:
            supply_factor = 1.0

    # Determine yesterday pressure
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    # If yesterday bids were extreme, we slightly overtake; else we undercut.
    # Use hp to decide whether to protect survival.
    if highest_prev_bid >= DAILY_SALARY * 1.15:  # ~103.5
        # High contest; bid more if low hp
        if hp <= 2.5:
            target = DAILY_SALARY * (0.95 + 0.10 * supply_factor)
        elif hp <= 4.0:
            target = DAILY_SALARY * (0.75 + 0.08 * supply_factor)
        else:
            target = DAILY_SALARY * (0.60 + 0.06 * supply_factor)
    elif avg_prev_bid >= DAILY_SALARY * 0.95:  # ~85.5
        # Medium-high contest; bid around mid
        if hp <= 2.5:
            target = DAILY_SALARY * (0.85 + 0.10 * supply_factor)
        else:
            target = DAILY_SALARY * (0.65 + 0.06 * supply_factor)
    else:
        # Lower contest; bid just enough to avoid being outbid
        if hp <= 2.5:
            target = DAILY_SALARY * (0.75 + 0.10 * supply_factor)
        else:
            target = DAILY_SALARY * (0.55 + 0.05 * supply_factor)

    # Additional safeguard: if budget is low, don't over-commit.
    # Also keep bid within reasonable range relative to salary.
    min_bid = 5.0
    max_bid = min(budget, DAILY_SALARY * 1.2)
    bid = max(min_bid, min(target, max_bid))

    # If my hp is critically low, spend more aggressively but still capped.
    if hp <= 1.5:
        bid = min(budget, max(bid, DAILY_SALARY * 0.98))

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

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if budget <= 0:
        return 0.0

    # React to yesterday's pressure using only previous_trace
    prev_bids = []
    prev_max_bid = None
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                prev_bids.append(float(bid))
            except Exception:
                pass
    if prev_bids:
        prev_max_bid = max(prev_bids)

    # Base target: if supply is near our requirement, competition is lower; if high supply, we can bid less.
    # Normalize supply to [0,1] where 15->0 and 25->1
    if MAX_SUPPLY > MIN_SUPPLY:
        s_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        s_norm = 0.5
    s_norm = max(0.0, min(1.0, float(s_norm)))

    # If my survival is at risk, bid harder.
    urgent = (hp <= 2) or (no_water_days >= 2)

    # Determine bid ceiling from budget and a fraction of daily salary.
    # Use yesterday max bid to decide whether the market is expensive.
    expensive_market = False
    if prev_max_bid is not None:
        if prev_max_bid >= DAILY_SALARY * 1.25:
            expensive_market = True

    # Choose a target bid
    if urgent:
        # High urgency: bid close to salary, but not exceed budget.
        if expensive_market:
            target = DAILY_SALARY * (0.95 - 0.10 * s_norm)
        else:
            target = DAILY_SALARY * (0.80 - 0.05 * s_norm)
    else:
        # Moderate urgency: bid around 55% of salary; reduce if supply is high.
        if expensive_market:
            # Still bid enough to beat the expensive crowd, but stay conservative.
            target = max(DAILY_SALARY * (0.60 - 0.10 * s_norm), (prev_max_bid * 0.65) if prev_max_bid is not None else DAILY_SALARY * 0.60)
        else:
            target = DAILY_SALARY * (0.52 - 0.08 * s_norm)

    # Additional tweak: if supply is very tight (near 15), increase slightly.
    if supply <= (MIN_SUPPLY + 1.0):
        target *= 1.10
    elif supply >= (MAX_SUPPLY - 1.0):
        target *= 0.90

    # Final cap to budget
    bid = min(float(budget), float(target))

    # Avoid returning negative/NaN
    if bid < 0:
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
    day = day_context['day']

    # Collect alive opponents and their yesterday bids
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        # No one to contest; bid conservatively
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    yesterday_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Determine pressure from yesterday
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    # Also detect if a specific opponent was very aggressive yesterday (likely Cindy)
    aggressive_prev = False
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is None:
            continue
        try:
            if float(b) >= 0.9 * highest_prev_bid and float(b) >= DAILY_SALARY * 1.0:
                aggressive_prev = True
                break
        except Exception:
            continue

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status.get('no_water_days', 0) or 0)

    # Base strategy: secure water when at risk; otherwise avoid overpaying.
    # If we are already low HP or have gone multiple no-water days, bid closer to aggressive pressure.
    risk_factor = 0.0
    if hp <= 2.0:
        risk_factor += 1.0
    if hp <= 4.0:
        risk_factor += 0.6
    if no_water_days >= 2:
        risk_factor += 0.8
    if no_water_days >= 3:
        risk_factor += 1.0

    # Supply level affects how many units could be won; with higher supply we can bid less.
    # Use integer index safety for any derived bins.
    supply_bin = int((supply - MIN_SUPPLY) / max(1.0, (MAX_SUPPLY - MIN_SUPPLY)) * 2)  # 0..2
    if supply_bin < 0:
        supply_bin = 0
    if supply_bin > 2:
        supply_bin = 2

    # Target bid multiplier table by supply_bin (lower supply => bid more)
    mult_table = [1.05, 0.95, 0.85]
    mult = float(mult_table[supply_bin])

    # If Cindy-like aggression exists, we slightly undercut relative to highest_prev_bid.
    # Otherwise bid around a moderate fraction of daily salary.
    if aggressive_prev and highest_prev_bid > 0:
        # Undercut by a small margin; if we're in danger, close the gap.
        undercut = 12.0
        if risk_factor >= 1.0:
            undercut = 6.0
        if risk_factor >= 1.6:
            undercut = 2.0
        target = highest_prev_bid * mult - undercut
    else:
        target = DAILY_SALARY * (0.55 + 0.25 * risk_factor) * mult

    # Ensure we don't bid more than budget and keep non-negative
    if target < 0:
        target = 0.0

    # If our hp is very low, we must bid high to survive
    if hp <= 1.5:
        target = max(target, DAILY_SALARY * 0.95)
    elif hp <= 3.0:
        target = max(target, DAILY_SALARY * 0.75)

    # If we have lots of budget and mid/high hp, avoid unnecessary overbids
    if hp >= 7.0 and budget > DAILY_SALARY * 3:
        target = min(target, DAILY_SALARY * 0.65)

    bid = float(min(budget, target))

    # Small day-based adjustment: later days require more water.
    # Episode length is 10; day ranges likely 1..10.
    if day >= 8:
        bid = min(budget, bid * 1.1)

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

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from immediate previous_trace only
    prev_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate opponent pressure: use max surviving bids
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Supply-based aggressiveness: when supply is scarce, bidding competition is higher.
    # supply is between 15 and 25.
    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    scarcity = max(0.0, min(1.0, scarcity))

    # Target bid: just above the strongest yesterday bid if I'm healthy and supply is scarce.
    # If I'm low hp / already on no-water streak, bid harder.
    base = DAILY_SALARY * (0.55 + 0.35 * scarcity)  # ~49.5 to 90

    # If yesterday pressure was high, mirror it; otherwise, slightly undercut.
    if highest_prev_bid > 0:
        # If highest_prev_bid is in the ~survivor band, try to beat it marginally.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            target = highest_prev_bid + 2.0 * (0.5 + scarcity)
        else:
            target = max(base, highest_prev_bid + 1.0)
    else:
        target = base

    # Emergency escalation based on my hp/no_water_days
    if my_hp <= 2 or my_no_water_days >= 2:
        target = max(target, DAILY_SALARY * 0.9)
    elif my_hp <= 3:
        target = max(target, DAILY_SALARY * 0.75)

    # Budget cap
    bid = min(my_budget, target)

    # Avoid negative/NaN
    if bid != bid or bid < 0.0:
        bid = 0.0

    return float(bid)
"""
