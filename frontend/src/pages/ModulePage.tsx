import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";
import { Markdown } from "../Markdown";
import type { AttemptResult, CheckStep, LearnModuleDetail, LearnStep } from "../types";

function firstOpenIndex(steps: LearnStep[]) {
  const idx = steps.findIndex((step) =>
    step.type === "content" ? !step.completed : !step.completed_correct,
  );
  return idx === -1 ? 0 : idx;
}

export function ModulePage() {
  const { slug } = useParams();
  const [module, setModule] = useState<LearnModuleDetail | null>(null);
  const [stepIndex, setStepIndex] = useState(0);
  const [choice, setChoice] = useState("");
  const [result, setResult] = useState<AttemptResult | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function reload(keepIndex?: number) {
    if (!slug) return;
    const data = await api.learnModule(slug);
    setModule(data);
    setStepIndex(keepIndex ?? firstOpenIndex(data.steps));
    setChoice("");
    setResult(null);
  }

  useEffect(() => {
    if (!slug) return;
    reload().catch((err: Error) => setError(err.message));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slug]);

  const step = module?.steps[stepIndex] ?? null;
  const progress = useMemo(() => {
    if (!module?.steps.length) return 0;
    return Math.round(((stepIndex + 1) / module.steps.length) * 100);
  }, [module, stepIndex]);

  async function markContentDone() {
    if (!step || step.type !== "content") return;
    setBusy(true);
    try {
      await api.completeLesson(step.slug);
      if (module && stepIndex < module.steps.length - 1) {
        await reload(stepIndex + 1);
      } else {
        await reload(stepIndex);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save progress");
    } finally {
      setBusy(false);
    }
  }

  async function submitCheck() {
    if (!step || step.type !== "check" || !choice) return;
    setBusy(true);
    try {
      const outcome = await api.learnCheck(step.public_id, choice);
      setResult(outcome);
      if (outcome.is_correct && module && stepIndex < module.steps.length - 1) {
        // stay on step so they can read explanation, then Next
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not grade check");
    } finally {
      setBusy(false);
    }
  }

  if (error) return <p className="error">{error}</p>;
  if (!module || !step) return <p className="muted">Loading module…</p>;

  return (
    <div>
      <div className="kicker">
        <Link to="/learn">Learn</Link> · Round {module.round} · {module.phase}
      </div>
      <div className="toolbar">
        <div>
          <h1>{module.title}</h1>
          <p className="muted">
            Step {stepIndex + 1} of {module.steps.length}
          </p>
        </div>
        <span className="pill">{progress}%</span>
      </div>
      <div className="bar" style={{ marginBottom: "1rem" }}>
        <span style={{ width: `${progress}%` }} />
      </div>

      <div className="card ka-step">
        {step.type === "content" ? (
          <>
            <div className="pill">Lesson</div>
            <h2>{step.title}</h2>
            <Markdown>{step.body_markdown}</Markdown>
            <div className="row" style={{ marginTop: "1.2rem" }}>
              <button className="btn ghost" disabled={stepIndex === 0} onClick={() => setStepIndex((i) => i - 1)}>
                Back
              </button>
              <button
                className="btn"
                disabled={busy}
                onClick={async () => {
                  if (step.completed) {
                    setStepIndex((i) => Math.min(i + 1, module.steps.length - 1));
                    return;
                  }
                  await markContentDone();
                }}
              >
                {step.completed ? "Continue" : "Got it — continue"}
              </button>
            </div>
          </>
        ) : (
          <CheckPanel
            step={step}
            choice={choice}
            setChoice={setChoice}
            result={result}
            busy={busy}
            onSubmit={submitCheck}
            onBack={() => {
              setResult(null);
              setChoice("");
              setStepIndex((i) => Math.max(0, i - 1));
            }}
            onNext={async () => {
              setResult(null);
              setChoice("");
              if (stepIndex < module.steps.length - 1) setStepIndex((i) => i + 1);
              else await reload(stepIndex);
            }}
          />
        )}
      </div>
    </div>
  );
}

function CheckPanel({
  step,
  choice,
  setChoice,
  result,
  busy,
  onSubmit,
  onBack,
  onNext,
}: {
  step: CheckStep;
  choice: string;
  setChoice: (v: string) => void;
  result: AttemptResult | null;
  busy: boolean;
  onSubmit: () => void;
  onBack: () => void;
  onNext: () => void;
}) {
  return (
    <>
      <div className="row">
        <span className="pill">Quick check</span>
        <span className="pill">{step.difficulty}</span>
        <span className="pill">{step.subtopic_slug}</span>
        {step.completed_correct && <span className="pill good">Mastered</span>}
      </div>
      <div style={{ marginTop: "0.8rem" }}>
        <Markdown>{step.prompt}</Markdown>
      </div>
      <div className="choices">
        {step.choices.map((option) => (
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
        <button className="btn ghost" onClick={onBack}>
          Back
        </button>
        {!result ? (
          <button className="btn" disabled={!choice || busy} onClick={onSubmit}>
            Check answer
          </button>
        ) : (
          <button className="btn" onClick={onNext}>
            {result.is_correct ? "Next" : "Try another step"}
          </button>
        )}
      </div>
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
    </>
  );
}
