# -----------------------------------------------------------------------------
# variables.tf — App environment (sandbox / staging / prod)
#
# Required stack outputs: artifact_registry_*, deploy_sa_email, iap_*.
# -----------------------------------------------------------------------------

variable "project_id" {
  type        = string
  description = "GCP project id where billing/credits apply."
}

variable "environment" {
  type        = string
  description = "App environment name (sandbox | staging | prod)."

  validation {
    condition     = contains(["sandbox", "staging", "prod"], var.environment)
    error_message = "environment must be one of: sandbox, staging, prod."
  }
}

variable "region" {
  type        = string
  description = "Region for Cloud Run."
  default     = "us-central1"
}

variable "name_prefix" {
  type        = string
  description = "Base name prefix (apps: {prefix}-{env}-…)."
  default     = "mila"
}

variable "artifact_registry_repository_id" {
  type        = string
  description = "Artifact Registry repository id from the project stack output."
}

variable "artifact_registry_location" {
  type        = string
  description = "Artifact Registry location from the project stack output."
}

variable "artifact_registry_name" {
  type        = string
  description = "Full Artifact Registry repository name from the project stack output."
}

variable "deploy_sa_email" {
  type        = string
  description = "GitHub deploy SA email from the project stack output."
}

variable "iap_oauth_client_id" {
  type        = string
  description = "IAP OAuth client ID from the project stack output."
}

variable "iap_oauth_client_secret" {
  type        = string
  description = "IAP OAuth client secret from the project stack output."
  sensitive   = true
}

variable "iap_members" {
  type        = list(string)
  description = "IAP accessors from the project stack output."
}

variable "qdrant_url" {
  type        = string
  description = "Qdrant HTTP URL for the agent (e.g. https://….qdrant.io:6333 or internal service)."
}

variable "agent_image" {
  type        = string
  description = "Full container image URI for the LangGraph agent. Empty = default …/{prefix}-agent:latest."
  default     = ""
}

variable "agent_iap_host" {
  type        = string
  description = "DNS hostname for the agent IAP HTTPS load balancer (e.g. agent.example.com)."
}

variable "copilot_host" {
  type        = string
  description = "DNS hostname for the CopilotKit copilot on the same LB IP (e.g. copilot.example.com)."
}

variable "copilot_image" {
  type        = string
  description = "Full container image URI for the copilot. Empty = default …/{prefix}-copilot:latest."
  default     = ""
}

variable "agent_langsmith_api_key" {
  type        = string
  description = "LangSmith API key — stored in Secret Manager and mounted on the agent Cloud Run service."
  sensitive   = true
}

variable "secret_env" {
  type        = map(string)
  description = "Extra sensitive env vars (Secret Manager), merged with LANGSMITH_API_KEY."
  sensitive   = true
  default     = {}
}
