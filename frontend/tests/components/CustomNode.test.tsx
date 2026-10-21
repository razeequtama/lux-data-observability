import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { ReactFlowProvider } from '@xyflow/react';
import { CustomNode, CustomNodeProps } from '../../src/components/lineage/CustomNode';

const renderWithProvider = (props: CustomNodeProps) => {
  return render(
    <ReactFlowProvider>
      <CustomNode {...props} />
    </ReactFlowProvider>
  );
};

describe('CustomNode Component', () => {
  it('renders SOURCE_DATASET node with labels, storage dataset, and Exit 0 / Corrupted chips', () => {
    const props: CustomNodeProps = {
      id: 'src_orders',
      data: {
        id: 'src_orders',
        label: 'orders.csv',
        name: 'orders.csv',
        type: 'SOURCE_DATASET',
        dataset_id: 'orders',
        execution_status: 'COMPLETED_SUCCESS',
        quality_health: 'CORRUPTED',
      },
    } as unknown as CustomNodeProps;

    renderWithProvider(props);

    expect(screen.getByText('orders.csv')).toBeInTheDocument();
    expect(screen.getByTitle('src_orders')).toBeInTheDocument();
    expect(screen.getByText('SOURCE')).toBeInTheDocument();
    expect(screen.getByText('orders')).toBeInTheDocument();

    // Dual status dimensions
    expect(screen.getByText('Exit 0')).toBeInTheDocument();
    expect(screen.getByText('Corrupted')).toBeInTheDocument();
  });

  it('renders TRANSFORMATION node with engine metadata and Healthy chip', () => {
    const props: CustomNodeProps = {
      id: 'tf_orders',
      data: {
        id: 'tf_orders',
        label: 'transform_clean_orders',
        name: 'transform_clean_orders',
        type: 'TRANSFORMATION',
        execution_status: 'COMPLETED_SUCCESS',
        quality_health: 'HEALTHY',
        metadata: { engine: 'SQL' },
      },
    } as unknown as CustomNodeProps;

    renderWithProvider(props);

    expect(screen.getByText('transform_clean_orders')).toBeInTheDocument();
    expect(screen.getByText('TRANSFORM')).toBeInTheDocument();
    expect(screen.getByText('SQL')).toBeInTheDocument();
    expect(screen.getByText('Healthy')).toBeInTheDocument();
  });

  it('renders METRIC and REPORT nodes correctly', () => {
    const metricProps: CustomNodeProps = {
      id: 'metric_revenue',
      data: {
        id: 'metric_revenue',
        label: 'Metric: Total Daily Revenue',
        type: 'METRIC',
        execution_status: 'COMPLETED_SUCCESS',
        quality_health: 'HEALTHY',
      },
    } as unknown as CustomNodeProps;

    const { unmount } = renderWithProvider(metricProps);
    expect(screen.getByText('Metric: Total Daily Revenue')).toBeInTheDocument();
    expect(screen.getByText('METRIC')).toBeInTheDocument();
    unmount();

    const reportProps: CustomNodeProps = {
      id: 'report_exec_dash',
      data: {
        id: 'report_exec_dash',
        label: 'Report: Executive Monday Dashboard',
        type: 'REPORT',
        execution_status: 'COMPLETED_SUCCESS',
        quality_health: 'HEALTHY',
      },
    } as unknown as CustomNodeProps;

    renderWithProvider(reportProps);
    expect(screen.getByText('Report: Executive Monday Dashboard')).toBeInTheDocument();
    expect(screen.getByText('REPORT')).toBeInTheDocument();
  });

  it('renders Blast Radius Failure Origin badge when CONFIRMED_FAILED', () => {
    const props: CustomNodeProps = {
      id: 'src_orders',
      data: {
        id: 'src_orders',
        label: 'orders.csv',
        type: 'SOURCE_DATASET',
        impactStatus: 'CONFIRMED_FAILED',
        quality_health: 'CORRUPTED',
      },
    } as unknown as CustomNodeProps;

    renderWithProvider(props);

    expect(screen.getByText('Failure Origin')).toBeInTheDocument();
    const nodeEl = screen.getByTestId('lineage-node-src_orders');
    expect(nodeEl).toHaveAttribute('data-impact-status', 'CONFIRMED_FAILED');
  });

  it('renders Direct Consumer badge when DIRECTLY_AFFECTED', () => {
    const props: CustomNodeProps = {
      id: 'dim_orders',
      data: {
        id: 'dim_orders',
        label: 'dim_orders',
        type: 'DERIVED_DATASET',
        impactStatus: 'DIRECTLY_AFFECTED',
      },
    } as unknown as CustomNodeProps;

    renderWithProvider(props);

    expect(screen.getByText('Direct Consumer')).toBeInTheDocument();
  });

  it('renders Blast Radius badge when POTENTIALLY_AFFECTED', () => {
    const props: CustomNodeProps = {
      id: 'report_exec_dash',
      data: {
        id: 'report_exec_dash',
        label: 'Report: Executive Monday Dashboard',
        type: 'REPORT',
        impactStatus: 'POTENTIALLY_AFFECTED',
      },
    } as unknown as CustomNodeProps;

    renderWithProvider(props);

    expect(screen.getByText('Blast Radius')).toBeInTheDocument();
  });

  it('applies dimmed opacity when node is not in active blast radius', () => {
    const props: CustomNodeProps = {
      id: 'src_inventory',
      data: {
        id: 'src_inventory',
        label: 'inventory.csv',
        type: 'SOURCE_DATASET',
        isDimmed: true,
      },
    } as unknown as CustomNodeProps;

    renderWithProvider(props);

    const nodeEl = screen.getByTestId('lineage-node-src_inventory');
    expect(nodeEl.className).toContain('opacity-30');
  });
});
