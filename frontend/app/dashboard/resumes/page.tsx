"use client";

import { SidebarTrigger } from "@/components/ui/sidebar";
import { candidateApi } from "@/lib/api/candidate";
import { getAccessToken, getUser } from "@/lib/auth";
import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { CandidateDataView } from "./_components/candidate-data-view";
import { UploadResumeDialog } from "./_components/upload-resume-dialog";

export default function ResumesPage() {
  const router = useRouter();
  const [candidateId, setCandidateId] = useState<string | null>(null);
  const [isAuthChecking, setIsAuthChecking] = useState(true);

  // Check authentication and get candidate_id from user data
  useEffect(() => {
    const user = getUser();
    const token = getAccessToken();

    if (!user || !token) {
      // Not authenticated, redirect to login
      router.push("/login");
      return;
    }

    if (!user.candidate_id) {
      // User doesn't have a candidate profile yet
      // You might want to create one automatically or show a setup screen
      console.warn("User does not have a candidate profile");
      // For now, we'll allow them to stay on the page
      // In production, you might want to create a candidate profile here
    }

    setCandidateId(user.candidate_id || null);
    setIsAuthChecking(false);
  }, [router]);

  // Fetch candidate data using react-query with JWT authentication
  const {
    data: candidate,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["candidate", candidateId],
    queryFn: () => {
      if (!candidateId) {
        throw new Error("No candidate ID available");
      }
      return candidateApi.getCandidate(candidateId, {
        authStrategy: "refresh", // Auto-refresh tokens if expired
      });
    },
    enabled: !!candidateId && !isAuthChecking, // Only run query if we have candidate_id
  });

  // Show loading state while checking authentication
  if (isAuthChecking) {
    return (
      <div className="flex h-full w-full items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  // Show message if no candidate profile
  if (!candidateId) {
    return (
      <div className="flex h-full w-full items-center justify-center">
        <div className="text-center max-w-md">
          <h2 className="text-2xl font-semibold mb-2">
            No Candidate Profile Found
          </h2>
          <p className="text-muted-foreground mb-4">
            You need to create a candidate profile before you can manage
            resumes.
          </p>
          {/* TODO: Add button to create candidate profile */}
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full w-full flex-col">
      {/* Header */}
      <header className="flex items-center justify-between border-b bg-background px-6 py-8">
        <div className="flex items-center gap-4">
          <SidebarTrigger />
          <div>
            <h1 className="text-3xl font-semibold">My Resumes</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              This is where you'll find all your resumes. Create new ones,
              delete those you no longer need, or use any resume when applying
              to jobs.
            </p>
          </div>
        </div>

        <UploadResumeDialog candidateId={candidateId} />
      </header>

      {/* Content Area - Candidate Data */}
      <div className="flex-1 overflow-auto px-6 py-6">
        <CandidateDataView
          candidate={candidate}
          isLoading={isLoading}
          error={error}
        />
      </div>
    </div>
  );
}
