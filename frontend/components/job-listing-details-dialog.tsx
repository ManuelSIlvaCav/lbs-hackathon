"use client";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Separator } from "@/components/ui/separator";
import { JobListing } from "@/lib/types/job-listing";
import { Copy, ExternalLink } from "lucide-react";
import { toast } from "sonner";

interface JobListingDetailsDialogProps {
  job: JobListing | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function JobListingDetailsDialog({
  job,
  open,
  onOpenChange,
}: JobListingDetailsDialogProps) {
  if (!job) return null;

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    toast.success(`${label} copied to clipboard`);
  };

  const formatDate = (dateString?: string | null) => {
    if (!dateString) return "N/A";
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return "N/A";
    }
  };

  const InfoRow = ({
    label,
    value,
    copyable = false,
  }: {
    label: string;
    value: string | null | undefined;
    copyable?: boolean;
  }) => (
    <div className="grid grid-cols-3 gap-2 py-2">
      <span className="text-sm font-medium text-muted-foreground">{label}</span>
      <span className="col-span-2 text-sm flex items-center gap-2">
        <span className="break-all">{value || "N/A"}</span>
        {copyable && value && (
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6 shrink-0"
            onClick={() => copyToClipboard(value, label)}
          >
            <Copy className="h-3 w-3" />
          </Button>
        )}
      </span>
    </div>
  );

  const ArrayRow = ({
    label,
    values,
  }: {
    label: string;
    values: string[] | null | undefined;
  }) => (
    <div className="grid grid-cols-3 gap-2 py-2">
      <span className="text-sm font-medium text-muted-foreground">{label}</span>
      <span className="col-span-2 text-sm">
        {values && values.length > 0 ? values.join(", ") : "N/A"}
      </span>
    </div>
  );

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            Job Listing Details
            <Button variant="ghost" size="sm" asChild className="h-7 text-xs">
              <a
                href={job.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1"
              >
                <ExternalLink className="h-3 w-3" />
                Open
              </a>
            </Button>
          </DialogTitle>
          <DialogDescription>{job.title || "Untitled Job"}</DialogDescription>
        </DialogHeader>

        <div className="max-h-[calc(90vh-120px)] overflow-y-auto pr-4">
          <div className="space-y-4">
            {/* IDs Section */}
            <div>
              <h3 className="text-sm font-semibold mb-2">IDs</h3>
              <div className="space-y-1">
                <InfoRow label="Job ID" value={job._id} copyable />
                <InfoRow label="Company ID" value={job.company_id} copyable />
              </div>
            </div>

            <Separator />

            {/* Basic Information */}
            <div>
              <h3 className="text-sm font-semibold mb-2">Basic Information</h3>
              <div className="space-y-1">
                <InfoRow label="Title" value={job.title} />
                <InfoRow label="Company" value={job.company} />
                <InfoRow label="URL" value={job.url} copyable />
                <InfoRow label="Origin" value={job.origin} />
                <InfoRow label="Origin Domain" value={job.origin_domain} />
              </div>
            </div>

            <Separator />

            {/* Location Information */}
            <div>
              <h3 className="text-sm font-semibold mb-2">Location</h3>
              <div className="space-y-1">
                <InfoRow label="Location" value={job.location} />
                <InfoRow label="City" value={job.city} />
                <InfoRow label="State" value={job.state} />
                <InfoRow label="Country" value={job.country} />
              </div>
            </div>

            <Separator />

            {/* Job Details */}
            <div>
              <h3 className="text-sm font-semibold mb-2">Job Details</h3>
              <div className="space-y-1">
                <InfoRow label="Employment Type" value={job.employement_type} />
                <InfoRow
                  label="Work Arrangement"
                  value={job.work_arrangement}
                />
                <InfoRow label="Status" value={job.status} />
                <InfoRow label="Listing Status" value={job.listing_status} />
                <InfoRow label="Source Status" value={job.source_status} />
                <ArrayRow
                  label="Profile Categories"
                  values={job.profile_categories}
                />
                <ArrayRow label="Role Titles" values={job.role_titles} />
              </div>
            </div>

            <Separator />

            {/* Salary Information */}
            <div>
              <h3 className="text-sm font-semibold mb-2">Salary</h3>
              <div className="space-y-1">
                <InfoRow
                  label="Min"
                  value={job.salary_range_min?.toLocaleString()}
                />
                <InfoRow
                  label="Max"
                  value={job.salary_range_max?.toLocaleString()}
                />
                <InfoRow label="Currency" value={job.salary_currency} />
              </div>
            </div>

            <Separator />

            {/* Dates */}
            <div>
              <h3 className="text-sm font-semibold mb-2">Dates</h3>
              <div className="space-y-1">
                <InfoRow label="Posted At" value={formatDate(job.posted_at)} />
                <InfoRow
                  label="Last Seen At"
                  value={formatDate(job.last_seen_at)}
                />
                <InfoRow
                  label="Created At"
                  value={formatDate(job.created_at)}
                />
                <InfoRow
                  label="Updated At"
                  value={formatDate(job.updated_at)}
                />
              </div>
            </div>

            <Separator />

            {/* Company Information */}
            {job.company_info && (
              <>
                <div>
                  <h3 className="text-sm font-semibold mb-2">
                    Company Information
                  </h3>
                  <div className="space-y-1">
                    <InfoRow label="Name" value={job.company_info.name} />
                    <InfoRow
                      label="Company URL"
                      value={job.company_info.company_url}
                      copyable
                    />
                    <InfoRow
                      label="LinkedIn URL"
                      value={job.company_info.linkedin_url}
                      copyable
                    />
                    <InfoRow label="Domain" value={job.company_info.domain} />
                    <ArrayRow
                      label="Industries"
                      values={job.company_info.industries}
                    />
                    {job.company_info.description && (
                      <div className="grid grid-cols-3 gap-2 py-2">
                        <span className="text-sm font-medium text-muted-foreground">
                          Description
                        </span>
                        <span className="col-span-2 text-sm">
                          {job.company_info.description}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
                <Separator />
              </>
            )}

            {/* Description */}
            {job.description && (
              <div>
                <h3 className="text-sm font-semibold mb-2">Description</h3>
                <div className="text-sm whitespace-pre-wrap bg-muted p-3 rounded-md max-h-60 overflow-y-auto">
                  {job.description}
                </div>
              </div>
            )}

            {/* Metadata */}
            {job.metadata?.categorization_schema && (
              <>
                <Separator />
                <div>
                  <h3 className="text-sm font-semibold mb-2">
                    Categorization Metadata
                  </h3>
                  <div className="text-sm bg-muted p-3 rounded-md">
                    <pre className="whitespace-pre-wrap text-xs overflow-x-auto">
                      {JSON.stringify(
                        job.metadata.categorization_schema,
                        null,
                        2
                      )}
                    </pre>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
