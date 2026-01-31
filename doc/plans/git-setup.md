# Git Setup Work Plan

## Overview

RoundtableTrading 프로젝트의 Git 초기 설정 및 GitHub 연동 작업 계획서입니다.

**Goal**: Git 저장소 초기화, pre-commit hooks 설정, GitHub remote 연결, initial commit 완료

**Estimated Time**: 30분

---

## Prerequisites

- [x] Git 설치 확인
- [x] GitHub CLI (gh) 설치 확인
- [x] GitHub repository 생성 완료: `https://github.com/toddnehd/RoundtableTrading.git`
- [x] Git workflow 문서 작성 완료: `doc/git-workflow.md`

---

## Tasks

### Task 1: Update .gitignore

**Parallelizable**: No (단독 작업)

**Description**: Python 프로젝트에 맞는 포괄적인 .gitignore 파일 생성

**Files to modify**:
- `.gitignore`

**Requirements**:
- Python 관련 파일 제외 (__pycache__, *.pyc, .venv 등)
- IDE 관련 파일 제외 (.idea, .vscode 등)
- 환경 변수 파일 제외 (.env, .env.local 등)
- 로그 파일 제외 (logs/, *.log)
- 테스트 캐시 제외 (.pytest_cache, .mypy_cache 등)
- 민감 정보 파일 제외 (credentials.json, *.pem, *.key)

**Acceptance Criteria**:
- [ ] .gitignore 파일이 모든 필수 패턴 포함
- [ ] git status 실행 시 불필요한 파일이 untracked로 표시되지 않음

---

### Task 2: Setup Pre-commit Hooks

**Parallelizable**: No (Task 1 이후)

**Description**: ruff (lint + format) + mypy (type check) pre-commit hooks 설정

**Files to create**:
- `.pre-commit-config.yaml`

**Requirements**:
- ruff check (linting)
- ruff format (formatting)
- mypy (type checking)
- Python 3.13 호환

**Configuration**:
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.4
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.13.0
    hooks:
      - id: mypy
        additional_dependencies: [pydantic-settings, types-requests]
```

**Commands to run**:
```bash
uv pip install pre-commit
pre-commit install
pre-commit run --all-files  # 초기 실행
```

**Acceptance Criteria**:
- [ ] .pre-commit-config.yaml 파일 생성
- [ ] pre-commit hooks 설치 완료
- [ ] 초기 실행 시 모든 파일 검증 통과

---

### Task 3: Configure Git Repository

**Parallelizable**: No (Task 2 이후)

**Description**: Git 저장소 설정 및 GitHub remote 연결

**Commands to run**:
```bash
# Git 사용자 정보 확인 (이미 설정되어 있으면 스킵)
git config user.name || git config --global user.name "Your Name"
git config user.email || git config --global user.email "your.email@example.com"

# Remote 추가
git remote add origin https://github.com/toddnehd/RoundtableTrading.git

# Default branch 확인
git branch -M main
```

**Acceptance Criteria**:
- [ ] Git 사용자 정보 설정 확인
- [ ] Remote origin 추가 완료
- [ ] Default branch가 main으로 설정

---

### Task 4: Create Initial Commit

**Parallelizable**: No (Task 3 이후)

**Description**: 현재 프로젝트 상태를 initial commit으로 생성

**Files to stage**:
- All project files except those in .gitignore

**Commit message**:
```
chore: initial project setup

- Python 3.13 + uv package manager
- PostgreSQL + TimescaleDB + Redis (Docker)
- Project structure (src/, tests/, scripts/, streamlit_app/, notebooks/)
- Configuration files (pyproject.toml, .env.example, Makefile)
- Database schema (8 tables with TimescaleDB hypertable)
- 170 packages installed
- Git workflow documentation
```

**Commands to run**:
```bash
git add .
git commit -m "chore: initial project setup

- Python 3.13 + uv package manager
- PostgreSQL + TimescaleDB + Redis (Docker)
- Project structure (src/, tests/, scripts/, streamlit_app/, notebooks/)
- Configuration files (pyproject.toml, .env.example, Makefile)
- Database schema (8 tables with TimescaleDB hypertable)
- 170 packages installed
- Git workflow documentation"
```

**Acceptance Criteria**:
- [ ] 모든 필요한 파일이 staging area에 추가됨
- [ ] .gitignore에 명시된 파일은 제외됨
- [ ] Commit message가 규칙에 맞게 작성됨
- [ ] Commit 생성 완료

---

### Task 5: Push to GitHub

**Parallelizable**: No (Task 4 이후)

**Description**: Initial commit을 GitHub에 push

**Commands to run**:
```bash
git push -u origin main
```

**Acceptance Criteria**:
- [ ] GitHub에 main 브랜치 push 완료
- [ ] GitHub 웹에서 파일 확인 가능
- [ ] Commit 히스토리 확인 가능

---

### Task 6: Verify Setup

**Parallelizable**: No (Task 5 이후)

**Description**: Git 설정이 올바르게 완료되었는지 검증

**Verification steps**:
```bash
# Remote 확인
git remote -v

# Branch 확인
git branch -a

# Pre-commit hooks 확인
pre-commit --version
ls -la .git/hooks/pre-commit

# GitHub 연결 확인
gh repo view toddnehd/RoundtableTrading
```

**Acceptance Criteria**:
- [ ] Remote origin이 올바르게 설정됨
- [ ] main 브랜치가 origin/main과 연결됨
- [ ] Pre-commit hooks가 설치됨
- [ ] GitHub에서 저장소 확인 가능

---

## Success Criteria

전체 작업 완료 조건:

1. ✅ .gitignore가 모든 필수 패턴 포함
2. ✅ Pre-commit hooks (ruff + mypy) 설치 및 작동
3. ✅ Git remote가 GitHub에 연결됨
4. ✅ Initial commit이 GitHub에 push됨
5. ✅ 모든 검증 단계 통과

---

## Rollback Plan

문제 발생 시:

1. **Pre-commit 실패**: `pre-commit uninstall` 후 재설정
2. **Push 실패**: Remote URL 확인 및 재설정
3. **Commit 수정 필요**: `git commit --amend` (push 전에만)

---

## Notes

### Important

- .env 파일은 절대 커밋하지 않음 (.gitignore에 포함)
- doc/plans/ 디렉토리는 계획서 저장용 (커밋됨)
- Initial commit은 squash 없이 그대로 유지

### References

- Git workflow: `doc/git-workflow.md`
- Commit message convention: Conventional Commits
- Branch naming: feature/, fix/, refactor/ 등

---

**Created**: 2026-01-29
**Status**: Ready for execution
