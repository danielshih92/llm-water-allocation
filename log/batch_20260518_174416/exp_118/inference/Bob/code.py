# ============================================================
# Experiment: exp_118
# Agent: Bob
# Source: exp_118
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

    supply = day_context['supply']
    day = day_context['day']

    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((opp_id, opp))

    # Baseline: value water highly, but avoid reckless overspending.
    # We target a bid that would typically secure enough water for our requirement.
    # Since supply is shared, bidding around our requirement is reasonable.
    base_target = min(my_status['budget'], DAILY_SALARY * 0.55)

    # React to yesterday's observed bids.
    prev_bids = []
    for _, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            prev_bids.append(float(b))

    # Compute a pressure signal.
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        lowest_prev_bid = min(prev_bids)

        # If someone bid very aggressively yesterday, we match pressure but not fully.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # If our hp is low, we must spend more.
            if my_status.get('hp', 0) <= 2:
                bid = min(my_status['budget'], DAILY_SALARY * 0.95)
            elif my_status.get('hp', 0) <= 3:
                bid = min(my_status['budget'], DAILY_SALARY * 0.75)
            else:
                bid = min(my_status['budget'], DAILY_SALARY * 0.65)
            return max(0.0, float(bid))

        # If bids were moderate, bid slightly above the median/low to secure water.
        if highest_prev_bid >= DAILY_SALARY * 0.55:
            # Use a small bump over the observed low to avoid getting outbid.
            bid = lowest_prev_bid + 5.0
            # Keep within budget and avoid extreme spending.
            bid = min(bid, my_status['budget'], DAILY_SALARY * 0.7)
            return max(0.0, float(bid))

        # If everyone was conservative yesterday, we can take water with a controlled bid.
        # Ensure we still stay meaningful relative to our need.
        bid = max(base_target, lowest_prev_bid + 2.0)
        bid = min(bid, my_status['budget'], DAILY_SALARY * 0.6)
        return max(0.0, float(bid))

    # No opponent trace bids available: decide based on our health and no-water days.
    hp = my_status.get('hp', 0)
    no_water_days = my_status.get('no_water_days', 0)

    # If we're near starvation, spend to avoid further no-water days.
    if hp <= 2 or no_water_days >= 2:
        return max(0.0, float(min(my_status['budget'], DAILY_SALARY * 0.9)))

    # Otherwise, bid moderately.
    return max(0.0, float(min(my_status['budget'], base_target)))
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Alive opponents
    alive_ids = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_ids.append(oid)

    if not alive_ids:
        # Conservative when alone
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids and outcomes (immediate reaction)
    prev_bids = []
    prev_pressures = []
    for oid in alive_ids:
        prev = opponents_status[oid].get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    prev_bids.append(float(b))
                except Exception:
                    pass
            # pressure proxy: if they died yesterday, treat as high desperation signal
            if opponents_status[oid].get('hp', 0) < 0 or prev.get('hp_after', 0) is not None:
                # if yesterday led to death, they likely over/under bid; use their last bid as signal
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    # Cindy/Eric survived with ~83 average; use that as a contested benchmark
    contest_threshold = DAILY_SALARY * 0.92  # 82.8

    # Supply pressure: how many full requirements fit in total supply
    # If supply is scarce relative to water requirement, bidding competition increases.
    # Use ratio rather than floor to avoid float indexing.
    scarcity = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.0
    scarcity = max(0.0, min(1.0, float(scarcity)))

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    # Base willingness to pay: aim to beat typical surviving bids when contest is observed
    if highest_prev_bid >= contest_threshold:
        # They likely bid aggressively; if I'm healthy, undercut slightly; if low hp, match high
        if hp > 5.0:
            target = min(budget, (highest_prev_bid + 2.0) * (1.0 - 0.10 * scarcity))
        else:
            target = min(budget, highest_prev_bid + 3.0)
    else:
        # If no strong contest signal, bid enough to stay competitive under scarcity
        # Keep moderate so budget lasts 10 days.
        target = min(budget, DAILY_SALARY * (0.45 + 0.25 * scarcity))

    # If my hp is critical, prioritize survival regardless of contest
    if hp <= 2.0:
        target = min(budget, DAILY_SALARY * (0.85 + 0.10 * scarcity))

    # Ensure non-negative and at least a small bid if budget allows
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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Alive opponents and immediate reaction from yesterday
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    # If no opponents are alive, conserve
    if not alive_opps:
        return float(min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids (only immediate previous_trace)
    y_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                y_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Determine pressure level from yesterday
    pressure = 0.0
    if y_bids:
        highest_prev_bid = max(y_bids)
        # If someone bid near the daily salary, the market is hot
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            pressure = 1.0
        elif highest_prev_bid >= DAILY_SALARY * 0.65:
            pressure = 0.7
        else:
            pressure = 0.4

    # Supply-based urgency: higher supply reduces urgency for a given requirement
    # Normalize supply between MIN_SUPPLY..MAX_SUPPLY
    if MAX_SUPPLY <= MIN_SUPPLY:
        supply_factor = 0.5
    else:
        supply_factor = (supply - float(MIN_SUPPLY)) / (float(MAX_SUPPLY) - float(MIN_SUPPLY))
        if supply_factor < 0.0:
            supply_factor = 0.0
        if supply_factor > 1.0:
            supply_factor = 1.0

    # Base bid: aim around a fraction of daily salary; adjust for HP/no-water days and pressure
    # If I'm low HP or have many no-water days, bid more.
    hp_risk = 0.0
    if hp <= 2:
        hp_risk = 1.0
    elif hp <= 4:
        hp_risk = 0.7
    elif hp <= 6:
        hp_risk = 0.4
    else:
        hp_risk = 0.2

    nw_risk = 0.0
    if no_water_days >= 3:
        nw_risk = 1.0
    elif no_water_days == 2:
        nw_risk = 0.7
    elif no_water_days == 1:
        nw_risk = 0.4
    else:
        nw_risk = 0.2

    urgency = 0.55 * hp_risk + 0.45 * nw_risk

    # Hot market adjustment from yesterday
    # Cindy/Eric seemed to bid ~92; Alex died with similar bid, so avoid always matching the top.
    base = DAILY_SALARY * (0.45 + 0.25 * pressure)

    # Supply reduces need when supply is high
    supply_adjust = (1.0 - supply_factor) * 0.20  # up to +0.20 when supply is low

    bid = base * (1.0 + urgency * 0.65 + supply_adjust)

    # Clamp strategy: never exceed budget; also avoid extreme bids early unless critical
    critical = (hp <= 2) or (no_water_days >= 3)
    if critical:
        bid = min(bid, DAILY_SALARY * 0.95)
    else:
        bid = min(bid, DAILY_SALARY * 0.75)

    # Ensure at least a small meaningful bid when budget allows
    min_bid = 5.0
    if budget <= min_bid:
        return float(max(0.0, budget))

    bid = float(max(min_bid, bid))
    if bid > budget:
        bid = float(budget)

    return float(bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context['supply'])
    day = day_context['day']

    # Identify alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # Baseline: if we're in danger, bid aggressively.
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Estimate competitive pressure from yesterday's bids.
    prev_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # If no info, bid moderate.
    if not prev_bids:
        target = DAILY_SALARY * 0.55
    else:
        # Use top bids as indicator of how hard others are fighting.
        top1 = max(prev_bids)
        # Also consider second-highest to avoid overreacting to one outlier.
        sorted_b = sorted(prev_bids)
        top2 = sorted_b[-2] if len(sorted_b) >= 2 else top1

        # Supply-aware: when supply is scarce, competition rises.
        # supply in [15,25]; map to [0,1]
        scarcity = (25.0 - supply) / (25.0 - 15.0) if 25.0 != 15.0 else 0.5
        scarcity = max(0.0, min(1.0, scarcity))

        # If opponent bids were high yesterday, we shade slightly above the median/top2.
        # Keep a small increment to win but not blow budget.
        # Increment scales with scarcity.
        increment = 1.0 + 3.0 * scarcity

        # Choose a reference bid: prefer top2 if available to avoid chasing extreme.
        ref = top2
        # If top1 is much larger than top2, still use top2 but add a bit more under scarcity.
        if top1 > top2 + 15.0:
            ref = top2
            increment = increment + 1.5 * scarcity

        target = ref + increment

    # Survival logic: if low HP or accumulating no-water days, increase bid.
    if hp <= 2.0 or no_water_days >= 2:
        target = max(target, DAILY_SALARY * 0.9)
    elif hp <= 4.0 or no_water_days >= 1:
        target = max(target, DAILY_SALARY * 0.7)

    # Never bid more than budget.
    if budget <= 0.0:
        return 0.0

    # Cap target to a reasonable fraction of budget to avoid going broke.
    # Also cap relative to DAILY_SALARY since typical bids seem around 90-130.
    cap = min(budget, DAILY_SALARY * 1.6)
    bid = min(target, cap)

    # If supply is very high, lower bid slightly (less need to overpay).
    if supply >= 22.0:
        bid *= 0.92

    # Final safety clamp.
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive'):
            alive_opponents.append(o)

    if not alive_opponents:
        return float(min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from immediate previous_trace only
    yesterday_bids = []
    yesterday_pressures = []
    for o in alive_opponents:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            b = float(prev['bid'])
            yesterday_bids.append(b)
            # pressure proxy: if opponent had low hp or many no-water days, they likely bid higher
            hp_after = prev.get('hp_after', None)
            if hp_after is not None:
                yesterday_pressures.append((b, float(hp_after)))

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid

    # Estimate how many water units are likely to be won with a given bid.
    # We don't know mapping bid->allocation, so we instead calibrate bid levels against observed peers.
    # Use supply to slightly reduce bid when supply is abundant.
    supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0..1
    supply_factor = max(0.0, min(1.0, supply_factor))

    # Determine urgency: if I'm already in no-water streak or low hp, I must secure water.
    urgency = 0.0
    if hp <= 2.5:
        urgency += 1.0
    if no_water_days >= 2:
        urgency += 0.7
    if no_water_days >= 3:
        urgency += 0.8

    # Base bid target: track yesterday maximum but discount with supply_factor.
    # If others bid very high yesterday, we need to match/beat slightly.
    if highest_prev_bid >= DAILY_SALARY * 1.6:  # ~144
        target = highest_prev_bid + 2.0
    elif highest_prev_bid >= DAILY_SALARY * 1.1:  # ~99
        target = max(second_prev_bid + 1.0, DAILY_SALARY * 1.15)
    else:
        target = max(DAILY_SALARY * (0.85 + 0.2 * urgency), highest_prev_bid + 5.0)

    # Adjust by supply: more supply -> bid less aggressively.
    target = target * (0.92 - 0.12 * supply_factor)

    # Ensure we don't overspend: keep some budget for later days.
    # If urgency is high, spend more; otherwise, be conservative.
    if urgency >= 1.4:
        budget_cap = budget * 0.85
    elif urgency >= 0.7:
        budget_cap = budget * 0.70
    else:
        budget_cap = budget * 0.55

    # Also avoid bidding beyond a reasonable fraction of budget.
    bid = min(target, budget_cap, DAILY_SALARY * 3.0)

    # If my hp is critical, force a higher bid (still capped).
    if hp <= 1.5:
        bid = min(max(bid, DAILY_SALARY * 2.2), budget_cap, DAILY_SALARY * 3.0)

    # Final safety: if budget is tiny, bid what we can.
    if budget <= 1.0:
        return float(budget)

    # Must be non-negative.
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = day_context['supply']
    day = day_context['day']

    # Alive opponents
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    if not alive:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Read yesterday trace bids
    yesterday_bids = []
    for oid, o in alive:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # If no trace info, use conservative baseline
    if not yesterday_bids:
        if my_status['hp'] <= 2:
            return min(my_status['budget'], DAILY_SALARY * 0.9)
        return min(my_status['budget'], DAILY_SALARY * 0.55)

    highest_prev_bid = max(yesterday_bids)
    second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid

    # Pressure estimate: if others were spending aggressively, we can undercut slightly.
    # Target bid is a bit above the likely second-highest, but capped.
    target = second_prev_bid + 2.0

    # If someone was extremely aggressive, don't let them dictate: bid near their level only if needed.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        if my_status['hp'] > 3:
            target = min(target, DAILY_SALARY * 0.35)
        else:
            target = min(target, DAILY_SALARY * 0.92)
    else:
        # Otherwise, bid moderately to secure water without overspending.
        if my_status['hp'] <= 2:
            target = max(target, DAILY_SALARY * 0.75)
        elif my_status['hp'] <= 3:
            target = max(target, DAILY_SALARY * 0.55)
        else:
            target = max(target, DAILY_SALARY * 0.45)

    # Supply-based adjustment: higher supply reduces competition; lower supply increases it.
    # supply is float; map to discrete bucket safely.
    if supply <= MIN_SUPPLY:
        target *= 1.05
    elif supply >= MAX_SUPPLY:
        target *= 0.95

    # No-water days increases urgency.
    no_water_days = my_status.get('no_water_days', 0)
    if no_water_days >= 2:
        target *= 1.18
    elif no_water_days >= 1:
        target *= 1.08

    # Final clamp to budget and reasonable cap.
    target = float(target)
    if my_status['budget'] <= 0:
        return 0.0
    if my_status['hp'] <= 1:
        cap = DAILY_SALARY * 1.0
    else:
        cap = DAILY_SALARY * 0.95

    bid = min(my_status['budget'], min(target, cap))

    # Ensure non-negative
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    # If no opponents are alive, bid to secure water cheaply.
    if not alive_opponents:
        return max(0.0, min(float(my_status['budget']), DAILY_SALARY * 0.4))

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])

    # Use only yesterday's immediate bid pressure from traces.
    prev_bids = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate how contested the market was yesterday.
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Determine our target bid fraction.
    # Cindy-like behavior suggests others bid aggressively; we counter with a near-top bid.
    # If our HP is low, we must secure water.
    # Supply affects likelihood of needing to win: lower supply => more competitive.
    supply_ratio = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))
    # Lower supply -> higher competition.
    competition = 1.0 - supply_ratio

    if my_hp <= 2.0:
        # Emergency: bid to win.
        base = DAILY_SALARY * (0.85 + 0.1 * competition)
    elif my_hp <= 4.0:
        base = DAILY_SALARY * (0.65 + 0.15 * competition)
    else:
        base = DAILY_SALARY * (0.50 + 0.10 * competition)

    # If yesterday someone bid very high, we raise our bid slightly above the likely leader.
    # Otherwise, bid around our base.
    if highest_prev_bid >= DAILY_SALARY * 0.8:
        target = max(base, highest_prev_bid * 0.98)
    elif highest_prev_bid >= DAILY_SALARY * 0.55:
        target = max(base, highest_prev_bid * 0.88)
    else:
        # If others were weak, don't overpay.
        target = base

    # Convert target into a conservative final bid within budget.
    # Also cap by daily salary to avoid pathological overbidding.
    cap = min(my_budget, DAILY_SALARY * 1.05)
    bid = min(cap, target)

    # Ensure non-negative.
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive.append((opp_id, opp))

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids to infer how aggressive the field is.
    prev_bids = []
    for _, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else 0.0

    # Supply pressure: with mid supply, fewer units exist; bid higher.
    # Use a simple scaling between MIN_SUPPLY..MAX_SUPPLY.
    if MAX_SUPPLY == MIN_SUPPLY:
        supply_factor = 1.0
    else:
        supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_factor = max(0.0, min(1.0, supply_factor))

    # If someone bid near max yesterday, assume they will continue strong.
    # Target a bid that slightly undercuts/contests without going to the extreme.
    if highest_prev_bid >= DAILY_SALARY * 1.55:
        base = DAILY_SALARY * (0.85 + 0.1 * supply_factor)  # ~76.5..85.5
        # If my HP is critical, increase willingness.
        if hp <= 2 or no_water_days >= 2:
            base *= 1.15
    else:
        # More moderate field: bid around the upper-middle to secure water.
        base = DAILY_SALARY * (0.65 + 0.25 * supply_factor)  # ~58.5..81
        if hp <= 2 or no_water_days >= 2:
            base *= 1.25

    # Slight reactive bump if we saw a big gap between top bids.
    if highest_prev_bid > 0 and second_prev_bid > 0:
        gap = highest_prev_bid - second_prev_bid
        if gap > DAILY_SALARY * 0.3:
            base += min(DAILY_SALARY * 0.05, gap * 0.15)

    # Never exceed budget; also avoid spending too much when already fine.
    # If HP is comfortable, cap spending.
    if hp >= 6 and no_water_days == 0:
        cap = DAILY_SALARY * 0.7
    elif hp >= 4:
        cap = DAILY_SALARY * 0.85
    else:
        cap = DAILY_SALARY * 0.98

    bid = min(budget, base, cap)

    # Ensure non-negative.
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

    supply = day_context['supply']
    day = day_context['day']

    # If we have no budget, bid 0.
    if my_status['budget'] <= 0:
        return 0.0

    # Consider only alive opponents.
    alive_opps = [o for o in opponents_status.values() if o.get('alive')]
    if not alive_opps:
        # Conservative default: keep some budget for later.
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace.
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(prev.get('bid'))

    # Estimate competitive pressure.
    # Alex/Cindy were around ~104-107 yesterday; we target just above their likely safe region.
    pressure = 0.0
    if prev_bids:
        pressure = max(prev_bids)

    # Health-based escalation.
    hp = my_status.get('hp', 0)

    # Supply-based adjustment: with higher supply, we can bid less.
    # supply range is [15,25]. Normalize to [0,1].
    s_norm = (supply - 15.0) / 10.0
    if s_norm < 0.0:
        s_norm = 0.0
    if s_norm > 1.0:
        s_norm = 1.0

    # Base bid fraction.
    if hp <= 2:
        frac = 0.90
    elif hp <= 4:
        frac = 0.75
    else:
        frac = 0.65

    # If yesterday pressure was high, slightly increase.
    # Use a soft cap so we don't overpay.
    if pressure >= DAILY_SALARY * 0.85:
        frac += 0.08
    elif pressure >= DAILY_SALARY * 0.70:
        frac += 0.03

    # Supply adjustment: higher supply -> bid less.
    frac -= 0.10 * s_norm

    # Clamp fraction.
    if frac < 0.35:
        frac = 0.35
    if frac > 0.98:
        frac = 0.98

    bid = my_status['budget']
    target = DAILY_SALARY * frac
    if target < bid:
        bid = target

    # Keep a small reserve to avoid bankruptcy late.
    reserve = DAILY_SALARY * 0.10
    if bid < reserve:
        bid = float(min(my_status['budget'], reserve))

    # Final clamp.
    if bid < 0.0:
        bid = 0.0
    if bid > my_status['budget']:
        bid = float(my_status['budget'])

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

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append((oid, o))

    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Immediate reaction from yesterday trace bids
    prev_bids = []
    for oid, o in alive_opponents:
        prev = o.get('previous_trace', {})
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                prev_bids.append(float(bid))
            except Exception:
                pass

    # Estimate how aggressive the field was yesterday
    if prev_bids:
        highest_prev = max(prev_bids)
        second_prev = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev
    else:
        highest_prev = 0.0
        second_prev = 0.0

    # If Cindy-like behavior (very high bids) happened, we don't need to match it.
    # We target a bid that is likely sufficient under medium supply without burning budget.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY + 1e-9)  # 0..1

    # Urgency increases with hp and consecutive no-water days
    urgency = 0.0
    if hp <= 2.0:
        urgency += 0.9
    elif hp <= 4.0:
        urgency += 0.6
    elif hp <= 6.0:
        urgency += 0.35
    else:
        urgency += 0.15

    if no_water_days >= 3:
        urgency += 0.6
    elif no_water_days == 2:
        urgency += 0.3
    elif no_water_days == 1:
        urgency += 0.15

    # Base bid level: medium supply => moderate bid
    base = DAILY_SALARY * (0.35 + 0.25 * supply_ratio)

    # If yesterday had extreme bids, slightly increase but cap far below their max.
    if highest_prev >= DAILY_SALARY * 1.2:
        base = max(base, DAILY_SALARY * (0.45 + 0.15 * supply_ratio))

    # If yesterday's highest was not extreme, try to beat the second-highest a bit.
    target = base + urgency * (DAILY_SALARY * 0.25)

    if highest_prev < DAILY_SALARY * 1.2 and second_prev > 0:
        target = max(target, second_prev + 2.0)

    # Never bid more than we can afford; also avoid wasting when hp is healthy.
    if hp >= 7.0 and no_water_days == 0:
        cap = DAILY_SALARY * 0.65
    elif hp >= 7.0:
        cap = DAILY_SALARY * 0.85
    else:
        cap = DAILY_SALARY * 0.95

    bid = min(budget, cap, target)

    # Safety: ensure non-negative and at least a small bid if budget allows.
    if bid < 0.0:
        bid = 0.0
    if budget > 0 and bid == 0.0:
        bid = min(budget, DAILY_SALARY * 0.2)

    return float(bid)
"""
