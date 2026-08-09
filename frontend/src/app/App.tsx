import { useEffect, useState } from "react";
import { Navigate, Route, Routes, useLocation, useParams } from "react-router";
import { AUTH_REQUIRED_EVENT, AUTH_RESTORED_EVENT } from "../api/client";
import { LoginPage } from "../features/auth/LoginPage";
import { LanguageGate } from "../features/language/LanguageGate";
import { LanguageSwitcher } from "../features/language/LanguageSwitcher";
import { HomePage } from "../features/home/HomePage";
import { EpisodeDetailPage } from "../features/learn/EpisodeDetailPage";
import { LearningHubPage } from "../features/learn/LearningHubPage";
import { GrammarCoursePage } from "../features/learn/GrammarCoursePage";
import { VocabularyBookPage } from "../features/learn/VocabularyBookPage";
import { LevelOnboardingPage } from "../features/onboarding/LevelOnboardingPage";
import { RecordsPage } from "../features/records/RecordsPage";
import { StudyPage } from "../features/study/StudyPage";
import { ConjugationPage } from "../features/conjugation/ConjugationPage";

function GrammarStudyRoute() {
  const { epNo } = useParams();
  return <StudyPage track="grammar" epNo={epNo} />;
}

export default function App() {
  const location = useLocation();
  const [authRequired, setAuthRequired] = useState(false);

  useEffect(() => {
    const requireAuth = () => setAuthRequired(true);
    const restoreAuth = () => setAuthRequired(false);
    window.addEventListener(AUTH_REQUIRED_EVENT, requireAuth);
    window.addEventListener(AUTH_RESTORED_EVENT, restoreAuth);
    return () => {
      window.removeEventListener(AUTH_REQUIRED_EVENT, requireAuth);
      window.removeEventListener(AUTH_RESTORED_EVENT, restoreAuth);
    };
  }, []);

  if (authRequired && location.pathname !== "/login") {
    return <Navigate to="/login" replace />;
  }

  return (
    <LanguageGate>
      <LanguageSwitcher />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/learn" element={<LearningHubPage />} />
        <Route path="/learn/vocabulary" element={<VocabularyBookPage />} />
        <Route path="/learn/grammar" element={<GrammarCoursePage />} />
        <Route path="/learn/grammar/:epNo" element={<EpisodeDetailPage />} />
        <Route path="/learn/conjugation" element={<ConjugationPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/onboarding/level" element={<LevelOnboardingPage />} />
        <Route path="/records" element={<RecordsPage />} />
        <Route path="/review" element={<StudyPage />} />
        <Route path="/study" element={<Navigate to="/study/vocabulary" replace />} />
        <Route path="/study/vocabulary" element={<StudyPage track="vocabulary" />} />
        <Route path="/study/grammar" element={<StudyPage track="grammar" />} />
        <Route path="/study/grammar/:epNo" element={<GrammarStudyRoute />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </LanguageGate>
  );
}
