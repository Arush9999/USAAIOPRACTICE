type Pyodide = {
  loadPackage: (packages: string | string[]) => Promise<void>;
  runPythonAsync: (code: string, options?: { globals?: unknown }) => Promise<unknown>;
  globals: { get: (name: string) => unknown };
  setStdout: (options: { batched: (text: string) => void }) => void;
  setStderr: (options: { batched: (text: string) => void }) => void;
};

declare global {
  interface Window {
    loadPyodide?: (options: { indexURL: string }) => Promise<Pyodide>;
  }
}

const INDEX_URL = "https://cdn.jsdelivr.net/pyodide/v0.27.7/full/";
let instance: Promise<Pyodide> | null = null;

function loadScript() {
  if (window.loadPyodide) return Promise.resolve();
  return new Promise<void>((resolve, reject) => {
    const existing = document.querySelector<HTMLScriptElement>('script[data-pyodide="true"]');
    if (existing) {
      existing.addEventListener("load", () => resolve(), { once: true });
      existing.addEventListener("error", () => reject(new Error("Could not load Pyodide")), { once: true });
      return;
    }
    const script = document.createElement("script");
    script.src = `${INDEX_URL}pyodide.js`;
    script.dataset.pyodide = "true";
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Could not load Pyodide"));
    document.head.appendChild(script);
  });
}

async function getPyodide() {
  if (!instance) {
    instance = (async () => {
      await loadScript();
      const pyodide = await window.loadPyodide!({ indexURL: INDEX_URL });
      await pyodide.loadPackage("numpy");
      return pyodide;
    })();
  }
  return instance;
}

export async function runPython(code: string, testsCode: string) {
  const pyodide = await getPyodide();
  const stdout: string[] = [];
  const stderr: string[] = [];
  pyodide.setStdout({ batched: (text) => stdout.push(text) });
  pyodide.setStderr({ batched: (text) => stderr.push(text) });
  try {
    await pyodide.runPythonAsync(`${code}\n\n${testsCode}`);
    return { passed: true, output: [...stdout, ...stderr, "All tests passed."].join("\n") };
  } catch (error) {
    return {
      passed: false,
      output: [...stdout, ...stderr, error instanceof Error ? error.message : String(error)].filter(Boolean).join("\n"),
    };
  }
}
