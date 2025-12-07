"use client";

import { CompanyCombobox } from "@/components/company-combobox";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useState } from "react";
import { CreateCompanyDialog } from "./create-company-dialog";

interface Company {
  id: string;
  name: string;
  company_url?: string;
  industry?: string;
  description?: string;
  logo_url?: string;
}

export default function AdminCompaniesPage() {
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null);

  const handleCompanyCreated = (company: Company) => {
    setSelectedCompany(company);
  };

  return (
    <div className="container mx-auto py-8 space-y-6">
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
            onSelect={setSelectedCompany}
            placeholder="Search companies..."
            className="max-w-md"
          />
        </CardContent>
      </Card>

      {selectedCompany && (
        <Card>
          <CardHeader>
            <CardTitle>Company Details</CardTitle>
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

              {selectedCompany.industry && (
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    Industry
                  </p>
                  <p className="text-sm">{selectedCompany.industry}</p>
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

              <div className="pt-4 border-t">
                <p className="text-xs text-muted-foreground">
                  Company ID: {selectedCompany.id}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
