"use client";

import { cvBuilderApi } from "@/lib/api/cv-builder";
import {
  CVBuilderCreate,
  CVBuilderDocument,
  CVBuilderUpdate,
  CVScore,
  CVTemplate,
  EnhanceBulletsRequest,
  EnhancementSuggestion,
  EnhanceSummaryRequest,
} from "@/lib/types/cv-builder";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createContext, ReactNode, useContext, useState } from "react";
import { toast } from "sonner";

interface CVBuilderContextType {
  // CV Data
  currentCV: CVBuilderDocument | null;
  cvList: CVBuilderDocument[];
  templates: CVTemplate[];
  isLoading: boolean;
  isLoadingList: boolean;
  isLoadingTemplates: boolean;
  error: Error | null;

  // CV Selection
  setCurrentCVId: (cvId: string | null) => void;
  selectedTemplateId: string | null;
  setSelectedTemplateId: (templateId: string) => void;

  // CV Operations
  createCV: (data: CVBuilderCreate) => Promise<CVBuilderDocument>;
  updateCV: (data: CVBuilderUpdate) => Promise<void>;
  deleteCV: (cvId: string) => Promise<void>;
  selectCV: (cvId: string) => void;
  setPrimaryCV: (cvId: string) => Promise<void>;
  isCreating: boolean;

  // Enhancement Operations
  enhanceBullets: (
    data: EnhanceBulletsRequest
  ) => Promise<EnhancementSuggestion>;
  enhanceSummary: (
    data: EnhanceSummaryRequest
  ) => Promise<EnhancementSuggestion>;
  isEnhancing: boolean;
  isEnhancingBullets: boolean;

  // Scoring Operations
  scoreCV: () => Promise<CVScore>;
  isScoring: boolean;

  // Export Operations
  exportCV: (templateId: string) => Promise<void>;
  isExporting: boolean;

  // Template Operations
  selectTemplate: (templateId: string) => Promise<void>;
}

const CVBuilderContext = createContext<CVBuilderContextType | undefined>(
  undefined
);

export function CVBuilderProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [selectedCVId, setSelectedCVId] = useState<string | null>(null);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(
    null
  );

  // Fetch all CVs
  const {
    data: cvList = [],
    isLoading: isLoadingCVs,
    error: cvError,
  } = useQuery({
    queryKey: ["cv-builder", "list"],
    queryFn: () => cvBuilderApi.getMyCVs({ authStrategy: "refresh" }),
    retry: 1,
  });

  // Fetch templates
  const { data: templates = [], isLoading: isLoadingTemplates } = useQuery({
    queryKey: ["cv-builder", "templates"],
    queryFn: () => cvBuilderApi.getTemplates({ authStrategy: "refresh" }),
    retry: 1,
    staleTime: 1000 * 60 * 60, // 1 hour
  });

  // Get current CV (selected or primary)
  const currentCVId = selectedCVId || cvList.find((cv) => cv.is_primary)?._id;
  const currentCV = cvList.find((cv) => cv._id === currentCVId) || null;

  // Create CV mutation
  const createCVMutation = useMutation({
    mutationFn: (data: CVBuilderCreate) =>
      cvBuilderApi.createCV(data, { authStrategy: "refresh" }),
    onSuccess: (newCV) => {
      queryClient.invalidateQueries({ queryKey: ["cv-builder", "list"] });
      setSelectedCVId(newCV._id || null);
      toast.success("CV created successfully!");
    },
    onError: (error) => {
      toast.error(
        error instanceof Error ? error.message : "Failed to create CV"
      );
    },
  });

  // Update CV mutation
  const updateCVMutation = useMutation({
    mutationFn: async (data: CVBuilderUpdate) => {
      if (!currentCVId) {
        throw new Error("No CV selected");
      }
      return cvBuilderApi.updateCV(currentCVId, data, {
        authStrategy: "refresh",
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cv-builder", "list"] });
      toast.success("CV updated!");
    },
    onError: (error) => {
      toast.error(
        error instanceof Error ? error.message : "Failed to update CV"
      );
    },
  });

  // Delete CV mutation
  const deleteCVMutation = useMutation({
    mutationFn: (cvId: string) =>
      cvBuilderApi.deleteCV(cvId, { authStrategy: "refresh" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cv-builder", "list"] });
      setSelectedCVId(null);
      toast.success("CV deleted!");
    },
    onError: (error) => {
      toast.error(
        error instanceof Error ? error.message : "Failed to delete CV"
      );
    },
  });

  // Set primary CV mutation
  const setPrimaryCVMutation = useMutation({
    mutationFn: (cvId: string) =>
      cvBuilderApi.setPrimaryCV(cvId, { authStrategy: "refresh" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cv-builder", "list"] });
      toast.success("Primary CV updated!");
    },
    onError: (error) => {
      toast.error(
        error instanceof Error ? error.message : "Failed to set primary CV"
      );
    },
  });

  // Enhance bullets mutation
  const enhanceBulletsMutation = useMutation({
    mutationFn: async (data: EnhanceBulletsRequest) => {
      if (!currentCVId) {
        throw new Error("No CV selected");
      }
      return cvBuilderApi.enhanceBullets(currentCVId, data, {
        authStrategy: "refresh",
      });
    },
    onError: (error) => {
      toast.error(
        error instanceof Error ? error.message : "Failed to enhance bullets"
      );
    },
  });

  // Enhance summary mutation
  const enhanceSummaryMutation = useMutation({
    mutationFn: async (data: EnhanceSummaryRequest) => {
      if (!currentCVId) {
        throw new Error("No CV selected");
      }
      return cvBuilderApi.enhanceSummary(currentCVId, data, {
        authStrategy: "refresh",
      });
    },
    onError: (error) => {
      toast.error(
        error instanceof Error ? error.message : "Failed to enhance summary"
      );
    },
  });

  // Score CV mutation
  const scoreCVMutation = useMutation({
    mutationFn: async () => {
      if (!currentCVId) {
        throw new Error("No CV selected");
      }
      return cvBuilderApi.scoreCV(currentCVId, { authStrategy: "refresh" });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cv-builder", "list"] });
      toast.success("CV scored successfully!");
    },
    onError: (error) => {
      toast.error(
        error instanceof Error ? error.message : "Failed to score CV"
      );
    },
  });

  // Export CV mutation
  const exportCVMutation = useMutation({
    mutationFn: async (templateId: string) => {
      if (!currentCVId) {
        throw new Error("No CV selected");
      }
      const blob = await cvBuilderApi.exportCV(
        currentCVId,
        { template_id: templateId },
        { authStrategy: "refresh" }
      );

      // Download the file
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${currentCV?.contact_info.full_name || "CV"}_Resume.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    },
    onSuccess: () => {
      toast.success("CV exported successfully!");
    },
    onError: (error) => {
      toast.error(
        error instanceof Error ? error.message : "Failed to export CV"
      );
    },
  });

  // Select template
  const selectTemplate = async (templateId: string) => {
    await updateCVMutation.mutateAsync({ selected_template: templateId });
  };

  const value: CVBuilderContextType = {
    // Data
    currentCV,
    cvList,
    templates,
    isLoading: isLoadingCVs || isLoadingTemplates,
    isLoadingList: isLoadingCVs,
    isLoadingTemplates,
    error: cvError as Error | null,

    // CV Selection
    setCurrentCVId: setSelectedCVId,
    selectedTemplateId,
    setSelectedTemplateId,

    // CV Operations
    createCV: async (data) => createCVMutation.mutateAsync(data),
    updateCV: async (data) => {
      await updateCVMutation.mutateAsync(data);
    },
    deleteCV: async (cvId) => {
      await deleteCVMutation.mutateAsync(cvId);
    },
    selectCV: setSelectedCVId,
    setPrimaryCV: async (cvId) => {
      await setPrimaryCVMutation.mutateAsync(cvId);
    },
    isCreating: createCVMutation.isPending,

    // Enhancement Operations
    enhanceBullets: async (data) => enhanceBulletsMutation.mutateAsync(data),
    enhanceSummary: async (data) => enhanceSummaryMutation.mutateAsync(data),
    isEnhancing:
      enhanceBulletsMutation.isPending || enhanceSummaryMutation.isPending,
    isEnhancingBullets: enhanceBulletsMutation.isPending,

    // Scoring Operations
    scoreCV: async () => scoreCVMutation.mutateAsync(),
    isScoring: scoreCVMutation.isPending,

    // Export Operations
    exportCV: async (templateId) => {
      await exportCVMutation.mutateAsync(templateId);
    },
    isExporting: exportCVMutation.isPending,

    // Template Operations
    selectTemplate,
  };

  return (
    <CVBuilderContext.Provider value={value}>
      {children}
    </CVBuilderContext.Provider>
  );
}

export function useCVBuilder() {
  const context = useContext(CVBuilderContext);
  if (context === undefined) {
    throw new Error("useCVBuilder must be used within a CVBuilderProvider");
  }
  return context;
}
