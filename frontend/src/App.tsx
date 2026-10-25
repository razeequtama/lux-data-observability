import React, { useState, useEffect, useCallback } from 'react';
import { AppHeader } from './components/common/AppHeader';
import { NAVIGATION_TABS } from './constants/navigation';
import { AlertBanner, AlertType } from './components/common/AlertBanner';
import { DatasetInspector } from './components/dataset/DatasetInspector';
import { DatasetPreviewModal } from './components/dataset/DatasetPreviewModal';
import { UploadModal } from './components/dataset/UploadModal';
import { ValidationView } from './components/validation/ValidationView';
import { LineageView } from './components/lineage/LineageView';
import { ImpactAnalysisView } from './components/impact';
import { PipelineObservabilityView } from './components/pipeline';
import { InvestigationWorkspace } from './components/reports';
import { RecoveryDiffView } from './components/recovery';
import { WelcomeModal } from './components/common/WelcomeModal';
import { GuideModal } from './components/common/GuideModal';
import { Language } from './i18n/translations';
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
  const [scenarioReloadCounter, setScenarioReloadCounter] = useState(0);

  // UI state
  const [language, setLanguage] = useState<Language>('en');
  const [isWelcomeModalOpen, setIsWelcomeModalOpen] = useState<boolean>(true);
  const [isGuideModalOpen, setIsGuideModalOpen] = useState<boolean>(false);
  const [isDatasetInspectorOpen, setIsDatasetInspectorOpen] = useState(false);
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
    setScenarioReloadCounter((prev) => prev + 1);
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
      setScenarioReloadCounter((prev) => prev + 1);
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
      setScenarioReloadCounter((prev) => prev + 1);
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
    <div className="min-h-screen bg-[#07080D] text-slate-100 flex flex-col font-sans relative selection:bg-purple-500/30 selection:text-purple-200 overflow-x-hidden">
      {/* Luminous Top Aurora / Light Cone */}
      <div
        className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-[450px] bg-[radial-gradient(ellipse_80%_50%_at_50%_-10%,rgba(139,92,246,0.18),rgba(99,102,241,0.06),transparent_70%)] pointer-events-none z-0"
        aria-hidden="true"
      />

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
        language={language}
        onLanguageChange={setLanguage}
        onOpenGuide={() => setIsGuideModalOpen(true)}
      />

      {/* Global Alert Banner */}
      {alert && (
        <div className="w-full px-6 sm:px-8 lg:px-10 pt-4 relative z-10">
          <AlertBanner
            type={alert.type}
            message={alert.message}
            details={alert.details}
            onClose={() => setAlert(null)}
          />
        </div>
      )}

      {/* Centered Dataset Inspector Modal */}
      {isDatasetInspectorOpen && (
        <div
          className="fixed inset-0 z-50 overflow-y-auto flex items-center justify-center p-4 sm:p-6 lg:p-10"
          role="dialog"
          aria-modal="true"
          aria-label="Scenario Datasets Inspector"
        >
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/80 backdrop-blur-md transition-opacity"
            onClick={() => setIsDatasetInspectorOpen(false)}
            aria-hidden="true"
            data-testid="dataset-inspector-backdrop"
          />

          {/* Centered Modal Card */}
          <div className="relative w-full max-w-5xl max-h-[90vh] flex flex-col z-10 animate-in fade-in zoom-in-95 duration-200">
            <DatasetInspector
              datasets={datasets}
              isLoading={isLoadingDatasets}
              isUnloading={isUnloadingScenario}
              onPreviewDataset={(dataset) => setPreviewingDataset(dataset)}
              onOpenUpload={() => setIsUploadModalOpen(true)}
              onRefresh={() => fetchDatasets(activeScenarioId)}
              onUnloadScenario={() => handleUnloadScenario(activeScenarioId)}
              onClose={() => setIsDatasetInspectorOpen(false)}
            />
          </div>
        </div>
      )}

      {/* Main Workspace Area */}
      <main className="flex-1 w-full px-6 sm:px-8 lg:px-10 py-5 space-y-5 relative z-10">
        {/* Tab Panel */}
        <div
          role="tabpanel"
          id={`panel-${activeTab}`}
          aria-labelledby={`tab-${activeTab}`}
          className="space-y-4"
        >

          {activeTab === 'validations' ? (
            <ValidationView
              scenarioId={activeScenarioId}
              fixtureVersion={activeFixtureVersion}
              lastReloadKey={scenarioReloadCounter}
              availableDatasets={datasets.map((d) => d.id)}
              onTraceImpact={(finding) => {
                setSelectedFindingForImpact(finding);
                setSelectedLineageNodeId(null);
                setActiveTab('impact');
                setAlert({
                  type: 'info',
                  message: `Tracing Impact for ${finding.rule_id}`,
                  details: `Downstream impact analysis requested from "${finding.rule_name}" on dataset "${finding.dataset_id}". Highlighting blast radius in Lineage DAG.`,
                });
              }}
            />
          ) : activeTab === 'lineage' ? (
            <LineageView
              scenarioId={activeScenarioId}
              isScenarioLoaded={datasets.length > 0}
              lastReloadKey={scenarioReloadCounter}
              initialSelectedNodeId={selectedLineageNodeId}
              initialTargetFinding={selectedFindingForImpact}
              onSelectNode={(nodeId) => {
                setSelectedLineageNodeId(nodeId);
              }}
            />
          ) : activeTab === 'impact' ? (
            <ImpactAnalysisView
              scenarioId={activeScenarioId}
              isScenarioLoaded={datasets.length > 0}
              lastReloadKey={scenarioReloadCounter}
              initialTargetFinding={selectedFindingForImpact}
              initialTargetNodeId={selectedLineageNodeId}
              onNavigateToLineage={(nodeId) => {
                setSelectedLineageNodeId(nodeId || null);
                setActiveTab('lineage');
              }}
              onNavigateToValidations={() => {
                setActiveTab('validations');
              }}
            />
          ) : activeTab === 'pipelines' ? (
            <PipelineObservabilityView
              scenarioId={activeScenarioId}
              lastReloadKey={scenarioReloadCounter}
              onTraceImpact={() => {
                setSelectedLineageNodeId('src_orders');
                setSelectedFindingForImpact(null);
                setActiveTab('impact');
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
              lastReloadKey={scenarioReloadCounter}
              onNavigateToLineage={(nodeId) => {
                setSelectedLineageNodeId(nodeId || null);
                setActiveTab('lineage');
              }}
              onNavigateToValidations={() => {
                setActiveTab('validations');
              }}
            />
          ) : activeTab === 'recovery' ? (
            <RecoveryDiffView
              scenarioId={activeScenarioId}
              onNavigateToLineage={() => {
                setActiveTab('lineage');
                setSelectedFindingForImpact(null);
              }}
              onNavigateToValidations={() => {
                setActiveTab('validations');
              }}
              onRecoveryVerified={(comparison) => {
                setActiveFixtureVersion('corrected');
                fetchDatasets(activeScenarioId);
                fetchScenarios();
                setAlert({
                  type: 'success',
                  message: 'Recovery Verified Successfully',
                  details: `Scenario "${activeScenarioId}" successfully verified on corrected fixtures. All ${comparison.resolved_findings.length} findings resolved and downstream assets are healthy.`,
                });
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

      {/* Welcome Modal: Shown first to every visitor */}
      <WelcomeModal
        isOpen={isWelcomeModalOpen}
        onClose={() => setIsWelcomeModalOpen(false)}
        language={language}
        onLanguageChange={setLanguage}
      />

      {/* Guide Modal: Explains only how the tool works */}
      <GuideModal
        isOpen={isGuideModalOpen}
        onClose={() => setIsGuideModalOpen(false)}
        language={language}
        onLanguageChange={setLanguage}
      />

      {/* Footer */}
      <footer className="border-t border-white/[0.06] bg-[#07080D]/90 backdrop-blur-md py-4 mt-auto relative z-10">
        <div className="w-full px-6 sm:px-8 lg:px-10 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-400 space-y-2 sm:space-y-0">
          <div className="flex items-center space-x-2">
            <span className="text-slate-300 font-medium">Lux Data Observability Platform</span>
            <span className="text-slate-600">|</span>
            <span className="text-lux-400 font-mono font-semibold">v0.1.0</span>
          </div>
          <div className="flex items-center space-x-2 text-slate-400">
            <span>Deterministic Quality Engine & Dependency Lineage</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
