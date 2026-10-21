import React from 'react';
import {
  ShieldCheck,
  GitFork,
  Target,
  Clock,
  FileText,
  RefreshCw,
} from 'lucide-react';
import { NavigationTab } from '../types';

export interface TabDefinition {
  id: NavigationTab;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
}

export const NAVIGATION_TABS: TabDefinition[] = [
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

