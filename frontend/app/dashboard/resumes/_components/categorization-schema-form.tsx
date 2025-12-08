"use client";

import { Button } from "@/components/ui/button";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { CategorizationSchema } from "@/lib/types/candidate";
import { ChevronDown, Loader2, Plus, Trash2 } from "lucide-react";
import { useEffect } from "react";
import { Controller, useForm } from "react-hook-form";

interface CategorizationSchemaFormProps {
  schema: CategorizationSchema;
  onSave: (data: CategorizationSchema) => Promise<void>;
  isSaving?: boolean;
}

export function CategorizationSchemaForm({
  schema,
  onSave,
  isSaving = false,
}: CategorizationSchemaFormProps) {
  const { control, handleSubmit, watch, setValue, reset } =
    useForm<CategorizationSchema>({
      defaultValues: schema,
    });

  // Reset form when schema prop changes (e.g., after uploading new CV)
  useEffect(() => {
    reset(schema);
  }, [schema, reset]);

  const onSubmit = async (data: CategorizationSchema) => {
    await onSave(data);
  };

  const addEducation = () => {
    const currentEducation = watch("education") || [];
    setValue("education", [
      ...currentEducation,
      {
        degree_type: null,
        degree_name: null,
        institution: null,
        major: null,
        start_date: null,
        end_date: null,
        grades: null,
        description: null,
      },
    ]);
  };

  const removeEducation = (index: number) => {
    const currentEducation = watch("education") || [];
    setValue(
      "education",
      currentEducation.filter((_, i) => i !== index)
    );
  };

  const addExperience = () => {
    const currentExperience = watch("experience") || [];
    setValue("experience", [
      ...currentExperience,
      {
        company_name: null,
        role_title: null,
        location: null,
        start_date: null,
        end_date: null,
        duration_years: null,
        industry_primary: null,
        industries_secondary: [],
        company_type: null,
        role_functions: [],
        is_internship: false,
        hard_skills: [],
        soft_skills: [],
        summary: null,
      },
    ]);
  };

  const removeExperience = (index: number) => {
    const currentExperience = watch("experience") || [];
    setValue(
      "experience",
      currentExperience.filter((_, i) => i !== index)
    );
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
      {/* Contact Info Section */}
      <section className="space-y-4">
        <h3 className="text-lg font-semibold border-b pb-2">
          Contact Information
        </h3>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="full_name">Full Name</Label>
            <Controller
              control={control}
              name="contact_info.full_name"
              render={({ field }) => (
                <Input
                  id="full_name"
                  placeholder="John Doe"
                  value={field.value || ""}
                  onChange={field.onChange}
                  onBlur={field.onBlur}
                />
              )}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Controller
              control={control}
              name="contact_info.email"
              render={({ field }) => (
                <Input
                  id="email"
                  type="email"
                  placeholder="john@example.com"
                  value={field.value || ""}
                  onChange={field.onChange}
                  onBlur={field.onBlur}
                />
              )}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="phone">Phone</Label>
            <Controller
              control={control}
              name="contact_info.phone"
              render={({ field }) => (
                <Input
                  id="phone"
                  placeholder="+1 234 567 8900"
                  value={field.value || ""}
                  onChange={field.onChange}
                  onBlur={field.onBlur}
                />
              )}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="linkedin">LinkedIn</Label>
            <Controller
              control={control}
              name="contact_info.linkedin"
              render={({ field }) => (
                <Input
                  id="linkedin"
                  placeholder="https://linkedin.com/in/..."
                  value={field.value || ""}
                  onChange={field.onChange}
                  onBlur={field.onBlur}
                />
              )}
            />
          </div>
        </div>
      </section>

      {/* Education Section */}
      <section className="space-y-4">
        <div className="flex items-center justify-between border-b pb-2">
          <h3 className="text-lg font-semibold">Education</h3>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={addEducation}
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Education
          </Button>
        </div>

        {watch("education")?.map((edu, index) => {
          const degreeTitle = edu.degree_name || "Untitled Degree";
          const institution = edu.institution || "Institution";
          const dateRange =
            [edu.start_date, edu.end_date].filter(Boolean).join(" - ") ||
            "Dates";

          return (
            <Collapsible key={index} defaultOpen={false}>
              <div className="border rounded-lg">
                <div className="flex items-center justify-between p-4 bg-muted/50">
                  <CollapsibleTrigger className="flex items-center gap-2 flex-1 text-left hover:opacity-70 transition-opacity">
                    <ChevronDown className="h-4 w-4 transition-transform duration-200 data-[state=open]:rotate-180" />
                    <div className="flex-1">
                      <div className="font-medium">{degreeTitle}</div>
                      <div className="text-sm text-muted-foreground">
                        {institution} • {dateRange}
                      </div>
                    </div>
                  </CollapsibleTrigger>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => removeEducation(index)}
                  >
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                </div>

                <CollapsibleContent>
                  <div className="p-4 border-t">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Degree Type</Label>
                        <Controller
                          control={control}
                          name={`education.${index}.degree_type`}
                          render={({ field }) => (
                            <Select
                              value={field.value || ""}
                              onValueChange={field.onChange}
                            >
                              <SelectTrigger className="w-full">
                                <SelectValue placeholder="Select type" />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="Bachelor">
                                  Bachelor
                                </SelectItem>
                                <SelectItem value="Master">Master</SelectItem>
                                <SelectItem value="PhD">PhD</SelectItem>
                                <SelectItem value="Associate">
                                  Associate
                                </SelectItem>
                                <SelectItem value="Diploma">Diploma</SelectItem>
                                <SelectItem value="Certificate">
                                  Certificate
                                </SelectItem>
                              </SelectContent>
                            </Select>
                          )}
                        />
                      </div>

                      <div className="space-y-2">
                        <Label>Degree Name</Label>
                        <Controller
                          control={control}
                          name={`education.${index}.degree_name`}
                          render={({ field }) => (
                            <Input
                              placeholder="Computer Science"
                              value={field.value || ""}
                              onChange={field.onChange}
                            />
                          )}
                        />
                      </div>

                      <div className="space-y-2">
                        <Label>Institution</Label>
                        <Controller
                          control={control}
                          name={`education.${index}.institution`}
                          render={({ field }) => (
                            <Input
                              placeholder="University Name"
                              value={field.value || ""}
                              onChange={field.onChange}
                            />
                          )}
                        />
                      </div>

                      <div className="space-y-2">
                        <Label>Major</Label>
                        <Controller
                          control={control}
                          name={`education.${index}.major`}
                          render={({ field }) => (
                            <Input
                              placeholder="Software Engineering"
                              value={field.value || ""}
                              onChange={field.onChange}
                            />
                          )}
                        />
                      </div>

                      <div className="space-y-2">
                        <Label>Start Date</Label>
                        <Controller
                          control={control}
                          name={`education.${index}.start_date`}
                          render={({ field }) => (
                            <Input
                              placeholder="2018"
                              value={field.value || ""}
                              onChange={field.onChange}
                            />
                          )}
                        />
                      </div>

                      <div className="space-y-2">
                        <Label>End Date</Label>
                        <Controller
                          control={control}
                          name={`education.${index}.end_date`}
                          render={({ field }) => (
                            <Input
                              placeholder="2022"
                              value={field.value || ""}
                              onChange={field.onChange}
                            />
                          )}
                        />
                      </div>

                      <div className="space-y-2">
                        <Label>Grades</Label>
                        <Controller
                          control={control}
                          name={`education.${index}.grades`}
                          render={({ field }) => (
                            <Input
                              placeholder="3.8 GPA"
                              value={field.value || ""}
                              onChange={field.onChange}
                            />
                          )}
                        />
                      </div>

                      <div className="space-y-2 col-span-2">
                        <Label>Description</Label>
                        <Controller
                          control={control}
                          name={`education.${index}.description`}
                          render={({ field }) => (
                            <Textarea
                              placeholder="Additional details..."
                              value={field.value || ""}
                              onChange={field.onChange}
                            />
                          )}
                        />
                      </div>
                    </div>
                  </div>
                </CollapsibleContent>
              </div>
            </Collapsible>
          );
        })}
      </section>

      {/* Experience Section */}
      <section className="space-y-4">
        <div className="flex items-center justify-between border-b pb-2">
          <h3 className="text-lg font-semibold">Experience</h3>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={addExperience}
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Experience
          </Button>
        </div>

        {watch("experience")?.map((exp, index) => {
          const roleTitle = exp.role_title || "Untitled Role";
          const company = exp.company_name || "Company";
          const dateRange =
            [exp.start_date, exp.end_date].filter(Boolean).join(" - ") ||
            "Dates";

          return (
            <Collapsible key={index} defaultOpen={false}>
              <div className="border rounded-lg">
                <div className="flex items-center justify-between p-4 bg-muted/50">
                  <CollapsibleTrigger className="flex items-center gap-2 flex-1 text-left hover:opacity-70 transition-opacity">
                    <ChevronDown className="h-4 w-4 transition-transform duration-200 data-[state=open]:rotate-180" />
                    <div className="flex-1">
                      <div className="font-medium">{roleTitle}</div>
                      <div className="text-sm text-muted-foreground">
                        {company} • {dateRange}
                      </div>
                    </div>
                  </CollapsibleTrigger>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => removeExperience(index)}
                  >
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                </div>

                <CollapsibleContent>
                  <div className="p-4 border-t">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Company Name</Label>
                        <Controller
                          control={control}
                          name={`experience.${index}.company_name`}
                          render={({ field }) => (
                            <Input
                              placeholder="Company Inc."
                              value={field.value || ""}
                              onChange={field.onChange}
                            />
                          )}
                        />
                      </div>

                      <div className="space-y-2">
                        <Label>Role Title</Label>
                        <Controller
                          control={control}
                          name={`experience.${index}.role_title`}
                          render={({ field }) => (
                            <Input
                              placeholder="Software Engineer"
                              value={field.value || ""}
                              onChange={field.onChange}
                            />
                          )}
                        />
                      </div>

                      <div className="space-y-2">
                        <Label>Location</Label>
                        <Controller
                          control={control}
                          name={`experience.${index}.location`}
                          render={({ field }) => (
                            <Input
                              placeholder="San Francisco, CA"
                              value={field.value || ""}
                              onChange={field.onChange}
                            />
                          )}
                        />
                      </div>

                      <div className="space-y-2">
                        <Label>Duration (years)</Label>
                        <Controller
                          control={control}
                          name={`experience.${index}.duration_years`}
                          render={({ field }) => (
                            <Input
                              type="number"
                              step="0.1"
                              placeholder="2.5"
                              value={field.value || 0}
                              onChange={(e) =>
                                field.onChange(parseFloat(e.target.value) || 0)
                              }
                            />
                          )}
                        />
                      </div>

                      <div className="space-y-2">
                        <Label>Start Date</Label>
                        <Controller
                          control={control}
                          name={`experience.${index}.start_date`}
                          render={({ field }) => (
                            <Input
                              placeholder="Jan 2020"
                              value={field.value || ""}
                              onChange={field.onChange}
                            />
                          )}
                        />
                      </div>

                      <div className="space-y-2">
                        <Label>End Date</Label>
                        <Controller
                          control={control}
                          name={`experience.${index}.end_date`}
                          render={({ field }) => (
                            <Input
                              placeholder="Dec 2022 or Present"
                              value={field.value || ""}
                              onChange={field.onChange}
                            />
                          )}
                        />
                      </div>

                      <div className="space-y-2">
                        <Label>Primary Industry</Label>
                        <Controller
                          control={control}
                          name={`experience.${index}.industry_primary`}
                          render={({ field }) => (
                            <Input
                              placeholder="Technology"
                              value={field.value || ""}
                              onChange={field.onChange}
                            />
                          )}
                        />
                      </div>

                      <div className="space-y-2">
                        <Label>Company Type</Label>
                        <Controller
                          control={control}
                          name={`experience.${index}.company_type`}
                          render={({ field }) => (
                            <Select
                              value={field.value || ""}
                              onValueChange={field.onChange}
                            >
                              <SelectTrigger className="w-full">
                                <SelectValue placeholder="Select type" />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="Startup">Startup</SelectItem>
                                <SelectItem value="Small Business">
                                  Small Business
                                </SelectItem>
                                <SelectItem value="Mid-size">
                                  Mid-size
                                </SelectItem>
                                <SelectItem value="Enterprise">
                                  Enterprise
                                </SelectItem>
                                <SelectItem value="Public">Public</SelectItem>
                                <SelectItem value="Non-profit">
                                  Non-profit
                                </SelectItem>
                              </SelectContent>
                            </Select>
                          )}
                        />
                      </div>

                      <div className="space-y-2 col-span-2">
                        <Label>Role Functions (comma-separated)</Label>
                        <Controller
                          control={control}
                          name={`experience.${index}.role_functions`}
                          render={({ field }) => (
                            <Input
                              placeholder="Strategy, Operations, Product Management"
                              value={field.value?.join(", ") || ""}
                              onChange={(e) =>
                                field.onChange(
                                  e.target.value
                                    .split(",")
                                    .map((s) => s.trim())
                                    .filter(Boolean)
                                )
                              }
                            />
                          )}
                        />
                      </div>

                      <div className="space-y-2 col-span-2">
                        <Label>Hard Skills (comma-separated)</Label>
                        <Controller
                          control={control}
                          name={`experience.${index}.hard_skills`}
                          render={({ field }) => (
                            <Input
                              placeholder="Python, React, AWS"
                              value={field.value?.join(", ") || ""}
                              onChange={(e) =>
                                field.onChange(
                                  e.target.value
                                    .split(",")
                                    .map((s) => s.trim())
                                    .filter(Boolean)
                                )
                              }
                            />
                          )}
                        />
                      </div>

                      <div className="space-y-2 col-span-2">
                        <Label>Soft Skills (comma-separated)</Label>
                        <Controller
                          control={control}
                          name={`experience.${index}.soft_skills`}
                          render={({ field }) => (
                            <Input
                              placeholder="Leadership, Communication"
                              value={field.value?.join(", ") || ""}
                              onChange={(e) =>
                                field.onChange(
                                  e.target.value
                                    .split(",")
                                    .map((s) => s.trim())
                                    .filter(Boolean)
                                )
                              }
                            />
                          )}
                        />
                      </div>

                      <div className="space-y-2 col-span-2">
                        <Label>Summary</Label>
                        <Controller
                          control={control}
                          name={`experience.${index}.summary`}
                          render={({ field }) => (
                            <Textarea
                              placeholder="Describe your role and achievements..."
                              value={field.value || ""}
                              onChange={field.onChange}
                            />
                          )}
                        />
                      </div>
                    </div>
                  </div>
                </CollapsibleContent>
              </div>
            </Collapsible>
          );
        })}
      </section>

      {/* Skills Summary Section */}
      <section className="space-y-4">
        <h3 className="text-lg font-semibold border-b pb-2">Skills Summary</h3>
        <div className="grid grid-cols-1 gap-4">
          <div className="space-y-2">
            <Label>Hard Skills (comma-separated)</Label>
            <Controller
              control={control}
              name="skills_summary.hard_skills_overall"
              render={({ field }) => (
                <Input
                  placeholder="Python, JavaScript, AWS, Docker"
                  value={field.value?.join(", ") || ""}
                  onChange={(e) =>
                    field.onChange(
                      e.target.value
                        .split(",")
                        .map((s) => s.trim())
                        .filter(Boolean)
                    )
                  }
                />
              )}
            />
          </div>

          <div className="space-y-2">
            <Label>Soft Skills (comma-separated)</Label>
            <Controller
              control={control}
              name="skills_summary.soft_skills_overall"
              render={({ field }) => (
                <Input
                  placeholder="Leadership, Communication, Problem Solving"
                  value={field.value?.join(", ") || ""}
                  onChange={(e) =>
                    field.onChange(
                      e.target.value
                        .split(",")
                        .map((s) => s.trim())
                        .filter(Boolean)
                    )
                  }
                />
              )}
            />
          </div>

          <div className="space-y-2">
            <Label>Software Knowledge (comma-separated)</Label>
            <Controller
              control={control}
              name="skills_summary.software_knowledge"
              render={({ field }) => (
                <Input
                  placeholder="VS Code, Git, Jira"
                  value={field.value?.join(", ") || ""}
                  onChange={(e) =>
                    field.onChange(
                      e.target.value
                        .split(",")
                        .map((s) => s.trim())
                        .filter(Boolean)
                    )
                  }
                />
              )}
            />
          </div>

          <div className="space-y-2">
            <Label>Languages (comma-separated)</Label>
            <Controller
              control={control}
              name="skills_summary.languages"
              render={({ field }) => (
                <Input
                  placeholder="English (Native), Spanish (Fluent)"
                  value={field.value?.join(", ") || ""}
                  onChange={(e) =>
                    field.onChange(
                      e.target.value
                        .split(",")
                        .map((s) => s.trim())
                        .filter(Boolean)
                    )
                  }
                />
              )}
            />
          </div>

          <div className="space-y-2">
            <Label>Interests (comma-separated)</Label>
            <Controller
              control={control}
              name="skills_summary.interests"
              render={({ field }) => (
                <Input
                  placeholder="Open Source, AI/ML, Startups"
                  value={field.value?.join(", ") || ""}
                  onChange={(e) =>
                    field.onChange(
                      e.target.value
                        .split(",")
                        .map((s) => s.trim())
                        .filter(Boolean)
                    )
                  }
                />
              )}
            />
          </div>
        </div>
      </section>

      {/* Form Actions */}
      <div className="flex items-center gap-4 pt-4 border-t sticky bottom-0 bg-background py-4">
        <Button type="submit" disabled={isSaving}>
          {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          Save Changes
        </Button>
        <Button
          type="button"
          variant="outline"
          onClick={() => reset()}
          disabled={isSaving}
        >
          Reset
        </Button>
      </div>
    </form>
  );
}
