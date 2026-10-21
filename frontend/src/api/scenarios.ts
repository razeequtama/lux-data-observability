/**
 * Scenarios API methods.
 */

import { apiGet, apiPost } from './client';
import {
  FixtureVersion,
  LoadScenarioRequest,
  LoadScenarioResponse,
  ScenarioDetail,
  ScenarioSummary,
} from '../types';

export async function listScenarios(): Promise<ScenarioSummary[]> {
  return apiGet<ScenarioSummary[]>('/scenarios');
}

export async function getScenario(scenarioId: string): Promise<ScenarioDetail> {
  return apiGet<ScenarioDetail>(`/scenarios/${encodeURIComponent(scenarioId)}`);
}

export async function loadScenario(
  scenarioId: string,
  fixtureVersion: FixtureVersion = 'defective'
): Promise<LoadScenarioResponse> {
  const payload: LoadScenarioRequest = { fixture_version: fixtureVersion };
  return apiPost<LoadScenarioResponse>(
    `/scenarios/${encodeURIComponent(scenarioId)}/load`,
    payload
  );
}

