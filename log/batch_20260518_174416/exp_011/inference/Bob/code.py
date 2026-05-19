# ============================================================
# Experiment: exp_011
# Agent: Bob
# Source: exp_011
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
    day = day_context.get('day', 0)

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    # If no opponents are alive, conserve budget.
    if not alive_opponents:
        cap = DAILY_SALARY * 0.4
        return min(budget, cap)

    # Read yesterday bids from previous_trace only (immediate reaction).
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate competitive pressure.
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev_bid
    else:
        highest_prev_bid = 0.0
        second_prev_bid = 0.0

    # Supply-aware baseline: when supply is tight, increase willingness to pay.
    # supply in [15,25]; map to a multiplier in [~1.2, ~0.8]
    if supply <= 0:
        tight_mult = 1.0
    else:
        tight_mult = 1.2 - 0.4 * ((supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY))
        if tight_mult < 0.8:
            tight_mult = 0.8
        if tight_mult > 1.2:
            tight_mult = 1.2

    # Our risk profile: low hp or many no-water days => bid harder.
    danger = 0
    if hp <= 2.0:
        danger = 2
    elif hp <= 3.0:
        danger = 1
    if no_water_days >= 2:
        danger += 1

    # If someone was bidding very high yesterday (near our salary), assume strong scarcity contest.
    strong_pressure = highest_prev_bid >= DAILY_SALARY * 0.85

    # Core bid target.
    if strong_pressure:
        if danger >= 2:
            target = DAILY_SALARY * 0.95 * tight_mult
        else:
            target = max(highest_prev_bid + 1.5, DAILY_SALARY * 0.3) * (1.0 if danger == 0 else 1.15)
    else:
        # Not extreme: try to outbid the second-highest slightly.
        # If highest was still meaningful, bid around it; else bid a moderate amount.
        anchor = max(second_prev_bid, highest_prev_bid * 0.9)
        base = max(DAILY_SALARY * 0.45, anchor + 1.0)
        target = base * tight_mult

    # Ensure we do not overpay beyond budget and keep some optionality.
    # Use a soft cap based on remaining budget.
    # If budget is low, bid proportionally.
    if budget <= 0:
        return 0.0

    # Hard cap: never exceed budget.
    bid = min(budget, target)

    # If budget is extremely low, still bid enough to avoid total collapse when danger is high.
    if bid < 1e-6 and danger >= 2:
        bid = min(budget, DAILY_SALARY * 0.5)

    # Final sanity: bid should be non-negative.
    if bid < 0.0:
        bid = 0.0

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

    supply = day_context['supply']
    day = day_context['day']
    my_hp = my_status['hp']
    my_budget = my_status['budget']

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    # If no opponents are alive, conserve budget.
    if not alive_opponents:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace for immediate reaction.
    yesterday_bids = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Base bid: undercut the top pressure slightly, scale with supply.
    # supply is float; convert to discrete tier.
    supply_tier = int((supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) * 2.0)  # 0..2
    if supply_tier <= 0:
        base = DAILY_SALARY * 0.60
    elif supply_tier == 1:
        base = DAILY_SALARY * 0.70
    else:
        base = DAILY_SALARY * 0.75

    # If yesterday pressure was high, nudge upward but still aim to beat without matching.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Undercut by a small amount, but keep within reason.
        target = max(base, highest_prev_bid * 0.90)
    elif highest_prev_bid >= DAILY_SALARY * 0.60:
        target = max(base, highest_prev_bid * 0.85)
    else:
        target = base

    # If my HP is critical, escalate to secure water.
    if my_hp <= 2:
        target = max(target, DAILY_SALARY * 0.95)
    elif my_hp <= 3:
        target = max(target, DAILY_SALARY * 0.80)

    # Convert target to feasible bid: can't exceed budget.
    bid = min(my_budget, float(target))

    # Ensure non-negative.
    if bid < 0.0:
        bid = 0.0

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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for k, o in opponents_status.items():
        if o is None:
            continue
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        bid = DAILY_SALARY * 0.4
        return float(min(my_budget, bid))

    # Yesterday reaction: use only previous_trace
    prev_bids = []
    prev_hp_after = []
    for o in alive_opps:
        pt = o.get('previous_trace', {}) or {}
        if pt.get('bid') is not None:
            try:
                prev_bids.append(float(pt.get('bid')))
            except Exception:
                pass
        if pt.get('hp_after') is not None:
            try:
                prev_hp_after.append(float(pt.get('hp_after')))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    lowest_prev_hp_after = min(prev_hp_after) if prev_hp_after else my_hp

    # Supply pressure heuristic
    # If supply is tight (near 15), we must secure water; if abundant (near 25), we can bid less.
    tightness = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    tightness = max(0.0, min(1.0, tightness))

    # Base bid: moderate, scaled by tightness
    base = DAILY_SALARY * (0.40 + 0.25 * tightness)

    # Escalate if my hp is low or I've gone without water
    if my_hp <= 2.0 or my_no_water_days >= 2:
        base = DAILY_SALARY * (0.85 + 0.10 * tightness)

    # Exploit opponent behavior: if someone previously bid very high, they likely were fighting for survival.
    # Match/beat slightly when their pressure was high.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        if my_hp > 3.0:
            base = max(base, highest_prev_bid + 5.0)
        else:
            base = max(base, highest_prev_bid + 15.0)

    # If lowest hp_after among survivors was already low, they may continue to bid to avoid death.
    if lowest_prev_hp_after <= 3.0:
        base = max(base, DAILY_SALARY * (0.65 + 0.15 * tightness))

    # Budget safety cap
    # Avoid overcommitting: keep some budget for later days.
    # If budget is low, bid up to what we can.
    reserve = DAILY_SALARY * 0.2
    max_affordable = max(0.0, my_budget - reserve)
    if max_affordable <= 0.0:
        return float(min(my_budget, DAILY_SALARY * 0.95))

    bid = min(base, max_affordable, my_budget)
    return float(max(0.0, bid))
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

    # Alive opponents and their yesterday bids
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid', None)
            if bid is not None:
                alive_opps.append((opp_id, float(bid), opp))

    # Baseline bid depends on our HP and no-water streak
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # If we're in danger, bid high enough to secure water.
    if hp <= 2 or no_water_days >= 2:
        cap = min(budget, DAILY_SALARY * 0.95)
        return max(1.0, cap)

    # Use yesterday bids to infer pressure.
    if alive_opps:
        yesterday_bids = [b for _, b, _ in alive_opps]
        max_prev = max(yesterday_bids)
        avg_prev = sum(yesterday_bids) / float(len(yesterday_bids))

        # If others were bidding very high, we must avoid losing the water.
        if max_prev >= DAILY_SALARY * 0.85:
            # Medium bid: enough to beat high bidders but not burn budget.
            target = min(budget, DAILY_SALARY * 0.65)
        elif avg_prev >= DAILY_SALARY * 0.55:
            target = min(budget, DAILY_SALARY * 0.55)
        else:
            target = min(budget, DAILY_SALARY * 0.45)
    else:
        target = min(budget, DAILY_SALARY * 0.45)

    # Adjust for supply: higher supply reduces the need to overbid.
    # supply is between 15 and 25; scale smoothly.
    if supply >= 22.0:
        target *= 0.90
    elif supply <= 17.0:
        target *= 1.10

    # Ensure we don't bid more than budget; also keep bid positive.
    bid = float(target)
    if bid > budget:
        bid = budget
    if bid < 1.0:
        bid = 1.0

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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    my_hp = int(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Read yesterday bids from previous_trace (immediate reaction only)
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                prev_bids.append(float(bid))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate how many water units this round likely covers; use to scale aggression.
    # (We don't know exact allocation mechanics, so keep it conservative.)
    # If supply is closer to max, we can bid less; if closer to min, bid more.
    supply_norm = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    supply_norm = max(0.0, min(1.0, supply_norm))

    # Base bid: aim to secure water when needed, but avoid burning budget.
    # If our hp is low or we've been without water, we must bid higher.
    need_factor = 1.0
    if my_hp <= 2:
        need_factor = 1.15
    elif my_hp <= 4:
        need_factor = 1.05

    if my_no_water_days >= 2:
        need_factor += 0.1

    # Match pressure if someone was bidding near the top yesterday.
    # Cindy's bids were high (~146) and Eric died; so if highest_prev_bid is high, we slightly undercut.
    pressure_threshold = DAILY_SALARY * 1.45  # 130.5

    if highest_prev_bid >= pressure_threshold:
        # Underbid by a small margin to try to win while saving budget.
        target = highest_prev_bid - 3.0
        # Ensure we still react to our own need.
        target *= need_factor
    else:
        # Moderate bid: higher when supply is scarce.
        scarcity_bonus = 0.35 + (1.0 - supply_norm) * 0.45  # 0.35..0.8
        target = DAILY_SALARY * (0.45 + scarcity_bonus * 0.25)  # ~50..70-ish
        target *= need_factor

    # Cap by budget and by a reasonable fraction of daily salary to avoid runaway spend.
    max_reasonable = DAILY_SALARY * (0.95 if my_hp <= 2 or my_no_water_days >= 2 else 0.65)
    bid = min(my_budget, max_reasonable, target)

    # Keep bid at least a small amount if budget allows.
    if bid < 1.0 and my_budget >= 1.0:
        bid = min(my_budget, 1.0)

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

    # Alive opponents only
    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive.append((opp_id, opp))

    # If no opponents, bid conservatively
    if not alive:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from immediate previous_trace
    prev_bids = []
    for _, opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Estimate opponent pressure
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev_bid
    else:
        highest_prev_bid = 0.0
        second_prev_bid = 0.0

    # Supply-based aggressiveness: moderate supply means competition likely for scarce units
    # (supply range is 15..25, so pressure often persists)
    supply_frac = (supply - MIN_SUPPLY) / max(1e-9, (MAX_SUPPLY - MIN_SUPPLY))
    supply_frac = max(0.0, min(1.0, supply_frac))

    # My urgency from hp and no_water_days
    hp = int(my_status.get('hp', 0))
    no_water_days = int(my_status.get('no_water_days', 0))
    budget = float(my_status.get('budget', 0.0))

    # Decide target bid
    # If opponents previously bid high, we need to match/just beat.
    # If my hp is low, spend more to avoid death.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # High-pressure environment
        if hp <= 2 or no_water_days >= 2:
            target = highest_prev_bid + 2.0
        else:
            # Slightly above to win without overpaying
            target = max(second_prev_bid + 1.5, highest_prev_bid * (0.98 + 0.04 * supply_frac))
    else:
        # Lower pressure: bid around a fraction of daily salary, adjusted by supply
        base = DAILY_SALARY * (0.45 + 0.25 * supply_frac)
        if hp <= 2 or no_water_days >= 2:
            base = DAILY_SALARY * (0.7 + 0.15 * supply_frac)
        target = max(base, second_prev_bid + 1.0)

    # Budget safety cap
    # Avoid bidding more than we can afford; also avoid spending too much early unless hp is critical.
    critical = (hp <= 2 or no_water_days >= 2)
    max_spend = budget if critical else min(budget, DAILY_SALARY * 1.2)

    bid = float(min(max_spend, max(0.0, target)))
    return bid
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

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace only (immediate reaction)
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    yesterday_bids.append(float(b))
                except Exception:
                    pass

    # If opponents bid aggressively yesterday, we slightly undercut to win more efficiently.
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid
    else:
        highest_prev_bid = 0.0
        second_prev_bid = 0.0

    # Determine how many of our requirement units the supply can support.
    # Use int() for any index-like logic; here it's just arithmetic.
    # With supply 15-25 and WATER_REQ 9, supply supports at most 2 allocations of requirement.
    capacity_units = int(supply / float(WATER_REQ)) if WATER_REQ > 0 else 0

    # Urgency: if we're already on consecutive dry days or very low HP, increase bid.
    critical = (hp <= 2) or (no_water_days >= 2)
    moderate = (hp <= 4) or (no_water_days == 1)

    # Baseline bid targets.
    # If opponents were bidding huge, target slightly below the second-highest to steal water.
    # Otherwise, bid around a fraction of daily salary.
    if highest_prev_bid >= DAILY_SALARY * 1.0:
        # High competition: bid near undercut level, but still bounded by budget.
        target = second_prev_bid + 1.0
        # If our situation is critical, be willing to match the highest.
        if critical:
            target = min(highest_prev_bid + 0.5, highest_prev_bid + 5.0)
        elif moderate:
            target = min(target, highest_prev_bid - 0.5) if highest_prev_bid > 1.0 else target
    else:
        # Low competition: bid enough to be likely to win without wasting.
        if critical:
            target = DAILY_SALARY * 0.9
        elif moderate:
            target = DAILY_SALARY * 0.65
        else:
            target = DAILY_SALARY * (0.45 + 0.05 * capacity_units)

    # If supply is low (closer to 15), competition is tighter; bump slightly.
    if supply <= (MIN_SUPPLY + 0.5):
        target *= 1.08
    elif supply >= (MAX_SUPPLY - 0.5):
        target *= 0.95

    # Never bid more than our budget.
    bid = max(0.0, min(float(budget), float(target)))

    # If budget is tiny, still bid something minimal but nonzero.
    if bid == 0.0 and budget > 0.0:
        bid = min(1.0, budget)

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

    supply = day_context['supply']
    day = day_context['day']

    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday bids from each opponent trace (only immediate reaction)
    prev_bids = []
    prev_max = []
    for oid, o in alive_opps:
        t = o.get('previous_trace', {})
        b = t.get('bid', None)
        if b is not None:
            prev_bids.append(float(b))
        # Use their stated max bid if present
        # (Not guaranteed in per-opponent state, so fallback to yesterday bid)
        if 'max_bid' in o and o['max_bid'] is not None:
            prev_max.append(float(o['max_bid']))

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    # If we have evidence they are bidding near their ceiling, we must respond.
    ceiling_signal = False
    if prev_max:
        # Compare highest yesterday bid to typical ceiling
        ceiling = max(prev_max)
        if ceiling > 0 and highest_prev_bid >= 0.85 * ceiling:
            ceiling_signal = True

    # Estimate how many water units are likely contested.
    # Supply is float; convert to integer indices only if needed.
    # We'll compute a soft target bid scale based on relative supply.
    # More supply => lower pressure.
    supply_level = (float(supply) - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_level = max(0.0, min(1.0, supply_level))

    # Base strategy: moderate bid when healthy; aggressive when low hp or no-water streak.
    if hp <= 2 or no_water_days >= 2:
        # Need water urgently.
        base = DAILY_SALARY * (0.85 if not ceiling_signal else 0.95)
    elif hp <= 4 or no_water_days >= 1:
        base = DAILY_SALARY * (0.65 if not ceiling_signal else 0.78)
    else:
        # Healthy: avoid overpaying against heavy bidders.
        # If supply is high, bid lower; if supply is low, bid higher.
        base = DAILY_SALARY * (0.48 + 0.18 * (1.0 - supply_level))
        if ceiling_signal:
            base = DAILY_SALARY * 0.62

    # Reaction to yesterday's highest bid: if they were spending very high, outbid slightly.
    # Keep it bounded by our budget.
    reaction = 0.0
    if highest_prev_bid > 0:
        # Only react strongly if yesterday pressure was extreme.
        if highest_prev_bid >= DAILY_SALARY * 0.85 or ceiling_signal:
            reaction = min(DAILY_SALARY * 0.35, highest_prev_bid * 0.08 + 5.0)
        elif highest_prev_bid >= DAILY_SALARY * 0.55:
            reaction = min(DAILY_SALARY * 0.18, highest_prev_bid * 0.05 + 2.0)

    bid = base + reaction

    # Ensure bid is feasible and not negative.
    if budget <= 0:
        return 0.0

    if bid > budget:
        bid = budget

    # Minimal bid floor: if we can pay, bid at least a small amount to avoid total starvation.
    # (Do not exceed budget.)
    min_bid = min(budget, DAILY_SALARY * 0.2)
    if bid < min_bid and budget > 0:
        bid = min_bid

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

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday's immediate pressure from each opponent's previous_trace
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    # Supply pressure: less supply -> need to outbid more
    # Map supply in [15,25] to a 0..1 pressure (1 means scarce)
    denom = float(MAX_SUPPLY - MIN_SUPPLY)
    if denom <= 0:
        scarcity = 0.5
    else:
        scarcity = (float(MAX_SUPPLY) - supply) / denom
        if scarcity < 0.0:
            scarcity = 0.0
        if scarcity > 1.0:
            scarcity = 1.0

    # If we are in danger (low hp or already accumulating no-water days), bid more aggressively.
    danger = 0.0
    if hp <= 2.0:
        danger = 1.0
    elif hp <= 4.0:
        danger = 0.7
    elif no_water_days >= 2:
        danger = 0.6
    else:
        danger = 0.25

    # Baseline target bid: try to be slightly above the best yesterday bid only when necessary.
    # If opponents were bidding high and surviving, we must match their intensity but not always exceed.
    # Use scarcity and danger to decide whether to go near-high or mid.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # They were very aggressive; aim between 0.75x and 1.05x of highest_prev_bid depending on scarcity/danger.
        mult = 0.75 + 0.35 * scarcity + 0.25 * danger
        target = highest_prev_bid * mult
    else:
        # They were not extremely aggressive; aim around average plus a premium scaled by scarcity/danger.
        target = avg_prev_bid + (DAILY_SALARY * 0.15) + (DAILY_SALARY * 0.25) * scarcity + (DAILY_SALARY * 0.15) * danger

    # Convert target into practical bounds tied to budget.
    # Keep a reserve so we don't die from budget exhaustion.
    # Reserve fraction increases when day is late.
    episode_days = 10
    late_factor = 0.0
    if episode_days > 0:
        late_factor = float(max(0, day)) / float(episode_days)
    reserve_frac = 0.35 + 0.25 * late_factor
    max_affordable = max(0.0, budget * (1.0 - reserve_frac))

    # Also ensure we can always buy at least one day of water if possible.
    # In many implementations, bids compete for supply; we don't know exact mapping, so we use a conservative floor.
    min_bid = DAILY_SALARY * (0.35 + 0.25 * scarcity)  # don't bid too low when scarce

    bid = max(min_bid, target)

    # If budget is low, scale down.
    if max_affordable < bid:
        bid = max_affordable

    # If we are extremely low hp, override to spend more (still capped by budget).
    if danger >= 1.0:
        bid = min(budget, max(bid, DAILY_SALARY * 0.85))

    # Final cap: cannot exceed budget.
    if bid > budget:
        bid = budget

    # If bid becomes non-positive, bid minimal.
    if bid <= 0.0:
        bid = min(budget, DAILY_SALARY * 0.1)

    return float(bid)
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

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    hp = my_status.get('hp', 0)
    budget = my_status.get('budget', 0.0)
    no_water_days = my_status.get('no_water_days', 0)

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return float(min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace for immediate reaction
    prev_bids = []
    prev_hp_after = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        if prev.get('bid') is not None:
            prev_bids.append(float(prev['bid']))
        if prev.get('hp_after') is not None:
            prev_hp_after.append(float(prev['hp_after']))

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    # If others were very aggressive yesterday, we must raise to keep up.
    aggressive_threshold = DAILY_SALARY * 0.85  # 76.5

    # Base target: aim to beat the highest recent bid with a small premium,
    # but cap to avoid overspending.
    # Since supply is limited (15-25), winning likely requires paying near competitors.
    if highest_prev_bid >= aggressive_threshold:
        if hp > 3:
            target = max(highest_prev_bid + 5.0, DAILY_SALARY * 0.35)
        else:
            target = max(highest_prev_bid + 10.0, DAILY_SALARY * 0.9)
    else:
        # If nobody was that aggressive, bid moderately above a typical level.
        target = max(DAILY_SALARY * 0.55, highest_prev_bid + 2.0)

    # React to my own risk.
    # If my no_water_days is high, I should secure water more aggressively.
    if no_water_days >= 2:
        target *= 1.15
    if hp <= 2:
        target *= 1.25

    # Convert target to a feasible bid given budget.
    # Keep a hard cap relative to daily salary to avoid running out.
    hard_cap = DAILY_SALARY * 1.2
    bid = float(min(budget, hard_cap, target))

    # Ensure non-negative and at least a minimal bid.
    if bid < 1.0:
        bid = float(min(budget, 1.0))

    return bid
"""
