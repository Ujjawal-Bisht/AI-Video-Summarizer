from __future__ import annotations

import os
import re

from dotenv import load_dotenv
from flask import Flask, render_template, request
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

import google.generativeai as genai


load_dotenv()

app = Flask(__name__)


def get_video_id(url: str) -> str:
    url = (url or "").strip()
    if not url:
        raise ValueError("Please paste a YouTube URL.")

    # youtu.be/<id>
    m = re.search(r"youtu\.be/([A-Za-z0-9_-]{6,})", url)
    if m:
        return m.group(1)

    # youtube.com/watch?v=<id>
    m = re.search(r"[?&]v=([A-Za-z0-9_-]{6,})", url)
    if m:
        return m.group(1)

    # youtube.com/shorts/<id>
    m = re.search(r"youtube\.com/shorts/([A-Za-z0-9_-]{6,})", url)
    if m:
        return m.group(1)

    raise ValueError("Invalid YouTube URL.")


def fetch_transcript_text(video_id: str) -> str:
    # Try common language preferences, then fallback to Hindi if that's all available.
    preferred_languages = ("en", "en-US", "en-GB", "hi", "hi-IN")

    # Support both old and new youtube-transcript-api versions.
    if hasattr(YouTubeTranscriptApi, "fetch"):
        transcript_items = YouTubeTranscriptApi().fetch(video_id, languages=preferred_languages)
        text_parts = [getattr(item, "text", "").strip() for item in transcript_items]
        return " ".join(part for part in text_parts if part).strip()

    if hasattr(YouTubeTranscriptApi, "get_transcript"):
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=list(preferred_languages))
        return TextFormatter().format_transcript(transcript).strip()

    raise RuntimeError("Unsupported youtube-transcript-api version.")


def build_prompt(transcript_text: str) -> str:
    return (
        "**Create a summary of a youtube video based on provided transcript.**\n\n"
        "The goal is to extract as much value as possible with clarity and insights over quantity.\n\n"
        "Provide the answer in a raw Markdown syntax, suitable for Notion, with no extra commentary or explanations.\n\n"
        "Highlight the following sections clearly:\n"
        "- The Main Message (the core idea of the video)\n"
        "- 3–5 Key Takeaways\n"
        "- Short Overall Summary\n"
        "- Clear Steps to implement the ideas taught in the video (If applicable)\n\n"
        "Here is the Transcript:\n"
        f"{transcript_text}"
    )


def summarize_with_gemini(transcript_text: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GEMINI_API_KEY in your environment (.env).")

    genai.configure(api_key=api_key)
    model_name = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash-lite")
    model = genai.GenerativeModel(model_name=model_name)

    prompt = build_prompt(transcript_text)
    response = model.generate_content(prompt)
    return (getattr(response, "text", None) or "").strip()


@app.get("/")
def index():
    return render_template("index.html", summary=None, error=None, url="")


@app.post("/summarize")
def summarize():
    url = request.form.get("url", "").strip()
    try:
        video_id = get_video_id(url)
        transcript_text = fetch_transcript_text(video_id)
        summary = summarize_with_gemini(transcript_text)
        if not summary:
            raise RuntimeError("Gemini returned an empty response. Try again.")
        return render_template("index.html", summary=summary, error=None, url=url)
    except Exception as e:
        message = str(e)
        if "No transcripts were found for any of the requested language codes" in message:
            message = (
                "Transcript is not available in the preferred languages for this video. "
                "Try another video or one with captions/subtitles enabled."
            )
        return render_template("index.html", summary=None, error=message, url=url), 400


if __name__ == "__main__":
    app.run(debug=True)
