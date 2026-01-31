# Git Workflow Guide

## Overview

RoundtableTrading 프로젝트의 Git 관리 전략 및 AI 에이전트 협업 가이드입니다.

---

## Workflow Strategy

**Feature Branch + Squash Merge** 전략을 사용합니다.

```
main ─────────────────────────●─────────────────●
                             ↑                 ↑
                        squash merge      squash merge
                             │                 │
feature/data ────●──●──●──●──┘                 │
                                               │
feature/agents ─────────●──●──●──●─────────────┘
```

---

## Complete Workflow

### 0. Issue 생성 (선택사항)

GitHub에서 작업할 기능/버그를 Issue로 기록합니다.

### 1. 기능 명세 및 작업 계획 정의

**참여자**: 사용자 + AI

**작업**:
- 요구사항 인터뷰
- 작업 계획서 작성: `doc/plans/{feature-name}.md`
- 산출물: PR 단위의 작업 계획서

### 2. AI Agent 구현 작업

**명령**: `/start-work`

**작업 순서**:
1. `git checkout main && git pull origin main` - main 최신화
2. `git checkout -b feature/{name}` - feature branch 생성
3. 계획서에 따라 구현 (커밋 단위로)
4. Pre-commit 검증 (ruff, mypy)
5. 테스트 실행 및 통과 확인
6. `git push origin feature/{name}` - remote에 push
7. `gh pr create` - PR 생성 (계획서 링크 포함)

### 3. PR 검토

**참여자**: 사용자

**검토 항목**:
- 코드 변경 내용 확인
- 테스트 결과 확인
- 불필요한 변경 없음 확인

**결과**:
- **승인**: Squash and Merge → Branch 삭제
- **수정 요청**: PR에 코멘트 작성 → AI가 피드백 반영 → 다시 검토

---

## Branch Naming Convention

| 타입 | 형식 | 예시 | 용도 |
|------|------|------|------|
| Feature | `feature/{기능명}` | `feature/data-collection` | 새로운 기능 개발 |
| Fix | `fix/{버그명}` | `fix/api-timeout` | 버그 수정 |
| Refactor | `refactor/{대상}` | `refactor/agent-base` | 리팩토링 |
| Docs | `docs/{문서명}` | `docs/api-guide` | 문서 작업 |
| Test | `test/{테스트명}` | `test/kis-api` | 테스트 추가 |

---

## Commit Message Convention

### Format

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Type

| Type | 설명 | 예시 |
|------|------|------|
| `feat` | 새로운 기능 추가 | `feat(data): add KIS API client` |
| `fix` | 버그 수정 | `fix(data): handle rate limiting` |
| `refactor` | 코드 리팩토링 | `refactor(agents): simplify prompt` |
| `test` | 테스트 추가/수정 | `test(data): add API client tests` |
| `docs` | 문서 수정 | `docs(readme): update setup guide` |
| `style` | 코드 포맷팅 | `style(agents): apply ruff format` |
| `chore` | 기타 작업 | `chore(deps): update dependencies` |
| `perf` | 성능 개선 | `perf(backtest): optimize loop` |

### Scope

프로젝트 모듈명을 사용합니다:

- `agents` - AI 에이전트 모듈
- `data` - 데이터 수집/처리
- `debate` - 토론 시스템
- `backtest` - 백테스팅 엔진
- `ui` - Streamlit UI
- `config` - 설정 관리
- `db` - 데이터베이스

### Examples

```bash
feat(data): add KIS API authentication
fix(agents): resolve prompt token overflow
refactor(debate): extract consensus logic
test(backtest): add portfolio calculation tests
docs(api): document KIS API endpoints
chore(docker): update PostgreSQL to 16.2
```

---

## PR Title Convention

### Format

```
[Type] 간결한 설명
```

### Examples

```
[Feature] 한국투자증권 API 연동
[Fix] API 타임아웃 처리 개선
[Refactor] 에이전트 베이스 클래스 구조 개선
[Test] 백테스팅 엔진 테스트 추가
[Docs] API 사용 가이드 작성
```

---

## PR Description Template

PR 생성 시 아래 템플릿을 사용합니다:

```markdown
## Summary
이 PR이 해결하는 문제와 구현 내용을 간략히 설명합니다.

## Related
- Issue: #123 (있는 경우)
- Plan: `doc/plans/{feature-name}.md`

## Changes
- 주요 변경사항 1
- 주요 변경사항 2
- 주요 변경사항 3

## Testing
- [ ] 로컬 테스트 통과
- [ ] Pre-commit hooks 통과 (ruff, mypy)
- [ ] 관련 테스트 추가/수정

## Screenshots (UI 변경 시)
(스크린샷 첨부)

## Notes
리뷰어가 특별히 확인해야 할 사항이나 추가 설명
```

---

## Pre-commit Checklist

AI 에이전트가 PR 생성 전 확인해야 할 사항:

- [ ] main 브랜치 최신화 완료
- [ ] feature branch에서 작업 완료
- [ ] 모든 커밋 메시지 규칙 준수
- [ ] `ruff check` 통과
- [ ] `ruff format` 적용
- [ ] `mypy` 타입 검사 통과
- [ ] 관련 테스트 통과 (있는 경우)
- [ ] PR 설명에 계획서 링크 포함

---

## Merge Checklist

사용자가 PR 병합 전 확인해야 할 사항:

- [ ] 코드 변경 내용 확인
- [ ] 불필요한 변경 없음 확인
- [ ] 테스트 통과 확인
- [ ] **Squash and Merge** 선택
- [ ] Merge 후 feature branch 삭제

---

## Branch Protection Rules

GitHub에서 main 브랜치에 적용할 보호 규칙:

1. **Require pull request before merging**
   - Require approvals: 1 (본인 승인 가능)
   
2. **Require status checks to pass**
   - CI/CD 설정 시 추가

3. **Do not allow bypassing the above settings**

---

## Remote Repository

```
https://github.com/toddnehd/RoundtableTrading.git
```

---

## Quick Commands

### 새 기능 시작
```bash
git checkout main
git pull origin main
git checkout -b feature/new-feature
```

### 작업 중 커밋
```bash
git add .
git commit -m "feat(scope): description"
```

### PR 생성
```bash
git push origin feature/new-feature
gh pr create --title "[Feature] 설명" --body "$(cat doc/plans/feature.md)"
```

### PR 병합 후
```bash
git checkout main
git pull origin main
git branch -d feature/new-feature
```

---

## Tips

### AI 작업 추적
- 각 AI 작업 세션은 하나의 feature branch
- 작업 계획서는 `doc/plans/`에 보관
- PR에 계획서 링크를 포함하여 작업 맥락 유지

### 커밋 단위
- 논리적으로 독립적인 변경사항 단위로 커밋
- 하나의 커밋은 하나의 목적만 가짐
- 너무 크지 않게 (파일 10개 이하 권장)

### Squash Merge 이유
- main 브랜치 히스토리를 깔끔하게 유지
- 세부 작업 과정은 feature branch에 보존
- 롤백이 용이함

---

## Troubleshooting

### Merge Conflict 발생 시
```bash
git checkout main
git pull origin main
git checkout feature/your-feature
git merge main
# 충돌 해결
git add .
git commit -m "chore: resolve merge conflicts"
git push origin feature/your-feature
```

### 잘못된 브랜치에서 작업한 경우
```bash
git stash
git checkout -b feature/correct-branch
git stash pop
```

### 커밋 메시지 수정 (push 전)
```bash
git commit --amend -m "올바른 메시지"
```

---

**Last Updated**: 2026-01-29
