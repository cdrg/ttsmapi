## TTS.Monster API client python module
    
Provides python methods to access the TTS.Monster API, including 'generate'ing text-to-speech audio, retrieving 'user' information, and listing available 'voices'.
    
An attempt is made to avoid exceeding endpoint rate limits by tracking and rate limiting usage locally.

By default, the 'generate' endpoint user account character quota is enforced for convenience. Requests that would exceed the character quota will raise a TTSMAPIError. If enforcement is disabled, you will be subject to requests being rejected by TTS.Monster (free plan) or overage fees (paid plans).
    
The 'voice-cloning' endpoint is not currently implemented because of its beta status and complexity.

Public voice name + voice ID associations are in enums.VoiceIDEnum

https://docs.tts.monster/introduction