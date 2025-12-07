# Testing the Forgot Password Feature

## Quick Test Guide

### Prerequisites
- Server is running on http://127.0.0.1:8000
- You have a registered user account with a valid email

### Test Steps

#### 1. Access Forgot Password Page
- Navigate to: http://127.0.0.1:8000/auth/signin/
- Click on "Forgot your password?" link
- OR directly visit: http://127.0.0.1:8000/auth/forgot-password/

#### 2. Request Password Reset
- Enter your registered email address
- Click "Send Verification Code"
- You should see: "Verification code sent to your email!"
- You'll be redirected to the OTP verification page

#### 3. Check Your Email
You should receive an email with:
- Subject: "GearUp - Password Reset Verification Code"
- A professional HTML template with:
  - Large 4-digit OTP code
  - "This code will expire in 2 minutes" warning
  - Security notice
  - GearUp branding

#### 4. Verify OTP
On the verification page you'll see:
- 4 individual input boxes for the OTP digits
- A countdown timer starting from 02:00
- Your email address displayed
- Options to:
  - Resend code
  - Use different email

Enter the 4-digit code from your email:
- Type or paste the code
- The boxes auto-advance as you type
- Click "Verify Code"

#### 5. Set New Password
After successful OTP verification:
- Enter your new password (minimum 8 characters)
- Confirm the new password
- Click "Reset Password"
- You'll see: "Password reset successful! You can now sign in with your new password."

#### 6. Sign In
- You'll be redirected to the signin page
- Sign in with your email and NEW password
- Success!

## Test Scenarios

### Happy Path
✅ Valid email → OTP sent → Correct OTP → New password → Success

### Error Scenarios to Test

1. **Invalid Email**
   - Enter non-existent email
   - Should see: "No account found with this email address."

2. **Expired OTP**
   - Wait more than 2 minutes after receiving OTP
   - Enter the expired OTP
   - Should see: "OTP has expired"

3. **Wrong OTP**
   - Enter incorrect 4-digit code
   - Should see: "Invalid OTP code"
   - After 3 failed attempts: "Too many failed attempts. Please request a new OTP."

4. **Password Mismatch**
   - Enter different passwords in the two fields
   - Should see: "The two password fields didn't match."

5. **Weak Password**
   - Try password less than 8 characters
   - Try all numeric password
   - Try common password like "password"
   - Should see appropriate error messages

### Resend OTP Test
1. Request password reset
2. On OTP verification page, click "Resend Code"
3. Check email for new OTP
4. Old OTP should no longer work
5. New OTP should work

## URLs Reference

- Forgot Password: `/auth/forgot-password/`
- Verify OTP: `/auth/verify-reset-otp/`
- Resend OTP: `/auth/resend-reset-otp/`
- Reset Password: `/auth/reset-password/`
- Sign In: `/auth/signin/`

## Email Configuration

Make sure your email settings are configured in `settings.py`:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # or your SMTP server
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'GearUp <your-email@gmail.com>'
```

For development, you can use console backend:
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```
This will print emails to the console instead of sending them.

## Troubleshooting

### Email Not Received
- Check spam/junk folder
- Verify email settings in settings.py
- Check server console for email output (if using console backend)
- Verify the email address is registered in the system

### OTP Expired Too Quickly
- Check server time is correct
- OTP expiry is set to 2 minutes in `OTP.create_otp()` method

### Session Issues
- Clear browser cookies
- Try in incognito/private mode
- Check Django session middleware is enabled

## Success Indicators

✅ Professional HTML email received
✅ OTP code is 4 digits
✅ Timer counts down from 2:00
✅ OTP expires after 2 minutes
✅ Password successfully reset
✅ Can login with new password
✅ Old password no longer works
