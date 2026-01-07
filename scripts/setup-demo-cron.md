# Setting Up Automatic Demo Reset

This guide shows how to configure the demo environment to automatically reset every 24 hours using cron.

## Option 1: Using crontab (Linux/macOS)

### 1. Make the reset script executable
```bash
chmod +x scripts/reset-demo.sh
```

### 2. Edit your crontab
```bash
crontab -e
```

### 3. Add one of these cron entries

**Reset every day at 3:00 AM:**
```cron
0 3 * * * /path/to/raisemyhand/scripts/reset-demo.sh >> /var/log/raisemyhand-demo-reset.log 2>&1
```

**Reset every day at midnight:**
```cron
0 0 * * * /path/to/raisemyhand/scripts/reset-demo.sh >> /var/log/raisemyhand-demo-reset.log 2>&1
```

**Reset every 24 hours from now:**
```cron
0 */24 * * * /path/to/raisemyhand/scripts/reset-demo.sh >> /var/log/raisemyhand-demo-reset.log 2>&1
```

### 4. Replace `/path/to/raisemyhand` with your actual path

Example:
```cron
0 3 * * * /home/user/repos/raisemyhand/scripts/reset-demo.sh >> /var/log/raisemyhand-demo-reset.log 2>&1
```

### 5. Verify the cron job
```bash
crontab -l
```

## Option 2: Using systemd timer (Linux only)

### 1. Create a systemd service

Create `/etc/systemd/system/raisemyhand-demo-reset.service`:
```ini
[Unit]
Description=Reset RaiseMyHand Demo Environment
After=docker.service

[Service]
Type=oneshot
ExecStart=/path/to/raisemyhand/scripts/reset-demo.sh
User=your-username
StandardOutput=journal
StandardError=journal
```

### 2. Create a systemd timer

Create `/etc/systemd/system/raisemyhand-demo-reset.timer`:
```ini
[Unit]
Description=Reset RaiseMyHand Demo Daily
Requires=raisemyhand-demo-reset.service

[Timer]
OnCalendar=daily
OnCalendar=*-*-* 03:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

### 3. Enable and start the timer
```bash
sudo systemctl daemon-reload
sudo systemctl enable raisemyhand-demo-reset.timer
sudo systemctl start raisemyhand-demo-reset.timer
```

### 4. Check timer status
```bash
sudo systemctl status raisemyhand-demo-reset.timer
sudo systemctl list-timers
```

## Option 3: Manual Reset (No automation)

You can also reset the demo environment manually at any time:

```bash
./scripts/reset-demo.sh
```

Or using Docker Compose directly:
```bash
docker compose -f docker-compose.demo.yml down
docker volume rm raisemyhand_demo-data
docker compose -f docker-compose.demo.yml up -d
```

## Verifying the Reset

After a reset, you can verify:

1. Check container logs:
   ```bash
   docker compose -f docker-compose.demo.yml logs
   ```

2. Visit http://localhost:8000 and verify fresh demo data is loaded

3. Check reset log file (if using cron):
   ```bash
   tail -f /var/log/raisemyhand-demo-reset.log
   ```

## Troubleshooting

**Cron job not running:**
- Verify cron service is running: `sudo systemctl status cron` (Linux) or `sudo launchctl list | grep cron` (macOS)
- Check cron logs: `grep CRON /var/log/syslog` (Linux) or `log show --predicate 'process == "cron"' --last 1h` (macOS)
- Ensure script has execute permissions: `ls -l scripts/reset-demo.sh`

**Docker permission issues:**
- Add your user to the docker group: `sudo usermod -aG docker $USER`
- Log out and back in for changes to take effect

**Container fails to start:**
- Check Docker logs: `docker compose -f docker-compose.demo.yml logs`
- Verify demo data exists: `ls -la demo/data/physics_101/`
- Manually test the reset script: `./scripts/reset-demo.sh`

## Changing Reset Time

To change when the demo resets, edit the cron schedule:

- **Every 12 hours:** `0 */12 * * *`
- **Every 6 hours:** `0 */6 * * *`
- **Twice daily (6 AM and 6 PM):** `0 6,18 * * *`
- **Monday mornings only:** `0 3 * * 1`

Format: `minute hour day month day-of-week`
