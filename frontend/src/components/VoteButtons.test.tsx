/**
 * VoteButtons Component Test Cases
 *
 * To run these tests, first install testing dependencies:
 * npm install -D vitest @testing-library/react @testing-library/user-event @testing-library/jest-dom
 *
 * Add to package.json scripts:
 * "test": "vitest"
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import VoteButtons from './VoteButtons';

describe('VoteButtons', () => {
  it('renders two voting buttons', () => {
    const mockOnVote = vi.fn();
    render(<VoteButtons onVote={mockOnVote} />);

    expect(screen.getByLabelText('Vote for cats')).toBeInTheDocument();
    expect(screen.getByLabelText('Vote for dogs')).toBeInTheDocument();
  });

  it('calls onVote with "cats" when cats button is clicked', async () => {
    const mockOnVote = vi.fn();
    const user = userEvent.setup();
    render(<VoteButtons onVote={mockOnVote} />);

    const catsButton = screen.getByLabelText('Vote for cats');
    await user.click(catsButton);

    expect(mockOnVote).toHaveBeenCalledWith('cats');
    expect(mockOnVote).toHaveBeenCalledTimes(1);
  });

  it('calls onVote with "dogs" when dogs button is clicked', async () => {
    const mockOnVote = vi.fn();
    const user = userEvent.setup();
    render(<VoteButtons onVote={mockOnVote} />);

    const dogsButton = screen.getByLabelText('Vote for dogs');
    await user.click(dogsButton);

    expect(mockOnVote).toHaveBeenCalledWith('dogs');
    expect(mockOnVote).toHaveBeenCalledTimes(1);
  });

  it('does not call onVote when disabled prop is true', async () => {
    const mockOnVote = vi.fn();
    const user = userEvent.setup();
    render(<VoteButtons onVote={mockOnVote} disabled={true} />);

    const catsButton = screen.getByLabelText('Vote for cats');
    await user.click(catsButton);

    expect(mockOnVote).not.toHaveBeenCalled();
  });

  it('does not call onVote when loading prop is true', async () => {
    const mockOnVote = vi.fn();
    const user = userEvent.setup();
    render(<VoteButtons onVote={mockOnVote} loading={true} />);

    const dogsButton = screen.getByLabelText('Vote for dogs');
    await user.click(dogsButton);

    expect(mockOnVote).not.toHaveBeenCalled();
  });

  it('displays loading text when loading prop is true', () => {
    const mockOnVote = vi.fn();
    render(<VoteButtons onVote={mockOnVote} loading={true} />);

    expect(screen.getByText('Submitting your vote...')).toBeInTheDocument();
  });

  it('supports keyboard navigation with Enter key', () => {
    const mockOnVote = vi.fn();
    render(<VoteButtons onVote={mockOnVote} />);

    const catsButton = screen.getByLabelText('Vote for cats');
    catsButton.focus();
    fireEvent.keyDown(catsButton, { key: 'Enter', code: 'Enter' });

    expect(mockOnVote).toHaveBeenCalledWith('cats');
  });

  it('supports keyboard navigation with Space key', () => {
    const mockOnVote = vi.fn();
    render(<VoteButtons onVote={mockOnVote} />);

    const dogsButton = screen.getByLabelText('Vote for dogs');
    dogsButton.focus();
    fireEvent.keyDown(dogsButton, { key: ' ', code: 'Space' });

    expect(mockOnVote).toHaveBeenCalledWith('dogs');
  });

  it('has proper ARIA attributes', () => {
    const mockOnVote = vi.fn();
    render(<VoteButtons onVote={mockOnVote} />);

    const catsButton = screen.getByLabelText('Vote for cats');
    const dogsButton = screen.getByLabelText('Vote for dogs');

    expect(catsButton).toHaveAttribute('aria-label', 'Vote for cats');
    expect(dogsButton).toHaveAttribute('aria-label', 'Vote for dogs');
    expect(catsButton).toHaveAttribute('aria-disabled', 'false');
  });

  it('sets aria-disabled to true when disabled', () => {
    const mockOnVote = vi.fn();
    render(<VoteButtons onVote={mockOnVote} disabled={true} />);

    const catsButton = screen.getByLabelText('Vote for cats');
    expect(catsButton).toHaveAttribute('aria-disabled', 'true');
  });
});
