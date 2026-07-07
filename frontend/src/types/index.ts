export type UserRole = 'owner' | 'manager' | 'employee';

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  agency_id: number;
  totp_enabled: boolean;
  is_active: boolean;
  last_login_at?: string;
}

export interface Agency {
  id: number;
  name: string;
  slug: string;
  domain?: string;
  logo_url?: string;
  is_active: boolean;
  settings?: string;
}

export interface Workspace {
  id: number;
  name: string;
  description?: string;
  is_active: boolean;
  created_at: string;
}

export type TenderStatus =
  | 'identified'
  | 'qualification'
  | 'in_progress'
  | 'internal_review'
  | 'submitted'
  | 'won'
  | 'lost'
  | 'withdrawn';

export interface Tender {
  id: number;
  client_workspace_id: number;
  title: string;
  reference_number?: string;
  description?: string;
  status: TenderStatus;
  bid_deadline?: string;
  estimated_value?: number;
  currency: string;
  assigned_to?: number;
  created_by: number;
  ai_readiness_score?: number;
  ai_go_nogo_recommendation?: string;
  ai_go_nogo_explanation?: string;
  created_at: string;
  updated_at: string;
}

export type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'blocked';
export type TaskPriority = 'low' | 'medium' | 'high' | 'urgent';

export interface Task {
  id: number;
  tender_id: number;
  title: string;
  description?: string;
  status: TaskStatus;
  priority: TaskPriority;
  assigned_to?: number;
  assigned_by?: number;
  due_date?: string;
  completed_at?: string;
  created_at: string;
}
