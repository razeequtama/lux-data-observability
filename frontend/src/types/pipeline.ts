/**
 * Domain types and schemas for pipeline run history and partition freshness.
 */

import { QualityHealthStatus } from './common';

export type PipelineExecutionStatus =
  | 'COMPLETED_SUCCESS'
  | 'COMPLETED_WITH_WARNINGS'
  | 'FAILED'
  | 'RUNNING'
  | 'CANCELLED';

export type FreshnessStatus = 'FRESH' | 'STALE' | 'MISSING';

export interface PipelineStepLog {
  step: string;
  status: string;
  records: number;
  duration_ms: number;
}

export interface PipelineRun {
  id: string;
  scenario_id: string;
  pipeline_name: string;
  execution_status: PipelineExecutionStatus | string;
  quality_health: QualityHealthStatus | string;
  start_time: string;
  end_time: string;
  duration_ms: number;
  records_ingested: number;
  records_written: number;
  error_message?: string | null;
  run_log: PipelineStepLog[];
  created_at?: string | null;
}

export interface FreshnessCheck {
  id?: string | null;
  scenario_id?: string | null;
  dataset_id: string;
  dataset_name: string;
  sla_hours: number;
  expected_partition_timestamp: string;
  observed_partition_timestamp?: string | null;
  status: FreshnessStatus | string;
  hours_behind: number;
  checked_at?: string | null;
}
