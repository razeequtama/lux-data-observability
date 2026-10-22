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
    if (isJson && typeof response.json === 'function') {
      try {
        const errorBody = (await response.json()) as Partial<ApiErrorResponse> & Record<string, unknown>;
        if (errorBody && typeof errorBody === 'object') {
          // Lux standard envelope: { error: { message, code, details } }
          const errorObj = errorBody.error as Record<string, unknown> | undefined;
          if (errorObj && typeof errorObj === 'object') {
            throw new ApiClientError(
              response.status,
              (errorObj.message as string) || `Request failed with status ${response.status}`,
              (errorObj.code as string) || `HTTP_${response.status}`,
              errorObj.details as Record<string, unknown> | undefined
            );
          }
          // FastAPI standard envelope: { detail: string | array }
          if (errorBody.detail !== undefined) {
            let detailMessage = '';
            if (typeof errorBody.detail === 'string') {
              detailMessage = errorBody.detail;
            } else if (Array.isArray(errorBody.detail)) {
              detailMessage = errorBody.detail
                .map((err: { msg?: string; loc?: (string | number)[] }) =>
                  err.msg ? `${err.loc ? err.loc.join('.') + ': ' : ''}${err.msg}` : JSON.stringify(err)
                )
                .join('; ');
            } else {
              detailMessage = JSON.stringify(errorBody.detail);
            }
            throw new ApiClientError(
              response.status,
              detailMessage || `Request failed with status ${response.status}`,
              `HTTP_${response.status}`,
              errorBody
            );
          }
          if (errorBody.message && typeof errorBody.message === 'string') {
            throw new ApiClientError(
              response.status,
              errorBody.message,
              (errorBody.code as string) || `HTTP_${response.status}`
            );
          }
        }
      } catch (e) {
        if (e instanceof ApiClientError) {
          throw e;
        }
      }
    }
    const text = typeof response.text === 'function' ? await response.text().catch(() => '') : '';
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

export async function apiPatch<T>(endpoint: string, body?: unknown): Promise<T> {
  const url = resolveUrl(endpoint);
  try {
    const response = await fetch(url, {
      method: 'PATCH',
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

export async function apiDelete<T = void>(endpoint: string): Promise<T> {
  const url = resolveUrl(endpoint);
  try {
    const response = await fetch(url, {
      method: 'DELETE',
      headers: {
        Accept: 'application/json',
      },
    });
    if (response.status === 204) {
      return undefined as unknown as T;
    }
    return await handleResponse<T>(response);
  } catch (error) {
    if (error instanceof ApiClientError) {
      throw error;
    }
    throw new ApiClientError(0, error instanceof Error ? error.message : 'Network connection failed', 'NETWORK_ERROR');
  }
}

export async function apiGetText(
  endpoint: string,
  params?: Record<string, string | number | boolean | undefined>
): Promise<string> {
  const url = resolveUrl(endpoint, params);
  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        Accept: '*/*',
      },
    });
    if (!response.ok) {
      const text = await response.text().catch(() => '');
      throw new ApiClientError(
        response.status,
        text || `Request failed with status ${response.status}`,
        `HTTP_${response.status}`
      );
    }
    return await response.text();
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
