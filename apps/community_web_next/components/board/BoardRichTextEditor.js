"use client";

import { forwardRef, useCallback, useEffect, useLayoutEffect, useRef } from "react";

import Box from "@mui/material/Box";
import { useTheme } from "@mui/material/styles";

let _Quill = null;
let _Delta = null;
let _quillReady = null;

function loadQuill() {
  if (!_quillReady) {
    _quillReady = import("quill").then((mod) => {
      _Quill = mod.default;
      _Delta = _Quill.import("delta");

      class CustomImage extends _Quill.import("formats/image") {
        static sanitize(url) {
          return super.sanitize(url, ["http", "https", "data", "blob"]) ? url : "//:0";
        }
      }
      _Quill.register("formats/image", CustomImage);
      return _Quill;
    });
  }
  return _quillReady;
}

const BoardRichTextEditor = forwardRef(function BoardRichTextEditor(
  { defaultValue, onSelectionChange, onTextChange, readOnly, showToolbar },
  ref
) {
  const theme = useTheme();
  const containerRef = useRef(null);
  const toolbarRef = useRef(null);
  const defaultValueRef = useRef(defaultValue);
  const onTextChangeRef = useRef(onTextChange);
  const onSelectionChangeRef = useRef(onSelectionChange);

  const imageHandler = useCallback(() => {
    const input = document.createElement("input");
    input.setAttribute("type", "file");
    input.setAttribute("accept", "image/*");

    input.addEventListener("change", () => {
      const file = input.files?.[0];
      if (!file) {
        return;
      }

      const range = ref.current?.getSelection(true);
      const blobUrl = URL.createObjectURL(file);

      ref.current?.updateContents(
        new _Delta().retain(range.index).delete(range.length).insert({ image: blobUrl }),
        _Quill.sources.USER
      );
      ref.current?.setSelection(range.index + 1, _Quill.sources.USER);
      input.value = "";
    });

    input.click();
  }, [ref]);

  useLayoutEffect(() => {
    onTextChangeRef.current = onTextChange;
    onSelectionChangeRef.current = onSelectionChange;
  });

  useEffect(() => {
    ref.current?.enable(!readOnly);
  }, [imageHandler, readOnly, ref]);

  useEffect(() => {
    let cancelled = false;
    const container = containerRef.current;

    loadQuill().then((Quill) => {
      if (cancelled) return;
      const editorContainer = container.appendChild(
        container.ownerDocument.createElement("div")
      );
      const toolbar = readOnly
        ? false
        : {
            container: toolbarRef.current,
            handlers: {
              image: imageHandler,
            },
          };

      const quill = new Quill(editorContainer, {
        modules: { toolbar },
        readOnly,
        theme: "snow",
      });

      ref.current = quill;

      if (defaultValueRef.current) {
        quill.setContents(defaultValueRef.current);
      }

      quill.on(Quill.events.TEXT_CHANGE, (...args) => {
        onTextChangeRef.current?.(...args);
      });

      quill.on(Quill.events.SELECTION_CHANGE, (...args) => {
        onSelectionChangeRef.current?.(...args);
      });
    });

    return () => {
      cancelled = true;
      ref.current = null;
      container.innerHTML = "";
    };
  }, [imageHandler, readOnly, ref]);

  return (
    <Box>
      {showToolbar ? (
        <Box
          ref={toolbarRef}
          sx={{
            bgcolor: theme.palette.mode === "dark" ? "light.main" : undefined,
            border: "none!important",
          }}
        >
          <span className="ql-formats">
            <select className="ql-font" />
            <select className="ql-size" />
          </span>
          <span className="ql-formats">
            <button className="ql-bold" />
            <button className="ql-italic" />
            <button className="ql-underline" />
            <button className="ql-strike" />
          </span>
          <span className="ql-formats">
            <select className="ql-color" />
            <select className="ql-background" />
          </span>
          <span className="ql-formats">
            <button className="ql-script" value="sub" />
            <button className="ql-script" value="super" />
          </span>
          <span className="ql-formats">
            <button className="ql-header" value="1" />
            <button className="ql-header" value="2" />
            <button className="ql-blockquote" />
            <button className="ql-code-block" />
          </span>
          <span className="ql-formats">
            <button className="ql-list" value="ordered" />
            <button className="ql-list" value="bullet" />
            <button className="ql-indent" value="-1" />
            <button className="ql-indent" value="+1" />
          </span>
          <span className="ql-formats">
            <button className="ql-direction" value="rtl" />
            <select className="ql-align" />
          </span>
          <span className="ql-formats">
            <button className="ql-link" />
            <button className="ql-image" />
          </span>
        </Box>
      ) : null}
      <Box
        component="div"
        ref={containerRef}
        sx={{
          minHeight: readOnly ? "auto" : 400,
          ".ql-container": {
            border: "none!important",
            ".ql-editor": {
              minHeight: readOnly ? "auto" : 400,
            },
          },
        }}
      />
    </Box>
  );
});

export default BoardRichTextEditor;
