import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { LoginPage } from "./LoginPage"

vi.mock("./useAuth", () => ({
  useLogin: vi.fn(),
}))

import { useLogin } from "./useAuth"

const mockMutate = vi.fn()

function defaultMutation() {
  return {
    mutate: mockMutate,
    isPending: false,
    isError: false,
    error: null,
  }
}

afterEach(cleanup)

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(useLogin).mockReturnValue(defaultMutation() as any)
})

describe("LoginPage", () => {
  it("renders email input, password input, and submit button", () => {
    render(<LoginPage />)

    expect(screen.getByTestId("email-input")).toBeInTheDocument()
    expect(screen.getByTestId("password-input")).toBeInTheDocument()
    expect(
      screen.getByRole("button", { name: /log in/i }),
    ).toBeInTheDocument()
  })

  it("shows inline error message when login fails with 401", () => {
    vi.mocked(useLogin).mockReturnValue({
      ...defaultMutation(),
      isError: true,
      error: {
        response: {
          data: { error: { message: "Invalid email or password." } },
        },
      },
    } as any)

    render(<LoginPage />)

    expect(
      screen.getByText("Invalid email or password."),
    ).toBeInTheDocument()
  })

  it("calls mutate with email and password on form submit", async () => {
    const user = userEvent.setup()
    render(<LoginPage />)

    await user.type(screen.getByTestId("email-input"), "test@example.com")
    await user.type(screen.getByTestId("password-input"), "password123")
    await user.click(screen.getByRole("button", { name: /log in/i }))

    expect(mockMutate).toHaveBeenCalledWith({
      email: "test@example.com",
      password: "password123",
    })
  })
})
