"use client";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Loader2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

interface Company {
  name: string;
  company_url?: string | null;
  linkedin_url?: string | null;
  logo_url?: string | null;
  domain?: string | null;
  industry?: string | null;
  description?: string | null;
}

interface SearchResponse {
  companies: Company[];
  total: number;
  page: number;
  per_page: number;
  provider: string;
}

export default function SearchCompanyPage() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<Company[]>([]);
  const [searchInfo, setSearchInfo] = useState<{
    total: number;
    provider: string;
  } | null>(null);

  const handleSearch = async () => {
    if (!query.trim()) {
      toast.error("Please enter a company name to search");
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(
        `http://localhost:8000/api/companies/provider-search?query=${encodeURIComponent(
          query
        )}&page=1&per_page=100`
      );

      if (!response.ok) {
        throw new Error("Search failed");
      }

      const data: SearchResponse = await response.json();
      setResults(data.companies);
      setSearchInfo({
        total: data.total,
        provider: data.provider,
      });

      if (data.companies.length === 0) {
        toast.info("No companies found");
      } else {
        toast.success(`Found ${data.companies.length} companies`);
      }
    } catch (error) {
      console.error("Search error:", error);
      toast.error("Failed to search companies");
      setResults([]);
      setSearchInfo(null);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !loading) {
      handleSearch();
    }
  };

  return (
    <div className="container mx-auto py-8 space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Search Companies</h1>
        <p className="text-muted-foreground mt-2">
          Search for companies using external data providers
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Search</CardTitle>
          <CardDescription>
            Enter a company name to search via Apollo.io
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              placeholder="Enter company name (e.g., OpenAI, Microsoft)..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={loading}
              className="flex-1"
            />
            <Button onClick={handleSearch} disabled={loading || !query.trim()}>
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Searching...
                </>
              ) : (
                "Search"
              )}
            </Button>
          </div>

          {searchInfo && (
            <div className="text-sm text-muted-foreground">
              Found {searchInfo.total} results via {searchInfo.provider}
            </div>
          )}
        </CardContent>
      </Card>

      {results.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-2xl font-semibold">Search Results</h2>

          <div className="grid gap-4 md:grid-cols-2">
            {results.map((company, index) => (
              <Card key={`${company.domain || company.name}-${index}`}>
                <CardHeader>
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <CardTitle className="text-lg">{company.name}</CardTitle>
                      {company.domain && (
                        <CardDescription className="mt-1">
                          {company.domain}
                        </CardDescription>
                      )}
                    </div>
                    {company.logo_url && (
                      <img
                        src={company.logo_url}
                        alt={`${company.name} logo`}
                        className="h-12 w-12 object-contain rounded"
                      />
                    )}
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  {company.company_url && (
                    <div>
                      <p className="text-xs font-medium text-muted-foreground mb-1">
                        Website
                      </p>
                      <a
                        href={company.company_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-blue-600 hover:underline break-all"
                      >
                        {company.company_url}
                      </a>
                    </div>
                  )}

                  {company.linkedin_url && (
                    <div>
                      <p className="text-xs font-medium text-muted-foreground mb-1">
                        LinkedIn
                      </p>
                      <a
                        href={company.linkedin_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-blue-600 hover:underline break-all"
                      >
                        {company.linkedin_url}
                      </a>
                    </div>
                  )}

                  {company.industry && (
                    <div>
                      <p className="text-xs font-medium text-muted-foreground mb-1">
                        Industry
                      </p>
                      <p className="text-sm">{company.industry}</p>
                    </div>
                  )}

                  {company.description && (
                    <div>
                      <p className="text-xs font-medium text-muted-foreground mb-1">
                        Description
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {company.description}
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {!loading && results.length === 0 && searchInfo && (
        <Card>
          <CardContent className="py-8 text-center text-muted-foreground">
            No companies found. Try a different search query.
          </CardContent>
        </Card>
      )}
    </div>
  );
}
