Absolutely. Here's a complete `README.md` for your **AI-powered B2B Social Media Post Generator** FastAPI project — clearly documenting what it does, how to run it, and how each part works:

---

```markdown
# ✨ AI-Powered B2B Social Media Post Generator

This project is a minimal yet powerful **FastAPI** application that helps users generate high-quality B2B social media posts using **Google Gemini 2.5 Flash** and intelligently structured metadata.

---

## 🚀 Features

- 🎯 Structured onboarding via multiple-choice selections:
  - **Industry**
  - **Niche**
  - **Role**
  - **Pain Point**
  - **Preferred Marketing Channel**

- 💡 Free-text input for core post idea.

- 🧠 AI-powered post generation using Gemini API:
  - Insightful, context-rich post
  - Custom tone, tailored to B2B audience
  - Includes soft CTA with user contact info
  - Output returned in markdown format (title + post)

- 🧪 Test-ready endpoint via Swagger UI or cURL

- 📦 Lightweight codebase – under 3 files for clarity

---

## 🧰 Tech Stack

| Component        | Tool / Library        |
|------------------|------------------------|
| Backend Framework | [FastAPI](https://fastapi.tiangolo.com/) |
| AI Model         | Google Gemini 2.5 Flash (via API) |
| Language         | Python 3.10+           |
| Server           | Uvicorn                |
| Dev Tools        | Swagger UI, cURL       |

---

## 📂 Project Structure

```

├── main.py                # FastAPI app
├── schema.py              # Pydantic models for input validation
├── post\_generator.py      # Gemini API interaction logic
├── requirements.txt       # Python dependencies
├── README.md              # Project documentation

````

---

## 🧑‍💻 How It Works

### 1. User Input

The user selects options from the following predefined menus:

```python
INDUSTRY_OPTIONS = [
    "Tech & Software", "Health & Wellness", "Finance & FinTech",
    "Education & EdTech", "Media & Entertainment", "Retail & eCommerce",
    "Manufacturing & Logistics"
]

NICHE_OPTIONS = [
    "SaaS Tools / Platforms", "Direct-to-Consumer (DTC) Brands",
    "Content Creators / Agencies", "B2B Services / Consulting",
    "Local Businesses / Franchises", "Non-profits / NGOs",
    "Government / Public Services"
]

ROLE_OPTIONS = [
    "Founders / CXOs", "Marketing Heads / CMOs", "Product Managers",
    "Developers / Engineers", "HR / Talent Heads", "Students / Learners",
    "Influencers / Key Opinion Leaders (KOLs)"
]

PAINPOINT_OPTIONS = [
    "Scaling Revenue", "Increasing Visibility / Brand", "Generating Leads",
    "Automating Operations", "Hiring & Retaining Talent", "Entering New Markets",
    "Cutting Costs / Efficiency"
]

CHANNEL_OPTIONS = [
    "LinkedIn", "Twitter (X)", "Email Newsletters", "Industry Forums / Reddit",
    "YouTube / Podcasts", "Conferences / Events", "Direct Sales / Referrals"
]
````

Plus, the user provides:

* `idea`: A free-text summary of their post concept.
* `contact_info`: Email or contact link for the soft CTA.

---

### 2. AI Prompting

The app crafts a prompt like:

```text
You are a B2B marketing assistant writing thought-leadership posts.

Write a professional social media post for:
- Industry: Tech & Software
- Niche: SaaS Tools / Platforms
- Role: Founders / CXOs
- Pain Point: Generating Leads
- Preferred Channel: LinkedIn

Core idea: how automation can unlock growth in early stage SaaS startups

Instructions:
- Start with a catchy title.
- Then write a short, insightful post (under 300 words).
- Subtly weave in the above details (user selected options) as naturally as possible — don't list them.
- End with a soft CTA including this contact info: founder@vertos.ai.
- Keep tone expert, authentic, and relevant to the industry.
Return only the title and post text in markdown format.
```

---

## ⚙️ How to Run

### 1. Clone the repo

```bash
git clone this repo
cd to the file location
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Add your Gemini API Key

Create a `.env` file in the root and add:

```
GEMINI_API_KEY=your_gemini_api_key_here
```

Or modify `post_generator.py` to hardcode it for now:

```python
api_key = "your_api_key"
```

### 4. Run the server

```bash
uvicorn main:app --reload
```

Then visit:

```
http://localhost:8000/docs
```

---

## 🔥 Test the Endpoint

### Swagger UI

Go to `/docs`, click on `/generate_post`, and try:

```json
{
  "industry": "Tech & Software",
  "niche": "SaaS Tools / Platforms",
  "role": "Founders / CXOs",
  "pain_point": "Generating Leads",
  "channel": "LinkedIn",
  "idea": "how automation can unlock growth in early stage SaaS startups",
  "contact_info": "founder@vertos.ai"
}
```

### cURL (optional)

```bash
curl -X POST "http://localhost:8000/generate_post" \
  -H "Content-Type: application/json" \
  -d '{
    "industry": "Tech & Software",
    "niche": "SaaS Tools / Platforms",
    "role": "Founders / CXOs",
    "pain_point": "Generating Leads",
    "channel": "LinkedIn",
    "idea": "how automation can unlock growth in early stage SaaS startups",
    "contact_info": "founder@vertos.ai"
  }'
```

---

## 💡 Future Improvements

* Store generated posts in a database
* User accounts & profiles
* Fine-tuned Gemini or open-source LLM alternatives
* A React frontend or CLI wrapper
* Feed ranking using sentence-transformer similarity

---

## 👨‍💼 Built For

This is ideal for:

* B2B founders, consultants, or agencies
* Content marketers and growth strategists
* Early-stage startup teams scaling organic visibility

---

## 🧠 Credits

Built with ❤️ by [Sri Krishna]
