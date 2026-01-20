resource "hcloud_firewall" "workshop" {
  name = "${var.workshop_name}-firewall"

  # SSH
  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "22"
    source_ips = ["0.0.0.0/0", "::/0"]
  }

  # HTTP (redirect to HTTPS)
  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "80"
    source_ips = ["0.0.0.0/0", "::/0"]
  }

  # HTTPS (nginx with basic auth)
  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "443"
    source_ips = ["0.0.0.0/0", "::/0"]
  }

  # OTLP gRPC (for traces)
  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "4317"
    source_ips = ["0.0.0.0/0", "::/0"]
  }

  # OTLP HTTP (for traces)
  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "4318"
    source_ips = ["0.0.0.0/0", "::/0"]
  }
}

resource "hcloud_firewall_attachment" "workshop" {
  firewall_id = hcloud_firewall.workshop.id
  server_ids  = [hcloud_server.workshop.id]
}
