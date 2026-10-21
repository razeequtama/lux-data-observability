import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { NodeDetailsPanel } from '../../src/components/lineage/NodeDetailsPanel';
import { BlastRadiusReport, LineageNodeDetail } from '../../src/types';

const mockNodeDetail: LineageNodeDetail = {
  id: 'src_orders',
  scenario_id: 'monday_revenue_mystery',
  name: 'orders.csv',
  type: 'SOURCE_DATASET',
  dataset_id: 'orders',
  owner: 'Data Engineering',
  description: 'Raw inbound e-commerce order transactions.',
  execution_status: 'COMPLETED_SUCCESS',
  quality_health: 'CORRUPTED',
  metadata: { engine: 'CSV' },
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

const mockBlastRadius: BlastRadiusReport = {
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
      explanation: 'Root failed dataset orders.csv',
    },
    {
      node_id: 'dim_orders',
      name: 'dim_orders',
      type: 'DERIVED_DATASET',
      impact_status: 'DIRECTLY_AFFECTED',
      distance: 2,
      dependency_path: ['src_orders', 'tf_orders', 'dim_orders'],
      dependency_path_names: ['orders.csv', 'transform_clean_orders', 'dim_orders'],
      explanation: 'Direct consumer of orders.csv via transform_clean_orders',
    },
    {
      node_id: 'report_exec_dash',
      name: 'Report: Executive Monday Dashboard',
      type: 'REPORT',
      impact_status: 'POTENTIALLY_AFFECTED',
      distance: 6,
      dependency_path: [
        'src_orders',
        'tf_orders',
        'dim_orders',
        'tf_revenue',
        'agg_daily_revenue',
        'metric_revenue',
        'report_exec_dash',
      ],
      dependency_path_names: [
        'orders.csv',
        'transform_clean_orders',
        'dim_orders',
        'aggregate_daily_revenue',
        'agg_daily_revenue',
        'metric_revenue',
        'report_exec_dash',
      ],
      explanation: 'Transitive consumer feeding revenue KPI into Executive Dashboard',
    },
  ],
};

describe('NodeDetailsPanel Component', () => {
  it('renders nothing when nodeDetail is null', () => {
    const { container } = render(
      <NodeDetailsPanel
        nodeDetail={null}
        blastRadius={null}
        onClose={vi.fn()}
        onSelectNode={vi.fn()}
      />
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders node details, metadata, and dual-dimension health cards', () => {
    render(
      <NodeDetailsPanel
        nodeDetail={mockNodeDetail}
        blastRadius={null}
        onClose={vi.fn()}
        onSelectNode={vi.fn()}
      />
    );

    expect(screen.getByText('orders.csv')).toBeInTheDocument();
    expect(screen.getByText('ID: src_orders')).toBeInTheDocument();
    expect(screen.getByText('SOURCE_DATASET')).toBeInTheDocument();
    expect(screen.getByText('Data Engineering')).toBeInTheDocument();
    expect(
      screen.getByText('Raw inbound e-commerce order transactions.')
    ).toBeInTheDocument();

    // Dual health dimension cards
    expect(screen.getByText('COMPLETED_SUCCESS')).toBeInTheDocument();
    expect(screen.getByText('CORRUPTED')).toBeInTheDocument();
  });

  it('renders downstream blast radius summary and impact explanation chains', () => {
    render(
      <NodeDetailsPanel
        nodeDetail={mockNodeDetail}
        blastRadius={mockBlastRadius}
        onClose={vi.fn()}
        onSelectNode={vi.fn()}
      />
    );

    expect(screen.getByTestId('blast-radius-summary')).toBeInTheDocument();
    expect(screen.getByText('4 Assets Affected')).toBeInTheDocument();
    expect(
      screen.getByText('This node is the root failure origin for this blast radius.')
    ).toBeInTheDocument();

    // Explanations
    expect(
      screen.getByText('Direct consumer of orders.csv via transform_clean_orders')
    ).toBeInTheDocument();
    expect(
      screen.getByText('Transitive consumer feeding revenue KPI into Executive Dashboard')
    ).toBeInTheDocument();
  });

  it('calls onSelectNode when a downstream affected asset or predecessor is clicked', () => {
    const handleSelectNode = vi.fn();
    render(
      <NodeDetailsPanel
        nodeDetail={mockNodeDetail}
        blastRadius={mockBlastRadius}
        onClose={vi.fn()}
        onSelectNode={handleSelectNode}
      />
    );

    const assetButton = screen.getByRole('button', {
      name: /Report: Executive Monday Dashboard/i,
    });
    fireEvent.click(assetButton);
    expect(handleSelectNode).toHaveBeenCalledWith('report_exec_dash');
  });

  it('calls onClose when close button is clicked', () => {
    const handleClose = vi.fn();
    render(
      <NodeDetailsPanel
        nodeDetail={mockNodeDetail}
        blastRadius={null}
        onClose={handleClose}
        onSelectNode={vi.fn()}
      />
    );

    const closeBtn = screen.getByRole('button', { name: /close inspector panel/i });
    fireEvent.click(closeBtn);
    expect(handleClose).toHaveBeenCalledTimes(1);
  });
});
