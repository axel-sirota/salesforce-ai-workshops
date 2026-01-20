variable "hcloud_token" {
  description = "Hetzner Cloud API token"
  type        = string
  sensitive   = true
}

variable "location" {
  description = "Hetzner datacenter location"
  type        = string
  default     = "nbg1" # Nuremberg
}

variable "server_type" {
  description = "Hetzner server type"
  type        = string
  default     = "cx23" # 2 vCPU, 4GB RAM (Gen3 cost-optimized)
}

variable "ssh_key_fingerprint" {
  description = "Fingerprint of existing SSH key in Hetzner"
  type        = string
  default     = "ea:16:44:11:14:3a:e4:ba:67:99:4f:b5:74:62:4e:a1"
}

variable "workshop_name" {
  description = "Workshop identifier"
  type        = string
  default     = "salesforce-ai-workshop"
}
