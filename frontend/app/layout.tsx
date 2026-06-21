import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Toaster } from "react-hot-toast";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "PowerBI Genius AI — Autonomous Dashboard Generation",
  description: "Transform any dataset into a stakeholder-ready Power BI dashboard with AI. Upload CSV, Excel, PDF, or connect any data source.",
  keywords: ["Power BI", "AI", "Dashboard", "Analytics", "Business Intelligence", "Data Visualization"],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} antialiased`}>
        {children}
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: "#1E293B",
              color: "#F8FAFC",
              border: "1px solid #334155",
            },
            success: { iconTheme: { primary: "#10B981", secondary: "#F8FAFC" } },
            error: { iconTheme: { primary: "#EF4444", secondary: "#F8FAFC" } },
          }}
        />
      </body>
    </html>
  );
}
