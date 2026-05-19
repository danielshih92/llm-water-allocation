# ============================================================
# Experiment: exp_027
# Agent: Bob
# Source: exp_027
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

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    # If we have no opponents, bid just enough to ensure water
    if not alive_opponents:
        target = int(WATER_REQ)
        return float(min(budget, max(0.0, target)))

    # Read yesterday's bids (only immediate reaction)
    prev_bids = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev.get('bid', 0.0)))

    # Baseline aggressiveness based on supply and day
    # More supply -> lower need; less supply -> higher need.
    supply_mid = (MIN_SUPPLY + MAX_SUPPLY) / 2.0
    supply_factor = 0.55 if supply >= supply_mid else 0.75

    # Pressure from our own health / risk
    if hp <= 2.0 or no_water_days >= 2:
        self_pressure = 0.90
    elif hp <= 3.0 or no_water_days == 1:
        self_pressure = 0.75
    else:
        self_pressure = 0.60

    # If opponents bid heavily yesterday, match/beat slightly.
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        # If they were close to salary, expect a bidding war.
        if highest_prev_bid >= 0.85 * DAILY_SALARY:
            bid = DAILY_SALARY * 0.35 if hp > 3.0 else DAILY_SALARY * 0.95
        else:
            # Otherwise, outbid modestly to secure allocation.
            bid = max(highest_prev_bid + 1.5, DAILY_SALARY * 0.50)
    else:
        # No trace context: use controlled mid-high bid.
        bid = DAILY_SALARY * supply_factor * self_pressure

    # Convert to a water-like bid scale: prefer at least around WATER_REQ when feasible.
    # But keep strictly within budget.
    min_reasonable = float(WATER_REQ)
    bid = max(bid, min_reasonable * 0.9)

    # Early days slightly more aggressive to avoid cascading no-water days.
    if day <= 3:
        bid *= 1.08

    # Final clamp
    bid = float(min(budget, max(0.0, bid)))
    return bid
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

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    if not alive_opponents:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    yesterday_bids = []
    yesterday_supplies = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                yesterday_bids.append(float(bid))
            except Exception:
                pass
        prev_supply = prev.get('supply', None)
        if prev_supply is not None:
            try:
                yesterday_supplies.append(float(prev_supply))
            except Exception:
                pass

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If someone spent near salary scale, they likely continue aggressive bidding.
        aggressive_threshold = 0.85 * DAILY_SALARY
        if highest_prev_bid >= aggressive_threshold:
            # Preserve budget unless I'm in danger.
            if hp <= 2 or no_water_days >= 2:
                target = 0.95 * DAILY_SALARY
            else:
                # Shade slightly below aggressor to still capture water.
                target = max(0.55 * DAILY_SALARY, highest_prev_bid - 10.0)
        else:
            # If nobody was aggressive, bid a bit higher than mid to secure allocation.
            target = max(0.45 * DAILY_SALARY, 0.55 * DAILY_SALARY)
            # Small boost if bids clustered high.
            avg_prev_bid = sum(yesterday_bids) / float(len(yesterday_bids))
            if avg_prev_bid > 0.5 * DAILY_SALARY:
                target = max(target, avg_prev_bid + 5.0)
    else:
        # No trace bids available; default based on my risk.
        if hp <= 2 or no_water_days >= 2:
            target = 0.9 * DAILY_SALARY
        else:
            target = 0.55 * DAILY_SALARY

    # Convert target into a supply-appropriate bid: higher supply reduces need to overbid.
    # supply is between MIN_SUPPLY and MAX_SUPPLY.
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_factor = 0.5
    supply_factor = max(0.0, min(1.0, supply_factor))

    # When supply is high, we can bid a bit lower.
    target *= (1.05 - 0.15 * supply_factor)

    # Ensure we don't bid more than budget.
    bid = max(0.0, min(budget, float(target)))

    # If I'm extremely low hp, ensure survival by bidding near salary cap.
    if hp <= 1.0:
        bid = max(bid, min(budget, 0.98 * DAILY_SALARY))

    return float(bid)
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
    day = int(day_context['day'])

    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    # Estimate how aggressive others were yesterday (only immediate reaction)
    prev_bids = []
    for oid, o in alive:
        prev = o.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    prev_bids.append(float(b))
                except Exception:
                    pass

    # Pressure signals from yesterday
    high_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    # Core need: ensure enough to avoid further no-water pressure
    # If supply is tight relative to our requirement, we must bid harder.
    tightness = 0.0
    if supply <= WATER_REQ:
        tightness = 1.0
    else:
        # map supply in [MIN_SUPPLY, MAX_SUPPLY] to [1,0]
        tightness = max(0.0, min(1.0, (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)))

    # Determine target bid level
    # Baseline: moderate bid to win water without mirroring their extreme spending.
    # Escalate when our HP is low or supply is tight.
    if hp <= 2 or no_water_days >= 1:
        # critical survival: bid closer to daily salary but cap by budget
        base = DAILY_SALARY * (0.85 + 0.1 * tightness)
    else:
        # not critical: stay below the aggressive cluster
        # if others were very high yesterday, we slightly increase; otherwise keep moderate.
        if high_prev >= DAILY_SALARY * 0.9:
            base = DAILY_SALARY * (0.55 + 0.25 * tightness)
        elif avg_prev >= DAILY_SALARY * 0.7:
            base = DAILY_SALARY * (0.50 + 0.20 * tightness)
        else:
            base = DAILY_SALARY * (0.45 + 0.15 * tightness)

    # Add a small reaction term: if others overbid yesterday, we can undercut slightly.
    # If their high bid was extreme, undercut by a bit to avoid overspending.
    if high_prev > 0:
        # If they were spending ~130-140, we try to bid around 95% of that but not above our cap.
        reaction = min(DAILY_SALARY * 0.95, high_prev * 0.95)
        # Blend with base
        base = 0.65 * base + 0.35 * reaction

    # Final cap: cannot exceed budget
    bid = min(budget, base)

    # If budget is very low, still try to survive: bid at least a fraction.
    if bid <= 0 and budget > 0:
        bid = min(budget, DAILY_SALARY * 0.4)

    # Ensure non-negative
    if bid < 0:
        bid = 0.0

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

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive = []
    for k, o in opponents_status.items():
        if o.get('alive', False):
            alive.append(o)

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Yesterday bids from immediate trace
    yesterday_bids = []
    yesterday_pressured = []
    for o in alive:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                b = float(b)
            except Exception:
                continue
            yesterday_bids.append(b)
            # If they were already low hp / dying, they may bid differently today
            hp_after = prev.get('hp_after', None)
            if hp_after is not None:
                try:
                    hp_after = float(hp_after)
                except Exception:
                    hp_after = None
                if hp_after is not None and hp_after <= 0:
                    yesterday_pressured.append(b)

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Base bid: aim to beat typical competition without matching Cindy's max aggressiveness.
    # If supply is higher, competition is likely lower; bid less.
    supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.0
    supply_norm = max(0.0, min(1.0, float(supply_norm)))

    # Determine urgency from hp/no_water_days
    urgency = 0
    if hp <= 2.0:
        urgency += 3
    if hp <= 4.0:
        urgency += 2
    if no_water_days >= 2:
        urgency += 2
    if no_water_days >= 3:
        urgency += 3

    # If the market was very hot yesterday, raise slightly but not to the same level.
    hot_market = highest_prev_bid >= DAILY_SALARY * 0.85

    # Conservative escalation policy
    if urgency >= 5:
        bid = DAILY_SALARY * (0.65 + 0.1 * supply_norm)
    elif urgency >= 3:
        bid = DAILY_SALARY * (0.55 + 0.1 * supply_norm)
    else:
        bid = DAILY_SALARY * (0.42 + 0.08 * supply_norm)

    # If Cindy-like aggressiveness was present (highest_prev_bid high), adjust upward a bit
    # but keep below the top bidder to avoid price lock.
    if hot_market:
        bid = max(bid, min(DAILY_SALARY * 0.6, highest_prev_bid * 0.55 + 5.0))

    # If someone died yesterday, they likely have 0 budget and won't bid much; reduce bid.
    if yesterday_pressured and max(yesterday_pressured) <= DAILY_SALARY * 0.2:
        bid *= 0.9

    # Final cap by budget
    bid = max(0.0, min(budget, bid))

    # Ensure we don't bid trivially when we need water.
    if my_status.get('no_water_days', 0) >= 1 and bid < DAILY_SALARY * 0.25:
        bid = min(budget, DAILY_SALARY * 0.25)

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

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((agent_id, opp))

    if not alive_opps:
        return float(min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace only (immediate reaction)
    prev_bids = []
    prev_hp_after = []
    for agent_id, opp in alive_opps:
        pt = opp.get('previous_trace', None)
        if isinstance(pt, dict):
            b = pt.get('bid', None)
            if b is not None:
                try:
                    prev_bids.append(float(b))
                    prev_hp_after.append(float(pt.get('hp_after', opp.get('hp', 0.0))))
                except Exception:
                    pass

    # Supply pressure: with low supply, winning costs more; with high supply, can bid less.
    # Use a conservative mid-range targeting.
    if supply <= (MIN_SUPPLY + 1):
        supply_factor = 1.05
    elif supply >= (MAX_SUPPLY - 1):
        supply_factor = 0.85
    else:
        supply_factor = 0.95

    # Identify yesterday aggressor level
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev_bid
    else:
        highest_prev_bid = 0.0
        second_prev_bid = 0.0

    # Determine our urgency
    urgency = 0
    if hp <= 2.0:
        urgency = 2
    elif hp <= 4.0:
        urgency = 1

    # If we are already accumulating no-water days, increase urgency.
    if no_water_days >= 2:
        urgency = max(urgency, 2)

    # Baseline bid: target just above the likely clearing price.
    # If Cindy/Alex were bidding near high levels, we shadow them; otherwise we undercut.
    # Use thresholds tied to DAILY_SALARY.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # High-pressure environment yesterday; shadow but cap by budget.
        target = max(DAILY_SALARY * 0.25, second_prev_bid + 2.0)
        if urgency >= 2:
            target = max(target, DAILY_SALARY * 0.55)
        else:
            target = max(target, DAILY_SALARY * 0.35)
    else:
        # Lower bids yesterday; we can bid moderately.
        target = max(DAILY_SALARY * 0.30, highest_prev_bid * 0.75 + 5.0)
        if urgency >= 2:
            target = max(target, DAILY_SALARY * 0.60)

    # Apply supply factor and small day-variant to avoid deterministic ties
    tie_break = 1.0 + (0.02 * (day % 5))
    target *= supply_factor * tie_break

    # Final cap: never exceed budget; also avoid extreme bids when not urgent.
    if urgency == 0:
        cap = DAILY_SALARY * 0.75
    elif urgency == 1:
        cap = DAILY_SALARY * 0.95
    else:
        cap = DAILY_SALARY * 1.10

    bid = float(min(budget, max(0.0, min(cap, target))))

    # Ensure at least a minimal competitive bid when we are alive and need water.
    if hp > 0 and bid < DAILY_SALARY * 0.15:
        bid = float(min(budget, DAILY_SALARY * 0.18))

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

    supply = float(day_context['supply'])
    day = day_context['day']

    # Alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # If no one alive, just spend enough to satisfy requirement
    if not alive_opps:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday traces for immediate reaction
    yesterday_bids = []
    yesterday_hp_after = []
    for o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
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

    # Estimate how contested it was
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = (sum(yesterday_bids) / len(yesterday_bids)) if yesterday_bids else 0.0

    # Supply pressure: if supply is close to requirement, competition matters more
    # supply_ratio in [~1.67, ~2.78]
    supply_ratio = supply / float(WATER_REQ)

    # Determine risk based on our hp and no_water_days
    my_hp = float(my_status['hp'])
    no_water_days = int(my_status['no_water_days'])
    my_budget = float(my_status['budget'])

    # Base bid level: moderate-high in medium scenario
    # If supply is scarce (ratio closer to 1.7), bid more.
    scarcity_factor = 0.55 + 0.25 * (1.0 - min(1.0, (supply_ratio - (MIN_SUPPLY / WATER_REQ)) / ((MAX_SUPPLY / WATER_REQ) - (MIN_SUPPLY / WATER_REQ) + 1e-9)))

    # React to yesterday: if someone bid very high, avoid getting outbid.
    # Alex/Eric/Cindy show aggressive bidding; use their max as a threshold.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # High contention yesterday: bid to beat them slightly if we are not in critical condition
        if my_hp > 3.0 and no_water_days <= 1:
            target = max(highest_prev_bid + 2.0, DAILY_SALARY * 0.62)
        else:
            target = max(highest_prev_bid + 5.0, DAILY_SALARY * 0.9)
    elif avg_prev_bid >= DAILY_SALARY * 0.65:
        # Medium contention: bid somewhat above average
        target = max(avg_prev_bid + 3.0, DAILY_SALARY * 0.55)
    else:
        # Low contention: bid enough to secure but not overpay
        target = DAILY_SALARY * (0.45 + 0.2 * scarcity_factor)

    # If we are already in danger (low hp or multiple no-water days), increase bid
    if my_hp <= 2.0 or no_water_days >= 2:
        target = max(target, DAILY_SALARY * 0.95)

    # Clamp by budget and keep within a reasonable fraction of salary
    max_affordable = my_budget
    # Do not bid above what we can pay; also cap to avoid runaway
    cap = DAILY_SALARY * (1.0 if highest_prev_bid >= DAILY_SALARY * 0.85 else 0.85)
    bid = min(max_affordable, min(cap, target * scarcity_factor + (DAILY_SALARY * 0.05)))

    # Ensure non-negative float
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
    day = int(day_context.get('day', 0))

    # Determine alive opponents and their yesterday bid pressure
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    prev_bids = []
    prev_max_bid = 0.0
    prev_min_bid = None
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                b = float(b)
            except Exception:
                continue
            prev_bids.append(b)
            if b > prev_max_bid:
                prev_max_bid = b
            if prev_min_bid is None or b < prev_min_bid:
                prev_min_bid = b

    my_hp = float(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Supply pressure: with higher supply, competition is weaker; with lower, competition stronger.
    # Map supply to [0,1] where 0 = min supply, 1 = max supply.
    if MAX_SUPPLY == MIN_SUPPLY:
        supply_factor = 0.5
    else:
        supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
        if supply_factor < 0:
            supply_factor = 0.0
        if supply_factor > 1:
            supply_factor = 1.0

    # Baseline aggressiveness: if my hp is low or I'm already accumulating no-water days, bid more.
    hp_risk = 0.0
    if my_hp <= 2.0:
        hp_risk = 1.0
    elif my_hp <= 4.0:
        hp_risk = 0.7
    elif my_hp <= 6.0:
        hp_risk = 0.4
    else:
        hp_risk = 0.2

    if no_water_days >= 2:
        hp_risk = min(1.0, hp_risk + 0.25)

    # Opponent pressure from yesterday: if someone bid very high, they likely needed water.
    # Use thresholds relative to DAILY_SALARY.
    opp_pressure = 0.0
    if prev_bids:
        if prev_max_bid >= DAILY_SALARY * 1.7:
            opp_pressure = 1.0
        elif prev_max_bid >= DAILY_SALARY * 1.2:
            opp_pressure = 0.7
        elif prev_max_bid >= DAILY_SALARY * 0.9:
            opp_pressure = 0.4
        else:
            opp_pressure = 0.2

    # Decide target bid.
    # When supply is scarce (low supply_factor), increase bid; when abundant, decrease.
    scarcity_boost = 1.0 + (1.0 - supply_factor) * 0.35

    # If yesterday max bid was high, we slightly undercut to avoid overpaying while still contesting.
    if prev_bids and prev_max_bid >= DAILY_SALARY * 1.2:
        target = (prev_max_bid * (0.78 + 0.1 * hp_risk)) * scarcity_boost
    else:
        # Otherwise, bid around a fraction of salary based on my risk.
        target = (DAILY_SALARY * (0.45 + 0.45 * hp_risk)) * scarcity_boost

    # Keep within budget and avoid absurd bids.
    # Also, since water_requirement is 9, competition is mostly about securing enough water; bid cap at ~2.2x salary.
    bid_cap = DAILY_SALARY * 2.2
    target = min(target, bid_cap)

    # If my budget is low, scale down proportionally.
    if my_budget <= 0:
        return 0.0

    # Ensure at least a small participation bid if we must survive.
    min_participation = DAILY_SALARY * 0.25
    if my_budget < min_participation:
        min_participation = my_budget

    # Final budget-aware clamp.
    bid = float(min(my_budget, max(min_participation, target)))

    # If my hp is critically low, be willing to spend more aggressively.
    if my_hp <= 2.0:
        bid = float(min(my_budget, max(bid, DAILY_SALARY * 0.95 * scarcity_boost)))

    return bid
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

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday immediate pressure from previous_trace
    prev_bids = []
    prev_hp_after = []
    for oid, o in alive_opps:
        pt = o.get('previous_trace', {}) or {}
        bid = pt.get('bid', None)
        if bid is not None:
            try:
                prev_bids.append(float(bid))
            except Exception:
                pass
        try:
            if pt.get('hp_after', None) is not None:
                prev_hp_after.append(float(pt.get('hp_after')))
        except Exception:
            pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Supply pressure: with supply 15-25, water units are usually 1-2 for us.
    # We aim to buy enough water to avoid losing another HP step.
    # Approx mapping: if supply is low, winning water is more valuable.
    supply_units = int(supply / float(WATER_REQ))  # safe int index not needed; just compute
    # If supply < 18, likely 1 unit max; otherwise 2.

    # Determine base bid aggressiveness
    # If someone previously bid very high, they were likely trying to secure scarce water.
    high_pressure = highest_prev_bid >= DAILY_SALARY * 0.85

    # HP urgency
    if hp <= 2.5 or no_water_days >= 2:
        urgency = 1.0
    elif hp <= 4.0:
        urgency = 0.7
    else:
        urgency = 0.4

    # Conservative baseline to avoid Cindy-like failure mode
    # When not high pressure and our HP is healthy, keep bid below typical survival bids.
    if high_pressure:
        # Compete but not max; attempt to outbid only slightly.
        target = min(budget, max(DAILY_SALARY * 0.55, highest_prev_bid * 0.92 + 2.0))
    else:
        # If supply is low, slightly increase bid; else keep low.
        if supply < 18.0:
            target = DAILY_SALARY * (0.48 + 0.25 * urgency)
        else:
            target = DAILY_SALARY * (0.40 + 0.22 * urgency)

    # Ensure we don't overspend when budget is tight
    # Also cap by a fraction of budget to preserve future rounds.
    budget_cap = budget * 0.65 if budget > 0 else 0.0
    target = min(target, budget_cap)

    # If our budget is extremely small, bid whatever we can.
    if budget <= DAILY_SALARY * 0.12:
        return max(0.0, min(budget, DAILY_SALARY * 0.2))

    # Final safety: never negative
    return max(0.0, float(target))
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

    # Identify alive opponents and their yesterday bids
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            prev = opp.get('previous_trace') or {}
            bid = prev.get('bid', None)
            alive_opps.append((opp_id, opp, bid))

    # If no opponents alive, just bid conservatively
    if not alive_opps:
        return min(float(my_status['budget']), DAILY_SALARY * 0.4)

    # Compute pressure from yesterday
    yesterday_bids = [b for (_, _, b) in alive_opps if b is not None]
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid
    else:
        highest_prev_bid = 0.0
        second_prev_bid = 0.0

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    # Supply-aware aggressiveness: if supply is high, we can afford to outbid to ensure we get water.
    supply_frac = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_frac = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    if supply_frac < 0.0:
        supply_frac = 0.0
    if supply_frac > 1.0:
        supply_frac = 1.0

    # Base bid target: try to slightly exceed yesterday's top bid when we are healthy.
    # If we are low HP, we bid more to avoid death.
    if hp <= 2:
        target = max(highest_prev_bid + 2.0, DAILY_SALARY * 0.85)
    elif hp <= 4:
        target = max(highest_prev_bid + 1.0, DAILY_SALARY * 0.65)
    else:
        # Healthy: aggress only when supply is favorable
        if supply_frac >= 0.6:
            target = max(highest_prev_bid + 1.5, DAILY_SALARY * (0.55 + 0.3 * supply_frac))
        else:
            # If supply is low, conserve; still try to beat typical winners by a small margin
            target = max(second_prev_bid + 1.0, DAILY_SALARY * 0.45)

    # Ensure we don't bid more than budget; also keep a minimum bid to avoid wasting too much
    bid = min(budget, target)

    # If budget is extremely low, bid what we can
    if bid < 0.0:
        bid = 0.0

    # Optional: if we have very low budget, avoid overbidding
    if budget <= DAILY_SALARY * 0.15:
        bid = min(budget, DAILY_SALARY * 0.2)

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

    # Alive opponents only
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace only
    yesterday_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Estimate how many water blocks we can reasonably afford to contest
    # If supply is low, competition matters more; if high, we can bid less.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if (MAX_SUPPLY - MIN_SUPPLY) != 0 else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Base bid: aim to be competitive but not wasteful.
    # When supply is low, increase; when high, decrease.
    base_bid = DAILY_SALARY * (0.62 - 0.18 * supply_ratio)

    # React to Cindy/Alex yesterday: if someone bid extremely high, we must respond.
    # Use the max yesterday bid as pressure signal.
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # If opponent(s) showed extreme pressure (near/above our daily salary), match more.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # If we're healthy, slightly undercut; if low HP, bid aggressively.
        if my_status['hp'] > 3:
            bid = DAILY_SALARY * (0.78 - 0.08 * supply_ratio)
        else:
            bid = DAILY_SALARY * (0.95 - 0.05 * supply_ratio)
    else:
        # Otherwise, undercut the typical Cindy-heavy pace by staying around base_bid.
        # If Cindy specifically bid high yesterday, nudge upward; if not, stay near base.
        cindy = opponents_status.get('Cindy', None)
        cindy_prev = (cindy.get('previous_trace', {}) if cindy else {}) or {}
        cindy_bid = cindy_prev.get('bid', None)
        cindy_bid_val = None
        if cindy_bid is not None:
            try:
                cindy_bid_val = float(cindy_bid)
            except Exception:
                cindy_bid_val = None

        if cindy_bid_val is not None and cindy_bid_val >= DAILY_SALARY * 0.75:
            bid = base_bid * 1.15
        else:
            bid = base_bid

    # Survival/triage: if we're in danger, ensure higher bid.
    if my_status['hp'] <= 2:
        bid = max(bid, DAILY_SALARY * 0.9)
    elif my_status['no_water_days'] >= 2:
        bid = max(bid, DAILY_SALARY * 0.72)

    # Budget cap
    bid = float(min(my_status['budget'], bid))

    # If budget is tiny, still bid what we can.
    if bid < 0.0:
        bid = 0.0

    return bid
"""
