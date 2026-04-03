[(An image of "Plaid logo")Docs](https://plaid.com/docs/index.html.md)

Search or Ask a Question

Close search modal

Search the docsAsk Bill!(An image of "Ask Bill!")

(An image of "Ask Bill!")

Hi! I'm Bill! You can ask me all about the Plaid API. Try asking questions like:

**Note:** Bill isn't perfect. He's just a robot platypus that reads our docs for fun. You should treat his answers with the same healthy skepticism you might treat any other answer on the internet. This chat may be logged for quality and training purposes. Please don't send Bill any PII -- he's scared of intimacy. All chats with Bill are subject to Plaid's [Privacy Policy.](https://plaid.com/legal/#all-audiences)

Markdown

[Plaid.com](https://plaid.com/)

[Log in](https://dashboard.plaid.com/signin?redirect=docs)

[Get API Keys](https://dashboard.plaid.com/signup)

Open nav

Accounts 
=========

#### API reference for retrieving account information and seeing all possible account types and subtypes 

\=\*=\*=\*=

#### /accounts/get 

#### Retrieve accounts 

The [/accounts/get](https://plaid.com/docs/api/accounts/index.html.md#accountsget) endpoint can be used to retrieve a list of accounts associated with any linked Item. Plaid will only return active bank accounts — that is, accounts that are not closed and are capable of carrying a balance. To return new accounts that were created after the user linked their Item, you can listen for the [NEW\_ACCOUNTS\_AVAILABLE](https://plaid.com/docs/api/items/index.html.md#new_accounts_available) webhook and then use Link's [update mode](https://plaid.com/docs/link/update-mode/index.html.md) to request that the user share this new account with you.

[/accounts/get](https://plaid.com/docs/api/accounts/index.html.md#accountsget) is free to use and retrieves cached information, rather than extracting fresh information from the institution. The balance returned will reflect the balance at the time of the last successful Item update. If the Item is enabled for a regularly updating product, such as Transactions, Investments, or Liabilities, the balance will typically update about once a day, as long as the Item is healthy. If the Item is enabled only for products that do not frequently update, such as Auth or Identity, balance data may be much older.

For realtime balance information, use the paid endpoints [/accounts/balance/get](https://plaid.com/docs/api/products/signal/index.html.md#accountsbalanceget) or [/signal/evaluate](https://plaid.com/docs/api/products/signal/index.html.md#signalevaluate) instead.

#### Request fields 

string

Your Plaid API `client_id`. The `client_id` is required and may be provided either in the `PLAID-CLIENT-ID` header or as part of a request body.

string

Your Plaid API `secret`. The `secret` is required and may be provided either in the `PLAID-SECRET` header or as part of a request body.

required, string

The access token associated with the Item data is being requested for.

object

An optional object to filter `/accounts/get` results.

\[string\]

An array of `account_ids` to retrieve for the Account.

/accounts/get

Node▼

```javascript
const request: AccountsGetRequest = {
  access_token: ACCESS_TOKEN,
};
try {
  const response = await plaidClient.accountsGet(request);
  const accounts = response.data.accounts;
} catch (error) {
  // handle error
}

```

#### Response fields 

\[object\]

An array of financial institution accounts associated with the Item. If `/accounts/balance/get` was called, each account will include real-time balance information.

string

Plaid’s unique identifier for the account. This value will not change unless Plaid can't reconcile the account with the data returned by the financial institution. This may occur, for example, when the name of the account changes. If this happens a new `account_id` will be assigned to the account.  
The `account_id` can also change if the `access_token` is deleted and the same credentials that were used to generate that `access_token` are used to generate a new `access_token` on a later date. In that case, the new `account_id` will be different from the old `account_id`.  
If an account with a specific `account_id` disappears instead of changing, the account is likely closed. Closed accounts are not returned by the Plaid API.  
When using a CRA endpoint (an endpoint associated with Plaid Check Consumer Report, i.e. any endpoint beginning with `/cra/`), the `account_id` returned will not match the `account_id` returned by a non-CRA endpoint.  
Like all Plaid identifiers, the `account_id` is case sensitive.

object

A set of fields describing the balance for an account. Balance information may be cached unless the balance object was returned by `/accounts/balance/get` or `/signal/evaluate` (using a Balance-only ruleset).

nullable, number

The amount of funds available to be withdrawn from the account, as determined by the financial institution.  
For `credit`\-type accounts, the `available` balance typically equals the `limit` less the `current` balance, less any pending outflows plus any pending inflows.  
For `depository`\-type accounts, the `available` balance typically equals the `current` balance less any pending outflows plus any pending inflows. For `depository`\-type accounts, the `available` balance does not include the overdraft limit.  
For `investment`\-type accounts (or `brokerage`\-type accounts for API versions 2018-05-22 and earlier), the `available` balance is the total cash available to withdraw as presented by the institution.  
Note that not all institutions calculate the `available` balance. In the event that `available` balance is unavailable, Plaid will return an `available` balance value of `null`.  
Available balance may be cached and is not guaranteed to be up-to-date in realtime unless the value was returned by `/accounts/balance/get`, or by `/signal/evaluate` with a Balance-only ruleset.  
If `current` is `null` this field is guaranteed not to be `null`.  
  

Format: `double`

nullable, number

The total amount of funds in or owed by the account.  
For `credit`\-type accounts, a positive balance indicates the amount owed; a negative amount indicates the lender owing the account holder.  
For `loan`\-type accounts, the current balance is the principal remaining on the loan, except in the case of student loan accounts at Sallie Mae (`ins_116944`). For Sallie Mae student loans, the account's balance includes both principal and any outstanding interest. Similar to `credit`\-type accounts, a positive balance is typically expected, while a negative amount indicates the lender owing the account holder.  
For `investment`\-type accounts (or `brokerage`\-type accounts for API versions 2018-05-22 and earlier), the current balance is the total value of assets as presented by the institution.  
Note that balance information may be cached unless the value was returned by `/accounts/balance/get` or by `/signal/evaluate` with a Balance-only ruleset; if the Item is enabled for Transactions, the balance will be at least as recent as the most recent Transaction update. If you require realtime balance information, use the `available` balance as provided by `/accounts/balance/get` or `/signal/evaluate` called with a Balance-only `ruleset_key`.  
When returned by `/accounts/balance/get`, this field may be `null`. When this happens, `available` is guaranteed not to be `null`.  
  

Format: `double`

nullable, number

For `credit`\-type accounts, this represents the credit limit.  
For `depository`\-type accounts, this represents the pre-arranged overdraft limit, which is common for current (checking) accounts in Europe.  
In North America, this field is typically only available for `credit`\-type accounts.  
  

Format: `double`

nullable, string

The ISO-4217 currency code of the balance. Always null if `unofficial_currency_code` is non-null.

nullable, string

The unofficial currency code associated with the balance. Always null if `iso_currency_code` is non-null. Unofficial currency codes are used for currencies that do not have official ISO currency codes, such as cryptocurrencies and the currencies of certain countries.  
See the [currency code schema](https://plaid.com/docs/api/accounts/index.html.md#currency-code-schema) for a full listing of supported `unofficial_currency_code`s.

nullable, string

Timestamp in [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) format (`YYYY-MM-DDTHH:mm:ssZ`) indicating the last time the balance was updated.  
This field is returned only when the institution is `ins_128026` (Capital One).  
  

Format: `date-time`

nullable, string

The last 2-4 alphanumeric characters of either the account’s displayed mask or the account’s official account number. Note that the mask may be non-unique between an Item’s accounts.

string

The name of the account, either assigned by the user or by the financial institution itself

nullable, string

The official name of the account as given by the financial institution

string

`investment:` Investment account. In API versions 2018-05-22 and earlier, this type is called `brokerage` instead.  
`credit:` Credit card  
`depository:` Depository account  
`loan:` Loan account  
`other:` Non-specified account type  
See the [Account type schema](https://plaid.com/docs/api/accounts/index.html.md#account-type-schema) for a full listing of account types and corresponding subtypes.  
  

Possible values: `investment`, `credit`, `depository`, `loan`, `brokerage`, `other`

nullable, string

See the [Account type schema](https://plaid.com/docs/api/accounts/index.html.md#account-type-schema) for a full listing of account types and corresponding subtypes.  
  

Possible values: `401a`, `401k`, `403B`, `457b`, `529`, `auto`, `brokerage`, `business`, `cash isa`, `cash management`, `cd`, `checking`, `commercial`, `construction`, `consumer`, `credit card`, `crypto exchange`, `ebt`, `education savings account`, `fixed annuity`, `gic`, `health reimbursement arrangement`, `home equity`, `hsa`, `isa`, `ira`, `keogh`, `lif`, `life insurance`, `line of credit`, `lira`, `loan`, `lrif`, `lrsp`, `money market`, `mortgage`, `mutual fund`, `non-custodial wallet`, `non-taxable brokerage account`, `other`, `other insurance`, `other annuity`, `overdraft`, `paypal`, `payroll`, `pension`, `prepaid`, `prif`, `profit sharing plan`, `rdsp`, `resp`, `retirement`, `rlif`, `roth`, `roth 401k`, `rrif`, `rrsp`, `sarsep`, `savings`, `sep ira`, `simple ira`, `sipp`, `stock plan`, `student`, `thrift savings plan`, `tfsa`, `trust`, `ugma`, `utma`, `variable annuity`

string

Indicates an Item's micro-deposit-based verification or database verification status. This field is only populated when using Auth and falling back to micro-deposit or database verification. Possible values are:  
`pending_automatic_verification`: The Item is pending automatic verification.  
`pending_manual_verification`: The Item is pending manual micro-deposit verification. Items remain in this state until the user successfully verifies the code.  
`automatically_verified`: The Item has successfully been automatically verified.  
`manually_verified`: The Item has successfully been manually verified.  
`verification_expired`: Plaid was unable to automatically verify the deposit within 7 calendar days and will no longer attempt to validate the Item. Users may retry by submitting their information again through Link.  
`verification_failed`: The Item failed manual micro-deposit verification because the user exhausted all 3 verification attempts. Users may retry by submitting their information again through Link.  
`unsent`: The Item is pending micro-deposit verification, but Plaid has not yet sent the micro-deposit.  
`database_insights_pending`: The Database Auth result is pending and will be available upon Auth request.  
`database_insights_fail`: The Item's numbers have been verified using Plaid's data sources and have signal for being invalid and/or have no signal for being valid. Typically this indicates that the routing number is invalid, the account number does not match the account number format associated with the routing number, or the account has been reported as closed or frozen. Only returned for Auth Items created via Database Auth.  
`database_insights_pass`: The Item's numbers have been verified using Plaid's data sources: the routing and account number match a routing and account number of an account recognized on the Plaid network, and the account is not known by Plaid to be frozen or closed. Only returned for Auth Items created via Database Auth.  
`database_insights_pass_with_caution`: The Item's numbers have been verified using Plaid's data sources and have some signal for being valid: the routing and account number were not recognized on the Plaid network, but the routing number is valid and the account number is a potential valid account number for that routing number. Only returned for Auth Items created via Database Auth.  
`database_matched`: (deprecated) The Item has successfully been verified using Plaid's data sources. Only returned for Auth Items created via Database Match.  
`null` or empty string: Neither micro-deposit-based verification nor database verification are being used for the Item.  
  

Possible values: `automatically_verified`, `pending_automatic_verification`, `pending_manual_verification`, `unsent`, `manually_verified`, `verification_expired`, `verification_failed`, `database_matched`, `database_insights_pass`, `database_insights_pass_with_caution`, `database_insights_fail`

string

The account holder name that was used for micro-deposit and/or database verification. Only returned for Auth Items created via micro-deposit or database verification. This name was manually-entered by the user during Link, unless it was otherwise provided via the `user.legal_name` request field in `/link/token/create` for the Link session that created the Item.

object

Insights from performing database verification for the account. Only returned for Auth Items using Database Auth.

nullable, integer

Indicates the score of the name match between the given name provided during database verification (available in the [verification\_name](https://plaid.com/docs/api/products/auth/index.html.md#auth-get-response-accounts-verification-name) field) and matched Plaid network accounts. If defined, will be a value between 0 and 100. Will be undefined if name matching was not enabled for the database verification session or if there were no eligible Plaid network matches to compare the given name with.

object

Status information about the account and routing number in the Plaid network.

boolean

Indicates whether we found at least one matching account for the ACH account and routing number.

boolean

Indicates if at least one matching account for the ACH account and routing number is already verified.

object

Information about known ACH returns for the account and routing number.

boolean

Indicates whether Plaid's data sources include a known administrative ACH return for account and routing number.

string

Indicator of account number format validity for institution.  
`valid`: indicates that the account number has a correct format for the institution.  
`invalid`: indicates that the account number has an incorrect format for the institution.  
`unknown`: indicates that there was not enough information to determine whether the format is correct for the institution.  
  

Possible values: `valid`, `invalid`, `unknown`

string

A unique and persistent identifier for accounts that can be used to trace multiple instances of the same account across different Items for depository accounts. This field is currently supported only for Items at institutions that use Tokenized Account Numbers (i.e., Chase and PNC, and in May 2025 US Bank). Because these accounts have a different account number each time they are linked, this field may be used instead of the account number to uniquely identify an account across multiple Items for payments use cases, helping to reduce duplicate Items or attempted fraud. In Sandbox, this field is populated for TAN-based institutions (`ins_56`, `ins_13`) as well as the OAuth Sandbox institution (`ins_127287`); in Production, it will only be populated for accounts at applicable institutions.

nullable, string

Indicates the account's categorization as either a personal or a business account. This field is currently in beta; to request access, contact your account manager.  
  

Possible values: `business`, `personal`, `unrecognized`

object

Metadata about the Item.

string

The Plaid Item ID. The `item_id` is always unique; linking the same account at the same institution twice will result in two Items with different `item_id` values. Like all Plaid identifiers, the `item_id` is case-sensitive.

nullable, string

The Plaid Institution ID associated with the Item. Field is `null` for Items created without an institution connection, such as Items created via Same Day Micro-deposits.

nullable, string

The name of the institution associated with the Item. Field is `null` for Items created without an institution connection, such as Items created via Same Day Micro-deposits.

nullable, string

The URL registered to receive webhooks for the Item.

nullable, string

The method used to populate Auth data for the Item. This field is only populated for Items that have had Auth numbers data set on at least one of its accounts, and will be `null` otherwise. For info about the various flows, see our [Auth coverage documentation](https://plaid.com/docs/auth/coverage/index.html.md) .  
`INSTANT_AUTH`: The Item's Auth data was provided directly by the user's institution connection.  
`INSTANT_MATCH`: The Item's Auth data was provided via the Instant Match fallback flow.  
`AUTOMATED_MICRODEPOSITS`: The Item's Auth data was provided via the Automated Micro-deposits flow.  
`SAME_DAY_MICRODEPOSITS`: The Item's Auth data was provided via the Same Day Micro-deposits flow.  
`INSTANT_MICRODEPOSITS`: The Item's Auth data was provided via the Instant Micro-deposits flow.  
`DATABASE_MATCH`: The Item's Auth data was provided via the Database Match flow.  
`DATABASE_INSIGHTS`: The Item's Auth data was provided via the Database Insights flow.  
`TRANSFER_MIGRATED`: The Item's Auth data was provided via [/transfer/migrate\_account](https://plaid.com/docs/api/products/transfer/account-linking/index.html.md#migrate-account-into-transfers) .  
`INVESTMENTS_FALLBACK`: The Item's Auth data for Investments Move was provided via a [fallback flow](https://plaid.com/docs/investments-move/index.html.md#fallback-flows) .  
  

Possible values: `INSTANT_AUTH`, `INSTANT_MATCH`, `AUTOMATED_MICRODEPOSITS`, `SAME_DAY_MICRODEPOSITS`, `INSTANT_MICRODEPOSITS`, `DATABASE_MATCH`, `DATABASE_INSIGHTS`, `TRANSFER_MIGRATED`, `INVESTMENTS_FALLBACK`, `null`

nullable, object

Errors are identified by `error_code` and categorized by `error_type`. Use these in preference to HTTP status codes to identify and handle specific errors. HTTP status codes are set and provide the broadest categorization of errors: 4xx codes are for developer- or user-related errors, and 5xx codes are for Plaid-related errors, and the status will be 2xx in non-error cases. An Item with a non-`null` error object will only be part of an API response when calling `/item/get` to view Item status. Otherwise, error fields will be `null` if no error has occurred; if an error has occurred, an error code will be returned instead.

string

A broad categorization of the error. Safe for programmatic use.  
  

Possible values: `INVALID_REQUEST`, `INVALID_RESULT`, `INVALID_INPUT`, `INSTITUTION_ERROR`, `RATE_LIMIT_EXCEEDED`, `API_ERROR`, `ITEM_ERROR`, `ASSET_REPORT_ERROR`, `RECAPTCHA_ERROR`, `OAUTH_ERROR`, `PAYMENT_ERROR`, `BANK_TRANSFER_ERROR`, `INCOME_VERIFICATION_ERROR`, `MICRODEPOSITS_ERROR`, `SANDBOX_ERROR`, `PARTNER_ERROR`, `SIGNAL_ERROR`, `TRANSACTIONS_ERROR`, `TRANSACTION_ERROR`, `TRANSFER_ERROR`, `CHECK_REPORT_ERROR`, `CONSUMER_REPORT_ERROR`, `USER_ERROR`

string

The particular error code. Safe for programmatic use.

nullable, string

The specific reason for the error code. Currently, reasons are only supported OAuth-based item errors; `null` will be returned otherwise. Safe for programmatic use.  
Possible values: `OAUTH_INVALID_TOKEN`: The user’s OAuth connection to this institution has been invalidated.  
`OAUTH_CONSENT_EXPIRED`: The user's access consent for this OAuth connection to this institution has expired.  
`OAUTH_USER_REVOKED`: The user’s OAuth connection to this institution is invalid because the user revoked their connection.

string

A developer-friendly representation of the error code. This may change over time and is not safe for programmatic use.

nullable, string

A user-friendly representation of the error code. `null` if the error is not related to user action.  
This may change over time and is not safe for programmatic use.

string

A unique ID identifying the request, to be used for troubleshooting purposes. This field will be omitted in errors provided by webhooks.

array

In this product, a request can pertain to more than one Item. If an error is returned for such a request, `causes` will return an array of errors containing a breakdown of these errors on the individual Item level, if any can be identified.  
`causes` will be provided for the `error_type` `ASSET_REPORT_ERROR` or `CHECK_REPORT_ERROR`. `causes` will also not be populated inside an error nested within a `warning` object.

nullable, integer

The HTTP status code associated with the error. This will only be returned in the response body when the error information is provided via a webhook.

string

The URL of a Plaid documentation page with more information about the error

nullable, string

Suggested steps for resolving the error

\[string\]

A list of the account subtypes that were requested via the `account_filters` parameter in `/link/token/create`. Currently only populated for `NO_ACCOUNTS` errors from Items with `investments_auth` as an enabled product.

\[string\]

A list of the account subtypes that were extracted but did not match the requested subtypes via the `account_filters` parameter in `/link/token/create`. Currently only populated for `NO_ACCOUNTS` errors from Items with `investments_auth` as an enabled product.

\[string\]

A list of products available for the Item that have not yet been accessed. The contents of this array will be mutually exclusive with `billed_products`.  
  

Possible values: `assets`, `auth`, `balance`, `balance_plus`, `beacon`, `identity`, `identity_match`, `investments`, `investments_auth`, `liabilities`, `payment_initiation`, `identity_verification`, `transactions`, `credit_details`, `income`, `income_verification`, `standing_orders`, `transfer`, `employment`, `recurring_transactions`, `transactions_refresh`, `signal`, `statements`, `processor_payments`, `processor_identity`, `profile`, `cra_base_report`, `cra_income_insights`, `cra_partner_insights`, `cra_network_insights`, `cra_cashflow_insights`, `cra_monitoring`, `cra_lend_score`, `cra_plaid_credit_score`, `layer`, `pay_by_bank`, `protect_linked_bank`

\[string\]

A list of products that have been billed for the Item. The contents of this array will be mutually exclusive with `available_products`. Note - `billed_products` is populated in all environments but only requests in Production are billed. Also note that products that are billed on a pay-per-call basis rather than a pay-per-Item basis, such as `balance`, will not appear here.  
  

Possible values: `assets`, `auth`, `balance`, `balance_plus`, `beacon`, `identity`, `identity_match`, `investments`, `investments_auth`, `liabilities`, `payment_initiation`, `identity_verification`, `transactions`, `credit_details`, `income`, `income_verification`, `standing_orders`, `transfer`, `employment`, `recurring_transactions`, `transactions_refresh`, `signal`, `statements`, `processor_payments`, `processor_identity`, `profile`, `cra_base_report`, `cra_income_insights`, `cra_partner_insights`, `cra_network_insights`, `cra_cashflow_insights`, `cra_monitoring`, `cra_lend_score`, `cra_plaid_credit_score`, `layer`, `pay_by_bank`, `protect_linked_bank`

\[string\]

A list of products added to the Item. In almost all cases, this will be the same as the `billed_products` field. For some products, it is possible for the product to be added to an Item but not yet billed (e.g. Assets, before `/asset_report/create` has been called, or Auth or Identity when added as Optional Products but before their endpoints have been called), in which case the product may appear in `products` but not in `billed_products`.  
  

Possible values: `assets`, `auth`, `balance`, `balance_plus`, `beacon`, `identity`, `identity_match`, `investments`, `investments_auth`, `liabilities`, `payment_initiation`, `identity_verification`, `transactions`, `credit_details`, `income`, `income_verification`, `standing_orders`, `transfer`, `employment`, `recurring_transactions`, `transactions_refresh`, `signal`, `statements`, `processor_payments`, `processor_identity`, `profile`, `cra_base_report`, `cra_income_insights`, `cra_partner_insights`, `cra_network_insights`, `cra_cashflow_insights`, `cra_monitoring`, `cra_lend_score`, `cra_plaid_credit_score`, `layer`, `pay_by_bank`, `protect_linked_bank`

\[string\]

A list of products that the user has consented to for the Item via [Data Transparency Messaging](https://plaid.com/docs/link/data-transparency-messaging-migration-guide/index.html.md) . This will consist of all products where both of the following are true: the user has consented to the required data scopes for that product and you have Production access for that product.  
  

Possible values: `assets`, `auth`, `balance`, `balance_plus`, `beacon`, `identity`, `identity_match`, `investments`, `investments_auth`, `liabilities`, `transactions`, `income`, `income_verification`, `transfer`, `employment`, `recurring_transactions`, `signal`, `statements`, `processor_payments`, `processor_identity`, `cra_base_report`, `cra_income_insights`, `cra_lend_score`, `cra_partner_insights`, `cra_cashflow_insights`, `cra_monitoring`, `layer`

nullable, string

The date and time at which the Item's access consent will expire, in [ISO 8601](https://wikipedia.org/wiki/ISO_8601) format. If the Item does not have consent expiration scheduled, this field will be `null`. Currently, only institutions in Europe and a small number of institutions in the US have expiring consent. For a list of US institutions that currently expire consent, see the [OAuth Guide](https://plaid.com/docs/link/oauth/index.html.md#refreshing-item-consent) .  
  

Format: `date-time`

string

Indicates whether an Item requires user interaction to be updated, which can be the case for Items with some forms of two-factor authentication.  
`background` - Item can be updated in the background  
`user_present_required` - Item requires user interaction to be updated  
  

Possible values: `background`, `user_present_required`

string

A unique identifier for the request, which can be used for troubleshooting. This identifier, like all Plaid identifiers, is case sensitive.

Response Object

```json
{
  "accounts": [
    {
      "account_id": "blgvvBlXw3cq5GMPwqB6s6q4dLKB9WcVqGDGo",
      "balances": {
        "available": 100,
        "current": 110,
        "iso_currency_code": "USD",
        "limit": null,
        "unofficial_currency_code": null
      },
      "holder_category": "personal",
      "mask": "0000",
      "name": "Plaid Checking",
      "official_name": "Plaid Gold Standard 0% Interest Checking",
      "subtype": "checking",
      "type": "depository"
    },
    {
      "account_id": "6PdjjRP6LmugpBy5NgQvUqpRXMWxzktg3rwrk",
      "balances": {
        "available": null,
        "current": 23631.9805,
        "iso_currency_code": "USD",
        "limit": null,
        "unofficial_currency_code": null
      },
      "mask": "6666",
      "name": "Plaid 401k",
      "official_name": null,
      "subtype": "401k",
      "type": "investment"
    },
    {
      "account_id": "XMBvvyMGQ1UoLbKByoMqH3nXMj84ALSdE5B58",
      "balances": {
        "available": null,
        "current": 65262,
        "iso_currency_code": "USD",
        "limit": null,
        "unofficial_currency_code": null
      },
      "mask": "7777",
      "name": "Plaid Student Loan",
      "official_name": null,
      "subtype": "student",
      "type": "loan"
    }
  ],
  "item": {
    "available_products": [
      "balance",
      "identity",
      "payment_initiation",
      "transactions"
    ],
    "billed_products": [
      "assets",
      "auth"
    ],
    "consent_expiration_time": null,
    "error": null,
    "institution_id": "ins_117650",
    "institution_name": "Royal Bank of Plaid",
    "item_id": "DWVAAPWq4RHGlEaNyGKRTAnPLaEmo8Cvq7na6",
    "update_type": "background",
    "webhook": "https://www.genericwebhookurl.com/webhook",
    "auth_method": "INSTANT_AUTH"
  },
  "request_id": "bkVE1BHWMAZ9Rnr"
}
```

\=\*=\*=\*=

#### Account type schema 

The schema below describes the various `types` and corresponding `subtypes` that Plaid recognizes and reports for financial institution accounts. For a mapping of supported types and subtypes to Plaid products, see the [Account type / product support matrix](https://plaid.com/docs/api/accounts/index.html.md#account-type--product-support-matrix) .

#### Properties 

string

An account type holding cash, in which funds are deposited.

string

A cash management account, typically a cash account at a brokerage

string

Certificate of deposit account

string

Checking account

string

An Electronic Benefit Transfer (EBT) account, used by certain public assistance programs to distribute funds (US only)

string

Health Savings Account (US only) that can only hold cash

string

Money market account

string

PayPal depository account

string

Prepaid debit card

string

Savings account

string

A credit card type account.

string

Bank-issued credit card

string

PayPal-issued credit card

string

A loan type account.

string

Auto loan

string

Business loan

string

Commercial loan

string

Construction loan

string

Consumer loan

string

Home Equity Line of Credit (HELOC)

string

Pre-approved line of credit

string

General loan

string

Mortgage loan

string

Other loan type or unknown loan type

string

Pre-approved overdraft account, usually tied to a checking account

string

Student loan

string

An investment account. In API versions 2018-05-22 and earlier, this type is called `brokerage`.

string

Tax-advantaged college savings and prepaid tuition 529 plans (US)

string

Employer-sponsored money-purchase 401(a) retirement plan (US)

string

Standard 401(k) retirement account (US)

string

403(b) retirement savings account for non-profits and schools (US)

string

Tax-advantaged deferred-compensation 457(b) retirement plan for governments and non-profits (US)

string

Standard brokerage account

string

Individual Savings Account (ISA) that pays interest tax-free (UK)

string

Standard cryptocurrency exchange account

string

Tax-advantaged Coverdell Education Savings Account (ESA) (US)

string

Fixed annuity

string

Guaranteed Investment Certificate (Canada)

string

Tax-advantaged Health Reimbursement Arrangement (HRA) benefit plan (US)

string

Non-cash tax-advantaged medical Health Savings Account (HSA) (US)

string

Traditional Individual Retirement Account (IRA) (US)

string

Non-cash Individual Savings Account (ISA) (UK)

string

Keogh self-employed retirement plan (US)

string

Life Income Fund (LIF) retirement account (Canada)

string

Life insurance account

string

Locked-in Retirement Account (LIRA) (Canada)

string

Locked-in Retirement Income Fund (LRIF) (Canada)

string

Locked-in Retirement Savings Plan (Canada)

string

Mutual fund account

string

A cryptocurrency wallet where the user controls the private key

string

A non-taxable brokerage account that is not covered by a more specific subtype

string

An account whose type could not be determined

string

An annuity account not covered by other subtypes

string

An insurance account not covered by other subtypes

string

Standard pension account

string

Prescribed Registered Retirement Income Fund (Canada)

string

Plan that gives employees share of company profits

string

Qualifying share account

string

Registered Disability Savings Plan (RSDP) (Canada)

string

Registered Education Savings Plan (Canada)

string

Retirement account not covered by other subtypes

string

Restricted Life Income Fund (RLIF) (Canada)

string

Roth IRA (US)

string

Employer-sponsored Roth 401(k) plan (US)

string

Registered Retirement Income Fund (RRIF) (Canada)

string

Registered Retirement Savings Plan (Canadian, similar to US 401(k))

string

Salary Reduction Simplified Employee Pension Plan (SARSEP), discontinued retirement plan (US)

string

Simplified Employee Pension IRA (SEP IRA), retirement plan for small businesses and self-employed (US)

string

Savings Incentive Match Plan for Employees IRA, retirement plan for small businesses (US)

string

Self-Invested Personal Pension (SIPP) (UK)

string

Standard stock plan account

string

Tax-Free Savings Account (TFSA), a retirement plan similar to a Roth IRA (Canada)

string

Thrift Savings Plan, a retirement savings and investment plan for Federal employees and members of the uniformed services.

string

Account representing funds or assets held by a trustee for the benefit of a beneficiary. Includes both revocable and irrevocable trusts.

string

'Uniform Gift to Minors Act' (brokerage account for minors, US)

string

'Uniform Transfers to Minors Act' (brokerage account for minors, US)

string

Tax-deferred capital accumulation annuity contract

string

A payroll account.

string

Standard payroll account

string

Other or unknown account type.

\=\*=\*=\*=

#### Account type / product support matrix 

The chart below indicates which products can be used with which account types. Note that some products can only be used with certain subtypes:

*   Auth and Signal require a debitable `checking`, `savings`, or `cash management` account.
*   Liabilities does not support `loan` types other than `student` or `mortgage`.
*   Transactions does not support `loan` types other than `student`. (For Canadian institutions, Transactions also supports the `mortgage` loan type.)
*   Investments does not support `depository` types other than `cash management`.

Also note that not all institutions support all products; for details on which products a given institution supports, use [/institutions/get\_by\_id](https://plaid.com/docs/api/institutions/index.html.md#institutionsget_by_id) or look up the institution on the [Plaid Dashboard status page](https://dashboard.plaid.com/activity/status) or the [Coverage Explorer](https://plaid.com/docs/institutions/index.html.md) .

| Product | Depository | Credit | Investments | Loan | Other |
| --- | --- | --- | --- | --- | --- |
| [Balance](https://plaid.com/docs/balance/index.html.md) |  |  | \* |  |  |
| [Transactions](https://plaid.com/docs/transactions/index.html.md) |  |  |  |  |  |
| [Identity](https://plaid.com/docs/identity/index.html.md) |  |  |  |  |  |
| [Assets](https://plaid.com/docs/assets/index.html.md) |  |  |  |  |  |
| [Consumer Reports by Plaid Check](https://plaid.com/docs/check/index.html.md) |  |  |  |  |  |
| [Investments](https://plaid.com/docs/investments/index.html.md) |  |  |  |  |  |
| [Investments Move](https://plaid.com/docs/investments/index.html.md) |  |  |  |  |  |
| [Liabilities](https://plaid.com/docs/liabilities/index.html.md) |  |  |  |  |  |
| [Auth](https://plaid.com/docs/auth/index.html.md) |  |  |  |  |  |
| [Transfer](https://plaid.com/docs/transfer/index.html.md) |  |  |  |  |  |
| [Income (Bank Income flow)](https://plaid.com/docs/income/index.html.md) |  |  |  |  |  |
| [Statements](https://plaid.com/docs/statements/index.html.md) |  |  |  |  |  |
| [Signal](https://plaid.com/docs/signal/index.html.md) |  |  |  |  |  |
| [Payment Initiation (UK and Europe)](https://plaid.com/docs/payment-initiation/index.html.md) |  |  |  |  |  |
| [Virtual Accounts (UK and Europe)](https://plaid.com/docs/payment-initiation/index.html.md) |  |  |  |  |  |

\* Investments holdings data is not priced intra-day.

\=\*=\*=\*=

#### Currency code schema 

The following currency codes are supported by Plaid.

#### Properties 

string

Plaid supports all ISO 4217 currency codes.

string

List of unofficial currency codes

string

Cardano

string

Basic Attention Token

string

Bitcoin Cash

string

Binance Coin

string

Bitcoin

string

Bitcoin Gold

string

Bitcoin Satoshi Vision

string

Chinese Yuan (offshore)

string

Dash

string

Dogecoin

string

Ethereum Classic

string

Ethereum

string

Pence sterling, i.e. British penny

string

Lisk

string

Neo

string

OmiseGO

string

Qtum

string

Tether

string

Stellar Lumen

string

Monero

string

Ripple

string

Zcash

string

0x

\=\*=\*=\*=

#### Investment transaction types schema 

Valid values for investment transaction types and subtypes. Note that transactions representing inflow of cash will appear as negative amounts, outflow of cash will appear as positive amounts.

#### Properties 

string

Buying an investment

string

Assignment of short option holding

string

Inflow of assets into a tax-advantaged account

string

Purchase to open or increase a position

string

Purchase to close a short position

string

Purchase using proceeds from a cash dividend

string

Purchase using proceeds from a cash interest payment

string

Purchase using long-term capital gain cash proceeds

string

Purchase using short-term capital gain cash proceeds

string

Selling an investment

string

Outflow of assets from a tax-advantaged account

string

Exercise of an option or warrant contract

string

Sell to close or decrease an existing holding

string

Sell to open a short position

string

A cancellation of a pending transaction

string

Activity that modifies a cash position

string

Fees paid for account maintenance

string

Inflow of assets into a tax-advantaged account

string

Inflow of cash into an account

string

Inflow of cash from a dividend

string

Inflow of stock from a distribution

string

Inflow of cash from interest

string

Fees paid for legal charges or services

string

Long-term capital gain received as cash

string

Fees paid for investment management of a mutual fund or other pooled investment vehicle

string

Fees paid for maintaining margin debt

string

Inflow of cash from a non-qualified dividend

string

Taxes paid on behalf of the investor for non-residency in investment jurisdiction

string

Pending inflow of cash

string

Pending outflow of cash

string

Inflow of cash from a qualified dividend

string

Short-term capital gain received as cash

string

Taxes paid on behalf of the investor

string

Taxes withheld on behalf of the customer

string

Fees incurred for transfer of a holding or account

string

Fees related to administration of a trust account

string

Unqualified capital gain received as cash

string

Outflow of cash from an account

string

Fees on the account, e.g. commission, bookkeeping, options-related.

string

Fees paid for account maintenance

string

Increase or decrease in quantity of item

string

Inflow of cash from a dividend

string

Inflow of cash from interest

string

Inflow of cash from interest receivable

string

Long-term capital gain received as cash

string

Fees paid for legal charges or services

string

Fees paid for investment management of a mutual fund or other pooled investment vehicle

string

Fees paid for maintaining margin debt

string

Inflow of cash from a non-qualified dividend

string

Taxes paid on behalf of the investor for non-residency in investment jurisdiction

string

Inflow of cash from a qualified dividend

string

Repayment of loan principal

string

Short-term capital gain received as cash

string

Inflow of stock from a distribution

string

Taxes paid on behalf of the investor

string

Taxes withheld on behalf of the customer

string

Fees incurred for transfer of a holding or account

string

Fees related to administration of a trust account

string

Unqualified capital gain received as cash

string

Activity that modifies a position, but not through buy/sell activity e.g. options exercise, portfolio transfer

string

Assignment of short option holding

string

Increase or decrease in quantity of item

string

Exercise of an option or warrant contract

string

Expiration of an option or warrant contract

string

Stock exchanged at a pre-defined ratio as part of a merger between companies

string

Request fiat or cryptocurrency to an address or email

string

Inflow or outflow of fiat or cryptocurrency to an address or email

string

Inflow of stock from spin-off transaction of an existing holding

string

Inflow of stock from a forward split of an existing holding

string

Trade of one cryptocurrency for another

string

Movement of assets into or out of an account