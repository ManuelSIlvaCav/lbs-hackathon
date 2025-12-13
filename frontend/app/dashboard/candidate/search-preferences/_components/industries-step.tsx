"use client";

import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useEffect, useRef, useState } from "react";

interface IndustriesStepProps {
  data: any;
  onChange: (data: any) => void;
}

const INDUSTRIES = [
  "Financial Services",
  "Technology",
  "Healthcare",
  "E-commerce",
  "Education",
  "Media & Entertainment",
  "Gaming",
  "Travel & Hospitality",
  "Real Estate",
  "Energy & Utilities",
  "Manufacturing",
  "Automotive",
  "Retail",
  "Telecommunications",
  "Consulting",
  "Government",
  "Non-profit",
  "Cryptocurrency",
  "Artificial Intelligence",
  "Cybersecurity",
];

export function IndustriesStep({ data, onChange }: IndustriesStepProps) {
  const onChangeRef = useRef(onChange);
  onChangeRef.current = onChange;

  const [favouriteIndustries, setFavouriteIndustries] = useState<string[]>(
    data.favourite_industries || []
  );
  const [hiddenIndustries, setHiddenIndustries] = useState<string[]>(
    data.hidden_industries || []
  );
  const [customIndustry, setCustomIndustry] = useState("");

  useEffect(() => {
    onChangeRef.current({
      favourite_industries: favouriteIndustries,
      hidden_industries: hiddenIndustries,
    });
  }, [favouriteIndustries, hiddenIndustries]);

  const toggleFavourite = (industry: string) => {
    if (favouriteIndustries.includes(industry)) {
      setFavouriteIndustries(favouriteIndustries.filter((i) => i !== industry));
    } else {
      setFavouriteIndustries([...favouriteIndustries, industry]);
      // Remove from hidden if it was there
      setHiddenIndustries(hiddenIndustries.filter((i) => i !== industry));
    }
  };

  const toggleHidden = (industry: string) => {
    if (hiddenIndustries.includes(industry)) {
      setHiddenIndustries(hiddenIndustries.filter((i) => i !== industry));
    } else {
      setHiddenIndustries([...hiddenIndustries, industry]);
      // Remove from favourite if it was there
      setFavouriteIndustries(favouriteIndustries.filter((i) => i !== industry));
    }
  };

  const addCustomIndustry = () => {
    if (customIndustry.trim() && !INDUSTRIES.includes(customIndustry.trim())) {
      setFavouriteIndustries([...favouriteIndustries, customIndustry.trim()]);
      setCustomIndustry("");
    }
  };

  return (
    <div className="space-y-8">
      {/* Favourite Industries */}
      <div>
        <h2 className="text-2xl font-semibold mb-2 font-sora">
          Favourite industries
        </h2>
        <p className="text-muted-foreground mb-6 font-inter">
          Select industries you're most interested in working in
        </p>

        <div className="grid grid-cols-2 gap-3">
          {INDUSTRIES.map((industry) => {
            const isFavourite = favouriteIndustries.includes(industry);
            const isHidden = hiddenIndustries.includes(industry);

            return (
              <Label
                key={industry}
                htmlFor={`industry-${industry}`}
                className={`flex items-center space-x-3 p-4 rounded-lg cursor-pointer transition-colors ${
                  isFavourite
                    ? "bg-green-200 hover:bg-green-300"
                    : isHidden
                    ? "bg-red-100 hover:bg-red-200"
                    : "bg-muted/50 hover:bg-muted"
                }`}
              >
                <Checkbox
                  id={`industry-${industry}`}
                  checked={isFavourite}
                  onCheckedChange={() => toggleFavourite(industry)}
                  className={
                    isFavourite
                      ? "border-green-600 data-[state=checked]:bg-green-600"
                      : ""
                  }
                />
                <span className="flex-1 font-medium font-inter">
                  {industry}
                </span>
              </Label>
            );
          })}
        </div>

        {/* Add custom industry */}
        <div className="mt-4">
          <div className="flex gap-2">
            <Input
              placeholder="Add custom industry..."
              value={customIndustry}
              onChange={(e) => setCustomIndustry(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  addCustomIndustry();
                }
              }}
            />
            <button
              type="button"
              onClick={addCustomIndustry}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 whitespace-nowrap"
            >
              Add Industry
            </button>
          </div>
        </div>
      </div>

      {/* Hidden Industries */}
      <div className="border-t pt-6">
        <h2 className="text-2xl font-semibold mb-2 font-sora">
          Hidden industries
        </h2>
        <p className="text-muted-foreground mb-6 font-inter">
          Select industries you want to avoid in your job search
        </p>

        <div className="grid grid-cols-2 gap-3">
          {INDUSTRIES.filter(
            (industry) => !favouriteIndustries.includes(industry)
          ).map((industry) => {
            const isHidden = hiddenIndustries.includes(industry);

            return (
              <Label
                key={industry}
                htmlFor={`hidden-industry-${industry}`}
                className={`flex items-center space-x-3 p-4 rounded-lg cursor-pointer transition-colors ${
                  isHidden
                    ? "bg-red-100 hover:bg-red-200"
                    : "bg-muted/50 hover:bg-muted"
                }`}
              >
                <Checkbox
                  id={`hidden-industry-${industry}`}
                  checked={isHidden}
                  onCheckedChange={() => toggleHidden(industry)}
                  className={
                    isHidden
                      ? "border-red-500 data-[state=checked]:bg-red-500"
                      : ""
                  }
                />
                <span className="flex-1 font-medium font-inter">
                  {industry}
                </span>
              </Label>
            );
          })}
        </div>
      </div>
    </div>
  );
}
