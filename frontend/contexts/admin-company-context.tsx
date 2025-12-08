"use client";

import { createContext, ReactNode, useContext, useState } from "react";

export interface Company {
  _id: string;
  name: string;
  company_url?: string;
  industries?: string[];
  description?: string;
  logo_url?: string;
}

interface SearchPageContextType {
  selectedCompany: Company | null;
  setSelectedCompany: (company: Company | null) => void;
  refreshTrigger: number;
  triggerRefresh: () => void;
}

const SearchPageContext = createContext<SearchPageContextType | undefined>(
  undefined
);

export function SearchPageProvider({ children }: { children: ReactNode }) {
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const triggerRefresh = () => {
    setRefreshTrigger((prev) => prev + 1);
  };

  return (
    <SearchPageContext.Provider
      value={{
        selectedCompany,
        setSelectedCompany,
        refreshTrigger,
        triggerRefresh,
      }}
    >
      {children}
    </SearchPageContext.Provider>
  );
}

export function useSearchPage() {
  const context = useContext(SearchPageContext);
  if (context === undefined) {
    throw new Error("useSearchPage must be used within a SearchPageProvider");
  }
  return context;
}
