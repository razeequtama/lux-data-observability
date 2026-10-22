/**
 * API client methods for scenario recovery verification and diff analysis.
 */

import { apiPost } from './client';
import { RecoveryVerifyRequest, RecoveryVerifyResponse } from '../types';

/**
 * Execute recovery verification for a scenario:
 * Swaps to clean fixtures, re-runs deterministic validations,
 * computes before-and-after diffs, and assesses downstream DAG health.
 */
export async function verifyRecovery(
  scenarioId: string,
  targetFixtureVersion: string = 'corrected'
): Promise<RecoveryVerifyResponse> {
  const payload: RecoveryVerifyRequest = {
    scenario_id: scenarioId,
    target_fixture_version: targetFixtureVersion,
  };
  return await apiPost<RecoveryVerifyResponse>('/recovery/verify', payload);
}

