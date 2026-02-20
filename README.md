# Company-CLO Matcher API

REST API for matching company job requirements to **Course Learning Outcomes (CLOs)** and **Program Learning Outcomes (PLOs)**.

---

## User Flow Overview

```
┌─────────────────────────────────────────────────────────┐
│  STEP 1: Fill Company Details                           │
│                                                         │
│  User types company name, requirements, culture,        │
│  desired traits manually                                │
│                                                         │
│  ── OR ──                                               │
│                                                         │
│  User presses [AI Suggest] button                       │
│  → Call POST /api/v1/suggest-company-details            │
│  → AI fills in requirements, culture, desired_traits    │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  STEP 2: Match CLOs                                     │
│                                                         │
│  User picks CLOs manually from the CLO list             │
│  → Call GET /api/v1/clos  (to populate CLO list)        │
│                                                         │
│  ── OR ──                                               │
│                                                         │
│  User presses [AI Analyze] button                       │
│  → Call POST /api/v1/analyze-company-grouped            │
│  → AI suggests CLOs grouped by category                 │
│  → User can edit/confirm the suggestions                │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  STEP 3: Submit → Get PLO Mappings                      │
│                                                         │
│  User confirms final CLO selection                      │
│  → Call POST /api/v1/submit-company-with-clos           │
│  → API returns CLO→PLO mappings + PLO details           │
└─────────────────────────────────────────────────────────┘
```

---

## Quick Start

### 1. Requirements
- Python 3.10+
- OpenAI API Key

### 2. Setup

```bash
cd cmu_obe_matcher

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env → set OPENAI_API_KEY
```

### 3. .env file
```
OPENAI_API_KEY=sk-...your-key-here...
OPENAI_MODEL=gpt-4.1-mini
```

### 4. Run
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Interactive Docs
- Swagger UI: **http://localhost:8000/docs**
- ReDoc: **http://localhost:8000/redoc**

---

## All Endpoints

| Method | Path | When to call |
|--------|------|-------------|
| POST | `/api/v1/suggest-company-details` | Step 1 — User presses [AI Suggest] button |
| GET | `/api/v1/clos` | Step 2 — Load CLO list for user to pick from |
| POST | `/api/v1/analyze-company-grouped` | Step 2 — User presses [AI Analyze] button |
| POST | `/api/v1/submit-company-with-clos` | Step 3 — User submits final CLO selection |
| GET | `/api/v1/companies` | Extra — List all saved companies |
| GET | `/api/v1/companies/{company_name}` | Extra — Get one saved company |
| DELETE | `/api/v1/companies/{company_name}` | Extra — Delete a company |

---

## Step 1 — AI Suggest Company Details

### POST `/api/v1/suggest-company-details`

Call when user presses **[AI Suggest]** button. AI generates requirements, culture, and desired traits based on company name.

**Request:**
```json
{
  "company_name": "บริษัท ABC จำกัด",
  "brief_description": "บริษัท IT ด้าน fintech สัญชาติไทย",
  "partial_requirements": "ต้องการโปรแกรมเมอร์..."
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `company_name` | ✅ | Company name |
| `brief_description` | ❌ | Short hint about the company (industry, size, etc.) |
| `partial_requirements` | ❌ | What the user has already typed (AI will continue from here) |

**Response:**
```json
{
  "company_name": "บริษัท ABC จำกัด",
  "suggested_requirements": "ต้องการวิศวกรซอฟต์แวร์ที่มีทักษะ Python, SQL, REST API และมีประสบการณ์ด้าน fintech อย่างน้อย 1 ปี",
  "suggested_culture": "วัฒนธรรมองค์กรที่เน้นการเรียนรู้ต่อเนื่อง ทำงานแบบ agile และให้ความสำคัญกับ work-life balance",
  "suggested_desired_traits": "มีความรับผิดชอบสูง สื่อสารได้ดี ทำงานเป็นทีมได้ และสามารถทำงานภายใต้แรงกดดันได้",
  "message": "Successfully generated suggestions for บริษัท ABC จำกัด"
}
```

> ⚠️ Calls OpenAI — takes ~5 seconds.

---

## Step 2A — Load CLO List (for manual selection)

### GET `/api/v1/clos`

Call once when the page loads to populate the CLO picker/dropdown.

**Response:**
```json
{
  "clos": [
    {
      "id": "11307",
      "no": "27",
      "name": "CLO 27",
      "description": "สามารถทำงานร่วมกับผู้อื่นได้อย่างมีประสิทธิภาพ",
      "curriculum_id": "70",
      "course_id": "1621"
    },
    {
      "id": "11308",
      "no": "28",
      "name": "CLO 28",
      "description": "สามารถสื่อสารได้หลากหลายรูปแบบอย่างเหมาะสมและมีประสิทธิภาพ",
      "curriculum_id": "70",
      "course_id": "1621"
    }
  ],
  "total": 12000
}
```

> Store the full CLO list on the frontend. When user selects CLOs, keep the full CLO objects (not just IDs) — you'll need them for Step 3.

---

## Step 2B — AI Analyze (suggest CLOs automatically)

### POST `/api/v1/analyze-company-grouped`

Call when user presses **[AI Analyze]** button. Web sends company details **+ pre-filtered CLO objects**. AI groups and selects the most relevant ones.

**Request:**
```json
{
  "company_name": "บริษัท ABC จำกัด",
  "requirements": "ต้องการวิศวกรซอฟต์แวร์ที่มีทักษะ Python, SQL และการทำงานเป็นทีม",
  "culture": "วัฒนธรรมองค์กรที่เน้นการเรียนรู้และนวัตกรรม",
  "desired_traits": "มีความรับผิดชอบ สื่อสารดี ทำงานภายใต้แรงกดดันได้",
  "clos": [
    {
      "id": "11281",
      "no": "1",
      "description": "มีความซื่อสัตย์ มีวินัย ตรงต่อเวลา",
      "curriculum_id": "70",
      "course_id": "1621"
    },
    {
      "id": "11282",
      "no": "2",
      "description": "มีความรับผิดชอบต่อตนเองและสังคม",
      "curriculum_id": "70",
      "course_id": "1621"
    },
    {
      "id": "456",
      "no": "1",
      "description": "analyze the concepts and principles related to healthcare quality",
      "curriculum_id": "48",
      "course_id": "174"
    }
  ]
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `company_name` | ✅ | Company name |
| `requirements` | ✅ | Job requirements (from Step 1) |
| `culture` | ❌ | Company culture (from Step 1) |
| `desired_traits` | ❌ | Desired traits (from Step 1) |
| `clos` | ✅ | Pre-filtered CLO objects from the web — AI will only consider these |
| `clos[].id` | ✅ | CLO ID |
| `clos[].no` | ❌ | CLO number within course |
| `clos[].description` | ✅ | CLO description |
| `clos[].curriculum_id` | ❌ | Curriculum ID |
| `clos[].course_id` | ❌ | Course ID |

> **How pre-filtering works:** The web fetches all CLOs via `GET /clos`, applies its own filter (e.g. by keyword, curriculum, or user selection), then sends only the relevant subset to this endpoint. The AI then groups and ranks within that subset — much faster and more accurate than searching all 10,000+ CLOs.

**Response:**
```json
{
  "company_name": "บริษัท ABC จำกัด",
  "requirements": "ต้องการวิศวกรซอฟต์แวร์...",
  "culture": "วัฒนธรรมองค์กร...",
  "desired_traits": "มีความรับผิดชอบ...",
  "groups": [
    {
      "group_id": "grp_1",
      "group_name": "ทักษะการสื่อสารและการทำงานร่วมกัน",
      "summary": "CLO ที่เน้นการสื่อสารและทีมเวิร์ค",
      "evidence": ["ต้องการการทำงานเป็นทีม", "สื่อสารดี"],
      "suggested_clos": ["11307", "11308"],
      "selected_clos": ["11307", "11308"],
      "reasoning": "CLO เหล่านี้เน้นทักษะการสื่อสารและการทำงานร่วมกัน"
    },
    {
      "group_id": "grp_2",
      "group_name": "ทักษะเทคนิคและการวิเคราะห์",
      "summary": "CLO ที่เน้นทักษะด้านเทคนิค",
      "evidence": ["Python", "SQL"],
      "suggested_clos": ["456", "457"],
      "selected_clos": ["456", "457"],
      "reasoning": "CLO เหล่านี้เน้นการวิเคราะห์และทักษะเทคนิค"
    }
  ],
  "all_suggested_clos": ["11307", "11308", "456", "457"],
  "all_selected_clos": ["11307", "11308", "456", "457"],
  "clo_context": [
    { "clo_id": "11307", "curriculum_id": 70, "course_id": 1621 }
  ],
  "clo_plo_mappings": [
    { "clo_id": "11307", "plo_id": "246", "curriculum_id": "70", "course_id": "1621", "is_map": true }
  ],
  "mapped_plos": [
    {
      "id": "246",
      "curriculum_id": "70",
      "name": "plo1",
      "name_en": null,
      "detail": "Read and Understand Relevant Information and Data",
      "plo_level": "1",
      "parent_plo_id": null
    }
  ],
  "message": "Successfully analyzed..."
}
```

**What to do with this response:**
- Show `groups` to the user — let them review/edit which CLOs to keep
- Each group has `group_name`, `reasoning`, and `selected_clos`
- User can add/remove CLOs from each group
- When user confirms → go to Step 3 with the final CLO list

> ⚠️ Calls OpenAI — takes 5–20 seconds.

---

## Step 3 — Submit Final CLOs → Get PLO Mappings

### POST `/api/v1/submit-company-with-clos`

Call when user **confirms their final CLO selection** (whether picked manually or from AI suggestions). Returns PLO mappings — no AI call, fast response.

**Request:**
```json
{
  "company_name": "บริษัท ABC จำกัด",
  "requirements": "ต้องการวิศวกรซอฟต์แวร์ที่มีทักษะ Python, SQL และการทำงานเป็นทีม",
  "culture": "วัฒนธรรมองค์กรที่เน้นการเรียนรู้และนวัตกรรม",
  "desired_traits": "มีความรับผิดชอบ สื่อสารดี ทำงานภายใต้แรงกดดันได้",
  "clos": [
    {
      "id": "11307",
      "no": "27",
      "description": "สามารถทำงานร่วมกับผู้อื่นได้อย่างมีประสิทธิภาพ",
      "curriculum_id": "70",
      "course_id": "1621"
    },
    {
      "id": "11308",
      "no": "28",
      "description": "สามารถสื่อสารได้หลากหลายรูปแบบอย่างเหมาะสมและมีประสิทธิภาพ",
      "curriculum_id": "70",
      "course_id": "1621"
    },
    {
      "id": "456",
      "no": "1",
      "description": "analyze the concepts and principles related to healthcare quality",
      "curriculum_id": "48",
      "course_id": "174"
    }
  ]
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `company_name` | ✅ | Company name |
| `requirements` | ✅ | Job requirements |
| `culture` | ❌ | Company culture |
| `desired_traits` | ❌ | Desired traits |
| `clos` | ✅ | Final list of CLO objects user confirmed |
| `clos[].id` | ✅ | CLO ID |
| `clos[].no` | ❌ | CLO number (e.g. "27") |
| `clos[].description` | ✅ | CLO description |
| `clos[].curriculum_id` | ❌ | Curriculum ID |
| `clos[].course_id` | ❌ | Course ID |

**Response:**
```json
{
  "company_name": "บริษัท ABC จำกัด",
  "requirements": "ต้องการวิศวกรซอฟต์แวร์...",
  "culture": "วัฒนธรรมองค์กร...",
  "desired_traits": "มีความรับผิดชอบ...",
  "clos": [
    {
      "id": "11307",
      "no": "27",
      "description": "สามารถทำงานร่วมกับผู้อื่นได้อย่างมีประสิทธิภาพ",
      "curriculum_id": "70",
      "course_id": "1621"
    }
  ],
  "clo_plo_mappings": [
    { "clo_id": "11307", "plo_id": "246", "curriculum_id": "70", "course_id": "1621", "is_map": true },
    { "clo_id": "11307", "plo_id": "247", "curriculum_id": "70", "course_id": "1621", "is_map": true },
    { "clo_id": "11308", "plo_id": "246", "curriculum_id": "70", "course_id": "1621", "is_map": true },
    { "clo_id": "456",   "plo_id": "506", "curriculum_id": "48", "course_id": "174",  "is_map": true }
  ],
  "mapped_plos": [
    {
      "id": "246",
      "curriculum_id": "70",
      "name": "plo1",
      "name_en": null,
      "detail": "Read and Understand Relevant Information and Data",
      "plo_level": "1",
      "parent_plo_id": null
    },
    {
      "id": "247",
      "curriculum_id": "70",
      "name": "plo2",
      "name_en": null,
      "detail": "Analyze and Apply Knowledge to Solve Problems",
      "plo_level": "2",
      "parent_plo_id": "246"
    },
    {
      "id": "506",
      "curriculum_id": "48",
      "name": "plo1",
      "name_en": null,
      "detail": "Healthcare quality management principles",
      "plo_level": "1",
      "parent_plo_id": null
    }
  ],
  "message": "Received 3 CLOs for 'บริษัท ABC จำกัด'. Found 3 mapped PLOs via 4 mappings."
}
```

**How to use the response:**
```javascript
// Build CLO → PLOs lookup
const cloToPLOs = {};
data.clo_plo_mappings.forEach(mapping => {
  if (!cloToPLOs[mapping.clo_id]) cloToPLOs[mapping.clo_id] = [];
  const plo = data.mapped_plos.find(p => p.id === mapping.plo_id);
  if (plo) cloToPLOs[mapping.clo_id].push(plo);
});

// Get PLOs for a specific CLO
console.log(cloToPLOs["11307"]);
// → [{ id: "246", name: "plo1", plo_level: "1", ... }, { id: "247", plo_level: "2", ... }]

// Separate main PLOs (level 1) vs sub-PLOs (level 2)
const mainPLOs = data.mapped_plos.filter(p => p.plo_level === "1");
const subPLOs  = data.mapped_plos.filter(p => p.plo_level === "2");
```

> ✅ No AI call — fast response (< 1 second).

---

## Data Models Reference

### CLO Object
```typescript
{
  id: string            // CLO unique ID — use as key
  no: string | null     // CLO number within course — display this to users
  name: string | null   // "CLO {no}"
  description: string   // Full CLO description text
  curriculum_id: string | null
  course_id: string | null
}
```

### PLO Object
```typescript
{
  id: string               // PLO unique ID
  curriculum_id: string
  name: string             // e.g. "plo1", "plo2"
  name_en: string | null
  detail: string           // Full PLO description text
  plo_level: "1" | "2"    // "1" = main PLO, "2" = sub-PLO
  parent_plo_id: string | null  // set when plo_level = "2"
}
```

### CLO-PLO Mapping Object
```typescript
{
  clo_id: string      // CLO ID
  plo_id: string      // PLO ID linked to this CLO
  curriculum_id: string
  course_id: string
  is_map: true        // always true (pre-filtered)
}
```

---

## Notes

- **Data is in-memory** — restarting the server clears all saved companies.
- **CORS is open** (`*`) — restrict `allow_origins` in production.
- `submit-company-with-clos` is **fast** (no AI, just CSV lookup).
- `suggest-company-details` and `analyze-company-grouped` are **slow** (call OpenAI, 5–20 sec).

---

## Project Structure

```
cmu_obe_matcher/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Reads .env settings
│   ├── models.py            # All request/response schemas
│   ├── api/endpoints.py     # All API routes
│   └── services/
│       ├── csv_loader.py    # Loads CLO/PLO data from CSV files
│       ├── openai_service.py# OpenAI integration
│       └── llm_factory.py   # Returns OpenAI service instance
├── data/
│   ├── tlic_obe_public_clo.csv
│   ├── tlic_obe_public_plo.csv
│   ├── tlic_obe_public_clo_has_plos.csv
│   └── tlic_obe_public_course_curriculum.csv
├── .env                     # Your API keys (do not commit)
├── .env.example
├── requirements.txt
└── README.md
```
