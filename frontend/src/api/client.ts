/**
 * Typed API client. One function per endpoint in docs/openapi.yaml.
 * Phase 5 uses auth/dashboard/ai-chat; the rest are pre-declared so Phase 6
 * only needs to build UI on top of these.
 */

import { apiRequest, buildAuthedUrl, fetchBlob } from "./http";
import type {
  AiChatRequest,
  AiChatResponse,
  AiSuggestion,
  AiValidationResult,
  AnswerInput,
  CanonicalOutput,
  CreateProcessRequest,
  Dashboard,
  FileUpload,
  ImportJob,
  ImportPreview,
  LoginRequest,
  LoginResponse,
  ModuleDetail,
  ProcessDefinition,
  ProcessSummary,
  ReviewTask,
  ReviewView,
  SaveAnswersResponse,
  StepDetail,
  Template,
} from "./types";

// ---- Auth -----------------------------------------------------------------

export function login(payload: LoginRequest): Promise<LoginResponse> {
  return apiRequest<LoginResponse>("/api/auth/login", { method: "POST", body: payload });
}

// ---- Definitions / processes ----------------------------------------------

export function getProcessDefinitions(): Promise<ProcessDefinition[]> {
  return apiRequest<ProcessDefinition[]>("/api/process-definitions");
}

export function getProcesses(): Promise<ProcessSummary[]> {
  return apiRequest<ProcessSummary[]>("/api/processes");
}

export function createProcess(payload: CreateProcessRequest): Promise<Dashboard> {
  return apiRequest<Dashboard>("/api/processes", { method: "POST", body: payload });
}

export function getDashboard(processInstanceId: string): Promise<Dashboard> {
  return apiRequest<Dashboard>(`/api/processes/${processInstanceId}`);
}

// ---- Modules / steps (Phase 6) --------------------------------------------

export function getModule(moduleInstanceId: string): Promise<ModuleDetail> {
  return apiRequest<ModuleDetail>(`/api/modules/${moduleInstanceId}`);
}

export function getStep(stepInstanceId: string): Promise<StepDetail> {
  return apiRequest<StepDetail>(`/api/steps/${stepInstanceId}`);
}

export function saveStepAnswers(
  stepInstanceId: string,
  answers: AnswerInput[],
): Promise<SaveAnswersResponse> {
  return apiRequest<SaveAnswersResponse>(`/api/steps/${stepInstanceId}/answers`, {
    method: "PUT",
    body: { answers },
  });
}

export function completeStep(stepInstanceId: string): Promise<StepDetail> {
  return apiRequest<StepDetail>(`/api/steps/${stepInstanceId}/complete`, { method: "POST" });
}

// ---- Uploads (Phase 6) ----------------------------------------------------

export function uploadFile(
  file: File,
  stepInstanceId: string,
  questionKey: string,
): Promise<FileUpload> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("stepInstanceId", stepInstanceId);
  formData.append("questionKey", questionKey);
  return apiRequest<FileUpload>("/api/uploads", { method: "POST", formData });
}

export function uploadDownloadUrl(uploadId: string): string {
  return buildAuthedUrl(`/api/uploads/${uploadId}/download`);
}

/**
 * Trigger a browser download for an auth-protected file. A plain anchor cannot
 * carry the Bearer token, so we fetch the bytes (token injected by the http
 * layer) and save the resulting blob via a temporary object URL.
 */
export async function downloadAuthedFile(path: string, fallbackName: string): Promise<void> {
  const { blob, fileName } = await fetchBlob(path);
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = fileName ?? fallbackName;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export function downloadUpload(uploadId: string, fallbackName: string): Promise<void> {
  return downloadAuthedFile(`/api/uploads/${uploadId}/download`, fallbackName);
}

export function downloadTemplateFile(templateKey: string, fallbackName: string): Promise<void> {
  return downloadAuthedFile(`/api/templates/${templateKey}/file`, fallbackName);
}

// ---- Templates (Phase 6) --------------------------------------------------

export function getTemplate(templateKey: string, moduleInstanceId?: string): Promise<Template> {
  return apiRequest<Template>(`/api/templates/${templateKey}`, { query: { moduleInstanceId } });
}

export function templateFileUrl(templateKey: string): string {
  return buildAuthedUrl(`/api/templates/${templateKey}/file`);
}

// ---- AI -------------------------------------------------------------------

export function aiChat(payload: AiChatRequest): Promise<AiChatResponse> {
  return apiRequest<AiChatResponse>("/api/ai/chat", { method: "POST", body: payload });
}

export function aiSuggest(stepInstanceId?: string, questionKey?: string): Promise<AiSuggestion> {
  return apiRequest<AiSuggestion>("/api/ai/suggest", {
    method: "POST",
    body: { stepInstanceId, questionKey },
  });
}

export function aiValidate(stepInstanceId: string): Promise<AiValidationResult> {
  return apiRequest<AiValidationResult>("/api/ai/validate", {
    method: "POST",
    body: { stepInstanceId },
  });
}

export function aiAnalyzeDocument(uploadId: string): Promise<AiSuggestion> {
  return apiRequest<AiSuggestion>("/api/ai/analyze-document", {
    method: "POST",
    body: { uploadId },
  });
}

// ---- Review (Phase 6) -----------------------------------------------------

export function getReviewTasks(): Promise<ReviewTask[]> {
  return apiRequest<ReviewTask[]>("/api/review/tasks");
}

export function getReviewModule(moduleInstanceId: string): Promise<ReviewView> {
  return apiRequest<ReviewView>(`/api/review/modules/${moduleInstanceId}`);
}

export function approveModule(moduleInstanceId: string): Promise<ModuleDetail> {
  return apiRequest<ModuleDetail>(`/api/review/modules/${moduleInstanceId}/approve`, {
    method: "POST",
  });
}

export function requestModuleChanges(
  moduleInstanceId: string,
  notes?: string,
): Promise<ModuleDetail> {
  return apiRequest<ModuleDetail>(`/api/review/modules/${moduleInstanceId}/request-changes`, {
    method: "POST",
    body: { notes },
  });
}

export function patchReviewAnswer(answerId: string, value: unknown): Promise<import("./types").Answer> {
  return apiRequest<import("./types").Answer>(`/api/review/answers/${answerId}`, {
    method: "PATCH",
    body: { value },
  });
}

// ---- Import (Phase 6) -----------------------------------------------------

export function generateCanonical(moduleInstanceId: string): Promise<CanonicalOutput> {
  return apiRequest<CanonicalOutput>(`/api/modules/${moduleInstanceId}/canonical`, {
    method: "POST",
  });
}

export function getImportPreview(
  moduleInstanceId: string,
  targetSystem = "dpms_v1",
): Promise<ImportPreview> {
  return apiRequest<ImportPreview>(`/api/modules/${moduleInstanceId}/import-preview`, {
    method: "POST",
    body: { targetSystem },
  });
}

export function createImportJob(
  moduleInstanceId: string,
  targetSystem = "dpms_v1",
): Promise<ImportJob> {
  return apiRequest<ImportJob>("/api/import-jobs", {
    method: "POST",
    body: { moduleInstanceId, targetSystem },
  });
}

export function runImportJob(id: string): Promise<ImportJob> {
  return apiRequest<ImportJob>(`/api/import-jobs/${id}/run`, { method: "POST" });
}
