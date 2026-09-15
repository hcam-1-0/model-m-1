export const investigationWorkloads = Object.freeze({
  C1: {
    investigations: 1,
    timelineEntriesPerInvestigation: 20,
    evidenceReferencesPerInvestigation: 4,
    graphNodes: 12,
    graphEdges: 24,
  },
  C10: {
    investigations: 10,
    timelineEntriesPerInvestigation: 100,
    evidenceReferencesPerInvestigation: 20,
    graphNodes: 50,
    graphEdges: 100,
  },
  C50: {
    investigations: 50,
    timelineEntriesPerInvestigation: 200,
    evidenceReferencesPerInvestigation: 40,
    graphNodes: 100,
    graphEdges: 200,
  },
});
export type InvestigationWorkload = keyof typeof investigationWorkloads;
export function workloadFor(name: InvestigationWorkload) {
  return investigationWorkloads[name];
}
