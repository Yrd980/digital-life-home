#!/usr/bin/env node
import { Codex } from "@openai/codex-sdk";
import fs from "node:fs";
import path from "node:path";

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const stateDir = path.join(root, "state");
const threadFile = path.join(stateDir, "codex-thread.json");
fs.mkdirSync(stateDir, { recursive: true });

const args = process.argv.slice(2);
const jsonMode = args.includes("--json");
const newMode = args.includes("--new");
const prompt = args.filter((a) => a !== "--json" && a !== "--new").join(" ").trim();
if (!prompt) {
  console.error("Usage: codex-thread [--new] [--json] <prompt>");
  process.exit(2);
}

function loadThreadId() {
  if (newMode || !fs.existsSync(threadFile)) return null;
  try { return JSON.parse(fs.readFileSync(threadFile, "utf8")).threadId || null; }
  catch { return null; }
}

const options = {
  model: "gpt-5.5",
  workingDirectory: root,
  skipGitRepoCheck: true,
  sandboxMode: "danger-full-access",
  approvalPolicy: "never",
  modelReasoningEffort: "medium",
  networkAccessEnabled: true,
};

const codex = new Codex({
  config: {
    model_provider: "OpenAI",
    model: "gpt-5.5",
    approval_policy: "never",
    sandbox_mode: "danger-full-access",
  },
});
const threadId = loadThreadId();
const thread = threadId ? codex.resumeThread(threadId, options) : codex.startThread(options);
const turn = await thread.run(prompt);
const id = thread.id || thread._id || threadId;
if (id) {
  fs.writeFileSync(threadFile, JSON.stringify({ threadId: id, updatedAt: new Date().toISOString() }, null, 2));
}
const result = {
  threadId: id,
  finalResponse: turn.finalResponse || "",
  items: turn.items || [],
};
if (jsonMode) {
  console.log(JSON.stringify(result, null, 2));
} else {
  if (id) console.log(`thread: ${id}`);
  console.log(result.finalResponse || "");
}
