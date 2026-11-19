import { useCallback, useEffect, useState } from "react";
import { apiRequest, apiUploadRequest } from "../services/api";
import MediaAttachment from "./MediaAttachment";
import UpdateComments from "./UpdateComments";

function BoardUpdates({
  boardId,
  tasks = [],
  selectedTaskId = null,
  onClearTaskFilter,
  onUpdateCreated,
  onUpdateDeleted,
  canManage = false,
}) {
  const [updates, setUpdates] = useState([]);
  const [content, setContent] = useState("");
  const [taskId, setTaskId] = useState("");
  const [mediaFile, setMediaFile] = useState(null);
  const [mediaFileName, setMediaFileName] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [showAllActivity, setShowAllActivity] = useState(false);

  const visibleUpdates = selectedTaskId
    ? updates.filter((update) => update.task_id === Number(selectedTaskId))
    : updates;
  const displayedUpdates = showAllActivity || selectedTaskId
    ? visibleUpdates
    : visibleUpdates.slice(0, 3);
  const selectedTask = tasks.find((task) => task.id === Number(selectedTaskId));

  const fetchUpdates = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const data = await apiRequest(`/boards/${boardId}/updates`);
      setUpdates(data.updates);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [boardId]);

  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    fetchUpdates();
  }, [fetchUpdates]);
  /* eslint-enable react-hooks/set-state-in-effect */

  async function handleSubmit(event) {
    event.preventDefault();

    if (!content.trim()) {
      setError("Update content is required.");
      return;
    }

    setSubmitting(true);
    setError("");

    try {
      let data;

      if (mediaFile) {
        const formData = new FormData();
        formData.append("content", content);
        if (taskId) {
          formData.append("task_id", taskId);
        }
        formData.append("media_file", mediaFile);

        data = await apiUploadRequest(`/boards/${boardId}/updates`, formData);
      } else {
        data = await apiRequest(`/boards/${boardId}/updates`, {
          method: "POST",
          body: JSON.stringify({ content, task_id: taskId || null }),
        });
      }

      setUpdates([data.update, ...updates]);
      onUpdateCreated?.(data.update);
      setContent("");
      setTaskId("");
      setMediaFile(null);
      setMediaFileName("");
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(updateId) {
    const confirmDelete = window.confirm("Delete this project update?");

    if (!confirmDelete) {
      return;
    }

    try {
      await apiRequest(`/updates/${updateId}`, {
        method: "DELETE",
      });

      onUpdateDeleted?.(updates.find((update) => update.id === updateId));
      setUpdates(updates.filter((update) => update.id !== updateId));
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <section className="update-section" id="board-progress-updates">
      <div className="task-section-header">
        <h2>Progress &amp; Discussion</h2>
        {selectedTaskId && (
          <div className="activity-filter-actions">
            <span className="count-pill">Task: {selectedTask?.title || "Selected task"}</span>
            <button type="button" className="cancel-button" onClick={onClearTaskFilter}>
              Clear filter
            </button>
          </div>
        )}
      </div>

      {canManage ? (
      <form className="update-form" onSubmit={handleSubmit}>
        <label>
          Related task (optional)
          <select value={taskId} onChange={(event) => setTaskId(event.target.value)}>
            <option value="">Whole board</option>
            {tasks.map((task) => (
              <option key={task.id} value={task.id}>
                {task.title}
              </option>
            ))}
          </select>
        </label>

        <label>
          Share a photo or video
          <input
            type="file"
            accept="image/*,video/*"
            onChange={(event) => {
              const file = event.target.files?.[0] || null;
              setMediaFile(file);
              setMediaFileName(file ? file.name : "");
            }}
          />
          {mediaFileName ? <span className="upload-file-name">Selected: {mediaFileName}</span> : null}
        </label>

        <label>
          Quick update
          <textarea
            value={content}
            onChange={(event) => setContent(event.target.value)}
            placeholder="Finished the frame, tested the first prototype, ordered supplies..."
          />
        </label>

        {error && <p className="error-message">{error}</p>}

        <button type="submit" className="secondary-button" disabled={submitting}>
          {submitting ? "Posting..." : "Post Update"}
        </button>
      </form>
      ) : null}

      {loading ? (
        <p className="loading-message">Loading updates...</p>
      ) : visibleUpdates.length === 0 ? (
        <p className="empty-state">
          {selectedTaskId
            ? "No progress posts for this task yet."
            : "No updates yet. Share the first milestone for this board."}
        </p>
      ) : (
        <>
          <div className="update-list">
            {displayedUpdates.map((update) => (
              <article className="update-card" key={update.id}>
                <div className="update-card-header">
                  <div>
                    <p className="update-author">{update.username || "You"}</p>
                    <p className="update-meta">
                      {new Date(update.created_at).toLocaleString()}
                    </p>
                  </div>

                  {canManage && (
                    <button
                      type="button"
                      className="danger-button"
                      onClick={() => handleDelete(update.id)}
                    >
                      Delete
                    </button>
                  )}
                </div>

                {update.is_announcement && <p className="activity-context">New public board</p>}
                {update.task_title && <p className="activity-context">Task: {update.task_title}</p>}
                <p className="update-content">{update.content}</p>

                {update.media_url && <MediaAttachment url={update.media_url} />}
                <UpdateComments updateId={update.id} />
              </article>
            ))}
          </div>

          {!selectedTaskId && visibleUpdates.length > 3 && (
            <button
              type="button"
              className="secondary-button activity-list-toggle"
              onClick={() => setShowAllActivity((showingAll) => !showingAll)}
            >
              {showAllActivity ? "Show recent only" : `View all activity (${visibleUpdates.length})`}
            </button>
          )}
        </>
      )}
    </section>
  );
}

export default BoardUpdates;