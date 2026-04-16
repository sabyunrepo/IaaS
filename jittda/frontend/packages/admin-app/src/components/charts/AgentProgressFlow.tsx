import { useMemo } from 'react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type AgentNodeStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface AgentNode {
  id: string;
  name: string;
  status: AgentNodeStatus;
  children?: string[];
}

export interface AgentProgressFlowProps {
  nodes: AgentNode[];
}

// ---------------------------------------------------------------------------
// Status styling
// ---------------------------------------------------------------------------

const STATUS_STYLES: Record<
  AgentNodeStatus,
  { bg: string; border: string; text: string; ring: string }
> = {
  pending: {
    bg: 'bg-gray-100',
    border: 'border-gray-300',
    text: 'text-gray-500',
    ring: '',
  },
  running: {
    bg: 'bg-blue-50',
    border: 'border-blue-400',
    text: 'text-blue-700',
    ring: 'ring-2 ring-blue-300 ring-offset-1 animate-pulse',
  },
  completed: {
    bg: 'bg-emerald-50',
    border: 'border-emerald-400',
    text: 'text-emerald-700',
    ring: '',
  },
  failed: {
    bg: 'bg-red-50',
    border: 'border-red-400',
    text: 'text-red-700',
    ring: '',
  },
};

const STATUS_ICONS: Record<AgentNodeStatus, string> = {
  pending: '\u25CB',    // ○
  running: '\u25C9',    // ◉
  completed: '\u2713',  // ✓
  failed: '\u2717',     // ✗
};

const STATUS_LABELS: Record<AgentNodeStatus, string> = {
  pending: '대기 중',
  running: '실행 중',
  completed: '완료',
  failed: '실패',
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

interface LayoutNode extends AgentNode {
  depth: number;
  childNodes: LayoutNode[];
}

function buildTree(nodes: AgentNode[]): LayoutNode[] {
  const nodeMap = new Map<string, AgentNode>();
  for (const node of nodes) {
    nodeMap.set(node.id, node);
  }

  // Find root nodes (not referenced as children of any other node)
  const childIds = new Set<string>();
  for (const node of nodes) {
    if (node.children) {
      for (const childId of node.children) {
        childIds.add(childId);
      }
    }
  }

  const roots = nodes.filter((n) => !childIds.has(n.id));

  function buildLayoutNode(node: AgentNode, depth: number): LayoutNode {
    const childNodes: LayoutNode[] = [];
    if (node.children) {
      for (const childId of node.children) {
        const child = nodeMap.get(childId);
        if (child) {
          childNodes.push(buildLayoutNode(child, depth + 1));
        }
      }
    }
    return { ...node, depth, childNodes };
  }

  return roots.map((r) => buildLayoutNode(r, 0));
}

// ---------------------------------------------------------------------------
// Node component
// ---------------------------------------------------------------------------

function FlowNode({ node }: { node: LayoutNode }) {
  const style = STATUS_STYLES[node.status];
  const icon = STATUS_ICONS[node.status];

  return (
    <div className="flex flex-col items-start">
      {/* Node box */}
      <div
        className={`
          flex items-center gap-2 px-3 py-2 rounded-lg border
          ${style.bg} ${style.border} ${style.ring}
          transition-all duration-300
        `}
      >
        <span className={`text-sm font-bold ${style.text}`}>{icon}</span>
        <div>
          <p className={`text-sm font-medium ${style.text}`}>{node.name}</p>
          <p className="text-xs text-[--color-text-tertiary]">
            {STATUS_LABELS[node.status]}
          </p>
        </div>
      </div>

      {/* Children */}
      {node.childNodes.length > 0 && (
        <div className="ml-4 mt-1 pl-4 border-l-2 border-gray-200 space-y-1">
          {node.childNodes.map((child) => (
            <div key={child.id} className="relative">
              {/* Connector horizontal line */}
              <div className="absolute -left-4 top-4 w-4 h-px bg-gray-300" />
              <FlowNode node={child} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function AgentProgressFlow({ nodes }: AgentProgressFlowProps) {
  const tree = useMemo(() => buildTree(nodes), [nodes]);

  // Summary counts
  const counts = useMemo(() => {
    const result = { pending: 0, running: 0, completed: 0, failed: 0 };
    for (const node of nodes) {
      result[node.status]++;
    }
    return result;
  }, [nodes]);

  const total = nodes.length;
  const progressPct = total > 0 ? Math.round((counts.completed / total) * 100) : 0;

  return (
    <div className="space-y-4">
      {/* Progress bar */}
      <div className="flex items-center gap-3">
        <div className="flex-1 bg-gray-200 rounded-full h-2 overflow-hidden">
          <div
            className="bg-blue-500 h-full rounded-full transition-all duration-500"
            style={{ width: `${progressPct}%` }}
          />
        </div>
        <span className="text-sm font-medium text-[--color-text-secondary] whitespace-nowrap">
          {progressPct}%
        </span>
      </div>

      {/* Status summary badges */}
      <div className="flex gap-3 flex-wrap">
        {(Object.keys(STATUS_LABELS) as AgentNodeStatus[]).map((status) => {
          if (counts[status] === 0) return null;
          const style = STATUS_STYLES[status];
          return (
            <span
              key={status}
              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${style.bg} ${style.text} border ${style.border}`}
            >
              {STATUS_ICONS[status]} {STATUS_LABELS[status]}: {counts[status]}
            </span>
          );
        })}
      </div>

      {/* Node tree */}
      <div className="space-y-2">
        {tree.map((rootNode) => (
          <FlowNode key={rootNode.id} node={rootNode} />
        ))}
      </div>
    </div>
  );
}
