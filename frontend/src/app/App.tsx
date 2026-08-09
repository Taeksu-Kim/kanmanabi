import { Navigate, Route, Routes } from "react-router";
import { StudyPage } from "../features/study/StudyPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/study" replace />} />
      <Route path="/study" element={<StudyPage />} />
      <Route path="*" element={<Navigate to="/study" replace />} />
    </Routes>
  );
}
