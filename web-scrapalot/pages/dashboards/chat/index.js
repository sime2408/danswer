import React from 'react';
import DashboardLayout from "../../../examples/LayoutContainers/DashboardLayout";
import DashboardNavbar from "../../../examples/Navbars/DashboardNavbar";
import MDBox from "../../../components/MDBox";
import Grid from "@mui/material/Grid";
import ChatWithAICard from "../../../examples/Cards/StatisticsCards/ChatWithAICard";

const ChatPage = () => {
  return (
    <DashboardLayout>
      <DashboardNavbar />
      <MDBox py={3}>
        <Grid container>
            <ChatWithAICard
                color="dark"
                icon="assistant"
                title="Talk to your documents"
            />
        </Grid>
      </MDBox>
    </DashboardLayout>
  );
};

export default ChatPage;
