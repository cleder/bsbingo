variable "account_id" {
  description = "The AWS account ID"
  type        = string
  default     = "000000000000"
}

variable "aws_region" {
  type        = string
  description = "AWS Region"
  default     = "eu-west-1"
}

variable "app_name" {
  description = "Application Name"
  type        = string
  default     = "bsbingo"
}

variable "environment" {
  description = "Environment Name"
  type        = string
  default     = "sandbox"
}

variable "cluster_name" {
  description = "Name of cluster"
  type        = string
  default     = "bsbingo-sandbox"
}

variable "domain_name" {
  type    = string
  default = "example.test"
}

variable "api_domain_name" {
  type    = string
  default = "api.example.test"
}

variable "cluster_domain_name" {
  type    = string
  default = "k8s.example.test"
}


variable "argocd_domain_name" {
  type    = string
  default = "argocd.example.test"
}


variable "prometheus_domain_name" {
  type    = string
  default = "prometheus.example.test"
}

variable "kubernetes_version" {

  description = "Kubernetes version to use for the cluster, if not set the k8s version shipped with the talos sdk or k3s version will be used"
  type        = string
  default     = null
}

variable "control_plane" {
  description = "Info for control plane that will be created"
  type = object({
    instance_type      = optional(string, "t3a.medium")
    ami_id             = optional(string, null)
    num_instances      = optional(number, 3)
    config_patch_files = optional(list(string), [])
    tags               = optional(map(string), {})
    disk_size          = optional(number, 100)
  })

  validation {
    condition     = var.control_plane.ami_id != null ? (length(var.control_plane.ami_id) > 4 && substr(var.control_plane.ami_id, 0, 4) == "ami-") : true
    error_message = "The ami_id value must be a valid AMI id, starting with \"ami-\"."
  }

  default = {}
}

variable "cluster_vpc_cidr" {
  description = "The IPv4 CIDR block for the VPC."
  type        = string
  default     = "172.16.0.0/16"
}



variable "repo_name" {
  type    = string
  default = "bsbingo"
}

variable "repo_url" {
  type    = string
  default = "git@github.com:cleder/bsbingo.git"
}



variable "backend_ecr_repo" {
  description = "The backend ECR repository name"
  type        = string
  default     = "bsbingo-sandbox-backend"
}

variable "admin_allowed_ips" {
  description = "A list of CIDR blocks that are allowed to access the kubernetes api"
  type        = string
  default     = "0.0.0.0/0"
}

variable "tags" {
  type    = map(string)
  default = {}
}

variable "existing_hosted_zone" {
  description = "Name of existing hosted zone to use instead of creating a new one"
  type        = string
  default     = ""
}
