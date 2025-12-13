"use client";

import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { useEffect, useRef, useState } from "react";

interface CompanyStepProps {
  data: any;
  onChange: (data: any) => void;
}

const COMPANY_SIZES = [
  { value: "1-10", label: "Startup (1-10 employees)" },
  { value: "11-50", label: "Small (11-50 employees)" },
  { value: "51-200", label: "Scale-up (51-200 employees)" },
  { value: "201-500", label: "Mid-size (201-500 employees)" },
  { value: "501-1000", label: "Large (501-1,000 employees)" },
  { value: "1001-5000", label: "Enterprise (1,001-5,000 employees)" },
  { value: "5001+", label: "Corporation (5,001+ employees)" },
];

export function CompanyStep({ data, onChange }: CompanyStepProps) {
  const onChangeRef = useRef(onChange);
  onChangeRef.current = onChange;

  const [companySize, setCompanySize] = useState<string[]>(
    data.company_size || []
  );

  useEffect(() => {
    onChangeRef.current({
      company_size: companySize,
      followed_companies: data.followed_companies || [],
      hidden_companies: data.hidden_companies || [],
    });
  }, [companySize, data.followed_companies, data.hidden_companies]);

  const toggleSize = (size: string) => {
    if (companySize.includes(size)) {
      setCompanySize(companySize.filter((s) => s !== size));
    } else {
      setCompanySize([...companySize, size]);
    }
  };

  return (
    <div className="space-y-8">
      {/* Company Size */}
      <div>
        <h2 className="text-2xl font-semibold mb-2 font-sora">Company size</h2>
        <p className="text-muted-foreground mb-6 font-inter">
          Select the company sizes you're interested in
        </p>

        <div className="space-y-3">
          {COMPANY_SIZES.map((size) => (
            <Label
              key={size.value}
              htmlFor={`company-size-${size.value}`}
              className={`flex items-center space-x-3 p-4 rounded-lg cursor-pointer transition-colors ${
                companySize.includes(size.value)
                  ? "bg-green-200 hover:bg-green-300"
                  : "bg-muted/50 hover:bg-muted"
              }`}
            >
              <Checkbox
                id={`company-size-${size.value}`}
                checked={companySize.includes(size.value)}
                onCheckedChange={() => toggleSize(size.value)}
                className={
                  companySize.includes(size.value)
                    ? "border-green-600 data-[state=checked]:bg-green-600"
                    : ""
                }
              />
              <span className="flex-1 font-medium font-inter">
                {size.label}
              </span>
            </Label>
          ))}
        </div>
      </div>

      {/* Followed Companies Info */}
      <div className="border-t pt-6">
        <h2 className="text-2xl font-semibold mb-2 font-sora">
          Followed companies
        </h2>
        <p className="text-muted-foreground mb-4 font-inter">
          You can follow specific companies from the job listings page to get
          priority notifications when they post new positions.
        </p>
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-blue-800 font-inter">
            💡 Tip: Browse job listings and click the "Follow" button on
            companies you're interested in to add them to your followed list.
          </p>
        </div>
      </div>

      {/* Hidden Companies Info */}
      <div className="border-t pt-6">
        <h2 className="text-2xl font-semibold mb-2 font-sora">
          Hidden companies
        </h2>
        <p className="text-muted-foreground mb-4 font-inter">
          Hide companies you don't want to see in your job search results.
        </p>
        <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
          <p className="text-sm text-orange-800 font-inter">
            💡 Tip: You can hide companies from the job listings page by
            clicking the "Hide" button on any company's job posting.
          </p>
        </div>
      </div>

      {/* Completion Message */}
      <div className="border-t pt-6">
        <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
          <h3 className="text-xl font-semibold text-green-800 mb-2 font-sora">
            🎉 Search preferences complete!
          </h3>
          <p className="text-green-700 mb-4 font-inter">
            Your job search preferences have been saved. We'll use these to help
            you find the most relevant opportunities.
          </p>
          <p className="text-sm text-green-600 font-inter">
            You can update these preferences anytime from the sidebar.
          </p>
        </div>
      </div>
    </div>
  );
}
