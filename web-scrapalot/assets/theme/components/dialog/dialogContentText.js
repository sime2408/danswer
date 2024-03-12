

// NextJS Material Dashboard 2 PRO base styles
import typography from "/assets/theme/base/typography";
import colors from "/assets/theme/base/colors";

// NextJS Material Dashboard 2 PRO helper functions
// import pxToRem from "/assets/theme/functions/pxToRem";

const { size } = typography;
const { text } = colors;

const dialogContentText = {
  styleOverrides: {
    root: {
      fontSize: size.md,
      color: text.main,
    },
  },
};

export default dialogContentText;
