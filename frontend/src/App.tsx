import { Route, Routes } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import RepositoryPage from "./pages/RepositoryPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/repository" element={<RepositoryPage />} />
    </Routes>
  );
}
