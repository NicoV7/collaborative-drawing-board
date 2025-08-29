/**
 * Canvas Drawing Core Tests - Phase 4 TDD Implementation
 * 
 * This test suite covers the collaborative drawing canvas functionality including:
 * - Konva.js canvas rendering and initialization
 * - Smooth stroke capture with requestAnimationFrame optimization
 * - Drawing tools (pen size, color picker, clear, undo/redo)
 * - Touch event handling for mobile collaboration
 * - Performance benchmarks for 60fps drawing experience
 * 
 * Architecture Context:
 * The DrawingCanvas component is the heart of the collaborative drawing system.
 * It handles real-time drawing input, stroke optimization, and provides the
 * foundation for WebSocket-based collaborative synchronization. Every drawing
 * interaction captured here will eventually be encrypted and broadcast to
 * other collaborators in real-time.
 * 
 * Performance Requirements:
 * - Canvas initialization: <100ms for immediate user feedback
 * - Stroke rendering: <16ms (60fps) for smooth drawing experience
 * - Drawing tool changes: <10ms for responsive UI interactions
 * - Undo/redo operations: <20ms for fluid workflow
 * - Touch events: <16ms for mobile collaboration support
 * 
 * Collaborative Integration Points:
 * - Stroke data structures designed for WebSocket transmission
 * - Drawing operations optimized for real-time synchronization
 * - Canvas state management for multi-user collaboration
 * - Performance monitoring for collaborative scenarios
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { act } from 'react-dom/test-utils';
import '@testing-library/jest-dom';
import DrawingCanvas from './DrawingCanvas';

// Mock Konva for testing environment
jest.mock('react-konva', () => ({
  Stage: ({ children, ...props }: any) => (
    <div data-testid="konva-stage" {...props}>
      {children}
    </div>
  ),
  Layer: ({ children, ...props }: any) => (
    <div data-testid="konva-layer" {...props}>
      {children}
    </div>
  ),
  Line: (props: any) => (
    <div data-testid="konva-line" data-stroke={props.stroke} data-strokewidth={props.strokeWidth}>
      Line: {JSON.stringify(props.points)}
    </div>
  )
}));

// Mock requestAnimationFrame for performance testing
let mockRafCallbacks: (() => void)[] = [];
const mockRequestAnimationFrame = jest.fn((callback: () => void) => {
  mockRafCallbacks.push(callback);
  return mockRafCallbacks.length;
});

beforeEach(() => {
  mockRafCallbacks = [];
  global.requestAnimationFrame = mockRequestAnimationFrame;
  jest.clearAllMocks();
});

describe('DrawingCanvas Component - Core Functionality', () => {
  /**
   * Test canvas initialization and rendering performance.
   * 
   * Architecture Notes:
   * The canvas must initialize quickly to provide immediate feedback when
   * users join collaborative drawing sessions. Slow initialization breaks
   * the real-time collaborative flow and degrades user experience.
   * 
   * Performance Considerations:
   * - Konva.js Stage creation should be optimized for large canvas sizes
   * - Initial render should not block the main thread
   * - Canvas should be responsive immediately after mounting
   */
  describe('Canvas Initialization', () => {
    it('should render canvas with proper dimensions', async () => {
      const startTime = performance.now();
      
      render(
        <DrawingCanvas
          width={800}
          height={600}
          onStrokeStart={jest.fn()}
          onStrokeUpdate={jest.fn()}
          onStrokeEnd={jest.fn()}
        />
      );
      
      // Verify canvas elements are rendered
      expect(screen.getByTestId('konva-stage')).toBeInTheDocument();
      expect(screen.getByTestId('konva-layer')).toBeInTheDocument();
      
      // Performance requirement: <100ms initialization
      const initTime = performance.now() - startTime;
      expect(initTime).toBeLessThan(100);
    });

    it('should initialize with default drawing state', () => {
      render(
        <DrawingCanvas
          width={800}
          height={600}
          onStrokeStart={jest.fn()}
          onStrokeUpdate={jest.fn()}
          onStrokeEnd={jest.fn()}
        />
      );

      // Canvas should be ready for drawing immediately
      const stage = screen.getByTestId('konva-stage');
      expect(stage).toHaveAttribute('width', '800');
      expect(stage).toHaveAttribute('height', '600');
    });

    it('should handle canvas resize without performance degradation', async () => {
      const { rerender } = render(
        <DrawingCanvas
          width={800}
          height={600}
          onStrokeStart={jest.fn()}
          onStrokeUpdate={jest.fn()}
          onStrokeEnd={jest.fn()}
        />
      );

      const startTime = performance.now();

      // Simulate canvas resize (common in responsive collaborative UI)
      rerender(
        <DrawingCanvas
          width={1200}
          height={800}
          onStrokeStart={jest.fn()}
          onStrokeUpdate={jest.fn()}
          onStrokeEnd={jest.fn()}
        />
      );

      // Resize should be fast for responsive collaborative experience
      const resizeTime = performance.now() - startTime;
      expect(resizeTime).toBeLessThan(50);

      const stage = screen.getByTestId('konva-stage');
      expect(stage).toHaveAttribute('width', '1200');
      expect(stage).toHaveAttribute('height', '800');
    });
  });

  /**
   * Test stroke capture mechanics with requestAnimationFrame optimization.
   * 
   * Collaborative Architecture:
   * Stroke capture is the foundation of real-time collaborative drawing.
   * Each captured stroke will be encrypted and broadcast to other users,
   * so the capture mechanism must be both performant and accurate.
   * 
   * Performance Strategy:
   * - Use requestAnimationFrame to batch stroke updates for 60fps
   * - Minimize memory allocations during active drawing
   * - Optimize point capture for smooth curves at high drawing speeds
   */
  describe('Stroke Capture and Rendering', () => {
    it('should capture stroke start with proper event handling', () => {
      const onStrokeStart = jest.fn();
      const onStrokeUpdate = jest.fn();
      const onStrokeEnd = jest.fn();

      render(
        <DrawingCanvas
          width={800}
          height={600}
          onStrokeStart={onStrokeStart}
          onStrokeUpdate={onStrokeUpdate}
          onStrokeEnd={onStrokeEnd}
        />
      );

      const stage = screen.getByTestId('konva-stage');

      // Simulate mouse down event to start drawing
      fireEvent.mouseDown(stage, {
        clientX: 100,
        clientY: 150,
        button: 0
      });

      // Stroke capture should begin immediately
      expect(onStrokeStart).toHaveBeenCalledWith({
        x: 100,
        y: 150,
        timestamp: expect.any(Number),
        pressure: expect.any(Number)
      });
    });

    it('should capture stroke updates with requestAnimationFrame optimization', async () => {
      const onStrokeUpdate = jest.fn();

      render(
        <DrawingCanvas
          width={800}
          height={600}
          onStrokeStart={jest.fn()}
          onStrokeUpdate={onStrokeUpdate}
          onStrokeEnd={jest.fn()}
          optimizeFor60FPS={true}
        />
      );

      const stage = screen.getByTestId('konva-stage');

      // Start drawing stroke
      fireEvent.mouseDown(stage, { clientX: 100, clientY: 150 });

      // Simulate rapid mouse movement (high-speed drawing)
      for (let i = 0; i < 10; i++) {
        fireEvent.mouseMove(stage, {
          clientX: 100 + i * 10,
          clientY: 150 + i * 5
        });
      }

      // Updates should be batched via requestAnimationFrame
      expect(mockRequestAnimationFrame).toHaveBeenCalled();

      // Process RAF callbacks
      act(() => {
        mockRafCallbacks.forEach(callback => callback());
      });

      // Verify stroke updates are captured efficiently
      expect(onStrokeUpdate).toHaveBeenCalledWith({
        points: expect.arrayContaining([100, 150]),
        timestamp: expect.any(Number),
        pressure: expect.any(Number)
      });
    });

    it('should complete stroke capture with proper timing', () => {
      const onStrokeEnd = jest.fn();

      render(
        <DrawingCanvas
          width={800}
          height={600}
          onStrokeStart={jest.fn()}
          onStrokeUpdate={jest.fn()}
          onStrokeEnd={onStrokeEnd}
        />
      );

      const stage = screen.getByTestId('konva-stage');
      const startTime = performance.now();

      // Complete drawing stroke
      fireEvent.mouseDown(stage, { clientX: 100, clientY: 150 });
      fireEvent.mouseMove(stage, { clientX: 120, clientY: 170 });
      fireEvent.mouseUp(stage);

      // Stroke completion should be immediate for responsive feedback
      const completionTime = performance.now() - startTime;
      expect(completionTime).toBeLessThan(20);

      expect(onStrokeEnd).toHaveBeenCalledWith({
        finalPoints: expect.any(Array),
        duration: expect.any(Number),
        totalDistance: expect.any(Number)
      });
    });

    it('should render strokes with 60fps performance target', () => {
      render(
        <DrawingCanvas
          width={800}
          height={600}
          onStrokeStart={jest.fn()}
          onStrokeUpdate={jest.fn()}
          onStrokeEnd={jest.fn()}
          strokes={[
            {
              id: '1',
              points: [100, 150, 120, 170, 140, 190],
              color: '#000000',
              size: 5,
              timestamp: Date.now()
            }
          ]}
        />
      );

      const startTime = performance.now();

      // Stroke rendering should meet 60fps requirement (16.67ms per frame)
      const lines = screen.getAllByTestId('konva-line');
      expect(lines).toHaveLength(1);

      const renderTime = performance.now() - startTime;
      expect(renderTime).toBeLessThan(16); // 60fps requirement

      // Verify stroke properties
      expect(lines[0]).toHaveAttribute('data-stroke', '#000000');
      expect(lines[0]).toHaveAttribute('data-strokewidth', '5');
    });
  });

  /**
   * Test drawing tools functionality with collaborative considerations.
   * 
   * Collaborative Features:
   * Drawing tools settings (color, size) need to be synchronized across
   * collaborators so everyone knows what tools others are using.
   * Changes should be immediate and reflected in real-time drawing.
   * 
   * Performance Requirements:
   * Tool changes must be instant (<10ms) to maintain drawing flow.
   * Color and size changes should not interrupt active drawing strokes.
   */
  describe('Drawing Tools', () => {
    it('should change pen color with immediate effect', () => {
      const onColorChange = jest.fn();

      render(
        <DrawingCanvas
          width={800}
          height={600}
          onStrokeStart={jest.fn()}
          onStrokeUpdate={jest.fn()}
          onStrokeEnd={jest.fn()}
          currentColor="#ff0000"
          onColorChange={onColorChange}
        />
      );

      const startTime = performance.now();

      // Color changes should be immediate for responsive drawing
      fireEvent.click(screen.getByTestId('color-picker-blue'));

      const changeTime = performance.now() - startTime;
      expect(changeTime).toBeLessThan(10); // Performance target

      expect(onColorChange).toHaveBeenCalledWith('#0000ff');
    });

    it('should adjust pen size with range validation', () => {
      const onSizeChange = jest.fn();

      render(
        <DrawingCanvas
          width={800}
          height={600}
          onStrokeStart={jest.fn()}
          onStrokeUpdate={jest.fn()}
          onStrokeEnd={jest.fn()}
          currentSize={5}
          onSizeChange={onSizeChange}
          minSize={1}
          maxSize={50}
        />
      );

      const startTime = performance.now();

      // Size changes should be immediate and validated
      fireEvent.change(screen.getByTestId('size-slider'), {
        target: { value: '25' }
      });

      const changeTime = performance.now() - startTime;
      expect(changeTime).toBeLessThan(10); // Performance target

      expect(onSizeChange).toHaveBeenCalledWith(25);
    });

    it('should validate pen size bounds for collaborative safety', () => {
      const onSizeChange = jest.fn();

      render(
        <DrawingCanvas
          width={800}
          height={600}
          onStrokeStart={jest.fn()}
          onStrokeUpdate={jest.fn()}
          onStrokeEnd={jest.fn()}
          currentSize={5}
          onSizeChange={onSizeChange}
          minSize={1}
          maxSize={50}
        />
      );

      // Test invalid size values (important for collaborative data integrity)
      fireEvent.change(screen.getByTestId('size-slider'), {
        target: { value: '100' } // Above maximum
      });

      // Should clamp to maximum value
      expect(onSizeChange).toHaveBeenCalledWith(50);

      fireEvent.change(screen.getByTestId('size-slider'), {
        target: { value: '0' } // Below minimum
      });

      // Should clamp to minimum value
      expect(onSizeChange).toHaveBeenCalledWith(1);
    });
  });

  /**
   * Test clear, undo/redo functionality for collaborative drawing.
   * 
   * Collaborative Complexity:
   * Undo/redo in collaborative environments requires careful coordination.
   * Individual users should be able to undo their own strokes while
   * preserving other collaborators' work. Clear operations may need
   * special permissions or confirmation in collaborative sessions.
   * 
   * Performance Targets:
   * Undo/redo should be near-instant (<20ms) to maintain drawing flow.
   * Clear operations should handle large canvases efficiently.
   */
  describe('Clear and Undo/Redo Operations', () => {
    it('should clear canvas with performance optimization', () => {
      const onClear = jest.fn();

      render(
        <DrawingCanvas
          width={800}
          height={600}
          onStrokeStart={jest.fn()}
          onStrokeUpdate={jest.fn()}
          onStrokeEnd={jest.fn()}
          onClear={onClear}
          strokes={[
            { id: '1', points: [100, 150, 120, 170], color: '#000000', size: 5, timestamp: Date.now() },
            { id: '2', points: [200, 250, 220, 270], color: '#ff0000', size: 8, timestamp: Date.now() }
          ]}
        />
      );

      const startTime = performance.now();

      // Clear should be immediate even with many strokes
      fireEvent.click(screen.getByTestId('clear-button'));

      const clearTime = performance.now() - startTime;
      expect(clearTime).toBeLessThan(50); // Performance target for large canvases

      expect(onClear).toHaveBeenCalled();
    });

    it('should handle undo operation with proper stroke management', () => {
      const onUndo = jest.fn();
      const mockStrokes = [
        { id: '1', points: [100, 150, 120, 170], color: '#000000', size: 5, timestamp: Date.now() - 2000 },
        { id: '2', points: [200, 250, 220, 270], color: '#ff0000', size: 8, timestamp: Date.now() - 1000 },
        { id: '3', points: [300, 350, 320, 370], color: '#0000ff', size: 3, timestamp: Date.now() }
      ];

      render(
        <DrawingCanvas
          width={800}
          height={600}
          onStrokeStart={jest.fn()}
          onStrokeUpdate={jest.fn()}
          onStrokeEnd={jest.fn()}
          onUndo={onUndo}
          strokes={mockStrokes}
          canUndo={true}
        />
      );

      const startTime = performance.now();

      // Undo should be immediate for responsive drawing workflow
      fireEvent.click(screen.getByTestId('undo-button'));

      const undoTime = performance.now() - startTime;
      expect(undoTime).toBeLessThan(20); // Performance target

      // Should undo the most recent stroke (collaborative consideration)
      expect(onUndo).toHaveBeenCalledWith('3');
    });

    it('should handle redo operation with stroke history', () => {
      const onRedo = jest.fn();

      render(
        <DrawingCanvas
          width={800}
          height={600}
          onStrokeStart={jest.fn()}
          onStrokeUpdate={jest.fn()}
          onStrokeEnd={jest.fn()}
          onRedo={onRedo}
          canRedo={true}
        />
      );

      const startTime = performance.now();

      // Redo should restore strokes efficiently
      fireEvent.click(screen.getByTestId('redo-button'));

      const redoTime = performance.now() - startTime;
      expect(redoTime).toBeLessThan(20); // Performance target

      expect(onRedo).toHaveBeenCalled();
    });

    it('should disable undo/redo buttons when not available', () => {
      render(
        <DrawingCanvas
          width={800}
          height={600}
          onStrokeStart={jest.fn()}
          onStrokeUpdate={jest.fn()}
          onStrokeEnd={jest.fn()}
          onUndo={jest.fn()}
          onRedo={jest.fn()}
          canUndo={false}
          canRedo={false}
        />
      );

      // Buttons should be disabled to prevent invalid operations
      expect(screen.getByTestId('undo-button')).toBeDisabled();
      expect(screen.getByTestId('redo-button')).toBeDisabled();
    });
  });

  /**
   * Test touch event handling for mobile collaborative drawing.
   * 
   * Mobile Collaboration Requirements:
   * Touch drawing must be as responsive as mouse drawing to support
   * mobile collaborators in the same session. Touch events have different
   * timing characteristics and require special handling.
   * 
   * Performance Considerations:
   * Touch events can fire more frequently than mouse events and need
   * efficient batching to maintain 60fps on mobile devices.
   */
  describe('Touch Event Handling', () => {
    it('should handle touch start for mobile drawing', () => {
      const onStrokeStart = jest.fn();

      render(
        <DrawingCanvas
          width={800}
          height={600}
          onStrokeStart={onStrokeStart}
          onStrokeUpdate={jest.fn()}
          onStrokeEnd={jest.fn()}
          touchEnabled={true}
        />
      );

      const stage = screen.getByTestId('konva-stage');

      // Simulate touch start event
      fireEvent.touchStart(stage, {
        touches: [{ clientX: 100, clientY: 150 }]
      });

      expect(onStrokeStart).toHaveBeenCalledWith({
        x: 100,
        y: 150,
        timestamp: expect.any(Number),
        pressure: expect.any(Number),
        inputType: 'touch'
      });
    });

    it('should handle touch move with pressure sensitivity', () => {
      const onStrokeUpdate = jest.fn();

      render(
        <DrawingCanvas
          width={800}
          height={600}
          onStrokeStart={jest.fn()}
          onStrokeUpdate={onStrokeUpdate}
          onStrokeEnd={jest.fn()}
          touchEnabled={true}
          pressureSensitive={true}
        />
      );

      const stage = screen.getByTestId('konva-stage');

      // Start touch drawing
      fireEvent.touchStart(stage, {
        touches: [{ clientX: 100, clientY: 150 }]
      });

      const startTime = performance.now();

      // Simulate touch movement with pressure
      fireEvent.touchMove(stage, {
        touches: [{ clientX: 120, clientY: 170, force: 0.8 }]
      });

      // Touch handling should meet mobile performance requirements
      const touchTime = performance.now() - startTime;
      expect(touchTime).toBeLessThan(16); // 60fps on mobile

      expect(onStrokeUpdate).toHaveBeenCalledWith({
        points: expect.arrayContaining([100, 150, 120, 170]),
        pressure: 0.8,
        timestamp: expect.any(Number)
      });
    });

    it('should prevent scrolling during drawing on touch devices', () => {
      render(
        <DrawingCanvas
          width={800}
          height={600}
          onStrokeStart={jest.fn()}
          onStrokeUpdate={jest.fn()}
          onStrokeEnd={jest.fn()}
          touchEnabled={true}
          preventScrolling={true}
        />
      );

      const stage = screen.getByTestId('konva-stage');

      // Touch events during drawing should prevent default scrolling
      const touchStartEvent = fireEvent.touchStart(stage, {
        touches: [{ clientX: 100, clientY: 150 }]
      });

      expect(touchStartEvent.defaultPrevented).toBe(true);
    });
  });

  /**
   * Test performance benchmarks for collaborative drawing requirements.
   * 
   * Performance Monitoring:
   * Collaborative drawing requires consistent performance across all
   * participants. Performance degradation in one client can affect
   * the entire collaborative session through network delays.
   * 
   * Benchmarking Strategy:
   * - Measure key operations under realistic load conditions
   * - Test performance with multiple simultaneous strokes
   * - Validate memory usage during extended drawing sessions
   */
  describe('Performance Benchmarks', () => {
    it('should maintain 60fps with multiple simultaneous strokes', async () => {
      const strokes = Array.from({ length: 100 }, (_, i) => ({
        id: `stroke-${i}`,
        points: Array.from({ length: 20 }, (_, j) => [i * 10 + j, i * 5 + j]).flat(),
        color: `hsl(${i * 3.6}, 70%, 50%)`,
        size: 5,
        timestamp: Date.now() - i * 100
      }));

      const startTime = performance.now();

      render(
        <DrawingCanvas
          width={1920}
          height={1080}
          onStrokeStart={jest.fn()}
          onStrokeUpdate={jest.fn()}
          onStrokeEnd={jest.fn()}
          strokes={strokes}
        />
      );

      // Large number of strokes should still render within 60fps budget
      const renderTime = performance.now() - startTime;
      expect(renderTime).toBeLessThan(16 * 5); // Allow 5 frames for complex scene

      // Verify all strokes are rendered
      const lines = screen.getAllByTestId('konva-line');
      expect(lines).toHaveLength(100);
    });

    it('should handle rapid drawing input without dropping frames', () => {
      const onStrokeUpdate = jest.fn();

      render(
        <DrawingCanvas
          width={800}
          height={600}
          onStrokeStart={jest.fn()}
          onStrokeUpdate={onStrokeUpdate}
          onStrokeEnd={jest.fn()}
          optimizeFor60FPS={true}
        />
      );

      const stage = screen.getByTestId('konva-stage');
      fireEvent.mouseDown(stage, { clientX: 100, clientY: 150 });

      const startTime = performance.now();

      // Simulate very rapid drawing input (stress test)
      for (let i = 0; i < 50; i++) {
        fireEvent.mouseMove(stage, {
          clientX: 100 + i * 2,
          clientY: 150 + Math.sin(i * 0.1) * 20
        });
      }

      // Process all RAF callbacks
      act(() => {
        mockRafCallbacks.forEach(callback => callback());
      });

      const processingTime = performance.now() - startTime;
      
      // Should handle rapid input efficiently
      expect(processingTime).toBeLessThan(100);
      expect(mockRequestAnimationFrame).toHaveBeenCalled();
    });

    it('should optimize memory usage during extended drawing sessions', () => {
      const initialMemory = (performance as any).memory?.usedJSHeapSize || 0;

      const { rerender } = render(
        <DrawingCanvas
          width={800}
          height={600}
          onStrokeStart={jest.fn()}
          onStrokeUpdate={jest.fn()}
          onStrokeEnd={jest.fn()}
          strokes={[]}
        />
      );

      // Simulate extended drawing session with many strokes
      for (let session = 0; session < 10; session++) {
        const sessionStrokes = Array.from({ length: 50 }, (_, i) => ({
          id: `session-${session}-stroke-${i}`,
          points: [i * 5, i * 5, i * 5 + 10, i * 5 + 10],
          color: '#000000',
          size: 5,
          timestamp: Date.now()
        }));

        rerender(
          <DrawingCanvas
            width={800}
            height={600}
            onStrokeStart={jest.fn()}
            onStrokeUpdate={jest.fn()}
            onStrokeEnd={jest.fn()}
            strokes={sessionStrokes}
          />
        );
      }

      // Memory usage should remain reasonable (basic check)
      const finalMemory = (performance as any).memory?.usedJSHeapSize || 0;
      if (finalMemory > 0 && initialMemory > 0) {
        const memoryIncrease = finalMemory - initialMemory;
        expect(memoryIncrease).toBeLessThan(50 * 1024 * 1024); // Less than 50MB increase
      }
    });
  });
});