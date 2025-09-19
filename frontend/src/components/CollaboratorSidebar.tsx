/**
 * CollaboratorSidebar - Phase 5 Collaborative User Interface Component
 * 
 * A minimizable sidebar panel showing active collaborators with:
 * - User presence list with avatars and online status
 * - Minimizable panel with toggle arrow
 * - Real-time user activity indicators
 * - Avatar management with fallback initials
 * - Integration with TTL user presence system
 * 
 * Features:
 * - Real-time collaboration status
 * - User avatar display with fallbacks
 * - Minimizable/expandable sidebar
 * - Keyboard accessibility
 * - Responsive design
 */

import React, { useState, useEffect, useCallback } from 'react';
import './CollaboratorSidebar.css';

interface User {
  id: string;
  username: string;
  email: string;
  avatarUrl?: string;
  isOnline: boolean;
  lastSeen: Date;
}

interface UserPresence {
  userId: string;
  boardId: string;
  isActive: boolean;
  lastSeen: Date;
  cursorPosition?: { x: number; y: number };
}

interface CollaboratorSidebarProps {
  boardId: string;
  currentUserId: string;
  isVisible?: boolean;
  onToggleVisibility?: (visible: boolean) => void;
  className?: string;
}

const CollaboratorSidebar: React.FC<CollaboratorSidebarProps> = ({
  boardId,
  currentUserId,
  isVisible = true,
  onToggleVisibility,
  className = ''
}) => {
  const [isMinimized, setIsMinimized] = useState(false);
  const [collaborators, setCollaborators] = useState<User[]>([]);
  const [userPresence, setUserPresence] = useState<Map<string, UserPresence>>(new Map());
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Toggle sidebar minimization
  const handleToggleMinimized = useCallback(() => {
    const newMinimized = !isMinimized;
    setIsMinimized(newMinimized);
    onToggleVisibility?.(newMinimized);
  }, [isMinimized, onToggleVisibility]);

  // Fetch collaborators for the board
  const fetchCollaborators = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // This would integrate with backend API
      const response = await fetch(`/api/boards/${boardId}/collaborators`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch collaborators');
      }
      
      const data = await response.json();
      setCollaborators(data.collaborators || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      console.error('Failed to fetch collaborators:', err);
    } finally {
      setIsLoading(false);
    }
  }, [boardId]);

  // Fetch user presence data
  const fetchUserPresence = useCallback(async () => {
    try {
      const response = await fetch(`/api/boards/${boardId}/presence`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        const presenceMap = new Map<string, UserPresence>();
        
        data.presence.forEach((p: UserPresence) => {
          presenceMap.set(p.userId, {
            ...p,
            lastSeen: new Date(p.lastSeen)
          });
        });
        
        setUserPresence(presenceMap);
      }
    } catch (err) {
      console.error('Failed to fetch user presence:', err);
    }
  }, [boardId]);

  // Update user presence (called by drawing events)
  const updateUserPresence = useCallback(async (cursorPosition?: { x: number; y: number }) => {
    try {
      await fetch(`/api/boards/${boardId}/presence`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          userId: currentUserId,
          boardId,
          isActive: true,
          cursorPosition,
          timestamp: new Date().toISOString()
        })
      });
    } catch (err) {
      console.error('Failed to update user presence:', err);
    }
  }, [boardId, currentUserId]);

  // Set up real-time presence updates
  useEffect(() => {
    let mounted = true;

    const initializeData = async () => {
      if (mounted) {
        await fetchCollaborators();
        await fetchUserPresence();
      }
    };

    initializeData();

    // Set up periodic presence updates
    const presenceInterval = setInterval(() => {
      if (mounted) {
        fetchUserPresence();
      }
    }, 5000); // Every 5 seconds

    // Set up WebSocket for real-time presence (would be implemented with actual WebSocket)
    // const ws = new WebSocket(`ws://localhost:8000/ws/boards/${boardId}/presence`);
    // ws.onmessage = (event) => {
    //   const presence = JSON.parse(event.data);
    //   if (mounted) {
    //     setUserPresence(prev => new Map(prev.set(presence.userId, presence)));
    //   }
    // };

    return () => {
      mounted = false;
      clearInterval(presenceInterval);
      // ws.close();
    };
  }, [boardId, fetchCollaborators, fetchUserPresence]);

  // Generate user initials for avatar fallback
  const getUserInitials = useCallback((username: string): string => {
    return username
      .split(' ')
      .map(word => word.charAt(0))
      .join('')
      .toUpperCase()
      .slice(0, 2);
  }, []);

  // Determine user online status
  const isUserOnline = useCallback((user: User): boolean => {
    const presence = userPresence.get(user.id);
    if (!presence) {
      // Fall back to user's base online status if no presence data
      return user.isOnline;
    }

    // User is online if they've been active in the last 2 minutes
    const threshold = new Date(Date.now() - 2 * 60 * 1000);
    return presence.isActive && presence.lastSeen > threshold;
  }, [userPresence]);

  // Format last seen time
  const formatLastSeen = useCallback((lastSeen: Date): string => {
    const now = new Date();
    const diff = now.getTime() - lastSeen.getTime();
    const minutes = Math.floor(diff / 60000);
    
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  }, []);

  // Handle keyboard navigation
  const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      handleToggleMinimized();
    }
  }, [handleToggleMinimized]);

  if (!isVisible) {
    return null;
  }

  const activeCollaborators = collaborators.filter(user => user.id !== currentUserId);
  const onlineCount = activeCollaborators.filter(isUserOnline).length;

  return (
    <div 
      className={`collaborator-sidebar ${isMinimized ? 'minimized' : 'expanded'} ${className}`}
      role="complementary"
      aria-label="Collaborators panel"
    >
      <div 
        className="sidebar-header"
        onClick={handleToggleMinimized}
        onKeyDown={handleKeyDown}
        role="button"
        tabIndex={0}
        aria-expanded={!isMinimized}
        aria-controls="collaborators-content"
      >
        <div className="header-content">
          <h3 className="sidebar-title">
            Collaborators {onlineCount > 0 && `(${onlineCount} online)`}
          </h3>
          <button 
            className={`toggle-button ${isMinimized ? 'minimized' : 'expanded'}`}
            aria-label={isMinimized ? 'Expand collaborators panel' : 'Minimize collaborators panel'}
          >
            <svg 
              className="toggle-icon"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
            >
              <polyline points="6,9 12,15 18,9" />
            </svg>
          </button>
        </div>
      </div>

      <div 
        id="collaborators-content"
        className={`sidebar-content ${isMinimized ? 'hidden' : 'visible'}`}
        aria-hidden={isMinimized}
      >
        {isLoading ? (
          <div className="loading-state" aria-live="polite">
            <div className="loading-spinner" />
            <span>Loading collaborators...</span>
          </div>
        ) : error ? (
          <div className="error-state" role="alert">
            <span className="error-message">{error}</span>
            <button 
              className="retry-button"
              onClick={fetchCollaborators}
              aria-label="Retry loading collaborators"
            >
              Retry
            </button>
          </div>
        ) : activeCollaborators.length === 0 ? (
          <div className="empty-state">
            <p>No other collaborators yet.</p>
            <p className="empty-hint">Share this board to start collaborating!</p>
          </div>
        ) : (
          <div className="collaborators-list" role="list">
            {activeCollaborators.map((user) => {
              const isOnline = isUserOnline(user);
              const presence = userPresence.get(user.id);
              
              return (
                <div 
                  key={user.id}
                  className={`collaborator-item ${isOnline ? 'online' : 'offline'}`}
                  role="listitem"
                >
                  <div className="user-avatar-container">
                    {user.avatarUrl ? (
                      <img 
                        className="user-avatar"
                        src={user.avatarUrl}
                        alt={`${user.username}'s avatar`}
                        onError={(e) => {
                          // Fallback to initials on image load error
                          const target = e.target as HTMLImageElement;
                          target.style.display = 'none';
                          const fallback = target.nextElementSibling as HTMLElement;
                          if (fallback) fallback.style.display = 'flex';
                        }}
                      />
                    ) : null}
                    <div 
                      className="user-avatar-fallback"
                      style={{ display: user.avatarUrl ? 'none' : 'flex' }}
                    >
                      {getUserInitials(user.username)}
                    </div>
                    <div className={`status-indicator ${isOnline ? 'online' : 'offline'}`} />
                  </div>
                  
                  <div className="user-info">
                    <div className="user-name">{user.username}</div>
                    <div className="user-status">
                      {isOnline ? (
                        presence?.cursorPosition ? 'Drawing' : 'Online'
                      ) : (
                        `Last seen ${formatLastSeen(user.lastSeen)}`
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default CollaboratorSidebar;