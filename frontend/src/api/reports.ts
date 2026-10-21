/**
 * API client methods for incident report generation, exports, and artifact retrieval.
 */

import { apiGet, apiGetText, apiPost } from './client';
import {
  ReportArtifactResponse,
  ReportFormat,
  ReportGenerateRequest,
  ReportGenerateResponse,
} from '../types';

export interface ListReportArtifactsOptions {
  scenarioId?: string;
  investigationId?: string;
  limit?: number;
  offset?: number;
}

/**
 * Generate an immutable incident report package containing JSON and standalone HTML artifacts.
 */
export async function generateReport(
  payload: ReportGenerateRequest
): Promise<ReportGenerateResponse> {
  return await apiPost<ReportGenerateResponse>('/reports/generate', payload);
}

/**
 * Fetch raw artifact content (sanitized HTML string or raw JSON string).
 */
export async function exportReportArtifact(
  reportId: string,
  format: ReportFormat
): Promise<string> {
  return await apiGetText(`/reports/${encodeURIComponent(reportId)}/export`, { format });
}

/**
 * Retrieve metadata for artifacts associated with a report or investigation ID.
 */
export async function getReportArtifacts(reportId: string): Promise<ReportArtifactResponse[]> {
  return await apiGet<ReportArtifactResponse[]>(`/reports/${encodeURIComponent(reportId)}`);
}

/**
 * List persisted report artifacts with optional scenario or investigation filters.
 */
export async function listReportArtifacts(
  options: ListReportArtifactsOptions = {}
): Promise<ReportArtifactResponse[]> {
  const { scenarioId, investigationId, limit = 50, offset = 0 } = options;
  return await apiGet<ReportArtifactResponse[]>('/reports', {
    scenario_id: scenarioId,
    investigation_id: investigationId,
    limit,
    offset,
  });
}

