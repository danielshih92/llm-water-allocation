# ============================================================
# Experiment: exp_067
# Agent: Bob
# Source: exp_067
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

    alive_opponents = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Read yesterday bids (immediate reaction only)
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            yesterday_bids.append(prev['bid'])

    # If no trace info, default to a mid bid
    if not yesterday_bids:
        if my_status['hp'] <= 2 or my_status['no_water_days'] >= 2:
            return min(my_status['budget'], DAILY_SALARY * 0.85)
        return min(my_status['budget'], DAILY_SALARY * 0.55)

    highest_prev_bid = max(yesterday_bids)

    # Determine our urgency
    urgent = (my_status.get('hp', 0) <= 2) or (my_status.get('no_water_days', 0) >= 2)

    # If opponents were very aggressive yesterday, slightly undercut to win at lower cost
    # Threshold tuned to DAILY_SALARY scale.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        if urgent:
            target = highest_prev_bid - 2.0
        else:
            target = highest_prev_bid - 6.0
        target = max(target, DAILY_SALARY * 0.25)
        bid = min(my_status['budget'], target)
        return bid

    # If opponents bid moderately/low, we bid enough to secure water but avoid escalation
    # Scale with available supply: if supply is tight, bid higher.
    # supply is float, but we only use it in arithmetic; no list indexing.
    supply_tightness = 0.0
    if supply <= 16.0:
        supply_tightness = 0.75
    elif supply <= 19.0:
        supply_tightness = 0.55
    elif supply <= 22.0:
        supply_tightness = 0.35
    else:
        supply_tightness = 0.2

    base = DAILY_SALARY * (0.45 + supply_tightness)
    if urgent:
        base = DAILY_SALARY * (0.70 + supply_tightness)

    # Also ensure we can beat the highest yesterday bid when possible, but not fully.
    # Undercut by a small margin to reduce overpayment.
    target = max(base, highest_prev_bid * 0.95)
    if not urgent:
        target = min(target, highest_prev_bid + 3.0)

    bid = min(my_status['budget'], target)

    # If our budget is extremely low, bid what we can.
    if bid < 1.0:
        bid = min(my_status['budget'], DAILY_SALARY * 0.2)

    return bid
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return min(float(my_status['budget']), DAILY_SALARY * 0.4)

    # Read yesterday traces for immediate reaction
    prev_bids = []
    for opp_id, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    prev_bids.append(float(b))
                except Exception:
                    pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])

    # Base aggressiveness from yesterday's market pressure
    # If others were bidding close to daily salary, we must bid enough to secure water.
    # But since we don't know exact allocation rules, keep bid in a mid band to avoid waste.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # High pressure yesterday
        if my_hp <= 2.0:
            target = DAILY_SALARY * 0.95
        elif my_hp <= 4.0:
            target = DAILY_SALARY * 0.75
        else:
            target = DAILY_SALARY * 0.65
    else:
        # Moderate pressure
        if my_hp <= 2.0:
            target = DAILY_SALARY * 0.85
        elif my_hp <= 4.0:
            target = DAILY_SALARY * 0.65
        else:
            target = DAILY_SALARY * 0.55

    # Supply-aware slight adjustment: when supply is higher, we can bid slightly less.
    # supply range is 15..25 (meta scenario medium)
    # Normalize: 15->0, 25->1
    norm = (supply - 15.0) / 10.0
    if norm < 0.0:
        norm = 0.0
    if norm > 1.0:
        norm = 1.0

    # If supply is scarce, increase bid; if abundant, decrease bid.
    target = target * (1.08 - 0.12 * norm)

    # No-water days: if we've been without water, increase urgency.
    no_water_days = float(my_status.get('no_water_days', 0.0))
    if no_water_days >= 2.0:
        target *= 1.15
    elif no_water_days >= 1.0:
        target *= 1.07

    # Budget cap
    bid = min(my_budget, target)

    # Ensure non-negative
    if bid < 0.0:
        bid = 0.0

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

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))

    alive_opponents = []
    for opp_id, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append((opp_id, o))

    # Baseline bid: aim to be competitive but not highest.
    # With supply 15-25 and WATER_REQ=9, typical scarcity is mild; overbidding wastes budget.
    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    baseline = DAILY_SALARY * (0.45 + 0.25 * scarcity)  # ~40-63

    # React to yesterday's bids (immediate trace only).
    prev_bids = []
    for opp_id, o in alive_opponents:
        prev = o.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                prev_bids.append(float(bid))
            except Exception:
                pass

    # If someone was bidding extremely high yesterday, assume they will repeat pressure.
    # But we avoid matching the maximum; we bid just above the 2nd-highest when possible.
    if prev_bids:
        sorted_bids = sorted(prev_bids)
        highest = sorted_bids[-1]
        second_highest = sorted_bids[-2] if len(sorted_bids) >= 2 else sorted_bids[-1]

        # If highest was very high, we need to ensure we get water.
        if highest >= DAILY_SALARY * 1.35:  # >=121.5
            # If our hp is low, we bid closer to highest; otherwise slightly below.
            if hp <= 3:
                target = min(highest - 1.0, second_highest + 8.0)
            else:
                target = min(second_highest + 6.0, highest - 4.0)
        else:
            # Otherwise, bid around baseline but nudge above the second-highest
            # to beat most non-top bidders.
            target = max(baseline, second_highest + 3.0)
    else:
        target = baseline

    # Budget/HP safety: if we're in danger, spend more; if healthy, cap spending.
    if hp <= 2:
        cap = DAILY_SALARY * 0.95
    elif hp <= 4:
        cap = DAILY_SALARY * 0.75
    else:
        cap = DAILY_SALARY * 0.65

    bid = min(budget, max(0.0, min(target, cap)))

    # Small adjustment based on day parity to avoid deterministic ties.
    if day % 2 == 1:
        bid *= 1.02

    # Final clamp
    bid = float(max(0.0, min(bid, budget)))
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Alive opponents
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', True):
            alive.append(o)

    # Read yesterday bids from previous_trace (immediate reaction only)
    yesterday_bids = []
    for o in alive:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # If no info, default to a safe moderate bid
    if not yesterday_bids:
        base = DAILY_SALARY * 0.55
        if my_status['hp'] <= 2:
            base = DAILY_SALARY * 0.9
        elif my_status['hp'] <= 4:
            base = DAILY_SALARY * 0.7
        return max(0.0, min(float(my_status['budget']), base))

    highest_prev_bid = max(yesterday_bids)

    # Estimate how many water units might matter today
    # Use supply to set aggressiveness: higher supply -> less need to overpay
    # Convert supply to an approximate number of allocations per unit, but avoid float indices.
    # We'll map supply into a tier.
    if supply <= 17.0:
        supply_tier = 0  # scarce
    elif supply <= 21.0:
        supply_tier = 1  # medium
    else:
        supply_tier = 2  # abundant

    # Aggression multiplier by tier
    tier_mult = [1.15, 1.0, 0.85]
    mult = tier_mult[int(supply_tier)]

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])

    # Decide target bid relative to yesterday's max bid.
    # Since Cindy and Eric were willing to bid ~150 and survive, we should not be too low.
    # But we also avoid matching the absolute max; we aim slightly above a fraction.
    # If highest_prev_bid was extremely high, we bid to contest but cap.
    if highest_prev_bid >= 145.0:
        target = highest_prev_bid * 0.72
    elif highest_prev_bid >= 120.0:
        target = highest_prev_bid * 0.65
    else:
        target = max(DAILY_SALARY * 0.55, highest_prev_bid + 5.0)

    # HP-based adjustment: if low HP, increase bid to secure survival
    if my_hp <= 1:
        target *= 1.35
    elif my_hp <= 2:
        target *= 1.25
    elif my_hp <= 4:
        target *= 1.12

    # Apply supply tier multiplier
    target *= mult

    # Keep within reasonable bounds relative to salary and budget.
    # Never exceed budget.
    # Also avoid wasting: if budget is low, bid a fraction to preserve for remaining days.
    no_water_days = int(my_status.get('no_water_days', 0))

    # Budget pressure heuristic
    if my_budget <= DAILY_SALARY * 0.6:
        # conserve
        target = min(target, DAILY_SALARY * 0.65)

    # If already had many no-water days, prioritize survival more
    if no_water_days >= 3:
        target = max(target, DAILY_SALARY * 0.75)

    # Final cap: don't exceed ~1.2*salary unless my HP is critical
    if my_hp > 2:
        target = min(target, DAILY_SALARY * 1.05)
    else:
        target = min(target, DAILY_SALARY * 1.25)

    bid = max(0.0, min(my_budget, float(target)))
    return bid
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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    my_hp = float(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Read yesterday bids from previous_trace only (immediate reaction)
    prev_bids = []
    for o in alive_opps:
        pt = o.get('previous_trace', {}) or {}
        b = pt.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate opponent pressure: if someone bid very high yesterday, they likely continue.
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Convert supply into a rough "urgency" proxy: more supply => easier to win without extreme bids.
    # Use integer-safe indexing by mapping to bins.
    # supply in [15,25] => 3 bins
    bin_idx = int((supply - MIN_SUPPLY) / ((MAX_SUPPLY - MIN_SUPPLY) / 3.0))
    if bin_idx < 0:
        bin_idx = 0
    if bin_idx > 2:
        bin_idx = 2

    # Base bid target: moderate, then adjust for my hp/no-water.
    # These targets aim to beat Cindy (high bidder) only when my situation is critical.
    base_targets = [DAILY_SALARY * 0.45, DAILY_SALARY * 0.55, DAILY_SALARY * 0.65]
    target = float(base_targets[bin_idx])

    # If highest opponent bid was huge, they likely value survival; avoid full contest unless needed.
    if highest_prev_bid >= DAILY_SALARY * 0.95:
        # Only escalate if I'm in danger.
        if my_hp <= 2 or my_no_water_days >= 2:
            target = DAILY_SALARY * 0.9
        else:
            target = min(target, DAILY_SALARY * 0.6)

    # If I am already near death, bid aggressively.
    if my_hp <= 2:
        target = max(target, DAILY_SALARY * 0.85)
    elif my_hp <= 4:
        target = max(target, DAILY_SALARY * 0.65)

    # If I've gone multiple days without water, increase urgency.
    if my_no_water_days >= 3:
        target = max(target, DAILY_SALARY * 0.8)
    elif my_no_water_days == 2:
        target = max(target, DAILY_SALARY * 0.65)

    # Budget cap
    if my_budget <= 0:
        return 0.0

    bid = min(my_budget, target)

    # Small rationalization: if supply is low end, slightly more to secure allocation.
    if supply <= (MIN_SUPPLY + 2):
        bid = min(my_budget, bid + DAILY_SALARY * 0.05)

    # Ensure non-negative
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

    # Alive opponents and yesterday bids
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    # If no one alive, spend conservatively
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace
    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', None)
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    yesterday_bids.append(float(b))
                except Exception:
                    pass

    # Estimate how many units we can plausibly secure: fewer units => higher competition => higher bid
    # supply is in [15,25]; competition increases as supply approaches 15.
    tightness = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)  # 0..1

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Determine target bid based on yesterday's max pressure
    base = DAILY_SALARY * (0.45 + 0.25 * tightness)  # mid-range, increases when supply tight

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # If someone previously overbid aggressively, avoid mirroring; instead bid slightly above base.
        # If yesterday pressure was low, bid closer to base to save budget.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            # Cindy-like behavior: don't chase; stay controlled.
            base = DAILY_SALARY * (0.50 + 0.20 * tightness)
        elif highest_prev_bid <= DAILY_SALARY * 0.35:
            base = DAILY_SALARY * (0.40 + 0.15 * tightness)
        else:
            base = max(base, highest_prev_bid * 0.55)

    # Urgency adjustment: if low HP or already in no-water streak, bid higher to avoid death
    if my_hp <= 2.0 or no_water_days >= 2:
        base = DAILY_SALARY * (0.80 + 0.15 * tightness)
    elif my_hp <= 4.0:
        base = max(base, DAILY_SALARY * (0.65 + 0.10 * tightness))

    # Budget cap
    bid = float(min(my_budget, base))

    # Ensure non-negative
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

    supply = day_context['supply']
    day = day_context['day']

    # Identify alive opponents
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # If no opponents alive, bid conservatively
    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Use only yesterday trace to infer aggressiveness
    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Estimate how many water units we likely need to avoid a no-water day
    # If supply is below WATER_REQ, we can't fully satisfy; still bid to maximize chance.
    supply_units = supply / float(WATER_REQ)

    # Pressure signal from yesterday
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Base target bid depends on our hp and supply regime
    # Keep bids below Cindy-like aggressive level unless our hp is critical.
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # Determine aggressiveness threshold from observed meta
    # Cindy averaged ~155.5; use 160 as a proxy for
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

    supply = day_context['supply']
    day = day_context['day']

    # Alive opponents
    alive_opponents = []
    for k, o in opponents_status.items():
        if o.get('alive', False):
            alive_opponents.append(o)

    if not alive_opponents:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Extract yesterday bids from previous_trace
    yesterday_bids = []
    for o in alive_opponents:
        prev = o.get('previous_trace', {})
        if isinstance(prev, dict) and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Determine target bid based on my hp and yesterday pressure
    my_hp = float(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0))

    # Supply pressure heuristic: with higher supply, bidding can be lower.
    # Normalize supply into [0,1]
    if MAX_SUPPLY - MIN_SUPPLY > 0:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_norm = 0.5
    supply_norm = max(0.0, min(1.0, float(supply_norm)))

    # Base aggressiveness
    if my_hp <= 2.0:
        base = DAILY_SALARY * 0.95
    elif my_hp <= 4.0:
        base = DAILY_SALARY * 0.70
    else:
        base = DAILY_SALARY * (0.45 + 0.15 * supply_norm)

    # React to yesterday's highest bid: if others were willing to pay near salary, increase to avoid losing.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # If I am not in immediate danger, still raise enough to compete.
        if my_hp > 3.0:
            bid = max(base, DAILY_SALARY * 0.65)
        else:
            bid = max(base, DAILY_SALARY * 0.95)
    elif highest_prev_bid >= DAILY_SALARY * 0.55:
        bid = max(base, highest_prev_bid * 0.85)
    else:
        # If yesterday bids were low, don't overpay.
        bid = min(base, max(DAILY_SALARY * 0.55, highest_prev_bid + 5.0))

    # If budget is low, cap aggressively to avoid going broke.
    # Also consider no_water_days: if already accumulating, bid more.
    no_water_days = float(my_status.get('no_water_days', 0))
    if no_water_days >= 2.0:
        bid = max(bid, DAILY_SALARY * 0.75)

    # Final cap
    bid = min(bid, my_budget)

    # If extremely low budget, bid whatever remains (game will likely end anyway)
    if bid <= 0:
        return 0.0

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
    day = day_context.get('day', 0)

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', True):
            alive_opps.append((oid, o))

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday bids from previous_trace only
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Determine pressure from yesterday
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Supply pressure heuristic: higher supply reduces need to overbid
    # (supply is within [15,25] in this meta-round)
    supply_norm = 0.0
    try:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    except Exception:
        supply_norm = 0.0
    supply_norm = max(0.0, min(1.0, supply_norm))

    # Core strategy: if others were bidding high, bid close to them to secure water.
    # Keep bid under budget and within a sensible band.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Match slightly below the highest to win while saving budget.
        target = highest_prev_bid * (0.98 - 0.12 * supply_norm)
        # If we're already in danger, bid more aggressively.
        if hp <= 3 or no_water_days >= 2:
            target = highest_prev_bid * (1.00 - 0.08 * supply_norm)
    elif highest_prev_bid >= DAILY_SALARY * 0.55:
        # Moderate competition: bid around the upper-middle.
        target = max(DAILY_SALARY * 0.6, highest_prev_bid + 2.0)
        target = target * (0.95 - 0.1 * supply_norm)
    else:
        # Low competition: bid just enough to likely secure water.
        base = DAILY_SALARY * (0.5 + 0.25 * (1.0 - supply_norm))
        if hp <= 3 or no_water_days >= 2:
            base = DAILY_SALARY * 0.85
        target = base

    # Ensure we don't bid more than our budget.
    # Also cap to avoid reckless spending.
    # Since winning requires water, spending too little risks losing; but overpaying burns budget.
    max_reasonable = min(budget, DAILY_SALARY * 1.6)
    bid = min(max_reasonable, max(0.0, target))

    # Final safety: if budget is tiny, bid what we can.
    if budget <= 1.0:
        return budget

    # Avoid exact zero if we still need water.
    if bid < 1e-6:
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

    supply = day_context['supply']
    day = day_context['day']

    # Basic feasibility/budget guard
    if my_status['budget'] <= 0:
        return 0.0

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        # If no one else alive, conserve: bid enough to cover our own need
        # (We don't know exact mapping from bid->water, so use a conservative fraction.)
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids to infer pressure
    prev_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            prev_bids.append(float(b))

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    # Supply-based aggressiveness: in medium scenario supply ~15-25, our water need is 9.
    # If supply is closer to 25, competition is less tight; if closer to 15, competition is tighter.
    # Normalize to [0,1]
    if MAX_SUPPLY != MIN_SUPPLY:
        supply_tightness = (MAX_SUPPLY - float(supply)) / float(MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_tightness = 0.5
    supply_tightness = max(0.0, min(1.0, supply_tightness))

    hp = float(my_status['hp'])
    no_water_days = int(my_status.get('no_water_days', 0))
    budget = float(my_status['budget'])

    # Target bid logic:
    # - If yesterday pressure was very high (>=120), we must bid higher to secure water.
    # - Otherwise, bid around a fraction of salary, adjusted by tightness and our hp.
    if highest_prev_bid >= 120.0:
        # Escalate depending on survival risk
        if hp <= 2.0 or no_water_days >= 2:
            target = DAILY_SALARY * 0.95
        elif hp <= 3.0:
            target = DAILY_SALARY * 0.75
        else:
            target = DAILY_SALARY * 0.60
        # Slightly undercut/track the market: add small premium over average if needed
        target = max(target, avg_prev_bid * 0.98)
    else:
        # Moderate bidding: preserve budget
        base = DAILY_SALARY * (0.45 + 0.25 * supply_tightness)
        # If we're already accumulating no-water days or low hp, increase
        if hp <= 3.0:
            base *= 1.25
        elif hp <= 5.0:
            base *= 1.10
        if no_water_days >= 3:
            base *= 1.20
        # If yesterday bids suggest mild competition, slightly raise above average
        if avg_prev_bid > 0:
            base = max(base, avg_prev_bid * 0.85)
        target = base

    # Convert to final bid within budget and reasonable cap
    # Also keep a floor to avoid bidding too low when tight.
    floor_bid = DAILY_SALARY * (0.25 + 0.25 * supply_tightness)
    target = max(float(floor_bid), float(target))

    # Never exceed budget
    bid = min(budget, float(target))

    # If hp is extremely low, go all-in on survival
    if hp <= 1.0:
        bid = min(budget, DAILY_SALARY * 1.0)

    return float(bid)
"""
