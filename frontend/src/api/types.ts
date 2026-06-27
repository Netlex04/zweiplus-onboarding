/**
 * TypeScript types mirroring the API contract (docs/openapi.yaml).
 * DTOs are camelCase. These types cover Phase 5 (auth, dashboard, ai chat)
 * and pre-declare the Phase 6 surface (modules, steps, uploads, templates,
 * ai suggest/validate/analyze, review, import) so Phase 6 only builds UI.
 */

export type Role = "customer" | "reviewer" | "admin";

export type ModuleStatus =
  | "locked"
  | "available"
  | "not_started"
  | "in_progress"
  | "waiting_customer"
  | "waiting_zweiplus"
  | "ai_check_pending"
  | "backend_validation_failed"
  | "completed"
  | "import_ready"
  | "imported";

export type StepStatus =
  | "not_started"
  | "in_progress"
  | "incomplete"
  | "complete"
  | "ai_check_pending"
  | "backend_validation_failed"
  | "review_pending"
  | "completed";

export type ImportStatus =
  | "not_prepared"
  | "mapping_ready"
  | "validated"
  | "approved"
  | "importing"
  | "imported"
  | "import_failed"
  | "reimport_required";

export type QuestionType = "single_select" | "multi_select" | "text" | "file_upload";

export type AnswerSource = "user" | "ai" | "document" | "manual";

// ---- Auth -----------------------------------------------------------------

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  role: Role;
  name: string;
}

// ---- Process definitions / summaries --------------------------------------

export interface ModuleDefinitionSummary {
  key: string;
  name: string;
  shortDescription: string;
  responsibleRole: string;
  estimatedEffort: string;
}

export interface ProcessDefinition {
  key: string;
  name: string;
  description: string;
  modules: ModuleDefinitionSummary[];
}

export interface ProcessSummary {
  id: string;
  customerName: string;
  customerOrg?: string;
  status: string;
}

export interface CreateProcessRequest {
  processDefKey: string;
  customerName: string;
  customerOrg?: string;
}

// ---- Dashboard ------------------------------------------------------------

export interface ModuleCard {
  moduleInstanceId: string;
  key: string;
  name: string;
  explainer: string;
  status: ModuleStatus;
  progress: number;
  responsibleRole: string;
  estimatedEffort: string;
  locked: boolean;
  unlockHint?: string | null;
  nextAction?: string | null;
}

export interface Dashboard {
  processInstanceId: string;
  customerName: string;
  overallProgress: number;
  modules: ModuleCard[];
}

// ---- Templates ------------------------------------------------------------

export interface Template {
  key: string;
  type: "email" | "file" | "text";
  title?: string;
  subject?: string;
  body?: string;
  fileName?: string;
  fileType?: string;
}

// ---- Modules / steps / questions / answers (Phase 6) ----------------------

export interface ModuleIntro {
  goal?: string;
  why?: string;
  who?: string;
  effort?: string;
  explainer?: string;
}

export interface ModuleStepSummary {
  stepInstanceId: string;
  key: string;
  title: string;
  status: StepStatus;
}

export interface ModuleDetail {
  moduleInstanceId: string;
  key: string;
  name: string;
  intro: ModuleIntro;
  status: ModuleStatus;
  progress: number;
  steps: ModuleStepSummary[];
  templates: Template[];
}

export interface Answer {
  id: string;
  questionKey: string;
  value: unknown;
  source?: AnswerSource;
  aiSuggested?: boolean;
  updatedAt?: string;
}

export interface Question {
  key: string;
  label: string;
  description?: string;
  type: QuestionType;
  required: boolean;
  options?: string[];
  helpText?: string;
  aiHelpEnabled?: boolean;
  visible: boolean;
  answer?: Answer;
}

export interface StepDetail {
  stepInstanceId: string;
  title: string;
  description?: string;
  status: StepStatus;
  templates: Template[];
  questions: Question[];
}

export interface AnswerInput {
  questionKey: string;
  value: unknown;
}

export interface BackendValidationError {
  questionKey: string;
  code: string;
  message: string;
}

export interface BackendValidationWarning {
  questionKey: string;
  message: string;
}

export interface BackendValidationResult {
  passed: boolean;
  errors: BackendValidationError[];
  warnings: BackendValidationWarning[];
}

export interface SaveAnswersResponse {
  stepStatus: StepStatus;
  validation: BackendValidationResult;
}

// ---- Uploads --------------------------------------------------------------

export interface FileUpload {
  id: string;
  originalName: string;
  contentType: string;
  sizeBytes: number;
  questionKey: string;
}

// ---- AI -------------------------------------------------------------------

export type AiChatContext = "dashboard" | "module" | "step" | "question";

export interface AiChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface AiChatRequest {
  context: AiChatContext;
  contextRef?: string;
  message: string;
  history?: AiChatMessage[];
}

export interface AiChatResponse {
  reply: string;
}

export interface AiSuggestion {
  id: string;
  suggestionType?: string;
  moduleId?: string;
  stepId?: string;
  questionId?: string;
  proposedValue?: unknown;
  confidence?: number;
  requiresReview?: boolean;
  openQuestions?: string[];
  sourceUploadId?: string;
}

export interface AiValidationCheck {
  question: string;
  ok: boolean;
  note?: string;
}

export interface AiValidationResult {
  id: string;
  passed: boolean;
  checks: AiValidationCheck[];
  issues: string[];
}

// ---- Review ---------------------------------------------------------------

export type ReviewTaskStatus = "open" | "in_review" | "changes_requested" | "approved";

export interface ReviewTask {
  id: string;
  moduleInstanceId: string;
  customerName: string;
  moduleName: string;
  status: ReviewTaskStatus;
  notes?: string | null;
}

export interface ReviewViewQuestion {
  key: string;
  label: string;
  answer?: Answer;
  aiSuggestions: AiSuggestion[];
}

export interface ReviewViewStep {
  stepInstanceId: string;
  title: string;
  questions: ReviewViewQuestion[];
  aiValidation?: AiValidationResult;
  backendValidation?: BackendValidationResult;
}

export interface ReviewView {
  moduleInstanceId: string;
  moduleName: string;
  moduleStatus: ModuleStatus;
  customerName?: string | null;
  reviewStatus?: ReviewTaskStatus | null;
  steps: ReviewViewStep[];
}

// ---- Import ---------------------------------------------------------------

export interface CanonicalOutput {
  moduleInstanceId: string;
  schemaKey: string;
  data: Record<string, unknown>;
}

export interface ImportPreview {
  targetSystem: string;
  mappedObjects: Record<string, unknown>[];
  unmappedFields: string[];
  warnings: string[];
  errors: string[];
}

export interface ImportJob {
  id: string;
  moduleInstanceId: string;
  targetSystem: string;
  status: ImportStatus;
  preview?: ImportPreview;
  errors: string[];
}

// ---- Error ----------------------------------------------------------------

export interface ApiErrorBody {
  error: string;
  detail: string;
}
