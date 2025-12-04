# URL Configuration Guide

RaiseMyHand needs to know its public URL to generate correct links for:
- Student session URLs
- QR codes
- Shared links in the instructor dashboard

## How It Works

The application uses the `BASE_URL` environment variable to generate all external links. If not set, it defaults to `http://localhost:8000`.

Additionally, the `TIMEZONE` environment variable controls how timestamps are displayed throughout the application. If not set, it defaults to `UTC`.

## Configuration Methods

### Method 1: Environment Variable (Recommended)

**For local development:**
```bash
export BASE_URL=http://localhost:8000
export TIMEZONE=America/New_York
python main.py
```

**For Docker:**
```bash
BASE_URL=https://raisemyhand.university.edu TIMEZONE=America/New_York docker-compose up -d
```

### Method 2: .env File

Create a `.env` file in the project root:
```bash
BASE_URL=https://raisemyhand.university.edu
HOST=0.0.0.0
PORT=8000
TIMEZONE=America/New_York
```

Then run:
```bash
docker-compose up -d
```

### Method 3: docker-compose.yml

Edit `docker-compose.yml` directly:
```yaml
environment:
  - BASE_URL=https://raisemyhand.university.edu
  - TIMEZONE=America/New_York
```

## Common Scenarios

### Scenario 1: Running on Laptop (Development)
```bash
# Use default - no configuration needed
python main.py
```
URLs will be: `http://localhost:8000`

### Scenario 2: Running on Local Network
```bash
# Find your local IP: ifconfig (Mac/Linux) or ipconfig (Windows)
export BASE_URL=http://192.168.1.100:8000
python main.py
```
Students can access from: `http://192.168.1.100:8000`

### Scenario 3: Docker with Custom Port
```yaml
# docker-compose.yml
ports:
  - "80:8000"  # Map host port 80 to container port 8000
environment:
  - BASE_URL=http://your-server-ip  # No port needed if using 80
```

### Scenario 4: Production with Domain
```yaml
# docker-compose.yml
environment:
  - BASE_URL=https://raisemyhand.university.edu
```

### Scenario 5: Behind nginx Reverse Proxy

**nginx configuration:**
```nginx
server {
    listen 80;
    server_name raisemyhand.university.edu;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support
    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

**docker-compose.yml:**
```yaml
environment:
  - BASE_URL=http://raisemyhand.university.edu
```

With SSL (Let's Encrypt):
```bash
# After setting up certbot
certbot --nginx -d raisemyhand.university.edu
```

Update BASE_URL:
```yaml
environment:
  - BASE_URL=https://raisemyhand.university.edu
```

## Internal vs External URLs

### Internal URL
- What the application binds to (HOST:PORT)
- Used by the server to listen for connections
- Default: `0.0.0.0:8000`

### External URL (BASE_URL)
- What users/students use to access the application
- Used in QR codes and shared links
- Examples:
  - `http://localhost:8000` (local development)
  - `http://192.168.1.100:8000` (local network)
  - `https://raisemyhand.university.edu` (production)

## Quick Reference

| Deployment | Internal (HOST:PORT) | External (BASE_URL) |
|------------|---------------------|---------------------|
| Laptop | 0.0.0.0:8000 | http://localhost:8000 |
| Local Network | 0.0.0.0:8000 | http://YOUR_IP:8000 |
| Docker (custom port) | 0.0.0.0:8000 | http://YOUR_DOMAIN:80 |
| nginx Proxy | 0.0.0.0:8000 | https://YOUR_DOMAIN |
| Cloud (Heroku, etc) | 0.0.0.0:$PORT | https://YOUR_APP.herokuapp.com |

## Verification

After configuration, check if URLs are correct:

1. **Start the application**
2. **Create a session**
3. **Check the instructor dashboard** - the "Student URL" should show your BASE_URL
4. **Generate QR code** - it should encode your BASE_URL

Test the config endpoint:
```bash
curl http://localhost:8000/api/config
# Should return: {"base_url":"YOUR_CONFIGURED_URL"}
```

## Troubleshooting

### Problem: QR codes show localhost instead of public URL
**Solution:** Set BASE_URL environment variable to your public URL

### Problem: Students can't access even though instructor can
**Solution:**
- Instructor is using `localhost`, which only works on their machine
- Set BASE_URL to your local IP or public domain
- Ensure firewall allows connections on port 8000

### Problem: URLs show wrong port
**Solution:**
- Include the port in BASE_URL if not using standard ports (80/443)
- Example: `BASE_URL=http://example.com:8000`

### Problem: WebSocket connections fail with reverse proxy
**Solution:**
- Ensure nginx config includes WebSocket upgrade headers (see example above)
- Use same protocol (http/https) in BASE_URL as external access

## Advanced: Multiple Environments

Use different .env files for different environments:

**.env.development:**
```bash
BASE_URL=http://localhost:8000
```

**.env.production:**
```bash
BASE_URL=https://raisemyhand.university.edu
```

Load with docker-compose:
```bash
docker-compose --env-file .env.production up -d
```

## Testing Different Configurations

```bash
# Test 1: Default (localhost)
python main.py

# Test 2: Local network
BASE_URL=http://192.168.1.100:8000 python main.py

# Test 3: Production URL
BASE_URL=https://raisemyhand.university.edu python main.py
```

After each test, verify the config endpoint returns the expected URL:
```bash
curl http://localhost:8000/api/config
```

## Timezone Configuration

The application supports configuring the timezone for displaying timestamps throughout the interface.

### Setting the Timezone

Use the `TIMEZONE` environment variable with any valid IANA timezone name:

```bash
# Common timezones
TIMEZONE=America/New_York
TIMEZONE=America/Los_Angeles
TIMEZONE=America/Chicago
TIMEZONE=Europe/London
TIMEZONE=Europe/Paris
TIMEZONE=Asia/Tokyo
TIMEZONE=Asia/Shanghai
TIMEZONE=Australia/Sydney
```

### Finding Your Timezone

To find valid timezone names, you can:

1. Check the [IANA timezone database](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)
2. On Linux/Mac, list available timezones:
   ```bash
   timedatectl list-timezones
   ```

### Default Behavior

- If `TIMEZONE` is not set, the application defaults to `UTC`
- If an invalid timezone is specified, the application will warn and fall back to `UTC`
- The JavaScript frontend will display times using the user's browser locale settings

### Example Configurations

**Docker Compose:**
```yaml
environment:
  - TIMEZONE=America/New_York
```

**.env file:**
```bash
TIMEZONE=America/Los_Angeles
```

**Command line:**
```bash
TIMEZONE=Europe/London python main.py
```
