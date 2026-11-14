import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SmartDoctor | Patient Knowledge Workspace",
  description: "Secure patient document workspace with evidence-grounded AI assistance.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
