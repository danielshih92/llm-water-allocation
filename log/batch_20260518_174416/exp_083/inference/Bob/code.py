# ============================================================
# Experiment: exp_083
# Agent: Bob
# Source: exp_083
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
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opps.append(opp)

    # Baseline bid: aim for at least one unit of water requirement, scaled by supply.
    # Since bidding is simultaneous and hidden, use a conservative fraction of budget.
    budget = float(my_status['budget'])
    hp = float(my_status['hp'])
    no_water_days = int(my_status['no_water_days'])

    # Extract yesterday bids from previous_trace for immediate reaction.
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                prev_bids.append(float(bid))
            except Exception:
                pass

    # If opponents were aggressive yesterday, we counter.
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        # Aggression threshold relative to our daily salary.
        if highest_prev_bid >= 0.85 * DAILY_SALARY:
            # We must protect hp if low; otherwise still bid decisively but not all-in.
            if hp <= 2 or no_water_days >= 2:
                target = 0.95 * DAILY_SALARY
            else:
                target = 0.65 * DAILY_SALARY
        else:
            # Moderate response: slightly above their likely effective level.
            # Add a small premium to win ties.
            target = max(0.45 * DAILY_SALARY, highest_prev_bid + 5.0)
    else:
        # No signal: bid based on our condition.
        if hp <= 2 or no_water_days >= 2:
            target = 0.9 * DAILY_SALARY
        elif hp <= 3:
            target = 0.65 * DAILY_SALARY
        else:
            target = 0.55 * DAILY_SALARY

    # Adjust for current supply: lower supply -> more competitive -> bid higher.
    # Normalize supply into [0,1] between MIN_SUPPLY and MAX_SUPPLY.
    if MAX_SUPPLY != MIN_SUPPLY:
        norm = (supply - float(MIN_SUPPLY)) / (float(MAX_SUPPLY) - float(MIN_SUPPLY))
    else:
        norm = 0.5
    # When norm is low (scarce), increase bid.
    scarcity_factor = 1.0 + (0.5 * (1.0 - max(0.0, min(1.0, norm))))
    target *= scarcity_factor

    # Convert target into a final bid capped by budget.
    bid = min(budget, target)

    # Ensure bid is non-negative.
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

    supply = float(day_context['supply'])
    day = day_context['day']

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive.append((opp_id, opp))

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday's bids to infer who is willing/able to pay.
    prev_bids = []
    for _, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Pressure proxy: if any opponent bid very high yesterday, they likely needed water urgently.
    high_bid = max(prev_bids) if prev_bids else 0.0

    # Cash constraint proxy from yesterday: if an opponent's budget_after was near zero, they can't outbid much.
    # Use only previous_trace.
    cash_starved = 0
    for _, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        ba = prev.get('budget_after', None)
        hb = prev.get('hp_after', None)
        if ba is not None:
            try:
                if float(ba) <= 1.0:
                    cash_starved += 1
            except Exception:
                pass
        # If they already had low hp_after, they may bid aggressively again.
        if hb is not None:
            try:
                if float(hb) <= 2.0:
                    cash_starved += 0  # keep separate from cash
            except Exception:
                pass

    # Base bid depends on supply: lower supply => more competitive.
    # Map supply to a competitiveness factor in [0,1].
    if MAX_SUPPLY == MIN_SUPPLY:
        comp = 0.5
    else:
        comp = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    comp = max(0.0, min(1.0, comp))

    # Urgency: if we've gone multiple days without water or low hp, bid harder.
    urgency = 0.0
    if hp <= 2.0:
        urgency += 0.7
    elif hp <= 4.0:
        urgency += 0.4
    if no_water_days >= 2:
        urgency += 0.4
    elif no_water_days == 1:
        urgency += 0.2

    # Strategy: target just below the strongest yesterday bidder when opponents are cash-starved.
    # Otherwise bid moderately.
    target = DAILY_SALARY * (0.35 + 0.35 * comp + 0.25 * urgency)

    if high_bid > 0.0:
        # If someone bid very high yesterday, try to contest but not fully match unless we're urgent.
        if high_bid >= DAILY_SALARY * 0.85:
            if urgency >= 0.5:
                target = max(target, high_bid * 0.85)
            else:
                target = max(target, high_bid * 0.55)
        else:
            target = max(target, high_bid * (0.45 + 0.25 * comp))

    # If many opponents appear cash-starved, we can bid lower and still win.
    if cash_starved >= 2:
        target *= 0.85

    # Never exceed budget.
    bid = max(0.0, min(budget, target))

    # If budget is very small, bid all-in.
    if budget <= DAILY_SALARY * 0.1:
        bid = min(budget, DAILY_SALARY * 0.9)

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

    # Alive opponents
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append(o)

    # If no opponents, just ensure survival
    if not alive:
        return float(min(my_status['budget'], DAILY_SALARY * 0.6))

    # Use only yesterday immediate behavior (previous_trace)
    yesterday_bids = []
    yesterday_bids_by_opp = []
    for o in alive:
        prev = o.get('previous_trace', {})
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                b = float(bid)
                yesterday_bids.append(b)
                yesterday_bids_by_opp.append((b, o))
            except Exception:
                pass

    # Estimate opponent pressure from yesterday bids
    if yesterday_bids:
        max_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / float(len(yesterday_bids))
    else:
        max_prev_bid = 0.0
        avg_prev_bid = DAILY_SALARY

    # Determine supply pressure: higher supply reduces urgency to overbid
    # Convert to a rough water-units scale for our requirement.
    # Note: indices not used.
    supply_ratio = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)  # 0..1
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # If our HP is low, bid to secure water more strongly.
    hp = float(my_status['hp'])
    no_water_days = int(my_status['no_water_days'])
    budget = float(my_status['budget'])

    # Base bid targets
    # When supply is high, we can bid closer to average; when low, bid closer to max_prev.
    # Also react to yesterday's max pressure.
    pressure = 0.6 * supply_ratio + 0.4 * (1.0 - supply_ratio)  # keeps mid

    # If someone was extremely aggressive yesterday, we slightly overbid when our HP is at risk.
    risk_factor = 0.0
    if hp <= 2.0:
        risk_factor = 1.0
    elif hp <= 4.0:
        risk_factor = 0.7
    elif no_water_days >= 2:
        risk_factor = 0.6
    else:
        risk_factor = 0.3

    # Choose target bid
    if yesterday_bids:
        target = (avg_prev_bid * (0.55 + 0.25 * supply_ratio) + max_prev_bid * (0.45 - 0.25 * supply_ratio))
        # If our risk is high, lean toward max_prev_bid
        target = target * (1.0 - 0.25 * risk_factor) + max_prev_bid * (0.15 * risk_factor)
        # Ensure some minimum competitiveness
        target = max(target, DAILY_SALARY * 0.45)
    else:
        target = DAILY_SALARY * (0.5 + 0.2 * (1.0 - supply_ratio))

    # If opponents likely conserved budget (high budgets and long survival), avoid overpaying.
    # Use Cindy/Eric style: if many have large budgets, reduce a bit.
    high_budget_count = 0
    for o in alive:
        if float(o.get('budget', 0.0)) > 300.0:
            high_budget_count += 1
    if high_budget_count >= 2:
        target *= 0.93

    # If we are very low HP, push up; if HP is healthy, throttle.
    if hp <= 2.0:
        target *= 1.12
    elif hp >= 7.0:
        target *= 0.88

    # Never exceed budget; also cap to avoid bankruptcy.
    # Typical max bids observed ~205; keep reasonable cap.
    cap = min(budget, 220.0)
    bid = float(min(max(1.0, target), cap))

    return bid
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

    supply = day_context['supply']
    day = day_context['day']

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive'):
            alive_opps.append(o)

    # If no opponents alive, spend enough to secure water.
    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.6))

    # Read yesterday bids from immediate previous_trace.
    prev_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Establish a target band based on observed behavior.
    # Cindy averaged ~124 and max ~142; Alex avg ~118 and max ~145.
    # We aim to outbid Alex-ish but stay under Cindy-ish.
    base_target_low = 115.0
    base_target_high = 138.0

    # Compute a pressure signal: how many days without water I have.
    pressure = 0
    if my_no_water_days is not None:
        try:
            pressure = int(my_no_water_days)
        except Exception:
            pressure = 0

    # If my HP is critical or I've already missed water, increase bid.
    if my_hp <= 2 or pressure >= 2:
        target = base_target_high
    elif my_hp <= 3 or pressure == 1:
        target = (base_target_low + base_target_high) / 2.0
    else:
        target = base_target_low

    # If yesterday we saw a high bid, slightly overcut it when possible.
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        # If opponent(s) were bidding aggressively yesterday, we need a bit more.
        if highest_prev_bid >= 130.0:
            target = max(target, min(highest_prev_bid + 2.0, base_target_high))
        else:
            # Otherwise, ensure we beat the likely median clearing level.
            target = max(target, min(sorted(prev_bids)[len(prev_bids) // 2] + 2.0, base_target_high))

    # Convert target to a feasible bid given budget.
    # Also add a small supply-aware adjustment: higher supply should allow less aggressive bids.
    try:
        supply_val = float(supply)
    except Exception:
        supply_val = (MIN_SUPPLY + MAX_SUPPLY) / 2.0

    # When supply is near max, we can shade down slightly.
    if supply_val >= 22.0:
        target *= 0.96
    elif supply_val <= 17.0:
        target *= 1.03

    bid = float(target)

    # Never exceed budget; keep non-negative.
    if my_budget is None:
        return 0.0
    if my_budget <= 0:
        return 0.0

    if bid > my_budget:
        bid = my_budget

    # If budget is extremely low, bid just enough not to waste.
    if my_budget < DAILY_SALARY * 0.2:
        bid = min(my_budget, DAILY_SALARY * 0.15)

    # Final clamp.
    if bid < 0.0:
        bid = 0.0

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

    # Alive opponents only
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # If no opponents, just bid to cover our need safely
    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Use only yesterday's trace for immediate reaction
    yesterday_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(float(prev['bid']))

    # Estimate pressure from yesterday bids
    pressure = 0.0
    if yesterday_bids:
        pressure = max(yesterday_bids)

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Urgency increases if we've already gone without water
    urgency = 1.0
    if no_water_days >= 2:
        urgency = 1.6
    elif no_water_days == 1:
        urgency = 1.25

    # If supply is high, we can bid less; if low, bid more
    # Normalize supply in [0,1]
    if MAX_SUPPLY > MIN_SUPPLY:
        norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        norm = 0.5
    norm = max(0.0, min(1.0, float(norm)))

    # Base bid target: moderate to beat low bidders but avoid Cindy's heavy spending
    # If yesterday pressure was very high, we avoid overmatching unless our HP is critical.
    base = DAILY_SALARY * (0.35 + 0.25 * (1.0 - norm))  # higher when supply is low

    if pressure >= DAILY_SALARY * 1.2:
        # Cindy-like behavior: only overbid if we are in danger
        if hp <= 2.0 or no_water_days >= 2:
            base = DAILY_SALARY * 0.85
        elif hp <= 4.0:
            base = DAILY_SALARY * 0.6
        else:
            base = DAILY_SALARY * 0.45
    elif pressure >= DAILY_SALARY * 0.7:
        # medium pressure
        if hp <= 3.0:
            base = DAILY_SALARY * 0.75
        else:
            base = DAILY_SALARY * 0.55

    # Apply urgency and HP
    if hp <= 1.0:
        base = DAILY_SALARY * 0.95
    elif hp <= 2.0:
        base = max(base, DAILY_SALARY * 0.8)
    elif hp <= 4.0:
        base = max(base, DAILY_SALARY * 0.6)

    bid = base * urgency

    # Never bid more than budget
    bid = min(bid, budget)

    # If budget is too low, bid whatever remains but keep it non-negative
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

    supply = float(day_context['supply'])
    day = day_context['day']

    # Alive opponents
    alive_opps = []
    for k, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # If no opponents, bid just enough to get water
    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Read yesterday bids from previous_trace (immediate reaction)
    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', None) or {}
        if prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate scarcity: with supply in [15,25], water units per day roughly 1 or 2.
    # If supply is high, competition lowers; if low, competition increases.
    # Use a conservative target bid around a fraction of DAILY_SALARY.
    if supply <= (MIN_SUPPLY + 0.5):
        scarcity_level = 1.0
    elif supply >= (MAX_SUPPLY - 0.5):
        scarcity_level = 0.3
    else:
        # linear between
        scarcity_level = 1.0 - 0.7 * ((supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY))

    # My urgency based on hp and no_water_days
    hp = float(my_status.get('hp', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # If I'm at risk, bid more aggressively.
    urgent = (hp <= 3.0) or (no_water_days >= 1)

    # If yesterday saw very high bids, others may be competing hard today.
    # Use highest_prev_bid as a proxy for their pressure.
    pressure = 0.0
    if highest_prev_bid >= DAILY_SALARY * 1.25:
        pressure = 1.0
    elif highest_prev_bid >= DAILY_SALARY * 0.9:
        pressure = 0.6
    elif highest_prev_bid >= DAILY_SALARY * 0.6:
        pressure = 0.3

    # Base bid target
    base = DAILY_SALARY * (0.35 + 0.35 * scarcity_level)

    # Adjust for urgency and pressure
    if urgent:
        base *= 1.55
    base *= (1.0 + 0.35 * pressure)

    # Ensure we don't overbid beyond what budget allows
    bid = min(my_status['budget'], base)

    # If yesterday pressure was extreme, slightly top up to beat likely bids, but cap.
    if highest_prev_bid > 0:
        target = min(my_status['budget'], max(bid, highest_prev_bid * (0.75 if not urgent else 0.95) + 2.0))
        bid = target

    # Final safety bounds: keep at least small positive if budget allows
    if my_status['budget'] <= 0:
        return 0.0
    if bid <= 0:
        return min(my_status['budget'], 1.0)
    return float(bid)
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    alive_opps = []
    for k, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((k, o))

    # If no opponents alive, bid conservatively
    if not alive_opps:
        return max(0.0, min(float(my_status['budget']), DAILY_SALARY * 0.4))

    # Read yesterday bids (immediate reaction)
    yesterday_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                yesterday_bids.append(float(bid))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Supply pressure: less supply => more aggressive bidding to secure WATER_REQ
    # Map supply in [15,25] to pressure in [1.0,0.6]
    if MAX_SUPPLY == MIN_SUPPLY:
        pressure = 1.0
    else:
        pressure = 1.0 - 0.4 * ((supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY))
        if pressure < 0.6:
            pressure = 0.6
        if pressure > 1.0:
            pressure = 1.0

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status.get('no_water_days', 0))

    # Critical HP: bid to avoid death
    if hp <= 2 or no_water_days >= 2:
        # Avoid overpaying; target near (but not equal to) their highest bids
        target = 0.85 * highest_prev_bid if highest_prev_bid > 0 else DAILY_SALARY * 0.9
        # Also scale by pressure
        target *= pressure
        bid = min(budget, max(DAILY_SALARY * 0.7, target))
        return max(0.0, bid)

    # Non-critical: bid moderately; if others were very high, slightly shadow them
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # They likely expect competition; bid enough to win when supply is tight
        bid = DAILY_SALARY * 0.55 * pressure
        # If their highest is far above, don't fully match; cap below their peak
        if highest_prev_bid > 0:
            bid = min(bid, highest_prev_bid * 0.75)
    else:
        # Their bids are moderate; we can be cheaper
        bid = DAILY_SALARY * 0.45 * pressure

    # Ensure we don't exceed budget
    bid = min(budget, bid)

    # Small day-based adjustment to avoid ties late (10-day episode)
    # Later days: slightly more aggressive
    if day >= 7:
        bid *= 1.08

    # Final clamp
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

    my_hp = int(my_status['hp'])
    my_budget = float(my_status['budget'])

    # Identify alive opponents and read yesterday's bid only (immediate reaction)
    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            prev = opp.get('previous_trace', {}) or {}
            if prev.get('bid') is not None:
                alive.append((opp_id, float(prev.get('bid', 0.0)), prev))

    # If no info, bid conservatively based on hp
    if not alive:
        if my_hp <= 2:
            target = DAILY_SALARY * 0.75
        else:
            target = DAILY_SALARY * 0.55
        return float(min(my_budget, max(0.0, target)))

    # Use yesterday's highest bid as an estimate of Cindy-like aggressive pressure
    highest_prev_bid = max(b for _, b, _ in alive)

    # Supply pressure: when supply is higher, we can afford to contest slightly less
    # Normalize supply to [0,1]
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_norm = 0.5
    supply_norm = max(0.0, min(1.0, float(supply_norm)))

    # Base target: try to outbid the leader modestly, but cap to avoid budget starvation
    # If opponent bids were very high, we must respond more to secure enough water for survival.
    if highest_prev_bid >= DAILY_SALARY * 0.75:
        if my_hp <= 2:
            target = DAILY_SALARY * (0.95 - 0.15 * supply_norm)
        else:
            target = min(highest_prev_bid + 2.0, DAILY_SALARY * (0.70 - 0.05 * supply_norm) + 0.25 * highest_prev_bid)
    else:
        # Mid/low pressure: bid enough to stay competitive against a potential swing.
        if my_hp <= 2:
            target = DAILY_SALARY * (0.70 - 0.10 * supply_norm)
        else:
            # Slightly above what mid bidders likely use
            target = max(DAILY_SALARY * 0.45, highest_prev_bid + 1.5)
            target = min(target, DAILY_SALARY * (0.65 - 0.05 * supply_norm) + 0.2 * highest_prev_bid)

    # Ensure we don't overpay when budget is tight
    # Also ensure at least some bid unless budget is extremely low
    if my_budget <= 0.0:
        return 0.0

    # If my budget is low relative to target, scale down but keep competitiveness when hp is critical
    if target > my_budget:
        if my_hp <= 2:
            target = my_budget * 0.95
        else:
            target = my_budget * 0.65

    # Final clamp
    target = float(max(0.0, target))
    return float(min(my_budget, target))
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

    supply = day_context['supply']
    day = day_context['day']

    # Alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # If no one else is alive, bid conservatively
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday traces to estimate pressure
    prev_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else 0.0

    # Our urgency: if low HP or already in no-water streak, increase bid
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Supply pressure: higher supply means we can win cheaper
    # (assume price correlates with competition rather than supply, but adjust slightly)
    supply_mid = (MIN_SUPPLY + MAX_SUPPLY) / 2.0
    supply_factor = 0.95 if supply >= supply_mid else 1.05

    # Base target: try to be around the median-ish previous pressure, but not overpay.
    # If Cindy-style pressure was extremely high, do not fully match; bid just enough to beat likely ties.
    if highest_prev_bid >= DAILY_SALARY * 1.25:
        # Cindy was aggressive; we undercut slightly
        target = max(DAILY_SALARY * 0.75, second_prev_bid + 2.0)
    elif highest_prev_bid >= DAILY_SALARY * 0.85:
        target = max(DAILY_SALARY * 0.6, highest_prev_bid * 0.85)
    else:
        target = max(DAILY_SALARY * 0.5, highest_prev_bid * 0.7)

    # Urgency adjustments
    if hp <= 2.0:
        target *= 1.25
    elif hp <= 4.0:
        target *= 1.10

    if no_water_days >= 2:
        target *= 1.15
    if no_water_days >= 4:
        target *= 1.30

    # Day-based slight escalation near end (episode_days inferred from environment not provided; use day number)
    if day >= 8:
        target *= 1.08

    # Cap by budget and keep within a reasonable range
    target *= supply_factor
    bid = min(budget, target)

    # Ensure non-negative and at least small bid if budget allows
    if bid < 0.0:
        bid = 0.0
    if bid == 0.0 and budget > 0.0:
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = day_context['supply']
    day = day_context['day']

    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water_days = my_status['no_water_days']

    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    if not alive:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Extract yesterday bids for alive opponents
    yesterday_bids = []
    for oid, o in alive:
        prev = o.get('previous_trace', {})
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                yesterday_bids.append(float(bid))
            except Exception:
                pass

    # Pressure estimate from yesterday
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        second_prev = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid
    else:
        highest_prev_bid = 0.0
        second_prev = 0.0

    # Supply-based aggressiveness: higher supply -> can bid lower; lower supply -> bid higher
    # Use a conservative mapping for medium scenario.
    supply_norm = (float(supply) - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY + 1e-9)
    supply_norm = max(0.0, min(1.0, supply_norm))
    # When supply is low, we raise bids.
    supply_factor = 0.95 - 0.25 * supply_norm  # ~0.95 at low supply, ~0.70 at high

    # Our urgency
    urgency = 0.0
    if my_hp <= 2:
        urgency += 1.0
    if my_hp <= 3:
        urgency += 0.5
    if my_no_water_days >= 2:
        urgency += 0.7
    if my_no_water_days >= 3:
        urgency += 0.8

    # If others were bidding very high yesterday, we need to match a bit below the leader.
    # If not, bid around a baseline to secure water.
    baseline = DAILY_SALARY * 0.55

    # Leader-following target
    target = baseline
    if highest_prev_bid > 0:
        # If the leader bid was near/exceeding 0.85 salary, we must be competitive.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            target = min(DAILY_SALARY * 0.95, highest_prev_bid * 0.92)
        elif highest_prev_bid >= DAILY_SALARY * 0.55:
            # Moderate competition: bid slightly above second-highest to beat most.
            target = max(baseline, second_prev * 1.05, highest_prev_bid * 0.75)
        else:
            target = max(baseline * 0.85, highest_prev_bid + 1.5)

    # Apply urgency and supply factor
    target *= supply_factor
    target *= (1.0 + 0.35 * urgency)

    # Budget guardrails
    # Ensure we don't bid too low when we are in danger.
    min_bid_when_urgent = DAILY_SALARY * (0.75 if urgency >= 1.0 else 0.55)
    if urgency >= 1.0:
        target = max(target, min_bid_when_urgent)

    # Final cap by budget
    bid = min(my_budget, target)

    # If budget is extremely low, bid what we can.
    if my_budget <= 1e-9:
        return 0.0

    # Avoid negative
    if bid < 0.0:
        bid = 0.0

    return float(bid)
"""
