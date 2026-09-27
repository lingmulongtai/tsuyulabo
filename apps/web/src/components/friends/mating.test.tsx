import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { afterEach, expect, it, vi } from "vitest";
import type { components } from "@/lib/api/schema";
import { wildType } from "@/game/genetics";
import { MatingForm } from "./MatingProposal";
import { MatingMessage } from "./MatingInbox";
import { PendingEggChoices } from "../breeding/PendingEggChoices";
import { OffspringPrediction } from "../breeding/OffspringPrediction";

const mocks = vi.hoisted(() => ({
  mutation: { isPending: false, isSuccess: false, error: null, mutate: vi.fn(), reset: vi.fn() },
  eggs: { data: [] as components["schemas"]["PendingEggView"][], error: null, isPending: false, refetch: vi.fn() },
}));
vi.mock("@/lib/api/hooks-mating", () => ({
  useProposeMating: () => mocks.mutation,
  useAcceptMating: () => mocks.mutation,
  useDeclineMating: () => mocks.mutation,
  usePendingEggs: () => mocks.eggs,
}));
afterEach(() => { mocks.mutation.isPending = false; mocks.mutation.isSuccess = false; mocks.eggs.data = []; });

const proposal: components["schemas"]["MatingView"] = {
  id: "p", proposer_id: "a", proposer_name: "あお", recipient_id: "b", recipient_name: "みどり",
  mother_id: "m", mother_name: "つゆこ", father_id: "f", father_name: "つゆお",
  status: "pending", created_at: "2026-09-27T00:00:00Z", expires_at: "2026-09-29T00:00:00Z",
};
const friend: components["schemas"]["MatingOption"] = {
  id: "f", name: "つゆお", sex: "m", available: true,
  genotype: { sex: "m", w: ["+"], y: ["+"], e: ["+", "+"], vg: ["+", "+"], Cy: ["+", "+"] },
};

it("only offers own adults of the opposite sex and disables an unselected proposal", () => {
  const adults = [
    { id: "m", name: "選べる母親", sex: "f" },
    { id: "f2", name: "選べない父親", sex: "m" },
  ] as components["schemas"]["Adult"][];
  const html = renderToStaticMarkup(createElement(MatingForm, { friendId: "b", friend, adults }));
  expect(html).toContain("選べる母親");
  expect(html).not.toContain("選べない父親");
  expect(html).toMatch(/<button[^>]*disabled=""/);
  expect(html).toContain("48時間");
});

it("explains missing candidates and used parents", () => {
  const html = renderToStaticMarkup(createElement(MatingForm, { friendId: "b", friend: { ...friend, available: false }, adults: [] }));
  expect(html).toContain("異性の成虫がまだいません");
  expect(html).toContain("今週すでに交配しています");
});

it.each(["accepted", "declined", "expired"] as const)("does not offer responses for %s proposals", status => {
  const html = renderToStaticMarkup(createElement(MatingMessage, { proposal: { ...proposal, status }, incoming: true }));
  expect(html).not.toContain("承諾する");
  expect(html).not.toContain("辞退する");
  if (status === "accepted") expect(html).toContain("ホームで卵を選ぶ");
});

it("offers responses only on incoming pending messages and disables them in flight", () => {
  let html = renderToStaticMarkup(createElement(MatingMessage, { proposal, incoming: false }));
  expect(html).not.toContain("承諾する");
  html = renderToStaticMarkup(createElement(MatingMessage, { proposal, incoming: true }));
  expect(html).toContain("承諾する");
  expect(html).toContain("辞退する");
  expect(html).toContain("次の週まで保留");
  mocks.mutation.isPending = true;
  html = renderToStaticMarkup(createElement(MatingMessage, { proposal, incoming: true }));
  expect(html.match(/<button[^>]*disabled=""/g)).toHaveLength(2);
});

it("offers pending eggs by parent names without promising a sex or phenotype", () => {
  mocks.eggs.data = [{ id: "egg", proposal_id: "p", mother_id: "m", mother_name: "つゆこ", father_id: "f", father_name: "つゆお", created_at: proposal.created_at }];
  const html = renderToStaticMarkup(createElement(PendingEggChoices, { pending: true, onStart: vi.fn() }));
  expect(html).toContain("つゆこ");
  expect(html).toContain("この卵で一週間をはじめる");
  expect(html).toContain("性別や見た目は羽化までのお楽しみ");
  expect(html).toMatch(/<button[^>]*disabled=""/);
});

it("uses the existing Punnett prediction with lethal odds and model limits", () => {
  const html = renderToStaticMarkup(createElement(OffspringPrediction, {
    mother: { ...wildType("f"), Cy: ["Cy", "+"] },
    father: { ...wildType("m"), Cy: ["Cy", "+"] },
  }));
  expect(html).toContain("25%");
  expect(html).toContain("連鎖と羽化時の新しい突然変異は含みません");
  expect(html).toContain("育つ子だけで計算");
});
