import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  generateReport,
  exportReportArtifact,
  getReportArtifacts,
  listReportArtifacts,
} from '../../src/api/reports';
import { ReportArtifactResponse, ReportGenerateResponse } from '../../src/types';

describe('Reports API Client', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  const mockGenerateResponse: ReportGenerateResponse = {
    report_id: 'rep_9a8b7c6d',
    investigation_id: 'inv_12345678',
    generated_at: '2026-10-20T22:32:00Z',
    json_url: '/api/v1/reports/rep_9a8b7c6d/export?format=json',
    html_url: '/api/v1/reports/rep_9a8b7c6d/export?format=html',
  };

  const mockArtifacts: ReportArtifactResponse[] = [
    {
      id: 'rep_9a8b7c6d_html',
      investigation_id: 'inv_12345678',
      scenario_id: 'monday_revenue_mystery',
      validation_run_id: 'val_run_18f6e2b4',
      format: 'html',
      file_path: 'data/reports/rep_9a8b7c6d.html',
      sha256_hash: 'abc123hash',
      file_size_bytes: 45210,
      generated_at: '2026-10-20T22:32:00Z',
    },
    {
      id: 'rep_9a8b7c6d_json',
      investigation_id: 'inv_12345678',
      scenario_id: 'monday_revenue_mystery',
      validation_run_id: 'val_run_18f6e2b4',
      format: 'json',
      file_path: 'data/reports/rep_9a8b7c6d.json',
      sha256_hash: 'def456hash',
      file_size_bytes: 12400,
      generated_at: '2026-10-20T22:32:00Z',
    },
  ];

  it('generateReport sends POST to /api/v1/reports/generate with payload', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: {
        get: (h: string) => (h === 'content-type' ? 'application/json' : null),
      },
      json: async () => mockGenerateResponse,
    } as unknown as Response);

    const payload = {
      scenario_id: 'monday_revenue_mystery',
      title: 'Incident Report: Monday Morning Revenue Anomaly',
      verified_facts: ['Fact 1'],
      hypotheses: ['Hypo 1'],
      action_items: ['Action 1'],
    };

    const result = await generateReport(payload);

    expect(result).toEqual(mockGenerateResponse);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/reports/generate'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify(payload),
      })
    );
  });

  it('exportReportArtifact sends GET to /api/v1/reports/{id}/export?format={format} and returns text', async () => {
    const mockHtml = '<!DOCTYPE html><html><body>Report</body></html>';
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      text: async () => mockHtml,
    } as unknown as Response);

    const result = await exportReportArtifact('rep_9a8b7c6d', 'html');

    expect(result).toBe(mockHtml);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/reports/rep_9a8b7c6d/export?format=html'),
      expect.objectContaining({ method: 'GET' })
    );
  });

  it('getReportArtifacts sends GET to /api/v1/reports/{id}', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: {
        get: (h: string) => (h === 'content-type' ? 'application/json' : null),
      },
      json: async () => mockArtifacts,
    } as unknown as Response);

    const result = await getReportArtifacts('rep_9a8b7c6d');

    expect(result).toEqual(mockArtifacts);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/reports/rep_9a8b7c6d'),
      expect.objectContaining({ method: 'GET' })
    );
  });

  it('listReportArtifacts sends GET to /api/v1/reports with query parameters', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: {
        get: (h: string) => (h === 'content-type' ? 'application/json' : null),
      },
      json: async () => mockArtifacts,
    } as unknown as Response);

    const result = await listReportArtifacts({
      scenarioId: 'monday_revenue_mystery',
      investigationId: 'inv_12345678',
    });

    expect(result).toEqual(mockArtifacts);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/reports?scenario_id=monday_revenue_mystery&investigation_id=inv_12345678&limit=50&offset=0'),
      expect.objectContaining({ method: 'GET' })
    );
  });
});

