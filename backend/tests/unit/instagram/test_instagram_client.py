import httpx

from veya.infrastructure.instagram.client import InstagramClient


def test_list_media_follows_paging_next() -> None:
    requests: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(str(request.url))
        if "page=2" in str(request.url):
            return httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "id": "m2",
                            "media_type": "IMAGE",
                            "caption": "Second",
                            "timestamp": "2026-09-18T12:00:00+00:00",
                        }
                    ]
                },
            )

        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": "m1",
                        "media_type": "REELS",
                        "caption": "First",
                        "timestamp": "2026-09-18T11:00:00+00:00",
                    }
                ],
                "paging": {
                    "next": "https://graph.instagram.com/fake/media?page=2"
                },
            },
        )

    client = InstagramClient(
        http_client=httpx.Client(transport=httpx.MockTransport(handler))
    )

    items = client.list_media(
        access_token="fake-access-token",
        instagram_user_id="ig-user",
    )

    assert [item.media_id for item in items] == ["m1", "m2"]
    assert len(requests) == 2


def test_list_comments_follows_paging_next() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if "page=2" in str(request.url):
            return httpx.Response(
                200,
                json={"data": [{"id": "c2", "text": "Second"}]},
            )

        return httpx.Response(
            200,
            json={
                "data": [{"id": "c1", "text": "First"}],
                "paging": {
                    "next": "https://graph.instagram.com/fake/comments?page=2"
                },
            },
        )

    client = InstagramClient(
        http_client=httpx.Client(transport=httpx.MockTransport(handler))
    )

    items = client.list_comments(
        access_token="fake-access-token",
        instagram_media_id="media-1",
    )

    assert [item.comment_id for item in items] == ["c1", "c2"]
