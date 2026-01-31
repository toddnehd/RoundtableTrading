# Work Plans

RoundtableTrading 프로젝트의 작업 계획서 관리 디렉토리입니다.

---

## 📋 계획서 목록

### Strategic Plans (장기 전략)
장기적인 프로젝트 로드맵 및 Phase 계획

- **`phase1-mvp.md`** - Phase 1 MVP 개발 계획 (8주) [🚧 IN PROGRESS]
  - 목표 기간: 2026-01-27 ~ 2026-03-27
  - 현재 진행: Week 0 완료

### Work Plans (실행 작업)
단기 실행 작업 계획서 (AI 에이전트가 생성 및 실행)

- **`git-setup.md`** - Git 초기 설정 및 GitHub 연동 [✅ COMPLETED - 2026-01-31]
  - 예상 시간: 30분 / 실제 시간: 25분
  - 완료 커밋: `ac5f100`

---

## 📊 Current Status

| Status | Count | Plans |
|--------|-------|-------|
| ✅ Completed | 1 | git-setup |
| 🚧 In Progress | 1 | phase1-mvp (Week 0 완료) |
| 📋 Next | 0 | - |

### Next Steps

Week 1-2 작업 계획:
- 데이터 수집 모듈 구현 (한국투자증권 API)
- 데이터베이스 모델 정의
- 데이터 수집 스크립트 작성

---

## 📝 Naming Convention

### Strategic Plans
```
{phase}-{scope}.md

예시:
- phase1-mvp.md
- phase2-optimization.md
```

### Tactical Work Plans
```
{feature}-{action}.md

예시:
- data-collection-setup.md
- agent-fundamental-impl.md
- backtest-engine-core.md
```

---

## 🔄 Lifecycle Management

### 계획서 상태

1. **생성**: Prometheus 에이전트가 작업 계획서 생성
2. **실행**: Sisyphus 에이전트가 계획서에 따라 작업 수행
3. **완료**: 모든 Task 완료 후 상태 업데이트

### 완료된 계획서 처리

완료된 계획서는 **삭제하지 않고 유지**합니다:
- 향후 참고 문서로 활용
- Git 히스토리에서 작업 과정 추적
- 유사 작업 수행 시 템플릿으로 사용

### 상태 업데이트

이 README.md의 "📊 Current Status" 섹션을 수동으로 업데이트:
1. 계획서 완료 시: Completed 섹션에 추가
2. 새 계획 시작 시: In Progress 업데이트
3. 다음 작업 예정 시: Next 섹션에 기록

---

## 🔗 References

- **Git Workflow**: `../git-workflow.md` - Git 작업 규칙 및 PR 가이드
- **PRD**: `../prd/prd.md` - 제품 요구사항 명세
- **Phase 1 Plan**: `phase1-mvp.md` - 현재 진행 중인 Phase 계획

---

## 💡 Tips

### 계획서 작성 시

1. **목표 명확화**: 작업의 목적과 예상 결과 명시
2. **Task 분해**: 작은 단위로 나누어 진행 상황 추적 용이하게
3. **검증 기준**: 각 Task의 완료 조건 (Acceptance Criteria) 명시
4. **예상 시간**: 현실적인 시간 추정

### 계획서 실행 시

1. **TODO 활용**: `todowrite` 도구로 진행 상황 실시간 추적
2. **검증 필수**: 각 Task 완료 후 반드시 검증
3. **문서화**: 중요한 결정사항이나 문제 해결 과정 기록

### AI 에이전트 사용

- Prometheus: 계획 수립
- Sisyphus: 계획 실행
- Oracle: 복잡한 아키텍처 결정 상담

---

**Last Updated**: 2026-01-31
