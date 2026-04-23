output "service_url" {
  value       = google_cloud_run_v2_service.gigaton.uri
  description = "Gigaton Engine API URL"
}

output "service_name" {
  value       = google_cloud_run_v2_service.gigaton.name
  description = "Cloud Run service name"
}

output "registry_url" {
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.gigaton.repository_id}"
  description = "Artifact Registry URL for container images"
}
