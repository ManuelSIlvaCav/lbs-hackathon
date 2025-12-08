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
import { CompanyJobListing } from "@/lib/types/company-job-listing";
import { Calendar, ExternalLink, MapPin } from "lucide-react";

interface JobListingsProps {
  jobs: CompanyJobListing[];
  isLoading?: boolean;
}

export function JobListings({ jobs, isLoading }: JobListingsProps) {
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
            <JobListingCard key={job._id} job={job} />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

interface JobListingCardProps {
  job: CompanyJobListing;
}

function JobListingCard({ job }: JobListingCardProps) {
  const formatDate = (dateString?: string) => {
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

  const postedDate = formatDate(job.posted_at);
  const lastSeenDate = formatDate(job.last_seen_at);

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="pt-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 space-y-3">
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

            {/* Provider Badge */}
            <div>
              <Badge variant="secondary" className="text-xs">
                {job.provider}
              </Badge>
            </div>
          </div>

          {/* Apply Button */}
          <div className="shrink-0">
            <Button asChild size="sm">
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
