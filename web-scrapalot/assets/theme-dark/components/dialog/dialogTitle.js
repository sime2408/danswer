

// NextJS Material Dashboard 2 PRO base styles
import typography from "/assets/theme-dark/base/typography";

// NextJS Material Dashboard 2 PRO helper functions
import pxToRem from "/assets/theme-dark/functions/pxToRem";

const { size } = typography;

const dialogTitle = {
  styleOverrides: {
    root: {
      padding: pxToRem(16),
      fontSize: size.xl,
    },
  },
};

export default dialogTitle;
