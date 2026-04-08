from sqlalchemy.orm import Session
from uuid import UUID
from .models import PlaidItem
from ...app.user.models import User
from ...infrastructure.aws.kms import KMSService


class PlaidItemRepository:

    def create_encrypted(
        self,
        db: Session,
        kms: KMSService,
        user: User,
        household_id: UUID,
        plaid_item_id: str,
        plaid_access_token: str,
        institution_id: str | None,
        institution_name: str | None,
    ):
        ciphertext, nonce, encrypted_data_key = kms.encrypt_secret(plaid_access_token)
        item = PlaidItem(
            user_id=user.id,
            household_id=household_id,
            plaid_item_id=plaid_item_id,
            institution_id=institution_id,
            institution_name=institution_name,
            access_token_ciphertext=ciphertext,
            access_token_nonce=nonce,
            access_token_encrypted_data_key=encrypted_data_key,
        )
        db.add(item)
        db.flush()  # ensures item.id is available before commit
        return item
