"use client";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useAuth } from "@/contexts/auth-context";
import { Briefcase, Building2, FileText, Zap } from "lucide-react";
import Link from "next/link";

export default function DashboardPage() {
  const { user } = useAuth();

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">
          Welcome back, {user?.full_name || user?.email}!
        </h1>
        <p className="text-muted-foreground mt-2">
          Here's what you can do in your dashboard
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <Link href="/dashboard/jobs">
          <Card className="hover:shadow-lg transition-shadow cursor-pointer">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Briefcase className="h-6 w-6 text-primary" />
                <CardTitle>Job Listings</CardTitle>
              </div>
              <CardDescription>
                Browse and manage job opportunities
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button variant="outline" className="w-full">
                View Jobs
              </Button>
            </CardContent>
          </Card>
        </Link>

        <Link href="/dashboard/resumes">
          <Card className="hover:shadow-lg transition-shadow cursor-pointer">
            <CardHeader>
              <div className="flex items-center gap-2">
                <FileText className="h-6 w-6 text-primary" />
                <CardTitle>Resumes</CardTitle>
              </div>
              <CardDescription>
                Manage your resumes and applications
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button variant="outline" className="w-full">
                View Resumes
              </Button>
            </CardContent>
          </Card>
        </Link>

        <Link href="/dashboard/auto-apply">
          <Card className="hover:shadow-lg transition-shadow cursor-pointer">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Zap className="h-6 w-6 text-primary" />
                <CardTitle>Auto Apply</CardTitle>
              </div>
              <CardDescription>
                Automatically apply to matching jobs
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button variant="outline" className="w-full">
                Configure
              </Button>
            </CardContent>
          </Card>
        </Link>

        {user?.role === "admin" && (
          <Link href="/dashboard/admin/companies">
            <Card className="hover:shadow-lg transition-shadow cursor-pointer border-orange-200 dark:border-orange-800">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Building2 className="h-6 w-6 text-orange-600" />
                  <CardTitle>Admin: Companies</CardTitle>
                </div>
                <CardDescription>
                  Manage company database (Admin only)
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button variant="outline" className="w-full">
                  Manage Companies
                </Button>
              </CardContent>
            </Card>
          </Link>
        )}
      </div>
    </div>
  );
}
