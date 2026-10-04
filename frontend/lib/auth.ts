import type { LoginResponse, MediLinkUser } from "./api";

const TOKEN_KEY = "medilink_token";
const USER_KEY = "medilink_user";

export function saveSession(session: LoginResponse) {
  localStorage.setItem(TOKEN_KEY, session.access_token);
  localStorage.setItem(USER_KEY, JSON.stringify(session.user));
}

export function getToken() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser(): MediLinkUser | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as MediLinkUser;
  } catch {
    return null;
  }
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function dashboardFor(role: MediLinkUser["role"]) {
  if (role === "doctor") return "/dashboard/doctor";
  if (role === "admin") return "/dashboard/admin";
  return "/dashboard/patient";
}
