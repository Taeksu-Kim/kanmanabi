import type { AnswerRequest, AnswerResponse, DueResponse, NextResponse } from "./types";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: {
      Accept: "application/json",
      ...init?.headers,
    },
  });

  if (!response.ok) {
    throw new ApiError(`API request failed: ${response.status}`, response.status);
  }

  return response.json() as Promise<T>;
}

export const studyApi = {
  next(level = 1, signal?: AbortSignal) {
    return request<NextResponse>(`/api/study/next?level=${level}`, { signal });
  },
  answer(payload: AnswerRequest, signal?: AbortSignal) {
    return request<AnswerResponse>("/api/study/answer", {
      method: "POST",
      body: JSON.stringify(payload),
      headers: { "Content-Type": "application/json" },
      signal,
    });
  },
  due(signal?: AbortSignal) {
    return request<DueResponse>("/api/study/due", { signal });
  },
};
