import "@testing-library/jest-dom/vitest";

const dialogPrototype = HTMLDialogElement.prototype as HTMLDialogElement & {
  showModal?: () => void;
  close?: () => void;
};
if (typeof dialogPrototype.showModal !== "function") {
  Object.defineProperty(dialogPrototype, "showModal", {
    configurable: true,
    value(this: HTMLDialogElement) {
      this.setAttribute("open", "");
    },
  });
}
if (typeof dialogPrototype.close !== "function") {
  Object.defineProperty(dialogPrototype, "close", {
    configurable: true,
    value(this: HTMLDialogElement) {
      this.removeAttribute("open");
    },
  });
}
