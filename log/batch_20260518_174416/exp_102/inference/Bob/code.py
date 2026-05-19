# ============================================================
# Experiment: exp_102
# Agent: Bob
# Source: exp_102
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
            alive_opponents.append((opp_id, opp))

    # If we have no budget, bid 0.
    if budget <= 0:
        return 0

    # Default bid targets based on our condition.
    # If low hp or already suffered no-water days, bid more aggressively.
    urgency = 0
    if hp <= 2:
        urgency += 2
    elif hp <= 4:
        urgency += 1
    if no_water_days >= 2:
        urgency += 2
    elif no_water_days >= 1:
        urgency += 1

    # Use yesterday traces only for immediate reaction: take max yesterday bid.
    yesterday_bids = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # Estimate a competitive target.
    # If opponents were bidding high yesterday, we slightly outbid to secure water.
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            target = DAILY_SALARY * (0.35 if hp > 3 else 0.95)
            # Slightly increase if we are already in trouble.
            target *= (1.0 + 0.15 * min(2, urgency))
        else:
            target = max(DAILY_SALARY * 0.5, highest_prev_bid + 1.5)
            target *= (1.0 + 0.1 * min(2, urgency))
    else:
        # No trace info: choose a stable strategy.
        # If supply is higher, bid a bit less; if lower, bid a bit more.
        supply_factor = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY + 1e-9)
        # supply_factor in [0,1] roughly: higher when supply is low.
        base = DAILY_SALARY * (0.55 + 0.25 * supply_factor)
        target = base * (1.0 + 0.12 * min(2, urgency))

    # Convert target into a bid that is likely to win but not exceed our budget.
    # Keep bid within [0, budget].
    bid = min(budget, max(0.0, target))

    # Small adjustment by day: later days are more critical if we still need water.
    # day is 0-index or 1-index unknown; keep mild.
    if int(day) >= 7:
        bid *= 1.05

    # Ensure bid is not absurdly high relative to supply: cap at budget and a fraction of supply.
    # (We don't know opponent utility; this is a safety cap.)
    max_reasonable = budget
    # If supply is low, allow higher bids; otherwise keep moderate.
    if supply <= float(WATER_REQ):
        max_reasonable = min(budget, DAILY_SALARY * 0.95)
    else:
        max_reasonable = min(budget, DAILY_SALARY * 0.75)

    bid = min(bid, max_reasonable)

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
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    # If no opponents, bid conservatively
    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday trace bids for immediate reaction
    prev_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    prev_bids.append(float(b))
                except Exception:
                    pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate how many water units are likely available relative to my requirement
    # (use only to tune aggressiveness, not to index arrays)
    supply_ratio = supply / float(WATER_REQ) if WATER_REQ > 0 else 1.0

    # Base bid target: aim to beat typical mid/high bids without exhausting budget
    # Observed: Cindy ~92.5, Eric ~73.6; use 0.75-0.95 of DAILY_SALARY depending on conditions.
    if my_hp <= 2.0 or my_no_water_days >= 2:
        # Critical survival pressure: bid near top of our comfort range
        target = DAILY_SALARY * 0.95
    elif supply_ratio >= 2.0:
        # Plenty of supply: don't overspend
        target = DAILY_SALARY * 0.65
    else:
        # Moderate supply: try to secure enough water against high bidders
        target = DAILY_SALARY * 0.78

    # If yesterday saw very high bids, slightly increase to avoid being outbid
    if highest_prev_bid >= DAILY_SALARY * 0.9:
        target = max(target, DAILY_SALARY * 0.9)
    elif highest_prev_bid >= DAILY_SALARY * 0.75:
        target = max(target, DAILY_SALARY * 0.82)

    # Ensure bid respects budget and keeps some buffer
    # If budget is low, scale down proportionally.
    if my_budget <= 0:
        return 0.0

    # Keep at least a small fraction for future days
    budget_cap = my_budget * 0.95
    bid = min(budget_cap, target)

    # Final clamp
    if bid < 0.0:
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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append(o)

    if not alive:
        return float(min(budget, DAILY_SALARY * 0.4))

    yesterday_bids = []
    for o in alive:
        prev = o.get('previous_trace', None) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how competitive the market is; Cindy's behavior implies others may chase.
    # If someone previously bid very high, we raise our bid to avoid being starved.
    pressure = 0.0
    if highest_prev_bid >= DAILY_SALARY * 1.2:
        pressure = 1.0
    elif highest_prev_bid >= DAILY_SALARY * 0.8:
        pressure = 0.6
    else:
        pressure = 0.3

    # Supply pressure: lower supply increases chance of losing water.
    supply_mid = (MIN_SUPPLY + MAX_SUPPLY) / 2.0
    supply_pressure = 0.0
    if supply <= supply_mid:
        supply_pressure = 0.6
    else:
        supply_pressure = 0.3

    # If I'm already low HP or have consecutive no-water days, bid more.
    urgency = 0.0
    if hp <= 2:
        urgency = 1.0
    elif hp <= 4:
        urgency = 0.7
    else:
        urgency = 0.4

    if no_water_days >= 2:
        urgency = min(1.0, urgency + 0.3)

    # Core bid target.
    # Aim to be competitive when pressure is high, but not max out unless critical.
    base = DAILY_SALARY * (0.45 + 0.25 * pressure + 0.15 * supply_pressure)
    if urgency >= 0.9:
        target = DAILY_SALARY * (0.85 + 0.1 * pressure)
    else:
        target = base + (highest_prev_bid * 0.05 if highest_prev_bid > 0 else 0.0)

    # Keep within reasonable bounds relative to supply.
    # If supply is very low, we increase slightly.
    if supply <= float(WATER_REQ):
        target *= 1.15

    # Convert to final bid bounded by budget.
    bid = min(budget, target)

    # Ensure non-negative.
    if bid < 0:
        bid = 0.0

    # If we have very low budget, still bid something to avoid being completely outcompeted.
    if budget > 0 and bid == 0.0:
        bid = min(budget, DAILY_SALARY * 0.2)

    return float(bid)
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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from immediate previous_trace only
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
    avg_prev_bid = (sum(yesterday_bids) / len(yesterday_bids)) if yesterday_bids else 0.0

    # Estimate how many full water units might be available
    # (supply is total pot; water requirement per player is WATER_REQ)
    # Use int indices safely by converting to ints where needed.
    supply_units = int(supply // float(WATER_REQ))
    if supply_units < 1:
        supply_units = 1

    # Core strategy: avoid matching the top bidders unless we're in danger.
    # Typical observed meta: many bids cluster around 120-150 with supply 15-25.
    # We'll target slightly below the average, but above a baseline.
    baseline = DAILY_SALARY * 0.55

    # If opponents were bidding extremely high yesterday, increase to avoid being outbid.
    if highest_prev_bid >= DAILY_SALARY * 0.85 or avg_prev_bid >= DAILY_SALARY * 0.75:
        danger_factor = 1.0
        if my_hp <= 2.5:
            danger_factor = 1.25
        elif my_hp <= 4.0:
            danger_factor = 1.12
        else:
            danger_factor = 1.05
        target = max(baseline, avg_prev_bid * 0.92) * danger_factor
    else:
        # If yesterday wasn't a bidding frenzy, bid around baseline but scale with our HP.
        if my_hp <= 2.5 or my_no_water_days >= 2:
            target = max(baseline * 1.2, avg_prev_bid * 0.9)
        elif my_hp <= 4.0:
            target = max(baseline * 1.05, avg_prev_bid * 0.85)
        else:
            # Healthy: bid just enough to compete.
            # Also slightly adjust with supply units (more supply => can bid less).
            supply_adjust = 1.0
            if supply_units >= 2:
                supply_adjust = 0.95
            elif supply_units <= 1:
                supply_adjust = 1.05
            target = baseline * supply_adjust

    # Ensure we don't exceed budget and keep within plausible range.
    # If budget is low, spend most of it when HP is critical.
    if my_budget <= 0:
        return 0.0

    if my_hp <= 1.5:
        bid = my_budget * 0.95
    elif my_hp <= 3.0:
        bid = min(my_budget, target * 1.05)
    else:
        bid = min(my_budget, target)

    # Hard cap to avoid irrational overspending beyond a day's salary scale.
    bid_cap = DAILY_SALARY * 1.2
    bid = min(bid, bid_cap)

    # Final safety
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    # Alive opponents only
    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive.append(opp)

    # If no opponents, just bid enough to secure water
    if not alive:
        return max(0.0, min(my_status.get('budget', 0.0), DAILY_SALARY * 0.4))

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))

    # Extract yesterday bids from immediate previous_trace
    prev_bids = []
    prev_max = 0.0
    for opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                fb = float(b)
                prev_bids.append(fb)
                if fb > prev_max:
                    prev_max = fb
            except Exception:
                pass

    # If we have a strong signal that others are bidding high, outbid slightly.
    # Cindy/Alex survived with ~118-122 and max around mid-140s.
    # David/Eric died with ~28-32, so low bids are losing.
    target = DAILY_SALARY * 0.95

    if prev_bids:
        # Use the observed max as a ceiling signal; bid just above, but not too high.
        # Add small premium to beat the likely top bidder.
        premium = 6.0
        target = max(target, prev_max + premium)

    # Adjust for supply: higher supply means we can bid slightly less.
    # Supply is between 15 and 25.
    if supply <= MIN_SUPPLY:
        supply_factor = 1.05
    elif supply >= MAX_SUPPLY:
        supply_factor = 0.95
    else:
        # linear between
        supply_factor = 1.05 - (supply - MIN_SUPPLY) * (0.10 / (MAX_SUPPLY - MIN_SUPPLY))

    # If my HP is low, increase urgency.
    if my_hp <= 2.0:
        hp_factor = 1.15
    elif my_hp <= 4.0:
        hp_factor = 1.08
    else:
        hp_factor = 1.00

    bid = target * supply_factor * hp_factor

    # Never bid above budget
    bid = min(bid, my_budget)

    # Also cap to a reasonable fraction of budget to avoid overspending if budget is huge.
    # (But still allow high bids when needed.)
    hard_cap = max(DAILY_SALARY * 1.8, my_budget)
    bid = min(bid, hard_cap)

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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    # If we are in immediate danger, secure water aggressively.
    if my_hp <= 2 or my_no_water_days >= 2:
        target = DAILY_SALARY * 0.9
        return max(0.0, min(my_budget, target))

    alive_opps = [o for o in opponents_status.values() if o.get('alive', True)]
    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday bids (only immediate reaction via previous_trace).
    prev_bids = []
    prev_budget_after = []
    prev_hp_after = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass
        if prev.get('budget_after', None) is not None:
            try:
                prev_budget_after.append(float(prev.get('budget_after')))
            except Exception:
                pass
        if prev.get('hp_after', None) is not None:
            try:
                prev_hp_after.append(float(prev.get('hp_after')))
            except Exception:
                pass

    # Estimate how hard others pushed yesterday.
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # If yesterday saw very high bids, avoid overbidding; bid just enough to beat typical mid bids.
    # If yesterday saw depletion (many near-zero budgets), we can safely undercut.
    depletion_count = 0
    for o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        ba = prev.get('budget_after', None)
        if ba is not None:
            try:
                if float(ba) <= 0.0:
                    depletion_count += 1
            except Exception:
                pass

    # Supply pressure: higher supply means cheaper to win; lower supply means we must bid more.
    # Normalize supply within [MIN_SUPPLY, MAX_SUPPLY].
    if MAX_SUPPLY == MIN_SUPPLY:
        supply_norm = 0.5
    else:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
        if supply_norm < 0.0:
            supply_norm = 0.0
        if supply_norm > 1.0:
            supply_norm = 1.0

    # Baseline bid: moderate fraction of salary.
    baseline = DAILY_SALARY * (0.48 - 0.12 * supply_norm)  # slightly higher when supply is lower

    # If others bid extremely high yesterday, don't match; bid below the top but above baseline.
    if highest_prev_bid >= DAILY_SALARY * 1.25:
        # Underbid the arms race.
        bid = min(baseline + 10.0, DAILY_SALARY * 0.65)
    else:
        bid = baseline

    # If multiple opponents depleted funds yesterday, we can undercut further.
    if depletion_count >= 1:
        bid *= 0.9

    # Ensure we don't bid more than we can pay.
    bid = max(0.0, min(my_budget, bid))

    # Final safety: if we still have low hp, add a small increment to avoid losing water.
    if my_hp <= 4.0:
        bid = max(bid, min(my_budget, DAILY_SALARY * 0.7))

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

    supply = float(day_context['supply'])
    day = day_context['day']

    # Identify alive opponents
    alive_ops = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_ops.append((oid, o))

    # If no opponents alive, bid conservatively
    if not alive_ops:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    my_hp = int(my_status['hp'])
    my_budget = float(my_status['budget'])

    # Read yesterday bids from each opponent's previous_trace
    prev_bids = []
    for oid, o in alive_ops:
        prev = o.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                prev_bids.append(float(bid))
            except Exception:
                pass

    # Estimate likely clearing price from yesterday
    if prev_bids:
        sorted_bids = sorted(prev_bids)
        # Top pressure is likely around max; second-highest helps shade
        top = sorted_bids[-1]
        second = sorted_bids[-2] if len(sorted_bids) >= 2 else sorted_bids[-1]

        # If someone was extremely aggressive, shade just below them.
        # Cindy averaged ~138 yesterday; Alex ~105; David low ~50.
        target = second + 0.75
        if top >= DAILY_SALARY * 1.35:
            # Cindy-like pressure; bid near (but under) top
            target = min(top - 2.0, second + 3.0)
        elif top >= DAILY_SALARY * 0.95:
            # Alex-like pressure
            target = min(top - 1.0, second + 2.0)
        else:
            # Low-pressure field
            target = max(DAILY_SALARY * 0.45, second + 1.0)
    else:
        target = DAILY_SALARY * 0.55

    # Adjust for my current hp and budget
    # Healthy (hp high): shade more; low hp: bid harder.
    if my_hp >= 8:
        target *= 0.95
    elif my_hp >= 5:
        target *= 1.00
    elif my_hp >= 3:
        target *= 1.10
    else:
        target *= 1.25

    # Supply-based cap: if supply is low, we should be more competitive.
    # supply range 15-25; higher supply means easier to win.
    if supply <= MIN_SUPPLY + 0.5:
        target *= 1.10
    elif supply >= MAX_SUPPLY - 0.5:
        target *= 0.90

    # Ensure non-negative and within budget
    bid = max(0.0, min(my_budget, float(target)))

    # Avoid bidding too tiny when we likely need water (water requirement 9)
    # Use a floor derived from daily salary to stay competitive.
    min_competitive = DAILY_SALARY * 0.35
    if my_budget >= min_competitive and bid < min_competitive:
        bid = min_competitive

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

    # Identify alive opponents and collect yesterday bids
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)

    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    yesterday_bids = []
    yesterday_hp_after = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                yesterday_bids.append(float(bid))
            except Exception:
                pass
        hp_after = prev.get('hp_after', None)
        if hp_after is not None:
            try:
                yesterday_hp_after.append(float(hp_after))
            except Exception:
                pass

    # If someone previously bid extremely high, assume scarcity and bid up to compete.
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Base aggressiveness tuned for medium scenario: moderate bid unless pressure is high.
    # Use supply to scale: higher supply reduces need to overbid.
    supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    supply_factor = max(0.0, min(1.0, supply_factor))

    # Estimate how many water units exist relative to our requirement.
    # This is a heuristic to decide how competitive bidding likely is.
    units = supply / float(WATER_REQ)

    # If yesterday shows high bids, compete; otherwise bid just enough.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Cindy-like behavior: others may be protecting survival.
        # If our hp is low, go higher; else conserve budget.
        if float(my_status['hp']) <= 2:
            target = DAILY_SALARY * 0.95
        else:
            target = DAILY_SALARY * (0.55 + 0.35 * (1.0 - supply_factor))
    elif highest_prev_bid >= DAILY_SALARY * 0.45:
        # Some opponents were active but not extreme.
        target = max(DAILY_SALARY * 0.45, highest_prev_bid * 0.75)
        target = target * (0.85 + 0.3 * (1.0 - supply_factor))
    else:
        # Low bids yesterday: likely underbidding; we can take advantage with moderate bid.
        target = DAILY_SALARY * (0.40 + 0.25 * (1.0 - supply_factor))
        # If supply is tight (units < 2), increase.
        if units < 2.0:
            target = target * 1.15

    # Ensure we don't bid beyond our budget.
    budget = float(my_status['budget'])
    if budget <= 0.0:
        return 0.0

    # If we are close to running out of water days, increase bid.
    no_water_days = int(my_status.get('no_water_days', 0))
    hp = float(my_status['hp'])
    if no_water_days >= 2 or hp <= 2:
        target = max(target, DAILY_SALARY * 0.75)

    # Cap bid to budget and keep within a sensible range.
    bid = float(min(budget, max(0.0, target)))
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Identify alive opponents
    alive_opponents = []
    for oid, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((oid, opp))

    # If no opponents alive, bid to survive comfortably
    if not alive_opponents:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from immediate previous_trace
    yesterday_bids = []
    for oid, opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Baseline: target a mid allocation pressure
    # If supply is high, we can bid less; if low, bid more.
    supply_ratio = 0.0
    try:
        supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    except Exception:
        supply_ratio = 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Conservative base bid to avoid overpaying
    base_bid = DAILY_SALARY * (0.65 - 0.25 * supply_ratio)

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # If I'm in danger, bid aggressively regardless
    if my_hp <= 2 or no_water_days >= 2:
        bid = DAILY_SALARY * 0.95
        return float(min(my_budget, bid))

    # React to yesterday's highest bid (likely indicates who is fighting for water)
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # Cindy-like consistent bidder likely has relatively high yesterday bids and survived.
        # If someone bid very high yesterday, slightly increase to compete.
        if highest_prev_bid >= DAILY_SALARY * 1.6:
            bid = base_bid + DAILY_SALARY * 0.25
        elif highest_prev_bid >= DAILY_SALARY * 1.2:
            bid = base_bid + DAILY_SALARY * 0.12
        else:
            bid = base_bid
    else:
        bid = base_bid

    # Ensure bid is at least enough to have a chance but not too wasteful
    bid = max(DAILY_SALARY * 0.45, bid)
    bid = min(bid, DAILY_SALARY * 0.9)

    return float(min(my_budget, bid))
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
    day = int(day_context.get('day', 0))

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from traces for immediate reaction
    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        if prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Estimate how aggressive others were yesterday
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_highest_prev_bid = 0.0
    if len(yesterday_bids) >= 2:
        sorted_b = sorted(yesterday_bids, reverse=True)
        second_highest_prev_bid = sorted_b[1]

    # Determine supply pressure: when supply is low, need to secure water more reliably
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))
    low_supply = supply_ratio < 0.5

    # If I'm close to death, bid to survive regardless of cost
    critical = (my_hp <= 2) or (my_no_water_days >= 2)

    # If others were bidding very high yesterday, we should at least approach that level.
    # Use a capped strategy to avoid burning budget.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Survivors likely spending heavily; match but slightly undercut.
        base = min(my_budget, max(DAILY_SALARY * 0.75, second_highest_prev_bid + 2.0))
        if critical:
            base = min(my_budget, max(base, DAILY_SALARY * 0.95))
        elif low_supply:
            base = min(my_budget, max(base, DAILY_SALARY * 0.85))
        return max(0.0, base)

    # Otherwise, bid moderately: enough to beat low bidders (Alex/Eric style), but not overpay.
    # Target a level that is above typical low bids; scale with supply pressure and my hp.
    if critical:
        target = DAILY_SALARY * (0.85 if low_supply else 0.95)
    else:
        # If hp is healthy, be more conservative.
        if my_hp >= 6:
            target = DAILY_SALARY * (0.45 if not low_supply else 0.65)
        else:
            target = DAILY_SALARY * (0.60 if not low_supply else 0.78)

    # If yesterday had some mid/high bids, nudge upward slightly.
    if highest_prev_bid > 0:
        target = max(target, min(my_budget, highest_prev_bid * 0.75))

    bid = min(my_budget, target)

    # Ensure non-negative and at least a minimal bid if budget allows.
    if bid < 0.0:
        bid = 0.0
    return bid
"""
