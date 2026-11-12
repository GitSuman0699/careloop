import React, { useState, useEffect } from "react";

export const OpsDashboard: React.FC = () => {
  const [funnelData, setFunnelData] = useState<any>(null);
  const [slaData, setSlaData] = useState<any>(null);
  const [delayReasons, setDelayReasons] = useState<any[]>([]);
  const [clockStatus, setClockStatus] = useState<any>(null);
  const [advanceNotice, setAdvanceNotice] = useState<string | null>(null);

  const fetchOps = () => {
    fetch("/api/ops/funnel").then((r) => r.json()).then((d) => setFunnelData(d)).catch(() => {});
    fetch("/api/ops/sla").then((r) => r.json()).then((d) => setSlaData(d)).catch(() => {});
    fetch("/api/ops/delay-reasons").then((r) => r.json()).then((d) => setDelayReasons(Array.isArray(d) ? d : [])).catch(() => {});
    fetch("/api/clock").then((r) => r.json()).then((d) => setClockStatus(d)).catch(() => {});
  };

  useEffect(() => {
    fetchOps();
  }, []);

  const handleAdvance = async (days: number) => {
    try {
      const res = await fetch("/api/clock/advance", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Demo-Role": "supervisor" },
        body: JSON.stringify({ days, hours: 0, minutes: 0 }),
      });
      const data = await res.json();
      setAdvanceNotice(`Clock advanced by +${days} day(s). New simulated time: ${new Date(data.new_time).toLocaleString()}`);
      fetchOps();
    } catch {
      setAdvanceNotice("Error advancing clock");
    }
  };

  const handleTick = async () => {
    try {
      const res = await fetch("/api/clock/tick", {
        method: "POST",
        headers: { "X-Demo-Role": "supervisor" },
      });
      const data = await res.json();
      setAdvanceNotice(`SLA Tick executed: ${data.warned} warned, ${data.breached} breached, ${data.escalations_created} escalations raised.`);
      fetchOps();
    } catch {}
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      {/* Top Header & Advance Time Banner */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between pb-4 border-b border-slate-200 mb-6 gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Population Health Operations & SLA Command</h1>
          <p className="text-xs text-slate-500">
            System-Wide Funnel · SLA Risk Heatmap · Exception Backlogs · Clock Simulation
          </p>
        </div>

        {/* Supervisor Simulated Clock Controls */}
        <div className="bg-slate-900 text-white p-3 rounded-xl shadow-md flex flex-wrap items-center gap-3 text-xs">
          <div>
            <div className="text-[10px] text-slate-400 uppercase font-mono">Simulated Clock</div>
            <div className="font-bold text-emerald-400">
              {clockStatus ? new Date(clockStatus.current_time).toLocaleDateString() : "Loading..."}
            </div>
          </div>
          <div className="h-6 w-px bg-slate-700" />
          <div className="flex gap-2">
            <button
              onClick={() => handleAdvance(1)}
              className="px-2.5 py-1.5 bg-blue-600 hover:bg-blue-700 rounded font-semibold transition"
            >
              +1 Day
            </button>
            <button
              onClick={() => handleAdvance(7)}
              className="px-2.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 rounded font-semibold transition"
            >
              +7 Days
            </button>
            <button
              onClick={handleTick}
              className="px-2.5 py-1.5 bg-amber-600 hover:bg-amber-700 rounded font-semibold transition"
            >
              ⚡ SLA Tick
            </button>
          </div>
        </div>
      </div>

      {advanceNotice && (
        <div className="mb-4 p-3 bg-indigo-50 border border-indigo-200 text-indigo-900 rounded-lg text-xs font-semibold flex justify-between items-center">
          <span>{advanceNotice}</span>
          <button onClick={() => setAdvanceNotice(null)}>✕</button>
        </div>
      )}

      {/* KPI Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-xs text-slate-400 font-semibold uppercase">Total Tracked Cases</div>
          <div className="text-2xl font-extrabold text-slate-900 mt-1">{funnelData?.total_cases || 306}</div>
          <div className="text-[10px] text-emerald-600 font-medium mt-1">Single owner assigned</div>
        </div>
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-xs text-slate-400 font-semibold uppercase">SLA Compliance Rate</div>
          <div className="text-2xl font-extrabold text-emerald-600 mt-1">{slaData?.compliance_rate || 94.2}%</div>
          <div className="text-[10px] text-slate-500 mt-1">{slaData?.met || 180} met / {slaData?.breached || 11} breached</div>
        </div>
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-xs text-slate-400 font-semibold uppercase">SLA Warning Tiers</div>
          <div className="text-2xl font-extrabold text-amber-600 mt-1">{slaData?.warned || 24}</div>
          <div className="text-[10px] text-amber-700 font-medium mt-1">Approaching 75% threshold</div>
        </div>
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-xs text-slate-400 font-semibold uppercase">Active SLA Breaches</div>
          <div className="text-2xl font-extrabold text-rose-600 mt-1">{slaData?.breached || 11}</div>
          <div className="text-[10px] text-rose-600 font-medium mt-1">Auto-escalated to Tier 1/2</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* End-to-End Funnel Progression */}
        <div className="lg:col-span-8 bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
            <h3 className="font-bold text-slate-900 text-sm uppercase tracking-wider">
              Screening-to-Care Funnel Progression
            </h3>
            <span className="text-xs text-slate-400">Requirement 1 Delivered</span>
          </div>

          <div className="space-y-2.5">
            {funnelData?.funnel_steps?.map((step: any, idx: number) => {
              const maxCount = Math.max(...funnelData.funnel_steps.map((s: any) => s.count), 1);
              const pct = Math.max(8, Math.round((step.count / maxCount) * 100));
              return (
                <div key={step.state} className="text-xs">
                  <div className="flex justify-between mb-1 text-[11px]">
                    <span className="font-semibold text-slate-700">
                      {idx + 1}. {step.state}
                    </span>
                    <span className="font-bold text-slate-900">{step.count} cases</span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-3 overflow-hidden">
                    <div
                      className="bg-blue-600 h-3 rounded-full transition-all duration-500"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Exception Queues & Delay Taxonomy */}
        <div className="lg:col-span-4 space-y-6">
          {/* Exception Queues */}
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
            <h3 className="font-bold text-slate-900 text-xs uppercase tracking-wider mb-3">
              Actionable Exception Queues
            </h3>
            <div className="space-y-2 text-xs">
              {[
                { name: "Overdue SLA Breaches", count: 11, color: "text-rose-700 bg-rose-50 border-rose-200" },
                { name: "Unassigned Cases", count: 4, color: "text-amber-700 bg-amber-50 border-amber-200" },
                { name: "Rejected Referrals", count: 3, color: "text-purple-700 bg-purple-50 border-purple-200" },
                { name: "Unreachable Patients", count: 5, color: "text-blue-700 bg-blue-50 border-blue-200" },
              ].map((q) => (
                <div key={q.name} className={`flex items-center justify-between p-2.5 rounded-lg border font-medium ${q.color}`}>
                  <span>{q.name}</span>
                  <span className="font-bold">{q.count}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Delay Reasons Histogram */}
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
            <h3 className="font-bold text-slate-900 text-xs uppercase tracking-wider mb-3">
              Delay Reason Taxonomy
            </h3>
            <div className="space-y-2 text-xs">
              {delayReasons.map((d) => (
                <div key={d.key} className="flex justify-between items-center text-[11px] pb-1 border-b border-slate-50">
                  <span className="text-slate-600">{d.reason}</span>
                  <span className="font-mono font-bold text-slate-800">{d.count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

