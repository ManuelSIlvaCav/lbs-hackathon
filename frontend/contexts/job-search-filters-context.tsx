"use client";

import { useQuery } from "@tanstack/react-query";
import React, { createContext, useContext } from "react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface SearchOptionsResponse {
  countries: string[];
  profile_categories: string[];
  role_titles: string[];
  updated_at: string;
  origins: string[];
  role_titles_by_category: Record<string, string[]>;
}

interface JobSearchOptions {
  origins: string[];
  countries: string[];
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
      const searchOptionsResponse = await fetch(
        `${API_BASE_URL}/api/search-options`
      );

      if (!searchOptionsResponse.ok) {
        throw new Error("Failed to fetch search options");
      }

      const searchOptions: SearchOptionsResponse =
        await searchOptionsResponse.json();

      // Return search options (origins and role_titles_by_category can be computed if needed)
      return {
        origins: searchOptions.origins, // No longer used
        countries: searchOptions.countries || [],
        profile_categories: searchOptions.profile_categories || [],
        role_titles: searchOptions.role_titles || [],
        role_titles_by_category: searchOptions.role_titles_by_category || {},
      };
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
