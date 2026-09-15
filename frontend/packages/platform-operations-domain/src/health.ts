import type { OperationalState, ServiceHealth } from "../../operations-contracts/src";
const severity: Readonly<Record<OperationalState, number>> = {
  healthy: 0,
  recovering: 1,
  stale: 2,
  degraded: 3,
  unknown: 4,
  unavailable: 5,
};
export function aggregateServiceState(services: readonly ServiceHealth[]): OperationalState {
  if (!services.length) return "unknown";
  return services.reduce<OperationalState>(
    (worst, service) => (severity[service.state] > severity[worst] ? service.state : worst),
    "healthy",
  );
}
export function boundedDependencies(service: ServiceHealth, ceiling = 12): readonly string[] {
  return [...new Set(service.dependencyRefs)].sort().slice(0, Math.max(0, ceiling));
}
