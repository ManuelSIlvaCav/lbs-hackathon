"use client";

import { SidebarTrigger } from "@/components/ui/sidebar";
import { candidateApi } from "@/lib/api/candidate";
import { useQuery } from "@tanstack/react-query";
import { CandidateDataView } from "./_components/candidate-data-view";
import { UploadResumeDialog } from "./_components/upload-resume-dialog";

export default function ResumesPage() {
  // Default candidate ID - replace with actual ID from your database
  const DEFAULT_CANDIDATE_ID = "692062c1ee4d1d50120c9f4a";

  // Fetch candidate data using react-query
  const {
    data: candidate,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["candidate", DEFAULT_CANDIDATE_ID],
    queryFn: () => candidateApi.getCandidate(DEFAULT_CANDIDATE_ID),
  });

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

        <UploadResumeDialog candidateId={DEFAULT_CANDIDATE_ID} />
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
