# ============================================================
# Experiment: exp1
# Agent: Eric
# Source: exp1
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = r'''
def get_bid(day_context, my_status):
    supply = day_context["supply"]
    # If supply is low (between 10 and 20 units), bid slightly above the minimal supply to secure water
    if supply >= 10 and supply <= 20:
        # Set bid just above the minimal supply (e.g., 11), but not exceeding the agent's valuation (~12)
        bid = 11
        # Ensure the bid does not exceed the agent's valuation of water (~12)
        if bid > my_status["water_requirement"]:
            bid = my_status["water_requirement"]
        # Make sure the bid is positive
        if bid < 0:
            bid = 0
        return bid
    else:
        # For higher supply, bid conservatively or abstain
        return 0.0
'''

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = r'''
def get_bid(day_context, my_status):
    # Extract supply and current day
    supply = day_context.get("supply", 15)
    day = day_context.get("day", 1)
    
    # Constants
    water_req = 12
    # Set bid slightly above water requirement, below typical opponent bids (~15)
    bid = water_req + 1  # 13
    
    # Ensure bid does not exceed remaining budget
    if "budget" in my_status:
        remaining_budget = my_status["budget"]
        # Limit bid to a reasonable portion of remaining budget
        max_bid = remaining_budget * 0.2
        if bid > max_bid:
            bid = max_bid
    
    # Round bid to 2 decimal places for simplicity
    return round(bid, 2)
'''

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = r'''
def get_bid(day_context, my_status):
    supply = day_context["supply"]
    water_req = 12
    # In low supply scenarios (supply 10-20), bid close to opponent's typical bid (~11)
    # Ensure bid does not exceed supply
    bid = 11
    if bid > supply:
        bid = supply
    # Keep bid reasonable to avoid overspending
    return bid
'''

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = r'''
def get_bid(day_context, my_status):
    # Since supply is low (10-20), aim for competitive bid just above 12
    # to secure enough water at minimal cost.
    return 12.5
'''

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = r'''
def get_bid(day_context, my_status):
    supply = day_context.get("supply", 0)
    water_need = 12  # Agent's water requirement
    # Base bid around 10 to stay competitive while avoiding overspending
    # Adjust bid slightly based on supply levels; lower supply may warrant a slightly higher bid
    if supply < 15:
        bid = 10.5
    elif supply < 20:
        bid = 10.0
    else:
        bid = 9.5
    # Ensure bid is at least enough to win the water
    bid = max(bid, water_need - 0.1)
    # Do not exceed the budget
    return min(bid, my_status["budget"])
'''

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = r'''
def get_bid(day_context, my_status):
    supply = day_context["supply"]
    budget = my_status["budget"]
    # Set a base bid around 12.2, slightly adjusted for supply and budget awareness
    bid = 12.2
    
    # Prevent bidding more than remaining budget
    if bid > budget:
        bid = budget
    
    return bid

'''

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = r'''
def get_bid(day_context, my_status):
    supply = day_context.get("supply", 15)
    budget = my_status.get("budget", 1000)
    no_water_days = my_status.get("no_water_days", 0)

    # Set a base bid around 11.5 to outbid competitors on low supply days
    base_bid = 11.5

    # Adjust bid slightly if supply is very low
    if supply <= 10:
        bid = base_bid + 0.2  # around 11.7
    elif supply >= 20:
        bid = base_bid - 0.2  # around 11.3
    else:
        # For medium supply, keep close to base bid
        bid = base_bid

    # Ensure not to exceed remaining budget
    if bid > budget:
        bid = max(0.0, budget)

    return bid
'''

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = r'''
def get_bid(day_context, my_status):
    supply = day_context["supply"]
    budget = my_status["budget"]
    water_needed = 12
    
    # Target bid based on the reasoning: a balance slightly above water need (around 11)
    # and considering supply constraints, opponent tendencies, and budget.
    
    # Keep the bid stable around 11 in low supply scenario
    bid = 11
    
    # Ensure not to bid more than remaining budget
    if bid > budget:
        bid = budget
    
    return bid
'''

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = r'''
def get_bid(day_context, my_status):
    # In low supply scenarios, a bid around 11.2 has proven competitive.
    # Ensure the bid is within the daily salary budget.
    bid = 11.2
    if bid > my_status["budget"]:
        # If the calculated bid exceeds remaining budget, bid the remaining amount.
        bid = my_status["budget"]
    return bid
'''

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = r'''
def get_bid(day_context, my_status):
    # Since scenario is "low" supply and previous data suggests around 11.2 bid,
    # set a bid slightly above that to increase winning chances without excessive cost.
    # To keep it simple, we'll choose a fixed bid of 11.5.
    return 11.5
'''

