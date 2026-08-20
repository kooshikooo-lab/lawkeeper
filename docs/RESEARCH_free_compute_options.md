# Free compute options — real research, 2026-08-20

Requested directly by the user, with real economic stakes stated plainly:
squeeze everything genuinely free out of what's available, across coding,
image generation, and voice recognition. Every claim below is sourced;
where sources disagreed (they often did — free-tier numbers shift fast
and get cut without notice), that disagreement is stated, not smoothed
over. **Live figures should always be re-checked at the provider's own
console before relying on them for anything time-sensitive** — this is
a snapshot, not a permanent guarantee.

---

## 1. Free LLM/coding inference (beyond what's already wired in)

Already in use tonight: `opencode/*-free` models (real, proven, $0 —
see `Windwright/scripts/model_switcher.py`), OpenRouter's `:free` models
(real but heavily rate-limited on the shared pool, confirmed live).

**New, real options found, not yet used:**

- **Gemini API** (Google AI Studio, `aistudio.google.com`) — you already
  use Gemini via the web/app; the **API** is a separate, genuinely free
  tier you're not using programmatically. Real free-tier figures found
  (sources disagree, re-check live): Gemini 2.5 Flash-Lite ~1,000
  requests/day, Flash ~250/day, Pro ~100/day; one source reports up to
  1,500 req/day / 1M tokens/min overall. No credit card required.
  **Real caveat:** Google cut free quotas 50-80% in December 2025
  without notice — treat any number here as "true as of today," not
  permanent.
- **Groq** — real, fast, generous: Llama 3.3 70B at 700+ tokens/sec,
  14,400 requests/day, 6,000 tokens/min. Strong enough for real coding/
  agentic work per multiple sources. No credit card mentioned as a
  barrier.
- **Cerebras** — highest raw daily volume found: 1M tokens/day, no
  credit card. Real caveat, same shape as OpenRouter's shifting free
  list: providers have been known to quietly remove free models.
- **Mistral** — ~1 billion tokens/month free, phone verification only
  (no credit card). Codestral (their code model) supports Fill-in-the-
  Middle, useful for IDE-style completion specifically.
- **HuggingFace Inference API** — free but real limits: ~1,000 requests/
  day on popular models, cold-start latency can exceed 30 seconds. Best
  as a fallback, not a primary.

Sources: [OpenRouter's own free-LLM comparison](https://openrouter.ai/blog/tutorials/free-llm-apis-compared/), [Gemini free tier guide](https://tokenmix.ai/blog/gemini-api-free-tier-limits), [Gemini billing-trap warning](https://usagebox.com/articles/gemini-api-billing-free-tier-confusion)

## 2. Free image generation

- **Pollinations.AI** — the standout real find: genuinely free, **no API
  key, no signup, no credit card**, includes Flux (a real, current-
  generation model). Directly relevant to tonight's laptop pipeline task
  (illustration generation) — could sidestep the local-GPU problem
  entirely (neither machine clearly clears SDXL's VRAM bar) at zero setup
  cost. Worth trying before investing more effort in local ComfyUI/SDXL
  setup.
- **HuggingFace Spaces** — free, browser-based, no setup, real
  open-source models (several with dedicated free Spaces).
- **Cloudflare Workers AI** — reported as the best free option for speed
  specifically.
- **Stability AI** — free trial credit balance (finite, not renewing),
  not a permanent free tier.

Sources: [Free image-gen API roundup](https://apiframe.ai/blog/free-ai-image-generation-api-2026), [Pollinations review](https://itsfree.dev/tools/pollinations-ai)

## 3. Free voice recognition / speech-to-text

- **Whisper (OpenAI, open-source)** — the strongest real option: free to
  self-host, 5-6% word error rate on English, reported to beat Azure/
  Google Speech-to-Text on some benchmarks, 99 languages, can also
  translate speech to English directly. Runs locally (GPU speeds it up
  significantly, but CPU works, just slower) — directly relevant to the
  already-logged voice-input reliability problems from earlier tonight
  (duplicate sends, unprompted sends) and the deferred "offline voice
  input" idea.
- **Vosk** — lighter-weight, fully offline, works on genuinely
  low-resource hardware (Raspberry Pi-class), 20+ languages. Worth
  considering specifically if Whisper's compute needs don't fit current
  hardware.

Sources: [AssemblyAI's free STT comparison](https://www.assemblyai.com/blog/the-top-free-speech-to-text-apis-and-open-source-engines), [Self-hosted Whisper guide](https://www.digitalapplied.com/blog/local-speech-to-text-whisper-self-hosted-transcription-2026)

## 4. Creative fallback: automating free consumer web/app UIs

Explicitly requested as a last resort ("hogging phase... copy and
paste if nothing else is possible"). **Real infrastructure for exactly
this already exists, don't rebuild it**: Windwright's
`scripts/gui_automation/desktop_chat.py` (clipboard-paste + OCR
read-back against a real desktop chat app window — the same pattern
`consensus_orchestrator.py` used for ChatGPT/Claude Desktop). Real,
known weakness already documented tonight: OCR automation is fragile
(window state, font rendering, UI changes) — genuinely worth using only
after the real API options above are exhausted, not as a first choice.

## Recommendation, priority order

1. Get a real Gemini API key (`aistudio.google.com`, no card) — you
   already trust Gemini's quality, this makes it programmatically usable.
2. Try Pollinations.AI for the laptop's image-generation pipeline stage
   before investing more in local SDXL/ComfyUI setup — zero-cost, zero
   local-GPU-constraint path to the same goal.
3. Groq and Mistral as real, generous alternatives to OpenRouter's
   congested free pool for text/coding work.
4. Whisper (local, self-hosted) for the voice-input reliability problem,
   when there's room to actually build it — ties into the already-logged
   `voice-input-offline-privacy` idea.
5. Desktop-UI automation (OCR) only as the genuine last resort, reusing
   existing Windwright infrastructure rather than building new.

## Re-check when

Any of these free-tier numbers should be re-verified at the provider's
own console immediately before depending on them for real, time-
sensitive work — multiple sources found here explicitly warn free tiers
get cut or removed without notice.
