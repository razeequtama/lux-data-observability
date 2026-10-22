import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { verifyRecovery } from '../../src/api/recovery';
import { RecoveryVerifyResponse } from '../../src/types';

describe('Recovery API Client', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it('verifyRecovery sends POST to /api/v1/recovery/verify with correct payload', async () => {
    const mockResponse: RecoveryVerifyResponse = {
      scenario_id: 'monday_revenue_mystery',
      comparison: {
        previous_run: {
          run_id: 'val_run_defective',
          fixture_version: 'defective',
          failed_checks: 4,
          quality_health: 'CORRUPTED',
          total_checks: 8,
          passed_checks: 4,
          execution_duration_ms: 25,
          executed_at: '2026-10-21T02:00:00Z',
        },
        current_run: {
          run_id: 'val_run_corrected',
          fixture_version: 'corrected',
          failed_checks: 0,
          quality_health: 'HEALTHY',
          total_checks: 8,
          passed_checks: 8,
          execution_duration_ms: 20,
          executed_at: '2026-10-21T02:05:00Z',
        },
        resolved_findings: [
          {
            rule_id: 'VAL-ORD-001',
            rule_name: 'Order ID Uniqueness Check',
            status: 'RESOLVED',
            severity: 'CRITICAL',
            category: 'UNIQUENESS',
            dataset_id: 'orders.csv',
            previous_status: 'FAILED',
            current_status: 'PASSED',
            message: 'All 1,250 order IDs unique',
          },
        ],
        downstream_recovery_status: 'ALL_ASSETS_HEALTHY',
      },
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: {
        get: (h: string) => (h === 'content-type' ? 'application/json' : null),
      },
      json: async () => mockResponse,
    } as unknown as Response);

    const result = await verifyRecovery('monday_revenue_mystery');
    expect(result).toEqual(mockResponse);

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/recovery/verify'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          scenario_id: 'monday_revenue_mystery',
          target_fixture_version: 'corrected',
        }),
      })
    );
  });

  it('verifyRecovery accepts custom targetFixtureVersion', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: {
        get: (h: string) => (h === 'content-type' ? 'application/json' : null),
      },
      json: async () => ({ scenario_id: 'test', comparison: {} }),
    } as unknown as Response);

    await verifyRecovery('custom_scenario', 'custom_version');

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/recovery/verify'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          scenario_id: 'custom_scenario',
          target_fixture_version: 'custom_version',
        }),
      })
    );
  });
});

