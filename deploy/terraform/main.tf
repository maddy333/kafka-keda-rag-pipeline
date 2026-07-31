terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.15.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. Google Cloud Storage Bucket for raw documents
resource "google_storage_bucket" "raw_documents" {
  name                        = "${var.project_id}-${var.gcs_bucket_name}"
  location                    = var.region
  force_destroy               = true
  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }
}

# 2. Artifact Registry for Docker images
resource "google_artifact_registry_repository" "rag_repo" {
  location      = var.region
  repository_id = var.artifact_repository_id
  description   = "Docker container repository for Distributed RAG pipeline"
  format        = "DOCKER"
}

# 3. VPC Network & Subnet
resource "google_compute_network" "vpc_network" {
  name                    = "rag-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "subnetwork" {
  name          = "rag-subnet"
  ip_cidr_range = "10.10.0.0/16"
  region        = var.region
  network       = google_compute_network.vpc_network.id
}

# 4. GKE Autopilot Cluster
resource "google_container_cluster" "gke_cluster" {
  name     = var.gke_cluster_name
  location = var.region
  network  = google_compute_network.vpc_network.name
  subnetwork = google_compute_subnetwork.subnetwork.name

  enable_autopilot = true

  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }
}

# 5. GCP Service Account for Workload Identity
resource "google_service_account" "rag_sa" {
  account_id   = "rag-workload-sa"
  display_name = "RAG Workload Service Account"
}

# 6. IAM Binding granting GCS storage object admin to Service Account
resource "google_storage_bucket_iam_binding" "gcs_admin" {
  bucket = google_storage_bucket.raw_documents.name
  role   = "roles/storage.objectAdmin"
  members = [
    "serviceAccount:${google_service_account.rag_sa.email}"
  ]
}

# 7. Workload Identity IAM binding with Kubernetes service account
resource "google_service_account_iam_binding" "workload_identity_user" {
  service_account_id = google_service_account.rag_sa.name
  role               = "roles/iam.workloadIdentityUser"

  members = [
    "serviceAccount:${var.project_id}.svc.id.goog[default/rag-workload-sa]"
  ]
}
