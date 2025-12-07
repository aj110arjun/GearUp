# Forgot Password with OTP Implementation

## Overview
Implemented a complete OTP-based password reset flow for the GearUp application with the following features:
- Email-based password reset using 4-digit OTP
- OTP expires in 2 minutes
- Professional HTML email template
- Three-step reset process

## Implementation Details

### 1. **Forms** (`common/user/auths/forms.py`)
Added two new forms:
- `ForgotPasswordForm`: Validates email and checks if account exists
- `ResetPasswordForm`: Validates new password with security checks

### 2. **Email Service** (`core/services.py`)
Added `send_password_reset_otp_email()`:
- Sends both plain text and HTML email
- Uses professional HTML template
- Includes OTP code and expiry information

### 3. **Email Template** (`templates/user/auth/password_reset_otp_email.html`)
Professional HTML email with:
- Branded GearUp styling
- Large, clear OTP display
- Security warnings
- 2-minute expiry notice
- Responsive design

### 4. **Views** (`common/user/auths/views.py`)
Four new views for the complete flow:

#### Step 1: `forgot_password()`
- User enters email address
- Validates email exists in database
- Generates 4-digit OTP (expires in 2 minutes)
- Sends HTML email with OTP
- Stores email in session
- Redirects to OTP verification

#### Step 2: `verify_reset_otp()`
- Displays 4-digit OTP input boxes
- Shows countdown timer (2 minutes)
- Verifies OTP code
- Handles expired OTPs
- Tracks failed attempts (max 3)
- On success, stores verification status in session

#### Step 3: `resend_reset_otp()`
- Generates new OTP
- Sends new email
- Resets timer

#### Step 4: `reset_password()`
- User enters new password
- Validates password strength
- Updates user password
- Cleans up session data
- Redirects to signin with success message

### 5. **Templates**
Created three new templates:

#### `forgot_password.html`
- Email input form
- Branded design matching signin page
- Error handling
- Link back to signin

#### `verify_reset_otp.html`
- 4 individual input boxes for OTP digits
- Live countdown timer (2 minutes)
- Auto-focus and auto-advance between boxes
- Paste support for OTP codes
- Resend OTP option
- Change email option

#### `reset_password.html`
- New password input
- Confirm password input
- Password visibility toggle
- Password strength requirements
- Success/error messages

### 6. **URLs** (`common/user/auths/urls.py`)
Added four new URL patterns:
- `/forgot-password/` - Request OTP
- `/verify-reset-otp/` - Verify OTP code
- `/resend-reset-otp/` - Resend OTP
- `/reset-password/` - Set new password

### 7. **Updated Signin Page**
Changed "Forgot your password?" link to use new OTP-based flow

## Security Features

1. **OTP Expiry**: 2-minute expiration (configurable in `OTP.create_otp()`)
2. **Attempt Limiting**: Max 3 failed OTP attempts before deletion
3. **Session-Based**: Uses Django sessions to track reset flow
4. **Password Validation**: 
   - Minimum 8 characters
   - Not entirely numeric
   - Not common passwords
   - Passwords must match
5. **Email Verification**: Only sends OTP to registered emails
6. **Auto-cleanup**: Deletes old OTPs when creating new ones

## User Flow

1. User clicks "Forgot your password?" on signin page
2. User enters email address
3. System sends OTP to email (4-digit code, expires in 2 minutes)
4. User receives professional HTML email with OTP
5. User enters OTP in verification page
6. Timer counts down from 2:00 to 0:00
7. On successful verification, user sets new password
8. Password is updated and user is redirected to signin
9. User can now login with new password

## Email Template Features

- **Professional Design**: Branded with GearUp colors and logo
- **Clear OTP Display**: Large, easy-to-read 4-digit code
- **Visual Hierarchy**: Important information highlighted
- **Security Warnings**: Alerts if user didn't request reset
- **Expiry Notice**: Clear 2-minute expiration warning
- **Responsive**: Works on all email clients
- **Plain Text Fallback**: Includes text version for compatibility

## Testing the Feature

1. Navigate to signin page
2. Click "Forgot your password?"
3. Enter registered email
4. Check email for OTP code
5. Enter OTP within 2 minutes
6. Set new password
7. Login with new password

## Configuration

OTP expiry time can be changed in `common/user/auths/models.py`:
```python
expires_at = timezone.now() + timezone.timedelta(minutes=2)  # Change minutes here
```

## Notes

- The old token-based password reset is still available for backward compatibility
- All password reset attempts are tracked in the OTP model
- Session data is automatically cleaned up after successful reset
- Email sending uses Django's EmailMultiAlternatives for HTML support
