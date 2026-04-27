# Contributing to WallasAPI

First — thank you. Seriously. Every contribution to this project, from a typo fix to a new provider integration, is treated as a gift.

## 🤲 Ways to contribute (all are valuable)

### Free things that help me a lot

- ⭐ **Star the repo** — visibility is everything for a solo developer
- 🐦 **Share WallasAPI** with anyone who builds with AI
- 🐛 **Report bugs** with clear repro steps
- 📝 **Improve documentation** — typos, clarity, examples in your language
- 🌍 **Translate** — see `docs/i18n/` and submit a PR with a new language

### Code contributions

1. **Fork** the repo
2. **Create a branch**: `git checkout -b feature/your-feature`
3. **Make your changes** — keep them focused and small
4. **Test** that the existing routing still works (try `python -m wallasAPI.api_server` and hit `/v1/chat/completions`)
5. **Commit** with a clear message: `feat: add X`, `fix: handle Y`, `docs: clarify Z`
6. **Push** and open a Pull Request

## 🎯 What I most need help with

- **New provider integrations** — see `wallasAPI/providers/` and `wallasAPI/router.py`
- **Better heuristics** for `model_fetcher.py` — patterns for capability detection
- **Tests** — anything that prevents regressions
- **Real-world usage feedback** — what's confusing? what's missing?
- **Translations** of the README into more languages

## 🛠 Development setup

```bash
git clone https://github.com/wubjak/wallasapi.git
cd wallasapi
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt

# Copy env template
cp .env.example .env
# Add at least one API key (Gemini or Groq are free)

# Run
python -m wallasAPI.api_server
```

## 📋 Code style

- Follow existing patterns in the codebase — pragmatic over dogmatic
- No unnecessary dependencies — every added package costs the user disk space and trust
- Keep error messages clear and actionable
- Comment WHY, not WHAT

## 🤝 Code of conduct

Be kind. We're all building things from imperfect circumstances. No harassment, no discrimination, no toxicity. If you wouldn't say it to a colleague's face, don't say it here.

## 💬 Questions?

- Open a [Discussion](https://github.com/wubjak/wallasapi/discussions)
- Email me directly: **wubjak@protonmail.ch**

— Willen Ponce
