import type { JwtPayload } from '../types';

// Permission map mirroring app/services/rbac.py ROLE_PERMISSIONS_FALLBACK so
// the UI can gate actions from the role claim in the JWT alone.
const VIEWER = ['dashboard:view', 'pipeline:view', 'test:view'];

export const ROLE_PERMISSIONS: Record<string, string[]> = {
  viewer: [...VIEWER],
  developer: [...VIEWER, 'pipeline:create'],
  qa_engineer: [...VIEWER, 'pipeline:create', 'heal:propose', 'heal:execute'],
  approver: [
    ...VIEWER,
    'pipeline:create',
    'test:approve',
    'test:reject',
    'heal:propose',
    'heal:approve',
    'heal:execute',
  ],
  // admin gains everything; the backend DB context is authoritative anyway.
  admin: [
    ...VIEWER,
    'pipeline:create',
    'test:approve',
    'test:reject',
    'heal:propose',
    'heal:approve',
    'heal:execute',
    'user:view',
    'user:create',
    'user:edit',
    'user:delete',
    'system:configure',
  ],
};

export function decodeToken(token: string): JwtPayload | null {
  try {
    const [, payloadB64] = token.split('.');
    if (!payloadB64) return null;
    const json = atob(payloadB64.replace(/-/g, '+').replace(/_/g, '/'));
    return JSON.parse(json) as JwtPayload;
  } catch {
    return null;
  }
}

export function isTokenExpired(token: string): boolean {
  const payload = decodeToken(token);
  if (!payload?.exp) return true;
  // Small skew margin so we don't race expiry.
  return payload.exp * 1000 < Date.now() + 5000;
}

export function permissionsForRole(role: string): string[] {
  return ROLE_PERMISSIONS[role] ?? ROLE_PERMISSIONS.viewer;
}
