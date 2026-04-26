# Submission Readiness Checklist

Gate 5 makes the repo judge-readable and Space-ready, but it is not a final submitted Space until the public HF link and video/blog/deck link are added.

## OpenEnv Checklist

- [x] OpenEnv-style `reset`, `step`, `state`
- [x] CPU-runnable environment
- [x] `openenv.yaml` present
- [x] reserved action names avoided
- [x] client/server separation preserved
- [x] deterministic verifier reward

## Space Checklist

- [x] FastAPI app entrypoint: `server.app:app`
- [x] Dockerfile runs Uvicorn on CPU
- [x] minimal runtime dependencies in `requirements.txt`
- [x] `scripts/space_smoke.py` passes locally
- [ ] Hugging Face Space URL added to README
- [ ] Space remote smoke checked after deployment

## Tests Checklist

- [x] `python -m pytest`
- [x] `python scripts/self_check.py`
- [x] hidden leakage tests
- [x] certificate gating tests
- [x] anti-hacking tests

## Baselines Checklist

- [x] `random_patch`
- [x] `explanation_only`
- [x] `block_everything`
- [x] `visible_overfit`
- [x] `oracle_correct_solver_for_sanity`
- [x] `outputs/results.csv`
- [x] `outputs/baseline_summary.json`

## Training Checklist

- [x] single-turn JSON dataset generator
- [x] GRPO scaffold
- [x] deterministic verifier reward function
- [x] sampled generation logging
- [x] metrics logging
- [x] SFT warmstart scaffold
- [x] CPU smoke modes
- [ ] real GRPO run
- [ ] real trained-model evaluation

## Plots Checklist

- [x] baseline scores plot
- [x] certificate success rate plot
- [x] hidden regression pass rate plot
- [x] valid preservation rate plot
- [ ] real training reward curve after real run
- [ ] real training loss curve after real run, if available
- [ ] real baseline vs trained plot after real run

## README Checklist

- [x] project identity and tagline
- [x] not-observability-dashboard statement
- [x] environment loop
- [x] observation/action/reward explanation
- [x] hidden regression explanation
- [x] anti-hacking explanation
- [x] MVP families
- [x] baseline results
- [x] training status without overclaiming
- [x] run commands
- [x] safety scope
- [ ] HF Space link
- [ ] video/blog/slides link
- [ ] real training plots after real run

## Video / Blog Checklist

- [ ] under-2-minute video or mini-blog/deck created
- [ ] linked from README
- [ ] stale retrieval demo emphasized
- [ ] no fake training claims

## Safety Checklist

- [x] symbolic traces only
- [x] no real credentials
- [x] no live APIs
- [x] no shell execution in environment
- [x] no browser automation
- [x] no exploit payloads
- [x] no offensive tooling
- [x] no real user data
- [x] bounded verification disclaimer

## Final No-Fake-Results Checklist

- [x] baseline plots are baseline-only
- [x] smoke metrics are labeled as smoke
- [x] no trained improvement claimed
- [x] no fake reward curve
- [x] no fake trained-vs-baseline plot
- [ ] real GRPO logs added before any trained claim

## Current Status

Ready for local review and HF Space deployment smoke. Not ready to claim trained improvement until a real GRPO run is completed and logged.
