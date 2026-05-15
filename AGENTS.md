# AGENTS.md

AI 에이전트가 이 프로젝트에서 작업할 때 반드시 숙지해야 할 기본 정보.

---

## 프로젝트 목적

회사가 제공하는 DOCX 양식에 구조화된 프로필 데이터를 자동으로 채워넣는 CLI 도구.  
AI 생성 콘텐츠, OCR, 브라우저 자동화, PDF 편집은 범위 밖이다.  
**지원 형식: 테이블 기반 DOCX만. 단락형 이력서는 지원하지 않는다.**

---

## 환경

- Python 3.12.13 (pyenv, `.python-version`으로 고정)
- 가상환경: `.venv/` — 작업 전 반드시 활성화
- 패키지 설치: `pip install -e .` (editable, `pyproject.toml` 기준)
- 주요 의존성: `python-docx`, `rapidfuzz`, `pyyaml`, `typer`

---

## 핵심 파일

| 파일 | 역할 |
|---|---|
| `resume_fill/loader.py` | 프로필(YAML/JSON) 로딩, aliases 로딩, 프로필 평탄화 |
| `resume_fill/matcher.py` | 라벨 매칭 (exact → alias → fuzzy) |
| `resume_fill/formatter.py` | 값 포맷 변환 (날짜, 리스트, 기간) |
| `resume_fill/writer.py` | DOCX 테이블 파싱 및 셀 채우기 |
| `resume_fill/cli.py` | CLI 진입점 (`resume-fill` 명령) |
| `aliases.yaml` | field_key → 템플릿 라벨 변형 목록 + `_exclude` 오매핑 차단 목록 |
| `profile_sample.yaml` | 프로필 데이터 구조 예시 (소스코드에서 직접 참조하지 않음) |
| `PROGRESS.md` | 구현 현황, 모듈별 라인 번호, 버그 이력 |
| `ANALYSIS.md` | 9개 실제 템플릿 분석 보고서 |

---

## 데이터 흐름

```
profile.yaml  →  load_profile()  →  flatten_profile()
aliases.yaml  →  load_aliases()  →  FieldMatcher
                                        ↓
template.docx →  doc.tables 순회  →  테이블 관련성 필터(라벨 ≥ 2)
                                        ↓
                              수평 테이블 / 수직 테이블 분기
                                        ↓
                              format_value() → _set_cell_text()
                                        ↓
                              output.docx 저장
```

---

## 규칙

### aliases.yaml
- field_key는 `profile.yaml`의 dotted-path와 일치해야 한다 (`basic.name`, `projects.0.role` 등).
- 오매핑이 확인된 라벨은 코드 수정 없이 `_exclude` 목록에 추가한다.
- `_exclude`에 추가할 때는 해당 파일명과 오매핑된 field_key를 주석으로 남긴다.

### writer.py
- 테이블 처리는 반드시 `rows_cells`를 사전 수집한 뒤 진행한다.  
  lxml proxy GC 문제로 인해 `row.cells`를 반복 호출하면 `id()` 충돌이 발생한다.
- value cell은 **빈 셀만** 대상으로 한다. 기존 내용이 있는 셀은 덮어쓰지 않는다.
- 수직 테이블에서 한 행에 매칭 라벨이 3개 이상이면 컬럼 헤더 행으로 간주하고 스킵한다.

### 코드 수정 시
- 함수 라인 번호가 바뀌면 `PROGRESS.md`의 모듈별 역할 섹션도 함께 업데이트한다.
- 새 버그를 수정했으면 `PROGRESS.md`의 버그 목록에 추가한다.

---

## 하지 말아야 할 것

- `profile_sample.yaml` 경로를 소스코드에 하드코딩하지 않는다.
- `aliases.yaml` 외부에 별도 매핑 로직을 소스코드에 직접 넣지 않는다.
- `.venv/`, `resume_sample*.docx`, `filled_*.docx`를 git에 추가하지 않는다.  
  (`.gitignore` 참조)
- DOC 바이너리 파일을 python-docx로 직접 열지 않는다. LibreOffice로 변환 후 처리한다.
