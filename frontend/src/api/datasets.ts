/**
 * Datasets API methods.
 */

import { apiGet, apiUpload } from './client';
import {
  DatasetPreviewResponse,
  DatasetResponse,
  DatasetUploadResponse,
} from '../types';

export async function listDatasets(scenarioId?: string): Promise<DatasetResponse[]> {
  const params = scenarioId ? { scenario_id: scenarioId } : undefined;
  return apiGet<DatasetResponse[]>('/datasets', params);
}

export async function getDataset(datasetId: string): Promise<DatasetResponse> {
  return apiGet<DatasetResponse>(`/datasets/${encodeURIComponent(datasetId)}`);
}

export async function previewDataset(
  datasetId: string,
  limit = 50,
  offset = 0
): Promise<DatasetPreviewResponse> {
  return apiGet<DatasetPreviewResponse>(
    `/datasets/${encodeURIComponent(datasetId)}/preview`,
    { limit, offset }
  );
}

export async function uploadDataset(
  file: File,
  scenarioId?: string,
  datasetName?: string
): Promise<DatasetUploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  if (scenarioId) {
    formData.append('scenario_id', scenarioId);
  }
  if (datasetName) {
    formData.append('dataset_name', datasetName);
  }
  return apiUpload<DatasetUploadResponse>('/datasets/upload', formData);
}

