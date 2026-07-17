"use client";

import { useState, useEffect, useCallback } from "react";
import { showToast } from "@/components/ui/toast";

interface UseApiOptions<T> {
  /** Function that performs the API call */
  fetcher: () => Promise<T>;
  /** Whether to run the fetcher immediately on mount */
  immediate?: boolean;
  /** Callback when fetch succeeds */
  onSuccess?: (data: T) => void;
  /** Error message to show in toast */
  errorMessage?: string;
}

interface UseApiResult<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

/**
 * Custom hook for API calls with loading/error state management.
 * Shows toast notifications on error and provides refetch capability.
 */
export function useApi<T>({
  fetcher,
  immediate = true,
  onSuccess,
  errorMessage = "Failed to load data",
}: UseApiOptions<T>): UseApiResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(immediate);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetcher();
      setData(result);
      onSuccess?.(result);
    } catch (err) {
      const message = err instanceof Error ? err.message : errorMessage;
      setError(message);
      showToast(message, "error");
    } finally {
      setLoading(false);
    }
  }, [fetcher, onSuccess, errorMessage]);

  useEffect(() => {
    if (immediate) {
      refetch();
    }
    // Only run on mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return { data, loading, error, refetch };
}
