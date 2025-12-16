# API Reference

## Overview

RaiseMyHand provides a REST API for programmatic access to sessions, questions, and data.

**Base URL:**
```
https://questions.yourschool.edu/api
```

**Interactive Documentation:**
Visit `/docs` on your instance for Swagger UI (e.g., `https://questions.yourschool.edu/docs`)

## Authentication

### API Key Authentication

Include your API key in the query string:

```bash
curl "https://questions.yourschool.edu/api/endpoint?api_key=rmh_abc123..."
```

Or in Authorization header:

```bash
curl "https://questions.yourschool.edu/api/endpoint" \
  -H "Authorization: Bearer rmh_abc123..."
```

### CSRF Token

For state-changing requests (POST, PUT, DELETE), include CSRF token:

```bash
# Get CSRF token
CSRF_TOKEN=$(curl -s https://questions.yourschool.edu/api/csrf-token | jq -r .csrf_token)

# Use in request
curl -X POST "https://questions.yourschool.edu/api/endpoint" \
  -H "X-CSRF-Token: $CSRF_TOKEN"
```

## Session Management

### Create Session

**POST** `/api/meetings`

Create a new question session.

**Request:**
```bash
curl -X POST "https://questions.yourschool.edu/api/meetings?api_key=YOUR_KEY" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: TOKEN" \
  -d '{
    "title": "Physics 101 - Lecture 5",
    "password": ""
  }'
```

**Response:**
```json
{
  "id": 42,
  "meeting_code": "abc123xyz",
  "instructor_code": "def456uvw",
  "title": "Physics 101 - Lecture 5",
  "created_at": "2025-12-16T10:30:00Z",
  "is_active": true,
  "student_url": "https://questions.yourschool.edu/student?code=abc123xyz",
  "instructor_url": "https://questions.yourschool.edu/instructor?code=def456uvw"
}
```

**Parameters:**
- `title` (required) - Session title
- `password` (optional) - Session password if access-controlled

### Get Session

**GET** `/api/meetings/{meeting_code}`

Get session details and questions.

**Request:**
```bash
curl "https://questions.yourschool.edu/api/meetings/abc123xyz"
```

**Response:**
```json
{
  "id": 42,
  "meeting_code": "abc123xyz",
  "title": "Physics 101 - Lecture 5",
  "created_at": "2025-12-16T10:30:00Z",
  "is_active": true,
  "question_count": 5,
  "questions": [
    {
      "id": 1,
      "text": "What is quantum entanglement?",
      "status": "approved",
      "upvotes": 8,
      "is_answered": false,
      "created_at": "2025-12-16T10:35:00Z"
    }
  ]
}
```

### End Session

**POST** `/api/meetings/{instructor_code}/end?api_key=KEY`

End an active session. Requires instructor code and API key.

**Request:**
```bash
curl -X POST "https://questions.yourschool.edu/api/meetings/def456uvw/end?api_key=YOUR_KEY" \
  -H "X-CSRF-Token: TOKEN"
```

**Response:**
```json
{
  "success": true,
  "message": "Session ended",
  "ended_at": "2025-12-16T11:45:00Z"
}
```

### Get Flagged Questions

**GET** `/api/meetings/{instructor_code}/flagged-questions?api_key=KEY`

Get questions flagged for review (profanity, etc.).

**Request:**
```bash
curl "https://questions.yourschool.edu/api/meetings/def456uvw/flagged-questions?api_key=YOUR_KEY"
```

**Response:**
```json
{
  "flagged_questions": [
    {
      "id": 42,
      "text": "What the *** is this?",
      "status": "flagged",
      "flagged_reason": "profanity",
      "upvotes": 2,
      "created_at": "2025-12-16T10:40:00Z"
    }
  ]
}
```

## Questions

### Submit Question

**POST** `/api/meetings/{meeting_code}/questions`

Submit a new question anonymously.

**Request:**
```bash
curl -X POST "https://questions.yourschool.edu/api/meetings/abc123xyz/questions" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: TOKEN" \
  -d '{
    "text": "How does photosynthesis work?"
  }'
```

**Response:**
```json
{
  "id": 52,
  "text": "How does photosynthesis work?",
  "status": "approved",
  "upvotes": 0,
  "created_at": "2025-12-16T10:45:00Z"
}
```

**Parameters:**
- `text` (required) - Question text (1-500 characters)

**Status Codes:**
- `201` - Question created
- `400` - Invalid input (empty, too long, etc.)
- `404` - Session not found
- `429` - Rate limited (too many requests)

### Upvote Question

**POST** `/api/questions/{question_id}/vote`

Toggle upvote on a question.

**Request:**
```bash
curl -X POST "https://questions.yourschool.edu/api/questions/52/vote" \
  -H "X-CSRF-Token: TOKEN"
```

**Response:**
```json
{
  "id": 52,
  "upvotes": 1,
  "user_voted": true
}
```

### Approve Question

**POST** `/api/questions/{question_id}/approve?api_key=KEY`

Approve a flagged question. Requires API key.

**Request:**
```bash
curl -X POST "https://questions.yourschool.edu/api/questions/42/approve?api_key=YOUR_KEY" \
  -H "X-CSRF-Token: TOKEN"
```

**Response:**
```json
{
  "success": true,
  "id": 42,
  "status": "approved",
  "censored_text": "What the *** is this?"
}
```

**Note:** Profanity is automatically censored as `***`

### Reject Question

**POST** `/api/questions/{question_id}/reject?api_key=KEY`

Reject a flagged question. Requires API key.

**Request:**
```bash
curl -X POST "https://questions.yourschool.edu/api/questions/42/reject?api_key=YOUR_KEY" \
  -H "X-CSRF-Token: TOKEN"
```

**Response:**
```json
{
  "success": true,
  "id": 42,
  "status": "rejected"
}
```

### Mark as Answered

**POST** `/api/questions/{question_id}/mark-answered?api_key=KEY`

Mark question as answered. Requires API key.

**Request:**
```bash
curl -X POST "https://questions.yourschool.edu/api/questions/52/mark-answered?api_key=YOUR_KEY" \
  -H "X-CSRF-Token: TOKEN"
```

**Response:**
```json
{
  "success": true,
  "id": 52,
  "is_answered": true
}
```

### Delete Question

**DELETE** `/api/questions/{question_id}?api_key=KEY`

Delete a question. Requires API key.

**Request:**
```bash
curl -X DELETE "https://questions.yourschool.edu/api/questions/52?api_key=YOUR_KEY" \
  -H "X-CSRF-Token: TOKEN"
```

**Response:**
```json
{
  "success": true,
  "message": "Question deleted"
}
```

## Answers

### Write Answer

**POST** `/api/questions/{question_id}/answer?api_key=KEY`

Write a detailed markdown answer. Requires API key.

**Request:**
```bash
curl -X POST "https://questions.yourschool.edu/api/questions/52/answer?api_key=YOUR_KEY" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: TOKEN" \
  -d '{
    "text": "# Photosynthesis\n\n**Light-dependent reactions:**\n- Occur in thylakoids\n- Produce ATP and NADPH"
  }'
```

**Response:**
```json
{
  "success": true,
  "question_id": 52,
  "answer_id": 10,
  "published": false
}
```

**Parameters:**
- `text` (required) - Markdown formatted answer

**Markdown Support:**
- Headers: `# Heading`
- Bold: `**bold**`
- Italic: `*italic*`
- Lists: `- item`
- Code: `` `code` ``
- Links: `[text](url)`

### Publish Answer

**POST** `/api/questions/{question_id}/answer/publish?api_key=KEY`

Make answer visible to students. Requires API key.

**Request:**
```bash
curl -X POST "https://questions.yourschool.edu/api/questions/52/answer/publish?api_key=YOUR_KEY" \
  -H "X-CSRF-Token: TOKEN"
```

**Response:**
```json
{
  "success": true,
  "question_id": 52,
  "published": true,
  "published_at": "2025-12-16T10:50:00Z"
}
```

## Data Export

### Download Session Report

**GET** `/api/meetings/{instructor_code}/report?api_key=KEY&format=FORMAT`

Export session data. Requires API key.

**Formats:**
- `csv` - Comma-separated values (Excel compatible)
- `json` - JSON format

**Request - CSV:**
```bash
curl "https://questions.yourschool.edu/api/meetings/def456uvw/report?api_key=YOUR_KEY&format=csv" \
  -o session_report.csv
```

**Request - JSON:**
```bash
curl "https://questions.yourschool.edu/api/meetings/def456uvw/report?api_key=YOUR_KEY&format=json" \
  -o session_report.json
```

**CSV Format:**
```csv
Question #,Text,Upvotes,Answered,Created,Answered At
1,"What is quantum entanglement?",8,true,2025-12-16T10:35:00Z,2025-12-16T10:50:00Z
2,"How does gravity work?",3,false,2025-12-16T10:40:00Z,
```

**JSON Format:**
```json
{
  "session": {
    "title": "Physics 101 - Lecture 5",
    "created_at": "2025-12-16T10:30:00Z",
    "ended_at": "2025-12-16T11:45:00Z",
    "total_questions": 5,
    "total_votes": 15
  },
  "questions": [
    {
      "id": 1,
      "number": 1,
      "text": "What is quantum entanglement?",
      "upvotes": 8,
      "is_answered": true,
      "created_at": "2025-12-16T10:35:00Z",
      "answered_at": "2025-12-16T10:50:00Z"
    }
  ]
}
```

## Admin API

### Create API Key

**POST** `/api/admin/api-keys?api_key=ADMIN_KEY`

Create a new API key for an instructor. Requires admin API key.

**Request:**
```bash
curl -X POST "https://questions.yourschool.edu/api/admin/api-keys?api_key=ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: TOKEN" \
  -d '{
    "name": "Prof. Smith - Physics 101"
  }'
```

**Response:**
```json
{
  "id": "rmh_abc123def456ghi789",
  "name": "Prof. Smith - Physics 101",
  "created_at": "2025-12-16T10:30:00Z",
  "is_active": true
}
```

**Note:** API key is only shown once. Save securely.

### List API Keys

**GET** `/api/admin/api-keys?api_key=ADMIN_KEY`

List all API keys. Requires admin API key.

**Request:**
```bash
curl "https://questions.yourschool.edu/api/admin/api-keys?api_key=ADMIN_KEY"
```

**Response:**
```json
{
  "api_keys": [
    {
      "id": "rmh_abc123...",
      "name": "Prof. Smith - Physics 101",
      "created_at": "2025-12-16T10:30:00Z",
      "is_active": true,
      "last_used": "2025-12-16T11:00:00Z"
    }
  ]
}
```

## WebSocket Connection

### Connect to Session

**WS** `/ws/{meeting_code}`

Establish WebSocket connection for real-time updates.

**Connection:**
```javascript
const ws = new WebSocket('wss://questions.yourschool.edu/ws/abc123xyz');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Update received:', message);
};
```

**Message Types:**

**new_question**
```json
{
  "type": "new_question",
  "question": {
    "id": 52,
    "text": "What is entropy?",
    "status": "approved",
    "upvotes": 0
  }
}
```

**question_voted**
```json
{
  "type": "question_voted",
  "question_id": 52,
  "upvotes": 3
}
```

**question_answered**
```json
{
  "type": "question_answered",
  "question_id": 52,
  "is_answered": true
}
```

**session_ended**
```json
{
  "type": "session_ended",
  "message": "This session has ended"
}
```

## Error Responses

### Error Format

All errors return JSON with status and message:

```json
{
  "error": "Invalid API key",
  "status": 401
}
```

### Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad request (invalid input)
- `401` - Unauthorized (invalid API key)
- `403` - Forbidden (no permission)
- `404` - Not found (session/question doesn't exist)
- `429` - Too many requests (rate limited)
- `500` - Server error

## Rate Limiting

Rate limits apply to prevent abuse:

- **Questions:** 1 per 2 seconds per IP
- **Votes:** 5 per second per IP
- **API requests:** 100 per minute per API key

Response includes rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1702805400
```

## Examples

### Python Script to Create Session and Submit Questions

```python
import requests
import json

BASE_URL = "https://questions.yourschool.edu/api"
API_KEY = "rmh_your_key_here"

# Get CSRF token
csrf_response = requests.get(f"{BASE_URL}/csrf-token")
csrf_token = csrf_response.json()['csrf_token']

# Create session
headers = {
    "X-CSRF-Token": csrf_token,
    "Content-Type": "application/json"
}

session_data = {
    "title": "My New Session",
    "password": ""
}

response = requests.post(
    f"{BASE_URL}/meetings?api_key={API_KEY}",
    json=session_data,
    headers=headers
)

session = response.json()
meeting_code = session['meeting_code']

# Submit a question
question_data = {"text": "What is the answer?"}
response = requests.post(
    f"{BASE_URL}/meetings/{meeting_code}/questions",
    json=question_data,
    headers=headers
)

question = response.json()
print(f"Question created: {question['id']}")
```

### Bash Script to Get Session Report

```bash
#!/bin/bash

API_KEY="rmh_your_key_here"
INSTRUCTOR_CODE="def456uvw"

# CSV format
curl "https://questions.yourschool.edu/api/meetings/$INSTRUCTOR_CODE/report?api_key=$API_KEY&format=csv" \
  -o report.csv

echo "Report saved to report.csv"
```

## Rate Limiting Headers

All API responses include rate limit information:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
X-RateLimit-Reset: 1609459200
```

Check `X-RateLimit-Remaining` to see how many requests you have left.

## CORS

API supports CORS for browser-based requests:

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, X-CSRF-Token, Authorization
```

## Webhooks

Webhooks are not currently supported. Use WebSocket for real-time updates or poll the API.

## API Deprecation Policy

- Endpoints may be deprecated with 6 months notice
- Deprecated endpoints will return a warning header
- Contact administrators for migration support
