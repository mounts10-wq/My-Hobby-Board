import { useCallback, useEffect, useState } from "react";
import { apiRequest, apiUploadRequest } from "../services/api";
import MediaAttachment from "./MediaAttachment";

function BoardUpdates({ boardId, canManage = false }) {
  const [updates, setUpdates] = useState([]);
  const [content, setContent] = useState("");
  const [mediaFile, setMediaFile] = useState(null);
  const [mediaFileName, setMediaFileName] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [commentsByUpdateId, setCommentsByUpdateId] = useState({});
  const [commentDrafts, setCommentDrafts] = useState({});
  const [commentLoadingByUpdateId, setCommentLoadingByUpdateId] = useState({});

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
        formData.append("media_file", mediaFile);

        data = await apiUploadRequest(`/boards/${boardId}/updates`, formData);
      } else {
        data = await apiRequest(`/boards/${boardId}/updates`, {
          method: "POST",
          body: JSON.stringify({ content }),
        });
      }

      setUpdates([data.update, ...updates]);
      setContent("");
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

      setUpdates(updates.filter((update) => update.id !== updateId));
    } catch (err) {
      setError(err.message);
    }
  }

  async function toggleComments(updateId) {
    if (commentsByUpdateId[updateId]) {
      setCommentsByUpdateId((current) => {
        const next = { ...current };
        delete next[updateId];
        return next;
      });
      return;
    }

    setCommentLoadingByUpdateId((current) => ({ ...current, [updateId]: true }));

    try {
      const data = await apiRequest(`/updates/${updateId}/comments`);
      setCommentsByUpdateId((current) => ({ ...current, [updateId]: data.comments || [] }));
    } catch (err) {
      setError(err.message);
    } finally {
      setCommentLoadingByUpdateId((current) => ({ ...current, [updateId]: false }));
    }
  }

  async function handlePostComment(updateId) {
    const draft = (commentDrafts[updateId] || "").trim();
    if (!draft) {
      return;
    }

    try {
      const data = await apiRequest(`/updates/${updateId}/comments`, {
        method: "POST",
        body: JSON.stringify({ content: draft }),
      });

      setCommentsByUpdateId((current) => ({
        ...current,
        [updateId]: [...(current[updateId] || []), data.comment],
      }));
      setCommentDrafts((current) => ({ ...current, [updateId]: "" }));
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <section className="update-section">
      <div className="task-section-header">
        <h2>Project Updates</h2>
      </div>

      {canManage ? (
      <form className="update-form" onSubmit={handleSubmit}>
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
      ) : updates.length === 0 ? (
        <p className="empty-state">No updates yet. Share the first milestone for this board.</p>
      ) : (
        <div className="update-list">
          {updates.map((update) => (
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

              <p className="update-content">{update.content}</p>

              {update.media_url && <MediaAttachment url={update.media_url} />}

              <div className="update-comments">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => toggleComments(update.id)}
                >
                  {commentsByUpdateId[update.id] ? "Hide comments" : "Show comments"}
                </button>

                {commentLoadingByUpdateId[update.id] && (
                  <p className="loading-message">Loading comments...</p>
                )}

                {commentsByUpdateId[update.id] && (
                  <div className="update-comment-thread">
                    {(commentsByUpdateId[update.id] || []).length === 0 ? (
                      <p className="empty-state">No comments yet. Start the discussion.</p>
                    ) : (
                      <ul className="comment-list">
                        {(commentsByUpdateId[update.id] || []).map((comment) => (
                          <li key={comment.id}>
                            <strong>{comment.username || "User"}:</strong> {comment.content}
                          </li>
                        ))}
                      </ul>
                    )}

                    <div className="comment-input-row">
                      <input
                        type="text"
                        value={commentDrafts[update.id] || ""}
                        onChange={(event) =>
                          setCommentDrafts((current) => ({
                            ...current,
                            [update.id]: event.target.value,
                          }))
                        }
                        placeholder="Add advice or feedback..."
                      />
                      <button
                        type="button"
                        className="secondary-button"
                        onClick={() => handlePostComment(update.id)}
                      >
                        Comment
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

export default BoardUpdates;