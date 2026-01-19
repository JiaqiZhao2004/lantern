import axios from "axios";
import { auth } from "../firebase/firebaseConfig";

// Create an Axios instance
const axiosClient = axios.create({
  baseURL: process.env.REACT_APP_BACKEND_HOST, // Use environment variable for base URL
  timeout: 10000, // Set timeout to 10 seconds
  headers: {
    "Content-Type": "application/json",
  },
});

// Add a request interceptor
axiosClient.interceptors.request.use(
  async (config) => {
    // Add authorization token or other custom headers if needed
    const user = auth.currentUser;
    if (user) {
      const token = await user.getIdToken();
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    // Handle request error
    return Promise.reject(error);
  }
);

// Add a response interceptor
axiosClient.interceptors.response.use(
  (response) => {
    // Handle successful response
    return response;
  },
  (error) => {
    // Handle response error
    if (error.response) {
      // Example: Handle specific HTTP status codes
      if (error.response.status === 401) {
        console.error("Unauthorized - Redirecting to login");
        // Redirect to login page or handle token refresh
      }
    }
    return Promise.reject(error);
  }
);

export default axiosClient;
