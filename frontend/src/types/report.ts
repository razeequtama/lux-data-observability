/**
 * Report generation and artifact domain types matching backend schemas.
 */

export type ReportFormat = 'json' | 'html';

export interface ReportGenerateRequest {
  scenario_id: string;
  validation_run_id?: string | null;
  investigation_id?: string | null;
  title?: string | null;
  verified_facts?: string[];
  hypotheses?: string[];
  action_items?: string[];
}

export interface ReportGenerateResponse {
  report_id: string;
  investigation_id: string;
  generated_at: string;
  json_url: string;
  html_url: string;
}

export interface ReportArtifactResponse {
  id: string;
  investigation_id: string;
  scenario_id: string;
  validation_run_id: string;
  format: 'json' | 'html' | string;
  file_path: string;
  sha256_hash: string;
  file_size_bytes: number;
  generated_at: string;
}

