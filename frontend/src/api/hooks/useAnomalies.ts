/**
 * React Query hook for GET /stores/{id}/anomalies.
 * Auto-refreshes every 60 seconds.
 */

import { useQuery } from "@tanstack/react-query";
import client from "../client";
import type { AnomaliesResponse } from "../../types/events";

export function useAnomalies(storeId: string | null) {
  return useQuery<AnomaliesResponse>({
    queryKey: ["anomalies", storeId],
    queryFn: async () => {
      const { data } = await client.get<AnomaliesResponse>(
        `/stores/${storeId}/anomalies`
      );
      return data;
    },
    enabled: !!storeId,
    refetchInterval: 60_000,
  });
}
