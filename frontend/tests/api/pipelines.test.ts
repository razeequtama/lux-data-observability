import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  listPipelineRuns,
  getPipelineRun,
  getPipelineFreshness,
} from '../../src/api/pipelines';
import { PipelineRun, FreshnessCheck } from '../../src/types';

describe('Pipelines API Client', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it('listPipelineRuns sends GET to /api/v1/pipelines/runs with query parameters', async () => {
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
        run_log: [],
      },
    ];

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: {
        get: (h: string) => (h === 'content-type' ? 'application/json' : null),
      },
      json: async () => mockRuns,
    } as unknown as Response);

    const result = await listPipelineRuns({
      scenarioId: 'monday_revenue_mystery',
      limit: 10,
      offset: 0,
      includeLogs: true,
    });

    expect(result).toEqual(mockRuns);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/pipelines/runs?scenario_id=monday_revenue_mystery&limit=10&offset=0&include_logs=true'),
      expect.objectContaining({ method: 'GET' })
    );
  });

  it('getPipelineRun sends GET to /api/v1/pipelines/runs/{runId}', async () => {
    const mockRun: PipelineRun = {
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
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: {
        get: (h: string) => (h === 'content-type' ? 'application/json' : null),
      },
      json: async () => mockRun,
    } as unknown as Response);

    const result = await getPipelineRun('pipe_run_20261020_0200');
    expect(result).toEqual(mockRun);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/pipelines/runs/pipe_run_20261020_0200'),
      expect.objectContaining({ method: 'GET' })
    );
  });

  it('getPipelineFreshness sends GET to /api/v1/pipelines/freshness with scenario_id', async () => {
    const mockFreshness: FreshnessCheck[] = [
      {
        dataset_id: 'orders',
        dataset_name: 'orders.csv',
        sla_hours: 24,
        expected_partition_timestamp: '2026-10-19T23:59:59Z',
        observed_partition_timestamp: '2026-10-19T18:00:00Z',
        status: 'STALE',
        hours_behind: 5.99,
      },
      {
        dataset_id: 'inventory',
        dataset_name: 'inventory.csv',
        sla_hours: 6,
        expected_partition_timestamp: '2026-10-20T01:00:00Z',
        observed_partition_timestamp: '2026-10-20T01:30:00Z',
        status: 'FRESH',
        hours_behind: 0.0,
      },
    ];

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: {
        get: (h: string) => (h === 'content-type' ? 'application/json' : null),
      },
      json: async () => mockFreshness,
    } as unknown as Response);

    const result = await getPipelineFreshness({
      scenarioId: 'monday_revenue_mystery',
    });

    expect(result).toEqual(mockFreshness);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/pipelines/freshness?scenario_id=monday_revenue_mystery'),
      expect.objectContaining({ method: 'GET' })
    );
  });
});

