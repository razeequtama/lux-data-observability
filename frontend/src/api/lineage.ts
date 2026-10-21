/**
 * API client methods for Lineage DAG retrieval, node details, and impact tracing.
 */

import { apiGet, apiPost } from './client';
import {
  BlastRadiusReport,
  ImpactTraceRequest,
  LineageGraphResponse,
  LineageNodeDetail,
} from '../types';

/**
 * Fetch complete lineage graph for a scenario, formatted with Dagre layout positions.
 */
export async function getLineageGraph(
  scenarioId = 'monday_revenue_mystery'
): Promise<LineageGraphResponse> {
  return await apiGet<LineageGraphResponse>('/lineage', {
    scenario_id: scenarioId,
  });
}

/**
 * Fetch detailed metadata, upstream inputs, and downstream consumers for a single node.
 */
export async function getLineageNodeDetail(
  nodeId: string,
  scenarioId = 'monday_revenue_mystery'
): Promise<LineageNodeDetail> {
  return await apiGet<LineageNodeDetail>(`/lineage/nodes/${encodeURIComponent(nodeId)}`, {
    scenario_id: scenarioId,
  });
}

/**
 * Trace downstream impact blast radius originating from a finding, dataset, or node.
 */
export async function traceDownstreamImpact(
  request: ImpactTraceRequest
): Promise<BlastRadiusReport> {
  return await apiPost<BlastRadiusReport>('/impact/trace', {
    scenario_id: request.scenario_id || 'monday_revenue_mystery',
    target_type: request.target_type || 'AUTO',
    target_id: request.target_id,
    include_transformations: request.include_transformations ?? true,
    include_root: request.include_root ?? true,
  });
}

