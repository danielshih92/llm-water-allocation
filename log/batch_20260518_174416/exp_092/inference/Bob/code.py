# ============================================================
# Experiment: exp_092
# Agent: Bob
# Source: exp_092
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

    supply = float(day_context.get('supply', (MIN_SUPPLY + MAX_SUPPLY) / 2.0))
    day = int(day_context.get('day', 0))

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    # If no opponents, bid to meet requirement but don't overspend.
    if not alive_opponents:
        target = min(budget, DAILY_SALARY * 0.55)
        return max(0.0, target)

    # Read only yesterday's immediate behavior.
    prev_bids = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    prev_bids.append(float(b))
                except Exception:
                    pass

    # Base bid: aim around a fraction of daily salary to avoid unnecessary price.
    # If my hp is low or I've been without water, increase urgency.
    urgency = 0.0
    if hp <= 2:
        urgency += 0.35
    elif hp <= 4:
        urgency += 0.15

    if no_water_days >= 2:
        urgency += 0.25
    elif no_water_days == 1:
        urgency += 0.10

    # Supply pressure: if supply is tight, bid more.
    # supply in [15,25], map to [0,1]
    supply_tightness = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_tightness = (float(MAX_SUPPLY) - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    supply_tightness = max(0.0, min(1.0, supply_tightness))

    base_fraction = 0.55 + urgency + 0.15 * supply_tightness

    # If an opponent previously bid extremely high, we counter modestly to avoid losing allocation.
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        # Thresholds relative to salary.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # They were likely fighting for survival; raise bid but cap by budget.
            counter_fraction = 0.70 + 0.20 * supply_tightness
            if hp <= 2:
                counter_fraction = 0.90
            target = min(budget, DAILY_SALARY * counter_fraction)
            return max(0.0, target)
        elif highest_prev_bid >= DAILY_SALARY * 0.60:
            # Mild counter.
            counter_fraction = base_fraction + 0.10
            target = min(budget, DAILY_SALARY * counter_fraction)
            return max(0.0, target)

    # Default: bid based on urgency and supply tightness.
    target = min(budget, DAILY_SALARY * base_fraction)

    # Ensure we don't bid trivially low when supply is near requirement.
    # If supply is close to WATER_REQ, increase slightly.
    if supply <= float(WATER_REQ) + 1.0:
        target = min(budget, max(target, DAILY_SALARY * 0.65))

    return max(0.0, target)
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

    supply = day_context['supply']
    day = day_context['day']

    # Identify alive opponents and extract yesterday bids
    alive_opps = []
    yesterday_bids = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)
            prev = o.get('previous_trace', {}) or {}
            if prev and prev.get('bid') is not None:
                yesterday_bids.append(prev.get('bid'))

    # If no opponents, conserve
    if not alive_opps:
        return max(0, min(my_status['budget'], int(DAILY_SALARY * 0.4)))

    # Reaction to yesterday's pressure
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0

    # Estimate how many water units are likely to be rationed today
    # (used only to scale aggressiveness, not for exact indexing)
    # Supply is between 15 and 25, so water units are roughly 1 or 2.
    # We'll prefer 2 units when supply is high.
    likely_units = 1
    if supply >= (MIN_SUPPLY + MAX_SUPPLY) / 2:
        likely_units = 2

    # Core bidding policy
    # - If someone bid extremely high yesterday, they likely needed water.
    #   Bid to secure at least one unit but stay slightly below the top pressure.
    # - If my hp is low or I have many no-water days, bid more.
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    # Base bid depends on expected units
    if likely_units >= 2:
        base = int(DAILY_SALARY * 0.55)
    else:
        base = int(DAILY_SALARY * 0.48)

    # Urgency adjustments
    urgency = 0
    if hp <= 2:
        urgency += 1
    if hp <= 3:
        urgency += 1
    if no_water_days >= 1:
        urgency += 1

    # Pressure adjustment from yesterday
    # Thresholds tuned to the provided trace magnitudes (~86-114).
    if highest_prev_bid >= int(DAILY_SALARY * 0.95):
        # Very high pressure: bid close but not equal to avoid overspending
        target = int(highest_prev_bid * 0.92)
    elif highest_prev_bid >= int(DAILY_SALARY * 0.80):
        target = int(highest_prev_bid * 0.85)
    else:
        target = base

    # Apply urgency
    if urgency >= 2:
        target = int(max(target, DAILY_SALARY * 0.75))
    elif urgency == 1:
        target = int(max(target, DAILY_SALARY * 0.62))

    # Ensure we don't bid more than budget
    bid = max(0, min(budget, target))

    # Small day-based variation to avoid ties being consistently exploited
    # (bounded to +/- 3%)
    jitter = 1.0
    if day is not None:
        # deterministic jitter using day parity
        if int(day) % 2 == 0:
            jitter = 0.98
        else:
            jitter = 1.02
    bid = int(max(0, min(budget, bid * jitter)))

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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    # Collect immediate yesterday traces for alive opponents
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    # Baseline: bid enough to not be starved, but avoid war
    # If supply is higher, water is easier to obtain; bid less.
    if supply >= 22.5:
        base_bid = DAILY_SALARY * 0.45
    elif supply <= 17.5:
        base_bid = DAILY_SALARY * 0.62
    else:
        base_bid = DAILY_SALARY * 0.52

    # React to yesterday behavior: if many opponents ended with 0 budget or very low hp, they likely overbid.
    low_hp_count = 0
    zero_budget_count = 0
    prev_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        prev_bid = prev.get('bid', None)
        if prev_bid is not None:
            try:
                prev_bids.append(float(prev_bid))
            except Exception:
                pass
        prev_hp_after = prev.get('hp_after', None)
        prev_budget_after = prev.get('budget_after', None)
        if prev_hp_after is not None:
            try:
                if float(prev_hp_after) <= 0.0:
                    low_hp_count += 1
            except Exception:
                pass
        if prev_budget_after is not None:
            try:
                if float(prev_budget_after) <= 0.0:
                    zero_budget_count += 1
            except Exception:
                pass

    # If opponents were punished yesterday (overbidding), we can underbid slightly.
    pressure = 0
    pressure += low_hp_count
    pressure += zero_budget_count

    # If my hp is low or I have gone without water, increase bid to survive.
    if my_hp <= 2.0 or my_no_water_days >= 2:
        urgency = 1
    else:
        urgency = 0

    # If there is evidence of high bids yesterday, avoid matching the maximum; target just above a lower quantile.
    if prev_bids:
        sorted_bids = sorted(prev_bids)
        # Use median-ish target to avoid extremes; ensure index is int.
        median_idx = int(len(sorted_bids) // 2)
        median_bid = float(sorted_bids[median_idx])
        # If there were many high bids, nudge up a bit.
        high_count = sum(1 for b in prev_bids if b >= DAILY_SALARY * 0.8)
        high_ratio = float(high_count) / float(len(prev_bids)) if len(prev_bids) > 0 else 0.0
    else:
        median_bid = base_bid
        high_ratio = 0.0

    # Compute target bid
    target = base_bid

    # If opponents got eliminated/emptied budgets yesterday, reduce bid.
    if pressure >= 2:
        target *= 0.90
    elif pressure == 1:
        target *= 0.97

    # If opponents were bidding aggressively yesterday, increase slightly but not to their max.
    if high_ratio >= 0.34:
        target *= 1.08

    # Urgency override
    if urgency:
        target = max(target, DAILY_SALARY * 0.75)

    # Safety: ensure we don't bid more than budget
    max_affordable = max(0.0, my_budget)

    # Also cap bids based on supply scarcity: fewer water units => slightly higher bids
    # Approximate scarcity factor using supply relative to WATER_REQ.
    # Higher scarcity => higher bid.
    scarcity = 1.0
    if supply > 0:
        scarcity = float(WATER_REQ) / float(supply)
    # scarcity in roughly [0.36..0.6]; map to multiplier range [0.95..1.15]
    if scarcity >= 0.55:
        target *= 1.12
    elif scarcity <= 0.40:
        target *= 0.96

    # Final clamp
    if target > max_affordable:
        bid = max_affordable
    else:
        bid = target

    # Ensure non-negative and at least a minimal bid if possible
    if bid < 0.0:
        bid = 0.0
    # If budget is tiny, still bid it (game likely uses highest bids to allocate water)
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

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']

    # Alive opponents and their previous-day bids
    alive_opps = []
    prev_bids = []
    for opp_id, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(opp_id)
            prev = o.get('previous_trace', {})
            b = prev.get('bid', None)
            if b is not None:
                prev_bids.append(float(b))

    # If no info, bid a safe mid value
    if not alive_opps or not prev_bids:
        base = DAILY_SALARY * 0.55
        return float(min(budget, base))

    highest_prev = max(prev_bids)
    avg_prev = sum(prev_bids) / float(len(prev_bids))

    # Supply pressure: lower supply => more likely everyone bids high
    # Map supply to a multiplier in [0.9, 1.2]
    if MAX_SUPPLY - MIN_SUPPLY > 0:
        t = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        t = 0.5
    # t in [0,1] ideally; clamp
    if t < 0.0:
        t = 0.0
    if t > 1.0:
        t = 1.0
    supply_mult = 1.2 - 0.3 * t  # 1.2 at 15, 0.9 at 25

    # If we are low HP, increase willingness to pay.
    hp_mult = 1.0
    if hp <= 1:
        hp_mult = 1.35
    elif hp == 2:
        hp_mult = 1.25
    elif hp == 3:
        hp_mult = 1.15
    elif hp >= 8:
        hp_mult = 0.95

    # Use opponent trace: if they were bidding very high yesterday, bid slightly below the top
    # to avoid budget burn but still compete.
    # Alex died (hp_after likely <=0) with high bids; we don't know agent identity here reliably,
    # but a very high highest_prev indicates overbidding pressure.
    if highest_prev >= DAILY_SALARY * 0.85:
        target = avg_prev * 0.75 + highest_prev * 0.25
    else:
        target = max(DAILY_SALARY * 0.45, avg_prev * 0.7)

    # Apply multipliers and keep within budget
    bid = target * supply_mult * hp_mult

    # Ensure we don't overpay relative to our budget; also ensure some minimum viable bid
    # (game may require positive bids to secure water).
    min_bid = 5.0
    if bid < min_bid:
        bid = min_bid

    if bid > budget:
        bid = budget

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

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    # Collect yesterday bids from alive opponents only
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # Baseline: infer aggressiveness from survivors' typical bids
    # Yesterday survivors (Alex/Eric) bid around ~66; aim slightly below to win at lower cost.
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / max(1, len(yesterday_bids))
    else:
        highest_prev_bid = 0.0
        avg_prev_bid = 0.0

    # Supply pressure heuristic: with medium supply, we can usually match their ~66 bids.
    # If supply is high, we can bid less; if low, bid more.
    supply_mid = (MIN_SUPPLY + MAX_SUPPLY) / 2.0  # 20
    if supply >= supply_mid:
        supply_factor = 0.95
    else:
        supply_factor = 1.05

    # HP/no-water urgency
    if my_hp <= 2.0 or my_no_water_days >= 2:
        urgency = 1.0
    elif my_hp <= 4.0:
        urgency = 0.9
    else:
        urgency = 0.75

    # Target bid
    # If others were very aggressive yesterday (>=~73), we must respond; otherwise slightly undercut.
    if highest_prev_bid >= 70.0:
        target = highest_prev_bid * 0.98
    else:
        # Undercut around avg/survivor level
        # If avg_prev_bid is small, still keep a meaningful bid.
        base = avg_prev_bid if avg_prev_bid > 0.0 else (DAILY_SALARY * 0.55)
        target = base * 0.92

    target = target * supply_factor * (1.0 + (1.0 - urgency) * 0.15)

    # Cap by budget and keep within reasonable fraction of daily salary
    max_reasonable = DAILY_SALARY * 0.85
    min_reasonable = DAILY_SALARY * 0.35

    bid = max(min_reasonable, min(target, max_reasonable))
    bid = min(bid, my_budget)

    # If budget is tiny, just spend what we can.
    if my_budget <= 0.0:
        return 0.0

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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for k, o in opponents_status.items():
        if o.get('alive'):
            alive_opps.append((k, o))

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from immediate previous_trace only
    yesterday_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # If Cindy was alive and bidding high yesterday, it indicates willingness to pay.
    # We react by bidding enough to not lose the allocation when supply is tighter.
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = (sum(yesterday_bids) / len(yesterday_bids)) if yesterday_bids else 0.0

    # Supply pressure: lower supply -> higher chance to be rationed -> bid more.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))
    tightness = 1.0 - supply_ratio

    # Urgency from hp and consecutive no-water days.
    urgency = 0.0
    if hp <= 2.0:
        urgency += 1.2
    elif hp <= 4.0:
        urgency += 0.7
    else:
        urgency += 0.3

    if no_water_days >= 2:
        urgency += 0.8
    elif no_water_days == 1:
        urgency += 0.4

    # Near end of episode, increase aggressiveness.
    # episode_days is 10 in meta-round, so day index 1..10; boost after day 7.
    endgame_boost = 0.0
    if day >= 8:
        endgame_boost = 0.25
    elif day >= 6:
        endgame_boost = 0.12

    # Base target bid: aim around a fraction of the highest yesterday bid,
    # adjusted by tightness and urgency.
    # Cindy's pattern suggests high bids win; we do not match blindly.
    target = 0.0
    if highest_prev_bid > 0.0:
        # Bid slightly above a percentile of yesterday bids to beat the typical contender.
        # Using avg and highest to avoid needing sorting.
        typical = 0.6 * avg_prev_bid + 0.4 * highest_prev_bid
        target = typical * (0.55 + 0.25 * tightness + 0.25 * urgency + endgame_boost)
    else:
        target = DAILY_SALARY * (0.45 + 0.25 * tightness + 0.2 * urgency + endgame_boost)

    # Clamp to budget and sensible bounds.
    # If we are low on budget, still bid enough to compete when urgency is high.
    min_compete = DAILY_SALARY * (0.25 + 0.25 * tightness + 0.15 * urgency)
    bid = max(min_compete * (0.7 if highest_prev_bid > 0 else 1.0), target)

    # If my budget is tiny, scale down proportionally.
    if budget <= 0.0:
        return 0.0

    # Keep bid within budget and avoid extreme overpaying.
    max_reasonable = min(budget, DAILY_SALARY * (0.95 if urgency >= 1.0 else 0.7))
    bid = min(bid, max_reasonable)

    # Also, if supply is abundant, reduce bid.
    if tightness < 0.25:
        bid *= 0.8

    # Final safety clamp
    bid = max(0.0, min(bid, budget))
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

    # Alive opponents and yesterday bids
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    yesterday_bids.append(float(b))
                except Exception:
                    pass

    # Estimate how aggressive the field was yesterday
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    # Supply pressure: fewer units available means higher chance others overbid
    # Target is to bid enough to beat typical moderate bids but avoid Cindy/Eric-like extremes.
    if supply <= float(WATER_REQ) + 1.0:
        supply_tight = True
    else:
        supply_tight = False

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Base bid: conservative to avoid budget depletion, but ensure survival.
    # Scale with HP risk and tight supply.
    if hp <= 2.0 or no_water_days >= 2:
        base = DAILY_SALARY * (0.65 if not supply_tight else 0.85)
    else:
        base = DAILY_SALARY * (0.45 if not supply_tight else 0.60)

    # React to yesterday: if highest bids were extreme, don't mirror them.
    # If field was moderate, slightly increase to secure water.
    if highest_prev_bid >= DAILY_SALARY * 1.05:
        # Cindy/Eric-like overbidding occurred; stay below their level.
        base = min(base, DAILY_SALARY * 0.62)
    else:
        # If no extreme spending, match a bit more.
        base = max(base, DAILY_SALARY * 0.50)

    # Convert base to a final bid with safety cap.
    # Also consider that supply is at most 25; bidding shouldn't exceed what we can afford.
    # Ensure we never bid above budget.
    bid = min(budget, base)

    # If budget is very low, bid what we can to avoid immediate death.
    if budget <= DAILY_SALARY * 0.25:
        bid = min(budget, DAILY_SALARY * 0.30)

    # Small day-based adjustment: later days require more reliability.
    # (No long history; just use day index.)
    if day >= 7:
        bid = min(budget, bid * 1.10)

    # Final integer-ish bid (game may accept float; keep float).
    if bid < 0.0:
        bid = 0.0
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # If we are already in danger, bid aggressively.
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from trace for immediate reaction.
    prev_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate how many full water units the supply can cover.
    # (We only use it to scale bids; indices not needed.)
    capacity_units = max(1.0, supply / float(WATER_REQ))

    # Core strategy:
    # - If Cindy likely keeps bidding near 90 (survived with max bid), we bid slightly below/around 90.
    # - If yesterday saw extreme low bids (others died), we still bid enough to secure water.
    # - If our hp is low or no_water_days is high, we increase bid.

    # Identify Cindy's yesterday bid if present.
    cindy_prev = None
    for opp_id, opp in alive_opps:
        if str(opp_id) == 'Cindy':
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    cindy_prev = float(prev['bid'])
                except Exception:
                    cindy_prev = None

    # Base target bid
    if cindy_prev is not None and cindy_prev >= DAILY_SALARY * 0.95:
        target = DAILY_SALARY * 0.88  # try to beat her without maxing out
    elif highest_prev_bid >= DAILY_SALARY * 0.85:
        target = min(DAILY_SALARY * 0.90, highest_prev_bid - 1.0)
    else:
        # Mid pressure: bid enough to secure, but conserve budget.
        target = max(DAILY_SALARY * 0.55, (highest_prev_bid + 5.0) if highest_prev_bid > 0 else DAILY_SALARY * 0.60)

    # Risk adjustment
    if hp <= 2.0:
        target = max(target, DAILY_SALARY * 0.95)
    elif hp <= 4.0:
        target = max(target, DAILY_SALARY * 0.80)

    if no_water_days >= 2:
        target = max(target, DAILY_SALARY * 0.85)

    # Budget constraint and slight day-based taper to avoid running out by episode end.
    # episode_days is fixed at 10 in meta, so day 1-10: taper near end.
    # Use day only for small adjustment.
    taper = 1.0
    if day >= 8:
        taper = 0.95
    if day >= 9:
        taper = 0.90

    bid = min(budget, target * taper)

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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context['supply'])
    day = day_context['day']

    alive_opponents = [o for o in opponents_status.values() if o.get('alive')]

    # Base bid: aim to cover our own requirement with a buffer.
    # If supply is near minimum, competition is tighter -> bid higher.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    tightness = 1.0 - max(0.0, min(1.0, supply_ratio))  # 1 when supply is low

    # React to yesterday: if any opponent bid extremely high, they likely tried to win early.
    # Avoid mirroring; instead slightly undercut unless our hp is critical.
    highest_prev_bid = None
    any_extreme_prev = False
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            b = float(prev['bid'])
            if highest_prev_bid is None or b > highest_prev_bid:
                highest_prev_bid = b
            if b >= DAILY_SALARY * 0.85:
                any_extreme_prev = True

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # If we're in danger, bid aggressively.
    if my_hp <= 2 or no_water_days >= 2:
        target = DAILY_SALARY * (0.85 + 0.1 * tightness)
    else:
        # Otherwise, moderate bid. If others previously went extreme, we undercut.
        if any_extreme_prev:
            # Keep below extreme pressure.
            target = DAILY_SALARY * (0.45 + 0.15 * tightness)
            if highest_prev_bid is not None:
                target = min(target, highest_prev_bid - 5.0)
        else:
            target = DAILY_SALARY * (0.55 + 0.2 * tightness)

    # Ensure bid is feasible with our budget.
    bid = min(my_budget, max(0.0, target))

    # Also cap bid to a reasonable fraction of budget to avoid running out.
    # If budget is already small, just spend what we can.
    if my_budget > DAILY_SALARY:
        bid = min(bid, DAILY_SALARY * 0.95)

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

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Read yesterday bids from immediate previous_trace
    prev_bids = []
    prev_by_id = {}
    for opp_id, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                b = float(b)
            except Exception:
                continue
            prev_bids.append(b)
            prev_by_id[opp_id] = b

    # Estimate how many allocations we might need: if supply is tight vs WATER_REQ, prioritize.
    # Since bids compete for limited supply, higher supply reduces pressure.
    # supply_per_unit_factor: how many WATER_REQ blocks fit
    blocks = supply / float(WATER_REQ) if WATER_REQ > 0 else 0.0
    # If blocks < 2, water is scarce; if >=2, less scarce.
    scarce = blocks < 2.0

    # Determine top opponent bid pressure
    top_bid = max(prev_bids) if prev_bids else 0.0

    # Base bid target: aim around a fraction of daily salary.
    # Undercut the top bid when it was very high to win at lower cost.
    if scarce:
        base = DAILY_SALARY * 0.62
    else:
        base = DAILY_SALARY * 0.48

    # If we are in danger (no water days or low hp), bid harder.
    if my_hp <= 2 or my_no_water_days >= 1:
        base = max(base, DAILY_SALARY * 0.82)

    # If someone previously bid extremely high, slightly undercut.
    # Use int() only for list indices; here we just compare floats.
    if top_bid >= DAILY_SALARY * 0.85:
        # Underbid just enough: target a bit below top_bid but still above our base.
        target = max(base, top_bid - 2.0)
    elif top_bid >= DAILY_SALARY * 0.65:
        target = max(base, top_bid - 4.0)
    else:
        # No extreme pressure: bid near base but not too high.
        target = base

    # Safety cap: never bid above what we can afford.
    # Also avoid reckless spending when hp is healthy.
    if my_hp >= 7 and my_no_water_days == 0:
        cap = DAILY_SALARY * 0.75
    else:
        cap = DAILY_SALARY * 0.95

    bid = min(my_budget, min(cap, target))

    # If budget is extremely low, still bid something to avoid guaranteed no-water days.
    if bid <= 0.0:
        bid = min(my_budget, DAILY_SALARY * 0.2)

    return float(bid)
"""
