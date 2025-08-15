# CoinLink Chat-Based Registration System

## Overview
CoinLink now includes a chat-based user registration system that allows users to create accounts directly through the chat interface.

## How It Works

### 1. Start Registration
Users can start the registration process by typing `/register` in the chat.

### 2. Multi-Step Flow
The registration follows a 4-step process:

1. **Email Input**: User enters their email address
2. **Password Input**: User creates a password (minimum 8 characters)
3. **Password Confirmation**: User re-enters password to confirm
4. **Verification**: System sends verification link to email

### 3. Commands
- `/register` - Start registration process
- `/cancel` - Cancel registration and return to normal chat

## Backend Implementation

### Files
- `backend/auth/registration_state.py` - Core registration flow logic
- `backend/auth/routes.py` - Verification endpoints
- `backend/api/main.py` - Updated chat endpoint with registration handling

### Features
- Session-based state management
- Email validation
- Password hashing with salt
- Secure verification token generation
- Automatic cleanup of expired sessions (1 hour) and pending users (24 hours)
- Rate limiting integration

### API Endpoints
- `POST /api/chat` - Handles both chat and registration messages
- `GET /api/auth/verify?token=<token>` - Verifies user account
- `GET /api/auth/status` - Registration system status

## Frontend Implementation

### Files
- `frontend/src/components/Chat.jsx` - Updated to handle registration messages
- `frontend/src/components/VerificationPage.jsx` - Account verification page
- `frontend/src/services/api.js` - Updated chat API with session support

### Features
- System message styling for registration prompts
- Session ID generation for each chat session
- Updated placeholder text with registration hint
- Welcome message includes registration instruction

## Security Features

### Password Security
- Minimum 8 character requirement
- Salted SHA-256 hashing
- Passwords never logged or stored in plain text

### Session Security
- Unique session IDs for each chat session
- Automatic session expiration (1 hour)
- Pending user cleanup (24 hours)

### Rate Limiting
- Chat endpoint: 20 requests per minute
- Integrated with existing SlowAPI rate limiting

## Usage Examples

### Registration Flow
```
User: /register
Bot: Welcome! Please enter your email address to register:

User: user@example.com
Bot: Great! Now enter your password (minimum 8 characters):

User: mypassword123
Bot: Please re-enter your password to confirm:

User: mypassword123
Bot: ✓ Registration successful! A verification link has been sent to user@example.com. Please check your email and click the link to activate your account.
```

### Verification
1. User receives verification email with link
2. Clicks link: `http://localhost:3000/auth/verify?token=<token>`
3. Account is activated
4. User can now use normal chat features

## Development Notes

### Current Limitations (MVP)
- In-memory storage (not persistent across restarts)
- No actual email sending (verification links logged to console)
- Basic validation (can be enhanced)

### Future Enhancements
- Database persistence
- Real email service integration
- Enhanced password requirements
- User authentication and login
- User tiers and permissions

## Testing

### Backend Testing
```bash
# Test registration flow
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "/register", "session_id": "test123"}'

# Check status
curl http://localhost:8000/api/auth/status
```

### Frontend Testing
1. Open chat interface
2. Type `/register`
3. Follow the prompts
4. Check console for verification link
5. Test verification page

## Error Handling

### Common Scenarios
- Invalid email format
- Password too short
- Passwords don't match
- Expired sessions
- Invalid verification tokens

### User Experience
- Clear error messages
- Option to restart registration
- Graceful fallback to normal chat
- No data loss on errors
