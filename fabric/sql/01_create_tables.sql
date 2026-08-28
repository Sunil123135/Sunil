-- Run in Fabric Lakehouse SQL analytics endpoint or Spark SQL
-- Database: lh_air_freight

CREATE TABLE IF NOT EXISTS rates_observed (
  collected_at_utc TIMESTAMP,
  source STRING,
  source_url STRING,
  attribution STRING,
  rate_type STRING,
  origin STRING,
  destination STRING,
  lane STRING,
  region STRING,
  weight_break_kg DOUBLE,
  chargeable_kg DOUBLE,
  currency STRING,
  usd_per_kg_min DOUBLE,
  usd_per_kg_max DOUBLE,
  usd_per_kg_mid DOUBLE,
  total_min_usd DOUBLE,
  total_max_usd DOUBLE,
  transit_min_days DOUBLE,
  transit_max_days DOUBLE,
  num_quotes DOUBLE,
  status STRING,
  error STRING,
  source_as_of STRING
);

CREATE TABLE IF NOT EXISTS proxies_macro (
  observation_date TIMESTAMP,
  series_id STRING,
  series_name STRING,
  value DOUBLE,
  source STRING,
  source_url STRING,
  rate_type STRING,
  collected_at_utc STRING
);

CREATE TABLE IF NOT EXISTS forecasts (
  generated_at_utc TIMESTAMP,
  model_name STRING,
  lane STRING,
  target STRING,
  horizon_months INT,
  forecast_date DATE,
  point_forecast DOUBLE,
  pi_low_80 DOUBLE,
  pi_high_80 DOUBLE,
  metrics_json STRING
);

CREATE TABLE IF NOT EXISTS collection_runs (
  run_id STRING,
  started_at_utc TIMESTAMP,
  finished_at_utc TIMESTAMP,
  status STRING,
  rates_rows INT,
  rates_ok INT,
  proxies_rows INT,
  message STRING
);
