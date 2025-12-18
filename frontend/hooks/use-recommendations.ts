import { Recommendation, recommendationApi } from "@/lib/api/recommendation";
import {
    useInfiniteQuery,
    useMutation,
    useQueryClient,
} from "@tanstack/react-query";
import { useEffect, useRef } from "react";
import { toast } from "sonner";

interface UseRecommendationsParams {
  candidateId: string | undefined;
  enabled?: boolean;
}

export function useRecommendations({
  candidateId,
  enabled = true,
}: UseRecommendationsParams) {
  const queryClient = useQueryClient();
  const observerTarget = useRef<HTMLDivElement>(null);

  // Infinite query for recommendations
  const {
    data,
    isLoading,
    isError,
    error,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery({
    queryKey: ["recommendations", candidateId],
    queryFn: ({ pageParam = 0 }) =>
      recommendationApi.getRecommendations({
        candidate_id: candidateId,
        skip: pageParam,
        limit: 20,
      }),
    getNextPageParam: (lastPage) => {
      return lastPage.has_more ? lastPage.skip + lastPage.limit : undefined;
    },
    initialPageParam: 0,
    enabled: enabled && !!candidateId,
  });

  // Mutation for updating recommendation status
  const updateStatusMutation = useMutation({
    mutationFn: ({
      id,
      status,
    }: {
      id: string;
      status: "viewed" | "applied" | "rejected";
    }) => recommendationApi.updateRecommendationStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["recommendations"] });
      toast.success("Recommendation status updated");
    },
    onError: (error) => {
      toast.error(`Failed to update status: ${error.message}`);
    },
  });

  // Setup intersection observer for infinite scroll
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasNextPage && !isFetchingNextPage) {
          fetchNextPage();
        }
      },
      { threshold: 0.1 }
    );

    const currentTarget = observerTarget.current;
    if (currentTarget) {
      observer.observe(currentTarget);
    }

    return () => {
      if (currentTarget) {
        observer.unobserve(currentTarget);
      }
    };
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

  // Flatten all pages into single array
  const allRecommendations = data?.pages.flatMap((page) => page.items) ?? [];
  const totalCount = data?.pages[0]?.total ?? 0;

  // Action handlers
  const handleMarkAsViewed = (recommendation: Recommendation) => {
    if (
      recommendation.recommendation_status === "pending" ||
      recommendation.recommendation_status === "recommended"
    ) {
      updateStatusMutation.mutate({ id: recommendation._id, status: "viewed" });
    }
  };

  const handleMarkAsApplied = (recommendation: Recommendation) => {
    updateStatusMutation.mutate({ id: recommendation._id, status: "applied" });
  };

  const handleMarkAsRejected = (recommendation: Recommendation) => {
    updateStatusMutation.mutate({
      id: recommendation._id,
      status: "rejected",
    });
  };

  return {
    recommendations: allRecommendations,
    totalCount,
    isLoading,
    isError,
    error,
    isFetchingNextPage,
    hasNextPage,
    observerTarget,
    isUpdating: updateStatusMutation.isPending,
    handleMarkAsViewed,
    handleMarkAsApplied,
    handleMarkAsRejected,
  };
}
