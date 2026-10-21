import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { LineageView } from '../../src/components/lineage/LineageView';
import * as lineageApi from '../../src/api/lineage';
import {
  BlastRadiusReport,
  LineageGraphResponse,
  LineageNodeDetail,
} from '../../src/types';

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
    {
      id: 'src_order_items',
      name: 'order_items.csv',
      type: 'SOURCE_DATASET',
      dataset_id: 'order_items',
      execution_status: 'COMPLETED_SUCCESS',
      quality_health: 'CORRUPTED',
      position: { x: 50, y: 220 },
      data: { label: 'order_items.csv', type: 'SOURCE_DATASET' },
    },
    {
      id: 'src_products',
      name: 'products.csv',
      type: 'SOURCE_DATASET',
      dataset_id: 'products',
      execution_status: 'COMPLETED_SUCCESS',
      quality_health: 'HEALTHY',
      position: { x: 50, y: 340 },
      data: { label: 'products.csv', type: 'SOURCE_DATASET' },
    },
    {
      id: 'src_inventory',
      name: 'inventory.csv',
      type: 'SOURCE_DATASET',
      dataset_id: 'inventory',
      execution_status: 'COMPLETED_SUCCESS',
      quality_health: 'CORRUPTED',
      position: { x: 50, y: 460 },
      data: { label: 'inventory.csv', type: 'SOURCE_DATASET' },
    },
    {
      id: 'tf_orders',
      name: 'transform_clean_orders',
      type: 'TRANSFORMATION',
      execution_status: 'COMPLETED_SUCCESS',
      quality_health: 'CORRUPTED',
      position: { x: 300, y: 100 },
      metadata: { engine: 'SQL' },
      data: { label: 'transform_clean_orders', type: 'TRANSFORMATION' },
    },
    {
      id: 'tf_items',
      name: 'transform_order_line_items',
      type: 'TRANSFORMATION',
      execution_status: 'COMPLETED_SUCCESS',
      quality_health: 'CORRUPTED',
      position: { x: 300, y: 280 },
      metadata: { engine: 'SQL' },
      data: { label: 'transform_order_line_items', type: 'TRANSFORMATION' },
    },
    {
      id: 'tf_inventory',
      name: 'transform_inventory_snapshot',
      type: 'TRANSFORMATION',
      execution_status: 'COMPLETED_SUCCESS',
      quality_health: 'CORRUPTED',
      position: { x: 300, y: 460 },
      metadata: { engine: 'Python' },
      data: { label: 'transform_inventory_snapshot', type: 'TRANSFORMATION' },
    },
    {
      id: 'dim_orders',
      name: 'dim_orders',
      type: 'DERIVED_DATASET',
      execution_status: 'COMPLETED_SUCCESS',
      quality_health: 'CORRUPTED',
      position: { x: 550, y: 100 },
      data: { label: 'dim_orders', type: 'DERIVED_DATASET' },
    },
    {
      id: 'fct_order_items',
      name: 'fct_order_items',
      type: 'DERIVED_DATASET',
      execution_status: 'COMPLETED_SUCCESS',
      quality_health: 'CORRUPTED',
      position: { x: 550, y: 280 },
      data: { label: 'fct_order_items', type: 'DERIVED_DATASET' },
    },
    {
      id: 'dim_inventory',
      name: 'dim_inventory',
      type: 'DERIVED_DATASET',
      execution_status: 'COMPLETED_SUCCESS',
      quality_health: 'CORRUPTED',
      position: { x: 550, y: 460 },
      data: { label: 'dim_inventory', type: 'DERIVED_DATASET' },
    },
    {
      id: 'tf_revenue',
      name: 'aggregate_daily_revenue',
      type: 'TRANSFORMATION',
      execution_status: 'COMPLETED_SUCCESS',
      quality_health: 'CORRUPTED',
      position: { x: 800, y: 190 },
      metadata: { engine: 'SQL' },
      data: { label: 'aggregate_daily_revenue', type: 'TRANSFORMATION' },
    },
    {
      id: 'agg_daily_revenue',
      name: 'agg_daily_revenue',
      type: 'DERIVED_DATASET',
      execution_status: 'COMPLETED_SUCCESS',
      quality_health: 'CORRUPTED',
      position: { x: 1050, y: 190 },
      data: { label: 'agg_daily_revenue', type: 'DERIVED_DATASET' },
    },
    {
      id: 'metric_revenue',
      name: 'Metric: Total Daily Revenue',
      type: 'METRIC',
      execution_status: 'COMPLETED_SUCCESS',
      quality_health: 'CORRUPTED',
      position: { x: 1300, y: 190 },
      data: { label: 'Metric: Total Daily Revenue', type: 'METRIC' },
    },
    {
      id: 'metric_inventory',
      name: 'Metric: Inventory Health Ratio',
      type: 'METRIC',
      execution_status: 'COMPLETED_SUCCESS',
      quality_health: 'CORRUPTED',
      position: { x: 800, y: 460 },
      data: { label: 'Metric: Inventory Health Ratio', type: 'METRIC' },
    },
    {
      id: 'report_exec_dash',
      name: 'Report: Executive Monday Dashboard',
      type: 'REPORT',
      execution_status: 'COMPLETED_SUCCESS',
      quality_health: 'CORRUPTED',
      position: { x: 1550, y: 190 },
      data: { label: 'Report: Executive Monday Dashboard', type: 'REPORT' },
    },
    {
      id: 'report_stock_alert',
      name: 'Report: Warehouse Stock Alert',
      type: 'REPORT',
      execution_status: 'COMPLETED_SUCCESS',
      quality_health: 'CORRUPTED',
      position: { x: 1050, y: 460 },
      data: { label: 'Report: Warehouse Stock Alert', type: 'REPORT' },
    },
  ],
  edges: [
    { id: 'e1', source: 'src_orders', target: 'tf_orders' },
    { id: 'e2', source: 'tf_orders', target: 'dim_orders' },
    { id: 'e3', source: 'src_order_items', target: 'tf_items' },
    { id: 'e4', source: 'src_products', target: 'tf_items' },
    { id: 'e5', source: 'tf_items', target: 'fct_order_items' },
    { id: 'e6', source: 'src_inventory', target: 'tf_inventory' },
    { id: 'e7', source: 'tf_inventory', target: 'dim_inventory' },
    { id: 'e8', source: 'dim_orders', target: 'tf_revenue' },
    { id: 'e9', source: 'fct_order_items', target: 'tf_revenue' },
    { id: 'e10', source: 'tf_revenue', target: 'agg_daily_revenue' },
    { id: 'e11', source: 'agg_daily_revenue', target: 'metric_revenue' },
    { id: 'e12', source: 'metric_revenue', target: 'report_exec_dash' },
    { id: 'e13', source: 'dim_inventory', target: 'metric_inventory' },
    { id: 'e14', source: 'metric_inventory', target: 'report_stock_alert' },
  ],
};

const mockOrdersBlastRadius: BlastRadiusReport = {
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
      impact_status: 'DIRECTLY_AFFECTED',
      distance: 2,
      dependency_path: ['src_orders', 'tf_orders', 'dim_orders'],
      dependency_path_names: ['orders.csv', 'transform_clean_orders', 'dim_orders'],
    },
    {
      node_id: 'agg_daily_revenue',
      name: 'agg_daily_revenue',
      type: 'DERIVED_DATASET',
      impact_status: 'POTENTIALLY_AFFECTED',
      distance: 4,
      dependency_path: ['src_orders', 'tf_orders', 'dim_orders', 'tf_revenue', 'agg_daily_revenue'],
      dependency_path_names: ['orders.csv', 'transform_clean_orders', 'dim_orders', 'aggregate_daily_revenue', 'agg_daily_revenue'],
    },
    {
      node_id: 'metric_revenue',
      name: 'Metric: Total Daily Revenue',
      type: 'METRIC',
      impact_status: 'POTENTIALLY_AFFECTED',
      distance: 5,
      dependency_path: ['src_orders', 'tf_orders', 'dim_orders', 'tf_revenue', 'agg_daily_revenue', 'metric_revenue'],
      dependency_path_names: ['orders.csv', 'transform_clean_orders', 'dim_orders', 'aggregate_daily_revenue', 'agg_daily_revenue', 'metric_revenue'],
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
  downstream_nodes: [
    { id: 'tf_orders', name: 'transform_clean_orders', type: 'TRANSFORMATION' },
  ],
  direct_upstream_count: 0,
  direct_downstream_count: 1,
  total_ancestors_count: 0,
  total_descendants_count: 6,
  upstream_dataset_ids: ['orders'],
};

describe('LineageView Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(lineageApi, 'getLineageGraph').mockResolvedValue(mockGraphResponse);
    vi.spyOn(lineageApi, 'getLineageNodeDetail').mockResolvedValue(mockNodeDetail);
    vi.spyOn(lineageApi, 'traceDownstreamImpact').mockResolvedValue(mockOrdersBlastRadius);
  });

  it('acceptance criterion: renders all 16 nodes with clear visual hierarchy', async () => {
    render(<LineageView scenarioId="monday_revenue_mystery" />);

    // Wait for graph data to load
    await waitFor(() => {
      expect(screen.getByText('16 Nodes')).toBeInTheDocument();
    });

    // Verify all 16 nodes are rendered via unique test IDs and labels
    expect(screen.getByTestId('lineage-node-src_orders')).toBeInTheDocument();
    expect(screen.getByTestId('lineage-node-src_order_items')).toBeInTheDocument();
    expect(screen.getByTestId('lineage-node-src_products')).toBeInTheDocument();
    expect(screen.getByTestId('lineage-node-src_inventory')).toBeInTheDocument();
    expect(screen.getByTestId('lineage-node-tf_orders')).toBeInTheDocument();
    expect(screen.getByTestId('lineage-node-tf_items')).toBeInTheDocument();
    expect(screen.getByTestId('lineage-node-tf_inventory')).toBeInTheDocument();
    expect(screen.getByTestId('lineage-node-dim_orders')).toBeInTheDocument();
    expect(screen.getByTestId('lineage-node-fct_order_items')).toBeInTheDocument();
    expect(screen.getByTestId('lineage-node-dim_inventory')).toBeInTheDocument();
    expect(screen.getByTestId('lineage-node-tf_revenue')).toBeInTheDocument();
    expect(screen.getByTestId('lineage-node-agg_daily_revenue')).toBeInTheDocument();
    expect(screen.getByTestId('lineage-node-metric_revenue')).toBeInTheDocument();
    expect(screen.getByTestId('lineage-node-metric_inventory')).toBeInTheDocument();
    expect(screen.getByTestId('lineage-node-report_exec_dash')).toBeInTheDocument();
    expect(screen.getByTestId('lineage-node-report_stock_alert')).toBeInTheDocument();

    // Verify toolbar counts
    expect(screen.getByText('14 Directed Edges')).toBeInTheDocument();
  });

  it('acceptance criterion: selecting src_orders highlights downstream path through to report_exec_dash', async () => {
    render(<LineageView scenarioId="monday_revenue_mystery" />);

    await waitFor(() => {
      expect(screen.getByText('orders.csv')).toBeInTheDocument();
    });

    // Click on the src_orders node
    const srcOrdersNode = screen.getByTestId('lineage-node-src_orders');
    fireEvent.click(srcOrdersNode);

    // Wait for blast radius and details to be fetched
    await waitFor(() => {
      expect(screen.getByTestId('node-details-panel')).toBeInTheDocument();
    });

    // Assert that src_orders is Failure Origin
    expect(srcOrdersNode).toHaveAttribute('data-impact-status', 'CONFIRMED_FAILED');

    // Assert that downstream assets on the path have active impact status
    const dimOrdersNode = screen.getByTestId('lineage-node-dim_orders');
    expect(dimOrdersNode).toHaveAttribute('data-impact-status', 'DIRECTLY_AFFECTED');

    const reportExecDashNode = screen.getByTestId('lineage-node-report_exec_dash');
    expect(reportExecDashNode).toHaveAttribute('data-impact-status', 'POTENTIALLY_AFFECTED');

    // Assert that unrelated branch (e.g. inventory) is dimmed
    const inventoryNode = screen.getByTestId('lineage-node-src_inventory');
    expect(inventoryNode.className).toContain('opacity-30');

    // Assert that inspector panel shows downstream blast radius summary
    expect(screen.getByText('6 Assets Affected')).toBeInTheDocument();
  });

  it('filters nodes by search query', async () => {
    render(<LineageView scenarioId="monday_revenue_mystery" />);

    await waitFor(() => {
      expect(screen.getByText('orders.csv')).toBeInTheDocument();
    });

    const searchInput = screen.getByRole('textbox', { name: /search dag nodes/i });
    fireEvent.change(searchInput, { target: { value: 'Executive' } });

    // Node matching query should be visible
    expect(screen.getByText('Report: Executive Monday Dashboard')).toBeInTheDocument();
  });

  it('filters nodes by asset type dropdown', async () => {
    render(<LineageView scenarioId="monday_revenue_mystery" />);

    await waitFor(() => {
      expect(screen.getByText('orders.csv')).toBeInTheDocument();
    });

    const typeSelect = screen.getByRole('combobox', { name: /filter by asset type/i });
    fireEvent.change(typeSelect, { target: { value: 'REPORT' } });

    expect(screen.getByText('Report: Executive Monday Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Report: Warehouse Stock Alert')).toBeInTheDocument();
  });

  it('resets selection and edge highlights when Reset Highlight is clicked', async () => {
    render(<LineageView scenarioId="monday_revenue_mystery" />);

    await waitFor(() => {
      expect(screen.getByText('orders.csv')).toBeInTheDocument();
    });

    // Select node
    const srcOrdersNode = screen.getByTestId('lineage-node-src_orders');
    fireEvent.click(srcOrdersNode);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /reset highlight/i })).toBeInTheDocument();
    });

    // Click Reset
    const resetBtn = screen.getByRole('button', { name: /reset highlight/i });
    fireEvent.click(resetBtn);

    // Inspector panel should be closed and nodes un-dimmed
    await waitFor(() => {
      expect(screen.queryByTestId('node-details-panel')).not.toBeInTheDocument();
    });

    const inventoryNode = screen.getByTestId('lineage-node-src_inventory');
    expect(inventoryNode.className).not.toContain('opacity-30');
  });

  it('renders error state when graph retrieval fails', async () => {
    vi.spyOn(lineageApi, 'getLineageGraph').mockRejectedValue(new Error('Network connection timeout'));

    render(<LineageView scenarioId="monday_revenue_mystery" />);

    await waitFor(() => {
      expect(screen.getByTestId('lineage-error')).toBeInTheDocument();
    });

    expect(screen.getByText('Failed to Load Lineage DAG')).toBeInTheDocument();
    expect(screen.getByText('Network connection timeout')).toBeInTheDocument();
  });
});
