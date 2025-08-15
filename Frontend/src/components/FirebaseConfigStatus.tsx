"use client";
import { firebaseConfigDiagnostics } from '@/lib/firebaseClient';

export default function FirebaseConfigStatus() {
  const diag = firebaseConfigDiagnostics();
  if (!diag.missing.length) return null;
  return (
    <div className="p-3 mb-4 text-xs rounded border border-red-300 bg-red-50 text-red-700 whitespace-pre-wrap">
      <strong>Firebase config missing: {diag.missing.join(', ')}</strong>\n
      Env keys seen:\n{diag.envReport.join('\n')}
    </div>
  );
}
