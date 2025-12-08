"use client";

import { candidateApi } from "@/lib/api/candidate";
import { Candidate, CategorizationSchema } from "@/lib/types/candidate";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import { CategorizationSchemaForm } from "./categorization-schema-form";

interface CandidateDataViewProps {
  candidate?: Candidate;
  isLoading: boolean;
  error: Error | null;
}

export function CandidateDataView({
  candidate,
  isLoading,
  error,
}: CandidateDataViewProps) {
  const queryClient = useQueryClient();

  const updateMutation = useMutation({
    mutationFn: async (data: Candidate["metadata"]) => {
      if (!candidate?._id) {
        throw new Error("Candidate ID is missing");
      }
      return candidateApi.updateCandidateMetadata(candidate._id, data);
    },
    onSuccess: (updatedCandidate) => {
      queryClient.setQueryData(["candidate", candidate?._id], updatedCandidate);
      toast.success("Candidate data updated successfully!");
    },
    onError: (error) => {
      toast.error(
        error instanceof Error ? error.message : "Failed to update candidate"
      );
    },
  });

  const handleSave = async (schema: CategorizationSchema) => {
    await updateMutation.mutateAsync({
      categorization_schema: schema,
    });
  };

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center space-y-2">
          <Loader2 className="h-8 w-8 animate-spin mx-auto text-muted-foreground" />
          <p className="text-muted-foreground">Loading candidate data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center space-y-2">
          <p className="text-destructive">Error loading candidate data</p>
          <p className="text-sm text-muted-foreground">
            {error instanceof Error ? error.message : "Unknown error"}
          </p>
        </div>
      </div>
    );
  }

  if (candidate && !candidate.metadata?.categorization_schema) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <p className="text-muted-foreground">No CV data parsed yet.</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Upload and parse a CV to see categorization data.
          </p>
        </div>
      </div>
    );
  }

  if (candidate?.metadata?.categorization_schema) {
    return (
      <div className="max-w-5xl">
        <div className="mb-6">
          <h2 className="text-2xl font-bold">{candidate.name}</h2>
          {candidate.email && (
            <p className="text-muted-foreground">{candidate.email}</p>
          )}
        </div>

        <CategorizationSchemaForm
          schema={candidate.metadata.categorization_schema}
          onSave={handleSave}
          isSaving={updateMutation.isPending}
        />
      </div>
    );
  }

  return null;
}
