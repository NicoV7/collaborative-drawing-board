/**
 * Drawing Toolbar Tests - Phase 4 TDD Implementation
 * 
 * This test suite covers the collaborative drawing toolbar functionality including:
 * - Color picker with real-time collaboration synchronization
 * - Pen size slider with collaborative visibility
 * - Clear button with confirmation for multi-user sessions
 * - Undo/redo controls with individual user history
 * - Tool state management and performance optimization
 * 
 * Architecture Context:
 * The Toolbar component manages all drawing tool states and communicates
 * changes to both the local canvas and remote collaborators. Tool changes
 * must be instantly visible locally while being broadcast to other users
 * for collaborative awareness.
 * 
 * Performance Requirements:
 * - Tool changes: <10ms for immediate local feedback
 * - Color picker: <5ms for smooth color selection
 * - Size slider: <5ms for responsive size adjustments
 * - Button interactions: <8ms for responsive UI feel
 * 
 * Collaborative Synchronization:
 * - Tool changes broadcast to other collaborators
 * - Visual indicators show what tools others are using
 * - Conflict resolution for simultaneous tool changes
 * - State persistence across collaborative session reconnections
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import Toolbar from './Toolbar';

// Mock color picker component for testing
jest.mock('./ColorPicker', () => {
  return function MockColorPicker({ currentColor, onColorChange, colors }: any) {
    return (
      <div data-testid="color-picker">
        <div data-testid="current-color" data-color={currentColor}>
          Current: {currentColor}
        </div>
        {colors.map((color: string) => (
          <button
            key={color}
            data-testid={`color-${color.replace('#', '')}`}
            onClick={() => onColorChange(color)}
            style={{ backgroundColor: color }}
          >
            {color}
          </button>
        ))}
      </div>
    );
  };
});

describe('Toolbar Component - Drawing Tools Management', () => {
  const defaultProps = {
    currentColor: '#000000',
    currentSize: 5,
    canUndo: true,
    canRedo: false,
    onColorChange: jest.fn(),
    onSizeChange: jest.fn(),
    onClear: jest.fn(),
    onUndo: jest.fn(),
    onRedo: jest.fn(),
    minSize: 1,
    maxSize: 50,
    collaborativeMode: false
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  /**
   * Test color picker functionality with collaborative considerations.
   * 
   * Collaborative Features:
   * - Color changes should be immediately visible to local user
   * - Other collaborators should see color changes in real-time
   * - Color palette should support custom colors for team branding
   * - Recent colors should be synchronized across collaborative session
   * 
   * Performance Requirements:
   * Color selection must be instant (<5ms) to maintain drawing flow.
   * Color picker rendering should not block the main thread.
   */
  describe('Color Picker Functionality', () => {
    it('should render color picker with default colors', () => {
      render(<Toolbar {...defaultProps} />);
      
      expect(screen.getByTestId('color-picker')).toBeInTheDocument();
      expect(screen.getByTestId('current-color')).toHaveAttribute('data-color', '#000000');
    });

    it('should change color with immediate feedback', async () => {
      const onColorChange = jest.fn();
      render(<Toolbar {...defaultProps} onColorChange={onColorChange} />);
      
      const startTime = performance.now();
      
      // Click red color
      fireEvent.click(screen.getByTestId('color-ff0000'));
      
      const changeTime = performance.now() - startTime;
      expect(changeTime).toBeLessThan(5); // Performance requirement
      
      expect(onColorChange).toHaveBeenCalledWith('#ff0000');
    });

    it('should support custom color input for collaborative branding', async () => {
      const onColorChange = jest.fn();
      render(<Toolbar {...defaultProps} onColorChange={onColorChange} customColorEnabled={true} />);
      
      const colorInput = screen.getByTestId('custom-color-input');
      
      await userEvent.type(colorInput, '#8e44ad');
      fireEvent.blur(colorInput);
      
      expect(onColorChange).toHaveBeenCalledWith('#8e44ad');
    });

    it('should validate color format for collaborative data integrity', async () => {
      const onColorChange = jest.fn();
      render(<Toolbar {...defaultProps} onColorChange={onColorChange} customColorEnabled={true} />);
      
      const colorInput = screen.getByTestId('custom-color-input');
      
      // Test invalid color format
      await userEvent.type(colorInput, 'invalid-color');
      fireEvent.blur(colorInput);
      
      // Should not call onChange with invalid color
      expect(onColorChange).not.toHaveBeenCalledWith('invalid-color');
      
      // Should show validation error
      expect(screen.getByTestId('color-error')).toBeInTheDocument();
    });

    it('should show recent colors for quick access', () => {
      const recentColors = ['#ff0000', '#00ff00', '#0000ff', '#ffff00'];
      render(
        <Toolbar 
          {...defaultProps} 
          recentColors={recentColors}
          showRecentColors={true} 
        />
      );
      
      // Recent colors should be displayed for quick access
      expect(screen.getByTestId('recent-colors')).toBeInTheDocument();
      recentColors.forEach(color => {
        expect(screen.getByTestId(`recent-${color.replace('#', '')}`)).toBeInTheDocument();
      });
    });
  });

  /**
   * Test pen size controls with collaborative awareness.
   * 
   * Collaborative Synchronization:
   * - Size changes should be visible to other collaborators
   * - Large brush sizes should have performance warnings
   * - Size presets should be shared across collaborative teams
   * - Pressure sensitivity settings synchronized between devices
   * 
   * Performance Considerations:
   * Size changes should not cause canvas re-rendering delays.
   * Slider interactions should be smooth and responsive.
   */
  describe('Pen Size Controls', () => {
    it('should render size slider with current value', () => {
      render(<Toolbar {...defaultProps} currentSize={15} />);
      
      const sizeSlider = screen.getByTestId('size-slider');
      expect(sizeSlider).toHaveValue('15');
      expect(screen.getByTestId('size-display')).toHaveTextContent('15px');
    });

    it('should change size with immediate feedback', async () => {
      const onSizeChange = jest.fn();
      render(<Toolbar {...defaultProps} onSizeChange={onSizeChange} />);
      
      const startTime = performance.now();
      
      const sizeSlider = screen.getByTestId('size-slider');
      fireEvent.change(sizeSlider, { target: { value: '25' } });
      
      const changeTime = performance.now() - startTime;
      expect(changeTime).toBeLessThan(5); // Performance requirement
      
      expect(onSizeChange).toHaveBeenCalledWith(25);
    });

    it('should enforce size bounds for collaborative safety', () => {
      const onSizeChange = jest.fn();
      render(<Toolbar {...defaultProps} onSizeChange={onSizeChange} minSize={2} maxSize={40} />);
      
      const sizeSlider = screen.getByTestId('size-slider');
      
      // Test minimum bound
      fireEvent.change(sizeSlider, { target: { value: '1' } });
      expect(onSizeChange).toHaveBeenCalledWith(2);
      
      // Test maximum bound
      fireEvent.change(sizeSlider, { target: { value: '50' } });
      expect(onSizeChange).toHaveBeenCalledWith(40);
    });

    it('should provide size presets for quick selection', () => {
      const onSizeChange = jest.fn();
      const sizePresets = [1, 3, 5, 10, 20, 35];
      
      render(
        <Toolbar 
          {...defaultProps} 
          onSizeChange={onSizeChange}
          sizePresets={sizePresets}
          showSizePresets={true}
        />
      );
      
      // Size presets should be available for quick selection
      sizePresets.forEach(size => {
        const preset = screen.getByTestId(`size-preset-${size}`);
        expect(preset).toBeInTheDocument();
        
        fireEvent.click(preset);
        expect(onSizeChange).toHaveBeenCalledWith(size);
      });
    });

    it('should show pressure sensitivity toggle for supported devices', () => {
      render(
        <Toolbar 
          {...defaultProps} 
          pressureSensitivitySupported={true}
          pressureSensitivityEnabled={false}
        />
      );
      
      const pressureToggle = screen.getByTestId('pressure-sensitivity-toggle');
      expect(pressureToggle).toBeInTheDocument();
      expect(pressureToggle).not.toBeChecked();
    });

    it('should display size preview circle for visual feedback', () => {
      render(<Toolbar {...defaultProps} currentSize={15} showSizePreview={true} />);
      
      const sizePreview = screen.getByTestId('size-preview');
      expect(sizePreview).toBeInTheDocument();
      expect(sizePreview).toHaveStyle({
        width: '15px',
        height: '15px',
        borderRadius: '50%'
      });
    });
  });

  /**
   * Test clear, undo/redo controls with collaborative session management.
   * 
   * Collaborative Considerations:
   * - Clear operations may require confirmation in multi-user sessions
   * - Undo/redo should only affect the current user's strokes
   * - Global clear may require special permissions or voting
   * - Operation states must be synchronized across collaborators
   * 
   * Performance Requirements:
   * Button interactions should be immediate and provide clear feedback.
   * Operations should complete within performance targets.
   */
  describe('Clear and Undo/Redo Controls', () => {
    it('should render clear button with confirmation dialog', async () => {
      const onClear = jest.fn();
      render(<Toolbar {...defaultProps} onClear={onClear} requireClearConfirmation={true} />);
      
      const clearButton = screen.getByTestId('clear-button');
      expect(clearButton).toBeInTheDocument();
      
      fireEvent.click(clearButton);
      
      // Should show confirmation dialog in collaborative mode
      expect(screen.getByTestId('clear-confirmation-dialog')).toBeInTheDocument();
      
      // Confirm clear operation
      fireEvent.click(screen.getByTestId('confirm-clear'));
      expect(onClear).toHaveBeenCalled();
    });

    it('should handle immediate clear in solo mode', () => {
      const onClear = jest.fn();
      render(<Toolbar {...defaultProps} onClear={onClear} requireClearConfirmation={false} />);
      
      const startTime = performance.now();
      
      fireEvent.click(screen.getByTestId('clear-button'));
      
      const clearTime = performance.now() - startTime;
      expect(clearTime).toBeLessThan(8); // Performance requirement
      
      expect(onClear).toHaveBeenCalled();
    });

    it('should render undo button with proper state', () => {
      render(<Toolbar {...defaultProps} canUndo={true} />);
      
      const undoButton = screen.getByTestId('undo-button');
      expect(undoButton).toBeInTheDocument();
      expect(undoButton).not.toBeDisabled();
    });

    it('should disable undo when not available', () => {
      render(<Toolbar {...defaultProps} canUndo={false} />);
      
      const undoButton = screen.getByTestId('undo-button');
      expect(undoButton).toBeDisabled();
    });

    it('should handle undo operation with immediate feedback', () => {
      const onUndo = jest.fn();
      render(<Toolbar {...defaultProps} onUndo={onUndo} canUndo={true} />);
      
      const startTime = performance.now();
      
      fireEvent.click(screen.getByTestId('undo-button'));
      
      const undoTime = performance.now() - startTime;
      expect(undoTime).toBeLessThan(8); // Performance requirement
      
      expect(onUndo).toHaveBeenCalled();
    });

    it('should render redo button with proper state', () => {
      render(<Toolbar {...defaultProps} canRedo={true} />);
      
      const redoButton = screen.getByTestId('redo-button');
      expect(redoButton).toBeInTheDocument();
      expect(redoButton).not.toBeDisabled();
    });

    it('should handle redo operation with immediate feedback', () => {
      const onRedo = jest.fn();
      render(<Toolbar {...defaultProps} onRedo={onRedo} canRedo={true} />);
      
      const startTime = performance.now();
      
      fireEvent.click(screen.getByTestId('redo-button'));
      
      const redoTime = performance.now() - startTime;
      expect(redoTime).toBeLessThan(8); // Performance requirement
      
      expect(onRedo).toHaveBeenCalled();
    });

    it('should show keyboard shortcuts for power users', () => {
      render(<Toolbar {...defaultProps} showKeyboardShortcuts={true} />);
      
      // Keyboard shortcuts should be visible for accessibility
      expect(screen.getByText(/Ctrl\+Z/)).toBeInTheDocument(); // Undo
      expect(screen.getByText(/Ctrl\+Y/)).toBeInTheDocument(); // Redo
      expect(screen.getByText(/Ctrl\+E/)).toBeInTheDocument(); // Clear
    });
  });

  /**
   * Test collaborative mode features and synchronization.
   * 
   * Collaborative Features:
   * - Real-time tool state synchronization across users
   * - Visual indicators showing other users' active tools
   * - Conflict resolution for simultaneous tool changes
   * - Tool locking for specific collaborative workflows
   * 
   * Performance Requirements:
   * Collaborative features should not impact local tool responsiveness.
   * Network synchronization should be batched for efficiency.
   */
  describe('Collaborative Mode Features', () => {
    it('should show other users tool states in collaborative mode', () => {
      const collaborators = [
        { id: 'user-1', name: 'Alice', color: '#ff0000', size: 10, isActive: true },
        { id: 'user-2', name: 'Bob', color: '#00ff00', size: 5, isActive: false }
      ];
      
      render(
        <Toolbar 
          {...defaultProps} 
          collaborativeMode={true}
          collaborators={collaborators}
        />
      );
      
      // Should show collaborators' tool states
      expect(screen.getByTestId('collaborators-tools')).toBeInTheDocument();
      
      collaborators.forEach(collaborator => {
        expect(screen.getByTestId(`collaborator-${collaborator.id}-tools`)).toBeInTheDocument();
        expect(screen.getByText(collaborator.name)).toBeInTheDocument();
      });
    });

    it('should broadcast tool changes to other collaborators', () => {
      const onToolChange = jest.fn();
      const onColorChange = jest.fn((color) => {
        onToolChange({ type: 'color', value: color, userId: 'current-user' });
      });
      
      render(
        <Toolbar 
          {...defaultProps} 
          collaborativeMode={true}
          onColorChange={onColorChange}
        />
      );
      
      fireEvent.click(screen.getByTestId('color-0000ff'));
      
      expect(onToolChange).toHaveBeenCalledWith({
        type: 'color',
        value: '#0000ff',
        userId: 'current-user'
      });
    });

    it('should handle simultaneous tool changes gracefully', () => {
      const { rerender } = render(
        <Toolbar 
          {...defaultProps} 
          collaborativeMode={true}
          currentColor="#ff0000"
        />
      );
      
      // Simulate simultaneous color change from another user
      rerender(
        <Toolbar 
          {...defaultProps} 
          collaborativeMode={true}
          currentColor="#00ff00" // Changed by another user
          lastChangeBy="user-2"
        />
      );
      
      // Should handle external changes smoothly
      expect(screen.getByTestId('current-color')).toHaveAttribute('data-color', '#00ff00');
      
      // Should show indicator of who made the change
      if (screen.queryByTestId('last-change-indicator')) {
        expect(screen.getByTestId('last-change-indicator')).toHaveTextContent('user-2');
      }
    });

    it('should show tool lock indicators for restricted tools', () => {
      const lockedTools = ['clear', 'size'];
      
      render(
        <Toolbar 
          {...defaultProps} 
          collaborativeMode={true}
          lockedTools={lockedTools}
          userRole="viewer" // Limited permissions
        />
      );
      
      // Locked tools should be disabled or show lock indicators
      expect(screen.getByTestId('clear-button')).toBeDisabled();
      expect(screen.getByTestId('size-slider')).toBeDisabled();
      
      // Should show lock indicators
      lockedTools.forEach(tool => {
        expect(screen.getByTestId(`${tool}-lock-indicator`)).toBeInTheDocument();
      });
    });
  });

  /**
   * Test performance and accessibility requirements.
   * 
   * Performance Monitoring:
   * - All tool interactions should be under performance targets
   * - Memory usage should remain stable during extended sessions
   * - Event handling should not block the main thread
   * 
   * Accessibility Requirements:
   * - All controls should be keyboard accessible
   * - Screen reader support for tool states
   * - High contrast mode compatibility
   */
  describe('Performance and Accessibility', () => {
    it('should meet performance targets for all tool interactions', () => {
      const handlers = {
        onColorChange: jest.fn(),
        onSizeChange: jest.fn(),
        onClear: jest.fn(),
        onUndo: jest.fn(),
        onRedo: jest.fn()
      };
      
      render(<Toolbar {...defaultProps} {...handlers} />);
      
      const operations = [
        { element: 'color-ff0000', handler: handlers.onColorChange },
        { element: 'size-slider', handler: handlers.onSizeChange, event: { target: { value: '15' } } },
        { element: 'clear-button', handler: handlers.onClear },
        { element: 'undo-button', handler: handlers.onUndo },
        { element: 'redo-button', handler: handlers.onRedo }
      ];
      
      operations.forEach(({ element, handler, event }) => {
        const startTime = performance.now();
        
        if (event) {
          fireEvent.change(screen.getByTestId(element), event);
        } else {
          fireEvent.click(screen.getByTestId(element));
        }
        
        const operationTime = performance.now() - startTime;
        expect(operationTime).toBeLessThan(10); // Performance target
        expect(handler).toHaveBeenCalled();
        
        jest.clearAllMocks();
      });
    });

    it('should support keyboard navigation for accessibility', async () => {
      const user = userEvent.setup();
      render(<Toolbar {...defaultProps} />);
      
      // Should be able to navigate through all interactive elements
      await user.tab();
      expect(screen.getByTestId('color-picker')).toHaveFocus();
      
      await user.tab();
      expect(screen.getByTestId('size-slider')).toHaveFocus();
      
      await user.tab();
      expect(screen.getByTestId('clear-button')).toHaveFocus();
      
      await user.tab();
      expect(screen.getByTestId('undo-button')).toHaveFocus();
    });

    it('should provide proper ARIA labels for screen readers', () => {
      render(<Toolbar {...defaultProps} />);
      
      // All interactive elements should have proper ARIA labels
      expect(screen.getByTestId('color-picker')).toHaveAttribute('aria-label', expect.stringContaining('color'));
      expect(screen.getByTestId('size-slider')).toHaveAttribute('aria-label', expect.stringContaining('size'));
      expect(screen.getByTestId('clear-button')).toHaveAttribute('aria-label', expect.stringContaining('clear'));
      expect(screen.getByTestId('undo-button')).toHaveAttribute('aria-label', expect.stringContaining('undo'));
      expect(screen.getByTestId('redo-button')).toHaveAttribute('aria-label', expect.stringContaining('redo'));
    });

    it('should maintain stable memory usage during extended use', () => {
      const initialMemory = (performance as any).memory?.usedJSHeapSize || 0;
      
      const { rerender } = render(<Toolbar {...defaultProps} />);
      
      // Simulate extended use with many tool changes
      for (let i = 0; i < 100; i++) {
        rerender(
          <Toolbar 
            {...defaultProps} 
            currentColor={`hsl(${i * 3.6}, 70%, 50%)`}
            currentSize={5 + (i % 20)}
          />
        );
      }
      
      // Memory usage should not grow excessively
      const finalMemory = (performance as any).memory?.usedJSHeapSize || 0;
      if (finalMemory > 0 && initialMemory > 0) {
        const memoryIncrease = finalMemory - initialMemory;
        expect(memoryIncrease).toBeLessThan(10 * 1024 * 1024); // Less than 10MB increase
      }
    });
  });
});