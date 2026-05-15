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
| LibreOffice | 26.2.3 (DOC→DOCX 변환용, `/Applications/LibreOffice.app`) |

pyenv 설치 절차 → `pyenv-setup.md`

---

## 파일 구조

```
resume-auto-fill/
├── resume_fill/               # 패키지
│   ├── cli.py
│   ├── loader.py
│   ├── matcher.py
│   ├── formatter.py
│   └── writer.py
├── aliases.yaml               # 필드 별칭 사전 + 제외 목록
├── profile_sample.yaml        # 프로필 샘플
├── pyproject.toml
├── README.md                  # 사용 가이드
├── PROGRESS.md                # 이 문서
└── ANALYSIS.md                # 9개 템플릿 분석 보고서
```

**샘플 템플릿** (테스트용, git 제외)

| 파일 | 형식 | 비고 |
|---|---|---|
| `resume_sample-1.docx` | DOCX | 검증 완료 기준 파일 |
| `resume_sample-2.docx` | DOCX | 단락형 — 지원 형식 외 |
| `resume_sample-3.docx` | DOCX | 테이블형, 프로젝트 표 포함 |
| `resume_sample-4.docx` | DOC→DOCX | LibreOffice 변환본 |
| `resume_sample-5.docx` | DOCX | 초대형 단일 테이블 (35r×18c) |
| `resume_sample-6.docx` | DOC→DOCX | 단락형 — 지원 형식 외 |
| `resume_sample-7.docx` | DOCX | 단락형 — 지원 형식 외 |
| `resume_sample-8.docx` | DOC→DOCX | 복합 구조 |
| `resume_sample-9.docx` | DOC→DOCX | 단락형 — 지원 형식 외 |

---

## 모듈별 역할 및 핵심 위치

### `resume_fill/loader.py`
- `load_profile()` L8 — YAML/JSON 프로필 로딩
- `load_aliases()` L18 — 별칭 사전 + `_exclude` 로딩, `(dict, set)` 반환
- `flatten_profile()` L26 — 중첩 dict → dotted-path 키로 평탄화

### `resume_fill/matcher.py`
- `_normalize(s)` L4 — 공백 전체 제거 (자간 표기 처리)
- `FieldMatcher` L9
  - `__init__(aliases, fuzzy_threshold, exclude)` — 정규화된 index 빌드, exclude 집합 저장
  - `match(label)` — normalize → exclude 확인 → exact → alias → fuzzy(rapidfuzz)
  - fuzzy threshold 기본값 75.0

### `resume_fill/formatter.py`
- `format_value(value, field_key)` L9
  - `datetime.date` → `YY.MM.DD`
  - `{"start", "end"}` dict → `"YY.MM ~ YY.MM"`
  - list: field_key에 "description/업무/수행/내용/주요" 포함 시 줄바꿈, 나머지 쉼표
  - `_fmt_date()` L31

### `resume_fill/writer.py`
- `fill_template()` L33 — 진입점. 테이블 관련성 필터 → 수직/수평 분기
- **관련성 필터**
  - `_count_table_labels()` L65 — 테이블 전체 매칭 라벨 수 반환, < 2이면 스킵
- **수평 테이블** (헤더 행 + 데이터 행)
  - `_build_col_map()` L98 — 상위 2개 행에서 열 인덱스 → field_key 매핑
  - `_is_horizontal_table()` L110 — 라벨 ≥ 3 AND identifying 필드 존재 AND 빈 데이터 행 존재
  - `_fill_horizontal()` L135 — 섹션 감지 → 인덱스 순서대로 빈 행 채움, cross-section 필드 스킵
  - `_detect_section()` L175 — col_map에서 섹션명 추출 (projects/career/education/certifications)
  - `_reindex_key()` L184 — `section.0.*` → `section.N.*` 치환
  - `_section_count()` L189 — flat 프로필에서 해당 섹션 항목 수 반환
- **수직 테이블** (라벨 셀 + 인접 값 셀)
  - `_label_count_in_row()` L201 — 행 내 라벨 수 카운트
  - `_fill_vertical()` L211 — 라벨 ≥ 3개인 행은 컬럼 헤더로 간주하고 스킵
  - `_find_value_cell()` L253 — 오른쪽 → 아래 순서로 빈 셀만 탐색
  - `_set_cell_text()` L290 — 기존 rPr(런 서식) 보존하며 텍스트 삽입

### `resume_fill/cli.py`
- `main()` L16 — typer CLI
- 옵션: `--template`, `--profile`, `--output`, `--aliases`, `--fuzzy-threshold`, `--verbose`

### `aliases.yaml`
- `_exclude` 섹션: 오매핑 방지 라벨 목록
- 정의된 field_key 섹션 (L210 기준):
  - `basic.*`: name, birth, career_year, email, phone, address, gender
  - `education.0.*`: school, major, degree, start, end
  - `certifications.0.*`: name, issuer, date, grade
  - `career.0.*`: company, department, title, period, period.start, period.end, duties
  - `skills`
  - `projects.0.*`: name, role, description, period, period.start, period.end
  - `projects.1.*`: name, role, description, period
- 공백은 자동 제거(`_normalize`)되므로 공백 변형 별칭은 등록하지 않음

### `profile_sample.yaml`
- 프로필 구조 예시 (L1–L62)
- 섹션: `basic`, `education`, `certifications`, `career`, `skills`, `projects`

---

## 구현 중 발견·수정한 버그

| # | 증상 | 원인 | 수정 위치 |
|---|---|---|---|
| 1 | lxml proxy ID 충돌로 셀이 이미 방문한 것으로 오인 | CPython `id()` 주소 재사용 (GC 타이밍) | `writer.py` — rows_cells 전체 사전 수집으로 강한 참조 유지 |
| 2 | `basic.birth` 날짜 포맷 불가 | PyYAML이 `1990-01-01`을 `datetime.date`로 자동 파싱 | `formatter.py` L9 — `datetime.date` 분기 추가 |
| 3 | `projects.0.period` 값 None | `_flatten()`이 dict 자체를 저장하지 않고 하위 키만 재귀 | `loader.py` L35 — prefix 있을 때 dict도 result에 저장 |
| 4 | 교육 테이블 헤더 셀 덮어씀 | 수직 fill이 컬럼 헤더 행을 key-value 행으로 오인 | `writer.py` L211 — 행 내 라벨 ≥ 3개면 스킵 |
| 5 | 기존 채워진 셀 덮어씀 | `_find_value_cell`이 비어있지 않은 셀도 반환 | `writer.py` L253 — 빈 셀만 value cell로 반환 |
| 6 | `참여기간` 중복 입력 | col1에 period(start~end) 채운 후 col2(종료일)에도 중복 | `aliases.yaml` — 서브헤더 `시작일`/`종료일` 우선 |
| 7 | `지원일자` → `basic.name` 오매핑 | fuzzy 85% 오매핑 | `aliases.yaml` `_exclude` 추가 |
| 8 | `상세경력사항` → `basic.career_year` 오매핑 | fuzzy 80% 오매핑 | `aliases.yaml` `_exclude` 추가 |
| 9 | `학력사항` → `basic.career_year` 오매핑 | 정규화 후 `경력사항` alias와 fuzzy 75% 일치 | `aliases.yaml` — `경력사항` alias 제거 |
| 10 | career 테이블에 project 데이터 입력 | 다른 섹션 필드가 col_map에 혼입 | `writer.py` L135 — cross-section 필드 스킵 |

---

## 검증 결과

| 파일 | 필드 수 | 비고 |
|---|---|---|
| `resume_sample-1.docx` | **18** | 기준 파일 |
| `resume_sample-3.docx` | 27 | career·education·certifications 수평 테이블 포함 |
| `resume_sample-4.docx` | 21 | DOC→DOCX 변환본 |
| `resume_sample-5.docx` | 9 | 초대형 단일 테이블 |
| `resume_sample-8.docx` | 4 | 복합 구조, alias 추가 여지 있음 |

상세 분석 → `ANALYSIS.md`

---

## 향후 과제

- [ ] `기간` alias 충돌 해결 — career/project 컨텍스트 구분 방안 설계
- [ ] `기  간(YYMM–YYMM)` 형식 날짜 파싱 지원 (`formatter.py`)
- [ ] sample-8 복합 구조 추가 검증 및 alias 보완
- [ ] 복수 템플릿 일괄 처리 (`--batch` 옵션)
