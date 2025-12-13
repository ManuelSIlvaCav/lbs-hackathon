"use client";

import { EmptyCandidateCV } from "@/components/empty-candidate-cv";
import { useCandidateContext } from "@/contexts/candidate-context";
import { Candidate, CategorizationSchema } from "@/lib/types/candidate";
import { Loader2 } from "lucide-react";
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
  const { updateMetadata, isUpdating } = useCandidateContext();

  const handleSave = async (schema: CategorizationSchema) => {
    await updateMetadata({
      categorization_schema: schema,
    });
  };

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center space-y-2">
          <Loader2 className="h-8 w-8 animate-spin mx-auto text-muted-foreground" />
          <p className="text-muted-foreground font-inter">
            Loading candidate data...
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    if (error.message === "Failed to fetch candidate: Not Found") {
      return <EmptyCandidateCV />;
    }
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center space-y-2">
          <p className="text-destructive font-sora">
            Error loading candidate data
          </p>
          <p className="text-sm text-muted-foreground font-inter">
            {error instanceof Error ? error.message : "Unknown error"}
          </p>
        </div>
      </div>
    );
  }

  if (candidate && !candidate.metadata?.categorization_schema) {
    return <EmptyCandidateCV />;
  }

  if (candidate?.metadata?.categorization_schema) {
    return (
      <div className="max-w-5xl">
        <div className="mb-6">
          <h2 className="text-2xl font-bold font-sora">{candidate.name}</h2>
          {candidate.email && (
            <p className="text-muted-foreground font-inter">
              {candidate.email}
            </p>
          )}
        </div>

        <CategorizationSchemaForm
          schema={candidate.metadata.categorization_schema}
          onSave={handleSave}
          isSaving={isUpdating}
        />
      </div>
    );
  }

  return null;
}
