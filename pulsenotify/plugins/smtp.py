import smtplib
import logging
import datetime
from smtplib import SMTPConnectError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import PackageLoader, Environment


log = logging.getLogger(__name__)

env = Environment(loader=PackageLoader('pulsenotify', 'templates'))


class Plugin(object):
    """
    SMTP Plugin for the Pulse Notification system.

    On startup, the config file must include an object with the following elements in the schema:
        - email (to send notifications from)
        - passwd (of email)
        - host (SMTP host domain)
        - port (port of host)
        - template (True/False indicator to use template)

    In each task, under extra/<desired exchange>, there must be an object with the following schema:
        - subject (of email)
        - recipients (who to notify)
        - body (of email in text format)
    """
    def __init__(self, config):
        self.email = config['email']
        self.passwd = config['passwd']
        self.host = config['host']
        self.port = config['port']
        self.template = env.get_template('email_template.html') if config['template'] == True else None


    @property
    def name(self):
        return 'smtp'

    async def notify(self, task_config):
        email_message = MIMEMultipart()
        email_message['Subject'] = task_config['subject']
        email_message['To'] = ', '.join(task_config['recipients'])
        email_message.attach(MIMEText(task_config['body'], 'text'))

        if self.template:
            rendered_email = self.template.render(task_config, date=datetime.datetime.now().strftime('%b %d, %Y'))
            email_message.attach(MIMEText(rendered_email, 'html'))

        for i in range(5):
            try:
                s = smtplib.SMTP(self.host, self.port)
                s.ehlo()
                s.starttls()
                s.login(self.email, self.passwd)
                s.sendmail(self.email, task_config['recipients'], email_message.as_string())
                s.quit()
                log.info("[!] Notified on smtp!")
                return
            except SMTPConnectError as ce:
                log.exception('[!] Attempt %s: SMTPConnectError %s', str(i), ce.message)
        else:
            log.exception('[!] Could not connect to %s with login %s: %s', self.host, self.email)
