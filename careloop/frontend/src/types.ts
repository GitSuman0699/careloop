export interface CaseSummary {
  id: string;
  patient_id: string;
  patient_name: string;
  pathway_id: string;
  urgency_tier: string;
  current_state: string;
  owner_id: string | null;
  owner_name: string;
  opened_at: string;
  closed_at: string | null;
}

export interface CaseDetail extends CaseSummary {
  patient_dob?: string;
  patient_language?: string;
  closure_type?: string;
}

export interface CaseEvent {
  seq: number;
  event_type: string;
  from_state: string | null;
  to_state: string | null;
  actor_id: string;
  actor_role: string;
  occurred_at: string;
  payload: any;
  prev_hash: string;
  hash: string;
}

export interface AIActionLog {
  id: string;
  kind: string;
  provider: string;
  model: string;
  output_text: string;
  validator_passed: boolean;
  fallback_used: boolean;
}

export interface AuditLogItem {
  id: string;
  actor_id: string;
  role: string;
  action: string;
  object_type: string;
  object_id: string;
  at: string;
  purpose: string;
}

