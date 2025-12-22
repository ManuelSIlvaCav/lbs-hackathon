"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useCVBuilder } from "@/contexts/cv-builder-context";
import { CVSkillsSummary } from "@/lib/types/cv-builder";
import { Plus, X } from "lucide-react";
import { KeyboardEvent, useEffect, useState } from "react";

export function SkillsSection() {
  const { currentCV, updateCV } = useCVBuilder();
  const [skills, setSkills] = useState<CVSkillsSummary>({
    technical_skills: [],
    soft_skills: [],
    tools: [],
    languages: [],
    certifications: [],
  });
  const [isDirty, setIsDirty] = useState(false);
  const [inputValues, setInputValues] = useState({
    technical_skills: "",
    soft_skills: "",
    tools: "",
    languages: "",
    certifications: "",
  });

  useEffect(() => {
    if (currentCV?.skills) {
      setSkills(currentCV.skills);
      setIsDirty(false);
    }
  }, [currentCV]);

  const handleSave = async () => {
    await updateCV({ skills });
    setIsDirty(false);
  };

  const addSkill = (category: keyof CVSkillsSummary) => {
    const value = inputValues[category].trim();
    if (value && !skills[category].includes(value)) {
      setSkills((prev) => ({
        ...prev,
        [category]: [...prev[category], value],
      }));
      setInputValues((prev) => ({ ...prev, [category]: "" }));
      setIsDirty(true);
    }
  };

  const removeSkill = (category: keyof CVSkillsSummary, skill: string) => {
    setSkills((prev) => ({
      ...prev,
      [category]: prev[category].filter((s) => s !== skill),
    }));
    setIsDirty(true);
  };

  const handleKeyPress = (
    e: KeyboardEvent<HTMLInputElement>,
    category: keyof CVSkillsSummary
  ) => {
    if (e.key === "Enter") {
      e.preventDefault();
      addSkill(category);
    }
  };

  if (!currentCV) {
    return <p className="text-muted-foreground">No CV selected</p>;
  }

  const skillCategories: {
    key: keyof CVSkillsSummary;
    label: string;
    placeholder: string;
    description: string;
  }[] = [
    {
      key: "technical_skills",
      label: "Technical Skills",
      placeholder: "e.g., Python, SQL, Machine Learning",
      description: "Hard skills and technical competencies",
    },
    {
      key: "tools",
      label: "Tools & Software",
      placeholder: "e.g., Excel, Tableau, Figma, JIRA",
      description: "Software and tools you're proficient with",
    },
    {
      key: "soft_skills",
      label: "Soft Skills",
      placeholder: "e.g., Leadership, Communication, Problem Solving",
      description: "Interpersonal and behavioral skills",
    },
    {
      key: "languages",
      label: "Languages",
      placeholder: "e.g., English (Native), Spanish (Fluent)",
      description: "Languages with proficiency levels",
    },
    {
      key: "certifications",
      label: "Certifications",
      placeholder: "e.g., AWS Certified, PMP, CFA",
      description: "Professional certifications",
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Skills</h2>
          <p className="text-sm text-muted-foreground">
            Add your technical and soft skills
          </p>
        </div>
        <Button onClick={handleSave} disabled={!isDirty}>
          Save Changes
        </Button>
      </div>

      <div className="space-y-6">
        {skillCategories.map(({ key, label, placeholder, description }) => (
          <div key={key} className="space-y-2">
            <div>
              <Label>{label}</Label>
              <p className="text-xs text-muted-foreground">{description}</p>
            </div>

            {/* Skills display */}
            <div className="flex flex-wrap gap-2">
              {skills[key].map((skill) => (
                <Badge key={skill} variant="secondary" className="gap-1 pr-1">
                  {skill}
                  <button
                    onClick={() => removeSkill(key, skill)}
                    className="ml-1 rounded-full hover:bg-muted-foreground/20"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              ))}
            </div>

            {/* Add skill input */}
            <div className="flex gap-2">
              <Input
                value={inputValues[key]}
                onChange={(e) =>
                  setInputValues((prev) => ({ ...prev, [key]: e.target.value }))
                }
                onKeyPress={(e) => handleKeyPress(e, key)}
                placeholder={placeholder}
                className="flex-1"
              />
              <Button
                variant="outline"
                size="icon"
                onClick={() => addSkill(key)}
                disabled={!inputValues[key].trim()}
              >
                <Plus className="h-4 w-4" />
              </Button>
            </div>
          </div>
        ))}
      </div>

      {/* Tips */}
      <div className="rounded-lg bg-muted/50 p-4">
        <h4 className="mb-2 text-sm font-medium">ATS Tips for Skills</h4>
        <ul className="space-y-1 text-xs text-muted-foreground">
          <li>
            • Use standard industry terminology (ATS looks for exact matches)
          </li>
          <li>
            • Include both acronyms and full names if common (SQL, Python)
          </li>
          <li>• Mirror keywords from job descriptions you're targeting</li>
          <li>• List 8-15 technical skills for optimal ATS scanning</li>
        </ul>
      </div>
    </div>
  );
}
