import { Editor } from "@tiptap/react";
import React from "react";

interface EditorToolbarProps {
  editor: Editor | null;
}

export const EditorToolbar: React.FC<EditorToolbarProps> = ({ editor }) => {
  if (!editor) {
    return null;
  }

  const toggleBold = () => editor.chain().focus().toggleBold().run();
  const toggleItalic = () => editor.chain().focus().toggleItalic().run();
  const toggleH2 = () =>
    editor.chain().focus().toggleHeading({ level: 2 }).run();
  const toggleBulletList = () =>
    editor.chain().focus().toggleBulletList().run();

  const insertSOAP = () => {
    editor
      .chain()
      .focus()
      .insertContent([
        {
          type: "heading",
          attrs: { level: 2 },
          content: [{ type: "text", text: "SOAP Note" }],
        },
        { type: "paragraph" },
      ])
      .run();
  };

  const isActive = (type: string, opts?: any) =>
    editor.isActive(type, opts) ? "bg-zinc-200 dark:bg-zinc-700" : "";
  const btnClass =
    "px-2 py-1 rounded hover:bg-zinc-100 dark:hover:bg-zinc-800 transition text-sm text-zinc-700 dark:text-zinc-200";

  return (
    <div className="border-b border-zinc-200 dark:border-zinc-800 p-2 flex space-x-2 bg-white dark:bg-zinc-900 sticky top-0 z-10">
      <div className="flex space-x-1 border-r border-zinc-200 dark:border-zinc-700 pr-2">
        <button
          onClick={toggleBold}
          className={`${btnClass} ${isActive("bold")}`}
        >
          B
        </button>
        <button
          onClick={toggleItalic}
          className={`${btnClass} ${isActive("italic")}`}
        >
          I
        </button>
      </div>

      <div className="flex space-x-1 border-r border-zinc-200 dark:border-zinc-700 pr-2">
        <button
          onClick={toggleH2}
          className={`${btnClass} ${isActive("heading", { level: 2 })}`}
        >
          H2
        </button>
        <button
          onClick={toggleBulletList}
          className={`${btnClass} ${isActive("bulletList")}`}
        >
          List
        </button>
      </div>

      <div className="flex space-x-1">
        <button
          onClick={() => editor.chain().focus().undo().run()}
          className={btnClass}
          disabled={!editor.can().undo()}
        >
          Undo
        </button>
        <button
          onClick={() => editor.chain().focus().redo().run()}
          className={btnClass}
          disabled={!editor.can().redo()}
        >
          Redo
        </button>
      </div>

      <div className="flex-1" />

      <div className="flex space-x-1">
        <button
          onClick={insertSOAP}
          className={`${btnClass} text-blue-600 font-medium`}
        >
          + SOAP
        </button>
      </div>
    </div>
  );
};
