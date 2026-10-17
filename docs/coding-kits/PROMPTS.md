# Coding prompt resources

The Coding Kit ships English UTF-8 prompt resources under
`kaiwen_agent.kits.coding.prompts`. They are opt-in and are not imported by the
package root. Technical system instructions remain English; user-facing replies use
typed runtime language preferences and support Turkish.

`install_coding_prompts()` installs immutable `PromptDefinition` records and is
idempotent only when an existing `id@version` definition is identical. Conflicting
content at an existing version is rejected.

Role definitions compose the full `coding.base@1` contract with one role-specific
resource. `coding.compact@1` is a standalone concise contract for constrained local
models and must not be stacked with every full role prompt.

| Prompt | SHA-256 |
|---|---|
| `coding.base@1` | `efe384b512244cbea2e726a7772cd8937c530e0493a677e9b6a652d2db4537f3` |
| `coding.solo@1` | `0b42ada254be1aac76e817fd6b38ab547fdb137708f3fbc9a6c1db992e1d4644` |
| `coding.lead@1` | `045567aadf9540cf9ac322058e444b8d8377b7fd26961c9e664850f8c18d2791` |
| `coding.planner@1` | `de1c359458f5e5cd5c86176fb19f2af3492287af658f47cf0ca693dfed87c595` |
| `coding.architect@1` | `cecca5201e757a186ec462ee632a199f1c91f7b3002c17d2f7d03f4484489527` |
| `coding.designer@1` | `bd825457ca72c5bb018df78f6aebb95acb22ce14d77645e67cb713b02475058a` |
| `coding.coder@1` | `5bf866f473b18e84037afd8030960e328f398aed04fb0edf703f86784e2a6a0f` |
| `coding.tester@1` | `3a818020437e6ca01e7db13c77fe3f98fc0171aa39e8e9c65594cabc6b0fafe9` |
| `coding.reviewer@1` | `050d633f70885181d93cb62c83730759613c411827faf37e4ae08dae19dfcfff` |
| `coding.devops@1` | `5fe37ca5693335c143bdd1529c822ce3869a09cfdf40dd8e83103db732c54f43` |
| `coding.compact@1` | `ccdc18c314b372627509a18e5540a3211724bd887bb13d6edddd0c6099146a56` |

These checksums describe the composed `PromptDefinition.template`, not only the raw
role resource. Any meaningful prompt edit requires a new prompt version and updated
regression evidence.

Prompt text provides behavior guidance only. It cannot grant a tool, select an
approval, weaken policy, remove a standard, or satisfy a verifier.
