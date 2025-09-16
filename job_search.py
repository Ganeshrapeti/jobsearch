import requests
import smtplib
import os
import csv
from email.message import EmailMessage
from datetime import datetime

# ---- Config ----
SEARCH_QUERY = "Angular developer 3.5 years site:naukri.com OR site:linkedin.com OR site:indeed.com India"
MAX_RESULTS = 10

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = os.getenv("SMTP_USER")   # your email
SMTP_PASS = os.getenv("SMTP_PASS")   # app password
EMAIL_TO   = os.getenv("EMAIL_TO")   # recipient email

# ---- Simple Web Search (DuckDuckGo HTML scraping) ----
def search_jobs(query, max_results=10):
    url = f"https://duckduckgo.com/html/?q={query}"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    text = resp.text

    results = []
    for line in text.split('href="')[1:]:
        link = line.split('"')[0]
        if link.startswith("http") and "duckduckgo.com" not in link:
            results.append({"link": link})
        if len(results) >= max_results:
            break
    return results

# ---- Save to CSV ----
def results_to_csv(results, filename):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["link"])
        writer.writeheader()
        writer.writerows(results)

# ---- Email ----
def send_email(subject, body, attachment_path=None):
    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = EMAIL_TO
    msg["Subject"] = subject
    msg.set_content(body)

    # Attach CSV if exists
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
        lines = ["Today's job search results:\n"]
        for i, r in enumerate(results, start=1):
            lines.append(f"{i}. {r['link']}")
        body = "\n".join(lines)

        # save csv
        csv_path = f"job_results_{datetime.now().strftime('%Y%m%d')}.csv"
        results_to_csv(results, csv_path)

    send_email("Daily Angular Job Search Results", body, csv_path)
    print("Email sent!")

if __name__ == "__main__":
    main()
