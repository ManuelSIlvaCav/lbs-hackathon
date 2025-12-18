import { SidebarTrigger } from "@/components/ui/sidebar";

interface RecommendationsHeaderProps {
  totalCount: number;
}

export function RecommendationsHeader({
  totalCount,
}: RecommendationsHeaderProps) {
  return (
    <header className="flex items-center justify-between border-b bg-background px-6 py-8">
      <div className="flex items-center gap-4">
        <SidebarTrigger />
        <div>
          <h1 className="text-3xl font-semibold font-sora">
            Job Recommendations
          </h1>
          <p className="mt-1 text-sm text-muted-foreground font-inter">
            {totalCount > 0 &&
              `${totalCount} recommendation${
                totalCount !== 1 ? "s" : ""
              } for you`}
          </p>
        </div>
      </div>
    </header>
  );
}
