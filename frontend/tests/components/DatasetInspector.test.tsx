import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { DatasetInspector } from '../../src/components/dataset/DatasetInspector';
import { DatasetResponse } from '../../src/types';

describe('DatasetInspector Component', () => {
  const mockDatasets: DatasetResponse[] = [
    {
      id: 'orders',
      scenario_id: 'monday_revenue_mystery',
      name: 'orders.csv',
      format: 'csv',
      file_size_bytes: 104857,
      record_count: 1250,
      column_count: 5,
    },
    {
      id: 'order_items',
      scenario_id: 'monday_revenue_mystery',
      name: 'order_items.csv',
      format: 'csv',
      file_size_bytes: 284920,
      record_count: 3420,
      column_count: 6,
    },
    {
      id: 'products',
      scenario_id: 'monday_revenue_mystery',
      name: 'products.csv',
      format: 'csv',
      file_size_bytes: 22450,
      record_count: 250,
      column_count: 4,
    },
    {
      id: 'inventory',
      scenario_id: 'monday_revenue_mystery',
      name: 'inventory.csv',
      format: 'csv',
      file_size_bytes: 18920,
      record_count: 250,
      column_count: 3,
    },
  ];

  it('renders dataset names, row counts, and column counts accurately', () => {
    render(
      <DatasetInspector
        datasets={mockDatasets}
        isLoading={false}
        onPreviewDataset={vi.fn()}
        onOpenUpload={vi.fn()}
        onRefresh={vi.fn()}
      />
    );

    expect(screen.getByText('Ingested Scenario Datasets')).toBeInTheDocument();
    expect(screen.getByText('4 files')).toBeInTheDocument();

    // Verify orders.csv record count (1,250) and column count (5)
    expect(screen.getByText('orders.csv')).toBeInTheDocument();
    expect(screen.getByText('1,250')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();

    // Verify order_items.csv record count (3,420)
    expect(screen.getByText('order_items.csv')).toBeInTheDocument();
    expect(screen.getByText('3,420')).toBeInTheDocument();

    // Verify products.csv and inventory.csv
    expect(screen.getByText('products.csv')).toBeInTheDocument();
    expect(screen.getByText('inventory.csv')).toBeInTheDocument();
  });

  it('triggers onPreviewDataset when preview button is clicked', () => {
    const handlePreview = vi.fn();
    render(
      <DatasetInspector
        datasets={mockDatasets}
        isLoading={false}
        onPreviewDataset={handlePreview}
        onOpenUpload={vi.fn()}
        onRefresh={vi.fn()}
      />
    );

    const previewOrdersBtn = screen.getByTestId('preview-btn-orders');
    expect(previewOrdersBtn).toBeInTheDocument();

    fireEvent.click(previewOrdersBtn);
    expect(handlePreview).toHaveBeenCalledTimes(1);
    expect(handlePreview).toHaveBeenCalledWith(mockDatasets[0]);
  });

  it('triggers onOpenUpload when upload dataset button is clicked', () => {
    const handleOpenUpload = vi.fn();
    render(
      <DatasetInspector
        datasets={mockDatasets}
        isLoading={false}
        onPreviewDataset={vi.fn()}
        onOpenUpload={handleOpenUpload}
        onRefresh={vi.fn()}
      />
    );

    const uploadBtn = screen.getByTestId('open-upload-btn');
    fireEvent.click(uploadBtn);
    expect(handleOpenUpload).toHaveBeenCalledTimes(1);
  });

  it('displays loading state while datasets are fetching', () => {
    render(
      <DatasetInspector
        datasets={[]}
        isLoading={true}
        onPreviewDataset={vi.fn()}
        onOpenUpload={vi.fn()}
        onRefresh={vi.fn()}
      />
    );

    expect(screen.getByText('Loading scenario datasets...')).toBeInTheDocument();
  });

  it('displays empty state when no datasets are loaded', () => {
    render(
      <DatasetInspector
        datasets={[]}
        isLoading={false}
        onPreviewDataset={vi.fn()}
        onOpenUpload={vi.fn()}
        onRefresh={vi.fn()}
      />
    );

    expect(
      screen.getByText(/No datasets found for this scenario/i)
    ).toBeInTheDocument();
  });

  it('renders "Unload Scenario" button and calls onUnloadScenario when clicked', () => {
    const handleUnloadScenario = vi.fn();
    render(
      <DatasetInspector
        datasets={mockDatasets}
        isLoading={false}
        isUnloading={false}
        onPreviewDataset={vi.fn()}
        onOpenUpload={vi.fn()}
        onRefresh={vi.fn()}
        onUnloadScenario={handleUnloadScenario}
      />
    );

    const unloadBtn = screen.getByTestId('dataset-inspector-unload-btn');
    expect(unloadBtn).toBeInTheDocument();
    fireEvent.click(unloadBtn);
    expect(handleUnloadScenario).toHaveBeenCalledTimes(1);
  });
});


