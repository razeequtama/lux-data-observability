import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { DownstreamRecoveryBanner } from '../../src/components/recovery/DownstreamRecoveryBanner';

describe('DownstreamRecoveryBanner Component', () => {
  it('renders ALL_ASSETS_HEALTHY state with trust restored messaging and lineage navigation button', () => {
    const handleNavigate = vi.fn();
    render(
      <DownstreamRecoveryBanner
        status="ALL_ASSETS_HEALTHY"
        onNavigateToLineage={handleNavigate}
      />
    );

    expect(screen.getByTestId('downstream-recovery-banner')).toBeInTheDocument();
    expect(
      screen.getByText(/Downstream Trust Restored: All Lineage Assets Healthy/i)
    ).toBeInTheDocument();
    expect(screen.getByText('Recovery Verified')).toBeInTheDocument();
    expect(screen.getByText(/DAG Status: ALL_ASSETS_HEALTHY/i)).toBeInTheDocument();
    expect(
      screen.getByText(/dim_orders/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Executive Monday Dashboard/i)
    ).toBeInTheDocument();

    const btn = screen.getByTestId('banner-navigate-lineage-btn');
    expect(btn).toHaveTextContent(/View Restored Lineage DAG/i);
    fireEvent.click(btn);
    expect(handleNavigate).toHaveBeenCalledTimes(1);
  });

  it('renders PARTIALLY_RECOVERED state with warning indicators', () => {
    const handleNavigate = vi.fn();
    render(
      <DownstreamRecoveryBanner
        status="PARTIALLY_RECOVERED"
        onNavigateToLineage={handleNavigate}
      />
    );

    expect(
      screen.getByText(/Partial Recovery Detected: Unresolved Finding\(s\) Remain/i)
    ).toBeInTheDocument();
    expect(screen.getByText('Partial Recovery')).toBeInTheDocument();
    expect(screen.getByText(/DAG Status: PARTIALLY_RECOVERED/i)).toBeInTheDocument();

    const btn = screen.getByTestId('banner-navigate-lineage-btn');
    expect(btn).toHaveTextContent(/Inspect Lineage Impact/i);
    fireEvent.click(btn);
    expect(handleNavigate).toHaveBeenCalledTimes(1);
  });

  it('renders RECOVERY_FAILED state with corruption indicators', () => {
    render(<DownstreamRecoveryBanner status="RECOVERY_FAILED" />);

    expect(
      screen.getByText(/Recovery Incomplete: Checks Failing on New Fixture/i)
    ).toBeInTheDocument();
    expect(screen.getByText('Recovery Incomplete')).toBeInTheDocument();
    expect(screen.getByText(/DAG Status: RECOVERY_FAILED/i)).toBeInTheDocument();
  });
});

