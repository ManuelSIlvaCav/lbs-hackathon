"use client";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { SidebarTrigger } from "@/components/ui/sidebar";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { jobListingApi } from "@/lib/api/job-listing";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ExternalLink, Loader2, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

export default function JobListingsPage() {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [jobUrl, setJobUrl] = useState("");
  const queryClient = useQueryClient();

  // Fetch job listings
  const {
    data: jobListings,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["jobListings"],
    queryFn: () => jobListingApi.getJobListings(),
  });

  // Create job listing mutation
  const createMutation = useMutation({
    mutationFn: (url: string) =>
      jobListingApi.createJobListing({
        url,
        title: "",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobListings"] });
      toast.success("Job listing added successfully!");
      setIsDialogOpen(false);
      setJobUrl("");
    },
    onError: (error) => {
      toast.error(
        error instanceof Error ? error.message : "Failed to add job listing"
      );
    },
  });

  // Delete job listing mutation
  const deleteMutation = useMutation({
    mutationFn: (jobId: string) => jobListingApi.deleteJobListing(jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobListings"] });
      toast.success("Job listing deleted successfully!");
    },
    onError: (error) => {
      toast.error(
        error instanceof Error ? error.message : "Failed to delete job listing"
      );
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!jobUrl.trim()) {
      toast.error("Please enter a job URL");
      return;
    }
    createMutation.mutate(jobUrl);
  };

  const handleDelete = (jobId: string) => {
    if (confirm("Are you sure you want to delete this job listing?")) {
      deleteMutation.mutate(jobId);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  return (
    <div className="flex h-full w-full flex-col">
      {/* Header */}
      <header className="flex items-center justify-between border-b bg-background px-6 py-8">
        <div className="flex items-center gap-4">
          <SidebarTrigger />
          <div>
            <h1 className="text-3xl font-semibold">Job Listings</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Manage and track job opportunities you're interested in
            </p>
          </div>
        </div>

        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Add Job
            </Button>
          </DialogTrigger>
          <DialogContent>
            <form onSubmit={handleSubmit}>
              <DialogHeader>
                <DialogTitle>Add New Job Listing</DialogTitle>
                <DialogDescription>
                  Enter the URL of the job listing you want to track.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="job-url">Job URL</Label>
                  <Input
                    id="job-url"
                    type="url"
                    placeholder="https://example.com/jobs/123"
                    value={jobUrl}
                    onChange={(e) => setJobUrl(e.target.value)}
                    required
                  />
                </div>
              </div>
              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setIsDialogOpen(false)}
                  disabled={createMutation.isPending}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={createMutation.isPending}>
                  {createMutation.isPending && (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  )}
                  Add Job
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </header>

      {/* Content Area */}
      <div className="flex-1 overflow-auto px-6 py-6">
        {isLoading ? (
          <div className="flex h-full items-center justify-center">
            <div className="text-center space-y-2">
              <Loader2 className="h-8 w-8 animate-spin mx-auto text-muted-foreground" />
              <p className="text-muted-foreground">Loading job listings...</p>
            </div>
          </div>
        ) : error ? (
          <div className="flex h-full items-center justify-center">
            <div className="text-center space-y-2">
              <p className="text-destructive">Error loading job listings</p>
              <p className="text-sm text-muted-foreground">
                {error instanceof Error ? error.message : "Unknown error"}
              </p>
            </div>
          </div>
        ) : !jobListings || jobListings.length === 0 ? (
          <div className="flex h-full items-center justify-center">
            <div className="text-center space-y-2">
              <p className="text-muted-foreground">No job listings yet</p>
              <p className="text-sm text-muted-foreground">
                Click "Add Job" to start tracking job opportunities
              </p>
            </div>
          </div>
        ) : (
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Company Name</TableHead>
                  <TableHead>Role Title</TableHead>
                  <TableHead>Location</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="w-[100px]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {jobListings.map((job) => {
                  // Extract data from metadata if available, fallback to top-level fields
                  const companyName =
                    job.metadata?.categorization_schema?.job_info
                      ?.company_name || job.company;
                  const roleTitle =
                    job.metadata?.categorization_schema?.job_info?.job_title ||
                    job.title;
                  const location =
                    job.metadata?.categorization_schema?.job_info?.location ||
                    job.location;

                  return (
                    <TableRow key={job._id}>
                      <TableCell className="font-medium">
                        {companyName || (
                          <span className="text-muted-foreground italic">
                            Not available
                          </span>
                        )}
                      </TableCell>
                      <TableCell>
                        {roleTitle ? (
                          <a
                            href={job.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-2 text-blue-600 hover:underline"
                          >
                            <ExternalLink className="h-4 w-4 shrink-0" />
                            <span>{roleTitle}</span>
                          </a>
                        ) : (
                          <a
                            href={job.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-2 text-blue-600 hover:underline"
                          >
                            <ExternalLink className="h-4 w-4 shrink-0" />
                            <span className="text-muted-foreground italic">
                              View Job
                            </span>
                          </a>
                        )}
                      </TableCell>
                      <TableCell>
                        {location || (
                          <span className="text-muted-foreground italic">
                            Not available
                          </span>
                        )}
                      </TableCell>
                      <TableCell>
                        <span
                          className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${
                            job.status === "active"
                              ? "bg-green-100 text-green-700"
                              : "bg-gray-100 text-gray-700"
                          }`}
                        >
                          {job.status}
                        </span>
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {formatDate(job.created_at)}
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(job._id)}
                          disabled={deleteMutation.isPending}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        )}
      </div>
    </div>
  );
}
