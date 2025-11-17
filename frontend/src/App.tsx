import { useState } from 'react';
import VoteButtons, { VoteOption } from './components/VoteButtons';
import './App.css';

function App() {
  const [selectedVote, setSelectedVote] = useState<VoteOption | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleVote = async (option: VoteOption) => {
    setIsLoading(true);
    console.log(`Vote submitted: ${option}`);

    setTimeout(() => {
      setSelectedVote(option);
      setIsLoading(false);
    }, 1000);
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>🐱 Cats vs Dogs 🐶</h1>
        <p className="subtitle">Cast your vote and see who wins!</p>
      </header>

      <main className="app-main">
        {selectedVote && (
          <div className="vote-confirmation">
            <p>✅ You voted for {selectedVote === 'cats' ? '🐱 Cats' : '🐶 Dogs'}!</p>
          </div>
        )}

        <VoteButtons
          onVote={handleVote}
          disabled={selectedVote !== null}
          loading={isLoading}
        />

        {selectedVote && (
          <button
            className="reset-button"
            onClick={() => setSelectedVote(null)}
          >
            Vote Again
          </button>
        )}
      </main>

      <footer className="app-footer">
        <p>Frontend v0.2.0 • Vite + TypeScript + React 18</p>
        <p className="api-info">
          API: {(window as any).APP_CONFIG?.API_URL || 'Not configured'}
        </p>
      </footer>
    </div>
  );
}

export default App;
