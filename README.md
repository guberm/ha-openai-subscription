# OpenAI (Sign in with ChatGPT) — Home Assistant custom component

A local deployment of the patched `openai_conversation` integration that adds
**Sign in with ChatGPT** as an authentication method next to the API key.
Upstream work: branch `openai-conversation-chatgpt-subscription` (commit
`92008813`) against `home-assistant/core` `dev`.

## What it does

- Adds an auth-method choice to the OpenAI config flow: **API key** (unchanged)
  or **Sign in with ChatGPT**.
- The ChatGPT option authorizes against OpenAI with PKCE and dynamic client
  registration (`client_id=dynamic_agent_client`), stores the issued client id
  and the tokens in the config entry, refreshes the one hour access token with
  the rotating refresh token, and starts the Home Assistant reauth flow when the
  grant is revoked.
- Requests for such entries are shaped for the ChatGPT plan usage route
  (`store: false`, `stream: true`, no `max_output_tokens`/`temperature`/`top_p`,
  function tools grouped in one namespace tool, no image generation / Code
  Interpreter / file search).
- Speech to text and text to speech subentries are not created for a ChatGPT
  entry: the plan usage route does not provide those APIs.

## Install

This component **shadows** the core `openai_conversation` integration, so Home
Assistant logs a warning that a custom integration is in use. The same domain is
kept deliberately: existing OpenAI entries, devices and entities stay as they
are, and removing the directory restores the core integration.

With HACS:

1. HACS -> Integrations -> menu -> *Custom repositories*.
2. Add this repository URL as an **Integration** repository.
3. Install it and restart Home Assistant.

Manually:

1. Copy `custom_components/openai_conversation` into your Home Assistant
   `config/custom_components/` directory.
2. Restart Home Assistant.

## Sign in

1. **Settings -> Devices & services -> Add integration -> OpenAI**.
2. Choose **Sign in with ChatGPT (subscription plan)**.
3. Open the shown URL, sign in with the ChatGPT account that holds the plan and
   approve the requested access.
4. The browser is redirected to `http://127.0.0.1:1455/auth/callback?...` and the
   page cannot load — that is expected, because the callback is a loopback
   address on the browser's machine. Copy the **full address** from the address
   bar and paste it into the form.

A ChatGPT plan (Plus, Pro or Go) is required for plan usage; without the granted
`chatgpt.tokens.use.direct` permission the flow refuses to continue.
