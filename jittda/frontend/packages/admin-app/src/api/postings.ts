import { BaseAPI } from '../lib/api';
import type { Posting, PostingCreateInput, PostingUpdateInput } from '../types/posting';

export class PostingsAPI extends BaseAPI {
  static list(status?: string): Promise<Posting[]> {
    const params = status ? `?status=${status}` : '';
    return this.get<Posting[]>(`/api/postings${params}`);
  }

  static getById(id: string): Promise<Posting> {
    return this.get<Posting>(`/api/postings/${id}`);
  }

  static create(input: PostingCreateInput): Promise<Posting> {
    return this.post<Posting>('/api/postings', input);
  }

  static update(id: string, input: PostingUpdateInput): Promise<Posting> {
    return this.put<Posting>(`/api/postings/${id}`, input);
  }

  static remove(id: string): Promise<void> {
    return this.delete(`/api/postings/${id}`);
  }
}
