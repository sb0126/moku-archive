// On the client (browser), always use relative path so requests go through
// Vercel's rewrite proxy (/api/* → Railway backend) and avoid CORS issues.
// On the server (SSR/SSG), use the absolute backend URL directly.
const API_BASE: string =
  typeof window !== "undefined"
    ? "" // relative path → Vercel rewrite handles routing to Railway
    : (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000");

export class ApiError extends Error {
  public status: number;
  public details: string | undefined;
  constructor(message: string, status: number, details?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${path}`;
  let res: Response;
  try {
    res = await fetch(url, {
      headers: { "Content-Type": "application/json", ...options.headers },
      ...options,
    });
  } catch (networkErr: unknown) {
    // Network failure (no response at all)
    throw new ApiError("ネットワークエラーが発生しました", 0);
  }

  // Try to parse JSON; fall back to text if not JSON
  let data: unknown;
  try {
    data = await res.json();
  } catch {
    const text = await res.text().catch(() => "");
    if (!res.ok) throw new ApiError(`サーバーエラー (${res.status})`, res.status);
    return text as unknown as T;
  }

  if (!res.ok) {
    const err = data as {
      error?: string;
      detail?: string | Array<{ msg?: string; message?: string }>;
      details?: string;
    };
    // FastAPI validation errors return detail as an array of objects
    let message: string;
    if (typeof err.detail === "string") {
      message = err.detail;
    } else if (Array.isArray(err.detail) && err.detail.length > 0) {
      message = err.detail.map((d) => d.msg || d.message || JSON.stringify(d)).join(", ");
    } else {
      message = err.error || `エラーが発生しました (${res.status})`;
    }
    throw new ApiError(message, res.status, err.details);
  }
  return data as T;
}

export const api = {
  get: <T>(path: string, init?: RequestInit): Promise<T> =>
    apiFetch<T>(path, { method: "GET", ...init }),
  post: <T>(path: string, body?: unknown, init?: RequestInit): Promise<T> =>
    apiFetch<T>(path, { method: "POST", body: JSON.stringify(body), ...init }),
  put: <T>(path: string, body?: unknown, init?: RequestInit): Promise<T> =>
    apiFetch<T>(path, { method: "PUT", body: JSON.stringify(body), ...init }),
  del: <T>(path: string, body?: unknown, init?: RequestInit): Promise<T> =>
    apiFetch<T>(path, { method: "DELETE", body: body ? JSON.stringify(body) : undefined, ...init }),
};
