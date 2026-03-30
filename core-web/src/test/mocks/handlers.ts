import { http, HttpResponse } from 'msw';

const API_BASE = 'http://localhost:8000/api';

export const handlers = [
  // Auth / profile
  http.get(`${API_BASE}/users/me/profile`, () => {
    return HttpResponse.json({
      id: 'user-1',
      email: 'test@example.com',
      name: 'Test User',
      avatar_url: null,
      onboarding_completed_at: '2025-01-01T00:00:00Z',
    });
  }),

  // Workspaces
  http.get(`${API_BASE}/workspaces`, () => {
    return HttpResponse.json([
      {
        id: 'ws-1',
        name: 'Test Workspace',
        owner_id: 'user-1',
        is_default: true,
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
        role: 'owner',
      },
    ]);
  }),

  // Fallback for unhandled API calls during tests
  http.all(`${API_BASE}/*`, ({ request }) => {
    console.warn(`Unhandled ${request.method} request to ${request.url}`);
    return HttpResponse.json({ detail: 'Not mocked' }, { status: 404 });
  }),
];
