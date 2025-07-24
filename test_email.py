import environ

env = environ.Env()
env.read_env()  # loads .env file from current directory

smtp_server = "smtp.gmail.com"
port = 587
sender_email = "c.wnt.nd1053@gmail.com"
password = env('EMAIL_HOST_PASSWORD')  # now this works

import smtplib

try:
    server = smtplib.SMTP(smtp_server, port)
    server.starttls()
    server.login(sender_email, password)
    print("Login successful!")
except Exception as e:
    print("Error:", e)
finally:
    server.quit()
