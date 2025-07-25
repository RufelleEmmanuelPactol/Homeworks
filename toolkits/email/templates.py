def get_class_invitation_template(class_name, student_email, instructor_email=""):
    """Generate a beautiful HTML email template for class invitations"""
    
    html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to {class_name}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #f8fafc;
            color: #334155;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}
        
        .header {{
            background: linear-gradient(135deg, oklch(0.7686 0.165 70.08) 0%, oklch(0.8 0.18 65) 100%);
            padding: 32px 24px;
            text-align: center;
            color: #1a1a1a;
        }}
        
        .logo {{
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 8px;
            letter-spacing: -0.025em;
        }}
        
        .header-subtitle {{
            font-size: 16px;
            opacity: 0.8;
            font-weight: 500;
        }}
        
        .content {{
            padding: 40px 32px;
        }}
        
        .welcome-title {{
            font-size: 24px;
            font-weight: 600;
            color: #1e293b;
            margin-bottom: 16px;
            text-align: center;
        }}
        
        .class-name {{
            background: linear-gradient(135deg, oklch(0.7686 0.165 70.08), oklch(0.8 0.18 65));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 700;
            font-size: 20px;
        }}
        
        .message {{
            font-size: 16px;
            color: #475569;
            margin-bottom: 32px;
            text-align: center;
        }}
        
        .steps {{
            background-color: #f8fafc;
            border-radius: 8px;
            padding: 24px;
            margin: 24px 0;
        }}
        
        .steps-title {{
            font-size: 18px;
            font-weight: 600;
            color: #1e293b;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
        }}
        
        .steps-title::before {{
            content: "🚀";
            margin-right: 8px;
        }}
        
        .step {{
            display: flex;
            align-items: flex-start;
            margin-bottom: 12px;
            font-size: 15px;
        }}
        
        .step-number {{
            background: oklch(0.7686 0.165 70.08);
            color: #1a1a1a;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 12px;
            margin-right: 12px;
            flex-shrink: 0;
        }}
        
        .step-text {{
            color: #475569;
        }}
        
        .cta-container {{
            text-align: center;
            margin: 32px 0;
        }}
        
        .cta-button {{
            display: inline-block;
            background: linear-gradient(135deg, oklch(0.7686 0.165 70.08) 0%, oklch(0.8 0.18 65) 100%);
            color: #1a1a1a;
            text-decoration: none;
            padding: 16px 32px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 16px;
            transition: all 0.2s ease;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}
        
        .cta-button:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
        }}
        
        .student-email {{
            background-color: #f1f5f9;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 12px 16px;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 14px;
            color: #1e293b;
            margin: 8px 0;
            text-align: center;
        }}
        
        .footer {{
            background-color: #f8fafc;
            padding: 24px 32px;
            text-align: center;
            border-top: 1px solid #e2e8f0;
        }}
        
        .footer-text {{
            font-size: 14px;
            color: #64748b;
            margin-bottom: 8px;
        }}
        
        .help-link {{
            color: oklch(0.7686 0.165 70.08);
            text-decoration: none;
            font-weight: 500;
        }}
        
        .help-link:hover {{
            text-decoration: underline;
        }}
        
        .divider {{
            height: 1px;
            background: linear-gradient(90deg, transparent, #e2e8f0, transparent);
            margin: 24px 0;
        }}
        
        @media (max-width: 600px) {{
            .container {{
                margin: 16px;
                border-radius: 8px;
            }}
            
            .content {{
                padding: 24px 20px;
            }}
            
            .header {{
                padding: 24px 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">Interview Query</div>
            <div class="header-subtitle">Homework Platform</div>
        </div>
        
        <div class="content">
            <h1 class="welcome-title">🎓 Welcome to Your New Class!</h1>
            
            <p class="message">
                You've been invited to join <span class="class-name">{class_name}</span>
                <br>Your coding journey starts here!
            </p>
            
            <div class="steps">
                <div class="steps-title">Get Started in 3 Easy Steps</div>
                
                <div class="step">
                    <div class="step-number">1</div>
                    <div class="step-text">
                        <strong>Visit Interview Query</strong><br>
                        Head over to interviewquery.com to access the platform
                    </div>
                </div>
                
                <div class="step">
                    <div class="step-number">2</div>
                    <div class="step-text">
                        <strong>Create Your Account</strong><br>
                        Sign up using this email address:
                        <div class="student-email">{student_email}</div>
                    </div>
                </div>
                
                <div class="step">
                    <div class="step-number">3</div>
                    <div class="step-text">
                        <strong>Start Learning</strong><br>
                        Access your homework assignments and track your progress
                    </div>
                </div>
            </div>
            
            <div class="cta-container">
                <a href="https://interviewquery.com" class="cta-button">
                    🚀 Get Started Now
                </a>
            </div>
            
            <div class="divider"></div>
            
            <p style="font-size: 14px; color: #64748b; text-align: center;">
                📚 You'll receive homework assignments directly through the platform<br>
                📊 Track your progress and see detailed analytics<br>
                💬 Get instant feedback on your solutions
            </p>
        </div>
        
        <div class="footer">
            <p class="footer-text">
                Need help? Contact your instructor or visit our 
                <a href="https://interviewquery.com/help" class="help-link">Help Center</a>
            </p>
            <p class="footer-text">
                Happy coding! 🎯<br>
                <strong>The Interview Query Team</strong>
            </p>
        </div>
    </div>
</body>
</html>
"""
    
    return html_template

def get_assignment_notification_template(assignment_name, class_name, due_date, question_count, student_email, questions=None):
    """Generate HTML email template for assignment notifications"""
    
    # Generate questions HTML if questions list is provided
    questions_html = ""
    if questions:
        questions_html = """
        <div style="margin: 24px 0;">
            <h3 style="color: #1e293b; margin-bottom: 16px;">📝 Assignment Questions:</h3>
        """
        
        for i, q in enumerate(questions, 1):
            difficulty_color = {
                'Easy': '#10b981',
                'Medium': '#f59e0b', 
                'Hard': '#ef4444'
            }.get(q.get('difficulty', 'Medium'), '#6b7280')
            
            questions_html += f"""
            <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <h4 style="margin: 0; color: #1e293b; font-size: 16px;">
                        {i}. {q['title']}
                    </h4>
                    <div style="display: flex; gap: 12px; align-items: center;">
                        <span style="color: {difficulty_color}; font-weight: 600; font-size: 14px;">
                            {q.get('difficulty', 'Medium')}
                        </span>
                        <span style="background-color: oklch(0.7686 0.165 70.08); color: #1a1a1a; padding: 4px 12px; border-radius: 16px; font-size: 14px; font-weight: 600;">
                            {q['points']} pts
                        </span>
                    </div>
                </div>
                <a href="{q['link']}" style="display: inline-block; background: linear-gradient(135deg, oklch(0.7686 0.165 70.08) 0%, oklch(0.8 0.18 65) 100%); color: #1a1a1a; text-decoration: none; padding: 10px 20px; border-radius: 6px; font-weight: 600; font-size: 14px; margin-top: 8px;">
                    Start Question →
                </a>
            </div>
            """
        
        questions_html += "</div>"
    
    html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>New Assignment: {assignment_name}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #f8fafc;
            color: #334155;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}
        
        .header {{
            background: linear-gradient(135deg, oklch(0.7686 0.165 70.08) 0%, oklch(0.8 0.18 65) 100%);
            padding: 32px 24px;
            text-align: center;
            color: #1a1a1a;
        }}
        
        .logo {{
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 8px;
            letter-spacing: -0.025em;
        }}
        
        .header-subtitle {{
            font-size: 16px;
            opacity: 0.8;
            font-weight: 500;
        }}
        
        .content {{
            padding: 40px 32px;
        }}
        
        .assignment-title {{
            font-size: 24px;
            font-weight: 600;
            color: #1e293b;
            margin-bottom: 16px;
            text-align: center;
        }}
        
        .assignment-name {{
            background: linear-gradient(135deg, oklch(0.7686 0.165 70.08), oklch(0.8 0.18 65));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 700;
            font-size: 20px;
        }}
        
        .assignment-details {{
            background-color: #f8fafc;
            border-radius: 8px;
            padding: 24px;
            margin: 24px 0;
        }}
        
        .detail-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #e2e8f0;
        }}
        
        .detail-row:last-child {{
            border-bottom: none;
        }}
        
        .detail-label {{
            font-weight: 600;
            color: #475569;
        }}
        
        .detail-value {{
            font-weight: 500;
            color: #1e293b;
        }}
        
        .due-date {{
            color: oklch(0.7686 0.165 70.08);
            font-weight: 600;
        }}
        
        .cta-container {{
            text-align: center;
            margin: 32px 0;
        }}
        
        .cta-button {{
            display: inline-block;
            background: linear-gradient(135deg, oklch(0.7686 0.165 70.08) 0%, oklch(0.8 0.18 65) 100%);
            color: #1a1a1a;
            text-decoration: none;
            padding: 16px 32px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 16px;
            transition: all 0.2s ease;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}
        
        .cta-button:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
        }}
        
        .tips {{
            background-color: #fef3c7;
            border: 1px solid #fde68a;
            border-radius: 8px;
            padding: 16px;
            margin: 24px 0;
        }}
        
        .tips-title {{
            font-weight: 600;
            color: #92400e;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
        }}
        
        .tips-title::before {{
            content: "💡";
            margin-right: 8px;
        }}
        
        .tips-content {{
            color: #78350f;
            font-size: 14px;
            line-height: 1.5;
        }}
        
        .footer {{
            background-color: #f8fafc;
            padding: 24px 32px;
            text-align: center;
            border-top: 1px solid #e2e8f0;
        }}
        
        .footer-text {{
            font-size: 14px;
            color: #64748b;
            margin-bottom: 8px;
        }}
        
        .help-link {{
            color: oklch(0.7686 0.165 70.08);
            text-decoration: none;
            font-weight: 500;
        }}
        
        .help-link:hover {{
            text-decoration: underline;
        }}
        
        @media (max-width: 600px) {{
            .container {{
                margin: 16px;
                border-radius: 8px;
            }}
            
            .content {{
                padding: 24px 20px;
            }}
            
            .header {{
                padding: 24px 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">Interview Query</div>
            <div class="header-subtitle">Homework Platform</div>
        </div>
        
        <div class="content">
            <h1 class="assignment-title">📚 New Assignment Posted!</h1>
            
            <p style="text-align: center; font-size: 16px; color: #475569; margin-bottom: 24px;">
                Your instructor has posted a new assignment in<br>
                <span class="assignment-name">{class_name}</span>
            </p>
            
            <div class="assignment-details">
                <div class="detail-row">
                    <span class="detail-label">📝 Assignment Name:</span>
                    <span class="detail-value">{assignment_name}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">📅 Due Date:</span>
                    <span class="detail-value due-date">{due_date}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">🎯 Questions to Complete:</span>
                    <span class="detail-value">{question_count} questions</span>
                </div>
            </div>
            
            {questions_html}
            
            <div class="tips">
                <div class="tips-title">Pro Tips for Success</div>
                <div class="tips-content">
                    • Start early to have time for questions<br>
                    • Test your code thoroughly before submitting<br>
                    • Remember to handle edge cases<br>
                    • Ask for help if you get stuck!
                </div>
            </div>
            
            <div class="cta-container">
                <a href="https://interviewquery.com" class="cta-button">
                    🚀 Go to Interview Query
                </a>
            </div>
            
            <p style="font-size: 14px; color: #64748b; text-align: center;">
                Log in with your email: <strong>{student_email}</strong>
            </p>
        </div>
        
        <div class="footer">
            <p class="footer-text">
                Questions? Reach out to your instructor or visit our 
                <a href="https://interviewquery.com/help" class="help-link">Help Center</a>
            </p>
            <p class="footer-text">
                Good luck! 🎯<br>
                <strong>The Interview Query Team</strong>
            </p>
        </div>
    </div>
</body>
</html>
"""
    
    return html_template