# ============================================================
# Experiment: exp_037
# Agent: Bob
# Source: exp_037
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = day_context['supply']
    day = day_context['day']

    # Alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # If no opponents, take as much as needed but cap by salary
    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.6)

    # Read yesterday's immediate bids
    yesterday_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # If we can't infer, default mid aggression
    if not yesterday_bids:
        base = DAILY_SALARY * 0.55
        if my_status['hp'] <= 2 or my_status['no_water_days'] >= 2:
            base = DAILY_SALARY * 0.85
        return min(my_status['budget'], base)

    # Opponent aggressiveness from yesterday
    highest_prev_bid = max(yesterday_bids)
    avg_prev_bid = sum(yesterday_bids) / float(len(yesterday_bids))

    # Supply pressure: if supply is tight (near MIN_SUPPLY), bidding competition likely higher
    # Use int() for any index-like operations; here we only compare values.
    tight_supply = supply <= float(MIN_SUPPLY) + 1.0

    # Decide bid
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # They were very aggressive; counter with slightly lower to preserve budget but still win share
        if my_status['hp'] > 3 and my_status['no_water_days'] <= 1:
            bid = DAILY_SALARY * (0.28 if not tight_supply else 0.38)
        else:
            bid = DAILY_SALARY * (0.75 if not tight_supply else 0.85)
    else:
        # They were not extremely aggressive; aim just above their average/highest to secure allocation
        # Keep within a budget-safe range.
        target = max(highest_prev_bid + 1.5, avg_prev_bid + 0.8)
        # If we are in danger, push higher.
        if my_status['hp'] <= 2 or my_status['no_water_days'] >= 2:
            target = max(target, DAILY_SALARY * (0.75 if tight_supply else 0.65))
        else:
            target = min(target, DAILY_SALARY * (0.65 if tight_supply else 0.55))
        bid = target

    # Hard caps: cannot exceed budget; also keep bid reasonable relative to salary.
    bid = min(bid, my_status['budget'], DAILY_SALARY * 0.95)

    # Ensure at least some bid if budget allows
    if bid <= 0 and my_status['budget'] > 0:
        bid = min(my_status['budget'], DAILY_SALARY * 0.2)

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

    # Alive opponents
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive'):
            alive.append(o)

    # Baseline: aim to get at least 1 unit of our need when supply is tight.
    # Convert to a rough bid target: bid scales with desired share.
    # With supply between 15-25 and WATER_REQ=9, typical allocation competition is meaningful.
    tight = supply <= 18.0

    # Use yesterday trace to infer aggressiveness
    prev_bids = []
    prev_hp_after = []
    for o in alive:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev.get('bid', 0.0)))
            prev_hp_after.append(float(prev.get('hp_after', o.get('hp', 0.0))))

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])

    # If we are in danger, bid harder.
    if my_hp <= 2.0:
        cap = my_budget
        bid = min(cap, DAILY_SALARY * (0.85 if tight else 0.75) + 10.0)
        return float(bid)

    # If any opponent bid extremely high yesterday, assume they are competing for survival.
    if prev_bids:
        max_prev = max(prev_bids)
        # Cindy-like aggressiveness: ~142.5 in trace.
        if max_prev >= DAILY_SALARY * 1.45:
            # Don't fully mirror; just secure enough. Use higher bid when supply is tight.
            base = DAILY_SALARY * (0.70 if tight else 0.55)
            # Slightly increase if our hp is mid-low.
            if my_hp <= 5.0:
                base += 15.0
            bid = min(my_budget, base)
            return float(bid)

        # Alex-like mid-high pressure
        if max_prev >= DAILY_SALARY * 1.25:
            base = DAILY_SALARY * (0.62 if tight else 0.50)
            if my_hp <= 6.0:
                base += 10.0
            # Ensure bid at least above a low-bid floor
            bid = min(my_budget, max(base, DAILY_SALARY * 0.45))
            return float(bid)

        # Eric-like low pressure
        base = DAILY_SALARY * (0.52 if tight else 0.45)
        if my_hp <= 6.5:
            base += 8.0
        bid = min(my_budget, base)
        return float(bid)

    # No trace info: default moderate bidding
    base = DAILY_SALARY * (0.55 if tight else 0.48)
    if my_hp <= 6.0:
        base += 10.0
    bid = min(my_budget, base)
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

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opponents:
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday bids from previous_trace only (immediate reaction)
    prev_bids = []
    prev_bid_by_agent = {}
    for agent_id, opp in opponents_status.items():
        if not opp.get('alive', False):
            continue
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                b = float(b)
            except Exception:
                b = None
        if b is not None:
            prev_bids.append(b)
            prev_bid_by_agent[agent_id] = b

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    # Estimate how aggressive the field was yesterday
    # If someone was near our daily salary, they likely fought for water; we match moderately.
    pressure = 0.0
    if prev_bids:
        pressure = highest_prev_bid

    # Supply pressure: when supply is low, bids should be higher.
    # For our fixed WATER_REQ=9, supply range 15..25 implies scarcity varies.
    scarcity = 0.0
    if supply <= float(MIN_SUPPLY):
        scarcity = 1.0
    elif supply >= float(MAX_SUPPLY):
        scarcity = 0.0
    else:
        scarcity = (float(MAX_SUPPLY) - supply) / (float(MAX_SUPPLY) - float(MIN_SUPPLY))

    # Base bid: target the lower band that kept Alex/Eric alive while avoiding Cindy's high spending.
    # Use hp/no_water_days to decide whether to escalate.
    # If we are in danger, bid more; otherwise keep moderate.
    risk = 0.0
    if hp <= 2.0:
        risk = 1.0
    elif hp <= 4.0:
        risk = 0.6
    else:
        risk = 0.2
    if no_water_days >= 2:
        risk = max(risk, 0.7)

    # Determine target bid using yesterday pressure and scarcity.
    # If yesterday highest bid was high, we raise slightly but not to Cindy-level.
    # Otherwise, keep near ~0.55*DAILY_SALARY (Eric/Alex band) adjusted by scarcity.
    baseline = DAILY_SALARY * 0.55
    if pressure >= DAILY_SALARY * 1.25:
        target = baseline + DAILY_SALARY * 0.15 * scarcity + DAILY_SALARY * 0.10 * risk
    elif pressure >= DAILY_SALARY * 0.95:
        target = baseline + DAILY_SALARY * 0.10 * scarcity + DAILY_SALARY * 0.07 * risk
    else:
        target = baseline + DAILY_SALARY * 0.08 * scarcity + DAILY_SALARY * 0.05 * risk

    # If our hp is very low, we must secure water: bid closer to daily salary.
    if hp <= 2.0:
        target = max(target, DAILY_SALARY * 0.85)
    elif hp <= 3.0:
        target = max(target, DAILY_SALARY * 0.65)

    # Never exceed budget; also keep a ceiling to avoid waste.
    ceiling = min(budget, DAILY_SALARY * (1.0 + 0.25 * scarcity))
    bid = min(target, ceiling)

    # Ensure non-negative and at least a tiny bid if budget allows
    if bid < 0.0:
        bid = 0.0
    if bid == 0.0 and budget > 0.0:
        bid = min(budget, 1.0)

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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    # If no opponents alive, conserve budget
    if not alive_opponents:
        bid = DAILY_SALARY * 0.35
        if my_budget < bid:
            bid = my_budget
        return float(max(0.0, bid))

    # Read yesterday bids from previous_trace only
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Supply pressure: lower supply means more likely competition for water
    # Normalize to [0,1]
    if MAX_SUPPLY <= MIN_SUPPLY:
        supply_pressure = 0.5
    else:
        supply_pressure = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)
        if supply_pressure < 0.0:
            supply_pressure = 0.0
        if supply_pressure > 1.0:
            supply_pressure = 1.0

    # Base bid: aim around a fraction of daily salary, adjusted by supply pressure
    base = DAILY_SALARY * (0.45 + 0.25 * supply_pressure)

    # If someone already bid very high yesterday, increment slightly to avoid losing
    # without going all-in.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # If I'm healthy, outbid slightly; if low hp, bid more aggressively
        if my_hp > 3.0:
            target = max(base, highest_prev_bid * 0.92)
        else:
            target = max(base, highest_prev_bid * 0.98)
    else:
        # Otherwise, bid just above the expected clearing pressure
        target = max(base, highest_prev_bid * 0.70 + 5.0)

    # Urgency from my own hp/no_water_days
    # If I've already gone several days without water, increase bid.
    if my_hp <= 2.5 or my_no_water_days >= 2:
        target *= 1.25
    elif my_hp >= 6.0 and my_no_water_days <= 0:
        target *= 0.85

    # Late-episode pressure: closer to day 10, more likely to need water
    if day >= 8:
        target *= 1.12

    # Budget safety: never exceed budget; keep some reserve
    # Reserve fraction increases when hp is low? Actually reserve decreases when low hp.
    if my_hp <= 2.5:
        reserve_frac = 0.05
    elif my_hp <= 4.0:
        reserve_frac = 0.10
    else:
        reserve_frac = 0.20

    max_affordable = max(0.0, my_budget * (1.0 - reserve_frac))
    bid = min(float(max_affordable), float(target))

    # Ensure non-negative
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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive = []
    for oid, o in opponents_status.items():
        if o and o.get('alive', False):
            alive.append(o)

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # React to yesterday's pressure using only previous_trace.
    prev_bids = []
    for o in alive:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Supply-based target: when supply is tight, increase bids to avoid water shortage.
    # supply in [15,25] => capacity roughly 1..2 units of WATER_REQ.
    # Use integer thresholds explicitly.
    tight = supply <= float(MIN_SUPPLY + 2.5)
    mid = (supply > float(MIN_SUPPLY + 2.5)) and (supply < float(MAX_SUPPLY - 2.5))

    # If we are in danger (low hp or consecutive no-water days), bid to secure water.
    danger = (hp <= 2.5) or (no_water_days >= 2)

    # Aggression calibration from yesterday: if someone bid very high, they likely tried to outbid.
    # Their max bids yesterday were ~175; use a relative threshold.
    very_high_prev = highest_prev_bid >= (DAILY_SALARY * 1.6)  # ~144
    high_prev = highest_prev_bid >= (DAILY_SALARY * 1.2)     # ~108

    # Base bid levels
    if danger:
        base = DAILY_SALARY * (0.75 if tight else 0.65)
    else:
        base = DAILY_SALARY * (0.55 if mid else (0.6 if tight else 0.5))

    # Adjust based on observed opponent pressure
    if very_high_prev:
        base *= 1.08
    elif high_prev:
        base *= 1.03
    else:
        base *= 0.98

    # If early in episode, slightly more aggressive to build hp buffer.
    if day <= 3:
        base *= 1.06

    # Convert to final bid with budget cap and non-negative.
    bid = min(budget, base)

    # Ensure bid is at least a small fraction to participate when supply is tight.
    if tight and bid < DAILY_SALARY * 0.25:
        bid = min(budget, DAILY_SALARY * 0.25)

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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # If no one else is alive, conserve
    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.35)

    # Use only yesterday's previous_trace bids for immediate reaction
    prev_bids = []
    for o in alive_opps:
        pt = o.get('previous_trace', None)
        if isinstance(pt, dict):
            b = pt.get('bid', None)
            if b is not None:
                prev_bids.append(float(b))
        elif isinstance(pt, list) and len(pt) > 0:
            last = pt[-1]
            if isinstance(last, dict) and last.get('bid', None) is not None:
                prev_bids.append(float(last['bid']))

    # Determine aggressiveness from yesterday
    # If bids were high, we must bid competitively; otherwise bid moderately.
    if prev_bids:
        max_prev = max(prev_bids)
        # Also consider a lower quantile proxy: average of top two if available
        sorted_b = sorted(prev_bids, reverse=True)
        top2_avg = sum(sorted_b[:2]) / float(min(2, len(sorted_b)))

        # Pressure thresholds based on observed meta-round behavior (~100-111)
        if max_prev >= DAILY_SALARY * 0.95 or top2_avg >= DAILY_SALARY * 0.9:
            # If we are at risk (low hp), bid higher to avoid water starvation.
            if my_status['hp'] <= 2 or my_status['no_water_days'] >= 1:
                target = max(DAILY_SALARY * 0.95, top2_avg * 1.03)
            else:
                # Bid slightly above the lower aggressive band to win water without overpaying.
                target = max(DAILY_SALARY * 0.8, top2_avg * 0.98)
        else:
            # Less aggressive field
            if my_status['hp'] <= 2 or my_status['no_water_days'] >= 2:
                target = DAILY_SALARY * 0.85
            else:
                target = max(DAILY_SALARY * 0.55, top2_avg * 0.9)
    else:
        # No trace info; default moderate bid
        if my_status['hp'] <= 2 or my_status['no_water_days'] >= 2:
            target = DAILY_SALARY * 0.85
        else:
            target = DAILY_SALARY * 0.55

    # Supply-aware adjustment: when supply is closer to MAX, we can bid slightly less.
    # supply is in [15,25]
    if supply >= 22.0:
        target *= 0.95
    elif supply <= 17.0:
        target *= 1.05

    # Convert to integer bid and cap by budget
    bid = int(round(target))
    if bid < 0:
        bid = 0

    # Ensure we don't exceed budget
    bid = min(bid, int(my_status['budget']))

    # If budget is extremely small, bid whatever we can but avoid zero when others are aggressive.
    if bid == 0 and my_status.get('budget', 0) > 0:
        # Small non-zero bid
        bid = 1

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

    my_hp = int(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append(opp)

    if not alive_opps:
        cap = DAILY_SALARY * 0.4
        return min(my_budget, cap)

    # Extract yesterday bids from immediate previous_trace only
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Baseline from yesterday: try to undercut the high bidders but stay competitive
    # If we saw high pressure, slightly increase.
    if prev_bids:
        sorted_bids = sorted(prev_bids)
        # Use median-ish and lower-quantile to avoid overbidding
        n = len(sorted_bids)
        lower = sorted_bids[int((n - 1) * 0.33)]
        upper = sorted_bids[int((n - 1) * 0.66)]
        max_prev = max(sorted_bids)

        # Pressure indicator
        high_pressure = max_prev >= DAILY_SALARY * 0.85
        mid_pressure = upper >= DAILY_SALARY * 0.75

        # Supply scaling: when supply is tight, bid more
        # Map supply in [MIN_SUPPLY, MAX_SUPPLY] to [0,1]
        denom = float(MAX_SUPPLY - MIN_SUPPLY)
        if denom <= 0.0:
            tightness = 0.5
        else:
            tightness = (float(MAX_SUPPLY) - supply) / denom
            if tightness < 0.0:
                tightness = 0.0
            if tightness > 1.0:
                tightness = 1.0

        # HP/budget urgency
        hp_urgent = my_hp <= 2 or my_no_water_days >= 2
        budget_tight = my_budget <= DAILY_SALARY * 0.8

        # Target bid
        if hp_urgent or budget_tight:
            target = DAILY_SALARY * (0.85 if high_pressure else 0.65)
        else:
            # Compete near the lower cluster plus a small premium
            premium = 5.0 + 10.0 * tightness
            if high_pressure:
                premium += 8.0
            elif mid_pressure:
                premium += 4.0
            target = lower + premium

        # Keep within reasonable bounds
        min_bid = DAILY_SALARY * 0.35
        max_bid = DAILY_SALARY * (0.95 if high_pressure else 0.75)
        target = max(min_bid, min(target, max_bid))

        return min(my_budget, target)

    # No valid previous bids: simple policy
    denom = float(MAX_SUPPLY - MIN_SUPPLY)
    if denom <= 0.0:
        tightness = 0.5
    else:
        tightness = (float(MAX_SUPPLY) - supply) / denom
        if tightness < 0.0:
            tightness = 0.0
        if tightness > 1.0:
            tightness = 1.0

    if my_hp <= 2 or my_no_water_days >= 2:
        base = DAILY_SALARY * 0.85
    else:
        base = DAILY_SALARY * (0.55 + 0.2 * tightness)

    return min(my_budget, base)
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

    alive_opps = [o for o in opponents_status.values() if o.get('alive', False)]

    # If no opponents alive, spend enough to avoid no-water days.
    if not alive_opps:
        target = DAILY_SALARY * 0.45
        return min(my_status['budget'], target)

    # Read yesterday's immediate behavior from previous_trace
    prev_bids = []
    opp_signals = []
    for opp_id, opp in opponents_status.items():
        if not opp.get('alive', False):
            continue
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            prev_bids.append(float(bid))
        # pressure signal: low hp or long no-water streak
        opp_signals.append((opp.get('hp', 10), opp.get('no_water_days', 0), float(bid) if bid is not None else None))

    avg_prev_bid = sum(prev_bids) / len(prev_bids) if prev_bids else DAILY_SALARY * 0.55
    max_prev_bid = max(prev_bids) if prev_bids else DAILY_SALARY * 0.9

    my_hp = my_status.get('hp', 0)
    my_no_water_days = my_status.get('no_water_days', 0)
    my_budget = my_status.get('budget', 0)

    # Supply pressure: higher supply reduces need to overbid.
    # Normalize supply within [15,25]
    s_norm = (supply - 15.0) / (25.0 - 15.0) if 25.0 != 15.0 else 0.5
    s_norm = max(0.0, min(1.0, s_norm))

    # Determine if opponents were already bidding aggressively (top-tail)
    # Use yesterday max as a proxy for their willingness to pay.
    aggressive = (max_prev_bid >= DAILY_SALARY * 1.45) or (avg_prev_bid >= DAILY_SALARY * 1.1)

    # If any opponent is in extreme danger yesterday (low hp after), raise bid slightly.
    # We can't see their hidden current bids; use trace status/hp_after if present.
    extreme = False
    for opp_id, opp in opponents_status.items():
        if not opp.get('alive', False):
            continue
        prev = opp.get('previous_trace', {}) or {}
        hp_after = prev.get('hp_after', None)
        status = prev.get('status', '')
        if hp_after is not None and float(hp_after) <= 3:
            extreme = True
        if isinstance(status, str) and ('critical' in status.lower() or 'low' in status.lower()):
            extreme = True

    # Base bid: undercut average, but never too low when our hp/no-water is threatened.
    # Also account for supply: at low supply we bid closer to avg_prev_bid.
    # At high supply we bid closer to 0.6*avg_prev_bid.
    if s_norm < 0.5:
        base = avg_prev_bid * 0.95
    else:
        base = avg_prev_bid * 0.75

    # Adjust for our own survival risk.
    if my_hp <= 2 or my_no_water_days >= 2:
        # Must secure water; bid more like the top tail but cap.
        base = max(base, DAILY_SALARY * 1.25)
    elif my_hp <= 4:
        base = max(base, DAILY_SALARY * 1.05)

    # If opponents were aggressive or extreme, increase to beat them with minimal overspend.
    if aggressive:
        base = max(base, avg_prev_bid * 1.05)
    if extreme:
        base = max(base, DAILY_SALARY * 1.15)

    # Final cap: don't chase the absolute max; aim slightly below max_prev_bid unless we are critical.
    if my_hp > 3 and my_no_water_days < 2:
        # try to be competitive but not wasteful
        target = min(base, max_prev_bid * 0.92)
    else:
        target = min(base, max_prev_bid * 0.98)

    # Ensure we at least bid enough to have a chance; also avoid bidding above budget.
    min_reasonable = DAILY_SALARY * 0.35
    target = max(min_reasonable, target)
    return min(my_budget, target)
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

    # React to yesterday bids (immediate behavior)
    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    yesterday_bids.append(float(b))
                except Exception:
                    pass

    # Estimate how many water units exist in this day (heuristic)
    # Ensure indices are int() if used; here we only compute thresholds.
    supply_units = supply / float(WATER_REQ)

    # Tight supply => need to outbid more
    tight_supply = supply <= (MIN_SUPPLY + 2.0)

    # Baseline from yesterday: aim slightly below the median/upper cluster
    if yesterday_bids:
        yesterday_bids_sorted = sorted(yesterday_bids)
        n = len(yesterday_bids_sorted)
        median_bid = yesterday_bids_sorted[int(n // 2)] if n > 0 else DAILY_SALARY * 0.55
        upper_bid = yesterday_bids_sorted[int(max(0, n - 1))] if n > 0 else median_bid

        # If opponents were aggressive (upper cluster near salary), we slightly undercut.
        aggressive = upper_bid >= DAILY_SALARY * 0.85

        # Choose target bid
        if my_hp <= 2.0 or my_no_water_days >= 1:
            # We are under pressure: bid closer to aggressive cluster
            if aggressive:
                target = min(my_budget, max(DAILY_SALARY * 0.65, median_bid * 0.95))
            else:
                target = min(my_budget, max(DAILY_SALARY * 0.55, median_bid * 0.85))
        else:
            # We can conserve budget: undercut typical bids
            if tight_supply:
                # still need to compete
                if aggressive:
                    target = min(my_budget, max(DAILY_SALARY * 0.55, median_bid * 0.85))
                else:
                    target = min(my_budget, max(DAILY_SALARY * 0.45, median_bid * 0.75))
            else:
                if aggressive:
                    target = min(my_budget, max(DAILY_SALARY * 0.45, median_bid * 0.75))
                else:
                    target = min(my_budget, max(DAILY_SALARY * 0.35, median_bid * 0.65))

        # Cap: never exceed a reasonable fraction of budget
        cap = my_budget
        if cap < 0.0:
            cap = 0.0
        return max(0.0, min(float(target), float(cap)))

    # Fallback without yesterday info
    if my_hp <= 2.0 or my_no_water_days >= 1:
        return max(0.0, min(my_budget, DAILY_SALARY * (0.85 if tight_supply else 0.75)))
    return max(0.0, min(my_budget, DAILY_SALARY * (0.55 if tight_supply else 0.45)))
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

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append(o)

    if not alive_opponents:
        return float(min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace only
    yesterday_bids = []
    for o in alive_opponents:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how tight the market is: fewer units when supply is lower
    # (We don't know exact allocation mechanics, so we bias toward mid bids.)
    supply_ratio = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Base willingness: mid-level to beat overbidders without burning budget.
    # If supply is low, raise slightly.
    base = DAILY_SALARY * (0.48 + 0.12 * (1.0 - supply_ratio))

    # If yesterday's max bid was very high, pressure is high; respond.
    if highest_prev_bid >= DAILY_SALARY * 1.6:
        if hp <= 2.5 or no_water_days >= 1:
            bid = DAILY_SALARY * 0.92
        else:
            bid = DAILY_SALARY * 0.62
    elif highest_prev_bid >= DAILY_SALARY * 1.2:
        if hp <= 2.5:
            bid = DAILY_SALARY * 0.80
        else:
            bid = DAILY_SALARY * 0.55
    else:
        # If opponents didn't overbid yesterday, try to secure with a modest edge.
        bid = base

    # Keep bids within budget and avoid extreme overspending.
    # Also, if budget is very low, bid as much as possible without going negative.
    bid = float(min(budget, bid))

    # If critically low HP, spend more aggressively.
    if hp <= 1.5:
        bid = float(min(budget, max(bid, DAILY_SALARY * 0.98)))

    # If we have already gone without water, increase odds.
    if no_water_days >= 2:
        bid = float(min(budget, max(bid, DAILY_SALARY * 0.75)))

    # Final clamp to non-negative
    if bid < 0.0:
        bid = 0.0

    return bid
"""
