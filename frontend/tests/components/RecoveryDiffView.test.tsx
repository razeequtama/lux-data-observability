import { render, screen, fireEvent, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { RecoveryDiffView } from '../../src/components/recovery/RecoveryDiffView';
import * as recoveryApi from '../../src/api/recovery';
import { RecoveryVerifyResponse } from '../../src/types';

describe('RecoveryDiffView Component', () => {
  const mockResponse: RecoveryVerifyResponse = {
    scenario_id: 'monday_revenue_mystery',
    comparison: {
      previous_run: {
        run_id: 'val_run_18f6e2b4',
        fixture_version: 'defective',
        failed_checks: 4,
        quality_health: 'CORRUPTED',
        total_checks: 8,
        passed_checks: 4,
        execution_duration_ms: 28,
        executed_at: '2026-10-21T02:00:00Z',
      },
      current_run: {
        run_id: 'val_run_29a7f3c5',
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
          message: 'Zero duplicate order IDs found across 1,250 records',
        },
        {
          rule_id: 'VAL-ORD-002',
          rule_name: 'Order Items Foreign Key Check',
          status: 'RESOLVED',
          severity: 'HIGH',
          category: 'REFERENTIAL_INTEGRITY',
          dataset_id: 'order_items.csv',
          previous_status: 'FAILED',
          current_status: 'PASSED',
          message: 'All 3,420 items reference valid product IDs',
        },
        {
          rule_id: 'VAL-INV-001',
          rule_name: 'Inventory Non-Negative Check',
          status: 'RESOLVED',
          severity: 'HIGH',
          category: 'VALUE_RANGE',
          dataset_id: 'inventory.csv',
          previous_status: 'FAILED',
          current_status: 'PASSED',
          message: 'Zero negative inventory counts found across 250 SKUs',
        },
        {
          rule_id: 'VAL-FRESH-001',
          rule_name: 'Partition Freshness Check',
          status: 'RESOLVED',
          severity: 'MEDIUM',
          category: 'FRESHNESS',
          dataset_id: 'orders.csv',
          previous_status: 'FAILED',
          current_status: 'PASSED',
          message: 'Partition freshness verified within SLA',
        },
      ],
      downstream_recovery_status: 'ALL_ASSETS_HEALTHY',
    },
  };

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders initial state before verification is triggered', () => {
    render(<RecoveryDiffView scenarioId="monday_revenue_mystery" />);

    expect(screen.getByTestId('recovery-diff-view')).toBeInTheDocument();
    expect(screen.getByTestId('recovery-initial-callout')).toBeInTheDocument();
    expect(screen.getByText('Ready to Verify Scenario Recovery')).toBeInTheDocument();
    expect(screen.getByTestId('verify-recovery-btn')).toBeInTheDocument();
    expect(screen.getByTestId('verify-recovery-cta-btn')).toBeInTheDocument();
  });

  it('acceptance criterion: user can click "Verify Recovery", view before-and-after diff, and observe all findings resolved', async () => {
    vi.spyOn(recoveryApi, 'verifyRecovery').mockResolvedValue(mockResponse);
    const onRecoveryVerified = vi.fn();
    const onNavigateToLineage = vi.fn();
    const onNavigateToValidations = vi.fn();

    render(
      <RecoveryDiffView
        scenarioId="monday_revenue_mystery"
        onRecoveryVerified={onRecoveryVerified}
        onNavigateToLineage={onNavigateToLineage}
        onNavigateToValidations={onNavigateToValidations}
      />
    );

    const verifyBtn = screen.getByTestId('verify-recovery-cta-btn');
    await act(async () => {
      fireEvent.click(verifyBtn);
    });

    expect(recoveryApi.verifyRecovery).toHaveBeenCalledWith('monday_revenue_mystery', 'corrected');
    expect(onRecoveryVerified).toHaveBeenCalledWith(mockResponse.comparison);

    // 1. Downstream trust restored banner
    expect(await screen.findByTestId('downstream-recovery-banner')).toBeInTheDocument();
    expect(
      screen.getByText(/Downstream Trust Restored: All Lineage Assets Healthy/i)
    ).toBeInTheDocument();

    // 2. Before vs After run cards
    expect(screen.getByTestId('before-run-card')).toBeInTheDocument();
    expect(screen.getByTestId('before-failed-count')).toHaveTextContent('4');
    expect(screen.getByTestId('before-health-badge')).toHaveTextContent('CORRUPTED');

    expect(screen.getByTestId('after-run-card')).toBeInTheDocument();
    expect(screen.getByTestId('after-failed-count')).toHaveTextContent('0');
    expect(screen.getByTestId('after-health-badge')).toHaveTextContent('HEALTHY');

    // 3. Resolved checks list with all 4 resolved
    expect(screen.getByTestId('resolved-checks-list')).toBeInTheDocument();
    expect(screen.getByTestId('resolution-count-badge')).toHaveTextContent('4 of 4 Resolved (100%)');

    expect(screen.getByTestId('status-badge-VAL-ORD-001')).toHaveTextContent('RESOLVED');
    expect(screen.getByTestId('status-badge-VAL-ORD-002')).toHaveTextContent('RESOLVED');
    expect(screen.getByTestId('status-badge-VAL-INV-001')).toHaveTextContent('RESOLVED');
    expect(screen.getByTestId('status-badge-VAL-FRESH-001')).toHaveTextContent('RESOLVED');

    // 4. Quick navigation buttons
    const navValBtn = screen.getByTestId('navigate-validations-btn');
    fireEvent.click(navValBtn);
    expect(onNavigateToValidations).toHaveBeenCalledTimes(1);

    const navLineageBtn = screen.getByTestId('navigate-lineage-btn');
    fireEvent.click(navLineageBtn);
    expect(onNavigateToLineage).toHaveBeenCalledTimes(1);
  });

  it('handles re-verification when reverify button is clicked', async () => {
    vi.spyOn(recoveryApi, 'verifyRecovery').mockResolvedValue(mockResponse);

    render(
      <RecoveryDiffView
        scenarioId="monday_revenue_mystery"
        initialComparison={mockResponse.comparison}
      />
    );

    expect(screen.getByTestId('reverify-recovery-btn')).toBeInTheDocument();

    await act(async () => {
      fireEvent.click(screen.getByTestId('reverify-recovery-btn'));
    });

    expect(recoveryApi.verifyRecovery).toHaveBeenCalledTimes(1);
  });

  it('displays error banner when verification request fails', async () => {
    vi.spyOn(recoveryApi, 'verifyRecovery').mockRejectedValue(
      new Error('Scenario not found or database error')
    );

    render(<RecoveryDiffView scenarioId="unknown_scenario" />);

    const verifyBtn = screen.getByTestId('verify-recovery-btn');
    await act(async () => {
      fireEvent.click(verifyBtn);
    });

    expect(await screen.findByTestId('recovery-error-alert')).toBeInTheDocument();
    expect(
      screen.getByText(/Scenario not found or database error/i)
    ).toBeInTheDocument();
  });
});

