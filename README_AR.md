<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/FastAPI-0.115+-green.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/Providers-12+-orange.svg" alt="12+ مزود">
  <img src="https://img.shields.io/badge/Models-100+-purple.svg" alt="100+ نموذج">
</p>

<h1 align="center">WallasAPI</h1>

<p align="center"><strong>محرك التوجيه الذكي متعدد المزودين</strong></p>

<p align="center"><em>مبني بالعرق والعزيمة ولابتوب من 2018، من غرفة مستأجرة، بواسطة <strong>Willen Ponce</strong></em></p>

---

## لماذا يوجد WallasAPI: قصة تهم

لم أولد مع MacBook Pro M4. ليس لدي خوادم سحابية ممولة من مستثمري وادي السيليكون. ليس لدي فريق من 50 مهندسًا خلفي. **ما لدي هو لابتوب من 2018، غرفة مستأجرة لا تخصني، وهوس: إثبات أنه من الفقر يمكن بناء شيء يتنافس مع الشركات.**

WallasAPI ولد في الساعات المسروقة بين القلق على الإيجار، والوجبة القادمة، والقدرة على النوم أربع ساعات على الأقل متواصلة دون الاستيقاظ وأنا أفكر بكم أدين. لم يكن لديّ مال لدفع APIs باهظة الثمن. لم تكن هناك شركة تدعمني. كان لديّ سؤال واحد مهووس:

> **"لماذا يجب أن أعتمد على مزود AI واحد عندما العالم كله من النماذج موجود هناك، الكثير مجاني، والكثير أفضل للمهام المحددة؟"**

فبنيته. **سطراً بسطر من Python. بدون أطر عمل فاخرة. بدون فرق. بدون مستثمرين.** فقط كود نقي، خوارزميات ذكية، والحاجة اليائسة لخلق شيء يعمل.

**WallasAPI ليس مجرد برنامج. إنه بقاء تقني.** إنه الموجه الذي لا يفرض عليك رسومًا على ذكائك. إنه النظام الذي لا يتخلى عنك عندما يسقط OpenAI، أو عندما تنتهي صلاحية مفتاح Claude API الخاص بك، أو عندما يقرر مزودك المفضل رفع الأسعار.

---

## ما هو WallasAPI؟

WallasAPI هو **محرك توجيه موحد** يربط تطبيقك أو IDE أو وكيلك بـ **أكثر من 12 مزود ذكاء اصطناعي** عبر **API واحد متوافق 100% مع OpenAI**.

عندما ترسل طلبًا، WallasAPI:
1. **يحلل المحتوى** (نص، صورة، صوت، PDF، فيديو)
2. **يختار المزود الأمثل** بناءً على القدرات والسرعة والتوفر والتكلفة
3. **يوجّه الطلب** تلقائيًا
4. **إذا فشل المزود الأساسي**، يعود تلقائيًا إلى التالي بشكل شفاف
5. **يرجع الاستجابة** بالتنسيق المتوافق مع OpenAI، مع بث مباشر عند الطلب

**كودك الموجود يعمل دون تغيير.** فقط غيّر عنوان URL الأساسي.

---

## الميزات الرئيسية

- **توجيه ذكي متعدد المزودين مع فشل ذاتي تلقائي**
- **بث مباشر حقيقي بشفافية تامة**
- **دعم متعدد الوسائط** — نص، صور، صوت، فيديو، PDF
- **بيانات وصفية غنية** — نافذة السياق، مستوى التسعير، الأدوات، البث، الأنماط
- **ذاكرة دائمة** — سجل JSON محلي، قابل للمزامنة مع Obsidian
- **توليد موحد** — صورة، فيديو، TTS من مزودين متعددين
- **OCR مع سلسلة فشل ذاتي** — EasyOCR → Mistral → Gemini → Ollama المحلي
- **نماذج محلية 100% خاصة** — عبر Ollama
- **تكامل Google كامل** — Drive، Calendar، Gmail مع OAuth2

---

## نقاط نهاية API

| نقطة النهاية | الطريقة | الوصف |
|---|---|---|
| `POST /v1/chat/completions` | دردشة | إكمال مع بث مباشر. نماذج افتراضية: `auto`، `fast`، `standard`، `reasoning`. |
| `POST /v1/embeddings` | تضمينات | توجيه متعدد المزودين. |
| `POST /v1/tts` | TTS | نص إلى كلام. |
| `POST /v1/images/generations` | صورة | توليد صور موحد. |
| `POST /v1/videos/generations` | فيديو | توليد فيديو موحد. |
| `GET /v1/models` | قائمة | نماذج مع بيانات وصفية كاملة. فلاتر: `?pricing=free`، `?capability=vision`. |
| `GET /v1/models/{id}` | تفاصيل | بيانات وصفية مفصلة لنموذج. |
| `GET /v1/capabilities/summary` | ملخص | عدد المجانية، الرؤية، الصوت، الاستدلال، إلخ. |
| `GET /v1/providers` | مزودون | بيانات وصفية عالمية لكل مزود. |

---

## التثبيت السريع

### Windows (موصى به: نقرتان على `start.bat`)

```bash
git clone https://github.com/your-username/wallasapi.git
cd wallasapi
# نقرتان على start.bat
```

### Linux / macOS

```bash
git clone https://github.com/your-username/wallasapi.git
cd wallasapi
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m wallasAPI.api_server
```

الخادم يبدأ على **http://localhost:8001**

المستندات التفاعلية: **http://localhost:8001/docs**

---

## الإعداد

أنشئ ملف `.env` بمفاتيح API للمزودين الذين تريد استخدامهم. **لا تحتاج جميعهم.**

```env
# مزودون مجانيون (موصى بهم للبدء)
GEMINI_API_KEY=your_key_here
GROQ_API_KEY=your_key_here
GITHUB_TOKEN=your_token_here

# مزودون مدفوعون (اختياري)
OPENAI_API_KEY=your_key_here
OPENROUTER_API_KEY=your_key_here
```

---

## الترخيص

المشروع مرخص بموجب MIT مخصص. احتفظ بالإسناد إلى **Willen Ponce**.

**طلب شخصي:** إذا استخدمت WallasAPI، أرسل بريدًا إلى **wubjak@protonmail.ch** تخبرني فيه أنك تستخدمه. "مرحبًا، أستخدم WallasAPI لـ X، شكرًا لبنائه" يكفي لجعل يوم مطوّر بنى هذا على لابتوب من 2018 أفضل.

انظر ملف `LICENSE` للنص الكامل.

---

## التبرعات: إبقاء هذا حيًا

هذا المشروع ليس لديه رعاة. لا مستثمرين من وادي السيليكون. لديه لابتوب من 2018، غرفة مستأجرة، وكود يعمل.

**إذا وفّر WallasAPI ساعات من التكامل أو ساعدك في بناء شيء رائع:**

- **PayPal** : [paypal.me/wubjak](https://paypal.me/wubjak)
- **Ko-fi** : [ko-fi.com/wubjak](https://ko-fi.com/wubjak)
- **Email** : wubjak@protonmail.ch

**Yape / Plin (بيرو) — الرقم: 980 702 580**

<p align="center">
  <img src="https://upload.wikimedia.org/wikipedia/commons/7/76/Yape_peru_logotype.svg" width="120" alt="Yape Logo">
  <img src="https://logos-world.net/wp-content/uploads/2024/11/Plin-Interbank-Logo.png" width="120" alt="Plin Logo">
</p>

**محافظ العملات المشفرة:**

| العملة | العنوان |
|---|---|
| **Ethereum** | `0xDec40634014bf05A40006BA48160cddAEe1143c2` |
| **Bitcoin** | `bc1qwrr5zal3tt7f5ye0ptgy8365cc8yt64hrj7dmt` |
| **Solana** | `HrTiFtmML4NJD1b3RrjQV3e1FgaBWgpqRtR6gFphApGh` |
| **Polygon** | `0xDec40634014bf05A40006BA48160cddAEe1143c2` |
| **Tron** | `TB1sHwCo3FFaabf26AHV8VNapWUJbca299` |
| **TronLink** | `TQsXuVbnSwicRNoCEmGVdFeo86X7ey7okx` |

> *"قبل أن يطردوني من المنزل، حتى أتمكن من تناول الإفطار، وسداد ديوني، والنوم أربع ساعات على الأقل متواصلة دون الاستيقاظ وأنا أفكر بكم أدين——كل مساهمة تهم. شكرًا لاستخدامك WallasAPI."* — **Willen Ponce**

---

<p align="center">
  <strong>WallasAPI</strong> — <em>واحد API ليحكمها جميعًا.<br>
  مبني من الفقر، بعزيمة من لا شيء ليخسره.</em>
</p>
