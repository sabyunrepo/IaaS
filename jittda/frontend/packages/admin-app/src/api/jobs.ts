import { BaseAPI } from '../lib/api';
import type { AnalysisResult } from '../types/result';

interface Job {
  id: string;
  status: string;
  progress: number;
}

interface JobDetail extends Job {
  input_data: Record<string, unknown> | null;
  result_data: Record<string, unknown> | null;
  error_message: string | null;
}

export class JobsAPI extends BaseAPI {
  static list(): Promise<Job[]> {
    return this.get<Job[]>('/api/jobs');
  }

  static getById(jobId: string): Promise<JobDetail> {
    return this.get<JobDetail>(`/api/jobs/${jobId}`);
  }

  static getResult(jobId: string): Promise<AnalysisResult> {
    return this.get<AnalysisResult>(`/api/jobs/${jobId}/result`);
  }
}
