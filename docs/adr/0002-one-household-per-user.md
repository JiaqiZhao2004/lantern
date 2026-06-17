# One Household per User, permanently

A User belongs to at most one Household at a time. They may leave a Household and join a different one, but the previous membership is terminated — they cannot remain in both. This is enforced by a unique constraint on `user_id` in `household_memberships`.

The product is scoped to families sharing financial visibility. That trust model does not extend to simultaneous multi-Household membership — a Member sees all other Members' transactions, so the Household boundary is a trust boundary, not a workspace. Supporting concurrent membership in multiple Households would require per-transaction visibility controls, which is a fundamentally different (and much more complex) product.
