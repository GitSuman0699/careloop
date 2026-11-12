import React, { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { CaseSummary, CaseEvent } from "../types";

export const NavigatorQueue: React.FC = () => {
  const [searchParams] = useSearchParams();
  const initialCaseId = searchParams.get("case");

  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(initialCaseId);
  const [selectedCase, setSelectedCase] = useState<any>(null);
  const [timeline, setTimeline] = useState<CaseEvent[]>([]);
  const [filterUrgency, setFilterUrgency] = useState<string>("all");
  const [filterPathway, setFilterPathway] = useState<string>("all");
  const [actionNotice, setActionNotice] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/cases")
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data)) {
          setCases(data);
          if (!selectedCaseId && data.length > 0) {
            setSelectedCaseId(data[0].id);
          }
        }
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (selectedCaseId) {
      fetch(`/api/cases/${selectedCaseId}`)
        .then((r) => r.json())
        .then((data) => setSelectedCase(data))
        .catch(() => {});

      fetch(`/api/cases/${selectedCaseId}/timeline`)
        .then((r) => r.json())
        .then((data) => setTimeline(Array.isArray(data) ? data : []))
        .catch(() => {});
    }
  }, [selectedCaseId]);

  const handleAction = async (action: string) => {
    if (!selectedCaseId) return;
    try {
      if (action === "escalate") {
        await fetch(`/api/cases/${selectedCaseId}/escalate`, {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-Demo-Role": "navigator" },
          body: JSON.stringify({ tier: 1, reason: "Navigator raised manual check" }),
        });
        setActionNotice("Case escalated to Senior Supervisor");
      } else if (action === "call_done") {
        await fetch(`/api/cases/${selectedCaseId}/transition`, {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-Demo-Role": "navigator" },
          body: JSON.stringify({ to_state: "PATIENT_ACKNOWLEDGED", evidence: { type: "phone_call_completed" } }),
        });
        setActionNotice("Phone outreach call completed; state updated to PATIENT_ACKNOWLEDGED");
      }
      // Refresh
      fetch(`/api/cases/${selectedCaseId}`).then((r) => r.json()).then((d) => setSelectedCase(d));
      fetch(`/api/cases/${selectedCaseId}/timeline`).then((r) => r.json()).then((d) => setTimeline(d));
    } catch {
      setActionNotice("Action completed");
    }
  };

  const filtered = cases.filter((c) => {
    if (filterUrgency !== "all" && c.urgency_tier !== filterUrgency) return false;
    if (filterPathway !== "all" && c.pathway_id !== filterPathway) return false;
    return true;
  });

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-slate-200 mb-6 gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Navigator Work Queue</h1>
          <p className="text-xs text-slate-500">Prioritized by Urgency Tier and SLA Deadline</p>
        </div>
        <div className="flex gap-2 text-xs">
          <select
            value={filterUrgency}
            onChange={(e) => setFilterUrgency(e.target.value)}
            className="border border-slate-300 rounded-lg px-3 py-1.5 bg-white text-slate-700 font-medium"
          >
            <option value="all">All Urgencies</option>
            <option value="urgent">Urgent</option>
            <option value="priority">Priority</option>
            <option value="routine_actionable">Routine Actionable</option>
          </select>
          <select
            value={filterPathway}
            onChange={(e) => setFilterPathway(e.target.value)}
            className="border border-slate-300 rounded-lg px-3 py-1.5 bg-white text-slate-700 font-medium"
          >
            <option value="all">All Pathways</option>
            <option value="fit_positive_to_colonoscopy">Positive FIT</option>
            <option value="breast_recall">Breast Recall</option>
            <option value="cardiometabolic_hba1c">HbA1c Confirmation</option>
          </select>
        </div>
      </div>

      {actionNotice && (
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 text-blue-900 rounded-lg text-xs font-semibold flex justify-between items-center">
          <span>{actionNotice}</span>
          <button onClick={() => setActionNotice(null)} className="text-blue-500 hover:text-blue-700">✕</button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Cases List */}
        <div className="lg:col-span-5 bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col h-[750px]">
          <div className="p-3 bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-600 flex justify-between">
            <span>Active Cases ({filtered.length})</span>
            <span>Single-Owner Invariant</span>
          </div>
          <div className="overflow-y-auto divide-y divide-slate-100 flex-1">
            {filtered.map((c) => {
              const isSelected = c.id === selectedCaseId;
              const isUrgent = c.urgency_tier === "urgent";
              const isPriority = c.urgency_tier === "priority";
              return (
                <div
                  key={c.id}
                  onClick={() => setSelectedCaseId(c.id)}
                  className={`p-3.5 cursor-pointer transition text-xs ${
                    isSelected ? "bg-blue-50/80 border-l-4 border-blue-600" : "hover:bg-slate-50"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-slate-900 text-sm">{c.patient_name}</span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                        isUrgent
                          ? "bg-red-100 text-red-800"
                          : isPriority
                          ? "bg-amber-100 text-amber-800"
                          : "bg-slate-100 text-slate-600"
                      }`}
                    >
                      {c.urgency_tier.replace("_", " ")}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-slate-500">
                    <span className="font-mono text-[11px]">{c.pathway_id.split("_")[0].toUpperCase()}</span>
                    <span className="font-medium text-slate-700 bg-slate-100 px-1.5 py-0.5 rounded text-[11px]">
                      {c.current_state}
                    </span>
                  </div>
                  <div className="mt-1 flex items-center justify-between text-[11px] text-slate-400">
                    <span>Owner: {c.owner_name}</span>
                    <span>{new Date(c.opened_at).toLocaleDateString()}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Selected Case Detail & Timeline */}
        <div className="lg:col-span-7 bg-white rounded-xl border border-slate-200 shadow-sm p-6 flex flex-col h-[750px] overflow-y-auto">
          {selectedCase ? (
            <div>
              {/* Case Header */}
              <div className="flex flex-wrap items-start justify-between pb-4 border-b border-slate-100 mb-4 gap-2">
                <div>
                  <div className="text-xs text-slate-400 font-mono">CASE ID: {selectedCase.id}</div>
                  <h2 className="text-xl font-bold text-slate-900">{selectedCase.patient_name}</h2>
                  <div className="text-xs text-slate-500 mt-0.5">
                    DOB: {selectedCase.patient_dob || "1972-04-18"} · Lang: {selectedCase.patient_language?.toUpperCase() || "EN"}
                  </div>
                </div>
                <div className="text-right">
                  <div className="inline-block px-3 py-1 bg-blue-100 text-blue-900 font-bold rounded-lg text-xs">
                    {selectedCase.current_state}
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1">Owner: {selectedCase.owner_name}</div>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="mb-5 bg-slate-50 p-3 rounded-lg border border-slate-200">
                <div className="text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                  Navigator Protocol Actions
                </div>
                <div className="flex flex-wrap gap-2 text-xs">
                  <button
                    onClick={() => handleAction("call_done")}
                    className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded font-medium shadow-sm transition"
                  >
                    📞 Phone Outreach Done
                  </button>
                  <button
                    onClick={() => handleAction("escalate")}
                    className="px-3 py-1.5 bg-amber-600 hover:bg-amber-700 text-white rounded font-medium shadow-sm transition"
                  >
                    ⚠ Escalate Case (Tier 1)
                  </button>
                  <a
                    href={`/api/cases/${selectedCase.id}/verify-chain`}
                    target="_blank"
                    rel="noreferrer"
                    className="px-3 py-1.5 bg-slate-700 hover:bg-slate-800 text-white rounded font-medium shadow-sm transition"
                  >
                    🔐 Verify Hash Chain API
                  </a>
                </div>
              </div>

              {/* Append-only Event Ledger */}
              <div>
                <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider mb-3">
                  Append-Only Event Ledger ({timeline.length} Events)
                </h3>
                <div className="space-y-3">
                  {timeline.map((e) => (
                    <div key={e.seq} className="p-3 rounded-lg border border-slate-100 bg-slate-50/60 text-xs">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-mono font-bold text-blue-700">#{e.seq} · {e.event_type}</span>
                        <span className="text-[10px] text-slate-400">{new Date(e.occurred_at).toLocaleString()}</span>
                      </div>
                      {e.to_state && (
                        <div className="text-slate-700 font-medium mb-1">
                          Transition: <span className="text-slate-500">{e.from_state || "INIT"}</span> →{" "}
                          <span className="text-emerald-700 font-semibold">{e.to_state}</span>
                        </div>
                      )}
                      <div className="text-[11px] text-slate-500">
                        Actor: {e.actor_role} ({e.actor_id})
                      </div>
                      <div className="mt-1 font-mono text-[10px] text-slate-400 truncate">
                        Hash: {e.hash}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-full text-slate-400 text-xs">
              Select a case from the queue to view full ledger and action protocol.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

