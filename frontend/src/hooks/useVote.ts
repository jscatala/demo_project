import { useState, useCallback } from 'react';
import { postVote } from '../services/api';
import type { ApiError } from '../types/api';

interface UseVoteResult {
  vote: (option: 'cats' | 'dogs') => Promise<void>;
  isLoading: boolean;
  error: string | null;
  clearError: () => void;
}

export const useVote = (onSuccess?: () => void): UseVoteResult => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const vote = useCallback(async (option: 'cats' | 'dogs') => {
    setIsLoading(true);
    setError(null);

    try {
      await postVote(option);
      if (onSuccess) {
        onSuccess();
      }
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.message || 'Failed to submit vote');
    } finally {
      setIsLoading(false);
    }
  }, [onSuccess]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return { vote, isLoading, error, clearError };
};
