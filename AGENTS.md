# AGENTS.md

AI 에이전트가 이 프로젝트에서 작업할 때 반드시 숙지해야 할 기본 정보.

---

## 프로젝트 목적

회사가 제공하는 DOCX 양식에 구조화된 프로필 데이터를 자동으로 채워넣는 CLI 도구.  
AI 생성 콘텐츠, OCR, 브라우저 자동화, PDF 편집은 범위 밖이다.

**지원 형식: 테이블 기반 DOCX만. 단락형 이력서는 지원하지 않는다.**

**자동화 한계**: 회사마다 양식이 일관되지 않아 기술스택·프로젝트·경력처럼 자동화 가능한 항목도 테이블 구조가 다르면 매핑이 누락된다. 이는 툴의 한계가 아닌 회사 양식의 비표준화 문제다.

---

## 환경

- Python 3.12.13 (pyenv, `.python-version`으로 고정)
- 가상환경: `.venv/` — 작업 전 반드시 활성화
- 패키지 설치: `pip install -e .` (editable, `pyproject.toml` 기준)
- 주요 의존성: `python-docx`, `rapidfuzz`, `pyyaml`, `typer`
- LibreOffice: DOC→DOCX 변환용 (`soffice --headless --convert-to docx`)

---

## 핵심 파일

| 파일 | 역할 |
|---|---|
| `resume_fill/loader.py` | 프로필(YAML/JSON) 로딩, aliases 로딩 `(dict, exclude, overwrite)` 반환, 프로필 평탄화 |
| `resume_fill/matcher.py` | 공백 정규화(`_normalize`) + exact→alias→fuzzy 매칭, exclude/overwrite 집합 관리 |
| `resume_fill/formatter.py` | 값 포맷 변환 (날짜, 리스트, 기간) |
| `resume_fill/writer.py` | DOCX 테이블 파싱, placeholder 감지, 수직/수평 테이블 채우기 |
| `resume_fill/cli.py` | CLI 진입점 (`resume-fill` 명령) |
| `aliases.yaml` | field_key → 라벨 변형 목록 + `_exclude` + `_overwrite` |
| `profile_sample.yaml` | 프로필 데이터 구조 예시 (소스코드에서 직접 참조하지 않음) |
| `PROGRESS.md` | 구현 현황, 모듈별 라인 번호, 버그 이력 |
| `ANALYSIS.md` | 9개 템플릿 분석 보고서 |

---

## 데이터 흐름

```
profile.yaml  →  load_profile()  →  flatten_profile()  (dotted-path 키)
aliases.yaml  →  load_aliases()  →  FieldMatcher (normalize + index)
                                        ↓
template.docx →  doc.tables 순회  →  관련성 필터 (라벨 ≥ 2)
                                        ↓
                              수평 테이블 / 수직 테이블 분기
                                        ↓
                         라벨 매칭 → format_value() → _set_cell_text()
                                        ↓
                              output.docx 저장
```

---

## 규칙

### aliases.yaml
- field_key는 `profile.yaml`의 dotted-path와 일치해야 한다.
- **공백 변형은 등록하지 않는다.** 공백은 매칭 전 자동 제거(`_normalize`)된다.
- 오매핑이 확인된 라벨은 `_exclude`에 추가한다. 파일명과 오매핑된 field_key를 주석으로 남긴다.
- 템플릿별 예시값(빈칸 안내 문구)은 `_overwrite`에 추가한다.
- 정규화 후 동일한 형태가 되는 alias를 두 field_key에 동시에 추가하면 마지막 정의가 이긴다 — 충돌 여부를 확인할 것.

### writer.py
- `rows_cells`를 반드시 사전 수집한 뒤 처리한다 (lxml proxy GC 문제).
- value cell은 **빈 셀 또는 `is_placeholder()`가 True인 셀만** 대상으로 한다.
- 수직 테이블에서 행 내 라벨 ≥ 3개면 컬럼 헤더 행으로 간주하고 스킵한다.
- 수평 테이블에서 다른 섹션의 field_key는 cross-section 체크로 차단한다.
- `_IDENTIFYING_FIELDS`에 없는 섹션은 수평 테이블로 감지되지 않는다.

### 코드 수정 시
- 함수 라인 번호가 바뀌면 `PROGRESS.md` 모듈별 역할 섹션도 업데이트한다.
- 새 버그를 수정했으면 `PROGRESS.md` 버그 목록에 추가한다.
- 충돌 가능한 alias 변경은 정규화 충돌 여부를 먼저 확인한다.

---

## 하지 말아야 할 것

- `profile_sample.yaml` 경로를 소스코드에 하드코딩하지 않는다.
- 공백 변형 alias를 aliases.yaml에 수동으로 추가하지 않는다 (자동 정규화로 처리).
- `.venv/`, `resume_sample*.docx`, `filled_*.docx`를 git에 추가하지 않는다.
- DOC 바이너리 파일을 python-docx로 직접 열지 않는다.
- 단락형 이력서 지원 기능을 추가하지 않는다 (지원 형식에서 제외).
