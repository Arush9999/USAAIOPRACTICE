import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import { Markdown } from "../Markdown";
import type { AttemptResult, PracticeTopic, Question } from "../types";

type Diff = "easy" | "medium" | "hard";

export function PracticePage() {
  const [topics, setTopics] = useState<PracticeTopic[]>([]);
  const [topic, setTopic] = useState("");
  const [subtopic, setSubtopic] = useState("");
  const [difficulty, setDifficulty] = useState<Diff>("medium");
  const [question, setQuestion] = useState<Question | null>(null);
  const [choice, setChoice] = useState("");
  const [hintsUsed, setHintsUsed] = useState(0);
  const [result, setResult] = useState<AttemptResult | null>(null);
  const [error, setError] = useState("");
  const [started, setStarted] = useState(false);

  useEffect(() => {
    api
      .practiceMeta()
      .then((data) => {
        setTopics(data.topics);
        if (data.topics[0]) setTopic(data.topics[0].slug);
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  const selected = useMemo(() => topics.find((t) => t.slug === topic), [topics, topic]);
  const subtopics = selected?.subtopics ?? [];
  const counts = useMemo(() => {
    if (!selected) return { easy: 0, medium: 0, hard: 0 };
    if (subtopic) {
      const row = selected.subtopics.find((s) => s.slug === subtopic);
      return row?.counts ?? { easy: 0, medium: 0, hard: 0 };
    }
    return selected.subtopics.reduce(
      (acc, s) => ({
        easy: acc.easy + s.counts.easy,
        medium: acc.medium + s.counts.medium,
        hard: acc.hard + s.counts.hard,
      }),
      { easy: 0, medium: 0, hard: 0 },
    );
  }, [selected, subtopic]);

  async function loadQuestion() {
    if (!topic) return;
    setResult(null);
    setChoice("");
    setHintsUsed(0);
    setError("");
    try {
      const next = await api.nextQuestion(topic, difficulty, subtopic || undefined);
      setQuestion(next);
      setStarted(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No questions");
      setQuestion(null);
    }
  }

  async function submit() {
    if (!question || !choice) return;
    const outcome = await api.attempt(question.public_id, choice, hintsUsed);
    setResult(outcome);
  }

  if (!topics.length && !error) return <p className="muted">Loading practice…</p>;

  return (
    <div>
      <div className="kicker">Practice</div>
      <h1>Drill by topic and difficulty</h1>
      <p className="lede">Unofficial practice questions. Pick a module, optional subtopic, and difficulty.</p>

      <div className="card" style={{ marginBottom: "1rem" }}>
        <div className="grid two">
          <div className="field">
            <label htmlFor="topic">Topic</label>
            <select
              id="topic"
              value={topic}
              onChange={(e) => {
                setTopic(e.target.value);
                setSubtopic("");
                setStarted(false);
                setQuestion(null);
              }}
            >
              {topics.map((t) => (
                <option key={t.slug} value={t.slug}>
                  R{t.round} · {t.title}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label htmlFor="subtopic">Subtopic (optional)</label>
            <select
              id="subtopic"
              value={subtopic}
              onChange={(e) => {
                setSubtopic(e.target.value);
                setStarted(false);
                setQuestion(null);
              }}
            >
              <option value="">All subtopics</option>
              {subtopics.map((s) => (
                <option key={s.slug} value={s.slug}>
                  {s.title} ({s.counts.easy}/{s.counts.medium}/{s.counts.hard})
                </option>
              ))}
            </select>
          </div>
        </div>
        <div className="row" style={{ marginBottom: "0.8rem" }}>
          {(["easy", "medium", "hard"] as Diff[]).map((level) => (
            <button
              key={level}
              className={`btn ${difficulty === level ? "" : "ghost"}`}
              onClick={() => {
                setDifficulty(level);
                setStarted(false);
                setQuestion(null);
              }}
            >
              {level} · {counts[level]}
            </button>
          ))}
        </div>
        <button className="btn" onClick={loadQuestion} disabled={!topic || counts[difficulty] === 0}>
          {started ? "New question" : "Start"}
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      {question && (
        <div className="card">
          <div className="row">
            <span className="pill">{question.public_id}</span>
            <span className="pill">{question.difficulty}</span>
            {question.subtopic_slug && <span className="pill">{question.subtopic_slug}</span>}
            <span className="pill">{question.practice_label}</span>
          </div>
          <div style={{ marginTop: "0.9rem" }}>
            <Markdown>{question.prompt}</Markdown>
          </div>
          <div className="choices">
            {question.choices.map((option) => (
              <button
                key={option}
                className={`choice${choice === option ? " selected" : ""}`}
                disabled={Boolean(result)}
                onClick={() => setChoice(option)}
              >
                <Markdown>{option}</Markdown>
              </button>
            ))}
          </div>
          <div className="row">
            <button className="btn" onClick={submit} disabled={!choice || Boolean(result)}>
              Submit
            </button>
            <button
              className="btn ghost"
              onClick={() => setHintsUsed((n) => Math.min(n + 1, question.hints.length))}
              disabled={hintsUsed >= question.hints.length || Boolean(result)}
            >
              Hint {hintsUsed}/{question.hints.length}
            </button>
            {result && (
              <button className="btn ghost" onClick={loadQuestion}>
                Next
              </button>
            )}
          </div>
          {question.hints.slice(0, hintsUsed).map((hint, i) => (
            <p key={hint} className="muted">
              Hint {i + 1}: {hint}
            </p>
          ))}
          {result && (
            <div className={`feedback ${result.is_correct ? "ok" : "no"}`}>
              <strong>{result.is_correct ? "Correct" : "Not yet"}</strong>
              {!result.is_correct && (
                <p>
                  Expected: <code>{result.correct_answer}</code>
                </p>
              )}
              <Markdown>{result.explanation}</Markdown>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
