# Speech pipeline contracts

`kaiwen_agent.speech` defines lightweight STT, TTS, transcript, and pipeline
contracts. It does not bundle a speech engine and does not replace the native
speech-to-speech Realtime Core.

`SpeechContext` carries trusted tenant, user, session, conversation, and trace
identity through every stage. `SpeechPipeline` refuses audio unless the host has set
`audio_processing_allowed`; this flag represents a host authorization decision, not
model input. The recognizer returns ordered `TranscriptSegment` records and only
final non-empty segments are sent to the injected text handler. The same context is
then passed to synthesis.

Input and output audio remain ephemeral bytes. `SpeechPipelineResult` contains only
the output audio and transcript; no store is called implicitly. If a product has
explicit recording consent and retention policy, it may persist audio through its
owner-scoped artifact service and expose only an `AudioArtifactRef`. Raw audio must
not be copied into durable conversation messages.

`FakeSpeechRecognizer` and `FakeSpeechSynthesizer` support provider-free contract
tests. Whisper, Piper, hosted speech APIs, VAD, codecs, and device capture are
optional host adapters. Native OpenAI Live and future native realtime providers
continue through `kaiwen_agent.realtime`, where final transcripts converge on the
same durable conversation identity.
