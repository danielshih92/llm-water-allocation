# ============================================================
# Experiment: exp_099
# Agent: Bob
# Source: exp_099
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

    # Determine alive opponents and collect yesterday bids
    alive_ops = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_ops.append((opp_id, opp))

    yesterday_bids = []
    for _, opp in alive_ops:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            yesterday_bids.append(float(b))

    # Budget/HP urgency
    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Estimate how scarce water is relative to our requirement
    # (Use supply range heuristics rather than exact allocation mechanics.)
    scarcity = 0.0
    try:
        scarcity = (float(MAX_SUPPLY) - float(supply)) / float(MAX_SUPPLY - MIN_SUPPLY)
    except Exception:
        scarcity = 0.5
    scarcity = max(0.0, min(1.0, scarcity))

    # Base bid policy
    if not alive_ops:
        # If no opponents, bid conservatively but enough to secure water when possible
        target = DAILY_SALARY * (0.35 + 0.25 * scarcity)
    else:
        # Use opponents' yesterday bids to infer their urgency
        if yesterday_bids:
            highest_prev_bid = max(yesterday_bids)
            lowest_prev_bid = min(yesterday_bids)
        else:
            highest_prev_bid = 0.0
            lowest_prev_bid = 0.0

        # Thresholds: compare to daily salary scale
        high_urgency = highest_prev_bid >= DAILY_SALARY * 0.85
        medium_urgency = highest_prev_bid >= DAILY_SALARY * 0.55

        if hp <= 2 or no_water_days >= 2:
            # We are close to losing; prioritize winning water
            target = DAILY_SALARY * (0.85 + 0.1 * scarcity)
        elif high_urgency:
            # Undercut slightly: try to win while not overpaying
            # If they were bidding very high, we bid a bit lower.
            target = min(DAILY_SALARY * (0.72 + 0.08 * scarcity), highest_prev_bid - 1.0)
        elif medium_urgency:
            # Moderate response
            target = max(DAILY_SALARY * (0.48 + 0.12 * scarcity), lowest_prev_bid + 2.0)
        else:
            # They appeared relaxed; bid enough to beat typical bids
            target = DAILY_SALARY * (0.45 + 0.15 * scarcity)

    # Convert target to a valid bid within budget
    # Ensure non-negative and integer-ish bids are acceptable.
    bid = max(0.0, min(budget, float(target)))

    # Add small day-based jitter to avoid ties; deterministic with day
    # (keeps within budget)
    jitter = ((int(day) % 7) - 3) * 0.5
    bid = max(0.0, min(budget, bid + jitter))

    # Final: return integer bid if possible; otherwise float is OK.
    return int(round(bid))
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

    # Alive opponents
    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append(o)

    # If alone, bid enough to cover requirement but not fully commit
    if not alive_opponents:
        return int(min(my_status['budget'], DAILY_SALARY * 0.45))

    # Read yesterday bids from previous_trace
    yesterday_bids = []
    for o in alive_opponents:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Determine pressure from yesterday
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = 0.0
    if yesterday_bids:
        sorted_bids = sorted(yesterday_bids)
        if len(sorted_bids) >= 2:
            second_prev_bid = sorted_bids[-2]

    # Estimate how many water units are likely available (discrete groups)
    # Use int indices explicitly; here only for logic thresholds.
    # Effective number of 'requirements' in supply range.
    # Example: supply=19 -> 2 groups (since 2*9=18).
    groups = int(supply / WATER_REQ)  # floor
    if groups < 1:
        groups = 1

    # Base bid tuned for medium scenario: secure water when supply is tight, avoid overpaying.
    # If supply is near min, be more aggressive.
    supply_tight = supply <= (MIN_SUPPLY + MAX_SUPPLY) / 2.0

    # If someone bid extremely high yesterday, they likely tried to secure water; we counter with moderate+.
    extreme = highest_prev_bid >= DAILY_SALARY * 1.2  # 108

    hp = my_status.get('hp', 0)
    budget = my_status.get('budget', 0)
    no_water_days = my_status.get('no_water_days', 0)

    # If low hp or already missing water, increase bid to prevent death.
    urgent = (hp <= 2) or (no_water_days >= 2)

    # Bid targets
    if urgent:
        # Try to beat the likely clearing price without going all-in.
        target = max(second_prev_bid + 2.0, DAILY_SALARY * (0.75 if supply_tight else 0.65))
    else:
        if extreme:
            target = max(second_prev_bid + 1.5, DAILY_SALARY * (0.55 if supply_tight else 0.45))
        else:
            # Follow Eric-like behavior: low bids work when others overspend.
            target = DAILY_SALARY * (0.48 if supply_tight else 0.38)

    # Cap by budget and avoid wasting too much early
    # Use a soft cap depending on remaining days (episode_days not provided here, so use day).
    # Later days require slightly higher bids.
    # day_context['day'] is assumed 1..10.
    day_factor = 1.0 + (int(day) - 1) * 0.03
    max_allow = budget * (0.35 if int(day) <= 3 else 0.55)

    bid = min(budget, target * day_factor, max_allow if max_allow > 0 else budget)

    # Ensure at least a small positive bid when budget allows
    if bid < 1.0:
        bid = min(budget, DAILY_SALARY * 0.2)

    # Return integer bid
    return int(max(0, min(budget, bid)))
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

    # Alive opponents and yesterday bids
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    yesterday_bids = []
    yesterday_pressures = []
    for o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            yesterday_bids.append(float(bid))
        # Use hp_after as a proxy for how costly yesterday was for them
        hp_after = prev.get('hp_after', None)
        if hp_after is not None:
            yesterday_pressures.append(float(hp_after))

    # Determine supply tightness
    # At low supply, bid more to avoid being outcompeted.
    supply_tight = (supply <= (MIN_SUPPLY + MAX_SUPPLY) / 2.0)  # <= 20

    # If we are low HP, prioritize survival.
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])

    # Estimate how aggressive others were yesterday.
    if yesterday_bids:
        avg_prev = sum(yesterday_bids) / float(len(yesterday_bids))
        max_prev = max(yesterday_bids)
    else:
        avg_prev = 0.0
        max_prev = 0.0

    # Base target bid: mid-high when supply is tight, else moderate.
    # Also react to yesterday aggression: if someone bid very high, slightly increase.
    if supply_tight:
        base = DAILY_SALARY * 0.75
    else:
        base = DAILY_SALARY * 0.55

    # If max_prev indicates strong contention, match closer.
    if max_prev >= DAILY_SALARY * 1.6:
        base = max(base, DAILY_SALARY * 0.85)
    elif avg_prev >= DAILY_SALARY * 1.2:
        base = max(base, DAILY_SALARY * 0.7)

    # Survival adjustment
    if hp <= 2.0:
        base = max(base, DAILY_SALARY * 0.95)
    elif hp <= 4.0:
        base = max(base, DAILY_SALARY * 0.8)

    # Budget cap: never exceed remaining budget.
    # Also avoid spending everything early unless critically low HP.
    if hp <= 2.0:
        cap = budget
    else:
        cap = min(budget, DAILY_SALARY * 3.0)

    bid = min(cap, base)

    # If budget is extremely low, bid proportionally to avoid zero.
    if budget <= DAILY_SALARY * 0.2:
        bid = min(budget, max(1.0, budget * 0.9))

    # Ensure non-negative
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

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # Baseline: keep enough budget to survive 10 days; avoid Cindy-like full depletion.
    # If supply is high, we can bid less because water allocation is likely easier.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY + 1e-9)
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Read yesterday's bid pressure from traces.
    prev_bids = []
    prev_hp_after = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            prev_bids.append(float(prev['bid']))
            prev_hp_after.append(float(prev.get('hp_after', o.get('hp', 0))))

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    # If Cindy-like behavior happened (very high bid, ended with 0 budget), expect others to bid less now.
    cindy = opponents_status.get('Cindy', None)
    cindy_was_zero = False
    if cindy is not None:
        cindy_was_zero = (float(cindy.get('budget', 0.0)) <= 0.0)

    # Determine target bid.
    # - If my HP is low or I have many no-water days, I must secure water.
    # - Otherwise, underbid relative to yesterday's highest to exploit budget pressure.
    must_have = (hp <= 3.0) or (no_water_days >= 3)

    # Supply tightness: lower supply -> bid more.
    tightness = 1.0 - supply_ratio

    # Core heuristic
    if must_have:
        # Aggressive but not reckless: aim around 0.9*DAILY_SALARY, scaled by tightness.
        target = (DAILY_SALARY * 0.75) + (DAILY_SALARY * 0.25 * tightness)
    else:
        # Moderate bid; if others overbid yesterday, we can shade down.
        # Use yesterday highest as an anchor but discount if Cindy ended at 0 budget.
        discount = 0.85 if cindy_was_zero else 0.95
        # If yesterday highest was huge, don't chase it; bid around mid of those.
        anchor = highest_prev_bid if highest_prev_bid > 0 else avg_prev_bid
        target = (DAILY_SALARY * (0.45 + 0.25 * tightness))
        if anchor > 0:
            target = 0.6 * target + 0.4 * (anchor * discount)

    # Convert target to an actionable bid bounded by budget.
    # Also ensure we don't exceed a reasonable cap to avoid running out like Cindy.
    cap = DAILY_SALARY * 0.95
    bid = min(budget, cap, target)

    # If budget is very low, bid proportionally to preserve remaining days.
    if budget <= DAILY_SALARY * 0.25:
        bid = min(budget, DAILY_SALARY * 0.35)

    # If supply is extremely low (near MIN_SUPPLY), slightly increase to secure.
    if supply <= (MIN_SUPPLY + 1.0):
        bid = min(budget, bid + 10.0)

    # If supply is high, reduce bid to conserve budget.
    if supply >= (MAX_SUPPLY - 2.0) and not must_have:
        bid = bid * 0.85

    # Final safety: bid must be non-negative.
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    # Alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # If no opponents, bid a safe fraction
    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Read yesterday bids from previous_trace only (immediate reaction)
    prev_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # Estimate aggressiveness from yesterday
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    # Pressure heuristic: if someone bid near our daily salary, expect continued competition
    pressure = 0.0
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        pressure = 1.0
    elif highest_prev_bid >= DAILY_SALARY * 0.5:
        pressure = 0.7
    elif avg_prev_bid > DAILY_SALARY * 0.25:
        pressure = 0.4
    else:
        pressure = 0.2

    # Base bid depends on our hp: low hp -> bid to survive
    my_hp = my_status.get('hp', 0)
    my_budget = my_status.get('budget', 0.0)

    # Supply scaling: more supply means we can bid less to still win allocation
    # Convert supply to a rough number of water units available
    # Note: do not use list indices with float; only numeric math.
    supply_level = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_level = (float(supply) - float(MIN_SUPPLY)) / (float(MAX_SUPPLY) - float(MIN_SUPPLY))
    if supply_level < 0.0:
        supply_level = 0.0
    if supply_level > 1.0:
        supply_level = 1.0

    # Target bid formula
    # If Cindy-style aggression occurred (pressure high), we bid moderately-high but not maximal.
    # If we are in danger (hp<=2), we bid close to daily salary.
    if my_hp <= 2:
        target = DAILY_SALARY * (0.85 + 0.15 * pressure)  # 76.5..90
    elif my_hp <= 4:
        target = DAILY_SALARY * (0.60 + 0.20 * pressure)  # 54..78
    else:
        target = DAILY_SALARY * (0.45 + 0.18 * pressure)  # 40.5..61.5

    # Adjust for supply: higher supply -> reduce bid slightly
    target = target * (1.0 - 0.15 * supply_level)

    # If yesterday highest bid was known and is not too far above our target, nudge upward slightly
    # to beat over-aggressive bids.
    if highest_prev_bid > 0.0:
        # If someone bid far above us, we still avoid overpaying; cap by 0.9*DAILY_SALARY
        cap = DAILY_SALARY * 0.9
        target = min(cap, max(target, highest_prev_bid * 0.55))

    # Ensure we don't exceed budget
    bid = min(my_budget, target)

    # Final safety: bid at least a small amount if budget allows
    min_bid = min(my_budget, DAILY_SALARY * 0.15)
    if bid < min_bid:
        bid = min_bid

    return float(bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append((oid, o))

    if not alive_opponents:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Read yesterday bids from each opponent's previous_trace
    yesterday_bids = []
    for _, o in alive_opponents:
        prev = o.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                yesterday_bids.append(float(bid))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Base target: moderate bid to avoid getting outcompeted when others are aggressive.
    # If someone yesterday bid very high, assume they will continue; increase ours.
    # If our HP is low, prioritize survival.
    if my_hp <= 2 or my_no_water_days >= 2:
        target = DAILY_SALARY * 0.85
    else:
        if highest_prev_bid >= DAILY_SALARY * 1.15:
            # Arms-race signal (e.g., Cindy-like aggressiveness)
            target = DAILY_SALARY * 0.65
        elif highest_prev_bid >= DAILY_SALARY * 0.75:
            target = DAILY_SALARY * 0.55
        else:
            target = DAILY_SALARY * 0.45

    # Supply-aware adjustment: if supply is tight, bids need to be stronger.
    # Estimate how many full water units are likely available.
    # Use int indices defensively.
    supply_int = int(round(supply))
    units = int(supply_int / int(WATER_REQ)) if WATER_REQ > 0 else 0
    # If units are 0, it's extremely tight; push higher.
    if units <= 0:
        target *= 1.15
    elif units == 1:
        target *= 1.05

    # Ensure we don't exceed budget
    bid = min(my_budget, float(target))

    # Keep bid non-negative
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
    day = day_context.get('day', 0)

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive = []
    for agent_id, st in opponents_status.items():
        if st.get('alive', False):
            alive.append((agent_id, st))

    if not alive:
        return float(min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace for immediate reaction
    prev_bids = []
    prev_hp_after = []
    for agent_id, st in alive:
        pt = st.get('previous_trace', None)
        if isinstance(pt, dict):
            b = pt.get('bid', None)
            if b is not None:
                try:
                    prev_bids.append(float(b))
                except Exception:
                    pass
            hpa = pt.get('hp_after', None)
            if hpa is not None:
                try:
                    prev_hp_after.append(int(hpa))
                except Exception:
                    pass

    # Baseline: aim to secure water when supply is tighter; otherwise bid less.
    # If supply is near MIN_SUPPLY, competition is likely higher.
    supply_ratio = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    # supply_ratio in [0,1]; closer to 0 => tighter
    tightness = 1.0 - max(0.0, min(1.0, supply_ratio))

    # Determine target bid near a percentile of yesterday bids to beat Cindy without matching her always.
    target = DAILY_SALARY * (0.35 + 0.25 * tightness)  # 31.5..58.5

    if prev_bids:
        sorted_b = sorted(prev_bids)
        # Use median as anchor, then add a small increment to beat top bidder when they were aggressive.
        median_bid = sorted_b[len(sorted_b) // 2] if len(sorted_b) > 0 else target
        max_bid = sorted_b[-1]

        # If someone was extremely aggressive yesterday (close to salary), increase bid.
        if max_bid >= DAILY_SALARY * 0.85:
            # If my hp is low, I must pay more; otherwise just slightly outbid.
            if hp <= 2 or no_water_days >= 2:
                target = max(median_bid * 0.95, DAILY_SALARY * (0.7 + 0.15 * tightness))
            else:
                target = max(median_bid * 1.02, DAILY_SALARY * (0.55 + 0.15 * tightness))
        else:
            # Moderate competition: bid slightly above median.
            target = max(median_bid * 1.03, DAILY_SALARY * (0.45 + 0.12 * tightness))

        # Cap so we don't overpay relative to my budget.
        # Also avoid bidding above what would likely be wasted in tight supply.
        # (Heuristic: if supply is small, excess bid likely loses water anyway.)
        if supply <= float(WATER_REQ) + 6.0:
            target = min(target, DAILY_SALARY * 0.75)

    # Urgency adjustments
    if hp <= 1:
        target *= 1.25
    elif hp <= 3:
        target *= 1.10

    if no_water_days >= 3:
        target *= 1.15

    # Final clamp by budget
    if budget <= 0.0:
        return 0.0

    # Ensure we never exceed budget
    bid = float(min(budget, target))

    # If we can afford a minimal meaningful bid, avoid returning too tiny when competition exists.
    # Use a floor tied to tightness.
    min_bid = DAILY_SALARY * (0.25 + 0.15 * tightness)  # 22.5..36
    if bid < min_bid and budget >= min_bid:
        bid = float(min(budget, min_bid))

    # Avoid negative/NaN
    if bid != bid or bid < 0.0:
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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Inspect yesterday bids only
    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how many water units are likely needed to secure survival
    # If supply is high, we can bid less because competition is less tight.
    # If supply is low, we bid more.
    supply_norm = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_norm = max(0.0, min(1.0, supply_norm))

    # Base bid: undercut aggressive bids unless I'm in danger.
    # hp==9 is safe, so prefer moderate bids.
    danger = (hp <= 2.0) or (no_water_days >= 1)

    if danger:
        target = DAILY_SALARY * 0.85
    else:
        # If someone bid extremely high yesterday, slightly increase to avoid being outbid.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            target = DAILY_SALARY * (0.45 + 0.25 * (1.0 - supply_norm))
        else:
            # Undercut: aim below the highest previous bid but not too low.
            # Use a fraction of highest_prev_bid to stay competitive.
            target = max(DAILY_SALARY * 0.35, highest_prev_bid * 0.75)
            # Adjust for supply tightness.
            target = target * (0.85 + 0.3 * (1.0 - supply_norm))

    # Convert to final bid with budget cap.
    # Also ensure bid is non-negative.
    bid = max(0.0, min(budget, target))

    # If budget is very low, still bid enough to not waste the day.
    if budget < DAILY_SALARY * 0.2:
        bid = max(0.0, min(budget, DAILY_SALARY * 0.15))

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

    # If we are near death, prioritize survival.
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    # Baseline bid based on urgency and supply.
    # If supply is tight, competition is likely higher -> bid more.
    supply_tightness = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_tightness = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_tightness = max(0.0, min(1.0, supply_tightness))

    urgency = 0.0
    if no_water_days >= 2:
        urgency = 1.0
    elif no_water_days == 1:
        urgency = 0.6
    else:
        urgency = 0.2

    # Use yesterday traces to infer aggressiveness.
    # If any opponent bid high yesterday and died, they likely overbid; we can bid less.
    # If any opponent survived with moderate/high bids, they may continue; bid enough to beat them.
    yesterday_bids = []
    yesterday_survivors = 0
    yesterday_deaths = 0
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            b = float(prev['bid'])
            yesterday_bids.append(b)
            if prev.get('status') == 'alive':
                yesterday_survivors += 1
            else:
                yesterday_deaths += 1

    # Determine a target bid ceiling/floor.
    # Observed meta: Cindy ~58 survived; Eric ~6 died quickly (or low bid). We'll aim around 45-70.
    if yesterday_bids:
        max_prev = max(yesterday_bids)
        avg_prev = sum(yesterday_bids) / float(len(yesterday_bids))
        # If someone bid extremely high, don't match; if bids are generally low, we can take advantage.
        if max_prev > DAILY_SALARY * 1.2:
            base = avg_prev * 0.85
        else:
            base = max(DAILY_SALARY * 0.45, avg_prev * 0.95)
    else:
        base = DAILY_SALARY * 0.55

    # Adjust by urgency and supply tightness.
    # When urgent, push toward survival bids; when supply tight, push slightly more.
    multiplier = 1.0 + 0.55 * urgency + 0.35 * supply_tightness

    # If our hp is very low, strongly increase.
    if hp <= 2:
        multiplier += 0.7
    elif hp <= 4:
        multiplier += 0.35

    target = base * multiplier

    # Keep within budget.
    # Also avoid wasting: if budget is large, we can bid more; if small, bid conservatively.
    budget_cap = budget
    if budget_cap <= 0:
        return 0.0

    # Soft cap to avoid extreme overspending.
    # Use remaining days heuristic: later days should bid more.
    remaining_days_factor = 1.0
    if day_context.get('episode_days') is not None:
        try:
            ep_days = int(day_context['episode_days'])
            remaining_days_factor = 1.0 + 0.1 * max(0, ep_days - day) / max(1, ep_days)
        except Exception:
            remaining_days_factor = 1.0

    soft_cap = min(budget_cap, DAILY_SALARY * 0.95 * remaining_days_factor)
    bid = min(target, soft_cap)

    # Ensure we bid at least enough to beat low-bid opponents.
    # If supply is at/near minimum, raise floor.
    floor = DAILY_SALARY * (0.35 + 0.25 * supply_tightness)
    if hp <= 4 or no_water_days >= 1:
        floor = max(floor, DAILY_SALARY * 0.55)

    bid = max(0.0, min(bid, budget_cap))
    if bid < floor and budget_cap >= floor:
        bid = floor

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

    # Identify alive opponents and their yesterday bids
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    # If no opponents are alive, bid conservatively
    if not alive_opps:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.4))

    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Baseline bid depends on our hp/budget urgency
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Urgency scaling: if we're already in danger or low hp, bid more
    urgency = 0.0
    if hp <= 2:
        urgency += 1.0
    if hp == 3:
        urgency += 0.6
    if no_water_days >= 2:
        urgency += 0.6
    if no_water_days >= 3:
        urgency += 0.8

    # Use yesterday's max bid as a proxy for how competitive the market was
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = (sum(yesterday_bids) / len(yesterday_bids)) if yesterday_bids else 0.0

    # Supply pressure: lower supply means fewer winners are satisfied, so bid slightly higher
    # Normalize supply into [0,1] where 0 => MIN_SUPPLY, 1 => MAX_SUPPLY
    if MAX_SUPPLY > MIN_SUPPLY:
        s_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        s_norm = 0.5
    supply_pressure = 1.0 - max(0.0, min(1.0, s_norm))

    # Decision rules
    # If opponents were bidding very high yesterday, we must match moderately to avoid losing water.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        base = DAILY_SALARY * (0.35 + 0.25 * supply_pressure)
        bid = base + 0.25 * (highest_prev_bid - DAILY_SALARY * 0.85)
    else:
        # Otherwise, stay near a mid bid; adjust with urgency and supply pressure
        bid = DAILY_SALARY * (0.50 + 0.15 * supply_pressure) + 20.0 * urgency

    # If our hp is comfortable, do not overspend
    if hp >= 6 and urgency < 0.5:
        bid *= 0.85

    # Ensure we don't bid more than our budget
    bid = max(0.0, min(budget, bid))

    # If budget is extremely low, bid whatever remains (to avoid guaranteed starvation)
    if budget <= 10.0:
        return bid

    # Small tie-breaker: if our hp is low, add a tiny increment
    if hp <= 3:
        bid += 2.0
        bid = min(budget, bid)

    return float(bid)
"""
