"use client";

import { ReactNode, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getMe, type MediLinkUser, type UserRole } from "@/lib/api";
import { clearSession, dashboardFor, getToken } from "@/lib/auth";

export default function ProtectedDashboard({
  requiredRole,
  children,
}: {
  requiredRole?: UserRole;
  children: (user: MediLinkUser, logout: () => void) => ReactNode;
}) {
  const router = useRouter();
  const [user, setUser] = useState<MediLinkUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = getToken();

    if (!token) {
      setLoading(false);
      router.replace("/login");
      return;
    }

    getMe(token)
      .then((currentUser) => {
        if (requiredRole && currentUser.role !== requiredRole) {
          router.replace(dashboardFor(currentUser.role));
          return;
        }

        setUser(currentUser);
      })
      .catch(() => {
        clearSession();
        router.replace("/login");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [requiredRole, router]);

  function logout() {
    clearSession();
    router.push("/login");
  }

  if (loading || !user) {
    return (
      <main className="loadingPage">
        <div className="loader" />
        <p>Opening secure MediLink workspace...</p>
      </main>
    );
  }

  return <>{children(user, logout)}</>;
}