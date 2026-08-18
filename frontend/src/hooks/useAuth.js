import { useCallback } from 'react';
import { useAuthStore } from '../store/authStore';
import { authService } from '../services/authService';

export const useAuth = () => {
  const {
    token,
    user,
    isAuthenticated,
    isLoading,
    error,
    setAuth,
    logout: storeLogout,
    setLoading,
    setError,
    clearError,
  } = useAuthStore();

  const login = useCallback(
    async (email, password) => {
      try {
        setLoading(true);
        clearError();
        const data = await authService.login({ email, password });
        setAuth(data.access_token, data.user);
        return data;
      } catch (err) {
        const message =
          err.response?.data?.detail ||
          err.message ||
          'Failed to sign in. Please check your credentials.';
        setError(message);
        throw new Error(message);
      }
    },
    [setAuth, setLoading, setError, clearError]
  );

  const signup = useCallback(
    async (email, password, role = 'candidate') => {
      try {
        setLoading(true);
        clearError();
        // 1. Create account
        await authService.signup({ email, password, role });
        // 2. Auto-login after successful registration
        const loginData = await authService.login({ email, password });
        setAuth(loginData.access_token, loginData.user);
        return loginData;
      } catch (err) {
        const message =
          err.response?.data?.detail ||
          err.message ||
          'Failed to create account. Please try again.';
        setError(message);
        throw new Error(message);
      }
    },
    [setAuth, setLoading, setError, clearError]
  );

  const logout = useCallback(() => {
    storeLogout();
  }, [storeLogout]);

  return {
    token,
    user,
    isAuthenticated,
    isLoading,
    error,
    login,
    signup,
    logout,
    clearError,
  };
};

export default useAuth;
