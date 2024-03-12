import React, { useState } from "react";
import PropTypes from "prop-types";
import Card from "@mui/material/Card";
import Grid from "@mui/material/Grid";
import MDBox from "/components/MDBox";
import MDButton from "/components/MDButton";
import MDTypography from "/components/MDTypography";
import Icon from "@mui/material/Icon";
import TextField from "@mui/material/TextField";
import SendIcon from "@mui/icons-material/Send";
import pxToRem from "/assets/theme/functions/pxToRem";

function ChatWithAICard({ color, icon, title }) {
  const [message, setMessage] = useState("");

  const commonQuestions = [
    "How to reset my password?",
    "Where can I find my invoices?",
    "How to contact support?",
    "Can I upgrade my plan?",
  ];

  const handleSendMessage = () => {
    console.log(message); // Replace with your send message logic
    setMessage("");
  };

  return (
   <Card sx={{
     width: "100%",
     minHeight: "400px",
     height: `calc(100vh - ${pxToRem(145)})`,
     marginBottom: pxToRem(8),
     display: "flex",
     flexDirection: "column"
   }}>
     <MDBox display="flex">
       <MDBox
        display="flex"
        justifyContent="center"
        alignItems="center"
        width="4rem"
        height="4rem"
        variant="gradient"
        bgColor={color}
        color={color === "light" ? "dark" : "white"}
        coloredShadow={color}
        shadow="md"
        borderRadius="xl"
        ml={3}
        mt={-2}
       >
         <Icon fontSize="medium" color="inherit">
           {icon}
         </Icon>
       </MDBox>
       <MDTypography variant="h6" sx={{ mt: 2, mb: 1, ml: 2 }}>
         {title}
       </MDTypography>
     </MDBox>
     <MDBox flexGrow={1} display="flex" flexDirection="column" alignItems="center" justifyContent="center" p={2}>
       <Icon fontSize="large" color="inherit">
         {icon}
       </Icon>
       <MDTypography variant="h5" mt={2} mb={2}>
         How can I help you today?
       </MDTypography>
     </MDBox>
     <MDBox p={2}>
       <Grid container spacing={2}>
         {commonQuestions.map((question) => (
          <Grid item xs={6} key={question}>
            <MDButton variant="outlined" color="dark" fullWidth>
              {question}
            </MDButton>
          </Grid>
         ))}
       </Grid>
       <MDBox mt={2} display="flex" alignItems="center">
         <TextField
          fullWidth
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Type your message..."
          variant="outlined"
          sx={{ mr: 1 }}
         />
         <MDButton variant="gradient" color="dark" onClick={handleSendMessage} sx={{ height: "44px" }}>
           <SendIcon />
         </MDButton>
       </MDBox>
     </MDBox>
   </Card>
  );
}

ChatWithAICard.defaultProps = {
  color: "dark",
  icon: "chat",
  title: "Chat with AI",
};

ChatWithAICard.propTypes = {
  color: PropTypes.oneOf([
    "primary",
    "secondary",
    "info",
    "success",
    "warning",
    "error",
    "light",
    "dark",
  ]),
  icon: PropTypes.node.isRequired,
  title: PropTypes.string.isRequired,
};

export default ChatWithAICard;
