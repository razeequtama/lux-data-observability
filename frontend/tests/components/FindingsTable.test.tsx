import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FindingsTable } from '../../src/components/validation/FindingsTable';
import { ValidationFindingItem } from '../../src/types';

describe('FindingsTable Component', () => {
  const mockFindings: ValidationFindingItem[] = [
    {
      id: 'finding_001',
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
    {
      id: 'finding_002',
      rule_id: 'VAL-ORD-002',
      rule_name: 'Order Items Foreign Key Integrity',
      rule_category: 'REFERENTIAL_INTEGRITY',
      severity: 'HIGH',
      status: 'FAILED',
      dataset_id: 'order_items',
      affected_fields: ['product_id'],
      affected_record_count: 24,
      total_record_count: 3420,
      message: 'Found 24 order_items with invalid product_id.',
      evidence: {
        sample_orphaned_keys: ['PRD-9001'],
      },
      execution_duration_ms: 22,
    },
    {
      id: 'finding_003',
      rule_id: 'VAL-INV-001',
      rule_name: 'Inventory Quantity Range Check',
      rule_category: 'VALUE_RANGE',
      severity: 'HIGH',
      status: 'FAILED',
      dataset_id: 'inventory',
      affected_fields: ['quantity_on_hand'],
      affected_record_count: 8,
      total_record_count: 250,
      message: 'Found 8 inventory records with negative stock.',
      evidence: {
        sample_violations: [{ row_index: 10, sku: 'SKU-001', quantity_on_hand: -12 }],
      },
      execution_duration_ms: 8,
    },
    {
      id: 'finding_004',
      rule_id: 'VAL-FRESH-001',
      rule_name: 'Order Ingestion Freshness SLA Check',
      rule_category: 'TEMPORAL_ANOMALY',
      severity: 'MEDIUM',
      status: 'FAILED',
      dataset_id: 'orders',
      affected_fields: ['order_date'],
      affected_record_count: 1,
      total_record_count: 1250,
      message: 'Detected 4.47h Sunday ingestion sync gap.',
      evidence: {
        max_gap_hours: 4.47,
        threshold_hours: 2.0,
      },
      execution_duration_ms: 18,
    },
    {
      id: 'finding_005',
      rule_id: 'VAL-ORD-003',
      rule_name: 'Order Status Type Validity Check',
      rule_category: 'TYPE_VALIDITY',
      severity: 'LOW',
      status: 'PASSED',
      dataset_id: 'orders',
      affected_fields: ['order_status'],
      affected_record_count: 0,
      total_record_count: 1250,
      message: 'All order status values are valid.',
      evidence: {},
      execution_duration_ms: 6,
    },
  ];

  it('renders all findings rows initially', () => {
    const handleSelect = vi.fn();
    render(<FindingsTable findings={mockFindings} onSelectFinding={handleSelect} />);

    expect(screen.getByTestId('findings-table')).toBeInTheDocument();
    expect(screen.getByTestId('finding-row-VAL-ORD-001')).toBeInTheDocument();
    expect(screen.getByTestId('finding-row-VAL-ORD-002')).toBeInTheDocument();
    expect(screen.getByTestId('finding-row-VAL-INV-001')).toBeInTheDocument();
    expect(screen.getByTestId('finding-row-VAL-FRESH-001')).toBeInTheDocument();
    expect(screen.getByTestId('finding-row-VAL-ORD-003')).toBeInTheDocument();
  });

  it('acceptance criterion: filtering by CRITICAL isolates duplicate order checks', async () => {
    const user = userEvent.setup();
    const handleSelect = vi.fn();
    render(<FindingsTable findings={mockFindings} onSelectFinding={handleSelect} />);

    const severityFilter = screen.getByTestId('filter-severity');
    await user.selectOptions(severityFilter, 'CRITICAL');

    // VAL-ORD-001 (CRITICAL) must be present
    expect(screen.getByTestId('finding-row-VAL-ORD-001')).toBeInTheDocument();
    expect(screen.getByText('Order ID Uniqueness Check')).toBeInTheDocument();

    // All other checks must be filtered out
    expect(screen.queryByTestId('finding-row-VAL-ORD-002')).not.toBeInTheDocument();
    expect(screen.queryByTestId('finding-row-VAL-INV-001')).not.toBeInTheDocument();
    expect(screen.queryByTestId('finding-row-VAL-FRESH-001')).not.toBeInTheDocument();
    expect(screen.queryByTestId('finding-row-VAL-ORD-003')).not.toBeInTheDocument();
  });

  it('filters by status correctly (PASSED vs FAILED)', async () => {
    const user = userEvent.setup();
    render(<FindingsTable findings={mockFindings} onSelectFinding={vi.fn()} />);

    const statusFilter = screen.getByTestId('filter-status');
    await user.selectOptions(statusFilter, 'PASSED');

    expect(screen.getByTestId('finding-row-VAL-ORD-003')).toBeInTheDocument();
    expect(screen.queryByTestId('finding-row-VAL-ORD-001')).not.toBeInTheDocument();
  });

  it('filters by dataset correctly', async () => {
    const user = userEvent.setup();
    render(<FindingsTable findings={mockFindings} onSelectFinding={vi.fn()} />);

    const datasetFilter = screen.getByTestId('filter-dataset');
    await user.selectOptions(datasetFilter, 'inventory');

    expect(screen.getByTestId('finding-row-VAL-INV-001')).toBeInTheDocument();
    expect(screen.queryByTestId('finding-row-VAL-ORD-001')).not.toBeInTheDocument();
    expect(screen.queryByTestId('finding-row-VAL-ORD-002')).not.toBeInTheDocument();
  });

  it('searches by keyword', async () => {
    const user = userEvent.setup();
    render(<FindingsTable findings={mockFindings} onSelectFinding={vi.fn()} />);

    const searchInput = screen.getByTestId('filter-search');
    await user.type(searchInput, 'Sunday');

    expect(screen.getByTestId('finding-row-VAL-FRESH-001')).toBeInTheDocument();
    expect(screen.queryByTestId('finding-row-VAL-ORD-001')).not.toBeInTheDocument();
  });

  it('triggers onSelectFinding when row or view evidence button is clicked', async () => {
    const user = userEvent.setup();
    const handleSelect = vi.fn();
    render(<FindingsTable findings={mockFindings} onSelectFinding={handleSelect} />);

    // Click on row
    const row = screen.getByTestId('finding-row-VAL-ORD-001');
    await user.click(row);
    expect(handleSelect).toHaveBeenCalledWith(mockFindings[0]);

    // Click on View Evidence button
    const viewBtn = screen.getByTestId('view-evidence-btn-VAL-ORD-002');
    await user.click(viewBtn);
    expect(handleSelect).toHaveBeenCalledWith(mockFindings[1]);
  });

  it('triggers onTraceImpact when Trace Impact button is clicked without bubbling row select', async () => {
    const user = userEvent.setup();
    const handleSelect = vi.fn();
    const handleTraceImpact = vi.fn();

    render(
      <FindingsTable
        findings={mockFindings}
        onSelectFinding={handleSelect}
        onTraceImpact={handleTraceImpact}
      />
    );

    const traceBtn = screen.getByTestId('trace-impact-btn-VAL-ORD-001');
    await user.click(traceBtn);

    expect(handleTraceImpact).toHaveBeenCalledWith(mockFindings[0]);
    expect(handleSelect).not.toHaveBeenCalled();
  });

  it('resets all filters when Reset button is clicked', async () => {
    const user = userEvent.setup();
    render(<FindingsTable findings={mockFindings} onSelectFinding={vi.fn()} />);

    const severityFilter = screen.getByTestId('filter-severity');
    await user.selectOptions(severityFilter, 'CRITICAL');

    expect(screen.queryByTestId('finding-row-VAL-ORD-002')).not.toBeInTheDocument();

    const resetBtn = screen.getByTestId('reset-filters-btn');
    await user.click(resetBtn);

    expect(screen.getByTestId('finding-row-VAL-ORD-001')).toBeInTheDocument();
    expect(screen.getByTestId('finding-row-VAL-ORD-002')).toBeInTheDocument();
  });
});
