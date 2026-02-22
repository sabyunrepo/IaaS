import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ApplicationsAPI } from '../api/applications';
import type {
  ApplicationCreateInput,
  ApplicationUpdateInput,
} from '../types/application';

const APPS_KEY = ['applications'] as const;

export function useApplications(postingId: string, status?: string) {
  return useQuery({
    queryKey: [...APPS_KEY, postingId, { status }],
    queryFn: () => ApplicationsAPI.list(postingId, status),
    enabled: !!postingId,
  });
}

export function useApplication(postingId: string, appId: string) {
  return useQuery({
    queryKey: [...APPS_KEY, postingId, appId],
    queryFn: () => ApplicationsAPI.getById(postingId, appId),
    enabled: !!postingId && !!appId,
  });
}

export function useCreateApplication(postingId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: ApplicationCreateInput) =>
      ApplicationsAPI.create(postingId, input),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: [...APPS_KEY, postingId] }),
  });
}

export function useUpdateApplication(postingId: string, appId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: ApplicationUpdateInput) =>
      ApplicationsAPI.update(postingId, appId, input),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [...APPS_KEY, postingId] });
      qc.invalidateQueries({ queryKey: [...APPS_KEY, postingId, appId] });
    },
  });
}

export function useDeleteApplication(postingId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (appId: string) => ApplicationsAPI.remove(postingId, appId),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: [...APPS_KEY, postingId] }),
  });
}

export function useAnalyzeApplication(postingId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (appId: string) => ApplicationsAPI.analyze(postingId, appId),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: [...APPS_KEY, postingId] }),
  });
}

export function useApplicationResult(postingId: string, appId: string) {
  return useQuery({
    queryKey: [...APPS_KEY, postingId, appId, 'result'],
    queryFn: () => ApplicationsAPI.getResult(postingId, appId),
    enabled: !!postingId && !!appId,
  });
}
