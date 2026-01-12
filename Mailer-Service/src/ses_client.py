"""AWS SES Email Client"""

import boto3
from botocore.exceptions import ClientError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from config import (
    AWS_REGION,
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    SES_SENDER_EMAIL,
    SES_CHARSET
)
from fastapi import HTTPException, status

ses_client = boto3.client(
    'ses',
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

def send_email(
    recipient: str,
    subject: str,
    body: str,
    pdf_attachment: bytes = None,
    pdf_filename: str = None
) -> str:
    """
    Send email using Amazon SES with optional PDF attachment
    Supports multiple recipients separated by commas
    
    Args:
        recipient: Email address(es) of recipient(s) - can be comma-separated
        subject: Email subject
        body: Email body (HTML or plain text)
        pdf_attachment: Binary PDF data (optional)
        pdf_filename: Name of PDF file (optional)
    
    Returns:
        Message ID from SES
    
    Raises:
        HTTPException: If email sending fails
    """
    try:
        recipients = [email.strip() for email in recipient.split(',') if email.strip()]
        
        if not recipients:
            raise ValueError("At least one recipient email is required")
        
        if pdf_attachment and pdf_filename:
            msg = MIMEMultipart()
            msg['Subject'] = subject
            msg['From'] = SES_SENDER_EMAIL
            msg['To'] = ', '.join(recipients)  
            
            html_part = MIMEText(body, 'html', SES_CHARSET)
            msg.attach(html_part)
            
            pdf_part = MIMEApplication(pdf_attachment, Name=pdf_filename)
            pdf_part['Content-Disposition'] = f'attachment; filename=\"{pdf_filename}\"'
            msg.attach(pdf_part)
            
            response = ses_client.send_raw_email(
                Source=SES_SENDER_EMAIL,
                Destinations=recipients,  
                RawMessage={'Data': msg.as_string()}
            )
        else:
            response = ses_client.send_email(
                Source=SES_SENDER_EMAIL,
                Destination={'ToAddresses': recipients},  
                Message={
                    'Subject': {'Data': subject, 'Charset': SES_CHARSET},
                    'Body': {
                        'Html': {'Data': body, 'Charset': SES_CHARSET}
                    }
                }
            )
        
        return response['MessageId']
    
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SES Error ({error_code}): {error_message}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}"
        )

def verify_email(email: str) -> bool:
    """
    Verify an email address is configured in SES
    
    Args:
        email: Email address to verify
    
    Returns:
        True if email is verified, False otherwise
    """
    try:
        response = ses_client.list_verified_email_addresses()
        return email in response.get('VerifiedEmailAddresses', [])
    except Exception as e:
        print(f"Error verifying email: {str(e)}")
        return False

def send_test_email(email: str, subject: str = "Test Email") -> str:
    """
    Send a test email to verify SES configuration
    
    Args:
        email: Email address to send test to
        subject: Email subject
    
    Returns:
        Message ID from SES
    """
    return send_email(
        recipient=email,
        subject=subject,
        body="This is a test email from Trackify Mailer Service."
    )
