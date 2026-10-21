/**
 * Common and error response types matching backend schemas.
 */

export interface ApiErrorDetail {
  code: string;
  message: string;
  details?: Record<string, unknown>;
  timestamp?: string;
}

export interface ApiErrorResponse {
  error: ApiErrorDetail;
}

export type ComputeHealthStatus = 'SUCCESS' | 'FAILED' | 'PENDING' | 'RUNNING';
export type QualityHealthStatus = 'HEALTHY' | 'WARNING' | 'DEGRADED' | 'CORRUPTED' | 'UNVALIDATED';

export type NavigationTab =
  | 'validations'
  | 'lineage'
  | 'impact'
  | 'pipelines'
  | 'investigation'
  | 'recovery';

