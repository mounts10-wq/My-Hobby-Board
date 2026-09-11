import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [slowStart, setSlowStart] = useState(false);

  function handleChange(event) {
    setFormData({
      ...formData,
      [event.target.name]: event.target.value,
    });
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setLoading(true);
    setSlowStart(false);

    // Free-tier backend can take ~30-50s to wake up after being idle.
    const slowStartTimer = setTimeout(() => setSlowStart(true), 4000);

    try {
      await login(formData);
      navigate("/dashboard");
    } catch (err) {
      setError(err.message);
    } finally {
      clearTimeout(slowStartTimer);
      setSlowStart(false);
      setLoading(false);
    }
  }

  return (
    <section className="form-page">
      <h1>Welcome back</h1>
      <p>Log in to continue tracking your hobby projects.</p>

      <form onSubmit={handleSubmit} className="auth-form">
        <label>
          Email
          <input
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
          />
        </label>

        <label>
          Password
          <input
            type="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
          />
        </label>

        {error && <p className="error-message">{error}</p>}
        {slowStart && (
          <p className="loading-message">
            Still working&hellip; the server can take up to a minute to wake up
            after sitting idle.
          </p>
        )}

        <button type="submit" disabled={loading}>
          {loading ? "Logging in..." : "Login"}
        </button>
      </form>
    </section>
  );
}

export default Login;