/**
 * Dataset and preview schemas matching backend Pydantic models.
 */

export interface ColumnSchema {
  name: string;
  type: string;
  nullable: boolean;
}

export interface DatasetResponse {
  id: string;
  scenario_id: string;
  name: string;
  format: string;
  file_size_bytes: number;
  record_count: number;
  column_count: number;
  created_at?: string | null;
}

export interface DatasetPreviewResponse {
  dataset_id: string;
  total_records: number;
  limit: number;
  offset: number;
  columns: string[];
  rows: Record<string, unknown>[];
}

export interface DatasetUploadResponse {
  dataset_id: string;
  name: string;
  format: string;
  file_size_bytes: number;
  record_count: number;
  column_count: number;
}

