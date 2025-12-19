"use client";

import { JobListingCard } from "@/components/job-listings";
import { JobSearchFilters } from "@/components/job-search-filters";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Company } from "@/contexts/admin-company-context";
import { jobListingApi } from "@/lib/api/job-listing";
import { useInfiniteQuery } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";

export default function JobListingsPage() {
  // Search filters
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null);
  const [selectedCountry, setSelectedCountry] = useState("");
  const [selectedCity, setSelectedCity] = useState("");
  const [selectedOrigin, setSelectedOrigin] = useState("");
  const [selectedProfileCategory, setSelectedProfileCategory] = useState("");
  const [selectedRoleTitle, setSelectedRoleTitle] = useState("");

  // Ref for infinite scroll observer
  const observerTarget = useRef<HTMLDivElement>(null);

  // Infinite query for job listings
  const {
    data,
    isLoading,
    isError,
    error,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery({
    queryKey: [
      "jobListings",
      selectedCompany?._id,
      selectedCountry,
      selectedCity,
      selectedOrigin,
      selectedProfileCategory,
      selectedRoleTitle,
    ],
    queryFn: ({ pageParam = 0 }) =>
      jobListingApi.searchJobListings({
        company_id: selectedCompany?._id,
        country: selectedCountry || undefined,
        city: selectedCity || undefined,
        origin: selectedOrigin || undefined,
        profile_category: selectedProfileCategory || undefined,
        role_title: selectedRoleTitle || undefined,
        skip: pageParam,
        limit: 20,
      }),
    getNextPageParam: (lastPage) => {
      return lastPage.has_more ? lastPage.skip + lastPage.limit : undefined;
    },
    initialPageParam: 0,
  });

  // Setup intersection observer for infinite scroll
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasNextPage && !isFetchingNextPage) {
          fetchNextPage();
        }
      },
      { threshold: 0.1 }
    );

    const currentTarget = observerTarget.current;
    if (currentTarget) {
      observer.observe(currentTarget);
    }

    return () => {
      if (currentTarget) {
        observer.unobserve(currentTarget);
      }
    };
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

  const handleSearch = () => {
    // Search is automatically triggered by query key changes
    console.log("Searching with filters:", {
      company: selectedCompany?.name,
      country: selectedCountry,
      city: selectedCity,
      origin: selectedOrigin,
      profileCategory: selectedProfileCategory,
      roleTitle: selectedRoleTitle,
    });
  };

  const handleClearFilters = () => {
    setSelectedCompany(null);
    setSelectedCountry("");
    setSelectedCity("");
    setSelectedOrigin("");
    setSelectedProfileCategory("");
    setSelectedRoleTitle("");
  };

  // Flatten all pages into single array
  const allJobs = data?.pages.flatMap((page) => page.items) ?? [];
  const totalCount = data?.pages[0]?.total ?? 0;

  return (
    <div className="flex h-full w-full flex-col">
      {/* Header */}
      <header className="flex items-center justify-between border-b bg-background px-6 py-8">
        <div className="flex items-center gap-4">
          <SidebarTrigger />
          <div>
            <h1 className="text-3xl font-semibold font-sora">Job Listings</h1>
            <p className="mt-1 text-sm text-muted-foreground font-inter">
              {totalCount > 0 &&
                `${totalCount} job${totalCount !== 1 ? "s" : ""} found`}
            </p>
          </div>
        </div>
      </header>

      {/* Search Filters */}
      <JobSearchFilters
        selectedCompany={selectedCompany}
        selectedCountry={selectedCountry}
        selectedCity={selectedCity}
        selectedOrigin={selectedOrigin}
        selectedProfileCategory={selectedProfileCategory}
        selectedRoleTitle={selectedRoleTitle}
        onCompanyChange={setSelectedCompany}
        onCountryChange={setSelectedCountry}
        onCityChange={setSelectedCity}
        onOriginChange={setSelectedOrigin}
        onProfileCategoryChange={setSelectedProfileCategory}
        onRoleTitleChange={setSelectedRoleTitle}
        onSearch={handleSearch}
        onClear={handleClearFilters}
      />

      {/* Content Area */}
      <div className="flex-1 overflow-auto px-6 py-6">
        {isLoading ? (
          <div className="flex h-full items-center justify-center">
            <div className="text-center space-y-2">
              <Loader2 className="h-8 w-8 animate-spin mx-auto text-muted-foreground" />
              <p className="text-muted-foreground font-inter">
                Loading job listings...
              </p>
            </div>
          </div>
        ) : isError ? (
          <div className="flex h-full items-center justify-center">
            <div className="text-center space-y-2">
              <p className="text-destructive">Error loading job listings</p>
              <p className="text-sm text-muted-foreground font-inter">
                {error instanceof Error ? error.message : "Unknown error"}
              </p>
            </div>
          </div>
        ) : allJobs.length === 0 ? (
          <div className="flex h-full items-center justify-center">
            <div className="text-center space-y-2">
              <p className="text-muted-foreground font-inter">
                No job listings found
              </p>
              <p className="text-sm text-muted-foreground font-inter">
                Try adjusting your filters or add a new job listing
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Job Listings Grid */}
            <div className="grid gap-4">
              {allJobs.map((job) => (
                <JobListingCard
                  key={`${job._id}`}
                  job={job as any}
                  onEnrich={undefined}
                />
              ))}
            </div>

            {/* Loading More Indicator */}
            {isFetchingNextPage && (
              <div className="flex items-center justify-center py-6">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                <span className="ml-2 text-muted-foreground font-inter">
                  Loading more...
                </span>
              </div>
            )}

            {/* Intersection Observer Target */}
            <div ref={observerTarget} className="h-4" />

            {/* End of Results */}
            {!hasNextPage && allJobs.length > 0 && (
              <div className="text-center py-6">
                <p className="text-sm text-muted-foreground font-inter">
                  No more results
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
