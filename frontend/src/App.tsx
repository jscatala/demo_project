import { useState } from 'react';
import VoteButtons, { VoteOption } from './components/VoteButtons';
import VoteResults from './components/VoteResults';
import { useVote } from './hooks/useVote';
import { useResults } from './hooks/useResults';
import './App.css';

function App() {
  const [selectedVote, setSelectedVote] = useState<VoteOption | null>(null);

  const { data: resultsData, isLoading: resultsLoading, error: resultsError, refetch } = useResults();
  const { vote, isLoading: voteLoading, error: voteError, clearError } = useVote(() => {
    refetch();
  });

  const handleVote = async (option: VoteOption) => {
    clearError();
    await vote(option);
    setSelectedVote(option);
  };

  const handleVoteAgain = () => {
    setSelectedVote(null);
    clearError();
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>🐱 Cats vs Dogs 🐶</h1>
        <p className="subtitle">Cast your vote and see who wins!</p>
      </header>

      <main className="app-main">
        <VoteResults
          data={resultsData ? { cats: resultsData.cats, dogs: resultsData.dogs } : undefined}
          loading={resultsLoading}
          error={resultsError || undefined}
        />

        {voteError && (
          <div className="error-message" role="alert">
            <span className="error-icon">⚠️</span>
            <p>{voteError}</p>
          </div>
        )}

        {selectedVote && !voteError && (
          <div className="vote-confirmation">
            <p>✅ You voted for {selectedVote === 'cats' ? '🐱 Cats' : '🐶 Dogs'}!</p>
          </div>
        )}

        <VoteButtons
          onVote={handleVote}
          disabled={selectedVote !== null && !voteError}
          loading={voteLoading}
        />

        {selectedVote && (
          <button
            className="reset-button"
            onClick={handleVoteAgain}
          >
            Vote Again
          </button>
        )}
      </main>

      <footer className="app-footer">
        <p>Frontend v0.5.0 • Vite + TypeScript + React 18</p>
        <p className="api-info">
          API: {(window as any).APP_CONFIG?.API_URL || 'Not configured'}
        </p>
      </footer>
    </div>
  );
}

export default App;
