# Stubble2Power — AWS Production Operations & Deployment Runbook

**Document ID:** S2P-DOC-AWS-DEP-2026-V1  
**Classification:** Site Reliability, Cloud Engineering & DevOps Operations  
**Platform Version:** v2.5.0  
**Target Cloud:** Amazon Web Services (AWS)  
**Primary Region:** `ap-south-1` (Mumbai, India)  
**Admin / Contact:** `meenal.iitpatna@gmail.com`  

---

## 1. System Topology Overview on AWS

Stubble2Power is architected for enterprise-grade deployment on Amazon Web Services. It supports two primary deployment topologies depending on cost and operational preferences:

### Architecture: Production EC2 + PostGIS + Nginx + SSL (Recommended)

```mermaid
graph TD
    User["End User (Web / Mobile Browser)"]
    Admin["Meenal Sinha (Administrator)"]

    subgraph AWSCloud["AWS Cloud (Region: ap-south-1 Mumbai)"]
        subgraph EdgeTier["Edge & Ingress Tier"]
            Route53["Amazon Route 53 / DNS"]
            NginxProxy["Hardened Nginx Reverse Proxy (Ports 80/443 + Let's Encrypt SSL)"]
        end

        subgraph ComputeTier["Compute & Application Tier (EC2 Instance: t3.medium)"]
            subgraph DockerNetwork["Internal Bridge Network: s2p-prod-network"]
                Frontend["Streamlit UI (Port 8501, Non-Root UID 10001)"]
                Backend["FastAPI Engine (Port 8000, 4 Workers, Non-Root UID 10001)"]
                Database[("PostGIS 16-3.4 (Port 5432 Internal Only)")]
            end
            StorageVolume[("Encrypted 40GB EBS gp3: /var/lib/postgresql/data")]
            CronBackup["Daily Automated Encrypted Backup (AES-128 + SHA-256)"]
        end

        subgraph ManagementTier["AWS Management & Governance Tier"]
            SSM["AWS Systems Manager (Session Manager - Zero SSH Port Exposure)"]
            CloudWatch["Amazon CloudWatch Logs & Metrics"]
            S3Backup[("Amazon S3 Offsite Encrypted Backup Vault")]
        end
    end

    subgraph External["External Cloud APIs"]
        NASA["NASA FIRMS API (MODIS / VIIRS Ingestion)"]
    end

    User -->|HTTPS :443| Route53
    Route53 --> NginxProxy
    NginxProxy -->|HTTP :8501 + WSS stream| Frontend
    NginxProxy -->|HTTP :8000 /api/| Backend
    Frontend -->|Internal RPC| Backend
    Backend -->|Internal SQL :5432| Database
    Database --- StorageVolume
    CronBackup -->|Offsite Sync| S3Backup
    Backend -->|HTTPS Outbound| NASA
    Admin -.->|Browser Shell| SSM
```

---

## 2. Quick Deployment Methods

| Method | Best For | Estimated Monthly Cost | Setup Time | Automation Tool |
|:---|:---|:---:|:---:|:---|
| **Option A: 1-Click AWS CloudFormation** | Full Production Stack (PostGIS + Backend + Frontend + SSL) | \$25 – \$35 / month | 4 minutes | `aws/cloudformation-ec2.yml` |
| **Option B: Automated Python / Boto3 CLI** | Developers with AWS credentials on their machine | \$25 – \$35 / month | 3 minutes | `python scripts/deploy_aws.py` |
| **Option C: Bash Deployment Script** | macOS / Linux / AWS CloudShell users | \$25 – \$35 / month | 3 minutes | `bash scripts/deploy_aws.sh` |
| **Option D: AWS Lightsail VPS** | Student / Academic / Budget-Conscious Deployment | \$10 – \$20 / month | 5 minutes | Docker Compose on Lightsail Ubuntu |

---

## 3. Option A: 1-Click CloudFormation Deployment (AWS Console)

This is the easiest method requiring **no CLI tools or credentials installed locally**.

### Step 3.1: Log in to AWS Management Console
1. Navigate to [AWS Management Console](https://console.aws.amazon.com/).
2. Switch region to **Asia Pacific (Mumbai) `ap-south-1`** (or your preferred region) in the top-right navbar.

### Step 3.2: Create CloudFormation Stack
1. Open the **CloudFormation** service in the console.
2. Click **Create stack** -> **With new resources (standard)**.
3. Under **Prerequisite - Prepare template**, select **Template is ready**.
4. Under **Specify template**, select **Upload a template file** and choose:
   ```
   aws/cloudformation-ec2.yml
   ```
5. Click **Next**.

### Step 3.3: Specify Stack Parameters
Fill in the stack parameters:
- **Stack name:** `stubble2power-production`
- **AdminEmail:** `meenal.iitpatna@gmail.com`
- **InstanceType:** `t3.medium` (2 vCPU, 4GB RAM — ideal for PostGIS and ML pipelines)
- **DomainName:** *(Optional)* Enter your domain (e.g., `stubble.example.com`) if you have one.
- **NASAKey:** *(Optional)* Enter your NASA FIRMS MAP Key.
- **KeyName:** *(Optional)* Leave blank to use AWS Systems Manager browser terminal.

### Step 3.4: Review and Deploy
1. Click **Next** through Configure stack options.
2. On the Review page, check the acknowledgment box:
   `[x] I acknowledge that AWS CloudFormation might create IAM resources.`
3. Click **Submit**.

CloudFormation will automatically provision the security groups, IAM roles, encrypted EBS volume, and launch the EC2 instance. The UserData bootstrap script will automatically install Docker, pull PostGIS, FastAPI, and Streamlit, configure Nginx, and launch the platform.

### Step 3.5: Access the Application
Once the stack status reaches `CREATE_COMPLETE`:
1. Click the **Outputs** tab in CloudFormation.
2. Note the endpoints:
   - **FrontendURL:** `http://<YOUR_EC2_PUBLIC_IP>` (Streamlit UI)
   - **APIDocsURL:** `http://<YOUR_EC2_PUBLIC_IP>/docs` (Interactive FastAPI Swagger docs)
   - **HealthCheckURL:** `http://<YOUR_EC2_PUBLIC_IP>/health`
   - **SSMConsoleURL:** Direct link to open an interactive web terminal inside the server.

---

## 4. Option B: Automated Python CLI Deployment (`deploy_aws.py`)

If you have AWS credentials, you can deploy in a single command using the built-in `boto3` script:

### Step 4.1: Configure AWS Credentials
Set your credentials in PowerShell or CMD:

```powershell
$env:AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"
$env:AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
$env:AWS_REGION="ap-south-1"
```

Or pass them directly as arguments:

```bash
python scripts/deploy_aws.py deploy \
  --region ap-south-1 \
  --email meenal.iitpatna@gmail.com \
  --instance-type t3.medium
```

### Step 4.2: Check Deployment Status
```bash
python scripts/deploy_aws.py status
```

---

## 5. Option C: Deployment via AWS CloudShell / Bash Script

If using AWS CloudShell (accessible with 1 click inside the AWS Console):

```bash
git clone https://github.com/MeenalSinha/Stubble2Power.git
cd Stubble2Power
chmod +x scripts/deploy_aws.sh
./scripts/deploy_aws.sh cloudformation
```

---

## 6. Option D: Low-Cost AWS Lightsail Deployment ($10/month)

For an ultra-budget deployment:
1. Open [AWS Lightsail Console](https://lightsail.aws.amazon.com/).
2. Click **Create instance**.
3. Select **Linux/Unix**, Platform **OS Only**, and select **Ubuntu 24.04 LTS**.
4. Choose the **$10/month plan** (2 GB RAM, 1 vCPU, 60 GB SSD).
5. Name the instance `stubble2power-lightsail`.
6. Click **Create instance**.
7. In the Lightsail networking tab, open firewall ports `80` (HTTP) and `443` (HTTPS).
8. Connect to the browser terminal and run:
   ```bash
   sudo apt-get update && sudo apt-get install -y git docker.io docker-compose-v2
   git clone https://github.com/MeenalSinha/Stubble2Power.git /opt/stubble2power
   cd /opt/stubble2power
   # Generate environment secrets
   JWT_KEY=$(openssl rand -hex 32)
   DB_PWD=$(openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 24)
   cat <<EOF > .env
   APP_ENV=production
   POSTGRES_DB=stubble2power_prod
   POSTGRES_USER=s2p_admin
   POSTGRES_PASSWORD=${DB_PWD}
   DATABASE_URL=postgresql+psycopg2://s2p_admin:${DB_PWD}@db:5432/stubble2power_prod
   JWT_SECRET_KEY=${JWT_KEY}
   EOF
   docker compose -f docker-compose.prod.yml up -d
   ```

---

## 7. Domain Setup & Free SSL/TLS (Let's Encrypt)

To secure `https://s2p.yourdomain.com`:

1. **Create DNS A Record:**  
   In your domain registrar (GoDaddy, Namecheap, Route 53), create an `A` record:
   - **Host / Name:** `s2p` (or `@`)
   - **Value:** `<YOUR_EC2_PUBLIC_IP>`
   - **TTL:** 300 seconds

2. **Run Certbot on the EC2 Server:**  
   Connect via SSH or AWS SSM Session Manager, then run:
   ```bash
   sudo certbot --nginx -d s2p.yourdomain.com --non-interactive --agree-tos -m meenal.iitpatna@gmail.com --redirect
   ```
   Certbot will automatically install the certificate, configure HTTPS on port 443, and set up auto-renewal.

---

## 8. Verification & Post-Deployment Smoke Tests

Verify system health by checking the endpoints:

| Endpoint | Expected Response | Description |
|:---|:---:|:---|
| `GET http://<PUBLIC_IP>/health` | `HTTP 200 {"status": "healthy"}` | Overall system health check |
| `GET http://<PUBLIC_IP>/docs` | `HTTP 200 (HTML)` | OpenAPI Swagger documentation |
| `GET http://<PUBLIC_IP>/_stcore/health` | `HTTP 200 ok` | Streamlit core engine check |
| `GET http://<PUBLIC_IP>/` | `HTTP 200 (HTML)` | Streamlit Glassmorphism UI |

To run automated container health checks inside the server:
```bash
docker compose -f /opt/stubble2power/docker-compose.prod.yml ps
```

All 3 containers (`stubble2power-prod-db`, `stubble2power-prod-backend`, `stubble2power-prod-frontend`) should show state `Up (healthy)`.

---

## 9. Automated Database Backups & Offsite S3 Storage

The deployment script registers a daily cron job at `/etc/cron.daily/stubble2power-backup`.

### Manual Backup Execution:
```bash
cd /opt/stubble2power
docker compose -f docker-compose.prod.yml exec -T backend python scripts/backup_db.py --keep-days 14
```

### Sync Backups to Amazon S3:
To enable offsite replication to an S3 bucket:
```bash
aws s3 sync /opt/stubble2power/backups/ s3://your-s2p-backup-bucket/backups/ --sse AES256
```

---

## 10. Cost Breakdown & Optimization (AWS Mumbai Region)

| Resource | Specification | Monthly Cost (USD) |
|:---|:---|:---:|
| **EC2 Instance (`t3.medium`)** | 2 vCPU, 4.0 GiB RAM (Reserved or Savings Plan) | ~$18.00 |
| **EBS Storage (`gp3`)** | 40 GB Encrypted SSD (3000 IOPS, 125 MB/s) | ~$3.20 |
| **Data Transfer Out** | First 100 GB / month free | ~$0.00 |
| **AWS Systems Manager** | Session Manager browser terminal | Free |
| **Total Estimated Cost** | **Production Grade Stubble2Power Stack** | **~$21.20 / month** |
| *(Lightsail Alternative)* | *1 vCPU, 2.0 GiB RAM, 60 GB SSD* | *~$10.00 / month* |

---

## 11. Maintenance & Emergency Incident Response

- **View Live Logs:**
  ```bash
  docker compose -f /opt/stubble2power/docker-compose.prod.yml logs -f --tail=100 backend
  docker compose -f /opt/stubble2power/docker-compose.prod.yml logs -f --tail=100 frontend
  ```
- **Restart All Services:**
  ```bash
  sudo systemctl restart stubble2power.service
  ```
- **Database Restore:**
  ```bash
  cd /opt/stubble2power
  docker compose -f docker-compose.prod.yml exec -T backend python scripts/restore_db.py backups/<backup_file>.sql.enc
  ```
