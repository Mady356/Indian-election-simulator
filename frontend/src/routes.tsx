import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "@/components/Layout";
import { ExplorePage } from "@/pages/ExplorePage";
import { ConstituencyPage } from "@/pages/ConstituencyPage";
import { StatePage } from "@/pages/StatePage";
import { ComparePage } from "@/pages/ComparePage";
import { InsightsLabPage } from "@/pages/InsightsLabPage";
import { MethodologyPage } from "@/pages/MethodologyPage";

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<ExplorePage />} />
        <Route path="compare" element={<ComparePage />} />
        <Route path="insights" element={<InsightsLabPage />} />
        <Route path="methodology" element={<MethodologyPage />} />
        <Route path="state/:stateKey" element={<StatePage />} />
        <Route path="constituency/:stateKey/:constituencyKey" element={<ConstituencyPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
