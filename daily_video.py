"""
Daily Learn Bot
Calls Claude API to recommend a 10–25 minute educational YouTube video,
then emails the recommendation via Gmail SMTP.
"""

import os
import json
import smtplib
import urllib.request
import urllib.error
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import anthropic
import yaml


# ── Load config ──
CONFIG_PATH = Path(__file__).parent / "config.yaml"
with open(CONFIG_PATH) as f:
    config = yaml.safe_load(f)

CATEGORIES = config["categories"]
MIN_DURATION = config.get("min_duration", 10)
MAX_DURATION = config.get("max_duration", 25)
PREFERRED_CHANNELS = config.get("preferred_channels", [])
EMAIL_SUBJECT_PREFIX = config.get("email_subject_prefix", "🎓 Daily Learn")

# ── Secrets from environment variables ──
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
GMAIL_ADDRESS = os.environ["GMAIL_ADDRESS"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL", GMAIL_ADDRESS)


def get_todays_category() -> str:
    """Pick a category based on the day of year so it rotates predictably."""
    day_of_year = datetime.now().timetuple().tm_yday
    idx = day_of_year % len(CATEGORIES)
    return CATEGORIES[idx]


MAX_RETRIES = 3


def is_video_available(url: str) -> bool:
    """Check if a YouTube video is available using the oEmbed API."""
    oembed_url = f"https://www.youtube.com/oembed?url={url}&format=json"
    try:
        req = urllib.request.Request(oembed_url, headers={"User-Agent": "DailyLearnBot/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        return False


def get_video_recommendation(category: str, excluded_urls: list[str] | None = None) -> dict:
    """Ask Claude to recommend a specific YouTube video."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    channels_str = ", ".join(PREFERRED_CHANNELS)

    exclusion_note = ""
    if excluded_urls:
        exclusion_note = (
            "\n\nIMPORTANT: The following URLs were already suggested but are unavailable. "
            f"Do NOT recommend any of these:\n" + "\n".join(f"- {u}" for u in excluded_urls)
        )

    prompt = f"""You are a curator for a daily learning habit. Today's category is: {category}

Recommend ONE specific YouTube video that:
- Is between {MIN_DURATION} and {MAX_DURATION} minutes long
- Actually exists on YouTube (use a real, well-known video you're confident about)
- Teaches something genuinely interesting that a curious person would enjoy — not limited to any specific field
- Leaves the viewer more educated about the world, teaches a practical skill, or provides genuine inspiration
- Comes from a reputable channel (think: {channels_str}, etc. — but not limited to these)
{exclusion_note}
Respond in JSON only. No markdown, no backticks, no preamble. Just the JSON object:
{{
    "title": "Exact video title",
    "channel": "Channel name",
    "url": "https://www.youtube.com/watch?v=VIDEO_ID",
    "duration_minutes": 18,
    "one_liner": "One sentence on what you'll learn",
    "category": "{category}",
    "why_watch": "2-3 sentences on why this will leave you more knowledgeable, skilled, or inspired"
}}"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = message.content[0].text.strip()
    response_text = response_text.replace("```json", "").replace("```", "").strip()
    return json.loads(response_text)


def send_email(video: dict) -> None:
    """Send the recommendation as a nicely formatted email."""
    today = datetime.now().strftime("%A, %B %d")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"{EMAIL_SUBJECT_PREFIX}: {video['title']}"
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = RECIPIENT_EMAIL

    # Plain text version
    plain = f"""Daily Learn — {today}
Category: {video['category']}

{video['title']}
by {video['channel']} ({video['duration_minutes']} min)

{video['one_liner']}

{video['why_watch']}

Watch: {video['url']}
"""

    # HTML version
    html = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 500px; margin: 0 auto; padding: 20px;">
        <p style="color: #888; font-size: 13px; margin-bottom: 4px;">{today} · {video['category']}</p>
        <h1 style="font-size: 22px; margin: 0 0 8px 0; color: #1a1a1a;">{video['title']}</h1>
        <p style="color: #555; font-size: 14px; margin: 0 0 16px 0;">by {video['channel']} · {video['duration_minutes']} min</p>
        <p style="font-size: 16px; color: #333; line-height: 1.5; margin-bottom: 12px;"><strong>{video['one_liner']}</strong></p>
        <p style="font-size: 15px; color: #444; line-height: 1.6; margin-bottom: 24px;">{video['why_watch']}</p>
        <a href="{video['url']}" style="display: inline-block; background: #FF0000; color: white; text-decoration: none; padding: 12px 28px; border-radius: 8px; font-weight: 600; font-size: 15px;">▶ Watch Now</a>
        <hr style="border: none; border-top: 1px solid #eee; margin-top: 32px;">
        <p style="color: #aaa; font-size: 12px;">{EMAIL_SUBJECT_PREFIX} Bot · Powered by Claude</p>
    </div>
    """

    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, RECIPIENT_EMAIL, msg.as_string())


def main():
    category = get_todays_category()
    print(f"📚 Today's category: {category}")

    excluded_urls = []
    video = None

    for attempt in range(1, MAX_RETRIES + 1):
        candidate = get_video_recommendation(category, excluded_urls or None)
        print(f"🎬 Attempt {attempt}: {candidate['title']}")
        print(f"🔗 {candidate['url']}")

        if is_video_available(candidate["url"]):
            print("✅ Video verified as available")
            video = candidate
            break

        print("⚠️  Video unavailable, retrying...")
        excluded_urls.append(candidate["url"])

    if video is None:
        print("❌ Could not find an available video after all retries — sending best candidate")
        video = candidate

    send_email(video)
    print(f"✅ Email sent to {RECIPIENT_EMAIL}")


if __name__ == "__main__":
    main()
