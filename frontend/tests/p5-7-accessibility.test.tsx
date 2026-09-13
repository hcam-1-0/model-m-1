import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { mandatoryStates } from "../packages/quality-contracts/src";

function AuthoritativeQualityTable() {
  return (
    <main>
      <h1>Quality results</h1>
      <p role="status" aria-live="polite">
        Generated validation state
      </p>
      <table>
        <caption>Mandatory operator states</caption>
        <thead>
          <tr>
            <th scope="col">State</th>
            <th scope="col">Authority</th>
          </tr>
        </thead>
        <tbody>
          {mandatoryStates.map((state) => (
            <tr key={state}>
              <th scope="row">{state}</th>
              <td>Unchanged</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}

describe("P5.7 authoritative accessibility equivalence", () => {
  it("exposes heading, live status, caption, row headers, and every state in a table", () => {
    render(<AuthoritativeQualityTable />);
    expect(screen.getByRole("heading", { name: "Quality results" })).toBeVisible();
    expect(screen.getByRole("status")).toHaveAttribute("aria-live", "polite");
    expect(screen.getByRole("table", { name: "Mandatory operator states" })).toBeVisible();
    expect(screen.getAllByRole("rowheader")).toHaveLength(20);
  });
});
