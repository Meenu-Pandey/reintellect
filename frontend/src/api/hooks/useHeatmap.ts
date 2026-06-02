/**
 * React Query hook for GET /stores/{id}/heatmap.
 * Accepts a timeWindow parameter for filtering.
 */

import { useQuery } from "@tanstack/react-query";
import client from "../client";
import type { HeatmapResponse } from "../../types/events";

export function useHeatmap(
  storeId: string | null,
  timeWindow?: { start: string; end: string }
) {
  return useQuery<HeatmapResponse>({
    queryKey: ["heatmap", storeId, timeWindow],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (timeWindow) {
        params.start = timeWindow.start;
        params.end = timeWindow.end;
      }
      const { data } = await client.get<HeatmapResponse>(
        `/stores/${storeId}/heatmap`,
        { params }
      );
      return data;
    },
    enabled: !!storeId,
  });
}
