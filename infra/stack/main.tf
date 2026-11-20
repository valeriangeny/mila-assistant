# -----------------------------------------------------------------------------
# main.tf — Project-level stack (once per GCP project)
#
# Creates: project APIs, Artifact Registry, WIF + deploy SA, IAP OAuth settings.
# Does not create: Cloud Run, Qdrant, secrets, logical DBs.
#
# Apply before any env in this project:
#   terraform -chdir=stack init -reconfigure -backend-config=backends/nonprod.hcl
#   terraform -chdir=stack apply -var-file=../envs/nonprod.tfvars
# -----------------------------------------------------------------------------

locals {
  enabled_apis = [
    "iam.googleapis.com",
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "iamcredentials.googleapis.com",
    "sts.googleapis.com",
    "cloudbuild.googleapis.com",
    "secretmanager.googleapis.com",
    # Agent (LangGraph) + Copilot behind IAP HTTPS LB + Vertex
    "compute.googleapis.com",
    "iap.googleapis.com",
    "aiplatform.googleapis.com",
  ]

  # AR: mila-nonprod-api. SA: gh-deploy-nonprod.
  prefix = "${var.name_prefix}-${var.environment}"

  common_labels = {
    app         = var.name_prefix
    environment = var.environment
    managed_by  = "terraform"
  }
}

module "project_apis" {
  source = "../modules/project_apis"

  project_id = var.project_id
  apis       = local.enabled_apis
}

module "artifact_registry" {
  source = "../modules/artifact_registry"

  depends_on = [module.project_apis]

  project_id  = var.project_id
  region      = var.region
  prefix      = local.prefix
  environment = var.environment
  labels      = local.common_labels
}

module "github_deploy" {
  source = "../modules/github_deploy"

  depends_on = [module.project_apis, module.artifact_registry]

  project_id                 = var.project_id
  environment                = var.environment
  artifact_registry_location = module.artifact_registry.location
  artifact_registry_name     = module.artifact_registry.name
  github_repository          = var.github_repository
}
