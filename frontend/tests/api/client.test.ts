import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { apiGet, apiPost, apiUpload, ApiClientError } from '../../src/api/client';

describe('API Client', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('performs GET request and returns JSON response', async () => {
    const mockData = { id: 'test_scenario', name: 'Test Scenario' };
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => mockData,
    } as Response);

    const result = await apiGet('/scenarios', { scenario_id: '123' });
    expect(result).toEqual(mockData);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/scenarios?scenario_id=123'),
      expect.objectContaining({ method: 'GET' })
    );
  });

  it('performs POST request with JSON payload', async () => {
    const payload = { fixture_version: 'defective' };
    const mockResponse = { message: 'Loaded' };
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => mockResponse,
    } as Response);

    const result = await apiPost('/scenarios/test/load', payload);
    expect(result).toEqual(mockResponse);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/scenarios/test/load'),
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({ 'Content-Type': 'application/json' }),
        body: JSON.stringify(payload),
      })
    );
  });

  it('performs multipart upload request', async () => {
    const formData = new FormData();
    formData.append('file', new Blob(['test']), 'test.csv');
    const mockResponse = { dataset_id: 'upload_1', record_count: 10 };

    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => mockResponse,
    } as Response);

    const result = await apiUpload('/datasets/upload', formData);
    expect(result).toEqual(mockResponse);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/datasets/upload'),
      expect.objectContaining({
        method: 'POST',
        body: formData,
      })
    );
  });

  it('parses structured API error envelope on 4xx/5xx failure', async () => {
    const errorEnvelope = {
      error: {
        code: 'SCENARIO_NOT_FOUND',
        message: 'Scenario "non_existent" not found.',
        details: { scenario_id: 'non_existent' },
        timestamp: '2026-10-21T00:00:00Z',
      },
    };

    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: false,
      status: 404,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => errorEnvelope,
    } as Response);

    await expect(apiGet('/scenarios/non_existent')).rejects.toThrow(ApiClientError);

    try {
      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
        ok: false,
        status: 404,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => errorEnvelope,
      } as Response);
      await apiGet('/scenarios/non_existent');
    } catch (e) {
      const err = e as ApiClientError;
      expect(err.status).toBe(404);
      expect(err.code).toBe('SCENARIO_NOT_FOUND');
      expect(err.message).toBe('Scenario "non_existent" not found.');
      expect(err.details).toEqual({ scenario_id: 'non_existent' });
    }
  });

  it('handles network failure cleanly', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValueOnce(new Error('Connection refused'));

    await expect(apiGet('/health')).rejects.toThrow(ApiClientError);

    try {
      vi.spyOn(globalThis, 'fetch').mockRejectedValueOnce(new Error('Connection refused'));
      await apiGet('/health');
    } catch (e) {
      const err = e as ApiClientError;
      expect(err.status).toBe(0);
      expect(err.code).toBe('NETWORK_ERROR');
      expect(err.message).toBe('Connection refused');
    }
  });
});

