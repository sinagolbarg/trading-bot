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
    return datetime.now(tz).weekday() >= 5   # 5 = Saturday, 6 = Sunday


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


def decision_A(price, I7, F7, label):
    change_ratio = (price - I7) / I7

    if price > I7 and change_ratio > 0.05:
        amount = change_ratio * F7
        return f"Decision A {label}: Sell {amount:.2f} — Price: {price} — Change ratio: {change_ratio:.4f}"

    if change_ratio > -0.05:
        return f"Decision A {label}: Do nothing — Price: {price} — Change ratio: {change_ratio:.4f}"

    dev = I7 - price
    threshold = I7 / 20
    unit = F7 / 15

    if dev <= 2 * threshold:
        qty = 1
    elif dev <= 3 * threshold:
        qty = 2
    else:
        qty = 3

    return f"Decision A {label}: Buy {qty} {unit:.2f} — Price: {price} — Change ratio: {change_ratio:.4f}"


def decision_B(price, H7, label):
    if price >= H7 * 1.1:
        return f"Decision B {label}: BUY 100 (STEP 1) — Price: {price}"
    else:
        return f"Decision B {label}: HOLD — Price: {price}"


# ---------------------------------------------------------
# RUN DECISIONS FOR BOTH STOCKS
# ---------------------------------------------------------
def run_all_decisions():
    # SHOP
    shop_price = get_price("SHOP.TO")
    shop_A = decision_A(shop_price, 159, 500, "SHOP")
    shop_B = decision_B(shop_price, 159, "SHOP")

    # RBC
    rbc_price = get_price("RY.TO")
    rbc_A = decision_A(rbc_price, 271, 500, "RBC")
    rbc_B = decision_B(rbc_price, 262, "RBC")

    body = f"{shop_A}\n{shop_B}\n\n{rbc_A}\n{rbc_B}"
    return body


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

    # Market closes at 4:00 PM
    if now >= dtime(16, 0) and not market_close_email_sent:
        body = run_all_decisions()
        send_email("Market Close — SHOP + RBC Update", body)
        print("Market closed — email sent:", body)
        market_close_email_sent = True

    # Reset for next day
    if now < dtime(9, 30):
        market_close_email_sent = False


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
    schedule.run_pending()
    time.sleep(1)
