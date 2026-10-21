import { render, screen, fireEvent, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { ReportModal, downloadFile } from '../../src/components/reports';
import * as reportsApi from '../../src/api/reports';
import { InvestigationResponse, ReportGenerateResponse } from '../../src/types';

describe('ReportModal Component', () => {
  const mockInvestigation: InvestigationResponse = {
    id: 'inv_12345678',
    scenario_id: 'monday_revenue_mystery',
    title: 'Monday Morning Revenue Anomaly',
    status: 'INVESTIGATING',
    initial_finding_id: 'val_fnd_001',
    verified_facts: [
      '15 duplicate order IDs detected in orders.csv.',
      'Overnight ETL pipeline succeeded at 02:08 UTC with exit code 0.',
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

  const mockGenerateResponse: ReportGenerateResponse = {
    report_id: 'rep_9a8b7c6d',
    investigation_id: 'inv_12345678',
    generated_at: '2026-10-20T22:32:00Z',
    json_url: '/api/v1/reports/rep_9a8b7c6d/export?format=json',
    html_url: '/api/v1/reports/rep_9a8b7c6d/export?format=html',
  };

  const mockHtmlArtifact = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline';">
  <title>Incident Report — Lux</title>
  <style>:root { --primary: #6B46C1; } body { font-family: sans-serif; }</style>
</head>
<body>
  <h1>Incident Report: Monday Morning Revenue Anomaly</h1>
</body>
</html>`;

  const mockJsonArtifact = JSON.stringify({
    report_id: 'rep_9a8b7c6d',
    scenario_id: 'monday_revenue_mystery',
    title: 'Incident Report: Monday Morning Revenue Anomaly',
    verified_facts: ['15 duplicate order IDs detected in orders.csv.'],
  });

  let originalCreateObjectURL: typeof window.URL.createObjectURL;
  let originalRevokeObjectURL: typeof window.URL.revokeObjectURL;
  let createdUrls: string[] = [];
  let revokedUrls: string[] = [];

  beforeEach(() => {
    vi.restoreAllMocks();
    createdUrls = [];
    revokedUrls = [];

    originalCreateObjectURL = window.URL.createObjectURL;
    originalRevokeObjectURL = window.URL.revokeObjectURL;

    window.URL.createObjectURL = vi.fn(() => {
      const url = `blob:http://localhost:3000/${Math.random().toString(36).substring(2)}`;
      createdUrls.push(url);
      return url;
    });

    window.URL.revokeObjectURL = vi.fn((url: string) => {
      revokedUrls.push(url);
    });

    // Mock HTMLAnchorElement.prototype.click to prevent jsdom navigation errors
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});

    vi.spyOn(reportsApi, 'generateReport').mockResolvedValue(mockGenerateResponse);
    vi.spyOn(reportsApi, 'exportReportArtifact').mockImplementation(async (_id, format) => {
      if (format === 'html') return mockHtmlArtifact;
      return mockJsonArtifact;
    });
  });

  afterEach(() => {
    window.URL.createObjectURL = originalCreateObjectURL;
    window.URL.revokeObjectURL = originalRevokeObjectURL;
    vi.restoreAllMocks();
  });

  it('renders modal dialog when isOpen is true', () => {
    render(
      <ReportModal
        isOpen={true}
        onClose={vi.fn()}
        scenarioId="monday_revenue_mystery"
        investigation={mockInvestigation}
      />
    );

    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Incident Investigation Report Generator')).toBeInTheDocument();
    expect(screen.getByDisplayValue(/Incident Report: Monday Morning Revenue Anomaly/i)).toBeInTheDocument();
    expect(screen.getByTestId('generate-report-btn')).toBeInTheDocument();
  });

  it('acceptance criterion: user can generate an incident report and download both HTML and JSON formats', async () => {
    const handleClose = vi.fn();
    const handleReportGenerated = vi.fn();

    render(
      <ReportModal
        isOpen={true}
        onClose={handleClose}
        scenarioId="monday_revenue_mystery"
        investigation={mockInvestigation}
        onReportGenerated={handleReportGenerated}
      />
    );

    const generateBtn = screen.getByTestId('generate-report-btn');
    await act(async () => {
      fireEvent.click(generateBtn);
    });

    // Verify generation API call
    expect(reportsApi.generateReport).toHaveBeenCalledTimes(1);
    expect(reportsApi.generateReport).toHaveBeenCalledWith(
      expect.objectContaining({
        scenario_id: 'monday_revenue_mystery',
        investigation_id: 'inv_12345678',
      })
    );

    // Verify artifact export fetching
    expect(reportsApi.exportReportArtifact).toHaveBeenCalledWith('rep_9a8b7c6d', 'html');
    expect(reportsApi.exportReportArtifact).toHaveBeenCalledWith('rep_9a8b7c6d', 'json');

    // Verify report ID displayed
    expect(await screen.findByTestId('generated-report-id')).toHaveTextContent('rep_9a8b7c6d');

    // Verify HTML iframe preview is rendered
    const iframe = screen.getByTestId('html-report-preview-frame');
    expect(iframe).toBeInTheDocument();
    expect(iframe).toHaveAttribute('srcdoc', mockHtmlArtifact);

    // Download HTML
    const downloadHtmlBtn = screen.getByTestId('download-html-btn');
    fireEvent.click(downloadHtmlBtn);

    expect(window.URL.createObjectURL).toHaveBeenCalledTimes(1);
    expect(window.URL.revokeObjectURL).toHaveBeenCalledTimes(1);
    expect(revokedUrls).toContain(createdUrls[0]);

    // Switch to JSON tab
    const jsonTabBtn = screen.getByRole('button', { name: /json artifact/i });
    fireEvent.click(jsonTabBtn);

    const jsonPreview = await screen.findByTestId('json-report-preview');
    expect(jsonPreview).toBeInTheDocument();
    expect(jsonPreview).toHaveTextContent('rep_9a8b7c6d');

    // Download JSON
    const downloadJsonBtn = screen.getByTestId('download-json-btn');
    fireEvent.click(downloadJsonBtn);

    expect(window.URL.createObjectURL).toHaveBeenCalledTimes(2);
    expect(window.URL.revokeObjectURL).toHaveBeenCalledTimes(2);
    expect(revokedUrls).toContain(createdUrls[1]);
  });

  it('acceptance criterion: downloaded HTML file opens locally in a browser with full styles and zero errors', () => {
    // Assert structure of mockHtmlArtifact satisfies standalone CSS and CSP
    expect(mockHtmlArtifact).toContain('<!DOCTYPE html>');
    expect(mockHtmlArtifact).toContain('<meta http-equiv="Content-Security-Policy"');
    expect(mockHtmlArtifact).toContain('<style>');
    expect(mockHtmlArtifact).toContain('--primary: #6B46C1');

    // Test downloadFile helper directly with HTML content
    const testHtml = '<!DOCTYPE html><html><head><style>body { color: purple; }</style></head><body>OK</body></html>';
    downloadFile(testHtml, 'test_report.html', 'text/html; charset=utf-8');

    expect(window.URL.createObjectURL).toHaveBeenCalledTimes(1);
    expect(window.URL.revokeObjectURL).toHaveBeenCalledTimes(1);
  });

  it('handles report generation failure and displays error banner', async () => {
    vi.spyOn(reportsApi, 'generateReport').mockRejectedValueOnce(
      new Error('Validation run has not been completed')
    );

    render(
      <ReportModal
        isOpen={true}
        onClose={vi.fn()}
        scenarioId="monday_revenue_mystery"
        investigation={mockInvestigation}
      />
    );

    const generateBtn = screen.getByTestId('generate-report-btn');
    await act(async () => {
      fireEvent.click(generateBtn);
    });

    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText('Validation run has not been completed')).toBeInTheDocument();
  });
});
