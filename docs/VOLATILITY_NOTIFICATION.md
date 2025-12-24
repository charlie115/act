# Volatility Notification Feature

This document describes the volatility notification feature that sends Telegram notifications to users when market volatility exceeds their configured thresholds.

## Overview

The volatility notification system allows users to:
- Configure volatility thresholds for specific market combinations
- Receive Telegram notifications when volatility exceeds their thresholds
- Control notification frequency with configurable intervals

## Architecture

### Components

1. **Model** (`infocore/models.py`)
   - `VolatilityNotificationConfig`: Stores user notification configurations

2. **Celery Task** (`infocore/tasks.py`)
   - `check_volatility_notifications`: Periodic task that monitors volatility and creates notifications

3. **API Endpoints** (`infocore/views.py`, `infocore/urls/urls.py`)
   - REST API for managing notification configurations

4. **Admin Interface** (`infocore/admin.py`)
   - Django admin interface for managing configurations

### Data Flow

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Celery Beat    │────>│  Celery Worker   │────>│    MongoDB      │
│  (every 30s)    │     │  (check task)    │     │ (volatility)    │
└─────────────────┘     └────────┬─────────┘     └─────────────────┘
                                 │
                                 v
                        ┌────────────────┐
                        │  PostgreSQL    │
                        │  (configs)     │
                        └────────┬───────┘
                                 │
                                 v
                        ┌────────────────┐     ┌─────────────────┐
                        │  Message DB    │────>│  Telegram Bot   │
                        │  (messagecore) │     │  (PM2 process)  │
                        └────────────────┘     └─────────────────┘
```

## Model: VolatilityNotificationConfig

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `user` | ForeignKey | The user who owns this configuration |
| `target_market_code` | CharField | Target market code (e.g., "UPBIT_SPOT/KRW") |
| `origin_market_code` | CharField | Origin market code (e.g., "BINANCE_USD_M/USDT") |
| `base_assets` | JSONField | Optional list of base assets to monitor (e.g., ["BTC", "ETH"]). Null = all assets |
| `volatility_threshold` | DecimalField | Trigger notification when `mean_diff` >= this value (e.g., 0.05 = 5%) |
| `notification_interval_minutes` | PositiveIntegerField | Minimum minutes between notifications (default: 180 = 3 hours) |
| `enabled` | BooleanField | Whether this config is active (default: True) |
| `last_notified_at` | DateTimeField | Timestamp of last notification sent |
| `created_at` | DateTimeField | When the config was created |
| `updated_at` | DateTimeField | When the config was last updated |

### Constraints

- Unique constraint on `(user, target_market_code, origin_market_code)` - a user can only have one config per market combination

## API Endpoints

### Base URL
```
/infocore/volatility-notifications/
```

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/volatility-notifications/` | List user's notification configs |
| POST | `/volatility-notifications/` | Create a new notification config |
| GET | `/volatility-notifications/{id}/` | Retrieve a specific config |
| PUT | `/volatility-notifications/{id}/` | Fully update a config |
| PATCH | `/volatility-notifications/{id}/` | Partially update a config |
| DELETE | `/volatility-notifications/{id}/` | Delete a config |

### Request/Response Examples

#### Create a notification config

**Request:**
```json
POST /infocore/volatility-notifications/
{
    "target_market_code": "UPBIT_SPOT/KRW",
    "origin_market_code": "BINANCE_USD_M/USDT",
    "base_assets": ["BTC", "ETH", "XRP"],
    "volatility_threshold": "0.05",
    "notification_interval_minutes": 180,
    "enabled": true
}
```

**Response:**
```json
{
    "id": 1,
    "target_market_code": "UPBIT_SPOT/KRW",
    "origin_market_code": "BINANCE_USD_M/USDT",
    "base_assets": ["BTC", "ETH", "XRP"],
    "volatility_threshold": "0.050000",
    "notification_interval_minutes": 180,
    "enabled": true,
    "last_notified_at": null,
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T10:30:00Z"
}
```

#### List notification configs

**Request:**
```
GET /infocore/volatility-notifications/
```

**Response:**
```json
{
    "results": [
        {
            "id": 1,
            "target_market_code": "UPBIT_SPOT/KRW",
            "origin_market_code": "BINANCE_USD_M/USDT",
            "base_assets": ["BTC", "ETH", "XRP"],
            "volatility_threshold": "0.050000",
            "notification_interval_minutes": 180,
            "enabled": true,
            "last_notified_at": "2025-01-15T12:00:00Z",
            "created_at": "2025-01-15T10:30:00Z",
            "updated_at": "2025-01-15T10:30:00Z"
        }
    ]
}
```

### Query Parameters (List endpoint)

| Parameter | Description |
|-----------|-------------|
| `target_market_code` | Filter by target market code |
| `origin_market_code` | Filter by origin market code |
| `enabled` | Filter by enabled status (true/false) |

## Celery Task

### Task: `check_volatility_notifications`

- **Schedule**: Runs every 30 seconds
- **Location**: `infocore.tasks.check_volatility_notifications`

### Task Logic

1. Fetches all enabled `VolatilityNotificationConfig` entries
2. For each config:
   - Checks if enough time has passed since `last_notified_at` (rate limiting)
   - Fetches current volatility data from MongoDB
   - Identifies assets where `mean_diff >= volatility_threshold`
   - If any assets exceed threshold, creates a Message record
   - Updates `last_notified_at` timestamp

### Task Statistics

The task returns statistics about its execution:
```python
{
    "configs_checked": 10,
    "notifications_sent": 2,
    "configs_skipped_interval": 5,
    "configs_skipped_no_alerts": 3,
    "errors": 0
}
```

## Message Format

When volatility exceeds the threshold, a Telegram message is created with:

**Title:** `Volatility Alert`

**Content:**
```
Market: UPBIT_SPOT/KRW:BINANCE_USD_M/USDT
Threshold: 5.00%

Assets exceeding threshold:
  BTC: 7.25%
  ETH: 6.10%
  XRP: 5.50%
```

## Installation

### 1. Apply Migrations

Run the following commands inside the Django container:

```bash
# Create migration
python manage.py makemigrations infocore

# Apply migration
python manage.py migrate
```

### 2. Restart Celery Services

After updating the code, restart Celery worker and beat:

```bash
# If using Docker Compose
docker compose restart celery-worker celery-beat

# Or if running directly
celery -A config worker -l INFO
celery -A config beat -l INFO
```

### 3. Verify Setup

1. Check the admin interface at `/admin/infocore/volatilitynotificationconfig/`
2. Create a test config via API or admin
3. Monitor Celery logs for task execution

## Configuration

### Celery Beat Schedule

The task is scheduled in `config/celery.py`:

```python
celery.conf.beat_schedule = {
    "check_volatility_notifications": {
        "task": "infocore.tasks.check_volatility_notifications",
        "schedule": 30.0,  # Runs every 30 seconds
    },
}
```

### Adjusting Check Frequency

To change how often the task runs, modify the `schedule` value:
- `30.0` = every 30 seconds
- `60.0` = every minute
- `crontab(minute="*/5")` = every 5 minutes

## Requirements

### User Requirements

For a user to receive notifications:
1. Must have `telegram_chat_id` configured in their user profile
2. Must have a Telegram bot linked via `UserSocialApps`

### System Requirements

1. Celery worker and beat must be running
2. MongoDB must be accessible (for volatility data)
3. Redis must be accessible (for Celery broker)
4. Telegram bot service must be running (PM2 process)

## Troubleshooting

### Notifications not being sent

1. **Check user has Telegram configured:**
   ```sql
   SELECT telegram_chat_id FROM users_user WHERE id = <user_id>;
   ```

2. **Check user has linked Telegram bot:**
   ```sql
   SELECT * FROM socialaccounts_usersocialapps
   WHERE user_id = <user_id>;
   ```

3. **Check Celery logs for errors:**
   ```bash
   docker compose logs celery-worker
   ```

4. **Check if config is enabled:**
   ```sql
   SELECT * FROM infocore_volatilitynotificationconfig
   WHERE user_id = <user_id> AND enabled = true;
   ```

### Messages not being delivered

1. **Check Message table:**
   ```sql
   SELECT * FROM messagecore_message
   WHERE origin = 'volatility_monitor'
   ORDER BY datetime DESC LIMIT 10;
   ```

2. **Check if Telegram bot process is running:**
   ```bash
   pm2 list | grep telegram
   ```

## Files Modified/Created

| File | Action | Description |
|------|--------|-------------|
| `apps/infocore/models.py` | Modified | Added `VolatilityNotificationConfig` model |
| `apps/infocore/tasks.py` | Created | Celery task for checking volatility |
| `apps/infocore/serializers.py` | Modified | Added serializer for the model |
| `apps/infocore/views.py` | Modified | Added ViewSet for API endpoints |
| `apps/infocore/urls/urls.py` | Modified | Added router for ViewSet |
| `apps/infocore/admin.py` | Modified | Added admin interface |
| `config/celery.py` | Modified | Added beat schedule entry |
