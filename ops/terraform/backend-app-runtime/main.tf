locals {
  stack_name = "backend-app-runtime"

  common_tags = merge(
    {
      ManagedBy = "terraform"
      Project   = "lantern"
      Stack     = local.stack_name
    },
    var.tags
  )
}

data "aws_caller_identity" "current" {}

resource "aws_iam_user" "app_runtime" {
  name = var.app_runtime_user_name
  tags = local.common_tags
}

data "aws_iam_policy_document" "backend_app_kms_key" {
  statement {
    sid    = "AllowAccountKeyAdministration"
    effect = "Allow"

    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }

    actions   = ["kms:*"]
    resources = ["*"]
  }

  statement {
    sid    = "AllowBackendAppRuntimeKmsUse"
    effect = "Allow"

    principals {
      type        = "AWS"
      identifiers = [aws_iam_user.app_runtime.arn]
    }

    actions = [
      "kms:Decrypt",
      "kms:DescribeKey",
      "kms:GenerateDataKey",
    ]

    resources = ["*"]
  }
}

resource "aws_kms_key" "backend_app" {
  description             = "Lantern backend app envelope encryption key"
  deletion_window_in_days = 30
  enable_key_rotation     = true
  policy                  = data.aws_iam_policy_document.backend_app_kms_key.json
  tags                    = local.common_tags
}

resource "aws_kms_alias" "backend_app" {
  name          = var.kms_alias_name
  target_key_id = aws_kms_key.backend_app.key_id
}

data "aws_iam_policy_document" "app_runtime_kms" {
  statement {
    sid    = "UseBackendAppKmsKey"
    effect = "Allow"

    actions = [
      "kms:Decrypt",
      "kms:DescribeKey",
      "kms:GenerateDataKey",
    ]

    resources = [aws_kms_key.backend_app.arn]
  }
}

resource "aws_iam_user_policy" "app_runtime_kms" {
  name   = "lantern-backend-app-kms"
  user   = aws_iam_user.app_runtime.name
  policy = data.aws_iam_policy_document.app_runtime_kms.json
}

resource "aws_iam_access_key" "app_runtime" {
  user = aws_iam_user.app_runtime.name
}
