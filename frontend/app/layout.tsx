import type { ReactNode } from "react";
import "./styles.css";

export const metadata = {
  title: "MediLink AI",
  description: "Connected healthcare powered by responsible AI",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
