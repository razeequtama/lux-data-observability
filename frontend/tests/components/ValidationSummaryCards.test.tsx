import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ValidationSummaryCards } from '../../src/components/validation/ValidationSummaryCards';
import { ValidationRunResponse } from '../../src/types';

describe('ValidationSummaryCards Component', () => {
  const mockRun: ValidationRunResponse = {
    run_id: 'val_run_18f6e2b4',
    scenario_id: 'monday_revenue_mystery',
    fixture_version: 'defective',
    status: 'FAILED',
    total_checks: 12,
    passed_checks: 8,
    failed_checks: 4,
    warning_checks: 1,
    skipped_checks: 0,
    error_checks: 0,
    execution_duration_ms: 142,
    executed_at: '2026-10-21T02:00:00Z',
  };

  it('renders all 5 metric cards with formatted counts', () => {
    render(<ValidationSummaryCards run={mockRun} />);

    expect(screen.getByTestId('validation-summary-cards')).toBeInTheDocument();
    expect(screen.getByTestId('summary-total-checks')).toHaveTextContent('12');
    expect(screen.getByTestId('summary-passed-checks')).toHaveTextContent('8');
    expect(screen.getByTestId('summary-failed-checks')).toHaveTextContent('4');
    expect(screen.getByTestId('summary-warning-checks')).toHaveTextContent('1');
    expect(screen.getByTestId('summary-duration')).toHaveTextContent('142');
  });

  it('renders run metadata including run ID, fixture version, and status', () => {
    render(<ValidationSummaryCards run={mockRun} />);

    expect(screen.getByText('val_run_18f6e2b4')).toBeInTheDocument();
    expect(screen.getByText('defective')).toBeInTheDocument();
    expect(screen.getByText('FAILED')).toBeInTheDocument();
  });

  it('handles null run gracefully with fallback metrics', () => {
    render(<ValidationSummaryCards run={null} />);

    expect(screen.getByTestId('summary-total-checks')).toHaveTextContent('0');
    expect(screen.getByTestId('summary-passed-checks')).toHaveTextContent('0');
    expect(screen.getByTestId('summary-failed-checks')).toHaveTextContent('0');
    expect(screen.getByTestId('summary-warning-checks')).toHaveTextContent('0');
    expect(screen.getByTestId('summary-duration')).toHaveTextContent('0');
  });

  it('displays loading state indicator when isLoading is true', () => {
    render(<ValidationSummaryCards run={mockRun} isLoading={true} />);

    expect(screen.getByTestId('summary-total-checks')).toHaveTextContent('...');
    expect(screen.getByTestId('summary-passed-checks')).toHaveTextContent('...');
    expect(screen.getByTestId('summary-failed-checks')).toHaveTextContent('...');
  });
});
