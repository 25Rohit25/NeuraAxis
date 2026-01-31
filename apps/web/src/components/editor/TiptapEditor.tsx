import { HocuspocusProvider } from "@hocuspocus/provider";
import Collaboration from "@tiptap/extension-collaboration";
import CollaborationCursor from "@tiptap/extension-collaboration-cursor";
import { EditorContent, useEditor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import React, { useEffect, useState } from "react";
import * as Y from "yjs";
import { EditorToolbar } from "./EditorToolbar";
import { MacroExpander } from "./extensions/MacroExpander";
import { MedicalAutocomplete } from "./extensions/MedicalAutocomplete";

// Styles for cursors and mentions (would typically be in a CSS file)
const styles = `
.collaboration-cursor__caret {
  border-left: 1px solid #0d0d0d;
  border-right: 1px solid #0d0d0d;
  margin-left: -1px;
  margin-right: -1px;
  pointer-events: none;
  position: relative;
  word-break: normal;
}
.collaboration-cursor__label {
  border-radius: 3px 3px 3px 0;
  color: #0d0d0d;
  font-size: 12px;
  font-style: normal;
  font-weight: 600;
  left: -1px;
  line-height: normal;
  padding: 0.1rem 0.3rem;
  position: absolute;
  top: -1.4em;
  user-select: none;
  white-space: nowrap;
}
.medical-term {
    color: #2563eb;
    background-color: #dbeafe;
    border-radius: 0.25rem;
    padding: 0.125rem 0.25rem;
}
`;

interface TiptapEditorProps {
  documentId: string;
  user: {
    name: string;
    color: string;
  };
}

export const TiptapEditor: React.FC<TiptapEditorProps> = ({
  documentId,
  user,
}) => {
  const [provider, setProvider] = useState<HocuspocusProvider | null>(null);

  useEffect(() => {
    // Initialize Y.js document
    const ydoc = new Y.Doc();

    // Connect to Hocuspocus (Y.js Backend)
    // In production, this URL should be your websocket server.
    // We assume the realtime-service facilitates this or a separate instance running.
    const newProvider = new HocuspocusProvider({
      url: process.env.NEXT_PUBLIC_COLLAB_URL || "ws://localhost:1234",
      name: documentId,
      document: ydoc,
      onAuthenticationFailed: () => {
        console.error("Auth failed");
      },
    });

    setProvider(newProvider);

    return () => {
      newProvider.destroy();
    };
  }, [documentId]);

  const editor = useEditor(
    {
      extensions: [
        StarterKit.configure({
          history: false, // Y.js handles history
        }),
        MacroExpander,
        MedicalAutocomplete,
        Collaboration.configure({
          document: provider?.document,
        }),
        CollaborationCursor.configure({
          provider: provider,
          user: {
            name: user.name,
            color: user.color,
          },
        }),
      ],
      editorProps: {
        attributes: {
          class:
            "prose prose-sm sm:prose lg:prose-lg xl:prose-xl focus:outline-none max-w-none p-4 min-h-[500px]",
        },
      },
      dependencies: [provider],
    },
    [provider]
  );

  if (!editor || !provider) {
    return <div>Loading editor...</div>;
  }

  return (
    <div className="border border-zinc-200 dark:border-zinc-800 rounded-lg overflow-hidden bg-white dark:bg-zinc-900 shadow-sm flex flex-col h-full">
      <style>{styles}</style>
      <EditorToolbar editor={editor} />
      <EditorContent editor={editor} className="flex-1 overflow-y-auto" />
      <div className="p-2 bg-zinc-50 dark:bg-zinc-950 text-xs text-zinc-500 border-t border-zinc-200 dark:border-zinc-800 flex justify-between">
        <span>{provider.status}</span>
        <span>{editor.storage.characterCount?.words()} words</span>
      </div>
    </div>
  );
};
