# API Response Structure Documentation

## 📌 สำหรับทีมพัฒนา Frontend

เอกสารนี้อธิบายโครงสร้างข้อมูลที่ API คืนกลับมา สำหรับนำไปใช้แสดงผลบนหน้าเว็บ

---

## 1. POST `/analyze-company-grouped` - วิเคราะห์บริษัท

### Request Body
```json
{
  "company_name": "ชื่อบริษัท",
  "requirements": "ความต้องการของบริษัท",
  "culture": "วัฒนธรรมองค์กร (optional)",
  "desired_traits": "คุณสมบัติที่ต้องการ (optional)"
}
```

### Response Structure
```json
{
  "company_name": "ชื่อบริษัท",
  "requirements": "ความต้องการของบริษัท",
  "culture": "วัฒนธรรมองค์กร",
  "desired_traits": "คุณสมบัติที่ต้องการ",
  "ai_reasoning": "เหตุผลจาก AI ว่าทำไมเลือก CLO เหล่านี้",
  "groups": [
    {
      "group_id": "unique_group_id",
      "group_name": "ชื่อกลุ่ม",
      "group_reasoning": "เหตุผลของกลุ่มนี้",
      "selected_clos": ["11307", "11308", ...],  // CLO IDs ที่เลือก
      "suggested_clos": ["11305", "11306", ...]  // CLO IDs ที่แนะนำ
    }
  ],
  "selected_clos": ["11307", "11308", ...],  // CLO IDs ทั้งหมดที่เลือก (union)
  "ai_suggested_clos": ["11305", "11306", ...],  // CLO IDs ทั้งหมดที่แนะนำ
  "clo_context": [
    {
      "clo_id": "11307",
      "curriculum_id": "70",
      "course_id": "1621"
    }
  ],
  "clo_plo_mappings": [
    {
      "id": "15091",
      "curriculum_id": "70",
      "course_id": "1621",
      "clo_id": "11307",
      "plo_id": "246",
      "is_map": true
    }
  ],
  "mapped_plos": [
    {
      "id": "246",
      "curriculum_id": "70",
      "name": "plo1",
      "detail": "Read and Understand Relevant Information...",
      "plo_level": "1"  // "1" = PLO หลัก, "2" = PLO ย่อย
    }
  ],
  "created_at": "2026-02-17T04:51:00.000000Z",
  "updated_at": "2026-02-17T04:51:00.000000Z"
}
```

---

## 2. GET `/clos` - ดึงข้อมูล CLO ทั้งหมด

### Response Structure
```json
{
  "clos": [
    {
      "id": "11307",           // CLO ID (unique)
      "no": "27",              // CLO No. (ซ้ำได้ตาม course)
      "course_id": "1621",
      "curriculum_id": "70",
      "description": "สามารถทำงานร่วมกับผู้อื่นได้อย่างมีประสิทธิภาพ...",
      "category": "",
      "name": "11307"          // Default name (same as id)
    }
  ]
}
```

---

## 3. GET `/companies` - ดึงรายชื่อบริษัททั้งหมด

### Response Structure
```json
{
  "companies": [
    {
      "company_name": "ชื่อบริษัท",
      "requirements": "ความต้องการ",
      "culture": "วัฒนธรรม",
      "desired_traits": "คุณสมบัติ",
      "groups": [...],
      "selected_clos": ["11307", ...],
      "ai_suggested_clos": ["11305", ...],
      "clo_context": [...],
      "clo_plo_mappings": [...],
      "mapped_plos": [...],
      "created_at": "...",
      "updated_at": "..."
    }
  ]
}
```

---

## 4. PUT `/companies/{company_name}/groups` - อัปเดตกลุ่ม CLO

### Request Body
```json
{
  "groups": [
    {
      "group_id": "group_1",
      "group_name": "ชื่อกลุ่ม",
      "group_reasoning": "เหตุผล",
      "selected_clos": ["11307", "11308"],
      "suggested_clos": ["11305"]
    }
  ]
}
```

### Response
เหมือนกับ response ของ `/analyze-company-grouped`

---

## 📊 ตัวอย่างการใช้งาน

### ตัวอย่างที่ 1: แสดง CLO ในตาราง

```javascript
// ดึงข้อมูล CLO ทั้งหมด
const closResponse = await fetch('/api/clos');
const { clos } = await closResponse.json();

// แสดง CLO No., Curriculum ID, Course ID
clos.forEach(clo => {
  console.log(`CLO No: ${clo.no}`);           // "27"
  console.log(`CLO ID: ${clo.id}`);           // "11307"
  console.log(`Curriculum: ${clo.curriculum_id}`);  // "70"
  console.log(`Course: ${clo.course_id}`);    // "1621"
  console.log(`Description: ${clo.description}`);
});
```

### ตัวอย่างที่ 2: แสดง CLO → PLO Mapping

```javascript
// หลังจาก analyze company
const response = await fetch('/api/analyze-company-grouped', {
  method: 'POST',
  body: JSON.stringify({ company_name: "...", requirements: "..." })
});
const data = await response.json();

// ดึง CLO context
const cloContext = data.clo_context;  
// [{ clo_id: "11307", curriculum_id: "70", course_id: "1621" }]

// ดึง CLO-PLO mappings
const mappings = data.clo_plo_mappings;
// [{ clo_id: "11307", plo_id: "246", is_map: true }]

// ดึง PLO details
const plos = data.mapped_plos;
// [{ id: "246", name: "plo1", detail: "...", plo_level: "1" }]

// สร้าง map: CLO ID → PLOs
const cloToPLOs = {};
mappings.forEach(m => {
  if (!cloToPLOs[m.clo_id]) cloToPLOs[m.clo_id] = [];
  const plo = plos.find(p => p.id === m.plo_id);
  if (plo) cloToPLOs[m.clo_id].push(plo);
});

// แสดง PLOs ของ CLO 11307
console.log(cloToPLOs["11307"]);
// [{ id: "246", name: "plo1", plo_level: "1", ... }]
```

### ตัวอย่างที่ 3: แสดง Heatmap

```javascript
// Column Header: แสดง CLO No. + Curriculum/Course
const headerText = `CLO ${clo.no}\n(${clo.curriculum_id}/${clo.course_id})`;
// "CLO 27\n(70/1621)"

// Tooltip: แสดงรายละเอียดครบ
const tooltip = `CLO No: ${clo.no}
CLO ID: ${clo.id}
Curriculum ID: ${clo.curriculum_id}
Course ID: ${clo.course_id}
Description: ${clo.description}`;
```

---

## 🎯 สิ่งสำคัญที่ต้องจำ

### CLO Fields
- **`id`**: CLO ID (unique) - ใช้เป็น key ในการอ้างอิง
- **`no`**: CLO No. (ซ้ำได้) - ใช้แสดงผลบนหน้าเว็บ
- **`curriculum_id`**: หลักสูตร
- **`course_id`**: รายวิชา
- **`description`**: คำอธิบาย CLO

### PLO Fields
- **`id`**: PLO ID (unique)
- **`name`**: ชื่อ PLO (เช่น "plo1", "plo2")
- **`detail`**: รายละเอียด PLO
- **`plo_level`**: 
  - `"1"` = PLO หลัก (🔵)
  - `"2"` = PLO ย่อย (🔸)
- **`curriculum_id`**: หลักสูตร

### CLO-PLO Mapping
- **`clo_id`**: CLO ID ที่เชื่อม
- **`plo_id`**: PLO ID ที่เชื่อม
- **`is_map`**: `true` = เชื่อมจริง, `false` = ไม่เชื่อม
- ใช้เฉพาะ `is_map: true` ในการแสดงผล

---

## 📞 ติดต่อ

หากมีคำถามเพิ่มเติมเกี่ยวกับโครงสร้างข้อมูล กรุณาติดต่อทีม Backend

**API Base URL**: `http://localhost:8000/api`

**Endpoints**:
- `POST /api/analyze-company-grouped`
- `GET /api/clos`
- `GET /api/companies`
- `GET /api/companies/{company_name}`
- `PUT /api/companies/{company_name}/groups`
- `DELETE /api/companies/{company_name}`
