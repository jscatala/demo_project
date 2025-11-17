import { useState, useEffect, useCallback } from 'react';
import { getResults } from '../services/api';
import type { ResultsResponse, ApiError } from '../types/api';

interface UseResultsResult {
  data: ResultsResponse | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export const useResults = (): UseResultsResult => {
  const [data, setData] = useState<ResultsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchResults = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const results = await getResults();
      setData(results);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.message || 'Failed to fetch results');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchResults();
  }, [fetchResults]);

  return {
    data,
    isLoading,
    error,
    refetch: fetchResults,
  };
};
