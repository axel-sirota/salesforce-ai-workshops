#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Workshop Infrastructure Deployment ==="

# Step 1: Terraform
echo ""
echo ">>> Step 1: Creating infrastructure with Terraform..."
cd "$DEPLOY_DIR/terraform"

if [ ! -d ".terraform" ]; then
    terraform init
fi

PLAN_FILE="terraform_plans/$(date +%Y%m%d_%H%M%S).tfplan"
mkdir -p terraform_plans
terraform plan -out="$PLAN_FILE"
terraform apply "$PLAN_FILE"

# Get server IP
SERVER_IP=$(terraform output -raw server_ip)
echo "Server IP: $SERVER_IP"

# Step 2: Generate Ansible inventory
echo ""
echo ">>> Step 2: Generating Ansible inventory..."
cd "$DEPLOY_DIR/ansible"

cat > inventory/hosts.yml << EOF
all:
  hosts:
    workshop:
      ansible_host: $SERVER_IP
      ansible_user: root
  vars:
    workshop_domain: "$SERVER_IP"
    htpasswd_user: workshop
    htpasswd_password: salesforce2025
EOF

# Step 3: Wait for SSH
echo ""
echo ">>> Step 3: Waiting for SSH to be available..."
until ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@$SERVER_IP "echo SSH ready" 2>/dev/null; do
    echo "Waiting for SSH..."
    sleep 5
done

# Step 4: Run Ansible
echo ""
echo ">>> Step 4: Provisioning with Ansible..."
ansible-playbook playbooks/workshop.yml

# Done
echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Jaeger UI: https://$SERVER_IP/jaeger"
echo "Username: workshop"
echo "Password: salesforce2025"
echo ""
echo "OTLP Endpoint: http://$SERVER_IP:4317"
echo ""
echo "SSH: ssh root@$SERVER_IP"
