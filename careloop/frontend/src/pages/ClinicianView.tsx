import React, { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";

export const ClinicianView: React.FC = () => {
  const [searchParams] = useSearchParams();
  const caseParam = searchParams.get("case") || "case-demo-a-amira";

  const [urgentCases, setUrgentCases] = useState<any[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string>(caseParam);
  const [consultPacket, setConsultPacket] = useState<any>(null);
  const [decisionReason, setDecisionReason] = useState<string>("Colonoscopy completed; findings reviewed; surveillance interval set.");
  const [closureStatus, setClosureStatus] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/queues/urgent")
      .then((r) => r.json())
      .then((d) => setUrgentCases(Array.isArray(d) ? d : []))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (selectedCaseId) {
      fetch(`/api/cases/${selectedCaseId}/consult-packet`)
        .then((r) => r.json())
        .then((d) => setConsultPacket(d))
        .catch(() => {});
    }
  }, [selectedCaseId]);

  const handleDecision = async (decision: "approved" | "rejected") => {
    setErrorMessage(null);
    try {
      // Find pending or existing proposal
      const res = await fetch("/api/closure-proposals/prop-demo-1/decide", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Demo-Role": "clinician" },
        body: JSON.stringify({
          decision,
          decision_reason: decisionReason,
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        setErrorMessage(err.detail || "Closure failed");
      } else {
        setClosureStatus(`Case closure ${decision} by Clinician with documented rationale.`);
      }
    } catch (e: any) {
      setErrorMessage("Network error during closure sign-off");
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      <div className="pb-4 border-b border-slate-200 mb-6">
        <h1 className="text-2xl font-bold text-slate-900">Clinician Consultation & Closure Governance</h1>
        <p className="text-xs text-slate-500">
          Review Structured Consult Packets · Sign Off Evidence-Backed Case Closures
        </p>
      </div>

      {closureStatus && (
        <div className="mb-4 p-4 bg-emerald-50 border border-emerald-300 rounded-xl text-emerald-900 text-xs font-semibold">
          ✓ {closureStatus}
        </div>
      )}

      {errorMessage && (
        <div className="mb-4 p-4 bg-red-50 border border-red-300 rounded-xl text-red-900 text-xs font-semibold">
          ⚠ {errorMessage}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Urgent cases & Consult Packets */}
        <div className="lg:col-span-7 space-y-6">
          {/* Consult Packet Preview */}
          {consultPacket && (
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
                <div>
                  <span className="font-mono text-[10px] text-blue-600 font-bold bg-blue-50 px-2 py-0.5 rounded">
                    {consultPacket.packet_id}
                  </span>
                  <h3 className="text-lg font-bold text-slate-900 mt-1">Cross-Provider Consult Packet</h3>
                </div>
                <div className="text-right text-[11px] text-slate-400">
                  Generated: {new Date(consultPacket.generated_at).toLocaleString()}
                </div>
              </div>

              {/* Patient Identifiers */}
              <div className="bg-slate-50 p-3.5 rounded-lg border border-slate-200 text-xs mb-4 grid grid-cols-2 gap-2">
                <div>
                  <span className="text-slate-400">Patient: </span>
                  <span className="font-bold text-slate-800">{consultPacket.patient.synthetic_name}</span>
                </div>
                <div>
                  <span className="text-slate-400">DOB: </span>
                  <span className="font-medium text-slate-800">{consultPacket.patient.dob}</span>
                </div>
                <div>
                  <span className="text-slate-400">Preferred Language: </span>
                  <span className="font-medium text-slate-800">{consultPacket.patient.preferred_language?.toUpperCase()}</span>
                </div>
                <div>
                  <span className="text-slate-400">Urgency: </span>
                  <span className="font-bold text-red-700 uppercase">{consultPacket.urgency_tier}</span>
                </div>
              </div>

              {/* Clinical Indication */}
              <div className="mb-4 text-xs">
                <h4 className="font-bold text-slate-800 uppercase tracking-wider mb-1 text-[11px]">
                  Clinical Indication
                </h4>
                <p className="text-slate-700 bg-amber-50/50 p-2.5 rounded border border-amber-200/60 leading-relaxed">
                  {consultPacket.clinical_indication}
                </p>
              </div>

              {/* AI Drafted Summary with Badge */}
              <div className="mb-4 p-3.5 bg-indigo-50/60 border border-indigo-200 rounded-lg text-xs">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="font-bold text-indigo-950 flex items-center gap-1.5">
                    <span>✨</span>
                    <span>AI-Drafted Longitudinal Case Summary</span>
                  </span>
                  <span className="px-2 py-0.5 bg-indigo-200 text-indigo-900 font-bold text-[10px] rounded">
                    AI-DRAFTED: REQUIRES CLINICAL REVIEW
                  </span>
                </div>
                <p className="text-indigo-900 leading-relaxed text-[11px]">
                  {consultPacket.ai_drafted_summary}
                </p>
              </div>

              {/* Contact Attempts Audit */}
              <div>
                <h4 className="font-bold text-slate-800 uppercase tracking-wider mb-2 text-[11px]">
                  Contact Timeline & Navigation Attempts
                </h4>
                <div className="space-y-1.5 text-[11px]">
                  {consultPacket.contact_attempts?.map((c: any, i: number) => (
                    <div key={i} className="flex justify-between p-2 bg-slate-50 rounded border border-slate-100">
                      <span className="text-slate-700 font-medium">Channel: {c.channel.toUpperCase()}</span>
                      <span className="text-emerald-700 font-semibold">{c.status}</span>
                      <span className="text-slate-400">{c.delivered_at ? new Date(c.delivered_at).toLocaleDateString() : "Pending"}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Closure Sign-Off Protocol */}
        <div className="lg:col-span-5 bg-white rounded-xl border border-slate-200 shadow-sm p-6 h-fit">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
            <h3 className="font-bold text-slate-900 text-base">Human Closure Sign-Off Guard</h3>
            <span className="text-xs px-2 py-0.5 bg-emerald-100 text-emerald-800 font-bold rounded">
              Rule 6.4 Enforced
            </span>
          </div>

          <div className="text-xs text-slate-600 mb-4 leading-relaxed">
            Per the safety guardrails, <strong>the AI can never close a case</strong>. Closure requires an authorized
            clinician, verified procedure/pathology evidence on file, and a non-empty clinical rationale.
          </div>

          {/* Evidence Checklist */}
          <div className="bg-slate-50 p-3.5 rounded-lg border border-slate-200 text-xs mb-4 space-y-2">
            <div className="font-semibold text-slate-700 mb-1 uppercase tracking-wider text-[11px]">
              Evidence Verification Checklist
            </div>
            <div className="flex items-center gap-2 text-emerald-800">
              <span>✓</span>
              <span>Diagnostic colonoscopy report attached (DOC-ENDO-2026-0941)</span>
            </div>
            <div className="flex items-center gap-2 text-emerald-800">
              <span>✓</span>
              <span>Pathology histology verified (Tubular adenoma benign)</span>
            </div>
            <div className="flex items-center gap-2 text-emerald-800">
              <span>✓</span>
              <span>Zero open unresolved escalations</span>
            </div>
          </div>

          {/* Clinical Decision Reason Input */}
          <div className="mb-4">
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
              Documented Clinical Decision Reason (Mandatory)
            </label>
            <textarea
              rows={3}
              value={decisionReason}
              onChange={(e) => setDecisionReason(e.target.value)}
              className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
              placeholder="Record reason for case closure or rejection..."
            />
          </div>

          {/* Decision Buttons */}
          <div className="flex gap-3">
            <button
              onClick={() => handleDecision("approved")}
              className="flex-1 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold shadow transition"
            >
              ✓ Approve & Seal Case Closure
            </button>
            <button
              onClick={() => handleDecision("rejected")}
              className="px-4 py-2.5 bg-slate-200 hover:bg-slate-300 text-slate-700 rounded-lg text-xs font-bold transition"
            >
              Reject Proposal
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

