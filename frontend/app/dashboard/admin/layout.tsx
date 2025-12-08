"use client";

import { ProtectedRoute } from "@/components/protected-route";

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <ProtectedRoute requireAdmin={true}>{children}</ProtectedRoute>;
}
