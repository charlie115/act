import { createTheme } from "@mui/material/styles";

const theme = createTheme({
  palette: {
    mode: "dark",
    primary: {
      main: "#2b73ff",
    },
    secondary: {
      main: "#0f9980",
    },
    background: {
      default: "#080c16",
      paper: "#121a2c",
    },
    text: {
      primary: "#eef2ff",
      secondary: "#8f9bb7",
    },
  },
  shape: {
    borderRadius: 12,
  },
});

export default theme;
