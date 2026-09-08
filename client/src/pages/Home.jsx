import { Link } from "react-router-dom";

function Home() {
  return (
    <section className="home-page">
      <section className="hero home-hero">
        <div className="hero-copy">
          <p className="hero-eyebrow">Project Journal + Workspace</p>
          <h1>Organize every project in one place.</h1>
          <p>
            MyHobbyBoard helps makers, builders, and hobbyists create project boards,
            track tasks, and manage progress without scattered notes.
          </p>

          <div className="hero-actions">
            <Link to="/signup" className="primary-button">
              Get Started
            </Link>

            <Link to="/login" className="secondary-button">
              Login
            </Link>
          </div>

          <div className="hero-proof-row" aria-label="MyHobbyBoard highlights">
            <span>Task clarity</span>
            <span>Milestone updates</span>
            <span>Community learning</span>
          </div>
        </div>

        <aside className="hero-panel" aria-label="Featured board preview">
          <article className="hero-panel-card">
            <div className="hero-panel-label-row">
              <span className="hero-panel-label">Featured board</span>
              <span className="hero-panel-badge">14 updates</span>
            </div>
            <h2>Workshop rebuild: vintage radio in milestones</h2>
            <p>
              Keep planning notes, task progress, and update history together so the
              project story stays visible from start to finish.
            </p>
          </article>
        </aside>
      </section>

      <section className="home-feature-grid" aria-label="Why MyHobbyBoard works">
        <article className="home-feature-card home-feature-card-wide">
          <p className="feature-kicker">Built for focus</p>
          <h3>Turn ideas into outcomes you can actually finish.</h3>
          <p>
            Start with one board, break work into clear tasks, and log what changed
            after each session so momentum stays real.
          </p>
        </article>

        <article className="home-feature-card">
          <p className="feature-kicker">Community signal</p>
          <h3>Learn from real progress</h3>
          <p>Follow public boards and discover practical updates, not generic advice.</p>
        </article>
      </section>
    </section>
  );
}

export default Home;