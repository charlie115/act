"use client";

import { useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import mime from "mime";

import RichTextEditor from "components/RichTextEditor";
import { useAuth } from "../auth/AuthProvider";
import { getAllowedBoardCategories } from "../../lib/board";

export default function BoardPostEditorClient() {
  const router = useRouter();
  const { authorizedRequest, user } = useAuth();
  const quillRef = useRef(null);
  const [title, setTitle] = useState("");
  const [category, setCategory] = useState("");
  const [content, setContent] = useState("");
  const [isBusy, setIsBusy] = useState(false);
  const [pageError, setPageError] = useState("");

  const categories = useMemo(() => getAllowedBoardCategories(user), [user]);

  async function handleSubmit(event) {
    event.preventDefault();
    setIsBusy(true);
    setPageError("");

    try {
      const attachedImages =
        quillRef.current
          ?.getContents()
          ?.ops?.filter?.((op) => op.insert?.image) || [];

      const formData = new FormData();
      let htmlContent = content;

      const images = await Promise.all(
        attachedImages.map(async (item) => {
          const image = await fetch(item.insert.image);
          const mimeType = image.headers.get("content-type");
          const fileName = item.insert.image.split("/").pop();
          const fileExtension = mimeType ? mime.getExtension(mimeType) : "png";
          const normalizedName = `${fileName}.${fileExtension}`;

          htmlContent = htmlContent.replace(item.insert.image, normalizedName);

          const blob = await image.blob();
          return new File([blob], normalizedName, {
            type: blob.type,
          });
        })
      );

      images.forEach((image) => {
        formData.append("image", image);
      });

      formData.append("author", user.uuid);
      formData.append("title", title);
      formData.append("category", category);
      formData.append("content", htmlContent);

      const payload = await authorizedRequest("/board/posts/", {
        method: "POST",
        body: formData,
      });

      router.replace(`/community-board/post/${payload.id}`);
    } catch (requestError) {
      setPageError(requestError.message || "Failed to create board post.");
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <section className="surface-card">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Community Board</p>
          <h1>새 게시글 작성</h1>
        </div>
      </div>

      <form className="auth-form" onSubmit={handleSubmit}>
        <label className="auth-form__field" htmlFor="board-title">
          Title
        </label>
        <input
          className="auth-form__input"
          id="board-title"
          maxLength={150}
          onChange={(event) => setTitle(event.target.value)}
          required
          value={title}
        />

        <label className="auth-form__field" htmlFor="board-category">
          Category
        </label>
        <select
          className="select-input"
          id="board-category"
          onChange={(event) => setCategory(event.target.value)}
          required
          value={category}
        >
          <option value="">Select a category</option>
          {categories.map((item) => (
            <option key={item.value} value={item.value}>
              {item.getLabel?.() || item.value}
            </option>
          ))}
        </select>

        <label className="auth-form__field" htmlFor="board-content">
          Content
        </label>
        <div className="legacy-rich-editor" id="board-content">
          <RichTextEditor
            showToolbar
            ref={quillRef}
            readOnly={isBusy}
            onTextChange={(change) => {
              if (change?.ops?.[0]?.delete) {
                setContent("");
                return;
              }

              setContent(quillRef.current?.getSemanticHTML?.() || "");
            }}
          />
        </div>

        <div className="modal-card__actions">
          <button
            className="ghost-button ghost-button--button"
            onClick={() => router.push("/community-board")}
            type="button"
          >
            Cancel
          </button>
          <button
            className="primary-button ghost-button--button"
            disabled={!title.trim() || !category || !content.trim() || isBusy}
            type="submit"
          >
            {isBusy ? "Submitting..." : "Complete"}
          </button>
        </div>
      </form>

      {pageError ? <p className="auth-card__error">{pageError}</p> : null}
    </section>
  );
}
