"use client";

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ScoringMetadata } from "@/lib/types/application";
import { CheckCircle2, XCircle } from "lucide-react";

interface ScoringDetailsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  scoringMetadata: ScoringMetadata | null | undefined;
  companyName?: string;
  jobTitle?: string;
}

export function ScoringDetailsDialog({
  open,
  onOpenChange,
  scoringMetadata,
  companyName = "Unknown Company",
  jobTitle = "Untitled Position",
}: ScoringDetailsDialogProps) {
  if (!scoringMetadata) {
    return null;
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-green-600";
    if (score >= 60) return "text-blue-600";
    if (score >= 40) return "text-orange-600";
    return "text-red-600";
  };

  const renderDimensionBreakdown = (
    breakdown: any,
    title: "Minimum" | "Preferred"
  ) => {
    const dimensions = Object.entries(breakdown).filter(
      ([_, value]: [string, any]) => value.active
    );

    if (dimensions.length === 0) {
      return (
        <p className="text-sm text-muted-foreground py-4">
          No {title.toLowerCase()} requirements specified
        </p>
      );
    }

    return (
      <div className="space-y-3">
        {dimensions.map(([key, value]: [string, any]) => (
          <div
            key={key}
            className="border rounded-lg p-4 bg-card hover:bg-accent/5 transition-colors"
          >
            <div className="flex items-start justify-between gap-3 mb-2">
              <div className="flex items-center gap-2">
                {value.active ? (
                  <CheckCircle2 className="h-4 w-4 text-green-600 shrink-0 mt-0.5" />
                ) : (
                  <XCircle className="h-4 w-4 text-gray-400 shrink-0 mt-0.5" />
                )}
                <h4 className="font-medium text-sm">
                  {key
                    .split("_")
                    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
                    .join(" ")}
                </h4>
              </div>
              <Badge
                variant="outline"
                className={`${getScoreColor(value.score)} border-current`}
              >
                {Math.round(value.score)}
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground pl-6">
              {value.explanation}
            </p>
          </div>
        ))}
      </div>
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Scoring Details</DialogTitle>
          <DialogDescription>
            {companyName} - {jobTitle}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Overall Scores */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 border rounded-lg bg-card">
              <div
                className={`text-2xl font-bold ${getScoreColor(
                  scoringMetadata.overall_match_score
                )}`}
              >
                {Math.round(scoringMetadata.overall_match_score)}
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                Overall Match
              </div>
            </div>
            <div className="text-center p-4 border rounded-lg bg-card">
              <div
                className={`text-2xl font-bold ${getScoreColor(
                  scoringMetadata.minimum_score
                )}`}
              >
                {Math.round(scoringMetadata.minimum_score)}
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                Minimum Score
              </div>
            </div>
            <div className="text-center p-4 border rounded-lg bg-card">
              <div
                className={`text-2xl font-bold ${getScoreColor(
                  scoringMetadata.preferred_score
                )}`}
              >
                {Math.round(scoringMetadata.preferred_score)}
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                Preferred Score
              </div>
            </div>
            <div className="text-center p-4 border rounded-lg bg-card">
              <div
                className={`text-2xl font-bold ${getScoreColor(
                  scoringMetadata.subjective_score
                )}`}
              >
                {Math.round(scoringMetadata.subjective_score)}
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                Subjective Score
              </div>
            </div>
          </div>

          {/* Subjective Rationale */}
          {scoringMetadata.subjective_rationale && (
            <div className="border rounded-lg p-4 bg-muted/50">
              <h3 className="font-medium text-sm mb-2">AI Analysis</h3>
              <p className="text-sm text-muted-foreground">
                {scoringMetadata.subjective_rationale}
              </p>
            </div>
          )}

          {/* Dimension Breakdown */}
          <Accordion type="single" collapsible className="w-full">
            <AccordionItem value="minimum">
              <AccordionTrigger>
                <div className="flex items-center gap-2">
                  <span>Minimum Requirements</span>
                  <Badge variant="secondary">
                    {Math.round(scoringMetadata.minimum_score)}
                  </Badge>
                </div>
              </AccordionTrigger>
              <AccordionContent>
                {renderDimensionBreakdown(
                  scoringMetadata.dimension_breakdown.minimum,
                  "Minimum"
                )}
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="preferred">
              <AccordionTrigger>
                <div className="flex items-center gap-2">
                  <span>Preferred Qualifications</span>
                  <Badge variant="secondary">
                    {Math.round(scoringMetadata.preferred_score)}
                  </Badge>
                </div>
              </AccordionTrigger>
              <AccordionContent>
                {renderDimensionBreakdown(
                  scoringMetadata.dimension_breakdown.preferred,
                  "Preferred"
                )}
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </div>
      </DialogContent>
    </Dialog>
  );
}
