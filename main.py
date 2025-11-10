from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import os
import json
import math
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration - Load from environment variables
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not GEMINI_API_KEY:
    print("⚠️  WARNING: GEMINI_API_KEY not found in environment variables!")
    print("Please set it in your .env file or environment.")
else:
    # Configure Gemini API
    genai.configure(api_key=GEMINI_API_KEY)
    print("✅ Gemini API configured successfully!")


class CalorieCalculator:
    """
    YAZIO Calorie Calculator using Mifflin-St. Jeor Equation
    
    Official YAZIO Formula:
    ========================
    Calorie Goal = (BMR × Activity Factor) + Energy Difference
    
    Components:
    -----------
    1. BMR (Basal Metabolic Rate) - Mifflin-St. Jeor Equation:
       • Men: (10 × weight in kg) + (6.25 × height in cm) - (5 × age) + 5
       • Women: (10 × weight in kg) + (6.25 × height in cm) - (5 × age) - 161
    
    2. Activity Factor:
       • Low: 1.25 (sedentary, mostly sitting)
       • Moderate: 1.38 (some activity, light exercise)
       • High: 1.52 (very active, regular exercise)
       • Very High: 1.65 (extremely active, athlete level)
       
       New Users (before activity level is set):
       • Men: 1.36
       • Women: 1.33
    
    3. TDEE (Total Daily Energy Expenditure):
       TDEE = BMR × Activity Factor
       This is your maintenance calories (to maintain current weight)
    
    4. Energy Difference:
       Energy Difference = Weekly Goal (kg) × 750
       
       Based on: 1 kg body weight ≈ 7,500 calories
       Distributed over 7 days: 7,500 ÷ 10 days per kg = 750 cal/day per 0.1 kg/week
       
       Sign Convention:
       • Weight LOSS: weekly_goal is NEGATIVE (-0.5, -1.0, etc.)
         Creates a calorie DEFICIT
       • Weight GAIN: weekly_goal is POSITIVE (+0.5, +1.0, etc.)
         Creates a calorie SURPLUS
       • MAINTAIN: weekly_goal is ZERO (0)
         No change to TDEE
    
    Example (from YAZIO documentation):
    -----------------------------------
    John Smith: 80 kg, 180 cm, 29 years, Male, Moderate activity (1.38)
    Goal: Gain to 85 kg at +0.5 kg/week
    
    BMR = (10 × 80) + (6.25 × 180) - (5 × 29) + 5 = 1,785 Cal
    TDEE = 1,785 × 1.38 = 2,463.3 Cal
    Energy Difference = 0.5 × 750 = 375 Cal
    Final Goal = 2,463.3 + 375 = 2,838.3 Cal/day
    
    References:
    -----------
    • YAZIO uses Mifflin-St. Jeor (5% more accurate than Harris-Benedict)
    • Does NOT use Broca Index Adjustment (only for Harris-Benedict)
    • 750 cal/day per kg/week includes a "safety cushion" vs. 1000 cal rule of thumb
    """
    
    # Activity level factors (YAZIO standard)
    ACTIVITY_FACTORS = {
        'low': 1.25,
        'sedentary': 1.25,
        'moderate': 1.38,
        'moderately active': 1.38,
        'high': 1.52,
        'very active': 1.52,
        'very_high': 1.65,
        'extremely active': 1.65
    }
    
    # New user default factors
    NEW_USER_FACTORS = {
        'male': 1.36,
        'female': 1.33
    }
    
    @staticmethod
    def calculate_bmr(weight_kg, height_cm, age, gender):
        """
        Calculate Basal Metabolic Rate using Mifflin-St. Jeor Equation
        
        Men: (10 × weight) + (6.25 × height) - (5 × age) + 5
        Women: (10 × weight) + (6.25 × height) - (5 × age) - 161
        """
        base = (10 * weight_kg) + (6.25 * height_cm) - (5 * age)
        
        if gender.lower() == 'male':
            bmr = base + 5
        else:  # female
            bmr = base - 161
            
        return round(bmr, 2)
    
    @staticmethod
    def calculate_energy_difference(starting_weight, goal_weight, weekly_goal):
        """
        Calculate energy difference for weight gain/loss
        
        Official YAZIO Formula:
        Energy Difference = (Weight difference × 750) ÷ (Weight difference ÷ Weekly goal)
        
        This simplifies to: Energy Difference = Weekly goal × 750
        
        IMPORTANT - Sign Convention:
        • Weight LOSS: weekly_goal is NEGATIVE (-0.5, -1.0, etc.)
          Example: -0.5 kg/week → -0.5 × 750 = -375 kcal/day (deficit)
        
        • Weight GAIN: weekly_goal is POSITIVE (+0.5, +1.0, etc.)
          Example: +0.5 kg/week → +0.5 × 750 = +375 kcal/day (surplus)
        
        • MAINTAIN: weekly_goal is ZERO (0)
          Example: 0 kg/week → 0 × 750 = 0 kcal/day (no change)
        
        The weekly_goal parameter MUST be correctly signed by the caller.
        """
        # Official YAZIO formula: Weekly goal × 750
        # No sign manipulation - the weekly_goal should already have the correct sign
        energy_diff = weekly_goal * 750
        
        return round(energy_diff, 2)
    
    @staticmethod
    def calculate_calorie_goal(weight_kg, height_cm, age, gender, 
                              activity_level, starting_weight, goal_weight, 
                              weekly_goal, is_new_user=False):
        """
        Complete calorie goal calculation using YAZIO methodology
        
        Returns dictionary with all calculated values
        """
        # Step 1: Calculate BMR
        bmr = CalorieCalculator.calculate_bmr(weight_kg, height_cm, age, gender)
        
        # Step 2: Get activity factor
        if is_new_user:
            activity_factor = CalorieCalculator.NEW_USER_FACTORS.get(gender.lower(), 1.36)
        else:
            activity_factor = CalorieCalculator.ACTIVITY_FACTORS.get(activity_level.lower(), 1.38)
        
        # Step 3: Calculate active metabolic rate (TDEE)
        tdee = bmr * activity_factor
        
        # Step 4: Calculate energy difference
        energy_difference = CalorieCalculator.calculate_energy_difference(
            starting_weight, goal_weight, weekly_goal
        )
        
        # Step 5: Final calorie goal
        calorie_goal = tdee + energy_difference
        
        # Calculate BMI
        height_m = height_cm / 100
        current_bmi = weight_kg / (height_m ** 2)
        goal_bmi = goal_weight / (height_m ** 2)
        
        # Determine goal type
        if starting_weight > goal_weight:
            goal_type = "weight_loss"
        elif starting_weight < goal_weight:
            goal_type = "weight_gain"
        else:
            goal_type = "maintain"
        
        return {
            'bmr': round(bmr, 2),
            'activity_factor': activity_factor,
            'tdee': round(tdee, 2),
            'energy_difference': round(energy_difference, 2),
            'daily_calorie_goal': round(calorie_goal, 2),
            'current_bmi': round(current_bmi, 2),
            'goal_bmi': round(goal_bmi, 2),
            'goal_type': goal_type,
            'weekly_goal_kg': weekly_goal,
            'weight_difference': round(starting_weight - goal_weight, 2)
        }
    
    @staticmethod
    def calculate_macros(calorie_goal, carb_percent=50, protein_percent=20, fat_percent=30):
        """
        Calculate macronutrient distribution
        
        1g Carbs = 4 calories
        1g Protein = 4 calories
        1g Fat = 9 calories
        """
        carb_calories = calorie_goal * (carb_percent / 100)
        protein_calories = calorie_goal * (protein_percent / 100)
        fat_calories = calorie_goal * (fat_percent / 100)
        
        return {
            'carbohydrates': {
                'grams': round(carb_calories / 4, 1),
                'calories': round(carb_calories, 1),
                'percentage': carb_percent
            },
            'protein': {
                'grams': round(protein_calories / 4, 1),
                'calories': round(protein_calories, 1),
                'percentage': protein_percent
            },
            'fats': {
                'grams': round(fat_calories / 9, 1),
                'calories': round(fat_calories, 1),
                'percentage': fat_percent
            }
        }


def extract_user_info(user_data):
    """
    Extract and normalize user information from onboarding data
    Returns standardized dictionary with all necessary fields
    """
    # Handle nested data structure
    if isinstance(user_data, dict) and 'data' in user_data:
        data_fields = user_data.get('data', {})
        user_info = user_data.get('user', {})
    else:
        data_fields = user_data
        user_info = {}
    
    # Extract basic info
    name = data_fields.get('What would you like to be called?', 
                          user_info.get('firstName', 'User'))
    
    # Extract gender
    gender_raw = data_fields.get("What's Your Sex?", data_fields.get('gender', 'male'))
    gender = gender_raw.lower() if gender_raw else 'male'
    
    # Extract height
    height_cm = float(data_fields.get('Height (cm)', data_fields.get('height_cm', 170)))
    height_ft_in = data_fields.get('Height (ft/in)', "5'7\"")
    
    # Extract weights
    current_weight_str = data_fields.get('Current Weight', data_fields.get('weight_kg', '65'))
    current_weight = float(str(current_weight_str).replace(' kg', '').replace('kg', '').strip())
    
    starting_weight = float(data_fields.get('starting_weight', current_weight))
    
    goal_weight_str = data_fields.get("Let's set the goal you're going to crush.", 
                                     data_fields.get('goal_weight', '60'))
    goal_weight = float(str(goal_weight_str).replace(' kg', '').replace('kg', '').strip())
    
    # Extract age from birthday
    birthday = data_fields.get('When is your birthday?', {})
    if isinstance(birthday, dict):
        birth_year = birthday.get('year', 2000)
        current_year = datetime.now().year
        age = current_year - birth_year
    else:
        age = int(data_fields.get('age', 25))
    
    # Extract activity level
    activity_raw = data_fields.get('How active are you?', data_fields.get('activity_level', 'moderate'))
    activity_level = activity_raw.lower() if activity_raw else 'moderate'
    
    # Extract goal
    goal = data_fields.get('Goal', data_fields.get("What's Your main goal?", 'Lose weight'))
    
    # Extract weekly goal
    weekly_goal = float(data_fields.get('weekly_goal', -0.5))
    
    # Extract diet type
    diet_type = data_fields.get('Do you follow a specific diet?', 'Classic')
    
    return {
        'name': name,
        'age': age,
        'gender': gender,
        'height_cm': height_cm,
        'height_ft_in': height_ft_in,
        'current_weight': current_weight,
        'starting_weight': starting_weight,
        'goal_weight': goal_weight,
        'activity_level': activity_level,
        'goal': goal,
        'weekly_goal': weekly_goal,
        'diet_type': diet_type,
        'full_data': data_fields  # Keep full data for LLM context
    }


def get_bmi_category(bmi):
    """Return BMI category based on value"""
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal weight"
    elif bmi < 30:
        return "Overweight"
    elif bmi < 35:
        return "Obese Class I"
    elif bmi < 40:
        return "Obese Class II"
    else:
        return "Obese Class III"


def calculate_timeline(weight_difference, weekly_goal):
    """Calculate timeline to reach goal weight"""
    if weekly_goal == 0:
        return {
            'weeks_to_goal': 0,
            'months_to_goal': 0,
            'start_date': datetime.now().strftime("%Y-%m-%d"),
            'estimated_goal_date': datetime.now().strftime("%Y-%m-%d")
        }
    
    weeks = abs(weight_difference / weekly_goal)
    days = int(weeks * 7)
    
    start_date = datetime.now()
    goal_date = start_date + timedelta(days=days)
    
    return {
        'weeks_to_goal': round(weeks, 1),
        'months_to_goal': round(weeks / 4.33, 1),
        'start_date': start_date.strftime("%Y-%m-%d"),
        'estimated_goal_date': goal_date.strftime("%Y-%m-%d")
    }


# Structured output schema for Gemini API
OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "meal_distribution": {
            "type": "object",
            "properties": {
                "breakfast": {
                    "type": "object",
                    "properties": {
                        "calories": {"type": "integer"},
                        "protein_g": {"type": "integer"},
                        "carbs_g": {"type": "integer"},
                        "fats_g": {"type": "integer"}
                    },
                    "required": ["calories", "protein_g", "carbs_g", "fats_g"]
                },
                "lunch": {
                    "type": "object",
                    "properties": {
                        "calories": {"type": "integer"},
                        "protein_g": {"type": "integer"},
                        "carbs_g": {"type": "integer"},
                        "fats_g": {"type": "integer"}
                    },
                    "required": ["calories", "protein_g", "carbs_g", "fats_g"]
                },
                "dinner": {
                    "type": "object",
                    "properties": {
                        "calories": {"type": "integer"},
                        "protein_g": {"type": "integer"},
                        "carbs_g": {"type": "integer"},
                        "fats_g": {"type": "integer"}
                    },
                    "required": ["calories", "protein_g", "carbs_g", "fats_g"]
                },
                "snacks": {
                    "type": "object",
                    "properties": {
                        "calories": {"type": "integer"},
                        "protein_g": {"type": "integer"},
                        "carbs_g": {"type": "integer"},
                        "fats_g": {"type": "integer"}
                    },
                    "required": ["calories", "protein_g", "carbs_g", "fats_g"]
                }
            },
            "required": ["breakfast", "lunch", "dinner", "snacks"]
        },
        "personalized_recommendations": {
            "type": "object",
            "properties": {
                "water_intake_liters": {"type": "number"},
                "protein_timing": {"type": "string"},
                "meal_prep_suggestions": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "activity_recommendations": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "key_challenges_addressed": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["water_intake_liters", "protein_timing", "meal_prep_suggestions", "activity_recommendations", "key_challenges_addressed"]
        },
        "weekly_goals": {
            "type": "object",
            "properties": {
                "weekday_calories": {"type": "integer"},
                "weekend_calories": {"type": "integer"},
                "step_goal": {"type": "integer"},
                "tracking_streak_goal": {"type": "string"}
            },
            "required": ["weekday_calories", "weekend_calories", "step_goal", "tracking_streak_goal"]
        },
        "warnings_and_notes": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": ["meal_distribution", "personalized_recommendations", "weekly_goals", "warnings_and_notes"]
}

# Simplified LLM prompt for personalized recommendations only
PERSONALIZATION_PROMPT = """You are a nutrition and wellness coach. Based on the user's onboarding data and calculated nutrition goals, provide personalized recommendations.

You will receive:
1. User's calculated nutrition data (BMR, TDEE, calorie goal, macros, etc.)
2. User's complete onboarding information (goals, challenges, preferences, lifestyle)

Your task is to provide ONLY personalized recommendations in the following areas:
- Meal distribution (breakfast, lunch, dinner, snacks) with calorie and macro breakdown
- Water intake recommendation
- Protein timing advice
- Meal prep suggestions (based on their lifestyle, work schedule, family situation)
- Activity recommendations (based on their stated activity plans and goals)
- Strategies to address their specific challenges (cravings, motivation, etc.)
- Weekend eating adjustments (if they indicated eating more on weekends)
- Weekly goals (weekday/weekend calorie split, step goals, tracking streak)
- Important safety notes and warnings

Provide detailed, personalized advice based on the user's specific situation, challenges, and goals."""


def call_gemini_for_recommendations(user_info, calculated_data):
    """Call Gemini LLM to get personalized recommendations with structured output"""
    try:
        # Create model with JSON mode
        model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            generation_config={
                'temperature': 0.3,
                'top_p': 0.95,
                'top_k': 40,
                'max_output_tokens': 4096,
            }
        )
        
        # Prepare context for LLM with explicit JSON schema
        schema_json = json.dumps(OUTPUT_SCHEMA, indent=2)
        context = f"""{PERSONALIZATION_PROMPT}

---

CALCULATED NUTRITION DATA:
{json.dumps(calculated_data, indent=2)}

USER ONBOARDING DATA:
{json.dumps(user_info['full_data'], indent=2)}

USER PROFILE:
- Name: {user_info['name']}
- Age: {user_info['age']}
- Gender: {user_info['gender']}
- Goal: {user_info['goal']}
- Diet Type: {user_info['diet_type']}

---

CRITICAL: You MUST return ONLY valid JSON matching this exact schema:

{schema_json}

Return ONLY the JSON object. No markdown, no code blocks, no explanatory text. Start with {{ and end with }}.
Ensure all required fields are present and match the specified types."""
        
        # Generate response with retry logic for JSON parsing
        max_retries = 2
        for attempt in range(max_retries):
            try:
                response = model.generate_content(context)
                result_text = response.text.strip()
                
                # Clean up response
                if result_text.startswith('```json'):
                    result_text = result_text[7:]
                elif result_text.startswith('```'):
                    result_text = result_text[3:]
                
                if result_text.endswith('```'):
                    result_text = result_text[:-3]
                
                result_text = result_text.strip()
                
                # Find JSON boundaries
                start_idx = result_text.find('{')
                end_idx = result_text.rfind('}')
                
                if start_idx != -1 and end_idx != -1:
                    result_text = result_text[start_idx:end_idx + 1]
                
                # Parse and validate JSON
                parsed_json = json.loads(result_text)
                
                # Validate required fields
                required_fields = ['meal_distribution', 'personalized_recommendations', 'weekly_goals', 'warnings_and_notes']
                missing = [f for f in required_fields if f not in parsed_json]
                
                if missing:
                    raise ValueError(f"Missing required fields: {missing}")
                
                return parsed_json
                
            except (json.JSONDecodeError, ValueError) as e:
                if attempt < max_retries - 1:
                    print(f"JSON parse/validation error on attempt {attempt + 1}, retrying...")
                    continue
                else:
                    print(f"Failed to get valid JSON after {max_retries} attempts: {str(e)}")
                    print(f"Raw response: {result_text[:500]}...")
                    raise Exception(f"Gemini API returned invalid JSON: {str(e)}")
        
    except Exception as e:
        raise Exception(f"Gemini API Error: {str(e)}")


@app.route('/')
def home():
    """API information endpoint"""
    return jsonify({
        'api': 'AI Nutrition Calculator',
        'version': '2.0',
        'description': 'YAZIO Calculator + Gemini AI Personalization',
        'endpoints': {
            '/health': 'GET - API health check',
            '/calculate-nutrition': 'POST - Calculate complete nutrition plan',
            '/calculate': 'POST - YAZIO calculator only (no AI)',
            '/activity-factors': 'GET - Get activity factor values'
        },
        'method': 'Mifflin-St. Jeor Equation + YAZIO Energy Difference Formula'
    })


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "AI Nutrition Calculator API",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    }), 200


@app.route('/activity-factors', methods=['GET'])
def get_activity_factors():
    """Get available activity factors"""
    return jsonify({
        'activity_factors': CalorieCalculator.ACTIVITY_FACTORS,
        'new_user_factors': CalorieCalculator.NEW_USER_FACTORS,
        'description': {
            'low/sedentary': 'Little or no exercise, desk job (1.25)',
            'moderate/moderately active': 'Moderate exercise 3-5 days/week (1.38)',
            'high/very active': 'Hard exercise 6-7 days/week (1.52)',
            'very_high/extremely active': 'Physical job + hard exercise daily (1.65)'
        }
    })


@app.route('/calculate', methods=['POST'])
def calculate_only():
    """
    YAZIO calculator endpoint (no AI personalization)
    
    Required fields:
    - weight_kg, height_cm, age, gender
    - activity_level, starting_weight, goal_weight, weekly_goal
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required = ['weight_kg', 'height_cm', 'age', 'gender', 'activity_level',
                   'starting_weight', 'goal_weight', 'weekly_goal']
        missing = [field for field in required if field not in data]
        
        if missing:
            return jsonify({
                'error': f'Missing required fields: {", ".join(missing)}'
            }), 400
        
        # Calculate calorie goal
        result = CalorieCalculator.calculate_calorie_goal(
            weight_kg=float(data['weight_kg']),
            height_cm=float(data['height_cm']),
            age=int(data['age']),
            gender=data['gender'],
            activity_level=data['activity_level'],
            starting_weight=float(data['starting_weight']),
            goal_weight=float(data['goal_weight']),
            weekly_goal=float(data['weekly_goal']),
            is_new_user=data.get('is_new_user', False)
        )
        
        # Calculate macros
        macros = CalorieCalculator.calculate_macros(
            calorie_goal=result['daily_calorie_goal'],
            carb_percent=data.get('carb_percent', 50),
            protein_percent=data.get('protein_percent', 20),
            fat_percent=data.get('fat_percent', 30)
        )
        
        # Calculate timeline
        timeline = calculate_timeline(result['weight_difference'], data['weekly_goal'])
        
        return jsonify({
            'success': True,
            'calculation': result,
            'macronutrients': macros,
            'timeline': timeline,
            'method': 'YAZIO - Mifflin-St. Jeor Equation',
            'timestamp': datetime.now().isoformat()
        })
        
    except ValueError as e:
        return jsonify({'error': f'Invalid input values: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/calculate-nutrition', methods=['POST'])
def calculate_nutrition():
    """
    Main endpoint: YAZIO Calculator + Gemini AI Personalization
    
    Accepts onboarding data in your app's format
    Returns complete nutrition plan with AI-powered recommendations
    """
    try:
        # Get request data
        request_data = request.get_json()
        
        if not request_data:
            return jsonify({
                "success": False,
                "error": "No data provided"
            }), 400
        
        # Extract user data - handle both direct object and array format
        if isinstance(request_data, dict) and 'data' in request_data:
            if isinstance(request_data['data'], list) and len(request_data['data']) > 0:
                user_data = request_data['data'][0]
            else:
                user_data = request_data
        else:
            user_data = request_data
        
        # Step 1: Extract and normalize user information
        user_info = extract_user_info(user_data)
        
        # Step 2: Calculate using YAZIO methodology
        calc_result = CalorieCalculator.calculate_calorie_goal(
            weight_kg=user_info['current_weight'],
            height_cm=user_info['height_cm'],
            age=user_info['age'],
            gender=user_info['gender'],
            activity_level=user_info['activity_level'],
            starting_weight=user_info['starting_weight'],
            goal_weight=user_info['goal_weight'],
            weekly_goal=user_info['weekly_goal']
        )
        
        # Step 3: Calculate macronutrients
        macros = CalorieCalculator.calculate_macros(
            calorie_goal=calc_result['daily_calorie_goal'],
            carb_percent=50,
            protein_percent=20,
            fat_percent=30
        )
        
        # Step 4: Calculate timeline
        timeline = calculate_timeline(
            calc_result['weight_difference'],
            user_info['weekly_goal']
        )
        
        # Step 5: Prepare calculated data for response
        calculated_data = {
            'user_profile': {
                'name': user_info['name'],
                'age': user_info['age'],
                'sex': user_info['gender'].capitalize(),
                'height_cm': user_info['height_cm'],
                'height_ft_in': user_info['height_ft_in'],
                'current_weight_kg': user_info['current_weight'],
                'goal_weight_kg': user_info['goal_weight'],
                'weight_to_lose_kg': abs(calc_result['weight_difference']),
                'goal': user_info['goal']
            },
            'body_metrics': {
                'current_bmi': {
                    'value': calc_result['current_bmi'],
                    'category': get_bmi_category(calc_result['current_bmi'])
                },
                'goal_bmi': {
                    'value': calc_result['goal_bmi'],
                    'category': get_bmi_category(calc_result['goal_bmi'])
                }
            },
            'calorie_calculation': {
                'bmr': int(calc_result['bmr']),
                'activity_level': user_info['activity_level'].title(),
                'activity_factor': calc_result['activity_factor'],
                'tdee': int(calc_result['tdee']),
                'daily_calorie_goal': int(calc_result['daily_calorie_goal']),
                'calorie_deficit': int(abs(calc_result['energy_difference'])),
                'expected_weekly_loss_kg': abs(user_info['weekly_goal'])
            },
            'macronutrients': {
                **macros,
                'diet_type': user_info['diet_type']
            },
            'timeline': timeline
        }
        
        # Step 6: Get AI-powered personalized recommendations
        try:
            ai_recommendations = call_gemini_for_recommendations(user_info, calculated_data)
            
            # Merge AI recommendations with calculated data
            final_result = {
                **calculated_data,
                **ai_recommendations
            }
        except Exception as e:
            print(f"AI recommendation error: {str(e)}")
            # Fallback: return calculated data without AI recommendations
            final_result = {
                **calculated_data,
                'meal_distribution': {
                    'breakfast': {'calories': int(calc_result['daily_calorie_goal'] * 0.25), 'protein_g': 0, 'carbs_g': 0, 'fats_g': 0},
                    'lunch': {'calories': int(calc_result['daily_calorie_goal'] * 0.35), 'protein_g': 0, 'carbs_g': 0, 'fats_g': 0},
                    'dinner': {'calories': int(calc_result['daily_calorie_goal'] * 0.30), 'protein_g': 0, 'carbs_g': 0, 'fats_g': 0},
                    'snacks': {'calories': int(calc_result['daily_calorie_goal'] * 0.10), 'protein_g': 0, 'carbs_g': 0, 'fats_g': 0}
                },
                'personalized_recommendations': {
                    'water_intake_liters': 2.0,
                    'protein_timing': 'Distribute protein evenly across meals',
                    'meal_prep_suggestions': ['Plan meals in advance', 'Prepare healthy snacks'],
                    'activity_recommendations': ['Stay active', 'Track your progress'],
                    'key_challenges_addressed': ['Stay consistent', 'Track your meals']
                },
                'weekly_goals': {
                    'weekday_calories': int(calc_result['daily_calorie_goal']),
                    'weekend_calories': int(calc_result['daily_calorie_goal']),
                    'step_goal': 8000,
                    'tracking_streak_goal': '30 days'
                },
                'warnings_and_notes': ['Consult a healthcare professional before starting any diet plan']
            }
        
        # Return successful response
        return jsonify({
            "success": True,
            "data": final_result,
            "metadata": {
                "processed_at": datetime.now().isoformat(),
                "api_version": "2.0.0",
                "calculation_method": "YAZIO (Mifflin-St. Jeor + Energy Difference)",
                "personalization": "Gemini AI"
            }
        }), 200
        
    except json.JSONDecodeError:
        return jsonify({
            "success": False,
            "error": "Invalid JSON format in request body"
        }), 400
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 Starting AI Nutrition Calculator API")
    print("="*70)
    print("\n📊 Calculation Method:")
    print("   - BMR: Mifflin-St. Jeor Equation")
    print("   - Energy Difference: YAZIO Formula (Weekly Goal × 750)")
    print("   - Personalization: Gemini 2.5 Flash AI")
    print("\n📝 Available endpoints:")
    print("   - GET  /                      - API information")
    print("   - GET  /health                - Health check")
    print("   - GET  /activity-factors      - View activity factors")
    print("   - POST /calculate             - YAZIO calculator only")
    print("   - POST /calculate-nutrition   - Full AI-powered nutrition plan")
    print("\n💡 API Key Status:", "✅ Configured" if GEMINI_API_KEY else "❌ Missing")
    print("\n🌐 Server running on: http://localhost:5000")
    print("="*70 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
