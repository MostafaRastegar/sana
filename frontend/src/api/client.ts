import axios from "axios";
import { notification } from "antd";
import { getCookie, setCookie, removeCookie } from "../utils/cookies";

const client = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
  withCredentials: true,
});

client.interceptors.request.use((config) => {
  const token = getCookie("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  // Prevent browser caching on GET requests
  if (config.method === "get") {
    config.headers["Cache-Control"] = "no-cache, no-store, must-revalidate";
    config.headers.Pragma = "no-cache";
  }
  return config;
});

// Unwrap {success: true, data: ...} envelope from custom actions
client.interceptors.response.use((response) => {
  const body = response.data;
  if (body && body.success === true && body.data !== undefined) {
    response.data = body.data;
  }
  return response;
});

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const refreshToken = getCookie("refresh_token");
      if (refreshToken) {
        try {
          const { data } = await axios.post("/api/token/refresh/", {
            refresh: refreshToken,
          });
          setCookie("access_token", data.access);
          originalRequest.headers.Authorization = `Bearer ${data.access}`;
          return client(originalRequest);
        } catch {
          removeCookie("access_token");
          removeCookie("refresh_token");
          window.location.href = "/login";
        }
      } else {
        window.location.href = "/login";
      }
    }

    // Show all non-401 errors as toast notifications
    if (error.response?.status !== 401) {
      const msg =
        error.response?.data?.detail ||
        error.response?.data?.message ||
        (typeof error.response?.data === "string" ? error.response.data : null) ||
        error.message ||
        "An unexpected error occurred";
      notification.error({ message: "Error", description: msg, placement: "topRight" });
    }

    return Promise.reject(error);
  }
);

export function isAuthenticated(): boolean {
  return getCookie("access_token") !== null;
}

export default client;