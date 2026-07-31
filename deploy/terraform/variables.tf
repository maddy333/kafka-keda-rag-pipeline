variable "project_id" {
  type        = string
  description = "GCP Project ID"
}

variable "region" {
  type        = string
  default     = "us-central1"
  description = "GCP Region for resources"
}

variable "gke_cluster_name" {
  type        = string
  default     = "distributed-rag-gke"
  description = "Name of the GKE Cluster"
}

variable "gcs_bucket_name" {
  type        = string
  default     = "distributed-rag-raw-documents"
  description = "Name of GCS Bucket for raw documents"
}

variable "artifact_repository_id" {
  type        = string
  default     = "distributed-rag-repo"
  description = "Artifact Registry Repository ID"
}
