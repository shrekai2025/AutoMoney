-- TimescaleDB Initialization Script
-- This script runs when the PostgreSQL container is first created

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create database if not exists (handled by POSTGRES_DB env var)
-- Additional setup can be done here

-- Create schema for time-series data
CREATE SCHEMA IF NOT EXISTS timeseries;

-- Set search path
SET search_path TO public, timeseries;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'TimescaleDB initialized successfully';
    RAISE NOTICE 'Database: automoney';
    RAISE NOTICE 'Extensions: timescaledb';
END $$;

-- Create a function to convert regular tables to hypertables
-- This will be used later when we create time-series tables
CREATE OR REPLACE FUNCTION timeseries.create_hypertable_if_not_exists(
    table_name TEXT,
    time_column TEXT,
    chunk_time_interval INTERVAL DEFAULT INTERVAL '1 day'
)
RETURNS VOID AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM timescaledb_information.hypertables
        WHERE hypertable_name = table_name
    ) THEN
        PERFORM create_hypertable(table_name, time_column, chunk_time_interval => chunk_time_interval);
        RAISE NOTICE 'Created hypertable: %', table_name;
    ELSE
        RAISE NOTICE 'Hypertable already exists: %', table_name;
    END IF;
END;
$$ LANGUAGE plpgsql;
