# Email Notification Setup

## Overview
Contact forms can now send email notifications when users submit the form. This feature is optional - if SMTP credentials are not configured, form submissions will still work but no emails will be sent.

## Configuration

### Step 1: Edit Backend .env File
Open `/app/backend/.env` and configure the following variables:

```env
# Email Configuration (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com
```

### Step 2: Get SMTP Credentials

#### For Gmail:
1. Go to your Google Account settings
2. Enable 2-Step Verification if not already enabled
3. Go to Security → App passwords
4. Generate an app password for "Mail"
5. Use this app password (not your regular password) in `SMTP_PASSWORD`

**Gmail App Password Guide:** https://support.google.com/accounts/answer/185833

#### For Other Email Providers:

**Outlook/Hotmail:**
- SMTP_HOST: smtp-mail.outlook.com
- SMTP_PORT: 587
- Use your email and password

**Yahoo:**
- SMTP_HOST: smtp.mail.yahoo.com
- SMTP_PORT: 587
- Generate an app password from Yahoo account settings

**Custom SMTP Server:**
- Contact your hosting provider for SMTP details

### Step 3: Configure Contact Form in Builder

1. Open your project in AXXO Builder
2. Add or edit a Contact Block
3. In the editing panel, find **Notification Email** field
4. Enter the email address where you want to receive notifications
5. Save your changes

### Step 4: Restart Backend

After configuring .env file:
```bash
sudo supervisorctl restart backend
```

## Features

### Email Template
Notification emails include:
- Sender's name
- Sender's email (clickable)
- Phone number (if provided)
- Message content
- Professional HTML formatting
- Responsive design

### Security
- Uses TLS encryption (STARTTLS)
- Credentials stored in .env file (not in code)
- Graceful fallback if SMTP not configured

## Testing

1. Configure SMTP credentials in `.env`
2. Restart backend
3. Submit a test form from your website
4. Check the notification email inbox
5. Check backend logs: `tail -f /var/log/supervisor/backend.*.log`

## Troubleshooting

### Email not sending?

**Check logs:**
```bash
tail -50 /var/log/supervisor/backend.err.log | grep -i email
```

**Common issues:**

1. **Invalid credentials**
   - Solution: Verify SMTP_USER and SMTP_PASSWORD are correct
   - For Gmail: Use app password, not regular password

2. **Port blocked**
   - Solution: Try port 465 (SSL) instead of 587 (TLS)
   - Update SMTP_PORT in .env

3. **"Less secure app" error (Gmail)**
   - Solution: Use App Password instead of regular password

4. **Connection timeout**
   - Solution: Check firewall settings
   - Verify SMTP_HOST is correct

### No error but email not received?

- Check spam/junk folder
- Verify notification_email is configured in Contact Block
- Check backend logs for "Email sent successfully" message

## Notes

- If SMTP credentials are not configured, forms will still work but emails won't be sent
- The backend logs will show: "SMTP credentials not configured. Email notification skipped."
- This is intentional to allow the app to function without email setup

## Support

For more help:
- Check backend logs: `/var/log/supervisor/backend.*.log`
- Verify .env configuration
- Test SMTP credentials with a simple email client first
