# Messaging App API Testing with Postman

This directory contains Postman collections and environment files for comprehensive testing of the Django messaging app API.

## Files Included

- `Messaging_App_API_Tests.postman_collection.json` - Complete test collection
- `Messaging_App_Environment.postman_environment.json` - Environment variables
- `README.md` - This instruction file

## Setup Instructions

### 1. Prerequisites

- Postman installed on your system
- Django development server running at `http://127.0.0.1:8000`
- Database with proper migrations applied

### 2. Import Collection and Environment

1. Open Postman
2. Click "Import" button
3. Import both JSON files:
   - `Messaging_App_API_Tests.postman_collection.json`
   - `Messaging_App_Environment.postman_environment.json`
4. Select the "Messaging App Environment" from the environment dropdown

### 3. Start Django Server

Ensure your Django server is running:
```bash
cd messaging_app
python manage.py runserver
```

## Test Execution Order

### Phase 1: Authentication Setup

1. **Register User** - Creates first test user (user1@example.com)
2. **Register Second User** - Creates second test user (user2@example.com)
3. **Login User 1** - Authenticates user1 and stores JWT token
4. **Login User 2** - Authenticates user2 and stores JWT token

### Phase 2: Conversation Testing

5. **Create Conversation (Authenticated)** - User1 creates conversation with User2
6. **Create Conversation (Unauthenticated)** - Tests authentication requirement
7. **List Conversations (User 1)** - Tests pagination and user filtering
8. **List Conversations with Filtering** - Tests ordering and pagination parameters
9. **Get Specific Conversation (User 1)** - Tests conversation retrieval
10. **Access Conversation (Unauthorized User)** - Tests authorization

### Phase 3: Message Testing

11. **Send Message (User 1)** - User1 sends first message
12. **Send Message (User 2)** - User2 replies
13. **Send Message (Unauthenticated)** - Tests authentication requirement
14. **List Messages in Conversation** - Tests message retrieval with pagination
15. **List Messages with Filtering and Pagination** - Tests advanced filtering
16. **Search Messages by Content** - Tests search functionality

## Key Features Tested

### Authentication & Authorization
- JWT token-based authentication
- User registration and login
- Unauthorized access prevention
- Token validation

### Conversation Management
- Creating conversations between users
- Listing user's conversations
- Conversation access control (participants only)
- Pagination (10 conversations per page)
- Ordering by creation date

### Message Management
- Sending messages in conversations
- Message retrieval with pagination (20 messages per page)
- Message filtering by conversation
- Content search functionality
- Ordering by timestamp

### Pagination & Filtering
- Page-based pagination
- Custom page sizes
- Ordering by various fields
- Search functionality
- Filter by conversation, sender, date ranges

## Expected Test Results

### Successful Operations (200/201 status)
- User registration and login
- Authenticated conversation creation
- Authenticated message sending
- Conversation and message listing for authorized users

### Authentication Failures (401 status)
- Unauthenticated requests to protected endpoints
- Invalid or expired tokens

### Authorization Failures (403/404 status)
- Accessing conversations user is not part of
- Attempting operations without proper permissions

## Environment Variables

The collection uses these variables (automatically set by test scripts):

- `base_url`: API base URL (http://127.0.0.1:8000)
- `user1_token`: JWT token for first user
- `user2_token`: JWT token for second user
- `conversation_id`: ID of created conversation
- `message_id`: ID of created message

## API Endpoints Tested

### Authentication
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login

### Conversations
- `GET /api/conversations/` - List conversations
- `POST /api/conversations/` - Create conversation
- `GET /api/conversations/{id}/` - Get specific conversation

### Messages
- `GET /api/messages/` - List messages
- `POST /api/messages/` - Send message

### Query Parameters Tested
- `page` - Page number for pagination
- `page_size` - Number of items per page
- `ordering` - Sort order (-created_at, -sent_at)
- `search` - Content search
- `conversation` - Filter by conversation ID

## Troubleshooting

### Common Issues

1. **Server not running**: Ensure Django server is active at http://127.0.0.1:8000
2. **Database errors**: Run migrations with `python manage.py migrate`
3. **Token expiration**: Re-run login requests to refresh tokens
4. **Permission errors**: Ensure users are properly authenticated

### Debugging Tips

1. Check response status codes and error messages
2. Verify environment variables are set correctly
3. Ensure proper request headers (Content-Type, Authorization)
4. Check Django server logs for detailed error information

## Advanced Testing Scenarios

### Security Testing
- Test with invalid/expired tokens
- Attempt cross-user data access
- Test input validation and sanitization

### Performance Testing
- Test pagination with large datasets
- Measure response times for various operations
- Test concurrent user scenarios

### Edge Cases
- Empty conversation lists
- Invalid conversation/message IDs
- Malformed request bodies
- Special characters in message content

## Notes

- All timestamps are in ISO format
- Pagination follows Django REST framework standards
- JWT tokens have expiration times (check your settings)
- Search is case-insensitive
- Ordering supports both ascending and descending (prefix with -)

For additional help or issues, refer to the Django REST framework and JWT documentation.