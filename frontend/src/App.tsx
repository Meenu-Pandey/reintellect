import { Routes, Route, useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { HomePage } from "./pages/HomePage";
import { DashboardPage } from "./pages/DashboardPage";

function App() {
  const location = useLocation();
  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route path="/" element={<motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.25 }}><HomePage /></motion.div>} />
        <Route path="/dashboard" element={<motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.25 }} style={{ height: "100vh" }}><DashboardPage /></motion.div>} />
      </Routes>
    </AnimatePresence>
  );
}

export default App;
