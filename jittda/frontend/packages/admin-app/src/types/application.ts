export interface Application {
  id: string;
  posting_id: string;
  candidate_name: string | null;
  candidate_email: string | null;
  github_username: string | null;
  github_urls: string[];
  linkedin_url: string | null;
  resume_path: string | null;
  cover_letter_path: string | null;
  portfolio_path: string | null;
  memo: string | null;
  source: 'self_apply' | 'admin_manual';
  status: 'pending' | 'analyzing' | 'completed' | 'failed';
  job_id: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface ApplicationCreateInput {
  candidate_name?: string;
  candidate_email?: string;
  github_username?: string;
  github_urls?: string[];
  linkedin_url?: string;
  resume_path?: string;
  cover_letter_path?: string;
  portfolio_path?: string;
  memo?: string;
}

export type ApplicationUpdateInput = Partial<ApplicationCreateInput> & {
  status?: string;
};

export interface AnalyzeResponse {
  job_id: string;
  status: string;
}

export interface FileUploadResponse {
  id: string;
  file_path: string;
  file_name: string;
}
