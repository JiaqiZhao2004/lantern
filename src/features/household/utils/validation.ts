export const HOUSEHOLD_NAME_MAX_LENGTH = 64;
export const HOUSEHOLD_NAME_PATTERN = /^[A-Za-z0-9_ ]+$/;

export function validateHouseholdName(value: string): string | null {
  if (value.trim().length === 0) {
    return "Household name is required.";
  }

  if (value.length > HOUSEHOLD_NAME_MAX_LENGTH) {
    return `Household name must be ${HOUSEHOLD_NAME_MAX_LENGTH} characters or fewer.`;
  }

  if (!HOUSEHOLD_NAME_PATTERN.test(value)) {
    return "Household name can only contain spaces, letters, numbers, and underscores.";
  }

  return null;
}
