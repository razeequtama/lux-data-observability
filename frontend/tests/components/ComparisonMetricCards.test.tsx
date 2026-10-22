import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { ComparisonMetricCards } from '../../src/components/recovery/ComparisonMetricCards';
import { RecoveryRunSummary } from '../../src/types';

describe('ComparisonMetricCards Component', () => {
  const previousRun: RecoveryRunSummary = {
    run_id: 'val_run_18f6e2b4',
    fixture_version: 'defective',
    failed_checks: 4,
    quality_health: 'CORRUPTED',
    total_checks: 8,
    passed_checks: 4,
    execution_duration_ms: 28,
    executed_at: '2026-10-21T02:00:00Z',
  };

  const currentRun: RecoveryRunSummary = {
    run_id: 'val_run_29a7f3c5',
    fixture_version: 'corrected',
    failed_checks: 0,
    quality_health: 'HEALTHY',
    total_checks: 8,
    passed_checks: 8,
    execution_duration_ms: 22,
    executed_at: '2026-10-21T02:05:00Z',
  };

  it('renders side-by-side run cards with accurate metrics and status badges', () => {
    render(<ComparisonMetricCards previousRun={previousRun} currentRun={currentRun} />);

    // Before card
    const beforeCard = screen.getByTestId('before-run-card');
    expect(beforeCard).toBeInTheDocument();
    expect(screen.getByTestId('before-health-badge')).toHaveTextContent('CORRUPTED');
    expect(screen.getByTestId('before-failed-count')).toHaveTextContent('4');
    expect(screen.getByText('val_run_18f6e2b4', { exact: false })).toBeInTheDocument();

    // After card
    const afterCard = screen.getByTestId('after-run-card');
    expect(afterCard).toBeInTheDocument();
    expect(screen.getByTestId('after-health-badge')).toHaveTextContent('HEALTHY');
    expect(screen.getByTestId('after-failed-count')).toHaveTextContent('0');
    expect(screen.getByText('val_run_29a7f3c5', { exact: false })).toBeInTheDocument();

    // Resolution delta footer
    expect(screen.getByText(/Resolution Delta:/i)).toBeInTheDocument();
    expect(screen.getByText(/4 check\(s\) resolved/i)).toBeInTheDocument();
    expect(screen.getByText(/4 failed → 0 failed/i)).toBeInTheDocument();
    expect(screen.getByText(/28ms vs 22ms/i)).toBeInTheDocument();
    expect(screen.getByText(/6ms faster/i)).toBeInTheDocument();
  });
});

