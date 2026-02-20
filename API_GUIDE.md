# API Guide for Web Developer

## Quick Start
```bash
# Start server
uvicorn app.main:app --reload
# API Base URL: http://localhost:8000/api/v1
# Interactive docs: http://localhost:8000/docs
```

---

## 1. AI Suggest Company Details

### `POST /api/v1/suggest-company-details`

**Purpose:** Generate company details when user can't think what to write.

**Request:**
```json
{
  "company_name": "บริษัท ABC จำกัด",
  "brief_description": "บริษัทเทคโนโลยีขนาดกลาง",
  "partial_requirements": "ต้องการวิศวกรซอฟต์แวร์"
}
```

**Response:**
```json
{
  "company_name": "บริษัท ABC จำกัด",
  "suggested_requirements": "ต้องการวิศวกรซอฟต์แวร์ที่มีประสบการณ์ Python, SQL, Git และการทำงานเป็นทีม",
  "suggested_culture": "วัฒนธรรมองค์กรที่เน้นการเรียนรู้ นวัตกรรม และความยืดหยุ่นในการทำงาน",
  "suggested_desired_traits": "มีความรับผิดชอบ สื่อสารดี ชอบแก้ปัญหา และทำงานภายใต้แรงกดดันได้",
  "message": "Generated suggestions for 'บริษัท ABC จำกัด'"
}
```

**Use Case:** User clicks "AI Suggest" button → fill form with these suggestions.

---

## 2. AI Analyze & Group CLOs

### `POST /api/v1/analyze-company-grouped`

**Purpose:** AI reads company details + pre-filtered CLOs, then groups and selects relevant ones.

**Important:** Web MUST send pre-filtered CLOs. AI will NOT search all 10,000+ CLOs.

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

**Response:**
```json
{
  "company_name": "บริษัท ABC จำกัด",
  "requirements": "ต้องการวิศวกรซอฟต์แวร์...",
  "groups": [
    {
      "group_id": "grp_1",
      "group_name": "ทักษะการสื่อสารและการทำงานร่วมกัน",
      "summary": "CLO ที่เน้นการสื่อสารและทีมเวิร์ค",
      "evidence": ["ต้องการการทำงานเป็นทีม", "สื่อสารดี"],
      "suggested_clos": ["11281", "11282"],
      "selected_clos": ["11281", "11282"],
      "reasoning": "CLO เหล่านี้เน้นทักษะการสื่อสารและการทำงานร่วมกัน"
    },
    {
      "group_id": "grp_2",
      "group_name": "ทักษะเทคนิคและการวิเคราะห์",
      "summary": "CLO ที่เกี่ยวข้องกับการวิเคราะห์และทักษะด้านเทคนิค",
      "evidence": ["Python", "SQL", "วิเคราะห์"],
      "suggested_clos": ["456", "789"],
      "selected_clos": ["456", "789"],
      "reasoning": "CLO เหล่านี้เน้นทักษะการวิเคราะห์และความเชี่ยวชาญด้านเทคนิค"
    },
    {
      "group_id": "grp_3",
      "group_name": "คุณธรรมและจริยธรรม",
      "summary": "CLO ที่เกี่ยวกับความซื่อสัตย์และความรับผิดชอบ",
      "evidence": ["ซื่อสัตย์", "รับผิดชอบ"],
      "suggested_clos": ["1011"],
      "selected_clos": ["1011"],
      "reasoning": "CLO เหล่านี้เน้นคุณธรรมและจริยธรรมในการทำงาน"
    }
  ],
  "all_suggested_clos": ["11281", "11282", "456", "789", "1011"],
  "all_selected_clos": ["11281", "11282", "456", "789", "1011"],
  "clo_plo_mappings": [
    {"clo_id": "11281", "plo_id": "653", "curriculum_id": "70", "course_id": "1621", "is_map": true}
  ],
  "mapped_plos": [
    {
      "id": "653",
      "curriculum_id": "70",
      "name": "1",
      "detail": "มีความซื่อสัตย์ มีวินัย ตรงต่อเวลา",
      "plo_level": "1"
    }
  ],
  "message": "Found 3 groups with 3 suggested CLOs"
}
```

**Use Case:** User clicks "AI Analyze" → show grouped CLOs → user can edit selection.

---

## Web Flow Example

```javascript
// Step 1: Load all CLOs for UI
const allClos = await fetch('/api/v1/clos').then(r => r.json());

// Step 2: User filters/selects CLOs in UI
const selectedClos = allClos.clos.filter(clo => userSelected(clo));

// Step 3: AI analyze
const analysis = await fetch('/api/v1/analyze-company-grouped', {
  method: 'POST',
  body: JSON.stringify({
    company_name: formData.company_name,
    requirements: formData.requirements,
    culture: formData.culture,
    desired_traits: formData.desired_traits,
    clos: selectedClos  // Send pre-filtered CLOs!
  })
});

// Step 4: Display groups, let user edit, then submit final CLOs
```

---

## Important Notes

- **Always send `clos` array** to `analyze-company-grouped`
- **CLO objects must include**: `id`, `description`, `curriculum_id`, `course_id`
- **Response includes**: AI groups + CLO→PLO mappings + PLO details
- **Processing time:** 5-20 seconds (AI analysis)
- **Rate limit:** None, but be reasonable with OpenAI costs
