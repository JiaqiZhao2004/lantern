import axios from "axios";
import { auth } from "@/features/auth/api/firebase/firebaseApp";
import { normalizeApiError } from "@/shared/api/appError";

const API_BASE_PATH = "/api/v1";

const httpClient = axios.create({
  // Keep browser API calls same-origin and let the dev server proxy /api to the backend.
  baseURL: API_BASE_PATH,
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
});

httpClient.interceptors.request.use(
  async (config) => {
    const user = auth.currentUser;

    if (user) {
      const token = await user.getIdToken();
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => Promise.reject(normalizeApiError(error))
);

httpClient.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(normalizeApiError(error))
);

export default httpClient;
