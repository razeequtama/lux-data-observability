/**
 * TypeScript domain models for Downstream Impact Analysis & Blast Radius.
 * Matches backend schemas from app/schemas/impact.py.
 */

export type AssetImpactStatus =
  | 'CONFIRMED_FAILED'
  | 'DIRECTLY_AFFECTED'
  | 'POTENTIALLY_AFFECTED'
  | 'HEALTHY';

export type ImpactTargetType = 'FINDING' | 'DATASET' | 'NODE' | 'RULE' | 'AUTO';

export interface AffectedAsset {
  node_id: string;
  name: string;
  type: string;
  impact_status: AssetImpactStatus;
  distance: number;
  dependency_path: string[];
  dependency_path_names: string[];
  explanation?: string | null;
}

export interface ImpactSummary {
  confirmed_failed: number;
  directly_affected: number;
  potentially_affected: number;
  healthy: number;
}

export interface BlastRadiusReport {
  target_id: string;
  target_type: string;
  root_node_id: string;
  root_dataset_id?: string | null;
  scenario_id?: string | null;
  total_affected_assets: number;
  impact_summary: ImpactSummary;
  affected_assets: AffectedAsset[];
}

export interface ImpactTraceRequest {
  scenario_id?: string;
  target_type?: ImpactTargetType | string;
  target_id: string;
  include_transformations?: boolean;
  include_root?: boolean;
}

