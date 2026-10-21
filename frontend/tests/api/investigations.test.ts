import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  listInvestigations,
  getInvestigation,
  createInvestigation,
  updateInvestigation,
  deleteInvestigation,
  synthesizeInvestigation,
} from '../../src/api/investigations';
import { InvestigationResponse } from '../../src/types';

describe('Investigations API Client', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  const mockInvestigation: InvestigationResponse = {
    id: 'inv_12345678',
    scenario_id: 'monday_revenue_mystery',
    title: 'Investigation: Monday Morning Revenue Anomaly',
    status: 'INVESTIGATING',
    initial_finding_id: 'val_fnd_001',
    verified_facts: [
      'Overnight ETL pipeline succeeded at 02:08 UTC with exit code 0.',
      '15 duplicate order IDs detected in orders.csv.',
    ],
    hypotheses: [
      'Upstream webhook duplicate delivery during Sunday night retry storm.',
    ],
    action_items: [
      'Deduplicate orders.csv using idempotent order UUID check.',
    ],
    created_at: '2026-10-20T22:30:00Z',
    updated_at: '2026-10-20T22:35:00Z',
  };

  it('listInvestigations sends GET to /api/v1/investigations with query parameters', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: {
        get: (h: string) => (h === 'content-type' ? 'application/json' : null),
      },
      json: async () => [mockInvestigation],
    } as unknown as Response);

    const result = await listInvestigations({
      scenarioId: 'monday_revenue_mystery',
      status: 'INVESTIGATING',
      limit: 20,
    });

    expect(result).toEqual([mockInvestigation]);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/investigations?scenario_id=monday_revenue_mystery&status=INVESTIGATING&limit=20&offset=0'),
      expect.objectContaining({ method: 'GET' })
    );
  });

  it('getInvestigation sends GET to /api/v1/investigations/{id}', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: {
        get: (h: string) => (h === 'content-type' ? 'application/json' : null),
      },
      json: async () => mockInvestigation,
    } as unknown as Response);

    const result = await getInvestigation('inv_12345678');

    expect(result).toEqual(mockInvestigation);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/investigations/inv_12345678'),
      expect.objectContaining({ method: 'GET' })
    );
  });

  it('createInvestigation sends POST to /api/v1/investigations with payload', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: {
        get: (h: string) => (h === 'content-type' ? 'application/json' : null),
      },
      json: async () => mockInvestigation,
    } as unknown as Response);

    const payload = {
      scenario_id: 'monday_revenue_mystery',
      title: 'Investigation: Monday Morning Revenue Anomaly',
      status: 'INVESTIGATING',
      verified_facts: ['Fact 1'],
      hypotheses: ['Hypo 1'],
      action_items: ['Action 1'],
    };

    const result = await createInvestigation(payload);

    expect(result).toEqual(mockInvestigation);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/investigations'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify(payload),
      })
    );
  });

  it('updateInvestigation sends PATCH to /api/v1/investigations/{id}', async () => {
    const updatedMock = { ...mockInvestigation, status: 'RESOLVED' };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: {
        get: (h: string) => (h === 'content-type' ? 'application/json' : null),
      },
      json: async () => updatedMock,
    } as unknown as Response);

    const payload = { status: 'RESOLVED' };
    const result = await updateInvestigation('inv_12345678', payload);

    expect(result).toEqual(updatedMock);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/investigations/inv_12345678'),
      expect.objectContaining({
        method: 'PATCH',
        body: JSON.stringify(payload),
      })
    );
  });

  it('deleteInvestigation sends DELETE to /api/v1/investigations/{id}', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 204,
      headers: {
        get: () => null,
      },
    } as unknown as Response);

    await deleteInvestigation('inv_12345678');

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/investigations/inv_12345678'),
      expect.objectContaining({ method: 'DELETE' })
    );
  });

  it('synthesizeInvestigation sends POST to /api/v1/investigations/synthesize', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: {
        get: (h: string) => (h === 'content-type' ? 'application/json' : null),
      },
      json: async () => mockInvestigation,
    } as unknown as Response);

    const payload = { scenario_id: 'monday_revenue_mystery' };
    const result = await synthesizeInvestigation(payload);

    expect(result).toEqual(mockInvestigation);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/investigations/synthesize'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify(payload),
      })
    );
  });
});

