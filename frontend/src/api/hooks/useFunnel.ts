/**
 * React Query hook for GET /stores/{id}/funnel.
 * Auto-refreshes every 30 seconds.
 */

import { useQuery } from "@tanstack/react-query";
import client from "../client";
import type { FunnelResponse } from "../../types/events";

export function useFunnel(storeId: string | null) {
  return useQuery<FunnelResponse>({
    queryKey: ["funnel", storeId],
    queryFn: async () => {
      const { data } = await client.get<FunnelResponse>(
        `/stores/${storeId}/funnel`
      );
      return data;
    },
    enabled: !!storeId,
    refetchInterval: 30_000,
  });
}
