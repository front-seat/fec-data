import { describe, expect, it } from "vitest";
import { toTitleCase } from "./format";

describe("toTitleCase()", () => {
  it("converts a string to title case", () => {
    expect(toTitleCase("hello world")).toBe("Hello World");
  });

  it("handles empty strings", () => {
    expect(toTitleCase("")).toBe("");
  });

  it("handles strings all in upercase", () => {
    expect(toTitleCase("HELLO WORxLD")).toBe("Hello World");
  });

  it("handles strings with punctuation", () => {
    expect(toTitleCase("hello, world!")).toBe("Hello, World!");
  });
});
