import { BaseAPI } from '../lib/api';
import type {
  Application,
  ApplicationCreateInput,
  ApplicationUpdateInput,
  AnalyzeResponse,
  FileUploadResponse,
} from '../types/application';
import type { AnalysisResult } from '../types/result';

export class ApplicationsAPI extends BaseAPI {
  static list(postingId: string, status?: string): Promise<Application[]> {
    const params = status ? `?status=${status}` : '';
    return this.get<Application[]>(
      `/api/postings/${postingId}/applications${params}`,
    );
  }

  static getById(postingId: string, appId: string): Promise<Application> {
    return this.get<Application>(
      `/api/postings/${postingId}/applications/${appId}`,
    );
  }

  static create(
    postingId: string,
    input: ApplicationCreateInput,
  ): Promise<Application> {
    return this.post<Application>(
      `/api/postings/${postingId}/applications`,
      input,
    );
  }

  static update(
    postingId: string,
    appId: string,
    input: ApplicationUpdateInput,
  ): Promise<Application> {
    return this.put<Application>(
      `/api/postings/${postingId}/applications/${appId}`,
      input,
    );
  }

  static remove(postingId: string, appId: string): Promise<void> {
    return this.delete(`/api/postings/${postingId}/applications/${appId}`);
  }

  static analyze(
    postingId: string,
    appId: string,
  ): Promise<AnalyzeResponse> {
    return this.post<AnalyzeResponse>(
      `/api/postings/${postingId}/applications/${appId}/analyze`,
    );
  }

  static getResult(
    postingId: string,
    appId: string,
  ): Promise<AnalysisResult> {
    return this.get<AnalysisResult>(
      `/api/postings/${postingId}/applications/${appId}/result`,
    );
  }

  static uploadFile(
    fileType: 'resume' | 'cover_letter' | 'portfolio',
    file: File,
  ): Promise<FileUploadResponse> {
    return this.upload<FileUploadResponse>(`/api/uploads/${fileType}`, file);
  }
}
