"use client";

import { CompanyCombobox } from "@/components/company-combobox";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { CompanyProvider, useCompany } from "@/contexts/CompanyContext";

function CompanyJobsContent() {
  const { selectedCompany, setSelectedCompany } = useCompany();

  return (
    <div className="container mx-auto py-8 space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Company Jobs</h1>
        <p className="text-muted-foreground mt-2">
          Search and select a company to view their job listings
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Select Company</CardTitle>
          <CardDescription>
            Search for a company by name. Start typing to see results.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <CompanyCombobox
            value={selectedCompany}
            onSelect={setSelectedCompany}
            placeholder="Search companies..."
            className="max-w-md"
          />
        </CardContent>
      </Card>

      {selectedCompany && (
        <Card>
          <CardHeader>
            <CardTitle>Selected Company</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h3 className="text-xl font-semibold">{selectedCompany.name}</h3>
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

            {selectedCompany.industry && (
              <div>
                <span className="text-sm font-medium">Industry:</span>{" "}
                <span className="text-sm">{selectedCompany.industry}</span>
              </div>
            )}

            {selectedCompany.description && (
              <div>
                <p className="text-sm text-muted-foreground">
                  {selectedCompany.description}
                </p>
              </div>
            )}

            <div className="pt-4 border-t">
              <p className="text-sm text-muted-foreground">
                Job listings for this company will be displayed here.
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default function CompanyJobsPage() {
  return (
    <CompanyProvider>
      <CompanyJobsContent />
    </CompanyProvider>
  );
}
