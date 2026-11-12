import React from "react";
import { Link } from "react-router-dom";

interface QuickTourProps {
  onSelectRole: (role: string) => void;
  currentRole: string;
}

export const QuickTour: React.FC<QuickTourProps> = ({ onSelectRole, currentRole }) => {
  const demoCases = [
    {
      id: "case-demo-a-amira",
      patientId: "pt-demo-amira",
      code: "Case A",
      name: "Amira Al-Mansouri",
      title: "The Happy Path (End-to-End Care Loop)",
      description: "Screening FIT positive. Notified in Arabic. Acknowledged, referred, attended colonoscopy, polyp resected. Sealed with clinician-approved evidence.",
      highlight: "Closed with Evidence & Human Sign-off",
      statusColor: "bg-emerald-100 text-emerald-800 border-emerald-300",
      targetPath: "/clinician?case=case-demo-a-amira",
      role: "clinician",
    },
    {
      id: "case-demo-b-rahul",
      patientId: "pt-demo-rahul",
      code: "Case B",
      name: "Rahul Sharma",
      title: "Unresponsive Patient & Escalating Retries",
      description: "Patient did not acknowledge notification. Channel retries failed. SLA breached, raising Tier 1 escalation and navigator phone call outreach task.",
      highlight: "SLA Breach & Outreach Task",
      statusColor: "bg-amber-100 text-amber-800 border-amber-300",
      targetPath: "/navigator?case=case-demo-b-rahul",
      role: "navigator",
    },
    {
      id: "case-demo-c-maria",
      patientId: "pt-demo-maria",
      code: "Case C",
      name: "Maria Santos",
      title: "Referral Rejected by Clinic (Auto-Return)",
      description: "Outpatient clinic rejected referral due to capacity. Single-owner ledger auto-returned ownership to navigator. Raised task for re-routing.",
      highlight: "Exception Queue & Re-routing",
      statusColor: "bg-rose-100 text-rose-800 border-rose-300",
      targetPath: "/navigator?case=case-demo-c-maria",
      role: "navigator",
    },
    {
      id: "case-demo-d-omar",
      patientId: "pt-demo-omar",
      code: "Case D",
      name: "Omar Tariq",
      title: "Red-Flag Symptoms Reported at Ack",
      description: "Patient reported rectal bleeding and >5% weight loss. Urgency auto-upgraded to Urgent. Immediate Tier 2 clinical lead escalation and safe guidance shown.",
      highlight: "Red-Flag Clinical Escalation",
      statusColor: "bg-red-100 text-red-800 border-red-300",
      targetPath: "/patient?patient=pt-demo-omar&case=case-demo-d-omar",
      role: "patient",
    },
    {
      id: "case-demo-e-chen",
      patientId: "pt-demo-chen",
      code: "Case E",
      name: "Chen Wei",
      title: "Provider Transfer with Intact Audit Chain",
      description: "Patient relocated to a new health district. Hand-off offered and accepted by receiving specialist. Hash chain preserved without data loss.",
      highlight: "Cross-Provider Transfer",
      statusColor: "bg-blue-100 text-blue-800 border-blue-300",
      targetPath: "/governance?case=case-demo-e-chen",
      role: "auditor",
    },
    {
      id: "case-demo-f-blocked",
      patientId: "pt-demo-fatima",
      code: "Case F",
      name: "Fatima Al-Nuaimi",
      title: "Responsible AI Guardrail: Diagnosis Blocked",
      description: "Adversarial AI rewrite attempted to disclose diagnosis ('you have cancer'). Rule validator blocked output, logged alert, and served deterministic safe template.",
      highlight: "AI Disclosure Blocked & Fallback Used",
      statusColor: "bg-purple-100 text-purple-800 border-purple-300",
      targetPath: "/governance",
      role: "supervisor",
    },
  ];

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Hero */}
      <div className="bg-gradient-to-r from-blue-900 to-indigo-900 text-white rounded-2xl p-8 mb-8 shadow-xl">
        <div className="inline-block px-3 py-1 bg-blue-700/60 rounded-full text-xs font-semibold uppercase tracking-wider mb-3">
          Future Health Challenge 05 · Working Prototype
        </div>
        <h1 className="text-3xl font-bold tracking-tight mb-3">
          CareLoop: Closing the Screening-to-Care Loop
        </h1>
        <p className="text-blue-100 text-lg max-w-3xl leading-relaxed">
          Every actionable screening result gets an accountable owner, an explicit deadline, 
          culturally appropriate patient communication, and a human-governed, evidence-backed closure.
        </p>
        <div className="mt-6 flex flex-wrap gap-4 items-center">
          <Link
            to="/patient?patient=pt-demo-amira&case=case-demo-a-amira"
            className="px-5 py-2.5 bg-emerald-500 hover:bg-emerald-600 font-semibold rounded-lg text-white shadow transition"
          >
            Open Patient Journey (Arabic / English)
          </Link>
          <Link
            to="/evidence"
            className="px-5 py-2.5 bg-white/10 hover:bg-white/20 font-semibold rounded-lg text-white border border-white/20 transition"
          >
            View Simulation Evidence (N=5,000)
          </Link>
        </div>
      </div>

      {/* 6 Demo Stories */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-slate-800">
            7-Minute Demo Walkthrough: 6 Scripted Scenarios
          </h2>
          <span className="text-sm text-slate-500">Click any card to inspect the real system state</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {demoCases.map((c) => (
            <Link
              key={c.id}
              to={c.targetPath}
              onClick={() => onSelectRole(c.role)}
              className="group block bg-white border border-slate-200 hover:border-blue-500 rounded-xl p-5 shadow-sm hover:shadow-md transition relative flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                    {c.code}
                  </span>
                  <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${c.statusColor}`}>
                    {c.highlight}
                  </span>
                </div>
                <h3 className="font-bold text-slate-900 group-hover:text-blue-600 transition text-base mb-1">
                  {c.name}
                </h3>
                <h4 className="text-xs font-semibold text-slate-500 mb-2">{c.title}</h4>
                <p className="text-xs text-slate-600 leading-relaxed mb-4">{c.description}</p>
              </div>
              <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-blue-600 font-semibold">
                <span>Switch to {c.role} role & view →</span>
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* Role Navigation Bar */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm mb-8">
        <h3 className="text-sm font-bold text-slate-700 uppercase tracking-wider mb-4">
          Direct Role Views
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {[
            { role: "patient", name: "Patient Portal", path: "/patient?patient=pt-demo-amira&case=case-demo-a-amira" },
            { role: "navigator", name: "Navigator Queue", path: "/navigator" },
            { role: "clinician", name: "Clinician View", path: "/clinician" },
            { role: "supervisor", name: "Ops Dashboard", path: "/ops" },
            { role: "auditor", name: "Governance & AI Log", path: "/governance" },
            { role: "supervisor", name: "Pathway Viewer", path: "/pathways" },
          ].map((item) => (
            <Link
              key={item.name}
              to={item.path}
              onClick={() => onSelectRole(item.role)}
              className="text-center p-3 rounded-lg border border-slate-200 hover:border-blue-500 hover:bg-blue-50/50 transition font-medium text-xs text-slate-700"
            >
              {item.name}
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
};
