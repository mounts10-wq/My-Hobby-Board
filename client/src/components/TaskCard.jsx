import { useState } from "react";

function TaskCard({ task, onUpdateTask, onDeleteTask, canManage = true }) {
  const [isEditing, setIsEditing] = useState(false);

  const [formData, setFormData] = useState({
    title: task.title,
    description: task.description || "",
    status: task.status,
    priority: task.priority,
  });

  const [error, setError] = useState("");

  const statusClassMap = {
    "Not Started": "status-not-started",
    "In Progress": "status-in-progress",
    Complete: "status-complete",
  };

  const priorityClassMap = {
    Low: "priority-low",
    Medium: "priority-medium",
    High: "priority-high",
  };

  function handleChange(event) {
    setFormData({
      ...formData,
      [event.target.name]: event.target.value,
    });
  }

  async function handleQuickStatusChange(event) {
    await onUpdateTask(task.id, {
      status: event.target.value,
    });
  }

  async function handleQuickPriorityChange(event) {
    await onUpdateTask(task.id, {
      priority: event.target.value,
    });
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");

    if (!formData.title.trim()) {
      setError("Task title is required.");
      return;
    }

    try {
      await onUpdateTask(task.id, formData);
      setIsEditing(false);
    } catch (err) {
      setError(err.message);
    }
  }

  if (isEditing && canManage) {
    return (
      <article className="task-card">
        <form onSubmit={handleSubmit} className="edit-form">
          <label>
            Task Title
            <input
              type="text"
              name="title"
              value={formData.title}
              onChange={handleChange}
            />
          </label>

          <label>
            Description
            <textarea
              name="description"
              value={formData.description}
              onChange={handleChange}
            />
          </label>

          <label>
            Status
            <select name="status" value={formData.status} onChange={handleChange}>
              <option value="Not Started">Not Started</option>
              <option value="In Progress">In Progress</option>
              <option value="Complete">Complete</option>
            </select>
          </label>

          <label>
            Priority
            <select
              name="priority"
              value={formData.priority}
              onChange={handleChange}
            >
              <option value="Low">Low</option>
              <option value="Medium">Medium</option>
              <option value="High">High</option>
            </select>
          </label>

          {error && <p className="error-message">{error}</p>}

          <div className="board-card-actions">
            <button type="submit" className="save-edit-button">
              Save
            </button>

            <button
              type="button"
              className="cancel-button"
              onClick={() => setIsEditing(false)}
            >
              Cancel
            </button>
          </div>
        </form>
      </article>
    );
  }

  return (
    <article className="task-card">
      <div>
        <div className="board-card-heading">
          <h3>{task.title}</h3>
          <span className={`task-badge ${priorityClassMap[task.priority] || "priority-medium"}`}>
            {task.priority} Priority
          </span>
        </div>
        <div className="task-meta">
          <span className={`task-badge ${statusClassMap[task.status] || "status-not-started"}`}>
            {task.status}
          </span>
        </div>
        <p>{task.description || "No description added."}</p>

        {canManage && (
          <div className="task-controls">
            <label>
              Status
              <select value={task.status} onChange={handleQuickStatusChange}>
                <option value="Not Started">Not Started</option>
                <option value="In Progress">In Progress</option>
                <option value="Complete">Complete</option>
              </select>
            </label>

            <label>
              Priority
              <select value={task.priority} onChange={handleQuickPriorityChange}>
                <option value="Low">Low</option>
                <option value="Medium">Medium</option>
                <option value="High">High</option>
              </select>
            </label>
          </div>
        )}
      </div>

      {canManage && (
        <div className="board-card-actions">
          <button className="edit-button" onClick={() => setIsEditing(true)}>
            Edit
          </button>

          <button className="danger-button" onClick={() => onDeleteTask(task.id)}>
            Delete Task
          </button>
        </div>
      )}
    </article>
  );
}

export default TaskCard;