/**
 * Types and interfaces for scenario recovery verification and before-and-after diffs.
 */

export interface RecoveryRunSummary {
  run_id: string;
  fixture_version: 'defective' | 'corrected' | string;
  failed_checks: number;
  quality_health: 'HEALTHY' | 'DEGRADED' | 'CORRUPTED' | string;
  total_checks?: number | null;
  passed_checks?: number | null;
  execution_duration_ms?: number | null;
  executed_at?: string | null;
}

export interface ResolvedFindingItem {
  rule_id: string;
  rule_name: string;
  status: 'RESOLVED' | 'UNRESOLVED' | string;
  severity?: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | null;
  category?: string | null;
  dataset_id?: string | null;
  previous_status?: string | null;
  current_status?: string | null;
  message?: string | null;
}

export type DownstreamRecoveryStatus =
  | 'ALL_ASSETS_HEALTHY'
  | 'PARTIALLY_RECOVERED'
  | 'RECOVERY_FAILED'
  | string;

export interface RecoveryComparison {
  previous_run: RecoveryRunSummary;
  current_run: RecoveryRunSummary;
  resolved_findings: ResolvedFindingItem[];
  downstream_recovery_status: DownstreamRecoveryStatus;
}

export interface RecoveryVerifyRequest {
  scenario_id: string;
  target_fixture_version?: string;
}

export interface RecoveryVerifyResponse {
  scenario_id: string;
  comparison: RecoveryComparison;
}

