import yfinance as yf
import schedule
import time
from datetime import datetime, time as dtime
import pytz
import smtplib
from email.mime.text import MIMEText

# ---------------------------------------------------------
# EMAIL SENDER
# ---------------------------------------------------------
def send_email(subject, body):
    sender = "sin.golbarg@gmail.com"
    password = "zwhc njll xaal bbtm"   # Gmail App Password

    receivers = [
        "sin.golbarg@gmail.com"
    ]

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(receivers)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.sendmail(sender, receivers, msg.as_string())


# ---------------------------------------------------------
# WEEKEND CHECK
# ---------------------------------------------------------
def is_weekend():
    tz = pytz.timezone("America/Toronto")
    return datetime.now(tz).weekday() >= 5


# ---------------------------------------------------------
# MARKET HOURS CHECK (TSX)
# ---------------------------------------------------------
def market_is_open():
    tz = pytz.timezone("America/Toronto")
    now = datetime.now(tz).time()
    return dtime(9, 30) <= now <= dtime(16, 0)


# ---------------------------------------------------------
# STOCK MODULE
# ---------------------------------------------------------
def get_price(ticker):
    return yf.Ticker(ticker).fast_info["last_price"]


# ---------------------------------------------------------
# STEP DECISION
# ---------------------------------------------------------
def step_decision(price, I7, F7, label):
    change_ratio = (price - I7) / I7

    if price > I7 and change_ratio > 0.05:
        amount = change_ratio * F7
        return f"Step Decision {label}: Sell {amount:.2f} — Price: {price} — Change ratio: {change_ratio:.4f}"

    if change_ratio > -0.05:
        return f"Step Decision {label}: Do nothing — Price: {price} — Change ratio: {change_ratio:.4f}"

    dev = I7 - price
    threshold = I7 / 20
    unit = F7 / 15

    if dev <= 2 * threshold:
        qty = 1
    elif dev <= 3 * threshold:
        qty = 2
    else:
        qty = 3

    return f"Step Decision {label}: Buy {qty} {unit:.2f} — Price: {price} — Change ratio: {change_ratio:.4f}"


# ---------------------------------------------------------
# INVEST DECISION
# ---------------------------------------------------------
def invest_decision(price, H7, label):
    if price >= H7 * 1.1:
        return f"Invest Decision {label}: BUY 100 (STEP 1) — Price: {price}"
    else:
        return f"Invest Decision {label}: HOLD — Price: {price}"


# ---------------------------------------------------------
# RUN DECISIONS FOR BOTH STOCKS
# ---------------------------------------------------------
def run_all_decisions():
    # SHOP
    shop_price = get_price("SHOP.TO")
    shop_step = step_decision(shop_price, 159, 500, "SHOP")
    shop_invest = invest_decision(shop_price, 159, "SHOP")

    # RBC
    rbc_price = get_price("RY.TO")
    rbc_step = step_decision(rbc_price, 271, 500, "RBC")
    rbc_invest = invest_decision(rbc_price, 262, "RBC")

    body = f"{shop_step}\n{shop_invest}\n\n{rbc_step}\n{rbc_invest}"
    return body


# ---------------------------------------------------------
# DAILY SUMMARY BODY (NEW)
# ---------------------------------------------------------
def daily_summary_body():
    tz = pytz.timezone("America/Toronto")
    today = datetime.now(tz).strftime("%Y-%m-%d")

    shop_price = get_price("SHOP.TO")
    rbc_price = get_price("RY.TO")

    shop_change = round((shop_price - 159) / 159 * 100, 2)
    rbc_change = round((rbc_price - 271) / 271 * 100, 2)

    return f"""
📊 DAILY SUMMARY — {today}

SHOP.TO closing price: {shop_price}
RBC.TO closing price:  {rbc_price}

Performance vs initial:
- SHOP: {shop_change}%
- RBC:  {rbc_change}%

Decisions:
{run_all_decisions()}
"""


# ---------------------------------------------------------
# MARKET OPEN TRIGGER
# ---------------------------------------------------------
market_open_email_sent = False

def check_market_open_trigger():
    global market_open_email_sent

    if is_weekend():
        market_open_email_sent = False
        return

    if market_is_open() and not market_open_email_sent:
        body = run_all_decisions()
        send_email("Market Open — SHOP + RBC Update", body)
        print("Market opened — email sent:", body)
        market_open_email_sent = True

    if not market_is_open():
        market_open_email_sent = False


# ---------------------------------------------------------
# MARKET CLOSE TRIGGER
# ---------------------------------------------------------
market_close_email_sent = False

def check_market_close_trigger():
    global market_close_email_sent

    if is_weekend():
        market_close_email_sent = False
        return

    tz = pytz.timezone("America/Toronto")
    now = datetime.now(tz).time()

    if now >= dtime(16, 0) and not market_close_email_sent:
        body = run_all_decisions()
        send_email("Market Close — SHOP + RBC Update", body)
        print("Market closed — email sent:", body)
        market_close_email_sent = True

    if now < dtime(9, 30):
        market_close_email_sent = False


# ---------------------------------------------------------
# DAILY SUMMARY TRIGGER (NEW)
# ---------------------------------------------------------
daily_summary_sent = False

def check_daily_summary_trigger():
    global daily_summary_sent

    if is_weekend():
        daily_summary_sent = False
        return

    tz = pytz.timezone("America/Toronto")
    now = datetime.now(tz).time()

    # 4:10 PM to 4:15 PM window
    if dtime(16, 10) <= now <= dtime(16, 15) and not daily_summary_sent:
        body = daily_summary_body()
        send_email("Daily Summary — SHOP + RBC", body)
        print("Daily summary email sent:", body)
        daily_summary_sent = True

    # Reset next morning
    if now < dtime(9, 30):
        daily_summary_sent = False


# ---------------------------------------------------------
# SCHEDULED JOB (EVERY 2 HOURS)
# ---------------------------------------------------------
def job():
    if is_weekend():
        print("Weekend — skipping scheduled job")
        return

    if market_is_open():
        body = run_all_decisions()
        send_email("Scheduled Update — SHOP + RBC", body)
        print("Scheduled email sent:", body)
    else:
        print("Market closed — skipping")


schedule.every(2).hours.do(job)

print("Bot started. Running every 2 hours...")


# ---------------------------------------------------------
# MAIN LOOP
# ---------------------------------------------------------
while True:
    check_market_open_trigger()
    check_market_close_trigger()
    check_daily_summary_trigger()   # NEW
    schedule.run_pending()
    time.sleep(1)
