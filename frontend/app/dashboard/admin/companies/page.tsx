"use client";

import { CompanyCombobox } from "@/components/company-combobox";
import { JobListingDetailsDialog } from "@/components/job-listing-details-dialog";
import { JobListings } from "@/components/job-listings";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Company } from "@/contexts/admin-company-context";
import { useAuth } from "@/contexts/auth-context";
import { getCompanyJobListings } from "@/lib/api/company-jobs";
import { JobListing } from "@/lib/types/job-listing";
import { Briefcase, Loader2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { CreateCompanyDialog } from "./create-company-dialog";

export default function AdminCompaniesPage() {
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null);
  const [jobListings, setJobListings] = useState<JobListing[]>([]);
  const [isLoadingJobs, setIsLoadingJobs] = useState(false);
  const [showJobs, setShowJobs] = useState(false);
  const [enriching, setEnriching] = useState(false);
  const [selectedJob, setSelectedJob] = useState<JobListing | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const { token } = useAuth();

  const handleCompanyCreated = (company: Company) => {
    setSelectedCompany(company);
    setShowJobs(false);
    setJobListings([]);
  };

  const handleCompanySelect = (company: Company | null) => {
    setSelectedCompany(company);
    setShowJobs(false);
    setJobListings([]);
  };

  const handleGetJobs = async () => {
    if (!selectedCompany?._id) return;

    setIsLoadingJobs(true);
    setShowJobs(true);

    try {
      const jobs = await getCompanyJobListings(
        selectedCompany._id,
        token || undefined
      );
      setJobListings(jobs);
      toast.success(`Found ${jobs.length} job listings`);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to fetch job listings";
      toast.error(message);
      setShowJobs(false);
    } finally {
      setIsLoadingJobs(false);
    }
  };

  const handleJobEnriched = async () => {
    // Refresh job listings after enrichment
    if (selectedCompany?._id) {
      await handleGetJobs();
    }
  };

  const handleJobCardClick = (job: JobListing) => {
    setSelectedJob(job);
    setIsDialogOpen(true);
  };

  const handleEnrich = async () => {
    if (!selectedCompany?._id) return;

    setEnriching(true);

    try {
      const response = await fetch(
        `http://localhost:8000/api/companies/${selectedCompany._id}/lookup-details`,
        {
          method: "POST",
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to enrich company");
      }

      const enrichedCompany = await response.json();
      toast.success(
        `Successfully enriched ${enrichedCompany.name} with Apollo.io data`
      );

      // Update the selected company with enriched data
      setSelectedCompany(enrichedCompany);
    } catch (error: any) {
      console.error("Enrich error:", error);
      toast.error(error.message || "Failed to enrich company");
    } finally {
      setEnriching(false);
    }
  };

  // Check if company has description or industries (indicators of enrichment)
  const isEnriched =
    selectedCompany &&
    (selectedCompany.description ||
      (selectedCompany.industries && selectedCompany.industries.length > 0));

  return (
    <div className="container mx-auto py-8 space-y-6 px-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            Company Management
          </h1>
          <p className="text-muted-foreground mt-2">
            Search for companies or create new ones
          </p>
        </div>

        <CreateCompanyDialog onCompanyCreated={handleCompanyCreated} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Search Companies</CardTitle>
          <CardDescription>
            Search and select a company to view details
          </CardDescription>
        </CardHeader>
        <CardContent>
          <CompanyCombobox
            value={selectedCompany}
            onSelect={handleCompanySelect}
            placeholder="Search companies..."
            className="max-w-md"
          />
        </CardContent>
      </Card>

      {selectedCompany && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
            <CardTitle>Company Details</CardTitle>
            <div className="flex gap-2">
              {!selectedCompany.description && (
                <Button
                  onClick={handleEnrich}
                  disabled={enriching}
                  size="sm"
                  variant="default"
                  className="gap-2"
                >
                  {enriching ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Enriching...
                    </>
                  ) : (
                    "Enrich"
                  )}
                </Button>
              )}
              {isEnriched && (
                <Button
                  onClick={handleGetJobs}
                  disabled={isLoadingJobs}
                  size="sm"
                  variant="outline"
                  className="gap-2"
                >
                  <Briefcase className="h-4 w-4" />
                  {isLoadingJobs ? "Loading..." : "Get Jobs"}
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4">
              <div>
                <h3 className="text-xl font-semibold">
                  {selectedCompany.name}
                </h3>
                {selectedCompany.company_url && (
                  <a
                    href={selectedCompany.company_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-blue-600 hover:underline"
                  >
                    {selectedCompany.company_url}
                  </a>
                )}
              </div>

              {selectedCompany.industries &&
                selectedCompany.industries.length > 0 && (
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">
                      Industries
                    </p>
                    <p className="text-sm">
                      {selectedCompany.industries.join(", ")}
                    </p>
                  </div>
                )}

              {selectedCompany.description && (
                <div>
                  <p className="text-sm font-medium text-muted-foreground mb-1">
                    Description
                  </p>
                  <p className="text-sm">{selectedCompany.description}</p>
                </div>
              )}

              {selectedCompany.logo_url && (
                <div>
                  <p className="text-sm font-medium text-muted-foreground mb-2">
                    Logo
                  </p>
                  <img
                    src={selectedCompany.logo_url}
                    alt={`${selectedCompany.name} logo`}
                    className="h-16 w-auto object-contain"
                  />
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {showJobs && (
        <JobListings
          jobs={jobListings}
          isLoading={isLoadingJobs}
          onJobEnriched={handleJobEnriched}
          isAdmin={true}
          onCardClick={handleJobCardClick}
        />
      )}

      <JobListingDetailsDialog
        job={selectedJob}
        open={isDialogOpen}
        onOpenChange={setIsDialogOpen}
      />
    </div>
  );
}
