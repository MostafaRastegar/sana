import axios from "axios";
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
  return config;
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

    return Promise.reject(error);
  }
);

export function isAuthenticated(): boolean {
  return getCookie("access_token") !== null;
}

export default client;
