"use client";

import { CompanyCombobox } from "@/components/company-combobox";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useSearchPage } from "@/contexts/admin-company-context";
import { Loader2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

export function EnrichTab() {
  const { selectedCompany, setSelectedCompany, triggerRefresh } =
    useSearchPage();
  const [enriching, setEnriching] = useState(false);

  console.log("EnrichTab - Current selectedCompany:", selectedCompany);

  const handleCompanySelect = (company: any) => {
    console.log("EnrichTab - handleCompanySelect called with:", company);
    setSelectedCompany(company);
  };

  const handleEnrich = async () => {
    if (!selectedCompany) {
      toast.error("Please select a company to enrich");
      return;
    }

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

      // Trigger refresh and clear selection
      triggerRefresh();
      setSelectedCompany(null);
    } catch (error: any) {
      console.error("Enrich error:", error);
      toast.error(error.message || "Failed to enrich company");
    } finally {
      setEnriching(false);
    }
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Enrich Company Data</CardTitle>
          <CardDescription>
            Select an existing company to enrich with Apollo.io data
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 pt-6">
          <div className="flex gap-2">
            <CompanyCombobox
              value={selectedCompany}
              onSelect={handleCompanySelect}
              placeholder="Select company to enrich..."
              className="flex-1"
            />

            <Button
              onClick={handleEnrich}
              disabled={enriching || !selectedCompany}
            >
              {enriching ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Enriching...
                </>
              ) : (
                "Enrich"
              )}
            </Button>
          </div>

          {selectedCompany && (
            <div className="rounded-lg bg-muted p-4 space-y-2">
              <div className="space-y-1">
                <p className="text-sm font-medium">
                  <strong>Selected:</strong> {selectedCompany.name}
                </p>
                {selectedCompany.industries &&
                  selectedCompany.industries.length > 0 && (
                    <p className="text-sm text-muted-foreground">
                      <strong>Industries:</strong>{" "}
                      {selectedCompany.industries.join(", ")}
                    </p>
                  )}
              </div>
              <p className="text-xs text-muted-foreground border-t pt-2">
                This will fetch enriched data from Apollo.io and update the
                company with description, industries, logo, employee count,
                funding information, and more.
              </p>
            </div>
          )}

          {!selectedCompany && (
            <div className="rounded-lg border border-dashed p-4 text-center">
              <p className="text-sm text-muted-foreground">
                Select a company from the dropdown above to enrich its data with
                information from Apollo.io
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
