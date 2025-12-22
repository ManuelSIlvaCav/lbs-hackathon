"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useCVBuilder } from "@/contexts/cv-builder-context";
import { CVEducationItem } from "@/lib/types/cv-builder";
import { ChevronDown, GripVertical, Plus, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";

export function EducationSection() {
  const { currentCV, updateCV } = useCVBuilder();
  const [education, setEducation] = useState<CVEducationItem[]>([]);
  const [isDirty, setIsDirty] = useState(false);
  const [openItems, setOpenItems] = useState<string[]>([]);

  useEffect(() => {
    if (currentCV?.education) {
      setEducation(currentCV.education);
      if (currentCV.education.length > 0 && openItems.length === 0) {
        setOpenItems([currentCV.education[0].id]);
      }
      setIsDirty(false);
    }
  }, [currentCV]);

  const handleSave = async () => {
    await updateCV({ education });
    setIsDirty(false);
  };

  const addEducation = () => {
    const newEdu: CVEducationItem = {
      id: `edu-${Date.now()}`,
      institution: "",
      degree_type: null,
      degree_name: null,
      major: null,
      start_date: null,
      end_date: null,
      grades: null,
      description: null,
      bullets: [],
    };
    setEducation([newEdu, ...education]);
    setOpenItems([newEdu.id, ...openItems]);
    setIsDirty(true);
  };

  const removeEducation = (id: string) => {
    setEducation(education.filter((edu) => edu.id !== id));
    setOpenItems(openItems.filter((item) => item !== id));
    setIsDirty(true);
  };

  const updateEducationItem = (
    id: string,
    field: keyof CVEducationItem,
    value: any
  ) => {
    setEducation(
      education.map((edu) => (edu.id === id ? { ...edu, [field]: value } : edu))
    );
    setIsDirty(true);
  };

  const addBullet = (eduId: string) => {
    setEducation(
      education.map((edu) =>
        edu.id === eduId ? { ...edu, bullets: [...edu.bullets, ""] } : edu
      )
    );
    setIsDirty(true);
  };

  const updateBullet = (eduId: string, bulletIndex: number, value: string) => {
    setEducation(
      education.map((edu) =>
        edu.id === eduId
          ? {
              ...edu,
              bullets: edu.bullets.map((b, i) =>
                i === bulletIndex ? value : b
              ),
            }
          : edu
      )
    );
    setIsDirty(true);
  };

  const removeBullet = (eduId: string, bulletIndex: number) => {
    setEducation(
      education.map((edu) =>
        edu.id === eduId
          ? { ...edu, bullets: edu.bullets.filter((_, i) => i !== bulletIndex) }
          : edu
      )
    );
    setIsDirty(true);
  };

  const toggleItem = (id: string) => {
    setOpenItems((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  if (!currentCV) {
    return <p className="text-muted-foreground">No CV selected</p>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Education</h2>
          <p className="text-sm text-muted-foreground">
            Add your educational background
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={addEducation} className="gap-2">
            <Plus className="h-4 w-4" />
            Add Education
          </Button>
          <Button onClick={handleSave} disabled={!isDirty}>
            Save Changes
          </Button>
        </div>
      </div>

      <div className="space-y-4">
        {education.length === 0 ? (
          <Card className="border-dashed">
            <CardContent className="flex flex-col items-center justify-center py-8">
              <p className="mb-4 text-sm text-muted-foreground">
                No education added yet
              </p>
              <Button
                variant="outline"
                onClick={addEducation}
                className="gap-2"
              >
                <Plus className="h-4 w-4" />
                Add Your Education
              </Button>
            </CardContent>
          </Card>
        ) : (
          education.map((edu) => (
            <Collapsible
              key={edu.id}
              open={openItems.includes(edu.id)}
              onOpenChange={() => toggleItem(edu.id)}
            >
              <Card>
                <CollapsibleTrigger asChild>
                  <CardHeader className="cursor-pointer hover:bg-muted/50">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <GripVertical className="h-4 w-4 text-muted-foreground" />
                        <div>
                          <CardTitle className="text-base">
                            {edu.degree_type || edu.degree_name
                              ? `${edu.degree_type || ""} ${
                                  edu.degree_name || ""
                                }`.trim()
                              : "New Degree"}
                          </CardTitle>
                          <p className="text-sm text-muted-foreground">
                            {edu.institution || "Institution"} •{" "}
                            {edu.end_date || "Year"}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={(e) => {
                            e.stopPropagation();
                            removeEducation(edu.id);
                          }}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                        <ChevronDown
                          className={`h-4 w-4 transition-transform ${
                            openItems.includes(edu.id) ? "rotate-180" : ""
                          }`}
                        />
                      </div>
                    </div>
                  </CardHeader>
                </CollapsibleTrigger>

                <CollapsibleContent>
                  <CardContent className="space-y-4 pt-0">
                    <div className="grid gap-4 sm:grid-cols-2">
                      <div className="space-y-2">
                        <Label>Institution *</Label>
                        <Input
                          value={edu.institution}
                          onChange={(e) =>
                            updateEducationItem(
                              edu.id,
                              "institution",
                              e.target.value
                            )
                          }
                          placeholder="Stanford University"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Degree Type</Label>
                        <Input
                          value={edu.degree_type || ""}
                          onChange={(e) =>
                            updateEducationItem(
                              edu.id,
                              "degree_type",
                              e.target.value
                            )
                          }
                          placeholder="Bachelor's, Master's, MBA..."
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Degree Name</Label>
                        <Input
                          value={edu.degree_name || ""}
                          onChange={(e) =>
                            updateEducationItem(
                              edu.id,
                              "degree_name",
                              e.target.value
                            )
                          }
                          placeholder="Computer Science"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Major / Specialization</Label>
                        <Input
                          value={edu.major || ""}
                          onChange={(e) =>
                            updateEducationItem(edu.id, "major", e.target.value)
                          }
                          placeholder="Machine Learning"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Start Date</Label>
                        <Input
                          value={edu.start_date || ""}
                          onChange={(e) =>
                            updateEducationItem(
                              edu.id,
                              "start_date",
                              e.target.value
                            )
                          }
                          placeholder="Sep 2018"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>End Date</Label>
                        <Input
                          value={edu.end_date || ""}
                          onChange={(e) =>
                            updateEducationItem(
                              edu.id,
                              "end_date",
                              e.target.value
                            )
                          }
                          placeholder="May 2022"
                        />
                      </div>
                      <div className="space-y-2 sm:col-span-2">
                        <Label>GPA / Grades / Honors</Label>
                        <Input
                          value={edu.grades || ""}
                          onChange={(e) =>
                            updateEducationItem(
                              edu.id,
                              "grades",
                              e.target.value
                            )
                          }
                          placeholder="3.9/4.0, First Class Honours, Summa Cum Laude"
                        />
                      </div>
                    </div>

                    {/* Additional Details / Bullets */}
                    <div className="space-y-2">
                      <Label>Notable Achievements (optional)</Label>
                      {edu.bullets.map((bullet, bulletIndex) => (
                        <div key={bulletIndex} className="flex gap-2">
                          <Input
                            value={bullet}
                            onChange={(e) =>
                              updateBullet(edu.id, bulletIndex, e.target.value)
                            }
                            placeholder="Dean's List, Thesis on..."
                            className="flex-1"
                          />
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => removeBullet(edu.id, bulletIndex)}
                          >
                            <Trash2 className="h-4 w-4 text-muted-foreground" />
                          </Button>
                        </div>
                      ))}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => addBullet(edu.id)}
                        className="gap-1"
                      >
                        <Plus className="h-3 w-3" />
                        Add Achievement
                      </Button>
                    </div>
                  </CardContent>
                </CollapsibleContent>
              </Card>
            </Collapsible>
          ))
        )}
      </div>
    </div>
  );
}
