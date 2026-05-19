# ============================================================
# Experiment: exp_033
# Agent: Bob
# Source: exp_033
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

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    # Base target: aim to win enough to avoid starvation but not overpay.
    # With supply in [15,25], winning bids around ~0.5-0.65 of a day salary are typically sufficient.
    base_bid = DAILY_SALARY * 0.6

    # If we have yesterday info, react to the most aggressive opponent.
    highest_prev_bid = None
    if alive_opponents:
        prev_bids = []
        for opp in alive_opponents:
            prev = opp.get('previous_trace', {}) or {}
            if prev.get('bid') is not None:
                try:
                    prev_bids.append(float(prev.get('bid')))
                except Exception:
                    pass
        if prev_bids:
            highest_prev_bid = max(prev_bids)

    # Urgency adjustments
    urgency = 0.0
    if hp <= 2:
        urgency += 0.35
    elif hp <= 4:
        urgency += 0.2

    if no_water_days >= 2:
        urgency += 0.25
    elif no_water_days == 1:
        urgency += 0.12

    # Supply pressure: if supply is low, bid more to secure water.
    if supply <= float(MIN_SUPPLY):
        urgency += 0.15
    elif supply >= float(MAX_SUPPLY):
        urgency -= 0.05

    bid = base_bid * (1.0 + urgency)

    # If someone previously bid very high, try to outbid slightly if we can afford it.
    if highest_prev_bid is not None:
        try:
            highest_prev_bid_f = float(highest_prev_bid)
        except Exception:
            highest_prev_bid_f = None
        if highest_prev_bid_f is not None:
            # If they were extremely aggressive, either match pressure or conserve if low hp.
            if highest_prev_bid_f >= DAILY_SALARY * 0.85:
                if hp > 3:
                    bid = min(bid, DAILY_SALARY * 0.75)
                else:
                    bid = max(bid, DAILY_SALARY * 0.9)
            else:
                # Otherwise, bid just above their typical pressure.
                bid = max(bid, highest_prev_bid_f + 1.0)

    # Budget safety: never bid more than what we can pay.
    # Also avoid bidding too low late in the episode.
    remaining_days = max(0, 10 - day)
    late_factor = 1.0
    if remaining_days <= 3:
        late_factor = 1.15
    elif remaining_days <= 5:
        late_factor = 1.07

    bid *= late_factor

    # Clamp bid to a reasonable range.
    min_reasonable = DAILY_SALARY * 0.25
    max_reasonable = DAILY_SALARY * 1.0
    if bid < min_reasonable:
        bid = min_reasonable
    if bid > max_reasonable:
        bid = max_reasonable

    if budget <= 0:
        return 0.0

    if bid > budget:
        bid = budget

    # Ensure non-negative and float output.
    if bid < 0:
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

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    my_hp = float(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Reaction to yesterday bids (only immediate trace)
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # If someone was bidding extremely high yesterday, increase pressure.
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate how many units of water are likely needed to avoid starvation pressure.
    # We don't know exact auction mechanics, but we can use supply to scale aggressiveness.
    # When supply is scarce (closer to MIN_SUPPLY), we bid more.
    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    scarcity = max(0.0, min(1.0, scarcity))

    # Baseline bid tuned to mid-tier bids seen yesterday (~108-115 around salary 90 -> ~1.2x salary).
    # We avoid overpaying by default; step up with low hp / no-water days or high opponent bids.
    base = DAILY_SALARY * (0.55 + 0.25 * scarcity)  # ~49.5 to 72.0

    # If our hp is low or we've missed water recently, we must secure allocation.
    if my_hp <= 2.0 or my_no_water_days >= 2:
        base = DAILY_SALARY * (0.85 + 0.1 * scarcity)  # ~76.5 to 86.5

    # If any opponent was bidding very high yesterday, match their pressure.
    if highest_prev_bid >= DAILY_SALARY * 1.2:  # ~108
        if my_hp > 3.0:
            base = max(base, DAILY_SALARY * (0.65 + 0.2 * scarcity))
        else:
            base = max(base, DAILY_SALARY * (0.95 + 0.05 * scarcity))

    # If opponents were bidding low, we can bid slightly above baseline to capture water.
    if highest_prev_bid > 0 and highest_prev_bid < DAILY_SALARY * 0.75:  # ~67.5
        base = max(base, highest_prev_bid + 10.0)

    # Final clamp to budget.
    bid = max(0.0, min(my_budget, base))
    return bid
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return min(float(my_status['budget']), DAILY_SALARY * 0.4)

    # Immediate reaction from yesterday's bids
    yesterday_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Supply pressure: more supply means we can bid less to still secure target water.
    # Target: aim to win only when needed; otherwise shade.
    # Estimate how many full water requirements exist.
    # (Not exact game mechanics, but used to scale aggressiveness.)
    supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if (MAX_SUPPLY - MIN_SUPPLY) != 0 else 0.5
    supply_factor = max(0.0, min(1.0, supply_factor))

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # If we're in danger, bid aggressively.
    if hp <= 2 or no_water_days >= 2:
        # Push above typical survival bids but cap by budget.
        base = DAILY_SALARY * (0.85 + 0.1 * (1.0 - supply_factor))
        if highest_prev_bid >= DAILY_SALARY * 0.8:
            base = max(base, highest_prev_bid * 1.05)
        return min(budget, base)

    # Otherwise, shade relative to yesterday's highest bid.
    # Cindy likely overbids; we undercut slightly unless supply is low.
    if highest_prev_bid > 0:
        # Undercut by 5% but keep a floor tied to water need.
        floor = DAILY_SALARY * (0.45 + 0.25 * (1.0 - supply_factor))
        bid = min(highest_prev_bid * 0.95, highest_prev_bid - 2.0)  # undercut
        bid = max(bid, floor)
    else:
        bid = DAILY_SALARY * (0.5 + 0.2 * (1.0 - supply_factor))

    # If our hp is comfortable, bid a bit less.
    if hp >= 6:
        bid *= 0.9

    # Ensure nonnegative and within budget.
    if bid < 0:
        bid = 0.0
    return min(budget, bid)
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

    # If we are already in critical hp, bid aggressively to secure water.
    if my_status['hp'] is not None and my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.5)

    # Read yesterday bids from previous_trace only (immediate reaction).
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            prev_bids.append(float(b))

    # Estimate scarcity pressure from yesterday bids.
    # Alex/Cindy had high average bids; if they were high again, we should not be last.
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Base bid depends on current supply: tighter supply => higher bid.
    # supply range is [15,25]; map to [0,1] scarcity.
    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    scarcity = max(0.0, min(1.0, scarcity))

    # If opponents previously bid very high (near our daily salary), slightly outbid.
    # Otherwise bid enough to compete but conserve.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Outbid by a small increment scaled by scarcity.
        increment = 2.0 + 6.0 * scarcity
        target = highest_prev_bid + increment
        cap = DAILY_SALARY * (0.65 + 0.25 * scarcity)
        bid = min(target, cap)
    else:
        # Moderate bid scaled by scarcity and our hp.
        hp = my_status.get('hp', 5)
        hp_factor = 0.55 if hp >= 6 else (0.7 if hp >= 4 else 0.85)
        bid = DAILY_SALARY * (0.45 + 0.35 * scarcity) * hp_factor

    # Ensure we can afford it and also avoid overspending if not needed.
    budget = float(my_status['budget']) if my_status.get('budget', 0) is not None else 0.0
    if budget <= 0:
        return 0.0

    bid = min(bid, budget)

    # If supply is extremely low relative to our requirement, increase slightly.
    # (Heuristic: when supply < 2*WATER_REQ, competition is sharper.)
    if supply < 2.0 * WATER_REQ:
        bid = min(budget, bid * (1.08 + 0.12 * scarcity))

    # Final clamp.
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    hp = my_status.get('hp', 0)
    budget = my_status.get('budget', 0.0)
    no_water_days = my_status.get('no_water_days', 0)

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', True):
            alive_opps.append(opp)

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from immediate previous_trace
    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if not opp.get('alive', True):
            continue
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Detect if someone is a likely aggressive bidder (yesterday max is high)
    aggressive = highest_prev_bid >= 0.85 * 190.5  # ~161.9

    # Tight supply means fewer winners; increase bid to secure water.
    # Use a smooth mapping based on supply position in [15,25].
    # (Convert to int only for any indexing; none used.)
    if MAX_SUPPLY - MIN_SUPPLY > 0:
        supply_t = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_t = 0.5
    supply_t = max(0.0, min(1.0, float(supply_t)))

    # Base bid target: mid-high to contest Cindy-like aggression.
    # When supply is tight (low supply_t), bid higher.
    if aggressive:
        base = DAILY_SALARY * (0.65 + 0.25 * (1.0 - supply_t))  # 0.65..0.90 of salary
    else:
        base = DAILY_SALARY * (0.45 + 0.20 * (1.0 - supply_t))  # 0.45..0.65 of salary

    # If we're in danger (low hp or accumulating no-water days), jump to near salary.
    if hp <= 2:
        base = max(base, DAILY_SALARY * 0.9)
    elif hp <= 3 or no_water_days >= 2:
        base = max(base, DAILY_SALARY * 0.75)

    # If yesterday bids were very high, slightly outbid the likely threshold.
    if highest_prev_bid > 0:
        # Bid just above highest_prev_bid fractionally, but cap by budget.
        # Keep it conservative to avoid overspending.
        threshold = min(DAILY_SALARY * 2.0, highest_prev_bid * 0.92 + 5.0)
        base = max(base, threshold)

    # Final cap: never exceed budget; also avoid extreme overspend.
    # In this game, bids are effectively bounded by budget; keep a hard safety cap.
    safety_cap = min(budget, DAILY_SALARY * 1.8)
    bid = min(base, safety_cap)

    # Ensure non-negative
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = day_context['supply']
    day = day_context['day']

    alive_opps = [o for o in opponents_status.values() if o.get('alive')]
    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Read yesterday bids from opponents (immediate reaction)
    prev_bids = []
    high_bid = 0.0
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                b = float(b)
            except Exception:
                b = None
        if b is not None:
            prev_bids.append(b)
            if b > high_bid:
                high_bid = b

    # Identify aggressive opponent(s) from yesterday
    # Cindy-like pattern: high average/max bids and survival.
    aggressive = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is None:
            continue
        try:
            b = float(b)
        except Exception:
            continue
        # Use yesterday bid as proxy for aggressiveness
        if b >= DAILY_SALARY * 1.1:  # ~99
            aggressive.append(b)

    # Base bid: target to secure water when supply is modest.
    # Supply is between 15 and 25; with our requirement 9, 2 units likely enough.
    # We approximate units needed by ceiling(supply / WATER_REQ)?? Actually allocation is per unit bid.
    # Use supply to scale aggressiveness.
    supply_level = (float(supply) - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY + 1e-9)  # 0..1

    # If we are in trouble, bid harder.
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Compute a conservative ceiling to avoid overpaying against Cindy.
    # If Cindy was bidding high, we try to slightly undercut her typical peak.
    # Use high_bid as observed maximum yesterday.
    if prev_bids:
        # Underbid strategy: aim at 70% of max observed if aggressive, else around 60% of max.
        if aggressive:
            target = max(DAILY_SALARY * (0.85 + 0.1 * (1.0 - supply_level)), high_bid * 0.75)
        else:
            target = max(DAILY_SALARY * (0.7 + 0.2 * (1.0 - supply_level)), high_bid * 0.6)
    else:
        target = DAILY_SALARY * (0.6 + 0.2 * (1.0 - supply_level))

    # Urgency adjustments
    if hp <= 2.0:
        target *= 1.15
    elif hp <= 4.0:
        target *= 1.05

    # If we've already gone some days without water, increase bid to avoid death spiral.
    if no_water_days >= 2:
        target *= 1.12

    # Safety: do not bid more than budget or too close to total budget.
    # Also, if budget is low, scale down.
    if budget <= 0:
        return 0.0

    # Keep bid below a hard cap derived from budget and salary.
    hard_cap = min(budget, DAILY_SALARY * 1.2)
    bid = min(target, hard_cap)

    # If supply is high, we can bid lower; if low, bid higher.
    if supply_level > 0.6:
        bid *= 0.9
    elif supply_level < 0.3:
        bid *= 1.05

    # Final clamp
    if bid < 0:
        bid = 0.0
    return float(min(bid, budget))
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
    day = day_context['day']

    # Alive opponents and their yesterday bid signals
    alive_opps = [o for o in opponents_status.values() if o.get('alive', False)]
    prev_bids = []
    for o in alive_opps:
        pt = o.get('previous_trace', {})
        if pt and pt.get('bid') is not None:
            try:
                prev_bids.append(float(pt['bid']))
            except Exception:
                pass

    # Baseline bid depends on supply and our HP
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Estimate how many full requirements supply can cover
    # (use int() for safety; indices not used but keep calculations robust)
    cap_units = int(supply // float(WATER_REQ)) if float(WATER_REQ) > 0 else 0

    # Determine target aggressiveness from yesterday's observed max bid pressure
    target_pressure = 0.0
    if prev_bids:
        target_pressure = max(prev_bids)

    # If someone was bidding near/above high levels yesterday, we slightly undercut unless we're in danger
    # Danger heuristic: low HP or accumulating no-water days
    in_danger = (hp <= 2.5) or (no_water_days >= 2)

    # Supply-based scaling: when supply is higher, we can bid less and still get water.
    # When supply is lower, bid more.
    supply_mid = (float(MIN_SUPPLY) + float(MAX_SUPPLY)) / 2.0
    supply_factor = 0.55 if supply >= supply_mid else 0.75

    # Core bid tiers
    if in_danger:
        # Need water now; bid to secure at least one unit of requirement.
        base = DAILY_SALARY * (0.85 if budget >= DAILY_SALARY else 0.9)
    else:
        base = DAILY_SALARY * (0.55 * supply_factor)

    # Undercut logic vs yesterday's max pressure
    if target_pressure > 0:
        # If pressure is extremely high, we avoid matching it; bid just below a fraction of it.
        if target_pressure >= DAILY_SALARY * 0.95:
            base = min(base, DAILY_SALARY * 0.65)
        elif target_pressure >= DAILY_SALARY * 0.75:
            base = min(base, DAILY_SALARY * 0.75)
        else:
            # If pressure was moderate, we can bid slightly above baseline.
            base = max(base, target_pressure * 0.85)

    # If we have very little budget, bid proportionally to avoid going bankrupt.
    if budget <= 0:
        return 0.0

    # Keep bid within budget and also avoid overspending when cap_units suggests ample supply.
    # If cap_units is 1 (tight), be more aggressive; if >=2, be more conservative.
    if cap_units <= 1:
        budget_cap = DAILY_SALARY * (0.75 if not in_danger else 0.95)
    else:
        budget_cap = DAILY_SALARY * (0.55 if not in_danger else 0.85)

    bid = min(budget, budget_cap, base)

    # Ensure non-negative and at least small positive bid if budget allows.
    if bid < 0:
        bid = 0.0
    if bid == 0.0 and budget > 0:
        bid = min(budget, DAILY_SALARY * 0.05)

    return float(bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = day_context['supply']
    day = day_context['day']

    # Identify alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # If no opponents, take a safe fraction of budget
    if not alive_opps:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace (immediate reaction only)
    yesterday_bids = []
    yesterday_info = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            b = prev.get('bid')
            yesterday_bids.append(b)
            yesterday_info.append((oid, b, prev.get('hp_after', None), prev.get('budget_after', None)))

    # Estimate opponent pressure: how aggressive yesterday was among those alive
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    # Determine baseline bid aggressiveness
    # Cindy/Eric survived with very high average bids (~110-125), so if we see high bids yesterday,
    # we avoid matching them fully unless our HP is critical.
    critical_hp = my_status.get('hp', 0) <= 2
    low_hp = my_status.get('hp', 0) <= 4

    # Supply pressure: higher supply reduces need to overbid
    supply_ratio = (float(supply) - float(MIN_SUPPLY)) / (float(MAX_SUPPLY) - float(MIN_SUPPLY))
    if supply_ratio < 0.0:
        supply_ratio = 0.0
    if supply_ratio > 1.0:
        supply_ratio = 1.0

    # If opponents were bidding very high yesterday, they likely continued to overbid.
    # We bid just enough to stay competitive.
    high_pressure = highest_prev_bid >= DAILY_SALARY * 1.15 or avg_prev_bid >= DAILY_SALARY

    # Compute target bid
    if critical_hp:
        # Must secure water; bid near salary but not beyond budget
        target = DAILY_SALARY * (0.85 + 0.1 * (1.0 - supply_ratio))
    elif low_hp:
        target = DAILY_SALARY * (0.6 + 0.25 * (1.0 - supply_ratio))
    else:
        if high_pressure:
            # Underbid relative to their high bids to exploit their tendency
            target = DAILY_SALARY * (0.45 + 0.15 * (1.0 - supply_ratio))
        else:
            target = DAILY_SALARY * (0.55 + 0.1 * (1.0 - supply_ratio))

    # If we have many no-water days, increase urgency
    no_water_days = my_status.get('no_water_days', 0)
    if no_water_days >= 2:
        target *= 1.15
    if no_water_days >= 4:
        target *= 1.25

    # Final clamp to budget and non-negative
    budget = float(my_status.get('budget', 0.0))
    if budget <= 0.0:
        return 0.0
    if target < 0.0:
        target = 0.0
    if target > budget:
        target = budget

    return float(target)
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

    # Identify alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # If no one is alive, bid minimally but safely
    if not alive_opps:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace only (immediate reaction)
    yesterday_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Determine opponent pressure from yesterday
    highest_prev = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev = (sum(yesterday_bids) / len(yesterday_bids)) if yesterday_bids else 0.0

    # Supply pressure: when supply is low, competition is higher.
    # Use a simple discretization with explicit int() for safety.
    # Map supply into 0..2 buckets.
    bucket = int((supply - MIN_SUPPLY) / ((MAX_SUPPLY - MIN_SUPPLY) / 3.0))
    if bucket < 0:
        bucket = 0
    if bucket > 2:
        bucket = 2

    # Base strategy: conserve unless my HP is low.
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # If I'm close to death, bid aggressively.
    if hp <= 1:
        target = DAILY_SALARY * 0.95
    elif hp == 2:
        target = DAILY_SALARY * 0.75
    else:
        # Otherwise, bid relative to yesterday's highest pressure.
        # We undercut Cindy/Alex-like extremes but can still match mid-tier.
        # bucket 0 (low supply) -> bid higher; bucket 2 (high supply) -> bid lower.
        supply_factor = [0.62, 0.50, 0.40][bucket]

        # If yesterday's highest bid was huge, assume someone overspent and will back off.
        # Still bid enough to avoid being starved.
        if highest_prev >= DAILY_SALARY * 1.9:
            target = DAILY_SALARY * supply_factor
        else:
            # If pressure was moderate, slightly exceed average but not the max.
            # Add a small increment over a fraction of avg/high.
            ref = max(avg_prev * 0.65, highest_prev * 0.35)
            target = max(DAILY_SALARY * supply_factor, ref + 5.0)

        # If I've already gone without water, increase bid to prevent further HP loss.
        if no_water_days >= 2:
            target *= 1.15

    # Final clamp: cannot exceed budget; also avoid runaway bids.
    # Keep bids within a reasonable cap relative to daily salary.
    cap = DAILY_SALARY * (2.0 if hp <= 2 else 1.2)
    target = min(float(cap), float(target))
    target = min(float(budget), float(target))

    # Ensure non-negative
    if target < 0.0:
        target = 0.0

    return target
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
    day = day_context.get('day', 0)

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return float(min(budget, DAILY_SALARY * 0.4))

    # React to yesterday bids (only immediate trace)
    yesterday_bids = []
    yesterday_dead = 0
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                yesterday_bids.append(float(bid))
            except Exception:
                pass
        # If opponent died yesterday (final_hp < 0), they tended to bid aggressively
        # We infer from their previous_trace status/hp_after if present.
        status = prev.get('status', '')
        hp_after = prev.get('hp_after', None)
        if (isinstance(hp_after, (int, float)) and float(hp_after) < 0) or (isinstance(status, str) and 'dead' in status.lower()):
            yesterday_dead += 1

    # Baseline aggressiveness from supply pressure (more supply -> lower bid needed)
    # supply is between 15 and 25
    supply_norm = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY + 1e-9)
    supply_norm = max(0.0, min(1.0, supply_norm))

    # Determine target bid level
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        avg_prev = sum(yesterday_bids) / float(len(yesterday_bids))
    else:
        highest_prev = 0.0
        avg_prev = 0.0

    # If we are in danger, bid higher; otherwise stay moderate to avoid budget burn.
    danger = (hp <= 2) or (no_water_days >= 2)

    # If others bid very high yesterday, they may be trying to secure water; bid slightly below the peak.
    peak_threshold = DAILY_SALARY * 0.85

    if danger:
        if highest_prev >= peak_threshold:
            target = min(budget, max(DAILY_SALARY * 0.75, highest_prev * 0.55))
        else:
            target = min(budget, DAILY_SALARY * (0.65 + 0.2 * (1.0 - supply_norm)))
    else:
        if highest_prev >= peak_threshold:
            # Avoid repeating their overbidding; bid around average or a bit above baseline.
            target = min(budget, max(DAILY_SALARY * 0.45, avg_prev * 0.55))
        else:
            target = min(budget, DAILY_SALARY * (0.48 + 0.18 * (1.0 - supply_norm)))

    # If we see any signs of yesterday deaths among opponents, slightly reduce to exploit potential budget exhaustion.
    if yesterday_dead > 0:
        target *= 0.92

    # Ensure at least a small competitive bid if budget allows
    min_reasonable = min(budget, DAILY_SALARY * 0.25)
    if target < min_reasonable:
        target = min_reasonable

    # Final cap
    if budget <= 0:
        return 0.0
    return float(max(0.0, min(budget, target)))
"""
