import os
import base64
import json
from apps.authentication.models import Wallet
from django.utils.deprecation import MiddlewareMixin
from eth_account.messages import defunct_hash_message
from web3 import Web3
from datetime import datetime
w3 = Web3(Web3.HTTPProvider(os.getenv('RPC_URL')))


class WalletMiddleware(MiddlewareMixin):
    def process_request(self, request):
        assert hasattr(request, 'session'), (
            "The Django authentication middleware requires session middleware "
            "to be installed. Edit your MIDDLEWARE setting to insert "
            "'django.contrib.sessions.middleware.SessionMiddleware' before "
            "'django.contrib.auth.middleware.AuthenticationMiddleware'."
        )
        if request.headers.get("signature") and request.headers.get("message"):
            decoded = base64.b64decode(request.headers.get("message"))
            now = datetime.now()
            m_json = json.loads(decoded)
            if now.timestamp() * 1000 < m_json.get("timestamp") + 60 * 60 * 24 * 7 * 1000:
                signature = request.headers.get("signature")
                message_hash = defunct_hash_message(text=request.headers.get("message"))
                address = w3.eth.account.recoverHash(message_hash, signature=signature)
                request.wallet, _ = Wallet.objects.get_or_create(
                    address=address
                )
            else:
                request.wallet = None
        else:
            request.wallet = None
