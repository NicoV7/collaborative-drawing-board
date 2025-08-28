/**
 * Frontend encryption utilities for end-to-end encryption.
 * Uses Web Crypto API for AES-GCM encryption/decryption.
 */

export interface EncryptedData {
  data: string; // Base64 encoded encrypted data
  nonce: string; // Base64 encoded nonce
}

export class DrawingEncryption {
  private key: CryptoKey | null = null;

  constructor(key?: CryptoKey) {
    this.key = key || null;
  }

  /**
   * Generate a new AES-GCM encryption key
   */
  async generateKey(): Promise<CryptoKey> {
    const key = await crypto.subtle.generateKey(
      {
        name: 'AES-GCM',
        length: 256,
      },
      true, // extractable
      ['encrypt', 'decrypt']
    );
    
    this.key = key;
    return key;
  }

  /**
   * Import key from raw bytes
   */
  async importKey(keyBytes: ArrayBuffer): Promise<CryptoKey> {
    const key = await crypto.subtle.importKey(
      'raw',
      keyBytes,
      {
        name: 'AES-GCM',
        length: 256,
      },
      true,
      ['encrypt', 'decrypt']
    );
    
    this.key = key;
    return key;
  }

  /**
   * Export key as raw bytes
   */
  async exportKey(): Promise<ArrayBuffer> {
    if (!this.key) {
      throw new Error('No key available');
    }
    
    return await crypto.subtle.exportKey('raw', this.key);
  }

  /**
   * Encrypt drawing data
   */
  async encryptDrawingData(drawingData: string): Promise<EncryptedData> {
    if (!this.key) {
      throw new Error('No encryption key available');
    }

    const nonce = crypto.getRandomValues(new Uint8Array(12)); // 96-bit nonce
    const encodedData = new TextEncoder().encode(drawingData);

    const encryptedData = await crypto.subtle.encrypt(
      {
        name: 'AES-GCM',
        iv: nonce,
      },
      this.key,
      encodedData
    );

    return {
      data: this.arrayBufferToBase64(encryptedData),
      nonce: this.arrayBufferToBase64(nonce.buffer),
    };
  }

  /**
   * Decrypt drawing data
   */
  async decryptDrawingData(encryptedData: EncryptedData): Promise<string> {
    if (!this.key) {
      throw new Error('No encryption key available');
    }

    const data = this.base64ToArrayBuffer(encryptedData.data);
    const nonce = this.base64ToArrayBuffer(encryptedData.nonce);

    const decryptedData = await crypto.subtle.decrypt(
      {
        name: 'AES-GCM',
        iv: nonce,
      },
      this.key,
      data
    );

    return new TextDecoder().decode(decryptedData);
  }

  private arrayBufferToBase64(buffer: ArrayBuffer): string {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
  }

  private base64ToArrayBuffer(base64: string): ArrayBuffer {
    const binaryString = atob(base64);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    return bytes.buffer;
  }
}