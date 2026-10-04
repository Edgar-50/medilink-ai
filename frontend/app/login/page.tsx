"use client";
import Link from "next/link";
import { FormEvent, Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { BrainCircuit, CalendarCheck, Eye, EyeOff, LockKeyhole, ShieldCheck } from "lucide-react";
import { loginUser } from "@/lib/api";
import { dashboardFor, saveSession } from "@/lib/auth";
import GoogleSignIn from "@/components/GoogleSignIn";
import EcgLine from "@/components/EcgLine";

function LoginForm() {
  const router = useRouter();
  const params = useSearchParams();
  const [email, setEmail] = useState(params.get("email") ?? "");
  const [password, setPassword] = useState("");
  const [show, setShow] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault(); setError(""); setLoading(true);
    try { const s = await loginUser(email, password); saveSession(s); router.push(dashboardFor(s.user.role)); }
    catch (err) { setError(err instanceof Error ? err.message : "Unable to sign in"); }
    finally { setLoading(false); }
  }

  return (
    <div className="authFormInner">
      <h2>Sign in to MediLink</h2>
      <p className="authLead">Use your account credentials or continue with Google.</p>
      {params.get("registered") && <div className="successBanner"><ShieldCheck size={16} /> Account created. Sign in to continue.</div>}
      <GoogleSignIn />
      <div className="authDivider"><span>or use email</span></div>
      <form className="authForm" onSubmit={submit}>
        <label>Email<input type="email" required autoComplete="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" /></label>
        <label>Password
          <span className="pwField"><input type={show ? "text" : "password"} required autoComplete="current-password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Your password" />
            <button type="button" className="iconBtn" onClick={() => setShow(s => !s)} aria-label={show ? "Hide password" : "Show password"}>{show ? <EyeOff size={17} /> : <Eye size={17} />}</button></span>
        </label>
        {error && <div className="errorBox" role="alert">{error}</div>}
        <button className="btn primary full" disabled={loading}>{loading ? "Signing in…" : "Sign in"}</button>
      </form>
      <p className="authFooter">New to MediLink? <Link href="/register">Create an account</Link></p>
    </div>
  );
}

export default function LoginPage() {
  return (
    <main className="auth">
      <section className="authStory">
        <EcgLine className="authEcg" duration={12} />
        <Link href="/" className="brand"><span className="brandMark">M</span><span>MediLink <b>AI</b></span></Link>
        <div className="authPitch">
          <h1>Welcome back to your care workspace.</h1>
          <ul className="authPoints">
            <li><CalendarCheck size={18} /><div><b>Appointments</b><span>See what's next and add it to your calendar.</span></div></li>
            <li><BrainCircuit size={18} /><div><b>Care routing</b><span>Describe a symptom and get matched to a doctor.</span></div></li>
            <li><LockKeyhole size={18} /><div><b>Protected sessions</b><span>Role-based access on every request.</span></div></li>
          </ul>
        </div>
        <small>Secure access to your MediLink workspace.</small>
      </section>
      <section className="authPanel"><Suspense fallback={<div className="loader" />}><LoginForm /></Suspense></section>
    </main>
  );
}
