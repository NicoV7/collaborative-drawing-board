"""
Security module for end-to-end encryption using AES-GCM.
All drawing data must be encrypted before storage and transmission.
"""

from typing import Tuple, Optional
import base64
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag


class DrawingEncryption:
    """Handles AES-GCM encryption/decryption for drawing data."""
    
    def __init__(self, key: Optional[bytes] = None):
        """Initialize with encryption key."""
        self.key = key or AESGCM.generate_key(bit_length=256)
        self.aesgcm = AESGCM(self.key)
    
    def encrypt_drawing_data(self, drawing_data: str) -> Tuple[str, str]:
        """
        Encrypt drawing data using AES-GCM.
        
        Args:
            drawing_data: JSON string of drawing data
            
        Returns:
            Tuple of (encrypted_data_base64, nonce_base64)
        """
        nonce = os.urandom(12)  # 96-bit nonce for GCM
        encrypted_data = self.aesgcm.encrypt(nonce, drawing_data.encode('utf-8'), None)
        
        return (
            base64.b64encode(encrypted_data).decode('ascii'),
            base64.b64encode(nonce).decode('ascii')
        )
    
    def decrypt_drawing_data(self, encrypted_data_b64: str, nonce_b64: str) -> str:
        """
        Decrypt drawing data using AES-GCM.
        
        Args:
            encrypted_data_b64: Base64 encoded encrypted data
            nonce_b64: Base64 encoded nonce
            
        Returns:
            Decrypted drawing data as JSON string
            
        Raises:
            InvalidTag: If authentication fails
        """
        encrypted_data = base64.b64decode(encrypted_data_b64.encode('ascii'))
        nonce = base64.b64decode(nonce_b64.encode('ascii'))
        
        decrypted_data = self.aesgcm.decrypt(nonce, encrypted_data, None)
        return decrypted_data.decode('utf-8')
    
    def get_key_b64(self) -> str:
        """Get the encryption key as base64 string."""
        return base64.b64encode(self.key).decode('ascii')
    
    @classmethod
    def from_key_b64(cls, key_b64: str) -> 'DrawingEncryption':
        """Create instance from base64 encoded key."""
        key = base64.b64decode(key_b64.encode('ascii'))
        return cls(key)