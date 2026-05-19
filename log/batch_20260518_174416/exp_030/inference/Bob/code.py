# ============================================================
# Experiment: exp_030
# Agent: Bob
# Source: exp_030
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

    alive_opponents = [o for o in opponents_status.values() if o.get('alive')]

    # Base affordability / risk control
    budget = float(my_status['budget'])
    hp = float(my_status['hp'])
    no_water_days = int(my_status['no_water_days'])

    # Estimate how much water we can reasonably target today
    # If supply is low, we need to be more competitive.
    supply_ratio = (supply - float(MIN_SUPPLY)) / (float(MAX_SUPPLY) - float(MIN_SUPPLY))
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Read yesterday's bids to infer opponent pressure.
    prev_bids = []
    high_prev = None
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            b = float(prev.get('bid'))
            prev_bids.append(b)
            if high_prev is None or b > high_prev:
                high_prev = b

    # If we are already in danger, bid more to avoid further no-water days.
    danger = (hp <= 2.0) or (no_water_days >= 2)

    # Determine a conservative target bid based on opponent pressure.
    # Use their daily_salary as a scale only from their own state.
    # If multiple opponents, use the max daily_salary among them as a proxy for the game scale.
    max_opp_salary = 0.0
    for opp in alive_opponents:
        max_opp_salary = max(max_opp_salary, float(opp.get('daily_salary', 0.0)))

    # Default bid when no trace info
    if high_prev is None or max_opp_salary <= 0.0:
        if danger:
            bid = DAILY_SALARY * (0.85 - 0.1 * supply_ratio)
        else:
            # More aggressive when supply is low
            bid = DAILY_SALARY * (0.55 + 0.15 * (1.0 - supply_ratio))
    else:
        # If opponents were bidding very high yesterday, expect continued aggression.
        # Scale threshold relative to max_opp_salary.
        high_threshold = 0.85 * max_opp_salary
        if high_prev >= high_threshold:
            if danger:
                bid = DAILY_SALARY * 0.65
            else:
                # Match pressure but not fully; try to win with a slight edge.
                bid = min(budget, max(high_prev * 0.95, DAILY_SALARY * (0.45 + 0.15 * (1.0 - supply_ratio))))
        else:
            # Yesterday was relatively calm: bid enough to secure water.
            # Use a small overbid above their max yesterday, adjusted for supply.
            over = 1.5 + 3.0 * (1.0 - supply_ratio)
            bid = max(high_prev + over, DAILY_SALARY * (0.40 + 0.10 * (1.0 - supply_ratio)))

    # Convert bid to a feasible integer-ish amount while staying within budget.
    bid = float(bid)
    if bid > budget:
        bid = budget

    # Ensure we don't bid trivially low; also cap to avoid bankruptcy.
    min_reasonable = 0.25 * DAILY_SALARY
    max_reasonable = min(budget, DAILY_SALARY * 0.95)
    bid = max(min_reasonable, min(max_reasonable, bid))

    # Final safety: if we have extremely low budget, bid what we can.
    if budget <= 0.0:
        return 0
    if budget < min_reasonable:
        return max(0.0, budget)

    return bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    # Alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # If no opponents, just secure enough water cheaply.
    if not alive_opps:
        target = 0.35 * DAILY_SALARY
        return max(0.0, min(float(my_status.get('budget', 0.0)), target))

    # Read yesterday bids from each opponent (immediate reaction only)
    prev_bids = []
    prev_hp_after = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid', 0.0)))
            except Exception:
                pass
            if prev.get('hp_after') is not None:
                try:
                    prev_hp_after.append(float(prev.get('hp_after')))
                except Exception:
                    pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))

    # Supply pressure: lower supply implies higher chance we need to win more.
    # With req=9 and supply in [15,25], the effective share is tight.
    # Use a normalized pressure in [0,1].
    pressure = 0.0
    if MAX_SUPPLY - MIN_SUPPLY > 0:
        pressure = (float(supply) - float(MIN_SUPPLY)) / float(MAX_SUPPLY - MIN_SUPPLY)
    # pressure=0 at MIN_SUPPLY (worst), pressure=1 at MAX_SUPPLY (best)
    supply_need = 1.0 - pressure

    # Baseline bid: moderate, scaled by supply_need and our HP.
    # If we're low HP, bid more to avoid running out of water days.
    hp_need = 0.0
    if my_hp <= 1.0:
        hp_need = 1.0
    elif my_hp <= 3.0:
        hp_need = 0.7
    elif my_hp <= 5.0:
        hp_need = 0.35
    else:
        hp_need = 0.15

    # Opponent aggression signal: Cindy survived with high bids; high average/highest suggests bidding war.
    # If highest_prev_bid is high, we may need to outbid slightly; otherwise stay cheaper.
    aggression = 0.0
    if highest_prev_bid >= 0.85 * DAILY_SALARY:
        aggression = 1.0
    elif avg_prev_bid >= 0.7 * DAILY_SALARY:
        aggression = 0.7
    elif avg_prev_bid >= 0.5 * DAILY_SALARY:
        aggression = 0.4
    else:
        aggression = 0.2

    # Compute a target bid.
    # Keep within budget; also avoid overpaying when HP is comfortable and supply is higher.
    base = 0.45 * DAILY_SALARY
    target = base * (0.6 + 0.8 * supply_need) * (0.7 + 0.6 * hp_need)

    # If yesterday showed very high bids, bid up but only to a capped level.
    if aggression >= 0.9:
        target = max(target, min(my_budget, 0.75 * DAILY_SALARY))
        # Slightly above highest yesterday to steal water if feasible.
        target = max(target, min(my_budget, highest_prev_bid + 2.5))
    elif aggression >= 0.6:
        target = max(target, min(my_budget, 0.6 * DAILY_SALARY))
        target = max(target, min(my_budget, highest_prev_bid * 0.95))
    else:
        # When not aggressive, stay near baseline but still responsive to supply.
        target = min(my_budget, target)

    # Hard caps for risk control.
    # If HP is very low, allow higher spending; otherwise cap at ~0.75 salary.
    if my_hp <= 2.0:
        cap = 0.95 * DAILY_SALARY
    else:
        cap = 0.75 * DAILY_SALARY

    target = min(float(my_budget), float(cap), float(target))
    if target < 0.0:
        target = 0.0

    # Ensure we always bid at least a small amount if budget allows.
    if my_budget > 0 and target == 0.0:
        target = min(my_budget, 0.1 * DAILY_SALARY)

    return float(target)
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

    # Alive opponents and yesterday bid signals
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # If no opponents, conserve
    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    prev_bids = []
    prev_hp_after = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev['bid']))
            # not always present; keep for potential tie-break
            if prev.get('hp_after') is not None:
                prev_hp_after.append(float(prev['hp_after']))

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Determine how many water units matter for me today (approx)
    # supply is between 15 and 25; each unit of water is a bundle decision by game mechanics.
    # We'll map supply to a confidence level: higher supply reduces need to outbid.
    supply_mid = (MIN_SUPPLY + MAX_SUPPLY) / 2.0
    supply_factor = 0.6 if supply >= supply_mid else 0.75

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])

    # Aggression policy:
    # - If others previously bid high (>= ~0.85*DAILY_SALARY), they are likely contesting.
    #   I bid enough to compete but not waste budget.
    # - If my hp is critical, I take a higher bid.
    high_pressure = highest_prev_bid >= DAILY_SALARY * 0.85

    # Compute a target bid baseline
    if my_hp <= 2.0:
        target = DAILY_SALARY * (0.95 if high_pressure else 0.85)
    elif my_hp <= 4.0:
        target = DAILY_SALARY * (0.75 if high_pressure else 0.62)
    else:
        target = DAILY_SALARY * (0.62 if high_pressure else 0.50)

    # Adjust by supply: lower supply => more likely scarcity => slightly higher bid
    if supply < supply_mid:
        target *= 1.08
    else:
        target *= 0.96

    # Small reactive bump over yesterday's highest bid when pressure is high, but cap.
    if high_pressure:
        # Bid just above their max signal to secure allocation when it matters.
        target = max(target, highest_prev_bid + 2.0)

    # Ensure bid is within budget and reasonable cap
    bid = min(my_budget, max(0.0, target))

    # If budget is extremely low, still bid something to avoid no-water streak.
    if my_budget < DAILY_SALARY * 0.2:
        bid = min(my_budget, DAILY_SALARY * 0.25)

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
    day = day_context.get('day', 0)

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive.append(opp)

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids to infer who overbids.
    prev_bids = []
    for opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate how many bidders likely needed water.
    # With supply 15..25 and requirement 9, at most 2 units/day are typically available.
    # So we should not overpay against a known high bidder.
    if supply <= WATER_REQ:
        base = DAILY_SALARY * 0.9
    else:
        # More supply means we can bid less.
        ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
        ratio = max(0.0, min(1.0, ratio))
        base = DAILY_SALARY * (0.55 + 0.25 * ratio)  # ~0.55..0.80

    # If opponent(s) were bidding extremely high yesterday, assume they are trying to secure water.
    # We can undercut slightly unless our hp is critical.
    if highest_prev_bid >= 0.9 * DAILY_SALARY * 1.5:  # ~121.5 threshold
        if hp <= 2.0 or no_water_days >= 2:
            target = DAILY_SALARY * 0.95
        else:
            # Undercut: bid enough to have a chance but not match.
            target = min(base, DAILY_SALARY * 0.65)
    else:
        # Otherwise bid near base, with urgency if we're already in no-water streak.
        if hp <= 2.0:
            target = DAILY_SALARY * 0.95
        elif no_water_days >= 2:
            target = DAILY_SALARY * 0.8
        else:
            target = base

    # Never bid more than budget.
    bid = max(0.0, min(budget, target))
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

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday pressure from previous_trace bids
    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Determine opponent aggressiveness
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid

    # Estimate how many water units supply can support
    # (Used only to scale bid; indices not needed.)
    units = supply / float(WATER_REQ)

    # Target bid: if someone was very aggressive yesterday, we match a fraction to secure water.
    # Otherwise, we bid moderately.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Cindy/Alex-like pressure
        if my_status['hp'] <= 2:
            bid = DAILY_SALARY * 0.95
        elif my_status['hp'] <= 4:
            bid = DAILY_SALARY * 0.65
        else:
            bid = DAILY_SALARY * 0.55
    else:
        # Eric-like mid aggression or David-like low; avoid overpaying
        # Use second_prev_bid as anchor to stay competitive.
        anchor = max(DAILY_SALARY * 0.5, second_prev_bid + 1.5)
        bid = min(anchor, DAILY_SALARY * 0.7)

    # Supply-aware adjustment: tighter supply means higher chance of being outbid.
    if supply <= float(MIN_SUPPLY) + 1.0:
        bid *= 1.08
    elif supply >= float(MAX_SUPPLY) - 1.0:
        bid *= 0.95

    # Budget and survival-day safety
    budget = float(my_status['budget'])
    hp = float(my_status['hp'])
    no_water_days = int(my_status['no_water_days'])

    # If we have accumulated no-water days, prioritize survival.
    if no_water_days >= 2 or hp <= 2:
        bid = max(bid, DAILY_SALARY * 0.85)

    # Never exceed budget
    bid = float(min(bid, budget))

    # If budget is extremely low, bid just enough to avoid wasting all budget.
    if bid <= 0.0:
        return 0.0

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

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday immediate behavior (previous_trace only)
    prev_bids = []
    prev_hp_after = []
    for o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        if prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid')))
            except Exception:
                pass
        if prev.get('hp_after') is not None:
            try:
                prev_hp_after.append(float(prev.get('hp_after')))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev_bid

    # Estimate scarcity pressure from supply
    # If supply is closer to MIN_SUPPLY, scarcity is higher.
    scarcity = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    # Base bid: aim to win water when scarcity is high, but avoid overpaying.
    # Use yesterday's aggressiveness as a proxy.
    baseline = DAILY_SALARY * (0.45 + 0.25 * scarcity)  # ~40-70

    # If someone yesterday bid extremely high, others likely overcompeted; adjust.
    # Cindy survived with very high bids; treat very high bid as signal of aggressive market.
    if highest_prev_bid >= DAILY_SALARY * 1.6:
        # Compete harder only if I'm at risk.
        if my_hp <= 3 or my_no_water_days >= 2:
            target = max(baseline, highest_prev_bid * 0.65)
        else:
            target = max(baseline, second_prev_bid * 0.85)
    elif highest_prev_bid >= DAILY_SALARY * 0.9:
        # Moderate competition
        if my_hp <= 2 or my_no_water_days >= 2:
            target = max(baseline, highest_prev_bid * 0.55)
        else:
            target = max(baseline, highest_prev_bid * 0.45)
    else:
        # Low competition; bid near baseline.
        target = baseline

    # If I'm critically low hp, bid aggressively.
    if my_hp <= 1:
        target = max(target, DAILY_SALARY * 0.95)
    elif my_hp <= 2:
        target = max(target, DAILY_SALARY * 0.75)

    # Convert target into a feasible bid bounded by budget.
    bid = min(my_budget, target)

    # Ensure non-negative
    if bid < 0.0:
        bid = 0.0

    # Small day-based adjustment to avoid ties (deterministic)
    # Use int() to avoid any float index issues (none used here, but keep deterministic).
    day_int = int(day)
    if day_int % 2 == 0:
        bid *= 1.02
    else:
        bid *= 0.98

    bid = min(my_budget, bid)
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

    supply = float(day_context.get('supply', (MIN_SUPPLY + MAX_SUPPLY) / 2.0))
    day = day_context.get('day', 0)

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for k, o in opponents_status.items():
        if o is not None and bool(o.get('alive', False)):
            alive_opps.append(o)

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids
    yesterday_bids = []
    yesterday_by_agent = {}
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                b_val = float(b)
            except Exception:
                continue
            yesterday_bids.append(b_val)
            yesterday_by_agent[opp.get('agent_id', None)] = b_val

    # If we can't read bids, fall back to survival-oriented bidding
    if not yesterday_bids:
        if hp <= 2 or no_water_days >= 1:
            return max(0.0, min(budget, DAILY_SALARY * 0.85))
        return max(0.0, min(budget, DAILY_SALARY * 0.55))

    highest_prev_bid = max(yesterday_bids)
    # Identify Cindy's likely pressure if present
    cindy_bid = None
    for opp in alive_opps:
        if opp.get('agent_id', None) == 'Cindy':
            prev = opp.get('previous_trace', {}) or {}
            if prev.get('bid', None) is not None:
                try:
                    cindy_bid = float(prev.get('bid'))
                except Exception:
                    cindy_bid = None

    # Estimate how many water units we can reasonably target
    # supply is total available; bidding competition determines allocation.
    # We aim to secure at least our requirement when supply is closer to MIN.
    supply_ratio = supply / float(WATER_REQ)
    # If supply is barely above our requirement, we must prioritize.
    scarcity = 1.0
    if supply_ratio >= 2.0:
        scarcity = 0.7
    elif supply_ratio >= 1.5:
        scarcity = 0.85

    # Pressure response: if someone paid near/above our daily salary, we should not underbid too much.
    pressure = 0.0
    if cindy_bid is not None:
        pressure = cindy_bid
    else:
        pressure = highest_prev_bid

    # Base bid level
    if hp <= 2 or no_water_days >= 2:
        base = DAILY_SALARY * 0.95
    elif hp <= 4 or no_water_days >= 1:
        base = DAILY_SALARY * 0.75
    else:
        base = DAILY_SALARY * 0.58

    # Adjust with yesterday pressure
    # If Cindy/highest_prev_bid was high, increase slightly to avoid losing allocation.
    # Otherwise, keep moderate to preserve budget.
    if pressure >= DAILY_SALARY * 1.25:
        base *= 1.05
    elif pressure >= DAILY_SALARY * 0.9:
        base *= 1.0
    else:
        base *= 0.92

    # Scarcity adjustment
    base *= scarcity

    # Practical cap: we never bid above budget or a fraction of remaining days' ability.
    # With episode_days=10, a conservative cap helps avoid running out.
    episode_days = int(getattr(day_context, 'episode_days', 10) if hasattr(day_context, 'episode_days') else 10)
    # day_context does not include episode_days; use 10 as default.
    # Avoid using non-provided fields.
    remaining_days = 10 - int(day) if isinstance(day, (int, float)) else 10
    if remaining_days < 1:
        remaining_days = 1
    daily_cap = DAILY_SALARY * 0.95
    cap = min(budget, daily_cap)

    bid = max(0.0, min(cap, base))

    # Small anti-tying/underbidding nudge: if highest_prev_bid was not too far above our base, bid slightly above it.
    # Use int() indices only if needed; here no indexing.
    if highest_prev_bid > 0:
        if bid < highest_prev_bid * 0.98:
            bid = min(cap, highest_prev_bid * 1.02)

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

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    # Identify alive opponents and collect yesterday bids
    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    if not alive_opponents:
        # No contest; conserve
        return min(my_status.get('budget', 0.0), DAILY_SALARY * 0.4)

    yesterday_bids = []
    yesterday_by_opp = {}
    for opp_id, opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            yesterday_bids.append(float(bid))
            yesterday_by_opp[opp_id] = float(bid)

    # If no trace bids, fall back to hp-based conservative
    if not yesterday_bids:
        hp = float(my_status.get('hp', 0.0))
        if hp <= 2:
            return min(my_status.get('budget', 0.0), DAILY_SALARY * 0.9)
        return min(my_status.get('budget', 0.0), DAILY_SALARY * 0.55)

    highest_prev_bid = max(yesterday_bids)
    second_highest_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    no_water_days = float(my_status.get('no_water_days', 0.0))

    # Estimate contest pressure from supply: higher supply reduces need to overbid
    # Normalize supply into [0,1]
    if MAX_SUPPLY == MIN_SUPPLY:
        supply_norm = 0.5
    else:
        supply_norm = (float(supply) - float(MIN_SUPPLY)) / float(MAX_SUPPLY - MIN_SUPPLY)
        if supply_norm < 0.0:
            supply_norm = 0.0
        if supply_norm > 1.0:
            supply_norm = 1.0

    # Target bid: beat the likely winner band (around Alex/Eric ~72-88) but avoid Cindy-like overbidding
    # Use a small premium over the second highest when supply is moderate/high.
    base_premium = 3.0 + 6.0 * (1.0 - supply_norm)  # lower premium when supply is high

    # If someone previously overbid aggressively (> ~1.1*salary), avoid matching; just clear the main band.
    aggressive_threshold = DAILY_SALARY * 1.15

    if highest_prev_bid >= aggressive_threshold:
        # Someone tends to overspend; we can undercut.
        # Bid slightly above second highest (or above a floor) to capture water.
        target = second_highest_prev_bid + base_premium
    else:
        # Normal contest: bid above highest by a small amount only if we are in danger.
        if my_hp <= 2 or no_water_days >= 2:
            target = highest_prev_bid + 1.5
        else:
            target = second_highest_prev_bid + base_premium

    # Safety floors/ceilings to manage budget
    # If my hp is low, spend more; if healthy, spend less.
    if my_hp <= 2:
        spend_cap = DAILY_SALARY * 0.95
    elif my_hp <= 4:
        spend_cap = DAILY_SALARY * 0.8
    else:
        spend_cap = DAILY_SALARY * 0.65

    # Also ensure we don't exceed budget
    target = min(target, spend_cap)
    target = min(target, my_budget)

    # If target is too low to be competitive, bump to a reasonable mid bid
    # (based on observed band ~72-88)
    min_competitive = DAILY_SALARY * 0.45
    if target < min_competitive:
        target = min(min_competitive, my_budget)

    # Final clamp
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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return float(min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace only (immediate reaction)
    yesterday_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # Pressure estimate: who likely bid high yesterday (Cindy survived with high bids)
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Determine urgency: if low HP or already accumulating no-water days, bid more.
    # Heuristic: if hp <= 2 or no_water_days >= 2, treat as critical.
    critical = (hp <= 2) or (no_water_days >= 2)

    # Supply scarcity factor: lower supply => bid higher to secure enough water share.
    # Map supply in [15,25] to scarcity in [1.0,0.6]
    if MAX_SUPPLY > MIN_SUPPLY:
        scarcity = 1.0 - 0.4 * ((supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY))
    else:
        scarcity = 1.0
    if scarcity < 0.6:
        scarcity = 0.6
    if scarcity > 1.0:
        scarcity = 1.0

    # Base bid target
    if critical:
        target = DAILY_SALARY * 0.85 * scarcity
    else:
        # If someone was already bidding very high yesterday, slightly undercut to avoid waste.
        # If highest_prev_bid is large, we need to match a fraction.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            target = max(DAILY_SALARY * 0.55, highest_prev_bid * 0.75)
        else:
            target = max(DAILY_SALARY * 0.45, highest_prev_bid * 0.65)
        target = target * scarcity

    # Budget cap: never exceed budget
    # Also keep some budget for later days: reserve a fraction unless critical.
    reserve_frac = 0.25 if critical else 0.45
    max_affordable = budget * (1.0 - reserve_frac)
    bid = min(float(target), float(max_affordable), float(budget))

    # Ensure non-negative
    if bid < 0.0:
        bid = 0.0

    # If supply is extremely low, add a small bump
    if supply <= float(WATER_REQ) + 6.0:
        bid = min(float(budget), bid + DAILY_SALARY * 0.05)

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

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    # If no one is alive, take what you can afford.
    if not alive_opponents:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace for immediate reaction.
    prev_bids = []
    prev_by_id = {}
    for opp_id, opp in opponents_status.items():
        if not opp.get('alive', False):
            continue
        prev = opp.get('previous_trace', {}) if isinstance(opp.get('previous_trace', {}), dict) else {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                bid_val = float(bid)
            except Exception:
                bid_val = None
            if bid_val is not None:
                prev_bids.append(bid_val)
                prev_by_id[opp_id] = bid_val

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # If Cindy previously spent big, assume she will keep contesting.
    # Use that to decide whether to outbid slightly or conserve.
    cindy_bid = prev_by_id.get('Cindy', None)
    cindy_contest = (cindy_bid is not None and cindy_bid >= DAILY_SALARY * 0.9)

    # Supply pressure: in medium scenario supply is 15-25.
    # If supply is high, winning costs less in utility terms; we can bid to secure.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if (MAX_SUPPLY - MIN_SUPPLY) > 0 else 0.0
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Base bid target
    # - If our hp is low or we already have no-water days, bid more aggressively.
    # - If Cindy contested yesterday, bid to beat her by a small margin.
    urgency = 0
    if hp <= 2.0:
        urgency += 2
    if no_water_days >= 1:
        urgency += 1

    # Determine a target threshold based on yesterday.
    if cindy_contest:
        # Cindy likely anchors high; try to beat the anchor but not overspend.
        target = min(budget, max(highest_prev_bid * 1.02, DAILY_SALARY * (0.75 + 0.15 * supply_ratio)) )
    else:
        # If no strong anchor, bid around a fraction of salary.
        target = min(budget, DAILY_SALARY * (0.55 + 0.25 * supply_ratio) + urgency * 10.0)

    # If our hp is critically low, push higher.
    if urgency >= 2:
        target = min(budget, max(target, DAILY_SALARY * 0.9))

    # If we are healthy and supply is decent, conserve.
    if hp >= 6.0 and urgency == 0:
        target = min(target, DAILY_SALARY * (0.45 + 0.2 * supply_ratio))

    # Final clamp to non-negative and reasonable upper bound.
    if budget <= 0.0:
        return 0.0

    bid = max(0.0, min(float(budget), float(target)))
    return bid
"""
