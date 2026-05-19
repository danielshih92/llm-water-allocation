# ============================================================
# Experiment: exp_076
# Agent: Bob
# Source: exp_076
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

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))

    alive_opponents = []
    for opp_id, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append((opp_id, o))

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Extract yesterday bids for immediate reaction
    prev_bids = []
    for _, o in alive_opponents:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Supply pressure factor: closer to min supply -> higher chance of competition
    # Use safe index-free math; only indices would need int() (none used).
    supply_mid = (MAX_SUPPLY + MIN_SUPPLY) / 2.0
    competition = 0.55
    if supply <= supply_mid:
        competition = 0.75
    elif supply >= MAX_SUPPLY:
        competition = 0.5

    aggressive_threshold = DAILY_SALARY * 0.85

    # Baseline bid: aim for at least one unit of water requirement share, scaled by competition
    # We cannot directly buy water; bid is the proxy.
    base_bid = DAILY_SALARY * (0.45 + 0.25 * competition)

    if prev_bids:
        highest_prev_bid = max(prev_bids)
        # If someone was aggressive yesterday, we counter just enough.
        if highest_prev_bid >= aggressive_threshold:
            # If our hp is low, we must secure water more strongly.
            if my_hp <= 2:
                bid = DAILY_SALARY * 0.95
            elif my_hp <= 4:
                bid = DAILY_SALARY * 0.75
            else:
                bid = DAILY_SALARY * 0.62
            # Outbid slightly to beat their likely continuation, but cap by our budget.
            bid = max(bid, highest_prev_bid + 1.0)
        else:
            # If they weren't aggressive, don't overpay; bid near base, slightly above their max.
            bid = max(base_bid, highest_prev_bid + 0.5)
    else:
        bid = base_bid

    # Final risk controls
    # If our hp is critical, push harder; otherwise conserve.
    if my_hp <= 1:
        bid = max(bid, DAILY_SALARY * 0.9)
    elif my_hp <= 3:
        bid = max(bid, DAILY_SALARY * 0.7)
    else:
        # If we have plenty of hp, avoid unnecessary escalation late in episode.
        if day >= 7:
            bid = min(bid, DAILY_SALARY * 0.6)

    # Budget cap
    if my_budget <= 0:
        return 0.0
    if bid > my_budget:
        bid = my_budget

    # Ensure non-negative
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
    day = int(day_context['day'])

    # Basic safety: if we're critically low, prioritize survival
    if my_status['hp'] <= 2:
        return float(min(my_status['budget'], DAILY_SALARY * 0.95))

    alive_opps = [o for o in opponents_status.values() if o.get('alive')]
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.45))

    # Read yesterday bids for immediate reaction (only previous_trace)
    prev_bids = []
    prev_hp_after = []
    for opp in alive_opps:
        pt = opp.get('previous_trace', {})
        if pt and pt.get('bid') is not None:
            prev_bids.append(float(pt['bid']))
            prev_hp_after.append(int(pt.get('hp_after', opp.get('hp', 0))))

    # Estimate aggressiveness from yesterday
    if prev_bids:
        max_prev = max(prev_bids)
        med_prev = sorted(prev_bids)[len(prev_bids)//2]
    else:
        max_prev = 0.0
        med_prev = DAILY_SALARY * 0.5

    # Convert supply into a rough need pressure: higher supply means less need to overbid
    supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0..1
    supply_norm = max(0.0, min(1.0, supply_norm))

    # Target bid: beat low/moderate bidders but avoid matching top aggressors
    # If others were bidding very high yesterday, slightly undercut them.
    if max_prev >= DAILY_SALARY * 0.85:
        # We assume top bidder is contesting; choose a bid around median + small premium
        target = med_prev + 2.0
        # Underbid cap to avoid spiraling
        cap = min(my_status['budget'], max_prev - 4.0)
        target = min(target, cap)
    else:
        # General case: bid enough to secure when hp is decent
        target = max(DAILY_SALARY * (0.45 + 0.15 * supply_norm), med_prev * 0.9)

    # Adjust based on our no_water_days (more days -> higher bid)
    no_water_days = int(my_status.get('no_water_days', 0))
    if no_water_days >= 2:
        target *= 1.15
    if no_water_days >= 4:
        target *= 1.35

    # If we're already doing well, avoid overspending
    if my_status.get('hp', 0) >= 7:
        target *= 0.95

    # Final clamp
    target = float(max(0.0, target))
    return float(min(my_status['budget'], target))
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

    my_hp = int(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids to infer aggressiveness/pressure
    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / float(len(yesterday_bids))
    else:
        highest_prev_bid = 0.0
        avg_prev_bid = 0.0

    # Supply pressure: if supply barely covers one requirement, expect bidding wars
    # supply is between 15 and 25; with WATER_REQ=9, 15~1 unit, 18~2 units, 25~2 units.
    if supply < (WATER_REQ * 2):
        supply_tight = True
    else:
        supply_tight = False

    # Base bid: aim to be competitive but not top out at extreme bids.
    # Scale with my HP and no-water streak.
    hp_factor = 1.0
    if my_hp <= 1:
        hp_factor = 1.35
    elif my_hp == 2:
        hp_factor = 1.2
    elif my_hp == 3:
        hp_factor = 1.1

    streak_factor = 1.0
    if my_no_water_days >= 2:
        streak_factor = 1.25
    elif my_no_water_days == 1:
        streak_factor = 1.1

    # Opponent aggressiveness: if their highest bid is very high relative to salary, avoid mirroring fully.
    aggressiveness = 0.0
    if highest_prev_bid > 0.0:
        aggressiveness = min(1.0, highest_prev_bid / (DAILY_SALARY * 1.6))

    # Choose target bid level.
    # If supply tight, increase more; if not, keep moderate.
    if supply_tight:
        base = DAILY_SALARY * (0.62 + 0.25 * aggressiveness)
    else:
        base = DAILY_SALARY * (0.48 + 0.18 * aggressiveness)

    # If yesterday average was already high, slightly raise to avoid being outbid.
    if avg_prev_bid > DAILY_SALARY * 1.2:
        base *= 1.08

    bid = base * hp_factor * streak_factor

    # If my HP is critical, push closer to salary cap.
    if my_hp <= 1:
        bid = max(bid, DAILY_SALARY * 0.85)

    # Budget safety and non-negativity
    bid = max(0.0, min(my_budget, bid))

    # If budget is too low, still bid what we can.
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

    supply = day_context['supply']
    day = day_context['day']

    # If critically low hp, prioritize survival regardless of opponents.
    if my_status['hp'] <= 2:
        return min(my_status['budget'], DAILY_SALARY * 0.95)

    # Collect yesterday bids from alive opponents.
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)

    highest_prev_bid = 0.0
    cindy_prev_bid = None
    alex_prev_bid = None

    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            b = float(prev['bid'])
            if b > highest_prev_bid:
                highest_prev_bid = b
            oid = opp.get('agent_id', None)
            # agent_id may not be present inside opp; try to infer via dict key
            # We'll instead match by previous_trace length? Not possible.
            # So also check external key by scanning again.

    # Second pass to identify Cindy/Alex by key (safer).
    for opp_id, opp in opponents_status.items():
        if not opp.get('alive'):
            continue
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            b = float(prev['bid'])
            if opp_id == 'Cindy':
                cindy_prev_bid = b
            if opp_id == 'Alex':
                alex_prev_bid = b

    # Base bid: aim around half salary when supply is healthy.
    # If supply is low (near MIN_SUPPLY), increase to contest.
    supply_ratio = (float(supply) - float(MIN_SUPPLY)) / (float(MAX_SUPPLY) - float(MIN_SUPPLY) + 1e-9)
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    base = DAILY_SALARY * (0.40 + 0.25 * supply_ratio)  # ~36 to 63

    # If Cindy or Alex bid high yesterday, expect competitive pressure today.
    pressure = 0.0
    if cindy_prev_bid is not None:
        if cindy_prev_bid >= DAILY_SALARY * 1.2:
            pressure += 0.35
        elif cindy_prev_bid >= DAILY_SALARY * 0.9:
            pressure += 0.20
    if alex_prev_bid is not None:
        if alex_prev_bid >= DAILY_SALARY * 1.0:
            pressure += 0.20
        elif alex_prev_bid >= DAILY_SALARY * 0.7:
            pressure += 0.10

    # Also use overall highest bid as a proxy.
    if highest_prev_bid >= DAILY_SALARY * 1.3:
        pressure += 0.25
    elif highest_prev_bid >= DAILY_SALARY * 0.9:
        pressure += 0.15

    # Convert pressure into bid multiplier.
    bid = base * (1.0 + pressure)

    # If budget is tight, scale down but keep some contesting when pressure is high.
    if my_status['budget'] < DAILY_SALARY:
        # Keep at least a fraction; higher pressure => higher fraction.
        min_frac = 0.55 if pressure >= 0.35 else 0.45
        bid = min(bid, my_status['budget'] * min_frac + my_status['budget'] * (1.0 - min_frac) * 0.5)

    # Ensure bid is within budget.
    bid = min(float(my_status['budget']), float(bid))

    # Hard floor: if bid becomes too low, raise slightly to avoid losing all water.
    if bid < DAILY_SALARY * 0.25:
        bid = min(float(my_status['budget']), DAILY_SALARY * 0.25)

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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Immediate reaction from yesterday's bid (only previous_trace)
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

    # Estimate how many units water might be available (heuristic)
    # Use int() to avoid float indices issues (even though we don't index lists here).
    approx_units = int(supply / float(WATER_REQ)) if WATER_REQ > 0 else 0
    if approx_units < 1:
        approx_units = 1

    # Base bid level: aim between Eric-like pressure and Alex-like restraint.
    # If opponent previously went very high, we slightly undercut to avoid overpaying.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # High-stakes day: bid moderately if healthy, aggressively if low hp.
        if my_hp > 3.0 and my_no_water_days <= 1:
            target = DAILY_SALARY * 0.35
        else:
            target = DAILY_SALARY * 0.75
    else:
        # Lower pressure: bid enough to secure, but avoid wasting budget.
        if my_hp <= 2.0 or my_no_water_days >= 2:
            target = DAILY_SALARY * 0.8
        else:
            # Scale with supply: if supply is scarce relative to requirement, bid more.
            scarcity = (float(MAX_SUPPLY) - supply) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
            target = DAILY_SALARY * (0.48 + 0.22 * scarcity)

    # Undercut vs previous highest bid to win at lower cost.
    # Keep it bounded and not too low.
    if highest_prev_bid > 0.0:
        target = min(target, highest_prev_bid - 1.0)
        # If undercut becomes too small, clamp to a reasonable floor.
        floor_bid = DAILY_SALARY * 0.28
        if target < floor_bid:
            target = floor_bid

    # Convert to final bid with safety caps.
    # Never bid more than budget.
    bid = max(0.0, min(my_budget, float(target)))

    # If we are in danger, ensure we bid closer to salary.
    if my_hp <= 1.5 or my_no_water_days >= 3:
        bid = max(bid, min(my_budget, DAILY_SALARY * 0.92))

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
    day = int(day_context['day'])

    # Identify alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # If no opponents alive, spend enough to secure survival
    if not alive_opps:
        target = DAILY_SALARY * 0.4
        return float(min(my_status['budget'], target))

    # Read yesterday bids from previous_trace
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', None)
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    prev_bids.append(float(b))
                except Exception:
                    pass

    # Fallback if trace missing
    if not prev_bids:
        # Conservative mid bid
        base = DAILY_SALARY * 0.55
    else:
        # Use distribution to choose a competitive threshold
        prev_sorted = sorted(prev_bids)
        # Use median-ish to avoid overpaying
        mid_idx = int(len(prev_sorted) // 2)
        mid_bid = float(prev_sorted[mid_idx])
        # Also look at max to detect panic bidding
        max_prev = float(prev_sorted[-1])

        # If someone bid very high yesterday, assume they were fighting for survival.
        # We slightly undercut the median/max region.
        if max_prev >= DAILY_SALARY * 1.7:  # ~153
            base = min(DAILY_SALARY * 1.25, mid_bid + 5.0)
        else:
            base = max(DAILY_SALARY * 0.5, mid_bid - 5.0)

    # Scale with our urgency
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Urgency factor: if low hp or close to running out, bid more.
    urgency = 0.0
    if hp <= 2.0:
        urgency = 1.0
    elif hp <= 4.0:
        urgency = 0.75
    elif hp <= 6.0:
        urgency = 0.5
    else:
        urgency = 0.35

    # If we have few no-water days left, increase urgency.
    if no_water_days <= 1:
        urgency = max(urgency, 0.9)
    elif no_water_days <= 3:
        urgency = max(urgency, 0.6)

    # Supply-based adjustment: higher supply reduces need to overbid.
    # Normalize supply within [MIN_SUPPLY, MAX_SUPPLY]
    s_norm = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        s_norm = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    if s_norm < 0.0:
        s_norm = 0.0
    if s_norm > 1.0:
        s_norm = 1.0

    # If supply is low, bid higher; if high, bid lower.
    supply_factor = 1.15 - 0.25 * s_norm

    bid = base * supply_factor
    bid = bid * (0.75 + 0.5 * urgency)

    # Ensure we don't exceed budget; also keep within reasonable daily spend bounds.
    # Since salary is the natural scale, cap at ~1.6*DAILY_SALARY.
    cap = DAILY_SALARY * 1.6
    bid = float(min(bid, cap))

    # If budget is very low, bid what we can.
    if budget <= 0.0:
        return 0.0

    # Final clamp
    bid = float(min(bid, budget))

    # Avoid bidding trivially when we still need water
    if my_status['hp'] > 0 and bid < DAILY_SALARY * 0.25:
        bid = float(min(budget, DAILY_SALARY * 0.25))

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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from immediate previous_trace
    prev_bids = []
    prev_hp_after = []
    for opp_id, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid', 0.0)))
                prev_hp_after.append(float(prev.get('hp_after', 0.0)))
            except Exception:
                pass

    # If we have no bid info, default to a conservative mid bid
    if not prev_bids:
        base = DAILY_SALARY * 0.55
    else:
        highest_prev_bid = max(prev_bids)
        second_prev = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev_bid

        # If someone was willing to overpay (Alex-like), we don't match blindly.
        # We instead aim to slightly exceed the second-highest pressure.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            base = max(second_prev + 1.5, DAILY_SALARY * 0.45)
        else:
            base = max(highest_prev_bid + 1.0, DAILY_SALARY * 0.5)

    # Scale by supply: higher supply reduces need to overbid
    # Expected water share depends on supply; we approximate urgency by how many WATER_REQ units exist.
    units = supply / float(WATER_REQ)
    if units <= 1.2:
        supply_factor = 1.15
    elif units <= 1.8:
        supply_factor = 1.05
    else:
        supply_factor = 0.95

    # Urgency by our HP and streak without water
    if hp <= 2 or no_water_days >= 2:
        urgency_factor = 1.25
    elif hp <= 4:
        urgency_factor = 1.10
    else:
        urgency_factor = 0.95

    # Keep bid within budget and a reasonable fraction of daily salary
    target = base * supply_factor * urgency_factor
    cap = DAILY_SALARY * 0.75

    bid = max(0.0, min(budget, min(target, cap)))

    # If budget is tiny, bid whatever we can
    if budget <= 1.0:
        return max(0.0, budget)

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

    supply = day_context.get('supply', MIN_SUPPLY)
    day = day_context.get('day', 0)

    # Identify alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # Base bid targets: aim to win enough water cheaply unless I'm in danger
    # Convert supply to an approximate number of water units being contested
    # (We don't know exact allocation mechanics; we use supply to scale aggressiveness.)
    supply_int = int(round(supply))
    # Heuristic: higher supply => lower need to bid aggressively
    supply_factor = 1.0
    if supply_int <= MIN_SUPPLY:
        supply_factor = 1.15
    elif supply_int >= MAX_SUPPLY:
        supply_factor = 0.85

    # Read yesterday bids to infer who tends to overbid
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate pressure from yesterday: if someone bid very high, they likely try to secure water
    # Use that to avoid being outbid when I'm also vulnerable.
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # If I'm low HP, bid closer to the likely winning range.
    hp = my_status.get('hp', 0)
    budget = my_status.get('budget', 0)

    # Conservative cap: never bid more than a fraction of budget.
    # But ensure enough to compete.
    budget_cap = budget

    # Strategy tiers
    if hp <= 1:
        # Critical: bid aggressively but not maximal
        target = DAILY_SALARY * 0.85
    elif hp <= 3:
        # Urgent: bid moderately high if others overbid yesterday
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            target = DAILY_SALARY * 0.70
        else:
            target = DAILY_SALARY * 0.55
    else:
        # Healthy: bid only enough to likely secure water
        if highest_prev_bid >= DAILY_SALARY * 1.20:
            # Someone is very aggressive; slightly increase to avoid being starved
            target = DAILY_SALARY * 0.60
        else:
            target = DAILY_SALARY * 0.45

    # Scale by supply conditions
    target *= supply_factor

    # If yesterday highest bid was extremely high, try to undercut slightly
    if highest_prev_bid > 0:
        if highest_prev_bid >= DAILY_SALARY * 1.00:
            target = min(target, highest_prev_bid * 0.85)

    # Final bid with budget constraints
    bid = target
    if bid > budget_cap:
        bid = budget_cap

    # Ensure non-negative
    if bid < 0:
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = day_context['supply']
    day = day_context['day']

    alive_opps = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Immediate reaction from yesterday traces
    prev_bids = []
    prev_hp = {}
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            prev_bids.append(float(bid))
        prev_hp[opp.get('agent_id', None)] = prev.get('hp_after', None)

    # If any opponent previously bid high, assume they will keep pressure; match just below to win consistently.
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev_bid

    # Estimate how many water units are effectively contested.
    # Supply is total available; each unit corresponds to WATER_REQ water.
    units = int(supply / float(WATER_REQ))
    units = max(1, min(units, int(MAX_SUPPLY / float(WATER_REQ))))

    # Determine urgency from our HP and no-water days.
    hp = float(my_status['hp'])
    no_water_days = int(my_status['no_water_days'])
    budget = float(my_status['budget'])

    # Base aggressiveness: secure water when we're near danger or early in episode.
    if hp <= 2 or no_water_days >= 2:
        base = 0.9 * DAILY_SALARY
    elif day <= 3:
        base = 0.7 * DAILY_SALARY
    else:
        base = 0.55 * DAILY_SALARY

    # If someone previously bid very low (likely collapsed opponents), we can undercut slightly.
    # But since we don't see current bids, we still target the likely winning band.
    # Use highest_prev_bid as a proxy for the competitive threshold.
    threshold = highest_prev_bid

    # If highest_prev_bid is already high, bid close to it; otherwise, bid enough to beat low-bidders.
    if threshold >= 0.75 * DAILY_SALARY:
        bid = min(budget, max(base, threshold * 0.98))
    else:
        # Aim to beat the top previous bidder by a small margin.
        bid = min(budget, max(base, threshold + 5.0))

    # Budget safety: avoid spending beyond what allows multiple days.
    # Since each day costs at most our bid, cap by remaining budget horizon.
    horizon = 10
    cap = budget / float(max(1, horizon - int(day)))
    bid = min(bid, cap)

    # Ensure non-negative integer-ish float
    if bid < 0:
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Identify alive opponents and extract yesterday bids
    alive = []
    for opp_id, opp in opponents_status.items():
        if bool(opp.get('alive', False)):
            prev = opp.get('previous_trace', {}) or {}
            bid = prev.get('bid', None)
            if bid is not None:
                alive.append((opp_id, float(bid), prev))

    # If no info, use a conservative baseline
    if not alive:
        base = DAILY_SALARY * (0.75 if hp <= 2 else 0.55)
        return max(0.0, min(budget, base))

    # Use yesterday behavior: detect whether someone overpaid aggressively
    bids = [b for _, b, _ in alive]
    highest_prev_bid = max(bids)
    second_prev_bid = sorted(bids)[-2] if len(bids) >= 2 else highest_prev_bid

    # Estimate how many
"""
