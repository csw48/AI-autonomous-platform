import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Platform",
  description: "AI Autonomous Knowledge & Workflow Platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
