# ============================================================
# Experiment: exp_057
# Agent: Bob
# Source: exp_057
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
    day = day_context.get('day', 0)

    my_hp = float(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Read yesterday bids from previous_trace
    prev_bids = []
    prev_bid_by_opp = {}
    for opp_id, opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                bid_val = float(bid)
            except Exception:
                continue
            prev_bids.append(bid_val)
            prev_bid_by_opp[opp_id] = bid_val

    # Fallback if no previous bids
    if not prev_bids:
        if my_hp <= 2 or my_no_water_days >= 2:
            return min(my_budget, DAILY_SALARY * 0.85)
        return min(my_budget, DAILY_SALARY * 0.55)

    highest_prev_bid = max(prev_bids)
    second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev_bid

    # Estimate supply pressure: higher supply means we can be cheaper; lower supply means we must secure water.
    # Normalize using known bounds.
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_norm = 0.5
    supply_norm = max(0.0, min(1.0, float(supply_norm)))

    # If opponents were bidding very high yesterday, they were likely under stress.
    # Exploit by bidding slightly below their likely next move.
    stress_threshold = DAILY_SALARY * 0.85

    # Base bid target to win: slightly above second-highest when supply is tight.
    tightness = 1.0 - supply_norm  # 1 when low supply, 0 when high supply
    win_target = max(second_prev_bid + 1.0, highest_prev_bid * (0.98 if tightness < 0.6 else 1.02))

    # Decide whether to underbid (when they were stressed) or overbid (when they were calm).
    if highest_prev_bid >= stress_threshold:
        # Underbid relative to their pressure; only ramp if we are also in danger.
        if my_hp <= 2 or my_no_water_days >= 2:
            bid = max(win_target * 0.95, DAILY_SALARY * 0.75)
        else:
            bid = max(win_target * 0.70, second_prev_bid + 0.5)
    else:
        # They were not bidding extremely; secure water by bidding moderately above their typical level.
        if my_hp <= 2 or my_no_water_days >= 2:
            bid = max(win_target * 1.05, highest_prev_bid + 2.0)
        else:
            bid = max(win_target * (0.95 + 0.1 * tightness), highest_prev_bid + 1.0)

    # Convert bid into a cap: never exceed what we can pay.
    bid = min(bid, my_budget)

    # Ensure we don't bid trivially low when supply is tight.
    min_reasonable = DAILY_SALARY * (0.35 + 0.25 * tightness)
    if bid < min_reasonable and (my_hp <= 2 or my_no_water_days >= 2 or tightness > 0.6):
        bid = min(my_budget, min_reasonable)

    # If our budget is extremely low, bid what we can.
    if my_budget <= DAILY_SALARY * 0.2:
        return max(0.0, my_budget)

    return float(max(0.0, bid))
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

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opps:
        return float(min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace only
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how many full water units supply can cover
    # (Used only to scale aggressiveness; not for indexing.)
    units = supply / float(WATER_REQ) if WATER_REQ > 0 else 0.0

    # Aggression policy:
    # - If opponent pressure was high yesterday (>= ~0.85*DAILY_SALARY), match moderately.
    # - Otherwise, bid near a baseline that still threatens their shared aggressive strategy.
    # - If our hp is low or we've already gone many days without water, bid harder.
    high_pressure = highest_prev_bid >= (DAILY_SALARY * 0.85)

    # Supply scaling: lower supply => slightly higher bid to secure allocation.
    # Map supply in [15,25] to factor in [1.10, 0.95]
    if MAX_SUPPLY > MIN_SUPPLY:
        t = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        t = 0.5
    if t < 0.0:
        t = 0.0
    if t > 1.0:
        t = 1.0
    supply_factor = 1.10 - 0.15 * t

    # Determine target bid
    if high_pressure:
        if hp > 3.0 and no_water_days <= 1:
            target = DAILY_SALARY * 0.30
        else:
            target = DAILY_SALARY * 0.70
        # Slightly react to their top bid
        target = max(target, highest_prev_bid * 0.72)
    else:
        # Baseline to exploit their consistent ~130 bids
        target = max(DAILY_SALARY * 0.50, highest_prev_bid * 0.85)
        if hp <= 2.0 or no_water_days >= 2:
            target = max(target, DAILY_SALARY * 0.85)

    target *= supply_factor

    # Hard cap by budget; also avoid bidding above a reasonable max relative to salary
    cap = min(budget, DAILY_SALARY * 1.2)
    bid = float(min(cap, max(0.0, target)))

    # If budget is tiny, still bid something minimal
    if bid <= 0.0 and budget > 0.0:
        bid = float(min(budget, DAILY_SALARY * 0.1))

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
    day = int(day_context['day'])

    # Identify alive opponents and their yesterday bids
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # If no one alive, conserve budget
    if not alive_opps:
        return max(0.0, min(float(my_status['budget']), DAILY_SALARY * 0.4))

    # Extract yesterday bids for alive opponents only
    yesterday_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate Cindy pressure: if Cindy bid was high yesterday, she likely continues.
    cindy = opponents_status.get('Cindy', None)
    cindy_pressure = 0.0
    if cindy is not None and cindy.get('alive', False):
        prev = cindy.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                cindy_pressure = float(b)
            except Exception:
                cindy_pressure = 0.0

    # Risk-based escalation
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Supply-aware target: medium scenario, supply between 15 and 25.
    # When supply is higher, water is easier to secure; bid less.
    # When supply is lower, bid more.
    supply_norm = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)  # 0..1
    supply_norm = 0.0 if supply_norm < 0.0 else (1.0 if supply_norm > 1.0 else supply_norm)

    # Base bid aims to be competitive but not wasteful vs Cindy.
    # If Cindy previously bid big, we try to undercut her by a small margin.
    undercut_margin = 2.5
    if cindy_pressure > 0:
        # Target slightly below Cindy's pressure to avoid overpaying.
        competitive_target = max(DAILY_SALARY * 0.35, cindy_pressure - undercut_margin)
    else:
        # If no Cindy info, react to highest previous bid.
        competitive_target = max(DAILY_SALARY * 0.45, highest_prev_bid * 0.75)

    # Adjust for supply (lower supply => bid higher)
    # At supply_norm=0 (15), multiplier ~1.15; at 1 (25), ~0.85
    supply_multiplier = 1.15 - 0.30 * supply_norm

    # Escalate if we're close to dying / accumulating no-water days
    # (Assuming strategy: secure water when no_water_days is high or hp is low.)
    risk_multiplier = 1.0
    if hp <= 2.0:
        risk_multiplier = 1.35
    elif hp <= 4.0:
        risk_multiplier = 1.18

    if no_water_days >= 2:
        risk_multiplier = max(risk_multiplier, 1.25)
    if no_water_days >= 3:
        risk_multiplier = max(risk_multiplier, 1.45)

    # Final target
    bid = competitive_target * supply_multiplier * risk_multiplier

    # Hard caps: never exceed what we can pay; also avoid going above a fraction of salary
    # to prevent bankroll exhaustion.
    max_reasonable = DAILY_SALARY * 0.95
    bid = min(bid, max_reasonable)

    # If budget is low, scale down
    bid = min(bid, budget)

    # If budget is extremely low, bid whatever remains (but non-negative)
    if bid < 0.0:
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Identify alive opponents
    alive = []
    for oid, o in opponents_status.items():
        try:
            if o.get('alive', False):
                alive.append((oid, o))
        except Exception:
            continue

    # If no opponents alive, take a safe amount
    if not alive:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday trace bids for immediate reaction
    prev_bids = []
    for oid, o in alive:
        prev = o.get('previous_trace', None)
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    prev_bids.append(float(b))
                except Exception:
                    pass
        elif isinstance(prev, list):
            # Only immediate reaction: take last entry if present
            if len(prev) > 0:
                last = prev[-1]
                if isinstance(last, dict):
                    b = last.get('bid', None)
                    if b is not None:
                        try:
                            prev_bids.append(float(b))
                        except Exception:
                            pass

    # Estimate competitive pressure from yesterday
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Base target bid: aim to win enough water while avoiding Cindy-like overbidding
    # Supply-dependent aggressiveness
    # More supply => lower bid needed; less supply => bid closer to salary
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # If I'm low HP, bid more to secure water
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    # No-water days increases urgency
    no_water_days = int(my_status['no_water_days'])
    urgency = 0
    if no_water_days >= 2:
        urgency = 2
    elif no_water_days == 1:
        urgency = 1

    # Determine a cap to avoid runaway spending
    # If Cindy overbid yesterday, highest_prev_bid will be huge; we don't want to match it.
    # We'll use a fraction of highest_prev_bid unless I'm in danger.
    danger = (hp <= 2.5) or (urgency >= 2)

    if danger:
        # Near-critical: bid high but still below extreme bids
        target = DAILY_SALARY * (0.75 + 0.1 * urgency)
        # If someone already bid extremely high yesterday, don't fully mirror; still avoid wasting budget
        if highest_prev_bid > DAILY_SALARY * 1.5:
            target = min(target, highest_prev_bid * 0.35)
    else:
        # Normal: bid moderate; react to competition
        # If yesterday someone bid very high, slightly increase to avoid losing water.
        if highest_prev_bid >= DAILY_SALARY * 1.2:
            target = DAILY_SALARY * (0.55 + 0.15 * (1.0 - supply_ratio))
            target = min(target, highest_prev_bid * 0.25)
        else:
            target = DAILY_SALARY * (0.45 + 0.10 * (1.0 - supply_ratio))

    # Ensure we don't bid above our budget
    bid = float(min(budget, target))

    # If budget is tiny, still bid what we can
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

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    # If we are already in danger, prioritize survival with a high bid.
    hp = my_status.get('hp', 0)
    budget = my_status.get('budget', 0)
    no_water_days = my_status.get('no_water_days', 0)

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        # No competition: bid low to conserve budget.
        return max(0.0, min(budget, DAILY_SALARY * 0.35))

    # Read yesterday's bid pressure from alive opponents only.
    prev_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_prev_bid = 0.0
    if len(prev_bids) >= 2:
        sorted_b = sorted(prev_bids, reverse=True)
        second_prev_bid = sorted_b[1]

    # Estimate number of water units available; use int() to avoid float index issues.
    # (We don't index arrays, but keep consistent with rule.)
    supply_units = int(supply / WATER_REQ) if WATER_REQ > 0 else 0
    # If supply is low, competition is tighter; increase bid.
    supply_tightness = 0.0
    if supply_units <= 1:
        supply_tightness = 1.0
    elif supply_units == 2:
        supply_tightness = 0.6
    else:
        supply_tightness = 0.3

    # Base willingness to bid.
    # Players like Alex/Cindy previously bid around/above ~100 and survived; emulate when safe.
    # Use highest_prev_bid to decide whether to match pressure.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # High pressure: either match with enough to beat them, or go defensive if low HP.
        if hp <= 2 or no_water_days >= 2:
            target = DAILY_SALARY * 0.95
        else:
            # Try to slightly undercut/beat the top bidder depending on our HP.
            target = max(highest_prev_bid + 2.0, DAILY_SALARY * 0.65)
    else:
        # Moderate pressure: bid enough to compete but conserve.
        if hp <= 2 or no_water_days >= 2:
            target = DAILY_SALARY * 0.75
        else:
            # Scale with tightness and yesterday's second-highest bid.
            target = max(second_prev_bid + 1.5, DAILY_SALARY * (0.45 + 0.25 * supply_tightness))

    # Convert target into final bid bounded by budget.
    # Also cap to avoid overspending when budget is low.
    # If budget is insufficient, spend what we can.
    bid = min(float(budget), float(target))

    # If our HP is very low, ensure we spend close to budget to avoid elimination.
    if hp <= 1:
        bid = min(float(budget), max(bid, DAILY_SALARY * 0.9))

    # Never negative.
    if bid < 0:
        bid = 0.0

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
    day = int(day_context['day'])

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opponents = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opponents:
        return float(min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace for immediate pressure signal
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Baseline bid: aim mid to win occasionally without burning budget
    # If supply is higher, competition likely increases; bid a bit more.
    supply_ratio = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Determine urgency from hp and no_water_days
    urgency = 0.0
    if hp <= 2.0:
        urgency += 0.9
    elif hp <= 4.0:
        urgency += 0.55
    else:
        urgency += 0.25

    if no_water_days >= 2:
        urgency += 0.35
    elif no_water_days == 1:
        urgency += 0.15

    # Use yesterday's highest bid as a proxy for aggressive opponents.
    # If someone already bid very high, avoid matching exactly; instead slightly undercut.
    target = None
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Cindy-like aggression: don't fully mirror; choose a defensive bid.
        target = DAILY_SALARY * (0.45 + 0.25 * supply_ratio) + urgency * DAILY_SALARY * 0.2
        # Undercut relative to yesterday peak
        target = min(target, highest_prev_bid - 5.0)
    else:
        # Moderate pressure: bid around mid-high based on urgency and supply.
        target = DAILY_SALARY * (0.5 + 0.2 * supply_ratio) + urgency * DAILY_SALARY * 0.25

    # If budget is low, scale down but still react to low hp.
    if budget <= DAILY_SALARY * 0.4:
        target = min(target, budget * (0.65 if hp > 2.0 else 0.9))

    # Ensure non-negative and within budget
    target = max(0.0, float(target))
    bid = min(budget, target)

    # If my hp is critically low, prioritize survival.
    if hp <= 1.5:
        bid = min(budget, max(bid, DAILY_SALARY * 0.9))

    # Small strategic oscillation by day to avoid ties/predictability
    if day % 2 == 0:
        bid *= (1.03)
    else:
        bid *= (0.98)

    bid = max(0.0, min(budget, float(bid)))
    return float(bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    # If we are already in critical health, bid aggressively to secure water.
    if hp <= 2 or no_water_days >= 2:
        bid = DAILY_SALARY * 0.85
        return float(min(budget, bid))

    # Read yesterday's pressure from opponents' bids.
    prev_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    # If others were spending heavily yesterday, we can underbid slightly to conserve budget.
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        # Heuristic thresholds: Cindy/David/Eric appear to spend ~100-130; Alex had lower avg.
        if highest_prev_bid >= DAILY_SALARY * 1.0:
            # Still bid enough to not be the weakest; scale with supply.
            # When supply is scarce, increase bid; when abundant, reduce.
            scarcity = (25.0 - supply) / 10.0  # supply in [15,25] => scarcity in [1,0]
            scarcity = max(0.0, min(1.0, scarcity))
            base = DAILY_SALARY * 0.55
            bid = base * (0.75 + 0.5 * scarcity)
            return float(min(budget, bid))
        else:
            # If overall bids were moderate, bid closer to the top.
            bid = min(budget, max(DAILY_SALARY * 0.45, highest_prev_bid * 0.85))
            return float(bid)

    # No opponent info: default moderate bid.
    bid = DAILY_SALARY * 0.5
    return float(min(budget, bid))
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

    # Basic sanity
    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # If we're effectively out of budget, bid 0
    if budget <= 0:
        return 0.0

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append((oid, o))

    # Reaction to yesterday's bids (immediate only)
    prev_bids = []
    for oid, o in alive_opponents:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Pressure estimate: how aggressive the field was
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        avg_prev_bid = sum(prev_bids) / float(len(prev_bids))
    else:
        highest_prev_bid = 0.0
        avg_prev_bid = 0.0

    # Supply tightness: lower supply => higher chance of needing to outbid
    # Use integer index safety patterns where needed (none here), but keep robust.
    tightness = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        tightness = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    tightness = max(0.0, min(1.0, tightness))

    # Core strategy:
    # - If our HP is low or we've had no water days, bid more.
    # - Otherwise, undercut slightly vs aggressive opponents.
    # - Use yesterday highest bid as a ceiling reference.
    low_hp = hp <= 2.0
    very_low_hp = hp <= 1.0
    critical_no_water = no_water_days >= 2

    # Baseline bid level
    if very_low_hp or critical_no_water:
        # Must secure water
        baseline = DAILY_SALARY * (0.85 + 0.1 * tightness)
    elif low_hp:
        baseline = DAILY_SALARY * (0.65 + 0.15 * tightness)
    else:
        # Moderate bid: competitive but not matching Cindy-like overbidding
        baseline = DAILY_SALARY * (0.50 + 0.10 * tightness)

    # If yesterday showed very high aggression, nudge upward but still avoid full matching
    if prev_bids:
        # If highest previous bid was extremely high, field likely overbids; we can still bid moderately.
        if highest_prev_bid >= DAILY_SALARY * 1.10:
            baseline = max(baseline, DAILY_SALARY * (0.55 + 0.10 * tightness))
        elif highest_prev_bid >= DAILY_SALARY * 0.85:
            baseline = max(baseline, DAILY_SALARY * (0.60 + 0.15 * tightness))
        else:
            # If aggression was low, we can bid closer to baseline.
            baseline = baseline

    # Cap by what we can afford and by a soft reference to previous highest bid
    # Soft cap prevents runaway spending.
    soft_cap = budget
    if prev_bids and highest_prev_bid > 0:
        # Don't exceed ~92% of yesterday's highest bid unless critical
        if not (very_low_hp or critical_no_water):
            soft_cap = min(soft_cap, highest_prev_bid * 0.92)

    bid = min(baseline, soft_cap)

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

    supply = float(day_context['supply'])
    day = day_context['day']

    # Identify alive opponents and their yesterday bids
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    # Default conservative bid
    if my_status['budget'] <= 0:
        return 0.0

    # If no opponents alive, bid enough to secure water cheaply
    if not alive_opps:
        return min(float(my_status['budget']), DAILY_SALARY * 0.4)

    # Gather immediate reaction from previous_trace only
    prev_bids = []
    prev_pressures = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            prev_bids.append(float(b))
        prev_hp_after = prev.get('hp_after', None)
        if prev_hp_after is not None:
            prev_pressures.append(float(prev_hp_after))

    # Estimate clearing pressure from yesterday bids
    if prev_bids:
        max_prev_bid = max(prev_bids)
        avg_prev_bid = sum(prev_bids) / float(len(prev_bids))
    else:
        max_prev_bid = 0.0
        avg_prev_bid = 0.0

    # Supply pressure: with higher supply, competition should be lower
    # Normalize supply into [0,1]
    if MAX_SUPPLY > MIN_SUPPLY:
        s_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        s_norm = 0.5
    s_norm = max(0.0, min(1.0, s_norm))

    # Determine urgency from my hp and no_water_days
    my_hp = float(my_status['hp'])
    no_water_days = int(my_status['no_water_days'])

    # If I'm in danger, go aggressive regardless of supply
    if my_hp <= 2 or no_water_days >= 2:
        bid = DAILY_SALARY * 0.95
        return float(min(my_status['budget'], bid))

    # If I'm moderately healthy, bid just above likely clearing level when supply is not too high
    # Use a target near avg_prev_bid but cap below max_prev_bid to avoid overspending.
    # When supply is low (s_norm small), increase bid slightly.
    base = max(DAILY_SALARY * 0.5, avg_prev_bid * 0.95)
    # Add a small increment to beat competitors who clustered around 120-153
    # More aggressive when supply is low.
    increment = (1.0 - s_norm) * 15.0
    target = base + increment

    # If yesterday max bid was very high, we may need to match closer to it.
    if max_prev_bid >= DAILY_SALARY * 0.85:
        # Match a fraction of the max to avoid full bidding war
        target = max(target, max_prev_bid * 0.85)

    # Final cap: never exceed what we can afford, and keep below a reasonable ceiling
    ceiling = DAILY_SALARY * 0.75
    bid = min(target, ceiling)

    # Ensure non-negative
    bid = max(0.0, bid)
    return float(min(my_status['budget'], bid))
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
    day = day_context['day']

    # If we can’t afford anything meaningful, conserve.
    if my_status['budget'] <= 0:
        return 0.0

    # Collect yesterday bids from alive opponents.
    alive_opps = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opps.append(opp)

    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Base urgency from our hp.
    hp = float(my_status['hp'])
    no_water_days = int(my_status['no_water_days'])

    # Estimate how competitive the market is from yesterday.
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / float(len(yesterday_bids))
    else:
        highest_prev_bid = 0.0
        avg_prev_bid = 0.0

    # Supply pressure: with higher supply, bidding can drop; with lower supply, bid higher.
    # Map supply in [15,25] to pressure in [1.1,0.9]
    if MAX_SUPPLY > MIN_SUPPLY:
        t = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    else:
        t = 0.5
    pressure = 1.1 - 0.2 * t

    # Decide target bid.
    # If others were bidding very high, we slightly undercut to secure water without burning budget.
    # If others were moderate, we bid around the average scaled by pressure.
    budget = float(my_status['budget'])

    # Safety rule: if we’ve already had several no-water days, increase.
    if no_water_days >= 2 or hp <= 3:
        urgency = 1.15
    else:
        urgency = 0.95

    # Compute candidate bids.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # They were near-max aggressive; bid just below highest but capped.
        target = min(budget, (highest_prev_bid * 0.98) * pressure * urgency)
    else:
        # Use average as anchor; ensure we bid enough to not be ignored.
        anchor = avg_prev_bid if avg_prev_bid > 0 else DAILY_SALARY * 0.55
        target = anchor * pressure * urgency

    # Ensure we don't bid too low when supply is tight.
    tight_floor = DAILY_SALARY * (0.45 if supply >= 20.0 else 0.65)
    target = max(target, tight_floor)

    # Cap to avoid running out before episode end.
    # With hp=9 we can stay conservative.
    cap = DAILY_SALARY * 0.75 if hp >= 7 else DAILY_SALARY * 0.95
    target = min(target, cap, budget)

    # Return non-negative float.
    if target < 0:
        target = 0.0
    return float(target)
"""
