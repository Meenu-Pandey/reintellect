/**
 * Store selector dropdown — dark themed.
 */

import { useEffect, useState } from "react";
import { theme } from "../styles/theme";
import client from "../api/client";

interface Store {
  store_id: string;
  name: string;
}

interface Props {
  selectedStoreId: string | null;
  onSelect: (storeId: string) => void;
}

export function StoreSelector({ selectedStoreId, onSelect }: Props) {
  const [stores, setStores] = useState<Store[]>([]);

  useEffect(() => {
    client
      .get("/stores")
      .then((res) => {
        const data = res.data;
        const list = Array.isArray(data) ? data : data?.stores || [];
        setStores(list);
        if (!selectedStoreId && list.length > 0) onSelect(list[0].store_id);
      })
      .catch(() => {
        const fallback = [{ store_id: "purplle-brigade-road", name: "Purplle Brigade Road" }];
        setStores(fallback);
        if (!selectedStoreId) onSelect(fallback[0].store_id);
      });
  }, []);

  return (
    <select
      value={selectedStoreId || ""}
      onChange={(e) => onSelect(e.target.value)}
      aria-label="Select store"
      style={{
        padding: "0.4rem 0.75rem",
        background: theme.bg.elevated,
        border: `1px solid ${theme.border}`,
        borderRadius: theme.radiusSm,
        color: theme.text.primary,
        fontSize: "0.78rem",
        cursor: "pointer",
        outline: "none",
      }}
    >
      <option value="" disabled>Select store</option>
      {stores.map((s) => (
        <option key={s.store_id} value={s.store_id}>{s.name}</option>
      ))}
    </select>
  );
}
