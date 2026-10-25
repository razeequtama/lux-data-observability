import React from 'react';
import { Database, FileSpreadsheet, Eye, Upload, RefreshCw, FolderX, X } from 'lucide-react';
import { DatasetResponse } from '../../types';

interface DatasetInspectorProps {
  datasets: DatasetResponse[];
  isLoading: boolean;
  isUnloading?: boolean;
  onPreviewDataset: (dataset: DatasetResponse) => void;
  onOpenUpload: () => void;
  onRefresh: () => void;
  onUnloadScenario?: () => void;
  onClose?: () => void;
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export const DatasetInspector: React.FC<DatasetInspectorProps> = ({
  datasets,
  isLoading,
  isUnloading = false,
  onPreviewDataset,
  onOpenUpload,
  onRefresh,
  onUnloadScenario,
  onClose,
}) => {
  return (
    <div
      className="bg-[#0d0f1b]/95 backdrop-blur-2xl border border-white/[0.1] border-t-purple-400/40 rounded-3xl overflow-hidden shadow-2xl shadow-black/80 flex flex-col"
      data-testid="dataset-inspector"
    >
      {/* Header bar */}
      <div className="flex flex-wrap items-center justify-between p-6 sm:p-7 border-b border-white/[0.08] bg-[#0c0e1a]/95 gap-4">
        <div className="flex items-center space-x-3.5">
          <div className="p-2.5 rounded-2xl bg-lux-950/80 border border-lux-700/50 text-lux-400 shadow-[0_0_16px_rgba(168,85,247,0.35)]">
            <Database className="w-5 h-5" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-bold text-white tracking-tight flex items-center space-x-2.5">
              <span>Ingested Scenario Datasets</span>
              <span className="text-xs px-3 py-0.5 rounded-full font-mono font-semibold bg-slate-900 text-purple-200 border border-white/[0.08] shadow-inner">
                {datasets.length} files
              </span>
            </h3>
            <p className="text-xs text-slate-400">
              Source tables, row counts, and structural schemas for validation
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2.5">
          <button
            type="button"
            onClick={onRefresh}
            disabled={isLoading || isUnloading}
            aria-label="Refresh datasets"
            className="p-2.5 rounded-xl bg-slate-900/80 hover:bg-slate-800 text-slate-300 border border-white/[0.08] hover:border-purple-400/40 transition-all cursor-pointer shadow-sm"
            title="Refresh datasets"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
          <button
            type="button"
            onClick={onOpenUpload}
            data-testid="open-upload-btn"
            className="flex items-center justify-center space-x-3 px-7 py-3 min-w-[155px] bg-slate-900/80 hover:bg-slate-800 text-slate-200 border border-white/[0.08] hover:border-purple-400/40 rounded-2xl text-xs sm:text-sm font-bold tracking-wide transition-all cursor-pointer shadow-sm whitespace-nowrap"
          >
            <Upload className="w-4 h-4 text-lux-400 shrink-0" />
            <span>Upload Dataset</span>
          </button>
          {onUnloadScenario && datasets.length > 0 && (
            <button
              type="button"
              onClick={onUnloadScenario}
              disabled={isLoading || isUnloading}
              data-testid="dataset-inspector-unload-btn"
              className="flex items-center justify-center space-x-3 px-7 py-3 min-w-[160px] bg-slate-900/80 hover:bg-rose-950/60 active:bg-rose-900/80 text-slate-300 hover:text-rose-200 border border-white/[0.08] hover:border-rose-700/60 rounded-2xl text-xs sm:text-sm font-bold tracking-wide transition-all cursor-pointer disabled:opacity-50 shadow-sm whitespace-nowrap"
              title="Unload scenario datasets and reset workspace"
            >
              <FolderX className={`w-4 h-4 text-rose-400 ${isUnloading ? 'animate-pulse' : ''} shrink-0`} />
              <span>{isUnloading ? 'Unloading...' : 'Unload Scenario'}</span>
            </button>
          )}
          {onClose && (
            <button
              type="button"
              onClick={onClose}
              data-testid="close-dataset-inspector-btn"
              aria-label="Close Datasets Inspector"
              className="p-3 rounded-2xl bg-slate-900/80 hover:bg-slate-800 text-slate-400 hover:text-white border border-white/[0.08] hover:border-purple-400/40 transition-all cursor-pointer shadow-sm ml-1"
              title="Close Inspector"
            >
              <X className="w-4.5 h-4.5" />
            </button>
          )}
        </div>
      </div>

      {/* Datasets Table */}
      <div className="overflow-x-auto p-4 sm:p-6">
        <table className="w-full text-left text-xs border-collapse" data-testid="datasets-table">
          <thead className="bg-[#090b14]/80 border-b border-white/[0.08] text-slate-400">
            <tr>
              <th className="py-3.5 px-5 font-semibold tracking-wider uppercase text-[11px]">Dataset / File</th>
              <th className="py-3.5 px-5 font-semibold tracking-wider uppercase text-[11px]">Format</th>
              <th className="py-3.5 px-5 font-semibold tracking-wider uppercase text-[11px] text-right">Records</th>
              <th className="py-3.5 px-5 font-semibold tracking-wider uppercase text-[11px] text-right">Columns</th>
              <th className="py-3.5 px-5 font-semibold tracking-wider uppercase text-[11px] text-right">File Size</th>
              <th className="py-3.5 px-5 font-semibold tracking-wider uppercase text-[11px] text-center w-32">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.05] font-mono text-slate-300">
            {isLoading ? (
              <tr>
                <td colSpan={6} className="py-16 text-center text-slate-400 font-sans">
                  <div className="flex flex-col items-center justify-center space-y-2.5">
                    <div className="w-7 h-7 border-2 border-lux-500 border-t-transparent rounded-full animate-spin" />
                    <span>Loading scenario datasets...</span>
                  </div>
                </td>
              </tr>
            ) : datasets.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-16 text-center text-slate-400 font-sans">
                  <div className="flex flex-col items-center justify-center space-y-2.5">
                    <FileSpreadsheet className="w-10 h-10 text-slate-600" />
                    <span>No datasets found for this scenario. Click "Load Scenario" above.</span>
                  </div>
                </td>
              </tr>
            ) : (
              datasets.map((dataset) => (
                <tr
                  key={dataset.id}
                  className="hover:bg-slate-800/40 transition-colors"
                  data-testid={`dataset-row-${dataset.id}`}
                >
                  <td className="py-4 px-5 font-sans">
                    <div className="flex items-center space-x-3">
                      <div className="p-2 rounded-xl bg-lux-950/60 border border-lux-700/30 text-lux-400 shrink-0">
                        <FileSpreadsheet className="w-4 h-4" />
                      </div>
                      <div>
                        <span className="font-semibold text-white font-mono text-xs">
                          {dataset.name}
                        </span>
                        <div className="text-[11px] text-slate-400 font-mono mt-0.5">
                          id: {dataset.id}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="py-4 px-5">
                    <span className="px-2.5 py-1 rounded-md text-[11px] font-bold bg-lux-950/80 text-lux-300 border border-lux-700/40 uppercase">
                      {dataset.format}
                    </span>
                  </td>
                  <td className="py-4 px-5 text-right font-semibold text-slate-200">
                    {dataset.record_count.toLocaleString()}
                  </td>
                  <td className="py-4 px-5 text-right text-slate-300">
                    {dataset.column_count}
                  </td>
                  <td className="py-4 px-5 text-right text-slate-400">
                    {formatBytes(dataset.file_size_bytes)}
                  </td>
                  <td className="py-4 px-5 text-center">
                    <button
                      type="button"
                      onClick={() => onPreviewDataset(dataset)}
                      data-testid={`preview-btn-${dataset.id}`}
                      className="inline-flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl bg-slate-900/80 hover:bg-lux-700 text-slate-200 hover:text-white border border-white/[0.08] hover:border-lux-500 text-xs font-sans font-semibold transition-all cursor-pointer shadow-sm hover:shadow-[0_0_12px_rgba(168,85,247,0.3)]"
                      title={`Preview records in ${dataset.name}`}
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>Preview</span>
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

