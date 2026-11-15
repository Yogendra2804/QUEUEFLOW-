import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Spinner } from '../components/ui/Spinner';
import { EmptyState } from '../components/ui/EmptyState';

describe('UI Components', () => {
  it('renders Spinner correctly with default and custom sizes', () => {
    const { container, rerender } = render(<Spinner size="sm" />);
    expect(container.firstChild).toBeInTheDocument();
    expect(container.firstChild).toHaveClass('h-4');

    rerender(<Spinner size="lg" />);
    expect(container.firstChild).toHaveClass('h-10');
  });

  it('renders EmptyState with title, description, and action button', () => {
    render(
      <EmptyState
        title="No queues found"
        description="Create your first queue to get started."
        action={<button>Create Queue</button>}
      />
    );

    expect(screen.getByText('No queues found')).toBeInTheDocument();
    expect(
      screen.getByText('Create your first queue to get started.')
    ).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: 'Create Queue' })
    ).toBeInTheDocument();
  });
});
