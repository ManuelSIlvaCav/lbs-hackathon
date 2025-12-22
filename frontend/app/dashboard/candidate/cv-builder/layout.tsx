import { CandidateProvider } from "@/contexts/candidate-context";
import { CVBuilderProvider } from "@/contexts/cv-builder-context";
import { ReactNode } from "react";

export default function CVBuilderLayout({ children }: { children: ReactNode }) {
  return (
    <CandidateProvider>
      <CVBuilderProvider>{children}</CVBuilderProvider>
    </CandidateProvider>
  );
}
