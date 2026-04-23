terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ── Enable required APIs ────────────────────────────────────────

resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
  ])
  project = var.project_id
  service = each.value
}

# ── Artifact Registry for container images ──────────────────────

resource "google_artifact_registry_repository" "gigaton" {
  location      = var.region
  repository_id = "gigaton-engine"
  format        = "DOCKER"
  description   = "Gigaton Sovereign Intelligence Engine container images"

  depends_on = [google_project_service.apis]
}

# ── Service Account ─────────────────────────────────────────────

resource "google_service_account" "gigaton" {
  account_id   = "gigaton-engine"
  display_name = "Gigaton Engine Service Account"
}

# ── Cloud Run Service ───────────────────────────────────────────

resource "google_cloud_run_v2_service" "gigaton" {
  name     = "gigaton-engine"
  location = var.region

  template {
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/gigaton-engine/api:${var.image_tag}"

      ports {
        container_port = 8080
      }

      resources {
        limits = {
          cpu    = var.cpu
          memory = var.memory
        }
      }

      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }

      env {
        name  = "APOLLO_MOCK_MODE"
        value = var.apollo_mock_mode ? "true" : "false"
      }

      env {
        name  = "SIE_SILENCE_RECOVERY_ENABLED"
        value = var.silence_recovery_enabled ? "true" : "false"
      }

      env {
        name  = "SIE_SILENCE_RECOVERY_DRY_RUN"
        value = var.silence_recovery_dry_run ? "true" : "false"
      }

      env {
        name  = "SIE_MAX_DAILY_ACTIONS"
        value = tostring(var.max_daily_actions)
      }
    }

    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    service_account = google_service_account.gigaton.email
  }

  depends_on = [
    google_project_service.apis,
    google_artifact_registry_repository.gigaton,
  ]
}

# ── Allow unauthenticated access (API has its own auth) ─────────

resource "google_cloud_run_v2_service_iam_member" "public" {
  count    = var.allow_unauthenticated ? 1 : 0
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.gigaton.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
