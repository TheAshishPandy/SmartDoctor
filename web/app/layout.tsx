import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SmartDoctor",
  description: "A patient and clinician healthcare information workspace.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
