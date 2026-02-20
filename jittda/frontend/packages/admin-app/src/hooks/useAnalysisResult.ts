import { useCallback, useEffect, useState } from 'react';
import { API_BASE } from '../lib/api';
import type { AnalysisResult } from '../types/result';

// ---------------------------------------------------------------------------
// Hook state
// ---------------------------------------------------------------------------

export interface UseAnalysisResultState {
  data: AnalysisResult | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => void;
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

/**
 * Fetches the analysis result for a given job from the backend API.
 *
 * Endpoint: GET /api/jobs/{jobId}/result
 *
 * Uses native `fetch` — no tanstack-query dependency required.
 */
export function useAnalysisResult(jobId: string): UseAnalysisResultState {
  const [data, setData] = useState<AnalysisResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchResult = useCallback(async () => {
    if (!jobId) {
      setError('Job ID가 제공되지 않았습니다.');
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/api/jobs/${jobId}/result`);

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('분석 결과를 찾을 수 없습니다.');
        }
        throw new Error(`API 오류: ${response.status} ${response.statusText}`);
      }

      const result: AnalysisResult = await response.json();
      setData(result);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다.';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, [jobId]);

  useEffect(() => {
    fetchResult();
  }, [fetchResult]);

  return { data, isLoading, error, refetch: fetchResult };
}
