# Local Development

**Status:** PLANNED — **no setup is possible yet.** No toolchain, dependency manifest, lockfile, scripts or code exist. This document is a placeholder with the structure that will be filled when the first implementation phase selects tools (DEC-015). **Do not invent or paste setup commands that do not exist.** · **Related:** [CONFIGURATION](CONFIGURATION.md), [CODING_STANDARDS](../engineering/CODING_STANDARDS.md), [TESTING_STRATEGY](../engineering/TESTING_STRATEGY.md)

## What is true today
- The repository contains documentation, directory placeholders and templates only.
- A Git repository exists in this folder with **no commits** (not created by the foundation run, which made no Git changes). Committing is the owner's decision.
- There is nothing to build, run, or test.

## To be completed when Phase 1 starts
| Section | Content to add | Blocked by |
|---|---|---|
| Prerequisites | OS support, language runtime versions, system packages | DEC-015 |
| Environment creation | Exact, tested commands to create the environment from the lockfile | DEC-015 |
| Configuration | Copy `.env.example` → `.env`, required variables (see [CONFIGURATION](CONFIGURATION.md)) | Phase 1 config module |
| Data | How to obtain **permitted** data; where it lives (`data/`, git-ignored); synthetic sample generation | DEC-002, Phase 0 |
| Running pipelines | Job entry points, order of stages | Phase 1–2 |
| Running tests | Commands per suite (unit / integration / scientific), expected duration | Phase 1 |
| Lint / type / format | Tool commands | DEC-015 |
| Backend API | Start command, port, docs URL | DEC-007, Phase 5 |
| Frontend | Install/build/dev commands | DEC-008, Phase 5 |
| Troubleshooting | Known issues and fixes | As discovered |

## Rules for this document
Every command listed must have been run successfully by the author on a clean checkout, with the date and OS recorded next to it. Remove instructions that stop working. Never include credentials.

## Acceptance
A new contributor can set up and run the test suite using only this document (verified by a clean-machine walkthrough at the Phase 1 gate).
