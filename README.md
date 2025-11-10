# 🥗 AI Calorie Calculator API

A comprehensive nutrition calculator API powered by Google Gemini AI that analyzes user onboarding data and provides personalized nutritional recommendations, calorie goals, macronutrient distributions, and meal planning.

## ✨ Features

- **Personalized Nutrition Calculations**: BMR, TDEE, and daily calorie goals based on user data
- **Macronutrient Distribution**: Optimized protein, carbs, and fats ratios
- **Meal Planning**: Breakfast, lunch, dinner, and snack calorie allocations
- **BMI Tracking**: Current and goal BMI calculations
- **Timeline Estimation**: Realistic goal achievement dates
- **Dietary Preferences**: Support for Classic, Keto, Vegetarian, and other diets
- **Batch Processing**: Calculate nutrition for multiple users at once
- **Google Gemini AI Integration**: Advanced AI-powered nutritional analysis

## 📋 Prerequisites

- Python 3.8 or higher
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

## 🚀 Quick Start

### 1. Clone or Download the Project

```bash
cd AI-calorie-calc
```

### 2. Run Setup Script

**Windows:**
```bash
setup.bat
```

This will:
- Create a virtual environment
- Install all dependencies
- Create a `.env` file from `.env.example`

### 3. Configure API Key

Edit the `.env` file and add your Gemini API key:

```env
GEMINI_API_KEY=your-actual-api-key-here
```

### 4. Start the Server

**Windows:**
```bash
start.bat
```

The API will be available at `http://localhost:5000`

## 🔧 Manual Setup (Alternative)

If you prefer to set up manually:

### 1. Create Virtual Environment

```bash
python -m venv venv
```

### 2. Activate Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
copy .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 5. Run the Application

```bash
python main.py
```

## 📡 API Endpoints

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "Nutrition Calculator API",
  "version": "1.0.0"
}
```

### Calculate Nutrition (Single User)
```http
POST /calculate-nutrition
Content-Type: application/json
```

**Request Body:**
```json
{
  "data": [
    {
      "id": 19,
      "data": {
        "Goal": "Lose weight",
        "Height (cm)": 165.1,
        "Current Weight": "65 kg",
        "Goal Weight": "60 kg",
        "Birthday": {
          "day": 15,
          "month": 5,
          "year": 1990
        },
        "Sex": "Female",
        "Activity Level": "Moderately Active",
        "Diet Type": "Classic"
      },
      "user": {
        "firstName": "Jane",
        "lastName": "Doe"
      }
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "user_profile": { ... },
    "body_metrics": { ... },
    "calorie_calculation": { ... },
    "macronutrients": { ... },
    "meal_distribution": { ... },
    "timeline": { ... },
    "personalized_recommendations": { ... }
  },
  "metadata": {
    "processed_at": "2025-11-06T15:30:00",
    "api_version": "1.0.0"
  }
}
```

### Calculate Nutrition (Batch)
```http
POST /calculate-nutrition/batch
Content-Type: application/json
```

**Request Body:**
```json
{
  "users": [
    { "data": { ... }, "user": { ... } },
    { "data": { ... }, "user": { ... } }
  ]
}
```

## 🧪 Testing the API

### Using cURL

```bash
# Health check
curl http://localhost:5000/health

# Calculate nutrition
curl -X POST http://localhost:5000/calculate-nutrition \
  -H "Content-Type: application/json" \
  -d @sample-request.json
```

### Using Python

```python
import requests

url = "http://localhost:5000/calculate-nutrition"
data = {
    "data": [{
        "data": {
            "Goal": "Lose weight",
            "Height (cm)": 170,
            "Current Weight": "75 kg",
            "Goal Weight": "70 kg",
            "Sex": "Male",
            "Birthday": {"day": 1, "month": 1, "year": 1995},
            "Activity Level": "Moderately Active"
        }
    }]
}

response = requests.post(url, json=data)
print(response.json())
```

### Using Postman

1. Create a new POST request to `http://localhost:5000/calculate-nutrition`
2. Set Headers: `Content-Type: application/json`
3. Add your JSON data in the Body (raw)
4. Click Send

## 📦 Project Structure

```
AI-calorie-calc/
├── main.py              # Main Flask application with Gemini integration
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variables template
├── .env                # Your actual API keys (not in git)
├── .gitignore          # Git ignore rules
├── setup.bat           # Windows setup script
├── start.bat           # Windows start script
└── README.md           # This file
```

## 🔑 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Your Google Gemini API key | Yes |

## 🛠️ Technology Stack

- **Framework**: Flask 3.0.0
- **AI Model**: Google Gemini 1.5 Pro
- **Python**: 3.8+
- **Libraries**:
  - `google-generativeai` - Gemini API client
  - `python-dotenv` - Environment variable management
  - `flask` - Web framework

## 📊 Calculation Methodology

The API uses scientifically-backed formulas:

- **BMR**: Mifflin-St. Jeor Equation
- **TDEE**: BMR × Activity Factor
- **Calorie Goals**: Based on weight loss/gain targets
- **Macros**: Evidence-based ratios optimized for goals
- **Safety Limits**: Enforced minimum/maximum calorie intake

## 🔒 Security Best Practices

✅ **Implemented:**
- Environment variables for API keys
- `.gitignore` to prevent committing secrets
- Virtual environment isolation

⚠️ **Recommendations for Production:**
- Use HTTPS
- Add rate limiting
- Implement authentication
- Add input validation
- Use production WSGI server (Gunicorn/uWSGI)
- Set up logging and monitoring

## 🐛 Troubleshooting

### "GEMINI_API_KEY not found"
- Make sure `.env` file exists in the project root
- Verify the API key is set correctly in `.env`
- Restart the server after updating `.env`

### "Module not found" errors
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt` again

### API returns errors
- Check your Gemini API key is valid
- Verify you have API quota remaining
- Check the request format matches the documentation

### Virtual environment issues
- Delete the `venv` folder and run `setup.bat` again
- Ensure Python 3.8+ is installed

## 📝 License

This project is provided as-is for educational and development purposes.

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📧 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the API documentation
3. Check Gemini API status

---

**Made with ❤️ using Google Gemini AI**
