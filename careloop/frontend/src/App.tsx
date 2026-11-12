import { BrowserRouter, Routes, Route, Link } from "react-router-dom";

function Banner() {
  return (
    <div className="bg-amber-400 text-amber-900 text-center py-2 font-bold text-sm">
      ⚠️ SIMULATED DATA: NOT FOR CLINICAL USE
    </div>
  );
}

function Nav() {
  return (
    <nav className="bg-gray-800 text-white px-6 py-3 flex gap-4 text-sm">
      <Link to="/" className="hover:underline">Home</Link>
      <Link to="/patient" className="hover:underline">Patient</Link>
      <Link to="/navigator" className="hover:underline">Navigator</Link>
      <Link to="/clinician" className="hover:underline">Clinician</Link>
      <Link to="/ops" className="hover:underline">Ops</Link>
      <Link to="/evidence" className="hover:underline">Evidence</Link>
      <Link to="/governance" className="hover:underline">Governance</Link>
    </nav>
  );
}

function Home() {
  return <div className="p-8"><h1 className="text-2xl font-bold">CareLoop Dashboard</h1><p className="mt-2 text-gray-600">Select a view from the navigation above.</p></div>;
}
function Patient() {
  return <div className="p-8"><h1 className="text-2xl font-bold">Patient View</h1><p className="mt-2 text-gray-600">Patient portal placeholder.</p></div>;
}
function Navigator() {
  return <div className="p-8"><h1 className="text-2xl font-bold">Navigator View</h1><p className="mt-2 text-gray-600">Care navigator worklist placeholder.</p></div>;
}
function Clinician() {
  return <div className="p-8"><h1 className="text-2xl font-bold">Clinician View</h1><p className="mt-2 text-gray-600">Clinician dashboard placeholder.</p></div>;
}
function Ops() {
  return <div className="p-8"><h1 className="text-2xl font-bold">Ops View</h1><p className="mt-2 text-gray-600">Operations metrics placeholder.</p></div>;
}
function Evidence() {
  return <div className="p-8"><h1 className="text-2xl font-bold">Evidence View</h1><p className="mt-2 text-gray-600">Evidence & analytics placeholder.</p></div>;
}
function Governance() {
  return <div className="p-8"><h1 className="text-2xl font-bold">Governance View</h1><p className="mt-2 text-gray-600">Governance & audit placeholder.</p></div>;
}

export default function App() {
  return (
    <BrowserRouter>
      <Banner />
      <Nav />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/patient" element={<Patient />} />
        <Route path="/navigator" element={<Navigator />} />
        <Route path="/clinician" element={<Clinician />} />
        <Route path="/ops" element={<Ops />} />
        <Route path="/evidence" element={<Evidence />} />
        <Route path="/governance" element={<Governance />} />
      </Routes>
    </BrowserRouter>
  );
}
