import { createClient, type SupabaseClient } from '@supabase/supabase-js';

const url = import.meta.env.VITE_SUPABASE_URL || '';
const key = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY || '';

// Capture the recovery marker before the SDK consumes the URL fragment.
// Reuse the already allowed confirmation callback; no wildcard redirect is needed.
export const isPasswordRecovery =
  new URL(window.location.href).searchParams.get('auth') === 'recovery' ||
  new URLSearchParams(window.location.hash.slice(1)).get('type') === 'recovery';

export const supabase: SupabaseClient | null =
  url && key ? createClient(url, key) : null;
