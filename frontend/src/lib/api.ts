import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import type {
  ActionResult,
  DashboardOverview,
  HealAttempt,
  LoginResponse,
  PipelineRun,
  RiskReport,
  RunsPage,
  TestCase,
  TestResult,
  UserPayload,
} from '../types';

// Requests are same-origin: the Vite dev server proxies /api, /auth and
// /report to the FastAPI backend; production deploys do the same via reverse
// proxy. Override with VITE_API_URL for a split-origin setup.
const API_BASE_URL = import.meta.env.VITE_API_URL || '';

const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

// Attach the JWT to every request.
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Global error handling: expired/invalid token kicks the user back to login.
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    const status = error.response?.status;
    const onLogin = window.location.pathname.startsWith('/login');
    if (status === 401 && !onLogin) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  login: (email: string, password: string) =>
    api.post<LoginResponse>('/auth/login', { email, password }),
};

export const pipelineApi = {
  list: (page = 1, pageSize = 20) =>
    api.get<RunsPage>('/api/runs/', { params: { page, page_size: pageSize } }),
  get: (id: string) => api.get<PipelineRun>(`/api/runs/${id}`),
  getTests: (id: string) => api.get<TestCase[]>(`/api/runs/${id}/tests`),
  getResults: (id: string) => api.get<TestResult[]>(`/api/runs/${id}/results`),
  getReport: (id: string) => api.get<RiskReport>(`/api/runs/${id}/report`),
  approve: (id: string) => api.post<ActionResult>(`/api/runs/${id}/approve`),
};

export const testApi = {
  approve: (id: string) => api.post<ActionResult>(`/api/tests/${id}/approve`),
  reject: (id: string, reason = '') =>
    api.post<ActionResult>(`/api/tests/${id}/reject`, null, { params: { reason } }),
  getHeals: (id: string) => api.get<HealAttempt[]>(`/api/tests/${id}/heals`),
};

export const healApi = {
  approve: (id: string) => api.post<ActionResult>(`/api/heals/${id}/approve`),
  reject: (id: string) => api.post<ActionResult>(`/api/heals/${id}/reject`),
  execute: (id: string) => api.post<ActionResult>(`/api/heals/${id}/execute`),
};

export const dashboardApi = {
  overview: () => api.get<DashboardOverview>('/api/dashboard/overview'),
};

export const usersApi = {
  list: () => api.get<UserPayload[]>('/api/users/'),
  create: (body: { email: string; password: string; full_name?: string; roles?: string[] }) =>
    api.post<UserPayload>('/api/users/', body),
  setRoles: (id: string, roles: string[]) =>
    api.put<UserPayload>(`/api/users/${id}/roles`, { roles }),
  deactivate: (id: string) => api.delete(`/api/users/${id}`),
};

export default api;
