# pyenv 환경 구성 가이드

## 전제 조건

- OS: macOS (Apple Silicon)
- Shell: zsh
- Homebrew: `/opt/homebrew` 에 설치됨
- 현재 Python: 3.9.6 (macOS 내장), 3.12.13 (Homebrew)
- pyenv: 미설치 상태

---

## Step 1. pyenv 설치

```bash
brew install pyenv
```

설치 확인:

```bash
pyenv --version
```

예상 출력: `pyenv 2.x.x` (버전 숫자는 다를 수 있음)

---

## Step 2. zshrc에 pyenv 초기화 설정 추가

아래 세 줄이 `~/.zshrc`에 없을 경우에만 추가한다.

```bash
grep -q 'PYENV_ROOT' ~/.zshrc || echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
grep -q 'pyenv/bin' ~/.zshrc || echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
grep -q 'pyenv init' ~/.zshrc || echo 'eval "$(pyenv init -)"' >> ~/.zshrc
```

설정 적용:

```bash
source ~/.zshrc
```

적용 확인:

```bash
which python
```

예상 출력: `/Users/neisii/.pyenv/shims/python` (shims 경로여야 정상)

---

## Step 3. Python 버전 설치

이 프로젝트에서 사용할 버전을 설치한다.

```bash
pyenv install 3.12.13
```

> 이미 Homebrew로 3.12.13이 설치되어 있어도, pyenv는 별도 경로(`~/.pyenv/versions/`)에 독립적으로 설치한다.

설치 확인:

```bash
pyenv versions
```

예상 출력:
```
  system
* 3.12.13 (set by ...)
```

---

## Step 4. 프로젝트 디렉터리에 버전 고정

```bash
cd /Users/neisii/Development/resume-auto-fill
pyenv local 3.12.13
```

고정 확인 (`.python-version` 파일 생성 여부):

```bash
cat .python-version
```

예상 출력: `3.12.13`

현재 활성 버전 확인:

```bash
python --version
```

예상 출력: `Python 3.12.13`

---

## Step 5. venv 생성 및 활성화

```bash
cd /Users/neisii/Development/resume-auto-fill
python -m venv .venv
source .venv/bin/activate
```

활성화 확인:

```bash
which python
python --version
```

예상 출력:
```
/Users/neisii/Development/resume-auto-fill/.venv/bin/python
Python 3.12.13
```

---

## Step 6. 패키지 설치 (프로젝트 시작 시)

```bash
# 개별 설치
pip install <패키지명>

# requirements.txt가 있는 경우
pip install -r requirements.txt

# 현재 설치된 패키지 저장
pip freeze > requirements.txt
```

---

## 이후 작업 시 진입 절차

터미널을 새로 열 때마다 venv를 활성화해야 한다.

```bash
cd /Users/neisii/Development/resume-auto-fill
source .venv/bin/activate
```

비활성화:

```bash
deactivate
```

---

## .gitignore 권장 설정

`.venv/`는 git에 포함하지 않고, `.python-version`은 포함한다.

```
# .gitignore
.venv/
```

`.python-version` 파일은 커밋하면 팀원 또는 다른 환경에서도 동일한 Python 버전을 자동 적용할 수 있다.

---

## 트러블슈팅

**`pyenv: command not found`**
→ Step 2의 `source ~/.zshrc`를 재실행하거나 터미널을 재시작한다.

**`which python`이 shims 경로가 아닌 경우**
→ `~/.zshrc`에서 pyenv 관련 세 줄이 다른 `PATH` 설정보다 **뒤에** 위치하는지 확인한다. 파일 맨 끝에 있어야 한다.

**`pyenv install` 중 빌드 오류**
→ Xcode Command Line Tools가 필요할 수 있다.
```bash
xcode-select --install
```
