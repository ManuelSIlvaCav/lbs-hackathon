"use client";

import { Checkbox } from "@/components/ui/checkbox";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { ChevronDown, ChevronUp } from "lucide-react";
import { useEffect, useRef, useState } from "react";

interface LocationStepProps {
  data: any;
  onChange: (data: any) => void;
}

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

  // Calculate initial open regions based on data
  const getInitialOpenRegions = () => {
    const openRegions: Record<string, boolean> = {
      UK: false,
      EU: false,
      US: false,
    };

    if (data.locations && Array.isArray(data.locations)) {
      Object.keys(LOCATION_GROUPS).forEach((region) => {
        const regionLocations =
          LOCATION_GROUPS[region as keyof typeof LOCATION_GROUPS];
        const hasSelection = regionLocations.some((city) =>
          data.locations.includes(city)
        );
        if (hasSelection) {
          openRegions[region] = true;
        }
      });
    }
    console.log("Initial open regions:", { openRegions, data });
    return openRegions;
  };

  const [openRegions, setOpenRegions] = useState<Record<string, boolean>>(
    getInitialOpenRegions()
  );
  const [selectedRegions, setSelectedRegions] = useState<string[]>([]);
  const [locations, setLocations] = useState<string[]>(data.locations || []);
  const [visaSponsorship, setVisaSponsorship] = useState<{
    uk: boolean;
    eu: boolean;
    us: boolean;
  }>(
    data.visa_sponsorship || {
      uk: false,
      eu: false,
      us: false,
    }
  );
  const [languages, setLanguages] = useState<string[]>(data.languages || []);

  // Sync state when data prop changes (e.g., when API data loads)
  useEffect(() => {
    if (data.locations && data.locations.length > 0) {
      setLocations(data.locations);
    }
    if (data.visa_sponsorship) {
      setVisaSponsorship(data.visa_sponsorship);
    }
    if (data.languages && data.languages.length > 0) {
      setLanguages(data.languages);
    }
  }, [data.locations, data.visa_sponsorship, data.languages]);

  // Determine which regions are selected based on locations and auto-open them
  useEffect(() => {
    const regions = new Set<string>();
    const newOpenRegions: Record<string, boolean> = {};

    Object.keys(LOCATION_GROUPS).forEach((region) => {
      const regionLocations =
        LOCATION_GROUPS[region as keyof typeof LOCATION_GROUPS];
      const hasSelection = regionLocations.some((city) =>
        locations.includes(city)
      );

      if (hasSelection) {
        regions.add(region);
        newOpenRegions[region] = true;
      } else {
        newOpenRegions[region] = openRegions[region] || false;
      }
    });

    setSelectedRegions(Array.from(regions));
    setOpenRegions(newOpenRegions);
  }, [locations]);

  useEffect(() => {
    onChangeRef.current({
      locations,
      visa_sponsorship: visaSponsorship,
      languages,
    });
  }, [locations, visaSponsorship, languages]);

  const toggleRegion = (region: string) => {
    const regionLocations =
      LOCATION_GROUPS[region as keyof typeof LOCATION_GROUPS];
    const allSelected = regionLocations.every((loc) => locations.includes(loc));

    if (allSelected) {
      // Deselect all locations in this region
      setLocations(locations.filter((loc) => !regionLocations.includes(loc)));
    } else {
      // Select all locations in this region
      const newLocations = [...new Set([...locations, ...regionLocations])];
      setLocations(newLocations);
    }
  };

  const toggleLocation = (location: string) => {
    setLocations((prev) =>
      prev.includes(location)
        ? prev.filter((l) => l !== location)
        : [...prev, location]
    );
  };

  const toggleLanguage = (language: string) => {
    setLanguages((prev) =>
      prev.includes(language)
        ? prev.filter((l) => l !== language)
        : [...prev, language]
    );
  };

  if (Object.keys(data).length === 0) {
    return <Skeleton className="h-48 w-full rounded-md" />;
  }

  console.log("Rendering LocationStep with data:", { data });

  return (
    <div className="space-y-8">
      {/* Location Selection by Region */}
      <div>
        <h2 className="text-2xl font-semibold mb-2 font-sora">
          Where would you like to work?
        </h2>
        <p className="text-muted-foreground mb-6 font-inter">
          Select regions and cities you would commute to
        </p>

        {/* Region Collapsibles */}
        <div className="space-y-3">
          {Object.keys(LOCATION_GROUPS).map((region) => {
            const regionLocations =
              LOCATION_GROUPS[region as keyof typeof LOCATION_GROUPS];
            const allSelected = regionLocations.every((loc) =>
              locations.includes(loc)
            );
            const someSelected = regionLocations.some((loc) =>
              locations.includes(loc)
            );
            const selectedCount = regionLocations.filter((loc) =>
              locations.includes(loc)
            ).length;
            const totalCount = regionLocations.length;
            const isOpen = openRegions[region];

            return (
              <Collapsible
                key={region}
                open={isOpen}
                onOpenChange={(open) =>
                  setOpenRegions((prev) => ({ ...prev, [region]: open }))
                }
              >
                <div
                  className={`rounded-lg border-2 transition-all ${
                    allSelected
                      ? "bg-green-200 border-green-300"
                      : someSelected
                      ? "bg-green-100 border-green-200"
                      : "bg-muted/50 border-muted"
                  }`}
                >
                  <CollapsibleTrigger asChild>
                    <div className="flex items-center justify-between p-4 cursor-pointer hover:opacity-80 transition-opacity">
                      <div className="flex-1">
                        <div className="flex items-center gap-3">
                          <h3 className="text-lg font-semibold font-sora">
                            {region}
                          </h3>
                          <span className="text-sm text-muted-foreground font-inter">
                            {selectedCount}/{totalCount} selected
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleRegion(region);
                          }}
                          className="px-3 py-1 text-sm font-medium font-inter rounded-md transition-colors hover:bg-white/50"
                        >
                          {allSelected ? "Deselect all" : "Select all"}
                        </button>
                        <div className="p-2">
                          {isOpen ? (
                            <ChevronUp className="h-4 w-4" />
                          ) : (
                            <ChevronDown className="h-4 w-4" />
                          )}
                        </div>
                      </div>
                    </div>
                  </CollapsibleTrigger>

                  <CollapsibleContent>
                    <div className="px-4 pb-4 pt-2 border-t">
                      <div className="grid grid-cols-2 gap-3">
                        {regionLocations.map((city) => (
                          <Label
                            key={city}
                            htmlFor={`location-${region}-${city}`}
                            className={`flex items-center space-x-3 p-3 rounded-lg cursor-pointer transition-colors ${
                              locations.includes(city)
                                ? "bg-green-200 hover:bg-green-300"
                                : "bg-white/50 hover:bg-white"
                            }`}
                          >
                            <Checkbox
                              id={`location-${region}-${city}`}
                              checked={locations.includes(city)}
                              onCheckedChange={() => toggleLocation(city)}
                              className={
                                locations.includes(city)
                                  ? "border-green-600 data-[state=checked]:bg-green-600"
                                  : ""
                              }
                            />
                            <span className="flex-1 font-medium font-inter">
                              {city}
                            </span>
                          </Label>
                        ))}
                      </div>
                    </div>
                  </CollapsibleContent>
                </div>
              </Collapsible>
            );
          })}
        </div>
      </div>

      {/* Visa Sponsorship - Conditional based on regions */}
      {selectedRegions.length > 0 && (
        <div className="border-t pt-6">
          <h3 className="text-lg font-semibold mb-4 font-sora">
            Visa sponsorship
          </h3>
          <p className="text-sm text-muted-foreground mb-4 font-inter">
            Select if you require visa sponsorship for the selected regions
          </p>

          <div className="space-y-3">
            {selectedRegions.includes("UK") && (
              <Label
                htmlFor="visa-uk"
                className="flex items-center space-x-3 cursor-pointer"
              >
                <Checkbox
                  id="visa-uk"
                  checked={visaSponsorship.uk}
                  onCheckedChange={(checked) =>
                    setVisaSponsorship({
                      ...visaSponsorship,
                      uk: checked as boolean,
                    })
                  }
                  className={
                    visaSponsorship.uk
                      ? "border-green-600 data-[state=checked]:bg-green-600"
                      : ""
                  }
                />
                <span className="font-inter">
                  I require visa sponsorship for UK
                </span>
              </Label>
            )}

            {selectedRegions.includes("EU") && (
              <Label
                htmlFor="visa-eu"
                className="flex items-center space-x-3 cursor-pointer"
              >
                <Checkbox
                  id="visa-eu"
                  checked={visaSponsorship.eu}
                  onCheckedChange={(checked) =>
                    setVisaSponsorship({
                      ...visaSponsorship,
                      eu: checked as boolean,
                    })
                  }
                  className={
                    visaSponsorship.eu
                      ? "border-green-600 data-[state=checked]:bg-green-600"
                      : ""
                  }
                />
                <span className="font-inter">
                  I require visa sponsorship for EU
                </span>
              </Label>
            )}

            {selectedRegions.includes("US") && (
              <Label
                htmlFor="visa-us"
                className="flex items-center space-x-3 cursor-pointer"
              >
                <Checkbox
                  id="visa-us"
                  checked={visaSponsorship.us}
                  onCheckedChange={(checked) =>
                    setVisaSponsorship({
                      ...visaSponsorship,
                      us: checked as boolean,
                    })
                  }
                  className={
                    visaSponsorship.us
                      ? "border-green-600 data-[state=checked]:bg-green-600"
                      : ""
                  }
                />
                <span className="font-inter">
                  I require visa sponsorship for US
                </span>
              </Label>
            )}
          </div>
        </div>
      )}

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
