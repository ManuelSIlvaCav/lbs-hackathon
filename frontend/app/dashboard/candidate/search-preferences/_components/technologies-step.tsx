"use client";

import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useEffect, useRef, useState } from "react";

interface TechnologiesStepProps {
  data: any;
  onChange: (data: any) => void;
}

const TECHNOLOGIES = [
  "React",
  "TypeScript",
  "Node.js",
  "Python",
  "Java",
  "Go",
  "Rust",
  "C++",
  "Swift",
  "Kotlin",
  "AWS",
  "Azure",
  "GCP",
  "Docker",
  "Kubernetes",
  "PostgreSQL",
  "MongoDB",
  "Redis",
  "GraphQL",
  "REST APIs",
  "Machine Learning",
  "TensorFlow",
  "PyTorch",
  "Next.js",
  "Vue.js",
  "Angular",
  "Django",
  "FastAPI",
  "Flask",
  "Spring Boot",
];

export function TechnologiesStep({ data, onChange }: TechnologiesStepProps) {
  const onChangeRef = useRef(onChange);
  onChangeRef.current = onChange;

  const [favouriteTechnologies, setFavouriteTechnologies] = useState<string[]>(
    data.favourite_technologies || []
  );
  const [hiddenTechnologies, setHiddenTechnologies] = useState<string[]>(
    data.hidden_technologies || []
  );
  const [customTechnology, setCustomTechnology] = useState("");

  useEffect(() => {
    onChangeRef.current({
      favourite_technologies: favouriteTechnologies,
      hidden_technologies: hiddenTechnologies,
    });
  }, [favouriteTechnologies, hiddenTechnologies]);

  const toggleFavourite = (tech: string) => {
    if (favouriteTechnologies.includes(tech)) {
      setFavouriteTechnologies(favouriteTechnologies.filter((t) => t !== tech));
    } else {
      setFavouriteTechnologies([...favouriteTechnologies, tech]);
      // Remove from hidden if it was there
      setHiddenTechnologies(hiddenTechnologies.filter((t) => t !== tech));
    }
  };

  const toggleHidden = (tech: string) => {
    if (hiddenTechnologies.includes(tech)) {
      setHiddenTechnologies(hiddenTechnologies.filter((t) => t !== tech));
    } else {
      setHiddenTechnologies([...hiddenTechnologies, tech]);
      // Remove from favourite if it was there
      setFavouriteTechnologies(favouriteTechnologies.filter((t) => t !== tech));
    }
  };

  const addCustomTechnology = () => {
    if (
      customTechnology.trim() &&
      !TECHNOLOGIES.includes(customTechnology.trim())
    ) {
      setFavouriteTechnologies([
        ...favouriteTechnologies,
        customTechnology.trim(),
      ]);
      setCustomTechnology("");
    }
  };

  return (
    <div className="space-y-8">
      {/* Favourite Technologies */}
      <div>
        <h2 className="text-2xl font-semibold mb-2 font-sora">
          Favourite technologies
        </h2>
        <p className="text-muted-foreground mb-6 font-inter">
          Select technologies and skills you want to work with
        </p>

        <div className="grid grid-cols-3 gap-3">
          {TECHNOLOGIES.map((tech) => {
            const isFavourite = favouriteTechnologies.includes(tech);
            const isHidden = hiddenTechnologies.includes(tech);

            return (
              <Label
                key={tech}
                htmlFor={`tech-${tech}`}
                className={`flex items-center space-x-3 p-4 rounded-lg cursor-pointer transition-colors ${
                  isFavourite
                    ? "bg-green-200 hover:bg-green-300"
                    : isHidden
                    ? "bg-red-100 hover:bg-red-200"
                    : "bg-muted/50 hover:bg-muted"
                }`}
              >
                <Checkbox
                  id={`tech-${tech}`}
                  checked={isFavourite}
                  onCheckedChange={() => toggleFavourite(tech)}
                  className={
                    isFavourite
                      ? "border-green-600 data-[state=checked]:bg-green-600"
                      : ""
                  }
                />
                <span className="flex-1 text-sm font-medium font-inter">
                  {tech}
                </span>
              </Label>
            );
          })}
        </div>

        {/* Add custom technology */}
        <div className="mt-4">
          <div className="flex gap-2">
            <Input
              placeholder="Add custom technology..."
              value={customTechnology}
              onChange={(e) => setCustomTechnology(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  addCustomTechnology();
                }
              }}
            />
            <button
              type="button"
              onClick={addCustomTechnology}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 whitespace-nowrap"
            >
              Add Technology
            </button>
          </div>
        </div>
      </div>

      {/* Hidden Technologies */}
      <div className="border-t pt-6">
        <h2 className="text-2xl font-semibold mb-2 font-sora">
          Hidden technologies
        </h2>
        <p className="text-muted-foreground mb-6 font-inter">
          Select technologies you want to avoid working with
        </p>

        <div className="grid grid-cols-3 gap-3">
          {TECHNOLOGIES.filter(
            (tech) => !favouriteTechnologies.includes(tech)
          ).map((tech) => {
            const isHidden = hiddenTechnologies.includes(tech);

            return (
              <Label
                key={tech}
                htmlFor={`hidden-tech-${tech}`}
                className={`flex items-center space-x-3 p-4 rounded-lg cursor-pointer transition-colors ${
                  isHidden
                    ? "bg-red-100 hover:bg-red-200"
                    : "bg-muted/50 hover:bg-muted"
                }`}
              >
                <Checkbox
                  id={`hidden-tech-${tech}`}
                  checked={isHidden}
                  onCheckedChange={() => toggleHidden(tech)}
                  className={
                    isHidden
                      ? "border-red-500 data-[state=checked]:bg-red-500"
                      : ""
                  }
                />
                <span className="flex-1 text-sm font-medium font-inter">
                  {tech}
                </span>
              </Label>
            );
          })}
        </div>
      </div>
    </div>
  );
}
