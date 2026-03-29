# 🎓 Daily Learn Bot

A Python script that runs every weekday at lunchtime via GitHub Actions. It asks Claude to recommend a ~20-minute educational YouTube video on a rotating topic, then emails it to you with a clean, formatted message.

## How It Works

1. **GitHub Actions** triggers the script Monday–Friday at 12:00 PM Mountain Time
2. **Claude API** picks a video recommendation based on today's rotating category
3. **Gmail SMTP** sends you a formatted email with the video title, summary, and a "Watch Now" link

Categories rotate daily across 20 topics: science, history, economics, psychology, AI/tech, geopolitics, business strategy, philosophy, neuroscience, marketing psychology, and more.

---

## Setup (5 minutes)

### Step 1: Create a Gmail App Password

You can't use your regular Gmail password — Google requires an "App Password" for SMTP.

1. Go to [myaccount.google.com](https://myaccount.google.com)
2. Security → 2-Step Verification (enable if not already on)
3. Search for "App Passwords" in your Google Account settings
4. Create a new app password — name it something like "Daily Learn Bot"
5. Copy the 16-character password (you won't see it again)

### Step 2: Get an Anthropic API Key

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Create an API key
3. Add some credits ($5 is plenty — this costs ~$0.01/day)

### Step 3: Create the GitHub Repo

1. Create a new GitHub repository (can be private)
2. Push this project to the repo:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/daily-learn-bot.git
   git push -u origin main
   ```

### Step 4: Add Secrets to GitHub

Go to your repo → Settings → Secrets and variables → Actions → New repository secret

Add these 4 secrets:

| Secret Name         | Value                              |
|---------------------|------------------------------------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key             |
| `GMAIL_ADDRESS`     | Your Gmail address                 |
| `GMAIL_APP_PASSWORD`| The 16-char app password from Step 1 |
| `RECIPIENT_EMAIL`   | The email to receive videos (can be the same as GMAIL_ADDRESS) |

### Step 5: Test It

1. Go to Actions tab in your repo
2. Click "Daily Learn Bot" workflow
3. Click "Run workflow" → "Run workflow"
4. Check your email!

---

## Customization

### Change the schedule
Edit `.github/workflows/daily_learn.yml` — the cron is in UTC:
- `"0 18 * * 1-5"` = 12:00 PM Mountain (UTC-6)
- `"0 17 * * 1-5"` = 12:00 PM Central (UTC-5)
- `"0 16 * * 1-5"` = 12:00 PM Eastern (UTC-4, during daylight saving)

### Change the topics
Edit the `CATEGORIES` list in `daily_video.py`. Add, remove, or reorder however you want.

### Change the video length
Edit the prompt in `get_video_recommendation()` — change "15 and 30 minutes" to whatever range you prefer.

---

## Cost

- **GitHub Actions**: Free (you get 2,000 minutes/month on free tier; this uses ~1 min/day)
- **Claude API**: ~$0.01/day (~$0.20/month)
- **Gmail SMTP**: Free

---

## Troubleshooting

**Email not sending?**
- Double-check the Gmail App Password (not your regular password)
- Make sure 2-Step Verification is enabled on your Google account
- Check the Actions tab for error logs

**Bad video recommendations?**
- Claude recommends real videos it's confident about, but occasionally a link might be outdated
- You can tweak the prompt to add/remove preferred channels

**Wrong time?**
- GitHub Actions cron uses UTC — adjust accordingly for your timezone
- Note: GH Actions can run up to ~15 min late on scheduled jobs (this is normal)
