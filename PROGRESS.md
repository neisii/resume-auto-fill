# Resume Auto Filler — 진행 문서

> 마지막 업데이트: 2026-05-16

---

## 현재 상태

MVP 구현 완료. 9개 실제 템플릿 분석 및 검증 완료.  
단락형 이력서는 지원 형식에서 제외. 테이블 기반 DOCX만 지원.

CLI 사용:
```
source .venv/bin/activate
resume-fill --template company.docx --profile profile.yaml --output filled.docx [--verbose]
```

---

## 환경

| 항목 | 내용 |
|---|---|
| Python | 3.12.13 (pyenv, `.python-version` 고정) |
| venv | `.venv/` |
| 패키지 관리 | `pyproject.toml` (hatchling, editable install) |
| LibreOffice | 26.2.3 (DOC→DOCX 변환용) |

---

## 파일 구조

```
resume-auto-fill/
├── resume_fill/
│   ├── cli.py
│   ├── loader.py
│   ├── matcher.py
│   ├── formatter.py
│   └── writer.py
├── aliases.yaml               # 필드 별칭 + _exclude + _overwrite
├── profile_sample.yaml        # 프로필 샘플
├── pyproject.toml
├── README.md
├── AGENTS.md
├── PROGRESS.md
└── ANALYSIS.md
```

---

## 모듈별 역할 및 핵심 위치

### `resume_fill/loader.py`
- `load_profile()` L8 — YAML/JSON 프로필 로딩
- `load_aliases()` L18 — aliases + `_exclude` + `_overwrite` 로딩, `(dict, set, set)` 반환
- `flatten_profile()` L27 — 중첩 dict → dotted-path 키로 평탄화

### `resume_fill/matcher.py`
- `_normalize(s)` L4 — 공백 전체 제거 (자간 표기 자동 처리)
- `FieldMatcher` L9
  - 정규화된 index 빌드, exclude/overwrite 집합 저장
  - `match(label)` — normalize → exclude → exact → alias → fuzzy(rapidfuzz, threshold 75.0)

### `resume_fill/formatter.py`
- `format_value(value, field_key)` L9
  - `datetime.date` → `YY.MM.DD`
  - `{"start", "end"}` dict → `"YY.MM ~ YY.MM"`
  - list: field_key에 "description/업무/수행/내용/주요" 포함 시 줄바꿈, 나머지 쉼표

### `resume_fill/writer.py`
- `fill_template()` L36 — 진입점. 관련성 필터 → 수직/수평 분기. `overwrite` 집합 전달
- **Placeholder 처리**
  - `_PLACEHOLDER_PATTERNS` L94 — 내장 패턴 (yyyy.mm, 0000.00, xxxx, 입력/기재/예) 등)
  - `is_placeholder()` L105 — 패턴 + `_overwrite` 집합으로 판단
  - `_row_is_fillable()` L118 — 행의 모든 셀이 빈 셀 또는 placeholder이면 True
- **관련성 필터**
  - `_count_table_labels()` L70 — 전체 매칭 라벨 수, < 2이면 스킵
- **수평 테이블**
  - `_build_col_map()` L139 — 상위 2개 행에서 열 인덱스 → field_key 매핑
  - `_is_horizontal_table()` L151 — 라벨 ≥ 3 AND `_IDENTIFYING_FIELDS` 존재 AND 빈 데이터 행 존재
  - `_fill_horizontal()` L176 — 섹션 감지 → 인덱스 순서대로 fillable 행 채움, cross-section 스킵
  - `_detect_section()` L218 — col_map에서 섹션명 추출
  - `_reindex_key()` L227 — `section.0.*` → `section.N.*`
  - `_section_count()` L232 — flat 프로필에서 섹션 항목 수 반환
- **수직 테이블**
  - `_label_count_in_row()` L244 — 행 내 라벨 수
  - `_fill_vertical()` L254 — 라벨 ≥ 3개 행 스킵, placeholder 셀 덮어쓰기 허용
  - `_find_value_cell()` L298 — 빈 셀 또는 placeholder 셀 반환
  - `_set_cell_text()` L339 — rPr 보존하며 텍스트 삽입

### `resume_fill/cli.py`
- `main()` L16 — typer CLI, `overwrite` 집합 언팩 및 전달
- 옵션: `--template`, `--profile`, `--output`, `--aliases`, `--fuzzy-threshold`, `--verbose`

### `aliases.yaml`
- `_exclude`: 오매핑 방지 라벨 (2개)
- `_overwrite`: 예시값 덮어쓰기 대상 (기본 비어있음)
- 정의된 field_key (L268 기준):
  - `basic.*`: name, birth, career_year, email, phone, address, gender, available_date, rrn
  - `education.0.*`: school, major, degree, location, start, end
  - `certifications.0.*`: name, issuer, date, grade
  - `career.0.*`: company, department, title, period, period.start, period.end, duties
  - `skills`
  - `projects.0.*`: name, role, description, period, period.start, period.end, client, company, environment.os/language/dbms/tool/framework/was/etc
  - `projects.1.*`: name, role, description, period

### `profile_sample.yaml`
- 프로필 구조 예시 (L1–L106)
- 섹션: `basic`(9개 필드), `education`, `certifications`, `career`(4개 이력), `skills`, `projects`(환경 정보 포함)

---

## 구현 중 발견·수정한 버그

| # | 증상 | 원인 | 수정 위치 |
|---|---|---|---|
| 1 | lxml proxy ID 충돌로 셀 이미 방문 오인 | CPython `id()` 주소 재사용 (GC) | `writer.py` — rows_cells 사전 수집 |
| 2 | `basic.birth` 날짜 포맷 불가 | PyYAML이 `1990-01-01`을 `datetime.date`로 파싱 | `formatter.py` L9 |
| 3 | `projects.0.period` 값 None | `_flatten()`이 dict 자체를 저장하지 않음 | `loader.py` L35 |
| 4 | 교육 테이블 헤더 셀 덮어씀 | 수직 fill이 컬럼 헤더를 key-value로 오인 | `writer.py` L254 — 라벨 ≥ 3 스킵 |
| 5 | 기존 채워진 셀 덮어씀 | `_find_value_cell`이 비어있지 않은 셀 반환 | `writer.py` L298 — 빈 셀만 반환 |
| 6 | `참여기간` 중복 입력 | period 전체를 col1에 채운 후 종료일 col2에도 중복 | `aliases.yaml` — 서브헤더 우선 |
| 7 | `지원일자` → `basic.name` 오매핑 | fuzzy 85% | `aliases.yaml` `_exclude` |
| 8 | `상세경력사항` → `basic.career_year` 오매핑 | fuzzy 80% | `aliases.yaml` `_exclude` |
| 9 | `학력사항` → `basic.career_year` 오매핑 | 정규화 후 `경력사항` alias와 fuzzy 75% 일치 | `aliases.yaml` — `경력사항` 제거 |
| 10 | career 테이블에 project 데이터 입력 | 다른 섹션 필드가 col_map에 혼입 | `writer.py` L176 — cross-section 스킵 |

---

## 검증 결과 (profile_sample.yaml 기준)

| 파일 | 채운 필드 | 비고 |
|---|---|---|
| `resume_sample-1.docx` | **32** | 기준 파일, 환경 컬럼 포함 |
| `resume_sample-3.docx` | **44** | career 4개 항목 수평 fill |
| `resume_sample-4.docx` | **41** | DOC→DOCX 변환본 |
| `resume_sample-5.docx` | 9 | 초대형 단일 테이블, alias 부족 |
| `resume_sample-8.docx` | 4 | 복합 구조, 비표준 라벨 다수 |
| `resume_sample-9.docx` | 4 | 단락형 혼합, 테이블 최소 |

상세 분석 → `ANALYSIS.md`

---

## 자동화 한계

양식이 표준화된 템플릿에서는 높은 커버리지를 보이나, 아래 이유로 누락이 발생한다.

| 원인 | 설명 |
|---|---|
| 라벨 다양성 | 같은 필드도 회사마다 표기 상이 — alias로 점진적 보완 가능 |
| 테이블 구조 비표준화 | 기술스택·프로젝트·경력처럼 자동화 가능한 항목도 구조가 예상과 다르면 누락 |
| 프로필 미정의 항목 | 자기소개서, 지원동기, 희망연봉 등은 데이터 자체가 없어 자동화 불가 |
| 단락형 구조 | 테이블 없는 이력서는 지원 형식 외 |

**실용적 운용**: 이름·연락처·기술스택·프로젝트처럼 매번 동일하게 반복되는 항목의 복붙 피로 제거가 핵심 가치. 나머지는 사람이 채우는 구조가 현실적이다.

---

## 향후 과제

- [ ] `기간` alias 충돌 — career/project 컨텍스트 구분 방안
- [ ] `기  간(YYMM–YYMM)` 형식 날짜 파싱 (`formatter.py`)
- [ ] sample-8 복합 구조 alias 보완
- [ ] 복수 템플릿 일괄 처리 (`--batch` 옵션)
