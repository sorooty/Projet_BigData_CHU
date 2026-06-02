-- Log principal des exécutions ETL.
-- Une ligne par run de job.
CREATE TABLE IF NOT EXISTS audit.etl_run_log (
    run_id BIGSERIAL PRIMARY KEY,
    job_name TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    status TEXT NOT NULL CHECK (status IN ('running', 'success', 'failed')),
    rows_read BIGINT DEFAULT 0,
    rows_written BIGINT DEFAULT 0,
    message TEXT
);

-- Log des contrôles qualité.
-- Permet de tracer ce qui passe et ce qui casse après chaque run.
CREATE TABLE IF NOT EXISTS audit.data_quality_log (
    quality_id BIGSERIAL PRIMARY KEY,
    run_id BIGINT REFERENCES audit.etl_run_log(run_id),
    check_name TEXT NOT NULL,
    table_name TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value NUMERIC NOT NULL,
    threshold_value NUMERIC,
    passed BOOLEAN NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
