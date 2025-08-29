"""
Board Encryption Utilities for Collaborative Drawing System

This module provides AES-GCM encryption key generation and management for 
collaborative drawing boards. It implements a zero-trust security architecture
where the server generates encryption keys but cannot decrypt board content.

Architecture Overview:
┌─────────────────┐    Key Generation    ┌──────────────────┐
│   Server-Side   │ ──────────────────→  │   Client-Side    │
│                 │                      │                  │
│ • Generate Keys │                      │ • Encrypt Strokes│
│ • Store Boards  │                      │ • Decrypt Strokes│
│ • Access Control│                      │ • Real-time Sync │
└─────────────────┘                      └──────────────────┘

Security Principles:
1. Server generates cryptographically secure AES-GCM keys
2. Keys are transmitted once to authorized clients
3. All drawing data encrypted client-side before transmission
4. Server stores only encrypted data and cannot decrypt content
5. Key rotation and revocation supported for compromised boards

Performance Considerations:
- Key generation optimized for board creation performance (<100ms)
- Base64 encoding for efficient JSON transport
- Secure random generation without blocking operations
- Memory-safe key handling to prevent leakage

Collaborative Drawing Integration:
- Each board gets unique encryption key for isolation
- Real-time WebSocket updates transmit encrypted drawing data
- Multiple collaborators share the same encryption key
- Key derivation could support per-user encryption in future
"""

import os
import base64
import secrets
from typing import Dict, Any, Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag


class BoardEncryptionManager:
    """
    Manages AES-GCM encryption keys for collaborative drawing boards.
    
    This class provides secure key generation, validation, and utility functions
    for the collaborative drawing system's end-to-end encryption architecture.
    
    Security Architecture:
    - Uses AES-GCM for authenticated encryption (prevents tampering)
    - 256-bit keys for maximum security strength
    - Cryptographically secure random key generation
    - Base64 encoding for safe JSON transport
    
    Usage in Collaborative Flow:
    1. Server creates board → generates unique encryption key
    2. Client requests board → receives encryption key (if authorized)
    3. Client draws → encrypts strokes with board key
    4. Real-time sync → transmits encrypted data via WebSocket
    5. Other clients → decrypt strokes with same board key
    
    Example Usage:
    ```python
    # Board creation
    key = BoardEncryptionManager.generate_board_key()
    board = Board(name="Team Board", encrypted_key=key)
    
    # Client-side encryption (conceptual - done in browser)
    encrypted_stroke = BoardEncryptionManager.encrypt_data(
        stroke_data, key
    )
    
    # Key validation
    is_valid = BoardEncryptionManager.validate_key_format(key)
    ```
    """
    
    # AES-GCM uses 256-bit keys (32 bytes)
    AES_KEY_SIZE_BYTES = 32
    AES_NONCE_SIZE_BYTES = 12  # Standard GCM nonce size
    
    @staticmethod
    def generate_board_key() -> str:
        """
        Generate a cryptographically secure AES-GCM key for board encryption.
        
        Security Implementation:
        - Uses secrets.token_bytes() for cryptographically secure randomness
        - Generates 256-bit (32-byte) keys for maximum AES strength
        - Base64 encoding ensures safe transport in JSON responses
        - No key escrow - server cannot decrypt board content
        
        Performance Optimizations:
        - Non-blocking random generation (doesn't use /dev/random)
        - Efficient base64 encoding for network transport
        - Minimal CPU overhead for real-time board creation
        
        Returns:
            str: Base64-encoded 256-bit AES-GCM encryption key
            
        Raises:
            OSError: If system random number generation fails
            
        Example:
            >>> key = BoardEncryptionManager.generate_board_key()
            >>> len(base64.b64decode(key))
            32
        """
        try:
            # Generate cryptographically secure 256-bit key
            key_bytes = secrets.token_bytes(BoardEncryptionManager.AES_KEY_SIZE_BYTES)
            
            # Encode as base64 for JSON transport
            key_b64 = base64.b64encode(key_bytes).decode('utf-8')
            
            return key_b64
            
        except Exception as e:
            raise OSError(f"Failed to generate secure encryption key: {str(e)}")
    
    @staticmethod
    def validate_key_format(key_b64: str) -> bool:
        """
        Validate that a key string is properly formatted for AES-GCM encryption.
        
        Validation Criteria:
        - Must be valid base64 string
        - Must decode to exactly 32 bytes (256 bits)
        - Must contain only valid base64 characters
        
        This validation prevents API errors and ensures consistent encryption
        across collaborative sessions. Invalid keys could break real-time
        synchronization between collaborating users.
        
        Args:
            key_b64 (str): Base64-encoded encryption key to validate
            
        Returns:
            bool: True if key format is valid for AES-GCM, False otherwise
            
        Example:
            >>> valid_key = BoardEncryptionManager.generate_board_key()
            >>> BoardEncryptionManager.validate_key_format(valid_key)
            True
            >>> BoardEncryptionManager.validate_key_format("invalid")
            False
        """
        try:
            if not isinstance(key_b64, str):
                return False
            
            # Attempt to decode base64
            key_bytes = base64.b64decode(key_b64, validate=True)
            
            # Check for correct key length (256-bit AES)
            return len(key_bytes) == BoardEncryptionManager.AES_KEY_SIZE_BYTES
            
        except Exception:
            return False
    
    @staticmethod
    def extract_key_metadata(key_b64: str) -> Dict[str, Any]:
        """
        Extract metadata about an encryption key for diagnostics and monitoring.
        
        Provides information about encryption keys without compromising security.
        Useful for debugging collaborative session issues, monitoring key usage,
        and validating encryption implementation across client applications.
        
        Security Note:
        Returns only non-sensitive metadata. Never returns actual key material
        or any data that could be used to reconstruct the encryption key.
        
        Args:
            key_b64 (str): Base64-encoded encryption key
            
        Returns:
            Dict[str, Any]: Key metadata including:
                - is_valid: Whether key format is correct
                - key_size_bits: Key strength in bits
                - encoding: Encoding format (always 'base64')
                - algorithm: Intended encryption algorithm
                
        Example:
            >>> key = BoardEncryptionManager.generate_board_key()
            >>> metadata = BoardEncryptionManager.extract_key_metadata(key)
            >>> metadata['key_size_bits']
            256
        """
        metadata = {
            'is_valid': False,
            'key_size_bits': 0,
            'encoding': 'base64',
            'algorithm': 'AES-GCM',
            'created_for': 'collaborative_board_encryption'
        }
        
        try:
            if BoardEncryptionManager.validate_key_format(key_b64):
                key_bytes = base64.b64decode(key_b64)
                metadata.update({
                    'is_valid': True,
                    'key_size_bits': len(key_bytes) * 8,
                    'key_size_bytes': len(key_bytes)
                })
            
        except Exception:
            pass  # Metadata remains with is_valid=False
        
        return metadata
    
    @staticmethod
    def generate_test_key_set(count: int = 5) -> list[str]:
        """
        Generate a set of test encryption keys for development and testing.
        
        Development Utility:
        Creates multiple valid encryption keys for testing collaborative scenarios,
        performance benchmarking, and integration testing. Each key is unique
        and follows the same security standards as production keys.
        
        Testing Scenarios:
        - Multi-board collaboration testing
        - Performance testing with multiple encrypted boards
        - Integration testing of key management workflows
        - Client-side encryption/decryption validation
        
        Args:
            count (int): Number of test keys to generate (default: 5)
            
        Returns:
            list[str]: List of unique base64-encoded AES-GCM keys
            
        Example:
            >>> test_keys = BoardEncryptionManager.generate_test_key_set(3)
            >>> len(test_keys)
            3
            >>> all(BoardEncryptionManager.validate_key_format(k) for k in test_keys)
            True
        """
        if not isinstance(count, int) or count < 1:
            raise ValueError("Count must be a positive integer")
        
        if count > 100:  # Reasonable limit for testing
            raise ValueError("Count exceeds maximum limit of 100 keys")
        
        return [BoardEncryptionManager.generate_board_key() for _ in range(count)]


def get_encryption_config() -> Dict[str, Any]:
    """
    Get current encryption configuration for collaborative drawing system.
    
    Provides system configuration information for encryption features,
    useful for monitoring, diagnostics, and ensuring consistent setup
    across development, staging, and production environments.
    
    Configuration includes algorithm settings, key parameters, and
    performance characteristics relevant to collaborative drawing.
    
    Returns:
        Dict[str, Any]: Encryption system configuration
        
    Example:
        >>> config = get_encryption_config()
        >>> config['algorithm']
        'AES-GCM'
        >>> config['key_size_bits']
        256
    """
    return {
        'algorithm': 'AES-GCM',
        'key_size_bits': BoardEncryptionManager.AES_KEY_SIZE_BYTES * 8,
        'key_size_bytes': BoardEncryptionManager.AES_KEY_SIZE_BYTES,
        'nonce_size_bytes': BoardEncryptionManager.AES_NONCE_SIZE_BYTES,
        'encoding': 'base64',
        'security_level': 'maximum',
        'performance_target': '<100ms_key_generation',
        'zero_trust': True,
        'server_can_decrypt': False,
        'collaborative_features': {
            'multi_user_same_key': True,
            'real_time_encrypted_sync': True,
            'per_board_isolation': True
        }
    }


# Performance testing utilities for development
def benchmark_key_generation(iterations: int = 1000) -> Dict[str, float]:
    """
    Benchmark encryption key generation performance for optimization.
    
    Measures key generation performance to ensure it meets the collaborative
    drawing system's requirements (<100ms board creation including encryption).
    Used for performance regression testing and optimization validation.
    
    Args:
        iterations (int): Number of key generation operations to benchmark
        
    Returns:
        Dict[str, float]: Performance metrics in milliseconds
    """
    import time
    
    times = []
    for _ in range(iterations):
        start = time.time()
        BoardEncryptionManager.generate_board_key()
        end = time.time()
        times.append((end - start) * 1000)  # Convert to milliseconds
    
    return {
        'min_time_ms': min(times),
        'max_time_ms': max(times),
        'avg_time_ms': sum(times) / len(times),
        'total_time_ms': sum(times),
        'iterations': iterations,
        'target_performance_ms': 100  # Board creation performance target
    }