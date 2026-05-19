# ============================================================
# Experiment: exp_052
# Agent: Bob
# Source: exp_052
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

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Collect yesterday bids from alive opponents for immediate reaction
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(float(prev['bid']))

    # Estimate how aggressive the market was yesterday
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid
    else:
        highest_prev_bid = 0.0
        second_prev_bid = 0.0

    # Risk-aware scaling
    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # If we're in danger, bid to secure water regardless of opponent bids
    danger = (hp <= 2.0) or (no_water_days >= 2)

    # Baseline target bid depends on supply pressure: lower supply -> higher bid
    # Normalize supply to [0,1] where 0 means MIN_SUPPLY, 1 means MAX_SUPPLY
    if MAX_SUPPLY == MIN_SUPPLY:
        supply_norm = 1.0
    else:
        supply_norm = (supply - float(MIN_SUPPLY)) / (float(MAX_SUPPLY) - float(MIN_SUPPLY))
    supply_norm = max(0.0, min(1.0, supply_norm))

    # When supply is low, we bid more.
    supply_factor = 0.45 + (1.0 - supply_norm) * 0.55  # range ~[0.45,1.0]

    # Decide bid
    if danger:
        # Bid high but not necessarily maximum; try to outbid the highest previous by a small margin
        target = max(highest_prev_bid + 1.0, DAILY_SALARY * 0.75) * supply_factor
    else:
        # If opponent was very aggressive yesterday, we avoid overpaying but still compete.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # Match slightly above second-highest to reduce chance of losing if others follow pattern
            competitor_anchor = second_prev_bid if second_prev_bid > 0.0 else highest_prev_bid
            target = max(competitor_anchor + 1.0, DAILY_SALARY * 0.45) * supply_factor
        else:
            # Market was calm: bid enough to win occasionally without exhausting budget
            # Use a fraction of daily salary plus a small premium over highest_prev_bid.
            target = max(highest_prev_bid + 0.5, DAILY_SALARY * 0.35) * supply_factor

    # Clamp to budget and a reasonable upper bound
    # Ensure non-negative
    target = max(0.0, float(target))
    bid = min(budget, target)

    # If budget is extremely low, still bid a minimal amount
    if bid <= 0.0:
        bid = min(budget, DAILY_SALARY * 0.1)

    return float(bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opponents = [o for o in opponents_status.values() if o.get('alive')]
    if not alive_opponents:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids (immediate reaction only)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    yesterday_bids.append(float(b))
                except Exception:
                    pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid

    # Estimate how many water units are likely available for this day
    # (not exact, but helps scale bids)
    expected_units = max(1, int(supply / float(WATER_REQ)))

    # Base target: aim slightly below yesterday's high pressure to win ties/near-ties.
    # If my HP is low, overbid to secure water.
    if hp <= 2.0 or no_water_days >= 2:
        target = max(highest_prev_bid * 0.98, second_prev_bid * 1.02, DAILY_SALARY * 0.85)
    elif hp <= 4.0:
        target = max(highest_prev_bid * 0.93, second_prev_bid * 1.00, DAILY_SALARY * 0.65)
    else:
        # HP is safe: conserve budget but stay competitive.
        target = max(highest_prev_bid * 0.90, second_prev_bid * 0.98, DAILY_SALARY * 0.55)

    # Adjust for supply: if supply is low, bidding should be more aggressive.
    # supply range is [15,25], so scale modestly.
    if supply <= 17.0:
        target *= 1.08
    elif supply >= 22.0:
        target *= 0.96

    # Keep bid within budget and reasonable upper bound.
    # Also avoid extreme overbids early unless HP is critical.
    if hp > 4.0 and highest_prev_bid > 0:
        cap = min(budget, highest_prev_bid + 5.0)
    else:
        cap = min(budget, highest_prev_bid + 15.0) if highest_prev_bid > 0 else min(budget, DAILY_SALARY * 0.95)

    bid = max(0.0, min(cap, float(target)))

    # If our budget is tiny, still bid what we can.
    if budget <= 1.0:
        return 0.0

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
    day = day_context['day']

    # Safety: if no budget, bid 0
    if my_status['budget'] <= 0:
        return 0.0

    # Collect alive opponents and yesterday bids
    alive_opps = []
    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)
            prev = opp.get('previous_trace', {}) or {}
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(float(prev['bid']))

    # If no info/opponents, bid a conservative share
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.45))

    # Pressure signal from yesterday
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_highest_prev_bid = 0.0
    if len(yesterday_bids) >= 2:
        sorted_bids = sorted(yesterday_bids, reverse=True)
        second_highest_prev_bid = float(sorted_bids[1])

    # Estimate how many full water units are likely to be affordable/needed
    # (not exact, but used for scaling)
    supply_units = int(supply / float(WATER_REQ)) if WATER_REQ > 0 else 0
    # If supply is near the lower bound, competition likely increases
    scarcity_factor = 1.0
    if supply <= (MIN_SUPPLY + 1.0):
        scarcity_factor = 1.25
    elif supply >= (MAX_SUPPLY - 1.0):
        scarcity_factor = 0.85

    # Base bid: aim to secure water without matching overbidding
    # Use hp and no_water_days to decide ramping.
    hp = float(my_status['hp'])
    no_water_days = int(my_status['no_water_days'])
    budget = float(my_status['budget'])

    # If I'm already in danger, bid aggressively.
    if hp <= 2 or no_water_days >= 1:
        base = DAILY_SALARY * 0.85
    elif hp <= 4:
        base = DAILY_SALARY * 0.65
    else:
        base = DAILY_SALARY * 0.50

    # If someone previously bid extremely high (Cindy-like), others may be overextending;
    # still, we must not be too low when highest_prev_bid is huge.
    if highest_prev_bid >= DAILY_SALARY * 1.35:
        # Bid enough to compete, but not necessarily equal.
        target = highest_prev_bid * 0.72
        base = max(base, target)
    elif highest_prev_bid >= DAILY_SALARY * 0.85:
        base = max(base, highest_prev_bid * 0.55)

    # If second-highest is close to highest, competition is intense; nudge up.
    if second_highest_prev_bid > 0 and highest_prev_bid > 0:
        if (highest_prev_bid - second_highest_prev_bid) / highest_prev_bid < 0.12:
            base *= 1.08

    # Scale by scarcity and mild day factor (later days can require more commitment)
    day_factor = 1.0
    if int(day) >= 7:
        day_factor = 1.10

    bid = base * scarcity_factor * day_factor

    # Convert to feasible bid respecting budget and typical cap.
    # Also, don't bid above budget.
    bid = float(min(bid, budget))

    # Ensure non-negative
    if bid < 0:
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Alive opponents
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    # Yesterday bids (immediate reaction only)
    yesterday_bids = []
    for oid, o in alive:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Estimate how many water units are likely needed today
    # If supply is low, competition increases; if supply is high, we can bid less.
    supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY + 1e-9)  # 0..1

    # Pressure from yesterday: if someone was willing to bid very high, they likely try to secure water.
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Base bid aggressiveness
    # - If supply is low, be more aggressive.
    # - If our hp is low, be more aggressive.
    # - If yesterday pressure was high, slightly increase to prevent being outbid.
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Minimum urgency threshold
    urgency = 0
    if hp <= 2:
        urgency += 2
    elif hp <= 4:
        urgency += 1
    if no_water_days >= 2:
        urgency += 1

    # Convert to a target bid range
    # Use fractions of DAILY_SALARY to keep within plausible budgets.
    # When highest_prev_bid is high, raise our target to just above a likely clearing point.
    low_supply_bonus = 0.25 if supply_factor < 0.5 else 0.0

    if highest_prev_bid >= DAILY_SALARY * 1.2:
        # Strong competitor trying to lock water; respond but avoid overpaying.
        target = DAILY_SALARY * (0.55 + low_supply_bonus + 0.15 * min(urgency, 2))
        # Nudge upward if we think they set a high clearing price.
        target = max(target, min(budget, highest_prev_bid * 0.75))
    elif highest_prev_bid >= DAILY_SALARY * 0.85:
        target = DAILY_SALARY * (0.45 + low_supply_bonus + 0.12 * min(urgency, 2))
        target = max(target, min(budget, highest_prev_bid * 0.6))
    else:
        target = DAILY_SALARY * (0.35 + low_supply_bonus + 0.10 * min(urgency, 2))

    # If supply is very low, increase more to avoid water deprivation.
    if supply <= float(WATER_REQ) + 2:
        target *= 1.25

    # Ensure we don't bid more than budget.
    if budget <= 0:
        return 0.0

    bid = min(budget, target)

    # If urgency is high, allow a higher ceiling but still bounded by budget.
    if urgency >= 3:
        bid = min(budget, max(bid, DAILY_SALARY * 0.9))

    # Keep bid non-negative.
    if bid < 0:
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive'):
            alive.append(o)

    if not alive:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # React to yesterday's bids (only immediate trace)
    prev_bids = []
    for o in alive:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    # Cindy appears the most aggressive from trace; hedge vs her by not matching her unless needed.
    # Use our hp/no_water_days to decide urgency.
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Urgency score: higher when hp is low or we've gone many days without water.
    urgency = 0
    if hp <= 2.0:
        urgency += 3
    elif hp <= 4.0:
        urgency += 2
    elif hp <= 7.0:
        urgency += 1

    if no_water_days >= 3:
        urgency += 3
    elif no_water_days == 2:
        urgency += 2
    elif no_water_days == 1:
        urgency += 1

    # Supply pressure: when supply is high, we can bid less and still expect allocation.
    # Map supply to a multiplier in [0.75, 1.15]
    if MAX_SUPPLY <= MIN_SUPPLY:
        supply_mult = 1.0
    else:
        t = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
        supply_mult = 0.75 + 0.4 * max(0.0, min(1.0, t))

    # Base bid target: moderate fraction of salary.
    # If Cindy-like aggression is present (high previous bid), we shade below it unless urgency is high.
    # highest_prev_bid threshold around 0.85*DAILY_SALARY = 76.5
    shaded = 0.55 * DAILY_SALARY
    if highest_prev_bid >= 0.85 * DAILY_SALARY:
        # Shade under the aggressor to avoid budget death; only escalate when urgency is high.
        if urgency >= 4:
            target = 0.95 * min(DAILY_SALARY, highest_prev_bid)
        elif urgency >= 2:
            target = 0.7 * min(DAILY_SALARY, highest_prev_bid)
        else:
            target = shaded * supply_mult
    else:
        # If no one is extremely aggressive yesterday, bid enough to stay competitive.
        if urgency >= 4:
            target = 0.9 * DAILY_SALARY
        elif urgency >= 2:
            target = 0.65 * DAILY_SALARY
        else:
            target = 0.5 * DAILY_SALARY
        target *= supply_mult

    # Ensure we don't overbid beyond our budget.
    # Also, if budget is low, bid nearly all remaining budget to prevent HP collapse.
    if budget <= 0:
        return 0.0

    # Budget-aware cap/floor
    low_budget = budget < 0.35 * DAILY_SALARY
    if low_budget:
        # Spend aggressively when we are already constrained.
        target = max(target, 0.85 * budget)

    bid = float(min(budget, max(0.0, target)))

    # Final safety: if we're in critical HP, bid to secure water.
    if hp <= 1.5:
        bid = float(min(budget, max(bid, 0.95 * DAILY_SALARY)))

    return bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    # Identify alive opponents
    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    # If no one alive, bid to maximize survival with minimal risk
    if not alive_opponents:
        return max(0.0, min(float(my_status.get('budget', 0.0)), DAILY_SALARY * 0.4))

    # Read yesterday bids from immediate trace
    prev_bids = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate opponent pressure
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    # Determine how tight the market is likely to be
    # supply in [15,25]: higher supply -> less competition; lower supply -> more competition
    supply_ratio = 0.0
    if (25.0 - 15.0) > 1e-9:
        supply_ratio = (supply - 15.0) / (25.0 - 15.0)
    # competition_factor: 1.0 at low supply, 0.0 at high supply
    competition_factor = max(0.0, min(1.0, 1.0 - supply_ratio))

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Base bid: aim around a fraction of salary; scale with competition
    # If opponents yesterday bid very high, we need to match a bit; if not, stay cheaper.
    # Also react to our own low hp / long no-water streak.
    need_multiplier = 1.0
    if my_hp <= 2.0:
        need_multiplier = 1.35
    elif my_hp <= 4.0:
        need_multiplier = 1.15

    if no_water_days >= 2:
        need_multiplier *= 1.15

    # Target bid level relative to yesterday pressure
    # If highest_prev_bid was huge, we slightly undercut rather than chase exactly.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        target = min(highest_prev_bid * 0.95, DAILY_SALARY * (0.95 - 0.25 * competition_factor))
    else:
        # Use average as a soft guide; add competition premium at low supply
        target = max(DAILY_SALARY * 0.45, avg_prev_bid * 0.9) + (DAILY_SALARY * 0.15) * competition_factor

    # Convert target into a final bid with some smoothing
    # Ensure we don't bid above what we can afford.
    max_affordable = max(0.0, my_budget)

    # Additional day-based gentle ramp: later days can justify higher bids if still alive
    # episode_days is 10 in meta-round, but day_context only has day.
    day_ramp = 1.0
    if day >= 7:
        day_ramp = 1.12
    elif day >= 4:
        day_ramp = 1.06

    bid = target * need_multiplier * day_ramp

    # Clamp bid to sensible bounds
    # If supply is high, keep bid lower; if supply is low, keep it higher.
    lower_bound = DAILY_SALARY * (0.35 + 0.15 * competition_factor)
    upper_bound = DAILY_SALARY * (1.05 - 0.10 * (1.0 - competition_factor))

    bid = max(lower_bound, min(upper_bound, bid))
    bid = min(bid, max_affordable)

    # If budget is extremely low, bid whatever remains (or 0)
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

    supply = day_context['supply']
    day = day_context['day']

    # Alive opponents
    alive_opponents = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opponents:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.4))

    # Extract yesterday bids for immediate reaction
    yesterday_bids = []
    yesterday_states = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            yesterday_bids.append(bid)
            yesterday_states.append((opp, bid, prev))

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Pressure heuristic: if someone bid extremely high yesterday, they likely overbid.
    # Use that to avoid matching unless our HP is critical.
    critical_hp = my_status['hp'] <= 2

    # Supply-based aggressiveness: when supply is low, competition for water is more costly.
    # We'll bid enough to beat typical mid bids, but not chase extremes.
    if supply <= float(MIN_SUPPLY) + 0.5:
        base = DAILY_SALARY * 0.65
    elif supply <= float(MIN_SUPPLY) + 5.0:
        base = DAILY_SALARY * 0.55
    else:
        base = DAILY_SALARY * 0.45

    # If opponents previously overreached (very high bid), we can shade downward.
    # If our HP is critical, we bid higher to secure water.
    if highest_prev_bid >= DAILY_SALARY * 1.4:
        if critical_hp:
            target = DAILY_SALARY * 0.95
        else:
            target = min(base, highest_prev_bid * 0.55)
    else:
        if critical_hp:
            target = max(base, DAILY_SALARY * 0.85)
        else:
            # If there were moderate-high bids, slightly outbid the median-ish level.
            # Use max of base and a fraction of highest_prev_bid to stay competitive.
            target = max(base, highest_prev_bid * 0.6)

    # Budget safety: never exceed our budget.
    bid = min(my_status['budget'], target)

    # If we have many no-water days, increase bid to avoid further HP loss.
    if my_status.get('no_water_days', 0) >= 2:
        bid = min(my_status['budget'], max(bid, DAILY_SALARY * 0.75))

    # Ensure non-negative
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = [o for o in opponents_status.values() if o.get('alive')]
    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids (immediate reaction only)
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Pressure estimate: if opponents were bidding very high yesterday, bidding wars happen.
    # We'll undercut slightly while still ensuring a chance to win.
    # Also increase urgency if we've already had no water.
    urgency = 0.0
    if no_water_days >= 2:
        urgency = 1.0
    elif no_water_days == 1:
        urgency = 0.5

    hp_urgency = 0.0
    if hp <= 2:
        hp_urgency = 1.0
    elif hp <= 4:
        hp_urgency = 0.6

    # Supply-based target: if supply is low, fewer units exist -> more competition.
    # We cannot guarantee allocation, so we scale bids with expected scarcity.
    # Expected water units available for us: supply/WATER_REQ
    expected_units = supply / float(WATER_REQ)
    scarcity = 0.0
    if supply <= 17:
        scarcity = 1.0
    elif supply <= 20:
        scarcity = 0.7
    elif supply <= 23:
        scarcity = 0.4
    else:
        scarcity = 0.2

    # Base bid: moderate to avoid draining budget in a likely bidding war.
    # Use yesterday highest bid as an upper reference, but don't match it.
    # If highest_prev_bid is extremely high, cap our bid to a fraction.
    if highest_prev_bid >= DAILY_SALARY * 1.5:
        base = DAILY_SALARY * (0.35 + 0.25 * scarcity)
        # If we're in danger, raise a bit.
        base *= (1.0 + 0.6 * hp_urgency + 0.4 * urgency)
        bid = min(base, highest_prev_bid * 0.65)
    elif highest_prev_bid >= DAILY_SALARY * 1.0:
        base = DAILY_SALARY * (0.45 + 0.25 * scarcity)
        base *= (1.0 + 0.5 * hp_urgency + 0.3 * urgency)
        bid = min(base, highest_prev_bid * 0.75)
    else:
        base = DAILY_SALARY * (0.55 + 0.2 * scarcity)
        base *= (1.0 + 0.4 * hp_urgency + 0.25 * urgency)
        bid = min(base, highest_prev_bid * 0.9 + DAILY_SALARY * 0.2)

    # If supply suggests we likely need to secure water (expected_units < 2), raise slightly.
    if expected_units < 2.0:
        bid *= (1.0 + 0.15 * (1.0 + hp_urgency))

    # Ensure non-negative and within budget.
    bid = max(0.0, min(budget, bid))

    # If budget is tiny, still try to bid something proportional.
    if budget <= DAILY_SALARY * 0.2:
        bid = max(0.0, min(budget, DAILY_SALARY * 0.15))

    return float(bid)
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((agent_id, opp))

    if not alive_opponents:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace only (immediate reaction)
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
    second_prev_bid = sorted(yesterday_bids, reverse=True)[1] if len(yesterday_bids) >= 2 else 0.0

    # Supply pressure: if supply is close to our requirement, water is scarce => bid more.
    # If supply is comfortably above requirement, we can bid lower.
    scarcity_ratio = supply / float(WATER_REQ) if WATER_REQ > 0 else 1.0
    if scarcity_ratio <= 1.2:
        scarcity_factor = 1.15
    elif scarcity_ratio <= 1.6:
        scarcity_factor = 1.0
    else:
        scarcity_factor = 0.85

    # If we are at/near critical hp, prioritize survival.
    critical = (my_hp <= 2) or (my_no_water_days >= 2)

    # Decide based on opponent yesterday intensity.
    # If someone previously bid very high (near salary), assume aggressive contest today.
    aggressive_threshold = DAILY_SALARY * 0.85

    # Base bid target
    if highest_prev_bid >= aggressive_threshold:
        # Try to beat the likely top bidder without going all-in.
        target = highest_prev_bid + 2.0
        if critical:
            target = max(target, DAILY_SALARY * 0.95)
        else:
            target = min(target, DAILY_SALARY * 0.75)
    else:
        # If no extreme aggression, bid around the second-highest to secure water.
        # Use highest_prev_bid as a soft anchor.
        anchor = max(second_prev_bid, highest_prev_bid * 0.8)
        target = max(DAILY_SALARY * 0.45, anchor + 1.5)
        if critical:
            target = max(target, DAILY_SALARY * 0.85)

    target *= scarcity_factor

    # Final caps to respect budget and avoid unnecessary overpaying.
    # If budget is low, spend what we can but still follow critical logic.
    max_reasonable = DAILY_SALARY * 1.05
    bid = min(my_budget, min(target, max_reasonable))

    # Ensure non-negative
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Alive opponents and their yesterday bids
    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append((opp_id, opp))

    yesterday_bids = []
    highest_prev_bid = 0.0
    second_prev_bid = 0.0
    if alive_opponents:
        for _, opp in alive_opponents:
            prev = opp.get('previous_trace', {}) or {}
            b = prev.get('bid', None)
            if b is not None:
                try:
                    b = float(b)
                except Exception:
                    continue
                yesterday_bids.append(b)
        if yesterday_bids:
            yesterday_bids.sort(reverse=True)
            highest_prev_bid = float(yesterday_bids[0])
            second_prev_bid = float(yesterday_bids[1]) if len(yesterday_bids) > 1 else 0.0

    # If we are in danger, bid aggressively regardless
    if my_status['hp'] <= 2 or my_status.get('no_water_days', 0) >= 3:
        return min(float(my_status['budget']), DAILY_SALARY * 0.95)

    # Estimate how many full water units supply can support
    # (used only to scale aggressiveness, not to index)
    supply_units = supply / float(WATER_REQ)

    # Base bid: secure water at moderate cost; scale with supply level
    # When supply is higher, we can bid lower; when lower, bid higher.
    # supply_units ~ 1.67..2.78 for supply 15..25.
    if supply_units <= 2.0:
        base = DAILY_SALARY * 0.70
    elif supply_units <= 2.4:
        base = DAILY_SALARY * 0.60
    else:
        base = DAILY_SALARY * 0.52

    budget = float(my_status['budget'])

    # Undercut strategy vs Cindy's heavy spending:
    # If the highest previous bid was very high, we match partially; otherwise underbid.
    # Threshold tuned from yesterday: Cindy max ~194.5, Alex max ~182.5.
    extreme_pressure = highest_prev_bid >= DAILY_SALARY * 1.6  # >=144

    if extreme_pressure:
        # Don't fully commit; bid just above a likely clearing price without matching the top.
        target = max(base, second_prev_bid + 2.0) if second_prev_bid > 0 else max(base, highest_prev_bid * 0.75)
    else:
        # If no extreme pressure, underbid relative to highest previous bid.
        if highest_prev_bid > 0:
            target = min(base, highest_prev_bid - 10.0) if highest_prev_bid - 10.0 > 0 else base
        else:
            target = base

    # Keep within budget and avoid overspending late
    # Since episode is 10 days, be slightly more conservative early-mid.
    # day is 1..10 typically; at day 10 we can spend more.
    day_factor = 0.85 if day < 8 else 1.0
    bid = target * day_factor

    # Final clamps
    if bid < 0:
        bid = 0.0
    bid = min(bid, budget)

    # If budget is very low, bid whatever we can but keep at least enough to compete
    if budget <= DAILY_SALARY * 0.25:
        return budget

    return bid
"""
