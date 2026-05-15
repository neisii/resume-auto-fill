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
| `--verbose` | `-v` | — | 상세 출력 (로드된 alias 수, skip 수) |

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
  address: 서울특별시 강남구 테헤란로 123

education:
  - school: 한국대학교
    major: 컴퓨터공학과
    degree: 학사
    start: 2006-03
    end: 2012-02

certifications:
  - name: 정보처리기사
    issuer: 한국산업인력공단
    date: 2015-05
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
    period:
      start: 2021-03
      end: 2023-08
    role: 백엔드 개발
    description:
      - 실시간 트래픽 처리 시스템 설계 및 구현
      - Kafka 기반 이벤트 처리 파이프라인 구축
```

### 날짜 형식

날짜 필드는 자동으로 변환됩니다.

| 입력 | 출력 |
|---|---|
| `2024-03` | `24.03` |
| `2024-03-15` | `24.03.15` |
| period `{start, end}` | `24.03 ~ 25.06` |

---

## 별칭 사전 (aliases.yaml)

템플릿 라벨과 프로필 필드를 연결합니다. **공백은 자동으로 무시**하므로 `기 간`, `기      간`은 `기간`과 동일하게 처리됩니다.

### 필드 추가

```yaml
basic.name:
  - 성명
  - 이름
  - 지원자명
```

### 오매핑 방지

특정 라벨이 잘못 매핑되면 `_exclude`에 추가합니다.

```yaml
_exclude:
  - 지원일자    # 특정 양식에서 basic.name으로 오매핑됨
```

---

## DOC 파일 처리

`.doc`(구 바이너리 형식)은 직접 지원하지 않습니다. LibreOffice로 변환 후 사용합니다.

```bash
soffice --headless --convert-to docx company.docx
```

---

## 동작 원리

```
profile.yaml  →  프로필 로딩 및 평탄화 (basic.name, projects.0.role 등 dotted-path 키)
aliases.yaml  →  라벨 별칭 사전 + 오매핑 제외 목록
                          ↓
template.docx →  테이블 순회 → 라벨 매칭 (exact → alias → fuzzy)
                          ↓
              수평 테이블 / 수직 테이블 분기 처리
                          ↓
              output.docx (서식 보존, 빈 셀만 채움)
```

**매칭 우선순위**: 정확 일치 → 별칭 일치 → 퍼지 매칭 (rapidfuzz, 기본 75%)

**지원 테이블 구조**

| 구조 | 예시 | 대상 섹션 |
|---|---|---|
| 수직 (라벨\|값 인접) | 기본정보표 | basic, skills |
| 수평 (헤더행 + 데이터행) | 프로젝트 목록, 경력 목록, 학력표 | projects, career, education, certifications |
