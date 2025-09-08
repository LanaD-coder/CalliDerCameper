import smtplib
import ssl
import environ
import certifi  # ← you need this!

env = environ.Env()
env.read_env()

smtp_server = "smtp.ionos.de"
port = 465  # SSL port
sender_email = "abenteuer@callidercamper.de"
password = env('EMAIL_HOST_PASSWORD')

# Create SSL context using certifi CA bundle
context = ssl.create_default_context(cafile=certifi.where())

try:
    server = smtplib.SMTP_SSL(smtp_server, port, context=context, timeout=10)
    server.set_debuglevel(1)  # prints SMTP conversation
    server.login(sender_email, password)
    print("✅ Login successful!")
except Exception as e:
    print("❌ Error:", e)
finally:
    server.quit()
