# English Reference

These notes explain how to use the templates as a working harness instead of a
loose pile of files.

## Internal Reference Notes

- [`method-map.md`](./method-map.md): map common long-running failure modes to
  the artifact or policy that addresses them first
- [`initializer-agent-playbook.md`](./initializer-agent-playbook.md): what the
  initializer should leave behind before feature work starts
- [`coding-agent-startup-flow.md`](./coding-agent-startup-flow.md): fixed
  session-start flow for later coding runs
- [`prompt-calibration.md`](./prompt-calibration.md): how to keep root
  instructions sharp without making them bloated and brittle
- [`document-budgets.md`](./document-budgets.md): word-count budgets per
  artifact and the reaudit pipeline that enforces them

## Primary Articles

This list is intentionally narrow. A harness means the execution system around
the model: the agent loop, tool execution, sandboxing, state, context,
verification, termination, orchestration, and observability. General prompt
engineering or broad agent-framework articles do not belong in the primary
list.

The original three articles remain the backbone of the course:

- [OpenAI: Harness engineering: leveraging Codex in an agent-first world](https://openai.com/index/harness-engineering/) (2026-02-11): repo-local context, custom linting, structural guardrails.
- [Anthropic: Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) (2025-11-26): initializer/coding agent, feature list, progress log, handoff across context windows.
- [Anthropic: Harness design for long-running application development](https://www.anthropic.com/engineering/harness-design-long-running-apps) (2026-03-24): planner/generator/evaluator roles, context resets, harness simplification.

Only a few highly relevant 2026 articles are added:

- [OpenAI: Unrolling the Codex agent loop](https://openai.com/index/unrolling-the-codex-agent-loop/) (2026-01-23): the Codex runtime harness, tool calls, context growth, loop termination.
- [Anthropic: Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) (2026-01-09): evaluating model and harness together; evaluation harnesses vs. agent harnesses.
- [LangChain: Improving Deep Agents with harness engineering](https://www.langchain.com/blog/improving-deep-agents-with-harness-engineering) (2026-02-17): holding the model fixed while improving prompts, tools, middleware, tracing, and self-verification — Top 30 to Top 5 on Terminal Bench 2.0.
- [Thoughtworks / Martin Fowler: Harness engineering for coding agent users](https://martinfowler.com/articles/harness-engineering.html) (2026-04-02): user harnesses as feedforward guides and feedback sensors, with deterministic and inferential controls.
- [Cursor: Continually improving our agent harness](https://cursor.com/blog/continually-improving-agent-harness) (2026-04-30): the harness as a continuously improved product — offline evals, online metrics, tool-error taxonomy, model-specific tuning, mid-chat model switching.

## 2026 Extended References

These are not core course sources, but they are useful when designing specific
harness modules. This section only keeps sources whose body directly covers the
agent loop, tool execution, context management, verification, sandboxing,
control layers, or regression governance. Pure agent products, platform
announcements, team case studies, and benchmarks are excluded.

- [OpenAI: Unlocking the Codex harness: how we built the App Server](https://openai.com/index/unlocking-the-codex-harness/) (2026-02-04): the harness as a reusable App Server protocol — thread lifecycle, resume, fork, diffs, client integrations.
- [OpenAI Developers: Run long horizon tasks with Codex](https://developers.openai.com/blog/run-long-horizon-tasks-with-codex) (2026-02-23): durable project memory, milestone validation, done-when examples.
- [OpenAI: The next evolution of the Agents SDK](https://openai.com/index/the-next-evolution-of-the-agents-sdk/) (2026-04-15): model-native harnesses, sandbox execution, file/command execution.
- [OpenAI: An open-source spec for Codex orchestration: Symphony](https://openai.com/index/open-source-codex-orchestration-symphony/) (2026-04-27): turning an issue tracker into a multi-agent control plane.
- [Anthropic: Building a C compiler with a team of parallel Claudes](https://www.anthropic.com/engineering/building-c-compiler) (2026-02-05): parallel agent teams, task locks, git sync, container isolation, autonomous loops.
- [Anthropic: Scaling Managed Agents: Decoupling the brain from the hands](https://www.anthropic.com/engineering/managed-agents) (2026-04-08): separating session, harness, and sandbox as swappable interfaces.
- [Anthropic: An update on recent Claude Code quality reports](https://www.anthropic.com/engineering/april-23-postmortem) (2026-04-23): reasoning effort and context pruning as harness changes needing regression governance.
- [LangChain: Context Management for Deep Agents](https://www.langchain.com/blog/context-management-for-deepagents) (2026-01-28): filesystem offloading, tool-call truncation, summarization, targeted evals.
- [LangChain: Tuning Deep Agents to Work Well with Different Models](https://www.langchain.com/blog/tuning-deep-agents-different-models) (2026-04-29): model-specific harness profiles for prompts, tools, middleware, subagents.
- [LangChain: Continual learning for AI agents](https://www.langchain.com/blog/continual-learning-for-ai-agents) (2026-04-05): splitting agent improvement into model, harness, and context layers via traces.
- [Microsoft: Agent Harness in Agent Framework](https://devblogs.microsoft.com/agent-framework/agent-harness-in-agent-framework/) (2026-03-12): shell/filesystem harnesses, approval flow, context compaction.
- [Google: Announcing ADK for Java 1.0.0](https://developers.googleblog.com/announcing-adk-for-java-100-building-the-future-of-ai-agents-in-java/) (2026-03-30): plugins, event compaction, HITL, session/memory services, A2A primitives.
- [GitHub: Automate repository tasks with GitHub Agentic Workflows](https://github.blog/ai-and-ml/automate-repository-tasks-with-github-agentic-workflows/) (2026-02-13): GitHub Actions as an agentic workflow runner — safe outputs, sandboxing, review.
- [AWS: AI agents in enterprises: Best practices with Amazon Bedrock AgentCore](https://aws.amazon.com/blogs/machine-learning/ai-agents-in-enterprises-best-practices-with-amazon-bedrock-agentcore/) (2026-02-03): harness layers across Runtime, Memory, Gateway, Identity/Policy, Observability, Evaluations.
- [Stripe: Minions: Stripe's one-shot, end-to-end coding agents](https://stripe.dev/blog/minions-stripes-one-shot-end-to-end-coding-agents) (2026-02-09) and [Part 2](https://stripe.dev/blog/minions-stripes-one-shot-end-to-end-coding-agents-part-2) (2026-02-19): devbox isolation, blueprint state machines, MCP tool curation, pre-push/CI feedback.
- [Cognition: What We Learned Building Cloud Agents](https://cognition.ai/blog/what-we-learned-building-cloud-agents) (2026-04-23): VM isolation, session snapshot/resume, governance, audit logging.
- [Cognition: Multi-Agents: What's Actually Working](https://cognition.ai/blog/multi-agents-working) (2026-04-22): generator-verifier loops, clean-context reviewers, manager-child coordination.
- [Replit: Decision-Time Guidance: Keeping Replit Agent Reliable](https://blog.replit.com/decision-time-guidance) (2026-01-20, updated 2026-01-23): a lightweight classifier injects guidance at the decision point instead of bloating the system prompt.
- [Vercel: How we made v0 an effective coding agent](https://vercel.com/blog/how-we-made-v0-an-effective-coding-agent) (2026-01-07): dynamic system prompts, a streaming rewrite layer, model-driven autofixers.
- [Vercel: Introducing deepsec](https://vercel.com/blog/introducing-deepsec-find-and-fix-vulnerabilities-in-your-code-base) (2026-05-04): a security-focused harness — scan, investigate, revalidate, export, refusal-checker steps.
- [Sourcegraph: CodeScaleBench](https://sourcegraph.com/blog/codescalebench-testing-coding-agents-on-large-codebases-and-multi-repo-software-engineering-tasks) (2026-03-03): MCP tool adoption, tool-use transcripts, verifier/reproducibility gates, prompt iteration.

Strictly 2025-only general references are excluded from the primary list. The
original 2025 Anthropic harness article remains because it is a foundation
source for the course.

## Suggested Reading Order

1. `method-map.md`
2. `initializer-agent-playbook.md`
3. `coding-agent-startup-flow.md`
4. `prompt-calibration.md`
5. OpenAI Harness engineering
6. Anthropic Effective harnesses
7. Anthropic Harness design for long-running application development
8. OpenAI Codex agent loop
9. Anthropic agent evals
10. LangChain Improving Deep Agents
11. Thoughtworks / Martin Fowler Harness engineering for coding agent users
12. Cursor Continually improving our agent harness
