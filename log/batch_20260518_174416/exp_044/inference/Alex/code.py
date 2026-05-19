# ============================================================
# Experiment: exp_044
# Agent: Alex
# Source: exp_044
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = day_context['supply']
    my_hp = my_status['hp']
    my_budget = my_status['budget']
    my_no_water = my_status['no_water_days']

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)

    if my_budget <= 0:
        return 0

    player_count = 1 + len(alive)
    likely_winners = max(1, int(supply // WATER_REQ))
    scarcity = player_count - likely_winners

    opp_prev_bids = []
    desperate_opp = 0
    rich_opp = 0
    for opp in alive:
        if opp.get('budget', 0) > my_budget:
            rich_opp += 1
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
            desperate_opp += 1
        prev = opp.get('previous_trace', {}) or {}
        bid = prev.get('bid')
        err = prev.get('error')
        status = prev.get('status')
        if bid is not None and err in (None, '', False):
            try:
                b = float(bid)
                if b >= 0:
                    opp_prev_bids.append(b)
            except Exception:
                pass
        if status == 'failed' or status == 'error':
            desperate_opp += 1

    highest_prev = max(opp_prev_bids) if opp_prev_bids else 0.0
    avg_prev = (sum(opp_prev_bids) / len(opp_prev_bids)) if opp_prev_bids else 0.0

    urgent = (my_hp <= 2) or (my_no_water >= 1)
    very_urgent = (my_hp <= 1) or (my_no_water >= 2)

    if not alive:
        if urgent:
            return min(my_budget, 35)
        return min(my_budget, 18)

    if likely_winners >= player_count:
        base = 12
        if urgent:
            base = 22
        if highest_prev > 0:
            base = max(base, min(26, highest_prev * 0.6))
        return min(my_budget, max(0, base))

    if very_urgent:
        bid = max(58, highest_prev + 4)
        return min(my_budget, bid)

    if urgent:
        bid = max(46, highest_prev + 2)
        if scarcity >= 2:
            bid = max(bid, 54)
        return min(my_budget, bid)

    if scarcity >= 3:
        bid = max(44, highest_prev + 1.5)
        if rich_opp >= 2:
            bid += 4
        return min(my_budget, bid)

    if scarcity == 2:
        bid = max(36, avg_prev + 3, highest_prev + 1)
        if desperate_opp >= 2:
            bid += 3
        return min(my_budget, bid)

    bid = max(28, avg_prev + 2)
    if highest_prev >= 50:
        bid = 24
    return min(my_budget, bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if budget <= 0:
        return 0.0

    if not alive:
        base = DAILY_SALARY * 0.22
        if hp <= 2 or no_water >= 1:
            base = DAILY_SALARY * 0.55
        return float(max(0.0, min(budget, base)))

    highest_prev = 0.0
    bob_prev = 0.0
    urgent_opp = 0
    rich_opp = 0
    for oid, opp in alive:
        if opp.get('budget', 0) >= DAILY_SALARY:
            rich_opp += 1
        if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1
        prev = opp.get('previous_trace') or {}
        bid = prev.get('bid')
        if isinstance(bid, (int, float)):
            if bid > highest_prev:
                highest_prev = float(bid)
            if oid == 'Bob':
                bob_prev = float(bid)

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    base = DAILY_SALARY * (0.28 + 0.22 * scarcity)

    if highest_prev > 0:
        if hp >= 7 and no_water == 0 and supply >= 20:
            target = max(base, highest_prev * 0.58)
        elif hp >= 5 and no_water == 0:
            target = max(base, highest_prev * 0.72)
        else:
            target = max(base, highest_prev * 0.92 + 1.0)
    else:
        target = base

    if bob_prev >= DAILY_SALARY * 1.5 and hp >= 6 and no_water == 0:
        target = min(target, bob_prev * 0.62)

    if urgent_opp >= 2 and hp >= 6 and no_water == 0:
        target *= 0.92

    if rich_opp == 1 and hp <= 4:
        target = max(target, DAILY_SALARY * 0.9)

    if hp <= 2:
        target = max(target, DAILY_SALARY * (0.95 + 0.15 * scarcity))
    elif hp <= 4 or no_water >= 1:
        target = max(target, DAILY_SALARY * (0.78 + 0.12 * scarcity))

    if supply >= 23 and hp >= 6 and no_water == 0:
        target *= 0.88
    elif supply <= 17:
        target *= 1.08

    if day >= 8:
        if hp >= 6 and no_water == 0:
            target *= 0.95
        else:
            target *= 1.05

    min_survival = 0.0
    if hp <= 2:
        min_survival = DAILY_SALARY * 0.9
    elif hp <= 4 or no_water >= 1:
        min_survival = DAILY_SALARY * 0.72

    bid = max(target, min_survival)
    bid = min(budget, bid)
    if budget < DAILY_SALARY * 0.35 and hp >= 5 and no_water == 0:
        bid = min(bid, budget * 0.7)

    if bid < 0:
        bid = 0.0
    return float(round(bid, 2))
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if not alive:
        return float(min(budget, DAILY_SALARY * 0.35))

    prev_bids = []
    rich_pressure = 0
    desperate_opp = 0
    for oid, opp in alive:
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(float(bid))
            if float(bid) >= 110:
                rich_pressure += 1
        if opp.get('no_water_days', 0) >= 2 or opp.get('hp', 10) <= 2:
            desperate_opp += 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    low_supply = supply <= 17
    high_supply = supply >= 22

    critical = (no_water >= 2) or (hp <= 2)
    urgent = (no_water >= 1 and hp <= 4) or (hp <= 3)

    if critical:
        bid = max(118.0, highest_prev + 4.0, DAILY_SALARY * 1.55)
        return float(min(budget, bid))

    if urgent:
        if low_supply:
            bid = max(102.0, highest_prev + 2.5, avg_prev + 8.0)
        else:
            bid = max(88.0, avg_prev + 5.0)
        return float(min(budget, bid))

    if high_supply and rich_pressure >= 2:
        return float(min(budget, DAILY_SALARY * 0.22))

    if low_supply:
        if rich_pressure >= 2:
            bid = max(74.0, avg_prev * 0.72)
        else:
            bid = max(79.0, highest_prev + 1.5, avg_prev + 4.0)
    else:
        if desperate_opp >= 2:
            bid = max(42.0, avg_prev * 0.55)
        elif highest_prev >= 120:
            bid = 36.0
        elif highest_prev >= 90:
            bid = 48.0
        else:
            bid = max(44.0, avg_prev * 0.7, DAILY_SALARY * 0.58)

    if day >= 8 and hp >= 5 and no_water == 0:
        bid *= 0.9

    return float(min(budget, max(0.0, bid)))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive_opponents = []
    for agent_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if not alive_opponents:
        return max(0.0, min(budget, 20.0))

    prev_bids = []
    active_threats = 0
    max_prev_bid = 0.0
    min_opp_req = WATER_REQ
    for opp in alive_opponents:
        req = opp.get('water_requirement', WATER_REQ)
        if req < min_opp_req:
            min_opp_req = req
        prev = opp.get('previous_trace', {})
        bid = None
        if prev:
            bid = prev.get('bid')
        if bid is not None:
            prev_bids.append(bid)
            if bid > max_prev_bid:
                max_prev_bid = bid
            if bid >= 80:
                active_threats += 1

    total_demand_units = WATER_REQ
    for opp in alive_opponents:
        total_demand_units += opp.get('water_requirement', WATER_REQ)

    tight_supply = supply <= total_demand_units * 0.55
    medium_tight = supply <= total_demand_units * 0.7

    emergency = hp <= 3 or no_water >= 1
    severe_emergency = hp <= 2 or no_water >= 2

    if severe_emergency:
        target = max(100.0, max_prev_bid + 2.0)
        if supply <= WATER_REQ:
            target = max(target, 112.0)
        return max(0.0, min(budget, target))

    if emergency:
        target = 92.0
        if max_prev_bid >= 98:
            target = max(target, max_prev_bid + 1.0)
        if tight_supply:
            target += 8.0
        return max(0.0, min(budget, target))

    if tight_supply:
        if active_threats >= 2:
            target = 99.5
        elif max_prev_bid > 0:
            target = max(72.0, max_prev_bid + 1.0)
        else:
            target = 75.0
        if budget < 250:
            target -= 10.0
        return max(0.0, min(budget, target))

    if medium_tight:
        target = 61.0
        if max_prev_bid >= 98:
            target = 68.0
        if day >= 8 and hp >= 5:
            target -= 6.0
        return max(0.0, min(budget, target))

    target = 34.0
    if max_prev_bid < 50 and max_prev_bid > 0:
        target = max(34.0, max_prev_bid + 1.0)
    if day >= 8:
        target = 28.0
    return max(0.0, min(budget, target))
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opps = []
    prev_bids = []
    aggressive_bids = []
    urgent_opps = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opps += 1
            prev = opp.get('previous_trace', {})
            if prev:
                bid = prev.get('bid')
                if bid is not None:
                    prev_bids.append(float(bid))
                    if float(bid) >= 100:
                        aggressive_bids.append(float(bid))

    if budget <= 0:
        return 0.0

    winner_slots = int(max(1, supply // WATER_REQ))
    scarcity = winner_slots <= 1

    if not alive_opps:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    second_prev = 0.0
    if len(prev_bids) >= 2:
        second_prev = sorted(prev_bids)[-2]

    my_urgent = hp <= 3 or no_water_days >= 1

    if my_urgent:
        target = highest_prev + 3.0 if highest_prev > 0 else 95.0
        if scarcity:
            target += 8.0
        return float(max(0.0, min(budget, target)))

    if scarcity:
        if highest_prev >= 135:
            bid = 38.0 if hp >= 7 and no_water_days == 0 else 112.0
        elif highest_prev >= 115:
            bid = highest_prev + 2.5
        elif highest_prev >= 90:
            bid = highest_prev + 4.0
        else:
            bid = 82.0

        if urgent_opps >= 2:
            bid += 6.0
        if hp >= 8 and no_water_days == 0 and budget < 250:
            bid *= 0.82
        return float(max(0.0, min(budget, bid)))

    bid = 46.0
    if highest_prev >= 120:
        bid = 72.0
    elif highest_prev >= 100:
        bid = 64.0
    elif highest_prev >= 70:
        bid = highest_prev * 0.78

    if urgent_opps >= 2:
        bid += 8.0
    if hp <= 5:
        bid += 10.0
    if no_water_days >= 1:
        bid += 14.0

    reserve_floor = 70.0 if hp >= 6 else 0.0
    bid = min(bid, max(0.0, budget - reserve_floor)) if budget > reserve_floor else min(budget, bid)
    return float(max(0.0, min(budget, bid)))
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opps = []
    prev_bids = []
    urgent_opp_count = 0
    rich_opp_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            if opp.get('budget', 0) >= 120:
                rich_opp_count += 1
            if opp.get('hp', 10) <= 4 or opp.get('no_water_days', 0) >= 1:
                urgent_opp_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if budget <= 0:
        return 0

    if not alive_opps:
        return min(budget, 18.0)

    capacity = float(supply) / float(WATER_REQ)
    scarcity = max(0.0, len(alive_opps) + 1 - capacity)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    emergency = hp <= 3 or no_water_days >= 1
    critical = hp <= 2 or no_water_days >= 2

    if critical:
        bid = max(92.0, highest_prev + 3.0)
        if supply <= 17:
            bid = max(bid, 108.0)
        return min(budget, bid)

    if emergency:
        bid = max(74.0, avg_prev + 2.0)
        if highest_prev >= 120:
            bid = 86.0
        if supply <= 17:
            bid += 10.0
        return min(budget, bid)

    if supply >= 22:
        bid = 18.0
    elif supply >= 20:
        bid = 28.0
    elif supply >= 18:
        bid = 42.0
    else:
        bid = 58.0

    if scarcity > 2.5:
        bid += 12.0
    elif scarcity > 1.5:
        bid += 7.0
    elif scarcity > 0.5:
        bid += 3.0

    if urgent_opp_count >= 2:
        bid += 6.0
    elif urgent_opp_count == 1:
        bid += 3.0

    if highest_prev >= 125:
        bid = min(bid, 62.0)
    elif highest_prev >= 100:
        bid = min(bid, 68.0)
    elif highest_prev > 0 and supply <= 17:
        bid = max(bid, min(highest_prev + 1.5, 88.0))
    elif highest_prev > 0 and supply <= 19:
        bid = max(bid, min(avg_prev * 0.72, 64.0))

    if rich_opp_count >= 3 and supply <= 17:
        bid += 8.0

    if day >= 8 and hp >= 6 and budget > 180:
        bid += 6.0

    reserve_floor = 25.0 if day < 8 else 10.0
    bid = min(bid, max(0.0, budget - reserve_floor))
    bid = max(0.0, bid)
    return min(budget, bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = {}
    for k, v in opponents_status.items():
        if v.get('alive'):
            alive[k] = v

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0 if hp > 3 else 35.0))

    bob = opponents_status.get('Bob', None)
    cindy = opponents_status.get('Cindy', None)

    bob_prev_bid = None
    bob_pressure = 0.0
    if bob and bob.get('alive'):
        prev = bob.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            bob_prev_bid = prev.get('bid')
            bob_pressure = bob_prev_bid
        else:
            bob_pressure = 75.0

    cindy_prev_bid = None
    if cindy and cindy.get('alive'):
        prev = cindy.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            cindy_prev_bid = prev.get('bid')

    alive_count = len(alive)

    desperate = hp <= 2 or no_water >= 2
    pressured = hp <= 4 or no_water >= 1

    if desperate:
        target = 92.0
        if bob_pressure > 0:
            target = max(target, bob_pressure + 3.0)
        if cindy_prev_bid is not None and cindy_prev_bid < 120:
            target = max(target, cindy_prev_bid + 2.0)
        return float(min(budget, target))

    if pressured:
        target = 78.0
        if bob_pressure > 80:
            target = bob_pressure + 1.5
        elif bob_pressure > 0:
            target = max(76.0, bob_pressure + 0.5)
        if alive_count >= 3:
            target += 2.0
        return float(min(budget, target))

    if day <= 3:
        if cindy_prev_bid is not None and cindy_prev_bid >= 150:
            return float(min(budget, 48.0))
        if bob_pressure >= 80:
            return float(min(budget, 58.0))
        return float(min(budget, 62.0))

    if alive_count == 1 and bob and bob.get('alive'):
        if hp >= bob.get('hp', 0) and budget > bob.get('budget', 0):
            return float(min(budget, max(72.0, bob_pressure + 1.0 if bob_pressure else 72.0)))
        return float(min(budget, 68.0 if hp > 3 else 82.0))

    if bob_pressure >= 85:
        return float(min(budget, 50.0))
    if bob_pressure >= 75:
        return float(min(budget, 57.0))

    base = 54.0
    if alive_count >= 3:
        base = 59.0
    return float(min(budget, base))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opps = []
    prev_bids = []
    urgent_opp_count = 0
    rich_aggressive = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 2:
                urgent_opp_count += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(float(bid))
                if float(bid) >= 80 and opp.get('budget', 0) >= 200:
                    rich_aggressive += 1

    if not alive_opps:
        return float(min(budget, 18.0))

    slots = max(1, int(supply // WATER_REQ))
    tight_supply = slots <= 1

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    danger = 0
    if hp <= 2:
        danger += 3
    elif hp <= 4:
        danger += 2
    elif hp <= 6:
        danger += 1

    if no_water >= 2:
        danger += 3
    elif no_water >= 1:
        danger += 1

    if tight_supply:
        danger += 2
    if urgent_opp_count >= 2:
        danger += 1
    if day >= 8:
        danger += 1

    if danger >= 5:
        bid = max(78.0, highest_prev + 2.5)
    elif danger >= 3:
        bid = max(58.0, min(88.0, avg_prev * 0.78 + 6.0))
    else:
        if rich_aggressive >= 2 or highest_prev >= 90:
            bid = 16.0 if not tight_supply else 24.0
        elif highest_prev >= 70:
            bid = 22.0 if not tight_supply else 32.0
        else:
            bid = 28.0 if tight_supply else 18.0

    if budget < DAILY_SALARY * 0.8 and danger < 3:
        bid = min(bid, 24.0)

    if hp <= 2 or no_water >= 2:
        bid = max(bid, 84.0)

    if day == 10 and hp <= 4:
        bid = max(bid, 90.0)

    return float(max(0.0, min(budget, bid)))
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) > budget:
                rich_opp += 1
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opp += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(bid)

    if not alive_opponents:
        return min(budget, 18.0)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    tight_supply = supply <= 17
    ample_supply = supply >= 22

    if hp <= 2 or no_water_days >= 2:
        bid = DAILY_SALARY * 1.18
    elif hp <= 4 or no_water_days >= 1:
        if highest_prev >= 140:
            bid = DAILY_SALARY * 0.92
        else:
            bid = max(DAILY_SALARY * 0.82, highest_prev + 3.0)
    else:
        if ample_supply:
            bid = DAILY_SALARY * 0.22
        elif tight_supply:
            if highest_prev >= 140:
                bid = DAILY_SALARY * 0.38
            elif highest_prev >= 90:
                bid = min(DAILY_SALARY * 0.78, highest_prev + 2.0)
            else:
                bid = DAILY_SALARY * 0.48
        else:
            if highest_prev >= 140:
                bid = DAILY_SALARY * 0.30
            elif avg_prev >= 90:
                bid = DAILY_SALARY * 0.58
            else:
                bid = DAILY_SALARY * 0.40

    if urgent_opp >= 2 and hp >= 5 and no_water_days == 0:
        bid *= 0.9
    if rich_opp >= 2 and tight_supply and hp <= 4:
        bid *= 1.08

    if day >= 8 and hp >= 6 and no_water_days == 0:
        bid *= 0.92

    if budget < DAILY_SALARY:
        bid = min(bid, budget * 0.75)

    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget
    return float(bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive_opps = []
    prev_bids = []
    desperate_opp = False
    rich_opp = False
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opps.append(opp)
            if opp.get('budget', 0) > budget * 1.2:
                rich_opp = True
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 2:
                desperate_opp = True
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    prev_bids.append(float(prev.get('bid')))
                except Exception:
                    pass

    if budget <= 0:
        return 0.0

    if not alive_opps:
        return float(min(budget, 18.0 if hp > 4 else 45.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    supply_tight = supply <= 17.0
    supply_loose = supply >= 22.0
    critical = hp <= 2 or no_water >= 2
    urgent = hp <= 4 or no_water >= 1
    late_game = day >= 8

    if critical:
        bid = max(72.0, highest_prev + 3.0)
        if supply_tight:
            bid += 8.0
        return float(min(budget, bid))

    if urgent:
        if highest_prev >= 110.0:
            bid = 62.0 if not supply_tight else 78.0
        else:
            bid = max(52.0, min(88.0, highest_prev + 2.5))
        if desperate_opp and supply_tight:
            bid += 6.0
        return float(min(budget, bid))

    if supply_loose and hp >= 6 and no_water == 0:
        return float(min(budget, 12.0))

    if highest_prev >= 120.0:
        bid = 16.0 if hp >= 7 else 34.0
    elif highest_prev >= 90.0:
        bid = 22.0 if hp >= 7 else 40.0
    else:
        bid = max(24.0, min(60.0, avg_prev * 0.55 + 3.0))

    if supply_tight:
        bid += 8.0
    if rich_opp and not urgent:
        bid -= 4.0
    if late_game and hp <= 5:
        bid += 10.0

    reserve_floor = DAILY_SALARY * max(0, 10 - day)
    if budget > reserve_floor + 120:
        bid += 4.0

    bid = max(0.0, min(budget, bid))
    return float(bid)
"""
