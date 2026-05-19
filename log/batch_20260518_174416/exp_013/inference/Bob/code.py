# ============================================================
# Experiment: exp_013
# Agent: Bob
# Source: exp_013
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    # If no opponents, bid conservatively to cover our requirement.
    if not alive_opponents:
        return min(my_status.get('budget', 0), DAILY_SALARY * 0.4)

    # Read yesterday's immediate behavior from previous_trace.
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

    hp = my_status.get('hp', 0)
    budget = my_status.get('budget', 0)

    # Estimate scarcity from supply.
    # Note: use int() for any list indexing; none used here.
    scarcity_factor = 0.0
    if supply <= float(WATER_REQ):
        scarcity_factor = 1.0
    elif supply <= float(WATER_REQ + 3):
        scarcity_factor = 0.7
    elif supply <= 20.0:
        scarcity_factor = 0.4
    else:
        scarcity_factor = 0.2

    # Determine competitive pressure from opponents' previous bids.
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev_bid

        # If someone previously bid very high, we assume they are trying to secure water.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # Bid enough to beat the likely winner but preserve budget.
            base = max(highest_prev_bid * 0.98, second_prev_bid + 1.0)
            # If our HP is low, we must prioritize water.
            if hp <= 2:
                target = base
            elif hp <= 3:
                target = base * (1.0 + 0.05 * scarcity_factor)
            else:
                target = base * (0.95 + 0.05 * (1.0 - scarcity_factor))
        else:
            # Low competition signal: bid moderately, slightly above previous leader to ensure advantage.
            leader = highest_prev_bid
            target = max(DAILY_SALARY * (0.45 + 0.2 * scarcity_factor), leader + 2.0)
    else:
        # No signal: bid based on our HP and scarcity.
        if hp <= 2:
            target = DAILY_SALARY * (0.85 + 0.1 * scarcity_factor)
        elif hp <= 3:
            target = DAILY_SALARY * (0.65 + 0.15 * scarcity_factor)
        else:
            target = DAILY_SALARY * (0.5 + 0.1 * scarcity_factor)

    # Keep within budget and avoid extreme overbids.
    # Cap at about 1.1 * daily salary to reduce waste.
    cap = DAILY_SALARY * 1.1
    bid = min(budget, cap, target)

    # Ensure non-negative bid.
    if bid < 0:
        bid = 0

    # Game safety: at least a small amount if budget allows.
    if bid == 0 and budget > 0:
        bid = min(budget, DAILY_SALARY * 0.2)

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

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    # Alive opponents and their yesterday bids
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            prev = o.get('previous_trace', {}) or {}
            bid = prev.get('bid', None)
            alive.append((oid, o, bid))

    if not alive:
        return float(min(my_status.get('budget', 0.0), DAILY_SALARY * 0.4))

    # Extract yesterday bids to infer aggressiveness
    yesterday_bids = []
    for _, _, bid in alive:
        if bid is not None:
            try:
                yesterday_bids.append(float(bid))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how many bids we might need to beat based on supply
    # If supply is scarce relative to WATER_REQ, we must bid more.
    supply_ratio = float(supply) / float(WATER_REQ) if WATER_REQ > 0 else 1.0
    scarcity = 1.0
    if supply_ratio >= 2.5:
        scarcity = 0.85
    elif supply_ratio >= 2.0:
        scarcity = 1.0
    else:
        scarcity = 1.15

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))

    # If we are in danger, bid much more.
    if hp <= 2:
        target = DAILY_SALARY * 0.95 * scarcity
    elif hp <= 4:
        target = DAILY_SALARY * 0.75 * scarcity
    else:
        # Otherwise, react to yesterday's highest pressure.
        # Cindy/Eric were bidding ~125-143; match partially unless they were extremely high.
        if highest_prev_bid >= DAILY_SALARY * 1.3:
            target = DAILY_SALARY * 0.85 * scarcity
        elif highest_prev_bid >= DAILY_SALARY * 0.9:
            target = DAILY_SALARY * 0.65 * scarcity
        else:
            target = DAILY_SALARY * 0.55 * scarcity

    # Keep bid within what budget can support.
    bid = min(budget, target)

    # Add a small increment if we think others are clustered high.
    # Use yesterday max bid to decide whether to slightly overbid.
    if highest_prev_bid > 0:
        if highest_prev_bid >= DAILY_SALARY * 1.0:
            bid = min(budget, bid + 3.0)

    # Ensure non-negative
    if bid < 0:
        bid = 0.0
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

    # Identify alive opponents and use only yesterday's previous_trace
    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            prev = opp.get('previous_trace', {}) or {}
            alive.append((opp_id, opp, prev))

    if not alive:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Collect yesterday bids and pressure signals
    yesterday_bids = []
    for _, opp, prev in alive:
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # If Cindy is alive, her yesterday high average suggests she will continue aggressive bidding.
    # We'll cap our bid to avoid burning budget while still contesting.
    cindy = opponents_status.get('Cindy', None)
    cindy_prev = (cindy.get('previous_trace', {}) if cindy else {})
    cindy_bid = cindy_prev.get('bid', None)

    # Base bid determined by supply and our HP
    # Higher supply -> we can bid less to still secure enough water.
    # Lower supply -> bid more to avoid losing to Cindy.
    supply_frac = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    if supply_frac < 0.0:
        supply_frac = 0.0
    if supply_frac > 1.0:
        supply_frac = 1.0

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    # Target contest level: start from a moderate fraction of salary.
    # If HP is low, increase.
    if hp <= 2.0:
        base = DAILY_SALARY * 0.85
    elif hp <= 4.0:
        base = DAILY_SALARY * 0.70
    else:
        base = DAILY_SALARY * 0.55

    # Adjust for supply: lower supply increases bid
    base *= (0.85 + (1.0 - supply_frac) * 0.35)  # range roughly 0.85..1.2

    # If Cindy was bidding high yesterday, slightly increase our bid to stay competitive.
    if cindy is not None and cindy.get('alive', False):
        if cindy_bid is not None:
            try:
                cindy_bid_f = float(cindy_bid)
            except Exception:
                cindy_bid_f = None
            if cindy_bid_f is not None:
                # If Cindy bid extremely high yesterday, we don't match fully; just nudge above a likely threshold.
                if cindy_bid_f >= DAILY_SALARY * 0.85:
                    base = max(base, DAILY_SALARY * 0.62)
                elif cindy_bid_f >= DAILY_SALARY * 0.6:
                    base = max(base, DAILY_SALARY * 0.56)

    # If there were any very high bids yesterday, raise a bit; otherwise keep moderate.
    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        if highest_prev >= DAILY_SALARY * 0.9:
            base *= 1.08
        elif highest_prev >= DAILY_SALARY * 0.7:
            base *= 1.04

    # Ensure we don't overbid beyond budget.
    # Also, avoid bidding more than what would be needed to secure water with some margin.
    # Convert supply to a rough number of water units we can potentially get.
    # If supply is near our requirement, contest more.
    if supply <= WATER_REQ + 1.0:
        base *= 1.12
    elif supply >= WATER_REQ + 6.0:
        base *= 0.92

    bid = float(min(budget, base))

    # Safety: if budget is tiny, bid what's left.
    if bid < 0.0:
        bid = 0.0

    return bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 1)

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if my_budget <= 0:
        return 0.0

    # Inspect yesterday bids to infer aggressiveness
    prev_bids = []
    prev_hp_after = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                prev_bids.append(float(bid))
                prev_hp_after.append(int(prev.get('hp_after', 0)))
            except Exception:
                pass

    # Base urgency: if we've gone without water, increase bid
    urgency = 0.0
    if my_no_water_days >= 2:
        urgency = 0.35
    elif my_no_water_days == 1:
        urgency = 0.18

    # If low HP, bid more
    if my_hp <= 2:
        urgency += 0.45
    elif my_hp <= 4:
        urgency += 0.25

    # Supply pressure: higher supply reduces need to outbid
    # approximate units available
    units = int(supply / float(WATER_REQ)) if WATER_REQ > 0 else 0
    if units <= 1:
        supply_factor = 0.95
    elif units == 2:
        supply_factor = 0.85
    else:
        supply_factor = 0.75

    # Aggression estimate from yesterday
    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / float(len(prev_bids))

        # If someone was very aggressive yesterday (high bid), we should not be too low.
        if highest_prev >= DAILY_SALARY * 0.85:
            aggression = 0.30
        elif highest_prev >= DAILY_SALARY * 0.60:
            aggression = 0.20
        else:
            aggression = 0.10

        # If many opponents dropped to low hp after, likely bidding mismatch; bid slightly higher.
        low_hp_count = 0
        for hp_after in prev_hp_after:
            if hp_after <= 0:
                low_hp_count += 1
        if low_hp_count >= 1:
            aggression += 0.08

        target = DAILY_SALARY * (0.40 + aggression + urgency)

        # Keep closer to avg if we expect price competition
        if avg_prev >= DAILY_SALARY * 0.60:
            target = max(target, avg_prev * 0.85)

    else:
        target = DAILY_SALARY * (0.38 + urgency)

    target *= supply_factor

    # Cap by budget
    bid = min(my_budget, target)

    # Ensure non-negative
    if bid < 0:
        bid = 0.0

    # Small strategic floor to avoid being priced out when others are aggressive
    if prev_bids and my_budget >= 10:
        if max(prev_bids) >= DAILY_SALARY * 0.85:
            bid = max(bid, min(my_budget, DAILY_SALARY * 0.35))

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

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    if not alive_opponents:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how tight the water is: more scarcity -> bid more.
    # With supply in [15,25], total units relative to our requirement.
    water_units = supply / float(WATER_REQ) if WATER_REQ > 0 else 0.0
    scarcity = 1.0
    if water_units >= 2.5:
        scarcity = 0.75
    elif water_units >= 2.0:
        scarcity = 0.95
    else:
        scarcity = 1.15

    # Base bid depends on our urgency.
    if hp <= 2 or no_water_days >= 2:
        urgency = 1.25
    elif hp <= 4 or no_water_days >= 1:
        urgency = 1.05
    else:
        urgency = 0.9

    # If others were already bidding very high yesterday, we must match closer.
    # From trace: Cindy/Alex avg around ~105-114 with max ~135; use that scale.
    if highest_prev_bid >= DAILY_SALARY * 1.15:
        target = DAILY_SALARY * 0.95 * scarcity * urgency
    elif highest_prev_bid >= DAILY_SALARY * 0.9:
        target = (highest_prev_bid * 0.85 + DAILY_SALARY * 0.25) * scarcity * urgency
    else:
        target = max(DAILY_SALARY * 0.5, highest_prev_bid * 0.6 + 10.0) * scarcity * urgency

    # Keep within budget and a reasonable cap (avoid overpaying early).
    cap = min(budget, DAILY_SALARY * 1.1)
    bid = max(0.0, min(cap, target))

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

    # Basic sanity
    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append(o)

    # If no one else is alive, conserve budget
    if not alive_opponents:
        return float(min(budget, DAILY_SALARY * 0.35))

    # Look only at yesterday's immediate behavior
    prev_bids = []
    for o in alive_opponents:
        prev = o.get('previous_trace', {}) or {}
        if prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Supply pressure: fewer days of survival if supply is near minimum
    # (We don't know exact HP dynamics; use supply to set a conservative baseline.)
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Baseline bid: mid strategy to secure enough water share without draining budget.
    # If supply is lower, bid slightly more.
    base = DAILY_SALARY * (0.48 + 0.18 * (1.0 - supply_ratio))

    # If opponents were bidding extremely high yesterday, they were likely under pressure.
    # Increase only if our HP is low.
    if highest_prev_bid >= DAILY_SALARY * 0.9:
        if hp <= 2.5 or no_water_days >= 2:
            bid = DAILY_SALARY * 0.75
        else:
            bid = base * 0.95
    elif highest_prev_bid >= DAILY_SALARY * 0.6:
        # Moderate pressure: small adjustment
        if hp <= 2.5:
            bid = DAILY_SALARY * 0.62
        else:
            bid = base
    else:
        # Low observed pressure: conserve
        if hp <= 2.5 or no_water_days >= 2:
            bid = DAILY_SALARY * 0.68
        else:
            bid = base * 0.88

    # Budget cap and safety
    bid = float(min(budget, bid))
    if bid < 0.0:
        bid = 0.0

    # Ensure we don't bid trivially when we must recover from no-water streak
    if no_water_days >= 3 and bid < DAILY_SALARY * 0.55:
        bid = float(min(budget, DAILY_SALARY * 0.7))

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

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for k, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # If no opponents alive, take what we can.
    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from each opponent's previous_trace.
    prev_bids = []
    prev_by_id = {}
    for opp_id, opp in opponents_status.items():
        if not opp.get('alive', False):
            continue
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                b_val = float(b)
            except Exception:
                continue
            prev_bids.append(b_val)
            prev_by_id[opp_id] = b_val

    # Baseline pressure estimate.
    if prev_bids:
        highest_prev = max(prev_bids)
        second_prev = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev
        # If Cindy-like behavior exists (very high bids), treat as strong competition.
        strong_competition = highest_prev >= 0.95 * 300.0 or highest_prev >= 0.9 * 195.0
    else:
        highest_prev = 0.0
        second_prev = 0.0
        strong_competition = False

    # Supply regime: higher supply means we can bid less and still likely secure water.
    # Convert supply to an integer bucket safely.
    # If supply is near max (25), competition can be relaxed; if near min (15), we must be more aggressive.
    supply_ratio = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    if supply_ratio < 0.0:
        supply_ratio = 0.0
    if supply_ratio > 1.0:
        supply_ratio = 1.0

    # Urgency based on hp and starvation days.
    urgency = 0.0
    if hp <= 2.0:
        urgency += 1.0
    if hp <= 4.0:
        urgency += 0.6
    if no_water_days >= 2:
        urgency += 0.7
    if no_water_days >= 4:
        urgency += 1.0

    # Decide target bid.
    # Strategy: if Cindy/others bid max yesterday, we slightly underbid/overbid depending on our urgency.
    # We do not know today's hidden bids, so we aim to be competitive but not waste budget.
    # Target around: (second_prev + small increment) when strong competition, else around (highest_prev * 0.75).
    if strong_competition:
        # If we are healthy, try to free budget: bid near second_prev.
        # If we are urgent, bid closer to highest_prev.
        if urgency >= 1.0:
            target = max(highest_prev * 0.92, second_prev + 5.0)
        else:
            target = min(highest_prev - 5.0, max(second_prev + 2.0, highest_prev * 0.78))
    else:
        # Moderate competition: bid to beat typical bids.
        base = highest_prev * (0.70 if urgency < 0.8 else 0.85)
        # Also account for supply: bid less when supply is high.
        supply_adjust = 1.0 - 0.25 * supply_ratio  # 1.0 at min supply, 0.75 at max supply
        target = base * supply_adjust + (5.0 if urgency >= 1.0 else 0.0)

    # Ensure we bid at least enough to matter but never exceed budget.
    # Use a floor tied to urgency.
    min_bid = 0.0
    if urgency >= 1.0:
        min_bid = DAILY_SALARY * 0.75
    elif urgency >= 0.6:
        min_bid = DAILY_SALARY * 0.55
    else:
        min_bid = DAILY_SALARY * 0.35

    # Cap target by budget and a reasonable fraction of DAILY_SALARY to avoid bankrupting.
    # (We do not know total rounds, but preserving budget is key.)
    cap = budget
    if cap <= 0.0:
        return 0.0

    # Slightly more aggressive late in episode (day index heuristic).
    # episode_days is 10; day_context day likely 0..9 or 1..10. We'll treat higher day as later.
    try:
        later = float(day) / 10.0
    except Exception:
        later = 0.5
    if later < 0.0:
        later = 0.0
    if later > 1.0:
        later = 1.0

    # Allow higher cap near the end.
    cap = min(cap, DAILY_SALARY * (0.95 if later >= 0.7 else 0.65))

    final_bid = float(target)
    if final_bid < min_bid:
        final_bid = min_bid
    if final_bid > cap:
        final_bid = cap

    # Never negative.
    if final_bid < 0.0:
        final_bid = 0.0

    return final_bid
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

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opps = [o for o in opponents_status.values() if o.get('alive', False)]

    # If no opponents alive, take what we need conservatively.
    if not alive_opps:
        # Bid enough to secure at least 1 unit of requirement if possible.
        # Since bids are abstract, use a low fraction of salary.
        return max(0.0, min(my_budget, DAILY_SALARY * 0.35))

    # Read yesterday bids from immediate previous_trace only.
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Estimate opponent pressure from yesterday.
    highest_prev = max(prev_bids) if prev_bids else 0.0
    second_highest = 0.0
    if prev_bids:
        sorted_b = sorted(prev_bids, reverse=True)
        if len(sorted_b) > 1:
            second_highest = sorted_b[1]

    # Determine risk level.
    # If we have been without water, or low HP, we must outbid.
    critical = (my_hp <= 2.5) or (my_no_water_days >= 2)

    # Supply factor: with higher supply, we can bid less.
    # Normalize between [MIN_SUPPLY, MAX_SUPPLY].
    if MAX_SUPPLY - MIN_SUPPLY > 0:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_norm = 0.5
    supply_norm = max(0.0, min(1.0, float(supply_norm)))

    # Base bid target anchored to observed Alex-like survival pressure.
    # Alex avg ~103; Cindy died with ~95 avg and higher max, suggesting bidding too high can burn budget.
    # We aim slightly under the typical high bidder unless critical.
    target = DAILY_SALARY * (0.55 + 0.15 * supply_norm)  # ~49.5..63

    # If yesterday had strong bids, adjust upward to just under the max pressure.
    if highest_prev > 0:
        # Keep within a band below highest_prev to avoid overpaying.
        # If critical, we may match/beat.
        if critical:
            target = max(target, highest_prev * 1.02)
        else:
            # Bid enough to beat second-highest but not necessarily the highest.
            if second_highest > 0:
                target = max(target, second_highest * 1.03)
            # Also cap just under the highest to avoid runaway.
            target = min(target, highest_prev * 0.97)

    # Additional day-based scaling: later days are less flexible.
    # episode_days is fixed at 10 in meta-round; use day fraction.
    episode_days = 10
    day_frac = float(day) / float(max(1, episode_days))
    if day_frac >= 0.8:
        target *= 1.12
    elif day_frac <= 0.2:
        target *= 0.95

    # Ensure affordability and minimum meaningful bid.
    # Budget constraint: never exceed my_budget.
    target = min(target, my_budget)

    # If target is too low relative to our requirement risk, bump.
    if not critical and my_hp <= 4.0:
        target = max(target, DAILY_SALARY * 0.75)
    if critical:
        target = max(target, DAILY_SALARY * 0.85)

    # Final clamp.
    if target < 0.0:
        target = 0.0
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

    # Identify alive opponents and read yesterday bids
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

    # If no info, play baseline conservative
    if not alive_opps or not yesterday_bids:
        base = DAILY_SALARY * 0.55
        return max(0.0, min(float(my_status['budget']), base))

    highest_prev_bid = max(yesterday_bids)
    avg_prev_bid = sum(yesterday_bids) / float(len(yesterday_bids))

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    # Determine how aggressive to be based on yesterday's bidding intensity
    # If someone was bidding near our daily salary, expect a scramble for water.
    scramble = highest_prev_bid >= DAILY_SALARY * 0.85

    # Supply pressure: higher supply reduces marginal value of extra bids.
    # Lower supply increases need to win water.
    supply_mid = (MIN_SUPPLY + MAX_SUPPLY) / 2.0
    low_supply = supply <= supply_mid

    # Compute target bid
    if scramble:
        # Price war likely; we bid enough to compete but not max out.
        if hp <= 2.0:
            target = DAILY_SALARY * 0.9
        elif low_supply:
            target = max(avg_prev_bid, DAILY_SALARY * 0.7)
        else:
            target = max(avg_prev_bid * 0.85, DAILY_SALARY * 0.6)
    else:
        # Not a scramble; bid to secure without overspending.
        if low_supply:
            target = max(avg_prev_bid * 0.8, DAILY_SALARY * 0.55)
        else:
            target = max(avg_prev_bid * 0.65, DAILY_SALARY * 0.45)

    # Budget safety cap: never bid above budget; also avoid extreme bids.
    # Use a soft cap relative to remaining budget.
    cap = budget
    if cap <= 0:
        return 0.0

    # If we are healthy, reduce bids slightly to conserve.
    if hp >= 7.0:
        target *= 0.9
    elif hp <= 3.0:
        target *= 1.05

    # Final bid
    bid = min(cap, target)
    if bid < 0.0:
        bid = 0.0
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

    supply = day_context['supply']
    day = day_context['day']

    # Alive opponents only
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive'):
            alive_opps.append(o)

    # If no opponents alive, bid to meet requirement safely
    if not alive_opps:
        target = DAILY_SALARY * 0.45
        return min(my_status['budget'], target)

    # Read yesterday bids to infer pressure level
    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        pbid = prev.get('bid', None)
        if pbid is not None:
            try:
                yesterday_bids.append(float(pbid))
            except Exception:
                pass

    # Pressure heuristic from yesterday
    highest_prev = max(yesterday_bids) if yesterday_bids else 0.0
    second_highest = 0.0
    if yesterday_bids:
        sorted_b = sorted(yesterday_bids)
        if len(sorted_b) >= 2:
            second_highest = sorted_b[-2]

    # Budget/hp urgency
    hp = my_status.get('hp', 0)
    budget = my_status.get('budget', 0.0)
    no_water_days = my_status.get('no_water_days', 0)

    # Supply scarcity: lower supply increases chance of losing water if we underbid
    # Normalize scarcity factor between 0 and 1
    if MAX_SUPPLY == MIN_SUPPLY:
        scarcity = 0.5
    else:
        scarcity = (float(MAX_SUPPLY) - float(supply)) / float(MAX_SUPPLY - MIN_SUPPLY)
        if scarcity < 0.0:
            scarcity = 0.0
        if scarcity > 1.0:
            scarcity = 1.0

    # If Cindy-style overspending likely occurred (very high highest_prev), avoid bidding to win by matching.
    # Instead, bid a fraction based on scarcity and our urgency.
    # Also, if our hp/no_water_days are critical, we must bid higher.
    critical = (hp <= 2) or (no_water_days >= 2)

    # Base bid: enough to compete when supply is low, but not always matching the top bidder.
    # Use highest_prev as a ceiling reference, but don't chase it fully.
    if highest_prev >= DAILY_SALARY * 1.4:
        # High pressure: likely someone (e.g., Cindy) is strong. Bid around the second-highest + small increment.
        # If we are critical, we may need to approach highest_prev fractionally.
        if critical:
            bid = 0.92 * highest_prev
        else:
            bid = 0.55 * highest_prev + 0.25 * second_highest
    else:
        # Moderate pressure: bid near the upper-middle.
        if critical:
            bid = DAILY_SALARY * (0.85 + 0.15 * scarcity)
        else:
            bid = DAILY_SALARY * (0.55 + 0.25 * scarcity)

    # Scarcity adjustment
    if not critical:
        bid = bid * (0.9 + 0.2 * scarcity)

    # Ensure we don't bid beyond budget
    if bid > budget:
        bid = budget

    # Safety minimum: if we have budget, keep a reasonable bid to avoid prolonged no-water days.
    # (If budget is very low, just spend what we have.)
    min_reasonable = DAILY_SALARY * 0.25
    if budget <= min_reasonable:
        return budget

    if bid < min_reasonable:
        bid = min_reasonable

    # Final clamp
    if bid > budget:
        bid = budget
    if bid < 0.0:
        bid = 0.0

    return bid
"""
