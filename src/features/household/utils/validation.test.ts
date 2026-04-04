import { describe, expect, it } from "vitest";
import {
  HOUSEHOLD_NAME_MAX_LENGTH,
  validateHouseholdName,
} from "./validation";

describe("validateHouseholdName", () => {
  it("rejects empty and whitespace-only names", () => {
    expect(validateHouseholdName("")).toBe("Household name is required.");
    expect(validateHouseholdName("   ")).toBe("Household name is required.");
  });

  it("rejects invalid characters", () => {
    expect(validateHouseholdName("Smith Family!")).toBe(
      "Household name can only contain spaces, letters, numbers, and underscores."
    );
  });

  it("rejects names that exceed the max length", () => {
    expect(validateHouseholdName("a".repeat(HOUSEHOLD_NAME_MAX_LENGTH + 1))).toBe(
      `Household name must be ${HOUSEHOLD_NAME_MAX_LENGTH} characters or fewer.`
    );
  });

  it("accepts spaces, alphanumerics, and underscores", () => {
    expect(validateHouseholdName("Smith_Family 2026")).toBeNull();
  });
});
