import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

_smtp_server = 'localhost'
_smtp_port = 1025
_smtp_username = ''
_smtp_password = ''

def send_email(from_email, to_email, subject, body):
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    server = None
    try:
        server = smtplib.SMTP(_smtp_server, _smtp_port)
        # server.starttls()
        # server.login(_smtp_username, _smtp_password)
        server.send_message(msg)


    except Exception as e:
        raise Exception(f"SMTP Error: {str(e)}")

    finally:
        if server:
            try:
                server.quit()
            except e:
                raise e  # Ignore errors when closing
