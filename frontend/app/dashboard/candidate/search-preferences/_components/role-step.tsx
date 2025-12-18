"use client";

import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useJobSearchFilters } from "@/contexts/job-search-filters-context";
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

  const { searchOptions, isLoading } = useJobSearchFilters();

  const [roleType, setRoleType] = useState<string[]>(data.role_type || []);
  const [roleLevel, setRoleLevel] = useState<string[]>(data.role_level || []);
  const [minimumSalary, setMinimumSalary] = useState(data.minimum_salary || "");
  const [profileCategories, setProfileCategories] = useState<string[]>(
    data.profile_categories || []
  );
  const [roleTitles, setRoleTitles] = useState<string[]>(
    data.role_titles || []
  );

  // Sync state when data changes
  useEffect(() => {
    if (data.role_type) setRoleType(data.role_type);
    if (data.role_level) setRoleLevel(data.role_level);
    if (data.minimum_salary !== undefined)
      setMinimumSalary(data.minimum_salary || "");
    if (data.profile_categories) setProfileCategories(data.profile_categories);
    if (data.role_titles) setRoleTitles(data.role_titles);
  }, [data]);

  useEffect(() => {
    onChangeRef.current({
      role_type: roleType,
      role_level: roleLevel,
      minimum_salary: minimumSalary ? parseInt(minimumSalary) : null,
      profile_categories: profileCategories,
      role_titles: roleTitles,
    });
  }, [roleType, roleLevel, minimumSalary, profileCategories, roleTitles]);

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

  const toggleCategory = (category: string) => {
    if (profileCategories.includes(category)) {
      // Remove category
      setProfileCategories(profileCategories.filter((c) => c !== category));

      // Remove all role titles from this category
      const categoryRoles =
        searchOptions?.role_titles_by_category[category] || [];
      setRoleTitles(roleTitles.filter((role) => !categoryRoles.includes(role)));
    } else {
      // Add category (max 3)
      if (profileCategories.length < 3) {
        setProfileCategories([...profileCategories, category]);
      }
    }
  };

  const toggleRoleTitle = (role: string, category: string) => {
    if (roleTitles.includes(role)) {
      // Remove role
      setRoleTitles(roleTitles.filter((r) => r !== role));
    } else {
      // Check how many roles are already selected from this category
      const categoryRoles =
        searchOptions?.role_titles_by_category[category] || [];
      const selectedFromCategory = roleTitles.filter((r) =>
        categoryRoles.includes(r)
      );

      // Add role (max 3 per category)
      if (selectedFromCategory.length < 3) {
        setRoleTitles([...roleTitles, role]);
      }
    }
  };

  const getRoleCountForCategory = (category: string) => {
    const categoryRoles =
      searchOptions?.role_titles_by_category[category] || [];
    return roleTitles.filter((r) => categoryRoles.includes(r)).length;
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

      {/* Profile Categories */}
      <div className="border-t pt-6">
        <h2 className="text-2xl font-semibold mb-2 font-sora">
          Profile Categories
        </h2>
        <p className="text-muted-foreground mb-4 font-inter">
          Select up to 3 job categories you're interested in
        </p>

        {profileCategories.length >= 3 && (
          <p className="text-sm text-amber-600 mb-4 font-inter">
            Maximum 3 categories selected. Deselect one to choose a different
            category.
          </p>
        )}

        {/* Selected Categories Badges */}
        {profileCategories.length > 0 && (
          <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-sm font-semibold mb-2 font-sora text-green-800">
              Selected Categories ({profileCategories.length}/3):
            </p>
            <div className="flex flex-wrap gap-2">
              {profileCategories.map((category) => (
                <div
                  key={category}
                  className="inline-flex items-center gap-2 px-3 py-1 bg-green-500 text-white rounded-full text-sm font-medium font-inter"
                >
                  {category}
                  <button
                    onClick={() => toggleCategory(category)}
                    className="hover:bg-green-600 rounded-full p-0.5 transition-colors"
                    type="button"
                  >
                    <svg
                      className="w-3 h-3"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {isLoading ? (
          <div className="text-center py-8 text-muted-foreground">
            Loading categories...
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 md:max-h-none max-h-96 overflow-y-auto">
            {searchOptions?.profile_categories.map((category) => (
              <Label
                key={category}
                htmlFor={`category-${category}`}
                className={`flex items-center space-x-3 p-4 rounded-lg cursor-pointer transition-colors ${
                  profileCategories.includes(category)
                    ? "bg-green-200 hover:bg-green-300"
                    : profileCategories.length >= 3
                    ? "bg-muted/30 hover:bg-muted/40 opacity-50 cursor-not-allowed"
                    : "bg-muted/50 hover:bg-muted"
                }`}
              >
                <Checkbox
                  id={`category-${category}`}
                  checked={profileCategories.includes(category)}
                  onCheckedChange={() => toggleCategory(category)}
                  disabled={
                    !profileCategories.includes(category) &&
                    profileCategories.length >= 3
                  }
                  className={
                    profileCategories.includes(category)
                      ? "border-green-600 data-[state=checked]:bg-green-600"
                      : ""
                  }
                />
                <span className="flex-1 font-medium font-inter text-sm">
                  {category}
                </span>
              </Label>
            ))}
          </div>
        )}
      </div>

      {/* Role Titles - Only show if categories are selected */}
      {profileCategories.length > 0 && (
        <div className="border-t pt-6">
          <h2 className="text-2xl font-semibold mb-2 font-sora">
            Specific Roles
          </h2>
          <p className="text-muted-foreground mb-4 font-inter">
            Select up to 3 specific roles within each chosen category
          </p>

          {/* Selected Roles Badges */}
          {roleTitles.length > 0 && (
            <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm font-semibold mb-2 font-sora text-blue-800">
                Selected Roles ({roleTitles.length}):
              </p>
              <div className="space-y-3">
                {profileCategories.map((category) => {
                  const categoryRoles =
                    searchOptions?.role_titles_by_category[category] || [];
                  const selectedRoles = roleTitles.filter((r) =>
                    categoryRoles.includes(r)
                  );

                  if (selectedRoles.length === 0) return null;

                  return (
                    <div key={category}>
                      <p className="text-xs font-semibold mb-1.5 font-sora text-blue-700">
                        {category}:
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {selectedRoles.map((role) => (
                          <div
                            key={role}
                            className="inline-flex items-center gap-2 px-3 py-1 bg-blue-500 text-white rounded-full text-xs font-medium font-inter"
                          >
                            {role}
                            <button
                              onClick={() => toggleRoleTitle(role, category)}
                              className="hover:bg-blue-600 rounded-full p-0.5 transition-colors"
                              type="button"
                            >
                              <svg
                                className="w-3 h-3"
                                fill="currentColor"
                                viewBox="0 0 20 20"
                              >
                                <path
                                  fillRule="evenodd"
                                  d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                                  clipRule="evenodd"
                                />
                              </svg>
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          <div className="space-y-6 max-h-[600px] overflow-y-auto pr-2">
            {profileCategories.map((category) => {
              const roleCount = getRoleCountForCategory(category);
              const categoryRoles =
                searchOptions?.role_titles_by_category[category] || [];

              return (
                <div key={category} className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold font-sora text-green-700">
                      {category}
                    </h3>
                    <span className="text-sm text-muted-foreground font-inter">
                      {roleCount}/3 selected
                    </span>
                  </div>
                  {roleCount >= 3 && (
                    <p className="text-xs text-amber-600 font-inter">
                      Maximum 3 roles selected for this category
                    </p>
                  )}
                  <div className="grid grid-cols-2 gap-2 pl-4">
                    {categoryRoles.map((role) => {
                      const isSelected = roleTitles.includes(role);
                      const isDisabled = !isSelected && roleCount >= 3;

                      return (
                        <Label
                          key={role}
                          htmlFor={`role-${role}`}
                          className={`flex items-center space-x-2 p-3 rounded-lg cursor-pointer transition-colors ${
                            isSelected
                              ? "bg-green-100 hover:bg-green-200"
                              : isDisabled
                              ? "bg-muted/20 hover:bg-muted/30 opacity-50 cursor-not-allowed"
                              : "bg-muted/30 hover:bg-muted/50"
                          }`}
                        >
                          <Checkbox
                            id={`role-${role}`}
                            checked={isSelected}
                            onCheckedChange={() =>
                              toggleRoleTitle(role, category)
                            }
                            disabled={isDisabled}
                            className={
                              isSelected
                                ? "border-green-600 data-[state=checked]:bg-green-600"
                                : ""
                            }
                          />
                          <span className="flex-1 font-medium font-inter text-sm">
                            {role}
                          </span>
                        </Label>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
