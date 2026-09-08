import { useState } from "react";

function BoardForm({ onCreateBoard }) {
  const [formData, setFormData] = useState({
    title: "",
    hobby_type: "",
    description: "",
    materials: "",
    notes: "",
    is_public: false,
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  function handleChange(event) {
    if (success) {
      setSuccess("");
    }

    setFormData({
      ...formData,
      [event.target.name]: event.target.type === "checkbox" ? event.target.checked : event.target.value,
    });
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setSuccess("");

    if (!formData.title.trim() || !formData.hobby_type.trim()) {
      setError("Title and hobby/project type are required.");
      return;
    }

    setLoading(true);

    try {
      await onCreateBoard(formData);

      setFormData({
        title: "",
        hobby_type: "",
        description: "",
        materials: "",
        notes: "",
        is_public: false,
      });
      setSuccess("Board created. You can add tasks from the board details page.");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="board-form">
      <h2>Create a New Hobby/Project Board</h2>
      <p className="form-helper-text">
        Add the essentials first. You can always refine the plan, materials, and visibility later.
      </p>

      <label>
        Board Title
        <input
          type="text"
          name="title"
          placeholder="Example: Mustang Restoration"
          value={formData.title}
          onChange={handleChange}
        />
      </label>

      <label>
        Hobby/Project Type
        <input
          type="text"
          name="hobby_type"
          placeholder="Example: Cars, Crochet, Woodworking"
          value={formData.hobby_type}
          onChange={handleChange}
        />
      </label>

      <label>
        Description
        <textarea
          name="description"
          placeholder="Describe what this board is for..."
          value={formData.description}
          onChange={handleChange}
        />
      </label>

      <label>
        Materials
        <textarea
          name="materials"
          placeholder="List the supplies, tools, or resources you need..."
          value={formData.materials}
          onChange={handleChange}
        />
      </label>

      <label>
        Planning Notes
        <textarea
          name="notes"
          placeholder="Add a quick plan, timeline, or reminders..."
          value={formData.notes}
          onChange={handleChange}
        />
      </label>

      <label className="checkbox-field">
        <input
          type="checkbox"
          name="is_public"
          checked={formData.is_public}
          onChange={handleChange}
        />
        Share this board publicly in Community discovery and feed.
      </label>

      {error && <p className="error-message">{error}</p>}
      {success && <p className="success-message">{success}</p>}

      <button type="submit" disabled={loading}>
        {loading ? "Creating..." : "Create Board"}
      </button>
    </form>
  );
}

export default BoardForm;