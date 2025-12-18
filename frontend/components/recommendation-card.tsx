import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Recommendation } from "@/lib/api/recommendation";
import {
  Building2,
  Calendar,
  ExternalLink,
  MapPin,
  Sparkles,
  ThumbsDown,
} from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

interface RecommendationCardProps {
  recommendation: Recommendation;
  onMarkAsViewed: (recommendation: Recommendation) => void;
  onMarkAsApplied: (recommendation: Recommendation) => void;
  onMarkAsRejected: (recommendation: Recommendation) => void;
  isUpdating?: boolean;
}

const getStatusBadge = (status: string) => {
  const statusConfig = {
    pending: {
      label: "Pending",
      variant: "secondary" as const,
      className: "bg-gray-100 text-gray-700 border-gray-200",
    },
    recommended: {
      label: "Recommended",
      variant: "default" as const,
      className: "bg-blue-100 text-blue-700 border-blue-200",
    },
    viewed: {
      label: "Viewed",
      variant: "outline" as const,
      className: "bg-purple-100 text-purple-700 border-purple-200",
    },
    applied: {
      label: "Applied",
      variant: "default" as const,
      className: "bg-green-100 text-green-700 border-green-200",
    },
    rejected: {
      label: "Not Interested",
      variant: "destructive" as const,
      className: "bg-red-100 text-red-700 border-red-200",
    },
  };

  const config =
    statusConfig[status as keyof typeof statusConfig] || statusConfig.pending;
  return (
    <Badge variant="outline" className={config.className}>
      {config.label}
    </Badge>
  );
};

export function RecommendationCard({
  recommendation,
  onMarkAsViewed,
  onMarkAsApplied,
  onMarkAsRejected,
  isUpdating = false,
}: RecommendationCardProps) {
  const [autoApplying, setAutoApplying] = useState(false);

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

  const handleAutoApply = async () => {
    setAutoApplying(true);
    try {
      // TODO: Implement auto-apply logic
      await new Promise((resolve) => setTimeout(resolve, 1500));
      onMarkAsApplied(recommendation);
      toast.success("Auto-apply submitted successfully!");
    } catch (error) {
      toast.error("Failed to auto-apply. Please try again.");
    } finally {
      setAutoApplying(false);
    }
  };

  const handleViewJob = () => {
    // Mark as viewed when clicking view job
    if (
      recommendation.recommendation_status === "pending" ||
      recommendation.recommendation_status === "recommended"
    ) {
      onMarkAsViewed(recommendation);
    }
  };

  const canInteract =
    recommendation.recommendation_status !== "applied" &&
    recommendation.recommendation_status !== "rejected";

  const job = recommendation.job_listing;
  const company = recommendation.company;
  const postedDate = formatDate(job?.posted_at);
  const recommendedDate = formatDate(recommendation.created_at);

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="pt-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 space-y-3">
            {/* Company Info */}
            {company && (
              <div className="flex items-center gap-3">
                {company.logo_url ? (
                  <img
                    src={company.logo_url}
                    alt={company.name || "Company logo"}
                    className="h-10 w-10 rounded object-contain border"
                  />
                ) : (
                  <div className="h-10 w-10 rounded bg-muted flex items-center justify-center border">
                    <Building2 className="h-5 w-5 text-muted-foreground" />
                  </div>
                )}
                <span className="text-sm font-medium text-muted-foreground">
                  {company.name || "Unknown Company"}
                </span>
              </div>
            )}

            {/* Job Title */}
            <div>
              <h3 className="text-lg font-semibold leading-tight">
                {job?.title || "Job Title"}
              </h3>
            </div>

            {/* Location */}
            {job?.location && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <MapPin className="h-4 w-4" />
                <span>{job.location}</span>
              </div>
            )}

            {/* Dates */}
            <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
              {recommendedDate && (
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4" />
                  <span>Recommended: {recommendedDate}</span>
                </div>
              )}
              {postedDate && (
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4" />
                  <span>Posted: {postedDate}</span>
                </div>
              )}
            </div>

            {/* Badges */}
            <div className="flex flex-wrap gap-2">
              {job?.employement_type && (
                <Badge variant="outline" className="text-xs">
                  {job.employement_type}
                </Badge>
              )}
              {job?.work_arrangement && (
                <Badge variant="outline" className="text-xs">
                  {job.work_arrangement}
                </Badge>
              )}
            </div>

            {/* Salary Range */}
            {formatSalary(
              job?.salary_range_min,
              job?.salary_range_max,
              job?.salary_currency
            ) && (
              <div className="text-sm font-medium text-green-600 dark:text-green-400">
                💰{" "}
                {formatSalary(
                  job?.salary_range_min,
                  job?.salary_range_max,
                  job?.salary_currency
                )}
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="shrink-0 flex flex-col gap-2 content-center">
            {/* View Job Button */}
            {job?.url && (
              <Button asChild size="sm" variant="outline">
                <a
                  href={job.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2"
                  onClick={handleViewJob}
                >
                  View Job
                  <ExternalLink className="h-4 w-4" />
                </a>
              </Button>
            )}
            {/* Auto Apply Button */}
            {canInteract && (
              <Button
                onClick={handleAutoApply}
                disabled={autoApplying || isUpdating}
                size="sm"
                variant="default"
                className="gap-2 bg-green-600 hover:bg-green-700 text-white"
              >
                {autoApplying ? (
                  <>
                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                    Applying...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4" />
                    Auto Apply
                  </>
                )}
              </Button>
            )}

            {/* Not Interested Button */}
            {canInteract && (
              <Button
                onClick={() => onMarkAsRejected(recommendation)}
                disabled={isUpdating}
                size="sm"
                variant="outline"
                className="gap-2 text-red-600 hover:text-red-700 hover:bg-red-50 border-red-200"
              >
                <ThumbsDown className="h-4 w-4" />
                Not Interested
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
