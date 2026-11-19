import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { apiRequest } from "../services/api";
import TaskForm from "../components/TaskForm";
import TaskCard from "../components/TaskCard";
import BoardUpdates from "../components/BoardUpdates";
import PlanningAssistant from "../components/PlanningAssistant";
import { formatDate } from "../dateUtils";

function BoardDetails() {
  const { boardId } = useParams();

  const [board, setBoard] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [selectedTaskId, setSelectedTaskId] = useState(null);
  const [followers, setFollowers] = useState([]);
  const [showFollowers, setShowFollowers] = useState(false);
  const [followersLoading, setFollowersLoading] = useState(false);
  const [followersError, setFollowersError] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const canManageBoard = Boolean(board?.is_owner);

  const completedCount = tasks.filter((task) => task.status === "Complete").length;
  const progressPercent = tasks.length ? Math.round((completedCount / tasks.length) * 100) : 0;
  const nextTask = tasks.find((task) => task.status !== "Complete");


  const fetchBoard = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const data = await apiRequest(`/boards/${boardId}`);
      setBoard(data.board);
      setTasks(data.board.tasks || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [boardId]);

  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    fetchBoard();
  }, [fetchBoard]);
  /* eslint-enable react-hooks/set-state-in-effect */

  async function handleCreateTask(formData) {
    const data = await apiRequest(`/boards/${boardId}/tasks`, {
      method: "POST",
      body: JSON.stringify(formData),
    });

    setTasks([data.task, ...tasks]);
  }

  async function handleUpdateTask(taskId, updates) {
    try {
      const data = await apiRequest(`/tasks/${taskId}`, {
        method: "PATCH",
        body: JSON.stringify(updates),
      });

      setTasks(
        tasks.map((task) => (task.id === taskId ? data.task : task))
      );
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleDeleteTask(taskId) {
    const confirmDelete = window.confirm(
      "Are you sure you want to delete this task?"
    );

    if (!confirmDelete) {
      return;
    }

    try {
      await apiRequest(`/tasks/${taskId}`, {
        method: "DELETE",
      });

      setTasks(tasks.filter((task) => task.id !== taskId));
    } catch (err) {
      setError(err.message);
    }
  }

  function handleTaskUpdateCount(update, change) {
    if (!update?.task_id) {
      return;
    }

    setTasks((currentTasks) => currentTasks.map((task) => (
      task.id === update.task_id
        ? { ...task, update_count: Math.max(0, (task.update_count || 0) + change) }
        : task
    )));
  }

  function handleViewTaskUpdates(taskId) {
    setSelectedTaskId(taskId);
    document.getElementById("board-progress-updates")?.scrollIntoView({ behavior: "smooth" });
  }

  async function handleToggleFollowers() {
    setFollowersError("");
    if (showFollowers) {
      setShowFollowers(false);
      return;
    }

    setFollowersLoading(true);
    try {
      const data = await apiRequest(`/boards/${boardId}/followers`);
      setFollowers(data.followers || []);
      setShowFollowers(true);
    } catch (requestError) {
      setFollowersError(requestError.message);
      setShowFollowers(true);
    } finally {
      setFollowersLoading(false);
    }
  }

  if (loading) {
    return <p className="loading-message">Loading board...</p>;
  }

  if (error) {
    return <p className="error-message">{error}</p>;
  }

  if (!board) {
    return <p className="empty-state">Board not found.</p>;
  }

  return (
    <section>
      <Link to="/dashboard" className="back-link">
        ← Back to Dashboard
      </Link>

      <div className="board-detail-header">
        <p className="feature-kicker">Board workspace</p>
        <div className="board-detail-title-row">
          <h1>{board.title}</h1>
          <span className={board.is_public ? "visibility-pill public" : "visibility-pill private"}>
            {board.is_public ? "Public board" : "Private board"}
          </span>
        </div>
        <div className="board-detail-meta-row">
          <span className="board-detail-type-pill">{board.hobby_type}</span>
          <span className="owner-pill">Owner: {board.owner_username || "Unknown"}</span>
          <span className="count-pill">{tasks.length} tasks</span>
          <span className="count-pill">{progressPercent}% complete</span>
          {board.is_public && (
            canManageBoard ? (
              <button
                type="button"
                className="count-pill follower-count-button"
                onClick={handleToggleFollowers}
                aria-expanded={showFollowers}
                aria-controls="board-followers-list"
              >
                {followersLoading ? "Loading followers..." : `${board.follower_count || 0} followers`}
              </button>
            ) : (
              <span className="count-pill">{board.follower_count || 0} followers</span>
            )
          )}
          {board.target_date && (
            <span className="count-pill">Target: {formatDate(board.target_date)}</span>
          )}
        </div>
        <p className="board-description">{board.description || "No description added yet."}</p>
        {canManageBoard && showFollowers && (
          <div className="board-followers-panel" id="board-followers-list">
            <div className="task-section-header">
              <h2>Followers</h2>
              <button type="button" className="cancel-button" onClick={handleToggleFollowers}>
                Close
              </button>
            </div>
            {followersError && <p className="error-message">{followersError}</p>}
            {followers.length === 0 ? (
              <p className="empty-state">No one follows this board yet.</p>
            ) : (
              <ul className="board-follower-list">
                {followers.map((follower) => (
                  <li key={follower.id}>
                    <span>{follower.username}</span>
                    <time>{new Date(follower.followed_at).toLocaleDateString()}</time>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>

      <section className="board-workspace">
        <div className="board-workspace-primary">
          <section className="planning-section">
            <div className="task-section-header">
              <h2>Planning Notes</h2>
              <span className="count-pill">{progressPercent}% done</span>
            </div>

            <div className="next-action-card">
              <h3>Next Action</h3>
              <p>
                {nextTask
                  ? `Focus next on: ${nextTask.title}`
                  : "Nice work. Every task is complete on this board."}
              </p>
            </div>

            <div className="planning-grid">
              <div className="planning-card">
                <h3>Materials</h3>
                <p>{board.materials || "No materials listed yet."}</p>
              </div>
              <div className="planning-card">
                <h3>Notes</h3>
                <p>{board.notes || "No planning notes yet."}</p>
              </div>
            </div>

            {canManageBoard ? <PlanningAssistant board={board} /> : null}
          </section>

          {canManageBoard ? <TaskForm onCreateTask={handleCreateTask} /> : null}
        </div>

        <div className="board-workspace-secondary">
          <BoardUpdates
            boardId={boardId}
            tasks={tasks}
            selectedTaskId={selectedTaskId}
            onClearTaskFilter={() => setSelectedTaskId(null)}
            onUpdateCreated={(update) => handleTaskUpdateCount(update, 1)}
            onUpdateDeleted={(update) => handleTaskUpdateCount(update, -1)}
            canManage={canManageBoard}
          />
        </div>
      </section>

      <div className="task-section">
        <div className="task-section-header">
          <h2>Tasks</h2>
          <span className="count-pill">{tasks.length} total</span>
        </div>

        {tasks.length === 0 ? (
          <p className="empty-state">No tasks yet. Add your first task above.</p>
        ) : (
          <div className="task-list">
            {tasks.map((task) => (
              <TaskCard
                key={task.id}
                task={task}
                onUpdateTask={handleUpdateTask}
                onDeleteTask={handleDeleteTask}
                onViewUpdates={handleViewTaskUpdates}
                canManage={canManageBoard}
              />
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

export default BoardDetails;