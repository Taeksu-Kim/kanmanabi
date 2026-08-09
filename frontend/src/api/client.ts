import type {
  AnswerRequest,
  AnswerResponse,
  DueResponse,
  EpisodeProgressResponse,
  EpisodeProgressPatch,
  EpisodeSummary,
  GoogleAuthResponse,
  LearningSummary,
  NextResponse,
  StudyTrack,
  UserProfile,
  UserProfileUpdate,
  VocabularyFavoriteResponse,
  VocabularyItem,
  VocabularyListResponse,
} from "./types";

export const AUTH_REQUIRED_EVENT = "kanmanabi:auth-required";
export const AUTH_RESTORED_EVENT = "kanmanabi:auth-restored";

interface NextQuestionParams {
  level?: number;
  track?: StudyTrack;
  ep_no?: string;
  signal?: AbortSignal;
}

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
    credentials: "include",
    headers: {
      Accept: "application/json",
      ...init?.headers,
    },
  });

  if (!response.ok) {
    if (response.status === 401 && typeof window !== "undefined") {
      window.dispatchEvent(new Event(AUTH_REQUIRED_EVENT));
    }
    throw new ApiError(`API request failed: ${response.status}`, response.status);
  }

  return response.json() as Promise<T>;
}

export const studyApi = {
  next({ level = 1, track, ep_no, signal }: NextQuestionParams = {}) {
    const search = new URLSearchParams({ level: String(level) });
    if (track) search.set("track", track);
    if (ep_no) search.set("ep_no", ep_no);

    return request<NextResponse>(`/api/study/next?${search}`, { signal });
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

export const profileApi = {
  me(signal?: AbortSignal) {
    return request<UserProfile>("/api/me", { signal });
  },
  update(payload: UserProfileUpdate, signal?: AbortSignal) {
    return request<UserProfile>("/api/me", {
      method: "PATCH",
      body: JSON.stringify(payload),
      headers: { "Content-Type": "application/json" },
      signal,
    });
  },
};

export const learnApi = {
  summary(signal?: AbortSignal) {
    return request<LearningSummary>("/api/learn/summary", { signal });
  },
  episodes(signal?: AbortSignal) {
    return request<EpisodeSummary[]>("/api/episodes", { signal });
  },
  openEpisode(epNo: string) {
    return request<EpisodeProgressResponse>(`/api/episodes/${epNo}/progress`, {
      method: "PUT",
      body: JSON.stringify({ opened: true }),
      headers: { "Content-Type": "application/json" },
    });
  },
  updateEpisodeProgress(epNo: string, patch: EpisodeProgressPatch, signal?: AbortSignal) {
    return request<EpisodeProgressResponse>(`/api/episodes/${epNo}/progress`, {
      method: "PUT",
      body: JSON.stringify(patch),
      headers: { "Content-Type": "application/json" },
      signal,
    });
  },
};

export const authApi = {
  async google(credential: string, signal?: AbortSignal) {
    const user = await request<GoogleAuthResponse>("/api/auth/google", {
      method: "POST",
      body: JSON.stringify({ credential }),
      headers: { "Content-Type": "application/json" },
      signal,
    });
    if (typeof window !== "undefined") {
      window.dispatchEvent(new Event(AUTH_RESTORED_EVENT));
    }
    return user;
  },
  logout(signal?: AbortSignal) {
    return request<{ ok: boolean }>("/api/auth/logout", { method: "POST", signal });
  },
};

interface VocabularyListParams {
  level: number;
  q?: string;
  favorite?: boolean;
  cursor?: number;
  limit?: number;
  signal?: AbortSignal;
}

export const vocabularyApi = {
  list({ level, q = "", favorite = false, cursor, limit = 50, signal }: VocabularyListParams) {
    const search = new URLSearchParams({ level: String(level) });
    if (q) search.set("q", q);
    if (favorite) search.set("favorite", "true");
    if (cursor !== undefined) search.set("cursor", String(cursor));
    search.set("limit", String(limit));

    return request<VocabularyListResponse>(`/api/vocab?${search}`, { signal });
  },
  detail(id: number, signal?: AbortSignal) {
    return request<VocabularyItem>(`/api/vocab/${id}`, { signal });
  },
  favorite(id: number, favorite: boolean, signal?: AbortSignal) {
    return request<VocabularyFavoriteResponse>(`/api/vocab/${id}/favorite`, {
      method: favorite ? "PUT" : "DELETE",
      signal,
    });
  },
};
