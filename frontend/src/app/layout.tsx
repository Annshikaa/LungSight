import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Toaster } from "react-hot-toast";
import "./globals.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: {
    default: "LungSight AI",
    template: "%s | LungSight AI",
  },
  description:
    "AI-powered chest X-ray diagnostic platform for explainable pneumonia detection, lung segmentation, and severity assessment.",
  keywords: ["pneumonia detection", "chest x-ray AI", "medical imaging", "explainable AI", "radiology"],
  authors: [{ name: "LungSight AI Team" }],
  openGraph: {
    title: "LungSight AI",
    description: "Explainable Pneumonia Detection from Chest X-Rays",
    type: "website",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#0ea5e9" },
    { media: "(prefers-color-scheme: dark)",  color: "#0284c7" },
  ],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${geistSans.variable} ${geistMono.variable} font-sans`}>
        {children}
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: "hsl(var(--card))",
              color: "hsl(var(--card-foreground))",
              border: "1px solid hsl(var(--border))",
              borderRadius: "0.75rem",
            },
          }}
        />
      </body>
    </html>
  );
}
