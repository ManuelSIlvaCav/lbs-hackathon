"use client";

import { CompanyCombobox } from "@/components/company-combobox";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Company } from "@/contexts/admin-company-context";
import { Search, X } from "lucide-react";

interface JobSearchFiltersProps {
  selectedCompany: Company | null;
  selectedCountry: string;
  selectedCity: string;
  selectedOrigin: string;
  onCompanyChange: (company: Company | null) => void;
  onCountryChange: (country: string) => void;
  onCityChange: (city: string) => void;
  onOriginChange: (origin: string) => void;
  onSearch: () => void;
  onClear: () => void;
}

// Location groups matching the backend structure
const LOCATION_GROUPS = {
  UK: [
    "Remote",
    "London",
    "Birmingham",
    "Bristol",
    "Cambridge",
    "Cardiff",
    "Edinburgh",
    "Glasgow",
    "Leeds",
    "Manchester",
    "Nottingham",
  ],
  EU: [
    "Remote",
    "Berlin",
    "Paris",
    "Amsterdam",
    "Barcelona",
    "Dublin",
    "Copenhagen",
    "Stockholm",
    "Zurich",
    "Vienna",
  ],
  US: [
    "Remote",
    "San Francisco",
    "New York",
    "Austin",
    "Seattle",
    "Boston",
    "Los Angeles",
    "Chicago",
    "Denver",
    "Miami",
  ],
};

const JOB_ORIGINS = [
  { value: "linkedin", label: "LinkedIn" },
  { value: "greenhouse", label: "Greenhouse" },
  { value: "careers", label: "Careers Page" },
];

export function JobSearchFilters({
  selectedCompany,
  selectedCountry,
  selectedCity,
  selectedOrigin,
  onCompanyChange,
  onCountryChange,
  onCityChange,
  onOriginChange,
  onSearch,
  onClear,
}: JobSearchFiltersProps) {
  // Get cities for selected country
  const cities =
    selectedCountry &&
    LOCATION_GROUPS[selectedCountry as keyof typeof LOCATION_GROUPS]
      ? LOCATION_GROUPS[selectedCountry as keyof typeof LOCATION_GROUPS]
      : [];

  // Clear city if country changes and city is not in new country's list
  const handleCountryChange = (country: string) => {
    const actualCountry = country === "all" ? "" : country;
    onCountryChange(actualCountry);
    if (actualCountry && selectedCity && !cities.includes(selectedCity)) {
      onCityChange("");
    }
  };

  const handleCityChange = (city: string) => {
    onCityChange(city === "all" ? "" : city);
  };

  const handleOriginChange = (origin: string) => {
    onOriginChange(origin === "all" ? "" : origin);
  };

  const hasActiveFilters =
    selectedCompany || selectedCountry || selectedCity || selectedOrigin;

  return (
    <div className="border-b bg-background px-6 py-6">
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold font-sora">Search Filters</h2>
          {hasActiveFilters && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onClear}
              className="text-muted-foreground hover:text-foreground"
            >
              <X className="mr-2 h-4 w-4" />
              Clear all
            </Button>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Company Search */}
          <div className="space-y-2">
            <label className="text-sm font-medium font-inter">Company</label>
            <CompanyCombobox
              value={selectedCompany}
              onSelect={onCompanyChange}
              placeholder="Select company..."
              className="w-full"
            />
          </div>

          {/* Country */}
          {/* <div className="space-y-2">
            <label className="text-sm font-medium font-inter">Country</label>
            <Select
              value={selectedCountry || "all"}
              onValueChange={handleCountryChange}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select country..." />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Countries</SelectItem>
                {Object.keys(LOCATION_GROUPS).map((country) => (
                  <SelectItem key={country} value={country}>
                    {country}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div> */}

          {/* City */}
          {/* <div className="space-y-2">
            <label className="text-sm font-medium font-inter">City</label>
            <Select
              value={selectedCity || "all"}
              onValueChange={handleCityChange}
              disabled={!selectedCountry}
            >
              <SelectTrigger className="w-full">
                <SelectValue
                  placeholder={
                    selectedCountry ? "Select city..." : "Select country first"
                  }
                />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Cities</SelectItem>
                {cities.map((city) => (
                  <SelectItem key={city} value={city}>
                    {city}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div> */}

          {/* Job Source */}
          <div className="space-y-2">
            <label className="text-sm font-medium font-inter">Job Source</label>
            <Select
              value={selectedOrigin || "all"}
              onValueChange={handleOriginChange}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select source..." />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Sources</SelectItem>
                {JOB_ORIGINS.map((origin) => (
                  <SelectItem key={origin.value} value={origin.value}>
                    {origin.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="flex justify-start">
          <Button onClick={onSearch} className="gap-2">
            <Search className="h-4 w-4" />
            Search Jobs
          </Button>
        </div>
      </div>
    </div>
  );
}
