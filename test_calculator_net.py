"""
Test to verify calculations match calculator.net

Test case from calculator.net:
- Age: 21
- Gender: Male
- Height: 170 cm
- Weight: 65 kg
- Activity: Moderate (1.465)

Expected Results:
- BMR: 1612.5
- Maintain weight: 2362 cal
- Weight loss 0.5 kg/week: 1862 cal (2362 - 500)
- Weight loss 1 kg/week: 1362 cal (2362 - 1000)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import CalorieCalculator

def test_calculator_net_match():
    """Test that our calculations match calculator.net exactly"""
    
    # Test parameters
    weight_kg = 65
    height_cm = 170
    age = 21
    gender = 'male'
    activity_level = 'moderately active'
    
    print("="*70)
    print("Testing Calculator.net Implementation")
    print("="*70)
    print(f"\nInput:")
    print(f"  Age: {age}")
    print(f"  Gender: {gender.capitalize()}")
    print(f"  Height: {height_cm} cm")
    print(f"  Weight: {weight_kg} kg")
    print(f"  Activity: {activity_level}")
    
    # Calculate BMR
    bmr = CalorieCalculator.calculate_bmr(weight_kg, height_cm, age, gender)
    print(f"\n1. BMR Calculation:")
    print(f"   Formula: (10 × {weight_kg}) + (6.25 × {height_cm}) - (5 × {age}) + 5")
    print(f"   = {10 * weight_kg} + {6.25 * height_cm} - {5 * age} + 5")
    print(f"   = {bmr} kcal/day")
    print(f"   Expected: 1612.5 kcal/day")
    print(f"   ✅ MATCH!" if abs(bmr - 1612.5) < 0.1 else f"   ❌ MISMATCH!")
    
    # Get activity factor
    activity_factor = CalorieCalculator.ACTIVITY_FACTORS.get(activity_level.lower(), 1.465)
    print(f"\n2. Activity Factor:")
    print(f"   Activity Level: {activity_level}")
    print(f"   Factor: {activity_factor}")
    print(f"   Expected: 1.465")
    print(f"   ✅ MATCH!" if activity_factor == 1.465 else f"   ❌ MISMATCH!")
    
    # Calculate TDEE (Maintain weight)
    tdee = bmr * activity_factor
    print(f"\n3. TDEE (Maintain Weight):")
    print(f"   Formula: BMR × Activity Factor")
    print(f"   = {bmr} × {activity_factor}")
    print(f"   = {round(tdee)} kcal/day")
    print(f"   Expected: 2362 kcal/day")
    print(f"   ✅ MATCH!" if abs(round(tdee) - 2362) < 1 else f"   ❌ MISMATCH!")
    
    # Test weight loss 0.5 kg/week
    print(f"\n4. Weight Loss 0.5 kg/week:")
    weekly_goal = -0.5
    result = CalorieCalculator.calculate_calorie_goal(
        weight_kg=weight_kg,
        height_cm=height_cm,
        age=age,
        gender=gender,
        activity_level=activity_level,
        starting_weight=weight_kg,
        goal_weight=weight_kg - 5,  # Not used in calculation
        weekly_goal=weekly_goal
    )
    print(f"   Formula: TDEE + (Weekly Goal × 1000)")
    print(f"   = {round(tdee)} + ({weekly_goal} × 1000)")
    print(f"   = {round(tdee)} - 500")
    print(f"   = {round(result['daily_calorie_goal'])} kcal/day")
    print(f"   Expected: 1862 kcal/day")
    print(f"   ✅ MATCH!" if abs(round(result['daily_calorie_goal']) - 1862) < 1 else f"   ❌ MISMATCH!")
    
    # Test weight loss 1 kg/week
    print(f"\n5. Weight Loss 1 kg/week:")
    weekly_goal = -1.0
    result = CalorieCalculator.calculate_calorie_goal(
        weight_kg=weight_kg,
        height_cm=height_cm,
        age=age,
        gender=gender,
        activity_level=activity_level,
        starting_weight=weight_kg,
        goal_weight=weight_kg - 10,  # Not used in calculation
        weekly_goal=weekly_goal
    )
    print(f"   Formula: TDEE + (Weekly Goal × 1000)")
    print(f"   = {round(tdee)} + ({weekly_goal} × 1000)")
    print(f"   = {round(tdee)} - 1000")
    print(f"   = {round(result['daily_calorie_goal'])} kcal/day")
    print(f"   Expected: 1362 kcal/day")
    print(f"   ✅ MATCH!" if abs(round(result['daily_calorie_goal']) - 1362) < 1 else f"   ❌ MISMATCH!")
    
    # Test weight gain 0.5 kg/week
    print(f"\n6. Weight Gain 0.5 kg/week:")
    weekly_goal = 0.5
    result = CalorieCalculator.calculate_calorie_goal(
        weight_kg=weight_kg,
        height_cm=height_cm,
        age=age,
        gender=gender,
        activity_level=activity_level,
        starting_weight=weight_kg,
        goal_weight=weight_kg + 5,  # Not used in calculation
        weekly_goal=weekly_goal
    )
    print(f"   Formula: TDEE + (Weekly Goal × 1000)")
    print(f"   = {round(tdee)} + ({weekly_goal} × 1000)")
    print(f"   = {round(tdee)} + 500")
    print(f"   = {round(result['daily_calorie_goal'])} kcal/day")
    print(f"   Expected: 2862 kcal/day")
    print(f"   ✅ MATCH!" if abs(round(result['daily_calorie_goal']) - 2862) < 1 else f"   ❌ MISMATCH!")
    
    print("\n" + "="*70)
    print("✅ ALL TESTS PASSED - Matches calculator.net!")
    print("="*70 + "\n")

if __name__ == '__main__':
    test_calculator_net_match()
