import { describe, it, expect, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import { server } from '../test/mocks/server';
import { api, AuthExpiredError } from './client';
import { useAuthStore } from '../stores/authStore';

const API_BASE = 'http://localhost:8000/api';

// Helper to seed a fake session into authStore so api() can read a token
function seedSession(overrides: { expiresAt?: number } = {}) {
  const expiresAt = overrides.expiresAt ?? Math.floor(Date.now() / 1000) + 3600;
  useAuthStore.setState({
    session: {
      access_token: 'test-token',
      refresh_token: 'test-refresh',
      expires_at: expiresAt,
      expires_in: 3600,
      token_type: 'bearer',
      user: {
        id: 'user-1',
        app_metadata: {},
        user_metadata: {},
        aud: 'authenticated',
        created_at: '',
      },
    },
    isAuthenticated: true,
    user: {
      id: 'user-1',
      app_metadata: {},
      user_metadata: {},
      aud: 'authenticated',
      created_at: '',
    },
  });
}

function clearSession() {
  useAuthStore.setState({
    session: null,
    isAuthenticated: false,
    user: null,
    userProfile: null,
  });
}

describe('api() client', () => {
  beforeEach(() => {
    clearSession();
  });

  it('makes authenticated GET requests and returns JSON', async () => {
    seedSession();

    server.use(
      http.get(`${API_BASE}/test-endpoint`, ({ request }) => {
        const auth = request.headers.get('Authorization');
        return HttpResponse.json({ ok: true, auth });
      }),
    );

    const result = await api<{ ok: boolean; auth: string }>('/test-endpoint');
    expect(result.ok).toBe(true);
    expect(result.auth).toBe('Bearer test-token');
  });

  it('parses FastAPI string error details', async () => {
    seedSession();

    server.use(
      http.get(`${API_BASE}/fail`, () => {
        return HttpResponse.json({ detail: 'Something went wrong' }, { status: 400 });
      }),
    );

    await expect(api('/fail')).rejects.toThrow('Something went wrong');
  });

  it('parses FastAPI validation error arrays', async () => {
    seedSession();

    server.use(
      http.post(`${API_BASE}/validate`, () => {
        return HttpResponse.json(
          {
            detail: [
              { loc: ['body', 'name'], msg: 'field required', type: 'value_error.missing' },
              { loc: ['body', 'email'], msg: 'invalid email', type: 'value_error' },
            ],
          },
          { status: 422 },
        );
      }),
    );

    await expect(api('/validate', { method: 'POST' })).rejects.toThrow(
      'field required, invalid email',
    );
  });

  it('handles 204 No Content responses', async () => {
    seedSession();

    server.use(
      http.delete(`${API_BASE}/resource/1`, () => {
        return new HttpResponse(null, { status: 204 });
      }),
    );

    const result = await api('/resource/1', { method: 'DELETE' });
    expect(result).toEqual({});
  });

  it('throws AuthExpiredError on terminal 401', async () => {
    seedSession();

    server.use(
      http.get(`${API_BASE}/protected`, () => {
        return HttpResponse.json({ detail: 'Unauthorized' }, { status: 401 });
      }),
    );

    await expect(api('/protected')).rejects.toBeInstanceOf(AuthExpiredError);
  });

  it('sends requests without auth header when no session exists', async () => {
    // No session seeded
    server.use(
      http.get(`${API_BASE}/public`, ({ request }) => {
        const auth = request.headers.get('Authorization');
        return HttpResponse.json({ hasAuth: !!auth });
      }),
    );

    // This will throw AuthExpiredError since ensureFreshToken returns null and
    // the 401 retry flow is triggered, but the important thing is the request
    // doesn't crash with a null reference
    const result = await api<{ hasAuth: boolean }>('/public');
    expect(result.hasAuth).toBe(false);
  });
});
