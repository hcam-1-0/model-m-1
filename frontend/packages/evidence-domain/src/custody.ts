import type { CustodyEvent, ProvenanceProjection } from "../../investigation-contracts/src";

export function orderCustodyEvents(events: readonly CustodyEvent[]): readonly CustodyEvent[] {
  return [...events].sort((left, right) => left.sequence - right.sequence).slice(0, 100);
}
export function custodyIsIndependent(
  events: readonly CustodyEvent[],
  provenance: ProvenanceProjection,
): boolean {
  return events.every((event) => {
    const runtimeEvent = event as unknown as Readonly<Record<string, unknown>>;
    return (
      event.evidenceRef === provenance.evidenceRef && runtimeEvent.inferredFromProvenance === false
    );
  });
}
