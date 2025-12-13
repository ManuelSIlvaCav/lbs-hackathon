"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Skeleton } from "@/components/ui/skeleton";
import { JobListing } from "@/lib/types/job-listing";
import { useQuery } from "@tanstack/react-query";
import {
  Building2,
  ExternalLink,
  Globe,
  Heart,
  Linkedin,
  Loader2,
} from "lucide-react";
import { useParams } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";

interface Company {
  _id: string;
  name: string;
  company_url?: string;
  linkedin_url?: string;
  logo_url?: string;
  domain?: string;
  industries?: string[];
  description?: string;
  created_at: string;
  updated_at: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function CompanyDetailPage() {
  const params = useParams();
  const companyId = params.id as string;
  const [isSaved, setIsSaved] = useState(false);

  // Fetch company details
  const {
    data: company,
    isLoading: isLoadingCompany,
    error: companyError,
  } = useQuery<Company>({
    queryKey: ["company", companyId],
    queryFn: async () => {
      const response = await fetch(
        `${API_BASE_URL}/api/companies/${companyId}`
      );
      if (!response.ok) {
        throw new Error("Failed to fetch company");
      }
      return response.json();
    },
  });

  // Fetch company job listings
  const {
    data: jobListings,
    isLoading: isLoadingJobs,
    error: jobsError,
  } = useQuery<JobListing[]>({
    queryKey: ["companyJobs", companyId],
    queryFn: async () => {
      const response = await fetch(
        `${API_BASE_URL}/api/companies/${companyId}/job-listings`
      );
      if (!response.ok) {
        throw new Error("Failed to fetch job listings");
      }
      return response.json();
    },
  });

  const handleSaveToFavorites = () => {
    // TODO: Implement save to favorites functionality
    setIsSaved(!isSaved);
    toast.success(
      isSaved
        ? "Removed from favorites"
        : `${company?.name} saved to favorites!`
    );
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return null;
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString("en-US", {
        year: "numeric",
        month: "long",
        day: "numeric",
      });
    } catch {
      return null;
    }
  };

  if (isLoadingCompany) {
    return (
      <div className="flex h-full w-full flex-col">
        <header className="flex items-center justify-between border-b bg-background px-6 py-8">
          <div className="flex items-center gap-4">
            <SidebarTrigger />
            <div className="space-y-2">
              <Skeleton className="h-8 w-64" />
              <Skeleton className="h-4 w-48" />
            </div>
          </div>
        </header>
        <div className="flex-1 overflow-auto px-6 py-6">
          <div className="flex items-center justify-center h-full">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        </div>
      </div>
    );
  }

  if (companyError || !company) {
    return (
      <div className="flex h-full w-full flex-col">
        <header className="flex items-center gap-4 border-b bg-background px-6 py-8">
          <SidebarTrigger />
          <h1 className="text-3xl font-semibold font-sora">
            Company Not Found
          </h1>
        </header>
        <div className="flex-1 overflow-auto px-6 py-6">
          <div className="flex items-center justify-center h-full">
            <div className="text-center space-y-2">
              <p className="text-destructive">Error loading company</p>
              <p className="text-sm text-muted-foreground font-inter">
                {companyError instanceof Error
                  ? companyError.message
                  : "Company not found"}
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full w-full flex-col">
      {/* Header */}
      <header className="border-b bg-background px-6 py-8">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-6">
            <SidebarTrigger />

            {/* Company Logo */}
            {company.logo_url ? (
              <img
                src={company.logo_url}
                alt={`${company.name} logo`}
                className="h-20 w-20 rounded-lg object-contain border"
              />
            ) : (
              <div className="h-20 w-20 rounded-lg border bg-muted flex items-center justify-center">
                <Building2 className="h-10 w-10 text-muted-foreground" />
              </div>
            )}

            {/* Company Name and Info */}
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <h1 className="text-3xl font-semibold font-sora">
                  {company.name}
                </h1>
                <Button
                  variant={isSaved ? "default" : "outline"}
                  size="sm"
                  onClick={handleSaveToFavorites}
                  className="gap-2"
                >
                  <Heart
                    className={`h-4 w-4 ${isSaved ? "fill-current" : ""}`}
                  />
                  {isSaved ? "Saved" : "Save"}
                </Button>
              </div>

              {/* Industries */}
              {company.industries && company.industries.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {company.industries.map((industry) => (
                    <Badge
                      key={industry}
                      variant="secondary"
                      className="font-inter"
                    >
                      {industry}
                    </Badge>
                  ))}
                </div>
              )}

              {/* Links */}
              <div className="flex flex-wrap gap-4">
                {company.company_url && (
                  <a
                    href={company.company_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 text-sm text-blue-600 hover:underline font-inter"
                  >
                    <Globe className="h-4 w-4" />
                    Website
                    <ExternalLink className="h-3 w-3" />
                  </a>
                )}
                {company.linkedin_url && (
                  <a
                    href={company.linkedin_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 text-sm text-blue-600 hover:underline font-inter"
                  >
                    <Linkedin className="h-4 w-4" />
                    LinkedIn
                    <ExternalLink className="h-3 w-3" />
                  </a>
                )}
                {company.domain && (
                  <span className="flex items-center gap-2 text-sm text-muted-foreground font-inter">
                    <Globe className="h-4 w-4" />
                    {company.domain}
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Content Area */}
      <div className="flex-1 overflow-auto px-6 py-6">
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Company Description */}
          {company.description && (
            <Card>
              <CardHeader>
                <CardTitle className="font-sora">About</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground font-inter leading-relaxed">
                  {company.description}
                </p>
              </CardContent>
            </Card>
          )}

          {/* Company Metadata */}
          <Card>
            <CardHeader>
              <CardTitle className="font-sora">Company Information</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-inter">
                {company.created_at && (
                  <div>
                    <p className="text-sm text-muted-foreground">Added on</p>
                    <p className="font-medium">
                      {formatDate(company.created_at)}
                    </p>
                  </div>
                )}
                {company.updated_at && (
                  <div>
                    <p className="text-sm text-muted-foreground">
                      Last updated
                    </p>
                    <p className="font-medium">
                      {formatDate(company.updated_at)}
                    </p>
                  </div>
                )}
                {jobListings && (
                  <div>
                    <p className="text-sm text-muted-foreground">
                      Open positions
                    </p>
                    <p className="font-medium">
                      {jobListings.length} job
                      {jobListings.length !== 1 ? "s" : ""}
                    </p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
