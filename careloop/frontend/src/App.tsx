import React, { useState } from "react";
import { BrowserRouter, Routes, Route, Link, useLocation } from "react-router-dom";
import { QuickTour } from "./pages/QuickTour";
import { PatientView } from "./pages/PatientView";
import { NavigatorQueue } from "./pages/NavigatorQueue";
import { ClinicianView } from "./pages/ClinicianView";
import { OpsDashboard } from "./pages/OpsDashboard";
import { EvidenceView } from "./pages/EvidenceView";
import { GovernanceView } from "./pages/GovernanceView";
import { PathwayViewer } from "./pages/PathwayViewer";

const NavigationHeader: React.FC<{
  currentRole: string;
  onRoleChange: (r: string) => void;
}> = ({ currentRole, onRoleChange }) => {
  const location = useLocation();

  const navLinks = [
    { path: "/", label: "Quick Tour (Demo)" },
    { path: "/patient?patient=pt-demo-amira&case=case-demo-a-amira", label: "Patient View" },
    { path: "/navigator", label: "Navigator" },
    { path: "/clinician", label: "Clinician" },
    { path: "/ops", label: "Ops & Funnel" },
    { path: "/evidence", label: "Evidence (N=5k)" },
    { path: "/governance", label: "Governance & AI" },
    { path: "/pathways", label: "Pathways" },
  ];

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-50 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 py-3 flex flex-wrap items-center justify-between gap-4">
        {/* Brand */}
        <Link to="/" className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-blue-600 text-white font-extrabold flex items-center justify-center text-sm shadow">
            CL
          </div>
          <div>
            <div className="font-bold text-slate-900 leading-tight">CareLoop</div>
            <div className="text-[10px] text-slate-400 leading-tight">Screening-to-Care Orchestration</div>
          </div>
        </Link>

        {/* Links */}
        <nav className="flex flex-wrap items-center gap-1 text-xs font-semibold">
          {navLinks.map((link) => {
            const isActive = location.pathname === link.path.split("?")[0];
            return (
              <Link
                key={link.label}
                to={link.path}
                className={`px-3 py-1.5 rounded-lg transition ${
                  isActive
                    ? "bg-blue-50 text-blue-700 font-bold"
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>

        {/* Role Switcher */}
        <div className="flex items-center gap-2">
          <span className="text-[11px] text-slate-400 font-medium">Role:</span>
          <select
            value={currentRole}
            onChange={(e) => onRoleChange(e.target.value)}
            className="text-xs font-bold border border-slate-300 rounded-lg px-2.5 py-1.5 bg-slate-50 text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="navigator">Navigator (Sarah)</option>
            <option value="clinician">Clinician (Dr. Tariq)</option>
            <option value="supervisor">Supervisor (Mona)</option>
            <option value="patient">Patient (Amira)</option>
            <option value="auditor">Auditor (David)</option>
          </select>
        </div>
      </div>
    </header>
  );
};

export const App: React.FC = () => {
  const [currentRole, setCurrentRole] = useState<string>("navigator");

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
        {/* Challenge Mandatory Banner */}
        <div className="bg-amber-500 text-amber-950 font-bold text-[11px] py-1.5 px-4 text-center tracking-wider shadow-sm flex items-center justify-center gap-2">
          <span>⚠️ SIMULATED DATA: NOT FOR CLINICAL USE</span>
          <span>·</span>
          <span>Future Health Challenge 05 Working Prototype</span>
        </div>

        <NavigationHeader currentRole={currentRole} onRoleChange={setCurrentRole} />

        <main className="flex-1">
          <Routes>
            <Route path="/" element={<QuickTour onSelectRole={setCurrentRole} currentRole={currentRole} />} />
            <Route path="/patient" element={<PatientView />} />
            <Route path="/navigator" element={<NavigatorQueue />} />
            <Route path="/clinician" element={<ClinicianView />} />
            <Route path="/ops" element={<OpsDashboard />} />
            <Route path="/evidence" element={<EvidenceView />} />
            <Route path="/governance" element={<GovernanceView />} />
            <Route path="/pathways" element={<PathwayViewer />} />
          </Routes>
        </main>

        <footer className="bg-white border-t border-slate-200 py-4 text-center text-xs text-slate-400">
          CareLoop Prototype · Future Health Digital Innovation Challenge 2026 · All data synthetic
        </footer>
      </div>
    </BrowserRouter>
  );
};

export default App;
