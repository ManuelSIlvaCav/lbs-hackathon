import { ConditionalSidebar } from "@/components/conditional-sidebar";
import { QueryProvider } from "@/components/providers/query-provider";
import { Toaster } from "@/components/ui/sonner";
import { AuthProvider } from "@/contexts/auth-context";
import { JobSearchFiltersProvider } from "@/contexts/job-search-filters-context";
import type { Metadata } from "next";
import { Inter, Sora } from "next/font/google";
import "./globals.css";

const sora = Sora({
  variable: "--font-sora",
  subsets: ["latin"],
  weight: ["100", "200", "300", "400", "500", "600", "700"],
});

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  weight: ["100", "200", "300", "400", "500", "600", "700", "800", "900"],
});

export const metadata: Metadata = {
  title: "aiApply - Auto Apply",
  description: "Automatically apply to jobs matching your criteria",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${inter.variable} ${sora.variable} font-sans antialiased`}
      >
        <AuthProvider>
          <QueryProvider>
            <JobSearchFiltersProvider>
              <ConditionalSidebar>{children}</ConditionalSidebar>
              <Toaster />
            </JobSearchFiltersProvider>
          </QueryProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
