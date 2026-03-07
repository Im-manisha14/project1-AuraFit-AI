import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Only handle 401 errors, not network errors
    if (error.response?.status === 401 && !originalRequest._retry) {
      // Don't retry if this is already a refresh or login request
      if (originalRequest.url?.includes('/auth/refresh') || 
          originalRequest.url?.includes('/auth/login')) {
        return Promise.reject(error);
      }

      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) {
          throw new Error('No refresh token');
        }

        const response = await axios.post(
          `${API_URL}/auth/refresh`,
          {},
          {
            headers: {
              Authorization: `Bearer ${refreshToken}`,
            },
          }
        );

        const { access_token } = response.data;
        localStorage.setItem('access_token', access_token);

        // Update the original request with new token
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return api(originalRequest);
      } catch (refreshError) {
        console.error('Token refresh failed:', refreshError);
        // Clear tokens and redirect only if refresh truly failed
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        
        // Only redirect to login if we're not already on a public page
        if (!window.location.pathname.includes('/login') && 
            !window.location.pathname.includes('/register')) {
          window.location.href = '/login';
        }
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  getCurrentUser: () => api.get('/auth/me'),
};

// User API
export const userAPI = {
  getProfile: () => api.get('/users/profile'),
  updateProfile: (data) => api.put('/users/profile', data),
  getPreferences: () => api.get('/users/preferences'),
  updatePreferences: (data) => api.put('/users/preferences', data),
};

// Outfit API
export const outfitAPI = {
  getOutfits: (params) => api.get('/outfits', { params }),
  getOutfit: (id) => api.get(`/outfits/${id}`),
  submitFeedback: (id, data) => api.post(`/outfits/${id}/feedback`, data),
  getTrending: (limit = 10) => api.get(`/outfits/trending?limit=${limit}`),
};

// Recommendation API
export const recommendationAPI = {
  generate: (data) => api.post('/recommendations/generate', data),
  getHistory: (params) => api.get('/recommendations/history', { params }),
  getRecommendation: (id) => api.get(`/recommendations/${id}`),
  getCollections: (params) => api.get('/recommendations/collections', { params }),
};

export default api;
