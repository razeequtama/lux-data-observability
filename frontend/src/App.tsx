import React, { useState, useEffect, useCallback } from 'react';
import { AppHeader } from './components/common/AppHeader';
import { NAVIGATION_TABS } from './constants/navigation';
import { AlertBanner, AlertType } from './components/common/AlertBanner';
import { DatasetInspector } from './components/dataset/DatasetInspector';
import { DatasetPreviewModal } from './components/dataset/DatasetPreviewModal';
import { UploadModal } from './components/dataset/UploadModal';
import { ValidationView } from './components/validation/ValidationView';
import { LineageView } from './components/lineage/LineageView';
import { PipelineObservabilityView } from './components/pipeline';
import { InvestigationWorkspace } from './components/reports';
import {
  listScenarios,
  loadScenario,
  unloadScenario,
  listDatasets,
} from './api';
import {
  DatasetResponse,
  DatasetUploadResponse,
  FixtureVersion,
  NavigationTab,
  ScenarioSummary,
  ValidationFindingItem,
} from './types';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavigationTab>('validations');
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]);
  const [activeScenarioId, setActiveScenarioId] = useState<string>('monday_revenue_mystery');
  const [activeFixtureVersion, setActiveFixtureVersion] = useState<FixtureVersion>('defective');
  const [datasets, setDatasets] = useState<DatasetResponse[]>([]);

  // UI state
  const [isDatasetInspectorOpen, setIsDatasetInspectorOpen] = useState(true);
  const [previewingDataset, setPreviewingDataset] = useState<DatasetResponse | null>(null);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [isLoadingScenario, setIsLoadingScenario] = useState(false);
  const [isUnloadingScenario, setIsUnloadingScenario] = useState(false);
  const [isLoadingDatasets, setIsLoadingDatasets] = useState(false);
  const [selectedFindingForImpact, setSelectedFindingForImpact] = useState<ValidationFindingItem | null>(null);
  const [selectedLineageNodeId, setSelectedLineageNodeId] = useState<string | null>(null);
  const [alert, setAlert] = useState<{
    type: AlertType;
    message: string;
    details?: string;
  } | null>(null);

  const activeTabDef = NAVIGATION_TABS.find((tab) => tab.id === activeTab) || NAVIGATION_TABS[0];

  const fetchDatasets = useCallback(async (scenarioId: string) => {
    setIsLoadingDatasets(true);
    try {
      const data = await listDatasets(scenarioId);
      setDatasets(data);
    } catch (err) {
      // Don't overwrite critical scenario alerts, but log failure
      console.warn('Could not fetch datasets:', err);
    } finally {
      setIsLoadingDatasets(false);
    }
  }, []);

  const fetchScenarios = useCallback(async () => {
    try {
      const list = await listScenarios();
      if (list && list.length > 0) {
        setScenarios(list);
        const current = list.find((s) => s.id === activeScenarioId) || list[0];
        setActiveScenarioId(current.id);
        if (current.active_fixture_version === 'corrected') {
          setActiveFixtureVersion('corrected');
        }
      }
    } catch (err) {
      console.warn('Could not list scenarios:', err);
    }
  }, [activeScenarioId]);

  useEffect(() => {
    fetchScenarios();
    fetchDatasets(activeScenarioId);
  }, [fetchScenarios, fetchDatasets, activeScenarioId]);

  const handleSelectScenario = (id: string) => {
    setActiveScenarioId(id);
    fetchDatasets(id);
  };

  const handleSelectFixtureVersion = (version: FixtureVersion) => {
    setActiveFixtureVersion(version);
  };

  const handleLoadScenario = async (scenarioId: string, version: FixtureVersion) => {
    setIsLoadingScenario(true);
    setAlert(null);
    try {
      const res = await loadScenario(scenarioId, version);
      setActiveFixtureVersion(version);
      setAlert({
        type: 'success',
        message: 'Scenario Loaded Successfully',
        details: `${res.message} Loaded ${res.loaded_datasets.length} datasets, ${res.rules_registered} rules, and ${res.lineage_nodes_loaded} lineage nodes.`,
      });
      await fetchDatasets(scenarioId);
      await fetchScenarios();
    } catch (err) {
      setAlert({
        type: 'error',
        message: 'Failed to Load Scenario',
        details: err instanceof Error ? err.message : 'Unknown network error loading scenario.',
      });
    } finally {
      setIsLoadingScenario(false);
    }
  };

  const handleUnloadScenario = async (scenarioId: string) => {
    setIsUnloadingScenario(true);
    setAlert(null);
    try {
      const res = await unloadScenario(scenarioId);
      setAlert({
        type: 'info',
        message: 'Scenario Unloaded',
        details: res.message,
      });
      await fetchDatasets(scenarioId);
      await fetchScenarios();
    } catch (err) {
      setAlert({
        type: 'error',
        message: 'Failed to Unload Scenario',
        details: err instanceof Error ? err.message : 'Unknown network error unloading scenario.',
      });
    } finally {
      setIsUnloadingScenario(false);
    }
  };

  const handleUploadSuccess = async (uploaded: DatasetUploadResponse) => {
    setAlert({
      type: 'success',
      message: 'Dataset Ingested Successfully',
      details: `File "${uploaded.name}" (${uploaded.record_count.toLocaleString()} rows, ${uploaded.column_count} columns) ingested into workspace.`,
    });
    await fetchDatasets(activeScenarioId);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-lux-700 selection:text-white">
      {/* Top Navigation Shell */}
      <AppHeader
        activeTab={activeTab}
        onTabChange={setActiveTab}
        scenarios={scenarios}
        activeScenarioId={activeScenarioId}
        activeFixtureVersion={activeFixtureVersion}
        isLoadingScenario={isLoadingScenario}
        isUnloadingScenario={isUnloadingScenario}
        onSelectScenario={handleSelectScenario}
        onSelectFixtureVersion={handleSelectFixtureVersion}
        onLoadScenario={handleLoadScenario}
        onUnloadScenario={handleUnloadScenario}
        onOpenUpload={() => setIsUploadModalOpen(true)}
        datasetsCount={datasets.length}
        isDatasetInspectorOpen={isDatasetInspectorOpen}
        onToggleDatasetInspector={() => setIsDatasetInspectorOpen((prev) => !prev)}
      />

      {/* Global Alert Banner */}
      {alert && (
        <div className="max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 pt-4">
          <AlertBanner
            type={alert.type}
            message={alert.message}
            details={alert.details}
            onClose={() => setAlert(null)}
          />
        </div>
      )}

      {/* Main Workspace Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Dataset Inspector Section */}
        {isDatasetInspectorOpen && (
          <section aria-label="Scenario Datasets Inspector">
            <DatasetInspector
              datasets={datasets}
              isLoading={isLoadingDatasets}
              isUnloading={isUnloadingScenario}
              onPreviewDataset={(dataset) => setPreviewingDataset(dataset)}
              onOpenUpload={() => setIsUploadModalOpen(true)}
              onRefresh={() => fetchDatasets(activeScenarioId)}
              onUnloadScenario={() => handleUnloadScenario(activeScenarioId)}
            />
          </section>
        )}

        {/* Tab Panel */}
        <div
          role="tabpanel"
          id={`panel-${activeTab}`}
          aria-labelledby={`tab-${activeTab}`}
          className="space-y-6"
        >
          {/* Active Section Banner */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
            <div className="flex items-start justify-between">
              <div>
                <h1 className="text-xl font-bold text-white tracking-tight flex items-center space-x-2">
                  <span>{activeTabDef.label}</span>
                </h1>
                <p className="text-sm text-slate-400 mt-1">{activeTabDef.description}</p>
              </div>
              <div className="hidden sm:block">
                <span className="text-xs font-mono px-2.5 py-1 rounded bg-slate-800 border border-slate-700 text-slate-400">
                  Tab: {activeTabDef.id}
                </span>
              </div>
            </div>
          </div>

          {activeTab === 'validations' ? (
            <ValidationView
              scenarioId={activeScenarioId}
              fixtureVersion={activeFixtureVersion}
              availableDatasets={datasets.map((d) => d.id)}
              onTraceImpact={(finding) => {
                setSelectedFindingForImpact(finding);
                setSelectedLineageNodeId(null);
                setActiveTab('lineage');
                setAlert({
                  type: 'info',
                  message: `Tracing Impact for ${finding.rule_id}`,
                  details: `Downstream impact analysis requested from "${finding.rule_name}" on dataset "${finding.dataset_id}". Highlighting blast radius in Lineage DAG.`,
                });
              }}
            />
          ) : activeTab === 'lineage' || activeTab === 'impact' ? (
            <LineageView
              scenarioId={activeScenarioId}
              initialSelectedNodeId={selectedLineageNodeId}
              initialTargetFinding={selectedFindingForImpact}
              onSelectNode={(nodeId) => {
                setSelectedLineageNodeId(nodeId);
              }}
            />
          ) : activeTab === 'pipelines' ? (
            <PipelineObservabilityView
              scenarioId={activeScenarioId}
              onTraceImpact={() => {
                setSelectedLineageNodeId('src_orders');
                setSelectedFindingForImpact(null);
                setActiveTab('lineage');
                setAlert({
                  type: 'info',
                  message: 'Tracing Impact from Pipeline Anomaly',
                  details:
                    'Highlighting downstream blast radius from src_orders across ETL transformations to Executive Dashboard.',
                });
              }}
            />
          ) : activeTab === 'investigation' ? (
            <InvestigationWorkspace
              scenarioId={activeScenarioId}
              onNavigateToLineage={(nodeId) => {
                setSelectedLineageNodeId(nodeId || null);
                setActiveTab('lineage');
              }}
              onNavigateToValidations={() => {
                setActiveTab('validations');
              }}
            />
          ) : (
            <div className="grid grid-cols-1 gap-6">
              <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-8 text-center space-y-4">
                <div className="w-12 h-12 mx-auto rounded-full bg-lux-900/50 border border-lux-700/30 flex items-center justify-center text-lux-300">
                  <activeTabDef.icon className="w-6 h-6" />
                </div>
                <div className="max-w-md mx-auto space-y-2">
                  <h2 className="text-lg font-semibold text-slate-200">
                    {activeTabDef.label} Module Ready
                  </h2>
                  <p className="text-sm text-slate-400">
                    Frontend scaffolding and Lux Purple tokens are operational. Domain view logic
                    will be mounted in subsequent tasks.
                  </p>
                </div>

                {/* Theme verification sample chips */}
                <div className="pt-4 border-t border-slate-800/80 max-w-lg mx-auto flex items-center justify-center space-x-3 text-xs">
                  <span className="px-2.5 py-1 rounded-full bg-lux-700 text-white font-medium">
                    Primary (#6B46C1)
                  </span>
                  <span className="px-2.5 py-1 rounded-full bg-lux-600 text-white font-medium">
                    Hover (#7C3AED)
                  </span>
                  <span className="px-2.5 py-1 rounded-full bg-status-healthy/15 text-status-healthy border border-status-healthy/30 font-medium">
                    Healthy
                  </span>
                  <span className="px-2.5 py-1 rounded-full bg-status-warning/15 text-status-warning border border-status-warning/30 font-medium">
                    Warning
                  </span>
                  <span className="px-2.5 py-1 rounded-full bg-status-corrupted/15 text-status-corrupted border border-status-corrupted/30 font-medium">
                    Corrupted
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Dataset Preview Modal */}
      {previewingDataset && (
        <DatasetPreviewModal
          isOpen={Boolean(previewingDataset)}
          datasetId={previewingDataset.id}
          datasetName={previewingDataset.name}
          onClose={() => setPreviewingDataset(null)}
        />
      )}

      {/* Upload Custom Dataset Modal */}
      <UploadModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        activeScenarioId={activeScenarioId}
        onUploadSuccess={handleUploadSuccess}
      />

      {/* Footer */}
      <footer className="border-t border-slate-800 bg-slate-900/60 py-4 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-400 space-y-2 sm:space-y-0">
          <div className="flex items-center space-x-2">
            <span>Lux Data Observability Platform</span>
            <span>•</span>
            <span className="text-lux-400 font-mono">v0.1.0</span>
          </div>
          <div>
            <span>Deterministic Quality Engine & Dependency Lineage</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
