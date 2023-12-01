import { DotReporter } from "vitest/reporters";

// See https://vitest.dev/guide/reporters.html#custom-reporters

class MinimalReporter extends DotReporter {
  async reportSummary() {
    // intentional no-op
  }
}

export default MinimalReporter;
