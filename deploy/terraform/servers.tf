data "hcloud_ssh_key" "workshop" {
  fingerprint = var.ssh_key_fingerprint
}

resource "hcloud_server" "workshop" {
  name        = var.workshop_name
  server_type = var.server_type
  location    = var.location
  image       = "ubuntu-24.04"
  ssh_keys    = [data.hcloud_ssh_key.workshop.id]

  labels = {
    purpose = "workshop"
    project = "salesforce-ai"
  }
}
