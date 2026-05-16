# resume-auto-fill

회사가 제공하는 DOCX 이력서 양식에 프로필 데이터를 자동으로 채워넣는 CLI 도구.

**지원 형식: 테이블 기반 DOCX만. 단락형 이력서는 지원하지 않습니다.**

---

## 요구사항

- Python 3.12.13 (pyenv 사용 권장)
- python-docx, rapidfuzz, pyyaml, typer

---

## 설치

```bash
git clone https://github.com/neisii/resume-auto-fill.git
cd resume-auto-fill
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

---

## 사용법

```bash
resume-fill \
  --template company.docx \
  --profile profile.yaml \
  --output filled.docx
```

### 옵션

| 옵션 | 단축 | 기본값 | 설명 |
|---|---|---|---|
| `--template` | `-t` | 필수 | 회사 제공 DOCX 양식 경로 |
| `--profile` | `-p` | 필수 | 프로필 YAML/JSON 파일 경로 |
| `--output` | `-o` | 필수 | 출력 파일 경로 |
| `--aliases` | `-a` | `aliases.yaml` | 필드 별칭 사전 경로 |
| `--fuzzy-threshold` | — | `75.0` | 퍼지 매칭 임계값 (0–100) |
| `--verbose` | `-v` | — | 상세 출력 |

---

## 프로필 파일 작성

`profile_sample.yaml`을 복사해 본인 정보로 채웁니다.

```yaml
basic:
  name: 홍길동
  birth: 1990-01-01
  career_year: 9년
  gender: 남
  email: hong@example.com
  phone: 010-1234-5678
  address: 서울특별시 강남구
  available_date: 즉시
  rrn: 000000-0******

education:
  - school: 한국대학교
    major: 컴퓨터공학부
    degree: 학사
    location: 서울
    start: 2006-03
    end: 2012-02

certifications:
  - name: 정보처리기사
    issuer: 한국산업인력공단
    date: 2015-05-14
    grade: 1급

career:
  - company: ㈜이전회사
    department: 개발팀
    title: 과장
    period:
      start: 2018-01
      end: 2021-02
    duties: 백엔드 시스템 설계 및 개발

skills:
  - Java
  - Spring Boot
  - Kafka

projects:
  - name: 광고 플랫폼 개발
    client: ㈜광고주
    company: ㈜이전회사
    period:
      start: 2021-03
      end: 2023-08
    role: 백엔드 개발
    description:
      - 실시간 트래픽 처리 시스템 설계 및 구현
      - Kafka 기반 이벤트 처리 파이프라인 구축
    environment:
      os: Linux
      language: Java
      dbms: PostgreSQL
      tool: IntelliJ, Git
      framework: Spring Boot
      was: Tomcat
      etc: Docker
```

### 날짜 형식

| 입력 | 출력 |
|---|---|
| `2024-03` | `24.03` |
| `2024-03-15` | `24.03.15` |
| period `{start, end}` | `24.03 ~ 25.06` |

---

## 별칭 사전 (aliases.yaml)

템플릿 라벨과 프로필 필드를 연결합니다.

**공백은 자동으로 무시**됩니다. `기 간`, `기      간`, `기간`은 동일하게 처리됩니다.

### 오매핑 방지

```yaml
_exclude:
  - 지원일자    # 특정 양식에서 basic.name으로 오매핑됨
```

### 예시값 덮어쓰기

템플릿에 예시 문구가 채워진 셀은 기본적으로 건드리지 않습니다.
`yyyy.mm`, `0000-00-00`, `입력하세요` 같은 패턴은 자동으로 덮어씁니다.
그 외 특정 예시값은 `_overwrite`에 추가합니다.

```yaml
_overwrite:
  - 홍길동
  - 000-0000-0000
```

---

## DOC 파일 처리

`.doc`(구 바이너리 형식)은 LibreOffice로 변환 후 사용합니다.

```bash
soffice --headless --convert-to docx company.doc
```

---

## 동작 원리

```
profile.yaml  →  프로필 로딩 및 평탄화 (dotted-path 키)
aliases.yaml  →  라벨 별칭 + 오매핑 제외 + 예시값 덮어쓰기 목록
                          ↓
template.docx →  테이블 순회 → 관련성 필터(라벨 ≥ 2)
                          ↓
              수평 / 수직 테이블 분기
                          ↓
              라벨 매칭 (exact → alias → fuzzy 75%)
                          ↓
              output.docx (서식 보존, 빈 셀 또는 예시값 셀만 채움)
```

**지원 테이블 구조**

| 구조 | 예시 | 대상 섹션 |
|---|---|---|
| 수직 (라벨\|값 인접) | 기본정보표 | basic, skills |
| 수평 (헤더행 + 데이터행) | 프로젝트 목록, 경력 목록, 학력표 | projects, career, education, certifications |

---

## 자동화 한계

회사마다 이력서 양식이 일관되지 않아 다음과 같은 한계가 발생합니다.

**라벨 다양성**  
같은 의미의 필드도 회사마다 표기가 달라 (`담당업무` / `수행업무` / `업무내용` 등) alias를 추가해도 처음 보는 표기가 계속 생깁니다.

**테이블 구조 다양성**  
기술스택, 프로젝트 목록, 경력사항처럼 자동화 가능한 항목도 테이블 구조가 예상과 다르면 매핑되지 않습니다. 단일 초대형 테이블, 비표준 병합 셀 구조 등이 해당합니다.

**자동화 불가 항목**  
자기소개서, 지원동기, 희망 연봉, 군별/계급, 추천인 등은 데이터 자체가 없거나 양식마다 맥락이 달라 자동화가 불가합니다.

**실용적 운용 방식**  
이 툴은 매번 동일하게 반복 입력하는 고정 항목(이름, 연락처, 기술스택, 프로젝트 목록 등)의 복붙 피로 제거를 목적으로 합니다. 나머지는 사람이 채우는 구조가 현실적입니다.
