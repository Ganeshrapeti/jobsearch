import requests
import smtplib
import os
import csv
from email.message import EmailMessage
from datetime import datetime
from bs4 import BeautifulSoup  # pip install beautifulsoup4

# ---- Config ----
SEARCH_QUERY = '"Angular developer" ("3 years" OR "3 yrs" OR "3+ years") India site:naukri.com OR site:linkedin.com OR site:indeed.com'
MAX_RESULTS = 10

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = os.getenv("SMTP_USER")   # sender email
SMTP_PASS = os.getenv("SMTP_PASS")   # app password
EMAIL_TO   = os.getenv("EMAIL_TO")   # recipient email

# ---- Search via DuckDuckGo HTML ----
def search_jobs(query, max_results=10):
    url = f"https://html.duckduckgo.com/html/?q={query}"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    results = []
    for res in soup.select(".result__body"):
        title_tag = res.select_one(".result__a")
        snippet_tag = res.select_one(".result__snippet")
        if not title_tag:
            continue

        title = title_tag.get_text(strip=True)
        link = title_tag["href"]
        snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""

        # ✅ Experience match check (3 years variations)
        experience_keywords = ["3 years", "3 yrs", "3+ years"]
        text_to_check = f"{title} {snippet}".lower()
        experience_match = "Yes" if any(kw in text_to_check for kw in experience_keywords) else "No"

        results.append({
            "title": title,
            "snippet": snippet,
            "link": link,
            "experience_match": experience_match
        })

        if len(results) >= max_results:
            break

    return results

# ---- Save to CSV ----
def results_to_csv(results, filename):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "snippet", "link", "experience_match"])
        writer.writeheader()
        writer.writerows(results)

# ---- Email ----
def send_email(subject, body, attachment_path=None):
    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = EMAIL_TO
    msg["Subject"] = subject
    msg.set_content(body)

    if attachment_path and os.path.exists(attachment_path):
        with open(attachment_path, "rb") as f:
            data = f.read()
        msg.add_attachment(
            data,
            maintype="application",
            subtype="octet-stream",
            filename=os.path.basename(attachment_path)
        )

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)

# ---- Main ----
def main():
    print(f"Running search at {datetime.now().isoformat()}")
    results = search_jobs(SEARCH_QUERY, MAX_RESULTS)

    if not results:
        body = "No job results found today."
        csv_path = None
    else:
        lines = ["Today's Angular (3 yrs) Job Search Results:\n"]
        for i, r in enumerate(results, start=1):
            lines.append(f"{i}. {r['title']}")
            lines.append(f"   Experience Match: {r['experience_match']}")
            if r['snippet']:
                lines.append(f"   {r['snippet']}")
            lines.append(f"   {r['link']}\n")
        body = "\n".join(lines)

        # save csv
        csv_path = f"job_results_{datetime.now().strftime('%Y%m%d')}.csv"
        results_to_csv(results, csv_path)

    send_email("Daily Angular Job Search Results (3 yrs)", body, csv_path)
    print("Email sent!")

if __name__ == "__main__":
    main()

