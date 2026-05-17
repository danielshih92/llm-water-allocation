# ============================================================
# Experiment: exp1
# Agent: Alex
# Source: exp1
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = r'''
def get_bid(day_context, my_status):
    supply = day_context["supply"]
    water_req = my_status["hp"]
    daily_salary = my_status["budget"]
    
    # Scenario is low supply, supply between 10 and 20
    # Basic strategy:
    # - Bid slightly above water requirement to secure water
    # - Avoid overbidding to save budget
    # - Bid around 15 units as a conservative amount
    
    bid = 15.0
    return bid
'''

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = r'''
def get_bid(day_context, my_status):
    # Extract current supply and day
    supply = day_context.get("supply", 15)  # default to middle if not provided
    day_number = day_context.get("day", 1)
    
    # Set base requirement and daily salary
    requirement = my_status.get("hp", 8)
    daily_salary = my_status.get("budget", 70)
    
    # Determine bid based on supply; in low supply scenario, bid slightly above requirement
    # to ensure competitiveness without overpaying.
    # Use a simple strategy: bid = requirement + 0.5, capped at supply
    bid = requirement + 0.5
    if bid > supply:
        bid = supply  # cannot bid more than supply
    
    return bid

'''

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = r'''
def get_bid(day_context, my_status):
    # Strategy based on low supply scenario, aiming to bid slightly above the water requirement
    # and aligned with opponent bidding patterns.
    
    water_requirement = 8
    opponent_bid_estimate = 11
    # Bid close to opponent's estimate, ensuring competitiveness without overspending
    bid_amount = opponent_bid_estimate
    return bid_amount
'''

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = r'''
def get_bid(day_context, my_status):
    supply = day_context["supply"]
    # Basic heuristic: bid slightly above the water requirement (~8)
    # Adjust bid downward if supply is very low (around 10) to avoid overbidding
    if supply <= 12:
        bid = 9.5
    else:
        bid = 10
    # Ensure bid does not exceed budget
    bid = min(bid, my_status["budget"])
    return bid
'''

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = r'''
def get_bid(day_context, my_status):
    # Extract relevant information
    supply = day_context.get("supply", 15)  # default to mid-range if not provided
    budget = my_status.get("budget", 1000)
    day = day_context.get("day", 1)
    
    # Based on reasoning, bid around 12.0 to 12.5
    # Ensure not to overspend early; bid is capped at a modest fraction of the remaining budget
    # For low supply scenario with a limited number of days, a bid of around 12.2 is reasonable
    bid = 12.2
    
    # Cap bid to available budget
    if bid > budget:
        bid = budget
    
    return bid
'''

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = r'''
def get_bid(day_context, my_status):
    supply = day_context.get("supply", 15)  # Default to mid-supply if not provided
    # Based on the reasoning, bid around 11 to outbid opponents in low supply
    return 11.0
'''

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = r'''
def get_bid(day_context, my_status):
    supply = day_context.get("supply", 15)
    # Since supply is generally low (10-20), bid around or slightly above the requirement.
    # Setting bid close to 8.5 to 9 to balance winning chances and budget.
    # Adjust bid based on supply level: slightly higher if supply is very low.
    if supply < 12:
        return 9.0
    else:
        return 8.5

'''

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = r'''
def get_bid(day_context, my_status):
    supply = day_context["supply"]
    # Opponent similar to previous low-supply bids around 11.7, and our water need is 8.
    # Bidding around 11.2 should be competitive in low supply conditions.
    bid_amount = 11.2
    return bid_amount
'''

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = r'''
def get_bid(day_context, my_status):
    supply = day_context["supply"]
    # In low supply scenarios, aim for a bid around 11.2 to 11.5 based on previous trends
    # Since previous bids hover around 11.2, set bid slightly above that to increase winning chances
    bid = 11.2
    return bid
'''

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = r'''
def get_bid(day_context, my_status):
    # In low supply scenario, previous data suggests bidding around 11.2
    # My agent, Alex, has a daily salary of 70, which is well above this amount,
    # so bidding around 11.2 is both strategic and affordable.
    return 11.2
'''

