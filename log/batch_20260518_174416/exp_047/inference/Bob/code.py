# ============================================================
# Experiment: exp_047
# Agent: Bob
# Source: exp_047
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

    supply = day_context.get('supply', 0)
    day = day_context.get('day', 0)

    # Collect alive opponents and their yesterday bids
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    # Base bid: aim to secure at least one unit of water share when supply is moderate.
    # Since bids translate to allocation in this challenge, we bias around a mid fraction.
    # Use supply to scale aggressiveness within [15,25].
    supply_clamped = max(MIN_SUPPLY, min(MAX_SUPPLY, float(supply)))
    supply_ratio = (supply_clamped - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY + 1e-9)  # 0..1

    # If we have low hp or are already suffering, bid more aggressively.
    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Immediate reaction to yesterday: if any opponent previously overbid, we slightly undercut.
    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        if prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # Determine target bid
    if no_water_days >= 2 or hp <= 2.0:
        # High urgency: bid near a high fraction of salary but capped by budget.
        base = DAILY_SALARY * (0.85 + 0.1 * (1.0 - min(1.0, supply_ratio)))
    else:
        # Moderate urgency: bid mid, increasing with supply.
        base = DAILY_SALARY * (0.45 + 0.25 * supply_ratio)

    if yesterday_bids:
        highest_prev = max(yesterday_bids)
        # If someone already bid extremely high, we try to avoid a bidding war while still competing.
        if highest_prev >= DAILY_SALARY * 0.85:
            # Undercut slightly if we can afford it; otherwise keep base.
            candidate = highest_prev - 1.5
            base = max(base, candidate)
        elif highest_prev >= DAILY_SALARY * 0.6:
            # Match pressure moderately.
            base = max(base, highest_prev * 0.85)

    # Convert to final bid with budget cap.
    bid = min(budget, max(0.0, base))

    # Ensure we don't bid above a reasonable upper bound to preserve budget across 10 days.
    # (Still allow high urgency to override via base.)
    bid_cap = DAILY_SALARY * 0.95
    bid = min(bid, bid_cap)

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

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return min(float(my_status['budget']), DAILY_SALARY * 0.4)

    # Extract yesterday bids from previous_trace only
    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Baseline target bid: Cindy appears to anchor around 90.
    # We undercut slightly unless supply is tight.
    tight_supply = supply <= 19.0
    very_tight_supply = supply <= 17.0

    # If someone previously overpaid heavily, raise bid to avoid losing the scarce slot.
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Compute a conservative cap based on remaining budget and urgency.
    urgency = 0
    if my_hp <= 2:
        urgency = 3
    elif my_hp <= 4:
        urgency = 2
    elif no_water_days >= 2:
        urgency = 1

    # Decision
    if very_tight_supply:
        # Need water; bid near Cindy's anchor but not equal.
        base = DAILY_SALARY * 0.92
    elif tight_supply:
        base = DAILY_SALARY * 0.78
    else:
        # Plenty of supply: bid lower to preserve budget.
        base = DAILY_SALARY * 0.55

    # If opponent previously bid extremely high, match pressure.
    if highest_prev_bid >= DAILY_SALARY * 1.15:
        base = max(base, DAILY_SALARY * 0.95)
    elif highest_prev_bid >= DAILY_SALARY * 0.85:
        base = max(base, DAILY_SALARY * 0.80)

    # Urgency adjustment
    if urgency >= 3:
        base = max(base, DAILY_SALARY * 0.98)
    elif urgency == 2:
        base = max(base, DAILY_SALARY * 0.90)
    elif urgency == 1:
        base = max(base, DAILY_SALARY * 0.75)

    # Ensure we don't exceed budget.
    bid = min(my_budget, base)

    # Additional safeguard: if budget is very low, bid what we can.
    if my_budget <= DAILY_SALARY * 0.2:
        bid = my_budget

    # Keep bid non-negative
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

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for oid, o in opponents_status.items():
        try:
            if o.get('alive', False):
                alive_opps.append((oid, o))
        except Exception:
            continue

    # If no opponents alive, conserve.
    if not alive_opps:
        return float(min(my_budget, DAILY_SALARY * 0.4))

    # Read only yesterday's immediate behavior.
    prev_bids = []
    prev_dead_pressure = 0
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                prev_bids.append(float(bid))
            except Exception:
                pass
        # If yesterday ended badly (likely aggressive/losing), treat as volatility.
        try:
            if float(prev.get('hp_after', 0)) < 0:
                prev_dead_pressure += 1
        except Exception:
            pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else 0.0

    # Supply pressure: less supply => higher chance of needing to outbid.
    # Map supply to a rough urgency factor.
    if supply <= MIN_SUPPLY:
        urgency = 1.0
    elif supply >= MAX_SUPPLY:
        urgency = 0.35
    else:
        urgency = 0.35 + 0.65 * ((MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY))

    # Our urgency from hp/no-water.
    hp_urgency = 0.0
    if my_hp <= 1.5:
        hp_urgency = 1.0
    elif my_hp <= 3.0:
        hp_urgency = 0.75
    elif my_hp <= 5.0:
        hp_urgency = 0.45
    else:
        hp_urgency = 0.2

    # If opponents were bidding very high yesterday, match just above their likely threshold.
    # Cindy/Eric seem to survive with high bids; avoid matching the absolute max unless necessary.
    target = 0.0

    # Baseline bid depends on urgency.
    baseline = DAILY_SALARY * (0.25 + 0.45 * urgency + 0.25 * hp_urgency)

    # If highest previous bid is strong, set a competitive target.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # If we are in danger, go closer to highest; otherwise just over second/highest fraction.
        if my_hp <= 3.0 or my_no_water_days >= 2:
            target = highest_prev_bid * (0.9 if urgency >= 0.7 else 0.75)
        else:
            target = max(baseline, second_prev_bid * 1.05, highest_prev_bid * 0.6)
    else:
        # If opponents were not bidding aggressively, keep baseline and slightly undercut.
        # But if we see volatility from deaths, be a bit more competitive.
        vol_boost = 0.08 * min(prev_dead_pressure, 3)
        target = max(baseline * (1.0 + vol_boost), highest_prev_bid * 0.7)

    # Ensure we can always afford and never bid negative.
    target = max(0.0, float(target))

    # Hard caps: don't overspend early unless hp is critical.
    if my_hp <= 3.0 or my_no_water_days >= 2:
        cap = min(my_budget, DAILY_SALARY * 0.95)
    else:
        cap = min(my_budget, DAILY_SALARY * (0.6 + 0.25 * urgency))

    bid = min(target, cap)

    # If budget is extremely low, bid what we can.
    if my_budget <= 1.0:
        bid = my_budget

    # Avoid bidding zero if we still need water soon.
    if bid < 1e-6 and (my_no_water_days >= 1 or my_hp <= 5.0):
        bid = min(my_budget, DAILY_SALARY * 0.2)

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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace (immediate reaction only)
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
    second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else 0.0

    # Aggression inference: if someone bid very high yesterday, others likely are contesting.
    # Use supply to scale aggressiveness: with higher supply, we can pay less to still get water.
    supply_ratio = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Base target bid band from yesterday.
    # If high contest yesterday, bid around (highest_prev_bid - small offset) to win enough.
    if highest_prev_bid >= DAILY_SALARY * 0.8:
        # Contested environment
        if hp <= 2 or no_water_days >= 2:
            target = min(budget, DAILY_SALARY * (0.95 - 0.1 * supply_ratio))
        else:
            # Slightly under the top bidder to conserve budget
            target = min(budget, max(0.0, highest_prev_bid * 0.92 - 2.0))
    else:
        # Less contested
        if hp <= 2 or no_water_days >= 2:
            target = min(budget, DAILY_SALARY * (0.8 - 0.05 * supply_ratio))
        else:
            # Aim to secure water without overpaying
            # Use second_prev_bid as a proxy for typical bids.
            base = second_prev_bid if second_prev_bid > 0 else (DAILY_SALARY * 0.55)
            target = min(budget, max(0.0, base * (0.85 + 0.1 * supply_ratio)))

    # Ensure we don't bid negative and keep within budget.
    target = max(0.0, min(float(budget), float(target)))

    # If budget is extremely low, bid everything.
    if budget <= 5.0:
        return max(0.0, float(budget))

    return target
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = day_context['supply']
    day = day_context['day']

    alive_opps = [o for o in opponents_status.values() if o.get('alive', False)]

    # Base safety: if we're in danger, bid high to avoid death.
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    # Extract yesterday bids from opponents (immediate reaction only)
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        if prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # Estimate pressure from yesterday
    pressure = 0.0
    if yesterday_bids:
        pressure = max(yesterday_bids)

    # Supply pressure: lower supply means water is scarce -> we need more.
    # Normalize to [0,1]
    if MAX_SUPPLY > MIN_SUPPLY:
        scarcity = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        scarcity = 0.5

    # Determine target bid fraction of daily salary.
    # Cindy's behavior suggests others may overbid; we avoid matching extreme bids unless needed.
    if hp <= 2 or no_water_days >= 3:
        # Critical survival: bid aggressively but cap to avoid overspending.
        target = DAILY_SALARY * (0.85 + 0.1 * scarcity)
    else:
        # Non-critical: bid enough to beat typical mid bids, but not chase Cindy's extremes.
        # If yesterday pressure was very high, slightly increase.
        high_pressure = 1.0 if pressure >= DAILY_SALARY * 1.05 else 0.0
        target = DAILY_SALARY * (0.45 + 0.25 * scarcity + 0.15 * high_pressure)

    # If yesterday pressure was extreme, don't fully follow; instead, bid moderate and rely on others wasting.
    if pressure >= DAILY_SALARY * 1.35 and hp > 3:
        target = min(target, DAILY_SALARY * (0.55 + 0.15 * scarcity))

    # Final cap by budget.
    bid = min(budget, target)

    # Ensure bid is non-negative and at least a small amount if budget allows.
    if bid < 0:
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
    day = day_context.get('day', 0)

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((opp_id, o))

    if not alive_opps:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Extract yesterday bids from previous_trace for immediate reaction.
    yesterday_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Baseline target from yesterday: follow the strongest surviving pattern.
    base = DAILY_SALARY * 0.55
    if yesterday_bids:
        highest = max(yesterday_bids)
        second = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest

        # If someone was extremely aggressive and survived, try to match slightly above risk tier.
        if highest >= DAILY_SALARY * 0.85:
            base = second + 5.0
        else:
            # Otherwise, bid around the upper mid to beat cautious bidders.
            base = max(base, second + 2.5)

    # Pressure adjustments: low HP or many no-water days => bid harder.
    if my_hp <= 2.0 or my_no_water_days >= 2:
        base *= 1.35
    elif my_hp <= 4.0 or my_no_water_days == 1:
        base *= 1.15

    # Supply scaling: when supply is low, competition is higher.
    if supply <= float(MIN_SUPPLY):
        base *= 1.20
    elif supply >= float(MAX_SUPPLY):
        base *= 0.95

    # Convert base to a bid cap based on affordability.
    # Keep some budget for future days (10-day episode): spend at most ~35% of current budget.
    spend_cap = my_budget * 0.35
    bid = min(base, spend_cap)

    # Ensure we can still bid a meaningful amount.
    min_bid = 0.0
    if my_hp <= 2.0:
        min_bid = DAILY_SALARY * 0.6
    elif my_no_water_days >= 2:
        min_bid = DAILY_SALARY * 0.5
    bid = max(bid, min_bid)

    # Final clamp to budget.
    bid = min(bid, my_budget)
    if bid < 0.0:
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

    # Read yesterday bids for immediate pressure signal
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else 0.0

    # Supply adequacy: more supply => can undercut slightly and still secure water.
    # We estimate how many water blocks are likely to be allocated.
    # Use a conservative target: want enough to keep hp stable.
    blocks = int(supply / WATER_REQ)  # safe int index usage not needed but keep int
    # blocks can be 1 or 2 (since supply in [15,25])

    # Base bid aggressiveness
    # If supply is high (>= 2 blocks), we can bid lower; if low, bid higher.
    if blocks >= 2:
        supply_factor = 0.55
    else:
        supply_factor = 0.85

    # React to yesterday's overbidding: if someone bid very high, they likely were aiming to survive.
    # We try to beat them with a small increment when my hp is at risk.
    pressure = 0.0
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        pressure = 1.0
    elif highest_prev_bid >= DAILY_SALARY * 0.65:
        pressure = 0.6

    # HP urgency
    if hp <= 1:
        hp_factor = 1.0
    elif hp == 2:
        hp_factor = 0.9
    elif hp == 3:
        hp_factor = 0.75
    else:
        hp_factor = 0.6

    # If we've already gone without water, increase urgency.
    if no_water_days >= 2:
        hp_factor = min(1.0, hp_factor + 0.2)

    # Target bid: undercut typical high bids unless necessary.
    # If pressure high, aim around highest_prev_bid minus a bit, but if my hp is low, aim above it.
    if pressure >= 0.9:
        if hp <= 3:
            target = highest_prev_bid + 2.0
        else:
            target = max(second_prev_bid + 1.0, highest_prev_bid * 0.92)
    elif pressure >= 0.6:
        target = max(second_prev_bid + 1.0, highest_prev_bid * 0.85)
    else:
        target = DAILY_SALARY * supply_factor

    # Apply hp urgency scaling
    target = target * hp_factor

    # Clamp to budget and reasonable bounds
    max_reasonable = DAILY_SALARY * 1.2
    bid = float(min(budget, max_reasonable, max(0.0, target)))

    # Ensure we don't bid trivially low when supply is low and hp is critical
    if blocks < 2 and hp <= 2:
        bid = float(min(budget, max(bid, DAILY_SALARY * 0.75)))

    return bid
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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    # Alive opponents and yesterday bids
    alive_opps = []
    yesterday_bids = []
    for oid, o in opponents_status.items():
        if bool(o.get('alive', False)):
            alive_opps.append(o)
            prev = o.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    yesterday_bids.append(float(prev.get('bid', 0.0)))
                except Exception:
                    pass

    if not alive_opps:
        # No competition: spend to secure water
        return min(float(my_status['budget']), DAILY_SALARY * 0.4)

    # Use only yesterday's immediate reaction
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else 0.0

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))

    # Supply pressure: fewer units => more aggressive bids
    # Expected max number of water units from supply
    units = int(supply / WATER_REQ) if WATER_REQ > 0 else 0
    # Normalize pressure: 15..25 -> 0..1
    pressure = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    pressure = max(0.0, min(1.0, pressure))

    # Determine target bid band exploiting Cindy's aggressive pattern
    # If Cindy-like pressure exists (high previous bid), slightly undercut or match depending on hp.
    # Otherwise, bid moderate to avoid overspending.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # High contest yesterday
        if my_hp > 3.5:
            target = max(DAILY_SALARY * 0.35, second_prev_bid + 1.0)
        else:
            target = max(DAILY_SALARY * 0.75, highest_prev_bid - 2.0)
    else:
        # Lower contest
        if my_hp <= 2.5:
            target = DAILY_SALARY * (0.75 + 0.15 * pressure)
        else:
            target = DAILY_SALARY * (0.45 + 0.25 * pressure)

    # Ensure we don't bid beyond what is sensible for our budget
    # Cap more tightly when supply is low but hp is healthy.
    if my_hp > 3.5:
        cap = DAILY_SALARY * (0.55 + 0.2 * pressure)
    else:
        cap = DAILY_SALARY * (0.95 + 0.05 * pressure)

    # If very low units, increase cap slightly
    if units <= 1:
        cap *= 1.05

    bid = min(my_budget, min(target, cap))

    # If bid too low relative to contest, bump a little to avoid losing completely
    if highest_prev_bid > 0 and bid < highest_prev_bid * 0.65:
        bid = min(my_budget, highest_prev_bid * (0.72 if my_hp > 3.5 else 0.9))

    # Final safety: non-negative
    if bid < 0.0:
        bid = 0.0

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

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    my_hp = my_status.get('hp', 0)
    my_budget = my_status.get('budget', 0)

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return float(min(my_budget, DAILY_SALARY * 0.4))

    # Immediate reaction from yesterday traces
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate how competitive the market is from the top yesterday bid
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Base bid depends on how much supply likely exists today
    # If supply is higher, we can bid a bit less; if lower, bid more.
    # Ensure indices are integers even if any derived list index is used.
    supply_norm = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (float(supply) - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    supply_norm = 0.0 if supply_norm < 0.0 else (1.0 if supply_norm > 1.0 else supply_norm)

    # Target fraction of daily salary
    # Lower supply -> higher fraction; higher supply -> lower fraction.
    base_frac = 0.62 - 0.18 * supply_norm

    # Pressure adjustment from yesterday's highest bid
    # If someone was willing to spend a lot, we increase to avoid losing water.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        pressure_frac = 0.78
    elif highest_prev_bid >= DAILY_SALARY * 0.60:
        pressure_frac = 0.70
    elif highest_prev_bid >= DAILY_SALARY * 0.35:
        pressure_frac = 0.64
    else:
        pressure_frac = 0.58

    # HP urgency
    if my_hp <= 1:
        hp_frac = 0.95
    elif my_hp <= 2:
        hp_frac = 0.88
    elif my_hp <= 3:
        hp_frac = 0.78
    else:
        hp_frac = base_frac

    frac = max(hp_frac, pressure_frac)

    # Budget safety: don't overbid beyond what we can afford
    bid = my_budget * frac

    # Also cap relative to daily salary to avoid rapid depletion
    cap = DAILY_SALARY * 0.85 if my_hp <= 3 else DAILY_SALARY * 0.65
    bid = min(bid, cap)

    # If budget is tiny, just spend what we can
    if my_budget <= 1.0:
        return float(max(0.0, my_budget))

    # Keep bid non-negative
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
    day = day_context.get('day', 0)

    # Collect alive opponents and their yesterday bids
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

    # If no one is alive, bid conservatively
    if not alive_opps:
        return float(min(my_status.get('budget', 0.0), DAILY_SALARY * 0.4))

    # Use yesterday's max bid as a proxy for Cindy/Alex aggressiveness
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else 0.0

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))

    # Estimate how many units of water exist (not used directly for indexing, but for scaling)
    # supply is between 15 and 25; map to an intensity factor
    if supply <= MIN_SUPPLY:
        intensity = 0.85
    elif supply >= MAX_SUPPLY:
        intensity = 1.05
    else:
        intensity = 0.85 + (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) * (1.05 - 0.85)

    # If my hp is low, I must secure water: bid more aggressively.
    # If my hp is healthy, I can undercut slightly above last top bids.
    if my_hp <= 2.0:
        target = max(highest_prev_bid * 1.03, second_prev_bid + 6.0) * intensity
    elif my_hp <= 4.0:
        target = max(highest_prev_bid * 1.02, second_prev_bid + 4.0) * intensity
    else:
        # Healthy: bid a small premium over yesterday's max to try to win without burning budget
        target = max(highest_prev_bid + 2.0, second_prev_bid + 3.0) * intensity

    # Hard caps to avoid overspending
    # Keep within a fraction of budget; also avoid bidding far beyond typical daily salary scale.
    cap = my_budget
    # If Cindy spent ~147, bidding around 120-160 is plausible; cap at 1.8*salary to be safe.
    cap = min(cap, DAILY_SALARY * 1.8)

    bid = float(min(cap, max(0.0, target)))

    # If budget is extremely low, bid what we can
    if my_budget <= 5.0:
        return float(my_budget)

    # Ensure bid is at least a minimal competitive amount when supply is high
    min_competitive = 0.25 * DAILY_SALARY * intensity
    if bid < min_competitive and my_hp > 2.0:
        bid = min(cap, min_competitive)

    return float(bid)
"""
