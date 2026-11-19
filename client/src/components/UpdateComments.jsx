import { useState } from "react";
import { apiRequest } from "../services/api";

function UpdateComments({ updateId }) {
  const [comments, setComments] = useState(null);
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function toggleDiscussion() {
    setError("");

    if (comments !== null) {
      setComments(null);
      return;
    }

    setLoading(true);
    try {
      const data = await apiRequest(`/updates/${updateId}/comments`);
      setComments(data.comments || []);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit(event) {
    event.preventDefault();
    const content = draft.trim();
    if (!content) {
      return;
    }

    setSubmitting(true);
    setError("");
    try {
      const data = await apiRequest(`/updates/${updateId}/comments`, {
        method: "POST",
        body: JSON.stringify({ content }),
      });
      setComments((current) => [...(current || []), data.comment]);
      setDraft("");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="update-comments">
      <button type="button" className="secondary-button" onClick={toggleDiscussion} disabled={loading}>
        {loading ? "Loading discussion..." : comments !== null ? "Hide discussion" : "Join discussion"}
      </button>

      {error && <p className="error-message">{error}</p>}

      {comments !== null && (
        <div className="update-comment-thread">
          {comments.length === 0 ? (
            <p className="empty-state">No comments yet. Start the discussion.</p>
          ) : (
            <ul className="comment-list">
              {comments.map((comment) => (
                <li key={comment.id}>
                  <strong>{comment.username || "User"}:</strong> {comment.content}
                </li>
              ))}
            </ul>
          )}

          <form className="comment-input-row" onSubmit={handleSubmit}>
            <input
              type="text"
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder="Add advice or feedback..."
              aria-label="Add a comment"
            />
            <button type="submit" className="secondary-button" disabled={submitting || !draft.trim()}>
              {submitting ? "Posting..." : "Comment"}
            </button>
          </form>
        </div>
      )}
    </div>
  );
}

export default UpdateComments;
