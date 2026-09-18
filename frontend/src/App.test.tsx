import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import App from "./App";

describe("Veya foundation dashboard", () => {
  it("renders the product message", () => {
    render(<App />);

    expect(
      screen.getByRole("heading", {
        name: /understand your audience without absorbing the negativity/i,
      }),
    ).toBeInTheDocument();
  });

  it("renders the sentiment summary cards", () => {
    render(<App />);

    expect(screen.getByText("Positive")).toBeInTheDocument();
    expect(screen.getByText("Neutral")).toBeInTheDocument();
    expect(screen.getByText("Negative")).toBeInTheDocument();
    expect(screen.getByText("Toxic filtered")).toBeInTheDocument();
  });
});
