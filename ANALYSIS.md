# 템플릿 분석 보고서

> 작성일: 2026-05-16  
> 분석 대상: 9개 템플릿 (DOCX 5개 + DOC→DOCX 변환 4개)

---

## 1. 파일 현황

| 파일 | 원본 형식 | 변환 | 테이블 수 | 단락 수 | 라벨 매칭 수 | 비고 |
|---|---|---|---|---|---|---|
| resume_sample.docx | DOCX | — | 8 | 8 | 12 | 검증 완료, 11필드 채움 |
| resume_sample-2.docx | DOCX | — | **0** | 114 | 0 | 테이블 없음 — 단락형 |
| resume_sample-3.docx | DOCX | — | 7 | 12 | 20 | 프로젝트 표 포함 |
| resume_sample-4.docx | **DOC** | LibreOffice | 7 | 10 | 10 | 원본 55K → 변환 10K |
| resume_sample-5.docx | DOCX | — | 2 | 5 | 6 | 단일 초대형 테이블 35r×18c |
| resume_sample-6.docx | **DOC** | LibreOffice | 1 | 160 | 0 | 단락 위주, 테이블 1개만 |
| resume_sample-7.docx | DOCX | — | 2 | 108 | 0 | 개인정보 동의서만, 본문 단락형 |
| resume_sample-8.docx | **DOC** | LibreOffice | 15 | 170 | 3 | 복잡 구조, 이미지 포함 추정 |
| resume_sample-9.docx | **DOC** | LibreOffice | 2 | 135 | 1 | 단락 위주 |

변환 파일 경로: `/Users/neisii/Development/resume-auto-fill/resume_sample-{4,6,8,9}.docx`

---

## 2. 구조 패턴 분류

분석 결과 4가지 구조 패턴 확인.

### 패턴 A — 수직 Key-Value 테이블 (현재 지원)
라벨 셀 | 값 셀이 같은 행에 인접한 구조.

```
| 이름     | [값]     | 생년월일 | [값] |
| 경력     | [값]     | 보유기술 | [값] |
```

해당 파일: sample.docx(Table 1), sample-3.docx(Table 1), sample-4.docx 일부

### 패턴 B — 수평 데이터 테이블 (현재 지원)
헤더 행 + 데이터 행 구조. 프로젝트 목록에 주로 사용.

```
| 프로젝트명 | 시작일 | 종료일 | 역할 | ... |
| [프로젝트1]| [날짜] | [날짜] | [역할] |
| [프로젝트2]| ...    |
```

해당 파일: sample.docx(Table 7), sample-3.docx(Table 6, 27r×11c)

### 패턴 C — 단락형 이력서 (미지원)
테이블 없이 Bold 라벨 + 텍스트로 구성.

```
■ 이름: 홍길동
■ 경력: 9년
```

해당 파일: sample-2.docx(테이블 0, 단락 114), sample-6.docx, sample-7.docx, sample-9.docx

### 패턴 D — 초대형 단일 병합 테이블 (부분 지원)
전체 이력서가 하나의 테이블. 병합 셀 수백 개.

해당 파일: sample-5.docx(35r×18c, 병합 476개), sample-8.docx(15개 테이블 복합)

---

## 3. 엣지 케이스 / 코너 케이스

### [E-1] 단락형 이력서 — 툴이 아무것도 채우지 못함
sample-2, 6, 7, 9는 테이블이 없거나 최소화돼 있고 내용이 단락으로 구성.  
현재 파서가 `doc.tables`만 탐색하므로 완전히 미커버.  
9개 중 4개(44%)가 이 패턴에 해당.

### [E-2] DOC→DOCX 변환 품질 손실
sample-4: 원본 55K → 변환본 10K (83% 감소).  
단순 인코딩 차이일 수 있으나 레이아웃·서식 손실 가능성 있음.  
LibreOffice 변환이 OLE2 포맷 구조를 완벽히 재현하지 못하는 경우 발생.

### [E-3] 프로젝트 반복 블록 (비표준 구조, sample-3 Table 6)
27r×11c 단일 테이블에 3~4개 프로젝트 블록이 병합 셀로 구분돼 반복 배치.  
헤더 없이 프로젝트별 섹션이 연속되는 구조로, 현재 수평 테이블 감지(`_is_horizontal_table`)가  
"빈 데이터 행이 존재해야 한다"는 조건을 만족하지 못할 수 있음.

### [E-4] 초대형 단일 테이블의 라벨 미매칭
sample-5의 `성명 (한글)` → fuzzy 62% (threshold 75% 미달).  
병합 셀이 476개인 구조에서 값 셀 탐색 경로가 예상과 다를 수 있음.

### [E-5] `참여기간` 제거로 인한 커버리지 손실
수평 테이블 중복 입력 방지를 위해 `aliases.yaml`에서 `참여기간` 삭제.  
결과: 수직 Key-Value 레이아웃에서 `참여기간` → `[기간값]` 구조를 사용하는 템플릿  
(sample-3 등 5개 파일에서 67% fuzzy로 감지, threshold 미달)에서 미채움 발생.

---

## 4. 오매핑 위험 (False Positive)

### [F-1] `프로젝트 상세설명` → `projects.0.name` (score 80%)
sample-3 Table 6에서 12번 반복 등장.  
"프로젝트"가 두 문자열에 공통으로 포함돼 유사도가 부풀려짐.  
실제로는 설명/내용 필드인데 프로젝트명 데이터로 채워질 위험.

**수정 필요**: `aliases.yaml`에 명시적 매핑 추가
```yaml
projects.0.description:
  - 프로젝트 상세설명
```

### [F-2] 교육 테이블의 `시작일`/`종료일` → 프로젝트 날짜 입력
`writer.py`의 below fallback이 교육 테이블의 열 헤더 셀을 row label로 오인.  
`시작일`(col 1) 오른쪽이 `종료일`(label)에 막혀 아래 행에 `21.03` 입력.

**수정 필요**: below fallback을 col 0에만 적용 (`writer.py` `_find_value_cell`, L214)

---

## 5. 미매핑 라벨 현황 (cross-file 빈도순)

아래 라벨들은 현재 `aliases.yaml`에 없어 채워지지 않음.  
분류: **A** = aliases만 추가하면 해결 / **B** = profile 구조 신설 필요 / **C** = 검토 필요

| 빈도 | 라벨 | fuzzy 최고점 | 분류 | 권장 매핑 |
|---|---|---|---|---|
| 8x | `자격증` | 33% | B | `certifications` 섹션 신설 |
| 7x | `근무회사` | 29% | B | `career.company` 신설 |
| 7x | `사진` | 40% | — | 입력 불필요 (이미지 셀) |
| 5x | `참여기간` | 67% | A\* | `projects.0.period` 재추가 검토 (트레이드오프 §6 참조) |
| 5x | `과 졸업` | 44% | B | `education.graduation` 신설 |
| 5x | `(사진)` | 46% | — | 입력 불필요 (이미지 셀) |
| 4x | `회사명` | 67% | B | `career.company` 신설 |
| 4x | `학력` | 50% | B | `education` 섹션 신설 |
| 4x | `교육` | 0% | B | `education` 섹션 신설 |
| 4x | `병역` | 50% | B | `basic.military` 신설 |
| 4x | `고객사` | 33% | B | `projects.0.client` 신설 |
| 4x | `yyyy.mm ~ yyyy.mm` | 19% | — | placeholder 텍스트, 입력 불필요 |
| 3x | `성    명` | 67% | A | `basic.name` aliases에 추가 |
| 3x | `근무기간` | 67% | A | `projects.0.period` aliases에 추가 |
| 3x | `성 별` | 67% | B | `basic.gender` 신설 |
| 3x | `E-Mail` | 33% | B | `basic.email` 신설 |
| 3x | `주    소` | 46% | B | `basic.address` 신설 |
| 3x | `취득일` | 40% | B | `certifications.date` 신설 |
| 3x | `교  육  명` | 43% | B | `education.name` 신설 |
| 3x | `기    관` | 46% | B | `education.institution` 신설 |
| 3x | `숙련도` | 29% | — | 숙련도(상/중/하) 입력값 profile 미정의 |
| 3x | `DBMS` | 0% | B | `skills.dbms` 신설 또는 skills 하위 분류 |
| 3x | `기타` | 50% | — | 맥락 불명확, 개별 판단 필요 |
| 3x | `수상` | 40% | B | `awards` 섹션 신설 |
| 3x | `근무기간` | 67% | A | `projects.0.period` aliases에 추가 |
| 3x | `부서명/최종직위` | 20% | B | `career.department`, `career.title` 신설 |
| 3x | `회사정보(요약)` | 29% | — | 자유기술 항목, 자동화 어려움 |
| 2x | `직위` | 29% | B | `career.title` 신설 |
| 2x | `자 격 증 명` | 43% | B | `certifications` 섹션 신설 |
| 2x | `졸업 년 월` | 62% | B | `education.graduation` 신설 |
| 2x | `회  사  명` | 43% | B | `career.company` aliases에 추가 |

\* `참여기간`: 수직 테이블에서는 aliases 재추가 유효, 수평 테이블에서는 제외 필요 (§6 트레이드오프 참조)

### 분류 요약

| 분류 | 건수 | 조치 |
|---|---|---|
| A (aliases 추가만으로 해결) | 4종 | `성    명`, `근무기간`, `회  사  명`, `참여기간`(조건부) |
| B (profile 구조 신설 필요) | 16종 | 학력, 자격증, 경력이력, 개인정보 확장 등 |
| 입력 불필요 / 자동화 한계 | 7종 | 사진 셀, placeholder, 자유기술 항목 |

---

## 6. 트레이드오프

| 결정 포인트 | 현재 값 | 낮추면 | 높이면 |
|---|---|---|---|
| fuzzy threshold | 75% | 오매핑 증가 (`프로젝트 상세설명` 등) | `성명 (한글)` 62% 같은 경계값 탈락 |
| 헤더행 감지 기준 | ≥ 3 라벨 | 기본정보 행 스킵 위험 | 2-라벨 교육헤더 미감지 → 잘못된 fill |
| below fallback 범위 | 전체 열 (버그) | col 0에만 적용하면 교육헤더 문제 해결 | 단일 열 레이아웃 일부 미지원 가능 |
| `참여기간` alias | 제거됨 | 재추가 시 수평테이블 중복 입력 재발 | 제거 유지 시 5개 파일 미채움 |

`참여기간` 트레이드오프 상세:
- 현재 제거 이유: 수평 테이블 col_map 빌드 시 col 1이 `period`(start~end)로 매핑돼  
  `종료일` col 2와 중복 데이터 입력 발생
- 재추가 허용 조건: 수평 테이블과 수직 테이블에서 동작이 달라야 함  
  → `_build_col_map`에서 해당 alias를 제외하고, 수직 fill에서만 사용하는 구조로 분리 가능

---

## 7. 우선순위별 액션 아이템

### 즉시 (aliases.yaml, 코드 변경 없음)
- [ ] `성    명`, `근무기간`, `근무기간` → `basic.name`, `projects.0.period` 추가
- [ ] `프로젝트 상세설명` → `projects.0.description` 추가

### 단기 (버그 수정, writer.py)
- [ ] `_find_value_cell` below fallback을 col 0에만 적용 (L214)
- [ ] `참여기간` 수직/수평 분리 처리 설계

### 단기 (profile 구조 확장)
- [ ] `basic` 섹션에 `email`, `phone`, `address`, `gender` 추가
- [ ] `education` 섹션 신설 (학교명, 학과, 졸업년월)
- [ ] `certifications` 섹션 신설 (자격증명, 취득일, 발행처)
- [ ] `career` 섹션 신설 (회사명, 근무기간, 직위, 담당업무)

### 중기
- [ ] 단락형 이력서 지원 — Bold 텍스트 + 패턴으로 라벨 감지
- [ ] DOC→DOCX 변환 품질 검증 루틴 (셀 수/단락 수 기준 경고)
- [ ] 프로젝트 반복 블록(비표준) 구조 지원

---

## 8. 현재 툴 실효성 평가

| 파일 | 구조 | 예상 커버리지 |
|---|---|---|
| resume_sample.docx | 수직+수평 | **높음** (검증 완료) |
| resume_sample-3.docx | 수직+수평(복합) | **중간** (aliases 추가 후 높음) |
| resume_sample-4.docx | 수직+수평 | **중간** (변환 품질 확인 필요) |
| resume_sample-5.docx | 단일 초대형 | **낮음** (aliases 추가로 개선 가능) |
| resume_sample-2.docx | 단락형 | **불가** |
| resume_sample-6.docx | 단락형+테이블 1개 | **불가** |
| resume_sample-7.docx | 동의서+단락형 | **불가** |
| resume_sample-8.docx | 복합+단락형 | **매우 낮음** |
| resume_sample-9.docx | 단락형 | **불가** |

9개 중 aliases 확장 없이 유의미하게 동작하는 파일: **1개 (11%)**  
aliases 확장 후 유의미하게 동작 가능한 파일: **3~4개 (33~44%)**  
구조적 한계로 지원 불가한 파일: **4~5개 (44~55%)**
