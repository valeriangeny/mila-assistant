# -----------------------------------------------------------------------------
# main.tf — App environment (sandbox / staging / prod)
#
# Mila runtime: secrets + LangGraph agent + CopilotKit (IAP HTTPS LB).
# Knowledge: Qdrant via qdrant_url (managed or self-hosted — not Cloud SQL).
# Local mock IdP: repo-root mock-oauth2/ (Compose profile auth), not this stack.
#
#   terraform -chdir=env init -reconfigure -backend-config=backends/sandbox.hcl
#   terraform -chdir=env apply -var-file=../envs/sandbox.tfvars
# -----------------------------------------------------------------------------

locals {
  prefix = "${var.name_prefix}-${var.environment}"

  common_labels = {
    app         = var.name_prefix
    environment = var.environment
    managed_by  = "terraform"
  }

  managed_secrets = merge(
    {
      LANGSMITH_API_KEY = var.agent_langsmith_api_key
    },
    var.secret_env,
  )

  agent_image = var.agent_image != "" ? var.agent_image : (
    "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_registry_repository_id}/${local.prefix}-agent:latest"
  )

  copilot_image = var.copilot_image != "" ? var.copilot_image : (
    "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_registry_repository_id}/${local.prefix}-copilot:latest"
  )
}

module "secrets" {
  source = "../modules/secrets"

  prefix  = local.prefix
  labels  = local.common_labels
  secrets = local.managed_secrets
}

module "agent" {
  source = "../modules/agent"

  depends_on = [module.secrets]

  project_id                 = var.project_id
  prefix                     = local.prefix
  environment                = var.environment
  region                     = var.region
  labels                     = local.common_labels
  image                      = local.agent_image
  qdrant_url                 = var.qdrant_url
  artifact_registry_location = var.artifact_registry_location
  artifact_registry_name     = var.artifact_registry_name
  secret_resources           = module.secrets.secret_resources
  deploy_members = [
    "serviceAccount:${var.deploy_sa_email}",
  ]

  iap_host                = var.agent_iap_host
  copilot_host            = var.copilot_host
  copilot_image           = local.copilot_image
  iap_oauth_client_id     = var.iap_oauth_client_id
  iap_oauth_client_secret = var.iap_oauth_client_secret
  iap_members             = var.iap_members
}
