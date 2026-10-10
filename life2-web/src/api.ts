const API_BASE = import.meta.env.VITE_LIFE2_API_BASE ?? "http://localhost:8100";

export type AwarenessOption = {
  value: string;
  label: string;
};

export type AwarenessQuestion = {
  id: string;
  domain: string;
  title?: string;
  title_single?: string;
  title_couple?: string;
  options: AwarenessOption[];
  action_catalog_id: string;
};

export async function fetchAwarenessQuestions(): Promise<AwarenessQuestion[]> {
  const response = await fetch(`${API_BASE}/v1/awareness/questions`);
  if (!response.ok) throw new Error("질문을 불러오지 못했습니다.");
  const body = await response.json();
  return body.questions;
}
