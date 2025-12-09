terraform {
  required_version = ">= 1.4"
  backend "s3" {
    region         = "eu-west-1"
    bucket         = "bsbingo-terraform-state"
    key            = "bsbingo.sandbox.json"
    encrypt        = true
    dynamodb_table = "bsbingo-terraform-state"
  }
}

module "global_variables" {
  source = "../modules/global_variables"
}
