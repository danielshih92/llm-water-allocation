# ============================================================
# Experiment: exp_084
# Agent: Bob
# Source: exp_084
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    # Safety: if no opponents, just buy enough to cover requirement.
    if not alive_opponents:
        target = WATER_REQ
        return min(my_status.get('budget', 0), target)

    # Read yesterday bids to infer their pressure.
    yesterday_bids = []
    yesterday_meta = []  # (opp_id, bid, hp_after, budget_after, status)
    for opp_id, opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                bid_val = float(bid)
            except Exception:
                bid_val = None
            if bid_val is not None:
                yesterday_bids.append(bid_val)
                yesterday_meta.append((opp_id, bid_val, prev.get('hp_after', None), prev.get('budget_after', None), prev.get('status', None)))

    my_budget = float(my_status.get('budget', 0.0))
    my_hp = float(my_status.get('hp', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    # Determine supply pressure.
    # Approximate how many full water requirements are even possible.
    # Indices are not used; only numeric logic.
    supply_ratio = supply / float(WATER_REQ) if WATER_REQ else 0.0

    # Default bid baseline: moderate, scaled by remaining budget and supply.
    # Keep some budget for later; avoid going all-in early.
    base_bid = 0.45 * DAILY_SALARY
    if my_hp <= 2 or my_no_water_days >= 2:
        base_bid = 0.75 * DAILY_SALARY

    # If opponents were bidding very high yesterday, they are likely desperate.
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid

        # Aggressive-but-controlled response.
        # Thresholds tuned to daily salary scale.
        if highest_prev_bid >= 0.85 * DAILY_SALARY:
            # They likely need water badly; we secure by bidding above typical.
            # If we are healthy, still bid strong but not maximal.
            if my_hp > 3 and my_no_water_days < 2:
                bid = 0.62 * DAILY_SALARY
            else:
                bid = 0.88 * DAILY_SALARY
        elif highest_prev_bid >= 0.60 * DAILY_SALARY:
            # Mildly escalate to avoid losing the water allocation.
            bid = max(base_bid, min(0.70 * DAILY_SALARY, highest_prev_bid + 5.0))
        else:
            # They were not too desperate; avoid price war.
            # Bid enough to compete but not overpay.
            bid = min(base_bid, (second_prev_bid + highest_prev_bid) * 0.5 + 2.0)
    else:
        # No trace bids available; use baseline.
        bid = base_bid

    # Adjust for current supply: lower supply => bid more.
    if supply_ratio < 1.2:
        bid *= 1.15
    elif supply_ratio > 2.0:
        bid *= 0.90

    # Final cap by budget.
    bid = float(bid)
    if my_budget <= 0:
        return 0.0

    # Don't bid more than budget.
    if bid > my_budget:
        bid = my_budget

    # Also avoid bidding negative.
    if bid < 0:
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

    # Safety/health-based scaling
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', True):
            alive_opponents.append(o)

    if not alive_opponents:
        # If no one else is alive, bid enough to secure water cheaply.
        target = DAILY_SALARY * 0.35
        return max(0.0, min(budget, target))

    # Read yesterday bids from previous_trace for immediate reaction
    prev_bids = []
    for o in alive_opponents:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Estimate how competitive the field is
    if prev_bids:
        highest_prev = max(prev_bids)
        second_prev = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev
    else:
        highest_prev = 0.0
        second_prev = 0.0

    # Competitive bid target:
    # - If others were bidding near the top of typical range, we shade slightly below the highest.
    # - Otherwise, we bid enough to be competitive but not reckless.
    if highest_prev >= DAILY_SALARY * 1.5:  # ~135+
        base_target = highest_prev * 0.92
    elif highest_prev >= DAILY_SALARY * 1.25:  # ~112+
        base_target = max(DAILY_SALARY * 0.75, second_prev + 2.0)
    else:
        base_target = max(DAILY_SALARY * 0.55, highest_prev + 5.0)

    # Adjust for our urgency
    urgency = 0.0
    if hp <= 2.0:
        urgency += 1.0
    if no_water_days >= 2:
        urgency += 0.7
    if hp <= 4.0:
        urgency += 0.4

    # Supply context: when supply is higher, we can shade; when lower, bid more.
    # Normalize supply in [MIN_SUPPLY, MAX_SUPPLY]
    s_norm = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        s_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    s_norm = min(1.0, max(0.0, s_norm))

    # If supply is low, increase bid; if high, decrease.
    supply_adjust = (1.0 - s_norm)  # 1 at low supply, 0 at high

    target = base_target * (1.0 + 0.35 * supply_adjust + 0.25 * urgency)

    # Keep within budget and avoid overspending early
    # Late in episode, spend more aggressively.
    episode_days = 10
    remaining = max(0, episode_days - int(day))
    endgame_factor = 1.0
    if remaining <= 2:
        endgame_factor = 1.25
    elif remaining <= 4:
        endgame_factor = 1.12

    target *= endgame_factor

    # Final cap: don't exceed budget; also keep some buffer if possible
    # Buffer heuristic: keep at least 20% of budget unless hp is critical.
    buffer_frac = 0.2
    if hp <= 2.0:
        buffer_frac = 0.05

    max_affordable = budget * (1.0 - buffer_frac)
    if max_affordable < 0:
        max_affordable = 0.0

    bid = min(target, max_affordable)

    # Ensure non-negative and at least a minimal bid if we have budget
    if bid < 0.0:
        bid = 0.0

    # If we have very low budget, just bid what we can.
    if budget <= DAILY_SALARY * 0.6:
        bid = min(budget, max(bid, DAILY_SALARY * 0.35))

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
    day = int(day_context.get('day', 0))

    # Alive opponents only
    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive.append((opp_id, opp))

    if not alive:
        return max(0.0, min(float(my_status['budget']), DAILY_SALARY * 0.4))

    # Read yesterday bids from immediate previous_trace
    prev_bids = []
    for _, opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # Estimate opponent aggressiveness
    highest_prev = max(prev_bids) if prev_bids else 0.0
    lowest_prev = min(prev_bids) if prev_bids else 0.0

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))

    # If I'm in danger, bid more aggressively.
    if my_hp <= 2:
        base = DAILY_SALARY * 0.9
    elif my_hp <= 4:
        base = DAILY_SALARY * 0.65
    else:
        # Otherwise, exploit low-bid behavior like Eric (~15 avg)
        # by bidding slightly above the low end unless Alex was very high.
        if highest_prev >= DAILY_SALARY * 0.85:
            # Alex likely bidding to secure; we can still try to win with a mid bid.
            base = max(DAILY_SALARY * 0.55, lowest_prev + 10.0)
        else:
            base = max(DAILY_SALARY * 0.35, lowest_prev + 8.0)

    # Supply scaling: when supply is higher, we can lower bids.
    # supply range is [15,25]
    if MAX_SUPPLY > MIN_SUPPLY:
        t = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        t = 0.5
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)

    # Higher supply => bid slightly less
    base = base * (1.0 - 0.12 * t)

    # Ensure we don't bid more than budget
    bid = max(0.0, min(my_budget, base))

    # On early days, slightly more conservative to preserve budget for later pressure.
    if day <= 3:
        bid *= 0.95

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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append((oid, o))

    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Extract yesterday bids from previous_trace for immediate reaction
    prev_bids = []
    prev_max_bid = None
    prev_high_pressure_count = 0
    for oid, o in alive_opponents:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                b = float(b)
                prev_bids.append(b)
                if prev_max_bid is None or b > prev_max_bid:
                    prev_max_bid = b
                if b >= DAILY_SALARY * 0.85:
                    prev_high_pressure_count += 1
            except Exception:
                pass

    # Estimate how many water units are likely needed this day
    # If supply is low, competition likely increases; if my HP is low, I must secure water.
    # Use a conservative target: aim to win when my HP is critical or supply is near minimum.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Base bid depends on supply scarcity
    scarcity_factor = 1.0 + (1.0 - supply_ratio) * 0.35  # up to +35% when supply is low

    # Determine urgency from HP and consecutive no-water days
    urgency = 0.0
    if hp <= 2.0:
        urgency = 1.0
    elif hp <= 4.0:
        urgency = 0.7
    elif hp <= 6.0:
        urgency = 0.4
    else:
        urgency = 0.2

    if no_water_days >= 2:
        urgency = max(urgency, 0.8)
    if no_water_days >= 3:
        urgency = 1.0

    # Use yesterday's observed high bids to set a competitive ceiling.
    # If multiple opponents pushed high (~>=77), we modestly increase to avoid being undercut.
    if prev_bids:
        target = (DAILY_SALARY * 0.55) * scarcity_factor
        if prev_high_pressure_count >= 2:
            target = max(target, (DAILY_SALARY * 0.75) * scarcity_factor)
        if prev_max_bid is not None:
            # If someone bid extremely high yesterday, we don't match fully; we slightly undercut
            # to reduce budget risk while still contesting.
            target = max(target, min(prev_max_bid * 0.92, DAILY_SALARY * 0.95) * scarcity_factor)
    else:
        target = (DAILY_SALARY * 0.55) * scarcity_factor

    # Escalate when urgency is high
    bid = target * (0.8 + 0.4 * urgency)

    # If my HP is critical, bid closer to salary cap; otherwise stay safer.
    if urgency >= 0.9:
        bid = max(bid, DAILY_SALARY * 0.85)
    elif urgency >= 0.6:
        bid = max(bid, DAILY_SALARY * 0.65)

    # Budget-aware cap: never exceed what we can pay.
    bid = min(bid, budget)

    # If budget is too low, bid all-in to prevent death if urgency is high.
    if budget <= DAILY_SALARY * 0.2:
        if urgency >= 0.7:
            return budget
        return min(budget, DAILY_SALARY * 0.1)

    # Final safety: keep within a reasonable range.
    lower_bound = 0.0
    upper_bound = min(budget, DAILY_SALARY * 1.0)
    if bid < lower_bound:
        bid = lower_bound
    if bid > upper_bound:
        bid = upper_bound

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

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((opp_id, o))

    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from immediate previous_trace
    prev_bids = []
    for opp_id, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # If we can't read bids, default conservative
    if not prev_bids:
        base = DAILY_SALARY * 0.55
        return max(0.0, min(my_budget, base))

    highest_prev_bid = max(prev_bids)
    # Alex-like behavior: push when they need survival; others likely quit (0 bids)

    # Determine aggressiveness by our HP cushion
    # If low HP or already many no-water days, prioritize winning this day.
    pressure = 0
    if my_hp <= 2.0:
        pressure = 2
    elif my_hp <= 4.0:
        pressure = 1

    if my_no_water_days >= 2:
        pressure = max(pressure, 1)

    # Target bid: slightly above typical competitor pressure.
    # We cap at a fraction of budget to avoid ruin.
    if pressure >= 2:
        target = max(highest_prev_bid + 1.0, DAILY_SALARY * 0.85)
        budget_cap = DAILY_SALARY * 0.95
    elif pressure == 1:
        target = max(highest_prev_bid * 0.98, DAILY_SALARY * 0.65)
        budget_cap = DAILY_SALARY * 0.75
    else:
        # With good HP, overpay less; just beat their likely bid.
        target = max(highest_prev_bid * 0.92, DAILY_SALARY * 0.55)
        budget_cap = DAILY_SALARY * 0.6

    # Supply context: if supply is tight, increase slightly; if abundant, reduce.
    # supply is between 15 and 25.
    if supply <= (MIN_SUPPLY + 0.5):
        target *= 1.08
    elif supply >= (MAX_SUPPLY - 0.5):
        target *= 0.95

    # Final clamp
    max_affordable = my_budget
    final_bid = min(max_affordable, budget_cap, target)

    # Ensure non-negative
    if final_bid < 0.0:
        final_bid = 0.0

    # Also ensure we don't bid more than a reasonable upper bound relative to supply
    # (prevents accidental huge bids if budgets are high)
    final_bid = min(final_bid, DAILY_SALARY)

    return float(final_bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    if budget <= 0:
        return 0.0

    # Estimate how many water units are likely available relative to our requirement.
    # We don't know exact mapping from supply to water given; use it only to scale our aggressiveness.
    # If supply is tight, we bid more.
    tightness = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        tightness = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    tightness = max(0.0, min(1.0, tightness))

    # Read yesterday bids from previous_trace (immediate reaction only)
    prev_bids = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    prev_bids.append(float(b))
                except Exception:
                    pass

    # If any opponent bid extremely high yesterday, they likely try to lock water.
    # We counter with a moderate bid to avoid budget wipe.
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Base target bid: moderate fraction of daily salary, increased when supply is tight or our hp is low.
    base = DAILY_SALARY * (0.45 + 0.25 * tightness)

    # Pressure adjustment based on yesterday aggressiveness.
    # If highest previous bid was very high, we slightly increase; otherwise keep moderate.
    if highest_prev_bid >= DAILY_SALARY * 1.1:
        base *= 1.15
    elif highest_prev_bid >= DAILY_SALARY * 0.85:
        base *= 1.05

    # Survival adjustment: if we're close to death or have gone without water, bid more.
    if hp <= 2.0:
        base *= 1.35
    elif hp <= 4.0:
        base *= 1.15

    if no_water_days >= 2:
        base *= 1.25
    elif no_water_days >= 1:
        base *= 1.10

    # Cap bid to avoid suiciding budget; also ensure non-negative.
    # If budget is small, spend a fraction rather than all.
    spend_fraction = 0.55
    if hp <= 2.0 or no_water_days >= 2:
        spend_fraction = 0.75
    elif hp <= 4.0 or no_water_days >= 1:
        spend_fraction = 0.65

    bid = min(budget * spend_fraction, base)

    # If we are competing against many alive opponents, slightly reduce to avoid overpaying.
    n_alive = len(alive_opponents)
    if n_alive >= 4:
        bid *= 0.9
    elif n_alive == 1:
        bid *= 1.05

    # Final clamp
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Determine alive opponents and extract yesterday bids
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    yesterday_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Estimate market pressure from yesterday
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid
    else:
        highest_prev_bid = 0.0
        second_prev_bid = 0.0

    # Supply pressure: if supply is scarce, we must secure water
    # Normalize supply to [0,1] where 1 means scarce
    if MAX_SUPPLY <= MIN_SUPPLY:
        scarcity = 0.5
    else:
        scarcity = 1.0 - (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
        if scarcity < 0.0:
            scarcity = 0.0
        if scarcity > 1.0:
            scarcity = 1.0

    # Health urgency
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    # Target bid: aim to outbid the likely overbidder only when needed
    # Use a cap to avoid bankruptcy.
    # If Cindy-type behavior exists (very high highest_prev_bid), we don't match it; we bid enough to win at lower cost.
    base = DAILY_SALARY * (0.35 + 0.45 * scarcity)

    # If my hp is low, bid more aggressively
    if hp <= 1.5:
        urgency_mult = 1.9
    elif hp <= 3.5:
        urgency_mult = 1.35
    else:
        urgency_mult = 1.0

    # If highest_prev_bid is extremely high, assume someone is overbidding; don't chase fully.
    # Instead, bid just above a fraction of it.
    if highest_prev_bid > DAILY_SALARY * 1.2:
        chase = second_prev_bid * 0.95 + 2.0
        target = min(base * urgency_mult, chase)
    else:
        # Normal pressure: hover near highest_prev_bid but with discount
        target = min(base * urgency_mult, highest_prev_bid * 0.92 + 3.0)

    # Ensure we don't bid more than budget
    if budget <= 0.0:
        return 0.0

    # Also ensure minimal competitive bid when supply is scarce
    min_competitive = DAILY_SALARY * (0.25 + 0.35 * scarcity)
    bid = max(target, min_competitive if scarcity >= 0.4 else target * 0.8)

    if bid > budget:
        bid = budget

    # Final safety clamp
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Alive opponents
    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive'):
            alive_opponents.append(o)

    # If no opponents, bid to ensure allocation but not overpay
    if not alive_opponents:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace only (immediate reaction)
    yesterday_bids = []
    for o in alive_opponents:
        prev = o.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Determine a target bid level based on yesterday's observed aggressiveness
    # If someone was bidding very low, the market may be weak today.
    low_bid = None
    high_bid = None
    if yesterday_bids:
        low_bid = min(yesterday_bids)
        high_bid = max(yesterday_bids)

    # Urgency factor: if we already missed water, increase bid.
    urgency = 0.0
    if no_water_days >= 2:
        urgency = 0.35
    elif no_water_days == 1:
        urgency = 0.18

    # HP safety: if low HP, increase bid.
    if hp <= 2:
        urgency += 0.35
    elif hp <= 4:
        urgency += 0.18

    # Supply pressure: lower supply => higher chance others compete; scale up.
    supply_pressure = 0.0
    if supply <= float(MIN_SUPPLY):
        supply_pressure = 0.25
    elif supply >= float(MAX_SUPPLY):
        supply_pressure = -0.05
    else:
        # linear between 15 and 25
        supply_pressure = 0.25 - 0.25 * ((supply - float(MIN_SUPPLY)) / (float(MAX_SUPPLY) - float(MIN_SUPPLY)))

    # Base bid: aim around mid of DAILY_SALARY with adjustments.
    # Yesterday had survivors with ~88-99 avg; use that as anchor.
    base = DAILY_SALARY * 0.62  # 55.8

    # If high_bid was large, we should not be too low; if low_bid was tiny, we can undercut.
    adjust = 0.0
    if high_bid is not None and high_bid >= DAILY_SALARY * 1.1:
        adjust += 0.12
    if low_bid is not None and low_bid <= DAILY_SALARY * 0.35:
        adjust -= 0.08

    target = base * (1.0 + urgency + supply_pressure + adjust)

    # Cap target to avoid overspending; also ensure we can afford it.
    # If we are very low on budget, bid a fraction.
    if budget <= DAILY_SALARY * 0.6:
        target = min(target, budget * 0.9)
    else:
        target = min(target, budget * 0.55)

    # If we are at/near critical HP, bid more aggressively.
    if hp <= 1:
        target = min(budget, DAILY_SALARY * 0.95)
    elif hp <= 3:
        target = min(budget, DAILY_SALARY * (0.75 + urgency))

    # Final sanity: bid at least a small amount if possible.
    min_bid = 1.0
    if budget < min_bid:
        return float(budget)

    bid = float(min(max(target, min_bid), budget))
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

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # If no opponents are alive, just bid conservatively.
    if not alive_opps:
        return max(0.0, min(my_status.get('budget', 0.0), DAILY_SALARY * 0.4))

    # Immediate reaction from yesterday's trace.
    yesterday_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Pressure estimate: if someone bid very high yesterday, competition is strong.
    high_pressure = highest_prev_bid >= (DAILY_SALARY * 0.85)

    # Supply tiers determine how likely we are to be rationed.
    # With supply 15-25 and WATER_REQ=9, low supply (15) is tight.
    # Use a stronger bid on low supply to avoid accumulating no_water_days.
    if supply <= float(MIN_SUPPLY) + 0.5:
        base_bid = DAILY_SALARY * (0.75 if not high_pressure else 0.95)
    elif supply <= 20.0:
        base_bid = DAILY_SALARY * (0.60 if not high_pressure else 0.85)
    else:
        base_bid = DAILY_SALARY * (0.45 if not high_pressure else 0.70)

    # If we're already in danger, increase bid.
    if my_hp <= 2 or no_water_days >= 2:
        base_bid = DAILY_SALARY * 0.95
    elif my_hp <= 4 or no_water_days >= 1:
        base_bid = max(base_bid, DAILY_SALARY * 0.70)

    # If we are doing well, avoid overspending.
    if my_hp >= 8 and no_water_days == 0:
        base_bid = min(base_bid, DAILY_SALARY * 0.55)

    # Final clamp to budget.
    bid = min(my_budget, base_bid)
    if bid < 0.0:
        bid = 0.0
    return bid
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

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append(o)

    if not alive_opponents:
        return float(min(budget, DAILY_SALARY * 0.4))

    # Immediate reaction to yesterday bids
    yesterday_bids = []
    for o in alive_opponents:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how many full water units supply can buy
    # (Not used for indexing; only to scale aggressiveness)
    units = supply / float(WATER_REQ) if WATER_REQ else 0.0

    # Pressure logic: if others bid near/above daily salary yesterday, they likely contest today.
    # We keep a mid bid unless our HP is low.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        if hp <= 2 or no_water_days >= 1:
            bid = DAILY_SALARY * 0.95
        elif hp <= 3:
            bid = DAILY_SALARY * 0.75
        else:
            bid = DAILY_SALARY * 0.35
    else:
        # If yesterday bids were not extreme, bid enough to secure water but conserve budget.
        # Scale slightly with supply (more supply => can bid a bit less).
        supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
        supply_factor = max(0.0, min(1.0, supply_factor))
        bid = DAILY_SALARY * (0.55 - 0.15 * supply_factor)

    # If our HP is critically low, override to maximize chance.
    if hp <= 1:
        bid = DAILY_SALARY * 1.0

    # Convert to feasible bid bounds
    bid = float(min(budget, bid))
    if bid < 0.0:
        bid = 0.0
    return bid
"""
