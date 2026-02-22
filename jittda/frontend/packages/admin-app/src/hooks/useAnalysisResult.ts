import { useQuery } from '@tanstack/react-query';
import { JobsAPI } from '../api/jobs';
import type { AnalysisResult } from '../types/result';

export function useAnalysisResult(jobId: string) {
  return useQuery<AnalysisResult>({
    queryKey: ['analysisResult', jobId],
    queryFn: () => JobsAPI.getResult(jobId),
    enabled: !!jobId,
  });
}
