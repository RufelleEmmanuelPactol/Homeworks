from toolkits.email.mail import send_email
from toolkits.db import run_query

users = run_query("SELECT * FROM users LIMIT 5")

email_html = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Email</title>
  <style>
    body {
      background-color: #f5f7fa;
      font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
      margin: 0;
      padding: 0;
      color: #333;
    }
    .container {
      max-width: 600px;
      margin: 40px auto;
      background-color: #ffffff;
      border-radius: 8px;
      overflow: hidden;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }
    .header {
      background-color: #2f80ed;
      padding: 30px 40px;
      color: #ffffff;
      text-align: center;
    }
    .header h1 {
      margin: 0;
      font-size: 24px;
    }
    .content {
      padding: 30px 40px;
      line-height: 1.6;
    }
    .button {
      display: inline-block;
      padding: 12px 24px;
      margin-top: 20px;
      background-color: #2f80ed;
      color: #fff;
      text-decoration: none;
      border-radius: 6px;
      font-weight: bold;
    }
    .footer {
      text-align: center;
      font-size: 12px;
      color: #aaa;
      padding: 20px;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>You're Invited to Something Great</h1>
    </div>
    <div class="content">
      <p>Hi there,</p>
      <p>We’re thrilled to bring you something special. Whether you're looking to grow, explore, or simply stay ahead, this is your moment.</p>
      <p>Click below to discover what we’ve prepared just for you.</p>
      <a href="https://your-link.com" class="button">Explore Now</a>
      <p>If you have any questions, feel free to reply—we’d love to hear from you.</p>
      <p>Warm regards,<br>Your Team</p>
    </div>
    <div class="footer">
      © 2025 Your Company. All rights reserved.
    </div>
  </div>
</body>
</html>


""" + users.to_html()
send_email(from_email='rufelle@interviewquery.com', to_email='dusan@gmail.com',body=email_html, subject='hello')