<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/FastAPI-0.115+-green.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/Providers-12+-orange.svg" alt="12+ 프로바이더">
  <img src="https://img.shields.io/badge/Models-100+-purple.svg" alt="100+ 모델">
</p>

<h1 align="center">WallasAPI</h1>

<p align="center"><strong>최종 멀티-프로바이더 AI 라우팅 엔진</strong></p>

<p align="center"><em>땀과 결단, 그리고 2018년 노트북으로, 임대한 방에서, <strong>Willen Ponce</strong>가 제작</em></p>

---

## WallasAPI가 존재하는 이유: 중요한 이야기

저는 MacBook Pro M4와 함께 태어나지 않았습니다. 실리콘 밸리 투자자들이 자금을 지원하는 클라우드 서버도 없습니다. 제 뒤에는 50명의 엔지니어 팀도 없습니다. **제가 가진 것은 2018년 노트북, 제 것이 아닌 임대 방, 그리고 집착입니다: 빈곤한 상황에서도 기업과 경쟁할 수 있는 무언가를 만들 수 있다는 것을 증명하겠다는 집착입니다.**

WallasAPI는 월세 걱정, 다음 식사, 연속으로 최소 4시간 잠들 수 있는지, 잠에서 깨어나도 빚이 얼마나 되는지 생각하지 않고 살 수 있는지——그 사이에 훔친 시간 속에서 태어났습니다. 비싼 API를 지불할 돈이 없었습니다. 저를 지지하는 회사도 없었습니다. 오직 하나의 강박적인 질문만 있었습니다:

> **"세상에는 많은 모델들이 있고, 많은 것들이 무료이며, 특정 작업에 더 나은데, 왜 단일 AI 프로바이더에 의존해야 합니까?"**

그래서 저는 만들었습니다. **한 줄 한 줄의 Python. 화려한 프레임워크 없이. 팀 없이. 투자자 없이.** 순수한 코드, 스마트한 휴리스틱, 그리고 작동하는 무언가를 만들어야 한다는 절박한 필요성만으로.

**WallasAPI는 단순한 소프트웨어가 아닙니다. 기술적 생존입니다.** OpenAI가 다운되었을 때, Claude API 키가 만료되었을 때, 좋아하는 프로바이더가 가격을 올릴 때——당신을 버리지 않는 시스템입니다.

---

## WallasAPI란?

WallasAPI는 **통합 라우팅 엔진**으로, **하나의 OpenAI 호환 API**를 통해 애플리케이션, IDE 또는 에이전트를 **12개 이상의 AI 프로바이더**에 연결합니다.

프롬프트를내면 WallasAPI는:
1. **콘텐츠를 분석** (텍스트, 이미지, 오디오, PDF, 비디오)
2. **기능, 속도, 가용성, 비용을 기반으로 최적의 프로바이더를 선택**
3. **요청을 자동으로 라우팅**
4. **주 프로바이더가 실패하면** 다음으로 투명하게 폴백
5. **OpenAI 호환 형식으로 응답 반환**, 요청 시 스트리밍 포함

**기존 코드는 변경 없이 작동합니다.** 기본 URL만 변경하면 됩니다.

---

## 주요 기능

- **지능형 멀티-프로바이더 라우팅 + 자동 폴백**
- **완전한 투명성의 실시간 스트리밍**
- **멀티모달 지원** — 텍스트, 이미지, 오디오, 비디오, PDF
- **풍부한 메타데이터** — 컨텍스트 윈도우, 가격대, 도구, 스트리밍, 모달리티
- **영구 메모리** — 로컬 JSON 기록, Obsidian과 동기화 가능
- **통합 생성** — 이미지, 비디오, TTS를 여러 프로바이더에서
- **폴백 체인이 있는 OCR** — EasyOCR → Mistral → Gemini → 로컬 Ollama
- **100% 프라이빗 로컬 모델** — Ollama 통해
- **완전한 Google 통합** — Drive, Calendar, Gmail (OAuth2 지원)

---

## API 엔드포인트

| 엔드포인트 | 메서드 | 설명 |
|---|---|---|
| `POST /v1/chat/completions` | 채팅 | 스트리밍이 있는 컴플리션. 가상 모델: `auto`, `fast`, `standard`, `reasoning`. |
| `POST /v1/embeddings` | 임베딩 | 멀티-프로바이더 라우팅. |
| `POST /v1/tts` | TTS | 텍스트 음성 변환. |
| `POST /v1/images/generations` | 이미지 | 통합 이미지 생성. |
| `POST /v1/videos/generations` | 비디오 | 통합 비디오 생성. |
| `GET /v1/models` | 목록 | 완전한 메타데이터가 있는 모델. 필터: `?pricing=free`, `?capability=vision`. |
| `GET /v1/models/{id}` | 상세 | 특정 모델의 상세 메타데이터. |
| `GET /v1/capabilities/summary` | 요약 | 무료, 비전, 오디오, 추론 등의 수. |
| `GET /v1/providers` | 프로바이더 | 프로바이더별 글로벌 메타데이터. |

---

## 빠른 설치

### Windows (권장: `start.bat` 더블클릭)

```bash
git clone https://github.com/your-username/wallasapi.git
cd wallasapi
# start.bat 더블클릭
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

서버는 **http://localhost:8001** 에서 시작

대화형 문서: **http://localhost:8001/docs**

---

## 설정

사용하려는 프로바이더의 API 키를 `.env` 파일에 작성하세요. **모두 필요하지 않습니다.**

```env
# 무료 프로바이더 (시작에 권장)
GEMINI_API_KEY=your_key_here
GROQ_API_KEY=your_key_here
GITHUB_TOKEN=your_token_here

# 유료 프로바이더 (선택)
OPENAI_API_KEY=your_key_here
OPENROUTER_API_KEY=your_key_here
```

---

## 라이선스

사용자 정의 MIT 라이선스. **Willen Ponce**에 대한 귀속을 유지하세요.

**개인적 요청:** WallasAPI를 사용하는 경우 **wubjak@protonmail.ch**로 이메일을 보내 주세요. "안녕하세요, WallasAPI를 사용하고 있습니다, 만들어 주셔서 감사합니다"만으로도 2018년 노트북으로 이것을 만든 개발자의 하루를 좋게 만들 수 있습니다.

자세한 내용은 `LICENSE` 파일을 참조하세요.

---

## 기부: 이것을 살아있게 유지하기

이 프로젝트에는 스폰서가 없습니다. 실리콘 밸리 투자자도 없습니다. 2018년 노트북, 임대 방, 그리고 작동하는 코드만 있습니다.

**WallasAPI가 통합 시간을 절약하거나 멋진 것을 만드는 데 도움이 된 경우:**

- **PayPal** : [paypal.me/wubjak](https://paypal.me/wubjak)
- **Ko-fi** : [ko-fi.com/wubjak](https://ko-fi.com/wubjak)
- **Email** : wubjak@protonmail.ch

**Yape / Plin (페루) — 번호: 980 702 580**

<p align="center">
  <img src="https://upload.wikimedia.org/wikipedia/commons/7/76/Yape_peru_logotype.svg" width="120" alt="Yape Logo">
  <img src="https://logos-world.net/wp-content/uploads/2024/11/Plin-Interbank-Logo.png" width="120" alt="Plin Logo">
</p>

**암호화폐 지갑:**

| 통화 | 주소 |
|---|---|
| **Ethereum** | `0xDec40634014bf05A40006BA48160cddAEe1143c2` |
| **Bitcoin** | `bc1qwrr5zal3tt7f5ye0ptgy8365cc8yt64hrj7dmt` |
| **Solana** | `HrTiFtmML4NJD1b3RrjQV3e1FgaBWgpqRtR6gFphApGh` |
| **Polygon** | `0xDec40634014bf05A40006BA48160cddAEe1143c2` |
| **Tron** | `TB1sHwCo3FFaabf26AHV8VNapWUJbca299` |
| **TronLink** | `TQsXuVbnSwicRNoCEmGVdFeo86X7ey7okx` |

> *"집에서 쫓겨나기 전에, 아침 식사를 하고, 빚을 갚고, 빚에 대해 깨어나지 않고 최소 4시간 연속으로 잘 수 있도록——모든 기여가 소중합니다. WallasAPI를 사용해 주셔서 감사합니다."* — **Willen Ponce**

---

<p align="center">
  <strong>WallasAPI</strong> — <em>모든 것을 지배하는 하나의 API.<br>
  잃을 것이 없는 자의 결단으로, 빈곤 속에서 구축되었습니다.</em>
</p>
