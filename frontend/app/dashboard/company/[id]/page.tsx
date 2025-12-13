"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/contexts/auth-context";
import { JobListing } from "@/lib/types/job-listing";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Building2,
  ExternalLink,
  Globe,
  Heart,
  Linkedin,
  Loader2,
} from "lucide-react";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
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

interface FollowedCompany {
  company_id: string;
  followed_at: string;
}

interface Candidate {
  _id: string;
  user_id: string;
  name: string;
  email?: string;
  followed_companies?: FollowedCompany[];
  created_at: string;
  updated_at: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function CompanyDetailPage() {
  const params = useParams();
  const companyId = params.id as string;
  const { user, token } = useAuth();
  const queryClient = useQueryClient();
  const [isFollowing, setIsFollowing] = useState(false);

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

  // Fetch candidate data to check followed companies
  const { data: candidate } = useQuery<Candidate>({
    queryKey: ["candidate", user?.candidate_id],
    queryFn: async () => {
      if (!user?.candidate_id || !token) {
        throw new Error("Not authenticated");
      }

      const response = await fetch(
        `${API_BASE_URL}/api/candidates/${user.candidate_id}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      if (!response.ok) {
        throw new Error("Failed to fetch candidate");
      }
      return response.json();
    },
    enabled: !!user?.candidate_id && !!token,
  });

  // Check if user is following this company based on candidate data
  useEffect(() => {
    if (candidate?.followed_companies) {
      const isCurrentlyFollowing = candidate.followed_companies.some(
        (fc) => fc.company_id === companyId
      );
      setIsFollowing(isCurrentlyFollowing);
    } else {
      setIsFollowing(false);
    }
  }, [candidate, companyId]);

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

  // Follow mutation
  const followMutation = useMutation({
    mutationFn: async () => {
      if (!user?.candidate_id || !token) {
        throw new Error("You must be logged in to follow companies");
      }

      const response = await fetch(
        `${API_BASE_URL}/api/candidates/${user.candidate_id}/follow/${companyId}`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to follow company");
      }

      return response.json();
    },
    onSuccess: (data) => {
      // Update the candidate query cache with the new data
      queryClient.setQueryData(["candidate", user?.candidate_id], data);
      toast.success(`Following ${company?.name}!`);
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to follow company");
    },
  });

  // Unfollow mutation
  const unfollowMutation = useMutation({
    mutationFn: async () => {
      if (!user?.candidate_id || !token) {
        throw new Error("You must be logged in to unfollow companies");
      }

      const response = await fetch(
        `${API_BASE_URL}/api/candidates/${user.candidate_id}/follow/${companyId}`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to unfollow company");
      }

      return response.json();
    },
    onSuccess: (data) => {
      // Update the candidate query cache with the new data
      queryClient.setQueryData(["candidate", user?.candidate_id], data);
      toast.success(`Unfollowed ${company?.name}`);
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to unfollow company");
    },
  });

  const handleToggleFollow = () => {
    if (!user?.candidate_id) {
      toast.error("You must be logged in to follow companies");
      return;
    }

    if (isFollowing) {
      unfollowMutation.mutate();
    } else {
      followMutation.mutate();
    }
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
                  variant={isFollowing ? "default" : "outline"}
                  size="sm"
                  onClick={handleToggleFollow}
                  disabled={
                    followMutation.isPending || unfollowMutation.isPending
                  }
                  className="gap-2"
                >
                  {followMutation.isPending || unfollowMutation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Heart
                      className={`h-4 w-4 ${isFollowing ? "fill-current" : ""}`}
                    />
                  )}
                  {isFollowing ? "Following" : "Follow"}
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
