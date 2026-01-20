output "server_ip" {
  description = "Public IP of the workshop server"
  value       = hcloud_server.workshop.ipv4_address
}

output "jaeger_ui_url" {
  description = "Jaeger UI URL (requires basic auth)"
  value       = "https://${hcloud_server.workshop.ipv4_address}/jaeger"
}

output "jaeger_otlp_endpoint" {
  description = "Jaeger OTLP gRPC endpoint"
  value       = "http://${hcloud_server.workshop.ipv4_address}:4317"
}

output "ssh_command" {
  description = "SSH command to connect"
  value       = "ssh root@${hcloud_server.workshop.ipv4_address}"
}
