# M9f — Tenant isolation

**Claim:** isolation is **application-layer**. Every authenticated request is bound to `user.tenant_id` (`require_tenant_access` / `require_transaction_access` in `app/core/auth.py`). Repositories stamp and filter `tenant_id`. Postgres RLS on tables such as `integrations` is **defense in depth**, not the primary control (service-role client can bypass RLS; the API must not).

Platform admin (`/api/v1/platform/*`) is a separate console, not a mailbox viewer.

## Passing tests (names to cite)

Cross-tenant / cross-owner (not an exhaustive suite):

| Test | File |
| --- | --- |
| `test_two_self_registrations_get_isolated_tenants` | `app/tests/test_auth_api.py` |
| `test_oauth_exchange_ignores_client_supplied_tenant_id` | `app/tests/test_auth_api.py` |
| `test_tenant_admin_cannot_read_another_tenant_by_id` | `app/tests/test_tenants_api.py` |
| `test_tenant_admin_cannot_update_another_tenant` | `app/tests/test_tenants_api.py` |
| `test_admin_cannot_manage_user_in_another_tenant` | `app/tests/test_user_management_api.py` |
| `test_task_get_by_id_respects_tenant_filter` | `app/tests/test_task_tenant_isolation.py` |
| `test_webhooks_are_tenant_isolated` | `app/tests/test_integration_isolation.py` |
| `test_api_keys_are_tenant_isolated` | `app/tests/test_integration_isolation.py` |
| `test_api_key_acts_only_in_its_own_tenant` | `app/tests/test_integration_isolation.py` |
| `test_branding_is_tenant_isolated` | `app/tests/test_integration_isolation.py` |
| `test_serving_isolation_between_tenants` | `app/tests/test_advertising_service.py` |
| `test_revoking_another_tenants_rule_is_refused` | `app/tests/test_inbound_correction.py` |
| `test_assert_access_denies_cross_tenant` | `app/tests/test_fsbo_workspace.py` |
| `test_property_detail_cross_owner_returns_404` | `app/tests/test_fsbo_workspace.py` |
| `test_fsbo_message_post_cross_owner_returns_404` | `app/tests/test_fsbo_workspace.py` |

Gmail tokens are keyed by `user_id` + `provider` on `integrations`. Webhook matching uses the connected mailbox, not “any user in the tenant.”
