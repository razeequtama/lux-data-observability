import React from 'react';
import { Database, FileSpreadsheet, Eye, Upload, RefreshCw, FolderX } from 'lucide-react';
import { DatasetResponse } from '../../types';

interface DatasetInspectorProps {
  datasets: DatasetResponse[];
  isLoading: boolean;
  isUnloading?: boolean;
  onPreviewDataset: (dataset: DatasetResponse) => void;
  onOpenUpload: () => void;
  onRefresh: () => void;
  onUnloadScenario?: () => void;
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
}) => {
  return (
    <div
      className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm"
      data-testid="dataset-inspector"
    >
      {/* Header bar */}
      <div className="flex flex-wrap items-center justify-between p-4 border-b border-slate-800 gap-3">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-lg bg-lux-950/60 border border-lux-700/40 text-lux-400">
            <Database className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white tracking-tight flex items-center space-x-2">
              <span>Ingested Scenario Datasets</span>
              <span className="text-xs px-2 py-0.5 rounded-full font-mono bg-slate-800 text-slate-300 border border-slate-700">
                {datasets.length} files
              </span>
            </h3>
            <p className="text-xs text-slate-400">
              Source tables, row counts, and structural schemas for validation
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            type="button"
            onClick={onRefresh}
            disabled={isLoading || isUnloading}
            aria-label="Refresh datasets"
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
            title="Refresh datasets"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
          <button
            type="button"
            onClick={onOpenUpload}
            data-testid="open-upload-btn"
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg text-xs font-semibold transition-colors cursor-pointer"
          >
            <Upload className="w-3.5 h-3.5 text-lux-400" />
            <span>Upload Dataset</span>
          </button>
          {onUnloadScenario && datasets.length > 0 && (
            <button
              type="button"
              onClick={onUnloadScenario}
              disabled={isLoading || isUnloading}
              data-testid="dataset-inspector-unload-btn"
              className="flex items-center space-x-1.5 px-3 py-1.5 bg-slate-800 hover:bg-rose-950/60 active:bg-rose-900/80 text-slate-300 hover:text-rose-200 border border-slate-700 hover:border-rose-700/60 rounded-lg text-xs font-semibold transition-colors cursor-pointer disabled:opacity-50"
              title="Unload scenario datasets and reset workspace"
            >
              <FolderX className={`w-3.5 h-3.5 text-rose-400 ${isUnloading ? 'animate-pulse' : ''}`} />
              <span>{isUnloading ? 'Unloading...' : 'Unload Scenario'}</span>
            </button>
          )}
        </div>
      </div>

      {/* Datasets Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse" data-testid="datasets-table">
          <thead className="bg-slate-950/50 border-b border-slate-800 text-slate-400">
            <tr>
              <th className="py-3 px-4 font-semibold">Dataset / File</th>
              <th className="py-3 px-4 font-semibold">Format</th>
              <th className="py-3 px-4 font-semibold text-right">Records</th>
              <th className="py-3 px-4 font-semibold text-right">Columns</th>
              <th className="py-3 px-4 font-semibold text-right">File Size</th>
              <th className="py-3 px-4 font-semibold text-center w-28">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
            {isLoading ? (
              <tr>
                <td colSpan={6} className="py-10 text-center text-slate-400 font-sans">
                  <div className="flex flex-col items-center justify-center space-y-2">
                    <div className="w-6 h-6 border-2 border-lux-500 border-t-transparent rounded-full animate-spin" />
                    <span>Loading scenario datasets...</span>
                  </div>
                </td>
              </tr>
            ) : datasets.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-10 text-center text-slate-400 font-sans">
                  <div className="flex flex-col items-center justify-center space-y-2">
                    <FileSpreadsheet className="w-8 h-8 text-slate-600" />
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
                  <td className="py-3 px-4 font-sans">
                    <div className="flex items-center space-x-2">
                      <FileSpreadsheet className="w-4 h-4 text-lux-400 shrink-0" />
                      <div>
                        <span className="font-semibold text-white font-mono text-xs">
                          {dataset.name}
                        </span>
                        <div className="text-[11px] text-slate-400 font-mono">
                          id: {dataset.id}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-lux-950/80 text-lux-300 border border-lux-700/40 uppercase">
                      {dataset.format}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right font-semibold text-slate-200">
                    {dataset.record_count.toLocaleString()}
                  </td>
                  <td className="py-3 px-4 text-right text-slate-300">
                    {dataset.column_count}
                  </td>
                  <td className="py-3 px-4 text-right text-slate-400">
                    {formatBytes(dataset.file_size_bytes)}
                  </td>
                  <td className="py-3 px-4 text-center">
                    <button
                      type="button"
                      onClick={() => onPreviewDataset(dataset)}
                      data-testid={`preview-btn-${dataset.id}`}
                      className="inline-flex items-center space-x-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-lux-700 text-slate-200 hover:text-white border border-slate-700 hover:border-lux-600 text-xs font-sans transition-colors cursor-pointer"
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

