import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { FreshnessView } from '../../src/components/pipeline/FreshnessView';
import { FreshnessCheck } from '../../src/types';

describe('FreshnessView Component', () => {
  const mockChecks: FreshnessCheck[] = [
    {
      id: 'fresh_orders_20261020',
      scenario_id: 'monday_revenue_mystery',
      dataset_id: 'orders',
      dataset_name: 'orders.csv',
      sla_hours: 24,
      expected_partition_timestamp: '2026-10-19T23:59:59Z',
      observed_partition_timestamp: '2026-10-19T18:00:00Z',
      status: 'STALE',
      hours_behind: 5.99,
      checked_at: '2026-10-20T02:10:00Z',
    },
    {
      id: 'fresh_inventory_20261020',
      scenario_id: 'monday_revenue_mystery',
      dataset_id: 'inventory',
      dataset_name: 'inventory.csv',
      sla_hours: 6,
      expected_partition_timestamp: '2026-10-20T01:00:00Z',
      observed_partition_timestamp: '2026-10-20T01:30:00Z',
      status: 'FRESH',
      hours_behind: 0.0,
      checked_at: '2026-10-20T02:10:00Z',
    },
  ];

  it('acceptance criterion: freshness panel displays orders.csv partition staleness', () => {
    render(<FreshnessView freshnessChecks={mockChecks} />);

    // orders.csv partition card
    expect(screen.getByText('orders.csv')).toBeInTheDocument();

    const staleBadge = screen.getByTestId('badge-freshness-orders');
    expect(staleBadge).toHaveTextContent('STALE');

    // Breach lag callout
    expect(
      screen.getByText(/SLA Breach: 5.99 hours behind schedule/i)
    ).toBeInTheDocument();
  });

  it('displays configured SLA hours and expected vs observed timestamps', () => {
    render(<FreshnessView freshnessChecks={mockChecks} />);

    // SLA hours display
    expect(screen.getByText('24 hours')).toBeInTheDocument();
    expect(screen.getByText('6 hours')).toBeInTheDocument();

    // Timestamp formatting
    expect(screen.getByText(/2026-10-19 23:59:59 UTC/i)).toBeInTheDocument();
    expect(screen.getAllByText(/2026-10-19 18:00:00 UTC/i).length).toBeGreaterThan(0);
  });

  it('displays compliant status for inventory.csv partition', () => {
    render(<FreshnessView freshnessChecks={mockChecks} />);

    expect(screen.getByText('inventory.csv')).toBeInTheDocument();
    const freshBadge = screen.getByTestId('badge-freshness-inventory');
    expect(freshBadge).toHaveTextContent('FRESH');
  });

  it('renders summary statistics cards for monitored, compliant, and stale partitions', () => {
    render(<FreshnessView freshnessChecks={mockChecks} />);

    expect(screen.getByText('Partitions Monitored')).toBeInTheDocument();
    expect(screen.getByText('SLA Compliant')).toBeInTheDocument();
    expect(screen.getByText('Stale / SLA Breached')).toBeInTheDocument();
    expect(screen.getByText('Max Lag Behind SLA')).toBeInTheDocument();
    expect(screen.getByText('5.99h')).toBeInTheDocument();
  });

  it('calls onRefresh when Refresh Status button is clicked', () => {
    const handleRefresh = vi.fn();
    render(<FreshnessView freshnessChecks={mockChecks} onRefresh={handleRefresh} />);

    const refreshBtn = screen.getByRole('button', { name: /refresh status/i });
    fireEvent.click(refreshBtn);
    expect(handleRefresh).toHaveBeenCalledTimes(1);
  });

  it('renders loading state when isLoading is true', () => {
    render(<FreshnessView freshnessChecks={[]} isLoading={true} />);
    expect(
      screen.getByText(/loading dataset partition freshness checkpoints/i)
    ).toBeInTheDocument();
  });

  it('renders empty state when no freshness checks are present', () => {
    render(<FreshnessView freshnessChecks={[]} isLoading={false} />);
    expect(screen.getByText(/no freshness checks found/i)).toBeInTheDocument();
  });
});
