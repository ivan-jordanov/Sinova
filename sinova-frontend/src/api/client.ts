const baseUrl = (import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1").replace(/\/$/, "");

export class ApiError extends Error {
  public readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

export const apiClient = {
  baseUrl,
  async request<T>(path: string, init?: RequestInit): Promise<T> {
    const response = await fetch(`${baseUrl}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
    });
    if (!response.ok) {
      throw new ApiError(response.status, await response.text());
    }
    const contentType = response.headers.get("content-type") ?? "";
    if (contentType.includes("application/octet-stream")) {
      return (await response.arrayBuffer()) as T;
    }
    return (await response.json()) as T;
  },
};
