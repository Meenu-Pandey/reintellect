/**
 * React Query hook for GET /stores/{id}/metrics.
 */

import { useQuery } from "@tanstack/react-query";
import client from "../client";
import type { StoreMetrics } from "../../types/events";

export function useMetrics(storeId: string | null) {
  return useQuery<StoreMetrics>({
    queryKey: ["metrics", storeId],
    queryFn: async () => {
      const { data } = await client.get<StoreMetrics>(
        `/stores/${storeId}/metrics`
      );
      return data;
    },
    enabled: !!storeId,
  });
}
