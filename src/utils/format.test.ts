import { describe, expect, it } from "vitest";
import { formatPercent, formatUSD, toTitleCase } from "./format";

describe("toTitleCase()", () => {
  it("converts a string to title case", () => {
    expect(toTitleCase("hello world")).toBe("Hello World");
  });

  it("handles empty strings", () => {
    expect(toTitleCase("")).toBe("");
  });

  it("handles strings all in upercase", () => {
    expect(toTitleCase("HELLO WORLD")).toBe("Hello World");
  });

  it("handles strings with punctuation", () => {
    expect(toTitleCase("hello, world!")).toBe("Hello, World!");
  });
});

describe("formatPercent()", () => {
  it("formats a number as a percentage", () => {
    expect(formatPercent(0.1234)).toBe("12.3%");
  });

  it("handles fractions", () => {
    expect(formatPercent(0.1234, 2)).toBe("12.34%");
  });
});

describe("formatUSD()", () => {
  it("formats a number as a dollar amount", () => {
    expect(formatUSD(123456)).toBe("$1,235");
  });

  it("handles fractions", () => {
    expect(formatUSD(123456, 2)).toBe("$1,234.56");
  });
});
