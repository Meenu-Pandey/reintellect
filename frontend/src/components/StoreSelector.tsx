/**
 * Store selector dropdown.
 * Fetches store list from the backend and allows selection.
 */

import { useEffect, useState } from "react";
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
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    client
      .get<{ stores: Store[] } | Store[]>("/stores")
      .then((res) => {
        const data = res.data;
        // Handle both array and object response shapes
        const list = Array.isArray(data) ? data : (data as { stores: Store[] }).stores || [];
        setStores(list);
        // Auto-select first store if nothing selected
        if (!selectedStoreId && list.length > 0) {
          onSelect(list[0].store_id);
        }
      })
      .catch(() => {
        // If endpoint doesn't exist yet, provide a default
        const fallback: Store[] = [
          { store_id: "purplle-brigade-road", name: "Purplle Brigade Road" },
        ];
        setStores(fallback);
        if (!selectedStoreId) {
          onSelect(fallback[0].store_id);
        }
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <span>Loading stores...</span>;
  }

  return (
    <select
      value={selectedStoreId || ""}
      onChange={(e) => onSelect(e.target.value)}
      aria-label="Select store"
    >
      <option value="" disabled>
        Select a store
      </option>
      {stores.map((s) => (
        <option key={s.store_id} value={s.store_id}>
          {s.name}
        </option>
      ))}
    </select>
  );
}
