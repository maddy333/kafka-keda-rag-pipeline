output "gcs_bucket_name" {
  value       = google_storage_bucket.raw_documents.name
  description = "Created GCS Bucket Name"
}

output "artifact_registry_url" {
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.rag_repo.repository_id}"
  description = "Artifact Registry Docker URL"
}

output "gke_cluster_name" {
  value       = google_container_cluster.gke_cluster.name
  description = "GKE Cluster Name"
}

output "service_account_email" {
  value       = google_service_account.rag_sa.email
  description = "GCP Service Account Email for Workload Identity"
}
