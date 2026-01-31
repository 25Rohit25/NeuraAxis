import { Extension, InputRule } from "@tiptap/core";

export const MacroExpander = Extension.create({
  name: "macroExpander",

  addInputRules() {
    return [
      // .soap macro
      new InputRule({
        find: /\.soap$/,
        handler: ({ state, range, chain }) => {
          chain()
            .deleteRange(range)
            .insertContent([
              {
                type: "heading",
                attrs: { level: 2 },
                content: [{ type: "text", text: "SOAP Note" }],
              },
              {
                type: "heading",
                attrs: { level: 3 },
                content: [{ type: "text", text: "Subjective" }],
              },
              { type: "paragraph" },
              {
                type: "heading",
                attrs: { level: 3 },
                content: [{ type: "text", text: "Objective" }],
              },
              { type: "paragraph" },
              {
                type: "heading",
                attrs: { level: 3 },
                content: [{ type: "text", text: "Assessment" }],
              },
              { type: "paragraph" },
              {
                type: "heading",
                attrs: { level: 3 },
                content: [{ type: "text", text: "Plan" }],
              },
              { type: "paragraph" },
            ])
            .run();
        },
      }),

      // .hpi macro
      new InputRule({
        find: /\.hpi$/,
        handler: ({ range, chain }) => {
          chain()
            .deleteRange(range)
            .insertContent([
              {
                type: "heading",
                attrs: { level: 3 },
                content: [{ type: "text", text: "History of Present Illness" }],
              },
              {
                type: "bulletList",
                content: [
                  {
                    type: "listItem",
                    content: [
                      {
                        type: "paragraph",
                        content: [{ type: "text", text: "Onset: " }],
                      },
                    ],
                  },
                  {
                    type: "listItem",
                    content: [
                      {
                        type: "paragraph",
                        content: [{ type: "text", text: "Location: " }],
                      },
                    ],
                  },
                  {
                    type: "listItem",
                    content: [
                      {
                        type: "paragraph",
                        content: [{ type: "text", text: "Duration: " }],
                      },
                    ],
                  },
                  {
                    type: "listItem",
                    content: [
                      {
                        type: "paragraph",
                        content: [{ type: "text", text: "Character: " }],
                      },
                    ],
                  },
                  {
                    type: "listItem",
                    content: [
                      {
                        type: "paragraph",
                        content: [
                          { type: "text", text: "Aggravating/Alleviating: " },
                        ],
                      },
                    ],
                  },
                  {
                    type: "listItem",
                    content: [
                      {
                        type: "paragraph",
                        content: [{ type: "text", text: "Radiation: " }],
                      },
                    ],
                  },
                  {
                    type: "listItem",
                    content: [
                      {
                        type: "paragraph",
                        content: [{ type: "text", text: "Timing: " }],
                      },
                    ],
                  },
                ],
              },
            ])
            .run();
        },
      }),

      // .lab macro
      new InputRule({
        find: /\.lab$/,
        handler: ({ range, chain }) => {
          chain()
            .deleteRange(range)
            .insertContent({
              type: "codeBlock",
              attrs: { language: "json" },
              content: [
                {
                  type: "text",
                  text: "Lab Results:\n- Hb: \n- WBC: \n- Plt: ",
                },
              ],
            })
            .run();
        },
      }),
    ];
  },
});
