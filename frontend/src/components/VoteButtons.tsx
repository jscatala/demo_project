import { KeyboardEvent } from 'react';
import styles from './VoteButtons.module.css';

export type VoteOption = 'cats' | 'dogs';

export interface VoteButtonsProps {
  onVote: (option: VoteOption) => void;
  disabled?: boolean;
  loading?: boolean;
}

export default function VoteButtons({ onVote, disabled = false, loading = false }: VoteButtonsProps) {
  const isDisabled = disabled || loading;

  const handleClick = (option: VoteOption) => {
    if (isDisabled) return;
    onVote(option);
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLButtonElement>, option: VoteOption) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      handleClick(option);
    }
  };

  return (
    <div className={styles.container}>
      <h2 className={styles.title}>Make Your Choice</h2>
      <div className={styles.buttonGroup}>
        <button
          type="button"
          className={`${styles.voteButton} ${isDisabled ? styles.disabled : ''}`}
          onClick={() => handleClick('cats')}
          onKeyDown={(e) => handleKeyDown(e, 'cats')}
          disabled={isDisabled}
          aria-label="Vote for cats"
          aria-disabled={isDisabled}
        >
          <span className={styles.emoji} role="img" aria-label="cat">
            🐱
          </span>
          <span className={styles.label}>Cats</span>
        </button>

        <button
          type="button"
          className={`${styles.voteButton} ${isDisabled ? styles.disabled : ''}`}
          onClick={() => handleClick('dogs')}
          onKeyDown={(e) => handleKeyDown(e, 'dogs')}
          disabled={isDisabled}
          aria-label="Vote for dogs"
          aria-disabled={isDisabled}
        >
          <span className={styles.emoji} role="img" aria-label="dog">
            🐶
          </span>
          <span className={styles.label}>Dogs</span>
        </button>
      </div>
      {loading && <p className={styles.loadingText}>Submitting your vote...</p>}
    </div>
  );
}
