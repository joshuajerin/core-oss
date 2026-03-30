import { describe, it, expect, beforeEach } from 'vitest';
import { useAuthStore } from './authStore';

describe('authStore', () => {
  beforeEach(() => {
    // Reset store to initial state before each test
    useAuthStore.setState({
      user: null,
      session: null,
      userProfile: null,
      isLoading: false,
      isAuthenticated: false,
      onboardingCompletedAt: undefined,
    });
  });

  it('starts with unauthenticated state', () => {
    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(state.user).toBeNull();
    expect(state.session).toBeNull();
    expect(state.userProfile).toBeNull();
  });

  it('getAccessToken returns null when no session exists', () => {
    const token = useAuthStore.getState().getAccessToken();
    expect(token).toBeNull();
  });

  it('getAccessToken returns token from session', () => {
    useAuthStore.setState({
      session: {
        access_token: 'my-token',
        refresh_token: 'refresh',
        expires_at: Math.floor(Date.now() / 1000) + 3600,
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
    });

    const token = useAuthStore.getState().getAccessToken();
    expect(token).toBe('my-token');
  });

  it('updateAvatarUrl updates the user profile avatar', () => {
    useAuthStore.setState({
      userProfile: {
        id: 'user-1',
        email: 'test@example.com',
        name: 'Test',
        avatar_url: null,
      },
    });

    useAuthStore.getState().updateAvatarUrl('https://example.com/avatar.png');

    const profile = useAuthStore.getState().userProfile;
    expect(profile?.avatar_url).toBe('https://example.com/avatar.png');
  });

  it('updateAvatarUrl is a no-op when no profile exists', () => {
    useAuthStore.setState({ userProfile: null });

    useAuthStore.getState().updateAvatarUrl('https://example.com/avatar.png');

    expect(useAuthStore.getState().userProfile).toBeNull();
  });
});
