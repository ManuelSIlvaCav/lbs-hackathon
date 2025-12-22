"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useCVBuilder } from "@/contexts/cv-builder-context";
import { CVContactInfo } from "@/lib/types/cv-builder";
import { useEffect, useState } from "react";

export function ContactSection() {
  const { currentCV, updateCV } = useCVBuilder();
  const [formData, setFormData] = useState<CVContactInfo>({
    full_name: "",
    email: null,
    phone: null,
    linkedin: null,
    location: null,
    website: null,
    other_links: [],
  });
  const [isDirty, setIsDirty] = useState(false);

  useEffect(() => {
    if (currentCV?.contact_info) {
      setFormData(currentCV.contact_info);
      setIsDirty(false);
    }
  }, [currentCV]);

  const handleChange = (field: keyof CVContactInfo, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value || null }));
    setIsDirty(true);
  };

  const handleSave = async () => {
    await updateCV({ contact_info: formData });
    setIsDirty(false);
  };

  if (!currentCV) {
    return <p className="text-muted-foreground">No CV selected</p>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Contact Information</h2>
          <p className="text-sm text-muted-foreground">
            Your basic contact details for recruiters
          </p>
        </div>
        <Button onClick={handleSave} disabled={!isDirty}>
          Save Changes
        </Button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="full_name">Full Name *</Label>
          <Input
            id="full_name"
            value={formData.full_name}
            onChange={(e) => handleChange("full_name", e.target.value)}
            placeholder="John Doe"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            value={formData.email || ""}
            onChange={(e) => handleChange("email", e.target.value)}
            placeholder="john@example.com"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="phone">Phone</Label>
          <Input
            id="phone"
            value={formData.phone || ""}
            onChange={(e) => handleChange("phone", e.target.value)}
            placeholder="+1 (555) 000-0000"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="location">Location</Label>
          <Input
            id="location"
            value={formData.location || ""}
            onChange={(e) => handleChange("location", e.target.value)}
            placeholder="San Francisco, CA"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="linkedin">LinkedIn</Label>
          <Input
            id="linkedin"
            value={formData.linkedin || ""}
            onChange={(e) => handleChange("linkedin", e.target.value)}
            placeholder="https://linkedin.com/in/johndoe"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="website">Website / Portfolio</Label>
          <Input
            id="website"
            value={formData.website || ""}
            onChange={(e) => handleChange("website", e.target.value)}
            placeholder="https://johndoe.com"
          />
        </div>
      </div>
    </div>
  );
}
