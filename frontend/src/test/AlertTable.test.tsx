import { describe, expect, it, vi } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AlertTable } from "../components/AlertTable";
import { renderWithProviders } from "./renderWithProviders";
import type { Alert } from "../api/types";

const base: Alert = {
  id: 1,
  greenhouse_id: 1,
  zone_id: 1,
  sensor_id: 1,
  alert_type: "threshold_high",
  severity: "critical",
  status: "open",
  message: "Temperature 40°C is above target",
  value: 40,
  threshold: "18–26 °C",
  created_at: new Date().toISOString(),
  acknowledged_at: null,
  resolved_at: null,
};

describe("AlertTable", () => {
  it("renders a row with message and severity", () => {
    renderWithProviders(<AlertTable alerts={[base]} />);
    expect(screen.getByText(base.message)).toBeInTheDocument();
    expect(screen.getByText("critical")).toBeInTheDocument();
  });

  it("calls onAcknowledge for open alerts", async () => {
    const onAcknowledge = vi.fn();
    renderWithProviders(
      <AlertTable alerts={[base]} onAcknowledge={onAcknowledge} />,
    );
    await userEvent.click(screen.getByRole("button", { name: /acknowledge/i }));
    expect(onAcknowledge).toHaveBeenCalledWith(1);
  });

  it("hides acknowledge for non-open alerts", () => {
    renderWithProviders(
      <AlertTable alerts={[{ ...base, status: "resolved" }]} />,
    );
    expect(screen.queryByRole("button", { name: /acknowledge/i })).toBeNull();
  });
});
