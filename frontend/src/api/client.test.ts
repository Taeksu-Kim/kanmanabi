import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  AUTH_REQUIRED_EVENT,
  AUTH_RESTORED_EVENT,
  authApi,
  learnApi,
  profileApi,
  studyApi,
  vocabularyApi,
} from "./client";

describe("studyApi.next", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ mode: "done", question: null }),
      }),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("requests the selected learning track", async () => {
    await studyApi.next({ level: 2, track: "grammar", ep_no: "EP17" });

    expect(fetch).toHaveBeenCalledWith(
      "/api/study/next?level=2&track=grammar&ep_no=EP17",
      expect.objectContaining({ signal: undefined }),
    );
  });

  it("sends whether choices were ever revealed", async () => {
    await studyApi.answer({ question_id: 203, answer: "가게", used_choices: true });

    expect(fetch).toHaveBeenCalledWith(
      "/api/study/answer",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ question_id: 203, answer: "가게", used_choices: true }),
      }),
    );
  });

  it("loads the profile, learning summary, and episodes from their fixed endpoints", async () => {
    await Promise.all([profileApi.me(), learnApi.summary(), learnApi.episodes()]);

    expect(fetch).toHaveBeenCalledWith("/api/me", expect.any(Object));
    expect(fetch).toHaveBeenCalledWith("/api/learn/summary", expect.any(Object));
    expect(fetch).toHaveBeenCalledWith("/api/episodes", expect.any(Object));
  });

  it("loads a filtered vocabulary cursor and updates favorites", async () => {
    await vocabularyApi.list({ level: 3, q: "학교", favorite: true, cursor: 30 });
    await vocabularyApi.favorite(91, true);
    await vocabularyApi.favorite(91, false);

    expect(fetch).toHaveBeenCalledWith(
      "/api/vocab?level=3&q=%ED%95%99%EA%B5%90&favorite=true&cursor=30&limit=50",
      expect.any(Object),
    );
    expect(fetch).toHaveBeenCalledWith(
      "/api/vocab/91/favorite",
      expect.objectContaining({ method: "PUT" }),
    );
    expect(fetch).toHaveBeenCalledWith(
      "/api/vocab/91/favorite",
      expect.objectContaining({ method: "DELETE" }),
    );
  });

  it("announces an authentication requirement on a 401 response", async () => {
    vi.mocked(fetch).mockResolvedValueOnce({ ok: false, status: 401 } as Response);
    const listener = vi.fn();
    window.addEventListener(AUTH_REQUIRED_EVENT, listener);

    await expect(profileApi.me()).rejects.toMatchObject({ status: 401 });
    expect(listener).toHaveBeenCalledOnce();

    window.removeEventListener(AUTH_REQUIRED_EVENT, listener);
  });

  it("submits a Google credential and announces the restored session", async () => {
    const listener = vi.fn();
    window.addEventListener(AUTH_RESTORED_EVENT, listener);

    await authApi.google("signed-google-id-token");

    expect(fetch).toHaveBeenCalledWith(
      "/api/auth/google",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ credential: "signed-google-id-token" }),
      }),
    );
    expect(listener).toHaveBeenCalledOnce();
    window.removeEventListener(AUTH_RESTORED_EVENT, listener);
  });

  it("partially updates an episode step instead of sending the old status contract", async () => {
    await learnApi.updateEpisodeProgress("EP17", { point: true });

    expect(fetch).toHaveBeenCalledWith(
      "/api/episodes/EP17/progress",
      expect.objectContaining({
        method: "PUT",
        body: JSON.stringify({ point: true }),
      }),
    );
  });

  it("records the episode that the learner most recently opened", async () => {
    await learnApi.openEpisode("EP17");

    expect(fetch).toHaveBeenCalledWith(
      "/api/episodes/EP17/progress",
      expect.objectContaining({
        method: "PUT",
        body: JSON.stringify({ opened: true }),
      }),
    );
  });
});
