import { CandidateProvider } from "@/contexts/candidate-context";
import { ReactNode } from "react";

export default function CandidateLayout({ children }: { children: ReactNode }) {
  return <CandidateProvider>{children}</CandidateProvider>;
}
