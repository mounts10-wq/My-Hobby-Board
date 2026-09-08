import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { apiRequest } from "../services/api";
import BoardForm from "../components/BoardForm";
import BoardCard from "../components/BoardCard";

function Dashboard() {
  const { user } = useAuth();

  const [boards, setBoards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [statsLoading, setStatsLoading] = useState(true);
  const [notice, setNotice] = useState("");
  const [stats, setStats] = useState({
    board_count: 0,
    task_count: 0,
    completed_tasks: 0,
    in_progress_tasks: 0,
    not_started_tasks: 0,
    high_priority_tasks: 0,
    completion_rate: 0,
  });

  useEffect(() => {
    fetchBoards();
    fetchStats();
  }, []);

  async function fetchBoards() {
    setLoading(true);
    setError("");

    try {
      const data = await apiRequest("/boards?page=1&per_page=10");
      setBoards(data.boards);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function fetchStats() {
    setStatsLoading(true);

    try {
      const data = await apiRequest("/dashboard/stats");
      setStats(data.stats);
    } catch {
      setStats({
        board_count: 0,
        task_count: 0,
        completed_tasks: 0,
        in_progress_tasks: 0,
        not_started_tasks: 0,
        high_priority_tasks: 0,
        completion_rate: 0,
      });
    } finally {
      setStatsLoading(false);
    }
  }
   
  async function handleUpdateBoard(boardId, updates) {
    const data = await apiRequest(`/boards/${boardId}`, {
      method: "PATCH",
      body: JSON.stringify(updates),
    });

    setBoards(
      boards.map((board) => (board.id === boardId ? data.board : board))
    );
    setNotice("Board updated successfully.");
  }

  async function handleCreateBoard(formData) {
    const data = await apiRequest("/boards", {
      method: "POST",
      body: JSON.stringify(formData),
    });

    setBoards([data.board, ...boards]);
    fetchStats();
    setNotice("Board created successfully.");
  }

  async function handleDeleteBoard(boardId) {
    const confirmDelete = window.confirm(
      "Are you sure you want to delete this board?"
    );

    if (!confirmDelete) {
      return;
    }

    try {
      await apiRequest(`/boards/${boardId}`, {
        method: "DELETE",
      });

      setBoards(boards.filter((board) => board.id !== boardId));
      fetchStats();
      setNotice("Board deleted.");
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <section className="dashboard-page">
      <div className="dashboard-hero">
        <div className="dashboard-hero-copy">
          <p className="feature-kicker">Workspace overview</p>
          <h1>Your boards, progress, and next moves in one place.</h1>
          <p>
            Welcome, {user?.username}. This view is your control room for active
            projects, planning notes, and milestones that need to stay visible.
          </p>
          <p className="dashboard-subcopy">
            Review progress, create intentionally, and keep each board focused on
            a real next step.
          </p>
        </div>
      </div>

      <section className="dashboard-workspace">
        <div className="dashboard-workspace-primary">
          <section className="insights-panel">
            <div className="insights-header">
              <h2>Progress Snapshot</h2>
              {!statsLoading && (
                <span className="count-pill">{stats.completion_rate}% complete</span>
              )}
            </div>

            {statsLoading ? (
              <p className="loading-message">Loading your stats...</p>
            ) : (
              <>
                <div className="progress-track" role="img" aria-label="Task completion progress">
                  <div
                    className="progress-fill"
                    style={{ width: `${Math.min(stats.completion_rate, 100)}%` }}
                  />
                </div>

                <div className="stats-grid">
                  <article className="stat-card">
                    <p className="stat-label">Boards</p>
                    <p className="stat-value">{stats.board_count}</p>
                  </article>
                  <article className="stat-card">
                    <p className="stat-label">Total Tasks</p>
                    <p className="stat-value">{stats.task_count}</p>
                  </article>
                  <article className="stat-card">
                    <p className="stat-label">Completed</p>
                    <p className="stat-value">{stats.completed_tasks}</p>
                  </article>
                  <article className="stat-card">
                    <p className="stat-label">In Progress</p>
                    <p className="stat-value">{stats.in_progress_tasks}</p>
                  </article>
                  <article className="stat-card">
                    <p className="stat-label">Not Started</p>
                    <p className="stat-value">{stats.not_started_tasks}</p>
                  </article>
                  <article className="stat-card">
                    <p className="stat-label">High Priority</p>
                    <p className="stat-value">{stats.high_priority_tasks}</p>
                  </article>
                </div>
              </>
            )}
          </section>

          <section className="dashboard-tip-panel">
            <div className="dashboard-tip-header">
              <div>
                <h2>Quick Start</h2>
                <p>A simple flow for turning ideas into a real project board.</p>
              </div>
              <span className="count-pill">3 steps</span>
            </div>

            <ol className="dashboard-tip-list">
              <li>Create one board for the project you care about most.</li>
              <li>Add a few tasks and mark the first one complete quickly.</li>
              <li>Post an update when you hit a milestone or learn something new.</li>
            </ol>
          </section>
        </div>

        <div className="dashboard-workspace-secondary">
          <BoardForm onCreateBoard={handleCreateBoard} />
        </div>
      </section>

      {notice && <p className="success-message">{notice}</p>}
      {loading && <p className="loading-message">Loading boards...</p>}
      {error && <p className="error-message">{error}</p>}

      {!loading && boards.length === 0 && (
        <div className="empty-state">
          <h3>No boards yet</h3>
          <p>Create your first board above to start planning your next hobby project.</p>
        </div>
      )}

      <section className="dashboard-board-section">
        <div className="board-grid">
          {boards.map((board) => (
            <BoardCard
              key={board.id}
              board={board}
              onDeleteBoard={handleDeleteBoard}
              onUpdateBoard={handleUpdateBoard}
            />
          ))}
        </div>
      </section>
    </section>
  );
}

export default Dashboard;