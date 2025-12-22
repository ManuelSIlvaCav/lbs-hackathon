"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useCVBuilder } from "@/contexts/cv-builder-context";
import { BulletEnhancement, CVExperienceItem } from "@/lib/types/cv-builder";
import {
  Check,
  ChevronDown,
  GripVertical,
  Loader2,
  Plus,
  Sparkles,
  Trash2,
  X,
} from "lucide-react";
import { useEffect, useState } from "react";

export function ExperienceSection() {
  const { currentCV, updateCV, enhanceBullets, isEnhancing } = useCVBuilder();
  const [experiences, setExperiences] = useState<CVExperienceItem[]>([]);
  const [isDirty, setIsDirty] = useState(false);
  const [openItems, setOpenItems] = useState<string[]>([]);
  const [enhancingId, setEnhancingId] = useState<string | null>(null);
  const [enhancements, setEnhancements] = useState<
    Record<string, BulletEnhancement[]>
  >({});

  useEffect(() => {
    if (currentCV?.experience) {
      setExperiences(currentCV.experience);
      // Open the first item by default
      if (currentCV.experience.length > 0 && openItems.length === 0) {
        setOpenItems([currentCV.experience[0].id]);
      }
      setIsDirty(false);
    }
  }, [currentCV]);

  const handleSave = async () => {
    await updateCV({ experience: experiences });
    setIsDirty(false);
  };

  const addExperience = () => {
    const newExp: CVExperienceItem = {
      id: `exp-${Date.now()}`,
      company_name: "",
      role_title: "",
      location: null,
      start_date: null,
      end_date: null,
      is_current: false,
      description: null,
      bullets: [],
    };
    setExperiences([newExp, ...experiences]);
    setOpenItems([newExp.id, ...openItems]);
    setIsDirty(true);
  };

  const removeExperience = (id: string) => {
    setExperiences(experiences.filter((exp) => exp.id !== id));
    setOpenItems(openItems.filter((item) => item !== id));
    setIsDirty(true);
  };

  const updateExperience = (
    id: string,
    field: keyof CVExperienceItem,
    value: any
  ) => {
    setExperiences(
      experiences.map((exp) =>
        exp.id === id ? { ...exp, [field]: value } : exp
      )
    );
    setIsDirty(true);
  };

  const addBullet = (expId: string) => {
    setExperiences(
      experiences.map((exp) =>
        exp.id === expId ? { ...exp, bullets: [...exp.bullets, ""] } : exp
      )
    );
    setIsDirty(true);
  };

  const updateBullet = (expId: string, bulletIndex: number, value: string) => {
    setExperiences(
      experiences.map((exp) =>
        exp.id === expId
          ? {
              ...exp,
              bullets: exp.bullets.map((b, i) =>
                i === bulletIndex ? value : b
              ),
            }
          : exp
      )
    );
    setIsDirty(true);
  };

  const removeBullet = (expId: string, bulletIndex: number) => {
    setExperiences(
      experiences.map((exp) =>
        exp.id === expId
          ? { ...exp, bullets: exp.bullets.filter((_, i) => i !== bulletIndex) }
          : exp
      )
    );
    setIsDirty(true);
  };

  const handleEnhanceBullets = async (exp: CVExperienceItem) => {
    if (exp.bullets.length === 0) return;

    setEnhancingId(exp.id);
    try {
      const result = await enhanceBullets({
        section_type: "experience",
        section_id: exp.id,
        bullets: exp.bullets.filter((b) => b.trim()),
        context: `${exp.role_title} at ${exp.company_name}`,
      });
      setEnhancements((prev) => ({
        ...prev,
        [exp.id]: result.bullet_enhancements,
      }));
    } catch (error) {
      console.error("Enhancement failed:", error);
    } finally {
      setEnhancingId(null);
    }
  };

  const acceptEnhancement = (
    expId: string,
    originalText: string,
    enhancedText: string
  ) => {
    setExperiences(
      experiences.map((exp) =>
        exp.id === expId
          ? {
              ...exp,
              bullets: exp.bullets.map((b) =>
                b === originalText ? enhancedText : b
              ),
            }
          : exp
      )
    );
    setEnhancements((prev) => ({
      ...prev,
      [expId]: prev[expId]?.filter((e) => e.original !== originalText) || [],
    }));
    setIsDirty(true);
  };

  const rejectEnhancement = (expId: string, originalText: string) => {
    setEnhancements((prev) => ({
      ...prev,
      [expId]: prev[expId]?.filter((e) => e.original !== originalText) || [],
    }));
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
          <h2 className="text-lg font-semibold">Work Experience</h2>
          <p className="text-sm text-muted-foreground">
            Add your relevant work history with achievements
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={addExperience} className="gap-2">
            <Plus className="h-4 w-4" />
            Add Experience
          </Button>
          <Button onClick={handleSave} disabled={!isDirty}>
            Save Changes
          </Button>
        </div>
      </div>

      <div className="space-y-4">
        {experiences.length === 0 ? (
          <Card className="border-dashed">
            <CardContent className="flex flex-col items-center justify-center py-8">
              <p className="mb-4 text-sm text-muted-foreground">
                No work experience added yet
              </p>
              <Button
                variant="outline"
                onClick={addExperience}
                className="gap-2"
              >
                <Plus className="h-4 w-4" />
                Add Your First Experience
              </Button>
            </CardContent>
          </Card>
        ) : (
          experiences.map((exp, index) => (
            <Collapsible
              key={exp.id}
              open={openItems.includes(exp.id)}
              onOpenChange={() => toggleItem(exp.id)}
            >
              <Card>
                <CollapsibleTrigger asChild>
                  <CardHeader className="cursor-pointer hover:bg-muted/50">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <GripVertical className="h-4 w-4 text-muted-foreground" />
                        <div>
                          <CardTitle className="text-base">
                            {exp.role_title || "New Position"}
                          </CardTitle>
                          <p className="text-sm text-muted-foreground">
                            {exp.company_name || "Company"} •{" "}
                            {exp.start_date || "Start"} -{" "}
                            {exp.is_current ? "Present" : exp.end_date || "End"}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={(e) => {
                            e.stopPropagation();
                            removeExperience(exp.id);
                          }}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                        <ChevronDown
                          className={`h-4 w-4 transition-transform ${
                            openItems.includes(exp.id) ? "rotate-180" : ""
                          }`}
                        />
                      </div>
                    </div>
                  </CardHeader>
                </CollapsibleTrigger>

                <CollapsibleContent>
                  <CardContent className="space-y-4 pt-0">
                    {/* Basic Info */}
                    <div className="grid gap-4 sm:grid-cols-2">
                      <div className="space-y-2">
                        <Label>Job Title *</Label>
                        <Input
                          value={exp.role_title}
                          onChange={(e) =>
                            updateExperience(
                              exp.id,
                              "role_title",
                              e.target.value
                            )
                          }
                          placeholder="Senior Product Manager"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Company *</Label>
                        <Input
                          value={exp.company_name}
                          onChange={(e) =>
                            updateExperience(
                              exp.id,
                              "company_name",
                              e.target.value
                            )
                          }
                          placeholder="Google"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Location</Label>
                        <Input
                          value={exp.location || ""}
                          onChange={(e) =>
                            updateExperience(exp.id, "location", e.target.value)
                          }
                          placeholder="San Francisco, CA"
                        />
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="flex-1 space-y-2">
                          <Label>Start Date</Label>
                          <Input
                            value={exp.start_date || ""}
                            onChange={(e) =>
                              updateExperience(
                                exp.id,
                                "start_date",
                                e.target.value
                              )
                            }
                            placeholder="Jan 2020"
                          />
                        </div>
                        <div className="flex-1 space-y-2">
                          <Label>End Date</Label>
                          <Input
                            value={exp.end_date || ""}
                            onChange={(e) =>
                              updateExperience(
                                exp.id,
                                "end_date",
                                e.target.value
                              )
                            }
                            placeholder="Present"
                            disabled={exp.is_current}
                          />
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id={`current-${exp.id}`}
                        checked={exp.is_current}
                        onCheckedChange={(checked) =>
                          updateExperience(exp.id, "is_current", checked)
                        }
                      />
                      <Label htmlFor={`current-${exp.id}`} className="text-sm">
                        I currently work here
                      </Label>
                    </div>

                    {/* Bullets */}
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label>Achievements & Responsibilities</Label>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleEnhanceBullets(exp)}
                          disabled={
                            isEnhancing ||
                            exp.bullets.filter((b) => b.trim()).length === 0
                          }
                          className="gap-1"
                        >
                          {enhancingId === exp.id ? (
                            <Loader2 className="h-3 w-3 animate-spin" />
                          ) : (
                            <Sparkles className="h-3 w-3" />
                          )}
                          {enhancingId === exp.id
                            ? "Enhancing..."
                            : "AI Enhance All"}
                        </Button>
                      </div>

                      {exp.bullets.map((bullet, bulletIndex) => (
                        <div key={bulletIndex} className="space-y-2">
                          <div className="flex gap-2">
                            <Textarea
                              value={bullet}
                              onChange={(e) =>
                                updateBullet(
                                  exp.id,
                                  bulletIndex,
                                  e.target.value
                                )
                              }
                              placeholder="Led cross-functional team of 5 to deliver..."
                              rows={2}
                              className="flex-1 resize-none"
                            />
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => removeBullet(exp.id, bulletIndex)}
                            >
                              <Trash2 className="h-4 w-4 text-muted-foreground" />
                            </Button>
                          </div>

                          {/* Enhancement for this bullet */}
                          {enhancements[exp.id]?.find(
                            (e) => e.original === bullet
                          ) && (
                            <Card className="border-primary/50 bg-primary/5">
                              <CardContent className="py-3">
                                <div className="mb-2 flex items-center justify-between">
                                  <span className="text-xs font-medium text-primary">
                                    AI Suggestion
                                  </span>
                                  <div className="flex gap-1">
                                    <Button
                                      size="sm"
                                      variant="ghost"
                                      onClick={() =>
                                        acceptEnhancement(
                                          exp.id,
                                          bullet,
                                          enhancements[exp.id].find(
                                            (e) => e.original === bullet
                                          )!.enhanced
                                        )
                                      }
                                      className="h-6 gap-1 text-xs text-green-600"
                                    >
                                      <Check className="h-3 w-3" />
                                      Accept
                                    </Button>
                                    <Button
                                      size="sm"
                                      variant="ghost"
                                      onClick={() =>
                                        rejectEnhancement(exp.id, bullet)
                                      }
                                      className="h-6 gap-1 text-xs text-red-600"
                                    >
                                      <X className="h-3 w-3" />
                                      Reject
                                    </Button>
                                  </div>
                                </div>
                                <p className="text-sm">
                                  {
                                    enhancements[exp.id].find(
                                      (e) => e.original === bullet
                                    )?.enhanced
                                  }
                                </p>
                                <p className="mt-1 text-xs text-muted-foreground">
                                  {
                                    enhancements[exp.id].find(
                                      (e) => e.original === bullet
                                    )?.explanation
                                  }
                                </p>
                              </CardContent>
                            </Card>
                          )}
                        </div>
                      ))}

                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => addBullet(exp.id)}
                        className="gap-1"
                      >
                        <Plus className="h-3 w-3" />
                        Add Bullet
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
