"use client";
import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { AlertTriangle, BrainCircuit, CalendarDays, ChevronRight, LayoutDashboard, Search, ShieldCheck, Sparkles } from "lucide-react";
import ProtectedDashboard from "@/components/ProtectedDashboard";
import AppShell, { type NavItem } from "@/components/AppShell";
import ScoreRing from "@/components/ScoreRing";
import { getAIDoctorMatches, type AIDoctorMatchResponse } from "@/lib/api";
import { getToken } from "@/lib/auth";
import { fmtDateTime } from "@/lib/format";

const nav: NavItem[] = [
  { href: "/dashboard/patient", label: "Overview", icon: LayoutDashboard },
  { href: "/doctors", label: "Find a doctor", icon: Search },
  { href: "/ai-match", label: "MediLink AI", icon: BrainCircuit, badge: "AI" },
  { href: "/dashboard/patient#appointments", label: "Appointments", icon: CalendarDays },
];
const examples = ["Recurring headaches, dizziness and tiredness for several days", "An itchy red rash on my arms that has lasted a week", "Chest tightness when I climb stairs", "Sore knee that clicks and swells after running"];
const phases = ["Reading your description", "Matching specialities", "Ranking available clinicians"];
const strengthN = { strong: 3, moderate: 2, weak: 1 } as const;

function Studio({ logout, user }: { logout: () => void; user: Parameters<typeof AppShell>[0]["user"] }) {
  const router = useRouter();
  const params = useSearchParams();
  const [symptoms, setSymptoms] = useState(params.get("q") ?? "");
  const [result, setResult] = useState<AIDoctorMatchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [phase, setPhase] = useState(0);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!loading) return;
    setPhase(0);
    const i = setInterval(() => setPhase(p => Math.min(p + 1, phases.length - 1)), 1100);
    return () => clearInterval(i);
  }, [loading]);

  async function analyse() {
    const token = getToken();
    if (!token || symptoms.trim().length < 5 || loading) return;
    setLoading(true); setError(""); setResult(null);
    try { setResult(await getAIDoctorMatches(token, symptoms)); }
    catch (e) { setError(e instanceof Error ? e.message : "MediLink AI could not analyse the request"); }
    finally { setLoading(false); }
  }

  return (
    <AppShell user={user} logout={logout} nav={nav} active="/ai-match"
      title="Tell MediLink what you need help with." subtitle="We suggest a care pathway and rank available clinicians. This is routing support, not a diagnosis.">
      <section className="composer">
        <div className="aiOrb big"><Sparkles size={20} /></div>
        <textarea value={symptoms} maxLength={4000} onChange={e => setSymptoms(e.target.value)}
          onKeyDown={e => { if ((e.metaKey || e.ctrlKey) && e.key === "Enter") analyse(); }}
          placeholder="Example: I've had recurring headaches, dizziness and fatigue for several days…" aria-label="Describe your symptoms" />
        <div className="promptChips">{examples.map(x => <button key={x} type="button" onClick={() => setSymptoms(x)}>{x}</button>)}</div>
        <div className="composerBottom">
          <span className="muted small">{symptoms.length}/4000 · Ctrl Enter to analyse · In an emergency call 999</span>
          <button className="btn primary" disabled={loading || symptoms.trim().length < 5} onClick={analyse}>{loading ? "Analysing…" : "Analyse care need"}</button>
        </div>
      </section>

      {loading && <section className="card scan" aria-live="polite">
        <div className="scanBar"><i /></div>
        <ul>{phases.map((p, i) => <li key={p} className={i < phase ? "done" : i === phase ? "now" : ""}><span />{p}</li>)}</ul>
      </section>}

      {error && <div className="errorBanner" role="alert">{error}</div>}

      {result?.urgent && <section className="urgent" role="alert">
        <AlertTriangle size={30} />
        <div><h2>Don't rely on routine appointment matching.</h2><p>{result.safety_message}</p>{result.urgent_reason && <b>Flag detected: {result.urgent_reason}</b>}</div>
      </section>}

      {result && !result.urgent && (
        <div className="results">
          <div className="resultsMain">
            <div className="sectionBar">
              <div><h2>Suggested specialities</h2></div>
              <span className={`modelPill ${result.mode}`}>{result.mode === "calibrated_model" ? "Calibrated model" : "Clinical routing"}</span>
            </div>
            <div className="notice"><ShieldCheck size={18} /><span>{result.confidence_note}</span></div>
            <div className="routeGrid">
              {result.suggested_specialties.map((s, i) => (
                <article className={`route${i === 0 ? " best" : ""}`} key={s.specialty}>
                  <div className="routeTop"><span className="rank">#{i + 1}</span>
                    {s.confidence !== null ? <ScoreRing value={s.confidence * 100} size={56} stroke={5} label={`${Math.round(s.confidence * 100)}%`} tone={i === 0 ? "cyan" : "violet"} />
                      : <span className="meter" data-n={strengthN[s.routing_strength]} title={`${s.routing_strength} signal`}><i /><i /><i /></span>}
                  </div>
                  <h3>{s.specialty}</h3>
                  <small className="muted">{s.confidence !== null ? " calibrated confidence" : `${s.routing_strength[0].toUpperCase() + s.routing_strength.slice(1)} signal`}</small>
                  <p>{s.explanation}</p>
                  {s.matched_terms.length > 0 && <div className="terms">{s.matched_terms.slice(0, 5).map(t => <span key={t}>{t}</span>)}</div>}
                </article>))}
            </div>

            <div className="sectionBar"><h2>Best available clinicians</h2><span className="muted small">{result.doctor_matches.length} found</span></div>
            {result.doctor_matches.length === 0 ? <article className="card"><h3>No matching clinicians yet</h3><p className="muted">Doctors need a profile and open slots to appear. You can still search manually.</p><Link href="/doctors" className="btn outline">Search all doctors</Link></article> :
              <div className="docList">{result.doctor_matches.map((d, i) => (
                <article className="docMatch" key={d.doctor_id}>
                  <ScoreRing value={d.match_score} size={76} stroke={7} label={String(Math.round(d.match_score))} sub="/100" tone={i === 0 ? "cyan" : "violet"} />
                  <div className="docBody">
                    <div className="cardTop"><div><span className="muted small">{d.specialty}</span><h3>{d.full_name}</h3><p className="muted">{d.clinic} · {d.consultation_type}</p></div><span className={`pill ${d.open_slots ? "scheduled" : "cancelled"}`}>{d.open_slots} open</span></div>
                    <div className="facts"><span>{d.years_experience} yrs experience</span><span>Next: {fmtDateTime(d.next_available_at)}</span></div>
                    <div className="why"><b>Why this doctor ranked here</b>{d.reasons.map(r => <p key={r}>{r}</p>)}</div>
                    <button className="btn primary" disabled={d.open_slots === 0} onClick={() => router.push(`/doctors?doctor=${d.doctor_id}`)}>View and book <ChevronRight size={16} /></button>
                  </div>
                </article>))}</div>}
          </div>

          <aside className="card modelCard">
            <BrainCircuit size={24} />
            <h3>Confidence is not a diagnosis.</h3>
            <p>Speciality confidence describes the routing model's output. The doctor match score separately combines speciality fit, experience and availability.</p>
            <dl>
              <div><dt>Model</dt><dd>{result.mode === "calibrated_model" ? "Calibrated routing" : "Clinical routing"}</dd></div>
              <div><dt>Version</dt><dd>{result.model_version ?? "rules-v1"}</dd></div>
              {typeof result.model_metrics?.accuracy === "number" && <div><dt>Validation accuracy</dt><dd>{Math.round((result.model_metrics.accuracy as number) * 100)}%</dd></div>}
            </dl>
            <div className="disclaimer">{result.disclaimer}</div>
          </aside>
        </div>
      )}
    </AppShell>
  );
}

export default function AIDoctorMatchPage() {
  return (
    <ProtectedDashboard requiredRole="patient">
      {(user, logout) => <Suspense fallback={<div className="loadingPage"><div className="loader" /></div>}><Studio user={user} logout={logout} /></Suspense>}
    </ProtectedDashboard>
  );
}
