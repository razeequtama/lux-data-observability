import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  executeValidationRun,
  getValidationRun,
  listValidationRuns,
  listValidationFindings,
} from '../../src/api/validations';
import { ValidationRunResponse, ValidationFindingsListResponse } from '../../src/types';

describe('Validations API Client', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it('executeValidationRun sends POST to /api/v1/validations/run', async () => {
    const mockRun: ValidationRunResponse = {
      run_id: 'val_run_123',
      scenario_id: 'monday_revenue_mystery',
      fixture_version: 'defective',
      status: 'FAILED',
      total_checks: 8,
      passed_checks: 4,
      failed_checks: 4,
      warning_checks: 0,
      skipped_checks: 0,
      error_checks: 0,
      execution_duration_ms: 45,
      executed_at: '2026-10-21T00:00:00Z',
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: {
        get: (h: string) => (h === 'content-type' ? 'application/json' : null),
      },
      json: async () => mockRun,
    } as unknown as Response);

    const result = await executeValidationRun('monday_revenue_mystery', ['orders']);
    expect(result).toEqual(mockRun);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/validations/run'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          scenario_id: 'monday_revenue_mystery',
          dataset_ids: ['orders'],
        }),
      })
    );
  });

  it('getValidationRun sends GET to /api/v1/validations/runs/{runId}', async () => {
    const mockRun: ValidationRunResponse = {
      run_id: 'val_run_456',
      scenario_id: 'monday_revenue_mystery',
      fixture_version: 'defective',
      status: 'FAILED',
      total_checks: 8,
      passed_checks: 4,
      failed_checks: 4,
      warning_checks: 0,
      skipped_checks: 0,
      error_checks: 0,
      execution_duration_ms: 30,
      executed_at: '2026-10-21T00:00:00Z',
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: {
        get: (h: string) => (h === 'content-type' ? 'application/json' : null),
      },
      json: async () => mockRun,
    } as unknown as Response);

    const result = await getValidationRun('val_run_456');
    expect(result).toEqual(mockRun);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/validations/runs/val_run_456'),
      expect.objectContaining({ method: 'GET' })
    );
  });

  it('listValidationRuns sends GET to /api/v1/validations/runs with query params', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: {
        get: (h: string) => (h === 'content-type' ? 'application/json' : null),
      },
      json: async () => [],
    } as unknown as Response);

    await listValidationRuns('monday_revenue_mystery', 10, 5);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringMatching(/\/api\/v1\/validations\/runs\?scenario_id=monday_revenue_mystery&limit=10&offset=5/),
      expect.objectContaining({ method: 'GET' })
    );
  });

  it('listValidationFindings sends GET with filtered severity, status, and dataset', async () => {
    const mockFindings: ValidationFindingsListResponse = {
      run_id: 'val_run_123',
      total_findings: 1,
      items: [
        {
          id: 'f1',
          rule_id: 'VAL-ORD-001',
          rule_name: 'Order ID Uniqueness Check',
          rule_category: 'UNIQUENESS',
          severity: 'CRITICAL',
          status: 'FAILED',
          dataset_id: 'orders',
          affected_fields: ['order_id'],
          affected_record_count: 15,
          total_record_count: 1250,
          message: 'Found 15 duplicate orders',
          evidence: {},
          execution_duration_ms: 12,
        },
      ],
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: {
        get: (h: string) => (h === 'content-type' ? 'application/json' : null),
      },
      json: async () => mockFindings,
    } as unknown as Response);

    const result = await listValidationFindings('val_run_123', {
      severity: 'CRITICAL',
      status: 'FAILED',
      datasetId: 'orders',
      limit: 50,
    });

    expect(result.items.length).toBe(1);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringMatching(
        /\/api\/v1\/validations\/runs\/val_run_123\/findings\?severity=CRITICAL&status=FAILED&dataset_id=orders&limit=50&offset=0/
      ),
      expect.objectContaining({ method: 'GET' })
    );
  });
});

