import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  getLineageGraph,
  getLineageNodeDetail,
  traceDownstreamImpact,
} from '../../src/api/lineage';
import * as client from '../../src/api/client';

describe('Lineage & Impact API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('getLineageGraph calls GET /lineage with scenario_id', async () => {
    const mockResponse = {
      scenario_id: 'monday_revenue_mystery',
      nodes: [
        {
          id: 'src_orders',
          name: 'orders.csv',
          type: 'SOURCE_DATASET',
          position: { x: 50, y: 100 },
        },
      ],
      edges: [
        {
          id: 'e1',
          source: 'src_orders',
          target: 'tf_orders',
        },
      ],
    };

    const spy = vi.spyOn(client, 'apiGet').mockResolvedValue(mockResponse);

    const result = await getLineageGraph('monday_revenue_mystery');

    expect(spy).toHaveBeenCalledWith('/lineage', {
      scenario_id: 'monday_revenue_mystery',
    });
    expect(result.nodes).toHaveLength(1);
    expect(result.nodes[0].id).toBe('src_orders');
  });

  it('getLineageNodeDetail calls GET /lineage/nodes/{id}', async () => {
    const mockDetail = {
      id: 'src_orders',
      scenario_id: 'monday_revenue_mystery',
      name: 'orders.csv',
      type: 'SOURCE_DATASET',
      dataset_id: 'orders',
      execution_status: 'COMPLETED_SUCCESS',
      quality_health: 'CORRUPTED',
      metadata: {},
      upstream_nodes: [],
      downstream_nodes: [
        {
          id: 'tf_orders',
          name: 'transform_clean_orders',
          type: 'TRANSFORMATION',
        },
      ],
      direct_upstream_count: 0,
      direct_downstream_count: 1,
      total_ancestors_count: 0,
      total_descendants_count: 6,
      upstream_dataset_ids: ['orders'],
    };

    const spy = vi.spyOn(client, 'apiGet').mockResolvedValue(mockDetail);

    const result = await getLineageNodeDetail('src_orders', 'monday_revenue_mystery');

    expect(spy).toHaveBeenCalledWith('/lineage/nodes/src_orders', {
      scenario_id: 'monday_revenue_mystery',
    });
    expect(result.name).toBe('orders.csv');
    expect(result.quality_health).toBe('CORRUPTED');
    expect(result.downstream_nodes[0].id).toBe('tf_orders');
  });

  it('traceDownstreamImpact calls POST /impact/trace with request payload', async () => {
    const mockReport = {
      target_id: 'orders.csv',
      target_type: 'DATASET',
      root_node_id: 'src_orders',
      root_dataset_id: 'orders',
      scenario_id: 'monday_revenue_mystery',
      total_affected_assets: 4,
      impact_summary: {
        confirmed_failed: 1,
        directly_affected: 1,
        potentially_affected: 2,
        healthy: 0,
      },
      affected_assets: [
        {
          node_id: 'src_orders',
          name: 'orders.csv',
          type: 'SOURCE_DATASET',
          impact_status: 'CONFIRMED_FAILED',
          distance: 0,
          dependency_path: ['src_orders'],
          dependency_path_names: ['orders.csv'],
        },
        {
          node_id: 'report_exec_dash',
          name: 'Report: Executive Monday Dashboard',
          type: 'REPORT',
          impact_status: 'POTENTIALLY_AFFECTED',
          distance: 6,
          dependency_path: ['src_orders', 'tf_orders', 'dim_orders', 'tf_revenue', 'agg_daily_revenue', 'metric_revenue', 'report_exec_dash'],
          dependency_path_names: ['orders.csv', 'transform_clean_orders', 'dim_orders', 'aggregate_daily_revenue', 'agg_daily_revenue', 'metric_revenue', 'report_exec_dash'],
        },
      ],
    };

    const spy = vi.spyOn(client, 'apiPost').mockResolvedValue(mockReport);

    const result = await traceDownstreamImpact({
      scenario_id: 'monday_revenue_mystery',
      target_type: 'NODE',
      target_id: 'src_orders',
    });

    expect(spy).toHaveBeenCalledWith('/impact/trace', {
      scenario_id: 'monday_revenue_mystery',
      target_type: 'NODE',
      target_id: 'src_orders',
      include_transformations: true,
      include_root: true,
    });
    expect(result.root_node_id).toBe('src_orders');
    expect(result.total_affected_assets).toBe(4);
    expect(result.affected_assets[1].impact_status).toBe('POTENTIALLY_AFFECTED');
  });
});

