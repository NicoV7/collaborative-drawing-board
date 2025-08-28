"""
Security tests for end-to-end encryption.
These tests ensure drawing data is properly encrypted using AES-GCM.
"""

import pytest
import json
from cryptography.exceptions import InvalidTag
from app.security import DrawingEncryption


class TestDrawingEncryption:
    """Test cases for drawing data encryption."""
    
    def test_encrypt_decrypt_drawing_data(self):
        """Test basic encryption and decryption of drawing data."""
        # Sample drawing data
        drawing_data = json.dumps({
            "shapes": [
                {"type": "line", "points": [10, 20, 30, 40], "stroke": "black"},
                {"type": "circle", "x": 100, "y": 150, "radius": 50, "fill": "red"}
            ],
            "timestamp": "2024-01-01T12:00:00Z"
        })
        
        encryption = DrawingEncryption()
        
        # Encrypt the data
        encrypted_data, nonce = encryption.encrypt_drawing_data(drawing_data)
        
        # Verify encrypted data is different from original
        assert encrypted_data != drawing_data
        assert len(encrypted_data) > 0
        assert len(nonce) > 0
        
        # Decrypt the data
        decrypted_data = encryption.decrypt_drawing_data(encrypted_data, nonce)
        
        # Verify decrypted data matches original
        assert decrypted_data == drawing_data
        assert json.loads(decrypted_data) == json.loads(drawing_data)
    
    def test_encryption_produces_different_ciphertext(self):
        """Test that same data produces different ciphertext due to random nonce."""
        drawing_data = '{"test": "data"}'
        encryption = DrawingEncryption()
        
        encrypted1, nonce1 = encryption.encrypt_drawing_data(drawing_data)
        encrypted2, nonce2 = encryption.encrypt_drawing_data(drawing_data)
        
        # Should produce different ciphertext and nonces
        assert encrypted1 != encrypted2
        assert nonce1 != nonce2
        
        # But both should decrypt to same data
        decrypted1 = encryption.decrypt_drawing_data(encrypted1, nonce1)
        decrypted2 = encryption.decrypt_drawing_data(encrypted2, nonce2)
        assert decrypted1 == decrypted2 == drawing_data
    
    def test_key_serialization(self):
        """Test key serialization and deserialization."""
        encryption1 = DrawingEncryption()
        key_b64 = encryption1.get_key_b64()
        
        # Create new instance from serialized key
        encryption2 = DrawingEncryption.from_key_b64(key_b64)
        
        # Should be able to decrypt data encrypted with first instance
        drawing_data = '{"shapes": [], "metadata": {"version": 1}}'
        encrypted_data, nonce = encryption1.encrypt_drawing_data(drawing_data)
        decrypted_data = encryption2.decrypt_drawing_data(encrypted_data, nonce)
        
        assert decrypted_data == drawing_data
    
    def test_invalid_tag_on_tampering(self):
        """Test that tampered ciphertext raises InvalidTag."""
        drawing_data = '{"secret": "drawing data"}'
        encryption = DrawingEncryption()
        
        encrypted_data, nonce = encryption.encrypt_drawing_data(drawing_data)
        
        # Tamper with encrypted data (flip last byte)
        tampered_data = encrypted_data[:-1] + ('A' if encrypted_data[-1] != 'A' else 'B')
        
        # Should raise InvalidTag when decrypting tampered data
        with pytest.raises(InvalidTag):
            encryption.decrypt_drawing_data(tampered_data, nonce)
    
    def test_wrong_key_fails_decryption(self):
        """Test that wrong key fails decryption."""
        drawing_data = '{"private": "user drawing"}'
        
        encryption1 = DrawingEncryption()
        encryption2 = DrawingEncryption()  # Different key
        
        encrypted_data, nonce = encryption1.encrypt_drawing_data(drawing_data)
        
        # Should fail with wrong key
        with pytest.raises(InvalidTag):
            encryption2.decrypt_drawing_data(encrypted_data, nonce)
    
    # FAILING TESTS for TDD - implement these features
    
    def test_encrypt_user_session_data(self):
        """Test encryption of user session data - SHOULD FAIL initially."""
        user_data = {"user_id": "123", "session_key": "secret_key", "permissions": ["read", "write"]}
        
        encryption = DrawingEncryption()
        encrypted_session = encryption.encrypt_user_session(json.dumps(user_data))
        
        assert "user_id" not in encrypted_session
        assert "session_key" not in encrypted_session
        
        decrypted_session = encryption.decrypt_user_session(encrypted_session)
        assert json.loads(decrypted_session) == user_data
    
    def test_batch_encrypt_drawing_operations(self):
        """Test batch encryption of drawing operations - SHOULD FAIL initially."""
        operations = [
            {"op": "draw_line", "data": [1, 2, 3, 4]},
            {"op": "draw_circle", "data": {"x": 10, "y": 20, "r": 5}},
            {"op": "erase", "data": {"area": [5, 5, 15, 15]}}
        ]
        
        encryption = DrawingEncryption()
        encrypted_batch = encryption.encrypt_operations_batch(operations)
        
        assert len(encrypted_batch) == len(operations)
        
        decrypted_batch = encryption.decrypt_operations_batch(encrypted_batch)
        assert decrypted_batch == operations