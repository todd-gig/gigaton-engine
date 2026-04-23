variable "project_id" {
  type        = string
  description = "GCP project ID"
}

variable "region" {
  type        = string
  default     = "us-central1"
  description = "GCP region for Cloud Run deployment"
}

variable "environment" {
  type        = string
  default     = "production"
  description = "Deployment environment"
}

variable "image_tag" {
  type        = string
  default     = "latest"
  description = "Container image tag"
}

variable "cpu" {
  type        = string
  default     = "1"
  description = "CPU allocation for Cloud Run"
}

variable "memory" {
  type        = string
  default     = "512Mi"
  description = "Memory allocation for Cloud Run"
}

variable "min_instances" {
  type        = number
  default     = 0
  description = "Minimum Cloud Run instances (0 = scale to zero)"
}

variable "max_instances" {
  type        = number
  default     = 5
  description = "Maximum Cloud Run instances"
}

variable "allow_unauthenticated" {
  type        = bool
  default     = false
  description = "Allow unauthenticated access to the API"
}

variable "apollo_mock_mode" {
  type        = bool
  default     = true
  description = "Run Apollo enrichment in mock mode"
}

variable "silence_recovery_enabled" {
  type        = bool
  default     = true
  description = "Enable silence recovery engine"
}

variable "silence_recovery_dry_run" {
  type        = bool
  default     = true
  description = "Run silence recovery in dry-run mode (no actual actions)"
}

variable "max_daily_actions" {
  type        = number
  default     = 50
  description = "Maximum daily automated actions"
}
