"use client";

import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useEffect, useRef, useState } from "react";

interface RoleStepProps {
  data: any;
  onChange: (data: any) => void;
}

const ROLE_TYPES = [
  "Full-time",
  "Part-time",
  "Contract",
  "Internship",
  "Freelance",
];

const ROLE_LEVELS = [
  { value: "Internships", label: "Internships", years: "" },
  { value: "Entry-level/graduate", label: "Entry-level/graduate", years: "" },
  { value: "Junior", label: "Junior (1-2 years)", years: "1-2 years" },
  { value: "Mid-level", label: "Mid-level (3-4 years)", years: "3-4 years" },
  { value: "Senior", label: "Senior (5-8 years)", years: "5-8 years" },
  {
    value: "Expert & Leadership",
    label: "Expert & Leadership (9+ years)",
    years: "9+ years",
  },
];

const ROLE_PRIORITIES = [
  "Work-life balance",
  "Learning & Development",
  "Impact & Ownership",
  "Compensation",
  "Company Culture",
  "Career Growth",
  "Remote Work",
  "Mission & Values",
];

export function RoleStep({ data, onChange }: RoleStepProps) {
  const onChangeRef = useRef(onChange);
  onChangeRef.current = onChange;

  const [roleType, setRoleType] = useState<string[]>(data.role_type || []);
  const [roleLevel, setRoleLevel] = useState<string[]>(data.role_level || []);
  const [minimumSalary, setMinimumSalary] = useState(data.minimum_salary || "");
  const [rolePriorities, setRolePriorities] = useState<string[]>(
    data.role_priorities || []
  );

  useEffect(() => {
    onChangeRef.current({
      role_type: roleType,
      role_level: roleLevel,
      minimum_salary: minimumSalary ? parseInt(minimumSalary) : null,
      role_priorities: rolePriorities,
    });
  }, [roleType, roleLevel, minimumSalary, rolePriorities]);

  const toggleItem = (
    item: string,
    list: string[],
    setter: (list: string[]) => void
  ) => {
    if (list.includes(item)) {
      setter(list.filter((i) => i !== item));
    } else {
      setter([...list, item]);
    }
  };

  return (
    <div className="space-y-8">
      {/* Type of Role */}
      <div>
        <h2 className="text-2xl font-semibold mb-2 font-sora">Type of role</h2>
        <p className="text-muted-foreground mb-6 font-inter">
          Select all employment types you're interested in
        </p>

        <div className="space-y-3">
          {ROLE_TYPES.map((type) => (
            <Label
              key={type}
              htmlFor={`role-type-${type}`}
              className={`flex items-center space-x-3 p-4 rounded-lg cursor-pointer transition-colors ${
                roleType.includes(type)
                  ? "bg-green-200 hover:bg-green-300"
                  : "bg-muted/50 hover:bg-muted"
              }`}
            >
              <Checkbox
                id={`role-type-${type}`}
                checked={roleType.includes(type)}
                onCheckedChange={() => toggleItem(type, roleType, setRoleType)}
                className={
                  roleType.includes(type)
                    ? "border-green-600 data-[state=checked]:bg-green-600"
                    : ""
                }
              />
              <span className="flex-1 font-medium font-inter">{type}</span>
            </Label>
          ))}
        </div>
      </div>

      {/* Level of Role - With Years */}
      <div className="border-t pt-6">
        <h2 className="text-2xl font-semibold mb-2 font-sora">
          What level of roles would you like to see?
        </h2>
        <p className="text-muted-foreground mb-6 font-inter">
          Select the most relevant for you (max 2)
        </p>

        <div className="space-y-2">
          {ROLE_LEVELS.map((level) => (
            <Label
              key={level.value}
              htmlFor={`role-level-${level.value}`}
              className={`flex items-center justify-between p-4 rounded-lg cursor-pointer transition-colors ${
                roleLevel.includes(level.value)
                  ? "bg-green-200 hover:bg-green-300"
                  : "bg-muted/10 hover:bg-muted/20 border border-muted"
              }`}
            >
              <div className="flex items-center space-x-3 flex-1">
                <Checkbox
                  id={`role-level-${level.value}`}
                  checked={roleLevel.includes(level.value)}
                  onCheckedChange={() => {
                    // Limit selection to 2 items
                    if (roleLevel.includes(level.value)) {
                      setRoleLevel(roleLevel.filter((l) => l !== level.value));
                    } else if (roleLevel.length < 2) {
                      setRoleLevel([...roleLevel, level.value]);
                    } else {
                      // Replace the first selection with the new one
                      setRoleLevel([roleLevel[1], level.value]);
                    }
                  }}
                  className={
                    roleLevel.includes(level.value)
                      ? "border-green-600 data-[state=checked]:bg-green-600"
                      : ""
                  }
                />
                <span className="font-medium font-inter">{level.label}</span>
              </div>
              {level.years && (
                <span className="text-sm text-muted-foreground font-medium font-inter">
                  {level.years}
                </span>
              )}
            </Label>
          ))}
        </div>

        {roleLevel.length >= 2 && (
          <p className="text-sm text-amber-600 mt-2 font-inter">
            Maximum 2 levels selected. Click to deselect or replace.
          </p>
        )}
      </div>

      {/* Minimum Salary */}
      <div className="border-t pt-6">
        <h2 className="text-2xl font-semibold mb-2 font-sora">
          Minimum salary
        </h2>
        <p className="text-muted-foreground mb-6 font-inter">
          What's your minimum acceptable salary? (Optional)
        </p>

        <div className="flex items-center gap-2">
          <span className="text-2xl font-semibold font-sora">£</span>
          <Input
            type="number"
            placeholder="e.g., 50000"
            value={minimumSalary}
            onChange={(e) => setMinimumSalary(e.target.value)}
            className="text-lg font-inter"
          />
          <span className="text-muted-foreground font-inter">/ year</span>
        </div>
      </div>

      {/* Role Priorities */}
      <div className="border-t pt-6">
        <h2 className="text-2xl font-semibold mb-2 font-sora">
          Role priorities
        </h2>
        <p className="text-muted-foreground mb-6 font-inter">
          What matters most to you in your next role?
        </p>

        <div className="grid grid-cols-2 gap-3">
          {ROLE_PRIORITIES.map((priority) => (
            <Label
              key={priority}
              htmlFor={`priority-${priority}`}
              className={`flex items-center space-x-3 p-4 rounded-lg cursor-pointer transition-colors ${
                rolePriorities.includes(priority)
                  ? "bg-green-200 hover:bg-green-300"
                  : "bg-muted/50 hover:bg-muted"
              }`}
            >
              <Checkbox
                id={`priority-${priority}`}
                checked={rolePriorities.includes(priority)}
                onCheckedChange={() =>
                  toggleItem(priority, rolePriorities, setRolePriorities)
                }
                className={
                  rolePriorities.includes(priority)
                    ? "border-green-600 data-[state=checked]:bg-green-600"
                    : ""
                }
              />
              <span className="flex-1 font-medium font-inter">{priority}</span>
            </Label>
          ))}
        </div>
      </div>
    </div>
  );
}
