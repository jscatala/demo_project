/**
 * VoteResults Component Test Cases
 *
 * To run these tests, first install testing dependencies:
 * npm install -D vitest @testing-library/react @testing-library/jest-dom
 *
 * Add to package.json scripts:
 * "test": "vitest"
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import VoteResults from './VoteResults';

describe('VoteResults', () => {
  describe('Data Display', () => {
    it('renders vote data with correct percentages', () => {
      const data = { cats: 200, dogs: 100 };
      render(<VoteResults data={data} />);

      expect(screen.getByText('66.7%')).toBeInTheDocument();
      expect(screen.getByText('33.3%')).toBeInTheDocument();
    });

    it('displays vote counts with thousand separators', () => {
      const data = { cats: 1234, dogs: 5678 };
      render(<VoteResults data={data} />);

      expect(screen.getByText(/1,234 votes/)).toBeInTheDocument();
      expect(screen.getByText(/5,678 votes/)).toBeInTheDocument();
    });

    it('displays total votes sum', () => {
      const data = { cats: 100, dogs: 50 };
      render(<VoteResults data={data} />);

      expect(screen.getByText('Total votes: 150')).toBeInTheDocument();
    });

    it('calculates 50/50 split correctly', () => {
      const data = { cats: 500, dogs: 500 };
      render(<VoteResults data={data} />);

      const percentages = screen.getAllByText('50.0%');
      expect(percentages).toHaveLength(2);
    });
  });

  describe('Loading State', () => {
    it('shows loading state when loading prop is true', () => {
      render(<VoteResults loading={true} />);

      expect(screen.getByText('Loading results...')).toBeInTheDocument();
      expect(screen.queryByText('Total votes:')).not.toBeInTheDocument();
    });

    it('displays skeleton placeholders during loading', () => {
      const { container } = render(<VoteResults loading={true} />);

      const skeletons = container.querySelectorAll('.skeleton');
      expect(skeletons.length).toBeGreaterThan(0);
    });
  });

  describe('Error State', () => {
    it('displays error message when error prop is provided', () => {
      const errorMessage = 'Failed to fetch results';
      render(<VoteResults error={errorMessage} />);

      expect(screen.getByText(errorMessage)).toBeInTheDocument();
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    it('does not show data when in error state', () => {
      const data = { cats: 100, dogs: 50 };
      render(<VoteResults data={data} error="Network error" />);

      expect(screen.queryByText('Total votes:')).not.toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('shows empty state when no votes exist', () => {
      const data = { cats: 0, dogs: 0 };
      render(<VoteResults data={data} />);

      expect(screen.getByText('No votes yet. Be the first to vote!')).toBeInTheDocument();
    });

    it('displays 0.0% for both options when no votes', () => {
      const data = { cats: 0, dogs: 0 };
      render(<VoteResults data={data} />);

      const percentages = screen.getAllByText('0.0%');
      expect(percentages.length).toBeGreaterThanOrEqual(2);
    });

    it('does not show total votes when count is zero', () => {
      const data = { cats: 0, dogs: 0 };
      render(<VoteResults data={data} />);

      expect(screen.queryByText(/Total votes:/)).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has ARIA live region for dynamic updates', () => {
      const data = { cats: 100, dogs: 50 };
      const { container } = render(<VoteResults data={data} />);

      const liveRegion = container.querySelector('[aria-live="polite"]');
      expect(liveRegion).toBeInTheDocument();
    });

    it('has proper progress bar ARIA attributes', () => {
      const data = { cats: 75, dogs: 25 };
      render(<VoteResults data={data} />);

      const progressBars = screen.getAllByRole('progressbar');
      expect(progressBars.length).toBe(2);

      expect(progressBars[0]).toHaveAttribute('aria-valuemin', '0');
      expect(progressBars[0]).toHaveAttribute('aria-valuemax', '100');
    });

    it('includes emoji with aria-label', () => {
      const data = { cats: 100, dogs: 50 };
      render(<VoteResults data={data} />);

      expect(screen.getByLabelText('cats')).toBeInTheDocument();
      expect(screen.getByLabelText('dogs')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles undefined data prop gracefully', () => {
      render(<VoteResults />);

      expect(screen.getByText('No votes yet. Be the first to vote!')).toBeInTheDocument();
    });

    it('handles very large numbers correctly', () => {
      const data = { cats: 1000000, dogs: 500000 };
      render(<VoteResults data={data} />);

      expect(screen.getByText('Total votes: 1,500,000')).toBeInTheDocument();
    });

    it('maintains percentage precision with uneven splits', () => {
      const data = { cats: 1, dogs: 2 };
      render(<VoteResults data={data} />);

      expect(screen.getByText('33.3%')).toBeInTheDocument();
      expect(screen.getByText('66.7%')).toBeInTheDocument();
    });
  });
});
