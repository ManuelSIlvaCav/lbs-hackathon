"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useCVBuilder } from "@/contexts/cv-builder-context";
import {
  Briefcase,
  Download,
  FileText,
  FolderOpen,
  GraduationCap,
  Plus,
  Sparkles,
  Target,
  Trash2,
  User,
  Wrench,
} from "lucide-react";
import {
  ContactSection,
  CVSelector,
  EducationSection,
  ExperienceSection,
  ProjectsSection,
  ScoreCard,
  SkillsSection,
  SummarySection,
  TemplateSelector,
} from "./_components";

export default function CVBuilderPage() {
  const {
    currentCV,
    cvList,
    templates,
    isLoading,
    error,
    createCV,
    deleteCV,
    scoreCV,
    exportCV,
    isScoring,
    isExporting,
  } = useCVBuilder();

  if (isLoading) {
    return (
      <div className="flex h-full w-full flex-col">
        <header className="flex items-center justify-between border-b px-6 py-4">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-10 w-32" />
        </header>
        <div className="flex-1 p-6">
          <div className="grid gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <Skeleton className="h-[600px] w-full" />
            </div>
            <div>
              <Skeleton className="h-[400px] w-full" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-full w-full items-center justify-center">
        <Card className="max-w-md">
          <CardContent className="pt-6">
            <p className="text-center text-muted-foreground">
              Error loading CV Builder: {error.message}
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // No CVs yet - show create prompt
  if (cvList.length === 0) {
    return (
      <div className="flex h-full w-full flex-col">
        <header className="flex items-center justify-between border-b px-6 py-4">
          <div className="flex items-center gap-2">
            <FileText className="h-6 w-6" />
            <h1 className="text-2xl font-semibold">CV Builder</h1>
          </div>
        </header>
        <div className="flex flex-1 items-center justify-center p-6">
          <Card className="max-w-lg text-center">
            <CardHeader>
              <CardTitle className="flex items-center justify-center gap-2">
                <Sparkles className="h-6 w-6 text-primary" />
                Create Your ATS-Optimized CV
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-muted-foreground">
                Build a professional CV that gets past Applicant Tracking
                Systems. Use AI to enhance your bullet points and get real-time
                scoring.
              </p>
              <div className="flex flex-col gap-2 sm:flex-row sm:justify-center">
                <Button
                  onClick={() =>
                    createCV({ name: "My CV", from_parsed_cv: true })
                  }
                  className="gap-2"
                >
                  <Plus className="h-4 w-4" />
                  Create from Uploaded CV
                </Button>
                <Button
                  variant="outline"
                  onClick={() =>
                    createCV({ name: "My CV", from_parsed_cv: false })
                  }
                  className="gap-2"
                >
                  <Plus className="h-4 w-4" />
                  Start from Scratch
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full w-full flex-col">
      {/* Header */}
      <header className="flex items-center justify-between border-b px-6 py-4">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <FileText className="h-6 w-6" />
            <h1 className="text-2xl font-semibold">CV Builder</h1>
          </div>
          <CVSelector />
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="destructive"
            onClick={() => {
              if (
                currentCV?._id &&
                confirm(
                  "Are you sure you want to delete this CV? This action cannot be undone."
                )
              ) {
                deleteCV(currentCV._id);
              }
            }}
            disabled={!currentCV}
            className="gap-2"
          >
            <Trash2 className="h-4 w-4" />
            Delete CV
          </Button>
          <Button
            variant="outline"
            onClick={() => scoreCV()}
            disabled={isScoring || !currentCV}
            className="gap-2"
          >
            <Target className="h-4 w-4" />
            {isScoring ? "Scoring..." : "Score CV"}
          </Button>
          <Button
            onClick={() => exportCV(currentCV?.selected_template || "classic")}
            disabled={isExporting || !currentCV}
            className="gap-2"
          >
            <Download className="h-4 w-4" />
            {isExporting ? "Exporting..." : "Export PDF"}
          </Button>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 overflow-auto p-6">
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Left Panel - Editor */}
          <div className="lg:col-span-2">
            <Card>
              <CardContent className="p-0">
                <Tabs defaultValue="contact" className="w-full">
                  <TabsList className="w-full justify-start rounded-none border-b bg-transparent p-0">
                    <TabsTrigger
                      value="contact"
                      className="gap-2 rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent"
                    >
                      <User className="h-4 w-4" />
                      Contact
                    </TabsTrigger>
                    <TabsTrigger
                      value="summary"
                      className="gap-2 rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent"
                    >
                      <FileText className="h-4 w-4" />
                      Summary
                    </TabsTrigger>
                    <TabsTrigger
                      value="experience"
                      className="gap-2 rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent"
                    >
                      <Briefcase className="h-4 w-4" />
                      Experience
                    </TabsTrigger>
                    <TabsTrigger
                      value="education"
                      className="gap-2 rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent"
                    >
                      <GraduationCap className="h-4 w-4" />
                      Education
                    </TabsTrigger>
                    <TabsTrigger
                      value="skills"
                      className="gap-2 rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent"
                    >
                      <Wrench className="h-4 w-4" />
                      Skills
                    </TabsTrigger>
                    <TabsTrigger
                      value="projects"
                      className="gap-2 rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent"
                    >
                      <FolderOpen className="h-4 w-4" />
                      Projects
                    </TabsTrigger>
                  </TabsList>

                  <div className="p-6">
                    <TabsContent value="contact" className="m-0">
                      <ContactSection />
                    </TabsContent>
                    <TabsContent value="summary" className="m-0">
                      <SummarySection />
                    </TabsContent>
                    <TabsContent value="experience" className="m-0">
                      <ExperienceSection />
                    </TabsContent>
                    <TabsContent value="education" className="m-0">
                      <EducationSection />
                    </TabsContent>
                    <TabsContent value="skills" className="m-0">
                      <SkillsSection />
                    </TabsContent>
                    <TabsContent value="projects" className="m-0">
                      <ProjectsSection />
                    </TabsContent>
                  </div>
                </Tabs>
              </CardContent>
            </Card>
          </div>

          {/* Right Panel - Score & Templates */}
          <div className="space-y-6">
            <ScoreCard />
            <TemplateSelector />
          </div>
        </div>
      </div>
    </div>
  );
}
