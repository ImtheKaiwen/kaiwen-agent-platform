# Prompt, standards and language customization

Bundled system prompts are immutable English resources with version `1`. The solo
prompt composes the shared professional base with the selected role. The compact
prompt is a separate pinned definition for constrained contexts.

User-facing language is independent from system prompt language. Set
`CodingConversationPreferences(language="tr")` for Turkish conversation; do not
translate identifiers, commands, requirements or evidence.

Hosts may register their own versioned prompts and standards. Conflicting definitions
under an existing ID/version are rejected. Standards describe quality, policies grant
authority, prompts guide behavior, and verifiers supply evidence; keep these four
boundaries separate.
