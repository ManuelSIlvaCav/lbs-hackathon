"use client";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { SearchPageProvider } from "@/contexts/admin-company-context";
import { EnrichTab } from "./enrich-tab";
import { SearchTab } from "./search-tab";

export default function SearchCompanyPage() {
  return (
    <SearchPageProvider>
      <div className="container mx-auto py-8 px-4 space-y-6">
        <div className="space-y-2">
          <h1 className="text-3xl font-bold tracking-tight">
            Search Companies
          </h1>
          <p className="text-muted-foreground">
            Search for companies using external data providers or enrich
            existing companies
          </p>
        </div>

        <Tabs defaultValue="search" className="w-full">
          <TabsList className="mb-4">
            <TabsTrigger value="search">Search</TabsTrigger>
            <TabsTrigger value="enrich">Enrich</TabsTrigger>
          </TabsList>

          <TabsContent value="search" className="mt-0">
            <SearchTab />
          </TabsContent>

          <TabsContent value="enrich" className="mt-0">
            <EnrichTab />
          </TabsContent>
        </Tabs>
      </div>
    </SearchPageProvider>
  );
}
