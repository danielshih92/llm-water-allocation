# ============================================================
# Experiment: exp1
# Agent: Bob
# Source: exp1
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = r'''
def get_bid(day_context, my_status):
    # Use a conservative bid close to the daily salary to secure water without overpaying
    daily_salary = 75
    supply = day_context.get("supply", 15)
    # Bidding slightly below the daily salary to remain competitive
    bid = daily_salary * 0.95
    return bid
'''

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = r'''
def get_bid(day_context, my_status):
    # Bid around the water requirement with a slight buffer
    # to ensure competitiveness without overspending.
    return 11.0

'''

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = r'''
def get_bid(day_context, my_status):
    # Extract supply and current day
    supply = day_context["supply"]
    day = day_context["day"]
    
    # Agent parameters
    water_req = my_status["hp"]  # water requirement, 9
    daily_salary = my_status["budget"]
    
    # Strategy:
    # Bid slightly above the water requirement (9), around 9.5 to 10
    # Ensure bid does not exceed current supply and is within budget
    bid = 10
    
    # Adjust bid if supply is very low
    if supply < 12:
        bid = 9.5
    
    # Ensure we do not bid more than our daily budget
    if bid > daily_salary:
        bid = daily_salary
    
    return bid
'''

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = r'''
def get_bid(day_context, my_status):
    supply = day_context["supply"]
    # Typical opponent bid in low supply scenario is around 11
    bid = 11.0
    # Ensure the bid does not exceed supply
    if bid > supply:
        bid = supply
    return bid
'''

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = r'''
def get_bid(day_context, my_status):
    supply = day_context.get("supply", 15)
    # Set a base bid slightly higher than requirement
    base_bid = 11.0
    # If supply is extremely low, lower the bid slightly
    if supply < 12:
        bid = base_bid - 0.5
    # If supply is moderate, keep base bid
    elif supply <= 18:
        bid = base_bid
    # If supply is higher, possibly increase bid slightly
    else:
        bid = base_bid + 0.5
    
    # Ensure we do not bid more than the agent's daily salary (budget threshold)
    if bid > my_status.get("budget", 75):
        bid = my_status.get("budget", 75)
    
    return bid
'''

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = r'''
def get_bid(day_context, my_status):
    supply = day_context.get("supply", 15)  # default to mid-range if not specified
    # Base bid around the water requirement
    base_bid = 9.0

    # Adjust bid based on supply to be more competitive on low supply days
    if supply <= 12:
        bid = base_bid + 1.0  # slightly above requirement for very low supply
    elif supply <= 15:
        bid = base_bid + 0.5  # moderately above requirement
    else:
        bid = base_bid  # standard bid on higher supply days

    # Ensure bid does not exceed the remaining budget significantly
    max_bid = my_status.get("budget", 1000)
    # Set a ceiling to avoid overspending
    if bid > max_bid * 0.3:
        bid = max_bid * 0.3

    # Ensure bid is at least slightly above zero
    if bid < 0.5:
        bid = 0.5

    return bid
'''

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = r'''
def get_bid(day_context, my_status):
    supply = day_context["supply"]
    # Based on the reasoning, bid slightly above 11 in low supply scenario.
    # To be conservative yet competitive, set the bid at 11.2
    return 11.2
'''

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = r'''
def get_bid(day_context, my_status):
    supply = day_context["supply"]
    remaining_budget = my_status["budget"]
    # In low supply scenarios (10-20), bid slightly above 11 to secure water without overspending
    base_bid = 11.5
    # Ensure we don't bid more than the remaining budget
    bid = min(base_bid, remaining_budget)
    return bid
'''

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = r'''
def get_bid(day_context, my_status):
    # In low supply situations, bid slightly above previous opponent bids (~11)
    # considering the historical context and agent profile, set bid to around 11.2.
    return 11.2
'''

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = r'''
def get_bid(day_context, my_status):
    supply = day_context.get("supply", 15)
    scenario = day_context.get("scenario", "normal")
    supply_min, supply_max = day_context.get("supply_range", [10, 20])
    opponent_bid = 11.2

    # Focus on low supply scenario
    if scenario == "low":
        # Target bids slightly above opponent's typical bid
        bid = opponent_bid + 0.3
    else:
        # For normal scenarios, bid near opponent's bid
        bid = opponent_bid

    # Ensure the bid does not exceed the daily salary
    if bid > my_status.get("budget", 75):
        bid = my_status.get("budget", 75)
    
    # Keep bid reasonable
    if bid < 0:
        bid = 0.0

    return bid
'''

