# Phase 1 MVP 개발 계획
# RoundtableTrading - 점진적 구축 전략

**버전**: v1.0  
**작성일**: 2026-01-27  
**목표 기간**: 8주 (2개월)  
**관련 문서**: prd.md, prd-addendum.md

---

## 📊 진행 상황 요약

### 전체 진행률

| Week | 기간 | 주제 | 핵심 작업 | 상태 | 완료율 |
|------|------|------|-----------|------|--------|
| **Week 0** | 사전 준비 | 환경 설정 | 프로젝트 구조, Docker, DB 스키마, Git 설정 | ✅ 완료 | 100% |
| **Week 1-2** | 2주 | 데이터 파이프라인 | KIS API 연동, DB 모델, 데이터 수집 스크립트 | 📋 대기 | 0% |
| **Week 3-4** | 2주 | 단일 에이전트 | LLM 클라이언트, 기술적 분석 에이전트, 프롬프트 | 📋 대기 | 0% |
| **Week 5-6** | 2주 | 멀티 에이전트 | 5개 에이전트, 토론 엔진, 합의 메커니즘 | 📋 대기 | 0% |
| **Week 7** | 1주 | 백테스팅 | 백테스팅 엔진, 성과 지표, Walk-forward | 📋 대기 | 0% |
| **Week 8** | 1주 | UI & 통합 | Streamlit 대시보드, 통합 테스트, 문서화 | 📋 대기 | 0% |

**전체 진행률**: 12.5% (1/8 단계 완료)

---

### Week별 상세 요약

<details>
<summary><b>✅ Week 0: 사전 준비 (환경 설정)</b> - 완료</summary>

**목표**: 로컬 개발 환경 완벽 구축

**완료 항목**:
- ✅ 프로젝트 구조 생성 (src/, tests/, scripts/, streamlit_app/, notebooks/)
- ✅ Python 3.13 + uv 패키지 매니저 설정
- ✅ Docker Compose (PostgreSQL + TimescaleDB + Redis)
- ✅ 데이터베이스 스키마 (8개 테이블)
- ✅ 170개 패키지 설치
- ✅ Git 설정 및 GitHub 연동
- ✅ Pre-commit hooks (ruff + mypy)

**산출물**:
- pyproject.toml, docker-compose.yml, Makefile
- scripts/init_db.sql
- .gitignore, .pre-commit-config.yaml
- doc/git-workflow.md

**완료일**: 2026-01-31

</details>

<details>
<summary><b>📋 Week 1-2: 데이터 수집 파이프라인</b> - 대기중</summary>

**목표**: 안정적인 데이터 수집 및 저장 시스템 구축

**주요 작업**:
- [ ] 한국투자증권 API 클라이언트 구현
- [ ] 데이터베이스 모델 정의 (SQLAlchemy ORM)
- [ ] 종목 정보 수집 스크립트
- [ ] 일봉 데이터 수집 스크립트
- [ ] 데이터 검증 및 테스트

**예상 산출물**:
- src/data/kis_api.py
- src/data/models.py
- scripts/collect_stocks.py
- scripts/collect_daily_prices.py
- tests/test_data_collection.py

</details>

<details>
<summary><b>📋 Week 3-4: 단일 에이전트 프로토타입</b> - 대기중</summary>

**목표**: 하나의 에이전트를 완벽하게 구현하여 패턴 확립

**주요 작업**:
- [ ] LLM 클라이언트 추상화 (Claude, GPT 지원)
- [ ] BaseAgent 클래스 설계
- [ ] 기술적 분석 에이전트 구현
- [ ] 프롬프트 엔지니어링
- [ ] 단위 테스트 작성

**예상 산출물**:
- src/agents/llm/base.py
- src/agents/base.py
- src/agents/technical.py
- tests/test_agents.py

</details>

<details>
<summary><b>📋 Week 5-6: 멀티 에이전트 협업 시스템</b> - 대기중</summary>

**목표**: 5개 에이전트 구현 및 토론 메커니즘 완성

**주요 작업**:
- [ ] 나머지 4개 에이전트 구현 (기업가치, 시장, 리스크, 조정자)
- [ ] 토론 엔진 구현 (5단계 프로토콜)
- [ ] 합의 메커니즘 구현
- [ ] 통합 테스트

**예상 산출물**:
- src/agents/fundamental.py
- src/agents/market.py
- src/agents/risk.py
- src/agents/moderator.py
- src/debate/engine.py
- src/debate/consensus.py

</details>

<details>
<summary><b>📋 Week 7: 백테스팅 엔진</b> - 대기중</summary>

**목표**: 과거 데이터로 전략 성과 검증

**주요 작업**:
- [ ] 백테스팅 엔진 구현
- [ ] 거래 비용 반영
- [ ] 성과 지표 계산 (Sharpe, MDD, Win Rate)
- [ ] Walk-forward 분석

**예상 산출물**:
- src/backtest/engine.py
- src/backtest/metrics.py
- tests/test_backtest.py

</details>

<details>
<summary><b>📋 Week 8: Streamlit UI 및 통합</b> - 대기중</summary>

**목표**: 사용자 인터페이스 완성 및 전체 시스템 통합

**주요 작업**:
- [ ] Streamlit 대시보드 구현
- [ ] 전체 시스템 통합 테스트
- [ ] 문서 작성 (README, 사용 가이드)
- [ ] 배포 준비

**예상 산출물**:
- streamlit_app/app.py
- streamlit_app/pages/
- README.md
- docs/user-guide.md

</details>

---

### 다음 작업

**현재 위치**: Week 0 완료  
**다음 단계**: Week 1-2 데이터 수집 파이프라인

**즉시 시작 가능한 작업**:
1. 한국투자증권 API 키 발급
2. KIS API 클라이언트 구현
3. 데이터베이스 모델 정의

## 📋 개요

### MVP 철학
- **처음부터 완벽을 추구하지 않음**
- **작동하는 최소 기능부터 구현**
- **점진적으로 기능 추가 및 개선**
- **각 단계마다 검증 및 테스트**

### 핵심 목표
1. ✅ 환경 설정 및 인프라 구축
2. ✅ 데이터 수집 파이프라인 구축
3. ✅ 단일 에이전트 프로토타입 완성
4. ✅ 멀티 에이전트 협업 시스템 구축
5. ✅ 백테스팅 및 검증

---

## 🏗️ Week 0: 사전 준비 (환경 설정)

### 목표
로컬 개발 환경 완벽 구축 - 이후 개발의 기반

### 작업 목록

#### 1. 프로젝트 구조 생성

```bash
RoundtableTrading/
├── .env.example              # 환경 변수 템플릿
├── .gitignore
├── README.md
├── pyproject.toml            # uv 프로젝트 설정
├── docker-compose.yml        # 미들웨어 구성
├── Makefile                  # 편의 명령어
│
├── src/
│   ├── __init__.py
│   ├── agents/              # 에이전트 모듈
│   ├── data/                # 데이터 수집/처리
│   ├── debate/              # 토론 시스템
│   ├── backtest/            # 백테스팅
│   ├── utils/               # 유틸리티
│   └── config.py            # 설정 관리
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
│
├── scripts/                 # 유틸리티 스크립트
│   ├── init_db.py
│   └── seed_data.py
│
├── notebooks/               # 실험용 Jupyter
│
├── docs/                    # 문서
│   ├── idea/
│   ├── prd/
│   └── plan/
│
└── streamlit_app/           # Streamlit UI
    ├── app.py
    └── pages/
```

#### 2. uv 프로젝트 초기화

```bash
# uv 설치 (macOS)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 프로젝트 초기화
cd RoundtableTrading
uv init

# Python 3.11 설정
uv python install 3.11
uv venv --python 3.11

# 기본 의존성 추가
uv add python-dotenv pydantic loguru
```

**pyproject.toml 예시**:
```toml
[project]
name = "roundtable-trading"
version = "0.1.0"
description = "Multi-Agent Stock Trading System"
requires-python = ">=3.11"
dependencies = [
    "python-dotenv>=1.0.0",
    "pydantic>=2.5.0",
    "loguru>=0.7.0",
    "asyncio>=3.4.3",
    "httpx>=0.25.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.1.0",
    "mypy>=1.7.0",
]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

#### 3. Docker Compose 설정

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  postgres:
    image: timescale/timescaledb:latest-pg16
    container_name: roundtable_postgres
    environment:
      POSTGRES_DB: roundtable
      POSTGRES_USER: roundtable_user
      POSTGRES_PASSWORD: roundtable_pass
      POSTGRES_HOST_AUTH_METHOD: trust
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init_db.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U roundtable_user -d roundtable"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: roundtable_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  # Phase 2 이후 추가 예정
  # pgadmin:
  #   image: dpage/pgadmin4:latest
  #   container_name: roundtable_pgadmin
  #   environment:
  #     PGADMIN_DEFAULT_EMAIL: admin@roundtable.local
  #     PGADMIN_DEFAULT_PASSWORD: admin
  #   ports:
  #     - "5050:80"
  #   depends_on:
  #     - postgres

volumes:
  postgres_data:
  redis_data:

networks:
  default:
    name: roundtable_network
```

#### 4. 데이터베이스 스키마 초기화

**scripts/init_db.sql**:
```sql
-- TimescaleDB 확장 활성화
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- 종목 기본 정보
CREATE TABLE IF NOT EXISTS stocks (
    ticker VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    sector VARCHAR(50),
    market VARCHAR(10) CHECK (market IN ('KOSPI', 'KOSDAQ')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 일봉 데이터 (TimescaleDB 하이퍼테이블)
CREATE TABLE IF NOT EXISTS daily_prices (
    ticker VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    open INTEGER,
    high INTEGER,
    low INTEGER,
    close INTEGER,
    volume BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (ticker, date),
    FOREIGN KEY (ticker) REFERENCES stocks(ticker) ON DELETE CASCADE
);

-- TimescaleDB 하이퍼테이블로 변환
SELECT create_hypertable('daily_prices', 'date', if_not_exists => TRUE);

-- 에이전트 의견
CREATE TABLE IF NOT EXISTS agent_opinions (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    agent_name VARCHAR(50) NOT NULL,
    opinion VARCHAR(20) CHECK (opinion IN ('매수', '중립', '매도')),
    score INTEGER CHECK (score >= 0 AND score <= 100),
    reasoning JSONB,
    timeframe VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (ticker) REFERENCES stocks(ticker) ON DELETE CASCADE
);

CREATE INDEX idx_agent_opinions_ticker ON agent_opinions(ticker);
CREATE INDEX idx_agent_opinions_created_at ON agent_opinions(created_at DESC);

-- 토론 기록
CREATE TABLE IF NOT EXISTS debates (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    round INTEGER DEFAULT 1,
    opinions JSONB NOT NULL,
    consensus_score INTEGER,
    final_decision JSONB,
    timeframe VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (ticker) REFERENCES stocks(ticker) ON DELETE CASCADE
);

CREATE INDEX idx_debates_ticker ON debates(ticker);
CREATE INDEX idx_debates_created_at ON debates(created_at DESC);

-- 백테스팅 결과
CREATE TABLE IF NOT EXISTS backtest_results (
    id SERIAL PRIMARY KEY,
    strategy_name VARCHAR(100) NOT NULL,
    timeframe VARCHAR(20),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    initial_capital NUMERIC(15, 2),
    final_capital NUMERIC(15, 2),
    total_return NUMERIC(10, 4),
    sharpe_ratio NUMERIC(10, 4),
    mdd NUMERIC(10, 4),
    win_rate NUMERIC(10, 4),
    total_trades INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 성과 추적 (예측 vs 실제)
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    predicted_direction VARCHAR(20),
    predicted_price INTEGER,
    predicted_at TIMESTAMPTZ NOT NULL,
    actual_price INTEGER,
    actual_at TIMESTAMPTZ,
    accuracy BOOLEAN,
    agent_opinions JSONB,
    timeframe VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (ticker) REFERENCES stocks(ticker) ON DELETE CASCADE
);

CREATE INDEX idx_predictions_ticker ON predictions(ticker);
CREATE INDEX idx_predictions_predicted_at ON predictions(predicted_at DESC);

-- 업데이트 트리거 함수
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- stocks 테이블에 트리거 적용
CREATE TRIGGER update_stocks_updated_at BEFORE UPDATE ON stocks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

#### 5. 환경 변수 설정

**.env.example**:
```bash
# Database
DATABASE_URL=postgresql://roundtable_user:roundtable_pass@localhost:5432/roundtable

# Redis
REDIS_URL=redis://localhost:6379/0

# LLM APIs
ANTHROPIC_API_KEY=your_claude_api_key_here
OPENAI_API_KEY=your_openai_api_key_here  # 폴백용

# 한국투자증권 API
KIS_APP_KEY=your_app_key_here
KIS_APP_SECRET=your_app_secret_here
KIS_ACCOUNT_NO=your_account_number_here

# DART OpenAPI
DART_API_KEY=your_dart_api_key_here

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/roundtable.log

# Application
ENVIRONMENT=development
DEBUG=true
```

#### 6. Makefile 작성

**Makefile**:
```makefile
.PHONY: help install dev-install up down restart logs db-init test lint format clean

help:
	@echo "RoundtableTrading - 개발 명령어"
	@echo ""
	@echo "  make install      - 프로덕션 의존성 설치"
	@echo "  make dev-install  - 개발 의존성 포함 설치"
	@echo "  make up           - Docker 컨테이너 시작"
	@echo "  make down         - Docker 컨테이너 중지"
	@echo "  make restart      - Docker 컨테이너 재시작"
	@echo "  make logs         - Docker 로그 확인"
	@echo "  make db-init      - 데이터베이스 초기화"
	@echo "  make test         - 테스트 실행"
	@echo "  make lint         - 코드 린트"
	@echo "  make format       - 코드 포맷팅"
	@echo "  make clean        - 캐시 및 임시 파일 삭제"

install:
	uv sync

dev-install:
	uv sync --all-extras

up:
	docker-compose up -d
	@echo "Waiting for services to be healthy..."
	@sleep 5
	@docker-compose ps

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

db-init:
	uv run python scripts/init_db.py

test:
	uv run pytest tests/ -v --cov=src --cov-report=html

lint:
	uv run ruff check src/ tests/
	uv run mypy src/

format:
	uv run ruff format src/ tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
```

#### 7. 기본 설정 모듈

**src/config.py**:
```python
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # Database
    database_url: str
    
    # Redis
    redis_url: str
    
    # LLM APIs
    anthropic_api_key: str
    openai_api_key: str | None = None
    
    # 한국투자증권 API
    kis_app_key: str | None = None
    kis_app_secret: str | None = None
    kis_account_no: str | None = None
    
    # DART OpenAPI
    dart_api_key: str | None = None
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/roundtable.log"
    
    # Application
    environment: str = "development"
    debug: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """설정 싱글톤"""
    return Settings()
```

#### 8. 로깅 설정

**src/utils/logger.py**:
```python
from loguru import logger
import sys
from pathlib import Path
from src.config import get_settings

settings = get_settings()

# 기존 핸들러 제거
logger.remove()

# 콘솔 출력
logger.add(
    sys.stdout,
    level=settings.log_level,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    colorize=True,
)

# 파일 출력
log_path = Path(settings.log_file)
log_path.parent.mkdir(parents=True, exist_ok=True)

logger.add(
    settings.log_file,
    level=settings.log_level,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    rotation="10 MB",
    retention="30 days",
    compression="zip",
)
```

### 검증 체크리스트

- [ ] uv 프로젝트 초기화 완료
- [ ] Docker Compose로 PostgreSQL + TimescaleDB 실행 확인
- [ ] Docker Compose로 Redis 실행 확인
- [ ] 데이터베이스 스키마 생성 확인
- [ ] .env 파일 설정 완료
- [ ] `make up` 명령어로 모든 서비스 정상 실행
- [ ] Python에서 DB 연결 테스트 성공
- [ ] 로깅 시스템 작동 확인

---

## 📊 Week 1-2: 데이터 수집 파이프라인 (Foundation)

### 목표
안정적인 데이터 수집 및 저장 시스템 구축

### 작업 목록

#### 1. 의존성 추가

```bash
# 데이터 수집
uv add pykrx pandas numpy

# 데이터베이스
uv add asyncpg sqlalchemy[asyncio] alembic

# API 클라이언트
uv add httpx aiohttp

# 기술적 지표 계산
uv add ta-lib pandas-ta

# 개발 도구
uv add --dev ipython jupyter
```

#### 2. 데이터 모델 정의

**src/data/models.py**:
```python
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class Stock:
    """종목 기본 정보"""
    ticker: str
    name: str
    sector: Optional[str] = None
    market: Optional[str] = None  # 'KOSPI' or 'KOSDAQ'


@dataclass
class DailyPrice:
    """일봉 데이터"""
    ticker: str
    date: date
    open: int
    high: int
    low: int
    close: int
    volume: int


@dataclass
class FinancialData:
    """재무 데이터"""
    ticker: str
    quarter: str  # '2024Q3'
    revenue: Optional[float] = None
    operating_income: Optional[float] = None
    net_income: Optional[float] = None
    per: Optional[float] = None
    pbr: Optional[float] = None
    roe: Optional[float] = None
```

#### 3. pykrx 데이터 수집기

**src/data/collectors/pykrx_collector.py**:
```python
from pykrx import stock
import pandas as pd
from datetime import datetime, timedelta
from loguru import logger
from src.data.models import Stock, DailyPrice


class PyKrxCollector:
    """pykrx를 이용한 데이터 수집"""
    
    def get_stock_list(self, market: str = "KOSPI") -> list[Stock]:
        """종목 리스트 조회"""
        try:
            today = datetime.now().strftime("%Y%m%d")
            tickers = stock.get_market_ticker_list(today, market=market)
            
            stocks = []
            for ticker in tickers:
                name = stock.get_market_ticker_name(ticker)
                stocks.append(Stock(
                    ticker=ticker,
                    name=name,
                    market=market
                ))
            
            logger.info(f"Retrieved {len(stocks)} stocks from {market}")
            return stocks
            
        except Exception as e:
            logger.error(f"Failed to get stock list: {e}")
            return []
    
    def get_ohlcv(
        self, 
        ticker: str, 
        start_date: str, 
        end_date: str
    ) -> list[DailyPrice]:
        """일봉 데이터 조회"""
        try:
            df = stock.get_market_ohlcv_by_date(start_date, end_date, ticker)
            
            if df.empty:
                logger.warning(f"No data for {ticker}")
                return []
            
            prices = []
            for date_idx, row in df.iterrows():
                prices.append(DailyPrice(
                    ticker=ticker,
                    date=date_idx.date(),
                    open=int(row['시가']),
                    high=int(row['고가']),
                    low=int(row['저가']),
                    close=int(row['종가']),
                    volume=int(row['거래량'])
                ))
            
            logger.info(f"Retrieved {len(prices)} days of data for {ticker}")
            return prices
            
        except Exception as e:
            logger.error(f"Failed to get OHLCV for {ticker}: {e}")
            return []
    
    def validate_data(self, prices: list[DailyPrice]) -> tuple[bool, list[str]]:
        """데이터 검증"""
        issues = []
        
        if not prices:
            issues.append("데이터 없음")
            return False, issues
        
        # 가격 이상치 확인
        for i in range(1, len(prices)):
            prev_close = prices[i-1].close
            curr_close = prices[i].close
            change_pct = abs((curr_close - prev_close) / prev_close)
            
            if change_pct > 0.3:  # 30% 이상 변동
                issues.append(f"가격 급변 감지: {prices[i].date} ({change_pct:.1%})")
        
        # 거래량 0 확인
        zero_volume_dates = [p.date for p in prices if p.volume == 0]
        if zero_volume_dates:
            issues.append(f"거래량 0: {len(zero_volume_dates)}일")
        
        return len(issues) == 0, issues
```

#### 4. 데이터베이스 저장

**src/data/storage/db_manager.py**:
```python
import asyncpg
from typing import List
from loguru import logger
from src.config import get_settings
from src.data.models import Stock, DailyPrice

settings = get_settings()


class DatabaseManager:
    """데이터베이스 관리"""
    
    def __init__(self):
        self.pool: asyncpg.Pool | None = None
    
    async def connect(self):
        """연결 풀 생성"""
        self.pool = await asyncpg.create_pool(settings.database_url)
        logger.info("Database connection pool created")
    
    async def close(self):
        """연결 풀 종료"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
    
    async def save_stocks(self, stocks: List[Stock]):
        """종목 정보 저장"""
        async with self.pool.acquire() as conn:
            for stock in stocks:
                await conn.execute(
                    """
                    INSERT INTO stocks (ticker, name, sector, market)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (ticker) DO UPDATE
                    SET name = EXCLUDED.name,
                        sector = EXCLUDED.sector,
                        market = EXCLUDED.market,
                        updated_at = NOW()
                    """,
                    stock.ticker, stock.name, stock.sector, stock.market
                )
        
        logger.info(f"Saved {len(stocks)} stocks to database")
    
    async def save_daily_prices(self, prices: List[DailyPrice]):
        """일봉 데이터 저장"""
        async with self.pool.acquire() as conn:
            await conn.executemany(
                """
                INSERT INTO daily_prices (ticker, date, open, high, low, close, volume)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (ticker, date) DO UPDATE
                SET open = EXCLUDED.open,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    close = EXCLUDED.close,
                    volume = EXCLUDED.volume
                """,
                [(p.ticker, p.date, p.open, p.high, p.low, p.close, p.volume) 
                 for p in prices]
            )
        
        logger.info(f"Saved {len(prices)} price records to database")
```

#### 5. 데이터 수집 스크립트

**scripts/collect_initial_data.py**:
```python
import asyncio
from datetime import datetime, timedelta
from loguru import logger
from src.data.collectors.pykrx_collector import PyKrxCollector
from src.data.storage.db_manager import DatabaseManager


async def collect_initial_data():
    """초기 데이터 수집 (3년치)"""
    
    collector = PyKrxCollector()
    db = DatabaseManager()
    
    try:
        await db.connect()
        
        # 1. 종목 리스트 수집
        logger.info("Collecting stock list...")
        kospi_stocks = collector.get_stock_list("KOSPI")
        kosdaq_stocks = collector.get_stock_list("KOSDAQ")
        all_stocks = kospi_stocks + kosdaq_stocks
        
        await db.save_stocks(all_stocks)
        
        # 2. 주요 종목 일봉 데이터 수집 (테스트용 10개만)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * 3)  # 3년
        
        test_tickers = [s.ticker for s in all_stocks[:10]]  # 처음 10개만
        
        for ticker in test_tickers:
            logger.info(f"Collecting data for {ticker}...")
            
            prices = collector.get_ohlcv(
                ticker,
                start_date.strftime("%Y%m%d"),
                end_date.strftime("%Y%m%d")
            )
            
            if prices:
                is_valid, issues = collector.validate_data(prices)
                if not is_valid:
                    logger.warning(f"Data validation issues for {ticker}: {issues}")
                
                await db.save_daily_prices(prices)
            
            # Rate limiting
            await asyncio.sleep(0.5)
        
        logger.info("Initial data collection completed")
        
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(collect_initial_data())
```

### 검증 체크리스트

- [ ] pykrx로 KOSPI/KOSDAQ 종목 리스트 조회 성공
- [ ] 테스트 종목 3년치 일봉 데이터 수집 성공
- [ ] 데이터 검증 로직 작동 확인
- [ ] PostgreSQL에 데이터 저장 확인
- [ ] TimescaleDB 하이퍼테이블 정상 작동 확인
- [ ] 데이터 수집 스크립트 에러 없이 완료

---

## 🤖 Week 3-4: 단일 에이전트 프로토타입

### 목표
하나의 에이전트를 완벽하게 구현하여 패턴 확립

### 작업 목록

#### 1. 의존성 추가

```bash
# LLM 클라이언트
uv add anthropic openai

# 비동기 처리
uv add aiofiles tenacity
```

#### 2. LLM 클라이언트 추상화

**src/agents/llm/base.py**:
```python
from abc import ABC, abstractmethod
from typing import Optional


class LLMClient(ABC):
    """LLM 클라이언트 인터페이스"""
    
    @abstractmethod
    async def generate(
        self, 
        prompt: str, 
        system: Optional[str] = None,
        **kwargs
    ) -> str:
        """텍스트 생성"""
        pass


class ClaudeClient(LLMClient):
    """Claude API 클라이언트"""
    
    def __init__(self, api_key: str):
        import anthropic
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
    
    async def generate(
        self, 
        prompt: str, 
        system: Optional[str] = None,
        **kwargs
    ) -> str:
        messages = [{"role": "user", "content": prompt}]
        
        response = await self.client.messages.create(
            model=kwargs.get("model", "claude-3-5-sonnet-20241022"),
            max_tokens=kwargs.get("max_tokens", 2000),
            system=system or "",
            messages=messages
        )
        
        return response.content[0].text
```

#### 3. 에이전트 기본 클래스

**src/agents/base.py**:
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from src.agents.llm.base import LLMClient


@dataclass
class AgentOpinion:
    """에이전트 의견"""
    agent_name: str
    opinion: str  # "매수" / "중립" / "매도"
    score: int  # 0-100
    reasoning: list[str]  # 근거 3개
    timestamp: datetime
    raw_response: Optional[str] = None


class BaseAgent(ABC):
    """에이전트 기본 클래스"""
    
    def __init__(self, name: str, llm_client: LLMClient):
        self.name = name
        self.llm = llm_client
        self.weight = 1.0  # 초기 가중치
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """시스템 프롬프트"""
        pass
    
    @abstractmethod
    async def prepare_prompt(self, ticker: str, data: dict) -> str:
        """분석 프롬프트 준비"""
        pass
    
    async def analyze(self, ticker: str, data: dict) -> AgentOpinion:
        """종목 분석"""
        system_prompt = self.get_system_prompt()
        user_prompt = await self.prepare_prompt(ticker, data)
        
        response = await self.llm.generate(
            prompt=user_prompt,
            system=system_prompt
        )
        
        # 응답 파싱
        opinion = self.parse_response(response)
        opinion.agent_name = self.name
        opinion.timestamp = datetime.now()
        opinion.raw_response = response
        
        return opinion
    
    @abstractmethod
    def parse_response(self, response: str) -> AgentOpinion:
        """응답 파싱"""
        pass
```

#### 4. 기술적 분석 에이전트 (프로토타입)

**src/agents/technical_agent.py**:
```python
import pandas as pd
from src.agents.base import BaseAgent, AgentOpinion
from loguru import logger


class TechnicalAgent(BaseAgent):
    """기술적 분석 에이전트"""
    
    def get_system_prompt(self) -> str:
        return """당신은 기술적 분석 전문가입니다.

역할:
- 차트 패턴, 기술적 지표, 거래량 분석
- 단기 가격 움직임 예측

분석 시 고려사항:
1. 여러 지표의 종합 판단 (단일 지표에 의존 금지)
2. 과거 유사 패턴의 성공률
3. 현재 시장 변동성

신뢰도 점수 기준:
- 90~100점: 매우 확실함. 과거 유사 패턴에서 승률 > 80%
- 75~89점: 확신함. 여러 근거가 일치.
- 60~74점: 약한 긍정. 일부 근거만 지지.
- 40~59점: 중립. 불확실함.
- 25~39점: 약한 부정.
- 10~24점: 부정적. 여러 근거가 반대.
- 0~9점: 매우 부정적. 명확한 리스크.

출력 형식 (반드시 준수):
의견: [매수/중립/매도]
신뢰도: [0-100 점수]
근거1: [간결한 설명]
근거2: [간결한 설명]
근거3: [간결한 설명]
"""
    
    async def prepare_prompt(self, ticker: str, data: dict) -> str:
        """프롬프트 준비"""
        
        # 기술적 지표 계산
        df = pd.DataFrame(data['prices'])
        indicators = self.calculate_indicators(df)
        
        prompt = f"""다음 종목의 기술적 분석을 수행하세요.

종목: {data['name']} ({ticker})
현재가: {data['current_price']:,}원

기술적 지표:
- 이동평균선:
  - 5일선: {indicators['ma5']:,}원
  - 20일선: {indicators['ma20']:,}원
  - 60일선: {indicators['ma60']:,}원
- RSI (14일): {indicators['rsi']:.1f}
- MACD: {indicators['macd']:.2f}
- 거래량 (최근 5일 평균 대비): {indicators['volume_ratio']:.1f}배

최근 5일 가격 추이:
{self.format_recent_prices(df.tail(5))}

위 데이터를 바탕으로 기술적 분석을 수행하고, 지정된 형식으로 의견을 제시하세요.
"""
        return prompt
    
    def calculate_indicators(self, df: pd.DataFrame) -> dict:
        """기술적 지표 계산"""
        # 이동평균선
        df['ma5'] = df['close'].rolling(window=5).mean()
        df['ma20'] = df['close'].rolling(window=20).mean()
        df['ma60'] = df['close'].rolling(window=60).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD (간단 버전)
        ema12 = df['close'].ewm(span=12).mean()
        ema26 = df['close'].ewm(span=26).mean()
        df['macd'] = ema12 - ema26
        
        # 거래량 비율
        avg_volume_5d = df['volume'].tail(5).mean()
        avg_volume_20d = df['volume'].tail(20).mean()
        volume_ratio = avg_volume_5d / avg_volume_20d if avg_volume_20d > 0 else 1.0
        
        latest = df.iloc[-1]
        
        return {
            'ma5': int(latest['ma5']),
            'ma20': int(latest['ma20']),
            'ma60': int(latest['ma60']),
            'rsi': float(latest['rsi']),
            'macd': float(latest['macd']),
            'volume_ratio': volume_ratio
        }
    
    def format_recent_prices(self, df: pd.DataFrame) -> str:
        """최근 가격 포맷팅"""
        lines = []
        for _, row in df.iterrows():
            lines.append(
                f"  {row.name.strftime('%Y-%m-%d')}: "
                f"{int(row['close']):,}원 (거래량: {int(row['volume']):,})"
            )
        return "\n".join(lines)
    
    def parse_response(self, response: str) -> AgentOpinion:
        """응답 파싱"""
        lines = response.strip().split('\n')
        
        opinion = "중립"
        score = 50
        reasoning = []
        
        for line in lines:
            line = line.strip()
            if line.startswith("의견:"):
                opinion = line.split(":", 1)[1].strip()
            elif line.startswith("신뢰도:"):
                score_str = line.split(":", 1)[1].strip()
                score = int(''.join(filter(str.isdigit, score_str)))
            elif line.startswith("근거"):
                reason = line.split(":", 1)[1].strip()
                reasoning.append(reason)
        
        return AgentOpinion(
            agent_name=self.name,
            opinion=opinion,
            score=score,
            reasoning=reasoning[:3],  # 최대 3개
            timestamp=datetime.now()
        )
```

#### 5. 단일 에이전트 테스트 스크립트

**scripts/test_single_agent.py**:
```python
import asyncio
from src.agents.technical_agent import TechnicalAgent
from src.agents.llm.base import ClaudeClient
from src.data.storage.db_manager import DatabaseManager
from src.config import get_settings
from loguru import logger

settings = get_settings()


async def test_technical_agent():
    """기술적 분석 에이전트 테스트"""
    
    # LLM 클라이언트 생성
    llm = ClaudeClient(api_key=settings.anthropic_api_key)
    
    # 에이전트 생성
    agent = TechnicalAgent(name="기술적분석", llm_client=llm)
    
    # 데이터베이스에서 테스트 데이터 가져오기
    db = DatabaseManager()
    await db.connect()
    
    try:
        # 삼성전자 데이터 조회
        ticker = "005930"
        
        async with db.pool.acquire() as conn:
            # 종목 정보
            stock = await conn.fetchrow(
                "SELECT * FROM stocks WHERE ticker = $1", ticker
            )
            
            # 최근 60일 가격 데이터
            prices = await conn.fetch(
                """
                SELECT date, open, high, low, close, volume
                FROM daily_prices
                WHERE ticker = $1
                ORDER BY date DESC
                LIMIT 60
                """,
                ticker
            )
        
        if not stock or not prices:
            logger.error(f"No data found for {ticker}")
            return
        
        # 데이터 준비
        data = {
            'name': stock['name'],
            'current_price': prices[0]['close'],
            'prices': [dict(p) for p in reversed(prices)]
        }
        
        # 분석 실행
        logger.info(f"Analyzing {stock['name']} ({ticker})...")
        opinion = await agent.analyze(ticker, data)
        
        # 결과 출력
        logger.info("=" * 50)
        logger.info(f"에이전트: {opinion.agent_name}")
        logger.info(f"의견: {opinion.opinion}")
        logger.info(f"신뢰도: {opinion.score}점")
        logger.info("근거:")
        for i, reason in enumerate(opinion.reasoning, 1):
            logger.info(f"  {i}. {reason}")
        logger.info("=" * 50)
        
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(test_technical_agent())
```

### 검증 체크리스트

- [ ] Claude API 연결 성공
- [ ] 기술적 지표 계산 정확성 확인
- [ ] 에이전트 프롬프트 생성 확인
- [ ] LLM 응답 파싱 성공
- [ ] 의견/점수/근거 형식 준수 확인
- [ ] 테스트 스크립트 에러 없이 완료

---

## 🎭 Week 5-6: 멀티 에이전트 협업 시스템

### 목표
5개 에이전트 구현 및 토론 메커니즘 완성

### 작업 목록

#### 1. 나머지 에이전트 구현

**구현 순서**:
1. ✅ 기술적 분석 에이전트 (Week 3-4 완료)
2. 기업 가치 분석 에이전트
3. 시장 분석 에이전트
4. 리스크 관리 에이전트
5. 조정자 에이전트

**패턴**: 모두 `BaseAgent`를 상속하여 동일한 구조로 구현

#### 2. 토론 엔진

**src/debate/engine.py**:
```python
import asyncio
from typing import List
from loguru import logger
from src.agents.base import BaseAgent, AgentOpinion
from dataclasses import dataclass


@dataclass
class DebateResult:
    """토론 결과"""
    ticker: str
    opinions: List[AgentOpinion]
    consensus_score: int
    final_decision: dict
    debate_rounds: int


class DebateEngine:
    """토론 엔진"""
    
    def __init__(self, agents: List[BaseAgent]):
        self.agents = agents
    
    async def conduct_debate(
        self, 
        ticker: str, 
        data: dict,
        timeframe: str = "중기"
    ) -> DebateResult:
        """토론 진행"""
        
        logger.info(f"Starting debate for {ticker} ({timeframe})")
        
        # 1단계: 개별 분석 (병렬)
        logger.info("Stage 1: Individual analysis...")
        opinions = await asyncio.gather(*[
            agent.analyze(ticker, data)
            for agent in self.agents
        ])
        
        # 2단계: 의견 제시
        logger.info("Stage 2: Opinion presentation...")
        self.log_opinions(opinions)
        
        # 3단계: 토론 (조건부)
        debate_rounds = 0
        if self.needs_debate(opinions):
            logger.info("Stage 3: Debate rounds...")
            opinions, debate_rounds = await self.debate_rounds(
                ticker, data, opinions, max_rounds=3
            )
        else:
            logger.info("Stage 3: Skipped (consensus reached)")
        
        # 4단계: 합의 도출
        logger.info("Stage 4: Consensus calculation...")
        consensus_score = self.calculate_consensus(opinions, timeframe)
        
        # 5단계: 최종 결정
        logger.info("Stage 5: Final decision...")
        final_decision = self.make_final_decision(
            opinions, consensus_score, timeframe
        )
        
        return DebateResult(
            ticker=ticker,
            opinions=opinions,
            consensus_score=consensus_score,
            final_decision=final_decision,
            debate_rounds=debate_rounds
        )
    
    def log_opinions(self, opinions: List[AgentOpinion]):
        """의견 로깅"""
        for op in opinions:
            logger.info(
                f"  {op.agent_name}: {op.opinion} ({op.score}점)"
            )
    
    def needs_debate(self, opinions: List[AgentOpinion]) -> bool:
        """토론 필요 여부"""
        scores = [op.score for op in opinions]
        std_dev = pd.Series(scores).std()
        return std_dev > 20  # 표준편차 20점 초과 시 토론
    
    async def debate_rounds(
        self,
        ticker: str,
        data: dict,
        opinions: List[AgentOpinion],
        max_rounds: int = 3
    ) -> tuple[List[AgentOpinion], int]:
        """토론 라운드"""
        # 간단 구현: 재분석
        # 실제로는 다른 에이전트 의견을 보고 재평가
        for round_num in range(1, max_rounds + 1):
            logger.info(f"  Round {round_num}...")
            
            # 재분석
            new_opinions = await asyncio.gather(*[
                agent.analyze(ticker, data)
                for agent in self.agents
            ])
            
            # 합의 도달 확인
            if not self.needs_debate(new_opinions):
                logger.info(f"  Consensus reached in round {round_num}")
                return new_opinions, round_num
            
            opinions = new_opinions
        
        return opinions, max_rounds
    
    def calculate_consensus(
        self, 
        opinions: List[AgentOpinion],
        timeframe: str
    ) -> int:
        """합의도 계산"""
        # 타임프레임별 가중치
        timeframe_weights = {
            "단기": {"기술적분석": 1.5, "기업가치": 0.7},
            "중기": {"기술적분석": 1.2, "기업가치": 1.0},
            "장기": {"기술적분석": 0.8, "기업가치": 1.5},
        }
        
        weights = timeframe_weights.get(timeframe, {})
        
        weighted_sum = 0
        total_weight = 0
        
        for op in opinions:
            weight = weights.get(op.agent_name, 1.0) * op.agent.weight
            weighted_sum += op.score * weight
            total_weight += weight
        
        return int(weighted_sum / total_weight) if total_weight > 0 else 50
    
    def make_final_decision(
        self,
        opinions: List[AgentOpinion],
        consensus_score: int,
        timeframe: str
    ) -> dict:
        """최종 결정"""
        
        # 합의 수준 판단
        if consensus_score >= 80:
            decision_type = "강한 합의"
            position_size = 0.15  # 15%
        elif consensus_score >= 60:
            decision_type = "약한 합의"
            position_size = 0.10  # 10%
        else:
            decision_type = "합의 실패"
            position_size = 0.0
        
        # 의견 집계
        buy_count = sum(1 for op in opinions if "매수" in op.opinion)
        sell_count = sum(1 for op in opinions if "매도" in op.opinion)
        neutral_count = len(opinions) - buy_count - sell_count
        
        if buy_count > sell_count:
            recommendation = "매수 추천"
        elif sell_count > buy_count:
            recommendation = "매도 추천"
        else:
            recommendation = "관찰"
        
        return {
            "recommendation": recommendation,
            "consensus_score": consensus_score,
            "decision_type": decision_type,
            "position_size": position_size,
            "timeframe": timeframe,
            "vote_summary": {
                "buy": buy_count,
                "neutral": neutral_count,
                "sell": sell_count
            }
        }
```

#### 3. 멀티 에이전트 테스트

**scripts/test_multi_agent.py**:
```python
import asyncio
from src.agents.technical_agent import TechnicalAgent
# from src.agents.fundamental_agent import FundamentalAgent
# ... (다른 에이전트들)
from src.agents.llm.base import ClaudeClient
from src.debate.engine import DebateEngine
from src.data.storage.db_manager import DatabaseManager
from src.config import get_settings
from loguru import logger

settings = get_settings()


async def test_multi_agent_debate():
    """멀티 에이전트 토론 테스트"""
    
    # LLM 클라이언트
    llm = ClaudeClient(api_key=settings.anthropic_api_key)
    
    # 에이전트 생성 (일단 기술적 분석만)
    agents = [
        TechnicalAgent(name="기술적분석", llm_client=llm),
        # FundamentalAgent(name="기업가치", llm_client=llm),
        # ... 나머지 에이전트
    ]
    
    # 토론 엔진
    engine = DebateEngine(agents=agents)
    
    # 데이터 준비 (생략 - test_single_agent.py와 동일)
    # ...
    
    # 토론 실행
    result = await engine.conduct_debate(
        ticker="005930",
        data=data,
        timeframe="중기"
    )
    
    # 결과 출력
    logger.info("=" * 60)
    logger.info(f"토론 결과: {result.ticker}")
    logger.info(f"합의도: {result.consensus_score}점")
    logger.info(f"최종 결정: {result.final_decision['recommendation']}")
    logger.info(f"포지션 크기: {result.final_decision['position_size']:.1%}")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_multi_agent_debate())
```

### 검증 체크리스트

- [ ] 5개 에이전트 모두 구현 완료
- [ ] 병렬 분석 정상 작동
- [ ] 토론 라운드 로직 작동
- [ ] 합의도 계산 정확성 확인
- [ ] 타임프레임별 가중치 적용 확인
- [ ] 최종 결정 로직 검증

---

## 📈 Week 7: 백테스팅 엔진

### 목표
과거 데이터로 전략 성과 검증

### 작업 내용
- 백테스팅 엔진 구현
- 거래 비용 반영
- 성과 지표 계산
- Walk-forward 분석

*(상세 내용은 길이 제한으로 생략 - 필요 시 추가 작성)*

---

## 🖥️ Week 8: Streamlit UI 및 통합

### 목표
사용자 인터페이스 완성 및 전체 시스템 통합

### 작업 내용
- Streamlit 대시보드 구현
- 전체 시스템 통합 테스트
- 문서 작성 (README, 사용 가이드)

*(상세 내용은 길이 제한으로 생략 - 필요 시 추가 작성)*

---

## 📝 다음 단계

이 계획서를 기반으로:
1. Week 0 환경 설정부터 시작
2. 각 주차별로 체크리스트 완료 확인
3. 문제 발생 시 즉시 조정
4. 점진적으로 기능 추가

**시작 준비 되셨나요?** Week 0부터 함께 진행하시겠습니까?
