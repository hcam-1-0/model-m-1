import { describe, expect, it } from "vitest";
import { localeTimeProfiles } from "../packages/quality-contracts/src";

describe("P5.7 localization and timezone", () => {
  it("formats the same instant in supported operator locales without changing the instant", () => {
    const instant = new Date("2026-09-12T06:30:00.000Z");
    for (const profile of localeTimeProfiles.filter(({ mode }) => mode === "operator")) {
      const formatted = new Intl.DateTimeFormat(profile.locale, {
        dateStyle: "medium",
        timeStyle: "medium",
        timeZone: profile.timezone,
      }).format(instant);
      expect(formatted.length).toBeGreaterThan(8);
    }
    expect(instant.toISOString()).toBe("2026-09-12T06:30:00.000Z");
  });
});
