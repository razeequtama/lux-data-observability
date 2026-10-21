/**
 * Investigation workspace domain types matching backend schemas.
 */

export type InvestigationStatus =
  | 'OPEN'
  | 'INVESTIGATING'
  | 'RESOLVED'
  | 'RECOVERED'
  | 'CLOSED';

export type InvestigationItemType =
  | 'VERIFIED_FACT'
  | 'HYPOTHESIS'
  | 'ACTION_ITEM';

export interface InvestigationItem {
  item_type: InvestigationItemType;
  content: string;
  source?: string | null;
}

export interface InvestigationResponse {
  id: string;
  scenario_id: string;
  title: string;
  status: InvestigationStatus | string;
  initial_finding_id?: string | null;
  verified_facts: string[];
  hypotheses: string[];
  action_items: string[];
  created_at: string;
  updated_at: string;
}

export interface InvestigationCreateRequest {
  scenario_id: string;
  title: string;
  status?: InvestigationStatus | string;
  initial_finding_id?: string | null;
  verified_facts?: string[];
  hypotheses?: string[];
  action_items?: string[];
}

export interface InvestigationUpdateRequest {
  title?: string;
  status?: InvestigationStatus | string;
  initial_finding_id?: string | null;
  verified_facts?: string[];
  hypotheses?: string[];
  action_items?: string[];
}

export interface InvestigationSynthesizeRequest {
  scenario_id: string;
  title?: string;
  finding_id?: string | null;
}

