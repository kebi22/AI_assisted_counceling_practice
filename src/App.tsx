import { BrowserRouter, Route, Routes } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import StudentDashboard from "./pages/StudentDashboard";
import ScenarioDetailPage from "./pages/ScenarioDetailPage";
import SimulationChatPage from "./pages/SimulationChatPage";
import FeedbackReportPage from "./pages/FeedbackReportPage";
import FacultyDashboard from "./pages/FacultyDashboard";
import FacultySessionReviewPage from "./pages/FacultySessionReviewPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/student" element={<StudentDashboard />} />
        <Route path="/student/scenario" element={<ScenarioDetailPage />} />
        <Route path="/student/simulation" element={<SimulationChatPage />} />
        <Route path="/student/feedback/:sessionId" element={<FeedbackReportPage />} />
        <Route path="/faculty" element={<FacultyDashboard />} />
        <Route path="/faculty/sessions/:sessionId" element={<FacultySessionReviewPage />} />
      </Routes>
    </BrowserRouter>
  );
}
