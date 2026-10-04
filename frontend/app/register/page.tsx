"use client";
import Link from "next/link";
import { FormEvent, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { CalendarClock, Eye, EyeOff, HeartPulse, Stethoscope, UsersRound } from "lucide-react";
import { registerUser, type UserRole } from "@/lib/api";
import GoogleSignIn from "@/components/GoogleSignIn";
import EcgLine from "@/components/EcgLine";

function strength(pw: string) {
  let s = 0;
  if (pw.length >= 8) s++;
  if (pw.length >= 12) s++;
  if (/[A-Z]/.test(pw) && /[a-z]/.test(pw)) s++;
  if (/\d/.test(pw) && /[^A-Za-z0-9]/.test(pw)) s++;
  return pw.length === 0 ? 0 : Math.max(1, s);
}
const strengthLabel = ["", "Weak", "Fair", "Good", "Strong"];

export default function RegisterPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [show, setShow] = useState(false);
  const [role, setRole] = useState<UserRole>("patient");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const score = useMemo(() => strength(password), [password]);

  async function submit(e: FormEvent) {
    e.preventDefault(); setError(""); setLoading(true);
    try { await registerUser({ full_name: fullName, email, password, role }); router.push(`/login?registered=1&email=${encodeURIComponent(email)}`); }
    catch (err) { setError(err instanceof Error ? err.message : "Unable to create account"); }
    finally { setLoading(false); }
  }

  return (
    <main className="auth">
      <section className="authStory">
        <EcgLine className="authEcg" duration={12} />
        <Link href="/" className="brand"><span className="brandMark">M</span><span>MediLink <b>AI</b></span></Link>
        <div className="authPitch">
          <h1>{role === "patient" ? "Get care without the guesswork." : "Run your clinic from one screen."}</h1>
          <ul className="authPoints">
            {role === "patient" ? <>
              <li><HeartPulse size={18} /><div><b>Describe, don't search</b><span>Tell MediLink how you feel and see the right speciality.</span></div></li>
              <li><CalendarClock size={18} /><div><b>Book in a few taps</b><span>Open slots from available doctors, ranked for you.</span></div></li>
            </> : <>
              <li><UsersRound size={18} /><div><b>Your patient queue</b><span>Upcoming bookings and statuses at a glance.</span></div></li>
              <li><CalendarClock size={18} /><div><b>Availability on your terms</b><span>Open slots in seconds with quick durations.</span></div></li>
            </>}
          </ul>
        </div>
        <small>The sign-up method doesn't change the role you pick.</small>
      </section>
      <section className="authPanel">
        <div className="authFormInner wide">
          <h2>Create your account</h2>
          <div className="roleGrid" role="radiogroup" aria-label="Account type">
            <button type="button" role="radio" aria-checked={role === "patient"} className={`roleCard${role === "patient" ? " active" : ""}`} onClick={() => setRole("patient")}><HeartPulse size={20} /><b>Patient</b><span>Care, bookings and AI help</span></button>
            <button type="button" role="radio" aria-checked={role === "doctor"} className={`roleCard${role === "doctor" ? " active" : ""}`} onClick={() => setRole("doctor")}><Stethoscope size={20} /><b>Doctor</b><span>Clinical workspace and patients</span></button>
          </div>
          <GoogleSignIn role={role} />
          <div className="authDivider"><span>or use email</span></div>
          <form className="authForm" onSubmit={submit}>
            <label>Full name<input required minLength={2} autoComplete="name" value={fullName} onChange={e => setFullName(e.target.value)} placeholder="Your full name" /></label>
            <label>Email<input type="email" required autoComplete="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" /></label>
            <label>Password
              <span className="pwField"><input type={show ? "text" : "password"} required minLength={8} maxLength={128} autoComplete="new-password" value={password} onChange={e => setPassword(e.target.value)} placeholder="At least 8 characters" />
                <button type="button" className="iconBtn" onClick={() => setShow(s => !s)} aria-label={show ? "Hide password" : "Show password"}>{show ? <EyeOff size={17} /> : <Eye size={17} />}</button></span>
              <span className="strength" data-s={score} aria-live="polite"><i /><i /><i /><i /><em>{strengthLabel[score]}</em></span>
            </label>
            {error && <div className="errorBox" role="alert">{error}</div>}
            <button className="btn primary full" disabled={loading}>{loading ? "Creating account…" : "Create account"}</button>
          </form>
          <p className="authFooter">Already registered? <Link href="/login">Sign in</Link></p>
        </div>
      </section>
    </main>
  );
}
