import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Actuarial Quant System",
  description: "Capital-survival underwriting portal (paper / informational mode)",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
