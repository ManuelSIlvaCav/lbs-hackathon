import { Loader2 } from "lucide-react";

interface RecommendationsListProps {
  recommendations: any[];
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
  isFetchingNextPage: boolean;
  hasNextPage: boolean;
  observerTargetRef: React.RefObject<HTMLDivElement | null>;
  children: React.ReactNode;
}

export function RecommendationsList({
  recommendations,
  isLoading,
  isError,
  error,
  isFetchingNextPage,
  hasNextPage,
  observerTargetRef,
  children,
}: RecommendationsListProps) {
  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center space-y-2">
          <Loader2 className="h-8 w-8 animate-spin mx-auto text-muted-foreground" />
          <p className="text-muted-foreground font-inter">
            Loading recommendations...
          </p>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center space-y-2">
          <p className="text-destructive">Error loading recommendations</p>
          <p className="text-sm text-muted-foreground font-inter">
            {error instanceof Error ? error.message : "Unknown error"}
          </p>
        </div>
      </div>
    );
  }

  if (recommendations.length === 0) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center space-y-2">
          <p className="text-muted-foreground font-inter">
            No recommendations yet
          </p>
          <p className="text-sm text-muted-foreground font-inter">
            Check back later for personalized job recommendations
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Recommendations Grid */}
      <div className="grid gap-4">{children}</div>

      {/* Loading More Indicator */}
      {isFetchingNextPage && (
        <div className="flex items-center justify-center py-6">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          <span className="ml-2 text-muted-foreground font-inter">
            Loading more...
          </span>
        </div>
      )}

      {/* Intersection Observer Target */}
      <div ref={observerTargetRef} className="h-4" />

      {/* End of Results */}
      {!hasNextPage && recommendations.length > 0 && (
        <div className="text-center py-6">
          <p className="text-sm text-muted-foreground font-inter">
            No more recommendations
          </p>
        </div>
      )}
    </div>
  );
}
