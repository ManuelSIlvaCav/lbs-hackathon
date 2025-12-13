"use client";

import { Button } from "@/components/ui/button";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { useCandidateContext } from "@/contexts/candidate-context";
import { useEffect, useState } from "react";
import { CompanyStep } from "./_components/company-step";
import { IndustriesStep } from "./_components/industries-step";
import { LocationStep } from "./_components/location-step";
import { RoleStep } from "./_components/role-step";
import { TechnologiesStep } from "./_components/technologies-step";

const STEPS = [
  { id: "location", title: "Location", component: LocationStep },
  { id: "role", title: "Role", component: RoleStep },
  { id: "industries", title: "Industries", component: IndustriesStep },
  { id: "technologies", title: "Technologies", component: TechnologiesStep },
  { id: "company", title: "Company", component: CompanyStep },
];

export default function SearchPreferencesPage() {
  const { candidate, isLoading, updateSearchPreferences, isUpdating } =
    useCandidateContext();
  const [currentStep, setCurrentStep] = useState(0);
  const [formData, setFormData] = useState<any>({});

  // Initialize form data from candidate's existing preferences
  useEffect(() => {
    if (candidate?.search_preferences) {
      console.log(
        "Initializing form data with candidate search preferences:",
        candidate.search_preferences
      );
      setFormData({
        locations: candidate.search_preferences.locations || [],
        visa_sponsorship: candidate.search_preferences.visa_sponsorship || {
          uk: false,
          eu: false,
          us: false,
        },
        languages: candidate.search_preferences.languages || [],
        role_type: candidate.search_preferences.role_type || [],
        role_level: candidate.search_preferences.role_level || [],
        minimum_salary: candidate.search_preferences.minimum_salary || null,
        role_priorities: candidate.search_preferences.role_priorities || [],
        favourite_industries:
          candidate.search_preferences.favourite_industries || [],
        hidden_industries: candidate.search_preferences.hidden_industries || [],
        favourite_technologies:
          candidate.search_preferences.favourite_technologies || [],
        hidden_technologies:
          candidate.search_preferences.hidden_technologies || [],
        company_size: candidate.search_preferences.company_size || [],
        followed_companies:
          candidate.search_preferences.followed_companies || [],
        hidden_companies: candidate.search_preferences.hidden_companies || [],
      });
    }
  }, [candidate]);

  const handleNext = async () => {
    // Save current step data
    await updateSearchPreferences(formData);

    if (currentStep < STEPS.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleStepData = (stepData: any) => {
    setFormData((prev: any) => ({
      ...prev,
      ...stepData,
    }));
  };

  if (isLoading) {
    return (
      <div className="flex h-full w-full items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground font-inter">Loading...</p>
        </div>
      </div>
    );
  }

  const CurrentStepComponent = STEPS[currentStep].component;
  const isLastStep = currentStep === STEPS.length - 1;

  return (
    <div className="flex h-full w-full flex-col">
      {/* Header */}
      <header className="flex items-center justify-between border-b bg-background px-6 py-8">
        <div className="flex items-center gap-4">
          <SidebarTrigger />
          <div>
            <h1 className="text-3xl font-semibold font-sora">
              Search Preferences
            </h1>
            <p className="mt-1 text-sm text-muted-foreground font-inter">
              Customize your job search criteria to find the perfect
              opportunities
            </p>
          </div>
        </div>
      </header>

      {/* Progress indicator - Sticky */}
      <div className="sticky top-0 z-10 border-b bg-background px-6 py-4 shadow-sm">
        <div className="flex items-center justify-between mb-2">
          {STEPS.map((step, index) => (
            <button
              key={step.id}
              onClick={() => setCurrentStep(index)}
              className={`flex-1 text-center transition-all ${
                index < STEPS.length - 1 ? "border-r" : ""
              } hover:bg-accent/50 py-2 rounded-t cursor-pointer font-inter`}
            >
              <div
                className={`text-sm font-medium transition-colors ${
                  index === currentStep
                    ? "text-primary font-semibold"
                    : index < currentStep
                    ? "text-muted-foreground hover:text-foreground"
                    : "text-muted-foreground/50 hover:text-muted-foreground"
                }`}
              >
                {step.title}
              </div>
            </button>
          ))}
        </div>
        <div className="relative h-2 bg-muted rounded-full overflow-hidden">
          <div
            className="absolute top-0 left-0 h-full bg-green-500 transition-all duration-300"
            style={{ width: `${((currentStep + 1) / STEPS.length) * 100}%` }}
          />
        </div>
      </div>

      {Object.keys(formData).length > 0 && (
        <>
          {/* Step content */}
          <div className="flex-1 overflow-auto p-6">
            <div className="max-w-3xl mx-auto">
              <CurrentStepComponent data={formData} onChange={handleStepData} />
            </div>
          </div>

          {/* Navigation */}
          <div className="border-t bg-background px-6 py-4">
            <div className="max-w-3xl mx-auto flex justify-between">
              <Button
                variant="outline"
                onClick={handleBack}
                disabled={currentStep === 0}
              >
                Back
              </Button>
              <Button onClick={handleNext} disabled={isUpdating}>
                {isUpdating ? "Saving..." : isLastStep ? "Finish" : "Next"}
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
