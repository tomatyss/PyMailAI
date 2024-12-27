"""Tests for handling multiple text parts and inline images in EmailData."""

from email.message import EmailMessage
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from pymailai.message import EmailData


def test_multiple_text_parts():
    """Test handling of multiple text/plain parts."""
    msg = MIMEMultipart()
    msg["Subject"] = "Test Multiple Parts"
    msg["From"] = "sender@example.com"
    msg["To"] = "recipient@example.com"
    msg["Message-ID"] = "<123@example.com>"

    # Add multiple text parts
    part1 = MIMEText("First part\n", "plain")
    part2 = MIMEText("Second part", "plain")
    msg.attach(part1)
    msg.attach(part2)

    email_data = EmailData.from_email_message(msg)

    # Verify text parts are combined
    assert "First part" in email_data.body_text
    assert "Second part" in email_data.body_text


def test_inline_images():
    """Test handling of inline images."""
    msg = MIMEMultipart()
    msg["Subject"] = "Test Inline Images"
    msg["From"] = "sender@example.com"
    msg["To"] = "recipient@example.com"
    msg["Message-ID"] = "<123@example.com>"

    # Add a text part
    text_part = MIMEText("Email with inline image", "plain")
    msg.attach(text_part)

    # Add an inline image
    img_data = b"dummy image data"
    img_part = MIMEImage(img_data, _subtype='jpeg')
    img_part.add_header("Content-Disposition", "inline", filename="image.jpg")
    msg.attach(img_part)

    email_data = EmailData.from_email_message(msg)

    # Verify inline image is included in attachments
    assert len(email_data.attachments) == 1
    assert email_data.attachments[0]["filename"] == "image.jpg"
    assert email_data.attachments[0]["content_type"].startswith("image/")
    assert email_data.attachments[0]["payload"] == img_data


def test_mixed_content():
    """Test handling of mixed content with text parts and both inline/attachment images."""
    msg = MIMEMultipart()
    msg["Subject"] = "Test Mixed Content"
    msg["From"] = "sender@example.com"
    msg["To"] = "recipient@example.com"
    msg["Message-ID"] = "<123@example.com>"

    # Add multiple text parts
    part1 = MIMEText("First text part\n", "plain")
    part2 = MIMEText("Second text part", "plain")
    msg.attach(part1)
    msg.attach(part2)

    # Add an inline image
    inline_img_data = b"inline image data"
    inline_img = MIMEImage(inline_img_data, _subtype='jpeg')
    inline_img.add_header("Content-Disposition", "inline", filename="inline.jpg")
    msg.attach(inline_img)

    # Add an attachment image
    attach_img_data = b"attachment image data"
    attach_img = MIMEImage(attach_img_data, _subtype='jpeg')
    attach_img.add_header("Content-Disposition", "attachment", filename="attach.jpg")
    msg.attach(attach_img)

    email_data = EmailData.from_email_message(msg)

    # Verify text parts are combined
    assert "First text part" in email_data.body_text
    assert "Second text part" in email_data.body_text

    # Verify both images are in attachments
    assert len(email_data.attachments) == 2
    filenames = {att["filename"] for att in email_data.attachments}
    assert filenames == {"inline.jpg", "attach.jpg"}
