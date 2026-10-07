import { describe, expect, it, vi } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ErrorState } from "../components/ErrorState";
import { renderWithProviders } from "./renderWithProviders";

describe("ErrorState", () => {
  it("renders the message and calls onRetry", async () => {
    const onRetry = vi.fn();
    renderWithProviders(<ErrorState message="boom" onRetry={onRetry} />);
    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.getByText("boom")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /retry/i }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });
});
