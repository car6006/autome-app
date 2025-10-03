# 🔌 API DOCUMENTATION

## Overview
Complete API documentation for the AUTO-ME PWA backend system, including all new endpoints added in Phase 1 enhancements.

## 🔐 Authentication
All API endpoints require JWT authentication via Bearer token.

```http
Authorization: Bearer <jwt_token>
```

## 📋 Base Information
- **Base URL**: `https://insight-api.preview.emergentagent.com/api`
- **API Version**: v2.1.0
- **Content-Type**: `application/json`
- **Authentication**: JWT Bearer Token

---

## 📝 NOTES ENDPOINTS

### Get Notes
```http
GET /api/notes
```

**Query Parameters**:
- `archived` (boolean, optional): Include archived notes
- `limit` (integer, optional): Maximum notes to return (default: 50)

**Response**:
```json
[
  {
    "id": "note-uuid",
    "title": "Meeting Notes",
    "kind": "audio",
    "status": "ready", 
    "artifacts": {
      "transcript": "Transcribed content...",
      "text": "Text content..."
    },
    "tags": ["meeting", "team", "weekly"],
    "created_at": "2025-09-11T10:00:00Z",
    "ready_at": "2025-09-11T10:05:00Z",
    "user_id": "user-uuid"
  }
]
```

### Create Note  
```http
POST /api/notes
```

**Request Body**:
```json
{
  "title": "New Note Title",
  "kind": "text|audio|photo",
  "content": "Optional initial content"
}
```

### Update Note
```http
PUT /api/notes/{note_id}
```

**Request Body**:
```json
{
  "artifacts": {
    "transcript": "Updated transcript content",
    "text": "Updated text content"
  },
  "title": "Updated title"
}
```

**Use Cases**:
- Editing transcript content
- Updating note titles
- Modifying note artifacts

### Delete Note
```http
DELETE /api/notes/{note_id}
```

### Retry Note Processing
```http
POST /api/notes/{note_id}/retry-processing
```

**Description**: Retry failed transcription or OCR processing

---

## 🏷️ TAG MANAGEMENT ENDPOINTS

### Add Tag to Note
```http
POST /api/notes/{note_id}/tags
```

**Request Body**:
```json
{
  "tag": "meeting"
}
```

**Validation**:
- Tag must be 1-50 characters
- Automatically converted to lowercase
- Duplicates prevented

### Remove Tag from Note
```http
DELETE /api/notes/{note_id}/tags/{tag}
```

**Example**:
```http
DELETE /api/notes/abc123/tags/meeting
```

### Get All User Tags
```http
GET /api/notes/tags
```

**Response**:
```json
{
  "tags": ["meeting", "call", "project", "team", "weekly"]
}
```

### Get Notes by Tag
```http
GET /api/notes/by-tag/{tag}
```

**Example**:
```http
GET /api/notes/by-tag/meeting
```

**Response**: Array of notes containing the specified tag

---

## 📝 TEMPLATE MANAGEMENT ENDPOINTS

### Create Template
```http
POST /api/templates
```

**Request Body**:
```json
{
  "name": "Weekly Team Meeting",
  "description": "Template for weekly team meetings",
  "title_template": "Team Meeting - {date}",
  "category": "meeting",
  "tags": ["meeting", "team", "weekly"],
  "content_template": "## Agenda\n\n## Notes\n\n## Action Items"
}
```

**Validation**:
- `name` (required): 1-100 characters
- `title_template` (required): 1-200 characters, supports {date} placeholder
- `category` (optional): meeting|call|project|interview|personal|general
- `tags` (optional): Array of strings, max 10 tags
- `description` (optional): Max 500 characters

### Get User Templates
```http
GET /api/templates
```

**Query Parameters**:
- `category` (string, optional): Filter by category

**Response**:
```json
[
  {
    "id": "template-uuid",
    "name": "Weekly Team Meeting", 
    "description": "Template for weekly team meetings",
    "title_template": "Team Meeting - {date}",
    "category": "meeting",
    "tags": ["meeting", "team", "weekly"],
    "usage_count": 15,
    "is_favorite": false,
    "created_at": "2025-09-11T08:00:00Z",
    "user_id": "user-uuid"
  }
]
```

### Get Template by ID
```http
GET /api/templates/{template_id}
```

### Update Template
```http
PUT /api/templates/{template_id}
```

**Request Body**: Same as create template
**Note**: Cannot modify `id`, `user_id`, `created_at`, `usage_count`

### Delete Template
```http
DELETE /api/templates/{template_id}
```

### Use Template
```http
POST /api/templates/{template_id}/use
```

**Description**: 
- Increments usage_count
- Returns template data for application
- Tracks template analytics

**Response**:
```json
{
  "template": {
    "id": "template-uuid",
    "name": "Weekly Team Meeting",
    "title_template": "Team Meeting - {date}",
    "tags": ["meeting", "team"],
    "usage_count": 16
  },
  "message": "Template usage recorded"
}
```

### Get Template Categories
```http
GET /api/templates/categories
```

**Response**:
```json
{
  "categories": ["meeting", "call", "project", "interview", "personal"]
}
```

---

## 📊 REPORT GENERATION ENDPOINTS

### Generate Detailed Report
```http
POST /api/notes/{note_id}/generate-report
```

**Description**: Generates a clean, structured report with conversation summary

**Response**:
```json
{
  "report": "Generated report content with date and heading...",
  "note_id": "note-uuid",
  "generated_at": "2025-09-11T12:00:00Z"
}
```

**Report Format**:
- Title and date header
- Conversation summary section
- Well-organized paragraphs
- Professional formatting

---

## 🧹 MAINTENANCE ENDPOINTS

### Get Failed Notes Count
```http
GET /api/notes/failed-count
```

**Response**:
```json
{
  "failed": 3
}
```

### Cleanup Failed Notes
```http
POST /api/notes/cleanup-failed
```

**Response**:
```json
{
  "message": "Cleaned up failed notes",
  "deleted_count": 3
}
```

---

## 📈 ANALYTICS ENDPOINTS

### User Statistics
```http
GET /api/user/stats
```

**Response**:
```json
{
  "total_notes": 145,
  "total_templates": 8,
  "total_tags": 25,
  "notes_this_month": 23,
  "templates_used": 42,
  "most_used_tags": ["meeting", "project", "call"],
  "most_used_template": "Weekly Team Meeting"
}
```

---

## 🔄 ERROR HANDLING

### Standard Error Response
```json
{
  "detail": "Error message description",
  "status_code": 400,
  "error_type": "validation_error"
}
```

### Common HTTP Status Codes
- **200 OK**: Successful operation
- **201 Created**: Resource created successfully
- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Missing or invalid authentication
- **403 Forbidden**: Access denied (not resource owner)
- **404 Not Found**: Resource not found
- **409 Conflict**: Resource already exists
- **422 Unprocessable Entity**: Validation error
- **500 Internal Server Error**: Server error

### Error Examples

**Validation Error**:
```json
{
  "detail": "Tag must be 50 characters or less",
  "status_code": 400
}
```

**Authorization Error**:
```json
{
  "detail": "Not authorized to modify this note",
  "status_code": 403
}
```

**Not Found Error**:
```json
{
  "detail": "Template not found", 
  "status_code": 404
}
```

---

## 🧪 TESTING EXAMPLES

### Using cURL

**Create Template**:
```bash
curl -X POST https://insight-api.preview.emergentagent.com/api/templates \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Client Call",
    "title_template": "Call with {date}",
    "category": "call",
    "tags": ["client", "call"]
  }'
```

**Add Tag to Note**:
```bash
curl -X POST https://insight-api.preview.emergentagent.com/api/notes/abc123/tags \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tag": "important"}'
```

**Search Notes by Tag**:
```bash
curl https://insight-api.preview.emergentagent.com/api/notes/by-tag/meeting \
  -H "Authorization: Bearer $JWT_TOKEN"
```

### Using JavaScript/Axios

```javascript
// Get user templates
const templates = await axios.get('/api/templates', {
  headers: { Authorization: `Bearer ${token}` }
});

// Create note with template
const response = await axios.post('/api/notes', {
  title: template.title_template.replace('{date}', new Date().toLocaleDateString()),
  kind: 'text',
  tags: template.tags
});

// Update note transcript
await axios.put(`/api/notes/${noteId}`, {
  artifacts: {
    transcript: editedContent,
    text: editedContent
  }
});
```

---

## 🔒 SECURITY CONSIDERATIONS

### Authentication Requirements
- All endpoints require valid JWT token
- Tokens expire after 24 hours
- User can only access their own resources

### Data Validation
- All inputs sanitized and validated
- SQL injection prevention
- XSS protection on text fields
- File upload size limits enforced

### Rate Limiting
- 100 requests per minute per user
- Burst protection for resource-intensive operations
- Automatic throttling for abuse prevention

---

## 📚 SDK Examples

### Python SDK
```python
import requests

class AutoMeAPI:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {'Authorization': f'Bearer {token}'}
    
    def create_template(self, name, title_template, category='general', tags=None):
        data = {
            'name': name,
            'title_template': title_template,
            'category': category,
            'tags': tags or []
        }
        return requests.post(f'{self.base_url}/templates', 
                           json=data, headers=self.headers)
    
    def add_tag(self, note_id, tag):
        return requests.post(f'{self.base_url}/notes/{note_id}/tags',
                           json={'tag': tag}, headers=self.headers)
```

### JavaScript SDK
```javascript
class AutoMeAPI {
  constructor(baseUrl, token) {
    this.baseUrl = baseUrl;
    this.token = token;
  }
  
  async searchNotes(query) {
    // Client-side implementation using tag filtering
    const notes = await this.getNotes();
    return notes.filter(note => 
      note.title.toLowerCase().includes(query.toLowerCase()) ||
      note.artifacts?.transcript?.toLowerCase().includes(query.toLowerCase())
    );
  }
  
  async useTemplate(templateId) {
    const response = await fetch(`${this.baseUrl}/templates/${templateId}/use`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      }
    });
    return response.json();
  }
}
```

---

**API Version**: 2.1.0  
**Last Updated**: September 11, 2025  
**Stability**: Production Ready  
**Breaking Changes**: None (backward compatible)