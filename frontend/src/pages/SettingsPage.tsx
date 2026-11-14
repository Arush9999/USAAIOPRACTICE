import { useEffect, useState } from "react";
import { api } from "../api";
import type { Settings } from "../types";

export function SettingsPage() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.settings().then(setSettings).catch((err: Error) => setError(err.message));
  }, []);

  async function save(event: React.FormEvent) {
    event.preventDefault();
    if (!settings) return;
    const next = await api.saveSettings(settings);
    setSettings(next);
    setSaved(true);
    document.documentElement.dataset.theme =
      next.theme === "system"
        ? window.matchMedia("(prefers-color-scheme: dark)").matches
          ? "dark"
          : "light"
        : next.theme;
  }

  if (error) return <p className="error">{error}</p>;
  if (!settings) return <p className="muted">Loading settings…</p>;

  return (
    <form onSubmit={save} className="card" style={{ maxWidth: 480 }}>
      <div className="kicker">Settings</div>
      <h1>Your profile</h1>
      <p className="muted">Update how your name and theme appear across the app.</p>
      <div className="field">
        <label htmlFor="name">Display name</label>
        <input
          id="name"
          value={settings.display_name}
          onChange={(event) => setSettings({ ...settings, display_name: event.target.value })}
        />
      </div>
      <div className="field">
        <label htmlFor="theme">Theme</label>
        <select
          id="theme"
          value={settings.theme}
          onChange={(event) => setSettings({ ...settings, theme: event.target.value as Settings["theme"] })}
        >
          <option value="system">System</option>
          <option value="light">Light</option>
          <option value="dark">Dark</option>
        </select>
      </div>
      <button className="btn" type="submit">
        Save
      </button>
      {saved && <p className="muted">Saved.</p>}
    </form>
  );
}
