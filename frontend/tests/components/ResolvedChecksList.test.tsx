import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { ResolvedChecksList } from '../../src/components/recovery/ResolvedChecksList';
import { ResolvedFindingItem } from '../../src/types';

describe('ResolvedChecksList Component', () => {
  const mockItems: ResolvedFindingItem[] = [
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
      message: 'All 3,420 line items reference existing product_id catalog records',
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
      message: 'Freshness verified within 1-hour SLA',
    },
  ];

  it('renders all 4 resolved checks with green checkmarks and status badges', () => {
    render(<ResolvedChecksList items={mockItems} />);

    expect(screen.getByTestId('resolved-checks-list')).toBeInTheDocument();
    expect(screen.getByTestId('resolution-count-badge')).toHaveTextContent('4 of 4 Resolved (100%)');

    // Rule IDs
    expect(screen.getByText('VAL-ORD-001')).toBeInTheDocument();
    expect(screen.getByText('Order ID Uniqueness Check')).toBeInTheDocument();
    expect(screen.getAllByText('orders.csv')[0]).toBeInTheDocument();

    expect(screen.getByText('VAL-ORD-002')).toBeInTheDocument();
    expect(screen.getByText('Order Items Foreign Key Check')).toBeInTheDocument();

    expect(screen.getByText('VAL-INV-001')).toBeInTheDocument();
    expect(screen.getByText('Inventory Non-Negative Check')).toBeInTheDocument();

    expect(screen.getByText('VAL-FRESH-001')).toBeInTheDocument();
    expect(screen.getByText('Partition Freshness Check')).toBeInTheDocument();

    // Check status badges
    expect(screen.getByTestId('status-badge-VAL-ORD-001')).toHaveTextContent('RESOLVED');
    expect(screen.getByTestId('status-badge-VAL-ORD-002')).toHaveTextContent('RESOLVED');
    expect(screen.getByTestId('status-badge-VAL-INV-001')).toHaveTextContent('RESOLVED');
    expect(screen.getByTestId('status-badge-VAL-FRESH-001')).toHaveTextContent('RESOLVED');
  });

  it('filters items by Resolved and Unresolved buttons', () => {
    const itemsWithUnresolved: ResolvedFindingItem[] = [
      ...mockItems,
      {
        rule_id: 'VAL-CUST-001',
        rule_name: 'Customer Email Syntax Check',
        status: 'UNRESOLVED',
        severity: 'LOW',
        dataset_id: 'customers.csv',
        previous_status: 'FAILED',
        current_status: 'FAILED',
        message: 'Invalid email syntax detected',
      },
    ];

    render(<ResolvedChecksList items={itemsWithUnresolved} />);

    expect(screen.getByTestId('resolution-count-badge')).toHaveTextContent('4 of 5 Resolved (80%)');

    // Click Unresolved filter
    fireEvent.click(screen.getByTestId('filter-unresolved-btn'));
    expect(screen.queryByText('VAL-ORD-001')).not.toBeInTheDocument();
    expect(screen.getByText('VAL-CUST-001')).toBeInTheDocument();

    // Click Resolved filter
    fireEvent.click(screen.getByTestId('filter-resolved-btn'));
    expect(screen.getByText('VAL-ORD-001')).toBeInTheDocument();
    expect(screen.queryByText('VAL-CUST-001')).not.toBeInTheDocument();

    // Click All filter
    fireEvent.click(screen.getByTestId('filter-all-btn'));
    expect(screen.getByText('VAL-ORD-001')).toBeInTheDocument();
    expect(screen.getByText('VAL-CUST-001')).toBeInTheDocument();
  });
});

