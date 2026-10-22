import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  ReactFlow,
  Controls,
  MiniMap,
  Background,
  useNodesState,
  useEdgesState,
  Node,
  Edge,
  MarkerType,
  NodeTypes,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import {
  Search,
  Filter,
  RotateCcw,
  AlertTriangle,
  Info,
} from 'lucide-react';
import clsx from 'clsx';
import { CustomNode, CustomNodeData } from './CustomNode';
import { LineageLegend } from './LineageLegend';
import { NodeDetailsPanel } from './NodeDetailsPanel';
import {
  getLineageGraph,
  getLineageNodeDetail,
  traceDownstreamImpact,
} from '../../api/lineage';
import {
  AssetImpactStatus,
  BlastRadiusReport,
  LineageGraphResponse,
  LineageNodeDetail,
} from '../../types';

export interface LineageViewProps {
  scenarioId?: string;
  lastReloadKey?: number | string;
  initialSelectedNodeId?: string | null;
  initialTargetFinding?: {
    id: string;
    rule_id: string;
    rule_name: string;
    dataset_id: string;
  } | null;
  onSelectNode?: (nodeId: string) => void;
}

const nodeTypes: NodeTypes = {
  custom: CustomNode,
  SOURCE_DATASET: CustomNode,
  TRANSFORMATION: CustomNode,
  DERIVED_DATASET: CustomNode,
  METRIC: CustomNode,
  REPORT: CustomNode,
};

export const LineageView: React.FC<LineageViewProps> = ({
  scenarioId = 'monday_revenue_mystery',
  lastReloadKey,
  initialSelectedNodeId = null,
  initialTargetFinding = null,
  onSelectNode,
}) => {
  const [graphData, setGraphData] = useState<LineageGraphResponse | null>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState<Node<CustomNodeData>>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  // Selection & Details State
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [selectedNodeDetail, setSelectedNodeDetail] = useState<LineageNodeDetail | null>(null);
  const [blastRadius, setBlastRadius] = useState<BlastRadiusReport | null>(null);

  // Filters & Toolbar
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState<string>('ALL');
  const [isLegendOpen, setIsLegendOpen] = useState(false);

  // Loading & Error States
  const [isLoading, setIsLoading] = useState(true);
  const [isDetailLoading, setIsDetailLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initial Data Fetching
  const loadGraph = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getLineageGraph(scenarioId);
      setGraphData(data);

      const initialNodes: Node<CustomNodeData>[] = data.nodes.map((n) => ({
        id: n.id,
        type: 'custom',
        position: { x: n.position.x, y: n.position.y },
        data: {
          id: n.id,
          label: n.name,
          name: n.name,
          type: n.type,
          dataset_id: n.dataset_id,
          execution_status: n.execution_status || 'COMPLETED_SUCCESS',
          quality_health: n.quality_health || 'HEALTHY',
          owner: n.owner,
          description: n.description,
          metadata: n.metadata,
          impactStatus: null,
          isHighlighted: false,
          isDimmed: false,
          isSelected: false,
        },
      }));

      const initialEdges: Edge[] = data.edges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        type: 'smoothstep',
        animated: e.animated ?? false,
        style: { stroke: '#475569', strokeWidth: 1.5 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 14,
          height: 14,
          color: '#475569',
        },
      }));

      setNodes(initialNodes);
      setEdges(initialEdges);
    } catch (err) {
      console.error('Failed to load lineage graph:', err);
      setError(err instanceof Error ? err.message : 'Failed to load lineage DAG');
    } finally {
      setIsLoading(false);
    }
  }, [scenarioId, setNodes, setEdges]);

  useEffect(() => {
    loadGraph();
  }, [loadGraph, lastReloadKey]);

  // Execute blast radius trace and highlight downstream paths
  const selectAndTraceNode = useCallback(
    async (nodeId: string) => {
      setSelectedNodeId(nodeId);
      if (onSelectNode) onSelectNode(nodeId);

      setIsDetailLoading(true);
      try {
        // Fetch detailed node info and downstream blast radius concurrently
        const [detailRes, impactRes] = await Promise.allSettled([
          getLineageNodeDetail(nodeId, scenarioId),
          traceDownstreamImpact({
            scenario_id: scenarioId,
            target_type: 'NODE',
            target_id: nodeId,
            include_transformations: true,
            include_root: true,
          }),
        ]);

        if (detailRes.status === 'fulfilled') {
          setSelectedNodeDetail(detailRes.value);
        }

        const blastReport =
          impactRes.status === 'fulfilled' ? impactRes.value : null;
        setBlastRadius(blastReport);

        // Compute affected node set & impact statuses
        const affectedMap = new Map<string, AssetImpactStatus>();
        const affectedNodeIds = new Set<string>();

        if (blastReport) {
          for (const asset of blastReport.affected_assets) {
            affectedMap.set(asset.node_id, asset.impact_status);
            affectedNodeIds.add(asset.node_id);
          }
        }
        affectedNodeIds.add(nodeId);

        // Update nodes with highlighting, impact status, and dimming
        setNodes((prevNodes) =>
          prevNodes.map((n) => {
            const isTarget = n.id === nodeId;
            const isAffected = affectedNodeIds.has(n.id);
            const impactStatus = affectedMap.get(n.id) || (isTarget ? 'CONFIRMED_FAILED' : null);

            return {
              ...n,
              data: {
                ...n.data,
                isSelected: isTarget,
                impactStatus: impactStatus,
                isHighlighted: isAffected,
                isDimmed: !isAffected,
              },
            };
          })
        );

        // Highlight affected edges in the downstream blast radius
        setEdges((prevEdges) =>
          prevEdges.map((edge) => {
            const isDownstreamEdge =
              affectedNodeIds.has(edge.source) && affectedNodeIds.has(edge.target);

            if (isDownstreamEdge) {
              return {
                ...edge,
                animated: true,
                style: { stroke: '#F43F5E', strokeWidth: 2.5 },
                markerEnd: {
                  type: MarkerType.ArrowClosed,
                  width: 16,
                  height: 16,
                  color: '#F43F5E',
                },
              };
            }

            return {
              ...edge,
              animated: false,
              style: { stroke: '#334155', strokeWidth: 1, opacity: 0.25 },
              markerEnd: {
                type: MarkerType.ArrowClosed,
                width: 12,
                height: 12,
                color: '#334155',
              },
            };
          })
        );
      } catch (err) {
        console.error('Error tracing impact for node:', err);
      } finally {
        setIsDetailLoading(false);
      }
    },
    [scenarioId, onSelectNode, setNodes, setEdges]
  );

  // Clear selection and restore default DAG appearance
  const handleResetHighlight = useCallback(() => {
    setSelectedNodeId(null);
    setSelectedNodeDetail(null);
    setBlastRadius(null);

    setNodes((prevNodes) =>
      prevNodes.map((n) => ({
        ...n,
        data: {
          ...n.data,
          isSelected: false,
          impactStatus: null,
          isHighlighted: false,
          isDimmed: false,
        },
      }))
    );

    setEdges((prevEdges) =>
      prevEdges.map((edge) => ({
        ...edge,
        animated: false,
        style: { stroke: '#475569', strokeWidth: 1.5, opacity: 1 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 14,
          height: 14,
          color: '#475569',
        },
      }))
    );
  }, [setNodes, setEdges]);

  // Handle external initial targets (from validations or initial props)
  useEffect(() => {
    if (graphData && graphData.nodes.length > 0) {
      if (initialSelectedNodeId) {
        selectAndTraceNode(initialSelectedNodeId);
      } else if (initialTargetFinding) {
        // Resolve finding dataset to source node
        const targetNode = graphData.nodes.find(
          (n) => n.dataset_id === initialTargetFinding.dataset_id || n.id === initialTargetFinding.dataset_id
        );
        if (targetNode) {
          selectAndTraceNode(targetNode.id);
        }
      }
    }
  }, [graphData, initialSelectedNodeId, initialTargetFinding, selectAndTraceNode]);

  // Handle user clicking on a node
  const handleNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      selectAndTraceNode(node.id);
    },
    [selectAndTraceNode]
  );

  // Handle pane click (clear selection)
  const handlePaneClick = useCallback(() => {
    handleResetHighlight();
  }, [handleResetHighlight]);

  // Filter nodes according to search and asset type
  const displayedNodes = useMemo(() => {
    return nodes.map((node) => {
      const matchesSearch =
        searchQuery.trim() === '' ||
        node.data.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
        node.id.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesType =
        selectedType === 'ALL' || node.data.type === selectedType;

      const shouldHide = !matchesSearch || !matchesType;

      return {
        ...node,
        hidden: shouldHide,
      };
    });
  }, [nodes, searchQuery, selectedType]);

  // MiniMap node color logic
  const getNodeColor = useCallback((node: Node) => {
    const data = node.data as CustomNodeData;
    if (data.impactStatus === 'CONFIRMED_FAILED') return '#F43F5E';
    if (data.impactStatus === 'DIRECTLY_AFFECTED') return '#F59E0B';
    if (data.impactStatus === 'POTENTIALLY_AFFECTED') return '#7C3AED';

    switch (data.type) {
      case 'SOURCE_DATASET':
        return '#3B82F6';
      case 'TRANSFORMATION':
        return '#F59E0B';
      case 'DERIVED_DATASET':
        return '#6366F1';
      case 'METRIC':
        return '#10B981';
      case 'REPORT':
        return '#D946EF';
      default:
        return '#64748B';
    }
  }, []);

  if (isLoading) {
    return (
      <div
        data-testid="lineage-loading"
        className="w-full h-[650px] bg-slate-950 border border-slate-800 rounded-2xl flex flex-col items-center justify-center space-y-3"
      >
        <div className="w-10 h-10 border-2 border-lux-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-sm text-slate-400 font-mono">
          Loading Directed Acyclic Graph & Computing Dagre Coordinates...
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div
        data-testid="lineage-error"
        className="w-full h-[400px] bg-slate-950 border border-rose-900/50 rounded-2xl p-8 flex flex-col items-center justify-center text-center space-y-4"
      >
        <div className="w-12 h-12 rounded-full bg-rose-950/80 border border-rose-700/60 flex items-center justify-center text-rose-400">
          <AlertTriangle className="w-6 h-6" />
        </div>
        <h3 className="text-lg font-bold text-white">Failed to Load Lineage DAG</h3>
        <p className="text-sm text-slate-400 max-w-md">{error}</p>
        <button
          type="button"
          onClick={loadGraph}
          className="px-4 py-2 rounded-lg bg-lux-700 hover:bg-lux-600 text-white text-xs font-semibold"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  return (
    <div
      data-testid="lineage-dag-container"
      className="w-full h-[750px] bg-slate-950 border border-slate-800 rounded-2xl overflow-hidden relative flex flex-col shadow-2xl"
    >
      {/* Top Toolbar */}
      <div className="bg-slate-900/90 border-b border-slate-800 px-4 py-3 flex flex-wrap items-center justify-between gap-3 z-10 backdrop-blur">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-xs font-bold text-white tracking-wide">
              Lineage DAG Visualizer
            </span>
          </div>

          <div className="hidden sm:flex items-center space-x-2 text-[11px] font-mono text-slate-400 border-l border-slate-700/80 pl-3">
            <span>{graphData?.nodes.length || 0} Nodes</span>
            <span>•</span>
            <span>{graphData?.edges.length || 0} Directed Edges</span>
          </div>
        </div>

        {/* Filter Controls & Search */}
        <div className="flex items-center space-x-2 flex-wrap">
          {/* Search Box */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
            <input
              type="text"
              aria-label="Search DAG nodes"
              placeholder="Search nodes..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 pr-3 py-1.5 text-xs bg-slate-800 border border-slate-700 rounded-lg text-slate-200 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-lux-500 w-36 sm:w-44"
            />
          </div>

          {/* Node Type Filter */}
          <div className="flex items-center space-x-1">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <select
              aria-label="Filter by asset type"
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="py-1.5 px-2 text-xs bg-slate-800 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:ring-1 focus:ring-lux-500 font-sans"
            >
              <option value="ALL">All Types (5)</option>
              <option value="SOURCE_DATASET">Source Datasets</option>
              <option value="TRANSFORMATION">Transformations</option>
              <option value="DERIVED_DATASET">Derived Tables</option>
              <option value="METRIC">Metrics & KPIs</option>
              <option value="REPORT">Reports & Dashboards</option>
            </select>
          </div>

          {/* Reset / Clear Button */}
          {selectedNodeId && (
            <button
              type="button"
              onClick={handleResetHighlight}
              className="flex items-center space-x-1.5 py-1.5 px-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs border border-slate-700 transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reset Highlight</span>
            </button>
          )}

          {/* Legend Toggle Button */}
          <button
            type="button"
            onClick={() => setIsLegendOpen((prev) => !prev)}
            className={clsx(
              'flex items-center space-x-1.5 py-1.5 px-2.5 rounded-lg text-xs border transition-colors',
              isLegendOpen
                ? 'bg-lux-700 text-white border-lux-600'
                : 'bg-slate-800 hover:bg-slate-700 text-slate-300 border-slate-700'
            )}
          >
            <Info className="w-3.5 h-3.5" />
            <span>Legend</span>
          </button>
        </div>
      </div>

      {/* Main Canvas & Inspector Layout */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* React Flow Canvas */}
        <div className="flex-1 h-full w-full relative">
          <ReactFlow
            nodes={displayedNodes}
            edges={edges}
            nodeTypes={nodeTypes}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={handleNodeClick}
            onPaneClick={handlePaneClick}
            fitView
            minZoom={0.2}
            maxZoom={1.8}
            defaultViewport={{ x: 0, y: 0, zoom: 0.85 }}
            proOptions={{ hideAttribution: true }}
            aria-label="Lineage DAG Canvas"
          >
            {/* Dark background grid */}
            <Background color="#334155" gap={24} size={1} />

            {/* Navigation & Zoom Controls */}
            <Controls
              showInteractive={false}
              className="!bg-slate-900/90 !border !border-slate-800 !rounded-xl !overflow-hidden !shadow-xl !fill-slate-300"
            />

            {/* MiniMap */}
            <MiniMap
              nodeColor={getNodeColor}
              nodeStrokeWidth={2}
              zoomable
              pannable
              className="!bg-slate-950/90 !border !border-slate-800 !rounded-xl !overflow-hidden !shadow-2xl"
            />
          </ReactFlow>

          {/* Collapsible Lineage Legend Panel */}
          {isLegendOpen && (
            <div className="absolute bottom-4 left-4 max-w-xl z-20">
              <LineageLegend />
            </div>
          )}
        </div>

        {/* Selected Node Details & Blast Radius Side Panel */}
        {selectedNodeDetail && (
          <NodeDetailsPanel
            nodeDetail={selectedNodeDetail}
            blastRadius={blastRadius}
            isLoading={isDetailLoading}
            onClose={handleResetHighlight}
            onSelectNode={(nodeId) => selectAndTraceNode(nodeId)}
          />
        )}
      </div>
    </div>
  );
};
