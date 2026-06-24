from pathlib import Path


def test_deploy_reconciles_plaid_webhooks_after_migrations_before_rollout():
    repo_root = Path(__file__).resolve().parents[4]
    deploy_script = repo_root / "ops/deployment/backend/app-stack/deploy.sh"
    content = deploy_script.read_text(encoding="utf-8")

    migration = "compose run --rm backend alembic upgrade head"
    reconcile = "compose run --rm backend python -m src.plaid_webhook_reconciler --apply"
    rollout = "compose up -d nginx backend worker"

    assert migration in content
    assert reconcile in content
    assert rollout in content
    assert content.index(migration) < content.index(reconcile) < content.index(rollout)
