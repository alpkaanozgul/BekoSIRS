import axios from 'axios';
import { getToken } from '../storage/storage.native';

// Development: Set EXPO_PUBLIC_API_URL in .env (e.g. http://192.168.1.5:8000/)
// Each developer should configure their own local IP address.
export const API_BASE_URL = __DEV__
  ? process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000/'
  : process.env.EXPO_PUBLIC_PROD_API_URL || 'https://api.bekosirs.com/';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
  timeout: 30000, // 30 second timeout for ML-heavy endpoints
});

// Request interceptor — attach JWT token
api.interceptors.request.use(
  async (config) => {
    try {
      const token = await getToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch (error) {
      // Token retrieval failed silently
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const userError = error.response?.data?.message ||
      error.response?.statusText ||
      'Bağlantı hatası. Lütfen bağlantınızı kontrol edin.';

    return Promise.reject({
      ...error,
      userMessage: userError
    });
  }
);

/** Test backend reachability (development utility). */
export const testBackendConnection = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}admin/`, {
      timeout: 5000,
      validateStatus: () => true
    });
    return true;
  } catch {
    return false;
  }
};


/**
 * Get full image URL from path.
 * Handles both full URLs (http/https) and relative paths.
 */
export const getImageUrl = (imagePath: string | null | undefined): string | null => {
  if (!imagePath) return null;

  if (imagePath.startsWith('http') || imagePath.startsWith('https')) {
    return imagePath;
  }

  const baseUrl = (api.defaults.baseURL || '').replace(/\/$/, '');
  const cleanPath = imagePath.startsWith('/') ? imagePath : `/${imagePath}`;

  return `${baseUrl}${cleanPath}`;
};

export default api;