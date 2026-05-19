# ============================================================
# Experiment: exp_077
# Agent: Bob
# Source: exp_077
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
    day = int(day_context['day'])

    budget = float(my_status['budget'])
    hp = float(my_status['hp'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for opp_id, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((opp_id, o))

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids (immediate reaction only)
    yesterday_bids = []
    yesterday_details = []
    for opp_id, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                b = float(bid)
                yesterday_bids.append(b)
                yesterday_details.append((opp_id, b, prev.get('status', None), prev.get('hp_after', None), prev.get('budget_after', None)))
            except Exception:
                pass

    # Baseline bid depends on our urgency
    # If we're already starving, increase bid to avoid falling further.
    if hp <= 2.0 or no_water_days >= 2:
        urgency_bid = DAILY_SALARY * 0.85
    elif hp <= 3.0 or no_water_days >= 1:
        urgency_bid = DAILY_SALARY * 0.65
    else:
        urgency_bid = DAILY_SALARY * 0.5

    # If opponents showed high bids yesterday, they are likely competing hard.
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        lowest_prev_bid = min(yesterday_bids)

        # Estimate how many water units we likely need to secure given supply.
        # Bidding higher than needed is wasteful when supply is abundant.
        # If supply is tight, we bid more aggressively.
        tightness = 0.0
        if supply <= (MIN_SUPPLY + WATER_REQ):
            tightness = 1.0
        elif supply >= (MAX_SUPPLY - WATER_REQ):
            tightness = 0.2
        else:
            tightness = 0.6

        # If someone bid near max urgency (close to daily salary), counter with strong bid.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            target = DAILY_SALARY * (0.75 + 0.2 * tightness)
        # If bids were mid-high, match slightly above the top to steal allocation.
        elif highest_prev_bid >= DAILY_SALARY * 0.55:
            target = min(DAILY_SALARY * (0.6 + 0.25 * tightness), highest_prev_bid + 5.0)
        else:
            # Otherwise, bid enough to compete but conserve budget.
            # Use a small premium over the lowest to avoid being outbid by low-pressure agents.
            target = max(DAILY_SALARY * 0.45, lowest_prev_bid + 2.0)

        # Blend with our urgency
        target = 0.55 * target + 0.45 * urgency_bid

    else:
        # No trace bids available: use urgency and supply tightness.
        tightness = 1.0 if supply <= (MIN_SUPPLY + WATER_REQ) else 0.6
        target = urgency_bid * (0.85 + 0.2 * tightness)

    # Convert target into feasible bid: cannot exceed budget.
    bid = max(0.0, min(budget, target))

    # Additional safeguard: if we can’t afford to bid enough, still bid what we can.
    # Also avoid overbidding when supply is high.
    if supply >= (MAX_SUPPLY - 1.0) and bid > DAILY_SALARY * 0.65:
        bid = min(bid, DAILY_SALARY * 0.65)

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

    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = [o for o in opponents_status.values() if o.get('alive')]
    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Reaction to yesterday bids (immediate)
    prev_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Base target bid: moderate to beat overbidders, but not as extreme as Cindy/Eric averages.
    # Supply scaling: when supply is closer to MAX, we can bid slightly less.
    supply_ratio = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # If someone previously bid extremely high, we slightly increase to avoid being starved.
    if highest_prev_bid >= DAILY_SALARY * 1.1:  # ~99
        urgency = 1.0
    elif highest_prev_bid >= DAILY_SALARY * 0.85:  # ~76.5
        urgency = 0.7
    else:
        urgency = 0.4

    # HP and consecutive no-water days increase urgency.
    if hp <= 1:
        urgency += 0.9
    elif hp <= 3:
        urgency += 0.5

    if no_water_days >= 2:
        urgency += 0.6
    elif no_water_days == 1:
        urgency += 0.3

    # Convert urgency to bid multiplier.
    # When supply is high, reduce; when low, increase.
    # bid ~ DAILY_SALARY * (0.35..1.3)
    bid_multiplier = (0.45 + 0.65 * (1.0 - supply_ratio)) * (0.75 + urgency)
    bid_multiplier = max(0.35, min(1.35, bid_multiplier))

    target_bid = DAILY_SALARY * bid_multiplier

    # Ensure we don't overpay relative to budget.
    # If low budget, bid as much as possible without going all-in unless critical.
    if budget <= DAILY_SALARY * 0.2:
        return min(budget, DAILY_SALARY * 0.25)

    # If critical HP, go higher (but still capped by a fraction of budget).
    if hp <= 1 or no_water_days >= 3:
        cap = budget if budget < DAILY_SALARY * 1.0 else DAILY_SALARY * 1.15
        return min(budget, cap, target_bid)

    # Normal case: cap at ~0.9 salary or budget.
    cap = DAILY_SALARY * 0.95
    return min(budget, cap, target_bid)
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

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append((oid, o))

    if not alive_opponents:
        return float(min(my_budget, DAILY_SALARY * 0.4))

    # Pull yesterday bids for immediate reaction
    opp_prev = []
    for oid, o in alive_opponents:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                b = float(b)
            except Exception:
                b = None
        if b is not None:
            opp_prev.append((oid, b, o))

    # Identify Cindy and highest/lowest yesterday bids
    cindy_bid = None
    highest_bid = None
    lowest_bid = None
    for oid, b, o in opp_prev:
        if highest_bid is None or b > highest_bid:
            highest_bid = b
        if lowest_bid is None or b < lowest_bid:
            lowest_bid = b
        if str(oid).lower() == 'cindy':
            cindy_bid = b

    # Base target: aim just above the most aggressive opponent, but cap by affordability
    # Use Cindy trace as primary signal; otherwise use highest bid.
    signal_bid = cindy_bid if cindy_bid is not None else (highest_bid if highest_bid is not None else DAILY_SALARY * 0.6)

    # Pressure factor: if my HP is low or no-water days are accumulating, bid more.
    # If my HP is high, bid less to conserve budget.
    if my_hp <= 2:
        pressure = 1.00
    elif my_hp <= 4:
        pressure = 0.85
    else:
        pressure = 0.70

    # Supply scaling: with higher supply, we can bid slightly less; with lower supply, bid more.
    # supply is between MIN_SUPPLY and MAX_SUPPLY.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    # When supply_ratio is low, scarcity high -> increase bid.
    scarcity_factor = 1.0 + (0.5 - supply_ratio) * 0.25

    # Compute a nominal bid: slightly above signal_bid, but not too high.
    # Also anchor to a fraction of my daily salary.
    target = signal_bid * 1.03
    anchor = DAILY_SALARY * 0.55
    target = max(target, anchor)

    # If my no-water days are high, ensure we secure water.
    if my_no_water_days >= 2:
        target *= 1.15

    # Final bid with pressure and scarcity
    target *= pressure * scarcity_factor

    # Ensure we don't overspend: use a budget fraction that depends on HP.
    if my_hp <= 2:
        budget_cap = my_budget * 0.55
    elif my_hp <= 4:
        budget_cap = my_budget * 0.45
    else:
        budget_cap = my_budget * 0.35

    # Also cap by a reasonable multiple of daily salary to avoid runaway.
    budget_cap = min(budget_cap, DAILY_SALARY * 1.25)

    bid = float(min(my_budget, budget_cap, target))

    # If bids were generally low (lowest_bid well below anchor), reduce to avoid waste.
    if lowest_bid is not None and lowest_bid < DAILY_SALARY * 0.45 and my_hp >= 5:
        bid = float(min(bid, DAILY_SALARY * 0.5))

    # Keep bid non-negative
    if bid < 0:
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
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    # Alive opponents
    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive.append((opp_id, opp))

    if not alive:
        # If no opponents, spend conservatively
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace only
    yesterday_bids = []
    for _, opp in alive:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Pressure estimate from yesterday: if someone bid extremely high, expect bidding war
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Determine how many water units are likely available today
    # (We don't know exact conversion, but supply range suggests 15..25 total.)
    supply_ratio = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    if supply_ratio < 0.0:
        supply_ratio = 0.0
    if supply_ratio > 1.0:
        supply_ratio = 1.0

    # Base bid target: slightly above typical midrange, scaled by supply and our HP
    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))

    # Conservative thresholding around observed bids (roughly 110-145 survivors, Alex died with high bids)
    # If yesterday highest was very high, we avoid extreme overbidding and instead anchor near 115-125.
    if highest_prev_bid >= 170.0:
        target = 120.0 + 10.0 * supply_ratio
    elif highest_prev_bid >= 140.0:
        target = 110.0 + 15.0 * supply_ratio
    else:
        target = 105.0 + 20.0 * supply_ratio

    # If our HP is low, we must secure water more aggressively.
    if my_hp <= 2.0:
        target += 40.0
    elif my_hp <= 4.0:
        target += 20.0

    # If our budget is tight, cap spending.
    # Also incorporate no_water_days to avoid starvation.
    no_water_days = int(my_status.get('no_water_days', 0))
    if no_water_days >= 2:
        target += 15.0

    # Final bid: cannot exceed budget; also keep within a reasonable band to avoid Alex-like overbidding.
    # Use DAILY_SALARY as a soft cap.
    max_reasonable = min(my_budget, DAILY_SALARY * 1.25)
    bid = min(target, max_reasonable)

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

    hp = my_status.get('hp', 0)
    budget = my_status.get('budget', 0.0)
    no_water_days = my_status.get('no_water_days', 0)

    alive_opponents = []
    for k, o in opponents_status.items():
        try:
            if o.get('alive', False):
                alive_opponents.append(o)
        except Exception:
            pass

    if budget <= 0:
        return 0.0

    # Estimate scarcity: with supply in [15,25], total water units are roughly supply/WATER_REQ.
    # When supply is closer to MIN_SUPPLY, competition is tighter.
    scarcity = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        scarcity = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)  # 0..1
    scarcity = max(0.0, min(1.0, float(scarcity)))

    # Read yesterday bids from traces (only immediate reaction).
    prev_bids = []
    for o in alive_opponents:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Base target bid: aim to outbid the typical aggressive pressure when supply is tight.
    # Use highest_prev_bid as a proxy for how much others were willing to pay.
    # Keep it within my budget.
    if highest_prev_bid > 0:
        # If yesterday had very high bids, assume a bidding war; respond with a controlled overtake.
        if highest_prev_bid >= DAILY_SALARY * 1.2:
            aggressiveness = 0.75 + 0.25 * scarcity
        elif highest_prev_bid >= DAILY_SALARY * 0.8:
            aggressiveness = 0.60 + 0.30 * scarcity
        else:
            aggressiveness = 0.45 + 0.25 * scarcity
    else:
        aggressiveness = 0.45 + 0.25 * scarcity

    # Health-aware adjustment: if I'm low HP or have had no water days, bid more.
    hp_factor = 1.0
    if hp <= 2:
        hp_factor = 1.25
    elif hp <= 4:
        hp_factor = 1.15
    elif hp <= 6:
        hp_factor = 1.05
    else:
        hp_factor = 0.95

    no_water_factor = 1.0 + 0.08 * max(0, int(no_water_days))
    no_water_factor = min(1.25, float(no_water_factor))

    # Convert supply to a rough need multiplier: if supply is low, need to secure water.
    # When supply is around 15, water units ~ 1.6; around 25, ~2.8.
    water_units = supply / float(WATER_REQ) if WATER_REQ > 0 else 1.0
    need_multiplier = 1.0
    if water_units <= 1.8:
        need_multiplier = 1.15
    elif water_units <= 2.2:
        need_multiplier = 1.05
    else:
        need_multiplier = 0.95

    # Target bid computation.
    # If highest_prev_bid is high, try to be slightly above it but cap to avoid busting.
    target = 0.0
    if highest_prev_bid > 0:
        # Slightly above highest_prev_bid when scarcity is high; otherwise, match-ish.
        bump = (highest_prev_bid * 0.03) + (5.0 * scarcity)
        target = (highest_prev_bid * (0.92 + 0.08 * (1.0 - scarcity))) + bump
    else:
        target = DAILY_SALARY * (0.50 + 0.35 * scarcity)

    target = target * float(aggressiveness) * float(hp_factor) * float(no_water_factor) * float(need_multiplier)

    # Ensure we don't exceed budget and keep some reserve.
    # If hp is very low, spend more aggressively.
    reserve_ratio = 0.25
    if hp <= 2:
        reserve_ratio = 0.05
    elif hp <= 4:
        reserve_ratio = 0.12
    elif hp >= 8:
        reserve_ratio = 0.35

    max_affordable = float(budget) * (1.0 - reserve_ratio)
    target = min(target, max_affordable)

    # Also avoid bidding too low when scarcity is high and I'm not doing well.
    min_bid = 0.0
    if scarcity >= 0.6 and (hp <= 6 or int(no_water_days) >= 1):
        min_bid = DAILY_SALARY * 0.35
    elif scarcity >= 0.6:
        min_bid = DAILY_SALARY * 0.25
    else:
        min_bid = DAILY_SALARY * 0.18

    bid = max(float(min_bid), float(target))

    # Final clamp
    if bid < 0.0:
        bid = 0.0
    if bid > float(budget):
        bid = float(budget)

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

    my_hp = int(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append(o)

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Read yesterday bids to infer competitive intensity
    yesterday_bids = []
    yesterday_pressures = []  # (bid, hp_after)
    for o in alive_opponents:
        prev = o.get('previous_trace', {}) or {}
        if prev and prev.get('bid') is not None:
            b = float(prev['bid'])
            hp_after = prev.get('hp_after', None)
            yesterday_bids.append(b)
            if hp_after is not None:
                try:
                    yesterday_pressures.append((b, int(hp_after)))
                except Exception:
                    pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid

    # Supply-to-water urgency: with supply in [15,25], competition likely rises as supply drops.
    # We only need WATER_REQ=9; if supply is near MIN_SUPPLY, scarcity is higher.
    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)  # 0..1
    scarcity = max(0.0, min(1.0, scarcity))

    # If we are in danger, bid harder.
    danger = 0.0
    if my_hp <= 2:
        danger = 1.0
    elif my_hp <= 3:
        danger = 0.6
    if my_no_water_days >= 2:
        danger = max(danger, 0.7)

    # Determine target bid band based on yesterday competitive bids.
    # Alex/Cindy were around 126-138; we aim slightly above their likely band when supply is mid/low.
    base_target = max(DAILY_SALARY * 0.55, highest_prev_bid * (0.95 + 0.05 * scarcity))

    # If yesterday had high competitive bids, we overbid slightly to secure water.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Overbid just enough; scale down if we are already safe.
        overbid = 6.0 * (0.5 + 0.5 * scarcity)
        if danger >= 0.7:
            target = highest_prev_bid + overbid
        else:
            target = min(highest_prev_bid + overbid, max(base_target, second_prev_bid + 3.0))
    else:
        # Lower competition: bid around base_target with small premium.
        target = base_target + 2.0 + 4.0 * scarcity

    # Convert target into a feasible bid with budget cap.
    # Also avoid spending too much when supply is generous.
    generous = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    generous = max(0.0, min(1.0, generous))
    spending_cap = DAILY_SALARY * (0.85 - 0.35 * generous)  # tighter when supply is high

    bid = min(my_budget, spending_cap, target)

    # If bid becomes too low while in danger, push closer to cap.
    if danger >= 0.7 and bid < DAILY_SALARY * 0.75:
        bid = min(my_budget, DAILY_SALARY * 0.85)

    # Ensure non-negative.
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # If we are already in critical condition, bid aggressively to prevent collapse.
    my_hp = int(my_status['hp'])
    my_budget = float(my_status['budget'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Read only yesterday's immediate trace bids.
    prev_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Determine how many full water units are likely available.
    # supply is float; convert to int for indexing-free logic.
    # If supply is near minimum, competition is higher.
    tight_supply = supply <= (MIN_SUPPLY + 2.0)

    # Base bid target: secure water when tight, otherwise bid moderately.
    if tight_supply:
        base = DAILY_SALARY * 0.75
    else:
        base = DAILY_SALARY * 0.55

    # If yesterday someone was bidding very high, raise slightly to beat them.
    # Eric died with very low bids, implying others avoid starvation; high_prev_bid is a proxy for current intensity.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        base = max(base, highest_prev_bid * 0.95)

    # If our hp is low, we must spend more.
    if my_hp <= 2:
        base = max(base, DAILY_SALARY * 0.95)
    elif my_hp <= 4:
        base = max(base, DAILY_SALARY * 0.75)

    # Never exceed budget; also cap to avoid burning money when supply is likely sufficient.
    # Slightly undercut highest_prev_bid when not tight.
    if not tight_supply and highest_prev_bid > 0:
        base = min(base, highest_prev_bid * 0.9 + 2.0)

    bid = min(my_budget, max(0.0, base))
    return float(bid)
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    yesterday_bids.append(float(b))
                except Exception:
                    pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how many rounds of water we can buy at minimum effective intensity.
    # (We don't know exact mapping from bid->water, but use supply to scale aggressiveness.)
    supply_factor = 0.5
    if supply >= 21.0:
        supply_factor = 0.85
    elif supply <= 17.0:
        supply_factor = 0.65

    # Pressure detection: if someone bid near our daily salary, they likely enforced a high-water contest.
    pressure = 0.0
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        pressure = 1.0
    elif highest_prev_bid >= DAILY_SALARY * 0.6:
        pressure = 0.6
    elif highest_prev_bid >= DAILY_SALARY * 0.35:
        pressure = 0.35

    # Core strategy: bid enough to avoid falling behind, but don't overpay when HP is safe.
    if hp <= 2 or no_water_days >= 2:
        # Emergency ramp: protect survival.
        target = DAILY_SALARY * (0.75 + 0.15 * pressure) * supply_factor
    elif hp <= 4:
        target = DAILY_SALARY * (0.55 + 0.20 * pressure) * supply_factor
    else:
        # Healthy: stay competitive but cheaper.
        target = DAILY_SALARY * (0.45 + 0.15 * pressure) * supply_factor

    # If yesterday pressure was very high, slightly undercut to still be competitive.
    if highest_prev_bid > 0.0 and pressure >= 0.6:
        target = min(target, highest_prev_bid + 5.0)

    # Clamp to budget and non-negative.
    bid = max(0.0, min(budget, target))

    # Avoid bidding absurdly high when budget is tiny.
    if budget < DAILY_SALARY * 0.2:
        bid = min(bid, budget)

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
    day = int(day_context['day'])

    # Alive opponents
    alive = []
    for oid, o in opponents_status.items():
        try:
            if o.get('alive', False):
                alive.append((oid, o))
        except Exception:
            continue

    # If no opponents alive, conserve budget
    if not alive:
        return max(0.0, min(float(my_status['budget']), DAILY_SALARY * 0.35))

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

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

    # Estimate how aggressive the table is
    highest_prev = max(prev_bids) if prev_bids else 0.0
    second_highest = 0.0
    if len(prev_bids) >= 2:
        sorted_bids = sorted(prev_bids, reverse=True)
        second_highest = sorted_bids[1]

    # Supply pressure: higher supply means cheaper to secure water.
    # Normalize to [0,1]
    if MAX_SUPPLY == MIN_SUPPLY:
        supply_norm = 0.5
    else:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
        if supply_norm < 0.0:
            supply_norm = 0.0
        if supply_norm > 1.0:
            supply_norm = 1.0

    # If we are in danger (low hp or many no-water days), bid more.
    danger = (my_hp <= 2.5) or (my_no_water_days >= 2)

    # Cindy-like behavior: very high bids (~>=110). We can try to undercut.
    # Target bid uses highest_prev but caps to avoid overspending.
    # Undercut by a small amount if we can.
    if highest_prev >= 100.0:
        base_target = highest_prev - 6.0
    elif highest_prev >= 60.0:
        base_target = highest_prev - 4.0
    else:
        base_target = max(DAILY_SALARY * 0.45, second_highest + 3.0)

    # Adjust for supply: when supply is high, we can bid less.
    # When supply is low, bid more.
    # supply_norm near 1 -> discount; near 0 -> increase.
    if supply_norm >= 0.7:
        base_target *= 0.82
    elif supply_norm <= 0.3:
        base_target *= 1.12

    # Safety floors/ceilings
    if danger:
        base_target = max(base_target, DAILY_SALARY * 0.85)
    else:
        base_target = max(base_target, DAILY_SALARY * 0.52)

    # Never exceed budget
    bid = min(my_budget, base_target)

    # If budget is tiny, still bid what we can (non-negative)
    if bid < 0.0:
        bid = 0.0

    # Additional micro-adjustment by day parity to avoid ties with predictable bots
    # (small perturbation)
    if day % 2 == 0:
        bid *= 0.995
    else:
        bid *= 1.005

    # Final clamp
    if my_budget <= 0.0:
        return 0.0
    return float(min(my_budget, max(0.0, bid)))
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

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    # Alive opponents and their yesterday bids
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    # If no opponents, bid modestly
    if not alive:
        return max(0.0, min(my_status.get('budget', 0.0), DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace
    yesterday_bids = []
    for oid, o in alive:
        prev = o.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                yesterday_bids.append(float(bid))
            except Exception:
                pass

    # Estimate how aggressive the field is: if any survived with high bids, we must match to avoid being outbid.
    # Otherwise, we can slightly overbid the lower cluster.
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        lowest_prev_bid = min(yesterday_bids)
        median_prev_bid = sorted(yesterday_bids)[len(yesterday_bids) // 2]
    else:
        highest_prev_bid = 0.0
        lowest_prev_bid = 0.0
        median_prev_bid = DAILY_SALARY * 0.5

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Supply pressure: higher supply means we can afford to bid less; lower supply means higher competition.
    # Map supply in [15,25] to a factor in [1.15,0.85]
    if MAX_SUPPLY > MIN_SUPPLY:
        t = (float(supply) - float(MIN_SUPPLY)) / (float(MAX_SUPPLY) - float(MIN_SUPPLY))
    else:
        t = 0.5
    if t < 0.0:
        t = 0.0
    if t > 1.0:
        t = 1.0
    supply_factor = 1.15 - 0.3 * t

    # Urgency based on hp and consecutive no-water days
    urgency = 0.0
    if my_hp <= 2.0:
        urgency += 1.0
    elif my_hp <= 4.0:
        urgency += 0.6
    if no_water_days >= 2:
        urgency += 0.7
    elif no_water_days == 1:
        urgency += 0.35

    # Target bid logic:
    # - If field previously used very high bids (survivors), we bid near that but with a cap.
    # - Otherwise, we bid just above the median/lowest cluster.
    # Cindy/Eric used ~83+ average while Alex/David were much lower; we aim around median/high-low boundary.
    base = median_prev_bid

    # If highest prev bid indicates a strong bidding war, match a fraction of it.
    if highest_prev_bid >= DAILY_SALARY * 0.75:
        target = 0.92 * highest_prev_bid
    else:
        # Otherwise, outbid the lower cluster by aiming above median but not too high.
        target = max(base, lowest_prev_bid + 8.0)

    # Apply urgency and supply pressure
    target = target * supply_factor
    target = target * (1.0 + 0.25 * urgency)

    # Keep within reasonable bounds relative to our budget and salary
    # If our budget is low, we bid a fraction to preserve remaining days.
    if my_budget <= 0.0:
        return 0.0

    # Soft cap: never exceed 1.0*budget and avoid spending more than salary*1.1 unless dying.
    dying = (my_hp <= 1.5) or (no_water_days >= 3)
    hard_cap = my_budget
    if dying:
        cap = min(hard_cap, DAILY_SALARY * 1.6)
    else:
        cap = min(hard_cap, DAILY_SALARY * 1.05)

    # Floor: if we are likely to lose water and survive matters, bid at least a fraction.
    if my_hp <= 3.0 or no_water_days >= 2:
        floor_bid = DAILY_SALARY * 0.65
    else:
        floor_bid = DAILY_SALARY * 0.45

    bid = max(floor_bid, target)
    bid = min(bid, cap)

    # Ensure non-negative
    if bid < 0.0:
        bid = 0.0
    return float(bid)
"""
