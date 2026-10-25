import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ImpactAnalysisView } from '../../src/components/impact/ImpactAnalysisView';
import * as lineageApi from '../../src/api/lineage';
import { BlastRadiusReport, LineageGraphResponse, LineageNodeDetail } from '../../src/types';

const mockBlastRadius: BlastRadiusReport = {
  target_id: 'src_orders',
  target_type: 'NODE',
  root_node_id: 'src_orders',
  root_dataset_id: 'orders',
  scenario_id: 'monday_revenue_mystery',
  total_affected_assets: 6,
  impact_summary: {
    confirmed_failed: 1,
    directly_affected: 2,
    potentially_affected: 3,
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
      node_id: 'tf_orders',
      name: 'transform_clean_orders',
      type: 'TRANSFORMATION',
      impact_status: 'DIRECTLY_AFFECTED',
      distance: 1,
      dependency_path: ['src_orders', 'tf_orders'],
      dependency_path_names: ['orders.csv', 'transform_clean_orders'],
    },
    {
      node_id: 'dim_orders',
      name: 'dim_orders',
      type: 'DERIVED_DATASET',
      impact_status: 'POTENTIALLY_AFFECTED',
      distance: 2,
      dependency_path: ['src_orders', 'tf_orders', 'dim_orders'],
      dependency_path_names: ['orders.csv', 'transform_clean_orders', 'dim_orders'],
    },
  ],
};

const mockGraphResponse: LineageGraphResponse = {
  scenario_id: 'monday_revenue_mystery',
  nodes: [
    {
      id: 'src_orders',
      name: 'orders.csv',
      type: 'SOURCE_DATASET',
      dataset_id: 'orders',
      execution_status: 'COMPLETED_SUCCESS',
      quality_health: 'CORRUPTED',
      position: { x: 50, y: 100 },
      data: { label: 'orders.csv', type: 'SOURCE_DATASET' },
    },
  ],
  edges: [],
};

const mockNodeDetail: LineageNodeDetail = {
  id: 'src_orders',
  scenario_id: 'monday_revenue_mystery',
  name: 'orders.csv',
  type: 'SOURCE_DATASET',
  dataset_id: 'orders',
  owner: 'Data Engineering',
  description: 'Inbound e-commerce order transactions.',
  execution_status: 'COMPLETED_SUCCESS',
  quality_health: 'CORRUPTED',
  metadata: {},
  upstream_nodes: [],
  downstream_nodes: [],
  direct_upstream_count: 0,
  direct_downstream_count: 0,
  total_ancestors_count: 0,
  total_descendants_count: 0,
  upstream_dataset_ids: ['orders'],
};

describe('ImpactAnalysisView Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(lineageApi, 'traceDownstreamImpact').mockResolvedValue(mockBlastRadius);
    vi.spyOn(lineageApi, 'getLineageGraph').mockResolvedValue(mockGraphResponse);
    vi.spyOn(lineageApi, 'getLineageNodeDetail').mockResolvedValue(mockNodeDetail);
  });

  it('renders the impact analysis view and blast radius summary metrics', async () => {
    render(
      <ImpactAnalysisView
        scenarioId="monday_revenue_mystery"
        isScenarioLoaded={true}
      />
    );

    expect(screen.getByTestId('impact-analysis-view')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByTestId('impact-summary-metrics')).toBeInTheDocument();
    });

    expect(screen.getByText('Downstream Impact & Blast Radius Analysis')).toBeInTheDocument();
    expect(screen.getByText('Total Blast Radius')).toBeInTheDocument();
    expect(screen.getByText('Root Cause')).toBeInTheDocument();
    expect(screen.getByText('Direct Consumers')).toBeInTheDocument();
    expect(screen.getByText('Transitive Impact')).toBeInTheDocument();
    expect(screen.getAllByText('orders.csv').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('transform_clean_orders').length).toBeGreaterThanOrEqual(1);
  });

  it('allows changing the root cause target and refetches blast radius', async () => {
    render(
      <ImpactAnalysisView
        scenarioId="monday_revenue_mystery"
        isScenarioLoaded={true}
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId('impact-target-select')).toBeInTheDocument();
    });

    const select = screen.getByTestId('impact-target-select');
    fireEvent.change(select, { target: { value: 'src_inventory' } });

    await waitFor(() => {
      expect(lineageApi.traceDownstreamImpact).toHaveBeenCalledWith(
        expect.objectContaining({
          target_id: 'src_inventory',
        })
      );
    });
  });

  it('displays error banner if blast radius tracing fails', async () => {
    vi.spyOn(lineageApi, 'traceDownstreamImpact').mockRejectedValueOnce(
      new Error('Failed to resolve graph cycle')
    );

    render(
      <ImpactAnalysisView
        scenarioId="monday_revenue_mystery"
        isScenarioLoaded={true}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Downstream Impact Error')).toBeInTheDocument();
      expect(screen.getByText('Failed to resolve graph cycle')).toBeInTheDocument();
    });
  });
});

