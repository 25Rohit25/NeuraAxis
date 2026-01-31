import React from "react";

interface ViewerToolbarProps {
  activeTool: string;
  onToolSelect: (tool: string) => void;
}

export const ViewerToolbar: React.FC<ViewerToolbarProps> = ({
  activeTool,
  onToolSelect,
}) => {
  const tools = [
    { id: "WindowLevel", label: "W/L", icon: "Adjust" },
    { id: "Zoom", label: "Zoom", icon: "Search" },
    { id: "Pan", label: "Pan", icon: "Move" },
    { id: "Length", label: "Ruler", icon: "Ruler" },
    { id: "Annotation", label: "Annotate", icon: "Edit" },
  ];

  const layouts = [
    { id: "1x1", label: "Axial" },
    { id: "mpr", label: "MPR 3D" },
  ];

  return (
    <div className="h-12 bg-zinc-900 border-b border-zinc-800 flex items-center px-4 justify-between">
      <div className="flex space-x-2">
        {tools.map((tool) => (
          <button
            key={tool.id}
            onClick={() => onToolSelect(tool.id)}
            className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
              activeTool === tool.id
                ? "bg-blue-600 text-white"
                : "bg-zinc-800 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-700"
            }`}
          >
            {tool.label}
          </button>
        ))}
      </div>

      <div className="flex space-x-2 border-l border-zinc-800 pl-4">
        {layouts.map((l) => (
          <button
            key={l.id}
            className="px-3 py-1.5 rounded text-sm font-medium bg-zinc-800 text-zinc-400 hover:bg-zinc-700"
          >
            {l.label}
          </button>
        ))}
      </div>
    </div>
  );
};
