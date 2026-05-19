# ============================================================
# Experiment: exp_032
# Agent: Bob
# Source: exp_032
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

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    budget = my_status.get('budget', 0.0)
    hp = my_status.get('hp', 0)
    no_water_days = my_status.get('no_water_days', 0)

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Extract yesterday bids for immediate reaction
    prev_bids = []
    prev_max_bid = None
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid', None)
        if bid is not None:
            prev_bids.append(float(bid))
    if prev_bids:
        prev_max_bid = max(prev_bids)
    else:
        prev_max_bid = 0.0

    # Base willingness: aim around what we'd need to secure at least WATER_REQ when supply is mid-range.
    # Convert supply to an approximate capacity pressure.
    # If supply is scarce, increase; if abundant, decrease.
    supply_ratio = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_ratio = (float(supply) - float(MIN_SUPPLY)) / float(MAX_SUPPLY - MIN_SUPPLY)
    supply_ratio = max(0.0, min(1.0, supply_ratio))
    scarcity_factor = 1.0 - supply_ratio  # 1 when scarce, 0 when abundant

    # Health/bad streak urgency
    urgency = 0.0
    if hp <= 2:
        urgency += 0.35
    elif hp <= 4:
        urgency += 0.18
    if no_water_days >= 2:
        urgency += 0.25
    elif no_water_days == 1:
        urgency += 0.1

    # Opponent aggressiveness inference
    # If they bid very high yesterday, they likely expect to win/avoid starvation.
    high_pressure = 1.0 if prev_max_bid >= DAILY_SALARY * 0.85 else 0.0

    # Strategy: undercut when others are aggressive; otherwise bid moderately.
    # Use small offsets to react to their max bid.
    if high_pressure >= 0.5:
        # Undercut slightly but still compete; scale with our urgency and scarcity.
        target = prev_max_bid - 2.0 - (urgency * 5.0) + (scarcity_factor * 3.0)
        # Ensure we don't go too low to be irrelevant
        floor_bid = DAILY_SALARY * (0.35 + urgency * 0.25)
        bid = max(floor_bid, target)
    else:
        # If they were conservative, we can bid to secure water efficiently.
        # Increase with scarcity and urgency.
        bid = DAILY_SALARY * (0.45 + 0.25 * scarcity_factor + 0.35 * urgency)

    # Convert bid into a safe range based on budget and expected competition.
    bid = max(0.0, float(bid))
    max_affordable = float(budget)

    # If supply is extremely low relative to WATER_REQ, we must spend more.
    if float(supply) < float(WATER_REQ) * 1.1:
        bid = max(bid, DAILY_SALARY * 0.75)

    # If our hp is critically low, prioritize survival.
    if hp <= 1:
        bid = max(bid, DAILY_SALARY * 0.9)

    return min(max_affordable, bid)
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

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Identify alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday bids to infer aggressive pressure
    yesterday_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid', 0.0)))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Supply pressure: higher supply means we can bid a bit less and still win
    # (but we don't know allocation rule; we use it as a conservative scaling)
    supply_ratio = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    if supply_ratio < 0.0:
        supply_ratio = 0.0
    if supply_ratio > 1.0:
        supply_ratio = 1.0

    # Base bid: aim around mid of daily salary, tempered by supply
    base = DAILY_SALARY * (0.45 + 0.15 * supply_ratio)

    # If my HP is low or I'm already accruing no-water days, increase bid to avoid death
    if hp <= 2:
        base = DAILY_SALARY * 0.9
    elif hp <= 4:
        base = DAILY_SALARY * 0.7

    if no_water_days >= 2:
        base = max(base, DAILY_SALARY * 0.65)

    # If yesterday saw very high bids, nudge upward slightly to compete.
    # Cindy/Eric were ~112-119; we don't want to match their full aggression unless necessary.
    if highest_prev_bid >= DAILY_SALARY * 1.15:
        if hp <= 4:
            target = max(base, highest_prev_bid * 0.75)
        else:
            target = max(base, highest_prev_bid * 0.55)
    elif highest_prev_bid >= DAILY_SALARY * 0.85:
        target = max(base, highest_prev_bid * 0.45)
    else:
        target = base

    # Never bid more than we can afford
    target = min(target, budget)

    # Also cap to avoid reckless spending (but allow above salary if budget permits)
    # In medium scenario supply is 15-25, so we can keep bids moderate.
    cap = DAILY_SALARY * 1.2
    target = min(target, cap)

    # If budget is extremely low, bid what we can
    if budget <= 1.0:
        return budget

    # Ensure non-negative
    if target < 0.0:
        target = 0.0

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
    day = day_context['day']

    # Identify alive opponents and inspect yesterday bids only
    alive_opps = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opps.append(opp)

    # If no opponents are alive, bid conservatively
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Estimate whether there is a strong bidding pressure (e.g., Cindy)
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = 0.0
    if len(yesterday_bids) >= 2:
        sorted_b = sorted(yesterday_bids, reverse=True)
        second_prev_bid = sorted_b[1]

    # Budget and HP heuristics
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    # Determine target bid: small edge over likely clearing price if pressure is high
    # But avoid overpaying since Cindy already spent huge and may be trying to lock supply.
    # If highest_prev_bid is very large, we try to undercut rather than match.
    if highest_prev_bid >= DAILY_SALARY * 1.2:
        # Underbid strategy: bid around a fraction of daily salary, but enough to compete.
        # Use second_prev_bid as a weak proxy for clearing.
        base = max(DAILY_SALARY * 0.35, second_prev_bid * 0.55)
        if hp <= 2:
            base *= 1.6
        elif hp <= 4:
            base *= 1.25
        # Also consider supply: if supply is near minimum, be slightly more aggressive.
        if supply <= float(MIN_SUPPLY) + 1.0:
            base *= 1.15
    elif highest_prev_bid >= DAILY_SALARY * 0.7:
        # Moderate pressure: bid near half daily salary or slightly above second-highest
        base = max(DAILY_SALARY * 0.5, second_prev_bid * 0.75)
        if hp <= 2:
            base *= 1.4
        elif hp <= 4:
            base *= 1.15
    else:
        # Low pressure: bid enough to ensure water without wasting budget
        base = DAILY_SALARY * 0.55
        if hp <= 2:
            base = DAILY_SALARY * 0.85
        elif hp <= 4:
            base = DAILY_SALARY * 0.7
        # If supply is low, increase slightly
        if supply <= float(MIN_SUPPLY) + 1.0:
            base *= 1.1

    # Convert base to a safe bid within budget; keep it integer-like but not required
    bid = float(min(budget, base))

    # Ensure non-negative
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = [o for o in opponents_status.values() if o.get('alive')]
    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace to infer who is bidding aggressively.
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', None)
        if isinstance(prev, dict):
            bid = prev.get('bid', None)
            if bid is not None:
                try:
                    prev_bids.append(float(bid))
                except Exception:
                    pass
        elif isinstance(prev, list) and prev:
            last = prev[-1]
            if isinstance(last, dict) and last.get('bid', None) is not None:
                try:
                    prev_bids.append(float(last['bid']))
                except Exception:
                    pass

    # Fallback if no trace.
    if not prev_bids:
        base = DAILY_SALARY * (0.6 if supply >= 20 else 0.45)
        return max(0.0, min(my_budget, base))

    highest_prev_bid = max(prev_bids)

    # Pressure estimate: Cindy-like behavior if someone consistently bid near salary.
    aggressive = highest_prev_bid >= DAILY_SALARY * 0.75

    # If we are in danger (low hp or already missing water), raise bid.
    danger = (my_hp <= 2.5) or (my_no_water_days >= 2)

    # Supply affects how likely we are to win enough water; higher supply means we can bid less.
    supply_factor = 0.0
    if supply >= 22:
        supply_factor = -0.05
    elif supply <= 17:
        supply_factor = 0.05
    else:
        supply_factor = 0.0

    if aggressive:
        # Try to outbid the leader slightly, but cap to avoid bankruptcy.
        target = highest_prev_bid + 1.0
        if supply >= 22:
            target -= 2.0
        if my_hp > 3 and not danger:
            target -= 5.0
        # If budget is tight, scale down.
        cap = my_budget if my_budget > 0 else 0.0
        bid = min(target, cap)
        # Ensure non-negative and at least some participation.
        return max(0.0, bid)

    # Not aggressive overall: bid enough to secure water when needed.
    if danger:
        bid = DAILY_SALARY * (0.85 + supply_factor)
    else:
        bid = DAILY_SALARY * (0.55 + supply_factor)

    # If supply is low, slightly increase.
    if supply < 18:
        bid += 10.0

    # Final budget cap.
    return max(0.0, min(my_budget, bid))
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

    # Alive opponents and yesterday bids
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', True):
            alive_opps.append(opp)

    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', None) or {}
        if prev.get('bid') is not None:
            yesterday_bids.append(float(prev['bid']))

    # Base target bid: aim to be competitive against the strongest yesterday bidder
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid
        pressure = 0.6 * highest_prev_bid + 0.4 * second_prev_bid
    else:
        pressure = 0.0

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))

    # Estimate how many
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

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))

    # Identify alive opponents and use only yesterday's immediate trace
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid', None)
            if bid is not None:
                alive_opps.append((opp_id, float(bid), prev))

    # Base bid depends on supply pressure
    # If supply is high, competition likely increases; if low, conserve.
    supply_frac = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_frac = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
        if supply_frac < 0.0:
            supply_frac = 0.0
        if supply_frac > 1.0:
            supply_frac = 1.0

    # Estimate opponent aggression from yesterday
    if alive_opps:
        prev_bids = [b for _, b, _ in alive_opps]
        highest_prev_bid = max(prev_bids)
        second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev_bid
    else:
        highest_prev_bid = 0.0
        second_prev_bid = 0.0

    # If my HP is critical, bid to secure water
    if hp <= 2.0:
        target = DAILY_SALARY * 0.9
    elif hp <= 4.0:
        target = DAILY_SALARY * 0.7
    else:
        # Otherwise, bid around a supply-dependent band.
        # Use yesterday's highest bid as a ceiling signal.
        band_low = DAILY_SALARY * (0.45 + 0.15 * supply_frac)
        band_high = DAILY_SALARY * (0.65 + 0.20 * supply_frac)
        target = (band_low + band_high) / 2.0

    # Exploit yesterday: if someone bid very high, we may need to slightly overtake.
    # Alex/Eric were ~76-83 with survival; Cindy died after lower survival, implying others may be inconsistent.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        target = max(target, highest_prev_bid + 2.0)
    elif highest_prev_bid >= DAILY_SALARY * 0.7:
        # Medium pressure: try to be near but not always above the top.
        target = max(target, min(highest_prev_bid + 1.0, second_prev_bid + 4.0))

    # Budget safety: never exceed budget; also avoid overspending late-ish days.
    # Episode is 10 days; day_context provides day.
    # Use a conservative spending cap that tightens as day increases.
    day_int = int(day) if day is not None else 0
    if day_int >= 9:
        cap = DAILY_SALARY * 0.5
    elif day_int >= 7:
        cap = DAILY_SALARY * 0.65
    else:
        cap = DAILY_SALARY * 0.85

    bid = min(budget, target, cap)

    # Ensure non-negative
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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 1))

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = [o for o in opponents_status.values() if bool(o.get('alive', False))]

    # If we are in danger, bid to secure water.
    if hp <= 2 or no_water_days >= 2:
        target = DAILY_SALARY * 0.95
        return max(0.0, min(budget, target))

    # Use only yesterday's previous_trace to infer pressure.
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        if prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # Estimate how contested it was yesterday.
    if prev_bids:
        highest = max(prev_bids)
        second = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest

        # If Cindy-like behavior (very high bids) likely continues, we bid just enough to stay in the game.
        if highest >= DAILY_SALARY * 0.85:
            # Keep bid moderate if we have decent hp; increase if our hp is dropping.
            pressure = 0.70 if hp >= 5 else 0.85
            # Also react to supply: if supply is near minimum, increase slightly.
            supply_factor = 0.08 if supply <= (MIN_SUPPLY + 1.0) else 0.0
            target = DAILY_SALARY * (pressure + supply_factor)
            # If yesterday's top bid was not far above our target, nudge upward.
            if highest - target > 15:
                target = min(DAILY_SALARY * 0.95, target + 10)
            return max(0.0, min(budget, target))

        # If bids were low, we can bid near a baseline to avoid wasting budget.
        baseline = DAILY_SALARY * 0.55
        # If we think others are conserving, bid slightly above second-highest.
        try:
            target = max(baseline, second + 2.0)
        except Exception:
            target = baseline
        # Supply scarcity: bid a bit more when supply is tight.
        if supply <= (MIN_SUPPLY + 2.0):
            target = max(target, DAILY_SALARY * 0.65)
        return max(0.0, min(budget, target))

    # No opponent bid info: choose a conservative mid bid.
    target = DAILY_SALARY * 0.58
    if supply <= (MIN_SUPPLY + 2.0):
        target = DAILY_SALARY * 0.68
    return max(0.0, min(budget, target))
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

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from immediate trace only
    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                yesterday_bids.append(float(bid))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Determine scarcity pressure from supply
    # If supply is just above our requirement, others likely compete harder.
    scarcity_ratio = (supply - float(MIN_SUPPLY)) / max(1e-9, float(MAX_SUPPLY - MIN_SUPPLY))
    # scarcity_ratio ~0 => low supply (15), ~1 => high supply (25)

    # Base bid: aim to secure water without overpaying.
    # When low supply, increase bid; when high supply, reduce.
    if supply <= float(WATER_REQ) + 6.0:  # around 15-16
        base = DAILY_SALARY * 0.75
    elif supply <= float(WATER_REQ) + 9.0:  # around 18-19
        base = DAILY_SALARY * 0.62
    else:
        base = DAILY_SALARY * 0.50

    # React to yesterday's highest bid: if they were bidding aggressively, we slightly overmatch.
    # Keep cap to avoid bankrupting.
    if highest_prev_bid > 0:
        # If highest_prev_bid was very high, we need to be closer to it.
        if highest_prev_bid >= DAILY_SALARY * 1.1:  # ~99
            target = max(base, highest_prev_bid * 0.98 + 2.0)
        else:
            target = max(base, highest_prev_bid * 0.85 + 5.0)
    else:
        target = base

    # Urgency adjustment from our hp and no-water streak
    if my_hp <= 2.0:
        target = max(target, DAILY_SALARY * 0.9)
    elif my_hp <= 4.0:
        target = max(target, DAILY_SALARY * 0.75)

    if my_no_water_days >= 2:
        target = max(target, DAILY_SALARY * 0.8)

    # Safety: never bid more than budget; also avoid extreme bids beyond what seems observed.
    # Cindy/Eric reached ~147-154; we keep a soft cap.
    soft_cap = min(my_budget, DAILY_SALARY * 1.75)  # 157.5
    bid = min(target, soft_cap)

    # If very low budget, go all-in proportionally
    if my_budget <= DAILY_SALARY * 0.35:
        bid = my_budget

    # Ensure non-negative
    if bid < 0.0:
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    if not alive:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Read yesterday bids from immediate previous_trace only
    prev_bids = []
    for oid, o in alive:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate how competitive the field was
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_highest_prev_bid = 0.0
    if len(prev_bids) >= 2:
        s = sorted(prev_bids, reverse=True)
        second_highest_prev_bid = s[1]

    # Supply pressure: with supply in [15,25], water units are roughly 1-2 per day.
    # If supply is closer to 15, competition is higher; if closer to 25, competition eases.
    supply_mid = (MIN_SUPPLY + MAX_SUPPLY) / 2.0
    supply_factor = 1.15 if supply <= supply_mid else 0.9

    # Urgency: if I'm low hp or have had no water days, bid more.
    urgency = 1.0
    if my_hp <= 2.0:
        urgency = 1.35
    elif my_hp <= 4.0:
        urgency = 1.15

    if my_no_water_days >= 2:
        urgency *= 1.25

    # If opponents previously bid very high, they likely were desperate.
    # Instead of matching exactly, slightly undercut to conserve budget.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        base = max(DAILY_SALARY * 0.25, highest_prev_bid * 0.72)
    elif highest_prev_bid >= DAILY_SALARY * 0.55:
        base = max(DAILY_SALARY * 0.35, highest_prev_bid * 0.6)
    else:
        # Low observed aggression: bid enough to capture water when possible.
        # Use second-highest as a soft ceiling to avoid overpaying.
        ceiling = second_highest_prev_bid if second_highest_prev_bid > 0 else (DAILY_SALARY * 0.7)
        base = min(DAILY_SALARY * 0.55, ceiling * 0.85)

    # Apply supply and urgency
    target = base * supply_factor * urgency

    # Budget safety: never bid more than what we can afford after reserving some survival buffer.
    # Reserve more when hp is low.
    reserve_frac = 0.35 if my_hp <= 3.0 else 0.2
    max_affordable = max(0.0, my_budget * (1.0 - reserve_frac))

    bid = min(max_affordable, target)

    # If my hp is extremely low, take a bolder move.
    if my_hp <= 1.0:
        bid = min(my_budget, max(bid, DAILY_SALARY * 0.9))

    # Clamp to non-negative
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
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read only yesterday's immediate trace bids
    prev_bids = []
    prev_by_opp = {}
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                bidf = float(bid)
                prev_bids.append(bidf)
                prev_by_opp[oid] = bidf
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate likely contention level from highest previous bid.
    # If someone bid near/above ~0.85*salary, assume strong pressure.
    pressure = 0.0
    if highest_prev_bid >= 0.85 * DAILY_SALARY:
        pressure = 1.0
    elif highest_prev_bid >= 0.6 * DAILY_SALARY:
        pressure = 0.7
    elif highest_prev_bid >= 0.4 * DAILY_SALARY:
        pressure = 0.4
    else:
        pressure = 0.2

    # Supply-based urgency: lower supply increases chance we lose water.
    supply_norm = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_norm = max(0.0, min(1.0, supply_norm))
    scarcity = 1.0 - supply_norm

    # If we're already in danger (low hp or many no-water days), bid more.
    danger = 0.0
    if hp <= 2.0:
        danger = 1.0
    elif hp <= 4.0:
        danger = 0.7
    elif no_water_days >= 2:
        danger = 0.6
    else:
        danger = 0.3

    # Base bid: aim to beat aggressive bids only when pressure is high.
    # Use a small increment over the observed highest previous bid when pressured.
    if pressure >= 0.9:
        target = min(budget, highest_prev_bid + 3.0)
    elif pressure >= 0.6:
        target = min(budget, max(highest_prev_bid * 0.85, 0.55 * DAILY_SALARY) + 2.0)
    else:
        target = min(budget, (0.45 + 0.2 * scarcity + 0.2 * danger) * DAILY_SALARY)

    # Safety caps: never spend more than a fraction when hp is comfortable.
    if hp >= 6.0 and danger < 0.6:
        target = min(target, 0.55 * DAILY_SALARY)
    elif hp >= 4.0 and danger < 0.8:
        target = min(target, 0.75 * DAILY_SALARY)

    # If danger is high, allow spending up to ~salary.
    if danger >= 0.8:
        target = min(budget, max(target, 0.85 * DAILY_SALARY))

    # Ensure non-negative and not exceeding budget.
    if target < 0.0:
        target = 0.0
    if target > budget:
        target = budget

    return float(target)
"""
