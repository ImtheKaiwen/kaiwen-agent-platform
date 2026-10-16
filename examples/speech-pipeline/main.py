import asyncio

from kaiwen_agent.speech import (
    AudioFormat,
    FakeSpeechRecognizer,
    FakeSpeechSynthesizer,
    SpeechContext,
    SpeechPipeline,
    SpeechRecognitionConfig,
    SpeechSynthesisConfig,
    user_segment,
)


class EchoTextHandler:
    async def respond(self, text: str, *, context: SpeechContext) -> str:
        return f"{context.conversation_id}: {text}"


async def main() -> None:
    audio_format = AudioFormat(mime_type="audio/pcm", sample_rate_hz=24_000)
    pipeline = SpeechPipeline(
        recognizer=FakeSpeechRecognizer((user_segment("Merhaba", language="tr"),)),
        text_handler=EchoTextHandler(),
        synthesizer=FakeSpeechSynthesizer(),
    )
    result = await pipeline.process(
        b"ephemeral-audio",
        context=SpeechContext(
            tenant_id="tenant-1",
            user_id="user-1",
            session_id="session-1",
            conversation_id="conversation-1",
            trace_id="trace-1",
            audio_processing_allowed=True,
        ),
        recognition=SpeechRecognitionConfig(audio_format=audio_format, language="tr"),
        synthesis=SpeechSynthesisConfig(audio_format=audio_format, language="tr"),
    )
    print(result.response_text)


if __name__ == "__main__":
    asyncio.run(main())
