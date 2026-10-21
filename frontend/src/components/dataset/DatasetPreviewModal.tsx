import React, { useEffect, useState, useCallback } from 'react';
import { ChevronLeft, ChevronRight, Database, FileSpreadsheet } from 'lucide-react';
import { Modal } from '../common/Modal';
import { AlertBanner } from '../common/AlertBanner';
import { previewDataset } from '../../api';
import { DatasetPreviewResponse } from '../../types';

interface DatasetPreviewModalProps {
  isOpen: boolean;
  datasetId: string | null;
  datasetName: string;
  onClose: () => void;
}

export const DatasetPreviewModal: React.FC<DatasetPreviewModalProps> = ({
  isOpen,
  datasetId,
  datasetName,
  onClose,
}) => {
  const [data, setData] = useState<DatasetPreviewResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [offset, setOffset] = useState(0);
  const limit = 50;

  const fetchPreview = useCallback(async (id: string, currentOffset: number) => {
    setLoading(true);
    setError(null);
    try {
      const response = await previewDataset(id, limit, currentOffset);
      setData(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dataset preview');
    } finally {
      setLoading(false);
    }
  }, [limit]);

  useEffect(() => {
    if (isOpen && datasetId) {
      setOffset(0);
      fetchPreview(datasetId, 0);
    } else {
      setData(null);
      setError(null);
      setOffset(0);
    }
  }, [isOpen, datasetId, fetchPreview]);

  const handleNextPage = () => {
    if (!data || offset + limit >= data.total_records) return;
    const nextOffset = offset + limit;
    setOffset(nextOffset);
    if (datasetId) {
      fetchPreview(datasetId, nextOffset);
    }
  };

  const handlePrevPage = () => {
    if (offset <= 0) return;
    const prevOffset = Math.max(0, offset - limit);
    setOffset(prevOffset);
    if (datasetId) {
      fetchPreview(datasetId, prevOffset);
    }
  };

  const totalRecords = data?.total_records || 0;
  const currentStart = totalRecords === 0 ? 0 : offset + 1;
  const currentEnd = Math.min(offset + limit, totalRecords);

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Dataset Preview: ${datasetName || datasetId || ''}`}
      description={
        data
          ? `Displaying records ${currentStart.toLocaleString()}–${currentEnd.toLocaleString()} of ${totalRecords.toLocaleString()} total rows across ${data.columns.length} columns.`
          : 'Loading dataset sample records...'
      }
      maxWidth="max-w-6xl"
      dialogId="dataset-preview-modal"
    >
      <div className="space-y-4">
        {error && (
          <AlertBanner
            type="error"
            message="Failed to preview dataset"
            details={error}
            onClose={() => setError(null)}
          />
        )}

        {/* Content Table */}
        <div className="border border-slate-800 rounded-lg overflow-hidden bg-slate-950/60">
          <div className="overflow-x-auto max-h-[55vh]">
            <table className="w-full text-left text-xs border-collapse">
              <thead className="bg-slate-900 border-b border-slate-800 sticky top-0 z-10">
                <tr>
                  <th className="py-2.5 px-3 text-slate-400 font-mono font-medium border-r border-slate-800 w-14 text-center">
                    #
                  </th>
                  {data?.columns.map((col) => (
                    <th
                      key={col}
                      className="py-2.5 px-3 font-semibold text-slate-200 border-r border-slate-800/80 last:border-r-0 whitespace-nowrap"
                    >
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                {loading ? (
                  <tr>
                    <td
                      colSpan={(data?.columns.length || 1) + 1}
                      className="py-12 text-center text-slate-400 font-sans"
                    >
                      <div className="flex flex-col items-center justify-center space-y-2">
                        <div className="w-6 h-6 border-2 border-lux-500 border-t-transparent rounded-full animate-spin" />
                        <span>Loading rows...</span>
                      </div>
                    </td>
                  </tr>
                ) : !data || data.rows.length === 0 ? (
                  <tr>
                    <td
                      colSpan={(data?.columns.length || 1) + 1}
                      className="py-12 text-center text-slate-400 font-sans"
                    >
                      <div className="flex flex-col items-center justify-center space-y-2">
                        <FileSpreadsheet className="w-8 h-8 text-slate-600" />
                        <span>No records found in this dataset.</span>
                      </div>
                    </td>
                  </tr>
                ) : (
                  data.rows.map((row, idx) => {
                    const rowNum = offset + idx + 1;
                    return (
                      <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
                        <td className="py-2 px-3 text-slate-400 text-center border-r border-slate-800 select-none">
                          {rowNum}
                        </td>
                        {data.columns.map((col) => {
                          const val = row[col];
                          const displayVal =
                            val === null || val === undefined
                              ? '<null>'
                              : typeof val === 'object'
                              ? JSON.stringify(val)
                              : String(val);
                          const isNull = val === null || val === undefined;

                          return (
                            <td
                              key={col}
                              className={`py-2 px-3 border-r border-slate-800/60 last:border-r-0 whitespace-nowrap max-w-xs truncate ${
                                isNull ? 'text-slate-400 italic' : ''
                              }`}
                              title={String(displayVal)}
                            >
                              {displayVal}
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Pagination & Status Footer */}
        <div className="flex flex-wrap items-center justify-between gap-4 pt-2 border-t border-slate-800 text-xs text-slate-400">
          <div className="flex items-center space-x-2">
            <Database className="w-3.5 h-3.5 text-lux-400" />
            <span>
              Showing {currentStart.toLocaleString()}–{currentEnd.toLocaleString()} of{' '}
              <strong className="text-slate-200">{totalRecords.toLocaleString()}</strong> rows
            </span>
          </div>

          <div className="flex items-center space-x-2">
            <button
              type="button"
              onClick={handlePrevPage}
              disabled={loading || offset <= 0}
              className="flex items-center space-x-1 px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:hover:bg-slate-800 text-slate-200 border border-slate-700 transition-colors cursor-pointer"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
              <span>Previous</span>
            </button>
            <span className="px-2 py-1 bg-slate-900 border border-slate-800 rounded font-mono text-slate-300">
              Page {Math.floor(offset / limit) + 1} of {Math.max(1, Math.ceil(totalRecords / limit))}
            </span>
            <button
              type="button"
              onClick={handleNextPage}
              disabled={loading || !data || offset + limit >= totalRecords}
              className="flex items-center space-x-1 px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:hover:bg-slate-800 text-slate-200 border border-slate-700 transition-colors cursor-pointer"
            >
              <span>Next</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </Modal>
  );
};

