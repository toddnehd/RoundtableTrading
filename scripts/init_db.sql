-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- 종목 정보 테이블
CREATE TABLE IF NOT EXISTS stocks (
    stock_code VARCHAR(10) PRIMARY KEY,
    stock_name VARCHAR(100) NOT NULL,
    market VARCHAR(10) NOT NULL CHECK (market IN ('KOSPI', 'KOSDAQ')),
    sector VARCHAR(100),
    industry VARCHAR(100),
    listed_date DATE,
    market_cap BIGINT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_stocks_market ON stocks(market);
CREATE INDEX idx_stocks_sector ON stocks(sector);
CREATE INDEX idx_stocks_is_active ON stocks(is_active);

-- 일봉 데이터 테이블 (TimescaleDB hypertable)
CREATE TABLE IF NOT EXISTS daily_prices (
    stock_code VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    open_price INTEGER NOT NULL,
    high_price INTEGER NOT NULL,
    low_price INTEGER NOT NULL,
    close_price INTEGER NOT NULL,
    volume BIGINT NOT NULL,
    trading_value BIGINT,
    market_cap BIGINT,
    shares_outstanding BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (stock_code, date),
    FOREIGN KEY (stock_code) REFERENCES stocks(stock_code) ON DELETE CASCADE
);

-- Convert to TimescaleDB hypertable
SELECT create_hypertable('daily_prices', 'date', if_not_exists => TRUE);

CREATE INDEX idx_daily_prices_stock_code ON daily_prices(stock_code, date DESC);

-- 에이전트 의견 테이블
CREATE TABLE IF NOT EXISTS agent_opinions (
    opinion_id SERIAL PRIMARY KEY,
    debate_id INTEGER NOT NULL,
    agent_type VARCHAR(50) NOT NULL CHECK (agent_type IN ('fundamental', 'technical', 'market', 'risk', 'moderator')),
    stock_code VARCHAR(10) NOT NULL,
    opinion_stage VARCHAR(20) NOT NULL CHECK (opinion_stage IN ('initial', 'rebuttal', 'consensus', 'final', 'decision')),
    opinion_text TEXT NOT NULL,
    confidence_score NUMERIC(3, 2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    reasoning JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (stock_code) REFERENCES stocks(stock_code) ON DELETE CASCADE
);

CREATE INDEX idx_agent_opinions_debate_id ON agent_opinions(debate_id);
CREATE INDEX idx_agent_opinions_agent_type ON agent_opinions(agent_type);
CREATE INDEX idx_agent_opinions_stock_code ON agent_opinions(stock_code);
CREATE INDEX idx_agent_opinions_created_at ON agent_opinions(created_at DESC);

-- 토론 기록 테이블
CREATE TABLE IF NOT EXISTS debates (
    debate_id SERIAL PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL,
    debate_date DATE NOT NULL,
    timeframe VARCHAR(20) NOT NULL CHECK (timeframe IN ('short_term', 'medium_term', 'long_term')),
    initial_price INTEGER NOT NULL,
    final_decision VARCHAR(10) CHECK (final_decision IN ('BUY', 'SELL', 'HOLD')),
    consensus_score NUMERIC(3, 2),
    debate_summary TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    FOREIGN KEY (stock_code) REFERENCES stocks(stock_code) ON DELETE CASCADE
);

CREATE INDEX idx_debates_stock_code ON debates(stock_code);
CREATE INDEX idx_debates_debate_date ON debates(debate_date DESC);
CREATE INDEX idx_debates_timeframe ON debates(timeframe);
CREATE INDEX idx_debates_created_at ON debates(created_at DESC);

-- Add foreign key to agent_opinions after debates table is created
ALTER TABLE agent_opinions ADD CONSTRAINT fk_agent_opinions_debate_id
    FOREIGN KEY (debate_id) REFERENCES debates(debate_id) ON DELETE CASCADE;

-- 백테스팅 결과 테이블
CREATE TABLE IF NOT EXISTS backtest_results (
    backtest_id SERIAL PRIMARY KEY,
    backtest_name VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    initial_capital BIGINT NOT NULL,
    final_capital BIGINT NOT NULL,
    total_return NUMERIC(10, 4),
    sharpe_ratio NUMERIC(10, 4),
    max_drawdown NUMERIC(10, 4),
    win_rate NUMERIC(5, 2),
    total_trades INTEGER,
    profitable_trades INTEGER,
    losing_trades INTEGER,
    config JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_backtest_results_created_at ON backtest_results(created_at DESC);
CREATE INDEX idx_backtest_results_start_date ON backtest_results(start_date);

-- 백테스팅 거래 내역 테이블
CREATE TABLE IF NOT EXISTS backtest_trades (
    trade_id SERIAL PRIMARY KEY,
    backtest_id INTEGER NOT NULL,
    stock_code VARCHAR(10) NOT NULL,
    trade_date DATE NOT NULL,
    action VARCHAR(10) NOT NULL CHECK (action IN ('BUY', 'SELL')),
    price INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    total_amount BIGINT NOT NULL,
    debate_id INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (backtest_id) REFERENCES backtest_results(backtest_id) ON DELETE CASCADE,
    FOREIGN KEY (stock_code) REFERENCES stocks(stock_code) ON DELETE CASCADE,
    FOREIGN KEY (debate_id) REFERENCES debates(debate_id) ON DELETE SET NULL
);

CREATE INDEX idx_backtest_trades_backtest_id ON backtest_trades(backtest_id);
CREATE INDEX idx_backtest_trades_stock_code ON backtest_trades(stock_code);
CREATE INDEX idx_backtest_trades_trade_date ON backtest_trades(trade_date);

-- 예측 vs 실제 추적 테이블
CREATE TABLE IF NOT EXISTS predictions (
    prediction_id SERIAL PRIMARY KEY,
    debate_id INTEGER NOT NULL,
    stock_code VARCHAR(10) NOT NULL,
    prediction_date DATE NOT NULL,
    target_date DATE NOT NULL,
    predicted_direction VARCHAR(10) NOT NULL CHECK (predicted_direction IN ('UP', 'DOWN', 'NEUTRAL')),
    predicted_price_range_min INTEGER,
    predicted_price_range_max INTEGER,
    actual_price INTEGER,
    actual_direction VARCHAR(10) CHECK (actual_direction IN ('UP', 'DOWN', 'NEUTRAL')),
    is_correct BOOLEAN,
    error_percentage NUMERIC(10, 4),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    evaluated_at TIMESTAMPTZ,
    FOREIGN KEY (debate_id) REFERENCES debates(debate_id) ON DELETE CASCADE,
    FOREIGN KEY (stock_code) REFERENCES stocks(stock_code) ON DELETE CASCADE
);

CREATE INDEX idx_predictions_debate_id ON predictions(debate_id);
CREATE INDEX idx_predictions_stock_code ON predictions(stock_code);
CREATE INDEX idx_predictions_prediction_date ON predictions(prediction_date DESC);
CREATE INDEX idx_predictions_target_date ON predictions(target_date);

-- 시스템 메타데이터 테이블
CREATE TABLE IF NOT EXISTS system_metadata (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert initial metadata
INSERT INTO system_metadata (key, value, description) VALUES
    ('last_data_update', '1970-01-01', 'Last date when daily price data was updated'),
    ('db_version', '1.0.0', 'Database schema version'),
    ('system_status', 'initialized', 'Current system status')
ON CONFLICT (key) DO NOTHING;

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to stocks table
CREATE TRIGGER update_stocks_updated_at BEFORE UPDATE ON stocks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Apply trigger to system_metadata table
CREATE TRIGGER update_system_metadata_updated_at BEFORE UPDATE ON system_metadata
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
