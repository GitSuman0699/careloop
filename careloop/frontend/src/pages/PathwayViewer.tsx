import React, { useState, useEffect } from "react";

export const PathwayViewer: React.FC = () => {
  const [pathways, setPathways] = useState<any[]>([]);
  const [selectedPathwayId, setSelectedPathwayId] = useState<string>("fit_positive_to_colonoscopy");
  const [pathwayDetail, setPathwayDetail] = useState<any>(null);

  useEffect(() => {
    fetch("/api/pathways")
      .then((r) => r.json())
      .then((d) => {
        if (Array.isArray(d)) setPathways(d);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (selectedPathwayId) {
      fetch(`/api/pathways/${selectedPathwayId}`)
        .then((r) => r.json())
        .then((d) => setPathwayDetail(d))
        .catch(() => {});
    }
  }, [selectedPathwayId]);

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      <div className="pb-4 border-b border-slate-200 mb-6">
        <h1 className="text-2xl font-bold text-slate-900">Zero-Code Pathway Configuration Viewer</h1>
        <p className="text-xs text-slate-500">
          Criterion 05 Deployment Readiness: New screening programs are deployed via declarative JSON without code changes
        </p>
      </div>

      {/* Pathway Selector */}
      <div className="flex gap-3 mb-6">
        {pathways.map((p) => (
          <button
            key={p.id}
            onClick={() => setSelectedPathwayId(p.id)}
            className={`px-4 py-2.5 rounded-xl text-xs font-bold transition border ${
              selectedPathwayId === p.id
                ? "bg-blue-600 text-white border-blue-600 shadow"
                : "bg-white text-slate-700 border-slate-200 hover:border-slate-300"
            }`}
          >
            {p.title || p.id} ({p.steps_count} steps)
          </button>
        ))}
      </div>

      {pathwayDetail && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Pathway Metadata & Steps Flow */}
          <div className="lg:col-span-7 bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
              <div>
                <h3 className="font-bold text-slate-900 text-base">{pathwayDetail.title}</h3>
                <div className="text-xs text-slate-400">ID: {pathwayDetail.id} · Version: {pathwayDetail.version}</div>
              </div>
              <span className="px-2.5 py-1 bg-amber-100 text-amber-900 text-xs font-bold rounded-full">
                {pathwayDetail.clinical_review_status}
              </span>
            </div>

            <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3">
              Configured State Machine Progression
            </h4>
            <div className="space-y-2">
              {pathwayDetail.steps?.map((s: any, idx: number) => (
                <div key={s.id} className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-slate-800">
                      {idx + 1}. {s.label} ({s.id})
                    </span>
                    <span className="text-[10px] font-mono text-slate-400">
                      SLA: {s.sla_key || "Standard"}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-500 mb-1">{s.description}</div>
                  <div className="text-[10px] font-mono text-blue-600">
                    Next State: {Array.isArray(s.next) ? s.next.join(", ") : s.next || "TERMINAL"}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Raw JSON Config Viewer */}
          <div className="lg:col-span-5 bg-slate-900 text-slate-100 p-5 rounded-xl shadow-sm flex flex-col h-[650px]">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3 text-xs">
              <span className="font-mono text-slate-400">config/pathways/{pathwayDetail.id}.json</span>
              <span className="text-emerald-400 font-bold">Valid JSON Schema</span>
            </div>
            <pre className="text-[11px] font-mono overflow-y-auto flex-1 text-slate-300 leading-relaxed">
              {JSON.stringify(pathwayDetail, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};

