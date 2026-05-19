# ============================================================
# Experiment: exp_080
# Agent: Bob
# Source: exp_080
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    my_hp = float(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    if not alive_opponents:
        target = min(my_budget, DAILY_SALARY * 0.35)
        return float(target)

    # Read yesterday's immediate behavior
    prev_bids = []
    prev_high_pressure = 0.0
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                b_val = float(b)
            except Exception:
                continue
            prev_bids.append(b_val)
            if b_val > prev_high_pressure:
                prev_high_pressure = b_val

    # Baseline: bid enough to contest but avoid overpaying
    # Supply is between 15 and 25; typical number of 9-unit blocks is 1.
    # We bias toward securing at least one unit of requirement.
    # Convert supply to a rough “how many winners possible” estimate.
    # Use conservative scaling to avoid index issues.
    blocks = max(1.0, supply / float(WATER_REQ))
    contest_factor = 1.0 / blocks

    if prev_bids:
        high_thresh = DAILY_SALARY * 0.85
        mid_thresh = DAILY_SALARY * 0.6

        if prev_high_pressure >= high_thresh:
            # They were likely desperate; we should not lose the contest.
            if my_hp <= 2.0 or my_no_water_days >= 2:
                bid = DAILY_SALARY * 0.95
            else:
                bid = DAILY_SALARY * 0.45 + (prev_high_pressure * 0.35)
        elif prev_high_pressure >= mid_thresh:
            # Moderate pressure: bid slightly above a safe baseline.
            bid = DAILY_SALARY * 0.35 + (prev_high_pressure * 0.25)
        else:
            # They were not aggressive: bid near baseline and save budget.
            bid = DAILY_SALARY * 0.28
    else:
        # No trace info: use hp/budget and supply to decide.
        if my_hp <= 2.0 or my_no_water_days >= 2:
            bid = DAILY_SALARY * 0.8
        else:
            bid = DAILY_SALARY * (0.32 + 0.12 * contest_factor)

    # Clamp to budget and reasonable bounds
    bid = float(bid)
    if bid > my_budget:
        bid = my_budget

    # Additional clamp relative to supply: never bid more than what would be wasteful.
    # Since water is scarce, keep within 0.95*DAILY_SALARY.
    if bid > DAILY_SALARY * 0.95:
        bid = DAILY_SALARY * 0.95
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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    if not alive:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Inspect yesterday bids from immediate previous_trace only
    prev_bids = []
    for oid, o in alive:
        prev = o.get('previous_trace', {})
        if isinstance(prev, dict) and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate how many full water units supply can support (per allocation unit = WATER_REQ)
    # Use int() for safety.
    capacity_units = int(supply / float(WATER_REQ))

    # Base aggressiveness: if supply is tight or we are close to death, bid more.
    tight_supply = supply <= float(WATER_REQ) * 1.2 or capacity_units <= 1

    # If Cindy likely dominates (very high previous bid), we avoid bidding near her unless necessary.
    cindy_like = highest_prev_bid >= DAILY_SALARY * 0.9

    if my_hp <= 2.0 or my_no_water_days >= 2:
        # Emergency: bid to secure water.
        target = DAILY_SALARY * (0.85 if cindy_like else 0.75)
    elif tight_supply:
        target = DAILY_SALARY * (0.65 if cindy_like else 0.55)
    else:
        # Normal: bid enough to beat low/medium bidders, but not to match the top.
        target = DAILY_SALARY * (0.45 if cindy_like else 0.55)

    # If yesterday's highest bid was not extreme, try to slightly undercut.
    if highest_prev_bid > 0 and highest_prev_bid < DAILY_SALARY * 0.9:
        target = min(target, highest_prev_bid + 10.0)

    # Clamp by budget
    bid = max(0.0, min(my_budget, target))

    # Small day-based modulation to reduce tie risk
    if day % 2 == 1:
        bid = bid * 0.98

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

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace only
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Pressure model from yesterday: if someone paid very high, they likely tried to outbid for scarce water.
    # We counter with a slightly lower but still competitive bid.
    scarcity_factor = 0.0
    if supply <= MIN_SUPPLY + 1e-9:
        scarcity_factor = 1.0
    elif supply <= (MIN_SUPPLY + MAX_SUPPLY) / 2.0:
        scarcity_factor = 0.6
    else:
        scarcity_factor = 0.3

    # Base bid: ensure we can keep hp stable; if we are already in danger, bid more.
    if my_hp <= 2.0 or my_no_water_days >= 2:
        base = DAILY_SALARY * (0.75 + 0.15 * scarcity_factor)
    elif my_hp <= 4.0 or my_no_water_days == 1:
        base = DAILY_SALARY * (0.55 + 0.15 * scarcity_factor)
    else:
        base = DAILY_SALARY * (0.45 + 0.10 * scarcity_factor)

    # If yesterday saw extreme bids, adjust to avoid being outbid.
    extreme_threshold = DAILY_SALARY * 0.95
    if highest_prev_bid >= extreme_threshold:
        # Bid just below the extreme to win with high probability without fully matching.
        target = min(my_budget, highest_prev_bid * 0.92)
        # Ensure target is not too low relative to our base.
        target = max(target, base)
        return max(0.0, min(my_budget, target))

    # Otherwise, try to beat typical bids without starting a full war.
    # Use a conservative increment over the highest previous bid if it is not too high.
    war_threshold = DAILY_SALARY * 0.70
    if highest_prev_bid >= war_threshold:
        target = min(my_budget, highest_prev_bid * 0.85)
        target = max(target, base)
        return max(0.0, min(my_budget, target))

    # Default: bid near base, but scaled by how much supply exists.
    # If supply is higher, we can bid less.
    supply_scale = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_scale = max(0.0, min(1.0, supply_scale))
    bid = base * (1.0 - 0.25 * supply_scale)

    # Never bid above budget or below a minimal floor.
    min_bid_floor = 1.0
    bid = max(min_bid_floor, min(my_budget, bid))
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
    day = day_context.get('day', 0)

    my_hp = float(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive.append((opp_id, opp))

    def clamp_bid(x):
        if my_budget <= 0:
            return 0.0
        if x < 0:
            return 0.0
        if x > my_budget:
            return my_budget
        return float(x)

    if not alive:
        return clamp_bid(min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from immediate previous_trace
    prev_bids = []
    for opp_id, opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Estimate how aggressive the field was yesterday
    prev_max = max(prev_bids) if prev_bids else 0.0
    prev_avg = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    # Base target: if others were bidding very high, we must compete; otherwise undercut slightly.
    # Use supply to decide aggressiveness (higher supply => less need to overbid).
    supply_norm = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    if supply_norm < 0.0:
        supply_norm = 0.0
    if supply_norm > 1.0:
        supply_norm = 1.0

    # Determine urgency from my HP/no-water streak
    urgency = 0.0
    if my_hp <= 2:
        urgency = 1.0
    elif my_hp <= 4:
        urgency = 0.7
    elif my_hp <= 6:
        urgency = 0.4
    else:
        urgency = 0.2

    if my_no_water_days >= 2:
        urgency = max(urgency, 0.8)
    elif my_no_water_days == 1:
        urgency = max(urgency, 0.5)

    # Aggression factor based on yesterday's max bid
    # Alex/Eric high bids suggest competition; Cindy died with 0 bids => others likely won't go that low.
    if prev_max >= DAILY_SALARY * 1.35:
        # Very competitive yesterday; bid near the high end but still slightly undercut.
        base = DAILY_SALARY * (0.95 - 0.25 * supply_norm)
        # If my HP is okay, try to undercut the max by a bit.
        if urgency < 0.6:
            base = min(base, prev_max - 3.0)
    elif prev_max >= DAILY_SALARY * 0.85:
        base = DAILY_SALARY * (0.75 - 0.18 * supply_norm)
        if urgency < 0.6:
            base = min(base, prev_max - 2.0)
    else:
        # Field was mostly low; we can bid enough to secure water without overspending.
        base = DAILY_SALARY * (0.55 - 0.15 * supply_norm)
        if urgency > 0.7:
            base = DAILY_SALARY * (0.75 - 0.12 * supply_norm)

    # Ensure we don't bid too low when supply is low (more likely others contest)
    if supply <= float(WATER_REQ) + 6.0:
        base = max(base, DAILY_SALARY * 0.45)

    # Convert urgency into final bid scaling
    final_bid = base * (0.75 + 0.5 * urgency)

    # Safety: if budget is low, cap to a fraction to avoid running out in later days
    # but still react to urgency.
    if my_budget < DAILY_SALARY * 0.6:
        final_bid = min(final_bid, my_budget * (0.85 if urgency > 0.7 else 0.6))

    # Final clamp
    return clamp_bid(final_bid)
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
    day = day_context['day']

    # Alive opponents and yesterday bids
    alive_opps = []
    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {}) or {}
            b = prev.get('bid', None)
            if b is not None:
                try:
                    yesterday_bids.append(float(b))
                except Exception:
                    pass

    # Budget/HP risk handling
    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # If we are already in danger, prioritize survival
    if my_hp <= 1 or no_water_days >= 2:
        # High bid but still bounded by budget
        return max(1.0, min(my_budget, DAILY_SALARY * 0.95))

    # Estimate market pressure from yesterday
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / float(len(yesterday_bids))
    else:
        highest_prev_bid = 0.0
        avg_prev_bid = 0.0

    # If someone was bidding very high yesterday, likely competition; bid above their typical level
    # But avoid overcommitting like Cindy (who died after high pressure).
    pressure = 0.0
    if highest_prev_bid > 0:
        pressure = min(1.0, highest_prev_bid / (DAILY_SALARY * 1.2))

    # Supply-based adjustment: higher supply reduces need to outbid.
    # Ensure indices are safe if we ever discretize.
    supply_norm = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_norm = max(0.0, min(1.0, supply_norm))

    # Base target bid
    # When supply is high, bid closer to avg; when supply is low, bid closer to highest_prev_bid.
    if highest_prev_bid > 0:
        target = (1.0 - supply_norm) * (highest_prev_bid * 0.98) + supply_norm * (avg_prev_bid * 1.02)
    else:
        target = DAILY_SALARY * (0.55 + 0.2 * (1.0 - supply_norm))

    # Apply pressure dampening to avoid Cindy-like collapse
    # If pressure is extreme, don't go all-in; instead, slightly under highest_prev_bid.
    damp = 1.0 - 0.25 * pressure
    target *= damp

    # HP-safe cap: if hp is modest, don't exceed a fraction of budget.
    hp_factor = 0.45 if my_hp <= 3 else 0.65
    budget_cap = my_budget * hp_factor

    # Final bid: at least enough to matter, at most budget_cap and a reasonable multiple of salary.
    min_bid = max(1.0, DAILY_SALARY * 0.25)
    max_bid = min(budget_cap, DAILY_SALARY * 0.9)

    bid = max(min_bid, min(max_bid, target))
    return float(bid)
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
    day = day_context.get('day', 0)

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive = []
    for oid, o in opponents_status.items():
        if o is not None and o.get('alive', False):
            alive.append(o)

    if not alive:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Pull yesterday bids from previous_trace only
    prev_bids = []
    for o in alive:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Identify if Cindy was applying strong pressure yesterday
    cindy_pressure = 0.0
    for oid, o in opponents_status.items():
        if oid == 'Cindy' and o is not None and o.get('alive', False):
            prev = o.get('previous_trace', {}) or {}
            b = prev.get('bid', None)
            if b is not None:
                try:
                    cindy_pressure = float(b)
                except Exception:
                    cindy_pressure = 0.0

    # Supply pressure: more supply => less need to overbid
    # Use int() for any index-like operations (none here), but keep logic numeric.
    supply_factor = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_factor = 0.5
    supply_factor = max(0.0, min(1.0, supply_factor))

    # Core bid target
    # If Cindy pushed hard yesterday, we bid enough to not lose the water entirely.
    # Otherwise bid a competitive mid value.
    if cindy_pressure >= DAILY_SALARY * 1.35 or highest_prev_bid >= DAILY_SALARY * 1.2:
        # When opponents likely spend, our hp/no-water days determine whether to match more.
        if my_hp <= 2 or my_no_water_days >= 2:
            target = DAILY_SALARY * (0.95 - 0.25 * supply_factor)
        else:
            target = DAILY_SALARY * (0.65 - 0.15 * supply_factor)
        # Slightly undercut relative to their pressure to avoid waste
        target = min(target, cindy_pressure * 0.98 if cindy_pressure > 0 else target)
    else:
        if my_hp <= 2 or my_no_water_days >= 2:
            target = DAILY_SALARY * (0.85 - 0.2 * supply_factor)
        else:
            target = DAILY_SALARY * (0.55 - 0.1 * supply_factor)

    # Ensure we don't bid more than we can afford
    bid = max(0.0, min(my_budget, target))

    # If budget is extremely low, bid whatever small amount still helps
    if my_budget <= 1.0:
        return my_budget

    # Add a small deterministic nudge by day to break ties
    nudge = ((int(day) % 7) - 3) * 0.5
    bid = bid + nudge
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = day_context['supply']
    day = day_context['day']

    # Alive opponents
    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    if not alive_opponents:
        # If no one else is alive, conserve budget but stay safe
        return min(my_status['budget'], DAILY_SALARY * 0.45)

    # Read yesterday bids from previous_trace (immediate reaction only)
    prev_bids = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Determine pressure from yesterday
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_highest_prev_bid = 0.0
    if len(prev_bids) >= 2:
        sorted_bids = sorted(prev_bids, reverse=True)
        second_highest_prev_bid = sorted_bids[1]

    # Compute a conservative target based on supply: if supply is tight, increase bid.
    # supply is between 15 and 25; translate to scarcity level.
    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)  # 0 (plenty) to 1 (tight)
    scarcity = max(0.0, min(1.0, scarcity))

    # Base bid: aim around mid of typical survivor bids (~90-110) but not max.
    # If highest_prev_bid is very high, we need to contest more.
    base = DAILY_SALARY * (0.48 + 0.25 * scarcity)  # ~43.2 to ~66.6

    # If others were bidding near/above daily salary, we must raise.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # If our hp is low, pay more; otherwise just slightly over second-highest.
        if my_status['hp'] <= 2:
            target = max(base, min(my_status['budget'], DAILY_SALARY * 0.95))
        else:
            # Try to beat the likely winner without going to their max.
            target = max(base, second_highest_prev_bid + 2.5)
    else:
        # If yesterday pressure was moderate, bid to secure water but conserve budget.
        # Slightly above base, and if highest_prev_bid exists, add a small increment.
        if highest_prev_bid > 0:
            target = max(base, min(highest_prev_bid + 1.5, DAILY_SALARY * (0.75 + 0.1 * scarcity)))
        else:
            target = base

    # If we are already on no-water streak, escalate
    no_water_days = my_status.get('no_water_days', 0)
    if no_water_days >= 2:
        target = max(target, DAILY_SALARY * (0.75 + 0.15 * scarcity))
    if no_water_days >= 3:
        target = max(target, DAILY_SALARY * 0.95)

    # Ensure we don't exceed budget
    budget = float(my_status['budget'])
    if budget <= 0:
        return 0.0

    # Final clamp: never bid above a reasonable ceiling to avoid elimination by spending
    ceiling = DAILY_SALARY * (1.05 + 0.05 * scarcity)
    target = min(float(target), ceiling, budget)

    # If target is too low to be meaningful vs typical bids, nudge upward.
    # This helps against aggressive survivors.
    if target < DAILY_SALARY * 0.55 and my_status['hp'] > 2:
        target = min(budget, DAILY_SALARY * (0.6 + 0.1 * scarcity))

    return float(target)
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

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    yesterday_bids = []
    yesterday_pressures = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                yesterday_bids.append(float(bid))
            except Exception:
                pass
        # Use yesterday hp_after as a proxy for how costly it was to them
        hp_after = prev.get('hp_after', None)
        if hp_after is not None:
            try:
                yesterday_pressures.append(float(hp_after))
            except Exception:
                pass

    # If others were spending a lot yesterday, they likely expect to win shares again.
    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / max(1, len(yesterday_bids))
    else:
        max_prev_bid = 0.0
        avg_prev_bid = 0.0

    # Base bid: tie to supply availability.
    # With medium supply (15-25), aim for a moderate bid unless my hp is critical.
    supply_factor = (supply - MIN_SUPPLY) / max(1e-9, (MAX_SUPPLY - MIN_SUPPLY))
    supply_factor = max(0.0, min(1.0, supply_factor))

    # Determine aggressiveness from my condition.
    critical = (hp <= 2) or (no_water_days >= 2)
    strained = (hp <= 4) or (no_water_days >= 1)

    # Exploit: if Cindy/Alex were high yesterday (max_prev_bid large), they may outbid each other.
    # I can stay below their peak but above a floor.
    if max_prev_bid >= DAILY_SALARY * 2.0:  # ~180
        base = DAILY_SALARY * (0.45 + 0.15 * supply_factor)
        if critical:
            base = DAILY_SALARY * 0.85
        elif strained:
            base = DAILY_SALARY * 0.65
        # Cap under the max_prev_bid to avoid overpaying.
        bid = min(base, max_prev_bid * 0.75)
    elif max_prev_bid >= DAILY_SALARY * 1.2:  # ~108
        base = DAILY_SALARY * (0.40 + 0.10 * supply_factor)
        if critical:
            base = DAILY_SALARY * 0.75
        elif strained:
            base = DAILY_SALARY * 0.55
        bid = min(base, max_prev_bid * 0.85)
    else:
        base = DAILY_SALARY * (0.35 + 0.08 * supply_factor)
        if critical:
            base = DAILY_SALARY * 0.70
        elif strained:
            base = DAILY_SALARY * 0.50
        # If others are not spending, slightly undercut average.
        bid = min(base, avg_prev_bid * 0.9) if avg_prev_bid > 0 else base

    # Ensure we don't bid more than we can afford.
    bid = float(bid)
    if bid < 0:
        bid = 0.0
    bid = min(bid, budget)

    # Safety floor: if budget is decent and I'm not critical, still bid enough to avoid starvation.
    if not critical and budget >= DAILY_SALARY * 0.6:
        bid = max(bid, DAILY_SALARY * 0.30)
    if critical:
        bid = max(bid, min(budget, DAILY_SALARY * 0.60))

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

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    # If no opponents are alive, bid conservatively.
    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.35))

    # Read yesterday bids from previous_trace (immediate reaction only).
    prev_bids = []
    for oid, o in alive:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Supply pressure: if supply is low, more likely others must fight for water.
    supply_ratio = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    # low ratio => tight supply => bid higher
    tightness = 1.0 - max(0.0, min(1.0, supply_ratio))

    # Determine a target bid band based on yesterday's observed aggressiveness.
    # Eric survived with moderate bids; Cindy overspent to 0 budget.
    # We'll anchor to a percentile-like heuristic from prev_bids.
    if prev_bids:
        sorted_bids = sorted(prev_bids)
        n = len(sorted_bids)
        # median and 75th percentile
        median_bid = sorted_bids[int((n - 1) * 0.5)]
        p75_bid = sorted_bids[int((n - 1) * 0.75)]
        highest_prev = sorted_bids[-1]
    else:
        median_bid = DAILY_SALARY * 0.55
        p75_bid = DAILY_SALARY * 0.75
        highest_prev = DAILY_SALARY * 0.9

    # If we are in danger (low hp or accumulating no-water days), increase bid.
    danger = 0.0
    if hp <= 2.0:
        danger += 1.0
    if no_water_days >= 2:
        danger += 0.7

    # If yesterday there was very high bidding (likely a war), we should avoid overbidding.
    # But if supply is tight and we're in danger, we must secure water.
    war_signal = 0.0
    if highest_prev >= DAILY_SALARY * 1.4:
        war_signal = 1.0
    elif highest_prev >= DAILY_SALARY * 1.0:
        war_signal = 0.6

    # Base bid: slightly above median when tight; otherwise around median.
    base = median_bid + (tightness * 0.25 * (p75_bid - median_bid))

    # Adjust for danger and war.
    # War reduces our willingness to chase; danger increases it.
    target = base + (danger * (DAILY_SALARY * 0.35)) - (war_signal * (DAILY_SALARY * 0.15))

    # Clamp target to reasonable range to avoid bankruptcy.
    # Also keep some budget for future days.
    max_affordable = max(0.0, min(budget, DAILY_SALARY * 1.2))
    min_reasonable = DAILY_SALARY * (0.35 if tightness < 0.5 else 0.55)

    # Ensure we can always bid at least something positive if possible.
    target = max(min_reasonable, min(target, max_affordable))

    # If budget is too low, bid whatever we can.
    if budget <= 0.0:
        return 0.0

    # Final: bid cannot exceed budget.
    return max(0.0, min(budget, float(target)))
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

    # Alive opponents and their yesterday bids
    alive_opponents = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    if not alive_opponents:
        # If no opponents alive, spend to secure requirement
        return int(min(my_status['budget'], DAILY_SALARY * 0.5))

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Pressure logic: Cindy/Alex/Eric were around ~100; bid just above when supply is tight.
    # Supply tightness: fewer multiples of WATER_REQ implies higher scarcity pressure.
    # Avoid float indices by not indexing lists.
    scarcity_ratio = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        scarcity_ratio = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY + 1e-9)

    # Base bid target
    # If yesterday's max bid indicates strong competition, increase bid slightly.
    if highest_prev_bid >= 0.85 * DAILY_SALARY:
        # When competition was high, only overbid if my HP is at risk or supply is tight.
        if my_status['hp'] <= 3 or scarcity_ratio >= 0.5:
            target = highest_prev_bid + 3.0
        else:
            target = max(DAILY_SALARY * 0.55, highest_prev_bid - 5.0)
    else:
        # Moderate competition: bid enough to not lose consistently, but conserve budget.
        if my_status['hp'] <= 2:
            target = DAILY_SALARY * 0.85
        else:
            target = DAILY_SALARY * (0.45 + 0.25 * scarcity_ratio)

    # Ensure we don't bid above budget; also avoid bidding too low when supply is very tight.
    budget = float(my_status.get('budget', 0.0))
    if budget <= 0:
        return 0

    # Minimum effective bid: if supply is near MIN_SUPPLY, slightly raise to secure water.
    min_effective = DAILY_SALARY * (0.35 + 0.25 * scarcity_ratio)

    final_bid = min(budget, max(target, min_effective if my_status['hp'] > 0 else DAILY_SALARY * 0.9))

    # If we've already had many no-water days, increase aggressiveness.
    no_water_days = int(my_status.get('no_water_days', 0) or 0)
    if no_water_days >= 2:
        final_bid = min(budget, final_bid * 1.15)

    # Return integer bid
    return int(final_bid)
"""
