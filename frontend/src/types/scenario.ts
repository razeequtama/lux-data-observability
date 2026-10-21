/**
 * Scenario schemas matching backend Pydantic models.
 */

import { DatasetResponse } from './dataset';

export type FixtureVersion = 'defective' | 'corrected';

export interface ScenarioSummary {
  id: string;
  name: string;
  description?: string | null;
  category: string;
  is_bundled: boolean;
  active_fixture_version: FixtureVersion | string;
  dataset_count: number;
  rule_count: number;
}

export interface ScenarioDetail extends ScenarioSummary {
  datasets: DatasetResponse[];
  created_at?: string | null;
  updated_at?: string | null;
}

export interface LoadScenarioRequest {
  fixture_version: FixtureVersion;
}

export interface LoadScenarioResponse {
  scenario_id: string;
  active_fixture_version: string;
  loaded_datasets: string[];
  rules_registered: number;
  lineage_nodes_loaded: number;
  message: string;
}

