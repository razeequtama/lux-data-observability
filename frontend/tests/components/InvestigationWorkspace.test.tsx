import { render, screen, fireEvent, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { InvestigationWorkspace } from '../../src/components/reports/InvestigationWorkspace';
import * as investigationsApi from '../../src/api/investigations';
import { InvestigationResponse } from '../../src/types';

describe('InvestigationWorkspace Component', () => {
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
      'Backfill missing products.csv catalog rows.',
    ],
    created_at: '2026-10-20T22:30:00Z',
    updated_at: '2026-10-20T22:35:00Z',
  };

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders empty state when no investigation exists and allows synthesis', async () => {
    vi.spyOn(investigationsApi, 'listInvestigations').mockResolvedValue([]);
    vi.spyOn(investigationsApi, 'synthesizeInvestigation').mockResolvedValue(mockInvestigation);

    render(<InvestigationWorkspace scenarioId="monday_revenue_mystery" />);

    expect(await screen.findByText('No Active Investigation Found')).toBeInTheDocument();

    const synthesizeBtn = screen.getByTestId('synthesize-initial-btn');
    await act(async () => {
      fireEvent.click(synthesizeBtn);
    });

    expect(investigationsApi.synthesizeInvestigation).toHaveBeenCalledTimes(1);
    expect(await screen.findByDisplayValue('Investigation: Monday Morning Revenue Anomaly')).toBeInTheDocument();
  });

  it('renders active investigation with boundary separation between facts, hypotheses, and action items', async () => {
    vi.spyOn(investigationsApi, 'listInvestigations').mockResolvedValue([mockInvestigation]);

    render(<InvestigationWorkspace scenarioId="monday_revenue_mystery" />);

    // Header & status badge
    expect(await screen.findByTestId('investigation-status-badge')).toHaveTextContent('INVESTIGATING');
    expect(screen.getByDisplayValue('Investigation: Monday Morning Revenue Anomaly')).toBeInTheDocument();

    // 1. Confirmed Observations (Facts)
    expect(screen.getByRole('region', { name: /confirmed observations/i })).toBeInTheDocument();
    expect(screen.getByText('15 duplicate order IDs detected in orders.csv.')).toBeInTheDocument();

    // 2. Working Hypotheses
    expect(screen.getByRole('region', { name: /working hypotheses/i })).toBeInTheDocument();
    expect(screen.getByText(/upstream webhook duplicate delivery/i)).toBeInTheDocument();

    // 3. Remediation Checklist
    expect(screen.getByRole('region', { name: /remediation action items/i })).toBeInTheDocument();
    expect(screen.getByText(/deduplicate orders\.csv using idempotent order UUID check/i)).toBeInTheDocument();
  });

  it('supports adding and removing facts, hypotheses, and action items', async () => {
    vi.spyOn(investigationsApi, 'listInvestigations').mockResolvedValue([mockInvestigation]);

    render(<InvestigationWorkspace scenarioId="monday_revenue_mystery" />);

    await screen.findByDisplayValue('Investigation: Monday Morning Revenue Anomaly');

    // Add hypothesis
    const hypoInput = screen.getByPlaceholderText('Add hypothesis theory...');
    fireEvent.change(hypoInput, { target: { value: 'Third-party API rate limited orders sync' } });
    fireEvent.submit(hypoInput.closest('form')!);

    expect(screen.getByText('Third-party API rate limited orders sync')).toBeInTheDocument();

    // Toggle action item
    const actionToggle = screen.getByLabelText('Toggle action 1');
    fireEvent.click(actionToggle);

    // Verify strike-through or updated state
    const actionText = screen.getByText(/deduplicate orders\.csv using idempotent order UUID check/i);
    expect(actionText).toHaveClass('line-through');

    // Remove hypothesis
    const removeHypoBtn = screen.getByLabelText('Remove hypothesis 1');
    fireEvent.click(removeHypoBtn);

    expect(screen.queryByText(/upstream webhook duplicate delivery/i)).not.toBeInTheDocument();
  });

  it('saves changes and updates investigation workspace', async () => {
    vi.spyOn(investigationsApi, 'listInvestigations').mockResolvedValue([mockInvestigation]);
    vi.spyOn(investigationsApi, 'updateInvestigation').mockResolvedValue({
      ...mockInvestigation,
      title: 'Updated Incident Title',
      status: 'RESOLVED',
    });

    render(<InvestigationWorkspace scenarioId="monday_revenue_mystery" />);

    await screen.findByDisplayValue('Investigation: Monday Morning Revenue Anomaly');

    const titleInput = screen.getByLabelText('Investigation Title');
    fireEvent.change(titleInput, { target: { value: 'Updated Incident Title' } });

    const statusSelect = screen.getByLabelText('Status');
    fireEvent.change(statusSelect, { target: { value: 'RESOLVED' } });

    const saveBtn = screen.getByTestId('save-investigation-btn');
    await act(async () => {
      fireEvent.click(saveBtn);
    });

    expect(investigationsApi.updateInvestigation).toHaveBeenCalledTimes(1);
    expect(investigationsApi.updateInvestigation).toHaveBeenCalledWith(
      'inv_12345678',
      expect.objectContaining({
        title: 'Updated Incident Title',
        status: 'RESOLVED',
      })
    );
  });

  it('opens ReportModal when Generate Report is clicked', async () => {
    vi.spyOn(investigationsApi, 'listInvestigations').mockResolvedValue([mockInvestigation]);

    render(<InvestigationWorkspace scenarioId="monday_revenue_mystery" />);

    await screen.findByDisplayValue('Investigation: Monday Morning Revenue Anomaly');

    const openReportBtn = screen.getByTestId('open-report-modal-btn');
    fireEvent.click(openReportBtn);

    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Incident Investigation Report Generator')).toBeInTheDocument();
  });

  it('calls navigation callbacks when cross-workspace links are clicked', async () => {
    vi.spyOn(investigationsApi, 'listInvestigations').mockResolvedValue([mockInvestigation]);
    const mockNavigateToLineage = vi.fn();
    const mockNavigateToValidations = vi.fn();

    render(
      <InvestigationWorkspace
        scenarioId="monday_revenue_mystery"
        onNavigateToLineage={mockNavigateToLineage}
        onNavigateToValidations={mockNavigateToValidations}
      />
    );

    await screen.findByDisplayValue('Investigation: Monday Morning Revenue Anomaly');

    const lineageLink = screen.getByRole('button', { name: /inspect lineage dag/i });
    fireEvent.click(lineageLink);
    expect(mockNavigateToLineage).toHaveBeenCalledTimes(1);

    const validationsLink = screen.getByRole('button', { name: /inspect quality findings/i });
    fireEvent.click(validationsLink);
    expect(mockNavigateToValidations).toHaveBeenCalledTimes(1);
  });
});
