"""
Daily Learn Bot
Calls Claude API to recommend a 10–25 minute educational YouTube video,
then emails the recommendation via Gmail SMTP.
"""

import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import anthropic


# ── Config from environment variables ──
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
GMAIL_ADDRESS = os.environ["GMAIL_ADDRESS"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL", GMAIL_ADDRESS)  # defaults to self

# ── Topic rotation ──
CATEGORIES = [
    "behavioral economics or decision science",
    "systems thinking or complex adaptive systems",
    "longevity, healthspan, or performance optimization",
    "philosophy of mind or consciousness",
    "negotiation, persuasion, or deal structure",
    "geopolitics or international relations",
    "AI, machine learning, or emerging tech",
    "history (a specific event, person, or era that changed everything)",
    "neuroscience or how the brain works",
    "business strategy, moats, or competitive dynamics",
    "space exploration or astronomy",
    "psychology of motivation, habits, or identity",
    "engineering or how things are built",
    "game theory or strategic decision-making",
    "physics or how the universe works",
    "personal finance, investing, or wealth building",
    "environmental science, energy, or climate",
    "design thinking or problem-solving frameworks",
    "sociology, culture, or how societies evolve",
    "investigative journalism or documentary-style deep dives",
]


def get_todays_category() -> str:
    """Pick a category based on the day of year so it rotates predictably."""
    day_of_year = datetime.now().timetuple().tm_yday
    idx = day_of_year % len(CATEGORIES)
    return CATEGORIES[idx]


def get_video_recommendation(category: str) -> dict:
    """Ask Claude to recommend a specific YouTube video."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""You are a curator for a daily learning habit. Today's category is: {category}

Recommend ONE specific YouTube video that:
- Is between 10 and 25 minutes long
- Actually exists on YouTube (use a real, well-known video you're confident about)
- Teaches something genuinely interesting that a curious person would enjoy — not limited to any specific field
- Leaves the viewer more educated about the world, teaches a practical skill, or provides genuine inspiration
- Comes from a reputable channel (think: Veritasium, Kurzgesagt, Wendover Productions, 3Blue1Brown, Half as Interesting, ColdFusion, Johnny Harris, Ali Abdaal, Polymatter, Real Engineering, Tom Scott, MKBHD, Lenny's Podcast, How Money Works, Economics Explained, Crash Course, etc. — but not limited to these)

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
    # Clean potential markdown fences
    response_text = response_text.replace("```json", "").replace("```", "").strip()
    return json.loads(response_text)


def send_email(video: dict) -> None:
    """Send the recommendation as a nicely formatted email."""
    today = datetime.now().strftime("%A, %B %d")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🎓 Daily Learn: {video['title']}"
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
        <p style="color: #aaa; font-size: 12px;">Daily Learn Bot · Powered by Claude</p>
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

    video = get_video_recommendation(category)
    print(f"🎬 Recommended: {video['title']} ({video['duration_minutes']} min)")
    print(f"🔗 {video['url']}")

    send_email(video)
    print(f"✅ Email sent to {RECIPIENT_EMAIL}")


if __name__ == "__main__":
    main()
