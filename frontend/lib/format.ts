import type { Appointment } from "@/lib/api";

export function fmtDateTime(v: string | null | undefined, empty = "No slot listed") {
  if (!v) return empty;
  return new Date(v).toLocaleString([], { weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
}
export function fmtDay(v: string) {
  return new Date(v).toLocaleDateString([], { weekday: "short", day: "numeric", month: "short" });
}
export function fmtTime(v: string) {
  return new Date(v).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}
export function countdown(v: string) {
  const ms = new Date(v).getTime() - Date.now();
  if (ms <= 0) return "Now";
  const m = Math.floor(ms / 60000);
  const d = Math.floor(m / 1440), h = Math.floor((m % 1440) / 60), mm = m % 60;
  if (d > 0) return `in ${d}d ${h}h`;
  if (h > 0) return `in ${h}h ${mm}m`;
  return `in ${mm}m`;
}
export function greeting() {
  const h = new Date().getHours();
  return h < 12 ? "Good morning" : h < 18 ? "Good afternoon" : "Good evening";
}
export function initials(name: string) {
  return name.replace(/^(dr|mr|mrs|ms)\.?\s+/i, "").split(/\s+/).slice(0, 2).map(p => p[0]?.toUpperCase() ?? "").join("");
}
export function toLocalInput(d: Date) {
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`;
}
/** Builds an .ics file for an appointment and triggers a download (assumes a 30 minute visit). */
export function downloadIcs(a: Appointment) {
  const start = new Date(a.scheduled_at);
  const end = new Date(start.getTime() + 30 * 60000);
  const z = (d: Date) => d.toISOString().replace(/[-:]/g, "").replace(/\.\d{3}/, "");
  const esc = (s: string) => s.replace(/([,;\\])/g, "\\$1").replace(/\n/g, "\\n");
  const ics = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//MediLink//EN", "BEGIN:VEVENT", `UID:medilink-${a.id}@medilink`, `DTSTAMP:${z(new Date())}`, `DTSTART:${z(start)}`, `DTEND:${z(end)}`, `SUMMARY:${esc(`MediLink · ${a.doctor_name}`)}`, `DESCRIPTION:${esc(a.reason)}`, "END:VEVENT", "END:VCALENDAR"].join("\r\n");
  const url = URL.createObjectURL(new Blob([ics], { type: "text/calendar" }));
  const link = document.createElement("a");
  link.href = url; link.download = `medilink-appointment-${a.id}.ics`; link.click();
  URL.revokeObjectURL(url);
}
