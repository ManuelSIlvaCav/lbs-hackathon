"use client";

import { RecommendationCard } from "@/components/recommendation-card";
import { RecommendationsHeader } from "@/components/recommendations-header";
import { RecommendationsList } from "@/components/recommendations-list";
import { useAuth } from "@/contexts/auth-context";
import { useRecommendations } from "@/hooks/use-recommendations";

export default function RecommendationsPage() {
  const { user } = useAuth();
  const candidateId = user?.candidate_id;

  const {
    recommendations,
    totalCount,
    isLoading,
    isError,
    error,
    isFetchingNextPage,
    hasNextPage,
    observerTarget,
    isUpdating,
    handleMarkAsViewed,
    handleMarkAsApplied,
    handleMarkAsRejected,
  } = useRecommendations({
    candidateId,
    enabled: !!candidateId,
  });

  return (
    <div className="flex h-full w-full flex-col">
      <RecommendationsHeader totalCount={totalCount} />

      <div className="flex-1 overflow-auto px-6 py-6">
        <RecommendationsList
          recommendations={recommendations}
          isLoading={isLoading}
          isError={isError}
          error={error}
          isFetchingNextPage={isFetchingNextPage}
          hasNextPage={hasNextPage}
          observerTargetRef={observerTarget}
        >
          {recommendations.map((recommendation) => (
            <RecommendationCard
              key={recommendation._id}
              recommendation={recommendation}
              onMarkAsViewed={handleMarkAsViewed}
              onMarkAsApplied={handleMarkAsApplied}
              onMarkAsRejected={handleMarkAsRejected}
              isUpdating={isUpdating}
            />
          ))}
        </RecommendationsList>
      </div>
    </div>
  );
}
