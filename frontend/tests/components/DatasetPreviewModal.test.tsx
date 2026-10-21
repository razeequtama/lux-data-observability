import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { DatasetPreviewModal } from '../../src/components/dataset/DatasetPreviewModal';
import * as api from '../../src/api/datasets';

describe('DatasetPreviewModal Component', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  const mockPreviewData = {
    dataset_id: 'orders',
    total_records: 125,
    limit: 50,
    offset: 0,
    columns: ['order_id', 'customer_id', 'order_status', 'total_amount'],
    rows: [
      {
        order_id: 'ORD-1001',
        customer_id: 'CUST-001',
        order_status: 'COMPLETED',
        total_amount: 149.5,
      },
      {
        order_id: 'ORD-1002',
        customer_id: 'CUST-002',
        order_status: 'PROCESSING',
        total_amount: 89.2,
      },
    ],
  };

  it('renders modal with table columns and rows from preview API', async () => {
    vi.spyOn(api, 'previewDataset').mockResolvedValueOnce(mockPreviewData);

    render(
      <DatasetPreviewModal
        isOpen={true}
        datasetId="orders"
        datasetName="orders.csv"
        onClose={vi.fn()}
      />
    );

    expect(screen.getByText('Dataset Preview: orders.csv')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('order_id')).toBeInTheDocument();
      expect(screen.getByText('customer_id')).toBeInTheDocument();
      expect(screen.getByText('ORD-1001')).toBeInTheDocument();
      expect(screen.getByText('ORD-1002')).toBeInTheDocument();
    });
  });

  it('paginates when Next button is clicked', async () => {
    vi.spyOn(api, 'previewDataset')
      .mockResolvedValueOnce(mockPreviewData)
      .mockResolvedValueOnce({
        ...mockPreviewData,
        offset: 50,
        rows: [
          {
            order_id: 'ORD-1051',
            customer_id: 'CUST-051',
            order_status: 'COMPLETED',
            total_amount: 200.0,
          },
        ],
      });

    render(
      <DatasetPreviewModal
        isOpen={true}
        datasetId="orders"
        datasetName="orders.csv"
        onClose={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('ORD-1001')).toBeInTheDocument();
    });

    const nextBtn = screen.getByRole('button', { name: /next/i });
    expect(nextBtn).toBeEnabled();

    fireEvent.click(nextBtn);

    await waitFor(() => {
      expect(api.previewDataset).toHaveBeenCalledWith('orders', 50, 50);
      expect(screen.getByText('ORD-1051')).toBeInTheDocument();
    });
  });

  it('calls onClose when close button is clicked', async () => {
    vi.spyOn(api, 'previewDataset').mockResolvedValueOnce(mockPreviewData);
    const handleClose = vi.fn();

    render(
      <DatasetPreviewModal
        isOpen={true}
        datasetId="orders"
        datasetName="orders.csv"
        onClose={handleClose}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('ORD-1001')).toBeInTheDocument();
    });

    const closeBtn = screen.getByRole('button', { name: /close dialog/i });
    fireEvent.click(closeBtn);

    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it('displays error alert if preview request fails', async () => {
    vi.spyOn(api, 'previewDataset').mockRejectedValueOnce(new Error('Dataset file not found'));

    render(
      <DatasetPreviewModal
        isOpen={true}
        datasetId="orders"
        datasetName="orders.csv"
        onClose={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Failed to preview dataset')).toBeInTheDocument();
      expect(screen.getByText('Dataset file not found')).toBeInTheDocument();
    });
  });
});
