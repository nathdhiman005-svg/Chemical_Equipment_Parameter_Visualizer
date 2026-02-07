import axios from "axios";

const API_BASE = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000/api";

const api = axios.create({
  baseURL: API_BASE,
});

// ── Request interceptor: attach JWT access token ──
api.interceptors.request.use((config) => {
  const tokens = JSON.parse(localStorage.getItem("tokens") || "null");
  if (tokens?.access) {
    config.headers.Authorization = `Bearer ${tokens.access}`;
  }
  return config;
});

// ── Auth endpoint paths that should NOT trigger the 401 redirect ──
const AUTH_PATHS = ["/auth/login", "/auth/register", "/auth/token/refresh"];

// ── Response interceptor: handle 401 → try refresh, else force re-login ──
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    const url = original?.url || "";

    // Never intercept 401 on login / register / refresh calls
    const isAuthRequest = AUTH_PATHS.some((p) => url.includes(p));
    if (isAuthRequest) return Promise.reject(error);

    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      const tokens = JSON.parse(localStorage.getItem("tokens") || "null");
      if (tokens?.refresh) {
        try {
          const { data } = await axios.post(`${API_BASE}/auth/token/refresh/`, {
            refresh: tokens.refresh,
          });
          localStorage.setItem(
            "tokens",
            JSON.stringify({ access: data.access, refresh: data.refresh || tokens.refresh })
          );
          original.headers.Authorization = `Bearer ${data.access}`;
          return api(original);
        } catch {
          localStorage.removeItem("tokens");
          localStorage.removeItem("user");
          window.location.href = "/login";
        }
      } else {
        localStorage.removeItem("tokens");
        localStorage.removeItem("user");
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

// ── Auth endpoints ──
export const register = (payload) => api.post("/auth/register/", payload);
export const login = (payload) => api.post("/auth/login/", payload);
export const getProfile = () => api.get("/auth/profile/");

// ── Equipment endpoints ──
export const uploadCSV = (file) => {
  const form = new FormData();
  form.append("file", file);
  return api.post("/equipment/upload/", form);
};
export const getStats = (uploadId) => {
  const params = uploadId ? { upload_id: uploadId } : {};
  return api.get("/equipment/stats/", { params });
};
export const getHistory = () => api.get("/equipment/history/");
export const deleteUpload = (id) => api.delete(`/equipment/history/${id}/`);
export const downloadReport = (uploadId) => {
  const params = uploadId ? { upload_id: uploadId } : {};
  return api.get("/equipment/report/", { responseType: "blob", params });
};

export default api;
