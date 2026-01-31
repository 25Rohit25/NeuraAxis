import Mention from "@tiptap/extension-mention";
import { ReactRenderer } from "@tiptap/react";
import tippy from "tippy.js";
import { SuggestionList } from "./SuggestionList"; // We will create this

export const MedicalAutocomplete = Mention.extend({
  name: "medicalAutocomplete",
}).configure({
  HTMLAttributes: {
    class: "medical-term",
  },
  suggestion: {
    char: "#",
    items: ({ query }) => {
      const db = [
        "Hypertension",
        "Diabetes Mellitus",
        "Hyperlipidemia",
        "Asthma",
        "COPD",
        "Pneumonia",
        "Bronchitis",
        "Atrial Fibrillation",
        "Heart Failure",
        "Appendicitis",
        "Cholecystitis",
        "Pancreatitis",
        "Migraine",
        "Seizure Disorder",
        "Stroke",
        "Anemia",
        "Thrombocytopenia",
        "Leukocytois",
        "Gastroesophageal Reflux Disease",
        "Peptic Ulcer Disease",
      ];
      return db
        .filter((item) => item.toLowerCase().startsWith(query.toLowerCase()))
        .slice(0, 5);
    },
    render: () => {
      let component: ReactRenderer;
      let popup: any;

      return {
        onStart: (props) => {
          component = new ReactRenderer(SuggestionList, {
            props,
            editor: props.editor,
          });

          if (!props.clientRect) {
            return;
          }

          popup = tippy("body", {
            getReferenceClientRect: props.clientRect,
            appendTo: () => document.body,
            content: component.element,
            showOnCreate: true,
            interactive: true,
            trigger: "manual",
            placement: "bottom-start",
          });
        },
        onUpdate(props) {
          component.updateProps(props);

          if (!props.clientRect) {
            return;
          }

          popup[0].setProps({
            getReferenceClientRect: props.clientRect,
          });
        },
        onKeyDown(props) {
          if (props.event.key === "Escape") {
            popup[0].hide();
            return true;
          }
          return component.ref?.onKeyDown(props);
        },
        onExit() {
          popup[0].destroy();
          component.destroy();
        },
      };
    },
  },
});
