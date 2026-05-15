# Resume Auto Filler MVP - PRD

## 1. Overview

This project automates repetitive copy-paste work required for freelancer/outsourcing resume submissions.

The system is NOT an AI resume generator.

The primary purpose is:

- document automation
- semantic field mapping
- template filling

The goal is to automatically populate company-provided DOCX forms using a structured master resume/profile.

---

# 2. Goal

## Primary Goal

Automatically fill DOCX template cells using structured profile data.

The system should:

- parse DOCX tables
- detect field labels
- map semantically similar fields
- insert matching profile data
- preserve original document formatting

---

# 3. Non Goals

The MVP explicitly excludes:

- GUI
- Web service
- Authentication
- Cloud storage
- AI-generated self introductions
- OCR
- PDF editing
- Browser automation
- ATS integration
- LLM-heavy workflows
- DOC(binary) editing
- Layout redesign

---

# 4. User Problem

Freelancer resume submissions require repeatedly copying the same information into slightly different DOCX templates.

Typical repeated fields:

- Name
- Skills
- Project history
- Role
- Work description
- Career period

Field labels differ per company:

| Variant Labels |
|---|
| 수행업무 |
| 담당업무 |
| 주요업무 |
| 업무내용 |

These represent the same semantic meaning but require manual mapping.

The repetitive manual work causes:

- fatigue
- input mistakes
- formatting inconsistency
- wasted time

---

# 5. Core Requirements

## 5.1 Input

### Profile Data

Supported formats:

- YAML
- JSON

Example:

```yaml
basic:
  name: 홍길동
  birth: 1990-01-01
  career_year: 9년

skills:
  - Java
  - Spring
  - Kafka

projects:
  - name: 광고 플랫폼
    period:
      start: 2021-03
      end: 2023-08
    role: 백엔드 개발
    description:
      - 실시간 트래픽 처리
      - Kafka 이벤트 처리
```

---

### DOCX Template

Requirements:

- `.docx` only
- table-based forms
- existing company forms used as-is

---

# 6. Functional Requirements

## 6.1 DOCX Parsing

The system must:

- scan all tables
- extract cell text
- identify row/column positions
- preserve table structure

---

## 6.2 Semantic Field Mapping

The system must map template fields to profile data using:

- exact matching
- alias dictionary
- fuzzy matching

Example:

| Template Field | Profile Mapping |
|---|---|
| 수행업무 | project.description |
| 주요업무 | project.description |
| 보유기술 | skills |
| 기술스택 | skills |

---

## 6.3 Alias Dictionary

The system must support configurable field aliases.

Example:

```yaml
role:
  - 담당업무
  - 수행업무
  - 업무내용
  - 주요업무

skills:
  - 기술스택
  - 사용기술
  - 보유기술
```

---

## 6.4 Data Formatting

The system must support output formatting transformations.

Examples:

| Input | Output |
|---|---|
| 2024-03 | 24.03 |
| skills array | Java, Spring, Kafka |

Supported formatting:

- date conversion
- multiline formatting
- comma-separated formatting

---

## 6.5 DOCX Output

The system must:

- preserve original formatting
- preserve table layout
- modify text only
- generate a new output file

Example:

```text
filled_companyA.docx
```

---

# 7. CLI Requirements

## Command

```bash
resume-fill \
  --template company.docx \
  --profile profile.yaml \
  --output filled.docx
```

---

# 8. System Architecture

```text
profile loader
    ↓
docx parser
    ↓
field matcher
    ↓
formatter
    ↓
docx writer
```

---

# 9. Recommended Tech Stack

## Language

- Python 3.12+

## Libraries

| Purpose | Library |
|---|---|
| DOCX processing | python-docx |
| String similarity | rapidfuzz |
| YAML parsing | pyyaml |
| CLI | typer |

---

# 10. Matching Strategy

## Priority Order

### 1. Exact Match

Example:

- 기술스택 == 기술스택

---

### 2. Alias Match

Example:

- 주요업무 → 수행업무 group

---

### 3. Fuzzy Match

Example:

- 사용 기술 → 보유기술

---

# 11. Output Quality Requirements

The generated document must:

- remain editable in Microsoft Word
- preserve original styling
- preserve merged cells where possible
- avoid modifying unrelated cells

---

# 12. MVP Scope Constraints

The MVP does NOT need to solve:

- broken DOCX recovery
- complex merged-cell edge cases
- image text extraction
- PDF editing
- AI-generated content
- automatic project selection
- advanced layout understanding
- binary `.doc` editing

---

# 13. Success Criteria

The MVP is considered successful if:

- 10+ real company templates are processed successfully
- major field mapping accuracy exceeds 80%
- manual input work is reduced by at least 70%
- output formatting remains stable

---

# 14. Future Expansion Possibilities

Possible future features:

- `.doc` conversion support
- interactive mapping correction
- LLM fallback matching
- browser autofill
- project auto-selection
- batch processing
- profile versioning
- schema validation

