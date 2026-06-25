def load_all_models() -> None:
    import src.modules.user.models  # noqa: F401
    import src.modules.household.models  # noqa: F401
    import src.modules.household_membership.models  # noqa: F401
    import src.modules.institution_connections.models  # noqa: F401
    import src.modules.accounts.models  # noqa: F401
    import src.modules.plaid_transactions.models  # noqa: F401
    import src.modules.sync_jobs.models  # noqa: F401
    import src.modules.named_queries.models  # noqa: F401
