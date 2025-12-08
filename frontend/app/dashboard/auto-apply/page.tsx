"use client";

import { ScoringDetailsDialog } from "@/components/scoring-details-dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { applicationApi } from "@/lib/api/application";
import { automationApi } from "@/lib/api/automation";
import { Application } from "@/lib/types/application";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Check,
  ChevronDown,
  ExternalLink,
  Loader2 as Loader2Icon,
  RefreshCw,
  Search,
  Sparkles,
  X,
} from "lucide-react";
import * as React from "react";
import { toast } from "sonner";

// For now, we'll use a hardcoded candidate ID
// In a real app, this would come from auth context or route params
const CANDIDATE_ID = "692062c1ee4d1d50120c9f4a";

const getStatusColor = (status: string) => {
  switch (status.toLowerCase()) {
    case "applied":
    case "pending":
      return "bg-green-50 text-green-700 border-green-200";
    case "rejected":
      return "bg-red-50 text-red-700 border-red-200";
    case "accepted":
      return "bg-blue-50 text-blue-700 border-blue-200";
    default:
      return "bg-gray-50 text-gray-700 border-gray-200";
  }
};

const getFitColor = (score: number | null) => {
  if (!score) return "text-gray-600";
  if (score >= 80) {
    return "text-green-600";
  } else if (score >= 60) {
    return "text-blue-600";
  } else if (score >= 40) {
    return "text-orange-600";
  }
  return "text-red-600";
};

const getFitLevel = (score: number | null) => {
  if (!score) return "No score";
  if (score >= 80) return "Very good fit";
  if (score >= 60) return "Good fit";
  if (score >= 40) return "Moderate fit";
  return "Poor fit";
};

const formatRelativeTime = (dateString: string) => {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffHours < 1) return "Just now";
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? "s" : ""} ago`;
  if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? "s" : ""} ago`;
  return date.toLocaleDateString();
};

export default function AutoApplyPage() {
  const [searchQuery, setSearchQuery] = React.useState("");
  const [selectedApplication, setSelectedApplication] =
    React.useState<Application | null>(null);
  const [scoringDialogOpen, setScoringDialogOpen] = React.useState(false);
  const queryClient = useQueryClient();

  const handleScoreClick = (application: Application) => {
    setSelectedApplication(application);
    setScoringDialogOpen(true);
  };

  // Fetch applications
  const {
    data: applications,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ["applications", CANDIDATE_ID],
    queryFn: () =>
      applicationApi.getApplications({
        candidate_id: CANDIDATE_ID,
        include_details: true,
      }),
  });

  // Generate recommendations mutation
  const generateRecommendations = useMutation({
    mutationFn: () =>
      applicationApi.createRecommendations({ candidate_id: CANDIDATE_ID }),
    onSuccess: (data) => {
      toast.success(
        `Generated ${data.length} new application recommendations!`
      );
      queryClient.invalidateQueries({
        queryKey: ["applications", CANDIDATE_ID],
      });
    },
    onError: (error: Error) => {
      toast.error(`Failed to generate recommendations: ${error.message}`);
    },
  });

  // Delete application mutation
  const deleteApplication = useMutation({
    mutationFn: (applicationId: string) =>
      applicationApi.deleteApplication(applicationId),
    onSuccess: () => {
      toast.success("Application rejected and removed");
      queryClient.invalidateQueries({
        queryKey: ["applications", CANDIDATE_ID],
      });
    },
    onError: (error: Error) => {
      toast.error(`Failed to reject application: ${error.message}`);
    },
  });

  // Approve application mutation
  const approveApplication = useMutation({
    mutationFn: async (applicationId: string) => {
      // First trigger the automation
      await automationApi.triggerJobApplication({
        candidate_id: CANDIDATE_ID,
        application_id: applicationId,
      });
      // Then update status to applied
      return applicationApi.updateApplicationStatus(applicationId, "applied");
    },
    onSuccess: () => {
      toast.success("Application approved and submitted!");
      queryClient.invalidateQueries({
        queryKey: ["applications", CANDIDATE_ID],
      });
    },
    onError: (error: Error) => {
      toast.error(`Failed to approve application: ${error.message}`);
    },
  });

  // Filter applications based on search query
  const filteredApplications = React.useMemo(() => {
    if (!applications) return [];
    if (!searchQuery) return applications;

    const query = searchQuery.toLowerCase();
    return applications.filter(
      (app) =>
        app.job_listing?.company?.toLowerCase().includes(query) ||
        app.job_listing?.title?.toLowerCase().includes(query)
    );
  }, [applications, searchQuery]);

  return (
    <div className="flex h-full w-full flex-col">
      {/* Header */}
      <header className="flex items-center gap-4 border-b bg-background px-6 py-4">
        <SidebarTrigger />
        <div className="flex flex-1 items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Auto Apply</h1>
            <p className="text-sm text-muted-foreground">
              Automatically apply to jobs matching your criteria
            </p>
          </div>
        </div>
      </header>

      {/* Table Section */}
      <div className="flex-1 overflow-hidden px-6 py-6">
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search jobs or companies"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-64 pl-9"
              />
            </div>
            <Button variant="outline" size="sm">
              <span>Sort</span>
              <ChevronDown className="ml-1 h-4 w-4" />
            </Button>
            <Button variant="outline" size="sm">
              <span>Status</span>
              <ChevronDown className="ml-1 h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetch()}
              disabled={isLoading}
            >
              <RefreshCw
                className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`}
              />
              Refresh
            </Button>
          </div>

          <Button
            onClick={() => generateRecommendations.mutate()}
            disabled={generateRecommendations.isPending}
            className="gap-2"
          >
            <Sparkles className="h-4 w-4" />
            {generateRecommendations.isPending
              ? "Generating..."
              : "Generate Recommendations"}
          </Button>
        </div>

        <div className="overflow-auto rounded-lg border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Company Name</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Updated At</TableHead>
                <TableHead>Job Posting</TableHead>
                <TableHead className="text-right">Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                // Loading skeleton
                Array.from({ length: 5 }).map((_, index) => (
                  <TableRow key={`skeleton-${index}`}>
                    <TableCell>
                      <Skeleton className="h-4 w-32" />
                    </TableCell>
                    <TableCell>
                      <Skeleton className="h-6 w-20" />
                    </TableCell>
                    <TableCell>
                      <Skeleton className="h-4 w-24" />
                    </TableCell>
                    <TableCell>
                      <Skeleton className="h-4 w-48 mb-2" />
                      <Skeleton className="h-3 w-32" />
                    </TableCell>
                    <TableCell>
                      <Skeleton className="h-4 w-8 ml-auto" />
                    </TableCell>
                  </TableRow>
                ))
              ) : error ? (
                // Error state
                <TableRow key="error-state">
                  <TableCell
                    colSpan={5}
                    className="text-center py-8 text-muted-foreground"
                  >
                    <p>Failed to load applications: {error.message}</p>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => refetch()}
                      className="mt-2"
                    >
                      Try Again
                    </Button>
                  </TableCell>
                </TableRow>
              ) : filteredApplications.length === 0 ? (
                // Empty state
                <TableRow key="empty-state">
                  <TableCell
                    colSpan={5}
                    className="text-center py-8 text-muted-foreground"
                  >
                    {searchQuery ? (
                      <p>
                        No applications found matching &quot;{searchQuery}&quot;
                      </p>
                    ) : (
                      <div className="flex flex-col items-center gap-2">
                        <p>No applications yet</p>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => generateRecommendations.mutate()}
                        >
                          <Sparkles className="h-4 w-4 mr-2" />
                          Generate Recommendations
                        </Button>
                      </div>
                    )}
                  </TableCell>
                </TableRow>
              ) : (
                // Data rows
                filteredApplications.map((application) => {
                  // Extract from metadata with fallback
                  const companyName =
                    application.job_listing?.metadata?.categorization_schema
                      ?.job_info?.company_name ||
                    application.job_listing?.company ||
                    "Unknown Company";
                  const jobTitle =
                    application.job_listing?.metadata?.categorization_schema
                      ?.job_info?.job_title ||
                    application.job_listing?.title ||
                    "Untitled Position";

                  return (
                    <TableRow key={application._id}>
                      <TableCell className="font-medium">
                        {companyName}
                      </TableCell>
                      <TableCell>
                        <span
                          className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${getStatusColor(
                            application.status
                          )}`}
                        >
                          {application.status.charAt(0).toUpperCase() +
                            application.status.slice(1)}
                        </span>
                      </TableCell>
                      <TableCell>
                        {formatRelativeTime(application.updated_at)}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {application.job_listing?.url ? (
                            <a
                              href={application.job_listing.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex items-center gap-1 hover:underline"
                            >
                              {jobTitle}
                              <ExternalLink className="h-3 w-3" />
                            </a>
                          ) : (
                            <span>{jobTitle}</span>
                          )}
                        </div>
                        {application.accuracy_score !== null &&
                          (application.scoring_metadata ? (
                            <button
                              onClick={() => handleScoreClick(application)}
                              className="mt-1 flex items-center gap-2 text-xs hover:underline cursor-pointer"
                            >
                              <span
                                className={`font-medium ${getFitColor(
                                  application.accuracy_score
                                )}`}
                              >
                                {application.accuracy_score}
                              </span>
                              <span className="text-muted-foreground">|</span>
                              <span
                                className={getFitColor(
                                  application.accuracy_score
                                )}
                              >
                                {getFitLevel(application.accuracy_score)}
                              </span>
                            </button>
                          ) : (
                            <div className="mt-1 flex items-center gap-2 text-xs">
                              <span
                                className={`font-medium ${getFitColor(
                                  application.accuracy_score
                                )}`}
                              >
                                {application.accuracy_score}
                              </span>
                              <span className="text-muted-foreground">|</span>
                              <span
                                className={getFitColor(
                                  application.accuracy_score
                                )}
                              >
                                {getFitLevel(application.accuracy_score)}
                              </span>
                            </div>
                          ))}
                      </TableCell>
                      <TableCell className="text-right">
                        {application.status.toLowerCase() === "pending" ? (
                          <div className="flex items-center justify-end gap-2">
                            <Button
                              size="sm"
                              variant="outline"
                              className="h-8 w-8 p-0 border-green-600 text-green-600 hover:bg-green-50 hover:text-green-700"
                              onClick={() =>
                                approveApplication.mutate(application._id)
                              }
                              disabled={
                                approveApplication.isPending ||
                                deleteApplication.isPending
                              }
                            >
                              {approveApplication.isPending ? (
                                <Loader2Icon className="h-4 w-4 animate-spin" />
                              ) : (
                                <Check className="h-4 w-4" />
                              )}
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              className="h-8 w-8 p-0 border-red-600 text-red-600 hover:bg-red-50 hover:text-red-700"
                              onClick={() =>
                                deleteApplication.mutate(application._id)
                              }
                              disabled={
                                approveApplication.isPending ||
                                deleteApplication.isPending
                              }
                            >
                              {deleteApplication.isPending ? (
                                <Loader2Icon className="h-4 w-4 animate-spin" />
                              ) : (
                                <X className="h-4 w-4" />
                              )}
                            </Button>
                          </div>
                        ) : (
                          <span
                            className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${getStatusColor(
                              application.status
                            )}`}
                          >
                            {application.status.charAt(0).toUpperCase() +
                              application.status.slice(1)}
                          </span>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </div>
      </div>

      {/* Scoring Details Dialog */}
      <ScoringDetailsDialog
        open={scoringDialogOpen}
        onOpenChange={setScoringDialogOpen}
        scoringMetadata={selectedApplication?.scoring_metadata}
        companyName={
          selectedApplication?.job_listing?.metadata?.categorization_schema
            ?.job_info?.company_name ||
          selectedApplication?.job_listing?.company ||
          "Unknown Company"
        }
        jobTitle={
          selectedApplication?.job_listing?.metadata?.categorization_schema
            ?.job_info?.job_title ||
          selectedApplication?.job_listing?.title ||
          "Untitled Position"
        }
      />
    </div>
  );
}
