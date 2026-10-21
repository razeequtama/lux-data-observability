/**
 * Types and interfaces for quality validation runs, rules, and findings.
 * Matches backend schemas from app/schemas/validation.py.
 */

export type RuleCategory =
  | 'NULL_CHECK'
  | 'UNIQUENESS'
  | 'TYPE_VALIDITY'
  | 'RECORD_COUNT'
  | 'VALUE_RANGE'
  | 'REFERENTIAL_INTEGRITY'
  | 'TEMPORAL_ANOMALY'
  | 'SCHEMA_INTEGRITY'
  | 'FRESHNESS'
  | string;

export type RuleSeverity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';

export type RuleStatus = 'PASSED' | 'FAILED' | 'WARNING' | 'SKIPPED' | 'ERROR';

export interface ValidationRunResponse {
  run_id: string;
  scenario_id: string;
  fixture_version: 'defective' | 'corrected' | string;
  status: 'PASSED' | 'FAILED' | 'WARNING' | string;
  total_checks: number;
  passed_checks: number;
  failed_checks: number;
  warning_checks: number;
  skipped_checks: number;
  error_checks: number;
  execution_duration_ms: number;
  executed_at: string;
}

export interface DuplicateRowEvidence {
  order_id?: string;
  occurrences?: number;
  row_indices?: number[];
  [key: string]: unknown;
}

export interface ViolationRowEvidence {
  row_index?: number;
  [key: string]: unknown;
}

export interface FindingEvidence {
  sample_duplicates?: DuplicateRowEvidence[];
  sample_duplicates_truncated?: boolean;
  sample_duplicates_total_count?: number;
  sample_orphaned_keys?: string[];
  sample_violations?: ViolationRowEvidence[];
  max_gap_hours?: number;
  gap_start?: string;
  gap_end?: string;
  threshold_hours?: number;
  observed_value?: unknown;
  expected_value?: unknown;
  [key: string]: unknown;
}

export interface ValidationFindingItem {
  id: string;
  rule_id: string;
  rule_name: string;
  rule_category: RuleCategory;
  severity: RuleSeverity;
  status: RuleStatus;
  dataset_id: string;
  affected_fields: string[];
  affected_record_count: number;
  total_record_count: number;
  message: string;
  evidence: FindingEvidence;
  execution_duration_ms: number;
  created_at?: string | null;
}

export interface ValidationFindingsListResponse {
  run_id: string;
  total_findings: number;
  items: ValidationFindingItem[];
}

export interface ValidationFilterParams {
  severity?: RuleSeverity | 'ALL';
  status?: RuleStatus | 'ALL';
  dataset_id?: string | 'ALL';
  search?: string;
}

