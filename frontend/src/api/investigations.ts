/**
 * API client methods for incident investigations and workspace management.
 */

import { apiDelete, apiGet, apiPatch, apiPost } from './client';
import {
  InvestigationCreateRequest,
  InvestigationResponse,
  InvestigationSynthesizeRequest,
  InvestigationUpdateRequest,
} from '../types';

export interface ListInvestigationsOptions {
  scenarioId?: string;
  status?: string;
  limit?: number;
  offset?: number;
}

/**
 * List investigation workspaces matching optional scenario or lifecycle status filters.
 */
export async function listInvestigations(
  options: ListInvestigationsOptions = {}
): Promise<InvestigationResponse[]> {
  const { scenarioId, status, limit = 50, offset = 0 } = options;
  return await apiGet<InvestigationResponse[]>('/investigations', {
    scenario_id: scenarioId,
    status,
    limit,
    offset,
  });
}

/**
 * Retrieve a specific investigation workspace by ID.
 */
export async function getInvestigation(investigationId: string): Promise<InvestigationResponse> {
  return await apiGet<InvestigationResponse>(`/investigations/${encodeURIComponent(investigationId)}`);
}

/**
 * Create a new investigation workspace.
 */
export async function createInvestigation(
  payload: InvestigationCreateRequest
): Promise<InvestigationResponse> {
  return await apiPost<InvestigationResponse>('/investigations', payload);
}

/**
 * Update an existing investigation workspace (title, status, facts, hypotheses, action items).
 */
export async function updateInvestigation(
  investigationId: string,
  payload: InvestigationUpdateRequest
): Promise<InvestigationResponse> {
  return await apiPatch<InvestigationResponse>(
    `/investigations/${encodeURIComponent(investigationId)}`,
    payload
  );
}

/**
 * Delete an investigation workspace by ID.
 */
export async function deleteInvestigation(investigationId: string): Promise<void> {
  await apiDelete(`/investigations/${encodeURIComponent(investigationId)}`);
}

/**
 * Automatically synthesize an investigation workspace from scenario evidence.
 */
export async function synthesizeInvestigation(
  payload: InvestigationSynthesizeRequest
): Promise<InvestigationResponse> {
  return await apiPost<InvestigationResponse>('/investigations/synthesize', payload);
}

