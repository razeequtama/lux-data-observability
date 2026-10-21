import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { EvidenceDrawer } from '../../src/components/validation/EvidenceDrawer';
import { ValidationFindingItem } from '../../src/types';

describe('EvidenceDrawer Component', () => {
  const mockDuplicateFinding: ValidationFindingItem = {
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
        { order_id: 'ORD-1088', occurrences: 2, row_indices: [87, 144] },
      ],
      sample_duplicates_truncated: false,
    },
    execution_duration_ms: 14,
  };

  const mockForeignKeyFinding: ValidationFindingItem = {
    id: 'f2',
    rule_id: 'VAL-ORD-002',
    rule_name: 'Order Items Foreign Key Integrity',
    rule_category: 'REFERENTIAL_INTEGRITY',
    severity: 'HIGH',
    status: 'FAILED',
    dataset_id: 'order_items',
    affected_fields: ['product_id'],
    affected_record_count: 24,
    total_record_count: 3420,
    message: 'Found 24 order_items records with non-existent product_id.',
    evidence: {
      sample_orphaned_keys: ['PRD-9001', 'PRD-9002'],
      sample_violations: [
        { row_index: 12, order_id: 'ORD-1002', product_id: 'PRD-9001' },
      ],
    },
    execution_duration_ms: 20,
  };

  it('renders nothing when isOpen is false', () => {
    render(
      <EvidenceDrawer
        finding={mockDuplicateFinding}
        isOpen={false}
        onClose={vi.fn()}
      />
    );

    expect(screen.queryByTestId('evidence-drawer')).not.toBeInTheDocument();
  });

  it('renders nothing when finding is null', () => {
    render(
      <EvidenceDrawer
        finding={null}
        isOpen={true}
        onClose={vi.fn()}
      />
    );

    expect(screen.queryByTestId('evidence-drawer')).not.toBeInTheDocument();
  });

  it('acceptance criterion: displays sample rows and observed vs expected values', () => {
    render(
      <EvidenceDrawer
        finding={mockDuplicateFinding}
        isOpen={true}
        onClose={vi.fn()}
      />
    );

    expect(screen.getByTestId('evidence-drawer')).toBeInTheDocument();
    expect(screen.getByText('Order ID Uniqueness Check')).toBeInTheDocument();
    expect(screen.getByText('VAL-ORD-001')).toBeInTheDocument();

    // Observed vs Expected section
    expect(screen.getByTestId('observed-vs-expected-card')).toBeInTheDocument();
    expect(
      screen.getByText('0 duplicate records (Every key must be unique)')
    ).toBeInTheDocument();
    expect(
      screen.getByText('15 duplicate keys detected in dataset')
    ).toBeInTheDocument();

    // Sample Duplicate Rows & Line Numbers (#43, #109)
    expect(screen.getByText('ORD-1042')).toBeInTheDocument();
    expect(screen.getByText('#43, #109')).toBeInTheDocument();
    expect(screen.getByText('ORD-1088')).toBeInTheDocument();
    expect(screen.getByText('#88, #145')).toBeInTheDocument();
  });

  it('renders orphaned keys and broken foreign key sample violations', () => {
    render(
      <EvidenceDrawer
        finding={mockForeignKeyFinding}
        isOpen={true}
        onClose={vi.fn()}
      />
    );

    expect(
      screen.getByText('All foreign keys exist in target dimension dataset')
    ).toBeInTheDocument();
    expect(
      screen.getByText('24 orphaned records referencing missing keys')
    ).toBeInTheDocument();

    // Orphaned keys badge
    expect(screen.getByText('PRD-9001')).toBeInTheDocument();
    expect(screen.getByText('PRD-9002')).toBeInTheDocument();

    // Sample violation row line number (#13)
    expect(screen.getByText('#13')).toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', async () => {
    const user = userEvent.setup();
    const handleClose = vi.fn();

    render(
      <EvidenceDrawer
        finding={mockDuplicateFinding}
        isOpen={true}
        onClose={handleClose}
      />
    );

    const closeBtn = screen.getByTestId('close-evidence-drawer');
    await user.click(closeBtn);

    expect(handleClose).toHaveBeenCalled();
  });

  it('calls onClose when clicking backdrop', async () => {
    const user = userEvent.setup();
    const handleClose = vi.fn();

    render(
      <EvidenceDrawer
        finding={mockDuplicateFinding}
        isOpen={true}
        onClose={handleClose}
      />
    );

    const backdrop = screen.getByTestId('evidence-drawer-backdrop');
    await user.click(backdrop);

    expect(handleClose).toHaveBeenCalled();
  });

  it('calls onClose when pressing Escape key', () => {
    const handleClose = vi.fn();

    render(
      <EvidenceDrawer
        finding={mockDuplicateFinding}
        isOpen={true}
        onClose={handleClose}
      />
    );

    fireEvent.keyDown(document, { key: 'Escape' });
    expect(handleClose).toHaveBeenCalled();
  });

  it('calls onTraceImpact when Trace Downstream Impact button is clicked', async () => {
    const user = userEvent.setup();
    const handleClose = vi.fn();
    const handleTraceImpact = vi.fn();

    render(
      <EvidenceDrawer
        finding={mockDuplicateFinding}
        isOpen={true}
        onClose={handleClose}
        onTraceImpact={handleTraceImpact}
      />
    );

    const traceBtn = screen.getByTestId('drawer-trace-impact-btn');
    await user.click(traceBtn);

    expect(handleTraceImpact).toHaveBeenCalledWith(mockDuplicateFinding);
    expect(handleClose).toHaveBeenCalled();
  });
});
