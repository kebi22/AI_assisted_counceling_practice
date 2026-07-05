import { BrowserRouter, Route, Routes } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import StudentDashboard from "./pages/StudentDashboard";
import ScenarioDetailPage from "./pages/ScenarioDetailPage";
import SimulationChatPage from "./pages/SimulationChatPage";
import FeedbackReportPage from "./pages/FeedbackReportPage";
import FacultyDashboard from "./pages/FacultyDashboard";
import FacultySessionReviewPage from "./pages/FacultySessionReviewPage";
import FacultyScenariosPage from "./pages/FacultyScenariosPage";
import FacultyScenarioDetailPage from "./pages/FacultyScenarioDetailPage";
import ScenarioBuilderPage from "./pages/ScenarioBuilderPage";
import ScenarioPreviewPage from "./pages/ScenarioPreviewPage";
import ScenarioTemplatesPage from "./pages/ScenarioTemplatesPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/student" element={<StudentDashboard />} />
        <Route path="/student/scenario/:scenarioId" element={<ScenarioDetailPage />} />
        <Route path="/student/simulation/:scenarioId" element={<SimulationChatPage />} />
        <Route path="/student/feedback/:sessionId" element={<FeedbackReportPage />} />
        <Route path="/faculty" element={<FacultyDashboard />} />
        <Route path="/faculty/sessions/:sessionId" element={<FacultySessionReviewPage />} />
        <Route path="/faculty/scenarios" element={<FacultyScenariosPage />} />
        <Route path="/faculty/scenario-templates" element={<ScenarioTemplatesPage />} />
        <Route path="/faculty/scenarios/new" element={<ScenarioBuilderPage />} />
        <Route path="/faculty/scenarios/:scenarioId" element={<FacultyScenarioDetailPage />} />
        <Route path="/faculty/scenarios/:scenarioId/edit" element={<ScenarioBuilderPage />} />
        <Route path="/faculty/scenarios/:scenarioId/preview" element={<ScenarioPreviewPage />} />
      </Routes>
    </BrowserRouter>
  );
}
