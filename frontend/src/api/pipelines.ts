/**
 * API client methods for pipeline observability, run history, and partition freshness.
 */

import { apiGet } from './client';
import { FreshnessCheck, PipelineRun } from '../types';

export interface ListPipelineRunsOptions {
  scenarioId?: string;
  limit?: number;
  offset?: number;
  includeLogs?: boolean;
}

export interface GetFreshnessOptions {
  scenarioId?: string;
  datasetId?: string;
}

/**
 * List historical pipeline runs, optionally filtered by scenario ID.
 */
export async function listPipelineRuns(
  options: ListPipelineRunsOptions = {}
): Promise<PipelineRun[]> {
  const { scenarioId, limit = 50, offset = 0, includeLogs = true } = options;
  return await apiGet<PipelineRun[]>('/pipelines/runs', {
    scenario_id: scenarioId,
    limit,
    offset,
    include_logs: includeLogs,
  });
}

/**
 * Get detailed execution metrics and step logs for a specific pipeline run.
 */
export async function getPipelineRun(runId: string): Promise<PipelineRun> {
  return await apiGet<PipelineRun>(`/pipelines/runs/${encodeURIComponent(runId)}`);
}

/**
 * Get dataset partition freshness checkpoints and SLA compliance status.
 */
export async function getPipelineFreshness(
  options: GetFreshnessOptions = {}
): Promise<FreshnessCheck[]> {
  const { scenarioId, datasetId } = options;
  return await apiGet<FreshnessCheck[]>('/pipelines/freshness', {
    scenario_id: scenarioId,
    dataset_id: datasetId,
  });
}

