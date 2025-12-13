"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { JobListing } from "@/lib/types/job-listing";
import {
  Building2,
  Calendar,
  ExternalLink,
  Loader2,
  MapPin,
  Sparkles,
} from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { toast } from "sonner";

interface JobListingsProps {
  jobs: JobListing[];
  isLoading?: boolean;
  onJobEnriched?: () => void;
}

export function JobListings({
  jobs,
  isLoading,
  onJobEnriched,
}: JobListingsProps) {
  const handleEnrich = (jobId: string) => {
    // Notify parent to refresh job listings
    if (onJobEnriched) {
      onJobEnriched();
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Job Listings</CardTitle>
          <CardDescription>Loading job listings...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (jobs.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Job Listings</CardTitle>
          <CardDescription>
            No job listings found for this company
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Job Listings</CardTitle>
        <CardDescription>
          Found {jobs.length} job {jobs.length === 1 ? "listing" : "listings"}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid gap-4">
          {jobs.map((job) => (
            <JobListingCard key={job._id} job={job} onEnrich={handleEnrich} />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

interface JobListingCardProps {
  job: JobListing;
  onEnrich?: (jobId: string) => void;
}

export function JobListingCard({ job, onEnrich }: JobListingCardProps) {
  const [enriching, setEnriching] = useState(false);

  const formatDate = (dateString?: string | null) => {
    if (!dateString) return null;
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
    } catch {
      return null;
    }
  };

  const formatSalary = (
    min?: number,
    max?: number,
    currency?: string
  ): string | null => {
    if (!min && !max) return null;

    const currencySymbol = currency === "USD" ? "$" : currency || "";
    const formatNumber = (num: number) => {
      if (num >= 1000) {
        return `${(num / 1000).toFixed(0)}K`;
      }
      return num.toString();
    };

    if (min && max) {
      return `${currencySymbol}${formatNumber(
        min
      )} - ${currencySymbol}${formatNumber(max)}`;
    } else if (min) {
      return `${currencySymbol}${formatNumber(min)}+`;
    } else if (max) {
      return `Up to ${currencySymbol}${formatNumber(max)}`;
    }
    return null;
  };

  const getOriginBadgeStyle = (
    origin?: string
  ): { bg: string; text: string; border: string } => {
    switch (origin) {
      case "linkedin":
        return {
          bg: "bg-blue-100 dark:bg-blue-950",
          text: "text-blue-700 dark:text-blue-300",
          border: "border-blue-200 dark:border-blue-800",
        };
      case "greenhouse":
        return {
          bg: "bg-green-100 dark:bg-green-950",
          text: "text-green-700 dark:text-green-300",
          border: "border-green-200 dark:border-green-800",
        };
      case "workday":
        return {
          bg: "bg-orange-100 dark:bg-orange-950",
          text: "text-orange-700 dark:text-orange-300",
          border: "border-orange-200 dark:border-orange-800",
        };
      case "careers":
        return {
          bg: "bg-purple-100 dark:bg-purple-950",
          text: "text-purple-700 dark:text-purple-300",
          border: "border-purple-200 dark:border-purple-800",
        };
      default:
        return {
          bg: "bg-gray-100 dark:bg-gray-800",
          text: "text-gray-700 dark:text-gray-300",
          border: "border-gray-200 dark:border-gray-700",
        };
    }
  };

  const handleEnrich = async () => {
    setEnriching(true);
    try {
      const response = await fetch(
        `http://localhost:8000/api/job-listings/${job._id}/enrich`,
        {
          method: "POST",
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to enrich job listing");
      }

      const enrichedJob = await response.json();
      toast.success(`Successfully enriched job listing: ${enrichedJob.title}`);

      // Notify parent component to refresh
      if (onEnrich) {
        onEnrich(job._id);
      }
    } catch (error: any) {
      console.error("Enrich error:", error);
      toast.error(error.message || "Failed to enrich job listing");
    } finally {
      setEnriching(false);
    }
  };

  const postedDate = formatDate(job.posted_at);
  const lastSeenDate = formatDate(job.last_seen_at);
  const isEnriched = job.source_status === "enriched";

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="pt-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 space-y-3">
            {/* Company Info */}
            {job.company_info && (
              <div className="flex items-center gap-3">
                {job.company_info.logo_url ? (
                  <img
                    src={job.company_info.logo_url}
                    alt={job.company_info.name || "Company logo"}
                    className="h-10 w-10 rounded object-contain border"
                  />
                ) : (
                  <div className="h-10 w-10 rounded bg-muted flex items-center justify-center border">
                    <Building2 className="h-5 w-5 text-muted-foreground" />
                  </div>
                )}
                {job.company_info._id ? (
                  <Link
                    href={`/dashboard/company/${job.company_info._id}`}
                    className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors hover:underline"
                  >
                    {job.company_info.name || job.company || "Unknown Company"}
                  </Link>
                ) : (
                  <span className="text-sm font-medium text-muted-foreground">
                    {job.company_info.name || job.company || "Unknown Company"}
                  </span>
                )}
              </div>
            )}

            {/* Job Title */}
            <div>
              <h3 className="text-lg font-semibold leading-tight">
                {job.title}
              </h3>
            </div>

            {/* Location */}
            {job.location && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <MapPin className="h-4 w-4" />
                <span>{job.location}</span>
              </div>
            )}

            {/* Dates */}
            <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
              {postedDate && (
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4" />
                  <span>Posted: {postedDate}</span>
                </div>
              )}
              {lastSeenDate && (
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4" />
                  <span>Last seen: {lastSeenDate}</span>
                </div>
              )}
            </div>

            {/* Badges */}
            <div className="flex flex-wrap gap-2">
              {/* Origin Badge */}
              {job.origin && (
                <Badge
                  variant="outline"
                  className={`text-xs border ${
                    getOriginBadgeStyle(job.origin).bg
                  } ${getOriginBadgeStyle(job.origin).text} ${
                    getOriginBadgeStyle(job.origin).border
                  }`}
                >
                  {job.origin.charAt(0).toUpperCase() + job.origin.slice(1)}
                </Badge>
              )}
              {isEnriched && (
                <Badge variant="default" className="text-xs">
                  <Sparkles className="h-3 w-3 mr-1" />
                  Enriched
                </Badge>
              )}
              {job.employement_type && (
                <Badge variant="outline" className="text-xs">
                  {job.employement_type}
                </Badge>
              )}
              {job.work_arrangement && (
                <Badge variant="outline" className="text-xs">
                  {job.work_arrangement}
                </Badge>
              )}
            </div>

            {/* Salary Range */}
            {formatSalary(
              job.salary_range_min,
              job.salary_range_max,
              job.salary_currency
            ) && (
              <div className="text-sm font-medium text-green-600 dark:text-green-400">
                💰{" "}
                {formatSalary(
                  job.salary_range_min,
                  job.salary_range_max,
                  job.salary_currency
                )}
              </div>
            )}

            {/* Profile Categories and Role Titles */}
            {(job.profile_categories || job.role_titles) && (
              <div className="space-y-1 text-sm">
                {job.profile_categories &&
                  job.profile_categories.length > 0 && (
                    <div>
                      <span className="text-muted-foreground">
                        Categories:{" "}
                      </span>
                      <span>{job.profile_categories.join(", ")}</span>
                    </div>
                  )}
                {job.role_titles && job.role_titles.length > 0 && (
                  <div>
                    <span className="text-muted-foreground">Roles: </span>
                    <span>{job.role_titles.join(", ")}</span>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="shrink-0 flex flex-col gap-2">
            {!isEnriched && onEnrich && (
              <Button
                onClick={handleEnrich}
                disabled={enriching}
                size="sm"
                variant="default"
                className="gap-2"
              >
                {enriching ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Enriching...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4" />
                    Enrich
                  </>
                )}
              </Button>
            )}
            <Button asChild size="sm" variant="outline">
              <a
                href={job.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2"
              >
                View Job
                <ExternalLink className="h-4 w-4" />
              </a>
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
