/**
 * API client methods for quality validations and findings inspection.
 */

import { apiGet, apiPost } from './client';
import {
  ValidationFindingsListResponse,
  ValidationRunResponse,
} from '../types';

export interface ExecuteValidationRunOptions {
  scenarioId: string;
  datasetIds?: string[];
}

export interface ListFindingsOptions {
  severity?: string;
  status?: string;
  datasetId?: string;
  limit?: number;
  offset?: number;
}

/**
 * Execute a validation run for a scenario against registered datasets.
 */
export async function executeValidationRun(
  scenarioId: string,
  datasetIds?: string[]
): Promise<ValidationRunResponse> {
  return await apiPost<ValidationRunResponse>('/validations/run', {
    scenario_id: scenarioId,
    dataset_ids: datasetIds && datasetIds.length > 0 ? datasetIds : undefined,
  });
}

/**
 * Get summary of a specific validation run by ID.
 */
export async function getValidationRun(runId: string): Promise<ValidationRunResponse> {
  return await apiGet<ValidationRunResponse>(`/validations/runs/${encodeURIComponent(runId)}`);
}

/**
 * List historical validation runs, optionally filtered by scenario ID.
 */
export async function listValidationRuns(
  scenarioId?: string,
  limit = 20,
  offset = 0
): Promise<ValidationRunResponse[]> {
  return await apiGet<ValidationRunResponse[]>('/validations/runs', {
    scenario_id: scenarioId,
    limit,
    offset,
  });
}

/**
 * List granular findings for a specific validation run with optional filters.
 */
export async function listValidationFindings(
  runId: string,
  options?: ListFindingsOptions
): Promise<ValidationFindingsListResponse> {
  return await apiGet<ValidationFindingsListResponse>(
    `/validations/runs/${encodeURIComponent(runId)}/findings`,
    {
      severity: options?.severity && options.severity !== 'ALL' ? options.severity : undefined,
      status: options?.status && options.status !== 'ALL' ? options.status : undefined,
      dataset_id: options?.datasetId && options.datasetId !== 'ALL' ? options.datasetId : undefined,
      limit: options?.limit ?? 100,
      offset: options?.offset ?? 0,
    }
  );
}

