import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { ApiError } from "../lib/api";
import { instagramService } from "../services/instagram-service";
import { sentimentService } from "../services/sentiment-service";
import { safetyService } from "../services/safety-service";
import { insightsService } from "../services/insights-service";
import { analyticsService } from "../services/analytics-service";
import type { InstagramAccount, InstagramMedia } from "../types/instagram";
import type { SentimentSummary } from "../types/sentiment";
import type { SafetyComment, SafetySummary } from "../types/safety";
import type { AudienceInsight } from "../types/insights";
import type { AudienceTrend } from "../types/analytics";

type MediaWithSentiment = {
  media: InstagramMedia;
  sentiment: SentimentSummary;
};

const EMPTY_SENTIMENT: SentimentSummary = {
  total: 0,
  positive: 0,
  neutral: 0,
  negative: 0,
  positive_percentage: 0,
  neutral_percentage: 0,
  negative_percentage: 0,
};

const EMPTY_SAFETY: SafetySummary = {
  total: 0,
  safe: 0,
  constructive: 0,
  toxic: 0,
  severe_abuse: 0,
  spam: 0,
  shielded: 0,
};

const EMPTY_TREND: AudienceTrend = {
  points: [],
  positive_change: null,
  negative_change: null,
  shielded_change: null,
};

function percentage(value: number): string {
  return `${value.toFixed(value % 1 === 0 ? 0 : 1)}%`;
}

function signedChange(value: number | null, suffix = ""): string {
  if (value === null) {
    return "Not enough history";
  }

  const prefix = value > 0 ? "+" : "";
  return `${prefix}${value}${suffix}`;
}

export function DashboardPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const [accounts, setAccounts] = useState<InstagramAccount[]>([]);
  const [selectedAccountId, setSelectedAccountId] = useState<number | null>(null);
  const [summary, setSummary] = useState<SentimentSummary>(EMPTY_SENTIMENT);
  const [safetySummary, setSafetySummary] = useState<SafetySummary>(EMPTY_SAFETY);
  const [feedComments, setFeedComments] = useState<SafetyComment[]>([]);
  const [shieldedComments, setShieldedComments] = useState<SafetyComment[]>([]);
  const [isShieldRevealed, setIsShieldRevealed] = useState(false);
  const [audienceInsight, setAudienceInsight] = useState<AudienceInsight | null>(null);
  const [isGeneratingInsights, setIsGeneratingInsights] = useState(false);
  const [trend, setTrend] = useState<AudienceTrend>(EMPTY_TREND);
  const [media, setMedia] = useState<MediaWithSentiment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isWorking, setIsWorking] = useState(false);
  const [isCheckingConnection, setIsCheckingConnection] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const selectedAccount = useMemo(
    () => accounts.find((account) => account.id === selectedAccountId) ?? null,
    [accounts, selectedAccountId],
  );

  const loadAccountData = useCallback(async (accountId: number) => {
    const [
      accountSummary,
      accountSafety,
      accountFeed,
      accountMedia,
      currentInsight,
      accountTrend,
    ] = await Promise.all([
      sentimentService.getAccountSummary(accountId),
      safetyService.getSummary(accountId),
      safetyService.getFeed(accountId),
      instagramService.listMedia(accountId),
      insightsService.getCurrent(accountId),
      analyticsService.getTrend(accountId, 30),
    ]);

    const mediaWithSentiment = await Promise.all(
      accountMedia.map(async (item) => ({
        media: item,
        sentiment: await sentimentService.getMediaSummary(accountId, item.id),
      })),
    );

    setSummary(accountSummary);
    setSafetySummary(accountSafety);
    setFeedComments(accountFeed);
    setShieldedComments([]);
    setIsShieldRevealed(false);
    setAudienceInsight(currentInsight);
    setTrend(accountTrend);
    setMedia(mediaWithSentiment);
  }, []);

  const loadDashboard = useCallback(async () => {
    setError("");

    try {
      const connectedAccounts = await instagramService.listAccounts();
      setAccounts(connectedAccounts);

      if (connectedAccounts.length === 0) {
        setSelectedAccountId(null);
        setSummary(EMPTY_SENTIMENT);
        setSafetySummary(EMPTY_SAFETY);
        setFeedComments([]);
        setShieldedComments([]);
        setIsShieldRevealed(false);
        setAudienceInsight(null);
        setTrend(EMPTY_TREND);
        setMedia([]);
        return;
      }

      const requestedAccountId = Number(searchParams.get("account_id"));
      const selected =
        connectedAccounts.find((account) => account.id === requestedAccountId) ??
        connectedAccounts[0];

      setSelectedAccountId(selected.id);
      await loadAccountData(selected.id);

      if (searchParams.get("instagram") === "connected") {
        setNotice(
          `Instagram @${selected.username ?? selected.instagram_user_id} connected successfully.`,
        );
        setSearchParams({}, { replace: true });
      }
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : "We could not load your Instagram dashboard.",
      );
    } finally {
      setIsLoading(false);
    }
  }, [loadAccountData, searchParams, setSearchParams]);

  useEffect(() => {
    void loadDashboard();
  }, [loadDashboard]);

  async function handleConnectInstagram() {
    setError("");
    setIsWorking(true);

    try {
      const result = await instagramService.connect();
      window.location.assign(result.authorization_url);
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : "We could not start the Instagram connection.",
      );
      setIsWorking(false);
    }
  }

  async function handleCheckConnection() {
    if (!selectedAccountId) {
      return;
    }

    setError("");
    setNotice("");
    setIsCheckingConnection(true);

    try {
      const result = await instagramService.checkConnection(selectedAccountId);
      setAccounts((current) =>
        current.map((account) =>
          account.id === result.account.id ? result.account : account,
        ),
      );
      setNotice(
        result.token_refreshed
          ? "Instagram connection is healthy and the access token was refreshed."
          : "Instagram connection is healthy.",
      );
    } catch (caught) {
      try {
        setAccounts(await instagramService.listAccounts());
      } catch {
        // Preserve the original connection-check error.
      }
      setError(
        caught instanceof ApiError
          ? caught.message
          : "We could not verify this Instagram connection.",
      );
    } finally {
      setIsCheckingConnection(false);
    }
  }

  async function handleSyncAndAnalyze() {
    if (!selectedAccountId) {
      return;
    }

    setError("");
    setNotice("");
    setIsWorking(true);

    try {
      const sync = await instagramService.sync(selectedAccountId);
      const [sentimentAnalysis, safetyAnalysis] = await Promise.all([
        sentimentService.analyzeAccount(selectedAccountId),
        safetyService.analyzeAccount(selectedAccountId),
      ]);
      await analyticsService.captureSnapshot(selectedAccountId);
      await loadAccountData(selectedAccountId);

      setNotice(
        `Synced ${sync.media_count} posts and ${sync.comment_count} comments. Analyzed ${sentimentAnalysis.analyzed_comments} sentiment records and ${safetyAnalysis.analyzed_comments} safety records.`,
      );
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : "We could not sync and analyze this Instagram account.",
      );
    } finally {
      setIsWorking(false);
    }
  }

  async function handleAccountChange(accountId: number) {
    setSelectedAccountId(accountId);
    setError("");
    setNotice("");
    setIsLoading(true);

    try {
      await loadAccountData(accountId);
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : "We could not load this Instagram account.",
      );
    } finally {
      setIsLoading(false);
    }
  }

  async function handleGenerateInsights() {
    if (!selectedAccountId) {
      return;
    }

    setError("");
    setNotice("");
    setIsGeneratingInsights(true);

    try {
      const insight = await insightsService.generate(selectedAccountId);
      setAudienceInsight(insight);
      setNotice(
        `AI audience insights generated from ${insight.source_comment_count} safe and constructive comments.`,
      );
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : "We could not generate AI audience insights.",
      );
    } finally {
      setIsGeneratingInsights(false);
    }
  }

  async function handleRevealShielded() {
    if (!selectedAccountId || isShieldRevealed) {
      return;
    }

    setError("");
    try {
      const comments = await safetyService.getShielded(selectedAccountId, true);
      setShieldedComments(comments);
      setIsShieldRevealed(true);
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : "We could not reveal shielded comments.",
      );
    }
  }

  async function handleLogout() {
    await logout();
    navigate("/login", { replace: true });
  }

  if (isLoading) {
    return <div className="route-loading">Loading your Veya dashboard…</div>;
  }

  return (
    <main className="page dashboard-page">
      <header className="dashboard-header">
        <div>
          <span className="eyebrow">VEYA</span>
          <p className="muted">{user?.email}</p>
        </div>

        <div className="header-actions">
          {accounts.length > 0 ? (
            <button
              className="secondary-button"
              disabled={isWorking}
              onClick={() => void handleConnectInstagram()}
              type="button"
            >
              Add Instagram
            </button>
          ) : null}
          <button
            className="secondary-button"
            onClick={() => void handleLogout()}
            type="button"
          >
            Log out
          </button>
        </div>
      </header>

      <section className="dashboard-hero">
        <div>
          <p className="auth-kicker">Creator wellbeing analytics</p>
          <h1>Understand your audience. Keep the emotional distance.</h1>
          <p>
            Veya turns your Instagram comments into clear sentiment signals so
            you can learn from your audience without reading everything yourself.
          </p>
        </div>
      </section>

      {error ? <div className="dashboard-banner dashboard-banner--error">{error}</div> : null}
      {notice ? <div className="dashboard-banner">{notice}</div> : null}

      {accounts.length === 0 ? (
        <section className="empty-state">
          <div className="empty-state__icon" aria-hidden="true">◎</div>
          <p className="auth-kicker">Start here</p>
          <h2>Connect your Instagram account</h2>
          <p>
            Connect a professional Instagram account to import posts and comments,
            then Veya will analyze the audience sentiment for you.
          </p>
          <button
            className="primary-button"
            disabled={isWorking}
            onClick={() => void handleConnectInstagram()}
            type="button"
          >
            {isWorking ? "Connecting…" : "Connect Instagram"}
          </button>
        </section>
      ) : (
        <>
          <section className="dashboard-toolbar">
            <div>
              <label className="account-selector">
                <span>Instagram account</span>
                <select
                  onChange={(event) => void handleAccountChange(Number(event.target.value))}
                  value={selectedAccountId ?? ""}
                >
                  {accounts.map((account) => (
                    <option key={account.id} value={account.id}>
                      @{account.username ?? account.instagram_user_id}
                    </option>
                  ))}
                </select>
              </label>

              <div className="connection-health">
                <span
                  className={`connection-health__dot connection-health__dot--${selectedAccount?.connection_status ?? "connected"}`}
                />
                <div>
                  <strong>
                    Instagram {
                      selectedAccount?.connection_status === "reconnect_required"
                        ? "needs reconnection"
                        : selectedAccount?.connection_status === "degraded"
                          ? "connection degraded"
                          : "connected"
                    }
                  </strong>
                  <small>
                    {selectedAccount?.last_connection_check_at
                      ? `Last checked ${new Date(selectedAccount.last_connection_check_at).toLocaleString()}`
                      : "Connection health has not been checked yet"}
                  </small>
                  {selectedAccount?.last_api_error_message ? (
                    <small className="auto-sync-error">
                      {selectedAccount.last_api_error_message}
                    </small>
                  ) : null}
                </div>
              </div>

              <div className="auto-sync-status">
                <span className={`auto-sync-dot auto-sync-dot--${selectedAccount?.sync_status ?? "idle"}`} />
                <div>
                  <strong>
                    Automatic sync {
                      selectedAccount?.connection_status === "reconnect_required"
                        ? "paused"
                        : selectedAccount?.sync_status === "failed"
                          ? "needs attention"
                          : "enabled"
                    }
                  </strong>
                  <small>
                    {selectedAccount?.last_synced_at
                      ? `Last synced ${new Date(selectedAccount.last_synced_at).toLocaleString()}`
                      : "Waiting for the first background sync"}
                  </small>
                  {selectedAccount?.last_sync_error ? (
                    <small className="auto-sync-error">{selectedAccount.last_sync_error}</small>
                  ) : null}
                </div>
              </div>
            </div>

            <div className="dashboard-toolbar__actions">
              {selectedAccount?.connection_status === "reconnect_required" ? (
                <button
                  className="secondary-button"
                  disabled={isWorking}
                  onClick={() => void handleConnectInstagram()}
                  type="button"
                >
                  Reconnect Instagram
                </button>
              ) : (
                <button
                  className="secondary-button"
                  disabled={isCheckingConnection}
                  onClick={() => void handleCheckConnection()}
                  type="button"
                >
                  {isCheckingConnection ? "Checking…" : "Check connection"}
                </button>
              )}

              <button
                className="primary-button"
                disabled={
                  isWorking ||
                  selectedAccount?.connection_status === "reconnect_required"
                }
                onClick={() => void handleSyncAndAnalyze()}
                type="button"
              >
                {isWorking ? "Syncing & analyzing…" : "Sync now"}
              </button>
            </div>
          </section>

          <section className="sentiment-overview">
            <article className="positivity-card">
              <div>
                <p className="auth-kicker">Profile positivity</p>
                <strong>{percentage(summary.positive_percentage)}</strong>
                <p>
                  Based on {summary.total.toLocaleString()} analyzed comments for
                  @{selectedAccount?.username ?? selectedAccount?.instagram_user_id}.
                </p>
              </div>
              <div className="positivity-ring" aria-label={`${summary.positive_percentage}% positive`}>
                <span>{percentage(summary.positive_percentage)}</span>
              </div>
            </article>

            <div className="sentiment-grid">
              <article className="sentiment-card">
                <span className="sentiment-card__icon">❤️</span>
                <strong>{percentage(summary.positive_percentage)}</strong>
                <span>Positive</span>
                <small>{summary.positive.toLocaleString()} comments</small>
              </article>
              <article className="sentiment-card">
                <span className="sentiment-card__icon">😐</span>
                <strong>{percentage(summary.neutral_percentage)}</strong>
                <span>Neutral</span>
                <small>{summary.neutral.toLocaleString()} comments</small>
              </article>
              <article className="sentiment-card">
                <span className="sentiment-card__icon">⚠️</span>
                <strong>{percentage(summary.negative_percentage)}</strong>
                <span>Negative</span>
                <small>{summary.negative.toLocaleString()} comments</small>
              </article>
            </div>
          </section>

          <section className="trends-section">
            <div className="section-heading">
              <div>
                <p className="auth-kicker">Historical analytics</p>
                <h2>Audience health trend</h2>
              </div>
              <p>Last 30 days · {trend.points.length} snapshots</p>
            </div>

            <div className="trend-summary-grid">
              <article>
                <span>Positive change</span>
                <strong>{signedChange(trend.positive_change, " pts")}</strong>
              </article>
              <article>
                <span>Negative change</span>
                <strong>{signedChange(trend.negative_change, " pts")}</strong>
              </article>
              <article>
                <span>Shielded change</span>
                <strong>{signedChange(trend.shielded_change)}</strong>
              </article>
            </div>

            {trend.points.length === 0 ? (
              <div className="empty-posts">
                <h3>No historical snapshots yet</h3>
                <p>
                  Each successful “Sync & analyze” will now save an audience-health
                  snapshot so you can see how sentiment changes over time.
                </p>
              </div>
            ) : (
              <div className="trend-chart" aria-label="Audience positivity trend">
                {trend.points.slice(-12).map((point) => (
                  <div className="trend-point" key={point.id}>
                    <div className="trend-bar-track">
                      <div
                        aria-label={`${point.positive_percentage}% positive`}
                        className="trend-bar"
                        style={{ height: `${Math.max(point.positive_percentage, 4)}%` }}
                      />
                    </div>
                    <strong>{percentage(point.positive_percentage)}</strong>
                    <small>
                      {new Date(point.captured_at).toLocaleDateString(undefined, {
                        month: "short",
                        day: "numeric",
                      })}
                    </small>
                  </div>
                ))}
              </div>
            )}
          </section>

          <section className="safety-section">
            <div className="section-heading">
              <div>
                <p className="auth-kicker">Creator safety</p>
                <h2>Comment Shield</h2>
              </div>
              <p>{safetySummary.total} safety-classified comments</p>
            </div>

            <div className="safety-grid">
              <article className="shield-card">
                <div>
                  <span className="shield-icon" aria-hidden="true">🛡️</span>
                  <p className="auth-kicker">Shielded by default</p>
                  <strong>{safetySummary.shielded}</strong>
                  <p>
                    Potentially harmful comments are counted in analytics without
                    being shown to you unless you choose to reveal them.
                  </p>
                </div>
                <button
                  className="secondary-button"
                  disabled={isShieldRevealed || safetySummary.shielded === 0}
                  onClick={() => void handleRevealShielded()}
                  type="button"
                >
                  {isShieldRevealed ? "Shielded comments revealed" : "View shielded comments"}
                </button>
              </article>

              <div className="safety-stats">
                <article><strong>{safetySummary.constructive}</strong><span>Constructive</span></article>
                <article><strong>{safetySummary.toxic}</strong><span>Toxic</span></article>
                <article><strong>{safetySummary.severe_abuse}</strong><span>Severe abuse</span></article>
                <article><strong>{safetySummary.spam}</strong><span>Spam</span></article>
              </div>
            </div>

            {isShieldRevealed && shieldedComments.length > 0 ? (
              <div className="shielded-list">
                {shieldedComments.map((comment) => (
                  <article key={comment.id}>
                    <strong>@{comment.username ?? "Instagram user"}</strong>
                    <p>{comment.text}</p>
                  </article>
                ))}
              </div>
            ) : null}

            <div className="positive-feed">
              <div className="section-heading">
                <div>
                  <p className="auth-kicker">Positive feed</p>
                  <h2>Useful comments without the harmful noise</h2>
                </div>
                <p>{feedComments.length} comments</p>
              </div>

              {feedComments.length === 0 ? (
                <div className="empty-posts">
                  <h3>No safety feed yet</h3>
                  <p>Run “Sync & analyze” to classify your latest comments.</p>
                </div>
              ) : (
                <div className="comment-feed">
                  {feedComments.slice(0, 8).map((comment) => (
                    <article key={comment.id}>
                      <strong>@{comment.username ?? "Instagram user"}</strong>
                      <p>{comment.text}</p>
                    </article>
                  ))}
                </div>
              )}
            </div>
          </section>

          <section className="insights-section">
            <div className="section-heading">
              <div>
                <p className="auth-kicker">AI audience insights</p>
                <h2>What your audience is telling you</h2>
              </div>
              <button
                className="primary-button"
                disabled={isGeneratingInsights || safetySummary.total === 0}
                onClick={() => void handleGenerateInsights()}
                type="button"
              >
                {isGeneratingInsights
                  ? "Generating insights…"
                  : audienceInsight
                    ? "Regenerate insights"
                    : "Generate AI insights"}
              </button>
            </div>

            {audienceInsight ? (
              <div className="insights-panel">
                <article className="insight-summary">
                  <p className="auth-kicker">Audience summary</p>
                  <p>{audienceInsight.summary}</p>
                  <small>
                    Generated from {audienceInsight.source_comment_count} safe or
                    constructive comments.
                  </small>
                </article>

                <div className="insight-grid">
                  <article>
                    <h3>❤️ What people loved</h3>
                    <ul>
                      {audienceInsight.what_people_loved.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </article>
                  <article>
                    <h3>💡 Constructive feedback</h3>
                    <ul>
                      {audienceInsight.constructive_feedback.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </article>
                  <article>
                    <h3>📌 Recurring complaints</h3>
                    <ul>
                      {audienceInsight.recurring_complaints.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </article>
                  <article>
                    <h3>❓ Common questions</h3>
                    <ul>
                      {audienceInsight.common_questions.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </article>
                  <article className="insight-suggestions">
                    <h3>✨ Content suggestions</h3>
                    <ul>
                      {audienceInsight.content_suggestions.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </article>
                </div>
              </div>
            ) : (
              <div className="empty-posts">
                <h3>No AI audience summary yet</h3>
                <p>
                  Sync and analyze your comments first, then generate a structured
                  audience summary when you want one.
                </p>
              </div>
            )}
          </section>

          <section className="posts-section">
            <div className="section-heading">
              <div>
                <p className="auth-kicker">Recent content</p>
                <h2>Post sentiment</h2>
              </div>
              <p>{media.length} imported posts</p>
            </div>

            {media.length === 0 ? (
              <div className="empty-posts">
                <h3>No posts imported yet</h3>
                <p>Run “Sync & analyze” to pull your Instagram content and comments.</p>
              </div>
            ) : (
              <div className="posts-grid">
                {media.map(({ media: item, sentiment }) => (
                  <article className="post-card" key={item.id}>
                    <div className="post-card__visual">
                      {item.thumbnail_url || item.media_url ? (
                        <img
                          alt=""
                          src={item.thumbnail_url ?? item.media_url ?? ""}
                        />
                      ) : (
                        <span>{item.media_type === "REELS" ? "▶" : "◇"}</span>
                      )}
                    </div>

                    <div className="post-card__body">
                      <div className="post-card__meta">
                        <span>{item.media_type}</span>
                        <span>{sentiment.total} comments</span>
                      </div>
                      <h3>{item.caption?.trim() || "Instagram post"}</h3>

                      <div className="mini-sentiment">
                        <span>❤️ {percentage(sentiment.positive_percentage)}</span>
                        <span>😐 {percentage(sentiment.neutral_percentage)}</span>
                        <span>⚠️ {percentage(sentiment.negative_percentage)}</span>
                      </div>

                      {item.permalink ? (
                        <a
                          href={item.permalink}
                          rel="noreferrer"
                          target="_blank"
                        >
                          View on Instagram ↗
                        </a>
                      ) : null}
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </main>
  );
}
