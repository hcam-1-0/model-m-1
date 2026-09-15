export const p56Workloads = Object.freeze({
  C1: { organizations: 1, departments: 2, users: 10, services: 10, queues: 4, changeRequests: 8 },
  C10: {
    organizations: 1,
    departments: 10,
    users: 100,
    services: 50,
    queues: 20,
    changeRequests: 100,
  },
  C50: {
    organizations: 5,
    departments: 50,
    users: 500,
    services: 200,
    queues: 100,
    changeRequests: 500,
  },
} as const);
export type P56Workload = keyof typeof p56Workloads;
export function workloadTotals(workload: P56Workload) {
  const value = p56Workloads[workload];
  return {
    workload,
    totalSubjects: value.organizations + value.departments + value.users,
    totalOperationalRecords: value.services + value.queues + value.changeRequests,
    functionalOnly: true,
    hardwareClaim: false,
    productionClaim: false,
  } as const;
}
