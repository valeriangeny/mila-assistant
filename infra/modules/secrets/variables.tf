# -----------------------------------------------------------------------------
# modules/secrets — variables
# -----------------------------------------------------------------------------

variable "prefix" {
  type        = string
  description = "Resource name prefix (e.g. mila-sandbox)."
}

variable "labels" {
  type        = map(string)
  description = "Labels applied to secrets."
  default     = {}
}

variable "secrets" {
  type        = map(string)
  description = "Map of env var name → secret data (e.g. LANGSMITH_API_KEY)."
  sensitive   = true
}
