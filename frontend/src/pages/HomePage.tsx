import { theme } from "../styles/theme";
import { Navbar } from "../components/landing/Navbar";
import { HeroSection } from "../components/landing/HeroSection";
import { LivePreview } from "../components/landing/LivePreview";
import { HowItWorks } from "../components/landing/HowItWorks";
import { StoreIntelligence } from "../components/landing/StoreIntelligence";
import { BusinessImpact } from "../components/landing/BusinessImpact";
import { TechStack } from "../components/landing/TechStack";
import { FinalCTA } from "../components/landing/FinalCTA";
import { Footer } from "../components/landing/Footer";

export function HomePage() {
  return (
    <div style={{ background: theme.bg.primary, color: theme.text.primary, fontFamily: theme.font, minHeight: "100vh", overflowX: "hidden" }}>
      <Navbar />
      <HeroSection />
      <LivePreview />
      <HowItWorks />
      <StoreIntelligence />
      <BusinessImpact />
      <TechStack />
      <FinalCTA />
      <Footer />
    </div>
  );
}
