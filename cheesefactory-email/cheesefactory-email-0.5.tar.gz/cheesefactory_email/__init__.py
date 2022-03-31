# cheesefactory_email/__init__.py

import logging
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import List, Optional, Union


logger = logging.getLogger(__name__)


class CfEmail:
    def __init__(self, host: str, use_tls: bool = False, header_tags: Optional[dict] = None,
                 port: Union[int, str] = 25, username: Optional[str] = None, password: Optional[str] = None,
                 local_hostname: Optional[str] = None):
        """Send an Email to a mail server with optional attachments.

        Arguments:
            host: Email server hostname or IP.
            port: Email server port.
            username: Email server account username.
            password: Email server account password.
            use_tls: Connect to the Email server using TLS?
            header_tags: Dictionary of tag:values for the header. i.e. {'X-Barracuda-Encrypted': 'RJSE-RSA-AES256-SHA'}
            local_hostname: Name of the sending host
        """
        # Sanity check arguments
        if header_tags is None:
            header_tags = {}
        if not isinstance(host, str):
            raise ValueError(f'host type is {str(type(host))}, not str.')
        if not isinstance(use_tls, bool):
            raise ValueError(f'use_tls type is {str(type(use_tls))}, not bool.')
        if not isinstance(header_tags, dict):
            raise ValueError(f'header_tags type is {str(type(header_tags))}, not dict.')
        if not isinstance(port, (int, str)):
            raise ValueError(f'port type is {str(type(port))}, not str.')
        if not isinstance(username, Optional[str]):
            raise ValueError(f'username type is {str(type(username))}, not str.')
        if not isinstance(password, Optional[str]):
            raise ValueError(f'password type is {str(type(password))}, not str.')
        if not isinstance(local_hostname, Optional[str]):
            raise ValueError(f'local_hostname type is {str(type(local_hostname))}, not str.')

        self.host = host
        self.port = int(port)
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.header_tags = header_tags
        self.local_hostname = local_hostname

        self.sender = None
        self.recipients = None
        self.cc_recipients = None
        self.subject = None
        self.body = None
        self.attachments = None

    #
    # PUBLIC METHODS
    #

    def send(self, sender: str, recipients: Union[str, List[str]], cc_recipients: Union[str, List[str], None] = None,
             subject: str = '', body: str = '', attachments: Optional[List] = None):
        """Send Email.

        Arguments:
            sender: Email sender.
            recipients: One recipient or a list of Email recipients.
            cc_recipients: One CC recipient or a list of CC recipients
            subject: Email subject line.
            body: Body of Email.
            attachments: A list of filepaths to be used as Email attachments.
        """
        # Sanity check arguments
        if not isinstance(sender, str):
            raise ValueError(f'sender is type {type(sender)}, not str.')
        if not isinstance(recipients, (list, str)):
            raise ValueError(f'recipient is type {type(recipients)}, not list or str.')
        if not isinstance(cc_recipients, Union[str, list, None]):
            raise ValueError(f'cc_recipients is type {type(cc_recipients)}, not list or str.')
        if not isinstance(subject, str):
            raise ValueError(f'subject is type {type(subject)}, not str.')
        if not isinstance(body, str):
            raise ValueError(f'body is type {type(body)}, not str.')
        if not isinstance(attachments, Union[list, None]):
            raise ValueError(f'attachments is type {type(attachments)}, not list.')

        self.sender = sender
        self.recipients = recipients
        self.cc_recipients = cc_recipients
        self.subject = subject
        self.body = body
        self.attachments = attachments

        # Create header

        logger.debug('Creating header.')
        message = MIMEMultipart()
        message['Subject'] = self.subject
        message['From'] = self.sender

        if isinstance(recipients, str):
            message['To'] = self.recipients
        else:  # it is a list
            message['To'] = ', '.join(self.recipients)

        if isinstance(cc_recipients, str):
            message['cc'] = self.cc_recipients
        elif isinstance(cc_recipients, list):  # it is a list
            message['cc'] = ', '.join(self.cc_recipients)

        if self.header_tags is not None:
            for key, value in self.header_tags.items():
                message[key] = value
        logger.debug(f'Message after header changes:\n{str(message)}')

        # Attach body

        logger.debug('Attaching body.')
        message.attach(MIMEText(self.body))

        # Attach attachments

        logger.debug('Attaching attachments.')
        if self.attachments is not None:
            for attachment_item in self.attachments:
                attachment = MIMEBase('application', 'octet-stream')
                attachment.set_payload(open(attachment_item, 'rb').read())
                encoders.encode_base64(attachment)
                attachment.add_header(
                    'Content-Disposition',
                    'attachment; filename="' + str(Path(attachment_item).name) + '"'
                )
                message.attach(attachment)

        # Connect to Email server

        logger.debug(f'Connecting: {self.username}@{self.host}:str({self.port})')
        logger.debug(f'local_hostname = {self.local_hostname}')

        with smtplib.SMTP(host=self.host, port=self.port, local_hostname=self.local_hostname) as smtp:
            if logger.level == logging.DEBUG:
                smtp.set_debuglevel(2)  # debuglevel 1=messages, 2=timestamped messages
            else:
                smtp.set_debuglevel(1)

            smtp.ehlo_or_helo_if_needed()

            logger.debug(f'use_tls = {str(self.use_tls)}')
            if self.use_tls is True:
                smtp.starttls()

            if self.username is not None and self.password is not None:
                smtp.login(self.username, self.password)

            # Send Email

            logger.debug('Sending Email.')
            try:
                smtp.send_message(message)

            except ValueError as e:
                logger.critical(f'Email send_message error {format(e)}')
                exit(1)

        logger.debug('Email sent')
