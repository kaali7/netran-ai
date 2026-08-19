import { create } from 'zustand';

const initialToken = localStorage.getItem('netran_token') || null;
let initialUser = null;
try {
  const savedUser = localStorage.getItem('netran_user');
  if (savedUser) {
    initialUser = JSON.parse(savedUser);
  }
} catch (e) {
  console.error('Failed to parse saved netran_user:', e);
}

export const useAuthStore = create((set) => ({
  token: initialToken,
  user: initialUser,
  isAuthenticated: Boolean(initialToken),
  isLoading: false,
  error: null,

  setAuth: (token, user) => {
    localStorage.setItem('netran_token', token);
    localStorage.setItem('netran_user', JSON.stringify(user));
    set({
      token,
      user,
      isAuthenticated: true,
      isLoading: false,
      error: null,
    });
  },

  logout: () => {
    localStorage.removeItem('netran_token');
    localStorage.removeItem('netran_user');
    set({
      token: null,
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
  },

  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error, isLoading: false }),
  clearError: () => set({ error: null }),

  updateUser: (updatedFields) => {
    set((state) => {
      const newUser = { ...state.user, ...updatedFields };
      localStorage.setItem('netran_user', JSON.stringify(newUser));
      return { user: newUser };
    });
  },
}));

export default useAuthStore;
