# API Reference

Complete documentation of the Nyne.ai API endpoints and data fields used by this tool.

## Overview

All Nyne.ai endpoints are **asynchronous**:
1. Submit a request → receive a `request_id`
2. Poll the endpoint with `request_id` until `status: "completed"`
3. Access data in the `result` field

## Authentication

All requests require these headers:
```
X-API-Key: your_api_key
X-API-Secret: your_api_secret
Content-Type: application/json
```

## Endpoints

---

## 1. Person Enrichment

**Endpoint:** `POST /person/enrichment`

The primary endpoint for person data. Returns comprehensive profile information.

### Request

```json
{
  "email": "john@company.com",
  "social_media_url": "https://linkedin.com/in/johndoe",
  "newsfeed": ["all"],
  "ai_enhanced_search": true
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | One of email or social_media_url | Person's email address |
| `social_media_url` | string | One of email or social_media_url | LinkedIn, Twitter, or Instagram URL |
| `newsfeed` | array | No | Sources for posts: `["all"]`, `["linkedin"]`, `["twitter"]` |
| `ai_enhanced_search` | boolean | No | Enable AI-powered data enhancement |

### Response - Result Fields

#### Basic Info
| Field | Type | Description |
|-------|------|-------------|
| `firstname` | string | First name |
| `lastname` | string | Last name |
| `displayname` | string | Display name |
| `headline` | string | Professional headline |
| `summary` | string | Bio/about text |
| `gender` | string | Gender |
| `location` | string | Current location |
| `languages` | array | Languages spoken |

#### Contact Info
| Field | Type | Description |
|-------|------|-------------|
| `best_email` | string | Best email to use |
| `best_personal_email` | string | Personal email |
| `best_work_email` | string | Work email |
| `altemails` | array | All known emails |
| `phones` | array | Phone numbers |

#### Career History (`careers_info`)
```json
{
  "careers_info": [
    {
      "company_name": "Acme Inc",
      "company_linkedin_url": "https://linkedin.com/company/acme",
      "title": "CEO",
      "startDate": "2020-01",
      "endDate": null,
      "is_current": true,
      "location": "San Francisco, CA",
      "description": "Leading the company..."
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `company_name` | string | Company name |
| `company_linkedin_url` | string | Company LinkedIn URL |
| `title` | string | Job title |
| `startDate` | string | Start date (YYYY-MM or YYYY) |
| `endDate` | string | End date (null if current) |
| `is_current` | boolean | Currently employed here |
| `location` | string | Office location |
| `description` | string | Role description |

#### Education (`schools_info`)
```json
{
  "schools_info": [
    {
      "name": "Stanford University",
      "degree": "MBA",
      "field": "Business Administration",
      "startDate": "2015",
      "endDate": "2017",
      "linkedin_url": "https://linkedin.com/school/stanford"
    }
  ]
}
```

#### Social Profiles (`social_profiles`)
```json
{
  "social_profiles": {
    "linkedin": {
      "url": "https://linkedin.com/in/johndoe",
      "username": "johndoe"
    },
    "twitter": {
      "url": "https://twitter.com/johndoe",
      "username": "johndoe"
    },
    "instagram": {
      "url": "https://instagram.com/johndoe"
    },
    "github": {
      "url": "https://github.com/johndoe"
    },
    "youtube": {
      "url": "https://youtube.com/c/johndoe"
    },
    "medium": {
      "url": "https://medium.com/@johndoe"
    },
    "substack": {
      "url": "https://johndoe.substack.com"
    }
  }
}
```

#### Newsfeed/Posts (`newsfeed`)
```json
{
  "newsfeed": [
    {
      "id": "urn:li:activity:123456",
      "platform_id": "urn:li:activity:123456",
      "source": "linkedin",
      "content": "Excited to announce our Series A...",
      "url": "https://linkedin.com/posts/...",
      "date_posted": "2024-01-15T10:30:00Z",
      "type": "post",
      "engagement": {
        "likes": 150,
        "comments": 23,
        "shares": 12,
        "total_reactions": 185
      },
      "media": [
        {
          "image_url": "https://..."
        }
      ],
      "author": {
        "display_name": "John Doe",
        "headline": "CEO at Acme",
        "image_url": "https://...",
        "profile_url": "https://linkedin.com/in/johndoe"
      }
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `source` | string | Platform: "linkedin", "twitter" |
| `content` | string | Post text content |
| `url` | string | Direct link to post |
| `date_posted` | string | ISO 8601 timestamp |
| `engagement` | object | Likes, comments, shares |
| `media` | array | Attached images/videos |

---

## 2. Person Interactions (Following)

**Endpoint:** `POST /person/interactions`

Returns who a person follows on Twitter/X. Extremely valuable for psychographic analysis.

### Request

```json
{
  "type": "following",
  "social_media_url": "https://twitter.com/johndoe",
  "max_results": 500
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Must be `"following"` |
| `social_media_url` | string | Yes | Twitter/X profile URL |
| `max_results` | integer | No | Max accounts to return (default 500) |

### Response - Result Fields

```json
{
  "result": {
    "interactions": [
      {
        "relationship_type": "following",
        "actor": {
          "username": "elonmusk",
          "display_name": "Elon Musk",
          "id": "44196397",
          "bio": "Mars & Cars, Chips & Dips",
          "location": "Austin, Texas",
          "profile_url": "https://twitter.com/elonmusk",
          "image_url": "https://pbs.twimg.com/...",
          "banner_url": "https://pbs.twimg.com/...",
          "website": "https://x.com",
          "website_url": "https://t.co/...",
          "followers_count": "180000000",
          "following_count": "500",
          "tweets_count": "45000",
          "likes_count": "30000",
          "media_count": "1500",
          "listed_count": "150000",
          "created_at": "2009-06-02T20:12:29Z",
          "verified": "0",
          "blue_verified": "1",
          "protected": "0"
        }
      }
    ]
  }
}
```

#### Actor Fields (Each Followed Account)
| Field | Type | Description |
|-------|------|-------------|
| `username` | string | Twitter handle (without @) |
| `display_name` | string | Display name |
| `id` | string | Twitter user ID |
| `bio` | string | Profile bio |
| `location` | string | Location from profile |
| `profile_url` | string | Full profile URL |
| `image_url` | string | Profile picture URL |
| `banner_url` | string | Header image URL |
| `website` | string | Website from profile |
| `followers_count` | string | Number of followers |
| `following_count` | string | Number following |
| `tweets_count` | string | Number of tweets |
| `likes_count` | string | Number of likes |
| `created_at` | string | Account creation date |
| `verified` | string | Legacy verified ("1" or "0") |
| `blue_verified` | string | Twitter Blue verified |

---

## 3. Person Article Search

**Endpoint:** `POST /person/articlesearch`

Searches for press mentions, podcast appearances, and interviews.

### Request

```json
{
  "name": "John Doe",
  "company": "Acme Inc",
  "sort": "recent",
  "limit": 15
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Person's full name |
| `company` | string | Yes | Company name |
| `sort` | string | No | Sort order: "recent" or "relevance" |
| `limit` | integer | No | Max articles to return |

### Response - Result Fields

```json
{
  "result": {
    "articles": [
      {
        "title": "Acme Inc Raises $50M Series B",
        "url": "https://techcrunch.com/...",
        "source": "TechCrunch",
        "date": "2024-01-15",
        "snippet": "John Doe, CEO of Acme Inc, announced...",
        "type": "article"
      }
    ]
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Article title |
| `url` | string | Article URL |
| `source` | string | Publication name |
| `date` | string | Publication date |
| `snippet` | string | Excerpt mentioning the person |
| `type` | string | Content type (article, podcast, etc.) |

---

## Possible Matches (`possible_matches`)

The enrichment endpoint also returns `possible_matches` - URLs to external content:

```json
{
  "possible_matches": {
    "other": [
      "https://techcrunch.com/author/johndoe/",
      "https://www.fastcompany.com/person/john-doe",
      "https://podcasts.apple.com/podcast/interview-with-john-doe"
    ]
  }
}
```

---

## Rate Limits & Best Practices

1. **Polling interval:** Wait 5 seconds between polls
2. **Timeout:** Results typically complete within 30-60 seconds
3. **Max retries:** 60 attempts (5 minutes total)
4. **Concurrent requests:** Up to 4 parallel polls supported

## Error Handling

All endpoints return:
```json
{
  "success": true,
  "data": {
    "request_id": "abc123",
    "status": "processing"
  }
}
```

Status values:
- `processing` - Still working
- `completed` - Results ready in `result` field
- `failed` - Error occurred, check `error` field

## Example: Full Research Flow

```python
import requests
import time

headers = {
    "X-API-Key": "your_key",
    "X-API-Secret": "your_secret",
    "Content-Type": "application/json"
}

# 1. Submit enrichment request
response = requests.post(
    "https://api.nyne.ai/person/enrichment",
    headers=headers,
    json={
        "email": "ceo@company.com",
        "newsfeed": ["all"],
        "ai_enhanced_search": True
    }
)
request_id = response.json()["data"]["request_id"]

# 2. Poll for results
while True:
    response = requests.get(
        "https://api.nyne.ai/person/enrichment",
        headers=headers,
        params={"request_id": request_id}
    )
    data = response.json()["data"]

    if data["status"] == "completed":
        result = data["result"]
        break
    elif data["status"] == "failed":
        raise Exception(data.get("error"))

    time.sleep(5)

# 3. Access data
print(result["firstname"], result["lastname"])
print(result["careers_info"][0]["company_name"])
print(result["social_profiles"]["twitter"]["url"])
```
