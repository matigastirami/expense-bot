# Enable IPv6 in Docker for Supabase Connectivity

Supabase databases use IPv6 addresses. To connect from Docker containers, you need to enable IPv6 support in Docker.

## Quick Fix (On Your Hetzner Server)

### Step 1: Check if IPv6 is Enabled in Docker

```bash
docker network inspect bridge | grep EnableIPv6
```

If it shows `"EnableIPv6": false` or nothing, you need to enable it.

### Step 2: Enable IPv6 in Docker Daemon

Edit or create the Docker daemon configuration file:

```bash
sudo nano /etc/docker/daemon.json
```

Add the following configuration (or merge with existing config):

```json
{
  "ipv6": true,
  "fixed-cidr-v6": "fd00::/64",
  "experimental": true,
  "ip6tables": true
}
```

**If the file already exists**, make sure to merge the settings properly. For example, if you have:

```json
{
  "log-driver": "json-file"
}
```

Change it to:

```json
{
  "log-driver": "json-file",
  "ipv6": true,
  "fixed-cidr-v6": "fd00::/64",
  "experimental": true,
  "ip6tables": true
}
```

### Step 3: Restart Docker

```bash
sudo systemctl restart docker
```

### Step 4: Verify IPv6 is Enabled

```bash
# Check daemon config
docker system info | grep -i ipv6

# Should show:
# IPv6: true

# Test IPv6 connectivity to Supabase
ping6 -c 3 YOUR_SUPABASE_HOST
```

### Step 5: Redeploy Your Application

```bash
cd ~/expense-bot
./deploy.sh
```

---

## Alternative: Test Without Full IPv6 Setup

If you can't enable IPv6 on the host, you can use IPv6 NAT in Docker Compose (already configured in `docker-compose.prod.yml`).

The docker-compose.prod.yml file already includes:

```yaml
networks:
  expense-tracker-network:
    driver: bridge
    enable_ipv6: true
    ipam:
      driver: default
      config:
        - subnet: 172.20.0.0/16
          gateway: 172.20.0.1
        - subnet: fd00::/64
          gateway: fd00::1
```

This creates an IPv6-enabled network for your containers.

---

## Troubleshooting

### Problem: "Cannot create network" error

If you see errors creating the network, try:

```bash
# Remove existing network
docker network rm expense-tracker-network

# Recreate with IPv6
docker network create expense-tracker-network --ipv6 --subnet=fd00::/64

# Try deployment again
./deploy.sh
```

### Problem: Still can't connect to Supabase

1. **Test IPv6 from the host:**
   ```bash
   ping6 -c 3 db.xxxxxxxxxxxxx.supabase.co
   ```

2. **Test from inside a container:**
   ```bash
   docker run --rm --network expense-tracker-network busybox ping6 -c 3 db.xxxxxxxxxxxxx.supabase.co
   ```

3. **Check if your server has IPv6:**
   ```bash
   ip -6 addr show
   ```

4. **Check Supabase IP:**
   ```bash
   nslookup db.xxxxxxxxxxxxx.supabase.co
   # or
   host db.xxxxxxxxxxxxx.supabase.co
   ```

### Problem: Hetzner IPv6 not working

Hetzner servers should have IPv6 by default. If not:

1. **Check Hetzner Cloud Console** - ensure IPv6 is enabled for your server
2. **Configure IPv6 route** (if needed):
   ```bash
   # Check current IPv6 config
   ip -6 route show
   
   # Add default IPv6 route (if missing)
   sudo ip -6 route add default via fe80::1 dev eth0
   ```

3. **Make it persistent** by editing `/etc/network/interfaces` or using netplan (Ubuntu 20.04+)

---

## Verification Checklist

After enabling IPv6, verify:

- ✅ Docker daemon has IPv6 enabled: `docker system info | grep IPv6`
- ✅ Server can ping Supabase: `ping6 db.xxxxxxxxxxxxx.supabase.co`
- ✅ Docker network has IPv6: `docker network inspect expense-tracker-network | grep IPv6`
- ✅ Container can reach internet via IPv6: `docker run --rm --network expense-tracker-network busybox ping6 -c 3 google.com`
- ✅ Migration succeeds: `./deploy.sh`

---

## Complete Example

Here's a complete example showing all commands:

```bash
# 1. Enable IPv6 in Docker
sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
  "ipv6": true,
  "fixed-cidr-v6": "fd00::/64",
  "experimental": true,
  "ip6tables": true
}
EOF

# 2. Restart Docker
sudo systemctl restart docker

# 3. Verify
docker system info | grep IPv6

# 4. Test Supabase connectivity
ping6 -c 3 db.xxxxxxxxxxxxx.supabase.co

# 5. Deploy
cd ~/expense-bot
./deploy.sh
```

---

## References

- [Docker IPv6 Documentation](https://docs.docker.com/config/daemon/ipv6/)
- [Docker Compose IPv6 Networks](https://docs.docker.com/compose/networking/#enable-ipv6)
- [Supabase Connection Issues](https://supabase.com/docs/guides/platform/going-into-prod#connection-pooling)
- [Hetzner IPv6 Setup](https://docs.hetzner.com/cloud/networks/faq#how-do-i-get-ipv6-connectivity)
