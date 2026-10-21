import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { DualStatusCallout } from '../../src/components/pipeline/DualStatusCallout';
import { PipelineRun } from '../../src/types';

describe('DualStatusCallout Component', () => {
  const anomalousRun: PipelineRun = {
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
    run_log: [],
  };

  const healthyRun: PipelineRun = {
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
  };

  it('renders visual callout when compute succeeded but quality is corrupted', () => {
    render(<DualStatusCallout run={anomalousRun} />);

    expect(
      screen.getByText('Execution Succeeded (Exit 0) but Data Quality is Corrupted')
    ).toBeInTheDocument();
    expect(
      screen.getByText(/The ETL orchestration job terminated cleanly with exit code 0/i)
    ).toBeInTheDocument();
    expect(screen.getByText('Compute: COMPLETED_SUCCESS (Exit 0)')).toBeInTheDocument();
    expect(screen.getByText('Quality: CORRUPTED')).toBeInTheDocument();
    expect(screen.getByText(/15 Duplicate Orders Ingested/i)).toBeInTheDocument();
    expect(screen.getByText(/24 Orphaned Line Items/i)).toBeInTheDocument();
  });

  it('triggers onTraceImpact when Trace Blast Radius button is clicked', () => {
    const handleTrace = vi.fn();
    render(<DualStatusCallout run={anomalousRun} onTraceImpact={handleTrace} />);

    const traceBtn = screen.getByRole('button', { name: /trace blast radius/i });
    fireEvent.click(traceBtn);
    expect(handleTrace).toHaveBeenCalledTimes(1);
  });

  it('triggers onViewLogs when View Step Logs button is clicked', () => {
    const handleViewLogs = vi.fn();
    render(<DualStatusCallout run={anomalousRun} onViewLogs={handleViewLogs} />);

    const logsBtn = screen.getByRole('button', { name: /view step logs/i });
    fireEvent.click(logsBtn);
    expect(handleViewLogs).toHaveBeenCalledTimes(1);
  });

  it('returns null and renders nothing when data quality is healthy', () => {
    const { container } = render(<DualStatusCallout run={healthyRun} />);
    expect(container.firstChild).toBeNull();
  });

  it('returns null when run is undefined or null', () => {
    const { container } = render(<DualStatusCallout run={null} />);
    expect(container.firstChild).toBeNull();
  });
});
