terraform {
  required_version = ">= 1.4"
  backend "s3" {
    region         = "us-east-1"
    bucket         = "bsbingo-terraform-state"
    key            = "bsbingo.staging.json"
    encrypt        = true
    dynamodb_table = "bsbingo-terraform-state"
  }
}
