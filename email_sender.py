import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import markdown
import logging

class EmailSender:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER")
        self.smtp_port = int(os.getenv("SMTP_PORT", 465))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_pass = os.getenv("SMTP_PASS")
        self.recipient_email = os.getenv("RECIPIENT_EMAIL")

    def send_report(self, subject: str, markdown_content: str):
        if not all([self.smtp_server, self.smtp_user, self.smtp_pass, self.recipient_email]):
            logging.warning("邮件配置不完整，跳过邮件发送。")
            return False

        try:
            # 将 Markdown 转换为 HTML
            html_content = markdown.markdown(markdown_content)
            
            # 简单的 HTML 样式增强
            styled_html = f"""
            <html>
                <head>
                    <style>
                        body {{ font-family: sans-serif; line-height: 1.6; color: #333; }}
                        h1 {{ color: #2c3e50; border-bottom: 2px solid #eee; }}
                        h2 {{ color: #34495e; margin-top: 20px; }}
                        .paper {{ background: #f9f9f9; padding: 15px; border-left: 5px solid #3498db; margin-bottom: 20px; }}
                        .score {{ font-weight: bold; color: #e67e22; }}
                        a {{ color: #3498db; }}
                    </style>
                </head>
                <body>
                    {html_content}
                </body>
            </html>
            """

            msg = MIMEMultipart()
            msg['Subject'] = subject
            msg['From'] = self.smtp_user
            msg['To'] = self.recipient_email

            msg.attach(MIMEText(styled_html, 'html'))

            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.smtp_user, self.smtp_pass)
                server.send_message(msg)
            
            logging.info(f"邮件报告已发送至 {self.recipient_email}")
            return True
        except Exception as e:
            logging.error(f"邮件发送失败: {e}")
            return False
