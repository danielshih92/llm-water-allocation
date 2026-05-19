# ============================================================
# Experiment: exp_029
# Agent: Bob
# Source: exp_029
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

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    def clamp_bid(x):
        if x < 0:
            return 0
        if my_status['budget'] is not None:
            return min(float(my_status['budget']), float(x))
        return float(x)

    # Immediate reaction from yesterday trace
    prev_bids = []
    prev_hp = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass
        try:
            prev_hp.append(float(prev.get('hp_after', opp.get('hp', 0))))
        except Exception:
            prev_hp.append(float(opp.get('hp', 0)))

    my_hp = float(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0))

    # Target bid: aim to win enough share for our fixed requirement.
    # With simultaneous bids, a near-competitor bid is usually best.
    base_need = DAILY_SALARY * 0.55
    if my_hp <= 2:
        base_need = DAILY_SALARY * 0.9
    elif my_hp <= 4:
        base_need = DAILY_SALARY * 0.7

    if prev_bids:
        highest_prev_bid = max(prev_bids)
        # If they were very aggressive, we match high pressure but stay slightly under.
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            bid = min(my_budget, highest_prev_bid * 0.92)
            # Ensure we don't go too low when low hp
            if my_hp <= 3:
                bid = max(bid, DAILY_SALARY * 0.35)
            return clamp_bid(bid)
        # If they were moderate, bid just above their likely clearing price.
        if highest_prev_bid >= DAILY_SALARY * 0.45:
            bid = highest_prev_bid + 2.0
            bid = min(bid, DAILY_SALARY * 0.7)
            return clamp_bid(bid)

    # No useful history: bid based on supply pressure and our health.
    # Higher supply -> we can bid a bit less; lower supply -> bid more.
    # supply is between MIN_SUPPLY and MAX_SUPPLY.
    if supply <= float(MIN_SUPPLY) + 0.5:
        factor = 0.85
    elif supply >= float(MAX_SUPPLY) - 0.5:
        factor = 0.6
    else:
        # linear-ish interpolation
        factor = 0.6 + 0.25 * ((supply - float(MIN_SUPPLY)) / (float(MAX_SUPPLY) - float(MIN_SUPPLY)))

    bid = base_need * factor

    # If we have no-water days, increase urgency.
    no_water_days = int(my_status.get('no_water_days', 0) or 0)
    if no_water_days >= 2:
        bid = max(bid, DAILY_SALARY * 0.75)
    elif no_water_days >= 1:
        bid = max(bid, DAILY_SALARY * 0.62)

    # Final clamp
    return clamp_bid(bid)
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

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive.append((opp_id, opp))

    if not alive:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids to infer who is applying max pressure.
    prev_bids = []
    for opp_id, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # If someone was bidding far above typical salary, treat as a pressure leader.
    pressure_leader = False
    if prev_bids:
        highest_prev_bid = max(prev_bids)
        if highest_prev_bid >= 1.2 * DAILY_SALARY:  # ~108+
            pressure_leader = True

    # Base bid: aim to secure enough water without fully matching pressure.
    # Convert supply to an approximate fraction of a day's requirement.
    # If supply is low, we bid higher.
    supply_ratio = 0.0
    if WATER_REQ > 0:
        supply_ratio = supply / float(WATER_REQ)

    # Ensure indices are int when using any lists.
    # (No lists used for indexing, but keep safe.)

    # Risk adjustment: if we've already gone without water, bid more aggressively.
    if no_water_days >= 2 or hp <= 2:
        urgency = 1.0
    elif no_water_days == 1 or hp <= 4:
        urgency = 0.7
    else:
        urgency = 0.45

    # Aggressiveness vs Cindy-like pressure.
    if pressure_leader:
        # Do not chase; bid enough to avoid being starved, but conserve budget.
        target = DAILY_SALARY * (0.35 + 0.35 * urgency)
    else:
        target = DAILY_SALARY * (0.55 + 0.35 * urgency)

    # Scale with supply: lower supply => higher bid.
    # supply range is [15,25], map to multiplier [1.15,0.85]
    if MAX_SUPPLY > MIN_SUPPLY:
        t = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
        if t < 0.0:
            t = 0.0
        if t > 1.0:
            t = 1.0
    else:
        t = 0.5
    supply_mult = 1.15 - 0.30 * t

    bid = target * supply_mult

    # Never exceed budget; never negative.
    bid = max(0.0, min(budget, bid))

    # If budget is very low, still try to bid something proportional.
    if budget <= DAILY_SALARY * 0.15:
        bid = min(bid, budget)

    # Small day-based variation to reduce predictability.
    # Keep deterministic-ish but not too large.
    if day % 3 == 0:
        bid *= 1.03
    elif day % 3 == 1:
        bid *= 0.98

    bid = max(0.0, min(budget, bid))
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
    day = int(day_context.get('day', 0))

    my_hp = int(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids for immediate reaction
    prev_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    prev_bids.append(float(b))
                except Exception:
                    pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0

    # Estimate how many water units are likely needed today
    # supply is 15..25, so with WATER_REQ=9, we assume 1 or 2 units matter.
    # If supply is high, we can bid less and still get water.
    # If supply is low, we bid more.
    if supply <= (MIN_SUPPLY + 0.5):
        scarcity_factor = 1.0
    elif supply >= (MAX_SUPPLY - 0.5):
        scarcity_factor = 0.75
    else:
        scarcity_factor = 0.9

    # Identify most threatening opponent from yesterday: highest bid and/or low hp
    threat_score = []
    for opp_id, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        prev_bid = prev.get('bid', 0.0)
        opp_hp = int(opp.get('hp', 10))
        try:
            prev_bid_f = float(prev_bid)
        except Exception:
            prev_bid_f = 0.0
        # low hp => likely to fight for water; high prev bid => likely to spend
        score = prev_bid_f + (10 - opp_hp) * 2.5
        threat_score.append((score, opp_id, prev_bid_f, opp_hp))

    threat_score.sort(reverse=True)
    top_threat = threat_score[0] if threat_score else (0.0, None, 0.0, 10)
    top_prev_bid = float(top_threat[2])

    # Base bid policy: aim around salary * 0.55, adjust by scarcity and our hp
    # If our hp is low or we've had no water, increase bid.
    if my_hp <= 2 or my_no_water_days >= 2:
        base = DAILY_SALARY * 0.85
    elif my_hp <= 4:
        base = DAILY_SALARY * 0.70
    else:
        base = DAILY_SALARY * 0.55

    # If opponents previously bid very high, slightly outbid but avoid overpaying.
    # This exploits that Cindy often has low hp but limited max bid; we don't need to match Eric's extremes.
    # Use a cap tied to highest_prev_bid.
    if highest_prev_bid >= DAILY_SALARY * 1.2:
        # Eric-like pressure: bid around 0.65 salary, scaled
        base = max(base, DAILY_SALARY * 0.65)

    # If top threat bid is moderate, we can bid just above it.
    target = base * scarcity_factor

    # Small reaction from yesterday's top threat bid
    if top_prev_bid > 0:
        # Bid to beat by a small margin when supply is scarce
        margin = 2.0 if scarcity_factor >= 0.9 else 1.0
        target = max(target, top_prev_bid + margin)

    # Final safety cap: never exceed what we can pay and avoid absurd spending
    # Cap at 1.1 * highest_prev_bid if that exists, else 0.95 salary.
    cap = my_budget
    if highest_prev_bid > 0:
        cap = min(cap, highest_prev_bid * 1.1)
    cap = min(cap, DAILY_SALARY * 1.0)

    bid = min(max(0.0, target), cap)
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
    day = int(day_context['day'])

    # Identify alive opponents and read their immediate yesterday bid
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    # If no opponents alive, conserve water
    if not alive_opps:
        conservative = DAILY_SALARY * 0.4
        return float(min(my_status['budget'], conservative))

    # Extract yesterday bids from previous_trace only
    yesterday_bids = []
    highest_prev_bid = None
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', None) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                b_val = float(b)
                yesterday_bids.append(b_val)
            except Exception:
                pass
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)

    # Determine how tight the supply is for us
    # Need at least WATER_REQ water to avoid no-water penalty.
    # If supply is barely above WATER_REQ, we must secure allocation.
    tight_supply = supply <= (WATER_REQ + 2)  # 11 or 12 only in this meta-range

    hp = int(my_status['hp'])
    budget = float(my_status['budget'])

    # Target bid heuristic:
    # - If we are low hp or supply is tight, bid more.
    # - Otherwise bid moderately to beat low-pressure bidders.
    # Use yesterday's highest bid as an upper anchor.
    base = DAILY_SALARY * 0.65
    if hp <= 2:
        base = DAILY_SALARY * 0.85
    elif hp <= 3:
        base = DAILY_SALARY * 0.75

    # If tight supply, add a bump
    if tight_supply:
        base *= 1.15

    # If there was a very high bid yesterday, we may need to match/beat it slightly
    if highest_prev_bid is not None:
        # If highest previous bid was already strong, ensure we slightly exceed it when needed.
        if hp <= 3 or tight_supply:
            target = max(base, highest_prev_bid + 2.0)
        else:
            # Otherwise, don't chase too hard; just ensure competitiveness.
            target = max(base, min(highest_prev_bid + 0.5, DAILY_SALARY * 0.8))
    else:
        target = base

    # Never exceed our budget; also keep within a reasonable fraction of max bid
    # to avoid bankruptcy.
    max_reasonable = budget
    if budget <= 0:
        return 0.0

    # If we have ample budget, still cap at 0.95*budget to reduce risk of overspending
    cap = min(max_reasonable, DAILY_SALARY * 1.1, budget * 0.95)
    bid = float(min(target, cap))

    # Ensure bid is non-negative
    if bid < 0:
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

    # Basic safety
    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    supply = float(day_context.get('supply', 0))
    day = int(day_context.get('day', 0))

    # Alive opponents only; use only their previous_trace for immediate reaction
    alive_opponents = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    # If no one alive, conserve
    if not alive_opponents:
        return max(0.0, min(budget, DAILY_SALARY * 0.35))

    # Extract yesterday bids from previous_trace
    prev_bids = []
    prev_hp_after = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass
        # Track who was under pressure yesterday (hp_after low implies losing water)
        try:
            prev_hp_after.append(float(prev.get('hp_after', 999)))
        except Exception:
            prev_hp_after.append(999)

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    # If someone bid high yesterday, they likely needed water; match slightly below/around it.

    # Pressure estimate: if many alive opponents had low hp_after, competition may be high today too.
    pressure_count = 0
    for hpa in prev_hp_after:
        if hpa <= 3:
            pressure_count += 1
    pressure_factor = 1.0 + 0.12 * min(3, pressure_count)

    # Supply scaling: with higher supply, can bid a bit less; with lower supply, bid more.
    # Normalize supply within [MIN_SUPPLY, MAX_SUPPLY]
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_norm = 0.5
    supply_norm = max(0.0, min(1.0, supply_norm))
    # bid_multiplier: lower supply => higher multiplier
    bid_multiplier = 1.15 - 0.25 * supply_norm

    # Base target bid near strong players' effective bids (~0.85*highest_prev_bid or ~0.6*DAILY_SALARY)
    # Use my hp/no_water_days to decide whether to overbid.
    if hp <= 2 or no_water_days >= 2:
        # Critical: secure water
        target = max(DAILY_SALARY * 0.75, highest_prev_bid * 0.95)
    elif hp <= 4:
        target = max(DAILY_SALARY * 0.65, highest_prev_bid * 0.85)
    else:
        # Comfortable: bid to stay competitive but conserve budget
        target = max(DAILY_SALARY * 0.55, highest_prev_bid * 0.78)

    # Adjust for competition pressure and supply
    target = target * pressure_factor * bid_multiplier

    # Hard caps to avoid overspending
    # If budget is low, bid proportionally to remaining days of survival risk
    # (We don't know exact survival model; use no_water_days as a proxy.)
    if budget <= 0:
        return 0.0

    # Ensure we don't exceed budget and keep within a reasonable fraction of daily salary
    max_reasonable = min(budget, DAILY_SALARY * (0.98 if hp <= 4 else 0.75))
    bid = min(max_reasonable, target)

    # If bid is extremely low relative to what strong players bid yesterday, bump slightly
    if highest_prev_bid > 0 and bid < highest_prev_bid * 0.6 and hp > 2:
        bid = min(max_reasonable, highest_prev_bid * 0.75)

    # Final clamp
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    if not alive:
        return min(my_budget, DAILY_SALARY * 0.4)

    # Extract yesterday bids for immediate reaction
    yesterday_bids = []
    highest_prev_bid = 0.0
    for oid, o in alive:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                b = float(b)
                yesterday_bids.append(b)
                if b > highest_prev_bid:
                    highest_prev_bid = b
            except Exception:
                pass

    # Baseline bid based on my urgency
    if my_hp <= 2 or my_no_water_days >= 2:
        base = DAILY_SALARY * 0.95
    elif my_hp <= 3 or my_no_water_days == 1:
        base = DAILY_SALARY * 0.75
    else:
        base = DAILY_SALARY * 0.55

    # If someone was strongly pressuring yesterday, undercut slightly
    # Cindy's behavior suggests a ceiling; we try to beat everyone except the top bidder.
    # Use a small margin to avoid overpaying.
    if highest_prev_bid > 0:
        # Convert supply to a rough need factor: more supply => lower bid pressure
        # Use explicit int for any indexing-like operations (none here), but keep safe math.
        need_factor = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
        need_factor = max(0.0, min(1.0, need_factor))

        # Target slightly below the highest previous bid if I'm not in critical HP.
        # If I'm critical, prioritize securing water.
        if my_hp > 3:
            target = min(my_budget, max(base, highest_prev_bid * 0.93 - 2.0))
        else:
            target = min(my_budget, max(base, highest_prev_bid * 0.98 + 1.0))

        # Clamp to reasonable range relative to supply and my budget
        # Higher supply reduces need; lower supply increases it.
        supply_pressure = 0.35 + 0.65 * need_factor
        target = min(target, my_budget, DAILY_SALARY * (0.35 + 0.9 * supply_pressure))
        return max(0.0, target)

    # Fallback if no usable yesterday bids
    if my_hp <= 2:
        return min(my_budget, DAILY_SALARY * 0.9)
    return min(my_budget, base)
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

    hp = float(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Determine alive opponents and read yesterday bids
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    # If no opponents are alive, bid conservatively
    if not alive_opps:
        cap = min(budget, DAILY_SALARY * 0.4)
        return max(0.0, cap)

    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # If we can infer competitive pressure from yesterday
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / float(len(yesterday_bids))
    else:
        highest_prev_bid = 0.0
        avg_prev_bid = 0.0

    # Base target: aim around the upper-middle of yesterday bids without matching the absolute max
    # Cindy avg ~129.8, David avg ~97.6; choose a level that should win against most but save budget.
    # Adjust for our urgency.
    urgency = 0
    if hp <= 2:
        urgency = 2
    elif hp <= 4:
        urgency = 1
    if no_water_days >= 2:
        urgency = max(urgency, 1)

    # Supply pressure: higher supply reduces need to overbid.
    # Convert supply to a 0..1 scale
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_scale = (supply - float(MIN_SUPPLY)) / float(MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_scale = 0.5
    supply_scale = max(0.0, min(1.0, supply_scale))

    # Start from a competitive anchor derived from yesterday
    # If highest bid was very high, we slightly undercut it; otherwise anchor to avg.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        anchor = highest_prev_bid * (0.92 - 0.04 * supply_scale)
    else:
        anchor = max(avg_prev_bid, DAILY_SALARY * 0.55) * (0.92 - 0.06 * supply_scale)

    # Urgency pushes bid upward
    bid = anchor
    if urgency == 2:
        bid = max(bid, DAILY_SALARY * 0.85)
    elif urgency == 1:
        bid = max(bid, DAILY_SALARY * 0.65)

    # If we are likely to lose (budget low), cap aggressively
    # Ensure bid never exceeds budget
    bid = min(bid, budget)

    # Also keep within a reasonable upper bound to avoid bankruptcy
    # (since this game likely uses salary as a natural scale)
    bid_cap = min(budget, DAILY_SALARY * 1.2)
    bid = min(bid, bid_cap)

    # If budget is extremely small, just bid what we can
    if budget <= 1e-6:
        return 0.0

    # Final safeguard: bid at least 0
    return max(0.0, float(bid))
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

    alive_opps = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opps:
        return min(my_status['budget'], DAILY_SALARY * 0.4)

    # Read yesterday bids from previous_trace only (immediate reaction)
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', None) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Estimate how competitive the field was yesterday
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Base target bid depends on supply pressure
    # If supply is high, we can bid less and still likely get enough; if low, bid more.
    supply_ratio = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Convert supply into rough expected water units we might secure.
    # We don't know opponent bids, so this is only a heuristic for aggressiveness.
    # Lower supply => higher aggressiveness.
    aggressiveness = 0.65 + (1.0 - supply_ratio) * 0.35

    # If yesterday competition was bidding very high, raise our bid to avoid losing the water.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        aggressiveness = min(1.0, aggressiveness + 0.15)

    # If our HP is low, we must prioritize survival.
    hp = float(my_status.get('hp', 0.0))
    if hp <= 2:
        aggressiveness = 1.0
    elif hp <= 4:
        aggressiveness = max(aggressiveness, 0.85)

    # Translate aggressiveness into a bid cap.
    # Keep within budget and avoid extreme overbidding.
    target = DAILY_SALARY * aggressiveness

    # Extra nudge: if supply is very low, bid closer to daily salary.
    if supply <= (MIN_SUPPLY + 1.0):
        target = max(target, DAILY_SALARY * 0.85)

    # Extra nudge: if supply is high, bid more conservatively.
    if supply >= (MAX_SUPPLY - 1.0):
        target = min(target, DAILY_SALARY * 0.7)

    # Ensure we can pay; also avoid bidding more than budget.
    bid = min(float(my_status['budget']), float(target))

    # If budget is tiny, bid whatever we can.
    if bid < 1.0:
        bid = min(float(my_status['budget']), DAILY_SALARY * 0.2)

    return float(max(0.0, bid))
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

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive.append((oid, o))

    if not alive:
        cap = DAILY_SALARY * 0.4
        return float(min(budget, cap))

    # Extract yesterday bids from previous_trace for immediate reaction
    prev_bids = []
    prev_by_id = {}
    for oid, o in alive:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                b = float(b)
                prev_bids.append(b)
                prev_by_id[oid] = b
            except Exception:
                pass

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    # Tight supply => more competition for water; use opponents' pressure to decide
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY + 1e-9)  # 0..1
    tightness = 1.0 - max(0.0, min(1.0, supply_ratio))

    # If our hp is low, prioritize survival; if our hp is high, shade to save budget
    low_hp = hp <= 2
    critical = hp <= 3 or no_water_days >= 1

    # Determine target bid based on yesterday's max pressure
    # If someone previously bid very high (Cindy-like), we don't need to match unless tight+critical.
    pressure_threshold = DAILY_SALARY * 1.5  # 135

    # Base aggressiveness from tightness and hp
    if critical:
        base = DAILY_SALARY * (0.65 + 0.25 * tightness)
    elif low_hp:
        base = DAILY_SALARY * 0.95
    else:
        base = DAILY_SALARY * (0.45 + 0.25 * tightness)

    # React to observed pressure
    if highest_prev_bid >= pressure_threshold:
        # Overpayers exist; shade unless we are critical and supply is tight.
        if critical and tightness >= 0.6:
            target = max(base, highest_prev_bid * 0.72)
        else:
            target = min(base, avg_prev_bid * 0.75 if avg_prev_bid > 0 else base)
    else:
        # No extreme overbids: bid around base, slightly above average pressure if needed.
        if tightness >= 0.7 and highest_prev_bid > 0:
            target = max(base, highest_prev_bid * 0.6)
        else:
            target = base

    # Convert to a practical cap: cannot exceed budget.
    # Also avoid wasting too much when not critical.
    if critical:
        budget_cap = DAILY_SALARY * 1.2
    else:
        budget_cap = DAILY_SALARY * 0.9

    bid = float(min(budget, budget_cap, target))

    # Ensure non-negative and at least a minimal bid if we can afford it.
    if bid < 0.0:
        bid = 0.0

    # If we are extremely likely to lose (hp low), bump to ensure water.
    # Use supply to estimate how many water units might be needed: more tightness => higher chance.
    if critical and supply <= (MIN_SUPPLY + WATER_REQ):
        # bump modestly
        bid = float(min(budget, max(bid, DAILY_SALARY * (0.75 + 0.1 * tightness))))

    return bid
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

    alive_opps = [o for o in opponents_status.values() if o.get('alive', False)]

    # If no one is alive, conserve budget.
    if not alive_opps:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.35))

    # Read yesterday bids to infer pressure.
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Supply-based aggressiveness: when supply is low, need to outbid to ensure water.
    # supply in [15,25] => ratio in [0,1]
    supply_ratio = 0.0
    try:
        supply_ratio = (float(supply) - float(MIN_SUPPLY)) / (float(MAX_SUPPLY) - float(MIN_SUPPLY))
    except Exception:
        supply_ratio = 0.0
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Base bid: moderate when supply is plentiful, higher when scarce.
    # At supply=15 => ~0.65*DAILY_SALARY, at supply=25 => ~0.45*DAILY_SALARY
    base = DAILY_SALARY * (0.65 - 0.20 * supply_ratio)

    # React to yesterday's highest pressure.
    # If someone already bid very high, we must compete; if not, we can shade down.
    if highest_prev_bid >= DAILY_SALARY * 1.15:  # ~103.5
        pressure_multiplier = 1.10
    elif highest_prev_bid >= DAILY_SALARY * 0.85:  # ~76.5
        pressure_multiplier = 1.00
    else:
        pressure_multiplier = 0.90

    # If I'm low hp, increase bid to avoid death.
    if my_status['hp'] <= 2:
        hp_multiplier = 1.25
    elif my_status['hp'] <= 4:
        hp_multiplier = 1.10
    else:
        hp_multiplier = 1.00

    # If I'm already accumulating no-water days, bid more.
    no_water_days = my_status.get('no_water_days', 0)
    if no_water_days >= 3:
        nwd_multiplier = 1.20
    elif no_water_days >= 1:
        nwd_multiplier = 1.05
    else:
        nwd_multiplier = 1.00

    target = base * pressure_multiplier * hp_multiplier * nwd_multiplier

    # Ensure we do not exceed budget; also keep some budget for later days.
    # Use a conservative cap: spend up to 70% of budget today.
    cap = my_status['budget'] * 0.70
    bid = min(target, cap, my_status['budget'])

    # Never bid negative.
    if bid < 0:
        bid = 0.0

    return float(bid)
"""
