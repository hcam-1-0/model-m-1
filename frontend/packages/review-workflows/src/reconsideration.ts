export interface Reconsideration {
  readonly priorRevision: number;
  readonly currentRevision: number;
  readonly changedFields: readonly string[];
  readonly requiresExplicitConfirmation: true;
  readonly automaticRetry: false;
}
export function buildReconsideration(
  prior: Readonly<Record<string, unknown>>,
  current: Readonly<Record<string, unknown>>,
  priorRevision: number,
  currentRevision: number,
): Reconsideration {
  const fields = [...new Set([...Object.keys(prior), ...Object.keys(current)])]
    .filter((key) => JSON.stringify(prior[key]) !== JSON.stringify(current[key]))
    .sort();
  return {
    priorRevision,
    currentRevision,
    changedFields: fields,
    requiresExplicitConfirmation: true,
    automaticRetry: false,
  };
}
