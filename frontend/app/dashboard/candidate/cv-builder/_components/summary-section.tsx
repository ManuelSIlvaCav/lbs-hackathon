"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useCVBuilder } from "@/contexts/cv-builder-context";
import { Check, Loader2, Sparkles, X } from "lucide-react";
import { useEffect, useState } from "react";

export function SummarySection() {
  const { currentCV, updateCV, enhanceSummary, isEnhancing } = useCVBuilder();
  const [summary, setSummary] = useState("");
  const [isDirty, setIsDirty] = useState(false);
  const [enhancement, setEnhancement] = useState<string | null>(null);

  useEffect(() => {
    if (currentCV?.summary?.text) {
      setSummary(currentCV.summary.text);
      setIsDirty(false);
    }
  }, [currentCV]);

  const handleChange = (value: string) => {
    setSummary(value);
    setIsDirty(true);
  };

  const handleSave = async () => {
    await updateCV({ summary: { text: summary } });
    setIsDirty(false);
  };

  const handleEnhance = async () => {
    try {
      const result = await enhanceSummary({ current_summary: summary });
      if (result.summary_enhancement) {
        setEnhancement(result.summary_enhancement);
      }
    } catch (error) {
      console.error("Enhancement failed:", error);
    }
  };

  const acceptEnhancement = () => {
    if (enhancement) {
      setSummary(enhancement);
      setEnhancement(null);
      setIsDirty(true);
    }
  };

  const rejectEnhancement = () => {
    setEnhancement(null);
  };

  if (!currentCV) {
    return <p className="text-muted-foreground">No CV selected</p>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Professional Summary</h2>
          <p className="text-sm text-muted-foreground">
            A brief overview of your experience and what you bring
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={handleEnhance}
            disabled={isEnhancing || !summary}
            className="gap-2"
          >
            {isEnhancing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Sparkles className="h-4 w-4" />
            )}
            {isEnhancing ? "Enhancing..." : "AI Enhance"}
          </Button>
          <Button onClick={handleSave} disabled={!isDirty}>
            Save Changes
          </Button>
        </div>
      </div>

      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="summary">Summary (3-4 sentences recommended)</Label>
          <Textarea
            id="summary"
            value={summary}
            onChange={(e) => handleChange(e.target.value)}
            placeholder="Results-driven professional with X years of experience in..."
            rows={5}
            className="resize-none"
          />
          <p className="text-xs text-muted-foreground">
            {summary.split(/\s+/).filter(Boolean).length} words
          </p>
        </div>

        {/* Enhancement Suggestion */}
        {enhancement && (
          <Card className="border-primary/50 bg-primary/5">
            <CardContent className="pt-4">
              <div className="mb-2 flex items-center justify-between">
                <div className="flex items-center gap-2 text-sm font-medium text-primary">
                  <Sparkles className="h-4 w-4" />
                  AI-Enhanced Summary
                </div>
                <div className="flex gap-1">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={acceptEnhancement}
                    className="h-8 gap-1 text-green-600 hover:text-green-700"
                  >
                    <Check className="h-4 w-4" />
                    Accept
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={rejectEnhancement}
                    className="h-8 gap-1 text-red-600 hover:text-red-700"
                  >
                    <X className="h-4 w-4" />
                    Reject
                  </Button>
                </div>
              </div>
              <p className="text-sm leading-relaxed">{enhancement}</p>
            </CardContent>
          </Card>
        )}

        {/* Tips */}
        <div className="rounded-lg bg-muted/50 p-4">
          <h4 className="mb-2 text-sm font-medium">Tips for a Great Summary</h4>
          <ul className="space-y-1 text-xs text-muted-foreground">
            <li>• Lead with your years of experience and area of expertise</li>
            <li>• Include 1-2 quantified achievements</li>
            <li>• Mention key skills relevant to your target role</li>
            <li>• Keep it between 50-75 words</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
