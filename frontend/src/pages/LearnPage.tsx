import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import type { LearnGroup } from "../types";

export function LearnPage() {
  const [groups, setGroups] = useState<LearnGroup[]>([]);
  const [round, setRound] = useState<number | "all">("all");
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .learnModules()
      .then((data) => setGroups(data.groups))
      .catch((err: Error) => setError(err.message));
  }, []);

  if (error) return <p className="error">{error}</p>;
  if (!groups.length) return <p className="muted">Loading modules…</p>;

  const visible = groups.filter((g) => round === "all" || g.round === round);

  return (
    <div>
      <div className="toolbar">
        <div>
          <div className="kicker">Learn</div>
          <h1>Modules</h1>
          <p className="lede">
            Work through each module like a course unit: short lessons with quick checks between them.
          </p>
        </div>
        <div className="row">
          <button className={`btn ${round === "all" ? "" : "ghost"}`} onClick={() => setRound("all")}>
            All
          </button>
          <button className={`btn ${round === 1 ? "" : "ghost"}`} onClick={() => setRound(1)}>
            Round 1
          </button>
          <button className={`btn ${round === 2 ? "" : "ghost"}`} onClick={() => setRound(2)}>
            Round 2
          </button>
        </div>
      </div>

      {visible.map((group) => (
        <section key={`${group.round}-${group.phase}`}>
          <div className="phase">
            Round {group.round} · {group.phase}
          </div>
          <div className="topic-list">
            {group.modules.map((mod) => (
              <Link className="topic" key={mod.slug} to={`/learn/${mod.slug}`}>
                <div className="seq">{String(mod.sequence).padStart(2, "0")}</div>
                <div>
                  <strong>{mod.title}</strong>
                  <div className="muted">{mod.summary}</div>
                  <div className="bar" style={{ marginTop: "0.45rem" }}>
                    <span style={{ width: `${mod.progress.percent}%` }} />
                  </div>
                </div>
                <span className="pill">{Math.round(mod.progress.percent)}%</span>
              </Link>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
