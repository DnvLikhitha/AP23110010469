# Stage 1

REST API Design for Notifications.

Core Actions:
- Get all unread notifications
- Mark a notification as read

**1. Fetch Notifications**
Endpoint: `GET /api/notifications`
Headers: `Authorization: Bearer <token>`
Response:
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid-string",
      "type": "Placement",
      "message": "CSX Corporation hiring",
      "timestamp": "2026-04-22 17:51:18"
    }
  ]
}
```

**2. Mark as read**
Endpoint: `PUT /api/notifications/{id}/read`
Headers: `Authorization: Bearer <token>`
Response:
```json
{
  "success": true,
  "message": "updated"
}
```

**Real-time mechanism:**
I suggest using Server-Sent Events (SSE). Since notifications just flow from server to client mostly, SSE is lightweight and very easy to set up compared to WebSockets.

---
# Stage 2

**DB Choice:** 
PostgreSQL (Relational). Since we have clear relationships between students and structured notification types, SQL is a safe choice.

**Schema:**
Table: `notifications`
- `id` (UUID, Primary Key)
- `student_id` (Int, Indexed)
- `type` (Enum: Event, Result, Placement)
- `message` (Text)
- `is_read` (Boolean, default false)
- `created_at` (Timestamp)

**Scaling Problems:**
As rows increase, reading becomes slow. To fix this we can:
1. Add composite indexes.
2. Archive older read notifications into cold storage tables.

**Queries:**
```sql
-- fetch unread
SELECT * FROM notifications WHERE student_id = 1 AND is_read = false;

-- mark as read
UPDATE notifications SET is_read = true WHERE id = 'uuid-val';
```

---
# Stage 3

**Is the query accurate and why is it slow?**
Yes, it is accurate. But scanning 5 million rows without an index takes a lot of time. 

**What I would change:**
I would add a composite index on `(studentID, isRead, createdAt)`. Cost is a little extra disk space and slight delay on inserts, but read speed becomes super fast.

**Is adding index on every column good?**
No. It slows down every insert and update because DB has to rebuild many indexes. It also wastes storage.

**Query for 7 days placements:**
```sql
SELECT DISTINCT student_id 
FROM notifications 
WHERE notificationType = 'Placement' 
AND created_at >= NOW() - INTERVAL '7 days';
```

---
# Stage 4

**Solution for DB load on page refreshes:**
Implement a caching layer using Redis. When a student loads the page, fetch unread count from Redis RAM directly. We also shift from polling to the SSE real-time mechanism we decided in Stage 1, so the client doesn't need to ask the DB on every load.

**Tradeoffs:**
- Redis: Needs extra RAM memory which costs money. Cache invalidation (keeping DB and Redis synced) can be tricky.
- Real-time SSE: Server has to keep open connections which eats up connection limits.

---
# Stage 5

**Shortcomings of current pseudocode:**
- It works sequentially (one by one). For 50k users, it takes hours.
- If `send_email` fails on student 200, the loop crashes and the remaining 49,800 students get nothing.
- DB save and email shouldn't be tied together in main thread.

**Redesign:**
Use a message broker/queue like RabbitMQ or Celery. We bulk insert to DB fast, then push to a background worker to handle emails safely.

**Revised Pseudocode:**
```python
function notify_all(student_ids, message):
    # Do this fast in one DB query
    bulk_insert_to_db(student_ids, message)
    
    # send jobs to background queue
    for sid in student_ids:
        push_to_email_queue(sid, message)
        push_to_live_notification(sid, message)

function email_worker(job):
    try:
        send_email(job.sid, job.message)
    except:
        # if it fails, retry later, don't break others
        retry_later(job)
```

---
# Stage 6

**Approach for Priority Inbox:**
I created a script in Python inside the `notification_app_be` folder. 
1. Fetched data using the provided evaluation API.
2. I assigned weight integers: Placement = 3, Result = 2, Event = 1.
3. I sorted the data first by the weight score (descending) and then by the `Timestamp` (descending for recency).
4. Sliced the array to keep only the top 10 items.

To maintain this efficiently when new notifications arrive, instead of sorting the entire huge array every time, we can use a Min-Heap (Priority Queue) data structure or keep a sorted Redis Set (ZSET) that auto-sorts new items on insertion.