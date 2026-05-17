# ============================================================
# Experiment: exp1
# Agent: David
# Source: exp1
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = r'''
def get_bid(day_context, my_status):
    supply = day_context["supply"]
    requirement = 11
    # Aim to bid slightly above the minimal supply needed to secure water without overpaying
    # Since supply varies from just below requirement to double it,
    # bidding around requirement (11-12) balances competitiveness and cost.
    if supply >= requirement:
        bid = max(0.0, requirement + 1)
    else:
        # If supply is less than requirement, bid low to avoid overpaying for unlikely wins
        bid = max(0.0, supply + 1)
    return bid
'''

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = r'''
def get_bid(day_context, my_status):
    supply = day_context["supply"]
    water_req = my_status["hp"]
    # Bid slightly above the water requirement if supply is low
    if supply <= water_req + 1:
        bid = water_req + 0.5
    # If supply is moderate, bid around the water requirement
    elif supply <= 15:
        bid = water_req + 1
    # If supply is abundant, bid just below the supply maximum
    else:
        bid = supply - 0.5
    # Ensure bid stays within reasonable bounds
    if bid > supply:
        bid = supply
    if bid < 0:
        bid = 0
    return bid
'''

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = r'''
def get_bid(day_context, my_status):
    # Bid exactly at the water requirement to maximize win chances in low supply scenario
    return 11.0
'''

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = r'''
def get_bid(day_context, my_status):
    supply = day_context["supply"]
    day = day_context["day"]
    hp = my_status["hp"]
    budget = my_status["budget"]
    no_water_days = my_status["no_water_days"]
    
    # If the water supply is low, bid higher on the first days to secure water
    # otherwise, bid lower to save budget for later.
    # Also, if the agent has not had water in recent days, increase bid.
    
    # Basic strategy:
    # - On early days, bid proportionally to supply to secure water if supply is low
    # - On later days, decrease bid slightly to conserve budget
    # - If no water for many days, increase bid to attempt to get water
    
    supply_threshold = 15  # midpoint of supply range [10,20]
    max_bid = min(budget, 200)  # cap bid to budget and a reasonable max
    
    # Determine bid based on supply
    if supply < supply_threshold:
        base_bid = (supply / supply_threshold) * 0.5 * max_bid
    else:
        base_bid = (supply / supply_threshold) * 0.3 * max_bid
    
    # Increase bid if haven't had water in a while
    if no_water_days > 2:
        increase = (no_water_days - 2) * 0.1 * max_bid
        bid = base_bid + increase
    else:
        bid = base_bid
    
    # Ensure bid does not exceed remaining budget
    if bid > budget:
        bid = budget
    
    # Bid should be at least a small positive amount
    if bid < 0.01:
        bid = 0.01
    
    return bid
'''

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = r'''
def get_bid(day_context, my_status):
    supply = day_context["supply"]
    budget = my_status["budget"]
    no_water_days = my_status["no_water_days"]
    water_requirement = 11
    
    # Base bid around the water requirement
    base_bid = water_requirement
    
    # Adjust bid slightly based on supply levels
    if supply >= 15:
        bid = base_bid + 0.3  # Slightly above requirement when supply is high
    elif supply >= 10 and supply < 15:
        bid = base_bid + 0.1  # Close to requirement when supply is moderate
    else:
        bid = base_bid - 0.2  # Slightly below requirement when supply is low
    
    # Ensure bid does not exceed remaining budget
    max_bid = min(bid, budget)
    
    # To add some variability and competitiveness, slightly tweak the bid
    final_bid = max(0, max_bid)
    
    return final_bid
'''

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = r'''
def get_bid(day_context, my_status):
    supply = day_context.get("supply", 15)
    # Set a base bid around the required water amount
    base_bid = 11
    
    # Adjust bid slightly upward if supply is very low to increase competitiveness
    if supply <= 10:
        bid = base_bid + 0.5  # bid around 11.5
    # Slightly decrease bid if supply is high to conserve budget
    elif supply >= 20:
        bid = base_bid - 0.5  # bid around 10.5
    else:
        # For medium supply, stay close to required amount
        bid = base_bid
    
    # Ensure bid does not exceed remaining budget
    if bid > my_status.get("budget", 0):
        bid = my_status.get("budget", 0)
    
    # Bid should not be negative
    if bid < 0:
        bid = 0
    
    return bid
'''

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = r'''
def get_bid(day_context, my_status):
    # Given the scenario and agent profile, bid approximately 11 units
    return 11.0
'''

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = r'''
def get_bid(day_context, my_status):
    # In a low supply scenario, aim to bid slightly above 11 to stay competitive.
    # Considering the reasoning, a bid around 11.2 balances competitiveness and budget.
    return 11.2
'''

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = r'''
def get_bid(day_context, my_status):
    supply = day_context["supply"]
    # Determine a competitive bid based on supply conditions
    # Low supply (close to the lower end of supply_range) suggests bidding around 11.2
    # Slight upward adjustment based on supply level
    # For simplicity, we set a fixed bid close to the target value
    bid = 11.2
    return bid
'''

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = r'''
def get_bid(day_context, my_status):
    # Based on the reasoning, bid slightly above previous competitive bids (~11.2)
    bid_amount = 11.3
    # Ensure bid does not exceed remaining budget
    if bid_amount > my_status["budget"]:
        bid_amount = my_status["budget"]
    return bid_amount
'''

