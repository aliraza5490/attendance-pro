import type { Metadata } from "next";
import { Sidebar } from "@/components/Sidebar";
import "./globals.css";

export const metadata: Metadata = {
  title: "VisionAttend | Gesture & Face Recognition Dashboard",
  description: "AI-powered real-time attendance tracking with gesture HUD and analytics",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#0b0f19] text-slate-100 min-h-screen flex antialiased selection:bg-cyan-500/30 selection:text-cyan-200">
        <Sidebar />
        <div className="flex-1 flex flex-col min-w-0 h-screen overflow-y-auto bg-radial-gradient">
          {children}
        </div>
      </body>
    </html>
  );
}
