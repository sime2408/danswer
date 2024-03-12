

import React from "react";

// prop-types is a library for typechecking of props
import PropTypes from "prop-types";

import dynamic from "next/dynamic";

// draft-js
import { EditorState } from "draft-js";
const Editor = dynamic(
  () => import("react-draft-wysiwyg").then((mod) => mod.Editor),
  { ssr: false }
);
import { convertToHTML } from "draft-convert";
import "react-draft-wysiwyg/dist/react-draft-wysiwyg.css";

// Custom styles for the MDEditor
import MDEditorRoot from "./MDEditorRoot";

// Material Dashboard 2 PRO React context
import { useMaterialUIController } from "../../context";

function MDEditor({ value }) {
  const [controller] = useMaterialUIController();
  const { darkMode } = controller;

  const [convertedContent, setConvertedContent] = React.useState(null);
  const [editorState, setEditorState] = React.useState(() =>
    EditorState.createEmpty()
  );

  React.useEffect(() => {
    let html = convertToHTML(editorState.getCurrentContent());
    setConvertedContent(html);
  }, [editorState]);

  return (
    <MDEditorRoot ownerState={{ darkMode }}>
      {value && typeof value === "function" && value(convertedContent)}
      <Editor editorState={editorState} onEditorStateChange={setEditorState} />
    </MDEditorRoot>
  );
}

// Setting default values for the props of MDEditor
MDEditor.defaultProps = {
  value: () => {},
};

// Typechecking props for the MDEditor
MDEditor.propTypes = {
  value: PropTypes.func,
};

export default MDEditor;
