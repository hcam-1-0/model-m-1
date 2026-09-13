import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { FeaturesConfigurationPage } from "../apps/admin-center/src/pages/features-configuration-page";
describe("P5.6 configuration proposals", () => {
  it("keeps all controls unavailable", () => {
    render(<FeaturesConfigurationPage />);
    expect(screen.getByRole("heading", { name: "Features and configuration" })).toBeInTheDocument();
    for (const button of screen.getAllByRole("button", { name: "Unavailable" }))
      expect(button).toBeDisabled();
  });
});
