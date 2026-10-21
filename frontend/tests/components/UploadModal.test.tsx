import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { UploadModal } from '../../src/components/dataset/UploadModal';
import * as api from '../../src/api/datasets';

describe('UploadModal Component', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders upload modal with dropzone and inputs', () => {
    render(
      <UploadModal
        isOpen={true}
        onClose={vi.fn()}
        activeScenarioId="monday_revenue_mystery"
        onUploadSuccess={vi.fn()}
      />
    );

    expect(screen.getByText('Upload Custom Dataset')).toBeInTheDocument();
    expect(screen.getByTestId('dropzone')).toBeInTheDocument();
    expect(screen.getByLabelText(/dataset display name/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /upload & ingest/i })).toBeDisabled();
  });

  it('rejects unsupported file formats with client validation error', () => {
    render(
      <UploadModal
        isOpen={true}
        onClose={vi.fn()}
        activeScenarioId="monday_revenue_mystery"
        onUploadSuccess={vi.fn()}
      />
    );

    const fileInput = screen.getByTestId('file-input');
    const invalidFile = new File(['binary data'], 'document.pdf', {
      type: 'application/pdf',
    });

    fireEvent.change(fileInput, { target: { files: [invalidFile] } });

    expect(screen.getByText('Validation Issue')).toBeInTheDocument();
    expect(
      screen.getByText(/Invalid file format: "document.pdf". Only .csv and .json files are supported./i)
    ).toBeInTheDocument();
  });

  it('rejects files exceeding 20MB limit with client validation error', () => {
    render(
      <UploadModal
        isOpen={true}
        onClose={vi.fn()}
        activeScenarioId="monday_revenue_mystery"
        onUploadSuccess={vi.fn()}
      />
    );

    const fileInput = screen.getByTestId('file-input');
    // Create mock file with size 25MB (25 * 1024 * 1024 + 1 bytes)
    const largeFile = new File(['a'], 'huge_transactions.csv', { type: 'text/csv' });
    Object.defineProperty(largeFile, 'size', { value: 25 * 1024 * 1024 + 10 });

    fireEvent.change(fileInput, { target: { files: [largeFile] } });

    expect(screen.getByText('Validation Issue')).toBeInTheDocument();
    expect(screen.getByText(/File size exceeds 20MB limit/i)).toBeInTheDocument();
  });

  it('accepts valid CSV file and submits upload successfully', async () => {
    const mockUploadResponse = {
      dataset_id: 'upload_custom_1',
      name: 'custom_orders.csv',
      format: 'csv',
      file_size_bytes: 4096,
      record_count: 50,
      column_count: 4,
    };
    vi.spyOn(api, 'uploadDataset').mockResolvedValueOnce(mockUploadResponse);
    const handleUploadSuccess = vi.fn();

    render(
      <UploadModal
        isOpen={true}
        onClose={vi.fn()}
        activeScenarioId="monday_revenue_mystery"
        onUploadSuccess={handleUploadSuccess}
      />
    );

    const fileInput = screen.getByTestId('file-input');
    const validFile = new File(['order_id,amount\n1,100\n2,200'], 'custom_orders.csv', {
      type: 'text/csv',
    });

    fireEvent.change(fileInput, { target: { files: [validFile] } });

    // File selected, submit button should be enabled
    const submitBtn = screen.getByTestId('submit-upload-btn');
    expect(submitBtn).toBeEnabled();

    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(api.uploadDataset).toHaveBeenCalledWith(
        validFile,
        'monday_revenue_mystery',
        'custom_orders.csv'
      );
      expect(handleUploadSuccess).toHaveBeenCalledWith(mockUploadResponse);
      expect(screen.getByText(/Successfully uploaded/i)).toBeInTheDocument();
    });
  });

  it('handles server upload error and displays error alert', async () => {
    vi.spyOn(api, 'uploadDataset').mockRejectedValueOnce(
      new Error('Malicious or corrupted CSV file payload detected.')
    );

    render(
      <UploadModal
        isOpen={true}
        onClose={vi.fn()}
        activeScenarioId="monday_revenue_mystery"
        onUploadSuccess={vi.fn()}
      />
    );

    const fileInput = screen.getByTestId('file-input');
    const validFile = new File(['malicious'], 'suspicious.csv', { type: 'text/csv' });

    fireEvent.change(fileInput, { target: { files: [validFile] } });

    const submitBtn = screen.getByTestId('submit-upload-btn');
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText('Upload Failed')).toBeInTheDocument();
      expect(
        screen.getByText('Malicious or corrupted CSV file payload detected.')
      ).toBeInTheDocument();
    });
  });
});

