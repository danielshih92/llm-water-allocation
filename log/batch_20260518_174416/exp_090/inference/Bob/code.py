# ============================================================
# Experiment: exp_090
# Agent: Bob
# Source: exp_090
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
    day = day_context['day']

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    # Budget-based caps
    budget = float(my_status['budget'])
    hp = int(my_status['hp'])
    no_water_days = int(my_status['no_water_days'])

    if not alive_opps:
        return float(min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids
    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Determine supply pressure: how many full allocations are possible
    # (use int indices safely; no list indexing needed)
    supply_units = int(supply // float(WATER_REQ))
    if supply_units < 1:
        supply_units = 1

    # Base bid targets
    # If we are in danger (low hp or many no-water days), bid more aggressively.
    danger = (hp <= 2) or (no_water_days >= 2)

    # Opponent pressure from yesterday
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    # Thresholds near salary-ish bids
    high_pressure = highest_prev_bid >= DAILY_SALARY * 0.85
    low_pressure = highest_prev_bid <= DAILY_SALARY * 0.45

    # Strategy:
    # - If opponents were bidding extremely high yesterday, shade down slightly (avoid bidding wars),
    #   but still ensure we can cover our requirement if possible.
    # - If opponents were bidding low, bid enough to secure water early.
    if danger:
        if high_pressure:
            bid = DAILY_SALARY * 0.65
        elif low_pressure:
            bid = DAILY_SALARY * 0.85
        else:
            bid = DAILY_SALARY * 0.75
    else:
        if high_pressure:
            # Shade: bid less than their peak but not too low.
            bid = min(DAILY_SALARY * 0.60, highest_prev_bid - 2.0)
        elif low_pressure:
            # Secure position: bid moderately above average.
            bid = max(DAILY_SALARY * 0.50, avg_prev_bid + 3.0)
        else:
            # Middle: bid near average with slight premium.
            bid = max(DAILY_SALARY * 0.52, avg_prev_bid + 1.5)

    # Adjust for current supply: lower supply -> bid more
    # supply_units ranges roughly 1..2 for given min/max.
    if supply_units <= 1:
        bid *= 1.10
    else:
        bid *= 0.98

    # Clamp to budget and reasonable bounds
    bid = float(bid)
    if bid < 0.0:
        bid = 0.0
    if bid > budget:
        bid = budget

    # Ensure we don't bid trivially low when we need water
    # (If we have no-water days, we should bid at least a fraction of salary.)
    if no_water_days >= 1 and bid < DAILY_SALARY * 0.35:
        bid = min(budget, DAILY_SALARY * 0.35)

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

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append(o)

    # If no one is alive, conserve.
    if not alive_opponents:
        bid = DAILY_SALARY * 0.4
        return max(0.0, min(my_budget, bid))

    # Read yesterday bids from previous_trace for immediate reaction.
    prev_bids = []
    for o in alive_opponents:
        prev = o.get('previous_trace', {}) or {}
        if prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate how competitive today is: higher supply tends to reduce scarcity,
    # but the game seems to reward aggressive bidding (Cindy/Eric).
    # Target a bid slightly under the highest observed aggressive tier.
    # Also adapt to our health.
    if my_hp <= 2.0 or my_no_water_days >= 2:
        # Need water now.
        target = min(my_budget, DAILY_SALARY * 0.95)
        # If others were bidding very high, stay near that.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            target = min(my_budget, max(target, highest_prev_bid * 0.9))
        return max(0.0, float(target))

    # If others were bidding very high yesterday, we should match the tier to avoid being outbid.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Slightly under to reduce burn while still likely winning.
        target = highest_prev_bid * 0.85
        # Adjust for supply: when supply is higher, we can bid a bit less.
        if supply >= 21.0:
            target *= 0.9
        else:
            target *= 1.0
    else:
        # Others were not extremely aggressive; bid moderate.
        target = DAILY_SALARY * 0.6
        if supply <= 18.0:
            target = DAILY_SALARY * 0.7

    # Safety cap: don't bid above what we can afford.
    target = min(my_budget, target)

    # Ensure non-negative.
    if target < 0.0:
        target = 0.0

    # Also avoid overbidding when we have plenty of HP.
    if my_hp >= 8.0 and my_no_water_days == 0:
        target = min(target, DAILY_SALARY * 0.7)

    return float(target)
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

    supply = float(day_context['supply'])
    day = day_context['day']

    # Alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # Budget safety
    budget = float(my_status['budget'])
    hp = float(my_status['hp'])
    no_water_days = int(my_status['no_water_days'])

    # If we cannot afford much, still try to avoid immediate death when already in danger
    def clamp_bid(x):
        x = float(x)
        if x < 0.0:
            x = 0.0
        if budget <= 0.0:
            return 0.0
        if x > budget:
            return budget
        return x

    # Estimate how many units of water the market likely awards if we win.
    # In this game, higher bid increases chance of getting enough water; we use supply-to-need ratio.
    # If supply is low (15), we likely need near full requirement to survive; if high (25), a smaller bid may still help.
    supply_ratio = supply / float(WATER_REQ)

    # Read yesterday bids from traces to infer opponent aggressiveness.
    yesterday_bids = []
    prev_death_count = 0
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass
        # If opponent died yesterday, that suggests they were underbidding.
        # But we only see alive opponents now; still, their hp/budget may reflect yesterday's outcome.
        if o.get('hp', 0) is not None and float(o.get('hp', 0)) < 0:
            prev_death_count += 1

    # If no trace info, use a conservative baseline.
    if not yesterday_bids:
        base = DAILY_SALARY * (0.75 if no_water_days >= 2 or hp <= 2 else 0.55)
        # Adjust with supply
        if supply_ratio >= 2.5:
            base *= 0.85
        return clamp_bid(base)

    highest_prev_bid = max(yesterday_bids)
    lowest_prev_bid = min(yesterday_bids)

    # Strategy:
    # - Cindy-like behavior: high bids; if highest_prev_bid is high, we must decide whether to contest.
    # - Alex/David-like behavior: low bids; if highest_prev_bid is low (~<=40), others likely underbid and we can outbid moderately.
    # - If we are in danger (low hp or multiple no-water days), bid to secure water.

    # Danger multiplier
    danger = 0.0
    if hp <= 2:
        danger += 1.0
    if no_water_days >= 2:
        danger += 0.7
    if hp <= 1:
        danger += 0.5

    # Determine target bid level relative to yesterday's highest.
    # If others were low, bid slightly above their typical level.
    if highest_prev_bid <= 45.0:
        # Their death spiral suggests we can win with a moderate bid.
        target = highest_prev_bid + 25.0
        # Ensure enough when supply is low.
        if supply <= float(MIN_SUPPLY):
            target += 15.0
        # If we're very safe, reduce a bit.
        if danger <= 0.2 and hp >= 6:
            target *= 0.85
    else:
        # If someone was bidding very high, we may not match; instead bid around a fraction of their level.
        # For survival, contest if we're in danger; otherwise conserve.
        contest_factor = 0.45 + 0.25 * min(1.0, danger)
        target = highest_prev_bid * contest_factor
        # If supply is low, increase.
        if supply <= float(MIN_SUPPLY):
            target *= 1.15

    # Convert target to a budget-aware bid with daily salary anchor.
    # Keep within [0, budget] and also avoid overspending near end of episode.
    # Episode length 10 days; later days require more.
    endgame = 0.0
    if day >= 8:
        endgame = 0.25
    elif day >= 6:
        endgame = 0.15

    # Blend with salary-based bid
    salary_bid = DAILY_SALARY * (0.65 + 0.25 * min(1.0, danger) + endgame)

    # If supply is high, we can slightly reduce.
    if supply_ratio >= 2.0:
        salary_bid *= 0.9

    final_bid = 0.6 * float(target) + 0.4 * float(salary_bid)

    # Hard cap to avoid wasting money if already safe
    if hp >= 7 and no_water_days <= 0:
        final_bid *= 0.75

    return clamp_bid(final_bid)
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

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((opp_id, o))

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Reaction to yesterday bids (immediate only)
    prev_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate how tight the market is: supply relative to our need.
    # If supply is low, competition likely higher.
    tightness = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        tightness = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)
    tightness = max(0.0, min(1.0, tightness))

    # Base bid: we aim to secure water without chasing the very highest bids.
    # If others were bidding very high yesterday, we bid around a fraction of DAILY_SALARY plus a small bump.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # High pressure: ensure we get water if our hp is not critical.
        if hp > 3.0:
            target = DAILY_SALARY * (0.30 + 0.25 * tightness) + 0.15 * highest_prev_bid
        else:
            target = DAILY_SALARY * (0.75 + 0.15 * tightness) + 0.10 * highest_prev_bid
    else:
        # Moderate pressure: bid enough to be competitive but not maximal.
        target = max(DAILY_SALARY * (0.45 + 0.20 * tightness), highest_prev_bid * 0.60 + 5.0)

    # If we've already gone without water, escalate quickly.
    if no_water_days >= 1:
        target *= 1.25
    if no_water_days >= 2:
        target *= 1.45

    # If we're in danger, bid more aggressively.
    if hp <= 2.0:
        target = max(target, DAILY_SALARY * (0.85 + 0.1 * tightness))

    # Budget and safety bounds.
    target = max(0.0, target)
    # Ensure we don't bid more than we can afford.
    if budget <= 0.0:
        return 0.0
    if target > budget:
        target = budget

    # Never bid above a reasonable cap relative to supply competition.
    # (Helps avoid getting into bidding wars.)
    cap = DAILY_SALARY * (1.1 + 0.3 * tightness)
    if target > cap:
        target = cap

    return float(target)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    max_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Base bid: aim to be competitive but not reckless
    # If supply is tighter (closer to 15), bid a bit higher.
    supply_factor = (25.0 - supply) / 10.0  # 0 at 25, 1 at 15
    supply_factor = max(0.0, min(1.0, supply_factor))

    # If yesterday's max bid was very high, others likely bid aggressively for survival.
    pressure = 0.0
    if max_prev_bid >= DAILY_SALARY * 1.7:
        pressure = 1.0
    elif max_prev_bid >= DAILY_SALARY * 1.2:
        pressure = 0.6
    elif max_prev_bid >= DAILY_SALARY * 0.8:
        pressure = 0.3

    # HP-based urgency
    if hp <= 1:
        hp_urgency = 1.0
    elif hp <= 3:
        hp_urgency = 0.8
    elif hp <= 5:
        hp_urgency = 0.5
    else:
        hp_urgency = 0.25

    # Construct target bid
    target = DAILY_SALARY * (0.45 + 0.25 * supply_factor + 0.25 * pressure + 0.25 * hp_urgency)

    # If we are extremely low on budget, scale down
    if budget < DAILY_SALARY * 0.6:
        target = min(target, budget * 0.9)

    # Ensure we don't overshoot budget
    bid = max(0.0, min(budget, target))

    # Small deterministic tie-breaker: alternate slightly by day parity
    if int(day) % 2 == 0:
        bid = bid * 1.02
    else:
        bid = bid * 0.98

    bid = max(0.0, min(budget, bid))
    return float(bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Determine how many water units are effectively available this day
    # (We only need 1 unit of WATER_REQ; higher supply just affects competition.)
    effective_units = int(max(0, supply // float(WATER_REQ)))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        # No competition: spend to secure survival quickly
        if hp <= 2 or no_water_days >= 1:
            return min(budget, DAILY_SALARY * 0.9)
        return min(budget, DAILY_SALARY * 0.55)

    # Read yesterday's bids from previous_trace for immediate reaction
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # If someone was bidding extremely high yesterday, they likely expect to win water again.
    # We bid just below that pressure to reduce cost while still outbidding typical mid bids.
    # Thresholds tuned to observed meta-round bids (~185-243).
    if highest_prev_bid >= 235:
        target = DAILY_SALARY * 0.75  # 67.5
        # If we are in danger, increase aggressiveness.
        if hp <= 2 or no_water_days >= 2:
            target = DAILY_SALARY * 0.95
        elif hp <= 4 or no_water_days >= 1:
            target = DAILY_SALARY * 0.85
        # Also ensure we are not trivially low when supply is tight.
        if effective_units <= 1:
            target = max(target, DAILY_SALARY * 0.65)
    elif highest_prev_bid >= 190:
        target = DAILY_SALARY * 0.65
        if hp <= 2 or no_water_days >= 2:
            target = DAILY_SALARY * 0.9
        elif hp <= 4 or no_water_days >= 1:
            target = DAILY_SALARY * 0.8
        if effective_units <= 1:
            target = max(target, DAILY_SALARY * 0.6)
    else:
        # Lower prior pressure: bid moderately to conserve budget.
        target = DAILY_SALARY * 0.55
        if hp <= 2 or no_water_days >= 2:
            target = DAILY_SALARY * 0.85
        elif hp <= 4 or no_water_days >= 1:
            target = DAILY_SALARY * 0.7

    # Convert target into a feasible bid given our budget.
    bid = min(budget, target)

    # If we still have budget and are very low HP, ensure we don't bid too little.
    if (hp <= 2 or no_water_days >= 2) and bid < DAILY_SALARY * 0.6:
        bid = min(budget, DAILY_SALARY * 0.85)

    # Final clamp: bid must be non-negative.
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

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    # Alive opponents only
    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive.append((opp_id, opp))

    if not alive:
        return float(min(my_status.get('budget', 0.0), DAILY_SALARY * 0.4))

    # Read yesterday bids to infer who is pressuring
    prev_bids = []
    for _, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            prev_bids.append(float(b))

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))

    # Pressure signals
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    # Identify likely strongest competitor from yesterday (max bid)
    # Use trace to approximate their urgency: if they bid high and survived, they likely have budget.
    # We'll target beating the max bidder with a slight premium.
    target_premium = 2.0

    # Supply-based aggressiveness: with more supply, we can lower bid since more water exists.
    # Convert supply to a rough multiplier in [0.8, 1.15]
    if supply <= MIN_SUPPLY:
        supply_mult = 1.15
    elif supply >= MAX_SUPPLY:
        supply_mult = 0.8
    else:
        # Linear interpolation
        supply_mult = 1.15 - (supply - MIN_SUPPLY) * (1.15 - 0.8) / (MAX_SUPPLY - MIN_SUPPLY)

    # Core strategy
    # If someone bid extremely high yesterday, we must match/beat to avoid water starvation.
    if highest_prev_bid >= DAILY_SALARY * 0.9:
        base = highest_prev_bid + target_premium
    elif highest_prev_bid >= DAILY_SALARY * 0.6:
        # Mid-high pressure: bid around avg or slightly above
        base = max(avg_prev_bid + 1.5, highest_prev_bid * 0.95)
    else:
        # Low pressure: bid enough to secure water but preserve budget
        base = avg_prev_bid * 0.65 if avg_prev_bid > 0 else DAILY_SALARY * 0.45

    # Urgency adjustment based on my hp
    if my_hp <= 2.0:
        base *= 1.25
    elif my_hp <= 4.0:
        base *= 1.12
    else:
        base *= 0.98

    # Apply supply multiplier
    bid = base * supply_mult

    # Budget safety: never exceed budget
    # Also cap to avoid runaway spending
    cap = my_budget
    if my_budget <= 0:
        return 0.0

    # Soft cap: don't exceed 1.1*DAILY_SALARY unless forced by extreme pressure
    if highest_prev_bid < DAILY_SALARY * 0.9:
        cap = min(cap, DAILY_SALARY * 1.1)

    bid = min(bid, cap)

    # Ensure non-negative
    if bid < 0:
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context['supply'])
    day = day_context['day']

    # Identify alive opponents
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    # If no one is alive, bid minimally to conserve budget
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Use only yesterday's immediate behavior
    prev_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate competitive pressure from highest previous bid
    # If someone was willing to spend near salary, they likely try to secure water strongly.
    pressure_high = highest_prev_bid >= DAILY_SALARY * 0.85

    # Supply-based urgency: with lower supply, winning is more valuable; but avoid overpaying.
    # Normalize supply between [15,25]
    if MAX_SUPPLY == MIN_SUPPLY:
        supply_norm = 0.5
    else:
        supply_norm = (supply - float(MIN_SUPPLY)) / float(MAX_SUPPLY - MIN_SUPPLY)
    supply_norm = max(0.0, min(1.0, supply_norm))

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # If I'm in danger (low hp or accumulating no-water days), bid more.
    danger = (hp <= 2.5) or (no_water_days >= 2)

    # Base bid: aim to be competitive but not maximal.
    # Target is around a fraction of salary; adjust by supply and danger.
    if danger:
        base = DAILY_SALARY * (0.75 + 0.15 * (1.0 - supply_norm))
    else:
        base = DAILY_SALARY * (0.45 + 0.20 * (1.0 - supply_norm))

    # If yesterday's highest bid was high, we should slightly undercut rather than match.
    # Since bids are simultaneous, undercutting can still win if others overbid.
    if pressure_high:
        # Undercut by a margin; but ensure we don't go too low.
        target = max(DAILY_SALARY * 0.55, highest_prev_bid * 0.92)
    else:
        # If pressure wasn't extreme, bid closer to base.
        target = base

    # Final cap by budget; also avoid bidding more than needed for a single day.
    bid = min(budget, target)

    # Ensure bid is non-negative and not trivially zero.
    if bid < 0.0:
        bid = 0.0

    # If budget is extremely low, bid whatever possible.
    if budget <= 1.0:
        return float(budget)

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

    # Basic safety
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        # If alone, bid conservatively
        target = DAILY_SALARY * 0.35
        return max(0.0, min(budget, target))

    # Read yesterday bids from previous_trace for immediate reaction
    prev_bids = []
    prev_hp_after = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            prev_bids.append(float(b))
        prev_hp_after.append(int(prev.get('hp_after', opp.get('hp', 0))))

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    # Estimate how many water units likely exist relative to requirement
    # (supply is in [15,25], so units is either 1 or 2)
    water_units = int(supply / float(WATER_REQ))
    if water_units < 1:
        water_units = 1
    if water_units > 2:
        water_units = 2

    # If my HP is low, I must bid aggressively but still avoid Cindy-level overpaying.
    if hp <= 2 or no_water_days >= 2:
        # react to pressure: if someone already overpaid yesterday, don't match fully
        if highest_prev_bid >= DAILY_SALARY * 1.45:
            target = DAILY_SALARY * 0.95
        else:
            target = DAILY_SALARY * 1.15
        return max(0.0, min(budget, target))

    # If yesterday's highest bid was very high, it indicates a bidding war; bid just enough.
    if highest_prev_bid >= DAILY_SALARY * 1.55:
        # Cindy-like behavior; undercut and rely on them overspending
        target = max(DAILY_SALARY * 0.55, avg_prev_bid * 0.75)
    elif highest_prev_bid >= DAILY_SALARY * 1.15:
        # moderate pressure
        target = max(DAILY_SALARY * 0.6, avg_prev_bid * 0.8)
    else:
        # low pressure; bid for value
        target = DAILY_SALARY * 0.5

    # Adjust with supply: with more units (2), we can bid slightly less.
    if water_units >= 2:
        target *= 0.9

    # Budget cap
    if budget <= 0.0:
        return 0.0

    # Final clamp
    target = float(target)
    if target > budget:
        target = budget
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

    supply = float(day_context['supply'])
    day = day_context['day']

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    # Baseline safety bids
    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Read yesterday bids to infer pressure
    yesterday_bids = []
    for opp_id, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict) and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    highest_prev = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev = 0.0
    if len(yesterday_bids) >= 2:
        s = sorted(yesterday_bids, reverse=True)
        second_prev = s[1]

    # Estimate how many winners might be needed; higher supply reduces urgency.
    # Supply is the total water available; each winner gets WATER_REQ.
    # Winners count approx supply/WATER_REQ.
    winners_est = int(supply / float(WATER_REQ))
    if winners_est < 1:
        winners_est = 1

    # Decide aggression based on our HP and observed opponent overbidding.
    # If opponents were bidding extremely high yesterday, we counter with a near-top bid.
    # If supply is higher, we can undercut slightly.

    # Emergency if we're close to death.
    if my_hp <= 2 or no_water_days >= 2:
        target = max(DAILY_SALARY * 0.85, highest_prev * 0.98)
    else:
        # Normal mode
        # If opponents previously bid very high, try to be just above the second-highest
        # to secure a share without matching the highest.
        if highest_prev >= DAILY_SALARY * 1.2:
            # Underbid slightly depending on supply (more supply => less need to match)
            undercut = 0.97 if supply <= 18.0 else 0.94
            target = second_prev * undercut if second_prev > 0 else highest_prev * 0.96
            # Ensure we still have enough to beat likely clearing price
            target = max(target, DAILY_SALARY * 0.55)
        else:
            # Lower opponent pressure: bid moderate, scaled by supply
            # Lower supply => higher bid
            if supply <= 17.0:
                target = DAILY_SALARY * 0.65
            elif supply <= 20.0:
                target = DAILY_SALARY * 0.55
            else:
                target = DAILY_SALARY * 0.45

    # Convert target to feasible bid within budget.
    # Also cap to avoid overspending; survival is priority but avoid Alex-like death spiral.
    # Max spend per day: 0.95 of budget and at most 1.6 salaries.
    max_affordable = my_budget * 0.95
    max_reasonable = DAILY_SALARY * 1.6
    bid = min(target, max_affordable, max_reasonable)

    # If budget is tiny, bid what we can.
    if bid <= 0.0:
        bid = min(my_budget, DAILY_SALARY * 0.25)

    # Ensure non-negative
    if bid < 0.0:
        bid = 0.0

    return float(bid)
"""
