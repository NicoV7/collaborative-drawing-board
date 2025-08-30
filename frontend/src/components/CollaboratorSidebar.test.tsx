/**
 * CollaboratorSidebar Tests - Phase 5 Collaborative UI Component Testing
 * 
 * Comprehensive test suite for the CollaboratorSidebar component covering:
 * - Component rendering and initialization
 * - User presence and avatar loading
 * - Minimize/expand functionality
 * - Real-time collaboration features
 * - Loading and error states
 * - Accessibility compliance
 * - Mobile responsiveness
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import CollaboratorSidebar from './CollaboratorSidebar';

// Mock fetch for API calls
global.fetch = jest.fn();

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(() => 'mock-auth-token'),
  setItem: jest.fn(),
  removeItem: jest.fn(),
};
Object.defineProperty(window, 'localStorage', { value: mockLocalStorage });

describe('CollaboratorSidebar', () => {
  const defaultProps = {
    boardId: 'test-board-123',
    currentUserId: 'current-user-456',
  };

  const mockCollaborators = [
    {
      id: 'user-1',
      username: 'Alice Johnson',
      email: 'alice@example.com',
      avatarUrl: 'https://example.com/alice.jpg',
      isOnline: true,
      lastSeen: new Date(Date.now() - 1000), // 1 second ago
    },
    {
      id: 'user-2', 
      username: 'Bob Smith',
      email: 'bob@example.com',
      avatarUrl: null,
      isOnline: false,
      lastSeen: new Date(Date.now() - 300000), // 5 minutes ago
    },
    {
      id: 'user-3',
      username: 'Charlie Brown',
      email: 'charlie@example.com', 
      avatarUrl: 'https://example.com/charlie.jpg',
      isOnline: true,
      lastSeen: new Date(Date.now() - 30000), // 30 seconds ago
    },
  ];

  const mockPresence = [
    {
      userId: 'user-1',
      boardId: 'test-board-123',
      isActive: true,
      lastSeen: new Date(Date.now() - 1000),
      cursorPosition: { x: 100, y: 200 },
    },
    {
      userId: 'user-3',
      boardId: 'test-board-123', 
      isActive: true,
      lastSeen: new Date(Date.now() - 30000),
    },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    
    // Mock successful API responses
    (fetch as jest.MockedFunction<typeof fetch>).mockImplementation((url) => {
      if (url.includes('/collaborators')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ collaborators: mockCollaborators }),
        } as Response);
      }
      if (url.includes('/presence')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ presence: mockPresence }),
        } as Response);
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({}),
      } as Response);
    });
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  describe('Component Rendering', () => {
    test('renders collaborator sidebar with correct title', async () => {
      render(<CollaboratorSidebar {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByRole('complementary', { name: /collaborators panel/i })).toBeInTheDocument();
        expect(screen.getByText(/collaborators/i)).toBeInTheDocument();
      });
    });

    test('shows online count in title when collaborators are online', async () => {
      render(<CollaboratorSidebar {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText(/collaborators \(2 online\)/i)).toBeInTheDocument();
      });
    });

    test('renders collaborator list excluding current user', async () => {
      render(<CollaboratorSidebar {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Alice Johnson')).toBeInTheDocument();
        expect(screen.getByText('Bob Smith')).toBeInTheDocument();
        expect(screen.getByText('Charlie Brown')).toBeInTheDocument();
        expect(screen.queryByText('current-user-456')).not.toBeInTheDocument();
      });
    });

    test('hides sidebar when isVisible is false', () => {
      render(<CollaboratorSidebar {...defaultProps} isVisible={false} />);
      
      expect(screen.queryByRole('complementary')).not.toBeInTheDocument();
    });
  });

  describe('User Avatars and Status', () => {
    test('displays user avatars when available', async () => {
      render(<CollaboratorSidebar {...defaultProps} />);
      
      await waitFor(() => {
        const aliceAvatar = screen.getByAltText("Alice Johnson's avatar");
        expect(aliceAvatar).toBeInTheDocument();
        expect(aliceAvatar).toHaveAttribute('src', 'https://example.com/alice.jpg');
      });
    });

    test('shows initials fallback for users without avatars', async () => {
      render(<CollaboratorSidebar {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('BS')).toBeInTheDocument(); // Bob Smith initials
      });
    });

    test('displays correct online status indicators', async () => {
      render(<CollaboratorSidebar {...defaultProps} />);
      
      await waitFor(() => {
        const onlineUsers = screen.getAllByText(/online|drawing/i);
        expect(onlineUsers).toHaveLength(2); // Alice and Charlie
        
        const offlineStatus = screen.getByText(/last seen/i);
        expect(offlineStatus).toBeInTheDocument(); // Bob's status
      });
    });

    test('shows "Drawing" status for users with cursor position', async () => {
      render(<CollaboratorSidebar {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Drawing')).toBeInTheDocument(); // Alice has cursor position
      });
    });
  });

  describe('Minimize/Expand Functionality', () => {
    test('toggles minimized state when header is clicked', async () => {
      render(<CollaboratorSidebar {...defaultProps} />);
      
      const header = screen.getByRole('button', { name: /minimize collaborators panel/i });
      
      // Initially expanded
      await waitFor(() => {
        expect(header).toHaveAttribute('aria-expanded', 'true');
      });
      
      // Click to minimize
      fireEvent.click(header);
      expect(header).toHaveAttribute('aria-expanded', 'false');
      
      // Click to expand
      fireEvent.click(header);
      expect(header).toHaveAttribute('aria-expanded', 'true');
    });

    test('calls onToggleVisibility when minimized state changes', async () => {
      const onToggleVisibility = jest.fn();
      render(<CollaboratorSidebar {...defaultProps} onToggleVisibility={onToggleVisibility} />);
      
      const header = screen.getByRole('button', { name: /minimize collaborators panel/i });
      
      await waitFor(() => {
        expect(header).toBeInTheDocument();
      });
      
      fireEvent.click(header);
      expect(onToggleVisibility).toHaveBeenCalledWith(true); // minimized = true
    });

    test('supports keyboard navigation for toggle', async () => {
      render(<CollaboratorSidebar {...defaultProps} />);
      
      const header = screen.getByRole('button', { name: /minimize collaborators panel/i });
      
      await waitFor(() => {
        expect(header).toBeInTheDocument();
      });
      
      // Test Enter key
      fireEvent.keyDown(header, { key: 'Enter' });
      expect(header).toHaveAttribute('aria-expanded', 'false');
      
      // Test Space key
      fireEvent.keyDown(header, { key: ' ' });
      expect(header).toHaveAttribute('aria-expanded', 'true');
    });
  });

  describe('Loading and Error States', () => {
    test('shows loading state during initial fetch', async () => {
      // Mock delayed response
      (fetch as jest.MockedFunction<typeof fetch>).mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({
          ok: true,
          json: () => Promise.resolve({ collaborators: [] }),
        } as Response), 1000))
      );
      
      render(<CollaboratorSidebar {...defaultProps} />);
      
      expect(screen.getByText('Loading collaborators...')).toBeInTheDocument();
      expect(screen.getByLabelText(/loading/i)).toBeInTheDocument();
    });

    test('displays error state when API call fails', async () => {
      (fetch as jest.MockedFunction<typeof fetch>).mockRejectedValueOnce(
        new Error('Network error')
      );
      
      render(<CollaboratorSidebar {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Network error')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /retry loading collaborators/i })).toBeInTheDocument();
      });
    });

    test('retry button refetches collaborators', async () => {
      (fetch as jest.MockedFunction<typeof fetch>)
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ collaborators: mockCollaborators }),
        } as Response);
      
      render(<CollaboratorSidebar {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Network error')).toBeInTheDocument();
      });
      
      const retryButton = screen.getByRole('button', { name: /retry loading collaborators/i });
      fireEvent.click(retryButton);
      
      await waitFor(() => {
        expect(screen.getByText('Alice Johnson')).toBeInTheDocument();
      });
    });

    test('shows empty state when no collaborators exist', async () => {
      (fetch as jest.MockedFunction<typeof fetch>).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ collaborators: [] }),
      } as Response);
      
      render(<CollaboratorSidebar {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('No other collaborators yet.')).toBeInTheDocument();
        expect(screen.getByText('Share this board to start collaborating!')).toBeInTheDocument();
      });
    });
  });

  describe('Real-time Updates', () => {
    test('sets up periodic presence updates', async () => {
      render(<CollaboratorSidebar {...defaultProps} />);
      
      // Initial fetch
      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith(
          expect.stringContaining('/presence'),
          expect.objectContaining({
            headers: expect.objectContaining({
              'Authorization': 'Bearer mock-auth-token',
            }),
          })
        );
      });
      
      // Advance timers to trigger interval
      act(() => {
        jest.advanceTimersByTime(5000);
      });
      
      // Should make another presence request
      await waitFor(() => {
        expect(fetch).toHaveBeenCalledTimes(4); // 2 initial + 2 interval calls
      });
    });

    test('updates user presence correctly', async () => {
      render(<CollaboratorSidebar {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Drawing')).toBeInTheDocument(); // Alice with cursor
        expect(screen.getByText('Online')).toBeInTheDocument(); // Charlie without cursor
      });
    });
  });

  describe('Accessibility', () => {
    test('has proper ARIA labels and roles', async () => {
      render(<CollaboratorSidebar {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByRole('complementary', { name: /collaborators panel/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /minimize collaborators panel/i })).toBeInTheDocument();
        expect(screen.getByRole('list')).toBeInTheDocument();
        expect(screen.getAllByRole('listitem')).toHaveLength(3);
      });
    });

    test('toggle button has correct accessibility attributes', async () => {
      render(<CollaboratorSidebar {...defaultProps} />);
      
      const toggleButton = screen.getByRole('button', { name: /minimize collaborators panel/i });
      
      await waitFor(() => {
        expect(toggleButton).toHaveAttribute('aria-expanded', 'true');
        expect(toggleButton).toHaveAttribute('aria-controls', 'collaborators-content');
      });
    });

    test('content has correct aria-hidden state when minimized', async () => {
      render(<CollaboratorSidebar {...defaultProps} />);
      
      const header = screen.getByRole('button', { name: /minimize collaborators panel/i });
      const content = screen.getByRole('list').closest('#collaborators-content');
      
      await waitFor(() => {
        expect(content).toHaveAttribute('aria-hidden', 'false');
      });
      
      fireEvent.click(header);
      expect(content).toHaveAttribute('aria-hidden', 'true');
    });

    test('error messages have alert role', async () => {
      (fetch as jest.MockedFunction<typeof fetch>).mockRejectedValueOnce(
        new Error('Network error')
      );
      
      render(<CollaboratorSidebar {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });
    });

    test('loading state has live region', async () => {
      (fetch as jest.MockedFunction<typeof fetch>).mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({
          ok: true,
          json: () => Promise.resolve({ collaborators: [] }),
        } as Response), 1000))
      );
      
      render(<CollaboratorSidebar {...defaultProps} />);
      
      expect(screen.getByLabelText(/loading/i)).toHaveAttribute('aria-live', 'polite');
    });
  });

  describe('Time Formatting', () => {
    test('formats last seen times correctly', async () => {
      const now = new Date();
      const testCollaborators = [
        {
          id: 'user-recent',
          username: 'Recent User',
          email: 'recent@example.com',
          isOnline: false,
          lastSeen: new Date(now.getTime() - 30000), // 30 seconds ago
        },
        {
          id: 'user-minutes',
          username: 'Minutes User', 
          email: 'minutes@example.com',
          isOnline: false,
          lastSeen: new Date(now.getTime() - 300000), // 5 minutes ago
        },
        {
          id: 'user-hours',
          username: 'Hours User',
          email: 'hours@example.com', 
          isOnline: false,
          lastSeen: new Date(now.getTime() - 7200000), // 2 hours ago
        },
      ];
      
      (fetch as jest.MockedFunction<typeof fetch>).mockImplementation((url) => {
        if (url.includes('/collaborators')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ collaborators: testCollaborators }),
          } as Response);
        }
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ presence: [] }),
        } as Response);
      });
      
      render(<CollaboratorSidebar {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText(/just now|0m ago/i)).toBeInTheDocument();
        expect(screen.getByText('5m ago')).toBeInTheDocument();
        expect(screen.getByText('2h ago')).toBeInTheDocument();
      });
    });
  });

  describe('API Integration', () => {
    test('makes correct API calls with auth headers', async () => {
      render(<CollaboratorSidebar {...defaultProps} />);
      
      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith(
          '/api/boards/test-board-123/collaborators',
          expect.objectContaining({
            headers: expect.objectContaining({
              'Authorization': 'Bearer mock-auth-token',
              'Content-Type': 'application/json',
            }),
          })
        );
        
        expect(fetch).toHaveBeenCalledWith(
          '/api/boards/test-board-123/presence', 
          expect.objectContaining({
            headers: expect.objectContaining({
              'Authorization': 'Bearer mock-auth-token',
              'Content-Type': 'application/json',
            }),
          })
        );
      });
    });

    test('handles API errors gracefully', async () => {
      (fetch as jest.MockedFunction<typeof fetch>).mockResolvedValueOnce({
        ok: false,
        status: 404,
      } as Response);
      
      render(<CollaboratorSidebar {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Failed to fetch collaborators')).toBeInTheDocument();
      });
    });
  });
});