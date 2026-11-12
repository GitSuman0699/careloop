import React, { useState, useEffect } from "react";
import { AIActionLog, AuditLogItem } from "../types";

export const GovernanceView: React.FC = () => {
  const [aiActions, setAiActions] = useState<AIActionLog[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>([]);
  const [verifyCaseId, setVerifyCaseId] = useState<string>("case-demo-a-amira");
  const [verifyResult, setVerifyResult] = useState<any>(null);

  useEffect(() => {
    fetch("/api/ai-actions", { headers: { "X-Demo-Role": "auditor" } })
      .then((r) => r.json())
      .then((d) => setAiActions(Array.isArray(d) ? d : []))
      .catch(() => {});

    fetch("/api/audit", { headers: { "X-Demo-Role": "auditor" } })
      .then((r) => r.json())
      .then((d) => setAuditLogs(Array.isArray(d) ? d : []))
      .catch(() => {});
  }, []);

  const handleVerifyChain = async () => {
    try {
      const res = await fetch(`/api/cases/${verifyCaseId}/verify-chain`);
      const data = await res.json();
      setVerifyResult(data);
    } catch {
      setVerifyResult({ is_valid: false, error: "Network verification error" });
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      <div className="pb-4 border-b border-slate-200 mb-6">
        <h1 className="text-2xl font-bold text-slate-900">Responsible AI & Governance Center</h1>
        <p className="text-xs text-slate-500">
          AI Action Audit Trail · Rule-Based Guardrail Verdicts · Tamper-Evident Hash Chain Inspector
        </p>
      </div>

      {/* Cryptographic Hash Chain Inspector */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm mb-8">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
          <div>
            <h3 className="font-bold text-slate-900 text-sm uppercase tracking-wider">
              Cryptographic Hash-Chain Verification Inspector
            </h3>
            <p className="text-xs text-slate-500">
              SHA-256 canonical JSON event chains verify tamper-evidence for every case ledger
            </p>
          </div>
          <span className="font-mono text-xs bg-slate-100 px-2 py-1 rounded text-slate-700">
            SHA-256 Immutable Ledger
          </span>
        </div>

        <div className="flex flex-wrap gap-3 items-center mb-4">
          <input
            type="text"
            value={verifyCaseId}
            onChange={(e) => setVerifyCaseId(e.target.value)}
            className="border border-slate-300 rounded-lg px-3 py-2 text-xs font-mono w-72"
            placeholder="Enter case ID to verify..."
          />
          <button
            onClick={handleVerifyChain}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold transition shadow-sm"
          >
            Verify Event Chain Integrity
          </button>
        </div>

        {verifyResult && (
          <div
            className={`p-4 rounded-xl text-xs font-mono ${
              verifyResult.is_valid
                ? "bg-emerald-50 border border-emerald-300 text-emerald-950"
                : "bg-red-50 border border-red-300 text-red-950"
            }`}
          >
            <div className="font-bold mb-1 flex items-center gap-2">
              <span>{verifyResult.is_valid ? "✓ CHAIN INTACT: VERIFICATION PASSED" : "✗ CHAIN COMPROMISED: INTEGRITY ERROR"}</span>
            </div>
            <div>Case ID: {verifyResult.case_id}</div>
            <div>Verified Events: {verifyResult.event_count}</div>
            <div>Timestamp: {verifyResult.verified_at}</div>
            {verifyResult.error && <div className="text-red-700 font-bold mt-1">Error: {verifyResult.error}</div>}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mb-8">
        {/* AI Action Log & Guardrail Interceptions */}
        <div className="lg:col-span-7 bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="pb-3 border-b border-slate-100 mb-4">
            <h3 className="font-bold text-slate-900 text-sm uppercase tracking-wider">
              AI Action Log & Guardrail Blocks ({aiActions.length})
            </h3>
            <p className="text-xs text-slate-500">
              Every LLM call is intercepted by validators; banned terms/diagnosis disclosures trigger fallback
            </p>
          </div>

          <div className="space-y-3 max-h-[500px] overflow-y-auto">
            {aiActions.map((a) => (
              <div
                key={a.id}
                className={`p-3.5 rounded-lg border text-xs ${
                  a.validator_passed
                    ? "bg-slate-50/70 border-slate-200"
                    : "bg-red-50/60 border-red-200 text-red-950"
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="font-mono font-bold text-slate-800">{a.kind}</span>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      a.validator_passed
                        ? "bg-emerald-100 text-emerald-800"
                        : "bg-red-100 text-red-800"
                    }`}
                  >
                    {a.validator_passed ? "VALIDATOR PASSED" : "BLOCKED: FALLBACK USED"}
                  </span>
                </div>
                <div className="text-slate-600 bg-white p-2 rounded border border-slate-100 text-[11px] mb-1 font-mono">
                  {a.output_text}
                </div>
                <div className="text-[10px] text-slate-400 flex justify-between font-mono">
                  <span>Model: {a.model}</span>
                  <span>Fallback Active: {a.fallback_used ? "YES" : "NO"}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Immutable Audit Log */}
        <div className="lg:col-span-5 bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="pb-3 border-b border-slate-100 mb-4">
            <h3 className="font-bold text-slate-900 text-sm uppercase tracking-wider">
              Immutable Access Audit Trail
            </h3>
            <p className="text-xs text-slate-500">
              Every read of patient records writes an immutable audit record
            </p>
          </div>

          <div className="space-y-2 max-h-[500px] overflow-y-auto text-xs">
            {auditLogs.map((log) => (
              <div key={log.id} className="p-2.5 bg-slate-50 rounded-lg border border-slate-100 text-[11px]">
                <div className="flex justify-between items-center mb-0.5">
                  <span className="font-bold text-slate-800">{log.role.toUpperCase()}</span>
                  <span className="text-[10px] text-slate-400">{new Date(log.at).toLocaleTimeString()}</span>
                </div>
                <div className="text-slate-600">{log.purpose}</div>
                <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                  Action: {log.action} · Target: {log.object_type}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
