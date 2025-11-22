"use client";

import { FileUpload } from "@/components/file-upload";
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
import { candidateApi } from "@/lib/api/candidate";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Loader2, Plus } from "lucide-react";
import * as React from "react";
import { toast } from "sonner";

interface UploadResumeDialogProps {
  candidateId: string;
}

export function UploadResumeDialog({ candidateId }: UploadResumeDialogProps) {
  const [open, setOpen] = React.useState(false);
  const [resumeName, setResumeName] = React.useState("");
  const [selectedFile, setSelectedFile] = React.useState<File | null>(null);
  const queryClient = useQueryClient();

  // Upload and parse CV mutation
  const uploadMutation = useMutation({
    mutationFn: (file: File) =>
      candidateApi.uploadAndParseCV(candidateId, file),
    onSuccess: async (updatedCandidate) => {
      // Update the query cache with the new candidate data
      queryClient.setQueryData(["candidate", candidateId], updatedCandidate);

      // Also invalidate to ensure a fresh fetch
      await queryClient.invalidateQueries({
        queryKey: ["candidate", candidateId],
      });

      toast.success("CV uploaded and parsed successfully!");
      // Close dialog and reset form
      handleClose();
    },
    onError: (error: Error) => {
      toast.error(`Failed to upload CV: ${error.message}`);
    },
  });

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    // Auto-fill resume name from filename if empty
    if (!resumeName) {
      const nameWithoutExtension = file.name.replace(/\.[^/.]+$/, "");
      setResumeName(nameWithoutExtension);
    }
  };

  const handleUpload = () => {
    if (!selectedFile || !resumeName) {
      return;
    }

    // Upload and parse the CV
    uploadMutation.mutate(selectedFile);
  };

  const handleClose = () => {
    setOpen(false);
    setResumeName("");
    setSelectedFile(null);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="lg" className="rounded-full">
          <Plus className="h-5 w-5" />
          New Resume
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Upload Resume</DialogTitle>
          <DialogDescription>
            Upload your resume file and give it a name to help you identify it
            later.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Resume Name Input */}
          <div className="space-y-2">
            <label htmlFor="resume-name" className="text-sm font-medium">
              Resume Name
            </label>
            <Input
              id="resume-name"
              placeholder="e.g., Senior Product Manager Resume"
              value={resumeName}
              onChange={(e) => setResumeName(e.target.value)}
              disabled={uploadMutation.isPending}
            />
          </div>

          {/* File Upload */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Resume File</label>
            <FileUpload
              onFileSelect={handleFileSelect}
              accept=".pdf,.doc,.docx"
              maxSize={10}
            />
            {selectedFile && (
              <p className="text-sm text-muted-foreground">
                Selected: {selectedFile.name}
              </p>
            )}
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={handleClose}
            disabled={uploadMutation.isPending}
          >
            Cancel
          </Button>
          <Button
            onClick={handleUpload}
            disabled={
              !selectedFile || !resumeName.trim() || uploadMutation.isPending
            }
          >
            {uploadMutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Uploading & Parsing...
              </>
            ) : (
              "Upload Resume"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
