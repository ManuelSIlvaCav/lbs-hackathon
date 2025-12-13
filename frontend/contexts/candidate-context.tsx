"use client";

import { candidateApi } from "@/lib/api/candidate";
import { getUser } from "@/lib/auth";
import { Candidate } from "@/lib/types/candidate";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createContext, ReactNode, useContext } from "react";
import { toast } from "sonner";

interface CandidateContextType {
  candidate: Candidate | undefined;
  candidateId: string | null;
  isLoading: boolean;
  error: Error | null;
  updateSearchPreferences: (preferences: any) => Promise<void>;
  uploadAndParseCV: (file: File) => Promise<void>;
  updateMetadata: (metadata: Candidate["metadata"]) => Promise<void>;
  isUpdating: boolean;
  isUploading: boolean;
}

const CandidateContext = createContext<CandidateContextType | undefined>(
  undefined
);

export function CandidateProvider({ children }: { children: ReactNode }) {
  const user = getUser();
  const candidateId = user?.candidate_id || null;
  const queryClient = useQueryClient();

  // Fetch candidate data
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
        authStrategy: "refresh",
      });
    },
    enabled: !!candidateId,
    retry: 1,
  });

  // Update search preferences mutation
  const updateSearchPreferencesMutation = useMutation({
    mutationFn: async (preferences: any) => {
      if (!candidateId) {
        throw new Error("No candidate ID available");
      }
      return candidateApi.updateSearchPreferences(candidateId, preferences, {
        authStrategy: "refresh",
      });
    },
    onSuccess: (updatedCandidate) => {
      queryClient.setQueryData(["candidate", candidateId], updatedCandidate);
      toast.success("Search preferences updated successfully!");
    },
    onError: (error) => {
      toast.error(
        error instanceof Error
          ? error.message
          : "Failed to update search preferences"
      );
    },
  });

  // Upload and parse CV mutation
  const uploadAndParseCVMutation = useMutation({
    mutationFn: async (file: File) => {
      if (!candidateId) {
        throw new Error("No candidate ID available");
      }
      return candidateApi.uploadAndParseCV(candidateId, file, {
        authStrategy: "refresh",
      });
    },
    onSuccess: async (updatedCandidate) => {
      queryClient.setQueryData(["candidate", candidateId], updatedCandidate);
      await queryClient.invalidateQueries({
        queryKey: ["candidate", candidateId],
      });
      toast.success("CV uploaded and parsed successfully!");
    },
    onError: (error) => {
      toast.error(
        error instanceof Error ? error.message : "Failed to upload CV"
      );
    },
  });

  // Update metadata mutation
  const updateMetadataMutation = useMutation({
    mutationFn: async (metadata: Candidate["metadata"]) => {
      if (!candidateId) {
        throw new Error("No candidate ID available");
      }
      return candidateApi.updateCandidateMetadata(candidateId, metadata);
    },
    onSuccess: (updatedCandidate) => {
      queryClient.setQueryData(["candidate", candidateId], updatedCandidate);
      toast.success("Candidate data updated successfully!");
    },
    onError: (error) => {
      toast.error(
        error instanceof Error ? error.message : "Failed to update candidate"
      );
    },
  });

  const value: CandidateContextType = {
    candidate,
    candidateId,
    isLoading,
    error,
    updateSearchPreferences: async (preferences) => {
      await updateSearchPreferencesMutation.mutateAsync(preferences);
    },
    uploadAndParseCV: async (file) => {
      await uploadAndParseCVMutation.mutateAsync(file);
    },
    updateMetadata: async (metadata) => {
      await updateMetadataMutation.mutateAsync(metadata);
    },
    isUpdating: updateSearchPreferencesMutation.isPending,
    isUploading: uploadAndParseCVMutation.isPending,
  };

  return (
    <CandidateContext.Provider value={value}>
      {children}
    </CandidateContext.Provider>
  );
}

export function useCandidateContext() {
  const context = useContext(CandidateContext);
  if (context === undefined) {
    throw new Error(
      "useCandidateContext must be used within a CandidateProvider"
    );
  }
  return context;
}
