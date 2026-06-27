const authMode = (import.meta.env.VITE_AUTH_MODE ?? "open").trim().toLowerCase();

export const isRestrictedAuthMode = authMode === "restricted";

export const accessContact = (import.meta.env.VITE_ACCESS_CONTACT ?? "Roy Zhao").trim()
  || "Roy Zhao";

export const restrictedAccessMessage =
  `Access to this Lantern deployment is limited to approved email addresses. Contact ${accessContact} for access.`;
