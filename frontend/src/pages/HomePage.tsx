import { theme } from "../styles/theme";
import { Navbar } from "../components/landing/Navbar";
import { HeroSection } from "../components/landing/HeroSection";
import { LiveCameras } from "../components/landing/LiveCameras";
import { StoreDigitalTwin } from "../components/landing/StoreDigitalTwin";
import { HowItWorks } from "../components/landing/HowItWorks";
import { RealInsights } from "../components/landing/RealInsights";
import { TechStack } from "../components/landing/TechStack";
import { FinalCTA } from "../components/landing/FinalCTA";
import { Footer } from "../components/landing/Footer";

export function HomePage() {
  return (
    <div style={{ background: theme.bg.primary, color: theme.text.primary, fontFamily: theme.font, minHeight: "100vh", overflowX: "hidden" }}>
      <Navbar />
      <HeroSection />
      <LiveCameras />
      <StoreDigitalTwin />
      <HowItWorks />
      <RealInsights />
      <TechStack />
      <FinalCTA />
      <Footer />
    </div>
  );
}
