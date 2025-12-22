"use client";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { useCVBuilder } from "@/contexts/cv-builder-context";
import { FileText, Loader2, Plus } from "lucide-react";
import { useState } from "react";

export function CVSelector() {
  const {
    cvList,
    isLoadingList,
    currentCV,
    setCurrentCVId,
    createCV,
    isCreating,
  } = useCVBuilder();

  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [newCVName, setNewCVName] = useState("");
  const [fromParsedCV, setFromParsedCV] = useState(true);

  const handleCreate = async () => {
    if (!newCVName.trim()) return;
    await createCV({ name: newCVName, from_parsed_cv: fromParsedCV });
    setIsDialogOpen(false);
    setNewCVName("");
    setFromParsedCV(true);
  };

  return (
    <div className="flex items-center gap-2">
      {isLoadingList ? (
        <div className="flex h-9 w-48 items-center justify-center rounded-md border">
          <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <Select
          value={currentCV?._id || ""}
          onValueChange={(value) => setCurrentCVId(value)}
        >
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Select a CV">
              {currentCV && (
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  <span className="truncate">{currentCV.name}</span>
                </div>
              )}
            </SelectValue>
          </SelectTrigger>
          <SelectContent>
            {cvList.length === 0 ? (
              <div className="py-6 text-center text-sm text-muted-foreground">
                No CVs created yet
              </div>
            ) : (
              cvList.map((cv) => (
                <SelectItem key={cv._id} value={cv._id || ""}>
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4" />
                    <span>{cv.name}</span>
                  </div>
                </SelectItem>
              ))
            )}
          </SelectContent>
        </Select>
      )}

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogTrigger asChild>
          <Button variant="outline" size="icon">
            <Plus className="h-4 w-4" />
          </Button>
        </DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New CV</DialogTitle>
            <DialogDescription>
              Start a new CV from scratch or pre-fill with your profile
              information.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="cv-name">CV Name</Label>
              <Input
                id="cv-name"
                value={newCVName}
                onChange={(e) => setNewCVName(e.target.value)}
                placeholder="e.g., Software Engineer CV"
              />
            </div>
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="from-parsed">Pre-fill from Profile</Label>
                <p className="text-xs text-muted-foreground">
                  Use your existing profile information as a starting point
                </p>
              </div>
              <Switch
                id="from-parsed"
                checked={fromParsedCV}
                onCheckedChange={setFromParsedCV}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleCreate}
              disabled={!newCVName.trim() || isCreating}
            >
              {isCreating ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating...
                </>
              ) : (
                "Create CV"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
