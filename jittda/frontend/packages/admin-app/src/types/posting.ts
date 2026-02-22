export interface Posting {
  id: string;
  user_id: string;
  title: string;
  department: string | null;
  jd_description: string | null;
  jd_languages: string[];
  jd_tech_stack: string[];
  jd_experience_years: number | null;
  auto_analyze: boolean;
  status: 'draft' | 'active' | 'closed';
  application_count: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface PostingCreateInput {
  title: string;
  department?: string;
  jd_description?: string;
  jd_languages?: string[];
  jd_tech_stack?: string[];
  jd_experience_years?: number;
  auto_analyze?: boolean;
  status?: 'draft' | 'active' | 'closed';
}

export type PostingUpdateInput = Partial<PostingCreateInput>;
