# ============================================================
# Experiment: exp_002
# Agent: Bob
# Source: exp_002
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    alive_opponents = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opponents:
        return min(my_status.get('budget', 0.0), DAILY_SALARY * 0.4)

    # Read yesterday's bids for immediate reaction
    yesterday_bids = []
    for opp_id, opp in opponents_status.items():
        if not opp.get('alive', False):
            continue
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # Threshold: if they were bidding aggressively yesterday, they likely continue.
        aggressive_threshold = DAILY_SALARY * 0.85

        if highest_prev_bid >= aggressive_threshold:
            # If we are healthy, slightly undercut; if low HP, match more.
            if hp > 3:
                bid = DAILY_SALARY * 0.30
            else:
                bid = DAILY_SALARY * 0.85
        else:
            # If they were moderate, aim to beat the leader by a small margin.
            bid = max(DAILY_SALARY * 0.50, highest_prev_bid + 1.5)
    else:
        # No signal: bid based on our HP.
        if hp <= 2:
            bid = DAILY_SALARY * 0.90
        elif hp <= 3:
            bid = DAILY_SALARY * 0.70
        else:
            bid = DAILY_SALARY * 0.55

    # Supply-aware adjustment: if supply is near minimum, slightly increase to secure water.
    # Use only safe arithmetic; no list indexing.
    try:
        if supply <= 16.0:
            bid *= 1.10
        elif supply >= 22.0:
            bid *= 0.95
    except Exception:
        pass

    # Never bid more than we can afford.
    bid = min(budget, bid)

    # Keep bids non-negative.
    if bid < 0.0:
        bid = 0.0

    return bid
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
        cap = min(budget, DAILY_SALARY * 0.4)
        return max(0.0, cap)

    # Read yesterday bids to infer aggressiveness
    prev_bids = []
    prev_max_bid = 0.0
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                b = float(b)
                prev_bids.append(b)
                if b > prev_max_bid:
                    prev_max_bid = b
            except Exception:
                pass

    # Supply pressure: if supply is near minimum, competition likely higher.
    # Convert supply to a coarse level.
    if supply <= float(MIN_SUPPLY):
        pressure = 1.0
    elif supply >= float(MAX_SUPPLY):
        pressure = 0.2
    else:
        # linear scale from 1.0 at MIN_SUPPLY to 0.2 at MAX_SUPPLY
        pressure = 1.0 - 0.8 * ((supply - float(MIN_SUPPLY)) / (float(MAX_SUPPLY) - float(MIN_SUPPLY)))

    # Base willingness to bid
    # If my HP is low or I have already missed water, increase bid.
    if hp <= 2.0 or no_water_days >= 1:
        base = DAILY_SALARY * (0.75 + 0.2 * pressure)
    elif hp <= 4.0:
        base = DAILY_SALARY * (0.55 + 0.2 * pressure)
    else:
        base = DAILY_SALARY * (0.45 + 0.15 * pressure)

    # Exploit trace: Cindy bid very high and survived; others with 0 budget/low hp suggest they can't sustain.
    # So we avoid matching extreme bids; only slightly react to the top bid unless it's near total salary.
    if prev_bids:
        if prev_max_bid >= DAILY_SALARY * 0.9:
            # Cindy-like aggression: don't chase fully; bid enough to beat weaker opponents.
            base = min(base, DAILY_SALARY * 0.65)
        else:
            # If top bid is moderate, nudge upward to outbid likely competitors.
            base = max(base, min(DAILY_SALARY * 0.6, prev_max_bid + 5.0))

    # Ensure we can afford it
    bid = min(budget, base)

    # Safety: if budget is tiny, still bid something to avoid starvation.
    if bid < 1.0:
        bid = min(budget, DAILY_SALARY * 0.15)

    # Clamp to non-negative
    if bid < 0.0:
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
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((opp_id, o))

    # Baseline: if low hp, bid to avoid collapse.
    if hp <= 2:
        cap = min(budget, DAILY_SALARY * 0.95)
        return max(0.0, cap)

    # React to yesterday's bids (immediate pressure signal)
    yesterday_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {})
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                yesterday_bids.append(float(bid))
            except Exception:
                pass

    # If someone bid extremely high yesterday, assume they were trying to secure water.
    # Counter by bidding somewhat high, but not maximal.
    pressure = 0.0
    if yesterday_bids:
        pressure = max(yesterday_bids)

    # Supply-aware adjustment: low supply days need more aggressive bidding to secure allocation.
    # Map supply in [15,25] to a multiplier in [1.15, 0.95]
    if MAX_SUPPLY > MIN_SUPPLY:
        t = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        t = 0.5
    t = max(0.0, min(1.0, float(t)))
    supply_mult = 1.15 - 0.20 * t

    # Budget safety: never bid more than what would likely waste money if we can survive.
    # If we've already had no-water days, increase urgency.
    urgency = 1.0 + min(0.4, 0.15 * max(0, no_water_days))

    # Core bid target
    target = DAILY_SALARY * 0.55 * supply_mult * urgency

    # If yesterday pressure was high, nudge up slightly to avoid being outbid.
    if pressure >= DAILY_SALARY * 0.85:
        target = max(target, DAILY_SALARY * 0.70 * supply_mult)
    elif pressure <= DAILY_SALARY * 0.20:
        # If opponents were timid, we can bid a bit lower.
        target = min(target, DAILY_SALARY * 0.50 * supply_mult)

    # Ensure not exceeding budget.
    bid = min(budget, target)

    # Hard floor: if we can’t bid much, bid at least a small amount to try to get water.
    if bid < 1.0 and budget >= 1.0:
        bid = 1.0

    return float(max(0.0, bid))
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
    day = day_context.get('day', 0)

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    if not alive_opponents:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from immediate previous_trace only
    prev_bids = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Determine if opponents were bidding aggressively yesterday
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    # Estimate how many
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
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday bids from immediate previous_trace
    prev_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Supply pressure: estimate how many full water units are available
    # (not exact game mechanic, but helps decide whether to conserve or contest)
    # Ensure indices are safe: we don't use list indexing.
    supply_units = supply / float(WATER_REQ) if WATER_REQ else 0.0

    # Base bid policy
    # - If our hp is low or we've gone without water, bid more.
    # - If others bid extremely high yesterday, bid moderately to avoid budget drain.
    # - If supply is tight, raise slightly.
    tight_supply = supply <= (MIN_SUPPLY + 1.0)

    if hp <= 2.0 or no_water_days >= 2:
        # Emergency: try to secure water
        target = DAILY_SALARY * (0.75 if tight_supply else 0.65)
    else:
        # Normal: contest only if yesterday bids were not already maxed out
        if highest_prev_bid >= DAILY_SALARY * 1.4:
            # Others were very aggressive; don't mirror fully.
            target = DAILY_SALARY * (0.45 if tight_supply else 0.40)
        elif highest_prev_bid >= DAILY_SALARY * 0.9:
            target = DAILY_SALARY * (0.55 if tight_supply else 0.50)
        else:
            target = DAILY_SALARY * (0.60 if tight_supply else 0.48)

    # If supply is abundant, we can bid lower
    if supply_units >= (MAX_SUPPLY / float(WATER_REQ)) * 0.85:
        target *= 0.85

    # Convert to an integer bid (typical auction style); ensure within budget
    bid = min(budget, float(target))

    # Avoid bidding too low when we are at risk
    if hp <= 4.0 and bid < DAILY_SALARY * 0.35:
        bid = min(budget, DAILY_SALARY * 0.45)

    # Ensure non-negative
    if bid < 0:
        bid = 0.0

    return int(bid)
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

    # Identify alive opponents and their yesterday bids
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace
    yesterday_bids = []
    yesterday_pressured = []
    for opp_id, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                b = float(bid)
                yesterday_bids.append(b)
                if b >= DAILY_SALARY * 0.85:
                    yesterday_pressured.append(b)
            except Exception:
                pass

    # Base bid target: aim to secure enough water without exhausting budget
    # With supply 15-25, one unit (9 water) is likely enough for us; we just need to win at least that.
    # Translate to a bid scale: moderate-high when opponents showed pressure.
    if my_status['hp'] <= 2:
        baseline = DAILY_SALARY * 0.9
    elif my_status['hp'] <= 4:
        baseline = DAILY_SALARY * 0.7
    else:
        baseline = DAILY_SALARY * 0.58

    # If any opponent bid very high yesterday, match pressure slightly below their peak
    if yesterday_pressured:
        peak = max(yesterday_pressured)
        # Keep a margin so we don't overpay; still likely to win against high bidders
        target = min(DAILY_SALARY * 0.95, peak - 2.0)
        bid = min(my_status['budget'], target)
        return float(max(0.0, bid))

    # Otherwise, follow the general level of survival bids
    if yesterday_bids:
        avg = sum(yesterday_bids) / float(len(yesterday_bids))
        # Bid around average but with a safety cap
        target = min(DAILY_SALARY * 0.8, max(DAILY_SALARY * 0.48, avg * 0.85))
    else:
        target = baseline

    # Budget-aware and supply-aware adjustment
    # If supply is closer to MIN_SUPPLY, competition is more valuable -> bid slightly higher.
    supply_factor = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY) if (MAX_SUPPLY - MIN_SUPPLY) != 0 else 0.5
    # supply_factor near 0 means low supply -> bid up; near 1 means high supply -> bid down
    competition_boost = (1.0 - supply_factor) * 0.12  # up to +12%

    if my_status['no_water_days'] >= 2:
        # We are at risk of running out; increase bid
        target = target * (1.0 + 0.18)

    bid = target * (1.0 + competition_boost)
    bid = min(my_status['budget'], bid)

    # Ensure we don't bid absurdly; also keep non-negative
    bid = float(max(0.0, bid))
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

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive.append((opp_id, opp))

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace for immediate reaction
    yesterday_bids = []
    for _, opp in alive:
        prev = opp.get('previous_trace', None) or {}
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how many water units are likely needed today.
    # With simultaneous auctions, bid more when supply is tight.
    # supply in [15,25] implies 1 or 2 units of water requirement.
    # Use a conservative target: if supply is closer to 15, assume only 1 unit.
    if supply <= (MIN_SUPPLY + MAX_SUPPLY) / 2.0:
        # tighter day
        pressure = 1.0
    else:
        pressure = 0.7

    # If my hp is low or I've already gone without water, increase bid.
    if hp <= 2.0 or no_water_days >= 2:
        self_need = 1.0
    elif hp <= 4.0 or no_water_days == 1:
        self_need = 0.75
    else:
        self_need = 0.55

    # Opponent aggression signal: if someone bid near/above salary, they likely fight for water.
    if highest_prev_bid >= DAILY_SALARY * 0.95:
        opp_aggression = 1.0
    elif highest_prev_bid >= DAILY_SALARY * 0.7:
        opp_aggression = 0.85
    elif highest_prev_bid >= DAILY_SALARY * 0.5:
        opp_aggression = 0.7
    else:
        opp_aggression = 0.55

    # Base bid: aim to be competitive but not maximal.
    # Target roughly around 0.55-0.85 of salary, scaled by pressure and needs.
    target = DAILY_SALARY * 0.55
    target *= (0.65 + 0.35 * pressure)
    target *= (0.6 + 0.4 * self_need)
    target *= (0.6 + 0.4 * opp_aggression)

    # If opponents were bidding high yesterday, nudge upward slightly.
    if highest_prev_bid > 0.0:
        # Keep within a reasonable band; avoid matching their max exactly.
        target = max(target, min(DAILY_SALARY * 0.85, highest_prev_bid * 0.75 + 5.0))

    # Ensure we don't bid above budget.
    bid = max(0.0, min(budget, target))

    # If budget is very low, still bid enough to try once.
    if budget <= DAILY_SALARY * 0.2:
        bid = max(0.0, min(budget, DAILY_SALARY * 0.15))

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
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace (immediate reaction only)
    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = sorted(yesterday_bids)[-2] if len(yesterday_bids) >= 2 else highest_prev_bid

    # Estimate how tight the market is: supply range is [15,25] with WATER_REQ=9.
    # If supply is low, water is scarce -> bid more.
    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    scarcity = max(0.0, min(1.0, scarcity))

    # Base bid: slightly above the typical aggressive cluster, but capped by budget.
    # Use highest_prev_bid to exploit their willingness to pay.
    # If they were already paying very high, we go higher only when our hp is ok.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        target = highest_prev_bid + (6.0 * scarcity)
        if hp <= 2.0 or no_water_days >= 2:
            target = highest_prev_bid + (12.0 * scarcity)
        else:
            target = highest_prev_bid + (4.0 * scarcity)
    else:
        # If they were not bidding extremely high, undercut slightly but still compete.
        # Aim between (second_prev_bid) and (highest_prev_bid), boosted by scarcity.
        mid = 0.5 * (second_prev_bid + highest_prev_bid)
        target = mid + (10.0 * scarcity)

    # Convert target into a safe bid within budget; also keep a floor to avoid losing to low bids.
    # Ensure we never bid negative.
    min_reasonable = DAILY_SALARY * (0.45 + 0.25 * scarcity)
    bid = max(min_reasonable, target)
    bid = max(0.0, min(budget, bid))

    # If our hp is critical, spend more aggressively.
    if hp <= 2.0:
        bid = max(bid, min(budget, DAILY_SALARY * (0.9 + 0.1 * scarcity)))

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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    my_hp = float(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    if not alive_opponents:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids for immediate reaction
    prev_bids = []
    for opp_id, opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Identify the likely highest-pressure opponent based on yesterday
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Supply-aware baseline: with supply in [15,25], allocate enough to compete for at least one unit
    # but avoid overpaying.
    supply_ratio = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # If my hp is critical or I've already gone without water, bid aggressively.
    critical = (my_hp <= 2.0) or (my_no_water_days >= 2)

    # If Cindy-like behavior is present (very high yesterday bid), we should not let her win cheaply.
    # Use a target bid slightly above yesterday's highest, but capped to budget.
    if highest_prev_bid >= DAILY_SALARY * 1.5:
        base_target = highest_prev_bid + 3.0
    elif highest_prev_bid >= DAILY_SALARY * 0.85:
        base_target = highest_prev_bid + 1.5
    else:
        # No strong pressure yesterday: bid around a moderate fraction of daily salary.
        base_target = DAILY_SALARY * (0.45 + 0.25 * supply_ratio)

    if critical:
        # Ensure we secure water when survival is at risk.
        base_target = max(base_target, DAILY_SALARY * (0.85 + 0.1 * supply_ratio))

    # Also consider that some opponents may be broke; if many are low budget, we can bid lower.
    low_budget_count = 0
    for _, opp in alive_opponents:
        if float(opp.get('budget', 0.0)) <= 1.0:
            low_budget_count += 1
    if low_budget_count >= 1:
        base_target *= 0.85

    # Final cap/floor
    bid = max(0.0, min(my_budget, base_target))
    # Avoid bidding 0 unless we truly have no budget.
    if bid == 0.0 and my_budget > 0.0:
        bid = min(my_budget, DAILY_SALARY * 0.2)

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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        try:
            if o.get('alive', False):
                alive_opps.append((oid, o))
        except Exception:
            continue

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace for immediate reaction
    yesterday_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) if isinstance(o, dict) else {}
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # Estimate a competitive target from yesterday
    target = DAILY_SALARY * 1.05  # ~94.5 baseline
    if yesterday_bids:
        # If there was a strong aggressive cluster, slightly overbid it
        max_prev = max(yesterday_bids)
        # If max_prev is very high, we don't chase fully; we just ensure competitiveness
        if max_prev >= DAILY_SALARY * 1.00:
            target = min(MAX_SUPPLY * 8.0, max_prev + 2.0)  # cap to avoid runaway
        else:
            # Otherwise, bid around the top of the pack
            target = min(MAX_SUPPLY * 8.0, max_prev + 1.0)

    # Adjust based on my survival pressure
    if hp <= 2.0 or no_water_days >= 2:
        # Need water; be aggressive but don't exceed affordable
        target = max(target, DAILY_SALARY * 1.10)  # ~99
    elif hp <= 4.0:
        target = max(target, DAILY_SALARY * 0.95)  # ~85.5
    else:
        # Healthy: bid enough to win but avoid wasting budget
        target = min(target, DAILY_SALARY * 1.00)  # ~90

    # Convert target into a bid that respects budget and plausible supply
    # Supply up to 25; typical winning bids seem around 90-100, so keep in that band.
    bid = min(budget, target)

    # If supply is low, slightly increase bid probability of securing water
    if supply <= float(MIN_SUPPLY):
        bid = min(budget, bid + 5.0)

    # Ensure non-negative
    if bid < 0.0:
        bid = 0.0

    return float(bid)
"""
