import axios from "axios";

const API_BASE_URL = "http://127.0.0.1:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access_token");

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

export function getToken() {
  return localStorage.getItem("access_token");
}

export function getStoredUser() {
  const storedUser = localStorage.getItem("user");

  if (!storedUser) {
    return null;
  }

  try {
    return JSON.parse(storedUser);
  } catch {
    localStorage.removeItem("user");
    return null;
  }
}

export function saveAuthentication(
  accessToken,
  user
) {
  localStorage.setItem(
    "access_token",
    accessToken
  );

  localStorage.setItem(
    "user",
    JSON.stringify(user)
  );
}

export function clearAuthentication() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("user");
}

export async function login(email, password) {
  const response = await api.post(
    "/auth/login",
    {
      email,
      password,
    }
  );

  return response.data;
}

export async function verifyMFA(
  mfaToken,
  code
) {
  const response = await api.post(
    "/auth/mfa/verify",
    {
      code,
    },
    {
      params: {
        mfa_token: mfaToken,
      },
    }
  );

  return response.data;
}

export async function setupMFA() {
  const response = await api.post(
    "/auth/mfa/setup"
  );

  return response.data;
}

export async function enableMFA(code) {
  const response = await api.post(
    "/auth/mfa/enable",
    {
      code,
    }
  );

  return response.data;
}

export async function getProtectedProfile() {
  const response = await api.get(
    "/protected"
  );

  return response.data;
}

export async function uploadQuestionPaper(
  formData
) {
  const response = await api.post(
    "/question-papers/upload",
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );

  return response.data;
}

export async function getPendingPapers() {
  const response = await api.get(
    "/approvals/pending"
  );

  return response.data;
}

export async function approvePaper(
  questionPaperId
) {
  const response = await api.post(
    `/approvals/${questionPaperId}/approve`
  );

  return response.data;
}

export async function rejectPaper(
  questionPaperId,
  reason
) {
  const response = await api.post(
    `/approvals/${questionPaperId}/reject`,
    {
      reason,
    }
  );

  return response.data;
}

export async function scheduleRelease(
  questionPaperId,
  releaseAt
) {
  const response = await api.post(
    `/release/${questionPaperId}/schedule`,
    {
      release_at: releaseAt,
    }
  );

  return response.data;
}

export async function getReleaseStatus(
  questionPaperId
) {
  const response = await api.get(
    `/release/${questionPaperId}/status`
  );

  return response.data;
}

export async function getAuditLogs(
  limit = 100
) {
  const response = await api.get(
    "/audit/logs",
    {
      params: {
        limit,
      },
    }
  );

  return response.data;
}

export async function verifyAuditChain() {
  const response = await api.get(
    "/audit/verify"
  );

  return response.data;
}

export async function downloadQuestionPaper(
  questionPaperId
) {
  const response = await api.get(
    `/downloads/${questionPaperId}`,
    {
      responseType: "blob",
    }
  );

  return response;
}

export default api;