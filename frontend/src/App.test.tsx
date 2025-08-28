import { render, screen } from '@testing-library/react';
import App from './App';

test('renders collaborative drawing board title', () => {
  render(<App />);
  const titleElement = screen.getByText(/collaborative drawing board/i);
  expect(titleElement).toBeInTheDocument();
});

test('shows TDD setup complete message', () => {
  render(<App />);
  const messageElement = screen.getByText(/TDD Setup Complete/i);
  expect(messageElement).toBeInTheDocument();
});

// Example failing test - implement in TDD cycle
test('renders canvas component - SHOULD FAIL initially', () => {
  render(<App />);
  const canvas = screen.getByTestId('drawing-canvas');
  expect(canvas).toBeInTheDocument();
});

// Example failing test - implement in TDD cycle
test('has drawing tools toolbar - SHOULD FAIL initially', () => {
  render(<App />);
  const toolbar = screen.getByTestId('drawing-toolbar');
  expect(toolbar).toBeInTheDocument();
});