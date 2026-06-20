import axios from "axios";
import { auth } from "@/features/auth/api/firebase/firebaseApp";
import { normalizeApiError } from "@/shared/api/appError";

const API_BASE_PATH = "/api/v1";
const backendHost = import.meta.env.VITE_BACKEND_HOST?.replace(/\/$/, "") ?? "";

const httpClient = axios.create({
  baseURL: `${backendHost}${API_BASE_PATH}`,
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
