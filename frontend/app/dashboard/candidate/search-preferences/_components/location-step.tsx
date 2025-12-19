"use client";

import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { useJobSearchFilters } from "@/contexts/job-search-filters-context";
import { useEffect, useRef, useState } from "react";

interface LocationStepProps {
  data: any;
  onChange: (data: any) => void;
}

const LANGUAGES = [
  "English",
  "Spanish",
  "French",
  "German",
  "Italian",
  "Portuguese",
  "Dutch",
  "Mandarin",
  "Arabic",
  "Hindi",
  "Urdu",
  "Japanese",
  "Korean",
  "Russian",
  "Turkish",
];

export function LocationStep({ data, onChange }: LocationStepProps) {
  const onChangeRef = useRef(onChange);
  onChangeRef.current = onChange;

  const { searchOptions, isLoading: isLoadingOptions } = useJobSearchFilters();

  const [selectedCountries, setSelectedCountries] = useState<string[]>(
    data.locations || []
  );
  const [languages, setLanguages] = useState<string[]>(data.languages || []);

  // Sync state when data prop changes (e.g., when API data loads)
  useEffect(() => {
    if (data.locations && data.locations.length > 0) {
      setSelectedCountries(data.locations);
    }
    if (data.languages && data.languages.length > 0) {
      setLanguages(data.languages);
    }
  }, [data.locations, data.languages]);

  useEffect(() => {
    onChangeRef.current({
      locations: selectedCountries,
      languages,
    });
  }, [selectedCountries, languages]);

  const toggleCountry = (country: string) => {
    setSelectedCountries((prev) =>
      prev.includes(country)
        ? prev.filter((c) => c !== country)
        : [...prev, country]
    );
  };

  const toggleLanguage = (language: string) => {
    setLanguages((prev) =>
      prev.includes(language)
        ? prev.filter((l) => l !== language)
        : [...prev, language]
    );
  };

  if (Object.keys(data).length === 0 || isLoadingOptions) {
    return <Skeleton className="h-48 w-full rounded-md" />;
  }

  if (!searchOptions?.countries || searchOptions.countries.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No location data available. Please trigger search options update.
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Country Selection */}
      <div>
        <h2 className="text-2xl font-semibold mb-2 font-sora">
          Where would you like to work?
        </h2>
        <p className="text-muted-foreground mb-6 font-inter">
          Select countries where you want to find opportunities (city selection
          coming soon)
        </p>

        {/* Country Checkboxes */}
        <div className="grid grid-cols-2 gap-3">
          {searchOptions.countries.map((country) => (
            <Label
              key={country}
              htmlFor={`country-${country}`}
              className={`flex items-center space-x-3 p-4 rounded-lg cursor-pointer transition-colors border-2 ${
                selectedCountries.includes(country)
                  ? "bg-green-50 border-green-500 hover:bg-green-100"
                  : "bg-white border-muted hover:border-muted-foreground/50"
              }`}
            >
              <Checkbox
                id={`country-${country}`}
                checked={selectedCountries.includes(country)}
                onCheckedChange={() => toggleCountry(country)}
                className={
                  selectedCountries.includes(country)
                    ? "border-green-600 data-[state=checked]:bg-green-600"
                    : ""
                }
              />
              <span className="flex-1 font-medium font-inter">{country}</span>
            </Label>
          ))}
        </div>

        {selectedCountries.length > 0 && (
          <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-800 font-inter">
              <strong className="font-semibold">Selected countries:</strong>{" "}
              {selectedCountries.join(", ")}
            </p>
          </div>
        )}
      </div>

      {/* Languages - Wrap style */}
      <div className="border-t pt-6">
        <h3 className="text-lg font-semibold mb-2 font-sora">
          Which languages can you work in?
        </h3>
        <p className="text-sm text-muted-foreground mb-4 font-inter">
          Add any languages other than English you are comfortable working in,
          so we can show you relevant jobs.
        </p>

        <div className="flex flex-wrap gap-2">
          {LANGUAGES.map((language) => (
            <button
              key={language}
              onClick={() => toggleLanguage(language)}
              className={`px-4 py-2 rounded-full transition-all font-inter ${
                languages.includes(language)
                  ? "bg-green-200 hover:bg-green-300 text-foreground"
                  : "bg-muted/50 hover:bg-muted text-muted-foreground"
              }`}
            >
              {language}
            </button>
          ))}
        </div>

        {languages.length > 0 && (
          <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-800 font-inter">
              <strong className="font-semibold">Selected languages:</strong>{" "}
              {languages.join(", ")}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
