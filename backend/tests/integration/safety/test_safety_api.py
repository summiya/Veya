from sqlalchemy import select

from veya.domain.instagram.models import InstagramAccount, InstagramComment, InstagramMedia
from veya.domain.safety.models import CommentSafety
from veya.infrastructure.instagram.token_cipher import encrypt_instagram_token
from veya.repositories.users import UserRepository


EMAIL = "creator@example.com"
PASSWORD = "strong-password-123"


def signup(client) -> dict:
    response = client.post(
        "/api/auth/signup",
        json={"email": EMAIL, "password": PASSWORD},
    )
    assert response.status_code == 201
    return response.json()


def auth_headers(auth: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth['access_token']}"}


def seed_comments(client, db) -> tuple[dict, int]:
    auth = signup(client)
    user = UserRepository(db).get_by_email(EMAIL)
    assert user is not None

    account = InstagramAccount(
        user_id=user.id,
        instagram_user_id="ig-safety",
        username="creator",
        access_token_encrypted=encrypt_instagram_token("fake-access-token"),
        token_expires_at=None,
    )
    db.add(account)
    db.flush()

    media = InstagramMedia(
        instagram_account_id=account.id,
        instagram_media_id="media-safety",
        media_type="REELS",
        caption="Safety test",
    )
    db.add(media)
    db.flush()

    db.add_all(
        [
            InstagramComment(
                instagram_media_id=media.id,
                instagram_comment_id="safe-1",
                text="Love this video!",
                username="fan",
            ),
            InstagramComment(
                instagram_media_id=media.id,
                instagram_comment_id="constructive-1",
                text="The audio is too low, please increase the volume next time.",
                username="helpful",
            ),
            InstagramComment(
                instagram_media_id=media.id,
                instagram_comment_id="toxic-1",
                text="You are an idiot.",
                username="toxic_user",
            ),
            InstagramComment(
                instagram_media_id=media.id,
                instagram_comment_id="severe-1",
                text="You should die.",
                username="abusive_user",
            ),
            InstagramComment(
                instagram_media_id=media.id,
                instagram_comment_id="spam-1",
                text="DM me for promotion, link in bio.",
                username="spam_user",
            ),
        ]
    )
    db.commit()
    return auth, account.id


def test_safety_analysis_and_summary(client, db) -> None:
    auth, account_id = seed_comments(client, db)

    analyze = client.post(
        f"/api/safety/instagram/accounts/{account_id}/analyze",
        headers=auth_headers(auth),
    )
    assert analyze.status_code == 200
    assert analyze.json() == {"analyzed_comments": 5}

    response = client.get(
        f"/api/safety/instagram/accounts/{account_id}",
        headers=auth_headers(auth),
    )

    assert response.status_code == 200
    assert response.json() == {
        "total": 5,
        "safe": 1,
        "constructive": 1,
        "toxic": 1,
        "severe_abuse": 1,
        "spam": 1,
        "shielded": 2,
    }


def test_shielded_comments_are_hidden_by_default(client, db) -> None:
    auth, account_id = seed_comments(client, db)
    client.post(
        f"/api/safety/instagram/accounts/{account_id}/analyze",
        headers=auth_headers(auth),
    )

    hidden = client.get(
        f"/api/safety/instagram/accounts/{account_id}/shielded",
        headers=auth_headers(auth),
    )
    revealed = client.get(
        f"/api/safety/instagram/accounts/{account_id}/shielded?reveal=true",
        headers=auth_headers(auth),
    )

    assert hidden.status_code == 200
    assert hidden.json() == []
    assert revealed.status_code == 200
    assert len(revealed.json()) == 2


def test_feed_excludes_shielded_and_spam(client, db) -> None:
    auth, account_id = seed_comments(client, db)
    client.post(
        f"/api/safety/instagram/accounts/{account_id}/analyze",
        headers=auth_headers(auth),
    )

    response = client.get(
        f"/api/safety/instagram/accounts/{account_id}/feed",
        headers=auth_headers(auth),
    )

    assert response.status_code == 200
    texts = {item["text"] for item in response.json()}
    assert "Love this video!" in texts
    assert "The audio is too low, please increase the volume next time." in texts
    assert "You are an idiot." not in texts
    assert "You should die." not in texts
    assert "DM me for promotion, link in bio." not in texts


def test_reanalysis_updates_existing_rows(client, db) -> None:
    auth, account_id = seed_comments(client, db)

    first = client.post(
        f"/api/safety/instagram/accounts/{account_id}/analyze",
        headers=auth_headers(auth),
    )
    second = client.post(
        f"/api/safety/instagram/accounts/{account_id}/analyze",
        headers=auth_headers(auth),
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert len(list(db.scalars(select(CommentSafety)))) == 5
