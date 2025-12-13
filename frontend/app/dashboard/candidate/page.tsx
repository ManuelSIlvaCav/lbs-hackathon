"use client";

import { SidebarTrigger } from "@/components/ui/sidebar";
import { useCandidateContext } from "@/contexts/candidate-context";
import { CandidateDataView } from "./_components/candidate-data-view";
import { UploadResumeDialog } from "./_components/upload-resume-dialog";

export default function CandidatePage() {
  const { candidate, candidateId, isLoading, error } = useCandidateContext();

  // Show loading state
  if (isLoading) {
    return (
      <div className="flex h-full w-full items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground font-inter">Loading...</p>
        </div>
      </div>
    );
  }

  // Show message if no candidate profile
  if (!candidateId) {
    return (
      <div className="flex h-full w-full items-center justify-center">
        <div className="text-center max-w-md">
          <h2 className="text-2xl font-semibold font-sora mb-2">
            No Candidate Profile Found
          </h2>
          <p className="text-muted-foreground font-inter mb-4">
            You need to create a candidate profile before you can manage
            resumes.
          </p>
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
            <h1 className="text-3xl font-semibold font-sora">
              Candidate Profile
            </h1>
            <p className="mt-1 text-sm text-muted-foreground font-inter">
              Manage your professional profile, resumes, and career information.
              Upload and organize your documents for job applications.
            </p>
          </div>
        </div>

        <UploadResumeDialog />
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
