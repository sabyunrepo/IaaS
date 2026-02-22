import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { PostingsAPI } from '../api/postings';
import type { PostingCreateInput, PostingUpdateInput } from '../types/posting';

const POSTINGS_KEY = ['postings'] as const;

export function usePostings(status?: string) {
  return useQuery({
    queryKey: [...POSTINGS_KEY, { status }],
    queryFn: () => PostingsAPI.list(status),
  });
}

export function usePosting(id: string) {
  return useQuery({
    queryKey: [...POSTINGS_KEY, id],
    queryFn: () => PostingsAPI.getById(id),
    enabled: !!id,
  });
}

export function useCreatePosting() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: PostingCreateInput) => PostingsAPI.create(input),
    onSuccess: () => qc.invalidateQueries({ queryKey: POSTINGS_KEY }),
  });
}

export function useUpdatePosting(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: PostingUpdateInput) => PostingsAPI.update(id, input),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: POSTINGS_KEY });
      qc.invalidateQueries({ queryKey: [...POSTINGS_KEY, id] });
    },
  });
}

export function useDeletePosting() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => PostingsAPI.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: POSTINGS_KEY }),
  });
}
