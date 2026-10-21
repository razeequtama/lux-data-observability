import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { PipelineHistoryTimeline } from '../../src/components/pipeline/PipelineHistoryTimeline';
import { PipelineRun } from '../../src/types';

describe('PipelineHistoryTimeline Component', () => {
  const mockRuns: PipelineRun[] = [
    {
      id: 'pipe_run_20261020_0200',
      scenario_id: 'monday_revenue_mystery',
      pipeline_name: 'nightly_ecommerce_etl',
      execution_status: 'COMPLETED_SUCCESS',
      quality_health: 'CORRUPTED',
      start_time: '2026-10-20T02:00:00Z',
      end_time: '2026-10-20T02:08:14Z',
      duration_ms: 494000,
      records_ingested: 4670,
      records_written: 4655,
      run_log: [
        {
          step: 'extract_sources',
          status: 'SUCCESS',
          records: 4670,
          duration_ms: 120000,
        },
        {
          step: 'transform_clean_orders',
          status: 'SUCCESS',
          records: 1250,
          duration_ms: 102000,
        },
        {
          step: 'transform_order_line_items',
          status: 'SUCCESS',
          records: 3420,
          duration_ms: 147000,
        },
        {
          step: 'aggregate_daily_revenue',
          status: 'SUCCESS',
          records: 1,
          duration_ms: 125000,
        },
      ],
    },
    {
      id: 'pipe_run_20261019_0200',
      scenario_id: 'monday_revenue_mystery',
      pipeline_name: 'nightly_ecommerce_etl',
      execution_status: 'COMPLETED_SUCCESS',
      quality_health: 'HEALTHY',
      start_time: '2026-10-19T02:00:00Z',
      end_time: '2026-10-19T02:08:02Z',
      duration_ms: 482000,
      records_ingested: 4600,
      records_written: 4600,
      run_log: [],
    },
  ];

  it('acceptance criterion: clearly renders the overnight pipeline run with SUCCESS compute badge alongside CORRUPTED data health badge', () => {
    render(<PipelineHistoryTimeline runs={mockRuns} />);

    // Overnight run id
    expect(screen.getByText('pipe_run_20261020_0200')).toBeInTheDocument();

    // Badges for the overnight run
    const computeBadge = screen.getByTestId('badge-compute-pipe_run_20261020_0200');
    expect(computeBadge).toHaveTextContent('COMPLETED_SUCCESS');

    const qualityBadge = screen.getByTestId('badge-quality-pipe_run_20261020_0200');
    expect(qualityBadge).toHaveTextContent('CORRUPTED');
  });

  it('renders summary statistics cards for runs count, compute rate, and data health', () => {
    render(<PipelineHistoryTimeline runs={mockRuns} />);

    expect(screen.getByText('Historical Runs')).toBeInTheDocument();
    expect(screen.getByText('Compute Success')).toBeInTheDocument();
    expect(screen.getByText('100%')).toBeInTheDocument();
    expect(screen.getByText('Healthy Data Runs')).toBeInTheDocument();
    expect(screen.getByText('Corrupted Data Runs')).toBeInTheDocument();
  });

  it('renders step logs with step names, statuses, records, and durations', () => {
    render(<PipelineHistoryTimeline runs={mockRuns} />);

    // First run is expanded by default
    expect(screen.getByText('extract_sources')).toBeInTheDocument();
    expect(screen.getByText('transform_clean_orders')).toBeInTheDocument();
    expect(screen.getByText('transform_order_line_items')).toBeInTheDocument();
    expect(screen.getByText('aggregate_daily_revenue')).toBeInTheDocument();

    expect(screen.getByText('4,670 rows')).toBeInTheDocument();
    expect(screen.getByText('1,250 rows')).toBeInTheDocument();
  });

  it('toggles collapsible step logs when button is clicked', () => {
    render(<PipelineHistoryTimeline runs={mockRuns} />);

    const toggleBtn = screen.getByRole('button', {
      name: /toggle step logs for pipe_run_20261020_0200/i,
    });
    expect(toggleBtn).toHaveTextContent('Hide Steps');

    // Click to collapse
    fireEvent.click(toggleBtn);
    expect(toggleBtn).toHaveTextContent('View Steps');
    expect(screen.queryByText('extract_sources')).not.toBeInTheDocument();

    // Click to expand again
    fireEvent.click(toggleBtn);
    expect(toggleBtn).toHaveTextContent('Hide Steps');
    expect(screen.getByText('extract_sources')).toBeInTheDocument();
  });

  it('renders loading state when isLoading is true', () => {
    render(<PipelineHistoryTimeline runs={[]} isLoading={true} />);
    expect(screen.getByText(/loading historical pipeline executions/i)).toBeInTheDocument();
  });

  it('renders empty state when no runs are present', () => {
    render(<PipelineHistoryTimeline runs={[]} isLoading={false} />);
    expect(screen.getByText(/no pipeline runs found/i)).toBeInTheDocument();
  });
});
