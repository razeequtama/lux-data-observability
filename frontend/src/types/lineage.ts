/**
 * TypeScript domain models for Lineage DAG nodes, edges, and graph responses.
 * Matches backend schemas from app/schemas/lineage.py.
 */

export type LineageNodeType =
  | 'SOURCE_DATASET'
  | 'TRANSFORMATION'
  | 'DERIVED_DATASET'
  | 'METRIC'
  | 'REPORT';

export interface NodePosition {
  x: number;
  y: number;
}

export interface LineageNodeData {
  label: string;
  type: LineageNodeType | string;
  dataset_id?: string | null;
  execution_status?: string | null;
  quality_health?: string | null;
  owner?: string | null;
  description?: string | null;
  metadata?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface LineageNode {
  id: string;
  name: string;
  type: LineageNodeType | string;
  dataset_id?: string | null;
  execution_status?: string | null;
  quality_health?: string | null;
  position: NodePosition;
  owner?: string | null;
  description?: string | null;
  metadata?: Record<string, unknown>;
  data?: LineageNodeData;
}

export interface LineageEdge {
  id: string;
  source: string;
  target: string;
  dependency_type?: string;
  animated?: boolean;
}

export interface LineageGraphResponse {
  scenario_id: string;
  nodes: LineageNode[];
  edges: LineageEdge[];
}

export interface LineageNodeSummary {
  id: string;
  name: string;
  type: string;
  dataset_id?: string | null;
  execution_status?: string | null;
  quality_health?: string | null;
}

export interface LineageNodeDetail {
  id: string;
  scenario_id: string;
  name: string;
  type: LineageNodeType | string;
  dataset_id?: string | null;
  owner?: string | null;
  description?: string | null;
  execution_status?: string | null;
  quality_health?: string | null;
  metadata: Record<string, unknown>;
  upstream_nodes: LineageNodeSummary[];
  downstream_nodes: LineageNodeSummary[];
  direct_upstream_count: number;
  direct_downstream_count: number;
  total_ancestors_count: number;
  total_descendants_count: number;
  upstream_dataset_ids: string[];
}

