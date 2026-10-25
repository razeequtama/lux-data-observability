import React from 'react';
import {
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
  isUnloadingScenario?: boolean;
  onSelectScenario: (scenarioId: string) => void;
  onSelectFixtureVersion: (version: FixtureVersion) => void;
  onLoadScenario: (scenarioId: string, version: FixtureVersion) => void;
  onUnloadScenario?: (scenarioId: string) => void;
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
  isUnloadingScenario = false,
  onSelectScenario,
  onSelectFixtureVersion,
  onLoadScenario,
  onUnloadScenario,
  onOpenUpload,
  datasetsCount,
  isDatasetInspectorOpen,
  onToggleDatasetInspector,
}) => {
  const activeScenario = scenarios.find((s) => s.id === activeScenarioId);
  const scenarioDisplayName = activeScenario?.name || 'Monday Revenue Mystery';
  const activeTabDef = NAVIGATION_TABS.find((t) => t.id === activeTab) || NAVIGATION_TABS[0];

  return (
    <header className="border-b border-white/[0.08] bg-[#08090E]/90 backdrop-blur-2xl sticky top-0 z-40 shadow-2xl shadow-black/50">
      {/* Top Command Bar Row */}
      <div className="w-full px-6 sm:px-8 lg:px-10">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between py-3.5 gap-4">
          {/* Left: Official Brand Logo & Subtitle */}
          <div className="flex items-center space-x-4 shrink-0">
            <div
              className="relative group flex items-center space-x-4 shrink-0"
              data-testid="lux-logo"
              aria-label="Lux Data Observability Logo"
            >
              {/* Smooth ambient purple glow behind the logo */}
              <div
                className="absolute -inset-3 bg-gradient-to-r from-purple-600/40 via-lux-500/35 to-indigo-600/30 rounded-3xl blur-2xl pointer-events-none group-hover:from-purple-600/55 group-hover:to-indigo-600/45 transition-all duration-300"
                aria-hidden="true"
              />

              <div className="relative z-10 flex items-center">
                <img
                  src="/logo_and_title.svg"
                  alt="Lux Logo"
                  className="h-16 sm:h-20 lg:h-22 w-auto object-contain filter drop-shadow-[0_0_20px_rgba(168,85,247,0.7)] transition-transform duration-200 group-hover:scale-105"
                />
              </div>

              {/* Screen reader only for 'Lux' text to prevent visual duplication with the logo SVG */}
              <span className="sr-only">Lux</span>

              <div className="relative z-10 flex flex-col justify-center space-y-1">
                <div className="flex items-center space-x-2">
                  <span className="text-xs px-2.5 py-0.5 rounded-md font-mono font-bold bg-lux-950/90 text-purple-200 border border-lux-500/60 shadow-[0_0_12px_rgba(168,85,247,0.4)]">
                    v0.1.0
                  </span>
                </div>
                <p className="text-xs sm:text-sm text-slate-300 font-bold tracking-wider uppercase whitespace-nowrap">
                  Data Observability Platform
                </p>
              </div>
            </div>
          </div>

          {/* Center / Right: Scenario Tools taking space all the way to the right of the screen */}
          <div className="flex-1 flex flex-wrap items-center justify-end gap-3 sm:gap-3.5">
            <ScenarioSwitcher
              scenarios={scenarios}
              activeScenarioId={activeScenarioId}
              activeFixtureVersion={activeFixtureVersion}
              isLoading={isLoadingScenario}
              isUnloading={isUnloadingScenario}
              onSelectScenario={onSelectScenario}
              onSelectFixtureVersion={onSelectFixtureVersion}
              onLoadScenario={onLoadScenario}
              onUnloadScenario={onUnloadScenario}
            />

            {/* Active Scenario Badge */}
            <div className="hidden xl:flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-slate-950/70 border border-white/[0.08] text-xs font-mono text-slate-300 shadow-inner">
              <span className="text-slate-500 font-medium">scenario:</span>
              <span data-testid="active-scenario" className="font-semibold text-purple-200">
                {scenarioDisplayName}
              </span>
            </div>

            {/* Dataset Inspector Drawer Toggle & Upload Buttons */}
            <div className="flex items-center space-x-2.5">
              <button
                type="button"
                onClick={onToggleDatasetInspector}
                data-testid="toggle-dataset-inspector-btn"
                className={`flex items-center justify-center space-x-3 px-6 py-3 min-w-[135px] rounded-xl text-xs sm:text-sm font-semibold tracking-wide border transition-all cursor-pointer shadow-sm whitespace-nowrap ${
                  isDatasetInspectorOpen
                    ? 'bg-lux-900/80 border-lux-500/70 text-lux-100 shadow-[0_0_16px_rgba(168,85,247,0.4)] ring-1 ring-purple-400/50'
                    : 'bg-slate-900/70 border-white/[0.08] text-slate-300 hover:text-white hover:bg-slate-800/80 hover:border-purple-400/40 hover:shadow-[0_0_14px_rgba(168,85,247,0.3)]'
                }`}
                title="Toggle Ingested Datasets Inspector Modal"
              >
                <Database className="w-4 h-4 text-lux-400 shrink-0" />
                <span>Datasets</span>
                <span className="px-2.5 py-0.5 rounded-full font-mono text-[11px] bg-slate-950 text-slate-200 border border-slate-700/80 ml-0.5">
                  {datasetsCount}
                </span>
              </button>

              <button
                type="button"
                onClick={onOpenUpload}
                data-testid="header-upload-btn"
                className="flex items-center justify-center space-x-2.5 px-6 py-3 min-w-[115px] rounded-xl text-xs sm:text-sm font-semibold tracking-wide bg-slate-900/70 hover:bg-slate-800/80 text-slate-300 hover:text-white border border-white/[0.08] hover:border-purple-400/40 hover:shadow-[0_0_14px_rgba(168,85,247,0.3)] transition-all cursor-pointer shadow-sm whitespace-nowrap"
                title="Upload Custom CSV/JSON Dataset"
              >
                <Upload className="w-4 h-4 text-lux-400 shrink-0" />
                <span className="hidden sm:inline">Upload</span>
              </button>
            </div>

            {/* ADR-006 Dual Health Indicator: Compute vs Quality */}
            <div
              className="flex items-center space-x-3 px-4 py-2.5 rounded-xl bg-slate-950/70 border border-white/[0.08] text-xs shadow-inner shrink-0"
              data-testid="dual-health-indicator"
              aria-label="System Health Status"
            >
              {/* Compute Health Badge */}
              <div
                className="flex items-center space-x-1.5"
                title="Pipeline Compute Health"
              >
                <span className="text-slate-400 font-medium">Compute:</span>
                <span className="inline-flex items-center space-x-1 font-bold text-status-healthy">
                  <CheckCircle2 className="w-3.5 h-3.5 text-status-healthy" />
                  <span>SUCCESS</span>
                </span>
              </div>

              <span className="text-white/20">|</span>

              {/* Data Quality Health Badge */}
              <div
                className="flex items-center space-x-1.5"
                title="Data Quality Health"
              >
                <span className="text-slate-400 font-medium">Quality:</span>
                {datasetsCount === 0 ? (
                  <span className="inline-flex items-center space-x-1 font-bold text-slate-400">
                    <span>NOT LOADED</span>
                  </span>
                ) : activeFixtureVersion === 'corrected' ? (
                  <span className="inline-flex items-center space-x-1 font-bold text-status-healthy">
                    <CheckCircle2 className="w-3.5 h-3.5 text-status-healthy" />
                    <span>HEALTHY</span>
                  </span>
                ) : (
                  <span className="inline-flex items-center space-x-1 font-bold text-status-corrupted">
                    <AlertTriangle className="w-3.5 h-3.5 text-status-corrupted" />
                    <span>CORRUPTED</span>
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Semantic Navigation Stepper Bar with Guided Thread */}
      <nav
        className="relative border-t border-white/[0.06] bg-[#0b0c16]/90 backdrop-blur-xl"
        aria-label="Observability Workspaces"
      >
        {/* Guided Optical Thread Line */}
        <div
          className="absolute top-1/2 left-0 right-0 -translate-y-1/2 h-[1px] bg-gradient-to-r from-transparent via-purple-500/20 to-transparent pointer-events-none hidden sm:block"
          aria-hidden="true"
        />

        <div className="w-full px-6 sm:px-8 lg:px-10 relative flex items-center justify-between">
          <div
            className="flex items-center flex-wrap gap-3 py-3 w-full"
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
                  className={`group relative flex items-center space-x-2.5 px-6 py-3 rounded-2xl text-xs sm:text-sm font-bold tracking-wide transition-all duration-200 whitespace-nowrap cursor-pointer ${
                    isActive
                      ? 'bg-gradient-to-r from-lux-700 via-lux-600 to-purple-600 text-white shadow-[0_0_24px_rgba(124,58,237,0.45)] ring-1 ring-purple-400/60'
                      : 'text-slate-400 hover:text-slate-100 hover:bg-white/[0.05] border border-transparent hover:border-white/[0.08]'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-400 group-hover:text-slate-200'}`} />
                  <span>{tab.label}</span>

                  {/* Downward Light Flare Under Active Step */}
                  {isActive && (
                    <>
                      <div
                        className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-14 h-[2px] bg-gradient-to-r from-transparent via-purple-400 to-transparent blur-[0.5px]"
                        aria-hidden="true"
                      />
                      <div
                        className="absolute -bottom-3 left-1/2 -translate-x-1/2 w-20 h-3 bg-purple-500/25 blur-md pointer-events-none"
                        aria-hidden="true"
                      />
                    </>
                  )}
                </button>
              );
            })}
          </div>

          {/* Accessible Active Step Heading & Description (Visually hidden to eliminate clutter while preserving test & a11y compatibility) */}
          <div className="sr-only">
            <h1>{activeTabDef.label}</h1>
            <p>{activeTabDef.description}</p>
          </div>
        </div>
      </nav>
    </header>
  );
};
