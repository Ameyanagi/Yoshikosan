# Proposal: Implement SOP Workflow Application

## Why

This proposal implements the core workflow application for Yoshikosan, the industrial safety management system. The application digitizes Japan's "指差呼称" (pointing and calling) safety practice by providing a complete three-phase workflow:

1. **Phase 1 (Pre-Work)**: Workers upload SOPs and KY documents (text or images), which are analyzed by AI to create structured task lists with hazard identification
2. **Phase 2 (Working)**: Workers perform tasks with real-time AI verification triggered by "ヨシッ!" confirmations, receiving immediate feedback via voice and visual analysis
3. **Phase 3 (Post-Work)**: Supervisors review completed work logs with full audit trails for safety compliance

Currently, the project has:
- ✅ Basic infrastructure (Next.js frontend, FastAPI backend, PostgreSQL)
- ✅ AI service connectors (SambaNova for multimodal analysis, Hume AI for TTS)
- ✅ Authentication system (JWT + OAuth)
- ✅ Deployment configuration

**Missing**: The core domain logic, application workflows, database models, and user interfaces that implement the actual safety verification process.

## What Changes

This proposal introduces **8 new capabilities** spanning the full application stack:

### Backend Capabilities

1. **sop-management** - Domain models and services for SOP lifecycle
   - Upload SOPs (text/images)
   - AI-powered structuring via SambaNova
   - User review and editing
   - Task persistence

2. **safety-check-execution** - Real-time verification during work
   - Camera capture + audio recording
   - Multimodal AI analysis (image + audio + context)
   - Pass/fail determination with feedback
   - Progress tracking through task steps

3. **work-session-management** - Orchestrate complete workflows
   - Session lifecycle (start, pause, resume, complete)
   - State management across phases
   - Task step progression
   - Audio feedback via Hume AI

4. **audit-logging** - Immutable compliance records
   - Timestamp all safety checks
   - Store evidence (images, audio transcripts)
   - Supervisor approval workflow
   - Lock completed sessions

5. **database-schema** - PostgreSQL models
   - SOPs, Tasks, Steps, Hazards tables
   - WorkSessions, SafetyChecks tables
   - User/Supervisor relationships
   - Migration scripts (Alembic)

### Frontend Capabilities

6. **sop-upload-ui** - Phase 1 interface
   - File upload (images + text)
   - AI structuring progress
   - Task list review/editing
   - Confirmation workflow

7. **work-execution-ui** - Phase 2 interface
   - Camera viewfinder (top half)
   - Current task display (bottom half)
   - "ヨシッ!" button (mocked voice trigger)
   - Real-time feedback display
   - Audio playback (Hume AI)
   - Manual override controls

8. **audit-review-ui** - Phase 3 interface
   - Session history list
   - Detailed step-by-step logs
   - Image/audio evidence viewer
   - Supervisor approval controls
   - Export/download capabilities

### Cross-Cutting

- **API endpoints** for all backend services
- **TypeScript types** matching backend schemas
- **React Query** hooks for data fetching
- **Zustand** store for session state
- **Error boundaries** and user feedback

## Out of Scope

### MVP Exclusions
- Voice trigger with "ヨシッ!" keyword detection (use button instead)
- Offline-first architecture with sync (requires network)
- Wearable camera support (smartphone camera only)
- Advanced analytics dashboard (basic list view only)
- Multi-company/multi-site support (single tenant)
- Gamification features
- Mobile native apps (PWA/responsive web only)
- Automated notifications (email/SMS)

### Future Enhancements
- Advanced prompt engineering and model fine-tuning
- Circuit breakers and retry logic for AI services
- Performance optimization (caching, CDN)
- Internationalization beyond Japanese
- Integration with existing ERP/MES systems
- Real-time collaboration features

## Dependencies

### Existing Infrastructure
- AI service connectors (SambaNova, Hume AI) - already implemented
- Authentication system - already implemented
- Docker deployment configuration - already implemented
- Database infrastructure (PostgreSQL) - already set up

### New Dependencies (Backend)
```toml
# Already in pyproject.toml, no new packages needed
sqlalchemy = "^2.0"
alembic = "^1.13"
pydantic = "^2.5"
fastapi = "^0.115"
httpx = "^0.27"
```

### New Dependencies (Frontend)
```json
{
  "@tanstack/react-query": "^5.0.0",
  "zustand": "^4.4.0",
  "react-hook-form": "^7.48.0",
  "zod": "^3.22.0"
}
```

### External Services
- SambaNova API (multimodal LLM) - configured
- Hume AI API (empathic TTS) - configured
- Browser MediaDevices API (camera + microphone) - built-in

### Test Data Requirements
- Sample SOP documents (LEGO assembly example already exists)
- Sample images for verification testing
- Japanese audio samples for TTS testing

## Risk Assessment

### High Risk
- **AI accuracy**: LLM may misinterpret safety-critical steps
  - *Mitigation*: User review/edit step, manual override button
- **Latency**: AI response time > 3s degrades UX
  - *Mitigation*: Loading states, optimistic UI updates, timeout handling

### Medium Risk
- **Camera permissions**: Users may deny browser access
  - *Mitigation*: Clear permission prompts, fallback to file upload
- **Database migrations**: Schema changes may fail in production
  - *Mitigation*: Test migrations thoroughly, backup before deploy

### Low Risk
- **Japanese language support**: TTS/STT quality varies
  - *Mitigation*: Use proven Hume AI service, allow text fallback
- **Mobile responsiveness**: Complex UI on small screens
  - *Mitigation*: Mobile-first design, progressive enhancement

## Success Criteria

### Functional
- [ ] Users can upload SOP (text or image) and get structured task list
- [ ] Users can edit AI-generated tasks before starting work
- [ ] Users can execute tasks with "ヨシッ!" button triggering verification
- [ ] System captures photo + audio and returns AI feedback
- [ ] Voice feedback plays automatically via Hume AI
- [ ] Users can manually override AI decisions
- [ ] All checks are logged with timestamps and evidence
- [ ] Supervisors can review and approve completed sessions
- [ ] Approved sessions are immutable (locked)

### Non-Functional
- [ ] AI response time < 3 seconds (p95)
- [ ] Camera capture works on mobile browsers
- [ ] Audio playback works on iOS and Android
- [ ] Database handles 1000+ concurrent sessions
- [ ] UI is responsive on screens 320px+ wide
- [ ] All safety-critical operations are logged

### User Experience
- [ ] Phase 1 takes < 2 minutes (upload to start)
- [ ] Phase 2 feels seamless (no UI lag)
- [ ] Phase 3 shows clear audit trail
- [ ] Error messages are actionable
- [ ] Japanese UI is natural and professional
