# SOP Management Spec

## ADDED Requirements

### Requirement: SOP Upload and Storage
**ID**: sop-mgmt-001
**Priority**: High
**Category**: Core Feature

The system SHALL allow users to upload SOP documents in text or image format.

#### Scenario: Upload text-based SOP
**Given** a user is authenticated
**And** they have a text-based SOP document
**When** they upload the SOP via the API
**Then** the text content is extracted and stored
**And** a unique SOP ID is generated
**And** the SOP is associated with the uploading user

**Implementation**:
- Endpoint: `POST /api/v1/sops`
- Request: multipart/form-data with `files[]` (text/images) and `text` (optional)
- Module: `src/api/v1/endpoints/sop.py`
- Use case: `src/application/sop/upload_sop.py`
- Validation: File size < 10MB, formats: .txt, .jpg, .jpeg, .png

---

#### Scenario: Upload image-based SOP
**Given** a user is authenticated
**And** they have SOP images (photos of documents)
**And** optionally have accompanying text
**When** they upload images and/or text via the API
**Then** the images are stored in file storage
**And** image URLs are saved to the SOP record
**And** both text and images are passed to the AI for structuring

**Implementation**:
- Support multiple file uploads in single request
- Accept both `files[]` (images) and `text` field in multipart form
- Store images in `storage/sops/{sop_id}/`
- Save file paths in database
- No separate OCR step - vision model handles text in images

---

### Requirement: AI-Powered SOP Structuring
**ID**: sop-mgmt-002
**Priority**: High
**Category**: AI Integration

The system SHALL use SambaNova LLM to automatically structure SOPs into tasks, steps, and hazards.

#### Scenario: Structure SOP from text and images
**Given** an uploaded SOP with text and/or images
**When** the structuring use case is invoked
**Then** the SambaNova multimodal API is called with both text and images
**And** the model extracts text from images and combines with provided text
**And** the response conforms to the SOP JSON schema
**And** tasks, steps, and hazards are extracted
**And** the structured data is persisted to the database

**Implementation**:
- Use case: `src/application/sop/structure_sop.py`
- AI client: `src/infrastructure/ai_services/sambanova.py` (already exists)
- Call `analyze_image()` with prompt, images, and response schema
- Include user-provided text in the prompt if available
- No separate OCR step - vision model reads text from images directly
- Prompt template: `STRUCTURE_SOP_PROMPT` (see design.md)
- Response schema: JSON with tasks array containing steps and hazards

---

#### Scenario: Handle AI structuring errors
**Given** the SambaNova API returns an error or invalid JSON
**When** the structuring use case is invoked
**Then** an appropriate error is logged
**And** the user receives a clear error message
**And** the SOP remains in "pending" status
**And** the user can retry or manually structure

**Implementation**:
- Error handling in use case
- Status field on SOP: `pending`, `structured`, `failed`
- Retry mechanism (user-initiated)

---

### Requirement: SOP Review and Editing
**ID**: sop-mgmt-003
**Priority**: High
**Category**: User Control

The system SHALL allow users to review and edit AI-structured SOPs before use.

#### Scenario: User reviews structured SOP
**Given** an SOP has been automatically structured
**When** the user retrieves the SOP details
**Then** all tasks, steps, and hazards are displayed
**And** the user can see which parts were AI-generated

**Implementation**:
- Endpoint: `GET /api/v1/sops/{id}`
- Response includes full SOP hierarchy
- Metadata: `structured_at`, `ai_confidence` (if available)

---

#### Scenario: User edits SOP tasks
**Given** a user is viewing a structured SOP
**When** they modify task titles, descriptions, or order
**And** they submit the changes
**Then** the SOP is updated in the database
**And** the `updated_at` timestamp is refreshed
**And** the changes are validated for completeness

**Implementation**:
- Endpoint: `PUT /api/v1/sops/{id}`
- Request body: Full SOP JSON
- Validation: At least one task, all tasks have steps
- Domain method: `SOP.validate()` returns error list

---

#### Scenario: User adds or removes hazards
**Given** a user is editing an SOP step
**When** they add a new hazard with severity and mitigation
**Or** they remove an existing hazard
**Then** the hazard list for that step is updated
**And** the changes are persisted

**Implementation**:
- Hazard is a child entity of Step
- Cascade updates when step is modified
- Validation: Severity must be one of: low, medium, high, critical

---

### Requirement: SOP Listing and Retrieval
**ID**: sop-mgmt-004
**Priority**: Medium
**Category**: User Experience

The system SHALL provide endpoints to list and retrieve SOPs for a user.

#### Scenario: List user's SOPs
**Given** a user is authenticated
**When** they request their SOP list
**Then** all SOPs created by the user are returned
**And** deleted SOPs are excluded
**And** SOPs are ordered by most recently updated first

**Implementation**:
- Endpoint: `GET /api/v1/sops`
- Query params: `limit` (default 20), `offset` (default 0)
- Filter: `deleted_at IS NULL`
- Order: `updated_at DESC`

---

#### Scenario: Retrieve SOP details
**Given** a user owns an SOP
**When** they request the SOP by ID
**Then** the full SOP with all tasks, steps, and hazards is returned
**And** the response includes metadata (created_at, updated_at)

**Implementation**:
- Endpoint: `GET /api/v1/sops/{id}`
- Authorization: Only owner can access
- Eager loading: Load tasks → steps → hazards in single query

---

### Requirement: SOP Soft Deletion
**ID**: sop-mgmt-005
**Priority**: Low
**Category**: Data Management

The system SHALL support soft deletion of SOPs to maintain audit history.

#### Scenario: User deletes an SOP
**Given** a user owns an SOP
**And** the SOP is not currently in use by an active work session
**When** they delete the SOP
**Then** the `deleted_at` timestamp is set
**And** the SOP is no longer visible in list endpoints
**And** the SOP data remains in the database

**Implementation**:
- Endpoint: `DELETE /api/v1/sops/{id}`
- Check: No active work sessions reference this SOP
- Update: Set `deleted_at = NOW()`
- Queries: Add `WHERE deleted_at IS NULL` filter

---

### Requirement: SOP Domain Model
**ID**: sop-mgmt-006
**Priority**: High
**Category**: Domain Design

The system SHALL implement the SOP aggregate using DDD principles.

#### Scenario: Create SOP aggregate
**Given** structured SOP data from AI or user input
**When** the SOP entity is instantiated
**Then** the aggregate contains SOP → Tasks → Steps → Hazards
**And** all child entities have correct parent references
**And** business rules are enforced

**Implementation**:
- Module: `src/domain/sop/entities.py`
- Classes: `SOP` (aggregate root), `Task`, `Step`, `Hazard`
- Business rules:
  - SOP must have title
  - SOP must have at least one task
  - Task must have at least one step
  - Hazard severity must be valid enum value
- Methods: `add_task()`, `Task.add_step()`, `Step.add_hazard()`, `validate()`

---

### Requirement: SOP Repository
**ID**: sop-mgmt-007
**Priority**: High
**Category**: Infrastructure

The system SHALL provide a repository for SOP persistence and retrieval.

#### Scenario: Save SOP to database
**Given** an SOP aggregate with tasks and steps
**When** the repository save method is called
**Then** the SOP and all child entities are persisted
**And** foreign key relationships are maintained
**And** a transaction ensures atomicity

**Implementation**:
- Protocol: `src/domain/sop/repositories.py` - `SOPRepository` (interface)
- Implementation: `src/infrastructure/database/repositories/sop_repository.py` - `SQLAlchemySOPRepository`
- Methods: `save(sop: SOP) -> None`, `get_by_id(id: UUID) -> SOP | None`, `list_by_user(user_id: UUID) -> list[SOP]`, `delete(id: UUID) -> None`
- Transaction: Use SQLAlchemy session with commit/rollback

---

#### Scenario: Retrieve SOP with all children
**Given** an SOP exists in the database
**When** the repository get method is called
**Then** the SOP aggregate is reconstructed with all tasks, steps, and hazards
**And** the data matches the database state

**Implementation**:
- Use SQLAlchemy eager loading: `joinedload(SOP.tasks).joinedload(Task.steps).joinedload(Step.hazards)`
- Map ORM models to domain entities
- Return `None` if not found or deleted

---

### Requirement: SOP-to-Domain Mapping
**ID**: sop-mgmt-008
**Priority**: High
**Category**: Infrastructure

The system SHALL map between SQLAlchemy ORM models and domain entities.

#### Scenario: Map ORM model to domain entity
**Given** an SQLAlchemy SOP model instance
**When** the mapper converts it to a domain entity
**Then** all fields are correctly mapped
**And** child relationships are recursively converted
**And** the result is a valid SOP aggregate

**Implementation**:
- Module: `src/infrastructure/database/mappers/sop_mapper.py`
- Function: `to_domain(model: SOPModel) -> SOP`
- Function: `to_model(entity: SOP) -> SOPModel`
- Handle nullable fields and relationships

---

### Requirement: SOP JSON Schema Definition
**ID**: sop-mgmt-009
**Priority**: High
**Category**: AI Integration

The system SHALL define a strict JSON schema for SOP structuring responses.

#### Scenario: Validate AI response against schema
**Given** the SambaNova API returns a JSON response
**When** the response is parsed
**Then** it conforms to the SOP schema
**And** all required fields are present
**And** field types match the schema

**Implementation**:
- Module: `src/domain/sop/schemas.py`
- Schema format: JSON Schema Draft 7
- Required fields: `title`, `tasks` array
- Task schema: `title` required, `steps` array required
- Step schema: `description` required, `hazards` array optional
- Hazard schema: `description` and `severity` required
- Use with SambaNova `response_schema` parameter for strict mode
