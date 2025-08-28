/**
 * Frontend encryption tests for AES-GCM encryption.
 * Ensures drawing data is properly encrypted on the client side.
 */

import { DrawingEncryption } from './encryption';

// Mock crypto for testing environment
const mockCrypto = {
  subtle: {
    generateKey: jest.fn(),
    importKey: jest.fn(),
    exportKey: jest.fn(),
    encrypt: jest.fn(),
    decrypt: jest.fn(),
  },
  getRandomValues: jest.fn(),
};

Object.defineProperty(global, 'crypto', {
  value: mockCrypto,
});

describe('DrawingEncryption', () => {
  let encryption: DrawingEncryption;

  beforeEach(() => {
    encryption = new DrawingEncryption();
    jest.clearAllMocks();
  });

  test('generates encryption key', async () => {
    const mockKey = {} as CryptoKey;
    mockCrypto.subtle.generateKey.mockResolvedValue(mockKey);

    const key = await encryption.generateKey();

    expect(crypto.subtle.generateKey).toHaveBeenCalledWith(
      { name: 'AES-GCM', length: 256 },
      true,
      ['encrypt', 'decrypt']
    );
    expect(key).toBe(mockKey);
  });

  test('encrypts drawing data', async () => {
    const mockKey = {} as CryptoKey;
    const mockEncryptedData = new ArrayBuffer(32);
    const mockNonce = new Uint8Array(12);
    
    mockCrypto.subtle.encrypt.mockResolvedValue(mockEncryptedData);
    mockCrypto.getRandomValues.mockReturnValue(mockNonce);

    // Set up encryption with mock key
    encryption = new DrawingEncryption(mockKey);

    const drawingData = JSON.stringify({
      shapes: [{ type: 'line', points: [0, 0, 10, 10] }]
    });

    const result = await encryption.encryptDrawingData(drawingData);

    expect(crypto.subtle.encrypt).toHaveBeenCalledWith(
      { name: 'AES-GCM', iv: mockNonce },
      mockKey,
      expect.any(Uint8Array)
    );
    expect(result).toHaveProperty('data');
    expect(result).toHaveProperty('nonce');
  });

  test('throws error when encrypting without key', async () => {
    const drawingData = '{"test": "data"}';

    await expect(encryption.encryptDrawingData(drawingData))
      .rejects.toThrow('No encryption key available');
  });

  // FAILING TESTS for TDD - implement these features

  test('encrypts user preferences - SHOULD FAIL initially', async () => {
    const preferences = {
      theme: 'dark',
      brushSize: 5,
      favoriteColors: ['#FF0000', '#00FF00', '#0000FF']
    };

    const mockKey = {} as CryptoKey;
    encryption = new DrawingEncryption(mockKey);

    const encrypted = await encryption.encryptUserPreferences(preferences);
    expect(encrypted).toHaveProperty('data');
    expect(encrypted).toHaveProperty('nonce');

    const decrypted = await encryption.decryptUserPreferences(encrypted);
    expect(decrypted).toEqual(preferences);
  });

  test('batch encrypts drawing operations - SHOULD FAIL initially', async () => {
    const operations = [
      { type: 'stroke', data: [1, 2, 3, 4] },
      { type: 'erase', data: { x: 10, y: 20 } }
    ];

    const mockKey = {} as CryptoKey;
    encryption = new DrawingEncryption(mockKey);

    const encrypted = await encryption.batchEncryptOperations(operations);
    expect(Array.isArray(encrypted)).toBe(true);
    expect(encrypted).toHaveLength(operations.length);

    const decrypted = await encryption.batchDecryptOperations(encrypted);
    expect(decrypted).toEqual(operations);
  });
});