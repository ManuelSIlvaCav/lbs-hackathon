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
import { cn } from "@/lib/utils";
import { AlertCircle, Loader2, RefreshCw, TrendingUp } from "lucide-react";

export function ScoreCard() {
  const { currentCV, scoreCV, isScoring } = useCVBuilder();

  const score = currentCV?.latest_score;

  const handleRefreshScore = async () => {
    await scoreCV();
  };

  const getScoreColor = (value: number) => {
    if (value >= 80) return "text-green-600";
    if (value >= 60) return "text-yellow-600";
    return "text-red-600";
  };

  const getScoreBadge = (value: number) => {
    if (value >= 80) return { label: "Excellent", variant: "default" as const };
    if (value >= 60) return { label: "Good", variant: "secondary" as const };
    return { label: "Needs Work", variant: "destructive" as const };
  };

  if (!currentCV) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8">
          <p className="text-muted-foreground">No CV selected</p>
        </CardContent>
      </Card>
    );
  }

  if (!score && !isScoring) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            ATS Score
          </CardTitle>
          <CardDescription>
            Analyze your CV for ATS compatibility
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center gap-4 py-4">
            <AlertCircle className="h-12 w-12 text-muted-foreground" />
            <p className="text-center text-muted-foreground">
              Your CV hasn't been scored yet. Run an analysis to see how
              ATS-friendly your CV is.
            </p>
            <Button onClick={handleRefreshScore}>
              <TrendingUp className="mr-2 h-4 w-4" />
              Analyze CV
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (isScoring) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <div className="flex flex-col items-center gap-4">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <p className="text-muted-foreground">Analyzing your CV...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const badge = getScoreBadge(score!.overall_score);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              ATS Score
            </CardTitle>
            <CardDescription>
              How well your CV performs with Applicant Tracking Systems
            </CardDescription>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefreshScore}
            disabled={isScoring}
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Overall score */}
        <div className="flex items-center gap-6">
          <div className="relative h-24 w-24">
            <svg className="h-24 w-24 -rotate-90 transform">
              <circle
                className="text-muted"
                strokeWidth="8"
                stroke="currentColor"
                fill="transparent"
                r="40"
                cx="48"
                cy="48"
              />
              <circle
                className={getScoreColor(score!.overall_score)}
                strokeWidth="8"
                strokeDasharray={`${
                  (score!.overall_score / 100) * 251.2
                } 251.2`}
                strokeLinecap="round"
                stroke="currentColor"
                fill="transparent"
                r="40"
                cx="48"
                cy="48"
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span
                className={cn(
                  "text-2xl font-bold",
                  getScoreColor(score!.overall_score)
                )}
              >
                {score!.overall_score}
              </span>
            </div>
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <span className="text-lg font-semibold">Overall Score</span>
              <Badge variant={badge.variant}>{badge.label}</Badge>
            </div>
            <p className="mt-1 text-sm text-muted-foreground">
              Your CV is{" "}
              {score!.overall_score >= 80
                ? "well-optimized"
                : score!.overall_score >= 60
                ? "fairly optimized"
                : "under-optimized"}{" "}
              for ATS parsing
            </p>
          </div>
        </div>

        {/* Breakdown */}
        <div className="space-y-4">
          <h4 className="text-sm font-medium">Score Breakdown</h4>
          <div className="space-y-3">
            <ScoreItem
              label="Keyword Optimization"
              value={score!.breakdown.keyword_optimization.score}
              description="Industry-relevant keywords and skills"
            />
            <ScoreItem
              label="Format Compliance"
              value={score!.breakdown.format_compliance.score}
              description="ATS-parseable structure and layout"
            />
            <ScoreItem
              label="Content Quality"
              value={score!.breakdown.content_quality.score}
              description="Action verbs and quantified achievements"
            />
            <ScoreItem
              label="Section Completeness"
              value={score!.breakdown.section_completeness.score}
              description="All essential sections included"
            />
            <ScoreItem
              label="Action Verbs"
              value={score!.breakdown.action_verbs.score}
              description="Use of strong action verbs"
            />
            <ScoreItem
              label="Quantification"
              value={score!.breakdown.quantification.score}
              description="Metrics and numbers in achievements"
            />
            <ScoreItem
              label="Length Optimization"
              value={score!.breakdown.length_optimization.score}
              description="CV length is appropriate"
            />
          </div>
        </div>

        {/* Recommendations */}
        {score!.top_recommendations &&
          score!.top_recommendations.length > 0 && (
            <div className="space-y-3">
              <h4 className="text-sm font-medium">Top Recommendations</h4>
              <ul className="space-y-2">
                {score!.top_recommendations.slice(0, 5).map((rec, index) => (
                  <li
                    key={index}
                    className="flex gap-2 text-sm text-muted-foreground"
                  >
                    <span className="text-primary">•</span>
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          )}
      </CardContent>
    </Card>
  );
}

interface ScoreItemProps {
  label: string;
  value: number;
  description: string;
}

function ScoreItem({ label, value, description }: ScoreItemProps) {
  const getProgressColor = (v: number) => {
    if (v >= 80) return "bg-green-500";
    if (v >= 60) return "bg-yellow-500";
    return "bg-red-500";
  };

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm">
        <span>{label}</span>
        <span className="font-medium">{value}/100</span>
      </div>
      <div className="h-2 rounded-full bg-muted">
        <div
          className={cn(
            "h-2 rounded-full transition-all",
            getProgressColor(value)
          )}
          style={{ width: `${value}%` }}
        />
      </div>
      <p className="text-xs text-muted-foreground">{description}</p>
    </div>
  );
}
