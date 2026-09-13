import type { ReviewOutcome } from "../../intelligence-contracts/src";

export interface ReviewDraft {
  readonly alertRef: string;
  readonly outcome: ReviewOutcome | null;
  readonly reasonCode: string;
  readonly createdAt: string;
}
export type DraftPurgeReason =
  "logout" | "department_switch" | "role_loss" | "expiry" | "route_disposal" | "window_close";
export class MemoryReviewDrafts {
  readonly #drafts = new Map<string, ReviewDraft>();
  #lastPurgeReason: DraftPurgeReason | null = null;
  set(draft: ReviewDraft) {
    this.#drafts.set(draft.alertRef, Object.freeze({ ...draft }));
  }
  get(alertRef: string) {
    return this.#drafts.get(alertRef) ?? null;
  }
  purge(reason: DraftPurgeReason) {
    const count = this.#drafts.size;
    this.#lastPurgeReason = reason;
    this.#drafts.clear();
    return count;
  }
  get size() {
    return this.#drafts.size;
  }
  get lastPurgeReason() {
    return this.#lastPurgeReason;
  }
}
