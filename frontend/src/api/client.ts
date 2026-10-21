/**
 * Typed HTTP client for the Lux Data Observability REST API.
 */

import { ApiErrorResponse } from '../types';

export class ApiClientError extends Error {
  public readonly status: number;
  public readonly code: string;
  public readonly details?: Record<string, unknown>;

  constructor(status: number, message: string, code = 'API_ERROR', details?: Record<string, unknown>) {
    super(message);
    this.name = 'ApiClientError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

const API_BASE_PATH = '/api/v1';

function resolveUrl(endpoint: string, params?: Record<string, string | number | boolean | undefined>): string {
  const fullPath = `${API_BASE_PATH}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;
  const origin =
    typeof window !== 'undefined' && window.location?.origin && window.location.origin !== 'null'
      ? window.location.origin
      : 'http://localhost:3000';

  const url = new URL(fullPath, origin);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        url.searchParams.append(key, String(value));
      }
    });
  }
  return url.toString();
}

async function handleResponse<T>(response: Response): Promise<T> {
  const contentType = response.headers.get('content-type');
  const isJson = contentType && contentType.includes('application/json');

  if (!response.ok) {
    if (isJson) {
      try {
        const errorBody = (await response.json()) as ApiErrorResponse;
        if (errorBody && errorBody.error) {
          throw new ApiClientError(
            response.status,
            errorBody.error.message || `Request failed with status ${response.status}`,
            errorBody.error.code || 'UNKNOWN_ERROR',
            errorBody.error.details
          );
        }
      } catch (e) {
        if (e instanceof ApiClientError) {
          throw e;
        }
      }
    }
    const text = await response.text().catch(() => '');
    throw new ApiClientError(
      response.status,
      text || `Request failed with status ${response.status}`,
      `HTTP_${response.status}`
    );
  }

  if (isJson) {
    return (await response.json()) as T;
  }
  return (await response.text()) as unknown as T;
}

export async function apiGet<T>(endpoint: string, params?: Record<string, string | number | boolean | undefined>): Promise<T> {
  const url = resolveUrl(endpoint, params);
  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        Accept: 'application/json',
      },
    });
    return await handleResponse<T>(response);
  } catch (error) {
    if (error instanceof ApiClientError) {
      throw error;
    }
    throw new ApiClientError(0, error instanceof Error ? error.message : 'Network connection failed', 'NETWORK_ERROR');
  }
}

export async function apiPost<T>(endpoint: string, body?: unknown): Promise<T> {
  const url = resolveUrl(endpoint);
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
    return await handleResponse<T>(response);
  } catch (error) {
    if (error instanceof ApiClientError) {
      throw error;
    }
    throw new ApiClientError(0, error instanceof Error ? error.message : 'Network connection failed', 'NETWORK_ERROR');
  }
}

export async function apiUpload<T>(endpoint: string, formData: FormData): Promise<T> {
  const url = resolveUrl(endpoint);
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        Accept: 'application/json',
      },
      body: formData,
    });
    return await handleResponse<T>(response);
  } catch (error) {
    if (error instanceof ApiClientError) {
      throw error;
    }
    throw new ApiClientError(0, error instanceof Error ? error.message : 'Network connection failed', 'NETWORK_ERROR');
  }
}
