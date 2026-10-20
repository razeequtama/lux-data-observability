import React, { useState } from 'react';
import {
  Layers,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  GitFork,
  Target,
  Clock,
  FileText,
  RefreshCw,
  Database,
  ExternalLink,
} from 'lucide-react';

type NavigationTab =
  | 'validations'
  | 'lineage'
  | 'impact'
  | 'pipelines'
  | 'investigation'
  | 'recovery';

interface TabDefinition {
  id: NavigationTab;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
}

const TABS: TabDefinition[] = [
  {
    id: 'validations',
    label: 'Validations',
    icon: ShieldCheck,
    description: 'Deterministic quality rule evaluation and findings inspector',
  },
  {
    id: 'lineage',
    label: 'Lineage',
    icon: GitFork,
    description: 'Interactive Directed Acyclic Graph (DAG) dependency visualization',
  },
  {
    id: 'impact',
    label: 'Impact Analysis',
    icon: Target,
    description: 'Downstream blast radius calculation and affected consumer tracing',
  },
  {
    id: 'pipelines',
    label: 'Pipelines',
    icon: Clock,
    description: 'Pipeline execution logs, run history, and partition freshness monitoring',
  },
  {
    id: 'investigation',
    label: 'Investigation',
    icon: FileText,
    description: 'Unified incident workspace and reproducible HTML/JSON report generation',
  },
  {
    id: 'recovery',
    label: 'Recovery',
    icon: RefreshCw,
    description: 'Before vs after verification and resolution evidence comparison',
  },
];

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavigationTab>('validations');
  const activeTabDef = TABS.find((tab) => tab.id === activeTab) || TABS[0];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-lux-700 selection:text-white">
      {/* Top Header / App Shell */}
      <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo and Brand */}
            <div className="flex items-center space-x-3">
              <div
                className="w-10 h-10 rounded-lg bg-lux-700 flex items-center justify-center shadow-lg shadow-lux-700/20 text-white"
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

            {/* Scenario Badge & Dual-Health Dimension Indicator */}
            <div className="flex items-center space-x-4">
              {/* Active Scenario Selector / Indicator */}
              <div className="hidden md:flex items-center space-x-2 px-3 py-1.5 rounded-md bg-slate-800/80 border border-slate-700 text-xs">
                <Database className="w-3.5 h-3.5 text-lux-400" />
                <span className="text-slate-400 font-medium">Scenario:</span>
                <span className="text-slate-200 font-mono font-semibold" data-testid="active-scenario">
                  Monday Revenue Mystery
                </span>
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
                  <span className="inline-flex items-center space-x-1 font-semibold text-status-corrupted">
                    <AlertTriangle className="w-3.5 h-3.5 text-status-corrupted" />
                    <span>CORRUPTED</span>
                  </span>
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
              {TABS.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    role="tab"
                    id={`tab-${tab.id}`}
                    aria-controls={`panel-${tab.id}`}
                    aria-selected={isActive}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center space-x-2 px-3.5 py-2 rounded-md text-sm font-medium transition-colors whitespace-nowrap ${
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

      {/* Main Workspace Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
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

          {/* Tab Specific Content Shell */}
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
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 bg-slate-900/60 py-4 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-400 space-y-2 sm:space-y-0">
          <div className="flex items-center space-x-2">
            <span className="w-2 h-2 rounded-full bg-status-healthy"></span>
            <span>Frontend Scaffolding Active</span>
            <span>&bull;</span>
            <span>Lux Purple Theme System</span>
          </div>
          <div className="flex items-center space-x-4">
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
              className="hover:text-lux-300 transition-colors inline-flex items-center space-x-1"
            >
              <span>Backend API Docs</span>
              <ExternalLink className="w-3 h-3" />
            </a>
            <span>&bull;</span>
            <span className="font-mono text-slate-400">Node v22 / Vite / React 18</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
