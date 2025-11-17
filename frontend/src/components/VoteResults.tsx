import styles from './VoteResults.module.css';

export interface VoteData {
  cats: number;
  dogs: number;
}

export interface VoteResultsProps {
  data?: VoteData;
  loading?: boolean;
  error?: string;
}

interface ResultItem {
  label: string;
  emoji: string;
  count: number;
  percentage: string;
}

function calculatePercentage(count: number, total: number): string {
  if (total === 0) return '0.0';
  return ((count / total) * 100).toFixed(1);
}

function formatCount(count: number): string {
  return count.toLocaleString('en-US');
}

export default function VoteResults({ data, loading = false, error }: VoteResultsProps) {
  if (loading) {
    return (
      <div className={styles.container}>
        <h2 className={styles.title}>Current Results</h2>
        <div className={styles.loading}>
          <div className={styles.skeleton}></div>
          <div className={styles.skeleton}></div>
        </div>
        <p className={styles.loadingText}>Loading results...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.container}>
        <h2 className={styles.title}>Current Results</h2>
        <div className={styles.error} role="alert">
          <span className={styles.errorIcon}>⚠️</span>
          <p className={styles.errorText}>{error}</p>
        </div>
      </div>
    );
  }

  const cats = data?.cats ?? 0;
  const dogs = data?.dogs ?? 0;
  const total = cats + dogs;

  const results: ResultItem[] = [
    {
      label: 'Cats',
      emoji: '🐱',
      count: cats,
      percentage: calculatePercentage(cats, total),
    },
    {
      label: 'Dogs',
      emoji: '🐶',
      count: dogs,
      percentage: calculatePercentage(dogs, total),
    },
  ];

  const hasVotes = total > 0;

  return (
    <div className={styles.container}>
      <h2 className={styles.title}>Current Results</h2>

      {!hasVotes && (
        <div className={styles.emptyState}>
          <p>No votes yet. Be the first to vote!</p>
        </div>
      )}

      <div
        className={styles.resultsGrid}
        aria-live="polite"
        aria-atomic="true"
      >
        {results.map((result) => (
          <div key={result.label} className={styles.resultItem}>
            <div className={styles.resultHeader}>
              <span className={styles.resultLabel}>
                <span role="img" aria-label={result.label.toLowerCase()}>
                  {result.emoji}
                </span>
                {' '}
                {result.label}
              </span>
              <span className={styles.resultPercentage}>
                {result.percentage}%
              </span>
            </div>

            <div
              className={styles.progressBar}
              role="progressbar"
              aria-valuenow={parseFloat(result.percentage)}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label={`${result.label} votes`}
            >
              <div
                className={styles.progressFill}
                style={{ width: `${result.percentage}%` }}
              >
                {hasVotes && (
                  <span className={styles.progressLabel}>
                    {formatCount(result.count)} votes
                  </span>
                )}
              </div>
            </div>

            <div className={styles.resultCount}>
              {formatCount(result.count)} votes
            </div>
          </div>
        ))}
      </div>

      {hasVotes && (
        <div className={styles.totalVotes}>
          Total votes: {formatCount(total)}
        </div>
      )}
    </div>
  );
}
