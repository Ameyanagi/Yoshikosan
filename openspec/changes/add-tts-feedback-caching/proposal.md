# Proposal: Add TTS Feedback Caching

## Why

Currently, when workers receive AI feedback during safety checks, the system:
1. Generates feedback text in Japanese
2. Synthesizes voice feedback using Hume AI TTS (empathic voice)
3. **Returns audio bytes only once** - no persistence
4. Audio is played and then discarded

**Problem**: Workers cannot replay feedback audio. If they miss the audio or want to hear it again, there's no way to do so. This is particularly important for:
- Noisy industrial environments where audio might be missed
- New workers who need to hear instructions multiple times
- Training scenarios where feedback replay is valuable
- First-time task execution where guidance is most critical

**User Request**:
- "Keep the latest voice for each session and make that repeatable"
- "I also want to do [TTS feedback] on the first task"

This proposal adds:
1. **Audio persistence**: Store TTS feedback audio in the database
2. **Session-level caching**: Keep the latest feedback audio for replay
3. **First task guidance**: Proactively generate welcome/instruction audio when starting first task

## What Changes

This proposal introduces **1 new capability**:

### tts-feedback-caching

**Backend Changes:**
- Add `feedback_audio_url` column to `safety_checks` table (nullable TEXT)
- Store TTS audio files in `/tmp/audio/feedback/{session_id}/{check_id}.mp3`
- Update `ExecuteSafetyCheckUseCase` to save audio to file and store URL
- Add `GET /api/v1/checks/{id}/audio` endpoint to serve audio files
- Add `latest_feedback_audio_url` field to session responses for quick replay access

**Frontend Changes:**
- Display replay button for each check's audio feedback
- Add "Replay Last Feedback" button in session execution UI
- Show audio player with controls instead of auto-play-only
- Pre-generate welcome audio when starting first task
- Cache audio URLs in session state for offline replay

**Database Changes:**
- Migration to add `feedback_audio_url` to `safety_checks` table
- Directory structure for organized audio file storage

## Out of Scope

### MVP Exclusions
- Audio file cleanup/archival (manual cleanup only for MVP)
- CDN integration for audio serving (local file serving only)
- Audio format conversion (MP3 only)
- Audio compression/optimization (use Hume AI default quality)
- Multiple audio language support (Japanese only)
- Voice customization (use default Hume AI voice)

### Future Enhancements
- Automatic audio file cleanup after session approval (retain only metadata)
- Cloud storage integration (S3, GCS) for production scale
- Audio transcription display alongside replay
- Waveform visualization
- Playback speed controls

## Dependencies

### Existing Infrastructure
- Hume AI TTS service - already integrated
- File system storage - `/tmp` directory available
- Database schema - `safety_checks` table exists
- Session repository - already implemented

### New Dependencies
**None** - uses existing infrastructure

### Modified Components
- `safety_checks` table schema (add column)
- `ExecuteSafetyCheckUseCase` (save audio files)
- Safety check endpoints (serve audio)
- Session execution UI (replay controls)

## Risk Assessment

### High Risk
- **File system I/O failures**: Disk full, permission errors
  - *Mitigation*: Graceful fallback - save check without audio URL if file write fails
  - *Mitigation*: Use `/tmp` (cleaned on reboot) to prevent disk fill
- **Audio file size**: 10-30 seconds of audio = ~100-300KB per check
  - *Mitigation*: Document cleanup procedures for production
  - *Mitigation*: Consider retention policy (delete after 30 days)

### Medium Risk
- **Concurrent access**: Multiple workers accessing same audio file
  - *Mitigation*: Read-only file access, file system handles concurrency
- **File path injection**: Malicious check ID in audio URL
  - *Mitigation*: Validate UUID format, use parameterized paths

### Low Risk
- **Audio playback compatibility**: Browser audio support varies
  - *Mitigation*: Use MP3 (universally supported), provide download fallback

## Success Criteria

### Functional
- [x] Audio feedback is saved to file system with unique filename
- [x] `feedback_audio_url` is stored in database for each check
- [x] Workers can replay any check's audio feedback
- [x] Latest feedback audio is easily accessible in session UI
- [x] First task generates welcome/instruction audio automatically
- [x] Audio files persist across session lifecycle
- [x] Approved sessions retain audio URLs for audit trail

### Non-Functional
- [x] Audio file write does not block check execution (async)
- [x] File serving latency < 500ms
- [x] Audio files are organized by session for easy management
- [x] Graceful degradation if audio save fails (check still succeeds)

### User Experience
- [x] Replay button appears next to each check
- [x] Audio player has play/pause/volume controls
- [x] Latest feedback is highlighted for quick access
- [x] First task shows "Welcome" audio with task overview
- [x] No audio auto-play on replay (user-initiated only)

## Implementation Approach

### Phase 1: Backend Foundation
1. Database migration: Add `feedback_audio_url` column
2. Update `ExecuteSafetyCheckUseCase` to save audio files
3. Add audio file path utilities
4. Add `GET /api/v1/checks/{id}/audio` endpoint

### Phase 2: Session Enhancement
1. Update session responses to include `latest_feedback_audio_url`
2. Add first task welcome audio generation
3. Update check schemas with audio URL field

### Phase 3: Frontend Integration
1. Add audio replay button component
2. Update session UI with replay controls
3. Add "Latest Feedback" replay button
4. Display welcome audio on first task start

### Phase 4: Testing & Validation
1. Test audio file persistence across session lifecycle
2. Test concurrent audio access
3. Test graceful degradation on file write failure
4. Validate audio playback on mobile browsers
