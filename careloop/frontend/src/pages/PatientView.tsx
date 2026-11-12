import React, { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";

export const PatientView: React.FC = () => {
  const [searchParams] = useSearchParams();
  const patientId = searchParams.get("patient") || "pt-demo-amira";
  const caseId = searchParams.get("case") || "case-demo-a-amira";

  const [lang, setLang] = useState<"en" | "ar">("ar");
  const [caseData, setCaseData] = useState<any>(null);
  const [acknowledged, setAcknowledged] = useState(false);
  const [showRedFlags, setShowRedFlags] = useState(false);
  const [redFlagAlert, setRedFlagAlert] = useState<string | null>(null);
  const [teachbackAnswer, setTeachbackAnswer] = useState<string | null>(null);
  const [teachbackResult, setTeachbackResult] = useState<any>(null);
  const [helpRequested, setHelpRequested] = useState(false);
  const [selectedSlot, setSelectedSlot] = useState<string | null>(null);

  const isRTL = lang === "ar";

  useEffect(() => {
    fetch(`/api/cases/${caseId}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data) {
          setCaseData(data);
          if (data.current_state !== "RESULT_ISSUED" && data.current_state !== "PATIENT_NOTIFIED") {
            setAcknowledged(true);
          }
        }
      })
      .catch(() => {});
  }, [caseId]);

  const handleAcknowledge = async () => {
    try {
      const res = await fetch(`/api/patients/${patientId}/acknowledge`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ case_id: caseId }),
      });
      if (res.ok) {
        setAcknowledged(true);
      }
    } catch {}
  };

  const handleRedFlagSubmit = async (answers: any) => {
    try {
      const res = await fetch(`/api/patients/${patientId}/redflags`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ case_id: caseId, answers }),
      });
      const data = await res.json();
      setRedFlagAlert(data.safe_action_guidance);
      setShowRedFlags(false);
    } catch {}
  };

  const handleTeachback = async (optId: string) => {
    setTeachbackAnswer(optId);
    try {
      const res = await fetch(`/api/patients/${patientId}/teachback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          case_id: caseId,
          question_id: "q_next_step",
          selected_option_id: optId,
        }),
      });
      const data = await res.json();
      setTeachbackResult(data);
    } catch {}
  };

  const handleHelp = async () => {
    try {
      await fetch(`/api/patients/${patientId}/help`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ case_id: caseId, note: "Patient tapped Need Help" }),
      });
      setHelpRequested(true);
    } catch {}
  };

  const content = {
    en: {
      tag: "Secure Patient Care Portal",
      patient: "Patient",
      pathway: "Bowel Health Screening Pathway",
      status: "Current Status",
      whatNext: "What Happens Next?",
      whatNextBody:
        "Your screening test detected signs that warrant a closer look. A specialist endoscopy consultation will be arranged. We will support you through preparation and scheduling.",
      navigator: "Your Dedicated Care Navigator",
      navigatorName: "Sarah Jenkins, RN",
      navigatorPhone: "+971 2 555 0100",
      needHelp: "I Need Help / Call Me",
      helpSent: "Your navigator has been notified and will call you shortly.",
      ackButton: "I Acknowledge Receiving This Result",
      ackDone: "Receipt Acknowledged — Thank you",
      symptomCheck: "Symptom Check (Red Flags)",
      symptomPrompt: "Are you currently experiencing any of the following symptoms?",
      bleedingQ: "Active rectal bleeding or blood in stool?",
      weightQ: "Unexplained weight loss over recent months?",
      yes: "Yes",
      no: "No",
      teachbackTitle: "Understanding Your Care (Quick Check)",
      teachbackPrompt: "What is your recommended next step according to this guidance?",
      opt1: "1. No further action is required; wait 2 years",
      opt2: "2. Attend a diagnostic colonoscopy assessment appointment",
      opt3: "3. Retake the screening stool test at home",
      correctFeedback: "✓ Correct! A diagnostic assessment is the recommended standard of care.",
      incorrectFeedback: "⚠ Not quite. Your result needs further assessment. Your navigator will review this with you.",
      bookTitle: "Select Colonoscopy Assessment Slot",
      slot1: "Monday 10:00 AM · Sheikh Shakhbout Pavilion",
      slot2: "Wednesday 02:30 PM · Sheikh Shakhbout Pavilion",
      bookConfirm: "Appointment Slot Selected & Confirmed",
    },
    ar: {
      tag: "بوابة رعاية المرضى الآمنة",
      patient: "المريض",
      pathway: "مسار الفحص المبكر لصحة القولون",
      status: "الحالة الحالية",
      whatNext: "ما هي الخطوة التالية؟",
      whatNextBody:
        "أظهر فحصك علامات تستدعي المتابعة التشخيصية الدقيقة. سيتم ترتيب موعد تنظير القولون التشخيصي. سيتواصل معك منسق الرعاية لمساعدتك في التحضير والموعد.",
      navigator: "منسق الرعاية المخصص لك",
      navigatorName: "سارة الجنيبي (ممرضة منسقة)",
      navigatorPhone: "+971 2 555 0100",
      needHelp: "أحتاج إلى مساعدة / يرجى الاتصال بي",
      helpSent: "تم إخطار منسق الرعاية وسيتصل بك في أقرب وقت.",
      ackButton: "أؤكد استلام نتيجة الفحص والاطلاع عليها",
      ackDone: "تم تأكيد الاستلام — شكراً لك",
      symptomCheck: "فحص الأعراض التحذيرية (علامات الخطر)",
      symptomPrompt: "هل تعاني حالياً من أي من الأعراض التالية؟",
      bleedingQ: "نزيف شرجي نشط أو وجود دم في البراز؟",
      weightQ: "فقدان وزن غير مبرر خلال الأشهر الماضية؟",
      yes: "نعم",
      no: "لا",
      teachbackTitle: "التحقق من الفهم (فحص سريع)",
      teachbackPrompt: "ما هي الخطوة التالية الموصى بها وفقاً لهذه الإرشادات؟",
      opt1: "١. لا يلزم اتخاذ أي إجراء؛ الانتظار عامين",
      opt2: "٢. حضور موعد تنظير القولون التشخيصي للمتابعة",
      opt3: "٣. إعادة إجراء فحص البراز المنزلي",
      correctFeedback: "✓ إجابة صحيحة! التقييم التشخيصي هو الخطوة الطبية المعتمدة للمتابعة.",
      incorrectFeedback: "⚠ الإجابة غير دقيقة. نتيجتك تتطلب متابعة تشخيصية. سيتواصل معك المنسق للتوضيح.",
      bookTitle: "اختيار موعد التقييم التشخيصي",
      slot1: "الإثنين ١٠:٠٠ صباحاً · جناح شخبوط التخصصي",
      slot2: "الأربعاء ٠٢:٣٠ ظهراً · جناح شخبوط التخصصي",
      bookConfirm: "تم تأكيد اختيار الموعد بنجاح",
    },
  };

  const t = content[lang];

  return (
    <div className={`max-w-md mx-auto px-4 py-6 font-sans ${isRTL ? "text-right" : "text-left"}`} dir={isRTL ? "rtl" : "ltr"}>
      {/* Language Toggle & Header */}
      <div className="flex items-center justify-between mb-4 bg-white p-3 rounded-xl border border-slate-200 shadow-sm">
        <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">{t.tag}</span>
        <div className="flex bg-slate-100 p-0.5 rounded-lg text-xs font-semibold">
          <button
            onClick={() => setLang("en")}
            className={`px-3 py-1 rounded-md transition ${lang === "en" ? "bg-white text-blue-600 shadow-sm" : "text-slate-600"}`}
          >
            English
          </button>
          <button
            onClick={() => setLang("ar")}
            className={`px-3 py-1 rounded-md transition ${lang === "ar" ? "bg-white text-blue-600 shadow-sm" : "text-slate-600"}`}
          >
            العربية (RTL)
          </button>
        </div>
      </div>

      {/* Red flag alert banner if present */}
      {redFlagAlert && (
        <div className="mb-4 p-4 bg-red-50 border-2 border-red-500 rounded-xl text-red-900 text-sm leading-relaxed shadow-md">
          <div className="font-bold mb-1 flex items-center gap-2">
            <span>🚨</span>
            <span>تنبيه عاجل / Urgent Medical Guidance</span>
          </div>
          <p>{redFlagAlert}</p>
        </div>
      )}

      {/* Patient Summary Card */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm mb-4">
        <div className="flex items-center justify-between mb-3">
          <div>
            <div className="text-xs text-slate-500 font-medium">{t.patient}</div>
            <div className="text-lg font-bold text-slate-900">
              {caseData?.patient_name || (lang === "ar" ? "أميرة المنصوري" : "Amira Al-Mansouri")}
            </div>
          </div>
          <span className="px-2.5 py-1 bg-amber-50 text-amber-700 border border-amber-200 text-xs font-semibold rounded-full">
            {caseData?.current_state || "PATIENT_NOTIFIED"}
          </span>
        </div>

        <div className="text-xs text-slate-600 bg-slate-50 p-2.5 rounded-lg border border-slate-100 mb-4">
          <span className="font-semibold text-slate-700">{t.pathway}: </span>
          <span>FIT Positive Result Follow-Up</span>
        </div>

        {/* What Happens Next */}
        <div className="border-t border-slate-100 pt-3">
          <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-1">{t.whatNext}</h4>
          <p className="text-xs text-slate-600 leading-relaxed">{t.whatNextBody}</p>
        </div>

        {/* Acknowledgement Button */}
        <div className="mt-4">
          {!acknowledged ? (
            <button
              onClick={handleAcknowledge}
              className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-semibold shadow transition"
            >
              {t.ackButton}
            </button>
          ) : (
            <div className="w-full py-2.5 bg-emerald-50 border border-emerald-300 text-emerald-800 rounded-xl text-xs font-semibold text-center">
              ✓ {t.ackDone}
            </div>
          )}
        </div>
      </div>

      {/* Red Flag Symptoms Check */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm mb-4">
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-sm font-bold text-slate-900">{t.symptomCheck}</h4>
          <span className="text-xs text-slate-400">Safety Check</span>
        </div>
        <p className="text-xs text-slate-600 mb-3">{t.symptomPrompt}</p>

        {!showRedFlags ? (
          <button
            onClick={() => setShowRedFlags(true)}
            className="w-full py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition"
          >
            Open Questionnaire / فحص الأعراض
          </button>
        ) : (
          <div className="space-y-3 bg-slate-50 p-3 rounded-xl border border-slate-200 text-xs">
            <div>
              <p className="font-medium text-slate-800 mb-2">{t.bleedingQ}</p>
              <div className="flex gap-2">
                <button
                  onClick={() => handleRedFlagSubmit({ rectal_bleeding: true })}
                  className="flex-1 py-1.5 bg-red-100 text-red-800 font-bold rounded border border-red-300 hover:bg-red-200"
                >
                  {t.yes}
                </button>
                <button
                  onClick={() => handleRedFlagSubmit({ rectal_bleeding: false })}
                  className="flex-1 py-1.5 bg-slate-200 text-slate-800 font-semibold rounded hover:bg-slate-300"
                >
                  {t.no}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Teach-back Comprehension Question */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm mb-4">
        <h4 className="text-sm font-bold text-slate-900 mb-1">{t.teachbackTitle}</h4>
        <p className="text-xs text-slate-600 mb-3">{t.teachbackPrompt}</p>

        <div className="space-y-2 text-xs">
          {[
            { id: "1", text: t.opt1 },
            { id: "2", text: t.opt2 },
            { id: "3", text: t.opt3 },
          ].map((opt) => (
            <button
              key={opt.id}
              onClick={() => handleTeachback(opt.id)}
              className={`w-full text-left p-3 rounded-lg border transition ${
                teachbackAnswer === opt.id
                  ? "border-blue-500 bg-blue-50/70 font-semibold text-blue-900"
                  : "border-slate-200 hover:border-slate-300 bg-white text-slate-700"
              }`}
            >
              {opt.text}
            </button>
          ))}
        </div>

        {teachbackResult && (
          <div
            className={`mt-3 p-3 rounded-lg text-xs font-medium leading-relaxed ${
              teachbackResult.is_correct
                ? "bg-emerald-50 text-emerald-900 border border-emerald-200"
                : "bg-amber-50 text-amber-900 border border-amber-200"
            }`}
          >
            {teachbackResult.is_correct ? t.correctFeedback : t.incorrectFeedback}
          </div>
        )}
      </div>

      {/* Slot Chooser */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm mb-4">
        <h4 className="text-sm font-bold text-slate-900 mb-2">{t.bookTitle}</h4>
        <div className="space-y-2 text-xs mb-3">
          {[
            { id: "s1", text: t.slot1 },
            { id: "s2", text: t.slot2 },
          ].map((s) => (
            <button
              key={s.id}
              onClick={() => setSelectedSlot(s.id)}
              className={`w-full text-left p-2.5 rounded-lg border transition ${
                selectedSlot === s.id
                  ? "border-emerald-500 bg-emerald-50 text-emerald-900 font-semibold"
                  : "border-slate-200 bg-white text-slate-700"
              }`}
            >
              📅 {s.text}
            </button>
          ))}
        </div>
        {selectedSlot && (
          <div className="text-xs text-emerald-700 font-semibold bg-emerald-50 p-2 rounded border border-emerald-200 text-center">
            ✓ {t.bookConfirm}
          </div>
        )}
      </div>

      {/* Care Navigator Contact & Need Help */}
      <div className="bg-slate-900 text-white rounded-2xl p-5 shadow-sm">
        <div className="text-xs text-slate-400 font-medium mb-1">{t.navigator}</div>
        <div className="text-base font-bold mb-1">{t.navigatorName}</div>
        <div className="text-xs text-slate-300 mb-4">{t.navigatorPhone}</div>

        {!helpRequested ? (
          <button
            onClick={handleHelp}
            className="w-full py-2.5 bg-white/10 hover:bg-white/20 text-white rounded-xl text-xs font-semibold border border-white/20 transition"
          >
            {t.needHelp}
          </button>
        ) : (
          <div className="text-xs text-amber-300 font-medium bg-white/5 p-2 rounded text-center">
            ✓ {t.helpSent}
          </div>
        )}
      </div>
    </div>
  );
};

