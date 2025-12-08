"use client";

import { Button } from "@/components/ui/button";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Company } from "@/contexts/admin-company-context";
import { cn } from "@/lib/utils";
import { Check, ChevronsUpDown, Loader2 } from "lucide-react";
import * as React from "react";

interface CompanyComboboxProps {
  value?: Company | null;
  onSelect: (company: Company | null) => void;
  placeholder?: string;
  className?: string;
}

export function CompanyCombobox({
  value,
  onSelect,
  placeholder = "Select company...",
  className,
}: CompanyComboboxProps) {
  const [open, setOpen] = React.useState(false);
  const [searchQuery, setSearchQuery] = React.useState("");
  const [companies, setCompanies] = React.useState<Company[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [hasMore, setHasMore] = React.useState(true);
  const [skip, setSkip] = React.useState(0);
  const limit = 20;

  // Debounce timer ref
  const debounceTimer = React.useRef<NodeJS.Timeout | null>(null);

  // Fetch companies from API
  const fetchCompanies = React.useCallback(
    async (query: string, skipCount: number, append: boolean = false) => {
      setLoading(true);
      try {
        const params = new URLSearchParams({
          query: query,
          skip: skipCount.toString(),
          limit: limit.toString(),
        });

        const response = await fetch(
          `${
            process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
          }/api/companies/search?${params}`
        );

        if (!response.ok) {
          throw new Error("Failed to fetch companies");
        }

        const data = await response.json();

        if (append) {
          setCompanies((prev) => [...prev, ...data.companies]);
        } else {
          setCompanies(data.companies);
        }

        setHasMore(data.has_more);
        setSkip(skipCount);
      } catch (error) {
        console.error("Error fetching companies:", error);
      } finally {
        setLoading(false);
      }
    },
    []
  );

  // Debounced search effect
  React.useEffect(() => {
    // Clear existing timer
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    // Set new timer
    debounceTimer.current = setTimeout(() => {
      fetchCompanies(searchQuery, 0, false);
    }, 300); // 300ms debounce

    // Cleanup
    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
    };
  }, [searchQuery, fetchCompanies]);

  // Load more companies
  const loadMore = React.useCallback(() => {
    if (!loading && hasMore) {
      fetchCompanies(searchQuery, skip + limit, true);
    }
  }, [loading, hasMore, searchQuery, skip, fetchCompanies]);

  // Handle scroll to bottom
  const handleScroll = React.useCallback(
    (e: React.UIEvent<HTMLDivElement>) => {
      const target = e.target as HTMLDivElement;
      const bottom =
        target.scrollHeight - target.scrollTop <= target.clientHeight + 50;

      if (bottom) {
        loadMore();
      }
    },
    [loadMore]
  );

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className={cn("w-full justify-between", className)}
        >
          {value ? value.name : placeholder}
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[400px] p-0" align="start">
        <Command shouldFilter={false}>
          <CommandInput
            placeholder="Search companies..."
            value={searchQuery}
            onValueChange={setSearchQuery}
          />
          <CommandList onScroll={handleScroll}>
            <CommandEmpty>
              {loading ? (
                <div className="flex items-center justify-center py-6">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span className="ml-2">Loading...</span>
                </div>
              ) : (
                "No company found."
              )}
            </CommandEmpty>
            <CommandGroup>
              {companies.map((company, index) => {
                const isSelected = value && value?._id === company._id;
                return (
                  <CommandItem
                    key={
                      company._id
                        ? `company-${company._id}`
                        : `company-index-${index}`
                    }
                    value={company.name}
                    onSelect={() => {
                      console.log("CompanyCombobox - Selecting company:", {
                        company,
                        currentValue: value,
                        isSelected,
                        willSelect: isSelected ? null : company,
                      });
                      // Toggle selection: if already selected, deselect; otherwise select
                      onSelect(isSelected ? null : company);
                      setOpen(false);
                    }}
                  >
                    <Check
                      className={cn(
                        "mr-2 h-4 w-4",
                        isSelected ? "opacity-100" : "opacity-0"
                      )}
                    />
                    <div className="flex flex-col">
                      <span className="font-medium">{company.name}</span>
                      {company.industries && company.industries.length > 0 && (
                        <span className="text-xs text-muted-foreground">
                          {company.industries.join(", ")}
                        </span>
                      )}
                    </div>
                  </CommandItem>
                );
              })}
              {loading && companies.length > 0 && (
                <div className="flex items-center justify-center py-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                </div>
              )}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
