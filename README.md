## TTS.Monster API client python module
    
Provides python methods to access the TTS.Monster API, including 'generate'ing text-to-speech audio, retrieving 'user' information, and listing available 'voices'.
    
An attempt is made to avoid exceeding endpoint rate limits by tracking and rate limiting usage locally.

By default, the 'generate' endpoint user account character quota is enforced for convenience. Requests that would exceed the character quota will raise a TTSMAPIError. If enforcement is disabled, you will be subject to requests being rejected by TTS.Monster (free plan) or overage fees (paid plans).
    
The 'voice-cloning' endpoint is not currently implemented because of its beta status and complexity.

Public voice name + voice ID associations are in enums.VoiceIDEnum

https://docs.tts.monster/introduction


## Links:

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/I2I7ROZFD)

[![patreon](https://github.com/user-attachments/assets/b7841f4d-5bcc-4642-a04c-2f22e5c48a24)](https://patreon.com/cdrpt)

[![discord](https://cdn.prod.website-files.com/6257adef93867e50d84d30e2/66e3d74e9607e61eeec9c91b_Logo.svg )](https://discord.gg/gRMjT5gVms)