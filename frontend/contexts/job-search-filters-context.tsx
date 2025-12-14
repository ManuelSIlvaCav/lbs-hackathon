"use client";

import { useQuery } from "@tanstack/react-query";
import React, { createContext, useContext } from "react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface JobSearchOptions {
  origins: string[];
  profile_categories: string[];
  role_titles: string[];
  role_titles_by_category: Record<string, string[]>;
}

interface JobSearchFiltersContextType {
  searchOptions: JobSearchOptions | null;
  isLoading: boolean;
  error: Error | null;
}

const JobSearchFiltersContext = createContext<
  JobSearchFiltersContextType | undefined
>(undefined);

export function JobSearchFiltersProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const { data, isLoading, error } = useQuery<JobSearchOptions>({
    queryKey: ["jobSearchOptions"],
    queryFn: async () => {
      const response = await fetch(
        `${API_BASE_URL}/api/job-listings/search-options`
      );
      if (!response.ok) {
        throw new Error("Failed to fetch search options");
      }
      return response.json();
    },
    staleTime: 1000 * 60 * 60, // Cache for 1 hour
    gcTime: 1000 * 60 * 60 * 24, // Keep in cache for 24 hours
  });

  return (
    <JobSearchFiltersContext.Provider
      value={{
        searchOptions: data || null,
        isLoading,
        error: error as Error | null,
      }}
    >
      {children}
    </JobSearchFiltersContext.Provider>
  );
}

export function useJobSearchFilters() {
  const context = useContext(JobSearchFiltersContext);
  if (context === undefined) {
    throw new Error(
      "useJobSearchFilters must be used within a JobSearchFiltersProvider"
    );
  }
  return context;
}
