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

  it("renders real sentiment and post data for a connected account", async () => {
    mocks.listAccounts.mockResolvedValue([
      {
        id: 7,
        instagram_user_id: "ig-7",
        username: "veya_creator",
        token_expires_at: null,
        created_at: new Date().toISOString(),
      },
    ]);

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
    mocks.getTrend.mockResolvedValue({
      points: [
        {
          id: 1,
          analyzed_comment_count: 80,
          positive: 48,
          neutral: 20,
          negative: 12,
          positive_percentage: 60,
          neutral_percentage: 25,
          negative_percentage: 15,
          constructive: 5,
          toxic: 3,
          severe_abuse: 1,
          spam: 2,
          shielded: 4,
          captured_at: "2026-09-10T10:00:00Z",
        },
        {
          id: 2,
          analyzed_comment_count: 100,
          positive: 72,
          neutral: 18,
          negative: 10,
          positive_percentage: 72,
          neutral_percentage: 18,
          negative_percentage: 10,
          constructive: 8,
          toxic: 6,
          severe_abuse: 2,
          spam: 4,
          shielded: 8,
          captured_at: "2026-09-18T10:00:00Z",
        },
      ],
      positive_change: 12,
      negative_change: -5,
      shielded_change: 4,
    });
    mocks.getInsight.mockResolvedValue({
      id: 99,
      summary: "People love the editing and want clearer audio.",
      what_people_loved: ["Editing style"],
      constructive_feedback: ["Increase audio volume"],
      recurring_complaints: ["Audio is low"],
      common_questions: ["Where is the location?"],
      content_suggestions: ["Add location details"],
      provider: "openai",
      model: "gpt-test",
      source_comment_count: 88,
      generated_at: new Date().toISOString(),
    });

    renderDashboard();

    expect((await screen.findAllByText("72%")).length).toBeGreaterThan(0);
    expect(screen.getByText("100 analyzed comments", { exact: false })).toBeInTheDocument();
    expect(screen.getByText("Dubai travel reel")).toBeInTheDocument();
    expect(screen.getByText("20 comments")).toBeInTheDocument();
    expect(screen.getByText("Comment Shield")).toBeInTheDocument();
    expect((await screen.findAllByText("8")).length).toBeGreaterThan(0);
    expect(screen.getByText("Love the editing!")).toBeInTheDocument();
    expect(screen.getByText("People love the editing and want clearer audio.")).toBeInTheDocument();
    expect(screen.getByText("Editing style")).toBeInTheDocument();
    expect(screen.getByText("Increase audio volume")).toBeInTheDocument();
    expect(screen.getByText("Audience health trend")).toBeInTheDocument();
    expect(screen.getByText("+12 pts")).toBeInTheDocument();
    expect(screen.getByText("-5 pts")).toBeInTheDocument();
    expect(screen.getByText("+4")).toBeInTheDocument();
    expect(mocks.getShielded).not.toHaveBeenCalled();

    await waitFor(() => {
      expect(mocks.getMediaSummary).toHaveBeenCalledWith(7, 42);
    });
  });
});


  it("captures a historical snapshot after sync and analysis", async () => {
    const user = userEvent.setup();

    mocks.listAccounts.mockResolvedValue([
      {
        id: 7,
        instagram_user_id: "ig-7",
        username: "veya_creator",
        token_expires_at: null,
        created_at: new Date().toISOString(),
      },
    ]);
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

    const button = await screen.findByRole("button", { name: /sync & analyze/i });
    await user.click(button);

    await waitFor(() => {
      expect(mocks.captureSnapshot).toHaveBeenCalledWith(7);
    });
  });
