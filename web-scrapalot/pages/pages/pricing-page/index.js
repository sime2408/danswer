import { useState } from "react";

// @mui material components
import Container from "@mui/material/Container";

// NextJS Material Dashboard 2 PRO examples
import PageLayout from "/examples/LayoutContainers/PageLayout";

// Pricing page components
import Header from "/pagesComponents/pages/pricing-page/components/Header";
import Footer from "/pagesComponents/pages/pricing-page/components/Footer";
import PricingCards from "/pagesComponents/pages/pricing-page/components/PricingCards";
import TrustedBrands from "/pagesComponents/pages/pricing-page/components/TrustedBrands";
import Faq from "/pagesComponents/pages/pricing-page/components/Faq";

function PricingPage() {
  const [tabValue, setTabValue] = useState(0);
  const [prices, setPrices] = useState(["59", "89", "99"]);

  const handleSetTabValue = (event, newValue) => {
    setTabValue(newValue);

    if (event.currentTarget.id === "annual") {
      setPrices(["119", "159", "399"]);
    } else {
      setPrices(["59", "89", "99"]);
    }
  };

  return (
    <PageLayout>
      <Header tabValue={tabValue} tabHandler={handleSetTabValue}>
        <Container>
          <PricingCards prices={prices} />
          <TrustedBrands />
          <Faq />
        </Container>
      </Header>
      <Footer />
    </PageLayout>
  );
}

export default PricingPage;
