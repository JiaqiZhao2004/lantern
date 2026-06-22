locals {
  stack_name = "db-durability"

  normalized_six_hourly_prefix = trimsuffix(var.six_hourly_prefix, "/")
  normalized_weekly_prefix     = trimsuffix(var.weekly_prefix, "/")

  common_tags = merge(
    {
      ManagedBy = "terraform"
      Project   = "lantern"
      Stack     = local.stack_name
    },
    var.tags
  )
}

data "aws_iam_policy_document" "backup_bucket_tls" {
  statement {
    sid    = "DenyInsecureTransport"
    effect = "Deny"

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    actions = ["s3:*"]

    resources = [
      aws_s3_bucket.backups.arn,
      "${aws_s3_bucket.backups.arn}/*",
    ]

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

data "aws_iam_policy_document" "backup_upload" {
  statement {
    sid    = "ListBackupPrefixes"
    effect = "Allow"

    actions = [
      "s3:GetBucketLocation",
      "s3:ListBucket",
    ]

    resources = [aws_s3_bucket.backups.arn]

    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values = [
        "${local.normalized_six_hourly_prefix}/*",
        "${local.normalized_weekly_prefix}/*",
      ]
    }
  }

  statement {
    sid    = "WriteBackupObjects"
    effect = "Allow"

    actions = [
      "s3:AbortMultipartUpload",
      "s3:PutObject",
    ]

    resources = [
      "${aws_s3_bucket.backups.arn}/${local.normalized_six_hourly_prefix}/*",
      "${aws_s3_bucket.backups.arn}/${local.normalized_weekly_prefix}/*",
    ]
  }
}

resource "aws_s3_bucket" "backups" {
  bucket = var.backup_bucket_name
  tags   = local.common_tags
}

resource "aws_s3_bucket_server_side_encryption_configuration" "backups" {
  bucket = aws_s3_bucket.backups.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "backups" {
  bucket = aws_s3_bucket.backups.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "backups" {
  bucket = aws_s3_bucket.backups.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "backups" {
  bucket = aws_s3_bucket.backups.id

  rule {
    id     = "expire-six-hourly-backups"
    status = "Enabled"

    filter {
      prefix = "${local.normalized_six_hourly_prefix}/"
    }

    expiration {
      days = 3
    }
  }

  rule {
    id     = "expire-weekly-backups"
    status = "Enabled"

    filter {
      prefix = "${local.normalized_weekly_prefix}/"
    }

    expiration {
      days = 28
    }
  }
}

resource "aws_s3_bucket_policy" "backups" {
  bucket = aws_s3_bucket.backups.id
  policy = data.aws_iam_policy_document.backup_bucket_tls.json
}

resource "aws_iam_user" "backup_upload" {
  name = var.backup_upload_user_name
  tags = local.common_tags
}

resource "aws_iam_user_policy" "backup_upload" {
  name   = "lantern-backup-upload"
  user   = aws_iam_user.backup_upload.name
  policy = data.aws_iam_policy_document.backup_upload.json
}

resource "aws_iam_access_key" "backup_upload" {
  user = aws_iam_user.backup_upload.name
}
