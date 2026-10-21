import React from 'react';
import {
  Layers,
  CheckCircle2,
  AlertTriangle,
  Upload,
  Database,
} from 'lucide-react';
import { FixtureVersion, NavigationTab, ScenarioSummary } from '../../types';
import { NAVIGATION_TABS } from '../../constants/navigation';
import { ScenarioSwitcher } from '../scenario/ScenarioSwitcher';

interface AppHeaderProps {
  activeTab: NavigationTab;
  onTabChange: (tab: NavigationTab) => void;
  scenarios: ScenarioSummary[];
  activeScenarioId: string;
  activeFixtureVersion: FixtureVersion;
  isLoadingScenario: boolean;
  onSelectScenario: (scenarioId: string) => void;
  onSelectFixtureVersion: (version: FixtureVersion) => void;
  onLoadScenario: (scenarioId: string, version: FixtureVersion) => void;
  onOpenUpload: () => void;
  datasetsCount: number;
  isDatasetInspectorOpen: boolean;
  onToggleDatasetInspector: () => void;
}

export const AppHeader: React.FC<AppHeaderProps> = ({
  activeTab,
  onTabChange,
  scenarios,
  activeScenarioId,
  activeFixtureVersion,
  isLoadingScenario,
  onSelectScenario,
  onSelectFixtureVersion,
  onLoadScenario,
  onOpenUpload,
  datasetsCount,
  isDatasetInspectorOpen,
  onToggleDatasetInspector,
}) => {
  const activeScenario = scenarios.find((s) => s.id === activeScenarioId);
  const scenarioDisplayName = activeScenario?.name || 'Monday Revenue Mystery';

  return (
    <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-40">
      {/* Top Banner Row */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between py-3 gap-3">
          {/* Left: Logo & Branding */}
          <div className="flex items-center space-x-3">
            <div
              className="w-10 h-10 rounded-lg bg-lux-700 flex items-center justify-center shadow-lg shadow-lux-700/20 text-white shrink-0"
              data-testid="lux-logo"
              aria-label="Lux Data Observability Logo"
            >
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg text-white tracking-tight">Lux</span>
                <span className="text-xs px-2 py-0.5 rounded font-mono font-medium bg-lux-900/80 text-lux-200 border border-lux-700/50">
                  v0.1.0
                </span>
              </div>
              <p className="text-xs text-slate-400">Data Observability Platform</p>
            </div>
          </div>

          {/* Center / Right: Scenario Switcher & Controls */}
          <div className="flex flex-wrap items-center gap-3">
            <ScenarioSwitcher
              scenarios={scenarios}
              activeScenarioId={activeScenarioId}
              activeFixtureVersion={activeFixtureVersion}
              isLoading={isLoadingScenario}
              onSelectScenario={onSelectScenario}
              onSelectFixtureVersion={onSelectFixtureVersion}
              onLoadScenario={onLoadScenario}
            />

            {/* Active Scenario Badge */}
            <div className="hidden md:flex items-center space-x-2 px-3 py-1.5 rounded-md bg-slate-800/80 border border-slate-700 text-xs">
              <Database className="w-3.5 h-3.5 text-lux-400" />
              <span className="text-slate-400 font-medium">Scenario:</span>
              <span className="text-slate-200 font-mono font-semibold" data-testid="active-scenario">
                {scenarioDisplayName}
              </span>
            </div>

            {/* Dataset Inspector Drawer Toggle & Upload Buttons */}
            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={onToggleDatasetInspector}
                data-testid="toggle-dataset-inspector-btn"
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-medium border transition-colors cursor-pointer ${
                  isDatasetInspectorOpen
                    ? 'bg-lux-900/80 border-lux-600 text-lux-200'
                    : 'bg-slate-800 border-slate-700 text-slate-300 hover:text-white hover:bg-slate-700'
                }`}
                title="Toggle Ingested Datasets Inspector"
              >
                <Database className="w-3.5 h-3.5 text-lux-400" />
                <span>Datasets</span>
                <span className="px-1.5 py-0.2 rounded-full font-mono text-[10px] bg-slate-900 text-slate-200 border border-slate-700">
                  {datasetsCount}
                </span>
              </button>

              <button
                type="button"
                onClick={onOpenUpload}
                data-testid="header-upload-btn"
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition-colors cursor-pointer"
                title="Upload Custom CSV/JSON Dataset"
              >
                <Upload className="w-3.5 h-3.5 text-lux-400" />
                <span className="hidden sm:inline">Upload</span>
              </button>
            </div>

            {/* ADR-006 Dual Health Indicator: Compute vs Quality */}
            <div
              className="flex items-center space-x-2 text-xs"
              data-testid="dual-health-indicator"
              aria-label="System Health Status"
            >
              {/* Compute Health Badge */}
              <div
                className="flex items-center space-x-1.5 px-2.5 py-1 rounded bg-slate-800 border border-slate-700"
                title="Pipeline Compute Health"
              >
                <span className="text-slate-400">Compute:</span>
                <span className="inline-flex items-center space-x-1 font-semibold text-status-healthy">
                  <CheckCircle2 className="w-3.5 h-3.5 text-status-healthy" />
                  <span>SUCCESS</span>
                </span>
              </div>

              {/* Data Quality Health Badge */}
              <div
                className="flex items-center space-x-1.5 px-2.5 py-1 rounded bg-slate-800 border border-slate-700"
                title="Data Quality Health"
              >
                <span className="text-slate-400">Quality:</span>
                {activeFixtureVersion === 'corrected' ? (
                  <span className="inline-flex items-center space-x-1 font-semibold text-status-healthy">
                    <CheckCircle2 className="w-3.5 h-3.5 text-status-healthy" />
                    <span>HEALTHY</span>
                  </span>
                ) : (
                  <span className="inline-flex items-center space-x-1 font-semibold text-status-corrupted">
                    <AlertTriangle className="w-3.5 h-3.5 text-status-corrupted" />
                    <span>CORRUPTED</span>
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Semantic Navigation Tabs */}
      <nav
        className="border-t border-slate-800/70 bg-slate-900/60"
        aria-label="Observability Workspaces"
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div
            className="flex space-x-1 overflow-x-auto py-2 scrollbar-none"
            role="tablist"
            aria-label="Observability Workspaces"
          >
            {NAVIGATION_TABS.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  role="tab"
                  id={`tab-${tab.id}`}
                  aria-controls={`panel-${tab.id}`}
                  aria-selected={isActive}
                  onClick={() => onTabChange(tab.id)}
                  className={`flex items-center space-x-2 px-3.5 py-2 rounded-md text-sm font-medium transition-colors whitespace-nowrap cursor-pointer ${
                    isActive
                      ? 'bg-lux-700 text-white shadow-sm shadow-lux-700/30'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      </nav>
    </header>
  );
};
