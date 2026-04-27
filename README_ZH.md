<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/FastAPI-0.115+-green.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/Providers-12+-orange.svg" alt="12+ Providers">
  <img src="https://img.shields.io/badge/Models-100+-purple.svg" alt="100+ Models">
</p>

<h1 align="center">WallasAPI</h1>

<p align="center"><strong>终极多供应商AI智能路由引擎</strong></p>

<p align="center"><em>用汗水、决心和一台2018年的笔记本，在一间租来的房间里，由 <strong>Willen Ponce</strong> 亲手打造</em></p>

---

## 为什么WallasAPI存在：一个值得讲述的故事

我不是含着MacBook Pro M4出生的。我没有硅谷投资者资助的云服务器。我身后没有50人的工程师团队。**我拥有的是一台2018年的笔记本电脑、一间不属于我的出租屋，以及一种执念：证明即使处于贫困之中，也能建造出与大公司竞争的东西。**

WallasAPI诞生于我在担忧房租、下一顿饭、以及能否连续睡至少四小时而不在梦中被债务惊醒之间偷来的时间里。我没有钱支付昂贵的API。没有公司支持我。我只有一个执着的问题：

> **"当世界上有那么多模型就在那里，许多免费，许多更适合特定任务时，我为什么要依赖单一的AI供应商？"**

所以我建造了它。**一行一行的Python代码。没有花哨的框架。没有团队。没有投资者。**只有纯粹的代码、聪明的启发式方法，以及创造有用东西的迫切需求。因为当你没有什么可失去的时候，每一行代码都是对绝望的一次押注。

**WallasAPI不仅仅是软件。它是技术生存。**它是不向你收取智能费用的路由器。它是当OpenAI宕机、当你的Claude API密钥过期、或当你最喜欢的供应商决定涨价时不会抛弃你的系统。它知道何时使用**Gemini**（免费），何时使用**Groq**（超快），何时使用**DeepSeek R1**（深度推理），何时使用你自己的**本地Ollama**（100%私密）。

**而且这一切都是自动完成的。**

---

## WallasAPI是什么？

WallasAPI是一个**统一路由引擎**，通过**单一OpenAI兼容API**将您的应用程序、IDE或智能体与**12+个AI供应商**（还在增加）连接起来。

您不需要集成12个不同的SDK。您不需要记住哪个模型接受图像、哪个免费、哪个支持流式传输、哪个有百万token上下文。**WallasAPI为您知道这些。并且暴露出来，让您的客户端自动发现。**

当您发送提示时，WallasAPI会：
1. **分析内容**（文本、图像、音频、PDF、视频）
2. **基于能力、速度、可用性和成本选择最佳供应商**
3. **自动路由请求**
4. **如果主供应商失败**，透明地回退到下一个，而您的用户不会察觉
5. **以OpenAI兼容格式返回响应**，如果您要求则支持流式传输

**您现有的代码无需更改。**只需更改基础URL。

---

## 改变规则的功能

这些功能中的每一个都是因为我作为一个没有预算的开发者需要生存而建造的：

### 1. 智能多供应商路由与自动回退
OpenAI失败？没问题。WallasAPI在毫秒内切换到**Gemini**。Groq宕机？立即路由到**Cerebras**或**本地Ollama**。没有单点故障。您的应用程序**永远不会没有响应。**

### 2. 完全透明的实时流式传输
响应像OpenAI一样实时逐token到达。但如果主供应商在流式传输中间失败怎么办？**回退是完全透明的。**您的用户不会注意到底层供应商已经更换。

### 3. 为您思考的多模态支持
文本、图像、音频、视频、PDF。这就是神奇之处：**路由器决定谁能处理什么。**想发送PDF给Groq？WallasAPI知道Groq不接受原生文件，因此自动用OCR提取文本并发送。想发送视频给Gemini？原生处理，无需转换。**您不需要决定供应商。内容由自己决定。**

### 4. 面向智能客户端的丰富元数据
每个模型暴露完整的元数据：上下文窗口、定价层级、工具支持、流式传输、推理能力、输入/输出模态、每请求最大图像数。您的IDE可以问："只给我接受原生文件的免费视觉模型"，WallasAPI自动过滤响应。

### 5. 尊重您隐私的持久记忆
对话历史以JSON格式本地保存。可与**Obsidian**同步，适合那些活在互联笔记中的人。您的历史不会传到云端，除非您愿意。

### 6. 统一的图像、视频和语音生成
单一端点，从多个供应商创建多模态内容：
- **图像**：Gemini、Pollinations（Flux、SDXL）、HuggingFace、OpenAI DALL-E、NVIDIA NIM、本地Ollama
- **视频**：Gemini、HuggingFace Spaces
- **文本转语音（TTS）**：OpenAI、edge-tts支持多种语音

### 7. 带回退链的OCR
使用**EasyOCR** -> **Mistral** -> **Gemini** -> **本地Ollama**从图像和PDF中提取文本。如果第一个失败，尝试下一个。没有一张图像会被遗漏。

### 8. 通过Ollama实现100%私密的本地模型
在您的自有机器上完全免费且私密地运行**Llama 3、Mistral、Qwen、DeepSeek**。不需要API密钥。不需要互联网。没有人阅读您的提示。

### 9. 完整的Google集成
Drive、Calendar、Gmail均支持OAuth2。本地提醒与Google Calendar同步。项目管理支持线程、文件和元数据。

---

## 丰富元数据系统：我们建造的大脑

当您有数百个模型分散在数十个供应商中时，问题不是"我用哪个？"问题是：**"这个模型接受图像吗？它的上下文窗口是多少？免费吗？支持工具吗？我能发送原生PDF还是需要先提取文本？"**

WallasAPI自动为每个模型提供精确的元数据：

```json
{
  "context_window": 128000,
  "max_images_per_request": 5,
  "supports_tools": true,
  "supports_streaming": true,
  "supports_reasoning_stream": false,
  "input_modalities": ["text", "image", "audio"],
  "output_modalities": ["text"],
  "pricing_tier": "free",
  "provider_limits": {
    "max_images_per_request": 5,
    "supports_tools": true,
    "supports_streaming": true,
    "max_context_hint": 128000,
    "pricing": "free"
  }
}
```

### 经过17项测试验证的自动启发式方法

| 系列 | 上下文窗口 | 工具 | 流式传输 | 视觉 | 音频 | 原生文件 |
|---|---|---|---|---|---|---|
| Gemini 2.5 Pro | 1,000,000 | 是 | 是 | 是 | 是 | 是 |
| Gemini 1.5 Pro | 2,000,000 | 是 | 是 | 是 | 是 | 是 |
| GPT-4o / 4.1 | 128K - 1M | 是 | 是 | 是 | 否 | 否 |
| Claude 3 | 200,000 | 是 | 是 | 是 | 否 | 否 |
| Llama 3.3 (Groq) | 128,000 | 是 | 是 | 是 | 否 | 否（自动兼容） |
| DeepSeek R1 | 64,000 | 是 | 是 | 否 | 否 | 否 |
| Llama 3.1 (Cerebras) | 8,192 | 否 | 是 | 否 | 否 | 否 |
| Flux (Pollinations) | 不适用 | 否 | 否 | 否 | 否 | 仅生成图像 |

**工作原理：**读取模型名称，检测模式（`vision`、`vl`、`audio`、`reasoning`、`r1`），查询供应商限制，自动构建元数据。这不是魔法。这是凌晨3点在2018年笔记本上一行一行手写的代码。

---

## API端点

### 聊天补全（100%兼容OpenAI）

| 端点 | 方法 | 描述 |
|---|---|---|
| `POST /v1/chat/completions` | 聊天 | 支持流式传输的补全。支持虚拟模型：`auto`、`fast`、`standard`、`reasoning`。 |
| `POST /v1/embeddings` | 嵌入 | 多供应商路由（NVIDIA、OpenAI、Ollama）。 |
| `POST /v1/tts` | TTS | 多供应商文本转语音。 |
| `POST /v1/images/generations` | 图像 | 统一图像生成。 |
| `POST /v1/videos/generations` | 视频 | 统一视频生成。 |

### 智能元数据

| 端点 | 描述 |
|---|---|
| `GET /v1/models` | 列出带完整元数据的模型。过滤：`?pricing=free`、`?capability=vision`、`?provider=groq`、`?search=llama`、`?modality=audio`。 |
| `GET /v1/models/{id}` | 特定模型的详细元数据。 |
| `GET /v1/capabilities/summary` | 聚合摘要：多少免费、视觉、音频、推理、流式传输、生成、原生文件模型。 |
| `GET /v1/providers` | 每个供应商的全局元数据：需要认证、支持视觉/音频/原生文件、模态、定价。 |

### 高级服务

| 端点 | 描述 |
|---|---|
| `POST /v1/ocr/process` | 带回退链的OCR（EasyOCR -> Mistral -> Gemini -> Ollama）。 |
| `POST /v1/interpret` | 图像分析与文本描述。 |
| `POST /v1/sync/obsidian` | 与Obsidian同步记忆。 |
| `GET /v1/health` | 系统健康检查。 |

---

## 虚拟模型：策略，而非供应商

不再说"用gpt-4o"然后祈祷，您使用**虚拟**模型，由路由器智能解析：

| 虚拟模型 | 策略 | 典型供应商 |
|---|---|---|
| `auto` | 基于能力+速度+可用性的自动选择 | 当前最佳可用 |
| `fast` | 最小延迟，即时响应 | Groq、Cerebras |
| `standard` | 质量/速度/成本平衡 | Gemini、GPT-4o、Llama 70B |
| `reasoning` | 响应前深度思考 | DeepSeek R1、o1、o3、Gemini 2.5 Pro |

---

## 支持的供应商

| 供应商 | 能力 | 定价 |
|---|---|---|
| **Gemini** (Google) | 聊天、视觉、音频、视频、原生文件、图像/视频生成 | **免费** |
| **Groq** | 超快LLM（Llama、Mixtral） | **免费** |
| **GitHub Models** | 免费访问GPT-4o、o1、o3、Mistral、Llama、Cohere | **免费** |
| **OpenRouter** | 统一访问（Claude、DeepSeek、Qwen等） | 混合 |
| **Cohere** | Command R、Command R+ | 付费 |
| **Mistral** | Mistral Large、Medium、Small | 付费 |
| **Ollama** | 完全私密的本地模型 | **免费** |
| **NVIDIA NIM** | GPU优化LLM | 付费 |
| **Cerebras** | 专有硬件上的超快推理 | **免费** |
| **Pollinations** | 图像/视频生成（Flux等） | **免费** |
| **HuggingFace** | 社区模型 | 混合 |
| **OpenAI** | GPT-4o、GPT-4.1、嵌入、TTS、DALL-E | 付费 |

**免费 + 快速 + 私密 + 付费 = 全部共存。**您决定用哪个。WallasAPI自动决定每个时刻最佳的是哪个。

---

## 快速安装

### Windows（推荐：双击 `start.bat`）

```bash
# 1. 克隆仓库
git clone https://github.com/your-username/wallasapi.git
cd wallasapi

# 2. 双击 start.bat
#    - 自动创建虚拟环境
#    - 安装依赖
#    - 在 http://localhost:8001 启动服务器

# 或手动：
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m wallasAPI.api_server
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

服务器在 **http://localhost:8001** 启动

交互式文档（Swagger UI）：**http://localhost:8001/docs**

---

## 配置

在项目根目录创建 `.env` 文件，填入您想使用的供应商API密钥。**您不需要全部。** WallasAPI用您有的就能工作。

```env
# 免费供应商（推荐开始）
GEMINI_API_KEY=your_gemini_key_here
GROQ_API_KEY=your_groq_key_here
GITHUB_TOKEN=your_github_token_here

# 付费供应商（可选）
OPENAI_API_KEY=your_openai_key_here
OPENROUTER_API_KEY=your_openrouter_key_here
COHERE_API_KEY=your_cohere_key_here
MISTRAL_API_KEY=your_mistral_key_here
NVIDIA_API_KEY=your_nvidia_key_here

# 安全（可选，VPS部署用）
PROXY_API_KEY=your_secret_key_to_protect_endpoints

# Ollama不需要API密钥 — 本地免费运行
```

---

## 供应商注册：如何获取免费API密钥（一步步）

**重要：**每个用户必须使用**自己的**API密钥。**不要分享您的 `.env` 文件，也不要把密钥上传到GitHub。**获取免费密钥很快，并且让您完全掌控。

### 100%免费供应商（从这里开始）

| 供应商 | 用途 | 如何注册并获取密钥 |
|---|---|---|
| **Gemini (Google)** | Gemini 2.0/2.5 Pro/Flash模型，1M-2M上下文、视觉、音频、视频、原生文件 | 1. 前往 [ai.google.dev](https://ai.google.dev)<br>2. 点击 "Get API key in Google AI Studio"<br>3. 用Google账号登录<br>4. 前往 "Get API key" 标签<br>5. 点击 "Create API key"<br>6. 复制密钥粘贴到 `GEMINI_API_KEY=...` |
| **Groq** | 超快LLM（Llama 3.3 70B、Mixtral、Gemma），延迟100-300ms | 1. 前往 [console.groq.com](https://console.groq.com)<br>2. 点击 "Sign Up"（邮箱或Google/GitHub）<br>3. 前往 "API Keys" 部分<br>4. 点击 "Create API Key"<br>5. 复制密钥粘贴到 `GROQ_API_KEY=...` |
| **GitHub Models** | 免费访问GPT-4o、o1、o3、Mistral、Llama、Cohere | 1. 需要GitHub账号（免费）<br>2. 前往 [github.com/settings/tokens](https://github.com/settings/tokens)<br>3. 点击 "Generate new token (classic)"<br>4. 勾选基本权限（不需要特殊范围）<br>5. 生成并复制token<br>6. 粘贴到 `GITHUB_TOKEN=...`<br>7. 同时在模型注册：[github.com/marketplace/models](https://github.com/marketplace/models) |
| **OpenRouter** | 统一访问Claude、DeepSeek、Qwen等100+模型 | 1. 前往 [openrouter.ai](https://openrouter.ai)<br>2. 点击 "Sign Up"（邮箱或Google/GitHub/Twitter）<br>3. 侧面板前往 "Keys"<br>4. 点击 "Create Key"<br>5. 复制密钥粘贴到 `OPENROUTER_API_KEY=...`<br>6. 许多模型免费，有慷慨的速率限制 |
| **Cerebras** | Cerebras硬件上的超快推理（Llama 3.1-8B） | 1. 前往 [cloud.cerebras.ai](https://cloud.cerebras.ai)<br>2. 用邮箱注册<br>3. 前往 "API Keys" 部分<br>4. 生成新密钥<br>5. 粘贴到您的 `.env` |
| **Pollinations** | 完全免费的图像生成（Flux、SDXL）和视频 | 1. 前往 [pollinations.ai](https://pollinations.ai)<br>2. 基础使用不需要API密钥<br>3. API使用：注册并从文档获取密钥<br>4. 注意：WallasAPI使用Pollinations的公共端点，不需要认证 |
| **Ollama** | 100%私密的本地模型（Llama、Mistral、Qwen、DeepSeek） | 1. 下载 [ollama.com](https://ollama.com) 并安装<br>2. 运行 `ollama run llama3.1`<br>3. WallasAPI自动检测 `localhost:11434` 上的Ollama<br>4. **不需要API密钥 — 100%免费且私密** |

### 付费供应商（可选，如果需要更多）

| 供应商 | 用途 | 如何注册 |
|---|---|---|
| **OpenAI** | GPT-4o、GPT-4.1、DALL-E、Whisper、嵌入、TTS | [platform.openai.com](https://platform.openai.com) — 注册，添加信用卡/预付费卡 |
| **Mistral AI** | Mistral Large、Medium、Pixtral | [console.mistral.ai](https://console.mistral.ai) — 注册送$5免费初始额度 |
| **Cohere** | Command R、Command R+ | [cohere.com](https://cohere.com) — 注册送免费试用额度 |
| **NVIDIA NIM** | 企业级GPU优化LLM | [build.nvidia.com](https://build.nvidia.com) — 注册送免费初始额度 |

### 安全提示

- **永远不要将 `.env` 上传到GitHub。**使用 `.gitignore` 排除它。
- **在生产中使用环境变量**代替 `.env` 文件。
- **定期轮换密钥**通过每个供应商的控制台。
- **监控使用量**在每个供应商的仪表板中，以免超出免费限制。

仅用 **Gemini + Groq + GitHub Models**，您就能免费访问数十个极其强大的模型。从这三个开始。

---

## 快速使用

### 使用虚拟模型的基础聊天

```python
import openai

client = openai.OpenAI(
    base_url="http://localhost:8001/v1",
    api_key="anything-local"  # 或您的 PROXY_API_KEY（如果配置）
)

# 选择策略，而非供应商
response = client.chat.completions.create(
    model="auto",  # WallasAPI选择最佳可用供应商
    messages=[{"role": "user", "content": "解释广义相对论"}]
)
print(response.choices[0].message.content)
```

### 带自动回退的流式传输

```python
for chunk in client.chat.completions.create(
    model="fast",  # 优先速度（Groq、Cerebras）
    messages=[{"role": "user", "content": "你好"}],
    stream=True
):
    print(chunk.choices[0].delta.content or "", end="")
```

### 发现免费视觉模型

```bash
curl "http://localhost:8001/v1/models?pricing=free&capability=vision"
```

### 检查模型是否支持原生文件

```bash
curl "http://localhost:8001/v1/providers"
# Gemini: supports_native_files = true（直接发送PDF）
# Groq: supports_native_files = false（自动OCR）
```

### 生成图像

```python
image = client.images.generate(
    model="flux",  # Pollinations，免费
    prompt="一只宇航员猫在太空，像素艺术风格"
)
```

---

## 项目结构

```
wallasAPI/
├── api_server.py          # 带OpenAI兼容端点的FastAPI服务器
├── router.py              # 带回退的智能路由引擎
├── config.py              # 配置、元数据模式、启发式方法
├── model_fetcher.py         # 动态模型发现
├── file_utils.py           # OCR、文本提取、文件处理
├── memory.py              # 持久对话记忆
├── google_service.py      # Google OAuth2集成
├── reminders.py           # 提醒系统
├── projects.py            # 项目管理
├── settings.py            # 用户偏好
├── logger.py              # 集中日志
├── providers/             # 各个供应商
│   ├── huggingface.py
│   └── ...
├── start.bat              # Windows启动脚本（双击）
├── requirements.txt       # 依赖
├── LICENSE                # 自定义许可证
└── README.md              # 本文件
```

---

## 许可证

本项目基于自定义MIT许可证授权。

**您可以自由使用、修改、分发和在此基础上构建。**唯一的真正条件是保留对 **Willen Ponce** 作为原作者的署名。

**一个个人请求（非法律要求）：**如果您在任何项目、产品、服务或部署中使用WallasAPI —— 无论商业与否 —— 如果您能发送邮件到 **wubjak@protonmail.ch** 告诉我您正在使用WallasAPI，我将不胜感激。您不需要分享技术细节或专有信息。一句简单的 **"嘿，我在用WallasAPI做X，谢谢你的构建"** 就足以让一个在一间出租屋里用2018年笔记本构建这一切的开发者的日子变得更好。

完整文本请见 `LICENSE` 文件。

---

## 捐赠：让这个项目活下去

这个项目没有赞助商。没有硅谷投资者。没有营销团队。它只有一台2018年的笔记本、一间出租屋，以及能用的代码。

**如果WallasAPI为您节省了数小时的集成时间、帮助您构建了很酷的东西，或者您只是相信免费软件应该存在而不依赖亿万富翁公司：**

### 您的直接支持能改变一切：

- **PayPal**: [paypal.me/wubjak](https://paypal.me/wubjak)
- **Ko-fi**: [ko-fi.com/wubjak](https://ko-fi.com/wubjak) — 每一杯咖啡都算数。
- **邮箱**: wubjak@protonmail.ch

**Yape / Plin（秘鲁）— 号码：980 702 580**

<p align="center">
  <img src="https://upload.wikimedia.org/wikipedia/commons/7/76/Yape_peru_logotype.svg" width="120" alt="Yape Logo">
  <img src="https://logos-world.net/wp-content/uploads/2024/11/Plin-Interbank-Logo.png" width="120" alt="Plin Logo">
</p>

**加密钱包：**

| 货币 | 地址 |
|---|---|
| **Ethereum** | `0xDec40634014bf05A40006BA48160cddAEe1143c2` |
| **Bitcoin** | `bc1qwrr5zal3tt7f5ye0ptgy8365cc8yt64hrj7dmt` |
| **Solana** | `HrTiFtmML4NJD1b3RrjQV3e1FgaBWgpqRtR6gFphApGh` |
| **Polygon** | `0xDec40634014bf05A40006BA48160cddAEe1143c2` |
| **Tron** | `TB1sHwCo3FFaabf26AHV8VNapWUJbca299` |
| **TronLink** | `TQsXuVbnSwicRNoCEmGVdFeo86X7ey7okx` |

> *"在被赶出房子之前，为了能吃上早餐、还清债务、至少能连续睡4小时而不在梦中被债务惊醒，每一份贡献都算数。感谢您使用WallasAPI。"* — **Willen Ponce**

---

## 致谢

- 感谢FastAPI的创造者，让Python中的API变得如此美丽。
- 感谢Google、Meta、DeepSeek、Mistral，以及所有提供免费模型的供应商。
- 感谢开源社区，证明免费软件可以与任何大公司竞争。
- **感谢您**，读到这里并考虑使用WallasAPI。

---

<p align="center">
  <strong>WallasAPI</strong> — <em>一个API统治一切。<br>
  从贫困中建造，带着一无所有的人的决心。</em>
</p>
