import React, { useState, useRef } from 'react';
import { Upload, FileSpreadsheet, CheckCircle2 } from 'lucide-react';
import { Modal } from '../common/Modal';
import { AlertBanner } from '../common/AlertBanner';
import { uploadDataset } from '../../api';
import { DatasetUploadResponse } from '../../types';

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  activeScenarioId?: string;
  onUploadSuccess: (uploaded: DatasetUploadResponse) => void;
}

const MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024; // 20 MB

export const UploadModal: React.FC<UploadModalProps> = ({
  isOpen,
  onClose,
  activeScenarioId,
  onUploadSuccess,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [datasetName, setDatasetName] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);
  const [successInfo, setSuccessInfo] = useState<DatasetUploadResponse | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const resetState = () => {
    setFile(null);
    setDatasetName('');
    setIsDragging(false);
    setIsUploading(false);
    setValidationError(null);
    setApiError(null);
    setSuccessInfo(null);
  };

  const handleClose = () => {
    resetState();
    onClose();
  };

  const validateAndSetFile = (selectedFile: File) => {
    setValidationError(null);
    setApiError(null);
    setSuccessInfo(null);

    // Validate file extension / format
    const nameLower = selectedFile.name.toLowerCase();
    const isCsv = nameLower.endsWith('.csv');
    const isJson = nameLower.endsWith('.json');
    if (!isCsv && !isJson) {
      setValidationError(
        `Invalid file format: "${selectedFile.name}". Only .csv and .json files are supported.`
      );
      setFile(null);
      return false;
    }

    // Validate size limit (20MB)
    if (selectedFile.size > MAX_FILE_SIZE_BYTES) {
      const sizeMb = (selectedFile.size / (1024 * 1024)).toFixed(2);
      setValidationError(
        `File size exceeds 20MB limit: "${selectedFile.name}" is ${sizeMb} MB. Please upload a file under 20 MB.`
      );
      setFile(null);
      return false;
    }

    setFile(selectedFile);
    if (!datasetName) {
      setDatasetName(selectedFile.name);
    }
    return true;
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setValidationError('Please select a file to upload.');
      return;
    }

    setIsUploading(true);
    setApiError(null);

    try {
      const response = await uploadDataset(
        file,
        activeScenarioId,
        datasetName.trim() || file.name
      );
      setSuccessInfo(response);
      onUploadSuccess(response);
      setTimeout(() => {
        handleClose();
      }, 1200);
    } catch (err) {
      setApiError(err instanceof Error ? err.message : 'Upload failed due to a server error.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Upload Custom Dataset"
      description="Upload a CSV or JSON dataset (max 20MB) to ingest into the active workspace."
      maxWidth="max-w-xl"
      dialogId="dataset-upload-modal"
    >
      <form onSubmit={handleSubmit} className="space-y-5">
        {validationError && (
          <AlertBanner
            type="warning"
            message="Validation Issue"
            details={validationError}
            onClose={() => setValidationError(null)}
          />
        )}

        {apiError && (
          <AlertBanner
            type="error"
            message="Upload Failed"
            details={apiError}
            onClose={() => setApiError(null)}
          />
        )}

        {successInfo && (
          <div className="flex items-center space-x-2 p-3 bg-emerald-950/40 border border-emerald-600/40 rounded-lg text-emerald-300 text-xs">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>
              Successfully uploaded <strong>{successInfo.name}</strong> ({successInfo.record_count.toLocaleString()} records, {successInfo.column_count} columns)!
            </span>
          </div>
        )}

        {/* Drag and drop target */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
            isDragging
              ? 'border-lux-500 bg-lux-950/30'
              : file
              ? 'border-emerald-600/60 bg-emerald-950/10'
              : 'border-slate-700 hover:border-slate-600 bg-slate-950/40'
          }`}
          data-testid="dropzone"
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,.json"
            onChange={handleFileInputChange}
            className="hidden"
            data-testid="file-input"
          />

          <div className="flex flex-col items-center justify-center space-y-2">
            {file ? (
              <>
                <div className="w-12 h-12 rounded-full bg-emerald-900/40 border border-emerald-600/40 flex items-center justify-center text-emerald-300">
                  <FileSpreadsheet className="w-6 h-6" />
                </div>
                <div className="space-y-1">
                  <p className="text-sm font-semibold text-white">{file.name}</p>
                  <p className="text-xs text-slate-400">
                    {(file.size / 1024).toFixed(1)} KB • {file.name.endsWith('.csv') ? 'CSV' : 'JSON'}
                  </p>
                </div>
                <p className="text-[11px] text-lux-400">Click or drag another file to replace</p>
              </>
            ) : (
              <>
                <div className="w-12 h-12 rounded-full bg-lux-900/30 border border-lux-700/30 flex items-center justify-center text-lux-300">
                  <Upload className="w-6 h-6" />
                </div>
                <div className="space-y-1">
                  <p className="text-sm font-semibold text-slate-200">
                    Drag and drop your file here, or{' '}
                    <span className="text-lux-400 hover:underline">browse</span>
                  </p>
                  <p className="text-xs text-slate-400">Supported formats: CSV, JSON (max 20MB)</p>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Dataset Name Input */}
        <div>
          <label htmlFor="custom-dataset-name" className="block text-xs font-medium text-slate-300 mb-1.5">
            Dataset Display Name (optional)
          </label>
          <input
            id="custom-dataset-name"
            type="text"
            placeholder={file ? file.name : 'e.g., custom_transactions.csv'}
            value={datasetName}
            onChange={(e) => setDatasetName(e.target.value)}
            disabled={isUploading}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-lux-500 focus:ring-1 focus:ring-lux-500 disabled:opacity-50"
          />
        </div>

        {/* Target Scenario indicator */}
        <div className="flex items-center justify-between text-xs text-slate-400 p-2.5 bg-slate-950/60 rounded-lg border border-slate-800">
          <span>Target Workspace:</span>
          <span className="font-mono text-slate-300">
            {activeScenarioId || 'custom_uploads'}
          </span>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-800">
          <button
            type="button"
            onClick={handleClose}
            disabled={isUploading}
            className="px-4 py-2 rounded-lg text-xs font-medium text-slate-300 hover:bg-slate-800 transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={!file || isUploading}
            data-testid="submit-upload-btn"
            className="flex items-center space-x-1.5 px-4 py-2 bg-lux-700 hover:bg-lux-600 active:bg-lux-800 disabled:opacity-40 text-white rounded-lg text-xs font-semibold shadow-sm shadow-lux-700/30 transition-colors cursor-pointer"
          >
            <Upload className={`w-3.5 h-3.5 ${isUploading ? 'animate-bounce' : ''}`} />
            <span>{isUploading ? 'Uploading...' : 'Upload & Ingest'}</span>
          </button>
        </div>
      </form>
    </Modal>
  );
};
