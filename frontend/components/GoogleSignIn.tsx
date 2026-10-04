"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { HeartPulse, LoaderCircle, Stethoscope } from "lucide-react";
import { ApiError, googleAuth, type UserRole } from "@/lib/api";
import { dashboardFor, saveSession } from "@/lib/auth";

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (o: { client_id: string; callback: (r: { credential: string }) => void }) => void;
          renderButton: (el: HTMLElement, o: Record<string, unknown>) => void;
        };
      };
    };
  }
}

export default function GoogleSignIn({ role }: { role?: UserRole }) {
  const router = useRouter();
  const ref = useRef<HTMLDivElement>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [pendingCredential, setPendingCredential] = useState<string | null>(null);
  const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;

  async function finish(credential: string, selectedRole?: UserRole) {
    setBusy(true);
    setError("");
    try {
      const session = await googleAuth(credential, selectedRole);
      saveSession(session);
      router.push(dashboardFor(session.user.role));
    } catch (e) {
      if (e instanceof ApiError && e.code === "role_required") {
        setPendingCredential(credential);
        setError("");
      } else {
        setError(e instanceof Error ? e.message : "Google sign-in failed");
      }
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    if (!clientId) return;

    const render = () => {
      if (!window.google || !ref.current) return;
      ref.current.innerHTML = "";
      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: ({ credential }) => finish(credential, role),
      });
      window.google.accounts.id.renderButton(ref.current, {
        theme: "filled_black",
        size: "large",
        shape: "pill",
        text: "continue_with",
        width: 360,
      });
    };

    if (window.google) {
      render();
      return;
    }

    const existing = document.querySelector("script[data-medilink-google]") as HTMLScriptElement | null;
    if (existing) {
      existing.addEventListener("load", render);
      return () => existing.removeEventListener("load", render);
    }

    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.dataset.medilinkGoogle = "1";
    script.onload = render;
    script.onerror = () => setError("Google sign-in could not be loaded. Check your connection and OAuth configuration.");
    document.head.appendChild(script);
  }, [clientId, role]);

  if (!clientId) {
    return (
      <div className="socialDisabled">
        Google sign-in is disabled until <code>NEXT_PUBLIC_GOOGLE_CLIENT_ID</code> is set in <code>.env.local</code>.
      </div>
    );
  }

  return (
    <>
      <div className={`googleButtonWrap${busy ? " busy" : ""}`} ref={ref} aria-busy={busy} />
      {busy && <div className="googleBusy"><LoaderCircle size={15} className="spin" /> Verifying Google account…</div>}

      {pendingCredential && !role && (
        <div className="googleRolePrompt">
          <div>
            <b>One last step</b>
            <span>How will you use MediLink?</span>
          </div>
          <div className="googleRoleActions">
            <button type="button" className="roleMini" disabled={busy} onClick={() => finish(pendingCredential, "patient")}>
              <HeartPulse size={17} /> Patient
            </button>
            <button type="button" className="roleMini" disabled={busy} onClick={() => finish(pendingCredential, "doctor")}>
              <Stethoscope size={17} /> Doctor
            </button>
          </div>
          <small>This choice controls your workspace and can be reviewed by an administrator later.</small>
        </div>
      )}

      {error && <div className="errorBox" role="alert">{error}</div>}
    </>
  );
}
