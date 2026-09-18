import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { ApiError } from "../lib/api";
import { instagramService } from "../services/instagram-service";
import { sentimentService } from "../services/sentiment-service";
import type { InstagramAccount, InstagramMedia } from "../types/instagram";
import type { SentimentSummary } from "../types/sentiment";

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

function percentage(value: number): string {
  return `${value.toFixed(value % 1 === 0 ? 0 : 1)}%`;
}

export function DashboardPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const [accounts, setAccounts] = useState<InstagramAccount[]>([]);
  const [selectedAccountId, setSelectedAccountId] = useState<number | null>(null);
  const [summary, setSummary] = useState<SentimentSummary>(EMPTY_SENTIMENT);
  const [media, setMedia] = useState<MediaWithSentiment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isWorking, setIsWorking] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const selectedAccount = useMemo(
    () => accounts.find((account) => account.id === selectedAccountId) ?? null,
    [accounts, selectedAccountId],
  );

  const loadAccountData = useCallback(async (accountId: number) => {
    const [accountSummary, accountMedia] = await Promise.all([
      sentimentService.getAccountSummary(accountId),
      instagramService.listMedia(accountId),
    ]);

    const mediaWithSentiment = await Promise.all(
      accountMedia.map(async (item) => ({
        media: item,
        sentiment: await sentimentService.getMediaSummary(accountId, item.id),
      })),
    );

    setSummary(accountSummary);
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

  async function handleSyncAndAnalyze() {
    if (!selectedAccountId) {
      return;
    }

    setError("");
    setNotice("");
    setIsWorking(true);

    try {
      const sync = await instagramService.sync(selectedAccountId);
      const analyzed = await sentimentService.analyzeAccount(selectedAccountId);
      await loadAccountData(selectedAccountId);

      setNotice(
        `Synced ${sync.media_count} posts and ${sync.comment_count} comments. Analyzed ${analyzed.analyzed_comments} comments.`,
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
            </div>

            <button
              className="primary-button"
              disabled={isWorking}
              onClick={() => void handleSyncAndAnalyze()}
              type="button"
            >
              {isWorking ? "Syncing & analyzing…" : "Sync & analyze"}
            </button>
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
