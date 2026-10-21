import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { PipelineObservabilityView } from '../../src/components/pipeline/PipelineObservabilityView';
import * as api from '../../src/api';
import { PipelineRun, FreshnessCheck } from '../../src/types';

vi.mock('../../src/api', () => ({
  listPipelineRuns: vi.fn(),
  getPipelineFreshness: vi.fn(),
}));

describe('PipelineObservabilityView Component', () => {
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
      ],
    },
  ];

  const mockFreshness: FreshnessCheck[] = [
    {
      id: 'fresh_orders_20261020',
      scenario_id: 'monday_revenue_mystery',
      dataset_id: 'orders',
      dataset_name: 'orders.csv',
      sla_hours: 24,
      expected_partition_timestamp: '2026-10-19T23:59:59Z',
      observed_partition_timestamp: '2026-10-19T18:00:00Z',
      status: 'STALE',
      hours_behind: 5.99,
      checked_at: '2026-10-20T02:10:00Z',
    },
  ];

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('loads and displays pipeline run history, dual-status anomaly, and partition freshness', async () => {
    vi.mocked(api.listPipelineRuns).mockResolvedValue(mockRuns);
    vi.mocked(api.getPipelineFreshness).mockResolvedValue(mockFreshness);

    render(<PipelineObservabilityView scenarioId="monday_revenue_mystery" />);

    // Wait for data to load
    await waitFor(() => {
      expect(
        screen.getByText('Execution Succeeded (Exit 0) but Data Quality is Corrupted')
      ).toBeInTheDocument();
    });

    // Run item rendered
    expect(screen.getByTestId('pipeline-run-item-pipe_run_20261020_0200')).toBeInTheDocument();

    // Freshness card rendered
    expect(screen.getByText('orders.csv')).toBeInTheDocument();
    expect(screen.getByText(/5.99 hours behind schedule/i)).toBeInTheDocument();
  });

  it('switches sub-tabs between All Observability, Run History, and Partition Freshness', async () => {
    vi.mocked(api.listPipelineRuns).mockResolvedValue(mockRuns);
    vi.mocked(api.getPipelineFreshness).mockResolvedValue(mockFreshness);

    render(<PipelineObservabilityView scenarioId="monday_revenue_mystery" />);

    await waitFor(() => {
      expect(screen.getByTestId('pipeline-run-item-pipe_run_20261020_0200')).toBeInTheDocument();
    });

    // Switch to Run History only
    const historyTab = screen.getByRole('button', { name: /run history/i });
    fireEvent.click(historyTab);

    expect(screen.getByTestId('pipeline-run-item-pipe_run_20261020_0200')).toBeInTheDocument();
    expect(screen.queryByTestId('freshness-view')).not.toBeInTheDocument();

    // Switch to Partition Freshness only
    const freshnessTab = screen.getByRole('button', { name: /partition freshness/i });
    fireEvent.click(freshnessTab);

    expect(screen.getByText('orders.csv')).toBeInTheDocument();
    expect(screen.queryByTestId('pipeline-history-timeline')).not.toBeInTheDocument();
  });

  it('refetches data when Refresh button is clicked', async () => {
    vi.mocked(api.listPipelineRuns).mockResolvedValue(mockRuns);
    vi.mocked(api.getPipelineFreshness).mockResolvedValue(mockFreshness);

    render(<PipelineObservabilityView scenarioId="monday_revenue_mystery" />);

    await waitFor(() => {
      expect(screen.getByTestId('pipeline-run-item-pipe_run_20261020_0200')).toBeInTheDocument();
    });

    const refreshBtn = screen.getByRole('button', { name: /^refresh$/i });
    await act(async () => {
      fireEvent.click(refreshBtn);
    });

    await waitFor(() => {
      expect(api.listPipelineRuns).toHaveBeenCalledTimes(2);
      expect(api.getPipelineFreshness).toHaveBeenCalledTimes(2);
    });
  });

  it('displays error message when API fails', async () => {
    vi.mocked(api.listPipelineRuns).mockRejectedValue(new Error('Backend service unavailable'));
    vi.mocked(api.getPipelineFreshness).mockRejectedValue(new Error('Backend service unavailable'));

    render(<PipelineObservabilityView scenarioId="monday_revenue_mystery" />);

    await waitFor(() => {
      expect(screen.getByText('Observability Sync Failed')).toBeInTheDocument();
      expect(screen.getByText('Backend service unavailable')).toBeInTheDocument();
    });
  });
});
