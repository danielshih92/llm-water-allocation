# ============================================================
# Experiment: exp1
# Agent: Cindy
# Source: exp1
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = r'''
def get_bid(day_context, my_status):
    # Water requirement per day
    requirement = 10
    # Supply range during the scenario (assumed known from scenario info)
    supply_min, supply_max = 10, 20
    
    # Calculate an average supply to set a bid just above this value
    avg_supply = (supply_min + supply_max) / 2
    
    # Bid slightly above the requirement or the average supply to ensure winning
    bid = requirement + 0.1
    
    # Ensure bid does not exceed the supply (to avoid paying more than the water's worth)
    if bid > supply_max:
        bid = supply_max
    
    return bid

'''

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = r'''
def get_bid(day_context, my_status):
    supply = day_context["supply"]
    # To balance bidding around the needed water and conservative spending,
    # bid slightly above the requirement, e.g., around 11 units.
    return 11.0
'''

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = r'''
def get_bid(day_context, my_status):
    supply = day_context.get("supply", 15)
    requirement = 10
    # In low supply scenario, bid slightly above requirement
    # Adjust bid based on supply: if supply is very low, bid closer to requirement
    if supply <= 12:
        bid = requirement + 0.5
    elif supply <= 15:
        bid = requirement + 1.0
    else:
        bid = requirement + 1.5
    # Ensure bid does not exceed supply
    if bid > supply:
        bid = supply
    return bid
'''

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = r'''
def get_bid(day_context, my_status):
    supply = day_context["supply"]
    # Prior strategies suggest bidding close to 11, with adjustments based on supply.
    # For low supply (10-20), bid around 10.5 to 11 to stay competitive.
    # If supply is higher, slightly increase bid; if lower, be cautious.
    if supply >= 15:
        bid = 10.8
    elif supply >= 12:
        bid = 10.5
    else:
        bid = 10.2
    # Ensure the bid does not exceed the remaining budget.
    return min(bid, my_status["budget"])
'''

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = r'''
def get_bid(day_context, my_status):
    # In a low supply scenario, historical data suggests bidding around 11
    # to stay competitive without overspending.
    # Slight adjustments can be made based on supply levels for better adaptation.
    supply = day_context.get("supply", 15)
    # If supply is very low (below 12), consider slightly increasing bid
    if supply < 12:
        bid = 11.5
    # If supply is high (above 18), consider lowering bid
    elif supply > 18:
        bid = 10.5
    else:
        bid = 11
    return bid
'''

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = r'''
def get_bid(day_context, my_status):
    supply = day_context["supply"]
    # Set a base bid around 11.5, considering opponents and supply conditions
    bid = 11.5
    
    # Adjust bid slightly based on supply: lower supply might mean bid slightly lower
    if supply <= 10:
        bid = 11
    elif supply >= 20:
        bid = 12
    
    # Ensure bid does not exceed daily salary
    if bid > my_status["budget"]:
        bid = my_status["budget"]
    
    return bid
'''

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = r'''
def get_bid(day_context, my_status):
    supply = day_context["supply"]
    budget = my_status["budget"]

    # Desired bid is slightly above water requirement for competitiveness
    base_bid = 11

    # Adjust bid if budget is low
    if budget < 15:
        bid = min(base_bid, budget * 0.8)
    else:
        bid = base_bid

    # Ensure bid does not exceed remaining budget
    if bid > budget:
        bid = budget

    return bid
'''

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = r'''
def get_bid(day_context, my_status):
    supply = day_context.get("supply", 15)  # default to midpoint if not provided
    budget = my_status.get("budget", 1000)
    # Determine bid based on supply, to stay competitive in low supply scenario
    # Aim for around 11 units, conservative to avoid overspending
    base_bid = 11
    
    # Adjust bid slightly downward if budget is low
    if budget < 50:
        bid = base_bid * 0.9
    # Adjust bid slightly upward if supply is very low
    elif supply <= 10:
        bid = base_bid * 1.1
    else:
        bid = base_bid
    
    # Ensure bid does not exceed remaining budget
    bid = min(bid, budget)
    
    return bid
'''

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = r'''
def get_bid(day_context, my_status):
    supply = day_context["supply"]
    # In low supply scenarios, bid around 11.2
    return 11.2
'''

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = r'''
def get_bid(day_context, my_status):
    # In low supply scenarios (supply between 10 and 20),
    # historical opponent bids are around 11.2.
    # To increase chances of winning, bid slightly above 11.2.
    # Ensure not to exceed budget constraints.
    bid = 11.3
    if bid > my_status['budget']:
        bid = my_status['budget']
    return bid
'''

