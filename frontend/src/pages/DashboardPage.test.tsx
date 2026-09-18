import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { DashboardPage } from "./DashboardPage";

const mocks = vi.hoisted(() => ({
  listAccounts: vi.fn(),
  connect: vi.fn(),
  sync: vi.fn(),
  listMedia: vi.fn(),
  analyzeAccount: vi.fn(),
  getAccountSummary: vi.fn(),
  getMediaSummary: vi.fn(),
  analyzeSafety: vi.fn(),
  getSafetySummary: vi.fn(),
  getFeed: vi.fn(),
  getShielded: vi.fn(),
  getInsight: vi.fn(),
  generateInsight: vi.fn(),
  getTrend: vi.fn(),
  captureSnapshot: vi.fn(),
  logout: vi.fn(),
}));

vi.mock("../context/AuthContext", () => ({
  useAuth: () => ({
    user: {
      uuid: "user-1",
      email: "creator@example.com",
      is_active: true,
      created_at: new Date().toISOString(),
    },
    logout: mocks.logout,
  }),
}));

vi.mock("../services/instagram-service", () => ({
  instagramService: {
    listAccounts: mocks.listAccounts,
    connect: mocks.connect,
    sync: mocks.sync,
    listMedia: mocks.listMedia,
  },
}));

vi.mock("../services/sentiment-service", () => ({
  sentimentService: {
    analyzeAccount: mocks.analyzeAccount,
    getAccountSummary: mocks.getAccountSummary,
    getMediaSummary: mocks.getMediaSummary,
  },
}));

vi.mock("../services/safety-service", () => ({
  safetyService: {
    analyzeAccount: mocks.analyzeSafety,
    getSummary: mocks.getSafetySummary,
    getFeed: mocks.getFeed,
    getShielded: mocks.getShielded,
  },
}));

vi.mock("../services/insights-service", () => ({
  insightsService: {
    getCurrent: mocks.getInsight,
    generate: mocks.generateInsight,
  },
}));

vi.mock("../services/analytics-service", () => ({
  analyticsService: {
    getTrend: mocks.getTrend,
    captureSnapshot: mocks.captureSnapshot,
  },
}));

function renderDashboard(route = "/dashboard") {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <DashboardPage />
    </MemoryRouter>,
  );
}

function connectedAccount() {
  return {
    id: 7,
    instagram_user_id: "ig-7",
    username: "veya_creator",
    token_expires_at: null,
    sync_status: "idle",
    last_synced_at: "2026-09-18T10:00:00Z",
    next_sync_at: "2026-09-18T10:15:00Z",
    last_sync_error: null,
    created_at: new Date().toISOString(),
  };
}

describe("DashboardPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.getSafetySummary.mockResolvedValue({
      total: 0,
      safe: 0,
      constructive: 0,
      toxic: 0,
      severe_abuse: 0,
      spam: 0,
      shielded: 0,
    });
    mocks.getFeed.mockResolvedValue([]);
    mocks.getShielded.mockResolvedValue([]);
    mocks.getInsight.mockResolvedValue(null);
    mocks.getTrend.mockResolvedValue({
      points: [],
      positive_change: null,
      negative_change: null,
      shielded_change: null,
    });
  });

  it("shows the Instagram connection state for a new user", async () => {
    mocks.listAccounts.mockResolvedValue([]);

    renderDashboard();

    expect(
      await screen.findByRole("heading", {
        name: /connect your instagram account/i,
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /connect instagram/i }),
    ).toBeInTheDocument();
  });

  it("renders real data and automatic sync state", async () => {
    mocks.listAccounts.mockResolvedValue([connectedAccount()]);
    mocks.getAccountSummary.mockResolvedValue({
      total: 100,
      positive: 72,
      neutral: 18,
      negative: 10,
      positive_percentage: 72,
      neutral_percentage: 18,
      negative_percentage: 10,
    });
    mocks.listMedia.mockResolvedValue([
      {
        id: 42,
        instagram_media_id: "media-42",
        media_type: "REELS",
        caption: "Dubai travel reel",
        media_url: null,
        thumbnail_url: null,
        permalink: null,
        posted_at: null,
        last_synced_at: new Date().toISOString(),
      },
    ]);
    mocks.getMediaSummary.mockResolvedValue({
      total: 20,
      positive: 16,
      neutral: 3,
      negative: 1,
      positive_percentage: 80,
      neutral_percentage: 15,
      negative_percentage: 5,
    });
    mocks.getSafetySummary.mockResolvedValue({
      total: 100,
      safe: 80,
      constructive: 8,
      toxic: 6,
      severe_abuse: 2,
      spam: 4,
      shielded: 8,
    });
    mocks.getFeed.mockResolvedValue([
      {
        id: 1,
        text: "Love the editing!",
        username: "viewer",
        commented_at: null,
      },
    ]);

    renderDashboard();

    expect((await screen.findAllByText("72%")).length).toBeGreaterThan(0);
    expect(screen.getByText("Automatic sync enabled")).toBeInTheDocument();
    expect(screen.getByText(/Last synced/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /sync now/i })).toBeInTheDocument();
    expect(screen.getByText("Dubai travel reel")).toBeInTheDocument();

    await waitFor(() => {
      expect(mocks.getMediaSummary).toHaveBeenCalledWith(7, 42);
    });
  });

  it("keeps manual sync as an immediate override", async () => {
    const user = userEvent.setup();

    mocks.listAccounts.mockResolvedValue([connectedAccount()]);
    mocks.getAccountSummary.mockResolvedValue({
      total: 0,
      positive: 0,
      neutral: 0,
      negative: 0,
      positive_percentage: 0,
      neutral_percentage: 0,
      negative_percentage: 0,
    });
    mocks.listMedia.mockResolvedValue([]);
    mocks.sync.mockResolvedValue({ media_count: 1, comment_count: 5 });
    mocks.analyzeAccount.mockResolvedValue({ analyzed_comments: 5 });
    mocks.analyzeSafety.mockResolvedValue({ analyzed_comments: 5 });
    mocks.captureSnapshot.mockResolvedValue({
      id: 1,
      analyzed_comment_count: 5,
      positive: 3,
      neutral: 1,
      negative: 1,
      positive_percentage: 60,
      neutral_percentage: 20,
      negative_percentage: 20,
      constructive: 1,
      toxic: 0,
      severe_abuse: 0,
      spam: 0,
      shielded: 0,
      captured_at: new Date().toISOString(),
    });

    renderDashboard();

    await user.click(await screen.findByRole("button", { name: /sync now/i }));

    await waitFor(() => {
      expect(mocks.captureSnapshot).toHaveBeenCalledWith(7);
    });
  });
});
