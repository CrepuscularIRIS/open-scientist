# 代码地图（示例：SuperMimic）

| 环节 | 文件 | 常见的默认假设 |
|---|---|---|
| 执行器 / 延迟 | `envs/actions.py`（`process_actions`、`executed_raw`、`delay_weights`） | 哪些执行器效应在 WM 外处理、哪些留给 WM 学 |
| 环境 DR / 推扰 / 终止 | `envs/tracking_env_cfg.py`、`envs/mdp/events.py`、`envs/mdp/terminations.py` | 哪些扰动被删掉、哪些只按 episode 抽一次 |
| sim context | `envs/sim_context.py` | ξ 只含摩擦 / 偏置 / 质心 |
| 记录 / 回放 | `data/recorder.py`、`data/replay_buffer.py`（`window_mask`、`sample_windows`、`sample_starts`） | 窗口与起点的采样规则、标签对齐（已知终止标签错位一步） |
| WM | `world_model/world_model.py`（`window_loss`）、`state_spec.py`、`dynamics.py` | 回归目标里包含了什么 |
| 想象 | `imagination/rollout.py`（`imagine`）、`compiled.py` | 想象上下文 = 采集上下文、起点分布 |
| 目标 / critic | `imagination/objective.py`、`imagination/policy_trainer.py`、`policy/nets.py`（`Critic`） | 对上下文取期望的单一目标、critic 只看 ξ |
| 课程采样 | `envs/mdp/commands.py`（`_sample_frames`、`bin_return`） | 回报统计不分上下文 |
| 评测 / 部署 | `research/diag/e7_deploy.py`、`scripts/eval_*.py` | 部署时 WM 被丢掉、里程计只认脚 |

首例：IdeaSpark run `supermimic-robust-nominal-tradeoff` → `research/exp/A-38-tradeoff/ASSUMPTIONS.zh.md`（U1–U6）。
准入审计：A-39 执行器分解（oracle 施加力矩）、A-40 配对想象（Spearman 0.69）、U6 采样器（排除）。
