import type { ChangeRequest } from "../../../../packages/admin-contracts/src";
export function ApprovalTimeline({ request }: { readonly request: ChangeRequest }) {
  const steps = ["Draft", "Submitted", "Independent review", "Approved projection"];
  const current =
    request.status === "draft"
      ? 0
      : request.status === "submitted"
        ? 1
        : request.status === "independent_review"
          ? 2
          : 3;
  return (
    <ol className="approval-timeline" aria-label="Approval chronology">
      {steps.map((step, index) => (
        <li key={step} className={index <= current ? "complete" : "pending"}>
          <span>{index + 1}</span>
          <div>
            <strong>{step}</strong>
            <small>
              {index < current
                ? "Recorded"
                : index === current
                  ? request.status.replaceAll("_", " ")
                  : "Pending"}
            </small>
          </div>
        </li>
      ))}
    </ol>
  );
}
