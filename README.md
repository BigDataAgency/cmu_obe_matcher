# Company-CLO Matcher

An AI-powered system that matches companies to relevant Course Learning Outcomes (CLOs) based on their requirements, culture, and desired traits.

## Features

- **AI-Powered Analysis**: Uses OpenAI GPT-4o-mini or Google Gemini to analyze company details and suggest relevant CLOs
- **Flexible LLM Provider**: Switch between OpenAI and Gemini (free tier available)
- **Interactive CLO Selection**: Users can add or remove CLOs from AI suggestions
- **Company Management**: Full CRUD operations for company profiles
- **Modern Web Interface**: Clean, responsive UI for easy interaction
- **RESTful API**: Well-documented API endpoints

## Project Structure

```
cmu_obe_matcher/
├── app/
│   ├── main.py                    # FastAPI application entry point
│   ├── models.py                  # Pydantic models for validation
│   ├── config.py                  # Configuration and environment variables
│   ├── services/
│   │   ├── openai_service.py     # OpenAI integration for CLO suggestion
│   │   ├── gemini_service.py     # Google Gemini integration for CLO suggestion
│   │   └── llm_factory.py        # Factory to select LLM provider
│   └── api/
│       └── endpoints.py           # API route handlers
├── data/
│   └── clo_definitions.json       # CLO definitions (15 CLOs)
├── static/
│   ├── index.html                 # Frontend HTML
│   ├── styles.css                 # CSS styling
│   └── app.js                     # JavaScript for API interaction
├── requirements.txt               # Python dependencies
├── .env.example                   # Example environment variables
└── README.md                      # This file
```

## Setup Instructions

### 1. Clone the Repository

```bash
cd cmu_obe_matcher
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and configure your preferred LLM provider:

#### Option A: Using Gemini (Free)

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-1.5-flash
```

Get your free Gemini API key from: https://aistudio.google.com/app/apikey

#### Option B: Using OpenAI

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-actual-api-key-here
OPENAI_MODEL=gpt-4o-mini
```

### 5. Run the Application

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The application will be available at `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## API Endpoints

### 1. Get All CLOs

**GET** `/api/v1/clos`

Returns all available Course Learning Outcomes.

**Response:**
```json
{
  "clos": [
    {
      "id": "CLO01",
      "name": "Python Programming",
      "description": "Proficiency in Python programming..."
    },
    ...
  ],
  "total": 15
}
```

### 2. Analyze Company (Grouped)

**POST** `/api/v1/analyze-company-grouped`

Analyzes company details and suggests relevant CLOs using AI.

**Request Body:**
```json
{
  "company_name": "Tech Startup Inc",
  "requirements": "Looking for graduates with strong programming skills...",
  "culture": "Fast-paced, innovative environment",
  "desired_traits": "Problem solvers, team players"
}
```

**Response:**
```json
{
  "company_name": "Tech Startup Inc",
  "requirements": "Looking for graduates with strong programming skills...",
  "culture": "Fast-paced, innovative environment",
  "desired_traits": "Problem solvers, team players",
  "ai_suggested_clos": ["CLO01", "CLO02", "CLO05", "CLO10"],
  "ai_reasoning": "Based on the requirements, CLO01 (Python) is essential...",
  "message": "Successfully analyzed company details for Tech Startup Inc"
}
```

### 3. List All Companies

**GET** `/api/v1/companies`

Returns all company profiles.

**Response:**
```json
{
  "companies": [
    {
      "company_name": "Tech Startup Inc",
      "requirements": "...",
      "culture": "...",
      "desired_traits": "...",
      "ai_suggested_clos": ["CLO01", "CLO02"],
      "selected_clos": ["CLO01", "CLO02", "CLO03"],
      "ai_reasoning": "...",
      "created_at": "2026-02-06T08:36:00Z",
      "updated_at": "2026-02-06T09:15:00Z"
    }
  ],
  "total": 1
}
```

### 4. Get Company Details

**GET** `/api/v1/companies/{company_name}`

Returns details for a specific company.

### 5. Update Company Groups

**PUT** `/api/v1/companies/{company_name}/groups`

Updates the selected groups for a company.

**Request Body:**
```json
{
  "selected_groups": ["Group A", "Group B"]
}
```

### 6. Delete Company

**DELETE** `/api/v1/companies/{company_name}`

Deletes a company profile.

## Usage Example

### Using the Web Interface

1. Navigate to `http://localhost:8000`
2. Click "➕ Add Company"
3. Fill in company details (name, requirements, culture, traits)
4. Click "🔍 Analyze with AI"
5. Review AI-suggested CLOs
6. Add or remove CLOs as needed
7. Click "💾 Save Company"
8. View all companies in the "🏢 Companies" tab

### Using cURL

```bash
# Analyze a company (grouped)
curl -X POST "http://localhost:8000/api/v1/analyze-company-grouped" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Tech Startup",
    "requirements": "Python, data analysis, SQL",
    "culture": "Fast-paced, collaborative",
    "desired_traits": "Problem solving, communication"
  }'
```

## CLO Definitions

The system uses 15 Course Learning Outcomes (CLOs):

1. **CLO01**: Python Programming
2. **CLO02**: Data Analysis
3. **CLO03**: Teamwork
4. **CLO04**: Communication
5. **CLO05**: Problem Solving
6. **CLO06**: Database Management
7. **CLO07**: Machine Learning
8. **CLO08**: Web Development
9. **CLO09**: Cloud Computing
10. **CLO10**: Software Engineering
11. **CLO11**: Business Analytics
12. **CLO12**: Project Management
13. **CLO13**: Data Visualization
14. **CLO14**: Research Skills
15. **CLO15**: Ethics and Professionalism

## How It Works

1. **Company Analysis**: User inputs company details (requirements, culture, desired traits)
2. **AI Processing**: OpenAI or Gemini analyzes the details and identifies relevant CLOs
3. **User Refinement**: User can add or remove CLOs from AI suggestions
4. **Storage**: Company profile with selected CLOs is stored in memory

## LLM Provider Selection

The system supports two LLM providers:

- **Gemini (Recommended for Free Tier)**: Google's Gemini 1.5 Flash offers free API access with generous quotas
- **OpenAI**: GPT-4o-mini provides high-quality analysis (paid API)

Switch between providers by changing `LLM_PROVIDER` in your `.env` file. Both providers use the same interface, so no code changes are needed.

## Technical Stack

- **FastAPI**: Modern web framework for building APIs
- **OpenAI / Gemini**: GPT-4o-mini or Gemini 1.5 Flash for intelligent company analysis
- **Pydantic**: Data validation using Python type annotations
- **Uvicorn**: ASGI server for running FastAPI
- **Vanilla JavaScript**: Frontend interaction without heavy frameworks

## Development

### Running in Development Mode

```bash
uvicorn app.main:app --reload
```

### Code Style

The project follows PEP 8 guidelines.

## Notes

- Company data is stored in-memory and will be lost when the server restarts
- For production use, consider implementing database persistence
- Either OpenAI or Gemini API key is required for the system to function
- Gemini offers a free tier, making it ideal for development and testing

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
