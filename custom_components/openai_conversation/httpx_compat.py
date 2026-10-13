"""Compatibility layer for the httpx flavour Home Assistant uses.

Home Assistant returned an ``httpx.AsyncClient`` from ``get_async_client`` until
2026.10 and an ``httpx2.AsyncClient`` from 2026.11. The OpenAI SDK validates the
auth flow we hand it against the base class of the client actually in use, so a
flow that subclasses the wrong one is rejected with
``TypeError: Invalid "auth" argument``.

The upstream core patch only needs ``httpx2``; this local deployment supports
both so the same integration runs on the current release as well.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, AsyncGenerator

try:  # pragma: no cover - depends on the Home Assistant release
    import httpx2
except ImportError:  # pragma: no cover
    httpx2 = None  # type: ignore[assignment]

import httpx

if TYPE_CHECKING:
    from .chatgpt_auth import ChatGPTAuth

_AUTH_CLASSES: dict[str, Any] = {}


def _module_for(client: Any) -> Any:
    """Return the httpx module whose client class this client belongs to."""
    if httpx2 is not None and isinstance(client, httpx2.AsyncClient):
        return httpx2
    if isinstance(client, httpx.AsyncClient):
        return httpx
    return httpx2 if httpx2 is not None else httpx


def _auth_class(module: Any) -> Any:
    """Build (once per httpx module) the auth flow class for that module."""
    key = module.__name__
    if key not in _AUTH_CLASSES:

        class _ChatGPTAuthFlow(module.Auth):  # type: ignore[misc, valid-type]
            """Attach the ChatGPT plan access token to every request.

            The token is refreshed before a request and, when the API rejects
            it, the request is replayed once with the refreshed token.
            """

            def __init__(self, auth: ChatGPTAuth) -> None:
                """Initialize the auth flow."""
                self._chatgpt_auth = auth
            async def async_auth_flow(
                self, request: Any
            ) -> AsyncGenerator[Any, Any]:
                """Attach a valid access token, refreshing once after a 401."""
                token = await self._chatgpt_auth.async_get_access_token()
                request.headers["Authorization"] = f"Bearer {token}"
                response = yield request
                if response is not None and response.status_code == 401:
                    await self._chatgpt_auth.async_handle_authentication_error()
                    request.headers["Authorization"] = (
                        f"Bearer {self._chatgpt_auth.credentials.access_token}"
                    )
                    yield request

        _AUTH_CLASSES[key] = _ChatGPTAuthFlow
    return _AUTH_CLASSES[key]


def create_auth_flow(client: Any, auth: ChatGPTAuth) -> Any:
    """Return an auth flow matching the httpx implementation of `client`."""
    return _auth_class(_module_for(client))(auth)
