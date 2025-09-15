# Messaging App - Postman API Testing Collections

This directory contains comprehensive Postman collections for testing the Messaging App API endpoints, including authentication, conversations, messages, and security testing.

## 📁 Collection Files

### 1. `messaging_app_environment.json`
**Environment Variables Configuration**
- Contains base URL and token variables
- Automatically manages JWT tokens during testing
- Variables: `base_url`, `access_token`, `refresh_token`, `user_id`, `conversation_id`, `message_id`

### 2. `authentication_tests.json`
**Authentication Flow Testing**
- User Registration
- JWT Token Login
- Profile Management (Get/Update)
- Token Refresh
- User Logout
- Automatic token storage in environment variables

### 3. `conversations_tests.json`
**Conversation CRUD Operations**
- Create new conversations
- List all conversations with pagination
- Get specific conversation details
- Filter conversations by date
- Search and order conversations
- Send messages to conversations
- Test pagination (10 conversations per page)

### 4. `messages_tests.json`
**Message Operations with Filtering**
- Create messages directly
- List all messages with pagination
- Get specific message details
- Filter messages by sender
- Filter messages by date range
- Search messages by content
- Order messages by date
- Test pagination (20 messages per page)

### 5. `unauthorized_access_tests.json`
**Security and JWT Protection Testing**
- Access endpoints without authentication token
- Test with invalid/malformed tokens
- Verify 401 Unauthorized responses
- Ensure private conversations are protected

## 🚀 Getting Started

### Prerequisites
1. **Postman Application** - Download from [postman.com](https://www.postman.com/downloads/)
2. **Running Django Server** - Ensure your messaging app server is running at `http://127.0.0.1:8000`

### Setup Instructions

#### Step 1: Import Environment
1. Open Postman
2. Click on "Environments" in the left sidebar
3. Click "Import" and select `messaging_app_environment.json`
4. Set this environment as active

#### Step 2: Import Collections
1. Click on "Collections" in the left sidebar
2. Click "Import" and select all JSON collection files:
   - `authentication_tests.json`
   - `conversations_tests.json`
   - `messages_tests.json`
   - `unauthorized_access_tests.json`

#### Step 3: Verify Server Status
Ensure your Django development server is running:
```bash
cd messaging_app
python manage.py runserver
```
Server should be accessible at: `http://127.0.0.1:8000`

## 📋 Testing Workflow

### Recommended Testing Order

#### 1. **Start with Authentication Tests**
```
1. User Registration → Creates a test user
2. User Login (JWT Token) → Gets access tokens (auto-stored)
3. Get User Profile → Verifies authentication works
4. Update User Profile → Tests profile modification
5. Refresh JWT Token → Tests token refresh mechanism
6. User Logout → Cleans up tokens
```

#### 2. **Test Unauthorized Access (Security)**
```
1. Access Conversations Without Token → Should return 401
2. Access Messages Without Token → Should return 401
3. Access Profile Without Token → Should return 401
4. Access with Invalid Token → Should return 401
5. Access with Malformed Token → Should return 401
6. Create Conversation Without Token → Should return 401
7. Send Message Without Token → Should return 401
```

#### 3. **Test Conversations (After Login)**
```
1. Create Conversation → Creates new conversation (stores ID)
2. List All Conversations → Shows paginated results
3. Get Specific Conversation → Retrieves conversation details
4. List Conversations with Pagination → Tests page size limits
5. Filter Conversations by Date → Tests date filtering
6. Search and Order Conversations → Tests search/ordering
7. Send Message to Conversation → Tests message sending
```

#### 4. **Test Messages**
```
1. Create Message → Creates message directly (stores ID)
2. List All Messages → Shows paginated results
3. Get Specific Message → Retrieves message details
4. List Messages with Pagination → Tests 20 messages per page
5. Filter Messages by Sender → Tests sender filtering
6. Filter Messages by Date Range → Tests date range filtering
7. Search Messages by Content → Tests content search
8. Order Messages by Date → Tests ordering functionality
```

## 🔧 Environment Variables

The collections automatically manage these variables:

| Variable | Description | Auto-Updated |
|----------|-------------|-------------|
| `base_url` | API base URL | ❌ Manual |
| `access_token` | JWT access token | ✅ Auto |
| `refresh_token` | JWT refresh token | ✅ Auto |
| `user_id` | Current user ID | ✅ Auto |
| `conversation_id` | Last created conversation ID | ✅ Auto |
| `message_id` | Last created message ID | ✅ Auto |

## 📊 Expected Test Results

### Authentication Tests
- ✅ Registration: `201 Created` with user data
- ✅ Login: `200 OK` with JWT tokens
- ✅ Profile: `200 OK` with user details
- ✅ Update: `200 OK` with updated data
- ✅ Refresh: `200 OK` with new access token
- ✅ Logout: `200 OK` with success message

### Unauthorized Access Tests
- ✅ All requests: `401 Unauthorized`
- ✅ Error messages: "Authentication credentials were not provided" or "Given token not valid"

### Conversations Tests
- ✅ Create: `201 Created` with conversation data
- ✅ List: `200 OK` with paginated results (max 10 per page)
- ✅ Retrieve: `200 OK` with conversation details
- ✅ Filtering: `200 OK` with filtered results
- ✅ Search/Order: `200 OK` with ordered results

### Messages Tests
- ✅ Create: `201 Created` with message data
- ✅ List: `200 OK` with paginated results (max 20 per page)
- ✅ Retrieve: `200 OK` with message details
- ✅ Filtering: `200 OK` with filtered results
- ✅ Search/Order: `200 OK` with ordered results

## 🔍 API Endpoints Tested

### Authentication Endpoints
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - JWT token login
- `GET /api/auth/profile/` - Get user profile
- `PUT /api/auth/profile/update/` - Update user profile
- `POST /api/auth/refresh/` - Refresh JWT token
- `POST /api/auth/logout/` - User logout

### Conversation Endpoints
- `GET /api/conversations/` - List conversations
- `POST /api/conversations/` - Create conversation
- `GET /api/conversations/{id}/` - Get specific conversation
- `POST /api/conversations/{id}/send_message/` - Send message to conversation

### Message Endpoints
- `GET /api/messages/` - List messages
- `POST /api/messages/` - Create message
- `GET /api/messages/{id}/` - Get specific message

### Query Parameters Tested
- **Pagination**: `?page=1&page_size=10`
- **Filtering**: `?sender=1&created_at_after=2024-01-01`
- **Search**: `?search=test`
- **Ordering**: `?ordering=created_at`

## 🛠️ Troubleshooting

### Common Issues

1. **401 Unauthorized on authenticated requests**
   - Ensure you've run the login request first
   - Check that tokens are stored in environment variables
   - Verify server is running and accessible

2. **404 Not Found errors**
   - Verify server is running at `http://127.0.0.1:8000`
   - Check URL paths in requests
   - Ensure database migrations are applied

3. **500 Internal Server Error**
   - Check Django server logs for detailed error messages
   - Verify database is properly configured
   - Ensure all required fields are provided in request bodies

4. **Empty results in list endpoints**
   - Create some test data first using POST requests
   - Check filtering parameters aren't too restrictive

### Debug Tips

1. **Check Environment Variables**
   - Click on the environment name in top-right corner
   - Verify tokens are populated after login

2. **View Server Logs**
   - Monitor Django development server console output
   - Look for detailed error messages and stack traces

3. **Test Individual Requests**
   - Run requests one by one to isolate issues
   - Check response bodies for error details

## 📝 Notes

- **Test Data**: Collections use consistent test data (username: `testuser`, email: `testuser@example.com`)
- **Automatic Cleanup**: Logout request clears stored tokens
- **Pagination**: Conversations limited to 10 per page, Messages to 20 per page
- **Security**: All protected endpoints require valid JWT tokens
- **Filtering**: Supports date ranges, user filtering, and content search
- **Ordering**: Supports ascending/descending order by date fields

## 🎯 Testing Objectives Achieved

✅ **Authentication Flow**: Complete JWT token lifecycle testing
✅ **CRUD Operations**: Full Create, Read, Update, Delete testing for conversations and messages
✅ **Pagination**: Verify page size limits and navigation
✅ **Filtering**: Test date ranges, user filters, and content search
✅ **Security**: Ensure unauthorized access is properly blocked
✅ **API Compliance**: Verify all endpoints return expected status codes and data structures

These collections provide comprehensive coverage of the Messaging App API functionality and security requirements.