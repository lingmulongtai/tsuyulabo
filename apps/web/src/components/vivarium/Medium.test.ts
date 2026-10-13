import { expect, it } from "vitest";
import { foodHeight, foodSurfaceGeometry } from "./Medium";

it("faces the wet surface upward so it is visible through the glass", () => {
  const geometry = foodSurfaceGeometry();
  try {
    const normals = geometry.getAttribute("normal");
    for (let i = 129; i < normals.count - 129; i++) expect(normals.getY(i)).toBeGreaterThan(0);
  } finally { geometry.dispose(); }
});
it("raises the wall meniscus and recesses a larval pit", () => {
  expect(foodHeight(11.8, 0)).toBeGreaterThan(foodHeight(10, 0) + 0.4);
  expect(foodHeight(-2.1, 1.5)).toBeLessThan(foodHeight(-2.8, 1.5) - 0.15);
});
