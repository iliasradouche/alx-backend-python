# Messaging App API - Postman Collection

This document provides a comprehensive Postman collection for testing the Messaging App API endpoints. The API uses JWT authentication and includes endpoints for user management, conversations, and messages.

## Base URL
```
http://127.0.0.1:8000/api/
```

## Authentication
The API uses JWT (JSON Web Token) authentication. You'll need to:
1. Register a user or login to get access and refresh tokens
2. Use the access token in the Authorization header for protected endpoints
3. Refresh the token when it expires

---

## 1. Authentication Endpoints

### 1.1 User Registration
**POST** `/api/auth/register/`

**Headers:**
```
Content-Type: application/json
```

**Body (JSON):**
```json
{
    "username": "testuser",
    "email": "testuser@example.com",
    "password": "testpassword123",
    "password_confirm": "testpassword123",
    "first_name": "Test",
    "last_name": "User"
}
```

**Expected Response (201):**
```json
{
    "message": "User registered successfully",
    "user": {
        "id": 1,
        "username": "testuser",
        "email": "testuser@example.com",
        "first_name": "Test",
        "last_name": "User"
    }
}
```

### 1.2 Login (Get JWT Token)
**POST** `/api/auth/login/`

**Headers:**
```
Content-Type: application/json
```

**Body (JSON):**
```json
{
    "username": "testuser",
    "password": "testpassword123"
}
```

**Expected Response (200):**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 1,
        "username": "testuser",
        "email": "testuser@example.com",
        "first_name": "Test",
        "last_name": "User"
    }
}
```

**⚠️ Important:** Save the `access` token for use in subsequent requests!

### 1.3 Refresh Token
**POST** `/api/auth/refresh/`

**Headers:**
```
Content-Type: application/json
```

**Body (JSON):**
```json
{
    "refresh": "your_refresh_token_here"
}
```

### 1.4 User Profile
**GET** `/api/auth/profile/`

**Headers:**
```
Authorization: Bearer your_access_token_here
Content-Type: application/json
```

### 1.5 Update Profile
**PUT** `/api/auth/profile/update/`

**Headers:**
```
Authorization: Bearer your_access_token_here
Content-Type: application/json
```

**Body (JSON):**
```json
{
    "first_name": "Updated",
    "last_name": "Name",
    "email": "updated@example.com"
}
```

### 1.6 Change Password
**POST** `/api/auth/change-password/`

**Headers:**
```
Authorization: Bearer your_access_token_here
Content-Type: application/json
```

**Body (JSON):**
```json
{
    "old_password": "testpassword123",
    "new_password": "newpassword123"
}
```

### 1.7 Logout
**POST** `/api/auth/logout/`

**Headers:**
```
Authorization: Bearer your_access_token_here
Content-Type: application/json
```

---

## 2. Conversation Endpoints

**⚠️ All conversation endpoints require authentication. Include the Authorization header with Bearer token.**

### 2.1 List Conversations (with Pagination & Filtering)
**GET** `/api/conversations/`

**Headers:**
```
Authorization: Bearer your_access_token_here
```

**Query Parameters (Optional):**
```
?page=1                           # Pagination (10 conversations per page)
&ordering=-created_at             # Order by creation date (newest first)
&ordering=created_at              # Order by creation date (oldest first)
&participants=user_id             # Filter by participant
&created_at__gte=2024-01-01       # Filter conversations created after date
&created_at__lte=2024-12-31       # Filter conversations created before date
```

**Example Request:**
```
GET /api/conversations/?page=1&ordering=-created_at
```

### 2.2 Create Conversation
**POST** `/api/conversations/`

**Headers:**
```
Authorization: Bearer your_access_token_here
Content-Type: application/json
```

**Body (JSON):**
```json
{
    "participants": [1, 2]  // User IDs of participants
}
```

**Expected Response (201):**
```json
{
    "conversation_id": "uuid-here",
    "participants": [
        {
            "user_id": 1,
            "username": "testuser",
            "email": "testuser@example.com"
        },
        {
            "user_id": 2,
            "username": "otheruser",
            "email": "other@example.com"
        }
    ],
    "created_at": "2024-01-15T10:30:00Z"
}
```

### 2.3 Get Specific Conversation
**GET** `/api/conversations/{conversation_id}/`

**Headers:**
```
Authorization: Bearer your_access_token_here
```

### 2.4 Send Message to Conversation
**POST** `/api/conversations/{conversation_id}/send_message/`

**Headers:**
```
Authorization: Bearer your_access_token_here
Content-Type: application/json
```

**Body (JSON):**
```json
{
    "message_body": "Hello! This is a test message."
}
```

---

## 3. Message Endpoints

**⚠️ All message endpoints require authentication. Include the Authorization header with Bearer token.**

### 3.1 List Messages (with Pagination & Filtering)
**GET** `/api/messages/`

**Headers:**
```
Authorization: Bearer your_access_token_here
```

**Query Parameters (Optional):**
```
?page=1                           # Pagination (20 messages per page)
&ordering=-sent_at                # Order by sent date (newest first)
&ordering=sent_at                 # Order by sent date (oldest first)
&sender=user_id                   # Filter by sender
&conversation=conversation_id     # Filter by conversation
&message_body__icontains=hello    # Search messages containing text
&sent_at__gte=2024-01-01          # Filter messages sent after date
&sent_at__lte=2024-12-31          # Filter messages sent before date
&search=hello                     # Search in sender email and message content
```

**Example Request:**
```
GET /api/messages/?conversation=uuid-here&page=1&ordering=-sent_at
```

### 3.2 Get Specific Message
**GET** `/api/messages/{message_id}/`

**Headers:**
```
Authorization: Bearer your_access_token_here
```

### 3.3 Create Message (Direct)
**POST** `/api/messages/`

**Headers:**
```
Authorization: Bearer your_access_token_here
Content-Type: application/json
```

**Body (JSON):**
```json
{
    "conversation": "conversation_uuid_here",
    "message_body": "Direct message content"
}
```

---

## 4. Testing Scenarios

### Scenario 1: Complete User Journey
1. **Register a new user** (POST `/api/auth/register/`)
2. **Login to get JWT token** (POST `/api/auth/login/`)
3. **Create another user** (repeat steps 1-2 with different credentials)
4. **Create a conversation** between the two users (POST `/api/conversations/`)
5. **Send messages** in the conversation (POST `/api/conversations/{id}/send_message/`)
6. **List conversations** to see the created conversation (GET `/api/conversations/`)
7. **List messages** to see the sent messages (GET `/api/messages/`)

### Scenario 2: Authentication Testing
1. **Try accessing protected endpoints without token** (should return 401)
2. **Login and get valid token**
3. **Access protected endpoints with valid token** (should work)
4. **Try accessing with expired/invalid token** (should return 401)
5. **Refresh token** and try again

### Scenario 3: Authorization Testing
1. **Create conversation with User A**
2. **Try to access conversation with User B** (should be denied if not participant)
3. **Add User B to conversation**
4. **User B should now be able to access the conversation**

### Scenario 4: Pagination and Filtering
1. **Create multiple conversations and messages**
2. **Test pagination** with different page numbers
3. **Test filtering** by date, participants, content
4. **Test ordering** by different fields
5. **Test search functionality**

---

## 5. Common HTTP Status Codes

- **200 OK**: Successful GET, PUT, PATCH requests
- **201 Created**: Successful POST requests (resource created)
- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Missing or invalid authentication token
- **403 Forbidden**: Valid token but insufficient permissions
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server error

---

## 6. Postman Environment Variables

Create these environment variables in Postman for easier testing:

```
base_url = http://127.0.0.1:8000/api
access_token = (set after login)
refresh_token = (set after login)
user_id = (set after login)
conversation_id = (set after creating conversation)
message_id = (set after creating message)
```

---

## 7. Tips for Testing

1. **Always check response status codes** and response bodies
2. **Save tokens** from login response for subsequent requests
3. **Test edge cases** like invalid data, missing fields, unauthorized access
4. **Use environment variables** to avoid hardcoding values
5. **Test pagination** by creating enough data to span multiple pages
6. **Verify filtering and search** work correctly
7. **Test token expiration** and refresh functionality
8. **Check that unauthorized users cannot access private conversations**

---

## 8. Sample Postman Collection JSON

You can import this JSON into Postman to get started quickly:

```json
{
    "info": {
        "name": "Messaging App API",
        "description": "API endpoints for the messaging application",
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    },
    "auth": {
        "type": "bearer",
        "bearer": [
            {
                "key": "token",
                "value": "{{access_token}}",
                "type": "string"
            }
        ]
    },
    "variable": [
        {
            "key": "base_url",
            "value": "http://127.0.0.1:8000/api"
        }
    ]
}
```

This collection provides comprehensive testing coverage for all API endpoints with proper authentication, pagination, filtering, and authorization testing scenarios.