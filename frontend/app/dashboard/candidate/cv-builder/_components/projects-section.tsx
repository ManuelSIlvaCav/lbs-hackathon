"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useCVBuilder } from "@/contexts/cv-builder-context";
import { BulletEnhancement, CVProject } from "@/lib/types/cv-builder";
import {
  Check,
  ChevronDown,
  Loader2,
  Plus,
  Sparkles,
  Trash2,
  X,
} from "lucide-react";
import { KeyboardEvent, useEffect, useState } from "react";
import { v4 as uuidv4 } from "uuid";

export function ProjectsSection() {
  const { currentCV, updateCV, enhanceBullets, isEnhancingBullets } =
    useCVBuilder();
  const [projects, setProjects] = useState<CVProject[]>([]);
  const [isDirty, setIsDirty] = useState(false);
  const [openIds, setOpenIds] = useState<Set<string>>(new Set());
  const [enhancements, setEnhancements] = useState<
    Record<string, BulletEnhancement[]>
  >({});
  const [enhancingId, setEnhancingId] = useState<string | null>(null);
  const [techInput, setTechInput] = useState<Record<string, string>>({});

  useEffect(() => {
    if (currentCV?.projects) {
      setProjects(currentCV.projects);
      if (currentCV.projects.length > 0) {
        setOpenIds(new Set([currentCV.projects[0].id]));
      }
      setIsDirty(false);
    }
  }, [currentCV]);

  const handleSave = async () => {
    await updateCV({ projects });
    setIsDirty(false);
  };

  const addProject = () => {
    const newProject: CVProject = {
      id: uuidv4(),
      name: "",
      description: "",
      technologies: [],
      bullets: [""],
    };
    setProjects((prev) => [...prev, newProject]);
    setOpenIds((prev) => new Set(prev).add(newProject.id));
    setIsDirty(true);
  };

  const removeProject = (id: string) => {
    setProjects((prev) => prev.filter((p) => p.id !== id));
    setIsDirty(true);
  };

  const updateProject = (
    id: string,
    field: keyof CVProject,
    value: unknown
  ) => {
    setProjects((prev) =>
      prev.map((p) => (p.id === id ? { ...p, [field]: value } : p))
    );
    setIsDirty(true);
  };

  const addBullet = (projectId: string) => {
    setProjects((prev) =>
      prev.map((p) =>
        p.id === projectId ? { ...p, bullets: [...p.bullets, ""] } : p
      )
    );
    setIsDirty(true);
  };

  const removeBullet = (projectId: string, index: number) => {
    setProjects((prev) =>
      prev.map((p) =>
        p.id === projectId
          ? { ...p, bullets: p.bullets.filter((_, i) => i !== index) }
          : p
      )
    );
    setIsDirty(true);
  };

  const updateBullet = (projectId: string, index: number, value: string) => {
    setProjects((prev) =>
      prev.map((p) =>
        p.id === projectId
          ? {
              ...p,
              bullets: p.bullets.map((b, i) => (i === index ? value : b)),
            }
          : p
      )
    );
    setIsDirty(true);
  };

  const addTechnology = (projectId: string) => {
    const value = techInput[projectId]?.trim();
    if (value) {
      const project = projects.find((p) => p.id === projectId);
      if (project && !project.technologies.includes(value)) {
        updateProject(projectId, "technologies", [
          ...project.technologies,
          value,
        ]);
        setTechInput((prev) => ({ ...prev, [projectId]: "" }));
      }
    }
  };

  const removeTechnology = (projectId: string, tech: string) => {
    const project = projects.find((p) => p.id === projectId);
    if (project) {
      updateProject(
        projectId,
        "technologies",
        project.technologies.filter((t) => t !== tech)
      );
    }
  };

  const handleTechKeyPress = (
    e: KeyboardEvent<HTMLInputElement>,
    projectId: string
  ) => {
    if (e.key === "Enter") {
      e.preventDefault();
      addTechnology(projectId);
    }
  };

  const handleEnhanceBullets = async (project: CVProject) => {
    setEnhancingId(project.id);
    try {
      const result = await enhanceBullets({
        section_type: "project",
        section_id: project.id,
        bullets: project.bullets.filter((b) => b.trim()),
      });
      setEnhancements((prev) => ({
        ...prev,
        [project.id]: result.bullet_enhancements,
      }));
    } finally {
      setEnhancingId(null);
    }
  };

  const acceptEnhancement = (
    projectId: string,
    originalBullet: string,
    enhancedBullet: string
  ) => {
    const project = projects.find((p) => p.id === projectId);
    if (project) {
      const newBullets = project.bullets.map((b) =>
        b === originalBullet ? enhancedBullet : b
      );
      updateProject(projectId, "bullets", newBullets);
      setEnhancements((prev) => ({
        ...prev,
        [projectId]: prev[projectId].filter(
          (e) => e.original !== originalBullet
        ),
      }));
    }
  };

  const rejectEnhancement = (projectId: string, originalBullet: string) => {
    setEnhancements((prev) => ({
      ...prev,
      [projectId]: prev[projectId].filter((e) => e.original !== originalBullet),
    }));
  };

  const toggleOpen = (id: string) => {
    setOpenIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  if (!currentCV) {
    return <p className="text-muted-foreground">No CV selected</p>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Projects</h2>
          <p className="text-sm text-muted-foreground">
            Showcase personal or professional projects
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={addProject}>
            <Plus className="mr-2 h-4 w-4" /> Add Project
          </Button>
          <Button onClick={handleSave} disabled={!isDirty}>
            Save Changes
          </Button>
        </div>
      </div>

      <div className="space-y-4">
        {projects.length === 0 ? (
          <div className="rounded-lg border border-dashed p-8 text-center">
            <p className="text-muted-foreground">No projects added yet</p>
            <Button variant="link" onClick={addProject}>
              Add your first project
            </Button>
          </div>
        ) : (
          projects.map((project, index) => (
            <Collapsible
              key={project.id}
              open={openIds.has(project.id)}
              onOpenChange={() => toggleOpen(project.id)}
            >
              <div className="rounded-lg border">
                <CollapsibleTrigger className="flex w-full items-center justify-between p-4 hover:bg-muted/50">
                  <div className="flex items-center gap-2 text-left">
                    <span className="text-sm text-muted-foreground">
                      {index + 1}.
                    </span>
                    <div>
                      <p className="font-medium">
                        {project.name || "New Project"}
                      </p>
                      {project.technologies.length > 0 && (
                        <p className="text-xs text-muted-foreground">
                          {project.technologies.slice(0, 3).join(", ")}
                          {project.technologies.length > 3 &&
                            ` +${project.technologies.length - 3} more`}
                        </p>
                      )}
                    </div>
                  </div>
                  <ChevronDown className="h-4 w-4 transition-transform ui-open:rotate-180" />
                </CollapsibleTrigger>

                <CollapsibleContent className="border-t p-4">
                  <div className="space-y-4">
                    {/* Basic info */}
                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="space-y-2">
                        <Label>Project Name</Label>
                        <Input
                          value={project.name}
                          onChange={(e) =>
                            updateProject(project.id, "name", e.target.value)
                          }
                          placeholder="e.g., E-commerce Platform"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>URL (optional)</Label>
                        <Input
                          value={project.url || ""}
                          onChange={(e) =>
                            updateProject(project.id, "url", e.target.value)
                          }
                          placeholder="https://github.com/..."
                        />
                      </div>
                    </div>

                    {/* Description */}
                    <div className="space-y-2">
                      <Label>Description</Label>
                      <Textarea
                        value={project.description || ""}
                        onChange={(e) =>
                          updateProject(
                            project.id,
                            "description",
                            e.target.value
                          )
                        }
                        placeholder="Brief overview of the project..."
                        rows={2}
                      />
                    </div>

                    {/* Technologies */}
                    <div className="space-y-2">
                      <Label>Technologies Used</Label>
                      <div className="flex flex-wrap gap-2">
                        {project.technologies.map((tech) => (
                          <Badge
                            key={tech}
                            variant="secondary"
                            className="gap-1 pr-1"
                          >
                            {tech}
                            <button
                              onClick={() => removeTechnology(project.id, tech)}
                              className="ml-1 rounded-full hover:bg-muted-foreground/20"
                            >
                              <X className="h-3 w-3" />
                            </button>
                          </Badge>
                        ))}
                      </div>
                      <div className="flex gap-2">
                        <Input
                          value={techInput[project.id] || ""}
                          onChange={(e) =>
                            setTechInput((prev) => ({
                              ...prev,
                              [project.id]: e.target.value,
                            }))
                          }
                          onKeyPress={(e) => handleTechKeyPress(e, project.id)}
                          placeholder="Add technology..."
                          className="flex-1"
                        />
                        <Button
                          variant="outline"
                          size="icon"
                          onClick={() => addTechnology(project.id)}
                          disabled={!techInput[project.id]?.trim()}
                        >
                          <Plus className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>

                    {/* Bullets */}
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label>Key Achievements / Highlights</Label>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleEnhanceBullets(project)}
                          disabled={
                            isEnhancingBullets ||
                            project.bullets.filter((b) => b.trim()).length === 0
                          }
                        >
                          {enhancingId === project.id ? (
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          ) : (
                            <Sparkles className="mr-2 h-4 w-4" />
                          )}
                          Enhance with AI
                        </Button>
                      </div>

                      <div className="space-y-2">
                        {project.bullets.map((bullet, bulletIdx) => (
                          <div key={bulletIdx}>
                            <div className="flex gap-2">
                              <span className="mt-2 text-muted-foreground">
                                •
                              </span>
                              <Input
                                value={bullet}
                                onChange={(e) =>
                                  updateBullet(
                                    project.id,
                                    bulletIdx,
                                    e.target.value
                                  )
                                }
                                placeholder="Describe achievement or highlight..."
                                className="flex-1"
                              />
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() =>
                                  removeBullet(project.id, bulletIdx)
                                }
                                disabled={project.bullets.length === 1}
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>

                            {/* Enhancement suggestion */}
                            {enhancements[project.id]?.find(
                              (e) => e.original === bullet
                            ) && (
                              <div className="ml-4 mt-2 rounded-md border border-primary/30 bg-primary/5 p-3">
                                <p className="mb-1 text-xs font-medium text-primary">
                                  AI Suggestion:
                                </p>
                                <p className="text-sm">
                                  {
                                    enhancements[project.id].find(
                                      (e) => e.original === bullet
                                    )?.enhanced
                                  }
                                </p>
                                <p className="mt-1 text-xs text-muted-foreground">
                                  {
                                    enhancements[project.id].find(
                                      (e) => e.original === bullet
                                    )?.explanation
                                  }
                                </p>
                                <div className="mt-2 flex gap-2">
                                  <Button
                                    size="sm"
                                    onClick={() =>
                                      acceptEnhancement(
                                        project.id,
                                        bullet,
                                        enhancements[project.id].find(
                                          (e) => e.original === bullet
                                        )!.enhanced
                                      )
                                    }
                                  >
                                    <Check className="mr-1 h-3 w-3" /> Accept
                                  </Button>
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() =>
                                      rejectEnhancement(project.id, bullet)
                                    }
                                  >
                                    <X className="mr-1 h-3 w-3" /> Reject
                                  </Button>
                                </div>
                              </div>
                            )}
                          </div>
                        ))}
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => addBullet(project.id)}
                          className="mt-1"
                        >
                          <Plus className="mr-1 h-3 w-3" /> Add Bullet
                        </Button>
                      </div>
                    </div>

                    {/* Delete */}
                    <div className="flex justify-end border-t pt-4">
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => removeProject(project.id)}
                      >
                        <Trash2 className="mr-2 h-4 w-4" /> Remove Project
                      </Button>
                    </div>
                  </div>
                </CollapsibleContent>
              </div>
            </Collapsible>
          ))
        )}
      </div>

      {/* Tips */}
      <div className="rounded-lg bg-muted/50 p-4">
        <h4 className="mb-2 text-sm font-medium">Tips for Projects</h4>
        <ul className="space-y-1 text-xs text-muted-foreground">
          <li>• Choose projects relevant to your target role</li>
          <li>• Highlight technical challenges you solved</li>
          <li>• Include measurable outcomes when possible</li>
          <li>• Link to live demos or repositories when available</li>
        </ul>
      </div>
    </div>
  );
}
