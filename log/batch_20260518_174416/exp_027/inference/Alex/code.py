# ============================================================
# Experiment: exp_027
# Agent: Alex
# Source: exp_027
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive = []
    prev_bids = []
    needy_pressure = 0
    for opp in opponents_status.values():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 0) <= 2 or opp.get('no_water_days', 0) >= 1:
                needy_pressure += 1
            prev = opp.get('previous_trace', {}) or {}
            if prev.get('error'):
                continue
            bid = prev.get('bid')
            if bid is not None:
                prev_bids.append(bid)

    if budget <= 0:
        return 0

    if not alive:
        return min(budget, 18)

    avg_req = 0.0
    if len(alive) > 0:
        total_req = 0
        for opp in alive:
            total_req += opp.get('water_requirement', WATER_REQ)
        avg_req = total_req / float(len(alive))
    else:
        avg_req = WATER_REQ

    total_players_est = len(alive) + 1
    total_req_est = WATER_REQ + avg_req * len(alive)
    scarcity = total_req_est / max(float(supply), 1.0)

    if scarcity >= total_players_est:
        base = 58
    elif scarcity >= total_players_est * 0.8:
        base = 48
    elif scarcity >= total_players_est * 0.6:
        base = 38
    else:
        base = 26

    if hp <= 2:
        base += 26
    elif hp <= 4:
        base += 14

    if no_water_days >= 2:
        base += 22
    elif no_water_days >= 1:
        base += 10

    if supply >= 23:
        base -= 8
    elif supply <= 17:
        base += 8

    if prev_bids:
        highest_prev = max(prev_bids)
        avg_prev = sum(prev_bids) / float(len(prev_bids))
        if highest_prev >= 60:
            if hp > 4 and no_water_days == 0:
                base = min(base, 28)
            else:
                base = max(base, highest_prev + 2)
        else:
            target = max(avg_prev + 2, highest_prev + 1)
            base = max(base, target)

    if needy_pressure >= max(1, len(alive) // 2):
        base += 6

    remaining_days = max(1, 10 - int(day) + 1)
    soft_cap = budget / float(remaining_days)
    if hp <= 2 or no_water_days >= 2:
        cap = max(soft_cap * 1.8, 35)
    elif hp <= 4 or no_water_days >= 1:
        cap = max(soft_cap * 1.35, 28)
    else:
        cap = max(soft_cap * 1.05, 22)

    bid = min(base, cap, budget)

    if day >= 8 and hp <= 4:
        bid = min(budget, max(bid, 52))

    if bid < 0:
        bid = 0
    return float(round(bid, 2))
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    rich_aggressive = 0
    desperate_opp = 0

    for opp in opponents_status.values():
        if opp.get('alive'):
            alive_opponents.append(opp)
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if bid >= 80:
                    rich_aggressive += 1
            if opp.get('hp', 10) <= 2 or opp.get('no_water_days', 0) >= 1:
                desperate_opp += 1

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    if hp <= 2 or no_water_days >= 1:
        emergency = max(88.0, highest_prev + 2.0)
        if supply <= 16:
            emergency = max(emergency, 98.0)
        return float(min(budget, emergency))

    if supply >= 22:
        bid = 8.0 if rich_aggressive >= 1 else 14.0
    elif supply >= 19:
        bid = 14.0 if rich_aggressive >= 1 else 22.0
    else:
        bid = 24.0 if rich_aggressive >= 1 else 34.0

    if desperate_opp >= 2:
        bid += 8.0
    elif desperate_opp == 1:
        bid += 4.0

    if highest_prev < 40:
        bid = max(bid, highest_prev + 2.0)
    elif avg_prev < 60 and supply <= 18:
        bid += 6.0

    if hp >= 8 and budget < 250:
        bid *= 0.75
    elif hp >= 8 and rich_aggressive >= 2:
        bid *= 0.8

    bid = max(1.0, min(float(budget), bid))
    return float(bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    dangerous_prev = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                bid = prev['bid']
                prev_bids.append(bid)
                if bid >= 100:
                    dangerous_prev += 1

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    tight_supply = supply <= 17
    ample_supply = supply >= 22

    urgency = 0
    if hp <= 2:
        urgency += 4
    elif hp <= 4:
        urgency += 2
    if no_water >= 2:
        urgency += 4
    elif no_water >= 1:
        urgency += 2
    if tight_supply:
        urgency += 2
    elif ample_supply:
        urgency -= 1
    if day >= 8:
        urgency += 1

    if urgency >= 7:
        bid = max(92.0, highest_prev * 0.9)
    elif urgency >= 4:
        if highest_prev >= 120:
            bid = 72.0
        else:
            bid = max(48.0, avg_prev + 6.0)
    else:
        if dangerous_prev >= 2:
            bid = 16.0 if ample_supply else 24.0
        elif highest_prev >= 120:
            bid = 28.0
        elif highest_prev >= 80:
            bid = 36.0
        else:
            bid = max(22.0, avg_prev * 0.45 if avg_prev > 0 else 26.0)

    reserve = 0.0
    if hp > 4 and no_water == 0 and day <= 6:
        reserve = 20.0
    elif hp > 2 and day <= 8:
        reserve = 10.0

    max_affordable = max(0.0, budget - reserve)
    bid = min(bid, max_affordable)

    if urgency >= 7 and budget > 0:
        bid = max(bid, min(budget, 85.0))

    if bid < 0:
        bid = 0.0
    return float(min(budget, bid))
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
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

    if budget <= 0:
        return 0.0

    alive_opponents = []
    yesterday_bids = []
    rich_alive = 0
    extreme_bidders = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) >= 100:
                rich_alive += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                yesterday_bids.append(float(bid))
                if float(bid) >= 120:
                    extreme_bidders += 1

    if not alive_opponents:
        return float(min(budget, 18.0))

    highest_prev = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev = sum(yesterday_bids) / len(yesterday_bids) if yesterday_bids else 0.0

    urgency = 0
    if hp <= 2:
        urgency += 4
    elif hp <= 4:
        urgency += 2
    if no_water_days >= 2:
        urgency += 4
    elif no_water_days >= 1:
        urgency += 2

    abundance = (float(supply) - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY)
    if abundance >= 0.8:
        urgency += 1

    if supply <= 16:
        scarcity_level = 2
    elif supply <= 19:
        scarcity_level = 1
    else:
        scarcity_level = 0

    if urgency >= 6:
        bid = 146.0 if budget >= 146.0 else budget
    elif urgency >= 4:
        if scarcity_level == 2:
            bid = 132.0
        elif scarcity_level == 1:
            bid = 118.0
        else:
            bid = 96.0
    else:
        if extreme_bidders >= 2 and scarcity_level >= 1:
            bid = 8.0 if hp > 4 and no_water_days == 0 else 72.0
        elif highest_prev >= 140:
            if scarcity_level == 0:
                bid = 61.0
            else:
                bid = 12.0 if hp > 5 and no_water_days == 0 else 78.0
        elif avg_prev >= 90:
            bid = 68.0 if scarcity_level == 0 else 74.0
        else:
            bid = 52.0 + 10.0 * abundance

    if day >= 8:
        bid += 8.0
    if rich_alive == 0:
        bid *= 0.8

    if hp >= 8 and no_water_days == 0 and scarcity_level == 2 and extreme_bidders >= 1:
        bid = min(bid, 10.0)

    bid = max(0.0, min(float(budget), float(bid)))
    return float(round(bid, 2))
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

    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive_opponents = []
    prev_bids = []
    aggressive_prev = []
    weak_opp_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('budget', 0) <= DAILY_SALARY * 1.2 or opp.get('hp', 0) <= 3:
                weak_opp_count += 1
            prev = opp.get('previous_trace', {})
            bid = prev.get('bid') if prev else None
            if bid is not None:
                prev_bids.append(float(bid))
                if bid >= DAILY_SALARY * 0.9:
                    aggressive_prev.append(float(bid))

    if not alive_opponents:
        return float(min(budget, DAILY_SALARY * 0.25))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = (MAX_SUPPLY - supply) / float(MAX_SUPPLY - MIN_SUPPLY)
    if scarcity < 0:
        scarcity = 0.0
    if scarcity > 1:
        scarcity = 1.0

    urgency = 0.0
    if hp <= 2:
        urgency += 0.55
    elif hp <= 4:
        urgency += 0.3
    if no_water_days >= 2:
        urgency += 0.35
    elif no_water_days == 1:
        urgency += 0.18
    urgency += scarcity * 0.28
    if day >= 8:
        urgency += 0.08
    if urgency > 1.0:
        urgency = 1.0

    if hp <= 2 or no_water_days >= 2:
        bid = max(DAILY_SALARY * 0.95, highest_prev + 2.0)
    elif supply >= 22 and hp >= 7 and no_water_days == 0:
        bid = DAILY_SALARY * 0.22
    elif supply <= 17:
        if aggressive_prev:
            bid = min(highest_prev + 1.5, DAILY_SALARY * 1.15)
        else:
            bid = DAILY_SALARY * (0.58 + 0.18 * urgency)
    else:
        anchor = max(avg_prev + 1.0, DAILY_SALARY * (0.38 + 0.32 * urgency))
        if highest_prev >= 120 and hp > 4 and no_water_days == 0:
            anchor = min(anchor, DAILY_SALARY * 0.42)
        bid = anchor

    if weak_opp_count >= 2 and hp >= 5 and no_water_days == 0:
        bid *= 0.9

    reserve_floor = DAILY_SALARY * (2.2 if hp > 3 else 1.0)
    max_affordable = budget
    if budget > reserve_floor:
        max_affordable = max(0.0, budget - reserve_floor + DAILY_SALARY * 0.75)

    if hp <= 2 or no_water_days >= 2:
        max_affordable = budget

    bid = min(bid, max_affordable)
    bid = min(bid, budget)
    bid = max(0.0, bid)
    return float(round(bid, 2))
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

    supply = float(day_context['supply'])
    day = int(day_context['day'])
    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water = int(my_status['no_water_days'])

    if budget <= 0:
        return 0.0

    alive = []
    for oid, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append((oid, opp))

    if not alive:
        return min(budget, 18.0)

    capacity = supply / float(WATER_REQ)
    tight = capacity <= 1.45
    very_tight = capacity <= 1.15
    abundant = capacity >= 1.8

    max_prev_bid = 0.0
    cindy_prev = 0.0
    pressure = 0.0
    desperate_opp = 0
    rich_opp = 0

    for oid, opp in alive:
        prev = opp.get('previous_trace', {}) or {}
        pbid = prev.get('bid')
        if pbid is None:
            pbid = 0.0
        pbid = float(pbid)
        if pbid > max_prev_bid:
            max_prev_bid = pbid
        if oid == 'Cindy':
            cindy_prev = pbid
        if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
            desperate_opp += 1
        if opp.get('budget', 0) >= 700:
            rich_opp += 1
        pressure += pbid

    avg_pressure = pressure / max(1, len(alive))
    main_threat = max(cindy_prev, max_prev_bid)

    if hp <= 2 or no_water >= 2:
        bid = min(budget, max(88.0, main_threat + 6.0, budget * 0.92))
        return float(max(0.0, bid))

    if hp <= 4 or no_water >= 1:
        if very_tight:
            bid = max(78.0, main_threat + 3.0)
        elif tight:
            bid = max(64.0, avg_pressure + 6.0, cindy_prev + 2.0)
        else:
            bid = max(48.0, avg_pressure + 2.0)
        return float(min(budget, bid))

    if very_tight:
        if main_threat >= 120:
            bid = 44.0
        else:
            bid = max(58.0, min(96.0, cindy_prev + 1.5, main_threat + 1.5))
    elif tight:
        if cindy_prev >= 130:
            bid = 38.0
        else:
            bid = max(34.0, min(72.0, avg_pressure + 4.0, main_threat + 1.0))
    elif abundant:
        bid = 16.0 if desperate_opp == 0 else 22.0
    else:
        bid = 24.0 if rich_opp == 0 else 30.0

    if day >= 8 and hp >= 6:
        bid *= 0.9
    if desperate_opp >= 2 and hp >= 5:
        bid *= 0.9
    if budget < 140:
        bid = min(bid, max(22.0, budget * 0.55))

    bid = min(budget, bid)
    if bid < 0:
        bid = 0.0
    return float(bid)
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    day = day_context['day']
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive = []
    prev_bids = []
    aggressive_count = 0
    needy_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                needy_count += 1
            prev = opp.get('previous_trace', {})
            if prev:
                bid = prev.get('bid')
                if bid is not None:
                    prev_bids.append(bid)
                    if bid >= 100:
                        aggressive_count += 1

    if budget <= 0:
        return 0.0

    if not alive:
        return float(min(budget, 18.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / float(len(prev_bids))) if prev_bids else 0.0

    tight_supply = supply <= 17
    loose_supply = supply >= 22

    if hp <= 2 or no_water >= 2:
        emergency = max(95.0, highest_prev + 3.0)
        return float(min(budget, emergency))

    if hp <= 4 or no_water >= 1:
        if tight_supply:
            bid = max(88.0, highest_prev + 2.0)
        else:
            bid = max(72.0, avg_prev * 0.72 + 6.0)
        return float(min(budget, bid))

    if tight_supply:
        if aggressive_count >= 2:
            bid = max(18.0, avg_prev * 0.22)
        else:
            bid = max(42.0, highest_prev * 0.45)
    elif loose_supply:
        if aggressive_count >= 2:
            bid = 8.0
        else:
            bid = max(14.0, avg_prev * 0.18)
    else:
        if needy_count >= 2:
            bid = max(36.0, avg_prev * 0.35)
        elif aggressive_count >= 2:
            bid = 12.0
        else:
            bid = max(22.0, avg_prev * 0.24)

    if day >= 8 and hp >= 6 and no_water == 0:
        bid *= 0.8

    reserve_floor = 10.0 if day < 8 else 0.0
    bid = min(bid, max(0.0, budget - reserve_floor))
    bid = max(0.0, bid)
    return float(min(budget, bid))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 13
    DAILY_SALARY = 70
    supply = day_context['supply']
    day = day_context['day']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water_days = my_status['no_water_days']

    alive_opponents = []
    prev_bids = []
    desperate_count = 0
    rich_count = 0

    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)
            if opp.get('hp', 0) <= 3 or opp.get('no_water_days', 0) >= 1:
                desperate_count += 1
            if opp.get('budget', 0) >= 140:
                rich_count += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                prev_bids.append(prev.get('bid', 0))

    if not alive_opponents:
        return max(0.0, min(budget, DAILY_SALARY * 0.25))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    tight_supply = supply <= 17
    ample_supply = supply >= 22
    critical_me = hp <= 3 or no_water_days >= 1
    very_critical = hp <= 2 or no_water_days >= 2

    bid = DAILY_SALARY * 0.45

    if ample_supply:
        bid = DAILY_SALARY * 0.28
    elif tight_supply:
        bid = DAILY_SALARY * 0.62
    else:
        bid = DAILY_SALARY * 0.48

    if highest_prev >= 140:
        if critical_me:
            bid = max(bid, min(highest_prev + 2.0, DAILY_SALARY * 1.55))
        else:
            bid = min(bid, DAILY_SALARY * 0.35)
    elif highest_prev >= 95:
        if critical_me:
            bid = max(bid, min(highest_prev + 1.5, DAILY_SALARY * 1.2))
        else:
            bid = max(bid, avg_prev * 0.72)
    elif highest_prev > 0:
        bid = max(bid, min(highest_prev + 1.2, DAILY_SALARY * 0.95))

    if desperate_count >= 2:
        bid += 10.0
    elif desperate_count == 1:
        bid += 4.0

    if rich_count >= 2 and tight_supply:
        bid += 8.0

    if critical_me:
        bid = max(bid, DAILY_SALARY * 0.92)
    if very_critical:
        bid = max(bid, DAILY_SALARY * 1.12)

    if day >= 8 and hp >= 6 and not tight_supply:
        bid *= 0.88

    if budget < DAILY_SALARY * 1.2:
        bid = min(bid, budget * 0.82)
    elif budget > 300 and critical_me:
        bid = max(bid, DAILY_SALARY * 1.05)

    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget
    return float(max(0.0, bid))
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

    day = day_context['day']
    supply = float(day_context['supply'])
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    if budget <= 0:
        return 0.0

    alive = []
    prev_bids = []
    rich_threats = 0
    urgent_opponents = 0
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive.append(opp)
            if opp.get('budget', 0) >= 120:
                rich_threats += 1
            if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
                urgent_opponents += 1
            prev = opp.get('previous_trace', {})
            if prev and prev.get('bid') is not None:
                try:
                    prev_bids.append(float(prev.get('bid', 0)))
                except:
                    pass

    if not alive:
        return float(min(budget, 1.0))

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = sum(prev_bids) / len(prev_bids) if prev_bids else 0.0

    scarcity = 0.0
    if supply <= 16:
        scarcity = 1.0
    elif supply <= 18:
        scarcity = 0.7
    elif supply <= 21:
        scarcity = 0.4
    else:
        scarcity = 0.1

    danger = 0.0
    if hp <= 2:
        danger += 1.0
    elif hp <= 4:
        danger += 0.6
    elif hp <= 6:
        danger += 0.25
    if no_water >= 1:
        danger += 0.5

    market_pressure = 0.0
    if highest_prev >= 130:
        market_pressure = 1.0
    elif highest_prev >= 100:
        market_pressure = 0.7
    elif highest_prev >= 60:
        market_pressure = 0.4
    else:
        market_pressure = 0.15

    if hp >= 7 and supply >= 22 and day <= 3:
        bid = 0.0
    elif danger >= 1.2:
        bid = min(budget, max(132.0, highest_prev + 1.0, DAILY_SALARY * 1.9))
    elif scarcity >= 0.7 and hp <= 4:
        bid = min(budget, max(131.0, highest_prev + 0.5))
    elif scarcity >= 0.7:
        if hp >= 7 and budget < 220:
            bid = 0.0
        else:
            bid = min(budget, max(18.0, avg_prev * 0.18 + 8.0))
    elif supply >= 22:
        if hp >= 6:
            bid = min(budget, 6.0)
        else:
            bid = min(budget, 24.0)
    else:
        base = 10.0 + scarcity * 18.0 + danger * 22.0 + market_pressure * 8.0
        if rich_threats >= 2 and hp >= 6:
            base -= 8.0
        if urgent_opponents >= 2 and hp <= 5:
            base += 10.0
        bid = min(budget, max(0.0, base))

    if day >= 8:
        if hp <= 4:
            bid = max(bid, min(budget, 133.0))
        elif hp >= 7 and supply >= 20:
            bid = min(bid, budget)

    if budget < 40 and hp >= 6 and supply >= 19:
        bid = min(bid, 5.0)

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
    supply = day_context['supply']
    hp = my_status['hp']
    budget = my_status['budget']
    no_water = my_status['no_water_days']

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive'):
            alive_opponents.append(opp)

    if budget <= 0:
        return 0.0

    guaranteed_winners = int(supply // WATER_REQ)
    if guaranteed_winners < 0:
        guaranteed_winners = 0

    prev_bids = []
    urgent_opp = 0
    rich_opp = 0
    for opp in alive_opponents:
        if opp.get('budget', 0) > budget:
            rich_opp += 1
        if opp.get('hp', 10) <= 3 or opp.get('no_water_days', 0) >= 1:
            urgent_opp += 1
        prev = opp.get('previous_trace', {})
        bid = prev.get('bid') if isinstance(prev, dict) else None
        if bid is not None:
            prev_bids.append(bid)

    highest_prev = max(prev_bids) if prev_bids else 0.0
    avg_prev = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    if not alive_opponents:
        return float(min(budget, 18.0))

    severe_danger = hp <= 2 or no_water >= 1
    medium_danger = hp <= 4

    if guaranteed_winners <= 1:
        if severe_danger:
            target = max(92.0, highest_prev + 2.0)
        elif medium_danger:
            target = max(58.0, avg_prev * 0.75)
        else:
            target = 12.0
    else:
        if severe_danger:
            target = max(72.0, avg_prev + 3.0)
        elif medium_danger:
            target = max(46.0, avg_prev * 0.7)
        else:
            target = 24.0

    if highest_prev >= 120 and not severe_danger:
        target = min(target, 20.0)
    elif highest_prev >= 90 and not medium_danger:
        target = min(target, 26.0)

    if urgent_opp >= 2 and not severe_danger:
        target = min(target, 18.0)

    reserve = DAILY_SALARY * 2
    max_affordable = budget - reserve
    if severe_danger:
        max_affordable = budget - DAILY_SALARY * 0.25
    elif medium_danger:
        max_affordable = budget - DAILY_SALARY * 1.0

    if max_affordable < 0:
        max_affordable = budget

    bid = min(target, max_affordable, budget)
    if bid < 0:
        bid = 0.0
    return float(bid)
"""
