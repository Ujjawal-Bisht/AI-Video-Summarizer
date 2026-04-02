# Video Summarizer (Flask)

Simple Flask app that:
- takes a YouTube URL
- fetches the transcript
- asks Gemini for a Markdown summary

## Setup

Create a virtual environment (recommended), then install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file (copy from `.env.example`) and set:

- `GEMINI_API_KEY`

## Run

```bash
python app.py
```

Open the URL shown in your terminal (usually `http://127.0.0.1:5000`).

## Notes

- If a video has no transcript available (or is disabled), transcript fetch will fail.
- The output is Markdown text intended for Notion / Markdown editors.
