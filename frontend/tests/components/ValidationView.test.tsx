import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ValidationView } from '../../src/components/validation/ValidationView';
import * as validationsApi from '../../src/api/validations';
import {
  ValidationFindingItem,
  ValidationRunResponse,
} from '../../src/types';

describe('ValidationView Component', () => {
  const mockRun: ValidationRunResponse = {
    run_id: 'val_run_18f6e2b4',
    scenario_id: 'monday_revenue_mystery',
    fixture_version: 'defective',
    status: 'FAILED',
    total_checks: 8,
    passed_checks: 4,
    failed_checks: 4,
    warning_checks: 0,
    skipped_checks: 0,
    error_checks: 0,
    execution_duration_ms: 120,
    executed_at: '2026-10-21T02:00:00Z',
  };

  const mockFindings: ValidationFindingItem[] = [
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
      message: 'Found 15 duplicate order_id records in orders.csv.',
      evidence: {
        sample_duplicates: [
          { order_id: 'ORD-1042', occurrences: 2, row_indices: [42, 108] },
        ],
      },
      execution_duration_ms: 14,
    },
  ];

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders empty state when no runs exist for the scenario', async () => {
    vi.spyOn(validationsApi, 'listValidationRuns').mockResolvedValue([]);

    render(
      <ValidationView
        scenarioId="monday_revenue_mystery"
        availableDatasets={['orders', 'order_items']}
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId('no-runs-empty-state')).toBeInTheDocument();
    });

    expect(
      screen.getByText('No Validation Runs Executed Yet')
    ).toBeInTheDocument();
  });

  it('loads and renders summary cards and findings when a run exists', async () => {
    vi.spyOn(validationsApi, 'listValidationRuns').mockResolvedValue([mockRun]);
    vi.spyOn(validationsApi, 'listValidationFindings').mockResolvedValue({
      run_id: mockRun.run_id,
      total_findings: 1,
      items: mockFindings,
    });

    render(
      <ValidationView
        scenarioId="monday_revenue_mystery"
        availableDatasets={['orders', 'order_items']}
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId('validation-summary-cards')).toBeInTheDocument();
      expect(screen.getByTestId('findings-table')).toBeInTheDocument();
    });

    expect(screen.getByTestId('summary-failed-checks')).toHaveTextContent('4');
    expect(screen.getByTestId('finding-row-VAL-ORD-001')).toBeInTheDocument();
  });

  it('opens evidence drawer when finding row is selected', async () => {
    const user = userEvent.setup();
    vi.spyOn(validationsApi, 'listValidationRuns').mockResolvedValue([mockRun]);
    vi.spyOn(validationsApi, 'listValidationFindings').mockResolvedValue({
      run_id: mockRun.run_id,
      total_findings: 1,
      items: mockFindings,
    });

    render(
      <ValidationView
        scenarioId="monday_revenue_mystery"
        availableDatasets={['orders', 'order_items']}
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId('finding-row-VAL-ORD-001')).toBeInTheDocument();
    });

    const row = screen.getByTestId('finding-row-VAL-ORD-001');
    await user.click(row);

    const drawer = screen.getByTestId('evidence-drawer');
    expect(drawer).toBeInTheDocument();
    expect(within(drawer).getByText('Order ID Uniqueness Check')).toBeInTheDocument();
    expect(within(drawer).getByText('ORD-1042')).toBeInTheDocument();
  });

  it('triggers execution when Execute Quality Validations is clicked', async () => {
    const user = userEvent.setup();
    vi.spyOn(validationsApi, 'listValidationRuns').mockResolvedValue([]);
    const execSpy = vi.spyOn(validationsApi, 'executeValidationRun').mockResolvedValue(mockRun);
    vi.spyOn(validationsApi, 'listValidationFindings').mockResolvedValue({
      run_id: mockRun.run_id,
      total_findings: 1,
      items: mockFindings,
    });

    render(
      <ValidationView
        scenarioId="monday_revenue_mystery"
        availableDatasets={['orders', 'order_items']}
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId('execute-validations-btn')).toBeInTheDocument();
    });

    await user.click(screen.getByTestId('execute-validations-btn'));

    expect(execSpy).toHaveBeenCalledWith('monday_revenue_mystery');
    await waitFor(() => {
      expect(screen.getByTestId('validation-summary-cards')).toBeInTheDocument();
    });
  });

  it('displays error alert when Execute Quality Validations fails', async () => {
    const user = userEvent.setup();
    vi.spyOn(validationsApi, 'listValidationRuns').mockResolvedValue([]);
    vi.spyOn(validationsApi, 'executeValidationRun').mockRejectedValue(
      new Error('Scenario monday_revenue_mystery was not found in the database. Please load the scenario first.')
    );

    render(
      <ValidationView
        scenarioId="monday_revenue_mystery"
        availableDatasets={['orders', 'order_items']}
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId('execute-validations-btn')).toBeInTheDocument();
    });

    await user.click(screen.getByTestId('execute-validations-btn'));

    await waitFor(() => {
      expect(screen.getByText('Validation Error')).toBeInTheDocument();
      expect(
        screen.getByText(/Scenario monday_revenue_mystery was not found in the database/)
      ).toBeInTheDocument();
    });
  });

  it('re-fetches runs when lastReloadKey prop changes', async () => {
    const listSpy = vi.spyOn(validationsApi, 'listValidationRuns').mockResolvedValue([mockRun]);
    vi.spyOn(validationsApi, 'listValidationFindings').mockResolvedValue({
      run_id: mockRun.run_id,
      total_findings: 1,
      items: mockFindings,
    });

    const { rerender } = render(
      <ValidationView
        scenarioId="monday_revenue_mystery"
        lastReloadKey={1}
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId('validation-summary-cards')).toBeInTheDocument();
    });

    expect(listSpy).toHaveBeenCalledTimes(1);

    // Re-render with new lastReloadKey (scenario reloaded)
    listSpy.mockResolvedValueOnce([]);
    rerender(
      <ValidationView
        scenarioId="monday_revenue_mystery"
        lastReloadKey={2}
      />
    );

    await waitFor(() => {
      expect(listSpy).toHaveBeenCalledTimes(2);
      expect(screen.getByTestId('no-runs-empty-state')).toBeInTheDocument();
    });
  });
});
