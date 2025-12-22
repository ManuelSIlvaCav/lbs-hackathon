"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useCVBuilder } from "@/contexts/cv-builder-context";
import { CVTemplate } from "@/lib/types/cv-builder";
import { cn } from "@/lib/utils";
import { Check, FileText, Loader2 } from "lucide-react";

interface TemplateSelectorProps {
  onExport?: () => void;
}

export function TemplateSelector({ onExport }: TemplateSelectorProps) {
  const {
    currentCV,
    templates,
    isLoadingTemplates,
    selectedTemplateId,
    setSelectedTemplateId,
    exportCV,
    isExporting,
  } = useCVBuilder();

  const handleExport = async () => {
    if (!currentCV || !selectedTemplateId) return;
    await exportCV(selectedTemplateId);
    onExport?.();
  };

  if (isLoadingTemplates) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Choose a Template</h2>
        <p className="text-sm text-muted-foreground">
          Select an ATS-friendly template for your CV export
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {templates.map((template) => (
          <TemplateCard
            key={template.id}
            template={template}
            isSelected={selectedTemplateId === template.id}
            onSelect={() => setSelectedTemplateId(template.id)}
          />
        ))}
      </div>

      <div className="flex justify-end gap-2 border-t pt-4">
        <Button
          size="lg"
          onClick={handleExport}
          disabled={!selectedTemplateId || !currentCV || isExporting}
        >
          {isExporting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Generating...
            </>
          ) : (
            <>
              <FileText className="mr-2 h-4 w-4" />
              Export as PDF
            </>
          )}
        </Button>
      </div>
    </div>
  );
}

interface TemplateCardProps {
  template: CVTemplate;
  isSelected: boolean;
  onSelect: () => void;
}

function TemplateCard({ template, isSelected, onSelect }: TemplateCardProps) {
  const previewColors = {
    Classic: { primary: "#2563eb", accent: "#3b82f6", bg: "#f8fafc" },
    Modern: { primary: "#18181b", accent: "#71717a", bg: "#fafafa" },
    Executive: { primary: "#1e3a5f", accent: "#2d5a8b", bg: "#f8fafc" },
    Tech: { primary: "#10b981", accent: "#34d399", bg: "#f0fdf4" },
  };

  const templateName = template.name.split(
    " "
  )[0] as keyof typeof previewColors;
  const colors = previewColors[templateName] || previewColors.Classic;

  return (
    <Card
      className={cn(
        "cursor-pointer transition-all hover:shadow-md",
        isSelected && "ring-2 ring-primary"
      )}
      onClick={onSelect}
    >
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="flex items-center gap-2 text-base">
              {template.name}
              {isSelected && <Check className="h-4 w-4 text-primary" />}
            </CardTitle>
            <CardDescription className="text-xs">
              {template.description}
            </CardDescription>
          </div>
          <Badge variant="outline" className="text-xs">
            ATS Friendly
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        {/* Mini preview */}
        <div
          className="rounded border p-3"
          style={{ backgroundColor: colors.bg }}
        >
          <div className="space-y-2">
            {/* Header preview */}
            <div className="space-y-1">
              <div
                className="h-3 w-24 rounded"
                style={{ backgroundColor: colors.primary }}
              />
              <div className="h-1.5 w-32 rounded bg-muted" />
            </div>
            {/* Section preview */}
            <div className="space-y-1 border-t pt-2">
              <div
                className="h-2 w-16 rounded"
                style={{ backgroundColor: colors.accent }}
              />
              <div className="space-y-0.5">
                <div className="h-1 w-full rounded bg-muted/80" />
                <div className="h-1 w-3/4 rounded bg-muted/60" />
              </div>
            </div>
            {/* Section preview */}
            <div className="space-y-1 border-t pt-2">
              <div
                className="h-2 w-20 rounded"
                style={{ backgroundColor: colors.accent }}
              />
              <div className="space-y-0.5">
                <div className="h-1 w-full rounded bg-muted/80" />
                <div className="h-1 w-2/3 rounded bg-muted/60" />
              </div>
            </div>
          </div>
        </div>

        {/* Template details */}
        <div className="mt-3 flex flex-wrap gap-1">
          <Badge variant="secondary" className="text-xs">
            {template.styling.font_family}
          </Badge>
          {template.sections.some((s) => s.name === "summary" && s.visible) && (
            <Badge variant="secondary" className="text-xs">
              Summary
            </Badge>
          )}
          {template.sections.some((s) => s.name === "skills" && s.visible) && (
            <Badge variant="secondary" className="text-xs">
              Skills
            </Badge>
          )}
          {template.sections.some(
            (s) => s.name === "projects" && s.visible
          ) && (
            <Badge variant="secondary" className="text-xs">
              Projects
            </Badge>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
