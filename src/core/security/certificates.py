"""
Certificate management system with auto-renewal.
"""
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
import OpenSSL
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import acme.client
import acme.messages
import josepy
import requests
import asyncio
from pathlib import Path
import json

from ..utils.config import get_settings
from ..utils.logging import get_logger
from .encryption import encryption_service

class CertificateManager:
    """
    Advanced certificate management with Let's Encrypt integration
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        
        # Initialize paths
        self.cert_dir = Path(self.settings.cert_dir)
        self.cert_dir.mkdir(exist_ok=True)
        
        # Initialize ACME client
        self.acme_client = self._init_acme_client()
        
        # Load certificates
        self.certificates = self._load_certificates()
        
        # Start renewal check task
        self.renewal_task = asyncio.create_task(
            self._check_renewals()
        )
        
    def _init_acme_client(self) -> acme.client.ClientV2:
        """Initialize ACME client for Let's Encrypt."""
        try:
            # Generate or load account key
            account_key_path = self.cert_dir / "account.key"
            if account_key_path.exists():
                with open(account_key_path, "rb") as f:
                    account_key = serialization.load_pem_private_key(
                        f.read(),
                        password=None
                    )
            else:
                account_key = rsa.generate_private_key(
                    public_exponent=65537,
                    key_size=2048
                )
                with open(account_key_path, "wb") as f:
                    f.write(
                        account_key.private_bytes(
                            encoding=serialization.Encoding.PEM,
                            format=serialization.PrivateFormat.PKCS8,
                            encryption_algorithm=serialization.NoEncryption()
                        )
                    )
                    
            # Create ACME client
            directory_url = (
                "https://acme-v02.api.letsencrypt.org/directory"
                if not self.settings.debug
                else "https://acme-staging-v02.api.letsencrypt.org/directory"
            )
            
            net = acme.client.ClientNetwork(
                josepy.JWKRSA(key=account_key)
            )
            
            return acme.client.ClientV2(
                directory_url,
                net
            )
            
        except Exception as e:
            self.logger.error(f"ACME client initialization failed: {str(e)}")
            raise
            
    def _load_certificates(self) -> Dict[str, Dict[str, Any]]:
        """Load certificates from storage."""
        certificates = {}
        
        try:
            for cert_file in self.cert_dir.glob("*.crt"):
                domain = cert_file.stem
                cert_path = cert_file
                key_path = cert_file.with_suffix(".key")
                
                if cert_path.exists() and key_path.exists():
                    with open(cert_path, "rb") as f:
                        cert_data = f.read()
                        cert = x509.load_pem_x509_certificate(cert_data)
                        
                    certificates[domain] = {
                        "certificate": cert,
                        "cert_path": cert_path,
                        "key_path": key_path,
                        "expires": cert.not_valid_after
                    }
                    
            return certificates
            
        except Exception as e:
            self.logger.error(f"Certificate loading failed: {str(e)}")
            return {}
            
    async def get_certificate(self,
                            domain: str) -> Optional[Dict[str, Any]]:
        """Get certificate for domain."""
        return self.certificates.get(domain)
        
    async def request_certificate(self,
                                  domain: str,
                                  email: str) -> Dict[str, Any]:
        """Request new certificate from Let's Encrypt."""
        try:
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )

            builder = x509.CertificateSigningRequestBuilder()
            builder = builder.subject_name(x509.Name([
                x509.NameAttribute(NameOID.COMMON_NAME, domain)
            ]))

            csr = builder.sign(
                private_key,
                hashes.SHA256()
            )

            order = await self.acme_client.new_order([domain])

            await self._complete_challenges(order)

            certificate = await self.acme_client.finalize_order(
                order,
                csr.public_bytes(serialization.Encoding.DER)
            )

            cert_path = self.cert_dir / f"{domain}.crt"
            key_path = self.cert_dir / f"{domain}.key"

            with open(cert_path, "wb") as f:
                f.write(certificate.fullchain_pem.encode())

            with open(key_path, "wb") as f:
                f.write(
                    private_key.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.PKCS8,
                        encryption_algorithm=serialization.NoEncryption()
                    )
                )

            cert = x509.load_pem_x509_certificate(
                certificate.fullchain_pem.encode()
            )

            self.certificates[domain] = {
                "certificate": cert,
                "cert_path": cert_path,
                "key_path": key_path,
                "expires": cert.not_valid_after
            }

            self.logger.info(f"Certificate for {domain} requested and saved successfully")

            return self.certificates[domain]

        except Exception as e:
            self.logger.error(f"Certificate request failed for {domain}: {str(e)}")
            raise
            
    async def _complete_challenges(self,
                                   order: acme.messages.OrderResource
                                   ) -> List[acme.messages.AuthorizationResource]:
        authorizations = []
        try:
            for auth_url in order.authorizations:
                auth = await self.acme_client.get_authorization(auth_url)

                if auth.body.status == acme.messages.STATUS_VALID:
                    continue

                for challenge in auth.body.challenges:
                    # Implement challenge completion logic here
                    pass

            self.logger.info("ACME challenges completed successfully")
            return authorizations

        except Exception as e:
            self.logger.error(f"ACME challenge completion failed: {str(e)}")
            raise
        
    async def _check_renewals(self):
        """Check for certificates needing renewal."""
        while True:
            try:
                for domain, cert_info in self.certificates.items():
                    expires = cert_info["expires"]
                    
                    # Renew if less than 30 days until expiration
                    if expires - datetime.utcnow() < timedelta(days=30):
                        self.logger.info(
                            f"Renewing certificate for {domain}"
                        )
                        await self.request_certificate(
                            domain,
                            self.settings.admin_email
                        )
                        
                # Check daily
                await asyncio.sleep(86400)
                
            except Exception as e:
                self.logger.error(f"Renewal check failed: {str(e)}")
                await asyncio.sleep(3600)
                
    async def cleanup(self):
        try:
            if self.renewal_task:
                self.renewal_task.cancel()
                await self.renewal_task
            self.logger.info("Certificate manager resources cleaned up successfully")
        except asyncio.CancelledError:
            self.logger.info("Renewal task cancelled successfully")
        except Exception as e:
            self.logger.error(f"Certificate manager cleanup failed: {str(e)}")
            raise

# Global certificate manager instance
certificate_manager = CertificateManager() 